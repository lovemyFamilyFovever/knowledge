---
title: "Rust系统编程入门到精通"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# Rust系统编程入门到精通


> 📌 **导航**：本文是 **Rust系统编程入门到精通** 词条，属于 programming-languages 术语集。相关枢纽：[[Go语言核心]]、[[Python高级编程完全指南]]、[[Rust系统编程入门到精通]]、[[Rust编程基础]]、[[TypeScript深入]]。

## Rust 系统编程教程：从入门到精通

## 1. 所有权系统：Rust安全的基石

所有权系统是Rust最独特的特性，它让Rust在编译时就能保证内存安全，无需垃圾回收器。

### 1.1 所有权规则

Rust的所有权系统基于三条基本规则：
1. 每个值都有一个变量作为其所有者
2. 同一时刻只能有一个所有者
3. 当所有者离开作用域时，值会被丢弃

```rust
fn main() {
    // s1是字符串的所有者
    let s1 = String::from("hello");
    // 所有权转移给s2，s1不再有效
    let s2 = s1;
    
    // println!("{}", s1); // 编译错误！s1已失效
    println!("{}", s2); // 正常工作
}
```

### 1.2 借用与引用

借用允许我们使用值而不获取所有权：

```rust
fn calculate_length(s: &String) -> usize { // s是对String的引用
    s.len()
} // s离开作用域，但因为不拥有所有权，所以String不会被丢弃

fn main() {
    let s1 = String::from("hello");
    // 不可变借用
    let len = calculate_length(&s1);
    println!("The length of '{}' is {}.", s1, len);
    
    // 可变借用
    let mut s2 = String::from("hello");
    change(&mut s2);
    println!("Changed: {}", s2);
}

fn change(s: &mut String) {
    s.push_str(", world");
}
```

**借用规则：**
- 任意时刻，要么有一个可变引用，要么有多个不可变引用
- 引用必须始终有效

### 1.3 生命周期

生命周期确保引用在有效期内：

```rust
// 显式生命周期标注
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() {
        x
    } else {
        y
    }
}

// 结构体中的生命周期
struct ImportantExcerpt<'a> {
    part: &'a str,
}

impl<'a> ImportantExcerpt<'a> {
    fn level(&self) -> i32 {
        3
    }
    
    fn announce_and_return_part(&self, announcement: &str) -> &str {
        println!("Attention please: {}", announcement);
        self.part
    }
}

fn main() {
    let string1 = String::from("long string is long");
    let result;
    {
        let string2 = String::from("xyz");
        result = longest(string1.as_str(), string2.as_str());
        println!("The longest string is '{}'", result);
    }
}
```

**生命周期省略规则：**
1. 每个引用参数都有自己的生命周期
2. 如果只有一个输入生命周期，该生命周期赋给所有输出生命周期
3. 如果是`&self`或`&mut self`，`self`的生命周期赋给所有输出生命周期

## 2. Trait系统和泛型

### 2.1 Trait基础

Trait定义共享行为，类似于其他语言的接口：

```rust
trait Summary {
    fn summarize(&self) -> String;
    
    // 默认实现
    fn default_summary(&self) -> String {
        String::from("(Read more...)")
    }
}

struct NewsArticle {
    headline: String,
    location: String,
    author: String,
    content: String,
}

impl Summary for NewsArticle {
    fn summarize(&self) -> String {
        format!("{}, by {} ({})", self.headline, self.author, self.location)
    }
}

struct Tweet {
    username: String,
    content: String,
    reply: bool,
    retweet: bool,
}

impl Summary for Tweet {
    fn summarize(&self) -> String {
        format!("{}: {}", self.username, self.content)
    }
}

// Trait作为参数
fn notify(item: &impl Summary) {
    println!("Breaking news! {}", item.summarize());
}

// Trait bound语法
fn notify2<T: Summary>(item: &T) {
    println!("Breaking news! {}", item.summarize());
}

// 多个Trait bound
fn notify3<T: Summary + std::fmt::Display>(item: &T) {
    println!("Breaking news! {}", item.summarize());
}

// where子句
fn some_function<T, U>(t: &T, u: &U) -> i32
where
    T: Display + Clone,
    U: Clone + Debug,
{
    // ...
}
```

