/* =====================================================================
   知库 · CodeMirror 6 编辑器桥接层（Story 2）
   设计契约（不破不立）：
     · textarea#ed-text 仍是「值的事实源」——app.js 的 openEditor / saveDoc /
       ED_SNAPSHOT dirty guard / tryCloseEditor 全部照旧读写 ta.value，一行不改。
     · CodeMirror 只是「可见输入载体」：onUpdate 时实时把 doc 同步回 ta.value，
       所以 app.js 任何时候读 ta.value 都拿到最新正文。
     · 换行契约：视图文本永远 LF（KBCM.toLF / bundle lineSeparator），
       服务端 write_text 再翻译 CRLF。tests/test_reader.py 有 LF-only 护栏。
   集成点（app.js 显式调用，不赌时序）：
     · openEditor 末尾 → KBED.attach()
     · closeEditor 末尾 → KBED.detach()
   [[ 双链补全（wikilink-suggest.js）通过 window.KBED.view 拿到 CM 实例，
   走 CM 分支（coordsAtPos 定位 + dispatch 插入）；CM 未就绪时回落 textarea 分支。
   ===================================================================== */
(function () {
  "use strict";
  var $ = function (s, p) { return (p || document).querySelector(s); };

  var ta = null;       // textarea#ed-text（值事实源，隐藏但保留）
  var host = null;     // .cm-host（CM 挂载容器）
  var view = null;     // CodeMirror EditorView
  var syncing = false; // 防 onUpdate 与 dispatch 灌值互相触发的重入闸

  /* 事件 fan-out：CM 视图创建时 extensions 固定，外部模块（如双链补全）无法事后
     挂钩，故这里做注册表，把 CM 的 update / keydown / blur / 开关态广播给订阅者。
     · docListeners(u)     : CM update 对象（docChanged 或 selectionSet 时触发）
     · keyListeners(e)     : 返回 true 表示已消费该按键（阻止 CM 默认行为）
     · blurListeners()     : 编辑器失焦
     · stateListeners(on)  : true=attach 完成 / false=detach 完成 */
  var docListeners = [], keyListeners = [], blurListeners = [], stateListeners = [];
  function fanout(fns, arg) {
    for (var i = 0; i < fns.length; i++) {
      try { fns[i](arg); } catch (e) { /* 单个订阅者出错不阻断其余 */ }
    }
  }
  /* keydown 专用：任一订阅者返回 true 即视为已消费 */
  function fanoutKey(e) {
    for (var i = 0; i < keyListeners.length; i++) {
      try { if (keyListeners[i](e)) return true; } catch (err) { /* 同上 */ }
    }
    return false;
  }

  function ensureHost() {
    if (host) return host;
    host = document.createElement("div");
    host.className = "cm-host";
    host.style.display = "none";
    // 插到 textarea 之后，同属 .editor flex column
    if (ta && ta.parentNode) ta.parentNode.insertBefore(host, ta.nextSibling);
    return host;
  }

  /* CM 内容 → ta.value（实时，保证 saveDoc/dirty guard 读到最新） */
  function syncToTextarea() {
    if (!view || !ta || syncing) return;
    ta.value = view.state.doc.toString();
  }

  function onUpdate(u) {
    if (u.docChanged) syncToTextarea();
    // 广播给补全等订阅者：docChanged（输入触发）与 selectionSet（光标移动需关下拉）。
    // syncing（灌值）期间不广播——loadIntoCM 的整文替换不是用户输入。
    if (!syncing && (u.docChanged || u.selectionSet)) fanout(docListeners, u);
  }

  /* 补全键（↑↓/Enter/Tab/Esc）：走 bundle 的高优先级 completion keymap，
     在 CM 默认 Enter/Tab 之前拦截——否则默认 Enter 会先插换行、docChanged
     让补全下拉自行关闭（实测坑）。返回 true = 已消费，CM 不执行默认行为。 */
  function onCompletionKey(e) { return fanoutKey(e); }

  /* CM 普通键盘：只兜 Ctrl/Cmd+S 保存（textarea 隐藏后原生 onkeydown 不再触发）。
     补全键已由 onCompletionKey 高优先级 keymap 处理，这里不再 fanout 避免双重消费。 */
  function onKeydown(e) {
    if ((e.ctrlKey || e.metaKey) && (e.key === "s" || e.key === "S")) {
      e.preventDefault();
      if (typeof window.saveDoc === "function") window.saveDoc();
      return true;
    }
    return false; // 交回 CM 默认处理
  }

  function onBlur() { fanout(blurListeners); }

  /* 把外部文本灌进 CM（openEditor 设完 ta.value 后调用） */
  function loadIntoCM(text) {
    var lf = window.KBCM ? KBCM.toLF(text) : String(text || "").replace(/\r\n?/g, "\n");
    syncing = true;
    try {
      if (!view) {
        view = KBCM.create(ensureHost(), lf,
          { onUpdate: onUpdate, onKeydown: onKeydown, onBlur: onBlur,
            onCompletionKey: onCompletionKey });
      } else {
        view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: lf } });
      }
    } finally {
      syncing = false;
    }
    ta.value = lf; // 灌值后对齐事实源（幂等，值相同）
  }

  function attach() {
    ta = $("#ed-text");
    if (!ta || !window.KBCM) return; // CM bundle 未加载则静默回落裸 textarea
    loadIntoCM(ta.value);
    ta.classList.add("cm-hidden");
    ensureHost().style.display = "";
    fanout(stateListeners, true); // 通知补全：切到 CM 模式
    // 等一帧让 flex 布局稳定后 focus + measure，避免首屏光标错位
    requestAnimationFrame(function () {
      try { view.focus(); } catch (e) {}
    });
  }

  function detach() {
    if (view) syncToTextarea(); // 关闭前把 CM 最终内容落回 ta.value
    if (host) host.style.display = "none";
    if (ta) ta.classList.remove("cm-hidden");
    fanout(stateListeners, false); // 通知补全：CM 已收起，回 textarea 模式
  }

  /* 供 wikilink-suggest.js 消费：CM 实例 + 便捷操作 + 事件订阅 */
  window.KBED = {
    get view() { return view; },
    get textarea() { return ta || $("#ed-text"); },
    /* CM 是否已接管输入（true 时补全走 CM 分支，false 走 textarea 分支） */
    active: function () { return !!(view && host && host.style.display !== "none"); },
    attach: attach,
    detach: detach,
    /* 订阅 CM 事件：doc(u) / key(e)->bool / blur() / state(on) */
    on: function (type, fn) {
      if (type === "doc") docListeners.push(fn);
      else if (type === "key") keyListeners.push(fn);
      else if (type === "blur") blurListeners.push(fn);
      else if (type === "state") stateListeners.push(fn);
    },
    /* 补全插入用：把 [from,to) 替换为 text，光标落在末尾 */
    replaceRange: function (from, to, text) {
      if (!view) return false;
      view.dispatch({
        changes: { from: from, to: to, insert: text },
        selection: { anchor: from + text.length },
        scrollIntoView: true,
      });
      syncToTextarea();
      return true;
    },
    /* 光标前文本（补全触发检测用） */
    textBeforeCursor: function () {
      if (!view) return "";
      var sel = view.state.selection.main;
      return view.state.doc.sliceString(0, sel.from);
    },
    cursorPos: function () { return view ? view.state.selection.main : null; },
  };

  // textarea 可能在 CM bundle 之后才可用；attach 由 app.js 显式调用，这里不自动跑。
})();
