---
outline: [1,3]
head:
  - - meta
    - name: description
      content: vue3 setup语法糖
  - - meta
    - name: keywords
      content: Vue.js Vue3 Vue3搭建步骤 Vue3教程 Vue3入门 前端开发 前端框架 前端工程师 setup
tags: [Vue3]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue3/setup.md"
---

# Vue3 setup语法糖

## 原生Vue3的写法

```javascript
import { ref, onMounted } from 'vue'

export default {
  setup() {
    const count = ref(0)
    const increment = () => {
      count.value++
    }

    onMounted(() => {
      console.log('mounted')
    })

    return {
      count,
      increment
    }
  }
}
```

## setup语法糖的写法

```javascript
import { ref, onMounted } from 'vue'
const count = ref(0)
const increment = () => {
    count.value++
}

onMounted(() => {
    console.log('mounted')
})
```

## 编译区别

传统的 setup 函数和 script setup 语法糖在编译后的结果基本一致,但后者会自动调用 `expose` 函数,只暴露开发者指定的组件成员,以保护组件的单向数据流。

- 原生Vue3的写法，script内的代码基本不变。

- setup的写法，会自动添加一个 `expose()` 函数,它将接收的参数暴露到外部。当它为空时，不暴露任何属性。（默认不暴露任何属性）

```javascript

setup(__props,{ expose }){
  expose();

  const __returned__ ={....}
}
```

> 当使用` expose `时，只有显式列出的属性将在组件实例上暴露。

## 手动暴露属性

原生Vue3的写法可以使用 `expose()` ,接收参数为**包含要暴露的属性名称字符串的数组**

```javascript
import { ref, expose } from 'vue'

export default {
  expose: ['count', 'increment']
  setup() {
    const count = ref(0)
    const increment = () => {
      count.value++
    }
  },
}
```

**setup语法糖可以使用 `defineExpose()` 方法：**（它不参与运行，只参与编译，类似的还有 `defineProps` ， `defineEmit` s等,所以它们不用引用，可以直接调用。）

```javascript
import { ref, defineExpose } from 'vue'

const count = ref(0)
const increment = () => {
  count.value++
}

defineExpose({
  count,
  increment
})
```
`defineExpose()` 在编译后会变成 `expose()` ，它会暴露 `count` 和 `increment` 两个属性。
