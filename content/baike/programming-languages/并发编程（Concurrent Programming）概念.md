---
title: "并发编程（Concurrent Programming）概念"
tags: []
source: "baike"
source_path: "开发术语 / 编程语言基础"
collected: "2026-09-05"
status: "imported"
---

# 并发编程（Concurrent Programming）概念


> 📌 **导航**：本文是 **并发编程（Concurrent Programming）概念** 词条，属于 programming-languages 术语集。相关枢纽：[[Go语言核心]]、[[Python高级编程完全指南]]、[[Rust系统编程入门到精通]]、[[Rust编程基础]]、[[TypeScript深入]]。

---

## 并发（Concurrency）vs 并行（Parallelism）

**一句话定义：** 并发是"交替处理"多个任务（像一个人同时接两个电话），并行是"同时处理"多个任务（像两个人各接一个电话）。

**通俗类比：** 并发就像一个厨师同时炒两个菜——先炒几下这个，再炒几下那个，来回切换；并行就像两个厨师各炒一个菜，真正同时进行。

**具体示例：**
```python
import asyncio
import concurrent.futures

# 并发（单线程交替执行）
async def fetch_data():
    print("开始请求")
    await asyncio.sleep(1)  # 模拟IO操作，不阻塞
    print("请求完成")

async def main():
    await asyncio.gather(
        fetch_data(),
        fetch_data(),
        fetch_data()
    )

asyncio.run(main())  # 三个任务交替执行，总耗时约1秒

# 并行（多线程/多进程同时执行）
import concurrent.futures

def process_item(item):
    import time
    time.sleep(1)
    return item * 2

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(process_item, [1, 2, 3]))
# 三个任务真正同时执行，总耗时约1秒
```

```go
// Go 语言：goroutine 天然支持并发
package main

import (
    "fmt"
    "time"
)

func worker(id int) {
    fmt.Printf("Worker %d starting\n", id)
    time.Sleep(time.Second)
    fmt.Printf("Worker %d done\n", id)
}

func main() {
    for i := 1; i <= 3; i++ {
        go worker(i)  // 启动 goroutine
    }
    time.Sleep(2 * time.Second)
}
```

```java
// Java Virtual Threads（虚拟线程）
import java.util.concurrent.*;

public class Concurrency {
    public static void main(String[] args) throws Exception {
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            IntStream.range(0, 10000).forEach(i ->
                executor.submit(() -> {
                    Thread.sleep(Duration.ofSeconds(1));
                    System.out.println("Task " + i + " done");
                })
            );
        }
    }
}
```

**为什么需要它：** 并发提高响应速度（如Web服务器同时处理多个请求），并行提高吞吐量（如多核CPU同时计算）。

**与相关术语对比：** 并发关注任务管理和切换，并行关注物理同时执行；并发是逻辑概念，并行是物理概念。

---

## 线程（Thread）vs 进程（Process）

**一句话定义：** 进程是操作系统分配资源的基本单位，线程是CPU调度的基本单位；一个进程可以包含多个线程。

**通俗类比：** 进程就像一栋办公楼（有独立的水电、网络），线程就像楼里的员工（共享办公楼的资源）。

**具体示例：**
```python
import multiprocessing
import threading

# 进程：独立的内存空间
def process_worker():
    print(f"进程 PID: {multiprocessing.current_process().pid}")

p1 = multiprocessing.Process(target=process_worker)
p2 = multiprocessing.Process(target=process_worker)
p1.start()
p2.start()

# 线程：共享内存空间
shared_data = {"count": 0}
lock = threading.Lock()

def thread_worker():
    for _ in range(1000):
        with lock:
            shared_data["count"] += 1

threads = [threading.Thread(target=thread_worker) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print(f"最终计数: {shared_data['count']}")  # 10000
```

```go
// Go：goroutine 比线程更轻量
package main

import (
    "fmt"
    "sync"
)

func main() {
    var wg sync.WaitGroup
    counter := 0
    var mu sync.Mutex

    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for j := 0; j < 1000; j++ {
                mu.Lock()
                counter++
                mu.Unlock()
            }
        }()
    }
    wg.Wait()
    fmt.Println(counter) // 10000
}
```

