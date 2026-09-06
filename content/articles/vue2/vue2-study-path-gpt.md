---
title: "vue2-study-path-gpt"
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/vue2-study-path-gpt.md"
---

Vue2 的源码目录其实比你想象中“规整”。

真正核心只有几个目录。

你读源码时，
不要一上来全看。

先知道：

> 每个目录是干什么的。

否则会迷路。

---

# Vue2 源码整体结构

Vue2 仓库：

[Vue 2 GitHub 仓库](https://github.com/vuejs/vue/tree/v2.7.16?utm_source=chatgpt.com)

核心目录：

```text
vue/
├── src/
├── dist/
├── scripts/
├── test/
├── types/
├── packages/
```

你真正重点关注：

```text
src/
```

别的先不用深究。

---

# src 目录结构（核心）

```text
src/
├── compiler/
├── core/
├── platforms/
├── server/
├── sfc/
├── shared/
```

---

# 一、core（最核心）

这是：

# Vue 的核心运行时

你之后 70% 时间都在这里。

---

目录：

```text
core/
├── observer/
├── instance/
├── vdom/
├── util/
├── components/
├── global-api/
```

---

## 1. observer/

这是：

# Vue2 响应式核心

最重要。

---

里面核心文件：

```text
observer/
├── index.js
├── dep.js
├── watcher.js
├── array.js
├── scheduler.js
```

---

你以后会发现：

Vue2 本质上就是：

```text
Observer + Watcher
```

---

### index.js

核心入口。

里面有：

```js
observe()
defineReactive()
```

这是响应式的真正实现。

---

### dep.js

发布订阅中心。

核心类：

```js
class Dep
```

负责：

```text
收集依赖
通知更新
```

---

### watcher.js

观察者。

比如：

```text
render watcher
computed watcher
user watcher
```

都在这里。

---

### array.js

Vue2 对数组的“魔改”。

因为：

```js
Object.defineProperty
```

监听不了数组变化。

所以 Vue2 重写了：

```js
push
pop
splice
```

等方法。

---

### scheduler.js

异步更新队列。

这里有：

```js
queueWatcher()
nextTick()
```

---

# 2. instance/

这是：

# new Vue() 初始化核心

你以后会看到：

```js
new Vue({
  data,
  computed,
  watch
})
```

背后全在这里。

---

核心文件：

```text
instance/
├── init.js
├── state.js
├── lifecycle.js
├── render.js
├── events.js
```

---

## init.js

Vue 初始化入口。

里面：

```js
Vue.prototype._init
```

最重要。

---

它负责：

```text
合并配置
初始化生命周期
初始化事件
初始化状态
挂载组件
```

---

## state.js

这里初始化：

```text
props
methods
data
computed
watch
```

非常重要。

---

## lifecycle.js

生命周期逻辑：

```text
mount
update
destroy
```

---

## render.js

渲染相关：

```js
_render()
```

---

## events.js

事件系统：

```js
$on
$emit
$off
```

---

# 3. vdom/

这是：

# Virtual DOM 实现

难度开始明显上升。

---

核心文件：

```text
vdom/
├── vnode.js
├── patch.js
├── create-element.js
```

---

## vnode.js

VNode 定义。

虚拟节点本体。

---

## patch.js

核心 diff 算法。

这里是 Vue 更新 DOM 的关键。

也是源码最复杂部分之一。

---

## create-element.js

```js
h()
createElement()
```

相关逻辑。

---

# 4. global-api/

这里是：

# Vue 全局 API

比如：

```js
Vue.component()
Vue.mixin()
Vue.use()
Vue.extend()
```

---

核心文件：

```text
global-api/
├── index.js
├── extend.js
├── assets.js
├── use.js
```

---

# 5. util/

工具函数。

大量：

```js
isObject
noop
warn
mergeOptions
```

---

这里很多函数会反复看到。

---

# 二、compiler（编译器）

这是：

# template 编译系统

---

它负责：

```text
template
↓
AST
↓
render function
```

---

核心目录：

```text
compiler/
├── parser/
├── codegen/
├── optimizer.js
```

---

# parser/

模板解析。

把：

```html
<div>{{msg}}</div>
```

变 AST。

---

# optimizer.js

静态节点优化。

Vue2 会标记：

```text
静态节点
```

减少更新成本。

---

# codegen/

代码生成。

AST 最后变成：

```js
render() {
  return _c(...)
}
```

---

# 三、platforms/

这是：

# 平台适配层

Vue 不止运行在浏览器。

还有：

* weex
* server-render

所以需要平台层。

---

最重要：

```text
platforms/web/
```

这里是浏览器相关实现。

---

例如：

```text
web/runtime/
web/compiler/
```

---

# 四、shared/

共享工具。

这里很多：

```js
常量
公共工具
```

编译器/runtime 都会用。

---

# 五、server/

SSR 服务端渲染。

你现在可以先忽略。

---

# 六、sfc/

Single File Component。

也就是：

```vue
xxx.vue
```

相关处理。

---

你以前 CDN 开发较多：

这一块你可能陌生。

不过先不用深入。

---

# 你现在最应该重点关注的目录

现阶段：

# 只看：

```text
core/
```

尤其：

```text
core/observer/
core/instance/
```

---

# Vue2 源码真正执行链路（极重要）

你现在先建立这个流程：

```text
new Vue()
↓
_init()
↓
initState()
↓
observe(data)
↓
defineReactive()
↓
mount()
↓
render()
↓
VNode
↓
patch()
↓
真实 DOM
```

后面所有源码，
都是围绕这条线展开。

---

# 推荐你的源码阅读顺序（非常重要）

别按文件夹顺序读。

按“执行链路”读：

---

## 第一阶段

```text
instance/init.js
instance/state.js
observer/index.js
observer/dep.js
observer/watcher.js
```

---

## 第二阶段

```text
lifecycle.js
render.js
vdom/vnode.js
```

---

## 第三阶段

```text
patch.js
scheduler.js
nextTick
```

---

## 第四阶段

```text
compiler/*
```

---

# 你接下来最适合进入的内容

建议下一步：

# “从 new Vue() 开始追源码”

这是最自然的入口。

我们会真正开始：

```js
new Vue({
  data() {
    return {
      msg: 'hello'
    }
  }
})
```

内部到底怎么一步步运行。
