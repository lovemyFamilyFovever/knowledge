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
indexes/            派生索引（FTS index.db / 向量 rag.db / 阅读统计 reading.db），
                    启动时按 mtime 自动重建，可随时删除（reading.db 删了统计归零）
app/                Flask 阅读器：浏览/搜索/编辑写回/备注/收藏/收件箱/统计
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

## 语义检索（RAG）

本地向量检索，语料不出网：切块（标题路径继承）→ bge-small-zh-v1.5 嵌入
（ONNX，CPU，~11ms/块）→ sqlite-vec 近邻检索。索引 `indexes/rag.db` 为
派生缓存，启动/后台 30s 增量同步，分词或嵌入逻辑变更时自动全量重建
（`RAG_CODE_VERSION` 管理）。索引只收 `.md`（排除 `.notes.md`），HTML 美化版不入索引。

- 搜索框输入 `? 如何排查 CSRF 403` —— `?` 前缀走语义模式（按意思找，不挑字面）
- 命令行 / Agent 入口：`python scripts/rag_search.py "查询" --json -k 8`
- 运行时：`.python\python.exe -m pip install -r requirements-rag.txt`
  （首次运行自动从 hf-mirror 下载模型约 95MB 至 `app/rag_models/`，之后离线）
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
.python\python.exe tests\test_reader.py       # 阅读器行为断言（临时语料）
.python\python.exe tests\test_new_project.py  # 新项目断言
.python\python.exe tests\test_rag.py          # RAG 断言（分词对齐/端到端语义命中）
.python\python.exe tests\test_govern.py       # 标签治理 + 阅读统计断言
```
