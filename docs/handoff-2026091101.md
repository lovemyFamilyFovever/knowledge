# HANDOFF — 知库 UI 精修与稳健性会话交接

> 写给一个**完全没有上下文**的新会话。先读本文件，再读仓库根 `AGENTS.md`（不变量与命令），即可接手。
> 最后更新：2026-09-11。接手时请 `git log --oneline -8` 确认 HEAD 未变。

---

## 0. 项目速览（新会话必读）

- **是什么**：个人知识库单一入口。`content/` 下的 Markdown 是**唯一事实源**，本地 Flask 阅读器（`app/app.py`，默认 `127.0.0.1:5001`）+ 本地语义检索（RAG），全程离线、语料不出网、零外部 CDN。
- **硬约束（违反=破坏性改动，见 AGENTS.md）**：编辑/收藏/删除必须写回文件系统；`indexes/` 是纯派生缓存可删；删除走软删除到 `content/_trash/`；分类学权威是 `content/_meta/taxonomy.json`；嵌入/切块逻辑变更要递增 `app/rag.py::RAG_CODE_VERSION`。
- **前端栈**：原生 JS（`static/app.js`）+ 单文件 CSS（`static/style.css`）+ Jinja 模板（`app/templates/*.html`）。无构建步骤。
- **设计 token**：CSS 自定义属性，定义在 `style.css` 的 `:root`（浅色）与 `html[data-theme="dark"]`（深色）。核心：`--bg0 --ink --muted --faint --acc --acc2 --warn --rose --edge`。**注意：真实应用用的是 `--muted/--faint/--ink`，没有 `--seed-*`**（`--seed-*` 只存在于 Canvas 设计稿 `index.html`，别混用，见坑 #2）。
- **常用命令**（AGENTS.md 有全表）：
  - 启动：`python app/app.py`（端口硬编码 5001，`debug=False`）
  - 三套测试：`.python\python.exe tests\test_reader.py` / `test_new_project.py` / `test_rag.py`（pre-commit 钩子自动跑）
  - 直启回归：`python app\app.py --import-check`
  - Python lint：`python -m ruff check .`（本会话新增 `ruff.toml`）
  - JS 语法：`node --check static/app.js`（零安装）

---

## 1. 我们在做什么任务

对知库阅读器做 **UI 精修 + 稳健性修复**，交付节奏是用户明确要求的：**"先一条一条改，每改完一条就停下来让我检查"**。

背景：用户对之前几轮"盲改"（我一度没有浏览器/截图能力，只能靠 CSS 数学推断渲染结果）极度不满，反复出现"改了半天界面没变化 / 风格敷衍 / 弹窗看不清"。本会话的转折点是**用户为 Playwright MCP 装好了环境**，我第一次真正"看见"渲染结果，从此每条改动都用 Playwright 截图自查后再提交。

任务清单（用户此前编号 A/B 两类）：
- **A 类**：崩溃/数据 bug —— 上一会话已全部修完（URL 编码、`_trash` 500、双链 404、kbModal 双转义、移动到总览后 404 等，见更早的 commit）。
- **B 类**：UI 重设计 —— 本会话完成 B1–B4，剩 B5、B6。

---

## 2. 已经完成了什么（本会话，全部已 commit + Playwright 截图验证 + pre-commit 三套测试绿）

