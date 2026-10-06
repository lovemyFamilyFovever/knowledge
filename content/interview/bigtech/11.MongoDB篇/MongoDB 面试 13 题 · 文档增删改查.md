---
title: "MongoDB 面试 13 题 · 文档增删改查"
tags: ["MongoDB", "数据库", "CRUD"]
source: "github"
source_path: "interview_internal_reference / 11.MongoDB篇"
collected: "2026-09-23"
status: "stable"
---

本页收录 13 道 MongoDB 库/集合操作与文档增删改查题，覆盖集合与库的创建查看删除、连接观测、插入与批量写入、更新与原子操作、条件查询与排序；难度分布为初级 8 题、中级 5 题，每题附核心结论与面试官追问。

> 💡 说明
> **上游仓库 `interview_internal_reference` 的 MongoDB 篇里，本页 13 题有 12 题只有题干、正文完全为空**（原仓库标注"持续更新中"，这部分从未写完）。本库按现行 MongoDB 7.x/8.x 的 `mongosh` 语法补写了全部答案，命令口径以官方文档为准；仅"查看连接"一题上游有一句话答案（且把 `connPoolStats` 当成通用命令，本页已修正其适用范围）。

## 库与集合操作（5 题）

### 1. 如何创建一个集合？｜初级

核心结论：集合通常由首次插入隐式创建；需要指定校验规则、封顶大小、时序属性时才用 `createCollection` 显式创建。

- 隐式：`db.orders.insertOne({ item: 'x' })` —— 集合不存在就顺手建出来。
- 显式：`db.createCollection("orders", { validator: {...}, validationLevel: "strict" })`。
- 常用选项：

| 选项 | 作用 |
|---|---|
| `capped: true` + `size` | 封顶集合，按插入顺序环形覆盖，天然 FIFO |
| `max` | capped 集合的最大文档数 |
| `validator` | `$jsonSchema` 规则，写入时校验 |
| `validationLevel` | `strict` / `moderate`（只校验已有合法文档） |
| `validationAction` | `error`（默认）/ `warn` |
| `timeseries: { timeField, metaField, granularity }` | 时序集合（5.0+） |
| `expireAfterSeconds` | TTL 索引，按字段自动过期删除 |
| `clusteredIndex` | 按指定索引物理聚簇存储（5.3+） |
| `changeStreamPreAndPostImages` | 变更流带前后镜像（6.0+） |

- 命名限制：不能含 `$`、不能有 null 字符、不能以 `system.` 开头；保留名如 `oplog.rs` 不可占用。
- 权限：建集合需要 `createCollection` 动作权限。

> 🎯 关键要点
> - 默认隐式创建，显式创建是为了带选项
> - validator 是防脏数据的第一道闸
> - capped 集合适合日志环形缓冲
> - TTL 索引实现"自动过期删除"

> 🔍 追问
> - 为什么生产上建议显式建集合？
> - capped 集合和普通集合在删除与更新上有什么不同？

### 2. 如何查看已经存在的集合？｜初级

核心结论：`show collections` 看当前库的集合名，`db.getCollectionNames()` 拿数组，`db.listCollections()` 拿到带选项与统计的完整信息。

- 三种粒度：
  - `show collections` —— 只列名字，最快。
  - `db.getCollectionNames()` —— 返回字符串数组，适合脚本。
  - `db.listCollections({ name: /^order/ })` —— 返回文档，含 `type`、`options`（validator、capped 等）；加 `--nameOnly` 可省开销。
- 看规模：`db.coll.stats()`（`count`、`size`、`storageSize`、`nindexes`、`avgObjSize`）；`db.coll.estimatedDocumentCount()` 走元数据、快且不精确；`db.coll.countDocuments({})` 精确统计、可带过滤条件。
- 权限：非管理员只能看到自己有权限的集合。
- 坑：`db.coll.count()` 在 6.0 起被弃用（mongosh 里仍可用但会告警），新代码用上面两个方法。

> ⚠️ 注意
> `stats()` 返回的 `count` 是估算值（来自集合元数据），副本集上不同节点、刚做完大批量写入后都可能不一致。要精确数就用 `countDocuments`，但它是真扫，大集合上很慢——面试里能区分这两者就够了。

> 🎯 关键要点
> - show collections / getCollectionNames / listCollections 三档
> - listCollections 才能看到 validator 等选项
> - estimated 快而粗，countDocuments 准而慢
> - 集合很多时列集合本身就有成本