```java
// Java 线程 vs 虚拟线程
// 传统线程
Thread t1 = new Thread(() -> {
    System.out.println("平台线程: " + Thread.currentThread());
});
t1.start();

// 虚拟线程（Java 21+）
Thread vt = Thread.ofVirtual().start(() -> {
    System.out.println("虚拟线程: " + Thread.currentThread());
});
```

**为什么需要它：** 进程提供隔离性（安全），线程提供并发性（高效共享内存）。

**与相关术语对比：** 进程切换开销大（需切换内存空间），线程切换开销小（共享内存）；进程间通信需IPC，线程间可直接读写共享变量。

---

## 锁（Lock）与互斥锁（Mutex）

**一句话定义：** 互斥锁就是同一时间只允许一个线程访问共享资源的"门锁"。

**通俗类比：** 就像卫生间——一个人进去就把门锁上，其他人只能在外面排队等着。

**具体示例：**
```python
import threading

# 互斥锁
lock = threading.Lock()
counter = 0

def increment():
    global counter
    lock.acquire()      # 加锁
    try:
        counter += 1     # 安全地修改共享变量
    finally:
        lock.release()  # 解锁（即使出错也要解锁）

# 更简洁的写法
def increment_safe():
    global counter
    with lock:           # 自动加锁和解锁
        counter += 1
```

```go
// Go：Mutex
package main

import (
    "fmt"
    "sync"
)

func main() {
    var mu sync.Mutex
    counter := 0

    var wg sync.WaitGroup
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            mu.Lock()
            counter++
            mu.Unlock()
        }()
    }
    wg.Wait()
    fmt.Println(counter)
}
```

```java
// Java ReentrantLock
import java.util.concurrent.locks.ReentrantLock;

ReentrantLock lock = new ReentrantLock();
int counter = 0;

void increment() {
    lock.lock();
    try {
        counter++;
    } finally {
        lock.unlock();
    }
}
```

**为什么需要它：** 多线程同时修改共享变量会导致数据竞争，锁保证同一时间只有一个线程能修改。

**与相关术语对比：** 互斥锁保证排他访问，读写锁允许多个读但排他写，信号量控制同时访问的数量。

---

## 读写锁（Read-Write Lock）

**一句话定义：** 读写锁允许多个线程同时读，但写操作必须独占——有写操作时不能读，有读操作时不能写。

**通俗类比：** 就像图书馆——多人可以同时看书（读），但整理书架（写）时必须清场。

**具体示例：**
```python
import threading

rw_lock = threading.RLock()  # 简化演示，实际用 ReadWriteLock
data = {"key": "value"}

def read_data(key):
    # 实际应用中应使用读写锁的读锁
    with rw_lock:
        return data.get(key)

def write_data(key, value):
    # 实际应用中应使用读写锁的写锁
    with rw_lock:
        data[key] = value
```

```go
// Go：sync.RWMutex
package main

import (
    "fmt"
    "sync"
)

func main() {
    var rwMu sync.RWMutex
    data := make(map[string]string)

    // 读操作（可并发）
    read := func(key string) string {
        rwMu.RLock()         // 读锁（多个 goroutine 可同时持有）
        defer rwMu.RUnlock()
        return data[key]
    }

    // 写操作（独占）
    write := func(key, value string) {
        rwMu.Lock()          // 写锁（独占）
        defer rwMu.Unlock()
        data[key] = value
    }

    var wg sync.WaitGroup
    // 并发读
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func(i int) {
            defer wg.Done()
            write(fmt.Sprintf("key%d", i), fmt.Sprintf("value%d", i))
        }(i)
    }
    wg.Wait()
    fmt.Println(read("key1"))
}
```

```java
// Java ReadWriteLock
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;

ReadWriteLock rwLock = new ReentrantReadWriteLock();
Map<String, String> data = new HashMap<>();

String read(String key) {
    rwLock.readLock().lock();
    try {
        return data.get(key);
    } finally {
        rwLock.readLock().unlock();
    }
}

void write(String key, String value) {
    rwLock.writeLock().lock();
    try {
        data.put(key, value);
    } finally {
        rwLock.writeLock().unlock();
    }
}
```

**为什么需要它：** 读多写少的场景下，读写锁比互斥锁性能更好——读操作不会互相阻塞。

