---
# outline: [1,3]
head:
  - - meta
    - name: description
      content: pinia 前端框架 前端开发 前端框架 前端工程师
  - - meta
    - name: keywords
      content: pinia 前端框架 前端开发 前端框架 前端工程师
tags: [Pinia]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/pinia/index.md"
---

# pinia 前端框架

Pinia **不是**一个类似 Next.js 或 Nuxt.js 的**全栈框架**，而是一个专门用于 **Vue.js 的状态管理库**。

简单类比：
- **Next.js / Nuxt.js** = 全栈框架（帮你搞定路由、渲染、构建等）
- **Pinia** = 全局数据仓库（帮你管理多个组件之间共享的数据）

## Pinia 是干什么用的？

在 Vue 应用中，如果多个组件需要共享同一份数据（比如用户登录信息、购物车内容、主题设置），直接把数据传来传去会很麻烦。Pinia 提供一个**集中式的 Store（仓库）**，任何组件都可以随时存取这份数据。

**典型使用场景：**
- 用户登录后，把 `userInfo` 存在 Pinia 里，任何页面都能拿到用户信息
- 电商网站的购物车，添加商品、删除商品、计算总价都通过 Pinia 管理
- 全局主题切换（暗色/亮色模式）、多语言设置等

## Pinia 的核心特点

| 特性 | 说明 |
| :--- | :--- |
| **轻量** | 压缩后只有 1KB 左右 |
| **TypeScript 友好** | 自动推断类型，写起来很舒服 |
| **Vue 3 优先** | 完全基于 Composition API，但同样支持 Vue 2 |
| **没有 mutations** | 相比老版的 Vuex，简化了概念，只有 `state`、`actions`、`getters` |
| **模块化** | 每个 Store 是独立的，可以按需引入，支持代码分割 |

## 它与 Next.js、Nuxt.js 的关系

- **Nuxt.js** 内置集成了 Pinia（有官方模块 `@pinia/nuxt`），可以直接使用。
- **Next.js** 是 React 框架，不使用 Pinia。React 生态对应的状态管理工具是 **Zustand**、**Redux**、**Jotai** 等。

## 一个简单代码示例（让你秒懂）

```javascript
// stores/user.js
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    name: '张三',
    isLoggedIn: false
  }),
  actions: {
    login(userName) {
      this.name = userName
      this.isLoggedIn = true
    },
    logout() {
      this.name = ''
      this.isLoggedIn = false
    }
  }
})
```

在 Vue 组件中使用：

```vue
<template>
  <div>
    <p>当前用户：{{ userStore.name }}</p>
    <button @click="userStore.login('李四')">登录</button>
  </div>
</template>

<script setup>
import { useUserStore } from '@/stores/user'
const userStore = useUserStore()
</script>
```

## 与传统 Vuex 的对比

| 维度 | Vuex (老方案) | Pinia (新方案) |
| :--- | :--- | :--- |
| 心智负担 | 需要写 `mutations`、`actions`、`getters` | 只有 `state`、`actions`、`getters` |
| TypeScript | 需要额外类型声明 | 天然支持，自动推断 |
| 体积 | 较大 | 很小 (~1KB) |
| 官方推荐 | Vue 2 官方推荐 | **Vue 3 官方推荐**（Vuex 已进入维护模式） |

## 什么时候用 Pinia？

- ✅ 构建中等或大型 Vue 应用，有多组件共享数据的需求
- ✅ 想做性能优化，避免 props 层层传递（prop drilling）
- ✅ 需要持久化插件（比如自动把 store 存到 localStorage）

- ❌ 极简单的小页面（几个组件不共享什么数据），用原生 Vue `provide/inject` 或 `ref` 全局变量就够了

## 总结一句话

**Pinia 是 Vue 生态里目前官方推荐的状态管理工具**，用来帮你管理多个组件之间共享的数据。它不是框架，是一个轻量级库。如果你用 Nuxt.js 开发项目，大概率会顺手装上 Pinia。