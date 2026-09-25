// 零依赖 CDP 多视口几何探针：node geom.mjs <url> <w1,w2,...> <expr@文件>
// 每档宽度输出一行 JSON（表达式的返回值），供测试侧断言"两块矩形不许相交"这类
// 只有几何才能锁的回归（例：顶栏绝对居中的搜索框在 1281~1796 压住导航，台账 §14.3 第 1 条）。
// 与 shot.mjs 的区别：shot 出像素，本脚本出矩形；两者共用同一套 CDP 骨架与稳定性 flag。
import { spawn } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';

const PORT = +(process.env.KB_GEOM_PORT || 9338);
const CDP = `http://127.0.0.1:${PORT}`;
const [, , url, argW, argExpr] = process.argv;
if (!url || !argExpr) {
  console.error('usage: node geom.mjs <url> <w1,w2,...> <expr@file|inline>');
  process.exit(2);
}
const WIDTHS = (argW || '1440').split(',').map(Number);
const expr = argExpr.startsWith('@') ? fs.readFileSync(argExpr.slice(1), 'utf8') : argExpr;

const CHROME_CANDIDATES = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  path.join(process.env.LOCALAPPDATA || '', 'Google/Chrome/Application/chrome.exe'),
].filter(Boolean);
const chrome = CHROME_CANDIDATES.find(p => { try { return fs.existsSync(p); } catch { return false; } });
if (!chrome) { console.error('chrome not found'); process.exit(3); }

const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'kbgeom-'));
const proc = spawn(chrome, [`--user-data-dir=${profile}`, '--headless=new',
  `--remote-debugging-port=${PORT}`, '--no-first-run', '--disable-gpu',
  '--force-color-profile=srgb', '--font-render-hinting=none', '--disable-lcd-text',
  'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function openTab(u) {
  const tab = await (await fetch(`${CDP}/json/new?${encodeURIComponent(u)}`, { method: 'PUT' })).json();
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((ok, err) => { ws.onopen = ok; ws.onerror = err; });
  let id = 0;
  const pending = new Map();
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  };
  const send = (method, params = {}) => new Promise(ok => {
    const mid = ++id; pending.set(mid, ok); ws.send(JSON.stringify({ id: mid, method, params }));
  });
  return { ws, send, targetId: tab.id };
}

try {
  for (let i = 0; i < 40; i++) {
    try { const r = await fetch(`${CDP}/json/version`); if (r.ok) break; } catch {}
    await sleep(300);
  }
  const { ws, send, targetId } = await openTab('about:blank');
  try {
    await send('Page.enable');
    await send('Page.navigate', { url });
    for (let i = 0; i < 40; i++) {
      const r = await send('Runtime.evaluate', { expression: 'document.readyState', returnByValue: true });
      if (r.result?.result?.value === 'complete') break;
      await sleep(200);
    }
    await sleep(2500);   // 字体/动效落定，和 shot.mjs 的 settle 同源经验值
    for (const w of WIDTHS) {
      await send('Emulation.setDeviceMetricsOverride',
        { width: w, height: 900, deviceScaleFactor: 1, mobile: false });
      await sleep(600);  // 断点切换后重排
      const out = await send('Runtime.evaluate', { expression: expr, returnByValue: true });
      if (out.result?.result?.value === undefined) {
        console.log(JSON.stringify({ vw: w, error: (out.exceptionDetails?.exception?.description || 'undefined').slice(0, 200) }));
      } else {
        console.log(out.result.result.value);
      }
    }
  } finally {
    ws.close();
    try { await fetch(`${CDP}/json/close/${targetId}`); } catch {}
  }
} catch (e) {
  console.error('FAIL', e.message);
  process.exitCode = 1;
} finally {
  proc.kill();
  try { fs.rmSync(profile, { recursive: true, force: true }); } catch {}
}
