# AGENTS.md — AI 协作契约

> 任何 AI 在本仓库工作前必读。违反不变量的改动一律回退。

## 项目一句话

个人知识库单一入口：全部语料以 **Markdown 文件为唯一事实源**，仓库提供本地阅读器（Flask）、本地语义检索（RAG），并导出一份 **GitHub Pages 静态只读档**（<https://lovemyfamilyfovever.github.io/knowledge/>）。**没有任何出站请求，语料只进不出。**

## 不变量（违反 = 破坏性改动）

1. `content/` 下的 md/html 是唯一事实源；编辑、收藏、备注必须写回文件系统（frontmatter / sidecar `.notes.md`），禁止引入第二真相（数据库 / 云端同步）。
2. 新知识只从 `content/_inbox/` 进；`_` 前缀目录（`_inbox/_assets/_trash/_meta/_unfiled`）不进分类树、不进任何索引。
3. `indexes/`（index.db / rag.db）、`site/`（公网档导出产物）是纯派生缓存：可随时删除重建；禁止手改、禁止 git 跟踪。
4. 删除必须走软删除（→ `content/_trash/`，`/api/delete`）。**git 历史不是第二重保险**（main 曾在泄露处置中重置，旧提交不可恢复）。软删除只有 `_trash/` 一层，别指望从 git 里 `show` 回来。
5. 分类学（域 / 子域 / 来源 / 状态 / 色相）的权威是 `content/_meta/taxonomy.json`；代码里的字典只是缺省回退。改分类先改 JSON，不改代码。域条目可选 `"search": false` = 该域不进搜索浮层的筛选钮（给了一个点了恒 0 结果的钮不如不给）。模板与 CSS 一律**不许再抄一份域名单**：浮层钮由 `LABELS` 派生，色点用 `--dh=色相数字`。
6. frontmatter 只存身世与元数据（title/source/collected/tags/favorite/status），不存阅读统计等高频运行时数据 —— 阅读统计走 `app/reading.py`（`indexes/reading.db` 事件制：open/read_minute/finish 只追加，语料零污染）。
7. 嵌入 / 分词 / 切块逻辑变更必须递增 `app/rag.py::RAG_CODE_VERSION`，并用 `tokenizers` 库做逐 token 交叉验证后再提交。**递增之后的重嵌是逐篇续跑的**：每篇跑完就在 `files.embed_ver` 落自己的章（一事务），中途被 kill 下次只补没盖章的那些。版本判据**只活在 `files.embed_ver` 一处**，不许有第二道闸门（`rag_status` 里那个 `stale` 就是剩余量）。旧库缺这一列时打开即迁移，但只有 `meta.code_version` 相符**且**向量行数与元数据一致才补章（`stamp_legacy`），来历不明就留 NULL 重嵌。这条有断言在管：`tests/test_rag.py::test_tokenizer_cross_validated_against_library()` 每次跑都拿参考库逐 id 比对，`tests/test_predicates.py` 另有不依赖模型文件的合成 `tokenizer.json` 断言。
8. 阅读器同时支持 `start.bat`（任意 Python）与便携运行时（`.python\`）；`python app\app.py` 直启时项目根会自动补进 sys.path，不要依赖 cwd。
9. **本项目不做任何出站请求**（不配 API key、不调任何 AI / 云 API）。曾有的「选词问 AI」已整体下线，用户两次明确要求做减法。要重新引入任何出站能力，必须先与用户确认。编号占住是为了防止有人顺手加回来。
10. **被跟踪即公开**：本仓库远端就是公开 GitHub 仓库，任何进入 git 跟踪的文件等于对外发布，**没有第二层拦截**。公开面的权威是 `.gitignore` 的「公开面硬边界」段 + `scripts/export_static.py` 的 `EXCLUDE_DIRS`，当前名单为 `content/projects/`、`content/小说/`、`content/漫画/`、`content/interview/AI金项目面试/resume-master.md`、`content/interview/AI金项目面试/profile-baseline.md`。**新语料含内部业务文档 / 凭据 / 真实身份信息时，必须先加进边界名单再 commit。** 这条没有门禁断言（I1~I9），提交前人工复核：

    ```sh
    git ls-files -z | xargs -0 grep -laE "(cli_[0-9a-f]{12,}|(app_?secret|password|token)[\"' ]{0,3}[:=][\" ]{0,2}[0-9A-Za-z]{20,})"
    ```

    命中须逐个判真伪后处置。注意两点实测：`xargs -0` 必须配 `-z` 的 NUL 分隔输入（用换行会把整串当一个文件名 → **假"0 命中"**）；`tests/test_export_static.py` 里有合成假凭据 `cli_abcdef012345`，**永久命中**，不是泄漏。

## 常用命令

```sh
start.bat                                      # 唯一启动入口（--dev 开发模式；自动探测 .python / 系统 Python）
start.bat --dev                                # 开发模式（py/模板改动自动热重载）
python scripts\export_static.py --out site --base /knowledge   # 导出公网只读档 → site/（见下方 MSYS 警告）
python scripts\rag_search.py "查询" --json     # 语义检索 CLI / Agent 入口
python scripts\check_ledger_counts.py          # 台账对账：§0 数字必须等于按 §1~§5 状态列重算的数
```

测试（`python tests\X.py`，无 pytest，各自可独立执行）：

| 套件 | 断言 | 管什么 |
|---|---|---|
| `test_reader.py` | 80 | 阅读器行为 + 启动路径 `--import-check` |
| `test_new_project.py` | 9 | 脚手架 |
| `test_predicates.py` | 73 | 判定谓词层（合成 tokenizer.json 钉分词 special 字面量 · rag 续跑判据真值表） |
| `test_properties.py` | 14 | 性质测试（每条 240 个随机样本，固定种子） |
| `test_invariants.py` | 71 | AGENTS 不变量门禁 I1~I9（含 I4 物理删除调用点白名单） |
| `test_e2e_smoke.py` | 170 | 端到端：逐条打满 40 条路由 |
| `test_export_static.py` | 135 | 公网只读档契约（导出同构 / 只读裁剪 / KB_BASE 口径 / 公网文案与首页 / PWA 清单） |
| `test_known_defects.py` | 6 | 已登记缺陷不回退 |
| `test_watch_ci.py` | 38 | Agent 工具自身（四类"读不到"分开点名；GBK/UTF-8 两档都要绿） |
| `test_ui_regress.py` | 31 | P5 视觉回归：11 张截图逐像素 vs `tests/ui-baselines/` + 10 条顶栏几何 |
| `test_ui_behavior.py` | 247 | UI 行为回归：真点每个控件，看它到底有没有反应 |
| `test_rag.py` | — | RAG（与 Rust tokenizers 逐 token 交叉验证 + 续跑三证；缺依赖/缺模型才 SKIP） |

`--stability` 只验"两次截图逐像素相同"（改矩阵或换环境后先跑它）；`--update` 在确认改动无误后刷新基线。

> **导出器在 Git Bash 里必须加 `MSYS_NO_PATHCONV=1`**：`--base /knowledge` 会被 MSYS 在交给 Windows 版 Python 之前改写成 `C:/Program Files/Git/knowledge`，整站链接与 404 兜底就此指到本机目录树（线上是 Linux runner 所以没中招）。`export_static.check_base()` 现在会直接拒绝带盘符/反斜杠的 KB_BASE，不再静默产出坏站；cmd 与 PowerShell 下无需该变量。
> 只读档本地预览：`mkdir .qa/serve-root && cmd /c mklink /J .qa\serve-root\knowledge site`，再 `python scripts\agent\serve404.py 8112 .qa/serve-root`，打开 `http://127.0.0.1:8112/knowledge/`。它按 GH Pages 的 SUBDIRECTORY 口径把 `<前缀>/404.html` 当深链回落（所以离线与路由桥才验得准），并**显式把 `.js` 钉成 `application/javascript`** —— Windows 注册表默认报 `text/plain`，Chrome 会拒绝执行，PWA 看着像做坏了。直接 `python -m http.server -d site` 只能验空前缀那一种口径，深链的 404 回落验不到。

