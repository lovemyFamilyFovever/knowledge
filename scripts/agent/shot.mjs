// 零依赖 CDP 截图：node shot.mjs <url> <outfile> [w] [h]
import { spawn } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';

const [, , url, out, w = '1440', h = '900', clickSel = ''] = process.argv;
if (!url || !out) { console.error('usage: node shot.mjs <url> <out> [w] [h]'); process.exit(2); }

const CHROME_CANDIDATES = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  path.join(process.env.LOCALAPPDATA || '', 'Google/Chrome/Application/chrome.exe'),
].filter(Boolean);
const chrome = CHROME_CANDIDATES.find(p => { try { return fs.existsSync(p); } catch { return false; } });
if (!chrome) { console.error('chrome not found'); process.exit(3); }

const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'kbshot-'));
const proc = spawn(chrome, [
  '--headless=new', '--remote-debugging-port=9333',
  `--user-data-dir=${profile}`, '--no-first-run', '--disable-gpu', 'about:blank',
], { stdio: 'ignore' });

const sleep = ms => new Promise(r => setTimeout(r, ms));
const waitPort = async () => {
  for (let i = 0; i < 30; i++) {
    try { const r = await fetch('http://127.0.0.1:9333/json/version'); if (r.ok) return; } catch {}
    await sleep(300);
  }
  throw new Error('CDP port not ready');
};

try {
  await waitPort();
  const res = await fetch('http://127.0.0.1:9333/json/new?' + encodeURIComponent(url), { method: 'PUT' });
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

  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride',
    { width: +w, height: +h, deviceScaleFactor: 1, mobile: false });
  await sleep(3500); // 等 JS/字体/动画
  if (clickSel) {
    // 支持逗号分隔的连续点击（如「先开抽屉再切页签」），每步间隔 700ms 等过渡
    for (const sel of String(clickSel).split(',')) {
      if (!sel.trim()) continue;
      await send('Runtime.evaluate', { expression: `document.querySelector(${JSON.stringify(sel.trim())})?.click()` });
      await sleep(700);
    }
  }
  const shot = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(out, Buffer.from(shot.result.data, 'base64'));
  console.log('OK', out);
  ws.close();
} catch (e) {
  console.error('FAIL', e.message);
  process.exitCode = 1;
} finally {
  proc.kill();
  try { fs.rmSync(profile, { recursive: true, force: true }); } catch {}
}
