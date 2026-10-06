---
title: "gRPC深入"
tags: [消息与中间件, gRPC, Protobuf, RPC]
source: "baike"
source_path: "开发术语 / 消息与中间件"
collected: "2026-09-05"
status: "imported"
---

# gRPC深入


> 📌 **导航**：本文是 **gRPC深入** 词条，属于 middleware 术语集。相关枢纽：[[ESB 与服务网格（Service Mesh）]]、[[GraphQL实践]]、[[Kafka深入]]、[[RabbitMQ vs Kafka vs Pulsar]]、[[gRPC深入]]。

## 定义

**一句话定义：** gRPC 是 Google 开源的高性能**远程过程调用（RPC）**框架，基于 HTTP/2 传输、以 Protocol Buffers 作为接口定义语言（IDL）与序列化格式，支持多语言与双向流式通信。

**通俗类比：** gRPC 像打电话点服务——按约定的"话术格式"（.proto 契约）说出需求（调用方法），对方照做并直接回话；不像寄信（REST/JSON）那样反复解析文本，也没有多余客套（协议开销小）。

> 多义说明：gRPC 常用于服务间（东西向）通信；对外（南北向）浏览器不能直接调 gRPC，需 gRPC-Web 或经网关转 REST。它与 [[HTTP协议]] 的 REST 是两种不同的 API 范式。

## 为什么需要它

微服务跨语言调用，手写 HTTP+JSON 要重复处理序列化、契约对齐、版本兼容，且 HTTP/1.1 一条连接串行、开销大。gRPC 用 `.proto` 做契约优先、`protoc` 生成多语言桩、Protobuf 二进制序列化 + HTTP/2 多路复用，把"接口即协议"标准化，显著降低跨语言联调成本并提升吞吐与流式能力。

## 核心机制

- **Protocol Buffers：** 用 `.proto` 定义服务与消息，`protoc` 生成各语言桩代码；二进制序列化、体积小、解析快、强类型，靠字段编号保持向后兼容。
- **HTTP/2：** 多路复用（一连接并发多请求）、头部压缩、双向流，是 gRPC 流式与高性能的基础（见 [[HTTP协议]]）。
- **四种通信模式：** Unary（一元）、Server/Client/Bidirectional Streaming（服务端流/客户端流/双向流），覆盖请求-响应到实时推送各种形态。
- **契约优先 + 工程能力：** 内置 deadline/cancellation（超时跨服务传播）、interceptor（统一鉴权/日志/重试/追踪）、标准 status code 错误模型。

## 具体示例

`.proto` 是跨语言唯一契约：

```protobuf
service UserService {
    rpc GetUser(GetUserRequest) returns (User);              // 一元
    rpc ListUsers(ListUsersRequest) returns (stream User);   // 服务端流
}
message User {
    int32 id = 1;   // 字段编号用于兼容，删除字段应 reserved 其编号、勿复用
    string name = 2;
    string email = 3;
}
```

同一份定义自动生成各语言客户端与服务端桩，`ListUsers` 以 stream 持续下发大结果集。

## 何时用 / 何时不用

- **用：** 微服务间高性能内部通信、多语言系统统一契约、需流式（实时推送/大文件传输）、移动/物联网省流量。
- **不用：** 面向浏览器/公网的简单 REST 接口（浏览器不能直连、REST 更通用直观）；简单 CRUD/小团队可能过重。

## 优劣与代价

✅ 性能高、强类型契约、多语言代码生成、原生流式、内置截止与拦截器。
⚠️ 浏览器不能直连（需 gRPC-Web/Envoy 网关）；二进制不便人工调试。
⚠️ 需 HTTP/2 通路支持；字段编号处理不当会破坏兼容。

## 与相关概念的区别

| 特性 | gRPC | REST |
|------|------|------|
| 传输/格式 | HTTP/2 + Protobuf 二进制 | 多为 HTTP/1.1 + JSON 文本 |
| 性能 | 通常更高（二进制+多路复用） | 相对较低 |
| 契约 | .proto 强类型 IDL | OpenAPI（可选） |
| 流式 | 原生四种流模式 | 需 SSE/WebSocket |
| 浏览器 | 需 gRPC-Web/网关 | 原生支持 |
| 调试 | 二进制需工具 | 文本直观 |

- **vs [[GraphQL实践]]：** GraphQL 面向客户端按需查询；gRPC 面向服务间高效 RPC，二者常互补。

## 常见误区

- gRPC 在任何场景下都比 REST 快 5–10 倍。
- 浏览器可以直接调用 gRPC 服务，无需任何额外组件。
- .proto 里的字段编号可以随便改、字段删除后还能复用原编号。

## 面试速答

> 🎯 gRPC=Google 开源高性能 RPC：HTTP/2（多路复用/头部压缩/双向流）+ Protobuf 契约优先、二进制强类型，支持一元与三种流式，内置 deadline 与拦截器。多语言代码生成降联调成本；短板是浏览器不能直连（需 gRPC-Web）、二进制难调试，性能提升幅度依场景而定。
> 🔍 追问：gRPC 性能优势主要来自哪两点？
> 🔍 追问：Protobuf 靠什么保证向后兼容、删字段要注意什么？
> 🔍 追问：浏览器为什么不能直连 gRPC？

## 相关术语

[[消息队列（Message Queue）]]、[[HTTP协议]]、[[ESB 与服务网格（Service Mesh）]]、[[GraphQL实践]]、[[微服务治理术语百科]]

## 参考资料

建议人工核验：可参考 gRPC 官方文档（grpc.io）、Protocol Buffers 语言指南、HTTP/2 规范 RFC 9113，以及 gRPC-Web 项目说明。