## 正文排版约定（markdown 渲染层消费）

`.a-body` 渲染由 CSS + `app.js::enhanceArticleDOM` 后处理，作者侧零负担：

- 大节写 `## 小节名`（自动包成 .sec-card 卡片，标题 hash 定渐变色）；题干写 `### N. 题干｜初级|中级|高级`（尾部难度自动转徽章）。
- 提示框用引用首行标记：`> 💡` 提示、`> ⚠️/❗` 警告、`> 🎯`/`关键要点` 关键点、`> 🔍`/`追问` 追问。
- 代码用围栏（hljs 克制单色高亮、随明暗主题翻转）；对比内容用表格。
- 设计基准：渐变条按标题 hash 稳定取色、代码浅底 + 单色高亮、`##` 分组。

## 架构地图

```
content/            语料（唯一不可再生资产）；_meta/taxonomy.json = 分类学权威
app/app.py          路由与请求编排（create_app / watcher / RAG 惰性接入）
app/store.py        语料层：frontmatter、扫描、分类树、备注、taxonomy 装载
app/fts.py          FTS5 全文索引 + [[双链]]解析（派生）
app/reading.py      阅读统计（reading.db 派生，事件制）
app/rag.py          语义检索：切块/嵌入/sqlite-vec（派生，RAG_CODE_VERSION 管版本）
app/wikilink.py     [[双链]]补全候选池 / 打分 / 断链检查
app/palette.py      命令面板索引
static/app.js       阅读器主逻辑；static/kb-core.js = KB 内核（overlay / 设置 / 命令面板 / 快捷键）
                    窄屏（≤860，与 style.css 隐藏 `main > section.wb-panel` 同一档）两坨抽屉：
                    底部工具栏（railSheet：分类 / 目录 / 标签 / 备注 / 双链，点页签从下往上展开）
                    与「分类」抽屉（navSheet，唤出被隐藏的左树）；两者互斥，
                    关闭手势四条齐全（再点当前页签 / Esc / 点抽屉外 / 换文档）
static/kb-static.js 只读适配器（只在导出产物里加载）：fetch 分诊（读→data/*.json、写→READ_ONLY、
                    裁剪端点→NOT_IN_STATIC）、KB_BASE 链接与路由桥、只读裁剪 CSS、
                    公网状态栏与 <title> 口径、根路径的「公网首页」态；
                    /api/doc 被 SW 判死（离线且没缓存过）时回 **503 OFFLINE**，app.js 对 503 单独
                    说一句人话——不许拿 404 顶它，那等于对读者宣称"这篇被删了"
scripts/export_static.py  导出器：公开白名单语料 staging → 复用读端点产 payload → site/ 落盘
static/kb-sw.js       公网档的 Service Worker **源**（占位符 KB_BASE / KB_BUILD / PRECACHE 由导出器
                    替换后落到 site/sw.js；产物里不留第二份）。缓存三档：导航=网络优先断了回壳、
                    data/*.json=网络优先并落缓存、static+raw=缓存优先；预热只装壳引用到的 30 件
                    资源（1.5MB），语料一条不预热。本地阅读器不注册它（热重载不该再叠一层缓存）
static/kb-pwa.js      SW 注册件，同样只由导出器写进 <head>；判据仍是 KB_STATIC.readonly
static/icons/         PWA 图标四件套（由 .qa 一次性从 base.html 的品牌标渲染，改标要重出）
app/templates/landing_panel.html  首页那一屏的唯一一份标记：本地 include 渲染（收件箱 / 本月统计 /
                    取景框全在），导出器以 home_readonly=True 再渲染一次成 data/home.html
                    （只留「搜索」+「继续上次阅读」）。改首页只改这一处，不许复制第二份
.github/workflows/pages.yml  push main → export_static → deploy-pages（线上即本仓 Pages）
.github/workflows/ci.yml     push → 静态层 + 上表全部套件（windows runner）
.githooks/pre-commit         静态层（ruff / 台账对账 / 悬空令牌 / RAG 版本）串行 → 纯 Python 套件
                             并行（KB_GATE_PARALLEL 默认 4，=1 串行）→ 动了语料加一道 frontmatter 闸
                             → 浏览器两套与 RAG 串行（缺依赖自动 SKIP）
requirements/       依赖清单（requirements.txt 核心 / -rag.txt 语义检索 / -lock.txt 便携环境锁）
测试文件/覆盖台账.md  覆盖率台账：§0 轮次汇总、§1~§5 格子清单、§6 发现台账、§7 门禁现状
```

