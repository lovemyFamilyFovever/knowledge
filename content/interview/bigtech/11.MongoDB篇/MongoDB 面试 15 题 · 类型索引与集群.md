---
title: "MongoDB 面试 15 题 · 类型索引与集群"
tags: ["MongoDB", "数据库", "分布式"]
source: "github"
source_path: "interview_internal_reference / 11.MongoDB篇"
collected: "2026-09-23"
status: "stable"
---

本页收录 15 道 MongoDB 数据类型、索引诊断与集群架构题，覆盖 BSON 类型与 ObjectId、索引种类与建法、主外键与聚合、分析器与性能诊断、复制/副本集/分片与 WiredTiger 引擎、可替代产品对比；难度分布为初级 3 题、中级 9 题、高级 3 题，每题附核心结论与面试官追问。

> 💡 说明
> **上游仓库 `interview_internal_reference` 的 MongoDB 篇里，本页 15 题有 14 题只有题干、正文完全为空**（原仓库标注"持续更新中"，这部分从未写完）；仅"分片是什么"一题有上游答案。本库按现行 MongoDB 7.x/8.x 补写全部内容，命令口径以官方文档为准。

## 数据类型与主键（5 题）

### 1. MongoDB 支持哪些数据类型（BSON 类型）？｜初级

核心结论：MongoDB 存的是 BSON（二进制编码的类 JSON），类型比 JSON 更丰富——除了基本类型还有 ObjectId、Date、Int32/Int64、Decimal128、Binary、Regex、Timestamp、MinKey/MaxKey 等。

- 常用类型：`Double`、`String`(UTF-8)、`Object`、`Array`、`BinData`、`ObjectId`、`Boolean`、`Date`（毫秒精度）、`Null`、`Regex`、`Int32`、`Timestamp`（内部 oplog 用）、`Int64`、`Decimal128`、`MinKey`、`MaxKey`。
- 容易踩的类型坑：
  - **数字默认是 Double**：`1` 和 `NumberLong(1)` 和 `NumberInt(1)` 是不同类型，`{n: 1}` 匹配不到存成 `NumberLong(1)` 的文档（旧版本严格区分；现在整型比较已放宽，但索引与聚合里仍有影响）。金额必须用 `Decimal128`，浮点会累积误差。
  - **Date 是 UTC 毫秒**：`new Date()` 存 UTC，展示时按客户端时区渲染；存成字符串就失去了范围索引与 TTL 能力。
  - `Timestamp` 不是 `Date`：它是 MongoDB 内部（oplog、副本集）用的"秒 + 递增序号"类型，别拿它存业务时间。
- 类型查询：`{ field: { $type: 'string' } }`（3.6+ 支持规范名，旧的数字代号仍兼容）；`$type` 在索引字段上可用。
- `Symbol` 已弃用，`JavaScript Code` 类型见第 4 题。

> ⚠️ 注意
> "同一字段可以混放不同类型"既是自由也是隐患：字段类型漂移会让索引退化为多类型索引、比较语义变得难预测、聚合 `$group` 结果诡异。生产上要么用 `$jsonSchema` validator 约束类型，要么在应用层用带类型的模型（Mongoose Schema / 驱动的类型映射）。

> 🎯 关键要点
> - BSON 类型比 JSON 丰富：ObjectId/Date/Int64/Decimal128/Binary
> - 金额用 Decimal128，时间用 Date，别存字符串
> - Timestamp 是内部类型，不是业务时间
> - 字段类型混放会毁掉索引与聚合的可预测性
> - $type 能查类型，但最好靠 validator 预防

> 🔍 追问
> - 为什么把时间存成字符串是个坏主意？
> - Int32 / Int64 / Double 在索引和聚合里表现有什么不同？

### 2. 为什么 MongoDB 要用 ObjectId？｜中级

核心结论：ObjectId 是一个"无需中心协调就能保证全局唯一、又大致按时间有序"的 12 字节主键——它把唯一性责任分散到每个客户端进程，同时保留了可排序性，正好适配分片与高并发写入。

- 解决什么问题：分布式环境里自增序列要中心分配（成为瓶颈与单点），UUID 又太长且完全无序（造成索引随机写、缓存命中率差）。ObjectId 是折中：12 字节、客户端可本地生成、时间前缀带来近似插入序。
- 为什么适合做 `_id`：① 生成不需要网络往返；② 唯一性由"时间 + 进程随机量 + 计数器"三层保证；③ 前 4 字节是秒级时间戳，所以按 `_id` 排序近似按创建时间排序，索引追加写友好（接近顺序写）。
- 局限（面试要能说全）：
  - 时间戳只到秒，同一秒内的顺序由计数器保证，但跨进程只靠随机量区分，**不能当严格的全局序号用**。
  - 12 字节比自增整型大，所有二级索引叶子都要存它，索引体积随之上涨。
  - 含创建时间与机器信息，作为对外暴露的 ID 会泄露业务量与内部信息（可改用 UUIDv7 或自定义 ID）。
  - 时间前缀导致"最新数据总写在索引尾部"，热页集中——分片场景下用 `_id` 做哈希分片键可缓解。
