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
start.bat          # 或: pip install -r requirements.txt && python app/app.py
# http://127.0.0.1:5001
```

写作层：用 Obsidian 打开 `content/` 作为 vault，与本应用共享同一份语料。

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
python tests/test_reader.py    # 23 项行为断言，临时语料，不碰真实 content/
```
