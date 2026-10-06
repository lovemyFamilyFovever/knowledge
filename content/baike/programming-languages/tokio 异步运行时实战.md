---
title: "tokio 异步运行时实战"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# tokio 异步运行时实战

> 📌 **导航**：本文是 **tokio 异步运行时实战** 词条，属 [[Rust Web开发实战]] 子词条。async/await 语言层与 Future 概念见 [[Rust 并发与异步]]。

## 定义

**一句话定义：** tokio 是 Rust 的异步运行时——提供多线程工作窃取调度器、`async fn`/`.await` 执行器、定时器、异步 IO 与通道；`#[tokio::main]` 启动它，让高并发 Web 服务用少量线程处理海量待决请求。

**通俗类比：** 像餐厅调度台：`async` 任务是需要等厨房（IO）的订单，调度台不会让服务员干等一桌，而是转去服务别的桌，菜好了再回来——少量人手照顾客流爆满。

## 为什么需要它

Web 服务绝大多数时间是"等"——等数据库、等下游 HTTP、等磁盘。若每个请求占一个 OS 线程阻塞等待，线程与内存会被 I/O 密集连接拖垮。tokio 用单线程事件循环 + 少量工作线程的"就绪即调度"模型，把百万级并发连接压缩到极少线程上，这正是 Axum/hyper 能高吞吐的底座。

## 核心机制

- **运行时构建**：`#[tokio::main]` 或 `Builder::new_multi_thread().worker_threads(n).max_blocking_threads(m).enable_all().build()`；worker 数默认=CPU 核。
- **任务**：`task::spawn(async {...})` 把 Future 交给调度器并发执行；`JoinHandle.await` 取回结果。
- **别阻塞执行器**：worker 线程上禁 `std::thread::sleep`/同步 IO/重计算——会饿死同线程其它任务；CPU 密集或阻塞调用走 `task::spawn_blocking(|| .. )`。
- **并发限流**：`Semaphore::new(k).acquire_owned()` 限制同时进行的下游调用数。
- **通道**：`mpsc`（多生产者单消费者，背压）、`oneshot`（一次性请求-响应）、`broadcast`（扇出）、`watch`（最新值订阅），是任务间通信首选。
- **时间**：`tokio::time::sleep` / `timeout(dur, fut)` 是非阻塞定时原语。

## 具体示例

并发限流的批处理（信号量 + spawn）：

```rust
let sem = Arc::new(Semaphore::new(10));
let mut hs = Vec::new();
for item in items {
    let permit = sem.clone().acquire_owned().await.unwrap();
    hs.push(tokio::spawn(async move { let r = process(item).await; drop(permit); r }));
}
for h in hs { let _ = h.await; }
```

## 何时用与何时不用

- **用**：I/O 密集、高并发连接的服务（Web、代理、爬虫）用 tokio 多线程运行时；CPU 密集计算外包给 `spawn_blocking` 或独立线程池。
- **不用**：纯同步 CLI、单任务脚本不必引入运行时；混合库要保证 Future 不跨运行时误用阻塞 API。

## 优劣与代价

✅ 极少线程扛高并发、吞吐与延迟俱佳；与 futures 生态、Axum/SQLx/hyper 无缝。
✅ 通道/信号量/超时等原语齐备，限流与背压有章可循。
⚠️ 一个 `spawn` 出的阻塞调用就能拖垮整条 worker——"不要在 async 里阻塞"是硬纪律，排查靠 `console` 与 clippy。
⚠️ 生命周期/`Send` 约束、`.await` 处对象借用规则让编译报错更绕；调试异步栈不如同步直观。

## 与相关概念的区别

- **`spawn` vs `spawn_blocking`**：前者投 async 任务到 worker；后者投阻塞/CPU 任务到专用阻塞线程池，避免卡住事件循环。
- **tokio vs 语言 async**：`async/await` 是 Rust 语言特性，tokio 是执行这些 Future 的运行时（见 [[Rust 并发与异步]]）。
- **mpsc vs watch**：mpsc 每条消息都送达、有界背压；watch 只保留最新值、适合配置广播。

## 常见误区

- `worker_threads` 越大越好，加到几百能线性提升吞吐。
- 在 `async fn` 里调 `std::fs`/`std::thread::sleep` 无所谓，反正都异步。
- `spawn` 出来的任务和当前任务是同一线程顺序执行的。

## 面试速答

> 🎯 tokio=异步运行时：多线程工作窃取 + 事件循环，极少线程扛 I/O 密集高并发。要点：`spawn` 投 async 任务、阻塞/CPU 走 `spawn_blocking`、`Semaphore` 限流、mpsc/watch 通道、非阻塞定时器。是 Axum 并发底座。
> 🔍 追问：为什么 async 里 `std::thread::sleep` 很危险？
> 🔍 追问：worker_threads 设多大合适？

## 相关术语

[[Rust Web开发实战]]、[[Rust 并发与异步]]、[[Axum 路由与中间件]]、[[Rust Web 数据库集成]]、[[Rust编程基础]]

## 参考资料

建议人工核验：以 tokio 官方文档（runtime / task / sync / time）为准；未编造文献编号、标准号或 URL。