- 替代做法：业务单号（天然唯一且有序）、UUIDv7（时间有序）、Snowflake（要管机器 id 分配）。选自定义 `_id` 时必须自己保证唯一且尽量单调递增。

> 💡 提示
> "ObjectId 能保证绝对唯一吗？"——在配置正确的前提下能，但它依赖进程随机量与计数器，同一秒内多进程并发写极端情况下唯一性来源是概率而非协议。所以真正的答案是：**唯一性由 `_id` 上的唯一索引强制**，ObjectId 只是把"撞车概率"降到可忽略。

> 🎯 关键要点
> - ObjectId = 去中心化唯一 + 近似时间有序
> - 12 字节，比整型大，会放大二级索引
> - 秒级时间戳不能当严格序号用
> - 对外暴露要考虑信息泄露
> - 真正的唯一性由 _id 唯一索引兜底

> 🔍 追问
> - 为什么 UUID 做主键会让 InnoDB / MongoDB 的索引变慢？
> - 你会在什么场景下放弃 ObjectId 改用业务主键？

### 3. ObjectId 由哪些部分组成？｜初级

核心结论：12 字节 = 4 字节秒级时间戳 + 5 字节进程级随机值 + 3 字节自增计数器；时间在前所以它可按创建时间粗排，计数器在同进程内保证单调。

- 结构（3.4 及以后）：

| 段 | 长度 | 内容 | 作用 |
|---|---|---|---|
| 时间戳 | 4 字节 | 创建时刻（秒，UTC） | 近似有序、可反推创建时间 |
| 随机值 | 5 字节 | 进程启动时生成的随机数 | 区分不同进程/机器 |
| 计数器 | 3 字节 | 每进程一个随机初值的自增计数 | 同秒内不同文档互不冲突 |

- 历史版本差异（原稿那代的答案是"机器标识 + PID + 时间 + 计数器"）：3.4 之前是 4 字节时间 + 3 字节机器 hostname 哈希 + 2 字节进程 PID + 3 字节计数器；后来发现机器哈希与 PID 都可能碰撞（容器化后 PID 高度重复），改成 5 字节随机值。
- 实用技巧：
  - 取创建时间：`ObjectId.getTimestamp()`（mongosh）/ `oid.getTimestamp()`（驱动）。
  - 按时间范围查历史数据：`_id: { $gte: ObjectId.fromDate(cutoff) }` —— 比额外建时间索引更省。
  - 合法性校验：必须是 24 位十六进制字符串（`/^[0-9a-fA-F]{24}$/`），前端传来的 id 先校验再查库，否则抛 `invalid ObjectId`。

> 🎯 关键要点
> - 4 + 5 + 3 = 12 字节，24 位十六进制字符串表示
> - 3.4 前后组成不同，答题要限定版本
> - getTimestamp 能反推创建时间
> - 用 ObjectId.fromDate 做时间范围查询很实用
> - 外部传入的 id 要先做格式校验

> 🔍 追问
> - 为什么 3.4 要把机器哈希 + PID 换成随机值？
> - 只给一个 ObjectId，你能推断出什么信息？

### 4. BSON 里的 Code 类型是什么？为什么现在不建议用它？｜中级

核心结论：Code 类型用来存 JavaScript 函数/代码片段，历史上服务于 `$where`、mapReduce 和存储函数；它让服务端执行任意 JS，性能上无法用索引、安全上扩大攻击面，因此现代实践是尽量避免。

- 出现在哪：`db.coll.find({ $where: "this.qty < this.min" })`（比较两个字段的旧写法）、`mapReduce` 的 map/reduce 函数、`db.eval()`（早已移除）。
- 为什么慢：`$where` 对每个候选文档都要**解释执行一段 JS**，无法使用索引谓词下推，等于全表扫 + 每文档一次脚本调用。
- 为什么危险：能执行任意代码就是注入面；服务端内嵌 JS 引擎（SpiderMonkey → 6.0 起换成 QuickJS）历史上出过多个内存安全与沙箱逃逸类问题。
- 现代替代：
  - 比较两个字段：`$expr`（3.6+）——`db.coll.find({ $expr: { $lt: ['$qty', '$min'] } })`，走聚合表达式引擎，比 `$where` 快且安全。
  - 复杂逻辑：聚合管道；派生字段：更新时用聚合式 update；视图：`createView` 存管道。
  - 真需要存储过程式逻辑：放到应用层或用 Atlas Function / 外部服务。
- 仍会碰到 Code 的地方：老数据里存的函数值、`mapReduce`（5.0 起弃用，被聚合取代）。

