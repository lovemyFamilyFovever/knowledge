---
tags: [Vue3, 组件通信]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue3/Component-Communication.md"
---

# Vue3 组件传值全套总结（Options API + Setup 组合式）
Vue3 常用**7种组件通信方式**，按日常开发频率排序，附带代码示例、适用场景。

## 1. 父传子：Props（最常用）
### 父组件
```vue
<Child :msg="parentMsg" :num="100" />

<script setup>
import { ref } from 'vue'
const parentMsg = ref('来自父组件')
</script>
```

### 子组件接收
```vue
<script setup>
// 方式1：基础接收
const props = defineProps(['msg', 'num'])

// 方式2：带类型、默认值、校验（推荐）
const props = defineProps({
  msg: String,
  num: {
    type: Number,
    required: true,
    default: 0
  }
})
</script>

<!-- 模板直接用 -->
{{ msg }} {{ num }}
```

---

## 2. 子传父：emit 自定义事件
### 子组件
```vue
<script setup>
const emit = defineEmits(['sendMsg'])

// 触发事件，传数据给父
const send = () => {
  emit('sendMsg', '子组件数据', 666)
}
</script>

<button @click="send">传给父</button>
```

### 父组件接收
```vue
<Child @sendMsg="getChildData" />

<script setup>
const getChildData = (val, num) => {
  console.log(val, num)
}
</script>
```

Vue 的自定义事件 emit 是通知机制，不是函数调用，天生不支持返回值。

- 一句话讲透原理
- emit('xxx') 本质是：
- “广播一个事件，谁监听谁执行”
- 它的返回值永远是 undefined
- 不管父组件的方法有没有 return，都传不回来

---

## 3. 父子双向绑定：v-model
Vue3 简化了双向绑定，**默认绑定 modelValue，触发 update:modelValue**
### 子组件
```vue
<script setup>
const props = defineProps(['modelValue'])
const emit = defineEmits(['update:modelValue'])

const change = () => {
  emit('update:modelValue', '新值')
}
</script>
```

### 父组件
```vue
<Child v-model="value" />

<script setup>
import { ref } from 'vue'
const value = ref('')
</script>
```

---

## 4. 父直接访问子组件：ref
父组件通过 `ref` 获取子组件**实例、属性、方法**
### 父
```vue
<Child ref="childRef" />

<script setup>
import { ref, onMounted } from 'vue'
const childRef = ref(null)

onMounted(() => {
  console.log(childRef.value) // 子组件实例
  childRef.value.子组件方法()
})
</script>
```

### 子组件（defineExpose 暴露属性）
```vue
<script setup>
import { ref } from 'vue'
const childMsg = ref('子数据')
const fun = () => console.log('子方法')

// 必须暴露，父组件才能拿到
defineExpose({ childMsg, fun })
</script>
```
> 注意：`<script setup>` 默认私有，**不 defineExpose 父组件拿不到**

---

## 5. 祖孙跨层传值：provide / inject
**隔多层组件传值，不用一层层 props 透传**
### 祖先组件提供
```vue
<script setup>
import { provide, ref } from 'vue'
const data = ref('祖孙共享数据')

// 响应式必须传 ref 本身
provide('key', data)
</script>
```

### 后代组件注入
```vue
<script setup>
import { inject } from 'vue'
const data = inject('key')
</script>
```

### 带默认值
```js
const data = inject('key', '默认值')
```

---

## 6. 任意组件通信：Pinia（Vue3官方状态库）
替代 Vue2 的 Vuex，**跨父子、跨兄弟、任意组件**通用
1. 创建 store
```js
// stores/user.js
import { defineStore } from 'pinia'
export const useUserStore = defineStore('user', {
  state: () => ({
    name: '张三'
  }),
  actions: {
    setName(val) {
      this.name = val
    }
  }
})
```

2. 任意组件使用
```vue
<script setup>
import { useUserStore } from '@/stores/user'
const userStore = useUserStore()

// 读取
console.log(userStore.name)
// 修改
userStore.setName('李四')
</script>
```

---

## 7. 兄弟组件通信
Vue3 **不推荐 eventBus**（官方已废弃）
兄弟传值最优方案：
1. **Pinia**（首选）
2. 父组件中转：A → 父 → B
3. provide/inject 间接传递

---

# 极简速记总结
1. **父→子**：`defineProps`
2. **子→父**：`defineEmits`
3. **双向绑定**：`v-model`
4. **父拿子**：`ref + defineExpose`
5. **祖孙跨层**：`provide / inject`
6. **任意组件全局**：**Pinia**
7. **兄弟组件**：Pinia / 父中转