**与相关术语对比：** 互斥锁读写都排他，读写锁允许多读排他写；读写锁适合读多写少，互斥锁适合写多或简单场景。

---

## 信号量（Semaphore）

**一句话定义：** 信号量就是一个计数器，控制同时访问某个资源的线程数量上限。

**通俗类比：** 就像停车场入口的电子屏——显示还有几个空位，满了就不让进了。

**具体示例：**
```python
import threading
import time

# 信号量：最多3个线程同时执行
semaphore = threading.Semaphore(3)

def worker(id):
    with semaphore:  # 获取信号量（计数-1）
        print(f"线程 {id} 开始执行")
        time.sleep(2)
        print(f"线程 {id} 执行完毕")
    # 离开 with 块自动释放信号量（计数+1）

threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
# 虽然有10个线程，但最多只有3个同时执行
```

```go
// Go：Semaphore
package main

import (
    "context"
    "fmt"
    "time"

    "golang.org/x/sync/semaphore"
)

func main() {
    sem := semaphore.NewWeighted(3)  // 容量为3

    for i := 0; i < 10; i++ {
        if err := sem.Acquire(context.Background(), 1); err != nil {
            break
        }
        go func(id int) {
            defer sem.Release(1)
            fmt.Printf("Task %d running\n", id)
            time.Sleep(2 * time.Second)
        }(i)
    }
}
```

```java
// Java Semaphore
import java.util.concurrent.Semaphore;

Semaphore semaphore = new Semaphore(3);  // 3个许可

void worker(int id) throws InterruptedException {
    semaphore.acquire();  // 获取许可
    try {
        System.out.println("线程 " + id + " 执行中");
        Thread.sleep(2000);
    } finally {
        semaphore.release();  // 释放许可
    }
}
```

**为什么需要它：** 信号量控制并发度，防止资源耗尽（如数据库连接池、API限流）。

**与相关术语对比：** 信号量 vs 互斥锁——互斥锁只允许1个，信号量允许N个；信号量可实现限流、资源池等场景。

---

## 条件变量（Condition Variable）

**一句话定义：** 条件变量让线程可以"等待"某个条件成立后再继续执行。

**通俗类比：** 就像医院叫号——你拿到号后在外面等，护士叫到你的号（条件满足）你才进去。

**具体示例：**
```python
import threading

condition = threading.Condition()
data_ready = False
shared_data = None

def producer():
    global data_ready, shared_data
    with condition:
        shared_data = "生产的数据"
        data_ready = True
        print("生产者：数据已准备好")
        condition.notify()  # 通知等待的消费者

def consumer():
    global data_ready, shared_data
    with condition:
        while not data_ready:
            print("消费者：等待数据...")
            condition.wait()  # 等待条件满足
        print(f"消费者：收到数据 - {shared_data}")

t1 = threading.Thread(target=consumer)
t2 = threading.Thread(target=producer)
t1.start()
t2.start()
t1.join()
t2.join()
```

```go
// Go：sync.Cond
package main

import (
    "fmt"
    "sync"
)

func main() {
    cond := sync.NewCond(&sync.Mutex{})
    ready := false

    go func() {
        cond.L.Lock()
        for !ready {
            cond.Wait()  // 等待条件
        }
        fmt.Println("收到信号")
        cond.L.Unlock()
    }()

    // 模拟延时
    cond.L.Lock()
    ready = true
    cond.Signal()  // 发送信号
    cond.L.Unlock()

    select {}
}
```

```java
// Java Condition
import java.util.concurrent.locks.*;

ReentrantLock lock = new ReentrantLock();
Condition condition = lock.newCondition();
boolean dataReady = false;

// 生产者
lock.lock();
try {
    dataReady = true;
    condition.signal();  // 通知
} finally {
    lock.unlock();
}

// 消费者
lock.lock();
try {
    while (!dataReady) {
        condition.await();  // 等待
    }
    // 处理数据
} finally {
    lock.unlock();
}
```

**为什么需要它：** 条件变量实现线程间的协调——生产者-消费者模型、事件通知等场景必备。

**与相关术语对比：** 条件变量 vs 信号量——条件变量关注"条件是否满足"，信号量关注"还有几个可用名额"。

