---
title: "Python 描述符与上下文管理器"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# Python 描述符与上下文管理器

> 📌 **导航**：本文是 **Python 描述符与上下文管理器** 词条，属 [[Python高级编程完全指南]] 子词条。

## 定义

**一句话定义：** 描述符是实现了 `__get__/__set__/__delete__` 的类，作为类属性时接管字段访问（property 的底层）；上下文管理器实现 `__enter__/__exit__`，配合 `with` 保证资源被成对获取与释放。

**通俗类比：** 描述符像装在门框上的"感应器"——每次读写这个属性都会先经过它做校验/计算；上下文管理器像"自动门"——进门(`__enter__`)、出门(`__exit__`)必关，异常也关。

## 为什么需要它

需要"访问某字段时自动做校验/惰性计算/类型转换"时，描述符把这逻辑收敛成一个可复用组件（多个字段共享），比每个属性写一堆 getter 优雅。需要"无论是否异常都释放资源"时，`with` 把 try/finally 的配对模板化，避免遗漏关闭。

## 核心机制

- **描述符**：数据描述符（定义 `__set__`/`__delete__`）优先于实例 `__dict__`；非数据描述符（只有 `__get__`）则被实例字典覆盖——这一优先级差异是常见坑。`property`、方法绑定、`classmethod` 底层都是描述符。
- **上下文管理器**：`with obj:` 调 `obj.__enter__()` 拿返回值、退出（含异常）必调 `obj.__exit__(exc)` 决定是否吞异常/清理。
- **`contextlib.contextmanager`**：用生成器 + `yield` 快速定义——yield 前=进入、后=退出，省去手写类。

## 具体示例

描述符做字段校验，或 contextmanager 用生成器包资源：

```python
# 描述符：访问 age 时自动校验
class Validated:
    def __set_name__(self, owner, name): self.n = name
    def __get__(self, inst, _): return inst.__dict__[self.n]
    def __set__(self, inst, v):
        if v < 0: raise ValueError
        inst.__dict__[self.n] = v

# 或用生成器造上下文管理器
@contextmanager
def open_db():
    c = connect(); 
    try: yield c
    finally: c.close()
```

## 何时用与何时不用

- **用**：多字段重复的校验/转换/惰性求值→描述符；任何"获取-释放"成对资源（文件/锁/事务/连接）→ with/contextmanager。
- **不用**：单字段简单存取用 `property` 即可，别过度上描述符类；`__exit__` 里别吞不该吞的异常。

## 优劣与代价

✅ 描述符把字段访问逻辑组件化、跨类复用，是 property/方法背后的统一机制。
✅ with 把资源清理与异常路径绑死，杜绝"忘记关闭"。
⚠️ 数据/非数据描述符的优先级规则反直觉、易踩坑。
⚠️ contextmanager 忘写 try/finally 会使异常时不清理。

## 与相关概念的区别

- **property vs 描述符**：property 是"函数包装成属性"的便捷语法，本质就是一个数据描述符；需要跨类复用/带参数才用自定义描述符。
- **with vs try/finally**：with 是成对清理的声明式封装，把 finally 模式抽象出来。
- 二者同属"协议驱动的魔法方法"，但作用对象不同：描述符管属性访问、上下文管理器管作用域资源。

## 常见误区

- property 和描述符是两套无关的机制。
- `with` 只是语法糖，对异常时资源释放没有实际保障。
- 非数据描述符（仅 `__get__`）的优先级高于实例 `__dict__`。

## 面试速答

> 🎯 描述符=实现 __get__/__set__/__delete__ 的类接管属性访问(数据描述符优先于实例 __dict__；property 即内置描述符)，校验/惰性求值可复用。上下文管理器 __enter__/__exit__ 配 with 成对释放，contextmanager 用生成器简化。
> 🔍 追问：property 和描述符什么关系？
> 🔍 追问：数据与非数据描述符的优先级差异会引发什么坑？

## 相关术语

[[Python高级编程完全指南]]、[[Python 元类编程]]、[[Python 高级装饰器]]、[[Python高级特性]]

## 参考资料

建议人工核验：以 Python descriptor-howto 与 contextlib 文档为准；未编造文献编号。
