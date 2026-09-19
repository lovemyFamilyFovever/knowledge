---
title: "GraphQL Schema 与 Resolver 设计"
tags: []
source: "baike"
source_path: "技术文章 / Web开发框架"
collected: "2026-09-05"
status: "imported"
---

# GraphQL Schema 与 Resolver 设计

> 📌 **导航**：本文是 **GraphQL Schema 与 Resolver 设计** 词条，属于 frontend-frameworks 术语集。相关枢纽：[[GraphQL从入门到精通]]、[[GraphQL实践]]。

## 定义

**一句话定义：** SDL 用类型系统声明一个 GraphQL 服务"能取什么、能改什么"的契约，Resolver 把契约里的每个字段落到真实数据源——前者是对外承诺、后者是兑现承诺的实现，二者共同构成服务端的核心。

**通俗类比：** SDL 像菜单，写明有哪些菜、每道菜的配料和必点/可选项；Resolver 像后厨的分工表，规定"这行字由谁去哪个冰箱拿什么"，菜单只承诺、后厨才出菜。

## 为什么需要它

没有类型契约，字段就是散落的字符串，前后端只能靠口头约定同步；有了 SDL，schema 可被工具校验、可生成客户端类型、字段弃用有标注。而字段级 Resolver 让"按需取数"成为可能——每个关联字段是一段独立取数逻辑，灵活但也要求把鉴权、批量、错误处理都组织进这四参数的解析体系里，否则越灵活越失控。

## 核心机制

- **类型系统**：`scalar`（自定义标量如 Date、JSON）、`enum`（角色枚举）、`interface`（共享 `id: ID!` 的 Node）、`union`（搜索可返回 User/Post/Comment）、`input`（带默认值的入参对象）、`type`（对象，`implements` 接口）。非空用 `!`、列表用 `[T!]!` 表达"必是数组且每项非空"。
- **分页契约**：游标分页用 `Connection` 三件套——`edges`（每个 `Edge` 含 `node` 与 `cursor`）、`pageInfo`（`hasNextPage`/`startCursor`/`endCursor`）、`totalCount`，比 offset 更能扛并发写入下的翻页漂移。
- **变更与错误**：Mutation 统一收单个 `input` 入参，返回 Payload 同时含业务字段与 `errors: [UserError!]!`（`field`/`message`/`code` 枚举）。可预期的业务错走数据返回、不抛异常，让客户端能区分"表单校验失败"与"系统故障"。
- **Resolver 四参**：`(parent, args, context, info)`——parent 是父字段返回值、args 是入参、context 放鉴权身份与 DataLoader、info 含本次查询的 AST（用于按被请求字段做投影或逐字段监控）。字段级解析可实现计算字段、条件字段（按角色把 email 返回 null 隐藏敏感信息）。
- **组织与中间件**：可用组合把一个 Resolver 复用进另一个（并行 Promise.all）、用插件的 `willResolveField` 做逐字段计时、用 class 装饰器（`@Authorized(['ADMIN'])`）声明式挂权限；自定义标量实现 serialize/parseValue/parseLiteral 三段式完成编解码。

## 具体示例

```graphql
type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
}
type CreateUserPayload {
  user: User
  errors: [UserError!]!   # 业务错作为数据返回
}
```

## 何时用与何时不用

- **用**：以 schema 为单一契约演进、需要客户端类型生成与字段弃用管理；关联字段多、要在字段级做鉴权投影时。
- **不用/从轻**：接口极少、契约不会演进时，一套轻量路由比维护完整类型图划算；把大量业务逻辑塞进 Resolver 会变成"分布式 if"，应下沉到 service 层。

## 优劣与代价

✅ 契约先行、可校验可生成，字段级解析让"隐藏某列/合并多源"就近完成。
✅ Payload + errors 约定把错误变数据，客户端处理表单错误更一致。
⚠️ 字段级解析放大底层调用（N+1），必须配批处理，见 [[N+1 问题与 DataLoader]]。
⚠️ 深嵌套类型图与 interface/union 的 `__resolveType` 增加心智负担与测试面。

## 与相关概念的区别

- **vs [[OpenAPI 规范]]**：OpenAPI 描述的是"端点形状"（路径、方法、状态码），SDL 描述的是"类型图"（字段与关系）；两者都是可校验契约，切面不同。
- **vs [[GraphQL实践]]**：后者讲 GraphQL 整体能力与选型，本篇专讲服务端如何用 SDL 立约、用 Resolver 兑现。
- **vs [[RESTful API 设计]]**：REST 的资源与状态码语义在此由类型系统与 Mutation Payload 承接。

## 常见误区

- 把业务逻辑直接堆在 Resolver 里，让 schema 层变成难以测试的巨型 if。
- 用 `throw` 处理所有错误，客户端就无法区分表单校验失败与服务器故障。
- 以为字段一定要一一对应数据库列，其实 Resolver 可聚合多源、可返回 null 隐藏。

## 面试速答

> 🎯 SDL 用类型系统（标量/枚举/接口/联合/输入/对象 + Connection 游标分页）声明能取能改的契约，Mutation 用 Payload+errors 把业务错当数据；Resolver 以 parent/args/context/info 四参把字段落到数据源，字段级可做鉴权投影与批处理。

## 相关术语

[[GraphQL从入门到精通]]、[[GraphQL实践]]、[[N+1 问题与 DataLoader]]、[[GraphQL 实时订阅与文件上传]]、[[OpenAPI 规范]]、[[RESTful API 设计]]

## 参考资料

建议人工核验：可参考 GraphQL 官方文档（graphql.org）关于 SDL、Relay Connection 分页规范与 Apollo Server 的 Resolver/错误约定。本篇合并自原《GraphQL从入门到精通》§2 Schema 定义语言（SDL）与 §3 Resolver 设计模式两节，原稿约 24 块 SDL/JS 代码按 v1.2 §8.1 收敛为散文与一段示例，仅保留契约要义不逐行照搬；原稿无相关可核验文献编号。
