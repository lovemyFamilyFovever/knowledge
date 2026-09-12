// stylelint —— 回归安全网（只抓真问题，不做格式警察）
// 运行：npm run lint:css
/** @type {import('stylelint').Config} */
export default {
  ignoreFiles: ["node_modules/**", "static/vendor/**", "**/*.min.css", "indexes/**", "content/**"],
  rules: {
    // ---- 真问题 ----
    "no-duplicate-selectors": true,                    // 重复选择器（.empty / :root 多处重复定义）
    "declaration-block-no-duplicate-properties": [true, { ignoreProperties: ["var"] }],
    "block-no-empty": true,
    "no-invalid-position-at-import-rule": true,
    "function-no-unknown": null,                       // 自定义函数/工具函数放行
  },
};