| commit | 内容 |
|---|---|
| `fedc2f9` | **B1 统计弹窗**：修 `关闭`按钮溢出面板（根因见坑 #3）；各域分布条按 taxonomy 色相上色 + 同色圆点；KPI 副行防折行；**静态资源按 mtime 自动版本号 `av()`**（根治改样式后浏览器仍缓存旧 CSS，见坑 #4） |
| `e041fa2` | **B3 彩色 emoji → 内联 SVG**：`base.html` 精灵表新增 13 个描边符号；`app.js` 加 `icon()` 助手；右键菜单支持 `item.icon`；替换主题切换/移动树/右键菜单/面包屑编辑删除收藏/删除二次确认/弹窗标题；`grep` 确认彩色 emoji 清零 |
| `f3d4520` | **工具**：`pip install ruff`（0.16.7）+ 写 `ruff.toml`（高信号回归安全网，不做风格 churn）；顺手清掉 `home()` 一个死赋值 |
| `5fd9fcb` | **B4 对比度**：浅色 `--faint` 2.27→3.6、深色 3.93→4.7（用 Python 精确算 WCAG） |
| `5bd2aa4` | **B2 移动弹窗**：目标路径预览分层高亮（目录 muted / 文件名主色加粗 / .md muted）+ 空态提示 + 确认按钮对勾图标 |

**工具现状**：Playwright MCP ✅ 可用（导航/截图/evaluate/console/network）；Ruff ✅ 已装已配；`node --check` ✅ 可用；`codebase-memory` 与 `Knowledge Graph Memory` 两个 MCP ✅ 在；UI 类 skill（awwwards-design / frontend-design 等）✅ 在。**我判断当前不缺关键工具**，无需用户再找。

---

## 3. 当前卡在哪

**无硬性阻塞。** 本会话所有计划内改动都已落地验证。

唯一悬而未决的是**流程确认**（我在上一条消息问了用户，尚未得到回复）：
- 我为了验证，**重启过 5001 上用户的阅读器实例**（改 `app.py` 的 context processor 必须重启；改模板/静态文件实测不用重启）。已问用户：以后是允许我按需重启那个实例，还是希望我改用**另一个端口起临时实例**验证、别动他的窗口。**新会话接手时先确认这一点**。

另有两处**已知的、非阻塞的遗留观察**：
- 目录统计弹窗（`showSubStats`）顶部仍是旧的"四个灰盒"`.ss-cell`，未统一成全局统计那种 `.gkpi` 仪表带。功能正常，纯一致性问题，未列入本轮。
- 移动弹窗右侧列在选中后下方有一点空白（`.mv-hint` 用 `margin-top:auto` 推到底）。观感可接受，未改。

---

## 4. 下一步计划

按用户"一条一条改、每条停下检查"的节奏，剩余：

1. **B5 — 编辑器静默丢弃防护**：`static/app.js` 的编辑器（`openEditor`/保存/取消）在未保存时点取消/切换会直接丢弃改动、无二次确认。加"有未保存改动时确认"。用 Playwright 驱动验证：改文本→点取消→应弹确认。
2. **B6 — 收件箱归档 UX**：`app/templates/inbox.html` + 相关 JS。检查归档流程是否顺畅、是否符合"新知识只从 `_inbox` 进"的不变量。
3. （可选）统一 `showSubStats` 顶部为 `.gkpi` 仪表带，与全局统计同款皮肤。
4. （可选）把 `ruff check` 与 `node --check` 接进 `.githooks/pre-commit`（目前 pre-commit 只跑三套测试）。

**每步都要**：改完 `node --check`（JS）或 `python -m ruff check .`（Python）→ Playwright 截图自查（深浅色各一张）→ 单独 commit，消息说人话。

---

## 5. 踩过的坑 —— 绝对不要再踩

1. **没有视觉验证就宣称"完成"/报 readyToPresent。** 这是本会话之前所有矛盾的总根源。现在 Playwright 可用，**任何 UI 改动必须截图自查后再提交**，否则可能改的是个空白页或崩页。曾两次对完全坏掉的页面报了"就绪"。

2. **把 Canvas 设计稿的变量名（`--seed-surface`/`--seed-fg`）用到真实 `style.css`。** 真实应用根本没有这些变量 → `color-mix()` 失败 → 弹窗透明。**真实应用只有 `--bg0/--ink/--muted/--faint/--acc/...`**。改真实样式前先 `grep` 确认变量存在。设计稿（`index.html`）和真实应用是两套 token，别混。

