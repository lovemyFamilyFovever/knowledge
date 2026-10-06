---
outline: [1,3]
head:
  - - meta
    - name: description
      content: vue2 查漏补缺
  - - meta
    - name: keywords
      content: vue2 查漏补缺
tags: [Vue2]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/leak-filling.md"
---

# vue2 查漏补缺

## Vue的数据为什么频繁变化但只会更新一次？

原因：Vue的响应式系统是异步的，当数据发生变化时，Vue并不会立即更新视图，而是等待下一个事件循环（宏任务）再去更新视图。

解决方法：

1. 使用Vue.set()方法，强制更新视图。
2. 使用$nextTick()方法，在下一个事件循环中更新视图。

```javascript
// 1. 使用Vue.set()方法，强制更新视图
this.$set(this.data, 'name', 'newName')

// 2. 使用$nextTick()方法，在下一个事件循环中更新视图
this.$nextTick(() => {
  console.log(this.data.name)
})
```
## vue使用Object.defineProperty() 的缺陷

Object.defineProperty() 方法是用来在对象上定义新属性，或者修改已有属性，它可以用来监听对象属性的变化。但是，它也有一些缺陷：

1. 无法监听数组的变化。
2. 无法监听对象新增的属性。
3. 无法监听数组的索引变化。

解决方法：

1. 使用Vue.set()方法，强制更新视图。
2. 使用$watch()方法，监听数组的变化。
3. 使用$data()方法，监听对象新增的属性。

```javascript
// 1. 使用Vue.set()方法，强制更新视图
this.$set(this.data, 'name', 'newName')

// 2. 使用$watch()方法，监听数组的变化
this.$watch('data', (newVal, oldVal) => {
  console.log(newVal, oldVal)
}, {deep: true})

// 3. 使用$data()方法，监听对象新增的属性
this.$data().$watch('name', (newVal, oldVal) => {
  console.log(newVal, oldVal)
})
```

## v-model和.sync的区别

v-model的实现:

```html
<!--v-model写法-->
<my-component type="text" v-model="value">
<!--展开语法糖后的写法-->
<my-component type="text"
  :value="value"
  @input="value = $event.target.value"
>
```

.sync的实现:

```html
<!--语法糖.sync-->
<my-component :value.sync="value" />
<!--编译后的写法-->
<my-component 
  :value="msg" 
  @update:value="(val) => value = val"
>
```

相同点：都是语法糖，都可以实现父子组件中的数据的双向通信。

不同点：

1. 只不过v-model默认对应的是input或者textarea等组件的input事件，如果在子组件替换这个input事件，其本质和.sync修饰符一模一样。比较单一，不能有多个。

```javascript
// 子组件手动 $emit
model: {
    prop: "value",
    event: "update"
},

//.sync   子组件往回传值的时候$emit所调用的事件名必须是update:属性名
```

2. 一个组件可以多个属性用.sync修饰符，可以同时"双向绑定多个“prop”，而并不像v-model那样，一个组件只能有一个

## 子组件的created、mounted中获取不到props中的值data?

原因：props属性 是通过发送请求获取的, 请求的这个过程是需要时间的，但是子组件的渲染要快于请求过程，所以此时 created 、mounted这样的只会执行一次的生命周期钩子，已经执行了，但是props还没有流进来（子组件），所以只能拿到默认值。

解决办法：使用watch监视props里的值

## nextTick吗，它是干什么的，实现原理是什么？

```javascript
Vue.nextTick(function () {
// DOM 更新了
})
```

想要立即获取更新后的dom状态，就需要使用这个方法。

使用场景：
1. 在`created`中想要获取DOM时，
2. 响应式数据变化后获取DOM更新后的状态，比如希望获取列表更新后的高度或者宽度。

Vue 在更新 DOM 时是异步执行的。只要侦听到数据变化，Vue 将开启一个队列，并缓冲在同一事件循环中发生的所有数据变更。

原理：它会在`callbacks`里面加入我们传入的函数，然后用`timerFunc`异步方式调用它们，首选的异步方式会是`Promise`。

## watch和computed的区别以及选择?

1. computed是计算属性，watch是监听一个值的变化，然后执行对应的回调。
2. computed支持缓存，相依赖的数据发生改变才会重新计算；watch不支持缓存，只要监听的数据变化就会触发相应操作。
3. computed默认第一次加载的时候就开始监听；watch默认第一次加载不做监听，如果需要第一次加载做监听，添加immediate属性，设置为true（immediate:true）
4. computed不支持异步，当computed内有异步操作时是无法监听数据变化的；watch支持异步操作。

## 怎么缓存当前的组件？缓存后怎么更新？

缓存组件使用keep-alive组件，keep-alive包裹动态组件component时，会缓存不活动的组件实例，而不是销毁它们，这样在组件切换过程中将状态保留在内存中，防止重复渲染DOM。

缓存后如果要获取数据，解决方案可以有以下两种：

1. beforeRouteEnter：在有vue-router的项目，每次进入路由的时候，都会执行beforeRouteEnter
2. actived：在keep-alive缓存的组件被激活的时候，都会执行actived钩子

## 写过自定义指令吗？使用场景有哪些？

- 复制粘贴 v-copy
- 长按 v-longpress
- 防抖 v-debounce
- 图片懒加载 v-lazy
- 按钮权限 v-premission
- 页面水印 v-waterMarker
- 拖拽指令 v-draggable

[超实用：Vue 自定义指令合集 - 墨天轮 (modb.pro)](https://www.modb.pro/db/326850)

## 说下$attrs和$listeners的使用

这两者可以用来进行父子间组件通信，

$attrs可以获取父元素的所有绑定的属性（除了props里面）

$listeners可以获取父元素的事件