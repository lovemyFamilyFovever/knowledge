// 零依赖 CDP 截图。
//   单张：node shot.mjs <url> <outfile> [w] [h] [clickSel]
//   批量：node shot.mjs --batch <manifest.json>      （彻查 P5 · 视觉回归批处理用）
// 批量清单形如 {"shots":[{"url","out","w","h","click","init","settle"}]}：
//   一个 Chrome、多个标签页依次截，省掉"每张重启浏览器"的 5 秒；
//   init = 在页面任何脚本之前注入的 JS（`Page.addScriptToEvaluateOnNewDocument`），
//   用来把 localStorage 偏好钉成确定态（主题、动效、阅读宽度），否则截出来的图每次不一样。
import { spawn, spawnSync } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';
import net from 'net';
import { PENDING_HOOK, waitQuiet } from './quiesce.mjs';   // 稳定态判定与 geom.mjs 共用一份

const PORT_PREF = +(process.env.KB_SHOT_PORT || 9333);
const PORT = await pickPort(PORT_PREF);
if (PORT !== PORT_PREF) console.error(`[shot] 首选调试端口 ${PORT_PREF} 被别的进程占着（多半是上一轮没退干净的 Chrome），已改用 ${PORT} —— 绝不连陌生浏览器`);
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
// —— 探针专用：端口与进程收尾（轮次 31 之后加的，别删）——————————————————————————
// ① 固定调试端口意味着：上一轮没退干净的 Chrome 还在听这个端口时，本轮的 /json/new
//    会**连到那个陌生浏览器**里 —— 里面是别的页面，而且是后台标签页
//    （rAF / IntersectionObserver 被节流），于是探针拿到 `{}` 或读到陈旧状态。
//    2026-09-25 pre-commit 的假红就是这个（本机实测泄漏 2 个 kbshot-* 无头实例）。
//    所以先探端口空不空，被占就改要一个临时端口：spawn 之前端口是空的，
//    回答我们的浏览器就一定是我们自己起的那个。
// ② Windows 下 `proc.kill()` 只杀父进程，Chrome 主进程活着继续占端口与 profile
//    → 用 taskkill /T /F 杀整棵进程树；profile 目录随之要多试几次才删得掉。
async function pickPort(pref) {
  const free = p => new Promise(res => {
    const s = net.createServer();
    s.once('error', () => res(false));
    s.once('listening', () => s.close(() => res(true)));
    s.listen(p, '127.0.0.1');
  });
  if (await free(pref)) return pref;
  return new Promise((res, rej) => {
    const s = net.createServer();
    s.once('error', rej);
    s.once('listening', () => { const p = s.address().port; s.close(() => res(p)); });
    s.listen(0, '127.0.0.1');
  });
}
function killChrome(p) {
  if (!p || p.pid == null) return;
  if (process.platform === 'win32') {
    try { spawnSync('taskkill', ['/pid', String(p.pid), '/T', '/F'], { stdio: 'ignore' }); } catch {}
    return;
  }
  try { p.kill(); } catch {}
}
async function rmProfile(dir) {
  for (let i = 0; i < 6; i++) {
    try { fs.rmSync(dir, { recursive: true, force: true }); return; } catch { await sleep(120); }
  }
}

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

/* 稳定态判定与在途请求计数都在 quiesce.mjs（与 geom.mjs 共用一份，别抄第二份）。
   这里只保留"上限"策略：清单里声明的 settle / clickWait 变成**最多等这么久**，
   页面先静默就提前走 —— P5 的 init 钉住 `kb-force-motion=0`（rAF 动画整体不跑），
   所以"DOM 静默 + 无在途请求"是可测的强信号，不必再靠固定睡眠。
   证据：`--stability` 两次截图逐像素相同 + 22 张对**既有基线** AE ≤ 2。 */
async function clickAll(send, clickSel, clickWait) {
  const cap = clickWait == null ? 700 : clickWait;
  for (const sel of String(clickSel || '').split(',')) {
    if (!sel.trim()) continue;
    await send('Runtime.evaluate', {
      expression: `document.querySelector(${JSON.stringify(sel.trim())})?.click()` });
    // 点了会发请求再重绘的按钮（记分、扫描）以前要固定给 2.5~8s 余量，
    // 否则截到的是"重绘前/后"的随机一侧 —— P5 实测 review_graded 因此两次差 637 像素。
    // 现在改成"等它真的重绘完"（在途 fetch 归零 + DOM 静默），上限就是原来那个数。
    await waitQuiet(send, cap, { tail: 120 });
  }
}

/** 等页面进入稳定态：readyState complete + 静默判定（上限 = 清单声明的 settle）。 */
async function settle(send, ms) {
  for (let i = 0; i < 40; i++) {
    const r = await send('Runtime.evaluate',
      { expression: 'document.readyState', returnByValue: true });
    if (r.result?.result?.value === 'complete') break;
    await sleep(250);
  }
  await waitQuiet(send, ms == null ? 3500 : ms, { tail: 200 });
}

/**
 * 一个截图任务的完整流程。
 * 有 init 时不能"先开页再注入"——那已经晚了，所以先开 about:blank、注册注入、再 navigate。
 */
async function shoot(job) {
  const w = job.w || 1440, h = job.h || 900;
  /* 一律先开 about:blank、注册注入、再 navigate —— 因为"在途请求计数器"必须在页面任何脚本
     之前挂上（先开页再注入已经晚了），而 P5 每张都带 init，两条路径正好统一成一条。 */
  const { ws, send, targetId } = await openTab('about:blank');
  try {
    await send('Page.enable');
    /* 钩子拼在调用方 init **之后**：document-start 脚本按注册顺序执行，
       桩先替换 fetch、计数器再包一层，这样连"被桩短路掉的请求"也会被正确计数。 */
    await send('Page.addScriptToEvaluateOnNewDocument',
      { source: (job.init || '') + '\n' + PENDING_HOOK });
    await send('Page.navigate', { url: job.url });
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
  killChrome(proc);
  await rmProfile(profile);
}
