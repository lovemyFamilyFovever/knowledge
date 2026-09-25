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
// —— 会话模式（轮次 33 加）———————————————————————————————————————————————
// `node geom.mjs --session` 起一台 Chrome 后**常驻**：从 stdin 逐行读作业、逐行回一行 JSON。
// 为什么要有这一档：一次调用一台浏览器意味着每次付 3~4s 冷启动 + 建/删 profile + 2.5s settle，
// 第 13 套 40 多次求值里大半时间花在这上面（实测见台账 §7）。
// 复用带来的语义差别必须补齐：一趟新 profile ≈ 干净的 localStorage/cookie，
// 所以**每个作业开始前清一次 origin 存储 + cookies**，否则上一趟写进 localStorage 的偏好会串到下一趟
// （那不是"快一点"，那是假绿）。init 也按作业逐个注册/注销，不共享。
const SESSION = process.argv[2] === '--session';
const [url, argW, argExpr] = process.argv.slice(SESSION ? 3 : 2);
if (!SESSION && (!url || !argExpr)) {
  console.error('usage: node geom.mjs <url> <w1,w2,...> <expr@file|inline>');
  console.error('       node geom.mjs --session        # 常驻：stdin 逐行读作业，stdout 逐行回 JSON');
  process.exit(2);
}
const WIDTHS = (argW || '1440').split(',').map(Number);
const expr = !argExpr ? '' : (argExpr.startsWith('@') ? fs.readFileSync(argExpr.slice(1), 'utf8') : argExpr);

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

/* 会话模式的一个作业：{id,url,expr,width,settle,click,click_wait,init,fresh}
   → stdout 回一行 {id,value} 或 {id,error}。错误分类与一次一档完全相同（抛异常 / 返回 undefined
   必须分辨得开，见轮次 28 那段注释）。 */
async function runJob(send, job) {
  /* 每个 CDP 调用都带超时：会话档是"一台浏览器跑完整套"，任何一个方法不回复就会把后面
     所有探针一起拖死（实测：一次挂住 = 白等 300s，门禁整挂）。宁可红一条也要说清卡在哪个方法。 */
  const TRACE = !!process.env.KB_GEOM_TRACE;
  const call = async (method, params = {}, ms = 15000) => {
    let t;
    if (TRACE) process.stderr.write(`[job ${job.id}] -> ${method}\n`);
    const guard = new Promise((_, rej) => { t = setTimeout(() => rej(new Error(`CDP timeout: ${method}`)), ms); });
    try {
      const r = await Promise.race([send(method, params), guard]);
      if (r && r.error) throw new Error(`${method} -> ${r.error.message || JSON.stringify(r.error)}`);
      if (TRACE) process.stderr.write(`[job ${job.id}] <- ${method} ok\n`);
      return r;
    } catch (e) {
      if (TRACE) process.stderr.write(`[job ${job.id}] !! ${method} ${e.message}\n`);
      throw e;
    } finally {
      clearTimeout(t);
    }
  };
  let initIdentifier = null;
  try {
    if (job.init) {
      const r = await call('Page.addScriptToEvaluateOnNewDocument', { source: job.init });
      initIdentifier = r?.result?.identifier || null;
    }
    /* 清存储 = 补上"每趟新 profile"的隔离语义。漏这一步，上一趟写进 localStorage 的偏好
       会串到这一趟，测出来的"默认态"其实是脏的 —— 那是假绿，不是提速。 */
    if (job.fresh !== false) {
      try { await call('Network.clearBrowserCookies', {}, 5000); } catch { /* 非关键 */ }
      try {
        await call('Storage.clearDataForOrigin',
          { origin: new URL(job.url).origin, storageTypes: 'all' }, 5000);
      } catch { /* 拿不到该域时至少 cookies 清了 */ }
    }
    await call('Page.navigate', { url: job.url });
    for (let i = 0; i < 80; i++) {
      const r = await call('Runtime.evaluate', { expression: 'document.readyState', returnByValue: true }, 8000);
      if (r.result?.result?.value === 'complete') break;
      await sleep(100);
    }
    /* settle 比一次一档的 2500ms 小：字体/CSS/JS 在这台浏览器里已经热过一轮。
       探针该等的东西由探针自己轮询（本套判据是"等到为止"，不是"等够为止"）。 */
    await sleep(job.settle == null ? 900 : job.settle);
    if (job.click) {
      for (const sel of String(job.click).split(',')) {
        if (!sel.trim()) continue;
        await call('Runtime.evaluate', {
          expression: `document.querySelector(${JSON.stringify(sel.trim())})?.click()` });
        await sleep(+(job.click_wait || 1500));
        for (let i = 0; i < 60; i++) {
          const r = await call('Runtime.evaluate',
            { expression: 'document.readyState', returnByValue: true }, 8000);
          if (r.result?.result?.value === 'complete') break;
          await sleep(150);
        }
      }
      await sleep(job.click_settle == null ? 600 : job.click_settle);
    }
    await call('Emulation.setDeviceMetricsOverride', {
      width: job.width || 1440, height: job.height || 900,
      deviceScaleFactor: 1, mobile: false
    });
    await sleep(job.reflow == null ? 350 : job.reflow);
    const out = await call('Runtime.evaluate',
      { expression: job.expr, returnByValue: true, awaitPromise: true }, job.timeout || 120000);
    const ex = out.exceptionDetails;
    const isRejected = out.result?.result?.subtype === 'error';
    if (ex || isRejected) {
      const detail = { text: ex?.text, class: ex?.className,
                       desc: (ex?.exception?.description || ex?.exception?.value || '').toString().slice(0, 200),
                       sub: out.result?.result?.subtype };
      return { error: ('' + (ex?.exception?.description || ex?.text || 'rejected')).slice(0, 400),
               detail: JSON.stringify(detail) };
    }
    const v = out.result?.result?.value;
    return v === undefined ? { error: 'undefined' } : { value: v };
  } finally {
    if (initIdentifier) {
      try { await send('Page.removeScriptToEvaluateOnNewDocument', { identifier: initIdentifier }); } catch { /* 已随文档失效 */ }
    }
  }
}

