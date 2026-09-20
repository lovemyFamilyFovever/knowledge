---
title: "Axum 路由与中间件"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# Axum 路由与中间件

> 📌 **导航**：本文是 **Axum 路由与中间件** 词条，属 [[Rust Web开发实战]] 子词条。错误处理见 [[Rust 错误处理]]。

## 定义

**一句话定义：** Axum 是 Tokio 团队出品、基于 tower 服务抽象的 Rust Web 框架，用类型安全的路由（`Router`+`extractor`）组合 handler，用可堆叠的中间件（`.layer`）横切地做日志、CORS、鉴权等通用逻辑。

**通俗类比：** 路由像"门牌号→接待员"的登记表（哪个路径、哪种方法交给哪个函数），中间件像大堂里一排必经的关卡（安检、登记、计时），请求穿过它们才到 handler。

## 为什么需要它

Rust 想在 Web 层拿到编译期保障，就得把"路径参数类型、请求体结构、共享状态"都编进类型里，运行时少踩空指针/错类型；同时横切关注点（追踪、CORS、认证）若写进每个 handler 会严重重复。Axum 用 tower 的 `Service`/`Layer` 把这两件事标准化，换来可组合、零成本抽象的路由骨架。

## 核心机制

- **路由与提取器（extractor）**：`Router::new().route("/users/:id", get(handler))`；handler 参数按顺序消费 `Path<T>`（路径）、`Query<T>`（查询串）、`Json<T>`（请求体）、`State<S>`（共享状态），全部编译期检查类型。
- **嵌套与分组**：`Router::new().nest("/api", user_routes().merge(post_routes()))`，把子路由组织成树。
- **中间件 layer**：内置 `TraceLayer`/`CorsLayer`；自定义用 `middleware::from_fn(async fn(req, next)->...)`；多个用 `ServiceBuilder::new().layer(a).layer(b)` 组合成栈。
- **共享状态**：`#[derive(Clone)] struct AppState{...}` + `.with_state(state)`，常用 `Arc<RwLock<...>>` 包连接池/缓存；配合 `FromRef` 拆分子状态做依赖注入。
- **错误映射**：handler 返回 `Result<Response, AppError>`，`AppError` 实现 `IntoResponse` 统一转状态码与 JSON（详见 [[Rust 错误处理]]、[[API 错误处理规范]]）。

## 具体示例

一条带状态与鉴权中间件的最小路由：

```rust
async fn get_user(State(st): State<AppState>, Path(id): Path<u64>)
    -> Result<Json<User>, AppError> {
    Ok(Json(st.db.get_user(id).await?))
}
let app = Router::new()
    .route("/users/:id", get(get_user))
    .layer(middleware::from_fn(auth_middleware))
    .with_state(state);
```

## 何时用与何时不用

- **用**：新项目要与 tokio 生态深度集成、看重类型安全与可组合中间件、 handler 数量多需分组管理时选 Axum。
- **不用**：追求极致并发且已有 Actix 经验可用 Actix-web；要"约定优于配置"的快速原型可用 Rocket。三框架对比见枢纽 [[Rust Web开发实战]]。

## 优劣与代价

✅ 编译期捕获路由/提取器/状态类型错误；tower layer 让横切逻辑可复用可组合。
✅ 与 tokio/sqlx/serde 同族协作顺滑，现代 Rust Web 事实标准之一。
⚠️ 泛型与 trait bound 报错冗长，学习曲线陡；提取器顺序有隐性规则。
⚠️ 过度嵌套的 `Service` 类型会让编译时间与可读性上升。

## 与相关概念的区别

- **extractor vs middleware**：extractor 从请求里"取数据"喂给 handler；middleware 在请求前后"做处理"再放行。
- **`.layer` vs `.route`**：layer 作用于其下所有路由的横切栈，route 只登记一条路径映射。
- **Axum vs Actix-web**：前者 tower/tokio 生态、后者 Actor 模型，抽象风格不同。

## 常见误区

- 中间件必须写成宏或实现复杂 trait，不能用 `from_fn` 一个 async fn。
- `State` 里放可变数据要每请求重建，不能 `Clone` 一份共享。
- 提取器参数谁先谁后无所谓，顺序不影响。

## 面试速答

> 🎯 Axum 路由=类型安全 `Router`+extractor（Path/Json/State 编译期取参）、`.nest` 分组；中间件基于 tower，用 `.layer`/`from_fn` 堆 Trace/CORS/鉴权；`with_state` 注入共享态，错误经 `IntoResponse` 统一映射。
> 🔍 追问：为什么 State 必须实现 Clone？
> 🔍 追问：layer 的先后顺序影响什么？

## 相关术语

[[Rust Web开发实战]]、[[Rust 错误处理]]、[[Rust 并发与异步]]、[[Rust编程基础]]、[[API 错误处理规范]]、[[Rust Web 认证与授权]]

## 参考资料

建议人工核验：以 Axum / tower 官方文档为准；未编造文献编号、标准号或 URL。
