# 知库 Knowledge

个人知识库单一入口：博客、百科、agent 记忆、踩坑记录等全部语料以 **Markdown 文件为唯一事实源**，本仓库提供迁移管线与本地阅读器。

## 布局

```
content/            语料本体（唯一不可再生资产）
  <domain>/<sub>/*.md   两层 taxonomy：7 域 × 子域 × 文档（权威定义 content/_meta/taxonomy.json）
  *.html                整页美化版旁挂文件（与同名 .md 共存，阅读页 iframe 内嵌直通渲染）
  _inbox/               暂存区：一切新材料的唯一入口，归档后才入 taxonomy（不入库）
  _assets/              附件
  _trash/               软删除回收站（可手动找回；不入库）
indexes/            派生索引（FTS index.db / 向量 rag.db / 阅读统计+复习进度 reading.db），
                    启动时按 mtime 自动重建，可随时删除（reading.db 删了统计与复习进度归零）
app/                Flask 阅读器：浏览/搜索/编辑写回/备注/收藏/收件箱/统计/闪卡复习/术语门户
app/rag.py          本地语义检索（切块 → ONNX 嵌入 → sqlite-vec）
app/learn.py        学习与复习：抽卡派生库 + SM-2 排期（复用 indexes/reading.db）
app/cards.py        语料 → 闪卡的解析引擎（baike 三种格式 + interview 四种格式）
scripts/            迁移与维护脚本（含每日备份 daily_backup.ps1）
tests/              smoke 测试
```

## 启动

```sh
start.bat          # 纯阅读器（系统 Python，只需 flask）
start-rag.bat      # 全功能（优先用 .python\ 便携运行时，含语义检索）
# http://127.0.0.1:5001
```

写作层：用 Obsidian 打开 `content/` 作为 vault，与本应用共享同一份语料。

## 功能速览

- **收件箱工作流**：新内容丢 `content/_inbox/` → 顶栏「收件箱」进 `/inbox` 页 → 逐篇或批量归档（复选框 + 批量移动，级联 FTS/双链/向量索引）或丢弃
- **全文 + 语义双检索**：搜索框直接输走 FTS（命中高亮）；`?` 前缀走语义模式（按意思找）
- **阅读页**：Markdown 渲染 + mermaid 图 + 美化版 HTML 弹窗内嵌；编辑器带 frontmatter 引导
- **右键菜单**：文档（统计/复制双链/URI/移动重命名）、子目录（目录统计/新建/复制路径）
- **标签管理** `/tags`：标签普查、单标签合并、多选批量合并（两段确认）
- **月度阅读统计** `/stats`：KPI + 环比上月 + 每日条形图 + 文档榜（60s 心跳埋点，本地 reading.db）
- **通用弹窗**：全站自研 kbModal，不再使用系统 prompt/confirm
- **间隔重复闪卡** `/review`：从语料自动抽卡，SM-2 排期，四档自评（重来/困难/良好/简单）
- **面试刷题** `/quiz`：interview 题库，显示问题 → 隐藏答案 → 自评会/不会，与闪卡共用同一套排期后端
- **今日术语 + 掌握度**：首页右上区推一张待复习术语，按子域显示掌握度进度
- **术语百科门户** `/glossary`：662 个术语按子域聚合 + A–Z/`#` 分桶 + 即时过滤 + 一键串学
- **命令面板** `Ctrl/Cmd+K`：662 术语 + 695 文档 + 73 子域 + 6 条命令，输入即模糊匹配
- **双链补全与断链提示**：编辑器输入 `[[` 联想已有词条，未解析链接在底部红条列出（带行号可跳转）
- **键盘导航**：`j`/`k` 上下篇、`/` 聚焦搜索、`Esc` 关闭面板、`?` 查看快捷键
- **阅读偏好**：字号 / 行宽 / 字体 / 行高，命令面板内调整，持久化到 localStorage
- **搜索直达与筛选**：结果按域/子域/标签分面过滤，术语精确命中置顶，`?` 前缀切语义模式
- **响应式**：手机/平板单栏阅读，面板收起为底部条，触控区 ≥44px

## 学习与复习系统

把「存知识」变成「练知识」。全部离线，复习状态只存派生库，**不写进语料 frontmatter**。

- **抽卡来源**：`content/baike/`（概念定义卡 + 常见误区卡）与 `content/interview/`（问答卡）。
  解析器兼容语料实际存在的多种格式（baike 三种、interview 四种），教程类长文**刻意不抽卡**（避免噪音）。
- **排期算法**：SM-2。评分四档映射到 `q`：重来 `0` / 困难 `3` / 良好 `4` / 简单 `5`。
  间隔序列 `1 → 6 → interval × EF`，`EF` 初值 2.5、下限 1.30、上限 2.8，间隔上限 365 天。
  掌握判定：`interval >= 21 且 reps >= 3`。
- **状态存放**：`indexes/reading.db` 的四张表（`cards` / `review_state` / `review_events` / `learn_meta`），
  事件制：`review_events` 只追加不修改，`review_state` 是当前态快照，两者在同一个事务里双写。
  **删掉 `reading.db` 会丢失复习进度，但卡片会按语料自动重建**（首次访问约 2 秒）。
- **卡片 ID 与路径解耦**：`card_id` 由「类型 + 术语名 + 正面文案」的哈希决定，**不含文件路径**。
  所以语料改名、换子域都不会丢复习记录；只有术语名或定义文案被改写才会生成新卡。
