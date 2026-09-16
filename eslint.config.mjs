// ESLint 9 flat config —— 回归安全网（抓崩溃/错误，不当风格警察）
// 与 ruff.toml 同一定位：no-redeclare / no-undef / no-unused-vars 这类真问题。
// 运行：npm run lint:js
import js from "@eslint/js";
import globals from "globals";

export default [
  {
    ignores: [
      "node_modules/**",
      "indexes/**",
      "content/**",
      ".python/**",
      "static/vendor/**",        // 第三方 vendored 库（mermaid/echarts/marked...）不检
      "**/*.min.js",
      "app/rag_models/**",
      "qwenwork/**",
      ".qoder-cn/**",
      ".cowork-temp/**",
    ],
  },
  js.configs.recommended,
  {
    files: ["static/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "script",       // 现有 JS 均为经典脚本（无 import/export）
      globals: {
        ...globals.browser,
        ...globals.es2022,
        // ---- 跨脚本共享全局（script 标签加载顺序约定）----
        // kb-core.js 定义，页面脚本使用：
        KB: "readonly",
        kbModal: "writable",   // app.js 定义；个别页面有本地同名 shim，允许遮蔽
        toast: "writable",
        esc: "writable",
        invalidate: "writable",
        util: "readonly",
        // app.js 定义的文档态全局（页面脚本读取当前文档元数据）：
        DOC: "writable",
        // Story 1/2：编辑器桥接层与双链补全的跨脚本全局
        // KBCM = vendor/codemirror.bundle.js 暴露；KBED = pages/cm-editor.js 暴露
        KBCM: "readonly",
        KBED: "readonly",
        // base.html / vendor 库暴露：
        DOMPurify: "readonly",
        marked: "readonly",
        hljs: "readonly",
        HUES: "readonly",
        mermaid: "readonly",
        echarts: "readonly",
        // 知识库模板注入：
        TAXONOMY: "readonly",
      },
    },
    rules: {
      // ---- 本次踩过坑的高信号规则 ----
      "no-redeclare": "error",           // const $$ 写成 const $ 的重复声明
      "no-undef": "error",               // 未定义变量
      "no-unused-vars": ["warn", { args: "none", varsIgnorePattern: "^(kb|util)$" }],
      "no-self-assign": "error",
      "no-unreachable": "error",
      "no-dupe-keys": "error",
      "no-dupe-args": "error",
      "no-constant-condition": ["error", { checkLoops: "allExceptWhileTrue" }],
      "no-empty": ["error", { allowEmptyCatch: true }],   // 空 catch 常见于"可选增强失败即忽略"，但保留告警可搜
      "no-regex-spaces": "warn",
      "no-useless-escape": "warn",
      "valid-typeof": "error",
      // 风格类一律关闭：不做风格警察
      "no-console": "off",
      "semi": "off",
      "quotes": "off",
    },
  },

  {
    // app.js 是 esc/toast/kbModal/invalidate 等跨脚本全局的"定义者"文件，
    // globals 里声明了它们，故定义处本身需豁免 no-redeclare。
    files: ["static/app.js"],
    rules: {
      "no-redeclare": "off",
    },
  },
];
