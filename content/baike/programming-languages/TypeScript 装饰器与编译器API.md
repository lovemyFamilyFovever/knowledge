---
title: "TypeScript 装饰器与编译器API"
tags: []
source: "baike"
source_path: "技术文章 / 编程语言"
collected: "2026-09-05"
status: "imported"
---

# TypeScript 装饰器与编译器API

> 📌 **导航**：本文是 **TypeScript 装饰器与编译器 API** 词条，属 [[TypeScript高级编程指南]] 子词条。

## 定义

**一句话定义：** TS 装饰器是在类/方法/属性/参数上"附加元信息与横切行为"的语法（Angular、NestJS 重度使用），编译器 API 则让你在类型检查之外读写程序 AST 与类型信息、做代码分析/生成/变换。

**通俗类比：** 装饰器像"给类部件贴便利贴、注入能力"；编译器 API 像"打开 TypeScript 这台机器的前盖"——你能拿到它的 AST 和类型检查器，自己写工具。

## 为什么需要它

框架常在声明处织入路由、依赖注入、可观察性等能力，装饰器让这在一行内完成。而 IDE 补全、lint 规则、自动迁移、代码生成等工具，需要程序化地"理解"代码结构与类型——靠编译器 API 而非正则会话。

## 核心机制

- **装饰器**：类/方法/访问器/属性/参数装饰器；分**实验性 legacy**（当前多数框架用，配合 `emitDecoratorMetadata` 反射元数据）与 **TC39 标准装饰器**（Stage 3，行为不同）；本质是在定义时接收目标+上下文、包装/登记。
- **编译器 API**：`ts.createSourceFile` 解析出 AST、`ts.forEachChild` 遍历；`ts.createProgram` + `TypeChecker` 拿到符号、类型、可赋值性等语义信息；据此做诊断、改写、代码生成。
- 上层常封装为 **ts-morph / tsutils**；框架集成（React/Vue）多为类型侧：JSX 类型、props/emit 泛型推导，与运行期无关。

## 具体示例

方法装饰器登记路由（NestJS 式）与用编译器 API 遍历：

```typescript
function Get(path: string) {           // 方法装饰器（实验性）
  return (t: any, key: string) => { routes.push({ key, path }); };
}
// 编译器侧：
const sf = ts.createSourceFile('a.ts', src, ts.ScriptTarget.ES2020, true);
ts.forEachChild(sf, node => /* 处理 AST 节点 */);
```

## 何时用与何时不用

- **用**：框架声明式元编程（DI/路由/校验）用装饰器；写 lint、重构、代码生成、文档工具用编译器 API（优先 ts-morph）。
- **不用**：普通业务别乱加装饰器（legacy/标准两套易混）；能用 TS 自带 `--noEmit`/诊断就别自己造编译器轮子。

## 优劣与代价

✅ 装饰器让横切能力声明式、贴近使用点。
✅ 编译器 API 带来类型感知的工具与代码生成。
⚠️ 实验性装饰器与标准语义不一致、依赖反射配置，迁移有坑。
⚠️ 直接用 tsc 内部 API 门槛高、版本易变。

## 与相关概念的区别

- **TS 装饰器 vs GoF 装饰器模式**（[[装饰器模式]]）：前者是"定义期登记/包装类部件"的语法，后者是"运行期同接口层层包裹对象"。
- **Python 装饰器 vs TS 装饰器**（[[Python 高级装饰器]]）：同名不同物——Python 包函数、TS 标注类成员。
- **编译器 API vs 运行期反射**：前者在编译/工具侧读 AST+类型，后者在运行时读元数据。

## 常见误区

- TS 的实验性装饰器和 TC39 标准装饰器完全兼容、可随意互换。
- 编译器 API 会在运行时改变代码的执行结果。
- 装饰器只能用于类，不能标注方法或属性。

## 面试速答

> 🎯 TS 装饰器=定义期给类/方法/属性贴元数据、织横切(Angular/Nest；分实验性 legacy 与 TC39 标准两套)。编译器 API(createProgram/TypeChecker，常经 ts-morph)在编译期读 AST+类型做 lint/生成/重构，不改运行结果。
> 🔍 追问：实验性装饰器和标准装饰器差在哪？
> 🔍 追问：编译器 API 在什么阶段工作、能拿到什么？

## 相关术语

[[TypeScript高级编程指南]]、[[装饰器模式]]、[[Python 高级装饰器]]、[[MVC 与 MVVM]]

## 参考资料

建议人工核验：以 TypeScript Handbook（Decorators）、TypeScript Compiler API docs 与 ts-morph 文档为准；未编造文献编号。