> ⚠️ 注意
> 别把 `$expr` 说成"完全等价且免费"：`$expr` 里的表达式部分场景不能利用索引（只有能归一化成索引谓词的形式才可以），所以它比 `$where` 好，但仍不如普通条件 + 索引。答这题能带出这一层，说明你真的调过。

> 🎯 关键要点
> - Code 类型 = 服务端存 JS，为 $where/mapReduce 服务
> - 每文档执行脚本、用不上索引，且是安全隐患
> - $expr 是 $where 的现代替代
> - mapReduce 已弃用，逻辑优先放应用层或聚合
> - 派生字段用聚合式 update 而不是脚本

> 🔍 追问
> - 为什么 `$where` 比 `$expr` 更慢？
> - 需要"字段 A 小于字段 B"的查询，索引怎么建才有效？

### 5. BSON 里的 Regular Expression 类型是什么？怎么用才不丢性能？｜中级

核心结论：正则是一等 BSON 类型（`/pattern/flags`），能直接写进查询与索引；但只有**锚定前缀**的正则才能利用索引做范围扫，含 `i` 忽略大小写时还得配 collation 索引。

- 两种写法：`{ name: /^Mon/ }` 与 `{ name: { $regex: '^Mon', $options: 'i' } }`。
- 索引利用规则：
  - `^abc`（前缀锚定、大小写敏感）→ 可转成索引范围扫 `[abc, abd)`，高效。
  - `^abc.*xyz`、`abc`（前导通配）、`$options: 'i'` → 退化为对索引键或全集合逐条正则匹配，`COLLSCAN` 级别开销。
  - 需要大小写不敏感：建带 collation 的索引 `{ locale: 'en', strength: 2 }`，查询也带同样 collation，才能既忽略大小写又走索引。
- 性能与语义细节：正则在服务端执行，代价随候选文档数线性增长；`$regex` 与字符串索引组合时，先让其他高选择性条件缩小范围。
- 替代方案：
  - 前缀匹配（如按编码前几位）：直接范围查 `{ code: { $gte: 'A1', $lt: 'A1\uffff' } }`，比正则更直观可索引。
  - 全文检索：`$text` 索引或 Atlas Search（倒排 + 分词 + 打分），别用正则硬做。
  - 拼音/模糊搜索：应用层生成 n-gram 字段再精确匹配。

> 🎯 关键要点
> - 正则是 BSON 原生类型，可进查询也可进索引
> - 只有锚定前缀的正则能走索引范围扫
> - 忽略大小写要配 collation 索引
> - 全文搜索该用 $text / Atlas Search
> - 前缀匹配用范围查询更清晰

> 🔍 追问
> - 一个 `LIKE '%关键词%'` 类需求，你在 MongoDB 里怎么落地？
> - 为什么大小写不敏感查询默认用不上索引？

## 索引与诊断（5 题）

### 6. MongoDB 里的索引是什么？有哪些种类？｜中级

核心结论：索引是独立于文档、按指定键有序存放的结构（B-tree），把"扫全集合"变成"定位到一小段"；MongoDB 支持十几种索引形态，选错类型比不建索引更常见。

- 默认：每个集合自动有 `_id` 升序索引，不可删除。
- 种类：

| 索引 | 用途 | 注意 |
|---|---|---|
| 单字段 | 高频等值/范围 | 方向影响排序复用 |
| 复合 | 多条件查询 | 必须满足最左前缀，等值列在前、范围列在后 |
| 多键 multikey | 数组字段 | 每个数组元素一条索引项；一个查询里只能有一个多键索引 |
| 文本 text | 分词全文 | 一词一索引项，性能一般，复杂需求用 Atlas Search |
| 哈希 hashed | 分片键均匀打散 | 只支持等值，不支持范围 |
| TTL | 自动过期 | 后台每 60 秒扫，删除有延迟 |
| 部分 partial | 只索引满足条件的文档 | 体积小，但查询必须显式带该条件才用得上 |
| 通配符 wildcard | 对未知字段名建索引 | 4.2+，稀疏/动态结构救星，不能替代精确索引 |
| 2d / 2dsphere | 平面/地理球面 | `$near`、`$geoWithin` |
| 聚簇 clustered | 按指定索引物理组织 | 5.3+，建集合时才能指定 |

- 生效机制：查询规划器为每个查询维护计划缓存（`planCache`），新索引不会自动让旧计划失效；必要时 `db.coll.resetPlanCache()` 或 `hint()` 强制。
- 判读：`explain('executionStats')` 看 `winningPlan.stage` 是 `IXSCAN` 还是 `COLLSCAN`、`indexFilterSet`、`docsExamined` vs `nReturned`。
- 代价：每个索引都要在写时维护、占内存与磁盘；副本集上索引通过 oplog 重放构建，写放大明显。经验上限是"一个集合不超过 10 个左右索引"。

