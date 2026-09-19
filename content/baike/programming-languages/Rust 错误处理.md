---
title: "Rust 错误处理"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# Rust 错误处理

> 📌 **导航**：本文是 **Rust 错误处理** 词条，属 [[Rust系统编程入门到精通]] 子词条。

## 定义

**一句话定义：** Rust 把错误分两类：不可恢复的用 `panic!` 直接终止，可恢复的用 `Result<T,E>`/`Option<T>` 显式携带、并用 `?` 运算符向上传播，强制调用方正视失败。

**通俗类比：** 像不用"抛异常打乱控制流"，而是把"可能失败"写进返回类型——每个会出错的函数都在签名上明说，`?` 则是"出错就早退、把错误往上递"的简写。

## 为什么需要它

异常式控制流隐晦、难看出哪条路径会抛、代价高。Rust 用类型把"失败"显式化：`Result`/`Option` 让编译器逼你处理 `Err`/`None`，减少被吞掉的错误与"漏网 panic"，失败路径一目了然、便于库间组合。

## 核心机制

- **`panic!`**：不可恢复（断言失败、越界、`unwrap()` 遇 `None`）；打印回溯并展开栈，适合 bug/无法继续场景，不用于常规错误。
- **`Result<T,E>`/`Option<T>`**：可恢复失败的正道；`.unwrap_or_else`/`.map`/`.ok_or` 等组合。
- **`?` 运算符**：`Ok`/`Some` 则取值继续，`Err`/`None` 则提前 return 上抛（要求错误类型可实现 `From` 转换）；只能在返回 `Result`/`Option` 的函数用。
- **错误类型设计**：自定义 enum 或用 `thiserror`(库)/`anyhow`(应用) 分层；跨模块用 `From` 让 `?` 自动转换。

## 具体示例

`?` 把可恢复错误逐级上抛、`unwrap` 只用于确定不会失败的测试：

```rust
fn read_port(path: &str) -> Result<u16, std::io::Error> {
    let s = std::fs::read_to_string(path)?;   // 出错即早退传播
    Ok(s.trim().parse().unwrap_or(8080))
}
```

## 何时用与何时不用

- **用**：可预期、调用方应处理的失败用 `Result`+`?`；真正的程序级 bug/无法恢复才 `panic!`。
- **不用**：别在库的常规路径用 `unwrap()/expect()` 赌不失败；别用 `panic!` 当业务错误处理。

## 优劣与代价

✅ 失败被编码进类型、编译期强制处理、控制流显式可追踪。
✅ `?` + `From` 让传播与错误转换简洁。
⚠️ 全 `Result` 样板略重，早期错误类型设计不当会到处 `map_err`。
⚠️ 混用 panic 与 Result 会让失败语义不清。

## 与相关概念的区别

- **`Result` vs `Option`**：`Option` 表"可能没有值"，`Result` 表"可能失败且带错误原因"。
- **`?` vs `match`/`unwrap`**：`?` 是传播的糖，`unwrap` 是直接崩——生产慎用后者。
- 与 Go 错误值（[[Go接口与反射]]语境）：Go 用多返回值 + `if err!=nil`，Rust 用 `Result`+`?`，皆"显式错误"路线。

## 常见误区

- 报错就该用 `panic!`，和别语言抛异常一样。
- `?` 可以写在任意函数里。
- `unwrap()` 只是取值、不会让程序崩。

## 面试速答

> 🎯 Rust 错误处理：不可恢复 `panic!`(终止)、可恢复 `Result<T,E>`/`Option<T>` 显式携带；`?` 在返回 Result/Option 的函数里"Ok 取值、Err 早退上抛"(靠 From 转换)。把失败编进类型、编译期强制处理，避免被吞的错误；库别到处 unwrap。
> 🔍 追问：`Result` 与 `Option` 的适用差别？
> 🔍 追问：什么时候该 panic、什么时候该返回 Err？

## 相关术语

[[Rust系统编程入门到精通]]、[[Rust编程基础]]、[[命令模式]]、[[API 错误处理规范]]

## 参考资料

建议人工核验：以 The Rust Book（错误处理）与 thiserror/anyhow 文档为准；未编造文献编号。
