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
