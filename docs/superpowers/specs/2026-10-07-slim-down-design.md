# 主项目瘦身：删除复习/术语/标签治理/书库处理四套子系统

日期：2026-10-07　状态：待主人复核　负责人：QwenWork

## 0. 前置未结事项（本规格执行前必须先销的账）

这三笔来自同日早些时候的泄露处置，不因瘦身而作废：

1. **旧远端是否已删除未确认**。`git ls-remote origin` 最后一次执行返回的是 `443 连接超时`，不是 404，两种情况含义不同。推送新历史前必须重新确认，否则会推不上去或被旧库吞掉。
2. **飞书凭据未重置**。`content/projects/AI金/docs/客服/01-人工客服-飞书Bot运维指南.md` 内含 `cli_` App ID（2 处）与 32 位 AppSecret 字面量，仓库已公开约一个月。该目录已排除出公开面，但**已发出的密钥不会因为删除文件而失效**，必须去飞书开放平台重置。
3. **AGENTS.md 现有三处已变为假话**，须与本次瘦身的契约改动合并进同一次提交修正：
   - 不变量 4「git 历史是软删除的第二重保险」—— 历史已重置为单提交（`b4cda2e`），该机制失效；
   - 禁区「禁止 `git push -f`、禁止改写 main 历史」—— 需注明 2026-10-07 经用户授权的一次性例外及授权范围；
   - 缺失：`NO_PROXY=localhost,127.0.0.1,::1` 会让 `tests/test_watch_ci.py` 的 A2/H1 假失败，本仓库以后每次提交须 `env -u NO_PROXY git commit`（这是环境隔离缺陷，修测试本身另案，不在本规格内）。
   - 新增：`.gitignore` 的「公开面硬边界」段已是既成事实（`content/projects/`、`content/小说/`、`content/漫画/`、两个 PII 文件），AGENTS 需记录"被跟踪即公开"这条新前提。

## 1. 目标与判据

**目标**：删除有实测使用证据支撑的死功能，降低维护心智。

**判据（按实测数据，不按印象）**：

| 证据来源 | 数值 |
|---|---|
| `indexes/reading.db.review_events` | 2 条（3157 张卡复习过 2 张，其中一次为 3600 秒挂机） |
| `indexes/reading.db.cards` | 3157 张（生成器一直在跑，消费为零） |
| `/api/rag`、`/api/rag/status` 前端引用数 | 0（本轮不删 RAG，仅记录） |
| `content/小说/`、`content/漫画/` | 语料已于 2026-10-01 永久退场，`kb-novel.js` 处理对象不存在 |
| `indexes/learn.db` | 0 字节 |

**明确保留**（用户未选砍）：RAG 语义检索（含不变量 7 全套）、统计与阅读心跳（`reading.py`/`/stats`）、frontmatter 的 `tags` 字段及其在文档列表与搜索过滤中的用途。

## 2. 删除清单

### 2.1 复习 / 学习 / 术语整栈（一次删除，术语表本就住在 learn.py 内）

依赖关系实测：`app/routes_search.py:226 /api/glossary` 与 `:255 /glossary` 调用的 `glossary()` 定义在 **`app/learn.py:874`**；命令面板 `goto-glossary` 定义在 `app/learn.py:69`。故"复习"与"术语"不可分拆。

整文件删除：

- `app/learn.py`（1244 行）、`app/cards.py`（714）、`app/sm2.py`（95）、`app/routes_learn.py`（351）
- `static/pages/learn.js`（546）、`static/pages/glossary.js`（343）
- `app/templates/review.html`、`app/templates/quiz.html`、`app/templates/glossary.html`（46）
- `tests/test_learn.py`（960 行 / 255 断言）

局部删除：

- `app/app.py`：`learn_bp` 注册
- `app/routes_search.py`：`/api/glossary`(226) 与 `/glossary`(255) 两个端点
- `app/routes_doc.py`、`app/routes_pages.py`、`app/routes_stats.py`、`app/store.py`：对 learn/cards/sm2 的 import 与调用点（逐处删，见 §2.4 波及面清单）
- `app/templates/base.html:206,207`：顶栏 `复习`、`术语` 两个 `.tn`（现共 7 项：阅读/复习/术语/统计 | 收藏/标签/治理，全瘦身后**剩 3 项：阅读/统计/收藏**）
- `static/kb-core.js`：learn/glossary 的 `KB.api.*` 方法（sync/due/review/mastery/today/roam/wlSuggest?/glossary）与快捷键 registry 中对应项
- 路由合计（实测 `create_app().url_map`，全库 56 条含 static、应用级 55 条）：`/api/learn/{sync,due,mock,review,mastery,recent_read,today,cards,roam}` 9 条 + `/review` `/quiz` 2 条 + `/api/glossary` `/glossary` 2 条 = **13 条**

### 2.2 /tags 页 + 标签治理链（用户选定第 2 档：页面与治理一起砍，保留 tags 元数据）

- `app/templates/tags.html`（53）、`app/templates/governance.html`
- `app/routes_pages.py:309 /tags` 及治理页路由
- 端点合计（实测）：`/tags`、`/api/tags`、`/api/tag/merge`、`/governance`、`/api/governance/scan` = **5 条**
- `static/pages/governance.js`（335）
- `app/store.py`：`tag_census`(619)、`find_similar_tags`(636)、`_merge_tags_line`(678)、`merge_tag`(710)
- `scripts/govern_tags.py`（108）
- `tests/test_govern.py`（174 行 / 28 断言）
- **入口与死链清理点（实测坐标，漏一个就是点开的 404）**：`app/templates/base.html:212` 顶栏「标签」钮、`:213` 顶栏「治理」钮、`app/templates/workbench.html:27` 左栏 tree-foot「标签管理」行、`static/app.js:3058` 命令面板「标签管理」项、`static/pages/misc.js:78-82`（合并成功后回取 `/tags` HTML 片段，随治理链一起删）、`app/templates/governance.html:3,59` 引用的 `pages/governance.css`/`.js`
- AGENTS.md 不变量 6 中「标签治理/重命名一律先 dry-run」整句及常用命令里的 `govern_tags.py` 行

