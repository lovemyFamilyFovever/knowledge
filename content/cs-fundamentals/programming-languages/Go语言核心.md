---
title: "Go语言核心"
tags: []
source: "baike"
source_path: "开发术语 / 编程语言基础"
collected: "2026-09-05"
status: "imported"
---

# Go语言核心

## Goroutine

轻量级协程，初始栈仅2KB（线程通常1-8MB）。

```go
func main() {
    // 启动10万个goroutine完全没问题
    for i := 0; i < 100000; i++ {
        go func(id int) {
            fmt.Printf("Goroutine %d\n", id)
        }(i)
    }
    time.Sleep(time.Second)
}
```

## Channel

goroutine之间的通信管道：

```go
// 无缓冲通道（同步）
ch := make(chan int)
go func() { ch <- 42 }()
val := <-ch  // 阻塞直到有数据

// 带缓冲通道（异步）
ch := make(chan int, 10)
ch <- 1  // 不阻塞（缓冲区未满）
ch <- 2

// select多路复用
select {
case msg := <-ch1:
    fmt.Println("从ch1收到:", msg)
case ch2 <- data:
    fmt.Println("发送到ch2")
case <-time.After(5 * time.Second):
    fmt.Println("超时")
default:
    fmt.Println("无数据")
}
```

## 接口

Go的接口是隐式实现的（鸭子类型）：

```go
type Writer interface {
    Write([]byte) (int, error)
}

// 只要实现了Write方法，就自动满足Writer接口
type FileWriter struct{ path string }
func (fw FileWriter) Write(data []byte) (int, error) {
    // 实现写文件逻辑
    return len(data), nil
}
```

## 错误处理

```go
// Go没有异常机制，用返回值处理错误
result, err := doSomething()
if err != nil {
    return fmt.Errorf("doSomething failed: %w", err)  // 错误包装
}

// 自定义错误类型
type ValidationError struct {
    Field   string
    Message string
}
func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation error: %s - %s", e.Field, e.Message)
}
```

## GC机制

Go使用三色标记清除算法：
- **并发标记**：不停止程序（STW < 1ms）
- **写屏障**：保证并发标记的正确性
- **内存分配**：tcmalloc思想，按大小分级分配

## 并发模式

```go
// Worker Pool
func workerPool(jobs <-chan int, results chan<- int) {
    for job := range jobs {
        results <- process(job)
    }
}

// Fan-out Fan-in
func fanOutFanIn(input <-chan int, workers int) <-chan int {
    chans := make([]<-chan int, workers)
    for i := 0; i < workers; i++ {
        chans[i] = worker(input)
    }
    return merge(chans...)
}
```
