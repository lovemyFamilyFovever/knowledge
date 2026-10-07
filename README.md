# 知库 Knowledge

个人知识库单一入口：博客、百科、面试、职业、agent 记忆等语料全部以 **Markdown 文件为唯一事实源**，本仓库提供本地阅读器（Flask）、本地语义检索（RAG），以及一份**已上线的 GitHub Pages 静态只读档**。全部离线，语料不出网。

线上只读档：<https://lovemyfamilyfovever.github.io/knowledge/>
本地阅读器：<http://127.0.0.1:5001>

## 布局

```
content/            语料本体（唯一不可再生资产）
  <domain>/<sub>/*.md   两层 taxonomy：域 × 子域 × 文档（权威定义 content/_meta/taxonomy.json）
  *.html                整页美化版旁挂文件（与同名 .md 共存，阅读页 iframe 内嵌直通渲染）
  _inbox/               暂存区：一切新材料的唯一入口，归档后才入 taxonomy（不入库、不进树）
  _assets/              附件
  _trash/               软删除回收站（不入库；删除一律走这里）
  _meta/taxonomy.json   分类学权威（域/子域/来源/状态/色相），改分类先改它
indexes/            派生缓存（FTS index.db / 向量 rag.db / 阅读统计 reading.db）
                    启动时按 mtime 自动重建，可随时删；删了阅读统计归零
site/               公网只读档的导出产物（派生缓存，同样可随时删，已 gitignore）
app/                Flask 阅读器与全部端点
app/fts.py          FTS5 全文索引 + [[双链]]解析
app/rag.py          本地语义检索（切块 → ONNX 嵌入 → sqlite-vec）
app/reading.py      阅读统计（事件制：open / read_minute / finish 只追加）
static/             前端（经典脚本，无构建工具）
static/kb-static.js 只读适配器：只在导出产物里加载，把同一套前端改成公网只读档
scripts/            迁移与维护脚本（scripts/agent/ 是跨会话常驻工具）
tests/              15 套自执行测试（无 pytest，`python tests/test_x.py`）
docs/               当前设计规格与交接
测试文件/覆盖台账.md  覆盖率台账（§0 数字由 check_ledger_counts.py 对账，已进门禁）
```

## 启动

```sh
start.bat           # 唯一启动入口（自动探测 .python\ 便携运行时或系统 Python）
start.bat --dev     # 开发模式（py / 模板改动自动热重载）
python app\app.py   # 直启（项目根会自动补进 sys.path，不依赖 cwd）
```

端口 5001 被占用时脚本会提示直接打开浏览器，不会闪退。写作层用 Obsidian 打开 `content/` 作为 vault，与本应用共享同一份语料。

## 功能速览

- **三栏工作台** `/`：左树（域 → 子域 → 文档，逐层原地展开）、中正文、右栏（目录 / 标签 / 备注 / 双链）。打开任意一篇文档时左树自动展开并聚焦到它所在的层级。
- **检索**：搜索框直接输入走 FTS5（命中高亮），`?` 前缀走语义模式（按意思找）。结果页 `/search` 支持域 / 子域 / 标签分面多选与清空；就地检索浮层 `/` 唤出。
- **收件箱** `/inbox`：新内容丢进 `content/_inbox/` → 逐篇或批量归档（级联更新 FTS / 双链 / 向量索引），或丢弃；「彻底删除」只允许作用于收件箱文件。
- **写回文件系统**：编辑（`Ctrl/Cmd+S`）、收藏、备注（sidecar `.notes.md`）、标签 chips、移动 / 重命名 / 软删除 —— 全部落盘，不引入第二真相。
- **双链**：编辑器输入 `[[` 联想已有词条；未解析链接在正文底部列成可点条目；右栏「双链」看反向链。
- **阅读统计** `/stats`：KPI + 环比上月 + 每日条形图 + 文档榜（60s 心跳埋点，数据在 `indexes/reading.db`）。顶栏「全库快照」看总量 / 各域分布 / 标签覆盖 / 双链健康。
- **命令面板** `Ctrl/Cmd+K`：文档 + 子域 + 命令，输入即模糊匹配。
- **阅读偏好**：界面风格（皮肤 / 主题）、字号、行宽、字体、行高、标题与代码样式，设置抽屉内改，存 localStorage。
- **键盘导航**：`j`/`k` 上下篇、`/` 聚焦搜索、`Esc` 分层关闭、`?` 快捷键帮助、`Menu`/`Shift+F10` 打开右键菜单。
- **响应式**：手机 / 平板单栏阅读，面板可收起，触控区 ≥44px。

## 公网只读档

同一套前端 + 只读适配器，不复制第二份界面：

```sh
MSYS_NO_PATHCONV=1 py -3 scripts\export_static.py --out site --base /knowledge
```

导出器把公开白名单语料经 `create_app().test_client()` 跑一遍读端点，把应答逐字段落盘成静态 JSON（同构由构造保证），并注入 `window.KB_STATIC`。推 main 后 `.github/workflows/pages.yml` 自动导出并部署到本仓 Pages。

只读档与本地的差别：写请求一律回 `READ_ONLY`；统计 / 收藏 / 收件箱入口、编辑与删除按钮、拖拽移动、动态写菜单项、依赖本地库的模块全部不出现；状态栏与标题换成公网口径；根路径是首页那一屏（只留「搜索」与「继续上次阅读」）。阅读进度与最近阅读存在访客自己的浏览器里，换设备不同步。