**只读档的两层裁剪分工（不许互相抄）**：静态存在的写入口（按钮、页签、导航链接、引擎钮）归 `kb-static.js` 里那份 CSS 隐藏清单；运行时才生成的写入口（右键菜单项、拖拽、动态图、快捷键帮助）归 `app.js` / `kb-core.js` 里的 `KB_READ_ONLY`（判据 = 注入的 `window.KB_STATIC.readonly`），菜单项打 `roHide: true` 由 `openCtxMenu` 单点过滤、空菜单不弹。**CSS 清单挡不住动态节点，别指望加选择器解决。**

## 工具与临时产物（`scripts/agent/` 进 git；`.qa/` 不进 git）

Agent 的**常驻工具**统一收在 `scripts/agent/`（进 git、跨机器复用）。`.qa/` 只放**一次性诊断产物**，不进 git：验证类脚本不要落盘 txt，直接看 stdout；**任务收工后 `.qa/` 里自己产生的东西要清掉**，别留给下一个人排雷。

| 常驻工具 | 用途 |
|---|---|
| `shot.mjs` | 零依赖 CDP 截图：`node scripts/agent/shot.mjs <url> <out.png> [w] [h] [clickSel]`；`--batch manifest.json` 批量截（一个 Chrome 多标签，清单形如 `{"shots":[{url,out,w,h,init,clickWait}]}`，`init` 是页面任何脚本前注入的 JS，用来钉死主题/动画等确定态）。`clickWait` 是**上限**不是睡眠：字体就绪 + 在途 fetch 归零 + DOM 连续 320ms 无变化就提前走 |
| `imgdiff.mjs` | 像素对比：`node scripts/agent/imgdiff.mjs <a.png> <b.png> [fuzz%]`，回差异像素数 AE 与占比 + 热图。**没有 ignoreRegions 参数** —— 要排除动画区域就先用 `magick <img> -crop WxH+X+Y +repage out.png` 裁开再比 |
| `evalcdp.mjs` | CDP 执行任意 JS 并回显返回值 + console 报错：`node scripts/agent/evalcdp.mjs <url> "<js>"`（表达式以 `@` 开头时按文件读取，长载荷塞不进 argv） |
| `geom.mjs` | 多视口几何探针：`node scripts/agent/geom.mjs <url> <w1,w2,...> <expr@文件>`，逐档设宽求值、每档回一行 JSON。用途：① 顶栏压字这类"像素基线永远绿"的重叠问题 ② 当行为测试的驱动器 —— **evalcdp 的视口只有 ~764px**，依赖侧栏/浮层定位的断言都得用它钉桌面宽度。**表达式必须一次求值取全部矩形**，逐字段各自 `getBoundingClientRect()` 会在过渡中读出三套数 |
| `verifyall.mjs` | 同页两阶段 evaluate 模板（如 pretty/md 切换），按需改表达式复用 |
| `watch_ci.py` | 盯 GitHub Actions 到结论：`python scripts/agent/watch_ci.py <sha 前缀> [等待秒=420]`。回 run 状态 + 逐步 conclusion + **annotations**（`::notice::STARTED` / `::warning::SKIPPED`，见 `tests/_ci.py`）—— 匿名 API 读不到日志正文，只有这三样能证明某一步真跑了。四类"读不到"分开报：够不着 API=4 / 限流=3 / 列表里没这个 sha=5 / 200 但正文不是 JSON=6。网络飘时设 `KB_CI_PROXY=http://127.0.0.1:7897` |
| `scan_fm.py` | frontmatter 污染扫描：正文前 400 字符内又出现完整 fm 块 = 污染 |
| `scan_dup.py` | 抓取残留副本扫描：`xxx-<数字>.md` 与 `xxx.md` 同名共存即残留 |
| `serve404.py` | GitHub Pages 本机模拟器：`python scripts/agent/serve404.py <端口> <文档根>`。文档根下必须放成 `<前缀>/…`（junction 到 `site/` 即可），404 走该前缀的 `404.html`（GH Pages 的 SUBDIRECTORY 行为），并显式钉 `.js`/`.webmanifest` 的 content-type（Windows 默认把 `.js` 报成 `text/plain`，Chrome 拒绝执行 → PWA 看着像坏的） |