async function runSession() {
  /* readline 必须**第一件事**就建：实测 Python 若在 Node 接管管道之前就把作业写进 stdin，
     那几个字节会被丢掉、这一条作业永远没有回复（轮次 33 排查：延后 4s 写就正常）。
     光靠"早点建接口"还不够保险，所以下面额外发一行 ready 握手，客户端等到它才准写。 */
  const rl = (await import('readline')).createInterface({ input: process.stdin, crlfDelay: Infinity });
  process.stdin.resume();
  for (let i = 0; i < 60; i++) {
    try { const r = await fetch(`${CDP}/json/version`); if (r.ok) break; } catch { }
    await sleep(250);
  }
  const { ws, send, targetId } = await openTab('about:blank');
  await send('Page.enable');
  await send('Network.enable');
  process.stdout.write(JSON.stringify({ session: 'ready', port: PORT }) + '\n');
  for await (const line of rl) {
    if (!line.trim()) continue;
    let job;
    try { job = JSON.parse(line); } catch (e) {
      process.stdout.write(JSON.stringify({ id: null, error: 'bad job json: ' + e.message }) + '\n');
      continue;
    }
    const t0 = Date.now();
    let res;
    try { res = await runJob(send, job); } catch (e) { res = { error: String(e?.message || e) }; }
    process.stdout.write(JSON.stringify({
      id: job.id, ms: Date.now() - t0, value: res.value, error: res.error, detail: res.detail
    }) + '\n');
  }
  ws.close();
  try { await fetch(`${CDP}/json/close/${targetId}`); } catch { }
}

if (SESSION) {
  try {
    await runSession();
  } catch (e) {
    console.error('SESSION FAIL', e.message);
    process.exitCode = 1;
  } finally {
    killChrome(proc);
    await rmProfile(profile);
  }
  process.exit(process.exitCode || 0);
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
