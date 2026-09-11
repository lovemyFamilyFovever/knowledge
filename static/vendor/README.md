# static/vendor/ · 本地化第三方依赖（T0 落地）

知识库前端重构引入的全部第三方库与字体均下载到本地；页面代码中不出现任何 `http(s)://` 外链，与仓库根 `AGENTS.md` 不变量一致（零外部 API / 零 CDN、语料不出网）。

## 清单

| 文件 | 大小 | 来源 | 版本 | 许可 |
|---|---|---|---|---|
| `gsap.min.js` | 72 KB | `https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/gsap.min.js` | 3.13.0 | Webflow GSAP License（免费商用，本地内嵌允许） |
| `ScrollTrigger.min.js` | 44 KB | `https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/ScrollTrigger.min.js` | 3.13.0 | 同上（GSAP 官方插件自 3.13 起并入标准许可） |
| `space-grotesk-var.woff2` | 22 KB | `https://cdn.jsdelivr.net/npm/@fontsource-variable/space-grotesk@5.1.1/files/space-grotesk-latin-wght-normal.woff2` | 5.1.1 (variable) | SIL Open Font License 1.1 |

## 重下载

若需刷新或补文件（在仓库根执行）：

```sh
curl -sSfLo static/vendor/gsap.min.js \
  https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/gsap.min.js

curl -sSfLo static/vendor/ScrollTrigger.min.js \
  https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/ScrollTrigger.min.js

curl -sSfLo static/vendor/space-grotesk-var.woff2 \
  https://cdn.jsdelivr.net/npm/@fontsource-variable/space-grotesk@5.1.1/files/space-grotesk-latin-wght-normal.woff2
```

## 备注

- **GSAP 商用许可**：Webflow Standard License 允许在自研产品中本地内嵌使用；保留本 README 作为许可出处凭证。
- **字体子集**：Latin 可变字重（300–700）约 22 KB，CJK 走系统 serif（Georgia + 中文回退），与仓库现状一致。
- **升级策略**：小版本内自由更新；大版本（GSAP 3 → 4）需先回归全部 `data-*` 动效挂载点（`static/motion.js`）。
