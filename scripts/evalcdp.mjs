// 零依赖 CDP evaluate：node evalcdp.mjs <url> <jsExpr>
//   <jsExpr> 以 `@` 开头时按文件路径读取（性质测试的载荷太长，塞不进 argv）
//   env KB_EVAL_WAIT_MS  等页面加载的时间（默认 4000）
//   env KB_EVAL_OUT_CHARS EVAL 输出截断长度（默认 1500）
import { spawn, spawnSync } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';
import net from 'net';
import { waitQuiet } from './quiesce.mjs';   // 稳定态判定：与 shot.mjs / geom.mjs 共用一份

const [, , url, argExpr] = process.argv;
// 载荷太长塞不进 Windows 的 argv（性质测试要把畸形样本带进页面）：
// 以 `@` 开头时按文件读取表达式，其余按字面量处理。
const expr = argExpr && argExpr.startsWith('@') ? fs.readFileSync(argExpr.slice(1), 'utf8') : argExpr;
const PORT_PREF = +(process.env.KB_EVAL_PORT || 9334);
const PORT = await pickPort(PORT_PREF);
if (PORT !== PORT_PREF) console.error(`[evalcdp] 首选调试端口 ${PORT_PREF} 被别的进程占着（多半是上一轮没退干净的 Chrome），已改用 ${PORT} —— 绝不连陌生浏览器`);
const CDP = `http://127.0.0.1:${PORT}`;
const WAIT = Number(process.env.KB_EVAL_WAIT_MS || 4000);
const OUT = Number(process.env.KB_EVAL_OUT_CHARS || 1500);
const CHROME = ['C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe']
  .find(p => { try { return fs.existsSync(p); } catch { return false; } });
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'kbeval-'));
const proc = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${profile}`, '--no-first-run', 'about:blank'], { stdio: 'ignore' });
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

const errors = [];
try {
  for (let i = 0; i < 30; i++) { try { const r = await fetch(`${CDP}/json/version`); if (r.ok) break; } catch {} await sleep(300); }
  // 先开 about:blank、挂好监听、再 navigate —— 原来直接 /json/new?<url>，
  // 于是"页面加载完了没有"根本没有信号，只能靠 `sleep(WAIT)` 硬等（js_props 传 6000ms × 4 次）。
  // 改成等 **Page.loadEventFired**（主信号）+ DOM 静默（收尾），WAIT 降级成上限。
  // 顺序错了就会拿到**导航之前**的那个空文档：readyState 一上来就是 complete，
  // 于是求值跑在 app.js 之前、每个样本都返回 {} —— 轮次 35 实测就是这样红了 22 条。
  const tab = await (await fetch(`${CDP}/json/new?about:blank`, { method: 'PUT' })).json();
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((ok, err) => { ws.onopen = ok; ws.onerror = err; });
  let id = 0; const pend = new Map();
  let onLoaded = null;
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); return; }
    if (m.method === 'Page.loadEventFired' && onLoaded) { const f = onLoaded; onLoaded = null; f(); }
    if (m.method === 'Runtime.consoleAPICalled' && (m.params.type === 'error' || m.params.type === 'warning')) {
      errors.push(m.params.args.map(a => a.value ?? a.description ?? '').join(' ').slice(0, 300));
    }
    if (m.method === 'Runtime.exceptionThrown') {
      errors.push('EXC: ' + (m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text || '').slice(0, 400));
    }
  };
  const send = (method, params = {}) => new Promise(ok => { const i = ++id; pend.set(i, ok); ws.send(JSON.stringify({ id: i, method, params })); });
  await send('Page.enable'); await send('Runtime.enable');
  const loadP = new Promise(ok => { onLoaded = ok; });
  await send('Page.navigate', { url });
  await Promise.race([loadP, sleep(WAIT)]);      // load 事件为准，WAIT 只是上限
  // 再等页面静默（字体就绪 + DOM 连续 320ms 无变化）。
  // 在途 fetch 计数器要注册在 document-start 才准，这里没地方挂 ——
  // 计数器缺席时 quiesceJs 按 0 处理，判定只剩"字体 + DOM"，对静态阅读器页面够用。
  for (let i = 0; i < 60; i++) {
    const rs = await send('Runtime.evaluate', { expression: 'document.readyState', returnByValue: true });
    if (rs.result?.result?.value === 'complete') break;
    await sleep(200);
  }
  await waitQuiet(send, WAIT, { tail: 250 });
  const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
  console.log('EVAL:', JSON.stringify(r.result?.result?.value ?? r.result, null, 1).slice(0, OUT));
  console.log('CONSOLE_ERRORS:', errors.length ? '\n  ' + errors.slice(0, 5).join('\n  ') : 'none');
  ws.close();
} catch (e) { console.error('FAIL', e.message); process.exitCode = 1; }
finally { killChrome(proc); await rmProfile(profile); }
