---
title: "gRPC深入"
tags: []
source: "baike"
source_path: "开发术语 / 消息与中间件"
collected: "2026-09-05"
status: "imported"
---

# gRPC深入

## Protobuf

```protobuf
syntax = "proto3";

service UserService {
    rpc GetUser(GetUserRequest) returns (User);
    rpc ListUsers(ListUsersRequest) returns (stream User);  // 服务端流
}

message User {
    int32 id = 1;
    string name = 2;
    string email = 3;
}
```

## 四种通信模式

| 模式 | 说明 | 适用 |
|------|------|------|
| Unary | 一请求一响应 | 普通RPC |
| Server Streaming | 一请求多响应 | 实时推送 |
| Client Streaming | 多请求一响应 | 文件上传 |
| Bidirectional | 双向流 | 聊天/实时 |

## 与REST对比

| 特性 | gRPC | REST |
|------|------|------|
| 协议 | HTTP/2 | HTTP/1.1(2.0) |
| 格式 | Protobuf(二进制) | JSON(文本) |
| 性能 | 快5-10倍 | 慢 |
| API定义 | .proto文件 | OpenAPI/Swagger |
| 浏览器 | 需要gRPC-Web | 原生支持 |
| 学习成本 | 较高 | 低 |
