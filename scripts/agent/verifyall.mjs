// 零依赖 CDP 全状态验证。node verifyall.mjs <url>
import { spawn } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';

const [, , url] = process.argv;
const CHROME = ['C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe']
  .find(p => { try { return fs.existsSync(p); } catch { return false; } });
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'kbv-'));
const proc = spawn(CHROME, ['--headless=new', '--remote-debugging-port=9335',
  `--user-data-dir=${profile}`, '--no-first-run', 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));

try {
  for (let i = 0; i < 30; i++) { try { const r = await fetch('http://127.0.0.1:9335/json/version'); if (r.ok) break; } catch {} await sleep(300); }
  const tab = await (await fetch('http://127.0.0.1:9335/json/new?' + encodeURIComponent(url), { method: 'PUT' })).json();
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((ok, err) => { ws.onopen = ok; ws.onerror = err; });
  let id = 0; const pend = new Map();
  ws.onmessage = ev => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } };
  const send = (method, params = {}) => new Promise(ok => { const i = ++id; pend.set(i, ok); ws.send(JSON.stringify({ id: i, method, params })); });
  await send('Page.enable'); await send('Runtime.enable');
  await sleep(4000);
  const evl = async (expression) => (await send('Runtime.evaluate', { expression, returnByValue: true })).result?.result?.value;

  /* ---- 阶段1：pretty 视图 ---- */
  const s1 = await evl(`JSON.stringify({
    crumbPathGone: !document.querySelector('#crumb .path'),
    mdSrcBtn: !!document.getElementById('kb-md-src-btn'),
    finishBarAtBottom: (() => { const w = document.querySelector('.html-frame-wrap'); const b = document.getElementById('kb-finish-bar');
      return w && b ? (w.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) > 0 : null })(),
    iframeW: Math.round(document.querySelector('.html-frame')?.getBoundingClientRect().width || 0),
    injected: (() => { try { return document.querySelector('.html-frame').contentDocument.head.innerHTML.includes('max-width:100%'); } catch (e) { return 'err:' + e.message.slice(0, 30); } })()
  })`);
  console.log('PRETTY :', s1);

  /* ---- 阶段2：切 Markdown 源 ---- */
  await evl(`document.getElementById('kb-md-src-btn').click(); 'ok'`);
  await sleep(600);
  const s2 = await evl(`JSON.stringify({
    mdView: !!document.querySelector('.a-body'),
    artMaxW: getComputedStyle(document.getElementById('article')).maxWidth,
    artW: Math.round(document.getElementById('article').getBoundingClientRect().width),
    bodyW: Math.round(document.querySelector('.a-body')?.getBoundingClientRect().width || 0),
    finishBarAtBottom: (() => { const b = document.querySelector('.a-body'); const fb = document.getElementById('kb-finish-bar');
      return b && fb ? (b.compareDocumentPosition(fb) & Node.DOCUMENT_POSITION_FOLLOWING) > 0 : null })(),
    measureVar: getComputedStyle(document.documentElement).getPropertyValue('--kb-measure').trim()
  })`);
  console.log('MD     :', s2);
  ws.close();
} catch (e) { console.error('FAIL', e.message); process.exitCode = 1; }
finally { proc.kill(); try { fs.rmSync(profile, { recursive: true, force: true }); } catch {} }
