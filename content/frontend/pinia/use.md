---
tags: [Pinia]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/pinia/use.md"
---

# Pinia 核心用法详解：getters、actions 与最佳实践

> 深入理解 Pinia 中 getters 的作用、使用场景，以及与 actions 的本质区别

## 目录

- [Getters 是什么](#getters-是什么)
- [核心使用场景](#核心使用场景)
- [Getters vs Actions：本质区别](#getters-vs-actions本质区别)
- [代码示例](#代码示例)
- [进阶用法](#进阶用法)
- [面试高频问答](#面试高频问答)
- [最佳实践总结](#最佳实践总结)

---

## Getters 是什么

**Getters 是 Pinia Store 中的计算属性**，类似于 Vue 组件中的 `computed`。

### 核心特性

| 特性 | 说明 |
| :--- | :--- |
| **派生数据** | 根据现有 state 计算出新数据 |
| **响应式** | 依赖的 state 变化时自动重新计算 |
| **缓存机制** | 计算结果会被缓存，只有依赖变化时才重新计算 |
| **类型推断** | TypeScript 自动推断返回类型 |

### 一句话理解

> Getters 就像 Store 里的 **Excel 公式单元格**——输入数据变化，输出结果自动更新，且不会重复计算。

---

## 核心使用场景

### 场景一：派生状态

当你需要从原始状态中**计算出新数据**，而不是直接使用原始数据时。

```javascript
// 示例：从用户列表中筛选出活跃用户
export const useUserStore = defineStore('user', {
  state: () => ({
    users: [
      { name: '张三', active: true },
      { name: '李四', active: false },
      { name: '王五', active: true }
    ]
  }),
  getters: {
    // 派生：只取活跃用户
    activeUsers: (state) => {
      return state.users.filter(user => user.active)
    },
    // 派生：统计活跃用户数量
    activeUsersCount: (state) => {
      return state.users.filter(user => user.active).length
    }
  }
})
```

### 场景二：缓存计算结果

当某个派生状态被**频繁使用**时，getters 可以缓存结果，避免重复计算。

```javascript
export const useReportStore = defineStore('report', {
  state: () => ({
    salesData: [] // 大量销售数据，比如 10 万条
  }),
  getters: {
    // 复杂聚合计算 - 有缓存，不会重复执行
    totalRevenue: (state) => {
      console.log('重新计算总营收...') // 只有 salesData 变化时才打印
      return state.salesData.reduce((sum, item) => sum + item.amount, 0)
    },
    // 分组统计 - 同样有缓存
    categorySummary: (state) => {
      return state.salesData.reduce((acc, item) => {
        acc[item.category] = (acc[item.category] || 0) + item.amount
        return acc
      }, {})
    }
  }
})
```

**效果对比：**

| 方式 | 每次访问 | 依赖变化时 |
| :--- | :--- | :--- |
| 普通函数 | 重新计算 ❌ | 重新计算 |
| Getters | 读取缓存 ✅ | 重新计算 |

### 场景三：组件间共享派生逻辑

多个组件需要**相同的派生数据**时，避免在每个组件中重复编写逻辑。

```javascript
// ❌ 错误做法：在 3 个组件里各写一遍
computed: {
  formattedDate() {
    return new Date(this.orderDate).toLocaleDateString('zh-CN')
  }
}

// ✅ 正确做法：在 getters 中定义一次
// store/order.js
export const useOrderStore = defineStore('order', {
  state: () => ({
    orderDate: '2024-01-15T10:30:00Z'
  }),
  getters: {
    formattedDate: (state) => {
      return new Date(state.orderDate).toLocaleDateString('zh-CN')
    }
  }
})

// 任何组件中使用
const orderStore = useOrderStore()
const date = orderStore.formattedDate  // "2024/1/15"
```

---

## Getters vs Actions：本质区别

| 维度 | Getters | Actions |
| :--- | :--- | :--- |
| **用途** | 同步计算派生数据 | 异步操作、复杂业务逻辑 |
| **是否修改 state** | ❌ 不能修改（只读） | ✅ 可以修改 |
| **缓存** | ✅ 有缓存（类似 computed） | ❌ 无缓存（每次调用都执行） |
| **参数** | 可选（支持传参） | 可选 |
| **执行时机** | 访问时自动计算 | 主动调用 |
| **类比** | 组件中的 `computed` | 组件中的 `methods` |

### 关键区别图解

```
State (原始数据)
    ↓
┌─────────────────────────────────────┐
│                                     │
│  Getters (派生计算)                  │
│  • 只读，不修改原数据                 │
│  • 有缓存，性能好                    │
│  • 类似 Excel 公式                   │
│                                     │
│  Actions (业务操作)                  │
│  • 可修改 state                      │
│  • 可做异步请求                      │
│  • 可包含多个步骤                    │
│                                     │
└─────────────────────────────────────┘
```

### 什么时候用哪个？

```javascript
// ✅ 用 Getters：需要计算/格式化，不改变原数据
getters: {
  fullName: (state) => `${state.firstName} ${state.lastName}`,
  isAdult: (state) => state.age >= 18,
  cartTotal: (state) => state.items.reduce((sum, i) => sum + i.price, 0)
}

// ✅ 用 Actions：需要改数据、调接口、复杂流程
actions: {
  async login(username, password) {
    const res = await api.login(username, password)  // 异步
    this.user = res.data  // 修改 state
    this.token = res.token
    localStorage.setItem('token', res.token)  // 副作用
  },
  addToCart(product) {
    // 多个步骤：检查库存、更新购物车、记录日志
    if (product.stock > 0) {
      this.items.push(product)
      this.logAction('add_to_cart', product.id)
    }
  }
}
```

---

## 代码示例

### 完整示例：购物车 Store

```javascript
// stores/cart.js
export const useCartStore = defineStore('cart', {
  state: () => ({
    items: [],           // [{ id, name, price, quantity }]
    shippingAddress: '',
    couponCode: ''
  }),

  getters: {
    // 计算商品总数
    totalItems: (state) => {
      return state.items.reduce((sum, item) => sum + item.quantity, 0)
    },

    // 计算总价（不含运费）
    subtotal: (state) => {
      return state.items.reduce((sum, item) => {
        return sum + item.price * item.quantity
      }, 0)
    },

    // 计算运费（满 100 免运费）
    shippingFee: (state) => {
      const subtotal = this.subtotal  // 可以访问其他 getter
      return subtotal >= 100 ? 0 : 10
    },

    // 计算折扣
    discount: (state) => {
      if (state.couponCode === 'SAVE20') return 0.2
      if (state.couponCode === 'SAVE10') return 0.1
      return 0
    },

    // 最终价格（组合多个 getter）
    totalPrice: (state) => {
      const subtotal = this.subtotal
      const discountAmount = subtotal * this.discount
      return subtotal - discountAmount + this.shippingFee
    },

    // 带参数的 getter（返回函数）
    findItemById: (state) => (id) => {
      return state.items.find(item => item.id === id)
    },

    // 检查商品是否在购物车中
    isItemInCart: (state) => (id) => {
      return state.items.some(item => item.id === id)
    }
  },

  actions: {
    addItem(product, quantity = 1) {
      const existing = this.items.find(item => item.id === product.id)
      if (existing) {
        existing.quantity += quantity
      } else {
        this.items.push({
          id: product.id,
          name: product.name,
          price: product.price,
          quantity
        })
      }
    },

    removeItem(id) {
      const index = this.items.findIndex(item => item.id === id)
      if (index !== -1) {
        this.items.splice(index, 1)
      }
    },

    updateQuantity(id, quantity) {
      const item = this.items.find(item => item.id === id)
      if (item && quantity > 0) {
        item.quantity = quantity
      }
    },

    applyCoupon(code) {
      this.couponCode = code
    },

    async checkout() {
      const orderData = {
        items: this.items,
        total: this.totalPrice,
        shippingAddress: this.shippingAddress
      }
      const response = await api.createOrder(orderData)
      
      // 下单成功后清空购物车
      this.items = []
      this.couponCode = ''
      
      return response
    }
  }
})
```

### 组件中使用

```vue
<template>
  <div class="cart">
    <h3>购物车 ({{ cartStore.totalItems }} 件商品)</h3>
    
    <div v-for="item in cartStore.items" :key="item.id">
      <span>{{ item.name }}</span>
      <span>¥{{ item.price }} x {{ item.quantity }}</span>
      <button @click="cartStore.updateQuantity(item.id, item.quantity - 1)">-</button>
      <button @click="cartStore.updateQuantity(item.id, item.quantity + 1)">+</button>
    </div>
    
    <div class="summary">
      <div>小计：¥{{ cartStore.subtotal }}</div>
      <div v-if="cartStore.discount > 0">
        折扣：-¥{{ (cartStore.subtotal * cartStore.discount).toFixed(2) }}
      </div>
      <div>运费：¥{{ cartStore.shippingFee }}</div>
      <div class="total">总计：¥{{ cartStore.totalPrice }}</div>
    </div>
    
    <input v-model="couponCode" placeholder="优惠码" />
    <button @click="cartStore.applyCoupon(couponCode)">使用优惠码</button>
    
    <button @click="checkout">去结算</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useCartStore } from '@/stores/cart'

const cartStore = useCartStore()
const couponCode = ref('')

// 检查特定商品是否在购物车（使用带参数的 getter）
const isLaptopInCart = cartStore.isItemInCart('laptop-001')

async function checkout() {
  const result = await cartStore.checkout()
  alert('下单成功！')
}
</script>
```

---

## 进阶用法

### 1. 带参数的 Getters

Getters 可以返回一个函数，接受参数进行动态查询。

```javascript
getters: {
  // 根据 ID 查找用户
  getUserById: (state) => (id) => {
    return state.users.find(user => user.id === id)
  },
  
  // 根据分数范围筛选
  getUsersByScore: (state) => (min, max) => {
    return state.users.filter(user => user.score >= min && user.score <= max)
  }
}

// 使用
const user = userStore.getUserById(123)
const topStudents = userStore.getUsersByScore(90, 100)
```

> ⚠️ **注意**：带参数的 getter **不会缓存结果**，每次调用都会重新执行。如果追求性能，可以考虑在组件中用 `computed` 包装。

### 2. 访问其他 Getters

Getters 内部可以通过 `this` 访问其他 getters。

```javascript
getters: {
  subtotal: (state) => {
    return state.items.reduce((sum, i) => sum + i.price, 0)
  },
  
  // ✅ 可以访问其他 getter
  tax: (state) => {
    return this.subtotal * 0.1
  },
  
  total: (state) => {
    return this.subtotal + this.tax
  }
}
```

> ⚠️ **注意**：使用 `this` 时，getter 的函数签名不能只写 `(state)`，需要写成普通函数（不能用箭头函数）。

```javascript
// ❌ 错误：箭头函数中 this 不指向 store
getters: {
  total: (state) => {
    return state.subtotal + this.tax  // this 是 undefined
  }
}

// ✅ 正确：使用普通函数
getters: {
  total(state) {
    return state.subtotal + this.tax
  }
}
```

### 3. 组合式 API 写法（推荐）

Pinia 也支持更现代的组合式 API 风格。

```javascript
// stores/counter.js - 组合式写法
export const useCounterStore = defineStore('counter', () => {
  // state
  const count = ref(0)
  const name = ref('')
  
  // getters（相当于 computed）
  const doubleCount = computed(() => count.value * 2)
  const greeting = computed(() => `Hello, ${name.value}!`)
  
  // actions
  function increment() {
    count.value++
  }
  
  async function fetchUser() {
    const data = await api.getUser()
    name.value = data.name
  }
  
  return { count, name, doubleCount, greeting, increment, fetchUser }
})
```

---

## 面试高频问答

### Q1：已经有 actions，为什么还需要 getters？

> **回答要点：**
> 
> 1. **用途不同**：getters 用于**派生计算**，不修改数据；actions 用于**业务操作**，可以修改数据和执行异步任务。
> 2. **性能优势**：getters 有**缓存机制**，依赖不变时直接返回缓存结果；actions 每次调用都重新执行。
> 3. **代码复用**：getters 让多个组件共享同一份派生逻辑，避免重复代码。
> 
> **一句话**：getters 是“计算属性”，actions 是“方法”，各司其职。

### Q2：getters 和 Vue 组件中的 computed 有什么区别？

> **回答要点：**
> 
> | 维度 | 组件 computed | Pinia getters |
> | :--- | :--- | :--- |
> | 作用范围 | 单个组件内部 | 全局 Store，跨组件共享 |
> | 依赖来源 | 组件 data/props | Store 的 state 和其他 getters |
> | 缓存 | 有 | 有 |
> 
> 本质逻辑相同，只是**作用域不同**：computed 服务于单个组件，getters 服务于整个应用。

### Q3：getters 可以传参数吗？有什么注意点？

> **回答要点：**
> 
> 可以，getters 可以返回一个接受参数的函数。
> 
> ```javascript
> getUserById: (state) => (id) => {
>   return state.users.find(u => u.id === id)
> }
> ```
> 
> **注意**：带参数的 getter **不会缓存结果**，每次调用都会重新计算。如果需要在列表循环中使用，要留意性能影响。

### Q4：组合式 API 写法中如何定义 getters？

> **回答要点：**
> 
> 在组合式 API 写法中，直接用 Vue 的 `computed` 即可：
> 
> ```javascript
> export const useStore = defineStore('main', () => {
>   const count = ref(0)
>   const double = computed(() => count.value * 2)  // 这就是 getter
>   return { count, double }
> })
> ```

---

## 最佳实践总结

### ✅ 推荐做法

| 场景 | 推荐方案 |
| :--- | :--- |
| 格式化数据（日期、货币、单位转换） | Getters |
| 过滤/排序列表 | Getters |
| 聚合计算（总和、平均值、计数） | Getters |
| 组合多个状态的计算 | Getters |
| API 请求 | Actions |
| 修改 state | Actions |
| 包含副作用的逻辑（localStorage、埋点） | Actions |
| 复杂的多步骤业务 | Actions |

### ❌ 常见误区

```javascript
// ❌ 误区1：在 getters 中修改 state
getters: {
  doSomething(state) {
    state.count++  // 错误！getters 应该是只读的
  }
}

// ❌ 误区2：在 getters 中做异步操作
getters: {
  async fetchData() {  // 错误！getters 不支持异步
    const data = await api.get()
    return data
  }
}

// ❌ 误区3：在所有地方都用 getters
// 简单的一对一映射没必要用 getter
getters: {
  // 完全没必要的 getter
  userName: (state) => state.user.name
}
// 组件里直接用 store.user.name 就行
```

### 📝 命名规范建议

```javascript
// 布尔值 getter：用 is/has/can 前缀
getters: {
  isLoggedIn: (state) => !!state.token,
  hasItems: (state) => state.items.length > 0,
  canCheckout: (state) => state.items.length > 0 && state.address
}

// 数值 getter：用名词或计算描述
getters: {
  totalPrice: (state) => { ... },
  itemCount: (state) => { ... },
  averageScore: (state) => { ... }
}

// 带参数的 getter：用 get/find 前缀
getters: {
  getUserById: (state) => (id) => { ... },
  findProduct: (state) => (sku) => { ... }
}
```

---

## 一句话记忆

- **Getters** = Store 里的计算属性 → **有缓存、只读、派生数据**
- **Actions** = Store 里的方法 → **可异步、可修改、执行操作**
- **选型口诀**：派生用 Getters，操作用 Actions，异步必走 Actions

---

> 📌 **本文总结**：Pinia 的 getters 和 actions 各司其职。getters 专注于从现有状态中高效派生出新数据，适合格式化、过滤、聚合等场景；actions 负责处理异步请求和状态修改。正确区分两者，能让代码更清晰、性能更好。
```

**主要补充和优化内容：**

1. **扩充了场景说明**：每个使用场景都有详细代码示例
2. **增加了对比表格**：getters vs actions 的可视化对比
3. **完整购物车示例**：展示两者配合使用的真实场景
4. **进阶用法**：带参数 getter、访问其他 getter、组合式 API
5. **面试问答**：3个高频追问及回答模板
6. **最佳实践**：✅推荐做法、❌常见误区、命名规范
7. **一句话记忆**：便于快速回顾核心要点