---

## 死锁（Deadlock）

**一句话定义：** 死锁就是两个或多个线程互相等待对方释放资源，导致所有线程都卡住无法继续。

**通俗类比：** 就像两个人在狭窄的过道相遇——A说"你先让我过"，B说"你先让我过"，谁也不让，结果都卡住了。

**具体示例：**
```python
import threading

lock_a = threading.Lock()
lock_b = threading.Lock()

# 死锁示例
def thread1():
    with lock_a:
        print("线程1：持有锁A，等待锁B")
        with lock_b:  # 等待锁B（被线程2持有）
            print("线程1：执行完成")

def thread2():
    with lock_b:
        print("线程2：持有锁B，等待锁A")
        with lock_a:  # 等待锁A（被线程1持有）
            print("线程2：执行完成")

# 两个线程互相等待，死锁！

# 解决方案：统一加锁顺序
def safe_thread1():
    with lock_a:    # 先锁A
        with lock_b:  # 再锁B
            print("安全线程1")

def safe_thread2():
    with lock_a:    # 也先锁A（统一顺序）
        with lock_b:  # 再锁B
            print("安全线程2")
```

```go
// Go：死锁检测与避免
package main

import (
    "fmt"
    "sync"
    "time"
)

func main() {
    lockA := &sync.Mutex{}
    lockB := &sync.Mutex{}

    go func() {
        lockA.Lock()
        fmt.Println("Goroutine 1: 持有 A，等待 B")
        time.Sleep(100 * time.Millisecond)
        lockB.Lock()  // 死锁！
        defer lockB.Unlock()
        lockA.Unlock()
    }()

    go func() {
        lockB.Lock()
        fmt.Println("Goroutine 2: 持有 B，等待 A")
        time.Sleep(100 * time.Millisecond)
        lockA.Lock()  // 死锁！
        defer lockA.Unlock()
        lockB.Unlock()
    }()

    time.Sleep(2 * time.Second)
    fmt.Println("程序卡死...")
}
```

**为什么需要它：** 死锁是并发编程中最难调试的问题之一，必须从设计上避免。

**与相关术语对比：** 死锁四个必要条件——互斥、持有并等待、不可剥夺、循环等待；避免策略：统一加锁顺序、超时机制、死锁检测。

---

## 原子操作（Atomic Operation）

**一句话定义：** 原子操作就是"不可分割"的操作——执行过程中不会被其他线程打断。

**通俗类比：** 就像ATM转账——从A扣钱和给B加钱必须是一个整体，不能中间被打断（否则钱可能凭空消失）。

**具体示例：**
```python
import threading

# 非原子操作（不安全）
counter = 0

def unsafe_increment():
    global counter
    for _ in range(100000):
        counter += 1  # 这不是原子操作！

# 原子操作（安全）
import ctypes
atomic_counter = ctypes.c_long(0)

def atomic_increment():
    for _ in range(100000):
        # 使用 ctypes 的原子操作（简化演示）
        ctypes.windll.kernel32.InterlockedIncrement(ctypes.byref(atomic_counter))
```

```go
// Go：atomic 包
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

func main() {
    var counter int64 = 0
    var wg sync.WaitGroup

    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            atomic.AddInt64(&counter, 1)  // 原子加
        }()
    }
    wg.Wait()
    fmt.Println(counter) // 1000
}
```

```java
// Java AtomicInteger
import java.util.concurrent.atomic.AtomicInteger;

AtomicInteger counter = new AtomicInteger(0);

void increment() {
    counter.incrementAndGet();  // 原子操作
    counter.addAndGet(10);      // 原子操作
    counter.compareAndSet(5, 10); // CAS 操作
}

int value = counter.get();  // 原子读取
```

**为什么需要它：** 原子操作是无锁并发的基础，比锁更高效，适合简单的计数器、标志位等场景。

**与相关术语对比：** 原子操作 vs 锁——原子操作更轻量但功能有限，锁更通用但开销更大；原子操作是硬件级别的支持。

---

## CAS（Compare-And-Swap）

**一句话定义：** CAS 就是"比较并交换"——先检查值是否还是预期值，如果是就更新，否则什么都不做。

