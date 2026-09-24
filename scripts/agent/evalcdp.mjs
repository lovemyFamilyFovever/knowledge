// 零依赖 CDP evaluate：node evalcdp.mjs <url> <jsExpr>
//   <jsExpr> 以 `@` 开头时按文件路径读取（性质测试的载荷太长，塞不进 argv）
//   env KB_EVAL_WAIT_MS  等页面加载的时间（默认 4000）
//   env KB_EVAL_OUT_CHARS EVAL 输出截断长度（默认 1500）
import { spawn } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';

const [, , url, argExpr] = process.argv;
// 载荷太长塞不进 Windows 的 argv（性质测试要把畸形样本带进页面）：
// 以 `@` 开头时按文件读取表达式，其余按字面量处理。
const expr = argExpr && argExpr.startsWith('@') ? fs.readFileSync(argExpr.slice(1), 'utf8') : argExpr;
const WAIT = Number(process.env.KB_EVAL_WAIT_MS || 4000);
const OUT = Number(process.env.KB_EVAL_OUT_CHARS || 1500);
const CHROME = ['C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe']
  .find(p => { try { return fs.existsSync(p); } catch { return false; } });
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'kbeval-'));
const proc = spawn(CHROME, ['--headless=new', '--remote-debugging-port=9334',
  `--user-data-dir=${profile}`, '--no-first-run', 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));

const errors = [];
try {
  for (let i = 0; i < 30; i++) { try { const r = await fetch('http://127.0.0.1:9334/json/version'); if (r.ok) break; } catch {} await sleep(300); }
  const tab = await (await fetch('http://127.0.0.1:9334/json/new?' + encodeURIComponent(url), { method: 'PUT' })).json();
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((ok, err) => { ws.onopen = ok; ws.onerror = err; });
  let id = 0; const pend = new Map();
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); return; }
    if (m.method === 'Runtime.consoleAPICalled' && (m.params.type === 'error' || m.params.type === 'warning')) {
      errors.push(m.params.args.map(a => a.value ?? a.description ?? '').join(' ').slice(0, 300));
    }
    if (m.method === 'Runtime.exceptionThrown') {
      errors.push('EXC: ' + (m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text || '').slice(0, 400));
    }
  };
  const send = (method, params = {}) => new Promise(ok => { const i = ++id; pend.set(i, ok); ws.send(JSON.stringify({ id: i, method, params })); });
  await send('Page.enable'); await send('Runtime.enable');
  await sleep(WAIT);
  const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
  console.log('EVAL:', JSON.stringify(r.result?.result?.value ?? r.result, null, 1).slice(0, OUT));
  console.log('CONSOLE_ERRORS:', errors.length ? '\n  ' + errors.slice(0, 5).join('\n  ') : 'none');
  ws.close();
} catch (e) { console.error('FAIL', e.message); process.exitCode = 1; }
finally { proc.kill(); try { fs.rmSync(profile, { recursive: true, force: true }); } catch {} }