> 🔍 追问
> - 一个库 3000 个集合，`show collections` 慢怎么办？
> - 怎么批量导出所有集合的 schema 校验规则？

### 3. 如何删除一个集合？｜初级

核心结论：`db.coll.drop()` 删除集合及其全部索引；它比"删光文档"快得多，因为不用逐条写 oplog，但删除后自增/唯一性等业务语义要自己重建。

- 三种做法对比：

| 做法 | 机制 | 速度 | 是否保留索引/选项 |
|---|---|---|---|
| `db.coll.drop()` | 直接丢弃集合与其索引 | 极快 | 否，全部消失 |
| `db.coll.deleteMany({})` | 逐条删除并写 oplog | 慢 | 是 |
| 重命名 `renameCollection` | 换个名字挪走 | 快 | 是 |

- 返回值：`drop()` 返回 `true`；集合不存在时返回 `false`（不报错）。
- 空间：WiredTiger 会把释放的空间用于后续同库写入，但**磁盘文件不一定立刻变小**；要归还给 OS 需 `compact`（会阻塞该节点，需在副本集上逐节点滚动做）。
- 风险：drop 不产生可回滚事务，副本集会把删除复制到所有成员；生产上建议"先 rename 观察几天再 drop"。

> 🎯 关键要点
> - drop 快、deleteMany({}) 慢，语义完全不同
> - drop 会连索引和 validator 一起没了
> - 磁盘空间不会自动归还，compact 有代价
> - 生产删集合先改名再删

> 🔍 追问
> - 为什么 deleteMany({}) 在亿级集合上是危险操作？
> - drop 之后想恢复，有哪些路子？

### 4. 如何删除（除去）一个数据库？｜初级

核心结论：`db.dropDatabase()` 删除**当前所在库**的全部集合、索引与元数据；它是不可回滚的高危动作，且必须先 `use` 到目标库——没有 `dropDatabase("name")` 这种带参写法。

- 步骤：`use mydb` → `db.dropDatabase()` → 返回 `{ ok: 1, dropped: 'mydb' }`。
- 危险点：`db` 是当前库对象，忘了 `use` 就会删错库；脚本里必须显式断言 `db.getName() === expected`。
- 分片集群：在 mongos 上 drop 会跨 shard 清理；在单个 shard 上直接 drop 会造成元数据不一致，属于运维事故。
- 权限：需要 `dropDatabase` 动作权限；默认没有给应用账号。
- 空间：与 drop 集合一样，磁盘不保证立即归还。
- 替代方案：多租户场景优先考虑"按字段隔离 + 索引前缀"，而不是每租户一个库——建库容易删库难。

> ⚠️ 注意
> 这题最该说的不是命令，而是防护：生产账号不给 `dropDatabase` 权限、开启审计日志（Enterprise/Atlas）、脚本里加库名断言、重要库定期快照。能主动讲防护，说明你不会写出删库脚本。

> 🎯 关键要点
> - db.dropDatabase() 作用于当前库，无参数形式
> - 不可回滚，副本集全成员同步删除
> - 分片集群别在 shard 上直接 drop
> - 用权限与脚本断言做防护

> 🔍 追问
> - 误删库之后你的恢复路径是什么？
> - 为什么"一个租户一个库"在 MongoDB 里要谨慎？

### 5. 怎么查看当前有哪些客户端连着 MongoDB？｜中级

核心结论：服务端看 `db.serverStatus().connections` 与 `db.currentOp({type:'conn'})`，客户端侧的连接池统计要用 `connPoolStats`——但它是 **mongos** 的命令，单机 mongod 上没有意义。

- 连接计数：`db.serverStatus().connections` → `current`（当前活跃）、`available`（还能接多少）、`totalCreated`（累计建立数）。
- 谁在连：`db.currentOp({ type: 'conn' })`（4.2+）列出每个连接会话；`db.currentOp({ active: true })` 看正在执行的操作；`db.auths()` 看已认证用户。
- 上限：`net.maxIncomingConnections`（默认 8388608，实际受 `ulimit -n` 与内存约束）；每个连接约占 1MB 栈内存，几千连接就要认真规划。
- `connPoolStats` 的正确位置：在 **mongos** 上执行，返回它到各 shard 的连接池（`numWaitingForConnections`、`poolId` 等），用于排查"路由到某个 shard 的连接被打满"。
- 排查套路：连接数异常 → 先看是不是应用没复用连接（每次请求新建 client）、再看驱动池参数（`maxPoolSize` 默认 100）、最后看有没有慢操作把连接占住（`currentOp` 里 `secs_running`）。