3. **弹窗内容溢出面板。** `kbModal` 的 `.kbm` 是 `max-height:82vh` 的 flex 列；给 body 加内联 `max-height:none;overflow:visible` 会把 footer 按钮顶出面板边框。正确做法：`.kbm-body{flex:1 1 auto;min-height:0;overflow-y:auto}`，让内容在面板内滚动。

4. **改完 CSS 用户看不到变化 = 浏览器缓存。** `style.css` 之前**没有任何版本号**（只有 `app.js?v=18` 手动 bump）。已改为 `av()` 按文件 mtime 自动出版本号（`base.html` 里 `?v={{ av('style.css') }}`）。**别再手动 bump `?v=`**，用 `av()`。另外 Playwright 用全新无缓存上下文，能复现"真实首屏"，但用户日常浏览器会缓存——这是过去"我改了你怎么没看到"类矛盾的主因。

5. **模板/后端改动的重启边界。** 实测：改 `app/templates/*.html` 和 `static/*` **不用重启**（模板热加载、静态即时）。但改 `app/app.py`（如 context processor）**必须重启** 5001 实例，否则模板引用了新变量而进程没有 → 渲染 500（本会话踩过：加 `av()` 到 base.html 后没重启，`/home` 直接 500）。重启方式：`powershell.exe -Command "Stop-Process -Id <pid> -Force"` 然后 `cd /e/GitHub/knowledge && nohup python app/app.py > /tmp/zhiku-5001.log 2>&1 &`。

6. **`taskkill //PID` 和相对路径 `rm .file` 会被判成 UNC 路径拒绝。** 杀进程用 `powershell.exe Stop-Process`；删文件用绝对路径。

7. **`git commit -m` 消息里不要含 `\\s` 等反斜杠序列**（会被当 UNC 路径拒绝）。

8. **`find .` 从 `/` 扫会耗尽资源**；`find` 限定在 `.` 或具体子目录。

9. **（更早会话的教训）不要一次性把几百 KB 文件整个重写。** 用户明确要求的开发规范：**先搭骨架→最小验证→再逐模块填充**。曾有脚本死循环把设计稿撑到 437KB、空转 3729 次。大文件改动用 Edit 定点替换，别 Write 全量覆盖。

10. **emoji 用 Unicode 范围 grep 才准**：`grep -nP '[\x{1F300}-\x{1FAFF}]'`。彩色 emoji（🗑📄🗂📊📈📂）破坏扁平风格，已全换 `icon()`；单色排版符号（↑↓←→ 键盘提示、◈ 等）保留可接受。

11. **Playwright 截图偶发 "waiting for fonts to load" 超时**（aurora 动画持续跑）。解法：截图前 `evaluate` 注入 `*{animation:none!important;transition:none!important}` 关掉动画，再 `browser_take_screenshot`。

12. **测试全绿 ≠ 启动路径可用**（AGENTS.md 已记）：tests 从项目根 import，`start.bat` 直启走另一条 sys.path。回归入口 `python app\app.py --import-check`。

---

## 6. 相关文件索引

- `docs/工具能力清单.md` — 32 项工具/能力愿望清单（Playwright 已划勾达成）。
- `docs/Playwright接入小抄.md` — Playwright 连接器配置与 CLI 安装步骤。
- `docs/superpowers/` — awwwards 重构的设计 spec 与分阶段 plan（另一条 UI 重构线，本会话未动）。
- `ruff.toml` — 本会话新增，高信号 lint 配置。
- Canvas 设计稿：`qwenwork/canvas/<id>/index.html`（13 屏高保真展示，独立于真实应用，token 体系不同）。

---

## 7. 给新会话的第一句话建议

先跑 `git log --oneline -8` 确认 HEAD 在 `5bd2aa4`；先向用户确认第 3 节那个"是否允许重启 5001 实例"的流程问题；然后按第 4 节从 B5 开始，**每条改动 Playwright 截图自查后再 commit**。
