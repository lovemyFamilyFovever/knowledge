---
title: "TypeScript深入"
tags: []
source: "baike"
source_path: "开发术语 / 编程语言基础"
collected: "2026-09-05"
status: "imported"
---

# TypeScript深入

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