> 🎯 关键要点
> - serverStatus().connections 看总量，currentOp 看明细
> - connPoolStats 是 mongos 的命令，不是通用命令
> - 连接是稀缺资源，客户端必须复用与限池
> - 连接打满常由慢查询占位引起

> 🔍 追问
> - 应用连接池设多大合适？依据是什么？
> - 副本集发生主从切换后，客户端连接会怎样？

## 写入与更新（4 题）

### 6. 如何在集合中插入一个文档？｜初级

核心结论：`insertOne()` 插一条（`insert()` 已弃用）；不写 `_id` 时客户端自动生成 ObjectId，插入是"要么成功要么失败"的单文档原子操作。

- 基本形态：`db.orders.insertOne({ sku: 'A1', qty: 2, created: new Date() })` → 返回 `{ acknowledged: true, insertedId: ObjectId(...) }`。
- `_id` 规则：客户端可以先塞自定义 `_id`（字符串、整数都行），服务端缺省才生成 ObjectId；重复 `_id` 报 `E11000 duplicate key error`。
- 单文档写天然原子：一个文档内多个字段的修改不会被别人看到"半更新"状态。
- 大文档：BSON 上限 16MB，超了要么拆分引用，要么 GridFS（本质是分块存储，仍不推荐放业务大对象）。
- 常见坑：① 忘记 `created` 用 `new Date()` 而写成字符串，导致范围查询与 TTL 索引失效；② 数值默认是 double，需要精确用 `NumberLong`/`Decimal128`；③ 嵌套对象里的键顺序影响唯一索引匹配。

> 🎯 关键要点
> - 用 insertOne，别用旧的 insert
> - _id 可自定义，重复即 E11000
> - 单文档写原子，跨文档要事务
> - 时间与数值类型要显式，别写字符串

> 🔍 追问
> - 自定义 `_id` 相比 ObjectId 有什么优劣？
> - 插入报 E11000，你的代码应该怎么处理？

### 7. 批量插入怎么写？ordered 和写关注分别控制什么？｜中级

核心结论：`insertMany()` 批量插入，`ordered` 决定遇错是否中断，写关注 `w` 决定"多少副本确认才算成功"——两者共同决定吞吐与数据安全性的边界。

- 批量：`db.orders.insertMany([...], { ordered: false, writeConcern: { w: 'majority', wtimeout: 5000 } })`。
- `ordered: true`（默认）：按数组顺序插入，遇到第一条失败就停止，后面的不执行；`false`：跳过失败继续插完，最后汇总错误。恢复类场景用 true（保证顺序），导入类场景用 false（最大化成功数）。
- 写关注（write concern）：

| 配置 | 含义 | 代价 |
|---|---|---|
| `w: 1`（默认） | 主节点落盘即返回 | 主节点崩溃可能丢写 |
| `w: "majority"` | 多数副本记入 oplog 才返回 | 延迟升高，防"已写被回滚" |
| `w: n` | n 个节点确认 | 需保证 n 个成员健康 |
| `journal: true` | 额外要求写 journal | 更强耐久，延迟更高 |
| `j:true` 已弃用 | 用 `w:"majority"` 或 `w:"j"` 的新写法 | — |

- 读关注（read concern）配套：`local`（默认）/ `committed` / `majority` / `linearizable`，决定你读到的文档是否可能"未提交"。
- 性能实践：批量比逐条快一个量级（少往返）；但单批也别太大（受 48MB 消息上限与内存约束，几千条一批较稳）；导入时先建索引不如后建索引快。
- 幂等导入：用确定性 `_id`（如业务单号）+ `ordered:false`，重跑时 E11000 可安全忽略。

> 💡 提示
> "写关注设成 majority 就绝对不丢数据"是错的——它防的是"主节点已确认但尚未复制到副本就崩溃导致写被回滚"这一类问题，不覆盖"整个多数派同时故障"。要真正耐久还得配合 journal 与备份。