> 💡 提示
> 复合索引的顺序不是小事：`{status:1, created:-1}` 能服务 `find({status:'paid'}).sort({created:-1})`（等值 + 排序都由索引完成）；反过来 `{created:-1, status:1}` 就变成"扫时间轴再逐条过滤状态"。这是索引题里最能区分"背过"和"用过"的地方。

> 🎯 关键要点
> - _id 索引自带且删不掉
> - 复合索引：等值在前、范围/排序在后、满足最左前缀
> - 数组自动 multikey，一次查询只能有一个多键索引
> - 部分索引要求查询显式带条件
> - 索引数量与写放大成正比

> 🔍 追问
> - 加了索引查询还是 COLLSCAN，可能是什么原因？
> - 部分索引和"把不关心的数据放另一个集合"怎么选？

### 7. 如何给集合添加索引？生产上要注意什么？｜中级

核心结论：`createIndex({key: 1}, {name, unique, sparse, background, collation, partialFilterExpression, expireAfterSeconds})`；4.2+ 默认用混合式（hybrid）索引构建，不再需要 `background: true`，但大集合建索引仍要按副本集滚动做。

- 常用命令：
  - `db.coll.createIndex({ email: 1 }, { unique: true })`
  - `db.coll.createIndex({ status: 1, created: -1 })`
  - `db.coll.createIndex({ created: 1 }, { expireAfterSeconds: 3600 })`（TTL）
  - `db.coll.createIndex({ 'attrs.k': 1 }, { partialFilterExpression: { type: 'x' } })`
  - `db.coll.getIndexes()` / `db.coll.dropIndex('name')` / `dropIndexes()`
- 唯一索引与空值：`unique` + 字段缺失时，**缺失字段的文档只允许存在一个**；要允许多个缺失用 `sparse: true`（或 3.2+ 直接靠 partial 索引）。
- 大集合建索引的正确姿势：
  1. 4.2+ 混合构建：构建期间不阻塞读写（只在开始与结束时短暂持锁），比旧的 foreground 好得多。
  2. 副本集滚动：先在 Secondary 上建（`secondaryIndex` 控制），逐个完成后 `rs.stepDown` 让原主降级，再在最后那个节点上建——避免全集群同时被索引构建拖慢。
  3. 分片集群：mongos 上建索引会下发到各 shard，注意超时与 `maxTimeMS`。
- `unique` 不是并发保险：唯一索引保证键不重复，但"检查后写入"这种业务约束仍要靠原子更新或事务，别用"先 find 再 insert"。
- 观察索引使用率：`db.coll.aggregate([{$indexStats:{}}])` 看每个索引的访问速率，长期为 0 的候选删除。

> ⚠️ 注意
> `background: true` 在 4.2+ 已被忽略（官方文档标注弃用），因为混合构建本身就是非阻塞的。如果面试里还坚持讲"foreground vs background 的区别"，会被认为停留在 3.x。

> 🎯 关键要点
> - createIndex 一次建一个，可批量传数组
> - unique + sparse / partial 处理缺失字段
> - 4.2+ 混合构建，background 已无意义
> - 大集合按副本集滚动建索引
> - $indexStats 找出没人用的索引

> 🔍 追问
> - 为什么"先查再插"挡不住并发重复？
> - 一个索引建了 3 小时还没完，你怎么判断该不该中断？

### 8. MongoDB 支持主键和外键关系吗？｜中级

核心结论：主键有（`_id` 天然唯一且必有索引，可自定义值），外键没有——MongoDB 不强制参照完整性，表间关系由应用层的内嵌或引用建模来表达，`$lookup` 只是查询期的临时关联。

- 主键：`_id` 唯一 + 必有索引 + 不可删除；可以是任意 BSON 类型（默认 ObjectId）。要"业务唯一键"就再建 `unique` 索引（相当于关系型的候选键/唯一约束）。
- 没有外键意味着：① 插入 `authorId` 指向不存在的作者不会被拒；② 删除父文档不会级联或限制；③ 完整性完全靠应用逻辑与数据修复任务保证。
- 两种建模：
  - 内嵌（embedding）：一对一、一对少（子项数量有界且不独立查询）→ 一次读取原子更新，无 JOIN。
  - 引用（referencing）：一对多且数量无界、子项需独立访问 → 存 `parentId`，靠 `$lookup` 或两次查询拼装。
- 关联查询工具：`$lookup`（左外连接，4.4+ 支持 `let` + 子管道、支持多键连接）、`$graphLookup`（递归查闭包，适合树/图，代价高）、`$unionWith`。
- 一致性怎么保：① 应用层事务（4.0+ 多文档事务、4.2+ 分片事务，但代价高、有时限，不适合高并发主链路）；② 双写 + 对账任务；③ 事件驱动（Change Streams 触发下游补偿）；④ 设计上让"一个聚合根一个文档"，把需要一致的内容收进同一个文档内（单文档写天然原子）。
- 为什么故意不做外键：强制参照校验意味着每次写都要跨文档/跨分片检查，与水平扩展目标冲突——这是分布式数据库的常见取舍（Cassandra、DynamoDB 同样不做）。