**通俗类比：** 就像你跟银行说"如果我账户里还有1000块，就帮我转500出去"——银行检查余额，够就转，不够就拒绝。

**具体示例：**
```python
# Python 模拟 CAS（实际用 threading 或 ctypes）
import threading

class CASCounter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def cas_increment(self, expected, new_value):
        with self.lock:
            if self.value == expected:
                self.value = new_value
                return True
            return False

    def increment(self):
        while True:
            current = self.value
            if self.cas_increment(current, current + 1):
                break
```

```go
// Go：atomic.Value 实现 CAS
package main

import (
    "fmt"
    "sync/atomic"
)

func main() {
    var value atomic.Value
    value.Store("initial")

    // CAS 操作
    for {
        old := value.Load().(string)
        if value.CompareAndSwap(old, "updated") {
            fmt.Println("CAS 成功:", old, "->", "updated")
            break
        }
    }

    // atomic.CompareAndSwapInt64
    var counter int64 = 100
    // 如果 counter == 100，则设为 200
    swapped := atomic.CompareAndSwapInt64(&counter, 100, 200)
    fmt.Println("是否成功:", swapped, "当前值:", counter)
}
```

```java
// Java CAS
import java.util.concurrent.atomic.AtomicInteger;

AtomicInteger value = new AtomicInteger(100);

// CAS：如果当前值 == 100，则设为 200
boolean success = value.compareAndSet(100, 200);
System.out.println("成功: " + success + " 值: " + value.get());

// 乐观锁原理
int expected = value.get();
int newValue = expected + 10;
while (!value.compareAndSet(expected, newValue)) {
    expected = value.get();  // 重新读取
    newValue = expected + 10;
}
```

**为什么需要它：** CAS 是无锁数据结构和乐观锁的核心，比互斥锁更高效，适合低竞争场景。

**与相关术语对比：** CAS vs 互斥锁——CAS 乐观（假设不会冲突），互斥锁悲观（假设一定会冲突）；CAS 可能有ABA问题。

---

## 线程池（Thread Pool）

**一句话定义：** 线程池就是预先创建一组线程放在那里，有任务来就分配给空闲线程执行，避免频繁创建销毁线程。

**通俗类比：** 就像餐厅的服务员——不是每来一个客人就招一个新服务员，而是固定几个服务员轮流服务。

**具体示例：**
```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time

def task(n):
    time.sleep(1)
    return n * n

# 线程池
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(task, i) for i in range(10)]
    results = [f.result() for f in futures]
    print(results)  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# 进程池（CPU密集型任务）
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(task, range(10)))
    print(results)
```

```go
// Go：goroutine 池（用 worker pool 模式）
package main

import (
    "fmt"
    "sync"
)

func worker(id int, jobs <-chan int, results chan<- int, wg *sync.WaitGroup) {
    defer wg.Done()
    for job := range jobs {
        fmt.Printf("Worker %d processing job %d\n", id, job)
        results <- job * job
    }
}

func main() {
    jobs := make(chan int, 100)
    results := make(chan int, 100)

    var wg sync.WaitGroup
    for w := 1; w <= 3; w++ {
        wg.Add(1)
        go worker(w, jobs, results, &wg)
    }

    for j := 0; j < 9; j++ {
        jobs <- j
    }
    close(jobs)

    go func() {
        wg.Wait()
        close(results)
    }()

    for r := range results {
        fmt.Println(r)
    }
}
```

```java
// Java 线程池
import java.util.concurrent.*;

// 固定大小线程池
ExecutorService fixedPool = Executors.newFixedThreadPool(4);
fixedPool.submit(() -> System.out.println("任务执行"));

// 虚拟线程池（Java 21+）
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 10000).forEach(i ->
        executor.submit(() -> {
            Thread.sleep(Duration.ofSeconds(1));
            System.out.println("Task " + i);
        })
    );
}
```

**为什么需要它：** 线程池减少线程创建销毁开销，控制并发度，防止系统过载。

**与相关术语对比：** 线程池 vs 手动创建线程——线程池复用线程、管理生命周期；手动创建难以控制数量和生命周期。

---

## 协程（Go Routine / Python asyncio / Java Virtual Threads）

