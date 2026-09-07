# 知库 Knowledge

个人知识库单一入口：博客、百科、agent 记忆、踩坑记录等全部语料以 **Markdown 文件为唯一事实源**，本仓库提供迁移管线与本地阅读器。

## 布局

```
content/            语料本体（唯一不可再生资产）
  <domain>/<sub>/*.md   两层 taxonomy：9 域 × 子域 × 文档
  *.html                整页美化版旁挂文件（与同名 .md 共存）
  _inbox/               暂存区：一切新材料的唯一入口，归档后才入 taxonomy（不入库）
  _assets/              附件
indexes/            派生索引（FTS5），启动时按 mtime 自动重建，可随时删除
app/                Flask 阅读器：浏览/搜索/编辑写回/备注/收藏
scripts/            迁移与维护脚本
tests/              smoke 测试
```

## 启动

```sh
start.bat          # 纯阅读器（系统 Python，只需 flask）
start-rag.bat      # 全功能（优先用 .python\ 便携运行时，含语义检索）
# http://127.0.0.1:5001
```

写作层：用 Obsidian 打开 `content/` 作为 vault，与本应用共享同一份语料。

## 语义检索（RAG）

本地向量检索，语料不出网：切块（标题路径继承）→ bge-small-zh-v1.5 嵌入
（ONNX，CPU，~11ms/块）→ sqlite-vec 近邻检索。索引 `indexes/rag.db` 为
派生缓存，启动/后台 30s 增量同步，分词或嵌入逻辑变更时自动全量重建。

- 搜索框输入 `? 如何排查 CSRF 403` —— `?` 前缀走语义模式（按意思找，不挑字面）
- 命令行 / Agent 入口：`python scripts/rag_search.py "查询" --json -k 8`
- 运行时：`.python\python.exe -m pip install -r requirements-rag.txt`
  （首次运行自动从 hf-mirror 下载模型约 95MB 至 `app/rag_models/`，之后离线）
- 依赖缺失时阅读器自动降级纯 FTS，其余功能不受影响

## 脚本

- `scripts/migrate_baike.py` — 百科 SQLite → content/（一次性，已执行）
- `scripts/ingest_blog.py` — myblog VitePress md 收编（一次性，已执行）
- `scripts/scan_sources.py` — 全量收集桌面散件 / ~/.dsh 记忆 / E:\GitHub 各仓库 md、txt → _inbox
- `scripts/build_index.py` — 手动重建 FTS 索引（通常不需要，应用自建）

## 纪律

- 任何新知识只从 `_inbox/` 进；博客与百科不再新增内容。
- 编辑、收藏、备注全部写回文件系统（frontmatter / sidecar `.notes.md`），git 全程可追溯。
- 派生物（indexes/、_inbox/）不入库；语料提交遵循"写完即 commit"。

## 测试

```sh
python tests/test_reader.py    # 阅读器行为断言（临时语料）
.python\python.exe tests\test_rag.py   # RAG 断言（分词对齐/端到端语义命中）
```