> 💡 提示
> "MongoDB 不能做关联"是误解。准确说法是：**关联能力有（$lookup/$graphLookup），但不该是设计的起点**——它慢、难下推到分片、且在写侧不提供任何保证。设计上先想"一次读取需要什么"，再决定内嵌还是引用。

> 🎯 关键要点
> - _id 就是主键，唯一约束靠 unique 索引
> - 无外键、无级联、无参照完整性检查
> - 内嵌优先，引用为辅，$lookup 是查询期拼装
> - 强一致靠"把内容收进一个文档"而不是事务
> - 不做外键是为水平扩展让路

> 🔍 追问
> - 订单和订单项，你内嵌还是分集合？判断依据是什么？
> - 没有外键，脏引用（orphan）怎么发现与清理？

### 9. MongoDB 的分析器（Profiler）是干什么用的？｜中级

核心结论：Profiler 是记录慢操作的内置开关，把实际执行的查询、耗时、扫描量写进 `system.profile` 集合，用来回答"这条到底慢在哪、扫了多少文档"。

- 三档级别：`db.setProfilingLevel(0)` 关闭（默认）；`1` 只记慢于 `slowms` 的；`2` 全记。
  - 例：`db.setProfilingLevel(1, { slowms: 100, sampleRate: 0.2 })` —— 采样 20% 的慢操作，降低开销。
  - 全局默认用 `operationProfiling.mode` / `.slowOpThresholdMs` 配在 `mongod.conf`。
- 查结果：`db.profileInfo()`、`db.system.profile.find().sort({ts:-1}).limit(20)`；关键字段 `op`、`ns`、`command`、`millis`、`nscanned`（扫的索引项/文档）、`nreturned`、`docsExamined`、`keysExamined`、`planSummary`（用了哪个索引）、`keysExamined/nReturned` 比值。
- 与 `currentOp` 的分工：Profiler 看**历史**，`db.currentOp({secs_running: {$gt: 5}})` 看**正在跑的**；`db.killOp(id)` 终止。
- 其他诊断入口：`mongostat`（集群级吞吐/锁/缺页）、`mongotop`（各命名空间读写耗时）、`db.serverStatus()`、Atlas Performance Advisor / Cloud Manager。
- 开销与边界：profiling 会写一个 capped 集合，级别 2 或高采样在繁忙库上明显增加写负担；它是**按库**开启的，不是全局一把梭。生产建议常开 `level 1 + slowms 100 + sampleRate 0.1~0.5`。

> 🎯 关键要点
> - 0/1/2 三档，配 slowms 与 sampleRate
> - 结果落在 system.profile（capped）
> - nscanned 与 nreturned 的比值是核心信号
> - currentOp 看现在，profiler 看过去
> - 别在生产开 level 2 全量记录

> 🔍 追问
> - 为什么采样率不是越高越好？
> - 一条查询 profiler 显示 keysExamined 很大、nReturned 很小，说明什么？

### 10. 什么是聚合（Aggregation）？｜中级

核心结论：聚合是"文档流经过一系列阶段、每个阶段做一次变换"的管道模型（`$match → $group → $project → $sort …`），是 MongoDB 做统计、派生与关系拼装的主工具，取代了早期的 mapReduce。

- 管道阶段（常用）：`$match`（过滤）、`$project`（选/算字段）、`$group`（分组聚合 `$sum/$avg/$push/$addToSet`）、`$sort`、`$limit/$skip`、`$unwind`（数组摊平成多行）、`$lookup`（关联）、`$addFields`、`$bucket`、`$facet`（一次跑多个子管道）、`$sample`、`$out/$merge`（结果写集合）、`$setWindowFields`（5.0+ 窗口函数）。
- 表达力：`$cond/$switch/$dateToString/$size/$map/$reduce` 等表达式可在阶段内做计算。
- 性能要点：
  - **`$match` 尽量放最前**，让索引先缩小数据集；规划器也会把 `$match`/`$sort`/`$limit` 往管道前推（pipeline 优化）。
  - 分片集合上，若 `$match` 含分片键则是 targeted 查询，否则 scatter-gather 打到所有 shard。
  - `$unwind` 会让文档数膨胀，放在 `$match` 之后、`$group` 之前。
  - 内存超 100MB/阶段会失败，加 `allowDiskUse: true` 允许落盘（或先 `$sort` 到索引上）。
  - 索引可服务 `$sort`/`$match`，复合索引顺序要匹配管道里的字段序。