### 2.2 泛型与单态化

Rust的泛型是零成本抽象，在编译时单态化：

```rust
// 泛型函数
fn largest<T: PartialOrd>(list: &[T]) -> &T {
    let mut largest = &list[0];
    
    for item in list {
        if item > largest {
            largest = item;
        }
    }
    
    largest
}

// 泛型结构体
struct Point<T> {
    x: T,
    y: T,
}

// 为泛型结构体实现方法
impl<T> Point<T> {
    fn x(&self) -> &T {
        &self.x
    }
}

// 特定类型的方法实现
impl Point<f32> {
    fn distance_from_origin(&self) -> f32 {
        (self.x.powi(2) + self.y.powi(2)).sqrt()
    }
}

// 泛型枚举
enum Option<T> {
    Some(T),
    None,
}

enum Result<T, E> {
    Ok(T),
    Err(E),
}

fn main() {
    let number_list = vec![34, 50, 25, 100, 65];
    let result = largest(&number_list);
    println!("The largest number is {}", result);
    
    let integer = Point { x: 5, y: 10 };
    let float = Point { x: 1.0, y: 4.0 };
    
    println!("p.x = {}", integer.x());
    println!("Distance from origin: {}", float.distance_from_origin());
}
```

### 2.3 Trait对象与动态分发

```rust
trait Draw {
    fn draw(&self);
}

struct Button {
    width: u32,
    height: u32,
    label: String,
}

impl Draw for Button {
    fn draw(&self) {
        println!("Drawing button: {}", self.label);
    }
}

struct SelectBox {
    width: u32,
    height: u32,
    options: Vec<String>,
}

impl Draw for SelectBox {
    fn draw(&self) {
        println!("Drawing select box with {} options", self.options.len());
    }
}

// 动态分发：使用Trait对象
struct Screen {
    components: Vec<Box<dyn Draw>>,
}

impl Screen {
    fn run(&self) {
        for component in self.components.iter() {
            component.draw();
        }
    }
}

// 静态分发：使用泛型和Trait bound
struct Screen2<T: Draw> {
    components: Vec<T>,
}

fn main() {
    // 动态分发示例
    let screen = Screen {
        components: vec![
            Box::new(SelectBox {
                width: 75,
                height: 10,
                options: vec![
                    String::from("Yes"),
                    String::from("Maybe"),
                    String::from("No"),
                ],
            }),
            Box::new(Button {
                width: 50,
                height: 10,
                label: String::from("OK"),
            }),
        ],
    };
    
    screen.run();
}
```

## 3. 错误处理：Result、Option与?运算符

### 3.1 不可恢复错误：panic!

```rust
fn main() {
    // panic!("crash and burn");
    
    // 通过环境变量控制回溯
    // RUST_BACKTRACE=1 cargo run
    
    let v = vec![1, 2, 3];
    v[99]; // 这会触发panic
}
```

### 3.2 可恢复错误：Result

```rust
use std::fs::File;
use std::io::ErrorKind;

fn main() {
    let f = File::open("hello.txt");
    
    let f = match f {
        Ok(file) => file,
        Err(error) => match error.kind() {
            ErrorKind::NotFound => match File::create("hello.txt") {
                Ok(fc) => fc,
                Err(e) => panic!("Problem creating the file: {:?}", e),
            },
            other_error => {
                panic!("Problem opening the file: {:?}", other_error)
            }
        },
    };
}
```

### 3.3 ?运算符简化错误处理

```rust
use std::fs::File;
use std::io::{self, Read};

fn read_username_from_file() -> Result<String, io::Error> {
    let mut s = String::new();
    
    // 使用?运算符，等价于：
    // let mut f = match File::open("hello.txt") {
    //     Ok(file) => file,
    //     Err(e) => return Err(e),
    // };
    
    File::open("hello.txt")?.read_to_string(&mut s)?;
    Ok(s)
}

// 更简洁的链式调用
fn read_username_from_file2() -> Result<String, io::Error> {
    let mut s = String::new();
    File::open("hello.txt")?.read_to_string(&mut s)?;
    Ok(s)
}

// 使用标准库函数
fn read_username_from_file3() -> Result<String, io::Error> {
    std::fs::read_to_string("hello.txt")
}

// main函数也可以返回Result
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let f = File::open("hello.txt")?;
    Ok(())
}
```

