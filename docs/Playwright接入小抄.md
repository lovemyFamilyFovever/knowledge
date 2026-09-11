# Playwright 接入小抄（照做就行）

目标：让我能把 `localhost:5001` 的任意页面/弹窗**截图成 PNG**，再用 Read 工具真的"看见"渲染结果，从此不再靠算 CSS 猜。
环境已确认：node v24.19.0、npm 12.0.2、mcp.json 在 `E:\GitHub\knowledge\.qoder-cn\mcp.json`。

---

## 路线 A（推荐）：本地 CLI，我直接驱动

在 `E:\GitHub\knowledge` 下依次执行（PowerShell 或 Git-Bash 都行）：

```bash
mkdir .dev-tools
cd .dev-tools
npm init -y
npm i playwright
npx playwright install chromium
```

- 最后一步会下载 Chromium（约 120–170MB，一次性）。
- `.dev-tools/` 需要加进 `.gitignore`（见下），别污染仓库。

加进 `.gitignore`（仓库根）：
```
.dev-tools/
```

装完后，把下面这段存成 `E:\GitHub\knowledge\.dev-tools\shot.js`（我也可以帮你建）：

```js
// 用法: node shot.js <url> <out.png> [--full] [--click <css选择器>]...
const { chromium } = require('playwright');
const [,, url, out, ...rest] = process.argv;
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1440, height: 900 } });
  const errs = [];
  p.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()); });
  p.on('pageerror', e => errs.push('pageerror: ' + e.message));
  try { await p.goto(url, { waitUntil: 'networkidle' }); } catch (e) { errs.push('goto: ' + e.message); }
  for (let i = 0; i < rest.length; i++) {
    if (rest[i] === '--click') { const sel = rest[++i]; try { await p.click(sel); await p.waitForTimeout(500); } catch (e) { errs.push('click ' + sel + ': ' + e.message); } }
  }
  await p.screenshot({ path: out, fullPage: rest.includes('--full') });
  console.log(errs.length ? 'ERRORS:\n' + errs.join('\n') : 'OK no console/page errors');
  await b.close();
})();
```

验证装好没：
```bash
cd .dev-tools
node shot.js http://127.0.0.1:5001/home /tmp/home.png --full
```
若打印 `OK no console/page errors` 且生成 `/tmp/home.png`，就成了。之后我截图统计弹窗：
```bash
node shot.js http://127.0.0.1:5001/home /tmp/stats.png --click "#global-stats-btn"
```
（前提：你的 :5001 是重启过、带 `/api/globalstats` 的那个进程。）

---

## 路线 B（可选）：加成 MCP，做交互式操作

编辑 `E:\GitHub\knowledge\.qoder-cn\mcp.json`，在 `mcpServers` 里加一段（保留原 codebase-memory）：

```json
{
  "mcpServers": {
    "codebase-memory": {
      "command": "C:\\Users\\Administrator\\AppData\\Local\\codebase-memory-mcp\\win\\codebase-memory-mcp.exe",
      "args": []
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```

- 存盘后**重启千问办公**才会加载新 MCP。
- 首次调用 `@playwright/mcp` 时它自己会拉起浏览器；若报缺浏览器，先跑一次路线 A 的 `npx playwright install chromium`。
- 优点：我能"打开→点→悬停→截图→读 console"交互式操作；缺点：依赖千问办公对自定义 stdio MCP 的支持，不如路线 A 稳。

---

## 建议顺序
1. 先做**路线 A**（最稳，我马上能用）。
2. 有闲再补**路线 B**（交互更强）。

## 顺带（可选，第二/三优先，见 docs/工具能力清单.md）
- 让 Flask 开发热重载：`app/app.py` 末尾 `app.run(..., debug=False)` 加个 `--dev` 开关走 `debug=True`，省你反复重启。
- 静态检查：`.dev-tools` 里 `npm i -D eslint stylelint` + `pip install ruff pyright`。