- 与 mapReduce 的关系：mapReduce（5.0 起弃用）能做但更慢更啰嗦；官方结论是能不用就不用。
- 与"应用层聚合"的取舍：小结果集、逻辑复杂、要复用代码 → 应用层；大结果集、只要统计值 → 聚合（减少网络传输）。

> 💡 提示
> 聚合题的加分点是"管道顺序即性能"：同一个需求，`$match` 在前和 `$unwind` 在前的执行量可能差三个数量级。能顺手说出 `$match` 会被下推到 shard、`$sort` 能用索引序，就是实战水平。

> 🎯 关键要点
> - 管道模型：阶段串接、文档流变换
> - $match 前置、$unwind 慎用、$sort 走索引
> - allowDiskUse 处理超 100MB 阶段内存
> - 分片键决定 targeted 还是 scatter-gather
> - mapReduce 已弃用，用聚合

> 🔍 追问
> - 统计"每个用户最近 30 天订单金额分布"，你的管道怎么写？
> - 聚合出来的结果要复用，怎么落地（$out / $merge）？

## 复制、分片与引擎（5 题）

### 11. 什么是复制（Replication）？MongoDB 为什么靠它？｜初级

核心结论：复制是把同一份数据保存在多个节点上，用来容错和分摊读；MongoDB 的复制以副本集实现，写统一进主节点、通过 oplog 有序重放到从节点。

- 复制的三个收益：可用性（节点挂了别人接管）、耐久性（多数派确认才返回）、读扩展（从节点分担查询）。
- MongoDB 的做法：副本集（Replica Set）= 1 个 Primary + N 个 Secondary（+ 可选 Arbiter）；所有写只发生在 Primary，写操作以"逻辑增量"形式记进 `local.oplog.rs`（一个 capped 集合），Secondary 拉取 oplog 并重放。
- 关键机制：心跳（默认 2 秒一次）、选举（需要多数派投票，超时约 10 秒内选出新主）、`w:"majority"` 写关注（多数节点记入 oplog 才算提交）、oplog 窗口（决定从节点能容忍多长的断线，超出就要重做初始同步）。
- 与原稿"复制"表述的关系：原稿只写了一句"什么是复制"，实质考点是"oplog + 多数派 + 选举"这三件事。
- 术语澄清：MongoDB 早期的 Master-Slave 主从模式已被废弃（4.0 移除），现在只有副本集；别答成"主从复制"。

> 🎯 关键要点
> - 复制管可用性、耐久性与读扩展
> - 写只进 Primary，靠 oplog 重放到 Secondary
> - 选举要多数派，oplog 窗口决定断线容忍度
> - Master-Slave 已废弃，只有副本集

> 🔍 追问
> - oplog 太小会发生什么？怎么估合适的大小？
> - 为什么 MongoDB 不允许从 Secondary 直接写？

### 12. 什么是副本集（Replica Set）？它怎么完成故障转移？｜高级

核心结论：副本集是一组共享同一数据集、通过 oplog 保持同步的 mongod，成员用多数派投票选主；主节点失联后其余节点在秒级选出新主，客户端通过副本集名自动重连，不需要人工介入。

- 成员形态：
  - Primary：唯一接受写的节点。
  - Secondary：同步 oplog、可读（默认读不到，需配 read preference）。
  - Arbiter：只有投票权、不存数据——用于凑奇数票，**不要在生产放超过一个**（它不存数据，若它和少数派成一组会影响可用性判断）。
  - 特殊 Secondary：`priority: 0`（永不参选，适合异地灾备）、`hidden: true`（不进监控/读选择，做备份专用）、`votes: 0`（不参与投票）。
- 配置要点：`rs.initiate({_id:'rs0', members:[{_id:0,host:'h1:27017'},{...}]})`；最多 50 个成员但**只有 7 个有投票权**；`rs.conf()`/`rs.status()`/`rs.printReplicationInfo()`（看 oplog 窗口）；改配置用 `rs.reconfig()`，多数派失联时用 `{force:true}`（危险）。
- 故障转移流程：Primary 心跳丢失 → 其他成员把它标记为 unreachable → 触发选举（term/epoch 递增，只有数据不落后于多数派的节点能当选）→ 新主 `stepUp`，其余转为它的 Secondary → 客户端收到 `not primary` 错误后按副本集名重新发现拓扑并重连。
- 读偏好与"读到旧数据"：`primary` / `primaryPreferred` / `secondary` / `secondaryPreferred` / `nearest`；从 Secondary 读默认可能滞后（复制延迟），要"读己之写"就用 `majority` 写关注 + `readConcern: 'majority'`，或干脆读主。
- 延迟副本：`member: { optDate: Seconds }` 配一个故意滞后的 Secondary，用来兜住"误删数据"——比备份恢复快得多。
- 数据回滚：Secondary 上存在但新主没有的 oplog 条目会被回滚（写进 `rollback/` 目录的 BSON 文件），这是"未提交写被丢弃"的具体表现。

