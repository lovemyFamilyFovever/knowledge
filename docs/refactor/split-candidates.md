# baike 拆分候选登记

判定见规范 §6：压到 2200 字会毁掉面试必需信息 **且** 含 ≥3 个可独立命名的子概念 →
本轮不重写、不 rename、不新建子文档，登记于此，等批量收敛后统一拆。

> **本表口径（2026-09-19 归一，规范见 `docs/writing-spec-v1.1.md`）**
> - 路径一律写 `content/baike/<子域>/<文件>.md`（s1/s3 原用子域相对路径、s2/s4/s5 原用 content 相对路径，已统一；每行均已核验文件存在）。
> - 排序：子域字母序，子域内路径字母序。
> - 共 **102** 行，一行一篇待拆长文，无重复。
> - 状态列本轮一律 `pending`（s1 原写 `待拆`，已归一）；二期落地时改 `doing` / `done` / `merged-into: <目标>` / `exempt-reference`（改判为参考手册型、原样保留不再排期拆分，行留在本表作记录）。
> - `子概念预览` 列从各片 split 理由中人工核对提取，仅供拆分时快速定位切口，**不是权威清单**——以 `理由` 列与原文为准。

## 重叠去重队列

拆分或新建词条前**必须先处理这 6 对跨子域重叠**，否则会造出重复词条（同一概念两处定义、双链指向分裂）。
第 1 对已随二期首篇打样执行完毕（见其 ✅ 行）；其余 5 对仍只登记预案、**未执行**，留待各自片轮到拆分时落地。四种预案动词的含义见 `docs/writing-spec-v1.1.md` §8 备注前缀约定。

**1. `programming-languages/软件测试完全指南.md` ↔ `testing/` 子域**（预案：改双链，不新建）
- 冲突：测试金字塔 / TDD·BDD·ATDD / 单元 / 集成 / 性能 六大块，`content/baike/testing/单元测试.md`、`集成测试.md`、`性能测试.md`、`测试驱动开发.md` 已有专文。
- 预案：长文里对应段落**删除并改双链**指向 testing 子域已有专文，不新建同名词条；只有 `E2E 与 Playwright·Cypress` 在 testing 子域无归口，允许独立成篇。
- ✅ 已执行（2026-09-19，二期首篇打样）：父文档原地改写为枢纽页（`s4.md` 登记 `done-hub`，正文 2825/3400），新建 `testing/E2E 测试.md`、`testing/Playwright 与 Cypress.md`，六大块全部改双链未新建。

**2. `software-engineering/03-代码质量.md` ↔ `重构.md` / `技术债务.md` / `代码评审.md`**（预案：改双链，不新建）
- 冲突：重构 / 技术债 / CodeReview 三个子概念，`content/baike/software-engineering/` 同子域已有专文。
- 预案：这三条**不新建**，汇编里删重复定义、改双链；`圈复杂度`、`代码异味`、`CleanCode` 无归口，可各自独立成篇。
- ✅ 已执行（2026-09-19，二期第 2 篇）：父文档原地改写为枢纽页（`s4.md` 登记 `done-hub`，正文 2402/3400），新建 `software-engineering/圈复杂度.md`、`代码异味.md`、`Clean Code 原则.md`；重构/技术债务/代码评审/SOLID 族全部双链不新建。原汇编的「坏味道（Bad Smell）」与「代码异味」是同义重复条，已并入后者、不再单列；`代码规范` 与 `ESLint/Prettier/Black` 无专条可双链，按 v1.1 §1 第三档留在枢纽内联。**未产生 `pending-merge`**：父汇编在同一篇内即收敛，无遗留双归口。

**3. `software-engineering/04-CI CD.md` ↔ `devops/蓝绿部署与灰度发布.md`**（预案：改双链，不新建）
- 冲突：蓝绿 / 金丝雀 / 滚动更新 三种发布策略，`content/baike/devops/蓝绿部署与灰度发布.md` 已重写完成并 PASS。
- ✅ **已执行**（2026-09-19，中小篇专场）：拆 `04-CI CD` 时蓝绿/金丝雀/滚动更新三条已删除并改双链 [[蓝绿部署与灰度发布]]；CI、持续交付、持续部署合成 [[CI 与 CD]]，流水线与三工具合成 [[构建流水线与 CI-CD 工具]]；制品 / 环境 / 特性开关留枢纽内联。
- 预案（原文）：发布策略三条**不新建**，改双链指向 devops 专文；`CI`、`持续交付`、`持续部署`、`流水线`、`制品`、`特性开关` 与 `Jenkins·GitHubActions·GitLabCI` 工具族可独立成篇。

**4. `programming-languages/编译原理与解释器实现.md` ↔ 已重写的编译叶子词条**（预案：改双链，不新建）
- 冲突：词法 / 语法 / AST 三阶段，`content/baike/programming-languages/词法分析.md`、`语法分析.md`、`抽象语法树.md` 已重写完成并 PASS。
- 预案：这三条**不新建**，长文对应段改双链；`语义分析`、`IR 与中间代码`、`代码优化`、`代码生成`、`GC`、`LLVM`、`实战构建语言` 无归口，按阶段独立成篇。

**5. `os/Shell 脚本详解.md` ↔ `os/Shell脚本编程.md`**（预案：合并 + 软删除）
- 冲突：同一子域两篇 Shell 教程，变量 / 条件 / 循环 / 函数 / grep·sed·awk 全面重叠；`Shell脚本编程.md` 已重写 PASS，`Shell 脚本详解.md` 是 8061 字手册式汇编。
- ✅ **已执行**（2026-09-19）：数组/关联数组、字符串参数展开、管道与重定向组合已并入接收方「做法」；原文件 `git mv` 至 `content/_trash/Shell 脚本详解.md`；**并额外重指向 19 篇的入站双链**（预案未提，见 autopilot-log §4.1），否则软删除会造出 22 条悬空链。
- 预案（原文）：**合并**——保留 `content/baike/os/Shell脚本编程.md` 为唯一 Shell 词条，把 `Shell 脚本详解.md` 独有的语法示例（数组、字符串操作、管道与重定向组合）补进去；随后 `Shell 脚本详解.md` 走软删除进 `content/_trash/`（`/api/delete`，禁直接 rm），并在 `docs/refactor/status/s2.md` 该行备注登记 `merged-into: os/Shell脚本编程.md`。

**6. `testing/01 - 测试基础.md` / `testing/02 - 测试工具.md` ↔ 新建的 `E2E 测试.md` / `Playwright 与 Cypress.md`**（预案：改双链，不新建）
- 冲突：拆第 1 对时才暴露——`01 - 测试基础.md` 有 `## 端到端测试（E2E）` 节，`02 - 测试工具.md` 有 `## Cypress`、`## Playwright`、`## Selenium WebDriver` 三节及一张 E2E 工具对比表，而这两篇汇编本身仍是 `split` 状态、未收敛。
- 预案：拆 `01 - 测试基础.md` 时**删除**其 E2E 节、改双链指向 `[[E2E 测试]]`；拆 `02 - 测试工具.md` 时把 Cypress/Playwright 两节合并改双链指向 `[[Playwright 与 Cypress]]`，Selenium 归入该页对比表，E2E 工具对比表（已作为素材并入新词条那张 7 行表）删除。**这两篇汇编拆完前，E2E 主题在库内有两处归口**，双链体检时按新词条为准。

