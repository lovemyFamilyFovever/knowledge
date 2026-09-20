---
title: "serde 序列化与反序列化"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# serde 序列化与反序列化

> 📌 **导航**：本文是 **serde 序列化与反序列化** 词条，属 [[Rust Web开发实战]] 子词条。Web 数据交换另见 [[Rust Web 数据库集成]]。

## 定义

**一句话定义：** serde 是 Rust 的序列化框架，用 `#[derive(Serialize, Deserialize)]` 把 Rust 结构与"数据格式"解耦——同一套类型可对接 JSON、YAML、TOML、MessagePack 等任意 `Serializer`/`Deserializer` 实现。

**通俗类比：** 像万能插座适配器：你的数据（电器）只管实现一次"可序列化"接口，插头（JSON/XML/二进制…）换哪个都不改电器本身。

## 为什么需要它

网络 API、配置文件、消息队列都要在"内存结构"与"字节/文本"间来回转换。若每种格式各写一套解析，代码爆炸且易错。serde 把"结构描述"和"具体格式"分离：你只 derive 一次，格式由后端库（serde_json 等）负责，跨格式复用、编译期对齐字段。

## 核心机制

- **derive 基础**：`#[derive(Serialize, Deserialize)]` + `serde_json::to_string` / `from_str` 即完成 JSON 互转。
- **字段属性**：`#[serde(rename="createdAt")]` 改键名；`skip_serializing_if="Option::is_none"` 省略空值；`skip_serializing` 完全隐藏敏感字段（如 password_hash）；`#[serde(default)]` 给默认值。
- **自定义 with**：`#[serde(with="module")]` 挂手写 `serialize/deserialize`（如 chrono 日期按指定 `FORMAT` 转字符串）。
- **泛型与标签**：`ApiResponse<T>` 直接携带；enum 用 `#[serde(tag=...)]` 控制内部/外部标签表示。
- **Web 集成**：Axum 的 `Json<T>` 提取器/响应的背后就是 serde；内容协商 JSON/XML 各接对应实现。

## 具体示例

```rust
#[derive(Serialize, Deserialize)]
struct UserDetail {
    id: u64,
    name: String,
    #[serde(rename="role")] user_role: UserRole,
    #[serde(skip_serializing_if="Option::is_none")] phone: Option<String>,
    #[serde(skip_serializing)] password_hash: String,
}
let s = serde_json::to_string(&user)?;   // 序列化为 JSON 字符串
```

## 何时用与何时不用

- **用**：任何要在结构体与 JSON/配置/消息间转换处都用 serde；API 请求响应体、配置文件、RPC 载荷是主战场。
- **不用**：极高频且需零拷贝的二进制协议，可能用 `bincode`/`prost`/手写更合适（serde 仍常作门面）；一次性 `format!` 拼字符串不值得引入结构。

## 优劣与代价

✅ 一次 derive 适配多格式；字段属性精细控制命名、省略、默认、脱敏，样板极少。
✅ 与 Axum/SQLx/配置库天然协作，是 Rust 数据交换事实标准。
⚠️ 反序列化错误信息对复杂 enum 有时晦涩；属性组合多时需要文档辅助记忆。
⚠️ 动态/自描述格式（如任意 JSON→Map）会牺牲类型安全，退化成 `serde_json::Value`。

## 与相关概念的区别

- **Serialize vs Deserialize**：前者 Rust→数据（出站），后者 数据→Rust（入站），各一个 trait。
- **`rename` vs `skip`**：rename 改键名仍传输，skip 干脆不出现于结果。
- **typed 结构 vs `Value`**：typed 编译期对齐字段，`Value` 灵活但把错误推迟到运行时。

## 常见误区

- 加了 `Deserialize` 就能自动校验业务规则（如邮箱格式），不合法会拒绝。
- `Option<T>` 字段默认就会省略 `None`，不需要 `skip_serializing_if`。
- `password_hash` 不加 `skip_serializing` 也不会被序列化出去。

## 面试速答

> 🎯 serde=用 `derive(Serialize,Deserialize)` 解耦结构与格式，一套类型对接 JSON/YAML/TOML；字段属性 `rename`/`skip`/`default`/`with` 控命名、省略、脱敏、自定义；Axum `Json<T>` 背后就是它。
> 🔍 追问：`Option` 字段序列化默认会怎样？
> 🔍 追问：日期字段如何自定义格式？

## 相关术语

[[Rust Web开发实战]]、[[Rust Web 数据库集成]]、[[Axum 路由与中间件]]、[[Rust编程基础]]、[[Rust 错误处理]]

## 参考资料

建议人工核验：以 serde / serde_json 官方文档为准；未编造文献编号、标准号或 URL。