- **同步接口**：`POST /api/learn/sync`（幂等，带 mtime 增量判据），`force=1` 可强制全量重扫。
  解析规则变更时必须递增 `app/cards.py::CARDS_PARSER_VERSION` 触发全量重建（对齐 `RAG_CODE_VERSION` 的做法）。
- **命令行/Agent 入口**：`python scripts/rag_search.py "查询" --json`（语义检索）；
  卡片库可直接查 `indexes/reading.db`。

## 快捷键

| 键 | 作用 |
|---|---|
| `Ctrl/Cmd + K` | 打开命令面板（术语/文档/子域/命令） |
| `/` | 聚焦搜索框 |
| `Esc` | 关闭面板 / 编辑器 |
| `j` / `k` | 文档列表或卡片队列上下移动 |
| `?` | 快捷键帮助 |
| `Space` | 复习页翻面 |
| `1` `2` `3` `4` | 复习页评分：重来 / 困难 / 良好 / 简单 |
| `Ctrl/Cmd + S` | 编辑器内保存 |

（输入框/文本域聚焦时，除 `Esc` 与 `Ctrl/Cmd+K` 外不劫持任何按键。）

## 语义检索（RAG）

本地向量检索，语料不出网：切块（标题路径继承）→ bge-small-zh-v1.5 嵌入
（ONNX，CPU，~11ms/块）→ sqlite-vec 近邻检索。索引 `indexes/rag.db` 为
派生缓存，启动/后台 30s 增量同步，分词或嵌入逻辑变更时自动全量重建
（`RAG_CODE_VERSION` 管理）。索引只收 `.md`（排除 `.notes.md`），HTML 美化版不入索引。

- 搜索框输入 `? 如何排查 CSRF 403` —— `?` 前缀走语义模式（按意思找，不挑字面）
- 命令行 / Agent 入口：`python scripts/rag_search.py "查询" --json -k 8`
- 运行时：`pip install -r requirements-rag.txt`
  （依赖 `numpy` + `onnxruntime` + `sqlite-vec`，合计约 52 MB 下载 / 约 130 MB 磁盘；
  首次运行自动从 hf-mirror 下载 `bge-small-zh-v1.5` 模型约 24MB 至 `app/rag_models/`，之后完全离线）
- 依赖缺失时阅读器自动降级纯 FTS，其余功能不受影响

## 备份

- `scripts/daily_backup.ps1` — content/ 变更自动 commit + push（v2：根路径自推导，跨机器可用）
- 计划任务注册（等用户在场监督时执行）：
  `schtasks /Create /F /TN "KnowledgeDailyBackup" /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File <仓库根>\scripts\daily_backup.ps1" /SC DAILY /ST 09:00`
- 注意：`_inbox/` 与 `_trash/` 在 .gitignore 中，不在 git 备份覆盖内，冷备份另行处理

## 脚本

- `scripts/migrate_baike.py` — 百科 SQLite → content/（一次性，已执行）
- `scripts/ingest_blog.py` — myblog VitePress md 收编（一次性，已执行）
- `scripts/scan_sources.py` — 全量收集桌面散件 / ~/.dsh 记忆 / E:\GitHub 各仓库 md、txt → _inbox
- `scripts/build_index.py` — 手动重建 FTS 索引（通常不需要，应用自建）
- `scripts/govern_tags.py` — 标签治理：census 普查 / similar 相似推荐 / merge 合并 / rename-sub 子域重命名（默认 dry-run，`--apply` 才写盘）

## 纪律

- 任何新知识只从 `_inbox/` 进；博客与百科不再新增内容。
- 编辑、收藏、备注全部写回文件系统（frontmatter / sidecar `.notes.md`），git 全程可追溯。
- 分类学权威是 `content/_meta/taxonomy.json`（改它，不要改代码里的硬编码）。
- 派生索引（indexes/）不入库；语料提交遵循"写完即 commit、提交信息写详细"。

## 测试

```sh
python tests\test_reader.py       # 阅读器行为断言（含启动路径 --import-check）
python tests\test_new_project.py  # 脚手架断言
python tests\test_learn.py        # 抽卡解析 + SM-2 + 派生库断言
python tests\test_govern.py       # 标签治理 + 阅读统计断言
python tests\test_rag.py          # RAG 断言（缺依赖时自动 SKIP）
```

`pre-commit` 钩子会在每次提交前自动跑上面五套（`git config core.hooksPath .githooks`）。
钩子会逐个候选解释器尝试 `import flask`，选第一个可用的；找不到就报错退出而不是静默跳过。

## 常见坑

- **本机可能没有 `.python\` 便携运行时**。`start.bat` 与 `start-rag.bat` 都会探测，但直接用
  绝对路径的解释器更稳（例如 `C:\Users\<你>\AppData\Local\Programs\Python\Python3xx\python.exe`）。
- **端口 5001 残留**：异常退出可能留下仍占着 5001 的旧进程，请求会被旧代码接走，症状是
  「改了没生效」。起服务前 `netstat -ano | findstr :5001` 确认只有一个监听者。
- **`indexes/` 可随时删**。`index.db` / `rag.db` 删了自动重建；`reading.db` 里的阅读统计与
  **复习进度**删了不恢复（卡片会重建，进度归零）。
- **语料是唯一事实源**。编辑器保存会原样回填 frontmatter，不会重排字段或给标签加引号；
  如果发现 `content/` 里出现你没做过的改动，那是 bug，不是预期行为。
