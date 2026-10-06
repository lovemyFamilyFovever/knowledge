---
title: "HTTP头部与内容协商"
tags: []
source: "baike"
source_path: "开发术语 / 网络与协议"
collected: "2026-09-05"
status: "imported"
---

# HTTP头部与内容协商

> 📌 **导航**：本文是 **HTTP头部与内容协商** 词条，由 [[HTTP协议]] 拆分而来。

## 定义

**一句话定义：** HTTP 头部是报文里以 key-value 传递的元数据，承载认证、缓存、编码与内容协商等信息；Content-Type 声明 body 实际格式、Accept 声明期望格式，二者与 Accept-Encoding / Language 共同完成内容协商。

**通俗类比：** 像快递包裹上的标签：Content-Type 是"内有衣物"（说明实际装了什么），Accept 是"请回寄书籍"（说明想要什么）——元信息与内容分开标注。

## 为什么需要它

HTTP body 只是一串字节，靠头部声明"是什么格式、能否缓存、支持哪些编码 / 语言"，接收方才能正确解析、协商与复用缓存。头部也是 HTTP "可扩展"的核心机制。

## 核心机制

- **通用头：** Host（目标主机）、User-Agent、Connection: keep-alive、Date。
- **请求头：** Accept（期望响应类型，可带 q 权重）、Accept-Encoding、Accept-Language、Authorization: Bearer <token>、Cookie。
- **响应头：** Content-Type（body 类型，如 application/json、multipart/form-data）、Content-Length、Set-Cookie、Location、Server。
- **内容协商：** 客户端用 Accept / Accept-Language / Accept-Encoding 表达偏好，服务器选最合适的表示返回；无可用表示则 406 Not Acceptable（见 [[HTTP 状态码]]）。
- **定长 vs 分块：** 已知长度用 Content-Length；边生成边发、长度未知用 Transfer-Encoding: chunked（末尾发一个 0 长度块收尾）。

## 具体示例

`Accept: application/json, application/xml;q=0.9` 让服务器优先回 JSON；上传文件用 `Content-Type: multipart/form-data; boundary=...`；流式响应长度未知就用 chunked 分块持续下发。

## 何时用与何时不用

- **用：** 构造 / 解析 HTTP 报文、做内容协商、设置缓存与认证头、声明 body 类型。
- **不用：** 自定义头要与标准头区分（新规范已不推荐再滥用 `X-` 前缀）；别把敏感信息塞进会被日志 / 缓存记录的 URL 或明文头。

## 优劣与代价

✅ 头部把元信息与 body 解耦，是 HTTP 可协商、可缓存、可扩展的核心。
⚠️ 头多而杂、易配错（Content-Type 与 body 不符会导致解析失败）；Cookie 等头部过大会拖累每一次请求。

## 与相关概念的区别

vs [[Cookie与Session]]：那是"用哪些头维持状态"，本文是头部体系全貌；vs [[缓存策略]]：Cache-Control / ETag 属于头部，但缓存本身是独立主题。

## 常见误区

- Content-Type 和 Accept 是一回事。
- 不知道 body 总长就不能传，必须先把全部数据算好长度。
- 请求头只是可选附加信息，删了不影响解析。

## 面试速答

> 🎯 HTTP 头部是报文里的 key-value 元数据：Content-Type 声明 body 格式、Accept 表达期望并做内容协商，认证 / 缓存 / 编码都靠它承载；定长用 Content-Length、流式用 chunked。
> 🔍 追问：Content-Type 与 Accept 的区别？
> 🔍 追问：什么时候必须用 Transfer-Encoding: chunked？

## 相关术语

[[Cookie与Session]]、[[缓存策略]]、[[HTTP 状态码]]、[[HTTP协议]]
