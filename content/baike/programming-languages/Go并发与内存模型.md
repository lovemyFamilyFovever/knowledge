---
title: "Go并发与内存模型"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# Go并发与内存模型

> 📌 **导航**：本文是 **Go 并发与内存模型** 词条，属 [[Go语言系统编程指南]] 子词条。goroutine/channel 入门见 [[Go语言核心]]。

## 定义

**一句话定义：** Go 并发以 CSP 为核心——用 goroutine、channel、select 与 sync 原语组织并发；其内存模型用 happens-before 定义并发访问的可观次序，正确同步才能消除数据竞争。

**通俗类比：** Go 的名言是"不要通过共享内存来通信，而要通过通信来共享内存"——与其多人抢改一块白板，不如递纸条（channel）传话。

## 为什么需要它

裸共享内存 + 加锁易出竞态、死锁、性能陷阱。CSP 把同步收敛到 channel 上、用 select 做超时/多路复用，更贴合并发思维；而数据竞争属未定义行为，必须靠内存模型（happens-before）与 `-race` 把"看似能跑"的隐患揪出来。

## 核心机制

- **goroutine**：运行时 GMP 模型调度、栈可增长；`sync.WaitGroup` 等待一组完成。
- **channel**：无缓冲=同步会合、有缓冲=异步解耦，支持 `close`/`range`/方向约束（`chan<-`）。
- **select**：多路等待 channel，配 `default` 非阻塞、`time.After` 超时。
- **sync**：Mutex/RWMutex/Once 保护临界区。
- **内存模型**：happens-before 定义"一次写对另一次读可见"的条件（channel 收发、加解锁、once 等建立边）；无 happens-before 的并发读写即数据竞争→未定义，用 `go run -race` 检测；`atomic` 提供无锁计数/CAS。

## 具体示例

select 做"谁先到用谁 + 超时兜底"，避免永久阻塞：

```go
select {
case v := <-resultCh:   handle(v)
case <-time.After(time.Second):  timeout()   // 超时
default:                busy()              // 非阻塞
}
```

## 何时用与何时不用

- **用**：并发扇出/扇入、限流 worker pool、超时与取消（配 context）、跨 goroutine 传数据用 channel、共享计数用 atomic/锁。
- **不用**：别用 goroutine 包一切（无并行需求反增开销）；别拿裸共享变量+忘记同步赌"看起来没事"。

## 优劣与代价

✅ CSP + 轻量 goroutine + select 让并发表达自然、可组合，配合 GMP 高并发成本低。
✅ happens-before + `-race` 给了可推理、可检测的并发正确性。
⚠️ channel 与共享锁各有适用面，误用（如在 channel 上仍无同步地读写共享态）照样竞争。
⚠️ goroutine 泄漏、死锁、闭包捕获循环变量是常见坑。

## 与相关概念的区别

- **channel vs 共享内存+锁**：前者以消息传递隐式同步；后者需显式加锁，二者可按场景选。
- **goroutine vs OS 线程**（见 [[协程]]）：前者用户态、栈 KB 级、可开海量。
- **sync.Mutex vs channel**：简单临界区用锁更直白；跨阶段/流水线/广播更适合 channel。

## 常见误区

- goroutine 就是轻量线程，和线程没本质区别。
- 只要用了 channel 就一定不会有数据竞争。
- select 带 default 分支时会阻塞等待任一 case 就绪。

## 面试速答

> 🎯 Go 并发=CSP：goroutine+channel(无缓冲同步/有缓冲异步)+select(多路/超时/default)+sync；内存模型用 happens-before 定可见次序，无同步并发读写=数据竞争(未定义)，靠 channel/锁/atomic 建边、-race 检测。口诀：通过通信共享内存。
> 🔍 追问：happens-before 与数据竞争什么关系？
> 🔍 追问：channel 和加锁共享内存怎么选？

## 相关术语

[[Go语言系统编程指南]]、[[Go语言核心]]、[[协程]]、[[并发编程模式与实践]]、[[线程]]

## 参考资料

建议人工核验：以 Go Memory Model 官方文档与《Concurrency is not Parallelism》为准；未编造文献编号。
