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

**通俗类比：** gRPC 像打电话点服务——你按约定的「话术格式」（.proto 契约）说出需求（调用方法），对方照做并直接回话；不像寄信（REST/JSON）那样反复解析文本，也没有多余客套（协议开销小）。

> 多义说明：gRPC 常用于**服务间（东西向）**通信；对外（南北向）浏览器不能直接调 gRPC，需 gRPC-Web 或经网关转 REST。它与 [[HTTP协议]] 的 REST 是两种不同的 API 范式。

## 原理与机制

- **Protocol Buffers（Protobuf）**：用 `.proto` 定义服务与消息，`protoc` 生成各语言桩代码；二进制序列化，体积小、解析快、强类型、靠字段编号保持向后兼容。
- **HTTP/2**：多路复用（一个连接并发多请求）、头部压缩、双向流——是 gRPC 流式与高性能的基础（见 [[HTTP协议]]）。
- **四种通信模式**：

| 模式 | 说明 | 适用 |
|------|------|------|
| Unary（一元） | 一请求一响应 | 普通 RPC |
| Server Streaming | 一请求多响应（流） | 实时推送、大结果集 |
| Client Streaming | 多请求一响应 | 上传、批量提交 |
| Bidirectional Streaming | 双向流 | 聊天、实时协作 |

### 接口定义示例

```protobuf
syntax = "proto3";

service UserService {
    rpc GetUser(GetUserRequest) returns (User);              // 一元
    rpc ListUsers(ListUsersRequest) returns (stream User);   // 服务端流
}

message User {
    int32 id = 1;        // 字段编号用于兼容，勿复用已删字段的编号
    string name = 2;
    string email = 3;
}
```

## 关键特性

- **契约优先**：`.proto` 是唯一事实源，多语言自动生成客户端/服务端桩，降低联调成本。
- **截止/取消（deadline/cancellation）**：可为调用设超时，超时或取消会跨服务传播。
- **拦截器（interceptor）**：类似中间件，统一处理鉴权、日志、重试、链路追踪。
- **错误模型**：用标准 status code（OK/INVALID_ARGUMENT/NOT_FOUND/UNAVAILABLE…）而非 HTTP 状态码。

## gRPC vs REST

| 特性 | gRPC | REST |
|------|------|------|
| 传输协议 | HTTP/2 | 多为 HTTP/1.1（也可 HTTP/2） |
| 数据格式 | Protobuf（二进制） | JSON（文本） |
| 性能 | 通常更高（二进制 + 多路复用） | 相对较低 |
| 契约 | .proto（强类型 IDL） | OpenAPI/Swagger（可选） |
| 流式 | 原生四种流模式 | 需 SSE/WebSocket 另行实现 |
| 浏览器 | 需 gRPC-Web/网关 | 原生支持 |
| 可读性/调试 | 二进制，需工具 | 文本，直观易调 |
| 学习成本 | 较高 | 低 |

## 应用场景

- 微服务间高性能内部通信、多语言系统统一契约、需要流式（实时推送/大文件传输）的场景、移动端/物联网（省流量）。

## 优点与局限

- 优点：性能高、强类型契约、多语言代码生成、原生流式、内置截止与拦截器。
- 局限：浏览器不能直连（需 gRPC-Web）；二进制不便人工调试；对防火墙/代理（需支持 HTTP/2）有要求；简单 CRUD/小团队可能过重（REST 更轻）。

## 常见误区

- 「gRPC 一定比 REST 快 5–10 倍」：优势来自 Protobuf 二进制 + HTTP/2 多路复用，但**具体倍数依场景**（报文大小、网络、序列化占比）而定，不宜一概而论（原文档表述已收敛）。
- 以为浏览器能直接调 gRPC：需 gRPC-Web 或经网关（如 Envoy）转换。
- 随意复用/修改 .proto 字段编号：会破坏向后兼容，删除字段应 `reserved` 其编号。

## 相关术语

[[消息队列（Message Queue）]]、[[HTTP协议]]、[[ESB 与服务网格（Service Mesh）]]、[[GraphQL实践]]、[[微服务治理术语百科]]

## 参考资料

建议人工核验：可参考 gRPC 官方文档（grpc.io）、Protocol Buffers 语言指南、HTTP/2 规范 RFC 9113，以及 gRPC-Web 项目说明。