**一句话定义：** 协程就是用户态的轻量级线程，由程序自己调度而非操作系统。

**通俗类比：** 协程就像接力赛跑的运动员——不是每个人都在跑，而是谁拿到接力棒谁跑，跑完交给下一个人。

**具体示例：**
```python
import asyncio

# Python asyncio 协程
async def fetch_data(url):
    print(f"开始获取 {url}")
    await asyncio.sleep(1)  # 异步等待，不阻塞
    return f"数据 from {url}"

async def main():
    # 并发执行多个协程
    results = await asyncio.gather(
        fetch_data("url1"),
        fetch_data("url2"),
        fetch_data("url3")
    )
    print(results)

asyncio.run(main())

# 异步迭代器
async def async_range(n):
    for i in range(n):
        await asyncio.sleep(0.1)
        yield i

async def process():
    async for num in async_range(5):
        print(num)
```

```go
// Go goroutine
package main

import (
    "fmt"
    "time"
)

func worker(id int) {
    fmt.Printf("Worker %d starting\n", id)
    time.Sleep(time.Second)
    fmt.Printf("Worker %d done\n", id)
}

func main() {
    for i := 0; i < 100; i++ {
        go worker(i)  // 启动100个goroutine，非常轻量
    }
    time.Sleep(2 * time.Second)
}
```

```java
// Java Virtual Threads（虚拟线程）
import java.util.concurrent.*;

public class VirtualThreadDemo {
    public static void main(String[] args) throws Exception {
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            // 轻松创建数十万虚拟线程
            IntStream.range(0, 100_000).forEach(i ->
                executor.submit(() -> {
                    Thread.sleep(Duration.ofSeconds(1));
                    if (i % 10000 == 0) {
                        System.out.println("Task " + i + " done");
                    }
                })
            );
        }
    }
}
```

**为什么需要它：** 协程比线程更轻量，可以轻松创建数十万个，特别适合IO密集型和高并发场景。

**与相关术语对比：** 协程 vs 线程——协程用户态调度（更轻量），线程内核态调度（开销大）；Go goroutine 可动态增长，Python asyncio 单线程协作式。

---

## 消息传递（Channel / Actor 模型）

**一句话定义：** 消息传递就是线程/进程之间不直接共享内存，而是通过发送消息来通信。

**通俗类比：** 就像公司内部邮件——部门之间不直接进对方办公室，而是通过邮件沟通，避免混乱。

**具体示例：**
```python
import multiprocessing

# Python multiprocessing Queue（类似 Channel）
def producer(queue):
    for i in range(5):
        queue.put(f"消息 {i}")
    queue.put(None)  # 结束信号

def consumer(queue):
    while True:
        msg = queue.get()
        if msg is None:
            break
        print(f"收到: {msg}")

queue = multiprocessing.Queue()
p1 = multiprocessing.Process(target=producer, args=(queue,))
p2 = multiprocessing.Process(target=consumer, args=(queue,))
p1.start()
p2.start()
p1.join()
p2.join()
```

```go
// Go Channel（最经典的消息传递）
package main

import (
    "fmt"
)

func main() {
    ch := make(chan string)

    // 生产者
    go func() {
        for i := 0; i < 5; i++ {
            ch <- fmt.Sprintf("消息 %d", i)
        }
        close(ch)
    }()

    // 消费者
    for msg := range ch {
        fmt.Println("收到:", msg)
    }
}
```

```java
// Java BlockingQueue
import java.util.concurrent.*;

BlockingQueue<String> queue = new LinkedBlockingQueue<>();

// 生产者
new Thread(() -> {
    try {
        for (int i = 0; i < 5; i++) {
            queue.put("消息 " + i);
        }
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
    }
}).start();

// 消费者
new Thread(() -> {
    try {
        while (true) {
            String msg = queue.take();
            System.out.println("收到: " + msg);
        }
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
    }
}).start();
```

**为什么需要它：** 消息传递避免了共享内存的复杂性（无需锁），让并发更安全、更易推理。

**与相关术语对比：** Channel vs 共享内存——Channel 通信不共享状态，共享内存直接读写但需同步；Actor 模型是消息传递的高级抽象。

---

## Future 与 Promise