> ⚠️ 注意
> 副本集保证的是"多数派确认的写不丢"，**不保证不切换**。切换会带来：客户端短暂报错（要配重试与超时）、`w:"majority"` 在只剩多数派时延迟上升、Secondary 落后时读到旧数据。面试里能说出"切换期间的真实表现"，比背一遍选举流程更有说服力。

> 🎯 关键要点
> - 副本集 = 自动选主的复制组，不是简单主从
> - 50 成员上限、7 票、Arbiter 只投票
> - 读偏好 + readConcern 决定一致性强度
> - 延迟副本是防误删的实用手段
> - 回滚目录里是被丢弃的未提交写

> 🔍 追问
> - 三节点副本集挂一台，写还能继续吗？挂两台呢？
> - priority 0 的节点有什么用？
> - 跨机房部署副本集，你怎么设计成员与读偏好？

### 13. MongoDB 的分片（Sharding）是什么意思？怎么工作？｜高级

核心结论：分片是把一个集合的数据按 shard key 水平切散到多个副本集上，用配置服务器记录"哪个区间在哪个 shard"，由 mongos 负责路由——它解决的是单机内存与吞吐装不下的问题。

- 组件：`mongos`（无状态路由，客户端连它）、config server（**必须是 3 节点副本集**，存元数据：chunk 分布、集合分片状态）、shard（每个 shard 就是一个副本集，存实际数据）。
- shard key 规则：
  - 必须对集合已存在且覆盖分片键的索引（分片前建好索引）。
  - 4.6+ 起分片键**不可变**（历史版本要重建集合）；6.0 提供 `refineCollectionShardKey` 追加后缀字段来细化。
  - 三种策略：范围分片（`{created:1}`，利于范围查询但**新数据全打最后一个 shard**，形成热点）、哈希分片（`hash` 索引，写均匀但范围查询要广播）、复合（`{tenantId:1, created:1}`，兼顾隔离与范围）。
- chunk：分片内部的数据区间，默认目标大小 128MB（6.0 起由自动合并/拆分机制管理），balancer 在 shard 之间迁移 chunk 来均衡；单个 chunk 大到无法迁移就成了 jumbo chunk，是典型的运维告警。
- 查询路由：带分片键的查询 → targeted 到 1 个（或少数）shard；不带 → scatter-gather 广播所有 shard 再合并（`explain` 里能看到 `SHARDING_FILTER`）。**这是分片场景下性能的头号决定因素。**
- 限制与代价：跨 shard 的多文档事务（4.2+）代价高、有超时；`_id` 唯一性只在分片键前缀相同范围内由唯一索引保证（跨 shard 的唯一索引要求索引以分片键为前缀，否则无法强制全局唯一）；聚合里 `$group` 大结果要 `allowDiskUse`；balancer 迁移期有额外负载，要设维护窗口。
- 什么时候分片：数据量或吞吐超过单机能力（通常内存装不下工作集、或写吞吐到万级）、或需要按租户做物理隔离。**能用副本集解决的就别分片**——分片带来的运维复杂度是数量级的。

> 💡 提示
> 分片题最能区分水平的是"热点"三个字：用自增/时间单调字段做范围分片键，等于把所有写入压到最后一个 shard，分片形同虚设。给出"哈希或复合键打散写、同时保留查询定向能力"的折中，才算真懂。

> 🎯 关键要点
> - mongos + config server 副本集 + shard 副本集
> - 分片键要建索引、要防写热点、要能定向查询
> - 不带分片键的查询会广播，代价巨大
> - 跨 shard 唯一约束与事务都受限
> - 能不分就不分，副本集优先

> 🔍 追问
> - 一个集合按时间范围分片，为什么写入会集中在一个 shard？
> - 分片之后怎么做备份？和副本集有什么不同？
> - 怎么判断某个查询是 targeted 还是 scatter-gather？

### 14. MongoDB 的存储特性与内部原理是怎样的？｜高级

核心结论：现行版本用 WiredTiger 作为存储引擎——文档按 BSON 存在每集合独立的 B-tree 里，靠 MVCC 做文档级并发、journal + checkpoint 保证崩溃恢复、块压缩换 CPU 与空间，整棵工作集应尽量驻留内存。

