# baike 拆分候选登记

判定见规范 §6：压到 2200 字会毁掉面试必需信息 **且** 含 ≥3 个可独立命名的子概念 →
本轮不重写、不 rename、不新建子文档，登记于此，等批量收敛后统一拆。

| 文件 | 子概念数 | 所属片 | 正文字数 | 理由 | 状态 |
|---|---|---|---|---|---|
| content/baike/architecture/API设计.md | 12 | s5 | — | RESTful/HTTP方法/状态码/命名/分页/GraphQL/gRPC/WebSocket/版本/幂等/HATEOAS/OpenAPI 各含独立示例与对比，压缩至2200必然毁掉面试深度 | pending |
| content/baike/design-patterns/创建型模式（Creational Patterns）.md | 6 | s4 | 14432 | 枢纽长文覆盖单例/工厂方法/抽象工厂/建造者/原型/对象池 6 个可独立命名子模式，各带代码示例与深浅拷贝、DCL+volatile、OCP 权衡等面试细节；正文 14432 字 ≫ 枢纽预算 3400、围栏 12 块 239 行 ≫ 上限 2/20，压缩至合规会毁掉逐模式机制 → 建议拆为 6 词条+1 枢纽 | pending |
| content/baike/design-patterns/结构型模式（Structural Patterns）.md | 10 | s4 | 16104 | 枢纽长文覆盖适配器/桥接/组合/装饰器/外观/享元/代理 7 种 GoF + 过滤器/MVC/MVVM，共 10 个可独立命名子概念，各带代码与对比表；正文 16104 字 ≫ 3400、围栏 15 块 311 行 ≫ 2/20，压缩会毁掉逐模式细节 → 建议拆为多词条+1 枢纽 | pending |
| content/baike/design-patterns/行为型模式（Behavioral Patterns）.md | 11 | s4 | 16222 | 枢纽长文覆盖策略/观察者/命令/状态/模板方法/迭代器/责任链/中介者/备忘录/访问者/解释器 11 种 GoF 行为型模式，各带代码与对比表；正文 16222 字 ≫ 3400、围栏 13 块 361 行 ≫ 2/20，压缩会毁掉逐模式细节 → 建议拆为 11 词条+1 枢纽 | pending |
| content/baike/architecture/SaaS产品技术架构.md | 6 | s5 | ~9000 | 架构模式/隔离策略/计费/权限/数据隔离/白标 各含大量代码与独立子话题，压缩毁面试细节 | pending |
| content/baike/architecture/云原生与多云架构实战指南.md | 8+ | s5 | ~4000+ | 容器/K8s/服务网格/多云/CI-CD/GitOps/Serverless/可观测 多独立子话题 | pending |
| content/baike/architecture/分布式系统设计完全指南.md | 8+ | s5 | ~4000+ | 一致性/共识/分布式事务/分片/复制/领导者选举等独立子话题 | pending |
| content/baike/architecture/可观测性工程实战.md | 5+ | s5 | ~4000+ | 日志/指标/链路追踪/APM/告警 各独立实践体系 | pending |
| content/baike/architecture/微服务架构设计与实践.md | 8+ | s5 | ~5000+ | 服务拆分/网关/通信/容错/数据一致性/部署/监控 各独立话题 | pending |
| content/baike/architecture/性能优化.md | 14 | s5 | ~1500+ | 缓存/CDN/负载均衡/连接池/异步/限流/熔断/降级等14个独立手段 | pending |
| content/baike/architecture/推荐系统设计与实现.md | 6+ | s5 | ~3500+ | 召回/排序/特征工程/AB测试/冷启动/实时性 各独立子系统 | pending |
| content/baike/architecture/数据工程完全指南.md | 6+ | s5 | ~4000+ | ETL/数仓/数据湖/流处理/数据质量/治理 各独立领域 | pending |
| content/baike/architecture/架构模式.md | 12 | s5 | ~1200+ | 单体/微服务/Serverless/EDA/CQRS/六边形/洋葱等12种独立模式 | pending |
| content/baike/architecture/系统设计.md | 12 | s5 | ~1500+ | CAP/BASE/一致性/分布式ID/分片/读写分离等12个独立话题 | pending |
| content/baike/architecture/设计原则.md | 12 | s5 | ~1800+ | SOLID/DRY/KISS/YAGNI/迪米特/组合/接口/IoC/DI等12个独立原则 | pending |
| content/baike/architecture/领域驱动设计DDD完全指南.md | 10 | s5 | ~2500+ | 核心思想/战略设计/战术设计/分层/事件风暴/CQRS/ES/微服务/实战/误区 10部分 | pending |
| database/MySQL从入门到架构师.md | 5 | s3 | 11081 | 全书式枢纽：存储引擎/索引优化/MVCC/锁/查询优化 5 个独立子概念，正文 11081 字、42 个代码块，压到 3400 仍毁掉面试级细节；与 MySQL深入 / 索引与查询优化术语 / 事务与并发控制术语 等专文高度重叠，宜拆为子文档 | pending |
| content/baike/developer-skills/开发者效率工具大全.md | 4 | s4 | 16942 | 目录型枢纽：终端工具/编辑器与IDE/Git高级用法/命令行工具 4 个可独立命名工具族，逐工具展开；正文 16942 字 ≫ 3400、围栏 28 块 880 行 ≫ 2/20，压缩会毁掉逐工具细节 → 建议按工具族拆词条 | pending |
| content/baike/developer-skills/敏捷项目管理实战.md | 10 | s4 | 13106 | 全书式枢纽：敏捷宣言/Scrum/看板/用户故事/估算/迭代管理/需求管理/技术实践/规模化敏捷/远程敏捷 10 个独立子话题，各带流程与示例；正文 13106 字 ≫ 3400、围栏 28 块 567 行 ≫ 2/20 → 建议按方法论拆词条+1 枢纽 | pending |
| database/NoSQL 数据库术语.md | 10 | s3 | 8568 | 全景文件实为 10 个独立词条（各库自带 def 卡、11 围栏、8568 字），无法并入单条 3400 上限。Redis/MongoDB/ES 已有专文应删除本文重复段；Memcached/HBase/Neo4j/InfluxDB/Cassandra/PynamoDB 各自拆为独立词条，NoSQL-vs-SQL 保留为选型枢纽并索引各子文档 | pending |
| content/baike/distributed/分布式ID与缓存术语百科.md | 8 | s2 | 12066 | 8 个可独立命名子概念（ID方案/穿透/雪崩/击穿/缓存一致性/多级缓存/热点数据/冷热分离），各带 Java 代码与对比表；正文 12066 字 ≫ 3400、围栏 11 块 ≫ 2/20，且为 baike B 多定义结构（8 张 def 卡）不符单词条契约 → 建议按子概念拆词条，穿透/击穿/雪崩/缓存一致性等宜各自成篇 | pending |
| content/baike/frontend-concepts/HTML & CSS 核心概念.md | 14 | s5 | ~3000+ | 14个独立HTML/CSS概念各带代码，压缩毁面试细节 | pending |
| content/baike/frontend-concepts/JavaScript 基础核心概念.md | 17 | s5 | ~4000+ | 17个独立JS概念各带示例 | pending |
| content/baike/frontend-concepts/前端工程化核心概念.md | 14 | s5 | ~4000+ | 14个独立工程化概念 | pending |
| content/baike/frontend-concepts/前端框架核心概念.md | 12 | s5 | ~3500+ | 12个独立框架概念 | pending |
| content/baike/frontend-frameworks/GraphQL从入门到精通.md | 10+ | s5 | ~5000+ | Schema/查询/变更/订阅/解析器/缓存/安全等独立话题 | pending |
| content/baike/frontend-frameworks/Next.js全栈开发实战.md | 10+ | s5 | ~5000+ | 路由/SSR/SSG/API Routes/Middleware/部署等独立话题 | pending |
| content/baike/frontend-frameworks/WebAssembly完全指南.md | 8+ | s5 | ~4000+ | 编译/内存模型/JS互操作/SIMD/线程等独立话题 | pending |
| content/baike/frontend-frameworks/现代前端工程化完全指南.md | 10+ | s5 | ~5000+ | 构建工具/模块/包管理/CI-CD/测试等独立话题 | pending |
| content/baike/security/哈希算法篇.md | 12 | s5 | ~2500+ | 12种哈希算法独立对比 | pending |
| content/baike/security/密码学基础篇.md | 14 | s5 | ~3500+ | 14个密码学基础概念 | pending |
| content/baike/security/加密技术篇.md | 14 | s5 | ~3000+ | 14种加密技术独立话题 | pending |
| content/baike/security/网络安全篇.md | 16 | s5 | ~3500+ | 16个网络安全独立话题 | pending |
| content/baike/security/认证与授权篇.md | 14 | s5 | ~3000+ | 14个认证授权独立话题 | pending |
| database/Redis深度解析与实战指南.md | 8 | s3 | 13550 | 书级实战指南：数据结构/底层实现/内存管理/持久化/主从/Sentinel/Cluster/分布式锁 8 大独立主题、56 个代码块、0 卡片，远超 3400 上限；速览已由 Redis深入 承载，本文件应按 8 主题各拆独立词条（含 Redlock、淘汰策略等面试必备细节，压缩必毁） | pending |
| database/SQL 基础术语.md | 12 | s3 | 8536 | 术语汇编实为 12 个独立词条(各带 def+示例、12 围栏、0 trap)：DDL/DML/DCL/DQL/TCL 可合并为一篇"SQL 语言分类"，SELECT 执行顺序/JOIN/子查询/UNION/GROUP BY-HAVING/窗口函数/CTE 各自独立且面试必备，压到 3400 必毁；窗口/CTE 与 PostgreSQL 篇重叠需去重 | pending |
| database/事务与并发控制术语.md | 12 | s3 | 9037 | 术语汇编实为 12 个独立词条(各带 def+示例、12 围栏、0 trap)：事务/ACID/隔离级别/脏读/不可重复读/幻读/MVCC/乐观锁/悲观锁/死锁/Redo Log/Undo Log。隔离级别·MVCC·死锁 已有专文应去重；ACID、三类并发读异常、乐观/悲观锁、Redo/Undo 各为面试必备独立词条，压入 3400 必毁 | pending |
| content/baike/distributed/分布式存储术语百科.md | 8 | s2 | 4308 | baike B 多定义（分片/副本/Raft/Paxos/ZAB/Gossip/一致性模型谱系/Quorum）；正文 4308 字 ≫ 3400、围栏 4 块 ≫ 2/20。Raft/Paxos/ZAB 已由 [[一致性算法]] 承载可删，但数据分片/副本/一致性模型谱系(线性·顺序·因果)/Quorum(NWR)/Gossip 是面试必需且无对应子词条，压缩至合规会毁掉这些表与追问级细节 → 建议拆为分片/副本/一致性模型/Quorum/Gossip 等词条 | pending |
| content/baike/distributed/微服务治理术语百科.md | 10 | s2 | 7925 | baike B 多定义（注册发现/负载均衡/熔断/限流/降级/链路追踪/配置中心/API网关/服务网格/灰度发布）；正文 7925 字 ≫ 3400、围栏 12 块 ≫ 2/20。负载均衡/服务网格/熔断与降级/限流/服务发现已有专文，但链路追踪/配置中心/API网关/灰度发布含 @FeignClient·Resilience4j·Gateway·Nacos·金丝雀等唯一代码与对比表，压缩必毁 → 建议按治理主题各拆词条 | pending |
| content/baike/devops/API设计最佳实践.md | 5 | s4 | 14388 | RESTful原则/版本管理/认证授权(OAuth四步)/错误处理/分页过滤排序 各独立话题带示例；正文 14388 ≫ 3400、围栏 35 块 647 行 ≫ 2/20 → 建议按话题拆词条 | pending |
| content/baike/devops/Docker容器化完全指南.md | 8 | s4 | 16568 | 容器vsVM/镜像构建/网络/数据/Compose/安全/Harbor/日志 8 独立话题；正文 16568、围栏 48 块 957 行 ≫ 上限 → 建议拆词条+1 枢纽 | pending |
| content/baike/devops/Kubernetes云原生实战指南.md | 3 | s4 | 6644 | 容器基础/K8s核心概念/网络模型 3 大独立块，正文 6644 字、代码 416 行 ≫ 3400/20；与 Kubernetes深入 有重叠 → 拆块并按需与深入去重 | pending |
| content/baike/devops/Linux系统管理高级指南.md | 10 | s4 | 12784 | 内核/进程/内存/文件系统/网络/性能/Shell/systemd/安全/容器运行时 10 独立话题；围栏 36 块 → 建议按主题拆词条 | pending |
| content/baike/devops/Web安全攻防实战指南.md | 13 | s4 | 13296 | OWASP Top10 各项 + 经典攻防详解共 13 个独立话题（枢纽信号①对比表10行②子概念26）；正文 13296 ≫ 3400 → 建议按漏洞/攻防各拆词条 | pending |
| content/baike/devops/操作系统内核原理.md | 9 | s4 | 13534 | 进程/线程/内存/文件系统/IO/系统调用与中断/设备驱动/容器隔离(Namespace+Cgroups)/安全 9 独立子系统；围栏 14 → 建议按子系统拆词条 | pending |
| content/baike/devops/网络安全与渗透测试.md | 5 | s4 | 17171 | 网络协议安全/Web渗透方法论/常见漏洞实战/内网渗透/安全工具链 5 大部分各成体系；正文 17171、围栏 29 块 752 行 ≫ 上限 → 建议按部分拆词条 | pending |
| database/数据库内核原理深度解析.md | 8 | s3 | 11136 | 内核原理全书：存储引擎/索引/查询优化器/事务/并发控制/日志恢复/分布式/实战对比 8 大主题、35 节、0 def 卡。含 CBO、ARIES、列存、TSO/OCC/2PC、InnoDB·PG·TiDB 对比等本文独有的深度子题，多数无对应专文，压到 3400 必毁面试级内核细节；应按主题拆分，末尾对比表可留作内核枢纽 | pending |
| database/数据库设计术语.md | 15 | s3 | 10034 | 术语汇编实为 15 个独立词条(各带 def+示例、17 围栏、0 trap)，无法并入单条上限；应按术语各拆独立词条，并与 数据库范式/数据库设计 相关专文去重后统一收敛 | pending |
| database/搜索引擎技术详解.md | 6 | s3 | 17928 | 搜索引擎全书：架构/爬虫设计/倒排索引/分词/查询解析/相关性排序 6 大主题、0 def 卡、19 围栏 922 内行(爬虫章节尤长)，远超上限。爬虫/分词/TF-IDF·BM25 排序等多为本文独有深度内容、无对应专文，压入 3400 必毁；应按 6 主题各拆词条，通用原理留作搜索枢纽并链接 ElasticSearch搜索/向量数据库技术 | pending |
| database/索引与查询优化术语.md | 12 | s3 | 9066 | 术语汇编实为 12 个独立词条(各带 def+示例、13 围栏、0 trap)：聚簇/非聚簇/B+树/哈希/全文/联合/覆盖索引、最左前缀、ICP、EXPLAIN、慢查询优化、索引失效场景，均面试必备且各自独立，压入 3400 必毁；应各拆词条，B+树索引段与 B+树 专文去重 | pending |
| content/baike/os/Linux 命令速查手册.md | 20+ | s2 | 4504 | 命令型速查手册：ls/cd/mkdir/cp·mv·rm/cat·less/grep/find/sed/awk/chmod/ps·top/df·du/netstat/tar 等按命令分组，每组带独立示例围栏；无 `## 定义`、15 围栏 ≫ 2/20，压缩会毁掉逐命令用法示例（这是手册的核心价值）→ 建议保留为速查参考或按命令族拆词条 | pending |
| content/baike/os/Shell 脚本详解.md | 8+ | s2 | 8061 | 教程/手册式汇编：变量/条件 if·case/循环 for·while·until/函数/grep·sed·awk 等多块各带大量代码，无 `## 定义` 单词条结构、正文 8061 ≫ 3400、15 围栏 ≫ 2/20，压缩必毁逐语法示例；与 Shell脚本编程 词条重叠需去重 → 建议按语法主题拆词条 | pending |
| content/baike/os/进程管理详解.md | 12+ | s2 | 6581 | 命令+概念混合详解：ps/top·htop/kill/nohup/systemd/cron/nice//proc/dmesg/journalctl/systemctl 等 11+ 子块各带 def 与代码，17 围栏 ≫ 2/20、6581 ≫ 3400，压缩会毁掉逐命令实战细节；与 Linux命令速查手册 重叠 → 建议拆命令词条+进程管理枢纽 | pending |
| data-science/数据分析与可视化实战.md | 3 | s3 | 17377 | 实战手册：Python工具链/数据清洗实战/EDA方法论 3 大主题、0 def 卡、8 围栏 784 代码行，远超上限。概念词条已由"数据分析与可视化"承载，本文是代码级实操详解，压入 3400 必毁实操细节；应拆为三篇实操子文档或并入 ETL/EDA 专题 | pending |
| content/baike/programming-languages/Flutter跨平台开发实战.md | 5 | s4 | 22743 | Dart精要/Widget体系/布局/路由GoRouter/状态管理 各独立且带大量代码；正文 22743、围栏 14 块 1284 行 ≫ 上限 → 按主题拆词条 | pending |
| content/baike/programming-languages/Go语言系统编程指南.md | 5 | s4 | 18340 | 并发模型/内存模型 happens-before/隐式接口/反射/unsafe 各独立话题；正文 18340、1187 代码行 → 拆词条 | pending |
| content/baike/programming-languages/Python全栈开发教程.md | 5 | s4 | 23070 | Python基础/FastAPI/SQLAlchemy/PostgreSQL/React 全栈五大块，各为独立体系；正文 23070、1166 代码行 → 拆子文档 | pending |
| content/baike/programming-languages/Python高级编程完全指南.md | 4 | s4 | 21427 | 装饰器高级/元类/描述符协议/上下文管理器 各独立带大量代码；正文 21427、1075 代码行 → 拆词条 | pending |
| content/baike/programming-languages/Rust系统编程入门到精通.md | 7 | s4 | 17989 | 所有权/Trait泛型/错误处理/智能指针/并发/异步/Unsafe 7 大独立主题；正文 17989、24 围栏 1121 行 → 按主题拆词条 | pending |
| content/baike/programming-languages/TypeScript高级编程指南.md | 8 | s4 | 22260 | 类型系统/泛型/类型体操/装饰器/模块/.d.ts/编译器API/框架集成 8 独立话题；正文 22260、33 围栏 → 拆词条 | pending |
| content/baike/programming-languages/函数式编程完全指南.md | 10 | s4 | 18943 | FP概念/高阶函数/闭包柯里化/Functor·Monad/Either·Option·IO/不可变/并发/JS·Haskell 实践 10 话题；正文 18943、24 围栏 → 拆词条 | pending |
| content/baike/programming-languages/密码学与区块链技术指南.md | 6 | s4 | 16609 | 密码学基础/加密算法/密钥管理/TLS·SSL/区块链原理/比特币 6 大部分各成体系；正文 16609、10 围栏 584 行 → 拆词条 | pending |
| content/baike/programming-languages/并发编程模式与实践.md | 8 | s4 | 17776 | 并发vs并行/线程模型/互斥同步/无锁/并发数据结构/协程/Channel·CSP/Actor（枢纽①mermaid②子概念20）；正文 17776、1071 代码行 ≫ 3400 → 拆词条 | pending |
| content/baike/programming-languages/程序员的数学基础.md | 6 | s4 | 19326 | 离散数学/线性代数/…多个独立数学分支章节；正文 19326、7 围栏 966 行 ≫ 上限 → 按分支拆词条 | pending |
| content/baike/programming-languages/编程概念音频课-数据结构.md | 6 | s4 | 8957 | 数组链表/栈队列/哈希表/树二叉树/图/堆 6 站各独立数据结构主题；正文 8957、8 围栏 178 行 → 按结构拆词条 | pending |
| content/baike/programming-languages/编程概念音频课-设计模式.md | 8 | s4 | 10591 | 单例/工厂/观察者/策略/装饰器/适配器/代理/模板方法 8 模式各独立；正文 10591、8 围栏 328 行 → 按模式拆词条 | pending |
| content/baike/programming-languages/编程语言通用概念.md | 11 | s4 | 7301 | 变量/常量/基本类型/引用值类型/运算符/控制流/循环/函数/递归/作用域/命名 11 词条（11 def 卡）；多定义汇编不符单词条契约，30 围栏 ≫ 2/20 → 按概念各拆词条 | pending |
| content/baike/programming-languages/编译原理与解释器实现.md | 10 | s4 | 16339 | 编译器架构/词法/语法/语义/IR/优化/代码生成/GC/实战构建语言/LLVM 十部分；正文 16339、501 代码行 → 按阶段拆词条 | pending |
| content/baike/programming-languages/计算机科学完整知识图谱.md | 5 | s4 | 14109 | 数据结构算法/操作系统/计算机网络/数据库/编译原理 多子系统图谱（枢纽①对比表8行②子概念20）；正文 14109、30 围栏 ≫ 3400/20 → 按子系统拆词条+枢纽 | pending |
| content/baike/programming-languages/软件测试完全指南.md | 6 | s4 | 20441 | 测试金字塔/TDD·BDD·ATDD/单元/集成/E2E·Playwright·Cypress/性能 各独立体系；正文 20441、20 围栏 937 行 → 拆词条（与 testing 子域去重） | pending |
| content/baike/programming-languages/面向对象编程（OOP）概念.md | 13 | s4 | 10181 | 类/对象/封装/继承/多态/抽象/接口/抽象类/构造析构/重载重写/访问修饰符/组合vs继承/LSP 13 词条（13 def）；32 围栏 ≫ 2/20 → 按概念各拆词条 | pending |
| content/baike/programming-languages/React Native移动应用开发.md | 6 | s4 | 21874 | RN新架构/核心组件布局/导航/状态管理/网络缓存/原生桥接 各独立；正文 21874、14 围栏 1122 行 ≫ 上限 → 拆词条 | pending |
| content/baike/programming-languages/Rust Web开发实战.md | 6 | s4 | 20339 | Web生态概览/Axum/数据库集成/serde/认证授权/tokio 六部分各独立；正文 20339、32 围栏 959 行 → 拆词条 | pending |
| content/baike/programming-languages/函数式编程（Functional Programming）概念.md | 14 | s4 | 11638 | 纯函数/副作用/不可变/高阶函数/Lambda/闭包/柯里化/组合/Monad/Functor/Applicative/声明式/惰性求值 14 词条（14 def）；29 围栏 ≫ 2/20 → 按概念各拆词条 | pending |
| content/baike/programming-languages/并发编程（Concurrent Programming）概念.md | 14 | s4 | 17338 | 并发vs并行/线程vs进程/锁Mutex/读写锁/信号量/条件变量/死锁/原子/CAS/线程池/协程/消息传递/Future·Promise/事件循环 14 词条（14 def）；40 围栏 ≫ 2/20 → 按概念各拆词条 | pending |
| content/baike/software-engineering/01-开发流程.md | 13 | s4 | 3855 | 术语汇编（13 def 卡）：瀑布/敏捷/Scrum/Kanban/Sprint/用户故事/验收标准/故事点/计划扑克/站会/回顾/产品待办/冲刺待办，各带独立定义，不符单词条 1def+2trap 契约 → 按术语各拆词条 | pending |
| content/baike/software-engineering/02-版本控制.md | 14 | s4 | 3948 | 术语汇编（14 def 卡、9 围栏）：三区模型/add·commit·push/分支/merge/rebase/冲突/PR·MR/CodeReview/Hooks/GitFlow/主干开发/cherry-pick/stash，与 Git 词条重叠 → 按命令与概念各拆词条 | pending |
| content/baike/software-engineering/03-代码质量.md | 13 | s4 | 3282 | 术语汇编（13 def 卡）：规范/linter/CodeReview/重构/技术债/圈复杂度/SOLID/DRY/KISS/YAGNI/CleanCode/代码异味，重构·技术债务·代码评审已有专文需去重 → 按主题各拆词条 | pending |
| content/baike/software-engineering/04-CI CD.md | 14 | s4 | 3659 | 术语汇编（14 def 卡）：CI/持续交付/持续部署/流水线/自动化测试/Jenkins/GitHubActions/GitLabCI/制品/环境/蓝绿/金丝雀/滚动更新/特性开关，与 devops 蓝绿部署重叠 → 按主题各拆词条 | pending |
| content/baike/software-engineering/05-项目管理.md | 13 | s4 | 3078 | 术语汇编（13 def 卡）：Jira/看板/燃尽图/燃起图/里程碑/需求管理/Bug生命周期/发布计划/风险管理/干系人/RACI/OKR/KPI → 按术语各拆词条 | pending |