**一句话定义：** Future/Promise 就是一个"承诺"——代表一个异步操作最终会产生一个值（或错误）。

**通俗类比：** 就像网购下单后的快递单号——你现在还没收到货，但快递单号承诺你"货在路上了"。

**具体示例：**
```python
import asyncio

# Python asyncio Future
async def fetch_data():
    await asyncio.sleep(1)
    return {"name": "张三"}

async def main():
    future = asyncio.ensure_future(fetch_data())
    result = await future  # 等待结果
    print(result)

asyncio.run(main())

# concurrent.futures.Future
from concurrent.futures import ThreadPoolExecutor
import time

def slow_task(n):
    time.sleep(2)
    return n * 2

with ThreadPoolExecutor() as pool:
    future = pool.submit(slow_task, 5)
    print("任务已提交，继续做其他事...")
    result = future.result()  # 阻塞等待结果
    print(f"结果: {result}")
```

```javascript
// JavaScript Promise
function fetchData() {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            resolve({ name: "张三" });
        }, 1000);
    });
}

// 使用
fetchData()
    .then(data => console.log(data))
    .catch(err => console.error(err));

// async/await（Promise 的语法糖）
async function main() {
    try {
        const data = await fetchData();
        console.log(data);
    } catch (err) {
        console.error(err);
    }
}
```

```java
// Java CompletableFuture
import java.util.concurrent.*;

CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> {
    try { Thread.sleep(1000); } catch (Exception e) {}
    return "结果";
});

future.thenAccept(result -> System.out.println(result));

// 链式组合
CompletableFuture.supplyAsync(() -> 10)
    .thenApply(x -> x * 2)        // 20
    .thenApply(x -> x + 5)        // 25
    .thenAccept(System.out::println);  // 25
```

**为什么需要它：** Future/Promise 让异步编程更优雅，避免回调地狱，支持链式组合。

**与相关术语对比：** Future（Java/Python）是只读的异步结果，Promise（JS）可被 resolve/reject；async/await 是 Promise 的语法糖。

---

## asyncio 事件循环（Event Loop）

**一句话定义：** 事件循环就是 asyncio 的"心脏"——它不断检查有没有待处理的任务，有的话就执行。

**通俗类比：** 就像餐厅的前台经理——不断检查有没有新客人、有没有菜做好了、有没有空桌，然后协调服务员处理。

**具体示例：**
```python
import asyncio

async def task1():
    await asyncio.sleep(2)
    return "任务1完成"

async def task2():
    await asyncio.sleep(1)
    return "任务2完成"

async def main():
    # 事件循环自动调度这些协程
    results = await asyncio.gather(
        task1(),
        task2()
    )
    print(results)  # ['任务1完成', '任务2完成']（总耗时约2秒）

# 运行事件循环
asyncio.run(main())

# 更底层的事件循环操作
async def manual_loop():
    loop = asyncio.get_event_loop()

    # 创建任务
    task = loop.create_task(task1())

    # 定时回调
    loop.call_later(1, lambda: print("1秒后执行"))

    # 在 executor 中运行阻塞代码
    result = await loop.run_in_executor(None, lambda: "同步代码结果")
    print(result)
```

```python
# asyncio 高级用法
import asyncio

async def producer(queue):
    for i in range(5):
        await asyncio.sleep(0.5)
        await queue.put(f"数据 {i}")
    await queue.put(None)

async def consumer(queue):
    while True:
        item = await queue.get()
        if item is None:
            break
        print(f"处理: {item}")

async def main():
    queue = asyncio.Queue()
    # 生产者和消费者并发运行
    await asyncio.gather(
        producer(queue),
        consumer(queue)
    )

asyncio.run(main())
```

**为什么需要它：** 事件循环是 asyncio 的核心调度器，管理所有异步任务的执行和切换。

**与相关术语对比：** 事件循环 vs 线程池——事件循环是单线程协作式调度，线程池是多线程抢占式调度；事件循环更适合IO密集型，线程池更适合CPU密集型。

## 相关术语

[[函数式编程（Functional Programming）概念]]、[[面向对象编程（OOP）概念]]、[[Flutter跨平台开发实战]]、[[Go语言核心]]、[[Go语言系统编程指南]]、[[Python全栈开发教程]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