**保留**：`app/routes_search.py:295 _pass(d, s, tags)` 的标签过滤、`static/app.js:1127` 文档列表 tag chip 与 `:1211` 头部 tagChips、995 个语料文件的 `tags:` 字段。理由：这些属于数据模型与检索面，删除需要批量重写语料，收益不成比例。

### 2.3 书库处理逻辑（**待勘查，本规格不含删法承诺**）

`static/kb-novel.js`（1020 行）与 `tests/test_js_props.py` 的畸形 zip/txt 样本。**勘查前置**：`app/store.py` 的目录扫描与 `app/routes_files.py` 的 `/raw/<rel>` 分支同时服务普通附件与文章配图；未逐处确认前不得删除，否则会砍断图片显示。执行时本项单独一次提交，先出勘查报告再动手。

`docs/note-library-reader.md` 归档说明保留。

### 2.4 引用波及面（需同步修改的文件，实测 grep 结果）

`app/app.py`、`app/routes_doc.py`、`app/routes_pages.py`、`app/routes_search.py`、`app/routes_stats.py`、`app/store.py`、`tests/test_e2e_smoke.py`、`tests/test_invariants.py`、`tests/test_js_props.py`、`tests/test_predicates.py`。

## 3. 契约与门禁同步（漏一条就会骗到下一个接手者）

- AGENTS.md：常用命令表删 `test_learn.py`、`test_govern.py` 两行及其断言数；`test_e2e_smoke.py`「打满 56 条路由」的数字按实删修正；不变量 6 删治理条款；架构地图删 `learn/sm2/cards` 行；§0 三条修正一并做。
- `tests/test_invariants.py`：I1~I9 中涉及 learn/glossary/标签治理的断言随删随改，不得留悬空断言。
- **UI 基线**：`tests/ui-baselines/` 的 22 张截图矩阵含 `/review`、`/quiz`、`/glossary`、`/tags` 镜头，必须同步从矩阵移除并 `python tests/test_ui_regress.py --update` 刷新基线。**不刷新 = 该门禁永久红**，此项列为验收硬条件。
- `scripts/check_ledger_counts.py` 是 pre-commit 台账对账闸：docs 台账 §0 数字须与 §1~§5 重算一致，瘦身改状态列后必须同批改数字。
- `indexes/ai.db`（轮次 54 遗留死文件，3 行记录）与 `indexes/learn.db`（0 字节）一并删除；`indexes/` 属 gitignored 派生缓存，零成本。`reading.db` 的 `cards`/`review_events`/`review_state` 表保留库本体、由新代码路径自然不再写入。

## 4. 执行顺序与提交切分

每批一次提交，每次提交用 `env -u NO_PROXY git commit` 并跑全量门禁（实测一趟约 10 分钟：并行 15 项 + UI 行为 430 断言 + RAG smoke）：

1. 勘查报告：`kb-novel.js` 与 `/raw` 附件路径的耦合点清单（纯读，不改代码）。
2. 提交一：删 §2.1 复习/术语整栈 + §3 对应契约行 + UI 基线矩阵同步。
3. 提交二：删 §2.2 标签页与治理链 + 契约同步。
4. 提交三：按勘查结论删 §2.3 书库逻辑（若勘查显示耦合过深，改为保留并记录理由——**不允许为了不砍而含糊，也不允许为了砍而打断附件**）。
5. 提交四：AGENTS.md 的泄露处置契约修正（§0 第 3 条）+ 死文件清理。
6. 提交五：推送新历史（前置：§0 第 1、2 条已确认）。

## 5. 验收标准

1. `python tests/test_reader.py`、`test_invariants.py`、`test_e2e_smoke.py`、`test_properties.py`、`test_predicates.py`、`test_rag.py` 全绿，且 `test_e2e_smoke` 的路由清点等于实际注册路由数（不许靠删断言凑数）。
2. `python tests/test_ui_regress.py` 绿（基线已随功能同步刷新，不是靠 `--update` 掩盖未预期的像素变化）。
3. `grep -rn "learn\|glossary\|govern_tags\|tag_census" app/ static/ tests/` 无残留引用；`python app/app.py --import-check` OK。
4. 阅读主路径人工可读：`/` 分类树、`/doc/…` 正文渲染、`/search`、`[[双链]]`、`/favorites`、`/inbox`、`/stats` 全部可用。
5. 语料零污染复核：`git status` 中不得出现任何 `content/**.md` 的修改（本规格明确禁止批量重写 frontmatter）。

## 6. 本规格不做什么

- 不改数据模型：frontmatter 键集、`tags` 字段、taxonomy 分类学权威位置不动。
- 不碰 RAG 与统计。
- 不动 `knowledge-site`（用户指令：先别动 site 页面）。
- 不做仓库合并方案（同一前端 + 静态适配器的设计已成形，因本轮转向瘦身而挂起，另立规格）。
- 不修 `test_watch_ci.py` 的 NO_PROXY 环境隔离缺陷（另案）。
