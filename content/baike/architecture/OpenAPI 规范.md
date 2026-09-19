---
title: "OpenAPI 规范"
tags: []
source: "baike"
source_path: "开发术语 / 架构与设计"
collected: "2026-09-05"
status: "imported"
---

# OpenAPI 规范

> 📌 **导航**：本文是 **OpenAPI 规范** 词条，属于 architecture 术语集。相关枢纽：[[API设计]]、[[RESTful API 设计]]、[[API 分页与版本控制]]、[[微服务架构设计与实践]]。

## 定义

**一句话定义：** OpenAPI 规范（OAS，前身为 Swagger）是**用 YAML/JSON 机器可读地描述一个 HTTP API** 的标准——端点、参数、请求/响应模式、鉴权与错误码写进一份契约，供文档、代码生成、Mock 与契约校验消费。

**通俗类比：** 像建筑施工图：楼怎么盖、管线怎么走先画在图纸上，各施工方照图施工；图一改，工程量清单与验收标准都能同步重算，不靠口头传达。

## 为什么需要它

没有机器可读的契约时，接口知识散落在代码注释、聊天录屏和某个人的记忆里，前后端只能靠"抓包对字段"来对齐，改一个字段要人肉通知所有调用方。契约把它变成可版本化的工件：文档与实现不再是两份东西、客户端 SDK 可自动生成、CI 能拦住"实现偷偷偏离约定"，新服务接入也从读源码变成读一份 schema。

## 核心机制

- **文档骨架**：`openapi` 版本 + `info`（标题/版本）+ `paths`（端点 → 方法 → 参数与响应）+ `components`（可复用的 `schemas`/`responses`/`securitySchemes`/`parameters`）。
- **模式描述**：数据结构用 JSON Schema 表达（类型、必填、枚举、`$ref` 复用）。
- **鉴权建模**：`securitySchemes` 声明 apiKey / HTTP bearer / OAuth2 / OIDC，`security` 指定端点要求，生成的 SDK 会自动带上认证。
- **工具链用途**：文档与调试台（Swagger UI、Redoc）、代码生成（openapi-generator 产 SDK 与服务端桩）、Mock（按 schema 造响应给前端并行开发）、契约与风格校验（Spectral、Prism）、网关与监控（按操作 ID 关联指标）。
- **两种工作流**：**design-first** 先写 spec 再生成骨架与客户端，适合同时服务多端；**code-first** 由框架（FastAPI、Spring、Nest）从代码注解反出 spec，省事但需人守住命名与模型。

## 具体示例

一份最小可用的 GET 契约：

```yaml
openapi: 3.0.0
info: { title: 用户 API, version: 1.0.0 }
paths:
  /users/{id}:
    get:
      summary: 获取用户
      parameters:
        - { name: id, in: path, required: true, schema: { type: string } }
      responses:
        '200': { content: { application/json: { schema: { $ref: '#/components/schemas/User' } } } }
        '404': { description: 不存在 }
```

关键是 `200`/`404` 都写进契约，前端与 Mock 才能一起覆盖异常分支，而不只对齐成功路径。

## 何时用与何时不用

- **用**：对外或有第三方/多语言客户端的 HTTP 接口；需要自动文档、SDK 生成、契约测试、Mock 并行开发、API 网关对接与服务治理度量的团队。
- **不必**：只有单一内部消费者的临时接口，用类型定义或 README 更省；[[gRPC深入]] 已有 `.proto` 作契约、[[GraphQL实践]] 有内省 schema，都无需再套 OAS。
- **别忘**：契约要进版本库并纳入 CI 校验，否则很快与实现脱节——**过期契约比没有契约更危险**。

## 优劣与代价

✅ 一份描述同时驱动文档、代码生成、Mock 与校验，接口知识有了单一事实源。
✅ 跨语言、跨团队协作时，把口头约定变成可校验的结构，评审可自动化。
⚠️ 复杂模式与多态写起来冗长，code-first 生成器产出的 schema 常需人工整理。
⚠️ 它只描述 HTTP 形状，不描述业务语义，也覆盖不了 gRPC / 消息队列。

## 与相关概念的区别

- **OpenAPI vs Swagger**：Swagger 是项目名，OpenAPI Specification 是它演进出的规范；习惯上 OAS 指 3.x、"Swagger 2.0" 指上一版，两者不互兼容。
- **OpenAPI vs JSON Schema**：JSON Schema 描述单个数据结构，OAS 在其上描述端点、参数、状态码与鉴权等 HTTP 语义。
- **契约测试 vs 集成测试**：契约测试用 spec 校验提供方是否兑现承诺（消费者驱动），集成测试验证真实链路跑通。
- **Postman 集合 vs OpenAPI**：前者是工具私有格式、面向手工调试；后者是标准规范、可供整条工具链消费，且常作为集合的来源。

## 常见误区

- 生成过 OpenAPI 文档，接口契约治理就算完成了。
- 有了 OpenAPI，就不需要写接口测试了。
- OpenAPI 能描述任意类型的服务接口，包括 gRPC 和消息队列。

## 面试速答

> 🎯 OpenAPI（前身 Swagger）是描述 HTTP 契约的标准：paths 写端点、components 用 JSON Schema 复用模型、securitySchemes 声明鉴权，一份 spec 同时驱动文档、SDK 生成、Mock 与 CI 契约校验；gRPC 和 GraphQL 各有自己的契约形式，不必套 OAS。
> 🔍 追问：design-first 与 code-first 各有什么风险？
> 🔍 追问：契约测试和接口测试的区别是什么？

## 相关术语

[[RESTful API 设计]]、[[API 分页与版本控制]]、[[gRPC深入]]、[[GraphQL实践]]、[[API设计]]、[[微服务架构设计与实践]]、[[04-CI CD]]

## 参考资料

建议人工核验：规范正文见 OpenAPI Initiative 官网（openapis.org specification）与 OAS 3.x 版本说明，Swagger 2.0 与 3.x 不兼容；工具生态（Swagger UI、openapi-generator、Spectral、Dredd）能力以各自官方文档当前版本为准。
