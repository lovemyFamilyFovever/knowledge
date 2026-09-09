# AGENTS.md — AI 协作契约

> 任何 AI（TRAE / AutoClaw / 其他）在本仓库工作前必读。违反不变量的改动一律回退。

## 项目一句话

个人知识库单一入口：全部语料以 **Markdown 文件为唯一事实源**，仓库提供迁移管线、本地阅读器（Flask）与本地语义检索（RAG），不依赖任何外部 API，语料不出网。

## 不变量（违反 = 破坏性改动）

1. `content/` 下的 md/html 是唯一事实源；编辑、收藏、备注必须写回文件系统（frontmatter / sidecar `.notes.md`），禁止引入第二真相（数据库 / 云端同步）。
2. 新知识只从 `content/_inbox/` 进；`_` 前缀目录（`_inbox/_assets/_trash/_meta/_unfiled`）不进分类树、不进任何索引。
3. `indexes/`（index.db / rag.db）是纯派生缓存：可随时删除重建；禁止手改、禁止 git 跟踪。
4. 删除必须走软删除（→ `content/_trash/`，`/api/delete`），git 历史是第二重保险。
5. 分类学（域 / 子域 / 来源 / 状态 / 色相）的权威是 `content/_meta/taxonomy.json`；代码里的字典只是缺省回退。改分类先改 JSON，不改代码。
6. frontmatter 只存身世与元数据（title/source/collected/tags/favorite/status），不存阅读统计等高频运行时数据——阅读统计走 app/reading.py（indexes/reading.db 事件制），标签治理/重命名一律先 dry-run（scripts/govern_tags.py）。
7. 嵌入 / 分词 / 切块逻辑变更必须递增 `app/rag.py::RAG_CODE_VERSION`（触发向量索引自动全量重建），并用 `tokenizers` 库做逐 token 交叉验证后再提交。
8. 阅读器同时支持 `start.bat`（任意 Python）与便携运行时（`.python\`）；`python app\app.py` 直启时项目根会自动补进 sys.path，不要依赖 cwd。

## 常用命令

```sh
start.bat                                      # 启动阅读器（存在 .python 时优先用）
start-rag.bat                                  # 显式用便携运行时启动（含语义检索）
.python\python.exe tests\test_reader.py        # 阅读器 smoke（38 断言）
.python\python.exe tests\test_new_project.py   # 脚手架 smoke（9 断言）
.python\python.exe tests\test_rag.py           # RAG smoke（缺依赖自动 SKIP）
.python\python.exe scripts\rag_search.py "查询" --json   # 语义检索 CLI / Agent 入口
```

## 架构地图

```
content/            语料（唯一不可再生资产）；_meta/taxonomy.json = 分类学权威
app/app.py          路由与请求编排（create_app / watcher / RAG 惰性接入）
app/store.py        语料层：frontmatter、扫描、分类树、备注、taxonomy 装载
app/fts.py          FTS5 全文索引 + [[双链]]解析（派生）
app/reading.py      月度阅读统计（reading.db 派生，事件制；设计定稿 docs/统计数据模型-定稿.md）
app/rag.py          语义检索：切块/嵌入/sqlite-vec（派生，RAG_CODE_VERSION 管版本）
scripts/            迁移与维护脚本（rag_search.py 是 Agent 检索入口）
.githooks/          pre-commit：提交前自动跑三套测试
.github/workflows/  CI（GitHub Actions）
```

## 提交纪律

- 写完即 commit；一次改动一个 commit，消息说人话（feat/fix/docs/test + 中文或英文摘要）。
- 提交前跑上面三套测试——pre-commit 钩子会自动跑（`git config core.hooksPath .githooks` 已设置）。
- push 是备份链的一环（另有 Windows 计划任务每日自动 commit+push，见 `scripts/daily_backup.ps1`）。

## 跨机器坑备忘

- git 输出含中文文件名时默认转义为带引号的八进制串（如 `"\347\231\276….md"`），行尾多出的引号使 `\.md$` 类正则大面积漏计（实测 baike 目录 245 个文件只命中 9 个）。统计/匹配 git 路径输出一律加 `-c core.quotepath=false`。
- PowerShell 5.1 读无 BOM 的 UTF-8 脚本按 GBK 解码：若文件还是 LF-only，行尾中文的 UTF-8 末字节（0x80-0xBF，合法 GBK 首字节）会把换行符吞进非法双字节序列，下一行代码被并入注释静默失效（实测 daily_backup.ps1 的 $root 赋值被吞，Join-Path 报 null）。仓库 .ps1 一律 UTF-8 BOM + CRLF（.gitattributes 已强制 `*.ps1 text eol=crlf`）。
- 测试全绿 ≠ 启动路径可用：tests 从项目根导入 `app`，start.bat 脚本直启走另一条解析路径（sys.path[0]=app/ 目录）；2026-09-09 实测 app/ 缺 __init__.py 时直启崩、测试全绿。回归入口：`python app\app.py --import-check`（已入 tests/test_reader.py 断言与 pre-commit 链）。

## 禁区

- 禁止 `git push -f`、禁止改写 main 历史。
- 禁止把语料衍生物、模型权重、虚拟机运行时提交进 git（`.python/`、`app/rag_models/`、`indexes/` 已忽略）。
- 禁止在 `content/` 根目录散放文件；一切新语料走 `_inbox`。
- 不要移除或绕过「写回文件系统」的任何一条路径（api_save / api_note / api_favorite / api_move / api_delete）。
- 不要在没有跑测试的情况下宣称"完成"。