**7. `design-patterns/创建型模式.md` 拆出的 单例/工厂 vs `programming-languages/编程概念音频课-设计模式.md`**（预案：改双链，不新建）
- 冲突：二期拆 `创建型模式` 时新立 [[单例模式]]、[[工厂模式（工厂方法与抽象工厂）]]；而 `编程概念音频课-设计模式.md`（仍 pending）含 `### 1. 单例模式`、`### 2. 工厂模式` 两节（音频课比喻体）。两概念在库内暂有双归口。
- 预案：轮到拆 `编程概念音频课-设计模式.md` 时，**删除**其单例、工厂两节、改双链指向 `[[单例模式]]`、`[[工厂模式（工厂方法与抽象工厂）]]`（该汇编其余模式节另按结构/行为族对齐）。
- 本轮扩展到结构型：二期拆 `结构型模式` 时又新立 [[装饰器模式]]、[[适配器模式]]、[[代理模式]]，同样与该音频课的 `### 5. 装饰器`、`### 6. 适配器`、`### 7. 代理` 三节重叠，一并改双链、不新建。
- 已登记：共五条先行立条已在 `docs/refactor/status/s4.md` 对应新词条行标 `pending-merge: programming-languages/编程概念音频课-设计模式.md`（单例、工厂、装饰器、适配器、代理）；拆该音频课前不得清。

## 待拆清单

