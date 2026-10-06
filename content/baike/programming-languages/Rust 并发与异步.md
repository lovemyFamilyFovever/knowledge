---
title: "Rust 并发与异步"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# Rust 并发与异步

> 📌 **导航**：本文是 **Rust 并发与异步** 词条，属 [[Rust系统编程入门到精通]] 子词条。跨语言并发概念见 [[并发编程模式与实践]]、[[协程]]。

## 定义

**一句话定义：** Rust 并发靠所有权与 Send/Sync trait 在编译期消灭数据竞争（线程、channel 消息传递、Mutex/RwLock 共享状态）；异步用 `async/await` + Tokio 运行时以极小成本调度大量并发任务。

**通俗类比：** "不共享内存地通信"由类型系统兜底——编译器替你查"这数据能不能安全传到另一线程"；异步像一个人轮流照看几百口锅，不为一口锅干等。

## 为什么需要它

多数语言里数据竞争、跨线程误用是运行期炸；Rust 把"能否 Send/Sync"编码进类型，编译不过就挡住误用。而网络 I/O 密集场景若一线程一请求会耗尽资源，async 用少量线程跑大量挂起任务，兼顾吞吐与成本。

## 核心机制

- **线程与所有权**：`thread::spawn` + `move` 闭包转移所有权；跨线程传数据必须转移所有权（避免悬垂），`join` 等待。
- **消息传递**：`mpsc::channel` 多生产者单消费者，"通过通信共享内存"。
- **共享状态**：`Mutex<T>`（`lock()` 拿内部值、作用域结束自动解锁）、`RwLock`（多读单写）；常配 `Arc` 跨线程共享。
- **Send/Sync**：`Send`＝所有权可跨线程转移，`Sync`＝可跨线程共享引用；泛型边界据此在编译期拒绝不安全并发（"fearless concurrency"）。
- **异步**：`async fn`/`.await` 返回 `Future`（惰性、需运行时驱动）；Tokio 提供多线程 runtime 调度，`Stream`/`Sink` 处理异步序列。

## 具体示例

Arc+Mutex 跨线程累加，Rust 在编译期保证不会裸数据竞争：

```rust
let n = Arc::new(Mutex::new(0));
let h = { let c = n.clone(); thread::spawn(move || { *c.lock().unwrap() += 1; }) };
h.join().unwrap();
```

## 何时用与何时不用

- **用**：CPU 密集并行→线程/数据并行；跨线程共享→Arc+Mutex/RwLock；大量 I/O 等待→async/Tokio；优先 channel 传递而非共享。
- **不用**：别让 `blocking` 调用跑进 async（卡 worker）；小并发别上 async 复杂度；共享可变尽量用所有权/消息替代加锁。

## 优劣与代价

✅ 类型系统杜绝数据竞争，并发错误大多编译期暴露。
✅ async 以少量线程承载海量并发，开销低。
⚠️ Send/Sync、生命周期与 `async` 签名有心智负担、报错陡。
⚠️ async 需运行时、易误用（未 await、阻塞混入、`Future` 惰性）；锁仍有死锁可能（仅杜绝数据竞争）。

## 与相关概念的区别

- **消息传递 vs 共享状态锁**：前者所有权随消息转移、天然安全；后者需 Mutex/RwLock 保护共享。
- **线程 vs async 任务**：线程 OS 调度、适合 CPU 并行；async 任务由 runtime 协作式调度、适合 I/O 海量并发。
- **Rust 无 GC 并发 vs 语言层 GC 并发**（[[内存管理]]）：靠所有权+Send/Sync 保证安全。

## 常见误区

- Rust 有 Mutex 就永远不会死锁。
- `async fn` 不调用 `.await`/不被 runtime 驱动也会自己跑起来。
- 任何类型都能安全 `thread::spawn` 到别的线程。

## 面试速答

> 🎯 Rust 并发=所有权+Send/Sync 编译期灭数据竞争：线程(move 转移所有权)、channel 消息传递、Arc+Mutex/RwLock 共享。异步 async/await 是惰性 Future、靠 Tokio runtime 调度、适合海量 I/O。能编译过基本无数据竞争（死锁仍在）。
> 🔍 追问：Rust 怎么在编译期杜绝数据竞争？
> 🔍 追问：channel 与 Arc+Mutex 何时各用？

## 相关术语

[[Rust系统编程入门到精通]]、[[Rust编程基础]]、[[并发编程模式与实践]]、[[协程]]、[[Rust 智能指针]]

## 参考资料

建议人工核验：以 The Rust Book 并发章、std::sync 与 Tokio 文档为准；未编造文献编号。