> 🎯 关键要点
> - insertMany + ordered 控制"遇错停不停"
> - w:majority 防已确认写被回滚，不是万能保险
> - 读关注 committed 配合事务才有意义
> - 批量插入用确定性 _id 做幂等

> 🔍 追问
> - 导入 1 亿条数据，你的参数怎么配、索引什么时候建？
> - majority 写关注和"两阶段提交"是什么关系？

### 8. 如何更新文档？原子操作符有哪些？｜中级

核心结论：用 `updateOne/updateMany/replaceOne` 加更新符（`$set/$inc/$push/...`）做局部原子更新，而不是"读出来改完写回去"——后者在并发下会互相覆盖。

- 三种更新：
  - `updateOne(f, { $set: {...} })` —— 改第一条匹配。
  - `updateMany(f, { $inc: { n: 1 } })` —— 改所有匹配。
  - `replaceOne(f, doc)` —— 整篇替换（除 `_id` 外全换），会丢未列出的字段。
- 常用更新符：`$set`、`$unset`、`$inc`、`$mul`、`$min/$max`、`$currentDate`、`$push`（配 `$each/$slice/$sort/$position`）、`$addToSet`、`$pull`、`$pullAll`、`$pop`、`$rename`、`$bit`。
- 数组定位：位置符 `items.0.qty`、`$`（第一个匹配元素）、`$[]`（全部）、`$[<ident>]` + `arrayFilters`（按条件筛选，最常用）。
- upsert：`{ upsert: true }` 没有匹配就插入；`insertedId` 与 `matchedCount/upsertedCount` 用来判断到底发生了什么。
- 聚合式更新（4.2+）：`updateOne(f, [{ $set: { total: { $multiply: ['$price', '$qty'] } } }])`，新值可以基于旧字段计算。
- 并发正确姿势：`updateOne({ _id: id, version: v }, { $set: { ...fields, version: v+1 } })`，靠 `matchedCount` 判断有没有被别人抢先——这就是文档型数据库的乐观锁。
- 返回体字段（6.0+ 统一）：`acknowledged`、`matchedCount`、`modifiedCount`、`upsertedCount`、`upsertedId`。注意 matched 与 modified 不同（值一样时 matched 有、modified 为 0）。

> ⚠️ 注意
> 不要用"先 find 再 replaceOne 整篇写回"来模拟更新：两个请求之间文档被别人改过，就会静默覆盖。所有更新都应下沉成服务端原子操作符，或者用版本号做 CAS。这是 MongoDB 线上事故的头号来源。

> 🎯 关键要点
> - 局部更新用 $set 等符，别整篇替换
> - 数组更新靠 arrayFilters，别用固定下标
> - upsert 适合计数与首次写入
> - 并发安全靠版本号 CAS 或原子符
> - matchedCount ≠ modifiedCount

> 🔍 追问
> - 库存扣减用 MongoDB 怎么做才不会超卖？
> - 为什么 `replaceOne` 容易丢字段？

### 9. 如何删除文档？｜初级

核心结论：`deleteOne(filter)` 删一条、`deleteMany(filter)` 删多条，都是服务端原子操作；删空集合用 `drop()` 而不是 `deleteMany({})`。

- 基本形态：`db.orders.deleteMany({ status: 'cancelled', created: { $lt: cutoff } })`。
- 返回：`{ acknowledged: true, deletedCount: n }`。
- 只删一条并想控制"是哪一条"：先 `find().sort().limit(1)` 拿到 `_id` 再按 `_id` 删，或用 6.10+ 的 `deleteOne` + `sort` 选项（驱动支持时）。
- 自动过期：给时间字段建 TTL 索引 `db.coll.createIndex({ created: 1 }, { expireAfterSeconds: 86400 })`，后台线程每 60 秒扫一次删除过期文档——注意 TTL 删除有最多 60 秒延迟，且副本集上只在主节点算、通过 oplog 传播。
- 性能：`deleteMany({})` 会为每个文档写一条 oplog 删除记录，大集合上极慢且会撑大 oplog；清空请用 `drop()`。
- 软删除模式：`{ isDeleted: true }` + 部分索引 `partialFilterExpression`，便于回收站与审计，但要记得物理清理。

> 🎯 关键要点
> - deleteOne/deleteMany 按过滤条件原子删
> - 清空用 drop，不用 deleteMany({})
> - TTL 索引实现自动过期，有 60 秒粒度
> - 软删除配部分索引，避免索引无限膨胀