| 文件 | 子概念数 | 所属片 | 正文字数 | 子概念预览 | 理由 | 状态 |
|---|---|---|---|---|---|---|
| content/baike/algorithms/复杂度分析.md | 11 | s3 | 5811 | 时间复杂度、空间复杂度、最好最坏平均、均摊、主定理、NP完全、P vs NP、空间换时间、时间换空间、对比表、实战模板 | 概念汇编：时间/空间复杂度/最好最坏平均/均摊/主定理/NP完全/P vs NP/空间换时间/时间换空间/对比表/实战模板 11 块、0 def、11 围栏，远超 3400；NP·P vs NP 属计算理论宜并入[[计算理论]]，其余各复杂度主题各自独立面试必备，压缩必毁；应按主题拆分或收敛为速查枢纽+子词条 | done（2026-09-19 枢纽页 + 5 子词条：时间/空间复杂度、均摊分析、主定理、时空权衡） |
| content/baike/algorithms/排序与搜索.md | 16 | s3 | 7437 | 冒泡、选择、插入、归并、快排、堆排、计数、桶、基数、二分、线性、DFS、BFS、A*、Dijkstra、Floyd | 算法汇编：冒泡/选择/插入/归并/快排/堆排/计数/桶/基数 + 二分/线性/DFS/BFS/A*/Dijkstra/Floyd 共 16 独立算法、0 def、16 围栏，远超上限；其中堆排序/二分/最短路径已有专文应去重，余下每个排序与搜索算法各为面试必备独立词条，压缩必毁；应按算法逐个拆词条，总览对比表留作排序/搜索枢纽 | done（2026-09-19 枢纽页 + 2 子词条：排序算法、查找算法） |
| content/baike/algorithms/算法思想.md | 13 | s3 | 6781 | 分治、DP、贪心、回溯、拓扑、并查集、最短路、MST、双指针、滑动窗口、前缀和、差分数组 | 思想汇编：分治/DP/贪心/回溯/拓扑/并查集/最短路/MST 多数已有专门词条(应去重)，双指针/滑动窗口/前缀和/差分数组 尚无专文且各自独立面试必备；0 def、12 围栏、6781 ≫ 上限，压缩必毁；应把无专文的 4 种技巧各拆词条、已有专文者删除重复段，本文件收敛为"算法思想速查枢纽" | done（2026-09-19 枢纽页 + 2 族词条：双指针与滑动窗口、前缀和与差分） |
| content/baike/architecture/API设计.md | 12 | s5 | — | RESTful、HTTP方法、状态码、命名、分页、GraphQL、gRPC、WebSocket、版本、幂等、HATEOAS、OpenAPI | RESTful/HTTP方法/状态码/命名/分页/GraphQL/gRPC/WebSocket/版本/幂等/HATEOAS/OpenAPI 各含独立示例与对比，压缩至2200必然毁掉面试深度 | done（2026-09-19 枢纽页 + 3 子词条：RESTful API 设计、API 分页与版本控制、OpenAPI 规范） |
| content/baike/architecture/SaaS产品技术架构.md | 6 | s5 | ~9000 | 架构模式、隔离策略、计费、权限、数据隔离、白标 | 架构模式/隔离策略/计费/权限/数据隔离/白标 各含大量代码与独立子话题，压缩毁面试细节 | done（2026-09-19 枢纽页 + 2 子词条：SaaS 多租户架构与数据隔离〔合并架构模式+隔离策略+数据隔离〕、SaaS 计费系统设计；权限双链[[访问控制]]不新建、白标原稿截断按 v1.2 §5 内联）|
| content/baike/architecture/云原生与多云架构实战指南.md | 8+ | s5 | ~4000+ | 容器、K8s、服务网格、多云、CI-CD、GitOps、Serverless、可观测 | 容器/K8s/服务网格/多云/CI-CD/GitOps/Serverless/可观测 多独立子话题 | done（2026-09-19 枢纽页 + 1 子词条：云原生十二要素；服务模型双链[[云服务详解]]、容器/K8s/网格/CI-CD/IaC/可观测 全双链既有专条不新建、多云一节原稿截断按 v1.2 §5 内联）|
| content/baike/architecture/分布式系统设计完全指南.md | 8+ | s5 | ~4000+ | 一致性、共识、分布式事务、分片、复制、领导者选举 | 一致性/共识/分布式事务/分片/复制/领导者选举等独立子话题 | pending |
| content/baike/architecture/可观测性工程实战.md | 5+ | s5 | ~4000+ | 日志、指标、链路追踪、APM、告警 | 日志/指标/链路追踪/APM/告警 各独立实践体系 | pending |
| content/baike/architecture/微服务架构设计与实践.md | 8+ | s5 | ~5000+ | 服务拆分、网关、通信、容错、数据一致性、部署、监控 | 服务拆分/网关/通信/容错/数据一致性/部署/监控 各独立话题 | done（2026-09-19 巨型专场第 1 篇：枢纽页 + 3 子词条） |
| content/baike/architecture/性能优化.md | 14 | s5 | ~1500+ | 缓存、CDN、负载均衡、连接池、异步、限流、熔断、降级 | 缓存/CDN/负载均衡/连接池/异步/限流/熔断/降级等14个独立手段 | done（2026-09-19 枢纽页 + 1 子词条：异步处理与线程池；CDN 双链 [[内容分发网络]]） |
| content/baike/architecture/推荐系统设计与实现.md | 6+ | s5 | ~3500+ | 召回、排序、特征工程、AB测试、冷启动、实时性 | 召回/排序/特征工程/AB测试/冷启动/实时性 各独立子系统 | pending |
| content/baike/architecture/数据工程完全指南.md | 6+ | s5 | ~4000+ | ETL、数仓、数据湖、流处理、数据质量、治理 | ETL/数仓/数据湖/流处理/数据质量/治理 各独立领域 | pending |
| content/baike/architecture/架构模式.md | 12 | s5 | ~1200+ | 单体、微服务、Serverless、EDA、CQRS、六边形、洋葱 | 单体/微服务/Serverless/EDA/CQRS/六边形/洋葱等12种独立模式 | pending |
| content/baike/architecture/系统设计.md | 12 | s5 | ~1500+ | CAP、BASE、一致性、分布式ID、分片、读写分离 | CAP/BASE/一致性/分布式ID/分片/读写分离等12个独立话题 | done（2026-09-19 枢纽页 + 1 子词条：数据分片与热点处理） |
| content/baike/architecture/设计原则.md | 12 | s5 | ~1800+ | SOLID、DRY、KISS、YAGNI、迪米特、组合、接口、IoC、DI | SOLID/DRY/KISS/YAGNI/迪米特/组合/接口/IoC/DI等12个独立原则 | pending |
| content/baike/architecture/领域驱动设计DDD完全指南.md | 10 | s5 | ~2500+ | 核心思想、战略设计、战术设计、分层、事件风暴、CQRS、ES、微服务、实战、误区 | 核心思想/战略设计/战术设计/分层/事件风暴/CQRS/ES/微服务/实战/误区 10部分 | pending |
| content/baike/data-science/数据分析与可视化实战.md | 3 | s3 | 17377 | Python工具链、数据清洗实战、EDA方法论 | 实战手册：Python工具链/数据清洗实战/EDA方法论 3 大主题、0 def 卡、8 围栏 784 代码行，远超上限。概念词条已由"数据分析与可视化"承载，本文是代码级实操详解，压入 3400 必毁实操细节；应拆为三篇实操子文档或并入 ETL/EDA 专题 | done（2026-09-19 枢纽页 + 3 子词条：Python 数据分析工具链、数据清洗实战、探索性数据分析） |
| content/baike/database/MySQL从入门到架构师.md | 5 | s3 | 11081 | 存储引擎、索引优化、MVCC、锁、查询优化 | 全书式枢纽：存储引擎/索引优化/MVCC/锁/查询优化 5 个独立子概念，正文 11081 字、42 个代码块，压到 3400 仍毁掉面试级细节；与 MySQL深入 / 索引与查询优化术语 / 事务与并发控制术语 等专文高度重叠，宜拆为子文档 | done（2026-09-19 枢纽页 + 3 子词条：InnoDB 存储引擎结构、MySQL 索引类型与优化、MySQL 锁机制；MVCC/隔离/B+树双链既有专条） |
| content/baike/database/NoSQL 数据库术语.md | 10 | s3 | 8568 | Redis、MongoDB、ES、Memcached、HBase、Neo4j、InfluxDB、Cassandra、PynamoDB、NoSQL-vs-SQL | 全景文件实为 10 个独立词条（各库自带 def 卡、11 围栏、8568 字），无法并入单条 3400 上限。Redis/MongoDB/ES 已有专文应删除本文重复段；Memcached/HBase/Neo4j/InfluxDB/Cassandra/PynamoDB 各自拆为独立词条，NoSQL-vs-SQL 保留为选型枢纽并索引各子文档 | pending |
| content/baike/database/Redis深度解析与实战指南.md | 8 | s3 | 13550 | 数据结构、底层实现、内存管理、持久化、主从、Sentinel、Cluster、分布式锁 | 书级实战指南：数据结构/底层实现/内存管理/持久化/主从/Sentinel/Cluster/分布式锁 8 大独立主题、56 个代码块、0 卡片，远超 3400 上限；速览已由 Redis深入 承载，本文件应按 8 主题各拆独立词条（含 Redlock、淘汰策略等面试必备细节，压缩必毁） | pending |
| content/baike/database/SQL 基础术语.md | 12 | s3 | 8536 | DDL、DML、DCL、DQL、TCL、SELECT执行顺序、JOIN、子查询、UNION、GROUP BY-HAVING、窗口函数、CTE | 术语汇编实为 12 个独立词条(各带 def+示例、12 围栏、0 trap)：DDL/DML/DCL/DQL/TCL 可合并为一篇"SQL 语言分类"，SELECT 执行顺序/JOIN/子查询/UNION/GROUP BY-HAVING/窗口函数/CTE 各自独立且面试必备，压到 3400 必毁；窗口/CTE 与 PostgreSQL 篇重叠需去重 | pending |
| content/baike/database/事务与并发控制术语.md | 12 | s3 | 9037 | 事务、ACID、隔离级别、脏读、不可重复读、幻读、MVCC、乐观锁、悲观锁、死锁、Redo Log、Undo Log | 术语汇编实为 12 个独立词条(各带 def+示例、12 围栏、0 trap)：事务/ACID/隔离级别/脏读/不可重复读/幻读/MVCC/乐观锁/悲观锁/死锁/Redo Log/Undo Log。隔离级别·MVCC·死锁 已有专文应去重；ACID、三类并发读异常、乐观/悲观锁、Redo/Undo 各为面试必备独立词条，压入 3400 必毁 | pending |
| content/baike/database/搜索引擎技术详解.md | 6 | s3 | 17928 | 架构、爬虫设计、倒排索引、分词、查询解析、相关性排序 | 搜索引擎全书：架构/爬虫设计/倒排索引/分词/查询解析/相关性排序 6 大主题、0 def 卡、19 围栏 922 内行(爬虫章节尤长)，远超上限。爬虫/分词/TF-IDF·BM25 排序等多为本文独有深度内容、无对应专文，压入 3400 必毁；应按 6 主题各拆词条，通用原理留作搜索枢纽并链接 ElasticSearch搜索/向量数据库技术 | pending |
| content/baike/database/数据库内核原理深度解析.md | 8 | s3 | 11136 | 存储引擎、索引、查询优化器、事务、并发控制、日志恢复、分布式、实战对比 | 内核原理全书：存储引擎/索引/查询优化器/事务/并发控制/日志恢复/分布式/实战对比 8 大主题、35 节、0 def 卡。含 CBO、ARIES、列存、TSO/OCC/2PC、InnoDB·PG·TiDB 对比等本文独有的深度子题，多数无对应专文，压到 3400 必毁面试级内核细节；应按主题拆分，末尾对比表可留作内核枢纽 | pending |
| content/baike/database/数据库设计术语.md | 15 | s3 | 10034 | 主键、外键、候选键、超键、1NF、2NF、3NF、BCNF | 术语汇编实为 15 个独立词条(各带 def+示例、17 围栏、0 trap)，无法并入单条上限；应按术语各拆独立词条，并与 数据库范式/数据库设计 相关专文去重后统一收敛 | pending |
| content/baike/database/索引与查询优化术语.md | 12 | s3 | 9066 | 聚簇、非聚簇、B+树、哈希、全文、联合、覆盖索引、最左前缀、ICP、EXPLAIN、慢查询优化、索引失效场景 | 术语汇编实为 12 个独立词条(各带 def+示例、13 围栏、0 trap)：聚簇/非聚簇/B+树/哈希/全文/联合/覆盖索引、最左前缀、ICP、EXPLAIN、慢查询优化、索引失效场景，均面试必备且各自独立，压入 3400 必毁；应各拆词条，B+树索引段与 B+树 专文去重 | pending |
| content/baike/design-patterns/创建型模式（Creational Patterns）.md | 6 | s4 | 14432 | 单例、工厂方法、抽象工厂、建造者、原型、对象池 | 枢纽长文覆盖单例/工厂方法/抽象工厂/建造者/原型/对象池 6 个可独立命名子模式，各带代码示例与深浅拷贝、DCL+volatile、OCP 权衡等面试细节；正文 14432 字 ≫ 枢纽预算 3400、围栏 12 块 239 行 ≫ 上限 2/20，压缩至合规会毁掉逐模式机制 → 建议拆为 6 词条+1 枢纽 | done（2026-09-19 二期拆分：枢纽页 + 5 子词条〔单例 / 工厂方法与抽象工厂 / 建造者 / 原型 / 对象池〕，工厂合并为族词条；见去重队列第 7 对） |
| content/baike/design-patterns/结构型模式（Structural Patterns）.md | 10 | s4 | 16104 | 适配器、桥接、组合、装饰器、外观、享元、代理、过滤器、MVC、MVVM | 枢纽长文覆盖适配器/桥接/组合/装饰器/外观/享元/代理 7 种 GoF + 过滤器/MVC/MVVM，共 10 个可独立命名子概念，各带代码与对比表；正文 16104 字 ≫ 3400、围栏 15 块 311 行 ≫ 2/20，压缩会毁掉逐模式细节 → 建议拆为多词条+1 枢纽 | done（2026-09-19 二期拆分：枢纽页 + 8 子词条〔适配器/桥接/组合/装饰器/外观/享元/代理 + MVC与MVVM 族〕，过滤器留枢纽内联；见去重队列第 7 对） |
| content/baike/design-patterns/行为型模式（Behavioral Patterns）.md | 11 | s4 | 16222 | 策略、观察者、命令、状态、模板方法、迭代器、责任链、中介者、备忘录、访问者、解释器 | 枢纽长文覆盖策略/观察者/命令/状态/模板方法/迭代器/责任链/中介者/备忘录/访问者/解释器 11 种 GoF 行为型模式，各带代码与对比表；正文 16222 字 ≫ 3400、围栏 13 块 361 行 ≫ 2/20，压缩会毁掉逐模式细节 → 建议拆为 11 词条+1 枢纽 | pending |
| content/baike/developer-skills/开发者效率工具大全.md | 4 | s4 | 16942 | 终端工具、编辑器与IDE、Git高级用法、命令行工具 | 目录型枢纽：终端工具/编辑器与IDE/Git高级用法/命令行工具 4 个可独立命名工具族，逐工具展开；正文 16942 字 ≫ 3400、围栏 28 块 880 行 ≫ 2/20，压缩会毁掉逐工具细节 → 建议按工具族拆词条 | pending |
| content/baike/developer-skills/敏捷项目管理实战.md | 10 | s4 | 13106 | 敏捷宣言、Scrum、看板、用户故事、估算、迭代管理、需求管理、技术实践、规模化敏捷、远程敏捷 | 全书式枢纽：敏捷宣言/Scrum/看板/用户故事/估算/迭代管理/需求管理/技术实践/规模化敏捷/远程敏捷 10 个独立子话题，各带流程与示例；正文 13106 字 ≫ 3400、围栏 28 块 567 行 ≫ 2/20 → 建议按方法论拆词条+1 枢纽 | pending |
| content/baike/devops/API设计最佳实践.md | 5 | s4 | 14388 | RESTful原则、版本管理、认证授权(OAuth四步)、错误处理、分页过滤排序 | RESTful原则/版本管理/认证授权(OAuth四步)/错误处理/分页过滤排序 各独立话题带示例；正文 14388 ≫ 3400、围栏 35 块 647 行 ≫ 2/20 → 建议按话题拆词条 | pending |
| content/baike/devops/Docker容器化完全指南.md | 8 | s4 | 16568 | 容器vsVM、镜像构建、网络、数据、Compose、安全、Harbor、日志 | 容器vsVM/镜像构建/网络/数据/Compose/安全/Harbor/日志 8 独立话题；正文 16568、围栏 48 块 957 行 ≫ 上限 → 建议拆词条+1 枢纽 | pending |
| content/baike/devops/Kubernetes云原生实战指南.md | 3 | s4 | 6644 | 容器基础、K8s核心概念、网络模型 | 容器基础/K8s核心概念/网络模型 3 大独立块，正文 6644 字、代码 416 行 ≫ 3400/20；与 Kubernetes深入 有重叠 → 拆块并按需与深入去重 | pending |
| content/baike/devops/Linux系统管理高级指南.md | 10 | s4 | 12784 | 内核、进程、内存、文件系统、网络、性能、Shell、systemd、安全、容器运行时 | 内核/进程/内存/文件系统/网络/性能/Shell/systemd/安全/容器运行时 10 独立话题；围栏 36 块 → 建议按主题拆词条 | pending |
| content/baike/devops/Web安全攻防实战指南.md | 13 | s4 | 13296 | OWASP Top10 十项、经典攻防详解 | OWASP Top10 各项 + 经典攻防详解共 13 个独立话题（枢纽信号①对比表10行②子概念26）；正文 13296 ≫ 3400 → 建议按漏洞/攻防各拆词条 | pending |
| content/baike/devops/操作系统内核原理.md | 9 | s4 | 13534 | 进程、线程、内存、文件系统、IO、系统调用与中断、设备驱动、容器隔离(Namespace+Cgroups)、安全 | 进程/线程/内存/文件系统/IO/系统调用与中断/设备驱动/容器隔离(Namespace+Cgroups)/安全 9 独立子系统；围栏 14 → 建议按子系统拆词条 | pending |
| content/baike/devops/网络安全与渗透测试.md | 5 | s4 | 17171 | 网络协议安全、Web渗透方法论、常见漏洞实战、内网渗透、安全工具链 | 网络协议安全/Web渗透方法论/常见漏洞实战/内网渗透/安全工具链 5 大部分各成体系；正文 17171、围栏 29 块 752 行 ≫ 上限 → 建议按部分拆词条 | pending |
| content/baike/distributed/分布式ID与缓存术语百科.md | 8 | s2 | 12066 | ID方案、穿透、雪崩、击穿、缓存一致性、多级缓存、热点数据、冷热分离 | 8 个可独立命名子概念（ID方案/穿透/雪崩/击穿/缓存一致性/多级缓存/热点数据/冷热分离），各带 Java 代码与对比表；正文 12066 字 ≫ 3400、围栏 11 块 ≫ 2/20，且为 baike B 多定义结构（8 张 def 卡）不符单词条契约 → 建议按子概念拆词条，穿透/击穿/雪崩/缓存一致性等宜各自成篇 | done（2026-09-19 枢纽页 + 2 子词条：缓存三大问题、缓存双写一致性；ID/一致性哈希/分布式缓存/读写姿势均双链已有专条，多级缓存/热点/冷热归口 web-backend·architecture 不重复立条） |
| content/baike/distributed/分布式存储术语百科.md | 8 | s2 | 4308 | 分片、副本、Raft、Paxos、ZAB、Gossip、一致性模型谱系、Quorum | baike B 多定义（分片/副本/Raft/Paxos/ZAB/Gossip/一致性模型谱系/Quorum）；正文 4308 字 ≫ 3400、围栏 4 块 ≫ 2/20。Raft/Paxos/ZAB 已由 [[一致性算法]] 承载可删，但数据分片/副本/一致性模型谱系(线性·顺序·因果)/Quorum(NWR)/Gossip 是面试必需且无对应子词条，压缩至合规会毁掉这些表与追问级细节 → 建议拆为分片/副本/一致性模型/Quorum/Gossip 等词条 | done（2026-09-19 枢纽页 + 2 子词条：数据复制与 Quorum、Gossip 协议） |
| content/baike/distributed/微服务治理术语百科.md | 10 | s2 | 7925 | 注册发现、负载均衡、熔断、限流、降级、链路追踪、配置中心、API网关、服务网格、灰度发布 | baike B 多定义（注册发现/负载均衡/熔断/限流/降级/链路追踪/配置中心/API网关/服务网格/灰度发布）；正文 7925 字 ≫ 3400、围栏 12 块 ≫ 2/20。负载均衡/服务网格/熔断与降级/限流/服务发现已有专文，但链路追踪/配置中心/API网关/灰度发布含 @FeignClient·Resilience4j·Gateway·Nacos·金丝雀等唯一代码与对比表，压缩必毁 → 建议按治理主题各拆词条 | done（2026-09-19 枢纽页 + 3 子词条：配置中心、API网关、灰度发布；服务发现/负载均衡/熔断与降级/限流/服务网格 双链已有专条，链路追踪双链 architecture/可观测性工程实战） |
| content/baike/frontend-concepts/HTML & CSS 核心概念.md | 14 | s5 | ~3000+ | HTML语义化标签、CSS盒模型、box-sizing、Flexbox、CSS Grid、响应式设计、BFC、选择器优先级 | 14个独立HTML/CSS概念各带代码，压缩毁面试细节 | pending |
| content/baike/frontend-concepts/JavaScript 基础核心概念.md | 17 | s5 | ~4000+ | var·let·const、闭包、原型链、事件循环与任务队列、Promise、async·await、Generator、作用域与作用域链 | 17个独立JS概念各带示例 | pending |
| content/baike/frontend-concepts/前端工程化核心概念.md | 14 | s5 | ~4000+ | Webpack、Vite、Babel、ESLint、TypeScript、npm·yarn·pnpm、Monorepo、PostCSS | 14个独立工程化概念 | pending |
| content/baike/frontend-concepts/前端框架核心概念.md | 12 | s5 | ~3500+ | React、JSX、Hooks、Vue、响应式原理、Composition API、Angular、依赖注入 | 12个独立框架概念 | pending |
| content/baike/frontend-frameworks/GraphQL从入门到精通.md | 10+ | s5 | ~5000+ | Schema、查询、变更、订阅、解析器、缓存、安全 | Schema/查询/变更/订阅/解析器/缓存/安全等独立话题 | pending |
| content/baike/frontend-frameworks/Next.js全栈开发实战.md | 10+ | s5 | ~5000+ | 路由、SSR、SSG、API Routes、Middleware、部署 | 路由/SSR/SSG/API Routes/Middleware/部署等独立话题 | pending |
| content/baike/frontend-frameworks/WebAssembly完全指南.md | 8+ | s5 | ~4000+ | 编译、内存模型、JS互操作、SIMD、线程 | 编译/内存模型/JS互操作/SIMD/线程等独立话题 | pending |
| content/baike/frontend-frameworks/现代前端工程化完全指南.md | 10+ | s5 | ~5000+ | 构建工具、模块、包管理、CI-CD、测试 | 构建工具/模块/包管理/CI-CD/测试等独立话题 | pending |
| content/baike/machine-learning/AI是否会取代人类辩论.md | 约4组独立子论(正方论据体系/反方论据体系/案例数据/哲学概念) | s1 | >5000(264行) | 正方论据体系、反方论据体系、案例数据、哲学概念 | 本质是一场六人模拟辩论长文，非单一面试术语；含大量可核验引用(麦肯锡2017/高盛2023/OpenAI2023/DeepMind Nature2020/IBM Watson等)，压到2200会毁掉论据链；≥3独立子块→建议按"正方论/反方论/关键数据案例"拆分 | done（2026-09-19 枢纽页 + 3 子词条：AI 取代就业的正反论据、AI 就业影响的实证数据、AI 与人类独特性的哲学概念） |
| content/baike/machine-learning/LLM应用开发完全指南.md | 约7章独立子块(架构演进/Tokenization/MoE/Prompt/FunctionCalling/RAG/Agent) | s1 | 约1000+行(被截断) | 架构演进、Tokenization、MoE、Prompt、FunctionCalling、RAG、Agent | 多章实战教程、含十余段大段代码与2026前瞻技术(FlashAttention-3/RoPE2.0等)，非单一术语卡片；压到2200会毁掉动手细节；且原文明显未写完→建议按章拆分为独立教程/词条 | done（2026-09-19 枢纽页，0 子词条：各章概念均归口已有专条→双链不重复建；实现级 RAG/提示细节留待 RAG系统工程化实践 / Prompt Engineering高级指南 各自收敛，2026 前瞻伪代码不作事实建条） |
| content/baike/machine-learning/MLOps机器学习工程化.md | 约5块独立子主题(成熟度0-1-2/CI-CD-CT自动化/实验管理MLflow·W&B/监控漂移/测试套件) | s1 | 约970行 | 成熟度0-1-2、CI-CD-CT自动化、实验管理MLflow·W&B、监控漂移、测试套件 | 工程实战教程、十余段大段代码(Mlflow/W&B/GH Actions yaml/pytest/监控)，非单一术语卡片；压缩会毁掉可复现实现；建议按主题拆成教程子文档 | pending |
| content/baike/machine-learning/Prompt Engineering高级指南.md | 约8块独立how-to(提示结构四要素/样本策略/CoT·SC·ToT/ReAct/结构化输出/注入防御/自动优化APE·OPRO/模板版本管理·各模型差异·50模板) | s1 | 约363行 | 提示结构四要素、样本策略、CoT·SC·ToT、ReAct、结构化输出、注入防御、自动优化APE·OPRO、模板版本管理 | 深度方法论长指南、非单一术语卡；多数小节(APE/OPRO/模板管理/各模型最佳实践)无专条归口、压缩会毁掉实操信息；建议按主题拆分或并入 ai-and-llm 提示工程枢纽后再拆 | pending |
| content/baike/machine-learning/RAG系统工程化实践.md | 约6块独立工程实现(Naive/Advanced/Modular/Agentic RAG/多格式解析/chunking四策略/Embedding选型微调对比/向量库Milvus·Qdrant·Chroma实战) | s1 | 约1090行(截断) | Naive·Advanced·Modular·Agentic RAG、多格式解析、chunking四策略、Embedding选型微调、向量库Milvus·Qdrant·Chroma | 深度工程化教程、~16段大代码、非单一术语卡；压缩毁掉可复现实现；与[[RAG 检索增强生成]][[向量数据库技术]]部分概念重叠但本篇是实现级；建议按实现主题拆分教程 | pending |
| content/baike/machine-learning/《AI时代生存指南》第三章.md | 约6块独立子主题(AI工具全景五类/工作效率场景/学新技能方法论/AI创业全流程/五大核心能力/终身学习系统) | s1 | 约557行 | AI工具全景五类、工作效率场景、学新技能方法论、AI创业全流程、五大核心能力、终身学习系统 | 面向普通人的 AI 实用指南/工具目录长文、非单一术语卡；大量具体工具清单与操作流程无归口、压缩会毁掉可操作价值；建议按"工具全景/提效/学习/创业/核心能力"拆分 | pending |
| content/baike/machine-learning/强化学习从入门到实践.md | ≥5章(RL概念/MDP/值函数贝尔曼/Q-Learning/…实战) | s1 | 926行·30围栏 | RL概念、MDP、值函数贝尔曼、Q-Learning、实战 | 多章实战教程、大量代码，与[[强化学习基础]][[深度强化学习]]概念重叠但本篇是实现级；压缩毁掉动手细节；建议按章拆分 | pending |
| content/baike/machine-learning/深度学习从零到精通.md | ≥2大部分(神经网络基础/CNN)·多小节 | s1 | 922行·20围栏 | 神经网络基础、卷积神经网络CNN（含反向传播、激活函数、梯度消失等多小节） | 从零到精通实战教程、大量代码，非单一术语卡；建议按神经网络/CNN等主题拆 | pending |
| content/baike/machine-learning/自然语言处理NLP完全指南.md | ≥6章(预处理/词向量/语言模型演进/文本分类/序列标注/机器翻译) | s1 | 947行·30围栏 | 预处理、词向量、语言模型演进、文本分类、序列标注、机器翻译 | NLP 实战教程、多章大量代码；词向量/语言模型等与 ai-and-llm 专条重叠但本篇实现级；建议按任务主题拆分 | pending |
| content/baike/machine-learning/计算机视觉入门到实战.md | ≥9章(图像基础/经典CV/CNN演进/目标检测/分割/生成/OCR/人脸/视频) | s1 | 585行·22围栏 | 图像基础、经典CV、CNN演进、目标检测、分割、生成、OCR、人脸、视频 | CV 入门到实战教程、九个子领域各成体系、含代码；单卡压缩必毁掉内容；建议按子任务拆成独立词条 | pending |
| content/baike/middleware/任务调度（Task Scheduling）.md | 10 | s3 | 6216 | 分布式任务调度概念、XXL-JOB、Elastic-JOB、SchedulerX、延迟队列、优先级队列、分布式定时任务、Crontab、DAG任务编排、监控告警 | 汇编 10 个独立主题：分布式任务调度概念/XXL-JOB/Elastic-JOB/SchedulerX(阿里云) 三大调度框架 + 延迟队列/优先级队列/分布式定时任务/Crontab 表达式/DAG 任务编排/监控告警；0 def、12 围栏、6216 ≫ 上限。各调度框架与队列/编排子题为面试必备独立词条，压入 3400 必毁；应各拆词条，本文件收敛为任务调度枢纽+选型索引 | pending |
| content/baike/network/HTTP协议.md | 13 | s2 | 7815 | 方法、状态码、头部、缓存、keep-alive、分块、CORS | baike B 多定义汇编（方法/状态码/头部/缓存/keep-alive/分块/CORS 各带 def+代码）；正文 7815 ≫ 3400、围栏 13 ≫ 2/20，且与 HTTP 状态码 等专文重叠；压缩必毁逐主题细节 → 建议按主题拆词条 | done（2026-09-19 枢纽页 + 3 子词条：HTTP请求方法、HTTP头部与内容协商、Cookie与Session；状态码/缓存/TLS/WebSocket/HTTP3 分别双链 HTTP 状态码·缓存策略·HTTPS 与 TLS·WebSocket·QUIC） |
| content/baike/network/TCP深入.md | 12 | s2 | 8090 | 三次握手、四次挥手、滑动窗口、拥塞控制、超时重传、Nagle | baike B 多定义（三次握手/四次挥手/滑动窗口/拥塞控制/超时重传/Nagle 各带 def+代码）；8090 ≫ 3400、14 围栏 ≫ 2/20，且与三次握手与四次挥手/滑动窗口/拥塞控制 专文重叠 → 建议去重后按机制拆词条 | pending |
| content/baike/network/应用层协议.md | 13 | s2 | 9411 | HTTP、DNS、SMTP、FTP、SSH、DHCP | baike B 多定义（HTTP/DNS/SMTP/FTP/SSH/DHCP 各协议带 def+报文示例）；9411 ≫ 3400、12 围栏 ≫ 2/20 → 建议按协议各拆词条 | pending |
| content/baike/network/网络基础.md | 14 | s2 | 8389 | OSI、TCP-IP、以太网、IP、MAC、子网、CIDR、VLAN | baike B 多定义（OSI/TCP-IP/以太网/IP/MAC/子网/CIDR/VLAN 各带 def）；8389 ≫ 3400、14 围栏 ≫ 2/20，且与 OSI 参考模型/IP 协议 等专文重叠 → 建议去重后按主题拆词条 | pending |
| content/baike/network/网络安全协议.md | 11 | s2 | 9247 | 防火墙、IDS-IPS、VPN、IPsec、TLS、DDoS、WAF | baike B 多定义（防火墙/IDS-IPS/VPN/IPsec/TLS/DDoS/WAF 各带 def+示例）；9247 ≫ 3400、11 围栏 ≫ 2/20 → 建议按主题各拆词条 | pending |
| content/baike/os/Linux 命令速查手册.md | 20+ | s2 | 4504 | ls、cd、mkdir、cp·mv·rm、cat·less、grep、find、sed、awk、chmod、ps·top、df·du、netstat、tar | 命令型速查手册：ls/cd/mkdir/cp·mv·rm/cat·less/grep/find/sed/awk/chmod/ps·top/df·du/netstat/tar 等按命令分组，每组带独立示例围栏；无 `## 定义`、15 围栏 ≫ 2/20，压缩会毁掉逐命令用法示例（这是手册的核心价值）→ 建议保留为速查参考或按命令族拆词条 | exempt-reference（已改判，见 `docs/refactor/exempt-reference.md`） |
| content/baike/os/Shell 脚本详解.md | 8+ | s2 | 8061 | 变量、条件if·case、循环for·while·until、函数、数组、字符串操作、正则grep·sed·awk、管道与重定向 | 教程/手册式汇编：变量/条件 if·case/循环 for·while·until/函数/grep·sed·awk 等多块各带大量代码，无 `## 定义` 单词条结构、正文 8061 ≫ 3400、15 围栏 ≫ 2/20，压缩必毁逐语法示例；与 Shell脚本编程 词条重叠需去重 → 建议按语法主题拆词条 | done（2026-09-19 合并 + 软删除，见去重队列第 5 对） |
| content/baike/os/进程管理详解.md | 12+ | s2 | 6581 | ps、top·htop、kill、nohup、systemd、cron、nice、/proc、dmesg、journalctl、systemctl | 命令+概念混合详解：ps/top·htop/kill/nohup/systemd/cron/nice//proc/dmesg/journalctl/systemctl 等 11+ 子块各带 def 与代码，17 围栏 ≫ 2/20、6581 ≫ 3400，压缩会毁掉逐命令实战细节；与 Linux命令速查手册 重叠 → 建议拆命令词条+进程管理枢纽 | pending |
| content/baike/programming-languages/Flutter跨平台开发实战.md | 5 | s4 | 22743 | Dart精要、Widget体系、布局、路由GoRouter、状态管理 | Dart精要/Widget体系/布局/路由GoRouter/状态管理 各独立且带大量代码；正文 22743、围栏 14 块 1284 行 ≫ 上限 → 按主题拆词条 | pending |
| content/baike/programming-languages/Go语言系统编程指南.md | 5 | s4 | 18340 | 并发模型、内存模型happens-before、隐式接口、反射、unsafe | 并发模型/内存模型 happens-before/隐式接口/反射/unsafe 各独立话题；正文 18340、1187 代码行 → 拆词条 | pending |
| content/baike/programming-languages/Python全栈开发教程.md | 5 | s4 | 23070 | Python基础、FastAPI、SQLAlchemy、PostgreSQL、React | Python基础/FastAPI/SQLAlchemy/PostgreSQL/React 全栈五大块，各为独立体系；正文 23070、1166 代码行 → 拆子文档 | pending |
| content/baike/programming-languages/Python高级编程完全指南.md | 4 | s4 | 21427 | 装饰器高级、元类、描述符协议、上下文管理器 | 装饰器高级/元类/描述符协议/上下文管理器 各独立带大量代码；正文 21427、1075 代码行 → 拆词条 | pending |
| content/baike/programming-languages/React Native移动应用开发.md | 6 | s4 | 21874 | RN新架构、核心组件布局、导航、状态管理、网络缓存、原生桥接 | RN新架构/核心组件布局/导航/状态管理/网络缓存/原生桥接 各独立；正文 21874、14 围栏 1122 行 ≫ 上限 → 拆词条 | pending |
| content/baike/programming-languages/Rust Web开发实战.md | 6 | s4 | 20339 | Web生态概览、Axum、数据库集成、serde、认证授权、tokio | Web生态概览/Axum/数据库集成/serde/认证授权/tokio 六部分各独立；正文 20339、32 围栏 959 行 → 拆词条 | pending |
| content/baike/programming-languages/Rust系统编程入门到精通.md | 7 | s4 | 17989 | 所有权、Trait泛型、错误处理、智能指针、并发、异步、Unsafe | 所有权/Trait泛型/错误处理/智能指针/并发/异步/Unsafe 7 大独立主题；正文 17989、24 围栏 1121 行 → 按主题拆词条 | pending |
| content/baike/programming-languages/TypeScript高级编程指南.md | 8 | s4 | 22260 | 类型系统、泛型、类型体操、装饰器、模块、.d.ts、编译器API、框架集成 | 类型系统/泛型/类型体操/装饰器/模块/.d.ts/编译器API/框架集成 8 独立话题；正文 22260、33 围栏 → 拆词条 | pending |
| content/baike/programming-languages/函数式编程完全指南.md | 10 | s4 | 18943 | FP概念、高阶函数、闭包柯里化、Functor·Monad、Either·Option·IO、不可变、并发、JS·Haskell实践 | FP概念/高阶函数/闭包柯里化/Functor·Monad/Either·Option·IO/不可变/并发/JS·Haskell 实践 10 话题；正文 18943、24 围栏 → 拆词条 | pending |
| content/baike/programming-languages/函数式编程（Functional Programming）概念.md | 14 | s4 | 11638 | 纯函数、副作用、不可变、高阶函数、Lambda、闭包、柯里化、组合、Monad、Functor、Applicative、声明式、惰性求值 | 纯函数/副作用/不可变/高阶函数/Lambda/闭包/柯里化/组合/Monad/Functor/Applicative/声明式/惰性求值 14 词条（14 def）；29 围栏 ≫ 2/20 → 按概念各拆词条 | pending |
| content/baike/programming-languages/密码学与区块链技术指南.md | 6 | s4 | 16609 | 密码学基础、加密算法、密钥管理、TLS·SSL、区块链原理、比特币 | 密码学基础/加密算法/密钥管理/TLS·SSL/区块链原理/比特币 6 大部分各成体系；正文 16609、10 围栏 584 行 → 拆词条 | pending |
| content/baike/programming-languages/并发编程模式与实践.md | 8 | s4 | 17776 | 并发vs并行、线程模型、互斥同步、无锁、并发数据结构、协程、Channel·CSP、Actor | 并发vs并行/线程模型/互斥同步/无锁/并发数据结构/协程/Channel·CSP/Actor（枢纽①mermaid②子概念20）；正文 17776、1071 代码行 ≫ 3400 → 拆词条 | pending |
| content/baike/programming-languages/并发编程（Concurrent Programming）概念.md | 14 | s4 | 17338 | 并发vs并行、线程vs进程、锁Mutex、读写锁、信号量、条件变量、死锁、原子、CAS、线程池、协程、消息传递、Future·Promise、事件循环 | 并发vs并行/线程vs进程/锁Mutex/读写锁/信号量/条件变量/死锁/原子/CAS/线程池/协程/消息传递/Future·Promise/事件循环 14 词条（14 def）；40 围栏 ≫ 2/20 → 按概念各拆词条 | pending |
| content/baike/programming-languages/程序员的数学基础.md | 6 | s4 | 19326 | 集合论、图论、组合数学、逻辑、向量、矩阵、特征值与SVD | 离散数学/线性代数/…多个独立数学分支章节；正文 19326、7 围栏 966 行 ≫ 上限 → 按分支拆词条 | pending |
| content/baike/programming-languages/编程概念音频课-数据结构.md | 6 | s4 | 8957 | 数组链表、栈队列、哈希表、树二叉树、图、堆 | 数组链表/栈队列/哈希表/树二叉树/图/堆 6 站各独立数据结构主题；正文 8957、8 围栏 178 行 → 按结构拆词条 | pending |
| content/baike/programming-languages/编程概念音频课-设计模式.md | 8 | s4 | 10591 | 单例、工厂、观察者、策略、装饰器、适配器、代理、模板方法 | 单例/工厂/观察者/策略/装饰器/适配器/代理/模板方法 8 模式各独立；正文 10591、8 围栏 328 行 → 按模式拆词条 | pending |
| content/baike/programming-languages/编程语言通用概念.md | 11 | s4 | 7301 | 变量、常量、基本类型、引用值类型、运算符、控制流、循环、函数、递归、作用域、命名 | 变量/常量/基本类型/引用值类型/运算符/控制流/循环/函数/递归/作用域/命名 11 词条（11 def 卡）；多定义汇编不符单词条契约，30 围栏 ≫ 2/20 → 按概念各拆词条 | pending |
| content/baike/programming-languages/编译原理与解释器实现.md | 10 | s4 | 16339 | 编译器架构、词法、语法、语义、IR、优化、代码生成、GC、实战构建语言、LLVM | 编译器架构/词法/语法/语义/IR/优化/代码生成/GC/实战构建语言/LLVM 十部分；正文 16339、501 代码行 → 按阶段拆词条 | pending |
| content/baike/programming-languages/计算机科学完整知识图谱.md | 5 | s4 | 14109 | 数据结构算法、操作系统、计算机网络、数据库、编译原理 | 数据结构算法/操作系统/计算机网络/数据库/编译原理 多子系统图谱（枢纽①对比表8行②子概念20）；正文 14109、30 围栏 ≫ 3400/20 → 按子系统拆词条+枢纽 | pending |
| content/baike/programming-languages/软件测试完全指南.md | 6 | s4 | 20441 | 测试金字塔、TDD·BDD·ATDD、单元、集成、E2E·Playwright·Cypress、性能 | 测试金字塔/TDD·BDD·ATDD/单元/集成/E2E·Playwright·Cypress/性能 各独立体系；正文 20441、20 围栏 937 行 → 拆词条（与 testing 子域去重） | done（2026-09-19 枢纽页 + 2 子词条，见去重队列第 1 对） |
| content/baike/programming-languages/面向对象编程（OOP）概念.md | 13 | s4 | 10181 | 类、对象、封装、继承、多态、抽象、接口、抽象类、构造析构、重载重写、访问修饰符、组合vs继承、LSP | 类/对象/封装/继承/多态/抽象/接口/抽象类/构造析构/重载重写/访问修饰符/组合vs继承/LSP 13 词条（13 def）；32 围栏 ≫ 2/20 → 按概念各拆词条 | pending |
| content/baike/security/加密技术篇.md | 14 | s5 | ~3000+ | 3DES、RSA、ElGamal、国密SM2·SM3·SM4、密钥交换、混合加密、数字信封 | 14种加密技术独立话题 | pending |
| content/baike/security/哈希算法篇.md | 12 | s5 | ~2500+ | MD5、SHA-256、SHA-512、哈希表原理、布隆过滤器、一致性哈希、校验和、加盐哈希 | 12种哈希算法独立对比 | pending |
| content/baike/security/密码学基础篇.md | 14 | s5 | ~3500+ | 盐、彩虹表、密钥、密钥对、公钥、私钥、证书链、密钥管理 | 14个密码学基础概念 | pending |
| content/baike/security/网络安全篇.md | 16 | s5 | ~3500+ | TLS·SSL握手、数字证书、数字签名、SQL注入、CC攻击 | 16个网络安全独立话题 | pending |
| content/baike/security/认证与授权篇.md | 14 | s5 | ~3000+ | OAuth 2.0、JWT、Session、Cookie、SSO、API Key、Bearer Token、OIDC | 14个认证授权独立话题 | pending |
| content/baike/software-engineering/01-开发流程.md | 13 | s4 | 3855 | 瀑布、敏捷、Scrum、Kanban、Sprint、用户故事、验收标准、故事点、计划扑克、站会、回顾、产品待办、冲刺待办 | 术语汇编（13 def 卡）：瀑布/敏捷/Scrum/Kanban/Sprint/用户故事/验收标准/故事点/计划扑克/站会/回顾/产品待办/冲刺待办，各带独立定义，不符单词条 1def+2trap 契约 → 按术语各拆词条 | pending |
| content/baike/software-engineering/02-版本控制.md | 14 | s4 | 3948 | 三区模型、add·commit·push、分支、merge、rebase、冲突、PR·MR、CodeReview、Hooks、GitFlow、主干开发、cherry-pick、stash | 术语汇编（14 def 卡、9 围栏）：三区模型/add·commit·push/分支/merge/rebase/冲突/PR·MR/CodeReview/Hooks/GitFlow/主干开发/cherry-pick/stash，与 Git 词条重叠 → 按命令与概念各拆词条 | pending |
| content/baike/software-engineering/03-代码质量.md | 13 | s4 | 3282 | 规范、linter、CodeReview、重构、技术债、圈复杂度、SOLID、DRY、KISS、YAGNI、CleanCode、代码异味 | 术语汇编（13 def 卡）：规范/linter/CodeReview/重构/技术债/圈复杂度/SOLID/DRY/KISS/YAGNI/CleanCode/代码异味，重构·技术债务·代码评审已有专文需去重 → 按主题各拆词条 | done（2026-09-19 枢纽页 + 圈复杂度/代码异味/Clean Code 原则 3 子词条，见去重队列第 2 对） |
| content/baike/software-engineering/04-CI CD.md | 14 | s4 | 3659 | CI、持续交付、持续部署、流水线、自动化测试、Jenkins、GitHubActions、GitLabCI、制品、环境、蓝绿、金丝雀、滚动更新、特性开关 | 术语汇编（14 def 卡）：CI/持续交付/持续部署/流水线/自动化测试/Jenkins/GitHubActions/GitLabCI/制品/环境/蓝绿/金丝雀/滚动更新/特性开关，与 devops 蓝绿部署重叠 → 按主题各拆词条 | done（2026-09-19 枢纽页 + 2 子词条：CI 与 CD、构建流水线与 CI-CD 工具） |
| content/baike/software-engineering/05-项目管理.md | 13 | s4 | 3078 | Jira、看板、燃尽图、燃起图、里程碑、需求管理、Bug生命周期、发布计划、风险管理、干系人、RACI、OKR、KPI | 术语汇编（13 def 卡）：Jira/看板/燃尽图/燃起图/里程碑/需求管理/Bug生命周期/发布计划/风险管理/干系人/RACI/OKR/KPI → 按术语各拆词条 | pending |
| content/baike/testing/01 - 测试基础.md | 12 | s4 | 10044 | 测试金字塔、单元、集成、E2E、冒烟、回归、探索性、验收、断言、覆盖率、测试替身、TDD | 术语汇编：测试金字塔/单元/集成/E2E/冒烟/回归/探索性/验收/断言/覆盖率/测试替身/TDD 12 个独立测试概念（枢纽①对比表14行②子概念7），0 def 卡；正文 10044 ≫ 3400、21 围栏 ≫ 2/20 → 按概念各拆词条 | pending |
| content/baike/testing/02 - 测试工具.md | 12 | s4 | 14217 | pytest、JUnit5、Jest、Mocha·Chai、Selenium、Cypress、Playwright、Postman、JMeter、Mockito、测试数据、环境管理 | 工具汇编：pytest/JUnit5/Jest/Mocha·Chai/Selenium/Cypress/Playwright/Postman/JMeter/Mockito/测试数据/环境管理 12 独立工具（①对比表7行②子概念5）；正文 14217、24 围栏 ≫ 上限 → 按工具各拆词条 | pending |
| content/baike/testing/03 - 性能测试.md | 12 | s4 | 11513 | 性能测试类型、QPS、TPS、并发用户、响应时间百分位、吞吐量、JMeter、K6、Locust、报告解读、瓶颈分析、优化思路 | 性能主题汇编：性能测试类型/QPS/TPS/并发用户/响应时间百分位/吞吐量/JMeter/K6/Locust/报告解读/瓶颈分析/优化思路 12 子话题（①对比表12行②子概念6）；正文 11513、18 围栏 ≫ 3400 → 按主题各拆词条 | pending |
