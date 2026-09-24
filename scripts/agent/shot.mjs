// 零依赖 CDP 截图。
//   单张：node shot.mjs <url> <outfile> [w] [h] [clickSel]
//   批量：node shot.mjs --batch <manifest.json>      （彻查 P5 · 视觉回归批处理用）
// 批量清单形如 {"shots":[{"url","out","w","h","click","init","settle"}]}：
//   一个 Chrome、多个标签页依次截，省掉"每张重启浏览器"的 5 秒；
//   init = 在页面任何脚本之前注入的 JS（`Page.addScriptToEvaluateOnNewDocument`），
//   用来把 localStorage 偏好钉成确定态（主题、动效、阅读宽度），否则截出来的图每次不一样。
import { spawn } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';

const PORT = +(process.env.KB_SHOT_PORT || 9333);
const CDP = `http://127.0.0.1:${PORT}`;
const [, , arg1, arg2] = process.argv;
const BATCH = arg1 === '--batch';

const CHROME_CANDIDATES = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  path.join(process.env.LOCALAPPDATA || '', 'Google/Chrome/Application/chrome.exe'),
].filter(Boolean);
const chrome = CHROME_CANDIDATES.find(p => { try { return fs.existsSync(p); } catch { return false; } });
if (!chrome) { console.error('chrome not found'); process.exit(3); }

if (!BATCH && !arg1) {
  console.error('usage: node shot.mjs <url> <out> [w] [h] [clickSel]\n   or: node shot.mjs --batch <manifest.json>');
  process.exit(2);
}

// 稳定性开关：色域与字体 hinting 固定下来，同一份代码两次截图才可能逐像素相同。
const FLAGS = ['--headless=new', `--remote-debugging-port=${PORT}`,
  '--no-first-run', '--disable-gpu', '--force-color-profile=srgb',
  '--font-render-hinting=none', '--disable-lcd-text', 'about:blank'];

const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'kbshot-'));
const proc = spawn(chrome, [`--user-data-dir=${profile}`, ...FLAGS], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));

const waitPort = async () => {
  for (let i = 0; i < 40; i++) {
    try { const r = await fetch(`${CDP}/json/version`); if (r.ok) return; } catch {}
    await sleep(300);
  }
  throw new Error('CDP port not ready');
};

/** 连上一个新标签页，返回 {ws, send}。 */
async function openTab(url) {
  const res = await fetch(`${CDP}/json/new?${encodeURIComponent(url)}`, { method: 'PUT' });
  const tab = await res.json();
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((ok, err) => { ws.onopen = ok; ws.onerror = err; });
  let id = 0;
  const pending = new Map();
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  };
  const send = (method, params = {}) => new Promise(ok => {
    const mid = ++id; pending.set(mid, ok);
    ws.send(JSON.stringify({ id: mid, method, params }));
  });
  return { ws, send, targetId: tab.id };
}

async function clickAll(send, clickSel, clickWait) {
  const wait = clickWait == null ? 700 : clickWait;
  for (const sel of String(clickSel || '').split(',')) {
    if (!sel.trim()) continue;
    await send('Runtime.evaluate', {
      expression: `document.querySelector(${JSON.stringify(sel.trim())})?.click()` });
    // 700ms 是"过渡动画跑完"的经验值；点了会发请求再重绘的按钮（记分、扫描）要另给余量，
    // 否则截到的是"重绘前/后"的随机一侧 —— P5 实测 review_graded 因此两次差 637 像素。
    await sleep(wait);
  }
}

/** 等页面进入稳定态：readyState complete + 再等 settle 毫秒（默认 3500，与旧单张模式一致）。 */
async function settle(send, ms) {
  for (let i = 0; i < 40; i++) {
    const r = await send('Runtime.evaluate',
      { expression: 'document.readyState', returnByValue: true });
    if (r.result?.result?.value === 'complete') break;
    await sleep(250);
  }
  await sleep(ms);
}

/**
 * 一个截图任务的完整流程。
 * 有 init 时不能"先开页再注入"——那已经晚了，所以先开 about:blank、注册注入、再 navigate。
 */
async function shoot(job) {
  const w = job.w || 1440, h = job.h || 900;
  const { ws, send, targetId } = await openTab(job.init ? 'about:blank' : job.url);
  try {
    await send('Page.enable');
    if (job.init) {
      await send('Page.addScriptToEvaluateOnNewDocument', { source: job.init });
      await send('Page.navigate', { url: job.url });
    }
    await send('Emulation.setDeviceMetricsOverride',
      { width: +w, height: +h, deviceScaleFactor: 1, mobile: false });
    await settle(send, job.settle == null ? 3500 : job.settle);
    await clickAll(send, job.click, job.clickWait);
    const shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.mkdirSync(path.dirname(job.out), { recursive: true });
    fs.writeFileSync(job.out, Buffer.from(shot.result.data, 'base64'));
    console.log('OK', job.out);
  } finally {
    ws.close();
    try { await fetch(`${CDP}/json/close/${targetId}`); } catch {}
  }
}

try {
  await waitPort();
  if (BATCH) {
    const manifest = JSON.parse(fs.readFileSync(arg2, 'utf8'));
    let bad = 0;
    for (const job of manifest.shots || []) {
      try {
        await shoot(job);
      } catch (e) {
        bad += 1;
        console.error(`FAIL ${job.out}: ${e.message}`);
      }
    }
    console.log(`BATCH DONE: ${(manifest.shots || []).length - bad}/${(manifest.shots || []).length} 张成功`);
    if (bad) process.exitCode = 1;
  } else {
    const [, , url, out, w = '1440', h = '900', clickSel = ''] = process.argv;
    await shoot({ url, out, w: +w, h: +h, click: clickSel });
  }
} catch (e) {
  console.error('FAIL', e.message);
  process.exitCode = 1;
} finally {
  proc.kill();
  try { fs.rmSync(profile, { recursive: true, force: true }); } catch {}
}