> 🔍 追问
> - TTL 索引为什么不能保证精确时刻删除？
> - 误删文档后有哪些恢复手段？

## 查询与排序（4 题）

### 10. 如何查询集合中的文档？｜初级

核心结论：`find(filter, projection)` 返回游标，配合 `sort/limit/skip` 与链式操作；真正取数据是在遍历游标时按批（默认首批 101 条）从服务端拉取。

- 常用形态：
  - `db.coll.find()` 全部；`db.coll.findOne({ _id: id })` 一条。
  - 条件：`{ age: { $gte: 18, $lt: 60 } }`、`{ tags: 'vip' }`（数组包含）、`{ name: /^张/ }`（正则）。
  - 投影：`db.coll.find({}, { name: 1, _id: 0 })`。
  - 分页：`.sort({ _id: -1 }).limit(20)`，深分页用游标式 `filter: { _id: { $lt: lastId } }` 而不是 `skip(100000)`。
- 操作符分类：比较（`$eq/$ne/$gt/$gte/$lt/$lte/$in/$nin`）、逻辑（`$and/$or/$nor/$not`）、元素（`$exists/$type`）、数组（`$all/$elemMatch/$size`）、字符串（`$regex`）、评估（`$expr` 让条件里能引用字段做计算）。
- 游标特性：默认 10 分钟无活动超时（`noCursorTimeout` 可关，但要自己负责关闭）；`batchSize` 控制每批条数；`hint()` 强制走某索引；`explain('executionStats')` 看是否 `IXSCAN`、`docsExamined` 与 `keysExamined`。
- 判读 `explain` 的三个数：`nReturned`、`docsExamined`、`keysExamined` —— 前两者接近说明索引选得好；`docsExamined` 远大于 `nReturned` 就是要补索引或改查询。

> ⚠️ 注意
> `$type`、`$exists`、正则前导通配、`$where`、`$regexOptions` 里的 `i` 忽略大小写——这几类都可能让索引失效。特别是大小写不敏感正则：要么建 collation 索引，要么存一个小写冗余字段。

> 🎯 关键要点
> - find 返回游标，遍历时才真正取数
> - 投影 + 排序 + 游标式分页是三板斧
> - explain 看 docsExamined/nReturned 比值
> - 深分页的 skip 是隐形成本
> - 大小写不敏感查询要专门设计索引

> 🔍 追问
> - 一个查询扫了 100 万文档返回 20 条，你第一步做什么？
> - skip 分页和游标分页的取舍是什么？

### 11. 怎么让查询结果输出得更易读（格式化输出）？｜初级

核心结论：旧 shell 用 `pretty()`，`mongosh` 里默认就是格式化输出（可折叠的 EJSON），要机器可读用 `EJSON.stringify` 或导出 JSON。

- `mongosh`：结果默认以带缩进、可展开的 EJSON 显示，日期显示为 `ISODate(...)`；`config.set('displayBatchSize', 50)` 控制一次显示条数。
- 旧 `mongo` shell：`db.coll.find().pretty()` 才缩进输出（这是原稿那代的答案）。
- 脚本化输出：`mongosh --quiet --eval 'EJSON.stringify(db.coll.find().toArray())' > out.json`；`JSON.stringify` 会丢掉 ObjectId/Date 的类型信息，EJSON 不会。
- 导出：`mongoexport --db mydb --coll orders --jsonArray --pretty -o orders.json`（`--type csv --fields` 出 CSV）。
- 单字段查看：`db.coll.findOne()._id`、`printjson(doc)`。

> 🎯 关键要点
> - mongosh 默认格式化，pretty() 是旧 shell 的写法
> - 脚本里用 EJSON 不用 JSON.stringify
> - 批量导出走 mongoexport
> - 版本口径要说清楚，别混答

> 🔍 追问
> - 为什么 JSON.stringify 一个文档会丢信息？
> - 怎么把查询结果直接喂给 jq 处理？

### 12. 怎么用 AND / OR 组合条件并遍历结果？｜中级

核心结论：AND 直接写在同一个对象里就成立，`$and` 只在"同一字段多个条件"或"多条件取反"时才必要；`$or` 要命中索引，参与分支的每个字段都得有索引。

