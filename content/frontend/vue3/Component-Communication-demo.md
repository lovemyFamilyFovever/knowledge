---
tags: [Vue3, 组件通信]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue3/Component-Communication-demo.md"
---

**一套可直接复制运行**的 Vue3 + `<script setup>` 完整传值 Demo，包含：
父 ↔ 子、v-model 双向绑定、祖孙传值、父调用子方法、兄弟组件传值（父中转）。

你只需要新建一个 Vue 项目，把下面代码复制到对应文件即可运行。

---

# 1. 主文件：App.vue（父组件）
```vue
<template>
  <div class="app">
    <h1>Vue3 组件传值大全</h1>

    <!-- 1. 父传子 Props -->
    <Child
      :msg="parentMsg"
      :count="count"
      @update-count="updateCount"
      @child-event="getChildMsg"
    />

    <!-- 2. v-model 双向绑定 -->
    <div style="margin: 20px 0">
      <h3>双向绑定 v-model</h3>
      <p>父组件：{{ modelVal }}</p>
      <ChildVModel v-model="modelVal" />
    </div>

    <!-- 3. ref 获取子组件实例 -->
    <div style="margin: 20px 0">
      <h3>父调用子方法 ref + defineExpose</h3>
      <ChildRef ref="childRef" />
      <button @click="callChildFn">父组件调用子方法</button>
    </div>

    <!-- 4. 祖孙传值 provide / inject -->
    <div style="margin: 20px 0">
      <h3>祖孙传值 provide / inject</h3>
      <ParentBox />
    </div>

    <!-- 5. 兄弟组件传值（父组件中转） -->
    <div style="margin: 20px 0">
      <h3>兄弟组件传值（父中转）</h3>
      <BrotherA @send-to-bro="toBrotherB" />
      <BrotherB :msg-from-a="brotherMsg" />
    </div>
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import Child from './components/Child.vue'
import ChildVModel from './components/ChildVModel.vue'
import ChildRef from './components/ChildRef.vue'
import ParentBox from './components/ParentBox.vue'
import BrotherA from './components/BrotherA.vue'
import BrotherB from './components/BrotherB.vue'

// 父传子
const parentMsg = ref('我是来自父组件的消息')
const count = ref(0)

// 子传父
const getChildMsg = (msg) => {
  alert('子组件传来：' + msg)
}

const updateCount = (val) => {
  count.value = val
}

// v-model
const modelVal = ref('双向绑定初始值')

// ref 调用子组件
const childRef = ref(null)
const callChildFn = () => {
  childRef.value.childFn()
  alert('子组件数据：' + childRef.value.childData)
}

// 祖孙传值
const grandData = ref('祖先组件的数据')
provide('grandKey', grandData)

// 兄弟传值
const brotherMsg = ref('')
const toBrotherB = (msg) => {
  brotherMsg.value = msg
}
</script>

<style scoped>
.app {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}
</style>
```

---

# 2. 子组件：`components/Child.vue`（Props + emit）
```vue
<template>
  <div class="child">
    <h3>子组件</h3>
    <p>父组件 msg：{{ msg }}</p>
    <p>count：{{ count }}</p>
    <button @click="sendToParent">子传父</button>
    <button @click="addCount">修改 count 并传回父组件</button>
  </div>
</template>

<script setup>
const props = defineProps({
  msg: String,
  count: Number
})

const emit = defineEmits(['child-event', 'update-count'])

const sendToParent = () => {
  emit('child-event', 'Hello 父组件')
}

const addCount = () => {
  emit('update-count', props.count + 1)
}
</script>
```

---

# 3. 双向绑定组件：`components/ChildVModel.vue`
```vue
<template>
  <div>
    <p>子组件：{{ modelValue }}</p>
    <input
      :value="modelValue"
      @input="emit('update:modelValue', $event.target.value)"
      placeholder="输入修改"
    />
  </div>
</template>

<script setup>
defineProps(['modelValue'])
defineEmits(['update:modelValue'])
</script>
```

---

# 4. 可被父调用的子组件：`components/ChildRef.vue`
```vue
<template>
  <div>
    <p>子组件内部数据：{{ childData }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const childData = ref('我是子组件内部数据')

const childFn = () => {
  alert('我是子组件方法，被父组件调用了')
}

// 必须暴露，父才能访问
defineExpose({
  childData,
  childFn
})
</script>
```

---

# 5. 中间父组件（祖孙用）：`components/ParentBox.vue`
```vue
<template>
  <div>
    <h4>中间父组件</h4>
    <Grandson />
  </div>
</template>

<script setup>
import Grandson from './Grandson.vue'
</script>
```

# 6. 孙子组件：`components/Grandson.vue`
```vue
<template>
  <div>
    <h4>孙子组件</h4>
    <p>来自祖先：{{ grandData }}</p>
  </div>
</template>

<script setup>
import { inject } from 'vue'
const grandData = inject('grandKey', '默认值')
</script>
```

---

# 7. 兄弟 A 组件：`components/BrotherA.vue`
```vue
<template>
  <div>
    <h4>兄弟 A</h4>
    <button @click="send">发送消息给兄弟 B</button>
  </div>
</template>

<script setup>
const emit = defineEmits(['send-to-bro'])
const send = () => {
  emit('send-to-bro', '来自 A 的消息')
}
</script>
```

# 8. 兄弟 B 组件：`components/BrotherB.vue`
```vue
<template>
  <div>
    <h4>兄弟 B</h4>
    <p>A 传来：{{ msgFromA }}</p>
  </div>
</template>

<script setup>
defineProps({
  msgFromA: String
})
</script>
```

---

# 运行效果
页面会依次展示：
- 父 ↔ 子 props / emit
- v-model 双向同步
- 父通过 ref 调用子方法
- 祖孙跨级传值
- 兄弟组件传值