公开面硬边界（永不进产物）见 `.gitignore` 与 `scripts/export_static.py` 的 `EXCLUDE_DIRS`。

## 语义检索（RAG）

本地向量检索：切块（标题路径继承）→ bge-small-zh-v1.5 嵌入（ONNX，CPU）→ sqlite-vec 近邻检索。`indexes/rag.db` 是派生缓存，启动与后台 30s 增量同步；切块 / 分词 / 嵌入逻辑变更必须递增 `app/rag.py::RAG_CODE_VERSION`，之后重嵌按篇续跑（每篇跑完在自己的事务里盖章，中断只补没盖章的）。索引只收 `.md`（排除 `.notes.md`），HTML 美化版不入索引。

```sh
python scripts\rag_search.py "如何排查 CSRF 403" --json -k 8   # 命令行 / Agent 入口
pip install -r requirements\requirements-rag.txt               # 依赖装在哪个解释器，哪个解释器就带语义检索
```

依赖或模型缺失时阅读器自动降级为纯 FTS，其余功能不受影响。

## 脚本

- `scripts/export_static.py` — 公网只读档导出器（见上一节）
- `scripts/rag_search.py` — 语义检索 CLI / Agent 入口
- `scripts/new_project.py` — 新项目脚手架（`tests/test_new_project.py` 断言它）
- `scripts/build_index.py` — 手动重建 FTS 索引（通常不需要，应用自建）
- `scripts/scan_sources.py` — 收集桌面散件 / 各仓库 md、txt → `_inbox`
- `scripts/clean_inbox_clones.py` — 清 `_inbox/repos` 里的重复副本（原件在树里才删）
- `scripts/backup_reading.py` — `reading.db` 轮转备份
- `scripts/daily_backup.ps1` — content/ 变更自动 commit + push（**未注册计划任务**，启用须用户在场）
- `scripts/check_*.py` — 门禁：frontmatter 严格 YAML / 台账对账 / 悬空 CSS 令牌 / RAG 版本
- `scripts/agent/` — 跨会话常驻工具：截图、像素对比、CDP 求值、多视口几何、CI 盯梢、语料扫描

## 纪律

契约与不变量的权威在 **[AGENTS.md](AGENTS.md)**，动手前先读。几条最常踩的：

- 任何新知识只从 `_inbox/` 进；`_` 前缀目录不进分类树、不进任何索引。
- 编辑、收藏、备注一律写回文件系统；删除只走软删除（→ `content/_trash/`）。
- 分类学改 `content/_meta/taxonomy.json`，代码里的字典只是兜底；模板与 CSS 不许再抄一份域名单。
- `indexes/` 与 `site/` 是纯派生缓存：可删可重建，禁止手改、禁止 git 跟踪。
- **被跟踪即公开**：本仓远端就是公开仓库，含凭据 / 内部业务 / 真实身份信息的语料必须先进公开面边界名单再提交。

## 测试

```sh
python tests\test_reader.py           # 阅读器行为 + 启动路径 --import-check
python tests\test_e2e_smoke.py        # 端到端：逐条打业务路由
python tests\test_export_static.py    # 公网只读档契约（导出同构 / 只读裁剪 / KB_BASE 口径）
python tests\test_invariants.py       # AGENTS 不变量门禁 I1~I9
python tests\test_predicates.py       # 判定谓词层
python tests\test_properties.py       # 性质测试（随机样本 + 固定种子）
python tests\test_rag.py              # RAG（含与 Rust tokenizers 逐 token 交叉验证；缺依赖自动 SKIP）
python tests\test_ui_regress.py       # P5 视觉回归（截图逐像素 + 顶栏几何）
python tests\test_ui_behavior.py      # UI 行为回归（真点每个控件）
python tests\test_watch_ci.py         # Agent 工具自身
python scripts\check_ledger_counts.py # 台账对账
```

`pre-commit` 钩子会自动跑（`git config core.hooksPath .githooks`）：静态层串行 → 纯 Python 套件并行 → 浏览器两套与 RAG 串行。**本仓库每次提交都要先剥掉 `NO_PROXY`**：`env -u NO_PROXY -u no_proxy git commit ...`，否则 `test_watch_ci` 永久假红。

## 常见坑

- **本机可能没有 `.python\` 便携运行时**。`start.bat` 会自动探测并回退到系统 Python；语义检索依赖装在哪个解释器里，那个解释器启动就带语义检索。
- **端口 5001 残留**：异常退出可能留下仍占着 5001 的旧进程，请求被旧代码接走，症状是"改了没生效"。起服务前 `netstat -ano | findstr :5001` 确认只有一个监听者。
- **`indexes/` 可随时删**，`reading.db` 删了阅读统计归零（语料不受影响）。
- **语料是唯一事实源**。编辑器保存会原样回填 frontmatter，不重排字段、不给标签加引号；`content/` 里出现你没做过的改动就是 bug。
- **bat 脚本一律全英文**（cmd 对 UTF-8 中文 rem/echo 会切碎执行）；测 bat 要用干净 PowerShell，Agent 的 bash shim 会污染 PATH 导致误判。
