---
tags: [TypeScript, Bug]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/TypeScript/bugs.md"
---

# 无法运行 TypeScript 项目

## 问题描述

在运行 TypeScript 项目时，出现如下错误：

> `error TS2583: Cannot find name 'Map'. Do you need to change your target library? Try changing the 'lib' compiler option to 'es2015' or later.`
> `5 type BluetoothManufacturerData = Map<number, DataView>;`


## 解决方案

1. `tsc -init` 生成 `tsconfig.json`，修改其中的 `target` 、`lib`，**结果无效。**
2. 直接运行
   1. `tsc --target es6 --module commonjs fileName.ts`
   或者
   2. `tsc --lib es2015 fileName.ts`