/* 稳定态判定（shot.mjs / geom.mjs 共用，轮次 33 从 shot.mjs 里抽出来——别抄第二份）。
 *
 * 背景：两个工具原来都是"睡够固定毫秒"（shot 的 settle 3500/6500 + clickWait 2500~8000，
 * geom 的 settle 2500 + reflow 600 + clickWait 1500）。P5 的 22 张因此要 165s、
 * 第 13 套的 45 次要 484s，而真正的求值是毫秒级。
 *
 * 改成"测出来"而不是"等出来"：
 *   readyState complete → 字体就绪 → **在途 fetch 归零** → DOM 连续 quietMs 没有任何变化
 * 调用方原来声明的毫秒数保留当**上限**：测不到静默就退回睡法，不会比原来差。
 *
 * 两条必须一起成立的性质：
 * 1) 计数器要包住**所有** fetch，包括探针自己打的桩 —— 所以 PENDING_HOOK 必须拼在
 *    调用方 init **之后**（document-start 脚本按注册顺序执行：桩先替换 window.fetch，
 *    钩子再包一层，桩的提前 return 也会被计数并归还；反了就会永远非零 → 每次打满上限）。
 * 2) 只有画面真的静止才谈得上逐像素可比 —— P5 的 init 钉 `kb-force-motion=0`（rAF 动画整体不跑），
 *    所以"DOM 静默"是强信号。判据成立的证据是 P5 自己两把尺子：
 *    `--stability`（同一份代码两次截图逐像素相同）与 22 张对基线 AE ≤ 2。
 */

export const PENDING_HOOK = "window.__kbPending=window.__kbPending||0;" +
  "(function(){if(window.__kbPendingHooked)return;window.__kbPendingHooked=1;" +
  "var f=window.fetch;window.fetch=function(){window.__kbPending++;" +
  "return f.apply(this,arguments).then(function(r){window.__kbPending--;return r;}," +
  "function(e){window.__kbPending--;throw e;});};})();";

/** 生成一段 awaitPromise 用的表达式：等到静默（或到 capMs 上限）为止。 */
export function quiesceJs(quietMs, capMs) {
  const quiet = Number(quietMs) || 320;
  const cap = Number(capMs) || 3500;
  return `(async () => {
  const t0 = performance.now();
  try { if (document.fonts && document.fonts.ready) await document.fonts.ready; } catch (e) {}
  await new Promise((res) => {
    let last = performance.now();
    const mo = new MutationObserver(() => { last = performance.now(); });
    mo.observe(document.documentElement, { subtree: true, childList: true, attributes: true, characterData: true });
    const tick = () => {
      const still = performance.now() - last >= ${quiet};
      const idle = (window.__kbPending || 0) === 0;
      if ((still && idle) || performance.now() - t0 > ${cap}) { mo.disconnect(); res(); }
      else { setTimeout(tick, 40); }
    };
    setTimeout(tick, ${quiet});
  });
  return 1;
})()`;
}

/** 一次 CDP 求值：等页面静默（上限 capMs）后再留一点落盘余量。 */
export async function waitQuiet(send, capMs, { quiet = 320, tail = 150 } = {}) {
  await send('Runtime.evaluate',
    { expression: quiesceJs(quiet, capMs), awaitPromise: true, returnByValue: true });
  if (tail) await new Promise(r => setTimeout(r, tail));
}