两个 scan 脚本的扫描根默认按脚本位置推导到仓库根下的 `content/`，传 argv[1] 可覆盖。

**UI 回归纪律**：改动 UI（css/js/模板/渲染逻辑）后

0. **首选一条命令**：`python tests\test_ui_regress.py`（合成语料的临时实例 + 11 张截图逐像素 + 10 条顶栏几何）。pre-commit 在提交含 css/js/模板时自动跑它。刷新基线用 `--update`，动矩阵/换环境先跑 `--stability` 证明截图本身是确定的。
1. 几何断言不是多余的：像素基线的口径是"和上次一样吗"，重叠/贴脸/溢出是**稳定地错**，比对永远绿。判"两块矩形相不相交"用 `geom.mjs`。
2. 手工对比用 `imgdiff.mjs a.png b.png 0%` 并按**差异像素数**判 —— 默认 2% 容差只适合肉眼复核，实测会把真回归读成绿。**不要用放大 fuzz 压噪点**：噪点靠钉死动态内容消除（截图清单的 `init` / `clickWait`），或者先测噪声地板（同页截两次比一次）。
3. 热图里出现**不该变的区域变红** = 改 A 崩 B，修完再交。`--update` 会顺手刷新别的镜头：字节变了而 AE=0 是 PNG 编码噪声，退回 HEAD 不入提交。
4. CSS 受严格 lint 管：`npm run lint:css` 开着 `no-duplicate-selectors` 与 `block-no-empty`。同选择器分块写是刻意的，但**必须就地写一条带理由的 `stylelint-disable`**；无理由放行视为回退。空规则块按缺陷删掉。唯一生效的配置是 `.stylelintrc.json`。