- 引擎沿革：原始引擎 → mmapv1（内存映射文件，2GB 文件上限、命名空间 16MB 限制都来自它，4.0 移除）→ **WiredTiger**（3.2 起默认）；in-memory 引擎（企业版，纯内存）。
- 数据组织：`--dbPath` 下 WiredTiger 元文件 + 每个集合/索引一个 `collection-*.wt` / `index-*.wt` 文件；文档以 record id 定位，`_id` 上另有唯一索引。
- 并发控制：**文档级并发 + MVCC**，多个写可以命中同一集合的不同文档而互不阻塞（对比 mmapv1 的库级/集合级锁，这是吞吐差距的来源）；同一文档的写会串行化。
- 耐久与恢复：写操作先进内存 + 记 journal（默认约每 100ms 或 `w:"majority"` 相关策略刷盘），后台每约 60 秒做一次 checkpoint 落盘；崩溃后"checkpoint + 重放 journal"恢复。
- 压缩：块级 snappy（默认）/ zlib / zstd，前缀压缩减少索引体积；典型压缩比 2~5 倍，代价是 CPU。
- 缓存：`wiredTigerCacheSizeGB` 默认 `(物理内存 - 1GB) / 2`（6.2 起改为更平滑的策略）；缓存是"工作集"的守门人，命中率下降会引发磁盘读放大——这是 MongoDB 性能断崖的最常见原因。
- 内存映射与页：WT 自己管理缓存与淘汰，不再像 mmapv1 那样依赖 OS 的 mmap 换页（当年"mmap 缺页导致抖动"的讨论已成历史）。
- oplog 与复制：`local.oplog.rs` 是 capped 集合，写路径是"应用 → 记 oplog → 多数派确认"；oplog 窗口决定 Secondary 断线容忍时长。
- 观测：`db.coll.stats({index:1})` 看 `wiredTiger` 段（cache 命中率、concurrent transactions、block-manager 读写）、`db.serverStatus().wiredTiger`、`db.stats()` 的 `size` vs `storageSize`。

> ⚠️ 注意
> 原稿那代的答案会讲"数据文件按 2 倍增长、单文件 2GB、命名空间 24000 上限"——这些全是 mmapv1 的特征，在 WiredTiger 上都不成立。今天答存储原理，主线应该是"文档级 MVCC + journal/checkpoint + 压缩 + 缓存命中率"。

> 🎯 关键要点
> - WiredTiger：每集合/索引一个文件，文档级 MVCC
> - journal 保耐久，checkpoint 定恢复点
> - 压缩换空间，代价是 CPU
> - 缓存命中率是性能生命线
> - mmapv1 那套限制已成历史

> 🔍 追问
> - 一台 32GB 内存的机器，WT 缓存设多大？为什么不能设成 30GB？
> - 文档级并发和 InnoDB 的行级锁差别在哪？
> - 集合 size 很大但 storageSize 小，说明什么？

### 15. MongoDB 有哪些可替代产品？｜中级

核心结论：替代者分三类——带 JSON 能力的关系型（PostgreSQL）、其他文档库（CouchDB）、其他 NoSQL（DynamoDB/Cassandra/Redis/ES）；真正的答案取决于访问模式，而不是"谁更好"。

| 产品 | 类型 | 相对 MongoDB 的定位 |
|---|---|---|
| PostgreSQL + JSONB | 关系型 + 文档 | 最强通用替代：既有 schema 约束、事务、JOIN，又有文档与 GIN 索引 |
| CouchDB | 文档 | 同为文档模型，HTTP API + 主主复制 + 离线同步（PouchDB） |
| DynamoDB | KV/文档（托管） | 超大规模点查与自动扩展，牺牲查询表达力 |
| Cassandra / ScyllaDB | 宽列 | 写吞吐与多活扩展更强，查询必须按建模好的模式来 |
| Redis | KV | 内存级延迟、数据结构丰富，但容量与耐久性有限 |
| Elasticsearch | 搜索 | 全文/聚合分析强，不是主存储（常与 MongoDB 并存） |
| ClickHouse | 列式分析 | 大范围聚合分析的量级碾压聚合管道 |
| Cosmos DB / Firestore | 多模型/文档（托管） | 云厂商绑定换取托管体验 |

- 选 MongoDB 而不是 Postgres 的理由：模式频繁演进、水平分片是刚需、文档天然成块、团队熟悉 JS/BSON 生态。
- 选 Postgres 而不是 MongoDB 的理由：需要强一致事务与外键、复杂关联分析、成熟 BI 工具链、运维人手有限（少一个组件）。
- 现实里最常见的是组合：MongoDB 存业务对象 + Elasticsearch 做搜索 + Redis 做缓存 + 数仓做分析，而不是"一个数据库打天下"。
- 迁移成本提醒：从 MongoDB 迁到 Postgres 不是改连接串——模式设计、驱动、事务边界、索引策略都要重做。

> 🎯 关键要点
> - PostgreSQL JSONB 是最常被低估的替代
> - 分片刚需与模式演进是 MongoDB 的主场
> - 强事务与复杂 JOIN 该回关系型
> - 生产上多是组合而非单一替代

> 🔍 追问
> - 如果只能选一个，Postgres 还是 MongoDB？给一条决定性理由
> - 已有 MongoDB 还要上 Elasticsearch，值不值？
