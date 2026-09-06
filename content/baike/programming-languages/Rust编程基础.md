---
title: "Rust编程基础"
tags: []
source: "baike"
source_path: "开发术语 / 编程语言基础"
collected: "2026-09-05"
status: "imported"
---

# Rust编程基础

## 所有权系统

```rust
let s1 = String::from("hello");
let s2 = s1;  // s1不再有效
let s3 = s2.clone();  // 深拷贝
```

## 借用与生命周期

```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

## 并发安全

```rust
let counter = Arc::new(Mutex::new(0));
// 多线程安全共享
```

| 特性 | 优势 |
|------|------|
| 零成本抽象 | 性能媲美C++ |
| 内存安全 | 编译时保证 |
| 并发安全 | 防数据竞争 |