注意：**bat 脚本一律全英文**（cmd 对 UTF-8 中文 rem/echo 会切碎执行）；**测 bat 必须用干净 PowerShell**，Agent 的 bash shim 会污染 PATH 导致误判。

## 提交纪律

- 适时提交：每完成一个逻辑独立的开发单元就 commit，不要等全部结束。消息说人话（feat/fix/docs/test + 中文摘要），并把"为什么"写清楚。
- **只提交自己改过的文件**：一律用显式 pathspec（`git commit -F msg -- <files>`），绝不用 `git add -A` / `git add .`。未跟踪文件先 `git add -- <file>` 再 pathspec 提交（否则整次提交会 abort）。
- **绝不用 `git reset` / `git checkout` / `git restore` 去动别的会话改过的文件**：多会话并发时会被误带出/误回退。碰了就立刻 `git add` 原样恢复其状态。改代码前先 `git status` 看清工作区归属。
- 宣称"已提交"之前必须核实落地：`git commit ... | tail` 之后的 `$?` 是 `tail` 的，后台任务通知里的 "exit code 0" 也不能证明提交成功 —— 紧跟 `echo "git rc=$?"` 或复查 `git log -1`。
- push 需手动执行（`scripts/daily_backup.ps1` 是为自动 commit+push 准备的，**未注册任何计划任务**；要启用须用户在场时用脚本注释里的 `schtasks` 命令注册）。

## 工作交接（Handoff）

- 交接文档放 `docs/`，命名 **`handoff-YYYYMMDDNN.md`**（年月日 + 当日两位序号），如 `handoff-2026100801.md`。
- **只留最新一份**：新建下一份时把上一份删掉，不堆归档。历史信息由 git 与台账承载。
- 每份 handoff **必含五节，缺内容写「无」不省略**：① 我们在做什么任务 ② 已经完成了什么 ③ 当前卡在哪 ④ 下一步计划 ⑤ 踩过的坑（绝对不要再踩）。
- 接手第一步：读 `AGENTS.md` → 读最新 handoff → `git log --oneline` 确认 HEAD、`git status` 看工作区。

