---
title: "TypeScript深入"
tags: []
source: "baike"
source_path: "开发术语 / 编程语言基础"
collected: "2026-09-05"
status: "imported"
---

# TypeScript深入


> 📌 **导航**：本文是 **TypeScript深入** 词条，属于 programming-languages 术语集。相关枢纽：[[Go语言核心]]、[[Python高级编程完全指南]]、[[Rust系统编程入门到精通]]、[[Rust编程基础]]、[[TypeScript深入]]。

## 泛型

```typescript
function identity<T>(arg: T): T { return arg; }
```

## 条件类型与映射

```typescript
type IsString<T> = T extends string ? "yes" : "no";
type Partial<T> = { [P in keyof T]?: T[P] };
```

## Utility Types

| 类型 | 作用 |
|------|------|
| Partial<T> | 所有属性可选 |
| Pick<T,K> | 选取部分属性 |
| Omit<T,K> | 排除部分属性 |
| Record<K,V> | 键值对类型 |

## 相关术语

[[TypeScript高级编程指南]]、[[Flutter跨平台开发实战]]、[[Go语言核心]]、[[Go语言系统编程指南]]、[[Python全栈开发教程]]、[[Python高级特性]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
