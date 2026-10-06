---
tags: [Vue2, 源码]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/Details/toRawType.md"
---

#  toRawType 

## 1. `_toString.call(value)`

- 调用原生 `toString` 方法来获取 `value` 的内部 `[[Class]]` 标签。

- 它返回的格式固定为：`"[object Type]"`
  
  

| 值           | `_toString.call(value)` 返回 |
| ------------ | ---------------------------- |
| `{} `        | `"[object Object]"`          |
| `[]`         | `"[object Array]"`           |
| `new Date()` | `"[object Date]"`            |
| `/^$/`       | `"[object RegExp]"`          |
| `Symbol()`   | `"[object Symbol]"`          |
| `null`       | `"[object Null]"`            |
| `undefined`  | `"[object Undefined]"`       |
| `new Map()`  | `"[object Map]"`             |



 这是 JS 中**唯一能准确区分数组、正则、日期、Map 等对象类型的方法**（`typeof` 是做不到的） 

## 2. `.slice(8, -1)`

- 对上面的结果字符串进行截取：

  - `.slice(8, -1)` 表示从索引 8 开始，到倒数第 1 个字符之前结束（不包含最后一个字符）。

  

   我们以 `"[object Array]"` 为例： 

``` tex
  字符串:  [  o  b  j  e  c  t     A  r  r  a  y  ]
  索引:   0  1  2  3  4  5  6  7  8  9 10 11 12 13
```

- 结果是：`"Array"`

 同理： 

| 输入         | 原始结果               | slice(8, -1) 后 |
| ------------ | ---------------------- | --------------- |
| `[]`         | `"[object Array]"`     | `"Array"`       |
| `{}`         | `"[object Object]"`    | `"Object"`      |
| `new Date()` | `"[object Date]"`      | `"Date"`        |
| `null`       | `"[object Null]"`      | `"Null"`        |
| `undefined`  | `"[object Undefined]"` | `"Undefined"`   |
| `new Map()`  | `"[object Map]"`       | `"Map"`         |

## ✅ 最终效果：`toRawType` 函数的作用

> **输入任意值，返回其真实的“原始类型名称”（字符串）**

```js
toRawType([])        // "Array"
toRawType({})        // "Object"
toRawType(null)      // "Null"
toRawType(undefined)// "Undefined"
toRawType(new Date())// "Date"
toRawType(/abc/)     // "RegExp"
toRawType(new Map()) // "Map"
toRawType('hello')   // "String"
toRawType(123)       // "Number"
toRawType(true)      // "Boolean"
```

## 🆚 对比 `typeof`

| 值           | `typeof`   | `toRawType` | 说明                                   |
| ------------ | ---------- | ----------- | -------------------------------------- |
| `[]`         | `"object"` | `"Array"`   | ✅ `typeof` 无法识别数组                |
| `null`       | `"object"` | `"Null"`    | ✅ 经典 bug：`typeof null === 'object'` |
| `new Date()` | `"object"` | `"Date"`    | ✅ 区分具体对象类型                     |
| `{}`         | `"object"` | `"Object"`  | 基本一致                               |

👉 所以 `toRawType` 比 `typeof` **更精确、更可靠**，尤其适合在框架内部做类型判断。

## 💡 在 Vue 中的用途

Vue 内部大量使用 `toRawType` 来判断数据类型，例如：

1. **响应式系统**：判断是否是对象或数组，决定是否需要劫持 `getter/setter`。
2. **props 类型校验**：`type: Array` 时，用它来验证传入的值是否真的是数组。
3. **警告提示**：比如你传了个字符串给 `data`，Vue 会检测并报错。
4. **特殊对象处理**：比如区分 `Date`、`RegExp`，避免错误地进行响应式追踪。