## 跨机器坑备忘

- git 输出含中文文件名时默认转义成带引号的八进制串，行尾多出的引号会让 `\.md$` 类正则大面积漏计（实测 245 个文件只命中 9 个）。统计/匹配 git 路径一律加 `-c core.quotepath=false`。
- PowerShell 5.1 读无 BOM 的 UTF-8 脚本按 GBK 解码：若文件还是 LF-only，行尾中文的 UTF-8 末字节会把换行吞进非法双字节序列，下一行代码被并入注释**静默失效**。仓库 `.ps1` 一律 UTF-8 BOM + CRLF（`.gitattributes` 已强制），且脚本内容**只用 ASCII**。
- 测试全绿 ≠ 启动路径可用：tests 从项目根 import `app`，而 `start.bat` 直启走另一条解析路径。回归入口：`python app\app.py --import-check`（已入 test_reader 与 pre-commit 链）。
- **`NO_PROXY` 会让 pre-commit 永久假红**：本机系统变量 `NO_PROXY=localhost,127.0.0.1,::1` 使 `curl` 跳过 `test_watch_ci.py` 自建的假代理，两条分支永不触发 → 固定红（实测带它 36/2、去掉 **38/0**）。所以**本仓库每次提交都要 `env -u NO_PROXY -u no_proxy git commit ...`**。这是清理执行环境，不是 `--no-verify` 绕闸。
- **推 GitHub 的可行路线**：直连时通时不通，先探活 `curl.exe -s -o NUL -w "%{http_code}" --proxy http://127.0.0.1:7897 https://github.com/`（应回 200），再 `git -c http.proxy=http://127.0.0.1:7897 -c http.version=HTTP/1.1 push origin main`（`-c` 不落配置）。代理没起来时**别直接下"推不出去"的结论**：清空 proxy 覆盖用一条只读 `git ls-remote` 实测直连，通了就直连推。哪条通要看**这一次**实测，别把上一小时的结论当这一小时的用。
- **判仓库是否真被删除**：`git ls-remote` 必须同时探一个已知公共仓做对照 —— 超时/reset 只代表线路问题，只有服务器实回 `remote: Repository not found` 才算删成；而本机存有凭据助手，**匿名 not-found 也可能只是"私有"**，别拿它当"已删"定论。同理 `git status` 干净、`log --not --remotes` 为空都不能证明远端还在 —— 它比的是本地那份可能已陈旧的 remote-tracking ref。

## 禁区

- 禁止 `git push -f`、禁止改写 main 历史。要改写必须由用户逐次重新授权，且**必须先抽取"只存在于历史里的元数据"**再 `gc`（顺序反了就是不可逆丢失）。
- 禁止把语料衍生物、模型权重、虚拟机运行时提交进 git（`.python/`、`app/rag_models/`、`indexes/`、`site/` 已忽略）。
- 禁止在 `content/` 根目录散放文件；一切新语料走 `_inbox`。
- 不要移除或绕过「写回文件系统」的任何一条路径（api_save / api_note / api_favorite / api_move / api_delete）。
- 不要在没有跑测试的情况下宣称"完成"。
- **不读书库正文、不写任何以真实书库为输入的脚本**：`小说/` `漫画/` 两棵树已彻底退场（归档目录也删了），公开面仍按不变量 10 排除它们。所有测试与自动化的样本一律**合成**（现造在 `tempfile` 里，见 `tests/test_ui_regress.py` 的 `content/ui-r`）。不因"只读不写""本地不外传"而放宽，也**不要再提议**"拿真实书库跑一遍解析器/坏书清单"这类事。
- 批量删除前先立物证：清单 + 校验和 + 可恢复路径（bundle / 副本）确认能还原，再动手；`gitignore` 里的东西要单独判定"是否可再生"，不可再生的未跟踪文件必须一并备份。