### 3.4 Option与?的结合使用

```rust
fn last_char_of_first_line(text: &str) -> Option<char> {
    text.lines().next()?.chars().last()
}

fn divide(numerator: f64, denominator: f64) -> Option<f64> {
    if denominator == 0.0 {
        None
    } else {
        Some(numerator / denominator)
    }
}

struct Person {
    name: Option<String>,
    age: Option<u32>,
}

impl Person {
    fn get_name(&self) -> Option<&str> {
        self.name.as_deref()
    }
    
    fn get_age(&self) -> Option<u32> {
        self.age
    }
}

fn get_person_info(person: &Person) -> Option<String> {
    let name = person.get_name()?;
    let age = person.get_age()?;
    Some(format!("{} is {} years old", name, age))
}

fn main() {
    let text = "first\nsecond";
    println!("{:?}", last_char_of_first_line(text));
    
    let person = Person {
        name: Some(String::from("Alice")),
        age: Some(30),
    };
    println!("{:?}", get_person_info(&person));
}
```

## 4. 智能指针

### 4.1 Box<T>：堆上分配

```rust
use List::{Cons, Nil};

// 递归类型需要Box
enum List {
    Cons(i32, Box<List>),
    Nil,
}

// 特征对象的使用
trait Animal {
    fn speak(&self);
}

struct Dog;
struct Cat;

impl Animal for Dog {
    fn speak(&self) {
        println!("Woof!");
    }
}

impl Animal for Cat {
    fn speak(&self) {
        println!("Meow!");
    }
}

fn main() {
    // Box的使用场景
    let b = Box::new(5);
    println!("b = {}", b);
    
    // 递归类型
    let list = Cons(1, Box::new(Cons(2, Box::new(Cons(3, Box::new(Nil))))));
    
    // 特征对象
    let animals: Vec<Box<dyn Animal>> = vec![Box::new(Dog), Box::new(Cat)];
    for animal in animals {
        animal.speak();
    }
    
    // 大数据堆分配
    let large_array = Box::new([0; 1000000]);
}
```

### 4.2 Rc<T>：引用计数

```rust
use std::rc::Rc;

enum List {
    Cons(i32, Rc<List>),
    Nil,
}

use List::{Cons, Nil};

fn main() {
    // 共享所有权
    let a = Rc::new(Cons(5, Rc::new(Cons(10, Rc::new(Nil)))));
    println!("count after creating a = {}", Rc::strong_count(&a));
    
    let b = Cons(3, Rc::clone(&a));
    println!("count after creating b = {}", Rc::strong_count(&a));
    
    {
        let c = Cons(4, Rc::clone(&a));
        println!("count after creating c = {}", Rc::strong_count(&a));
    }
    
    println!("count after c goes out of scope = {}", Rc::strong_count(&a));
}
```

### 4.3 RefCell<T>：内部可变性

```rust
use std::cell::RefCell;

// 内部可变性模式
pub trait Messenger {
    fn send(&self, msg: &str);
}

struct MockMessenger {
    sent_messages: RefCell<Vec<String>>,
}

impl MockMessenger {
    fn new() -> MockMessenger {
        MockMessenger {
            sent_messages: RefCell::new(vec![]),
        }
    }
}

impl Messenger for MockMessenger {
    fn send(&self, message: &str) {
        self.sent_messages.borrow_mut().push(String::from(message));
    }
}

fn main() {
    let mock_messenger = MockMessenger::new();
    mock_messenger.send("test message");
    
    println!("Messages sent: {:?}", mock_messenger.sent_messages.borrow());
    
    // RefCell在运行时检查借用规则
    let data = RefCell::new(5);
    
    // 同时存在多个不可变借用
    let r1 = data.borrow();
    let r2 = data.borrow();
    println!("r1: {}, r2: {}", r1, r2);
    
    // 可变借用需要单独进行
    // let r3 = data.borrow_mut(); // 这会panic，因为已有不可变借用
    drop(r1);
    drop(r2);
    
    let mut r3 = data.borrow_mut();
    *r3 += 10;
    println!("r3: {}", r3);
}
```