- AND：`db.coll.find({ status: 'paid', amount: { $gte: 100 } })` —— 隐式 AND。
- 必须用 `$and` 的情况：`{ $and: [{ age: { $gte: 18 } }, { age: { $lt: 30 } }] }`（同一字段写两次，不能塞进同一个对象）；`{ tags: { $ne: 'x', $exists: true } }` 这类也要拆开。
- OR：`db.coll.find({ $or: [{ type: 'a' }, { owner: 'u1' }] })`。
- `$in` 优于 `$or`：`{ type: { $in: ['a','b','c'] } }` 比三个分支的 `$or` 更简洁，且走同一个索引，规划器更容易选到 `IXSCAN`。
- 索引与 `$or`：每个分支字段都要有可用索引，否则整体退化为全表扫（4.4+ 的 `OR` 合并做了改进，但仍依赖分支索引）。
- 遍历结果：
  - `for (const doc of await cursor.forEach(...))` / `cursor.forEach(fn)`；
  - `while (await cursor.hasNext()) { const d = await cursor.next(); }`；
  - 大批量用 `cursor.batchSize(5000)` + 流式处理，别 `toArray()` 把 100 万条拉进内存；
  - 聚合替代：`$match` 里天然支持 `$and/$or`，且能配 `$project` 只取需要的字段。
- 逻辑取反：`$nor` 能表达"两个条件都不满足"，比手写 `$and:[{$ne},{$ne}]` 清晰。

> 💡 提示
> 这题真正的区分点是"$or 走不走索引"。能答出"每个分支字段都要有索引，否则整个查询全表扫"，并顺手说出 `$in` 通常比 `$or` 更好，就是这题的高分线。

> 🎯 关键要点
> - 同对象即 AND，$and 只在字段复用时才需要
> - $in 一般优于多分支 $or
> - $or 要求每个分支都有索引
> - 大结果集流式遍历，不要 toArray
> - $nor 表达"都不满足"

> 🔍 追问
> - 一个 $or 查询走了 COLLSCAN，你怎么排查？
> - 遍历 500 万条做数据修复，你怎么写才不打爆内存？

### 13. 如何对查询结果排序？｜中级

核心结论：`sort({ field: 1 })`（1 升序、-1 降序），链式顺序必须是 `find().sort().limit().skip()`；排序最好由索引提供，否则超过 32MB 的内存排序会直接报错。

- 基本：`db.coll.find().sort({ created: -1, _id: -1 })` —— 第二排序键用来保证分页稳定（同一时间戳的文档不会在翻页时重复或漏掉）。
- 索引提供顺序：建 `{ created: -1 }` 或复合 `{ status: 1, created: -1 }`，`explain` 里 `sortPattern` 被满足、`executionStages` 中没有 `SORT` 阶段即为索引排序。
- 不走索引会怎样：内存排序上限 32MB，超出报 `Sort exceeded memory limit of 32 bytes`；`find()` 不能加 `allowDiskUse`（那是聚合的选项），只能建索引、缩小结果集，或改用聚合管道 `sort` + `allowDiskUse: true`。
- 复合排序方向：`{ a: 1, b: -1 }` 需要索引 `{ a: 1, b: -1 }` 完全匹配；方向不一致时索引 `{a:1,b:1}` 帮不上忙（反向扫描只支持整体反向）。
- 自然顺序：`$natural` 按磁盘/插入顺序，只对 capped 集合有意义，别在生产查询里依赖。
- 中文/大小写排序：用 collation（`{ locale: 'zh', strength: 2 }`），并让索引带同样 collation，否则索引无法用于排序。

> ⚠️ 注意
> 深分页 + 排序是最容易出线上事故的组合：`skip(500000).limit(20)` 会真的扫过并丢弃 50 万个文档。正确做法是游标式分页——把上一页最后一行的排序键值放进 filter（`{ created: { $lt: lastSeen } }`），配合 `{ created: -1 }` 索引，每页成本恒定。

> 🎯 关键要点
> - sort 要在 limit/skip 之前，链式顺序有讲究
> - 排序尽量交给索引，32MB 内存排序会报错
> - 加 _id 作第二排序键保证翻页稳定
> - 深分页改游标式，不用 skip
> - 中文排序靠 collation，索引要同配置

> 🔍 追问
> - 一个排序查询报 32MB 超限，你有哪几种解法？
> - 为什么"按时间倒序取前 100 万条"永远不该用 skip 翻页？
