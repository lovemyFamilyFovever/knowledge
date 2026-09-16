import { EditorState } from "@codemirror/state";
import { EditorView, keymap, lineNumbers, highlightActiveLine,
         highlightActiveLineGutter, drawSelection, rectangularSelection } from "@codemirror/view";
import { defaultKeymap, history, historyKeymap, indentWithTab } from "@codemirror/commands";
import { markdown } from "@codemirror/lang-markdown";
import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { tags } from "@lezer/highlight";

// 主题继承项目 CSS 变量（--c-panel/--c-ink/--c-line/--f-mono），
// 明暗主题由 html[data-theme] 驱动，编辑器自动跟随，无需另造 token。
const theme = EditorView.theme({
  "&": {
    fontSize: "14.5px", flex: "1", minHeight: "0",
    backgroundColor: "transparent", color: "var(--c-ink)",
    fontFamily: "var(--f-mono)",
  },
  ".cm-scroller": {
    fontFamily: "var(--f-mono)", lineHeight: "1.75",
    padding: "10px 14px 40px",
  },
  ".cm-content": { caretColor: "var(--c-acc)", padding: "0" },
  ".cm-gutters": {
    backgroundColor: "transparent", color: "var(--c-line2)",
    border: "none", borderRight: "1px solid var(--c-line)",
    paddingRight: "8px", fontSize: "12px",
  },
  ".cm-activeLineGutter": { backgroundColor: "transparent", color: "var(--c-acc)" },
  ".cm-activeLine": { backgroundColor: "color-mix(in oklab, var(--c-acc), transparent 94%)" },
  ".cm-cursor, .cm-dropCursor": { borderLeftColor: "var(--c-acc)", borderLeftWidth: "2px" },
  "&.cm-focused .cm-selectionBackground, .cm-selectionBackground": {
    backgroundColor: "color-mix(in oklab, var(--c-acc), transparent 78%) !important",
  },
  ".cm-selectionMatch": {
    backgroundColor: "color-mix(in oklab, var(--hex-mark), transparent 65%)",
  },
}, { dark: false });

const hl = HighlightStyle.define([
  { tag: tags.heading1, fontSize: "1.45em", fontWeight: "700", color: "var(--c-ink)" },
  { tag: tags.heading2, fontSize: "1.25em", fontWeight: "700", color: "var(--c-ink)" },
  { tag: tags.heading3, fontSize: "1.12em", fontWeight: "600", color: "var(--c-ink)" },
  { tag: [tags.heading4, tags.heading5, tags.heading6], fontWeight: "600", color: "var(--c-ink)" },
  { tag: tags.strong, fontWeight: "700" },
  { tag: tags.emphasis, fontStyle: "italic" },
  { tag: tags.strikethrough, textDecoration: "line-through" },
  { tag: tags.link, color: "var(--c-acc)", textDecoration: "underline" },
  { tag: tags.url, color: "var(--c-info)" },
  { tag: tags.monospace, color: "var(--c-info)", fontFamily: "var(--f-mono)" },
  { tag: tags.quote, color: "var(--c-line2)", fontStyle: "italic" },
  { tag: tags.meta, color: "var(--c-line2)" },
  { tag: tags.contentSeparator, color: "var(--c-line2)", fontWeight: "700" },
  { tag: tags.processingInstruction, color: "var(--c-line2)" },
  { tag: tags.content, color: "var(--c-ink)" },
  { tag: tags.list, color: "var(--c-acc)" },
]);

/** 归一到 LF：与 textarea.value / app.js saveDoc 安全网同源的换行契约。 */
const toLF = (s) => String(s == null ? "" : s).replace(/\r\n?/g, "\n");

/**
 * 创建编辑器视图。
 * 契约：文档文本永远 LF —— 服务端 write_text 再按平台翻译 CRLF。
 * 提交含 \r 的文本会被二次翻译成 \r\r\n 污染语料
 * （tests/test_reader.py「编辑器桥接层文本不含裸 CR」护栏守这条）。
 */
function create(parent, doc, opts) {
  opts = opts || {};
  return new EditorView({
    parent,
    state: EditorState.create({
      doc: toLF(doc),
      extensions: [
        lineNumbers(), highlightActiveLineGutter(),
        history(), drawSelection(), rectangularSelection(),
        EditorView.lineWrapping,
        highlightActiveLine(),
        keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]),
        markdown(),
        syntaxHighlighting(hl),
        theme,
        EditorView.updateListener.of((u) => { if (opts.onUpdate) opts.onUpdate(u); }),
        EditorView.domEventHandlers({
          keydown: (e) => (opts.onKeydown ? !!opts.onKeydown(e) : false),
          scroll: () => { if (opts.onScroll) opts.onScroll(); },
          blur: () => { if (opts.onBlur) opts.onBlur(); },
        }),
      ],
    }),
  });
}

window.KBCM = { EditorState, EditorView, create, toLF };