### 4.4 Arc<T>：原子引用计数

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    // 线程安全的共享所有权
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];
    
    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            let mut num = counter.lock().unwrap();
            *num += 1;
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    println!("Result: {}", *counter.lock().unwrap());
    
    // 组合使用：多线程共享可变状态
    let shared_data = Arc::new(RefCell::new(vec![]));
    let mut handles = vec![];
    
    for i in 0..5 {
        let data = Arc::clone(&shared_data);
        let handle = thread::spawn(move || {
            data.borrow_mut().push(i);
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    println!("Shared data: {:?}", shared_data.borrow());
}
```

## 5. 并发编程

### 5.1 线程基础

```rust
use std::thread;
use std::time::Duration;

fn main() {
    // 创建线程
    let handle = thread::spawn(|| {
        for i in 1..10 {
            println!("hi number {} from the spawned thread!", i);
            thread::sleep(Duration::from_millis(1));
        }
    });
    
    for i in 1..5 {
        println!("hi number {} from the main thread!", i);
        thread::sleep(Duration::from_millis(1));
    }
    
    handle.join().unwrap();
    
    // 使用move闭包
    let v = vec![1, 2, 3];
    
    let handle = thread::spawn(move || {
        println!("Here's a vector: {:?}", v);
    });
    
    handle.join().unwrap();
    // println!("{:?}", v); // 编译错误！v的所有权已转移给线程
}
```

### 5.2 消息传递：通道

```rust
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

fn main() {
    // 多生产者，单消费者
    let (tx, rx) = mpsc::channel();
    
    thread::spawn(move || {
        let val = String::from("hi");
        tx.send(val).unwrap();
        // println!("val is {}", val); // 编译错误！所有权已转移
    });
    
    let received = rx.recv().unwrap();
    println!("Got: {}", received);
    
    // 多个值
    let (tx, rx) = mpsc::channel();
    
    thread::spawn(move || {
        let vals = vec![
            String::from("hi"),
            String::from("from"),
            String::from("the"),
            String::from("thread"),
        ];
        
        for val in vals {
            tx.send(val).unwrap();
            thread::sleep(Duration::from_secs(1));
        }
    });
    
    for received in rx {
        println!("Got: {}", received);
    }
    
    // 多个发送者
    let (tx, rx) = mpsc::channel();
    
    let tx1 = mpsc::Sender::clone(&tx);
    thread::spawn(move || {
        let vals = vec![
            String::from("1: hi"),
            String::from("1: from"),
            String::from("1: the"),
            String::from("1: thread"),
        ];
        
        for val in vals {
            tx1.send(val).unwrap();
            thread::sleep(Duration::from_secs(1));
        }
    });
    
    thread::spawn(move || {
        let vals = vec![
            String::from("2: more"),
            String::from("2: messages"),
            String::from("2: for"),
            String::from("2: you"),
        ];
        
        for val in vals {
            tx.send(val).unwrap();
            thread::sleep(Duration::from_secs(1));
        }
    });
    
    for received in rx {
        println!("Got: {}", received);
    }
}
```

### 5.3 共享状态：Mutex和RwLock

```rust
use std::sync::{Mutex, RwLock, Arc};
use std::thread;

fn main() {
    // Mutex示例
    let m = Mutex::new(5);
    
    {
        let mut num = m.lock().unwrap();
        *num = 6;
    }
    
    println!("m = {:?}", m);
    
    // 多线程共享Mutex
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];
    
    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            let mut num = counter.lock().unwrap();
            *num += 1;
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    println!("Result: {}", *counter.lock().unwrap());
    
    // RwLock示例：多个读者或单个写者
    let rw_lock = Arc::new(RwLock::new(0));
    let mut handles = vec![];
    
    // 创建多个读者
    for i in 0..5 {
        let lock = Arc::clone(&rw_lock);
        let handle = thread::spawn(move || {
            let read_guard = lock.read().unwrap();
            println!("Reader {}: value is {}", i, *read_guard);
        });
        handles.push(handle);
    }
    
    // 创建写者
    let lock = Arc::clone(&rw_lock);
    let handle = thread::spawn(move || {
        let mut write_guard = lock.write().unwrap();
        *write_guard = 42;
        println!("Writer: set value to {}", *write_guard);
    });
    handles.push(handle);
    
    // 再创建一些读者
    for i in 5..10 {
        let lock = Arc::clone(&rw_lock);
        let handle = thread::spawn(move || {
            let read_guard = lock.read().unwrap();
            println!("Reader {}: value is {}", i, *read_guard);
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
}
```

### 5.4 Send和Sync Trait

```rust
// Send：可以在线程间转移所有权
// Sync：可以安全地从多个线程访问

use std::rc::Rc;
use std::sync::Arc;

fn main() {
    // Rc不是Send，因为它的引用计数不是原子的
    // let rc = Rc::new(5);
    // let handle = thread::spawn(move || {
    //     println!("{}", rc);
    // });
    
    // Arc是Send和Sync的
    let arc = Arc::new(5);
    let arc_clone = Arc::clone(&arc);
    
    let handle = thread::spawn(move || {
        println!("Arc value: {}", arc_clone);
    });
    
    handle.join().unwrap();
    println!("Main thread Arc: {}", arc);
    
    // 自动实现Send和Sync的规则
    // 1. 如果所有字段都是Send，则结构体是Send
    // 2. 如果所有字段都是Sync，则结构体是Sync
    // 3. 包含非Send/Sync类型的结构体需要用PhantomData标记
}
```

## 6. 异步编程

### 6.1 async/await基础

```rust
use std::future::Future;
use std::pin::Pin;
use std::task::{Context, Poll};

// 手动实现Future
struct CountDown {
    count: u32,
}

impl Future for CountDown {
    type Output = String;
    
    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        if self.count == 0 {
            Poll::Ready("Done!".to_string())
        } else {
            println!("Count: {}", self.count);
            self.count -= 1;
            cx.waker().wake_by_ref();
            Poll::Pending
        }
    }
}

// 使用async/await
async fn async_function() -> String {
    println!("Starting async function");
    
    // 模拟异步操作
    let count = 3;
    let mut counter = count;
    
    while counter > 0 {
        println!("Counter: {}", counter);
        counter -= 1;
        // 这里会让出执行权
        yield_now().await;
    }
    
    "Async function completed".to_string()
}

// 简单的yield实现
struct YieldNow {
    yielded: bool,
}

impl Future for YieldNow {
    type Output = ();
    
    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<()> {
        if self.yielded {
            Poll::Ready(())
        } else {
            self.yielded = true;
            cx.waker().wake_by_ref();
            Poll::Pending
        }
    }
}

fn yield_now() -> YieldNow {
    YieldNow { yielded: false }
}

// 异步块和异步移动
async fn fetch_data(url: &str) -> Result<String, Box<dyn std::error::Error>> {
    // 模拟网络请求
    Ok(format!("Data from {}", url))
}

async fn process_data(data: String) -> String {
    format!("Processed: {}", data)
}

fn main() {
    let rt = tokio::runtime::Runtime::new().unwrap();
    rt.block_on(async {
        // 使用.await等待Future完成
        let result = async_function().await;
        println!("Result: {}", result);
        
        // 异步组合
        let data = fetch_data("https://example.com").await.unwrap();
        let processed = process_data(data).await;
        println!("Final: {}", processed);
        
        // 并发执行多个Future
        let future1 = async { 1 };
        let future2 = async { 2 };
        let (result1, result2) = tokio::join!(future1, future2);
        println!("Results: {} and {}", result1, result2);
    });
}
```

### 6.2 Tokio运行时

```rust
use tokio::time::{sleep, Duration};
use tokio::fs;
use tokio::io::{self, AsyncReadExt, AsyncWriteExt};

#[tokio::main]
async fn main() -> io::Result<()> {
    // 异步sleep
    println!("Start");
    sleep(Duration::from_secs(1)).await;
    println!("End after 1 second");
    
    // 异步文件操作
    let mut file = fs::File::create("hello.txt").await?;
    file.write_all(b"Hello, async world!").await?;
    
    let mut contents = String::new();
    let mut file = fs::File::open("hello.txt").await?;
    file.read_to_string(&mut contents).await?;
    println!("File contents: {}", contents);
    
    // 异步网络操作
    use tokio::net::TcpListener;
    use tokio::io::{AsyncReadExt, AsyncWriteExt};
    
    let listener = TcpListener::bind("127.0.0.1:8080").await?;
    
    loop {
        let (mut socket, _) = listener.accept().await?;
        
        tokio::spawn(async move {
            let mut buf = [0; 1024];
            
            loop {
                let n = match socket.read(&mut buf).await {
                    Ok(0) => return,
                    Ok(n) => n,
                    Err(_) => return,
                };
                
                if socket.write_all(&buf[..n]).await.is_err() {
                    return;
                }
            }
        });
    }
}

// 多个异步任务并发
async fn perform_tasks() {
    let task1 = tokio::spawn(async {
        sleep(Duration::from_secs(2)).await;
        println!("Task 1 completed");
        1
    });
    
    let task2 = tokio::spawn(async {
        sleep(Duration::from_secs(1)).await;
        println!("Task 2 completed");
        2
    });
    
    let result1 = task1.await.unwrap();
    let result2 = task2.await.unwrap();
    println!("Results: {} and {}", result1, result2);
}
```

### 6.3 Stream和Sink

```rust
use tokio::stream::{self, Stream, StreamExt};
use tokio::sync::mpsc;

// 创建Stream
fn create_number_stream() -> impl Stream<Item = i32> {
    stream::iter(1..=10)
}

// 自定义Stream
struct Counter {
    count: u32,
    max: u32,
}

impl Counter {
    fn new(max: u32) -> Counter {
        Counter { count: 0, max }
    }
}

impl Stream for Counter {
    type Item = u32;
    
    fn poll_next(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Option<Self::Item>> {
        if self.count < self.max {
            self.count += 1;
            cx.waker().wake_by_ref();
            Poll::Ready(Some(self.count))
        } else {
            Poll::Ready(None)
        }
    }
}

#[tokio::main]
async fn main() {
    // 使用Stream
    let mut stream = create_number_stream();
    
    while let Some(number) = stream.next().await {
        println!("Got: {}", number);
    }
    
    // 收集Stream结果
    let numbers: Vec<i32> = create_number_stream().collect().await;
    println!("Collected: {:?}", numbers);
    
    // 过滤和映射
    let filtered: Vec<i32> = create_number_stream()
        .filter(|x| x % 2 == 0)
        .map(|x| x * 10)
        .collect()
        .await;
    println!("Filtered and mapped: {:?}", filtered);
    
    // 使用通道作为Stream
    let (tx, mut rx) = mpsc::channel(32);
    
    tokio::spawn(async move {
        for i in 1..=5 {
            tx.send(i).await.unwrap();
            tokio::time::sleep(std::time::Duration::from_millis(100)).await;
        }
    });
    
    while let Some(value) = rx.recv().await {
        println!("Received: {}", value);
    }
}
```

## 7. Unsafe Rust

### 7.1 unsafe的使用场景

```rust
// unsafe允许的额外操作：
// 1. 解引用裸指针
// 2. 调用unsafe函数或方法
// 3. 访问或修改可变静态变量
// 4. 实现unsafe trait

fn main() {
    // 1. 裸指针
    let mut num = 5;
    
    let r1 = &num as *const i32;
    let r2 = &mut num as *mut i32;
    
    // 创建裸指针是安全的，解引用才需要unsafe
    unsafe {
        println!("r1 is: {}", *r1);
        println!("r2 is: {}", *r2);
        *r2 = 10;
        println!("r2 is: {}", *r2);
    }
    
    // 2. 调用unsafe函数
    unsafe fn dangerous() {}
    
    unsafe {
        dangerous();
    }
    
    // 3. 安全抽象封装unsafe代码
    fn split_at_mut(slice: &mut [i32], mid: usize) -> (&mut [i32], &mut [i32]) {
        let len = slice.len();
        let ptr = slice.as_mut_ptr();
        
        assert!(mid <= len);
        
        unsafe {
            (
                std::slice::from_raw_parts_mut(ptr, mid),
                std::slice::from_raw_parts_mut(ptr.add(mid), len - mid),
            )
        }
    }
    
    let mut v = vec![1, 2, 3, 4, 5, 6];
    let (left, right) = split_at_mut(&mut v, 3);
    println!("Left: {:?}, Right: {:?}", left, right);
}

// 4. 访问可变静态变量
static mut COUNTER: u32 = 0;

fn add_to_count(inc: u32) {
    unsafe {
        COUNTER += inc;
    }
}

// 5. 实现unsafe trait
unsafe trait Foo {
    fn dangerous_method(&self);
}

unsafe impl Foo for i32 {
    fn dangerous_method(&self) {
        println!("called dangerous_method on {}", self);
    }
}

// extern函数调用（FFI，将在下一章详细讨论）
extern "C" {
    fn abs(input: i32) -> i32;
}

#[link(name = "m")]
extern "C" {
    fn sqrt(x: f64) -> f64;
}
```

### 7.2 裸指针与FFI

```rust
use std::ffi::{CStr, CString};
use std::os::raw::c_char;

// 与C字符串交互
fn safe_print_cstring(ptr: *const c_char) {
    if ptr.is_null() {
        println!("Null pointer!");
        return;
    }
    
    unsafe {
        let c_str = CStr::from_ptr(ptr);
        match c_str.to_str() {
            Ok(s) => println!("C string: {}", s),
            Err(e) => println!("Invalid UTF-8: {}", e),
        }
    }
}

// 将Rust字符串转换为C字符串
fn rust_to_c_string(s: &str) -> *const c_char {
    let c_string = CString::new(s).expect("CString::new failed");
    c_string.into_raw()
}

// 从C字符串收回所有权
fn reclaim_c_string(ptr: *mut c_char) {
    unsafe {
        if !ptr.is_null() {
            // 重新获取CString的所有权，确保内存被正确释放
            let _ = CString::from_raw(ptr);
        }
    }
}

fn main() {
    // 使用C标准库函数
    let x = -5;
    unsafe {
        println!("Absolute value of {}: {}", x, abs(x));
    }
    
    let x = 4.0;
    unsafe {
        println!("Square root of {}: {}", x, sqrt(x));
    }
    
    // C字符串操作
    let c_string = CString::new("Hello, C!").unwrap();
    let ptr = c_string.as_ptr();
    safe_print_cstring(ptr);
    
    // Rust字符串到C字符串
    let rust_string = "Hello from Rust";
    let c_ptr = rust_to_c_string(rust_string);
    safe_print_c_string(c_ptr);
    reclaim_c_string(c_ptr as *mut c_char);
}
```

### 7.3 内存布局与对齐

```rust
use std::mem;

// 结构体布局
#[repr(C)] // 使用C内存布局
struct CStyleStruct {
    a: u8,
    b: u32,
    c: u8,
}

#[repr(packed)] // 紧凑布局，无填充
struct PackedStruct {
    a: u8,
    b: u32,
    c: u8,
}

// 带枚举的内存布局
#[repr(u8)]
enum Color {
    Red = 0,
    Green = 1,
    Blue = 2,
}

fn main() {
    println!("Size of CStyleStruct: {}", mem::size_of::<CStyleStruct>());
    println!("Alignment of CStyleStruct: {}", mem::align_of::<CStyleStruct>());
    
    println!("Size of PackedStruct: {}", mem::size_of::<PackedStruct>());
    println!("Alignment of PackedStruct: {}", mem::align_of::<PackedStruct>());
    
    // 内存对齐检查
    let c_struct = CStyleStruct { a: 1, b: 2, c: 3 };
    let packed_struct = PackedStruct { a: 1, b: 2, c: 3 };
    
    println!("CStyleStruct offsets: a={}, b={}, c={}",
        memoffset_of!(CStyleStruct, a),
        memoffset_of!(CStyleStruct, b),
        memoffset_of!(CStyleStruct, c)
    );
    
    // 裸指针算术
    let mut data = [1u8, 2, 3, 4, 5, 6, 7, 8];
    let ptr = data.as_mut_ptr();
    
    unsafe {
        // 转换为u32指针（假设小端序）
        let u32_ptr = ptr as *mut u32;
        println!("u32 at
```

## 相关术语

[[Rust编程基础]]、[[Rust Web开发实战]]、[[Flutter跨平台开发实战]]、[[Go语言核心]]、[[Go语言系统编程指南]]、[[Python全栈开发教程]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
