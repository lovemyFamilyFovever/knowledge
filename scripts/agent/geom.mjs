// 零依赖 CDP 多视口几何探针：node geom.mjs <url> <w1,w2,...> <expr@文件>
// 每档宽度输出一行 JSON（表达式的返回值），供测试侧断言"两块矩形不许相交"这类
// 只有几何才能锁的回归（例：顶栏绝对居中的搜索框在 1281~1796 压住导航，台账 §14.3 第 1 条）。
// 与 shot.mjs 的区别：shot 出像素，本脚本出矩形；两者共用同一套 CDP 骨架与稳定性 flag。
import { spawn, spawnSync } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';
import net from 'net';

const PORT_PREF = +(process.env.KB_GEOM_PORT || 9338);
const PORT = await pickPort(PORT_PREF);
if (PORT !== PORT_PREF) console.error(`[geom] 首选调试端口 ${PORT_PREF} 被别的进程占着（多半是上一轮没退干净的 Chrome），已改用 ${PORT} —— 绝不连陌生浏览器`);
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
    // 可选的"页面任何脚本之前先注入"：env KB_GEOM_INIT（JS 源码）。
    // 与 shot.mjs 的 init 同源（Page.addScriptToEvaluateOnNewDocument），
    // 用来把 localStorage 偏好钉成确定态 —— 例如验"刷新后偏好仍然生效"。
    const initSrc = process.env.KB_GEOM_INIT || '';
    if (initSrc) {
      await send('Page.addScriptToEvaluateOnNewDocument', { source: initSrc });
    }
    await send('Page.navigate', { url });
    for (let i = 0; i < 40; i++) {
      const r = await send('Runtime.evaluate', { expression: 'document.readyState', returnByValue: true });
      if (r.result?.result?.value === 'complete') break;
      await sleep(200);
    }
    await sleep(2500);   // 字体/动效落定，和 shot.mjs 的 settle 同源经验值
    // 可选的"先点一下再量"：env KB_GEOM_CLICK=CSS 选择器（逗号分隔可多点），
    // KB_GEOM_CLICK_WAIT=每次点击后的毫秒数（默认 1500）。
    // 点击引发整页导航时也没问题：这里等的是 readyState 而不是 Promise 结果，
    // 求值发生在**导航之后**的新文档里 —— 所以"点了到底换没换页"能直接断出来。
    const clickSel = process.env.KB_GEOM_CLICK || '';
    if (clickSel) {
      for (const sel of clickSel.split(',')) {
        if (!sel.trim()) continue;
        await send('Runtime.evaluate', {
          expression: `document.querySelector(${JSON.stringify(sel.trim())})?.click()` });
        await sleep(+(process.env.KB_GEOM_CLICK_WAIT || 1500));
        for (let i = 0; i < 60; i++) {
          const r = await send('Runtime.evaluate',
            { expression: 'document.readyState', returnByValue: true });
          if (r.result?.result?.value === 'complete') break;
          await sleep(200);
        }
      }
      await sleep(1200);
    }
    for (const w of WIDTHS) {
      await send('Emulation.setDeviceMetricsOverride',
        { width: w, height: 900, deviceScaleFactor: 1, mobile: false });
      await sleep(600);  // 断点切换后重排
      const out = await send('Runtime.evaluate',
        { expression: expr, returnByValue: true, awaitPromise: true });
      // 求值失败要能看见：**promise reject 时 Chrome 把 Error 对象原样回传**，
      // returnByValue 反序列化后是 `{}`（Error 的 message/stack 不是可枚举自有属性）——
      // 只看 value === undefined 会把"表达式抛了"和"返回了空对象"混成同一种输出，
      // 测试侧拿到 {} 时完全无从下手（2026-09-25 轮次 28 在这上面耗过一轮）。
      const ex = out.exceptionDetails;
      const isRejected = out.result?.result?.subtype === 'error';
      if (ex || isRejected) {
        const desc = ex?.exception?.description || ex?.text || 'rejected';
        console.log(JSON.stringify({ vw: w, error: desc.slice(0, 400) }));
      } else if (out.result?.result?.value === undefined) {
        console.log(JSON.stringify({ vw: w, error: 'undefined' }));
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
  killChrome(proc);
  await rmProfile(profile);
}
