---
title: "GraphQL 实时订阅与文件上传"
tags: []
source: "baike"
source_path: "技术文章 / Web开发框架"
collected: "2026-09-05"
status: "imported"
---

# GraphQL 实时订阅与文件上传

> 📌 **导航**：本文是 **GraphQL 实时订阅与文件上传** 词条，属于 frontend-frameworks 术语集。相关枢纽：[[GraphQL从入门到精通]]、[[GraphQL实践]]。

## 定义

**一句话定义：** Subscription 让服务端在事件发生时把数据主动推给已订阅的客户端（跑在 WebSocket 长连接上），文件上传则用 Upload 标量把 multipart 请求映射进 Mutation——两者都超出了 Query/Mutation 的请求—响应模型，是 GraphQL 的两条"非常规传输"支线。

**通俗类比：** Query/Mutation 像发邮件（一问一答）；Subscription 像订了直播（留个地址，有更新主动推给你）；文件上传像寄大件（挂号单加纸箱，不能塞进普通信封）。

## 为什么需要它

靠轮询拿实时状态既费带宽又费延迟，消息、订单状态、协作光标这类场景要求"变了就推"；而 GraphQL 的 Mutation 走 JSON，天然不擅长搬运二进制大文件。把这两件事从主模型里分出来单独设计，既复用 schema 的类型与鉴权，又不牺牲实时性和传输效率。

## 核心机制

- **订阅三件套**：`type Subscription` 声明事件，`PubSub` 作进程内事件总线（`publish(event)` 发、`asyncIterator([events])` 收），Resolver 的 `subscribe` 返回异步迭代器、配 `withFilter` 按变量或权限过滤（只推本房间消息、只推关注用户的状态），`resolve` 再按角色裁剪下发字段。
- **连接与鉴权**：用 `graphql-ws` 跑在 WebSocket 上，握手期 `connectionParams` 带 token 做连接级鉴权；客户端用 split link 按操作类型把 subscription 走 WS、其余走 HTTP。单进程 PubSub 不能跨实例，多实例部署要换成共享总线（Redis/Kafka），思想见 [[事件驱动架构]]。
- **频率与成本**：事件越频繁，每个订阅连接都要收一遍，与订阅深度相乘会放大成倍流量——要按用户节流、限制单连接订阅数。
- **文件上传**：`scalar Upload` 加 `graphqlUploadExpress` 中间件把 multipart 解析成 Promise，Resolver 里 `await file` 取 `createReadStream/filename/mimetype/encoding`，用流落盘或转对象存储；带额外字段（如标题）时靠 multipart 的路径映射关联。
- **分片与续传**：大文件切成 chunk 逐片 `uploadChunk(index)`、最后 `completeUpload` 按 index 排序合并，前端切片循环更新进度——本质是断点续传，通用安全（幻数校验、拒可执行）见 [[文件上传与反序列化]]。

## 具体示例

```graphql
type Subscription {
  messageAdded(roomId: ID!): Message!   # 以 withFilter 按 roomId 分流
}
type Mutation {
  uploadFile(file: Upload!): File!       # Upload 承载 multipart 流
}
```

## 何时用与何时不用

- **用**：协作编辑、聊天、订单/行情状态推送等需要服务端主动推的场景；确需通过同一 API 网关搬运用户文件时。
- **不用**：低频单向更新轮询即可、别为它维护一条 WS；超大文件或纯静态资源走对象存储直传（预签名 URL）远好过塞进 GraphQL。底层连接/帧/心跳通用机制见 [[WebSocket]]。

## 优劣与代价

✅ 订阅复用 schema 的类型与字段级权限，前后端围绕同一契约拿到实时数据。
✅ Upload 让文件走统一的鉴权与错误语义，分片支持断点续传与进度反馈。
⚠️ 长连接占资源、单进程 PubSub 无法横向扩展，需共享总线。
⚠️ 大文件流经 GraphQL 层成本高、易超时，实时事件与订阅数叠加会放大流量。

## 与相关概念的区别

- **vs [[WebSocket]]**：WebSocket 是传输层（升级、帧、心跳、消息顺序），本篇是 GraphQL 语义层如何用订阅把类型化事件推到这条通道上。
- **vs [[文件上传与反序列化]]**：后者讲上传的通用安全（幻数、可执行拦截、反序列化红线），本篇讲 GraphQL 侧的 Upload 标量与分片协议。
- **vs [[事件驱动架构]]**：事件驱动是跨系统解耦的一般模型，PubSub 只是单服务内的进程事件总线，规模化时要升级为前者。

## 常见误区

- 以为 Subscription 与 Query 复用同一条普通 HTTP 请求，忽略它必须有 WebSocket 长连接。
- 用单进程 PubSub 直接上多实例部署，结果换台机器的连接收不到事件。
- 把所有文件都塞进 GraphQL 传，大视频不直传对象存储，导致超时与内存压力。

## 面试速答

> 🎯 实时订阅：type Subscription 声明事件、PubSub 总线、withFilter 按房间与权限过滤，跑在 WebSocket 上握手带 token，多实例需换共享总线；文件上传：Upload 标量配 multipart 中间件取流落盘或转 S3，大文件切分片续传，通用安全归 [[文件上传与反序列化]]。

## 相关术语

[[GraphQL从入门到精通]]、[[GraphQL实践]]、[[WebSocket]]、[[文件上传与反序列化]]、[[事件驱动架构]]、[[GraphQL Schema 与 Resolver 设计]]

## 参考资料

建议人工核验：可参考 graphql-ws、graphql-upload 与 Apollo Subscriptions 官方文档。本篇合并自原《GraphQL从入门到精通》§6 文件上传实现与 §7 实时数据（Subscription）两节，原稿大量服务端/前端 JS 代码（PubSub、withFilter、graphqlUploadExpress、分片合并、useSubscription 组件）按 v1.2 §8.1 收敛为散文与一段 schema 示例，未新增原稿没有的性能数字；传输层与上传安全的通用口径以 [[WebSocket]]·[[文件上传与反序列化]] 为准；原稿无可核验文献编号。
