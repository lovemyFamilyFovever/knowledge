---
outline: [1,3]
head:
  - - meta
    - name: description
      content:  Vue2 组件通讯传值组件通讯
  - - meta
    - name: keywords
      content: Vue2 组件通讯传值组件通讯
tags: [Vue2, 组件通信]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/ComponentCommunication.md"
---

# Vue2 组件通讯传值

---

# props/$emit

## props

props 是父组件向子组件传递数据的方式，子组件接收 props 后，可以直接使用。

**父组件**定义要传的参数， 注意：props可以传任何东西，对象、函数等
``` html
<template>
  <div id="app">
    <Child ref="child" :paramter="paramter" :paramter2="showMsg()"/>
  </div>
</template>

<script>
import Child from "./components/Child";

export default {
  name: "App",
  components: {
    Child,
  },
  data() {
    return {
      paramter: "test",
      msg:"it is msg"
    };
  },
  methods: {      
      showMsg(){
          return this.msg
      }      
  },
};
</script>
```
**子组件**
``` html
<template>
  <div class="hello"></div>
</template>

<script>
export default {
  name: "Child",
  props: ["paramter", "paramter2"],
  data() {
    return {};
  },
  mounted() {
    console.log(this.paramter); //"test"

    console.log(this.paramter2); //"it is msg"
  },
};
</script>
```

## $emit 子传父

$emit 是子组件向父组件传递数据的方式，父组件接收 $emit 后，可以直接使用。

``` html
<template>
  <div id="app">
    <!--1.必须用@或者v-on来注册事件， -->
    <HelloWorld @method1="parentMethod"></HelloWorld>
    <HelloWorld @method2="parentMethod(参数1, 参数2)"></HelloWorld>
  </div>
</template>
<script>
import HelloWorld from "./components/HelloWorld.vue";

export default {
  name: "App",
  components: {
    HelloWorld,
  },
  data() {
    return {};
  },
  methods: {
    //参数1为$emit传过来的参数，参数2为当前组件里面的参数
    parentMethod(参数1, 参数2) {
      console.log(参数1, 参数2);
    },
    // 可以用arguments来接受多个参数
    // parentMethod() {
    //   console.log(arguments);
    // }
  },
  mounted() {},
};
</script>
```

```html
<template>
  <div class="hello"></div>
</template>

<script>
export default {
  name: "HelloWorld",
  data() {
    return {
      list: [
        1,
        2,
        {
          a: 0,
        },
      ],
      msg: "Hello",
    };
  },
  mounted() {
    this.$emit("method1", this.list);
    this.$emit("method2", this.list);
  },
};
</script>
```

# $children/$parent

$children/$parent 是父子组件通讯的方式，父组件可以直接访问子组件，也可以通过 $children/$parent 访问子组件。

## $children

> vm.$children，需要注意 $children 并不保证顺序，也不是响应式的。如果加入新的子组件，$children[0] 的索引值也要修改，不够灵活。

```javascript
// 子元素获取父元素的值

// 在父元素中调用子元素的方法
this.$children[0].showMsg(this.msg)

// 子元素
methods:{
   showMsg(val) {
        console.log(val);
    } 
}
```

```javascript
// 父元素获取子元素的值

// 在父元素中调用子元素的方法
var msg = this.$children[0].showMsg()

// 子元素
methods:{
    showMsg() {
        return this.msg
    }
}
```

```javascript
//或者直接在父元素中获取子元素的data
var msg = this.$children[0].msg
```

## $parent

> 跟$children 类似的使用方式，但是不用添加索引。


```javascript
// 父元素获取子元素的值

// 父元素
methods:{
    showMsg(val) {
        console.log(val)
    }
}
// 在子元素中调用父元素的方法，传递参数
this.$parent.showMsg(this.msg)
```

```javascript
// 子元素获取父元素的值

// 父元素
methods:{
    showMsg() {
        return this.msg
    }
}

// 在子元素中调用父元素的方法，接受参数
var msg = this.$parent.showMsg()
```

```javascript
//或者直接在子元素中获取父元素的data
this.$parent.msg
```

# $refs

1. 一个对象，持有注册过 ref attribute 的所有 DOM 元素和组件实例。
2. 如果在普通的 DOM 元素上使用，引用指向的就是DOM元素；
3. 如果用在子组件上，引用就指向组件实例，可以通过实例直接调用组件的方法或访问数据

注：`this.$refs.reference === this.$children[0]`

所以可以直接使用$children的方法

```javascript
this.$refs.reference.data
this.$refs.reference.showMsg()
```

# provide/reject

这对选项需要一起使用，以允许一个祖先组件向其所有子孙后代注入一个依赖

> 提示：provide 和 inject 绑定并不是可响应的。这是刻意为之的。
> 然而，如果你传入了一个可监听的对象，那么其对象的 property 还是可响应的。

1. 传this
2. 传Vue.observe({})
3. 传一个data里面的对象
   
由上可知

**祖先组件**
```javascript
export default {
  name: 'App',
  components: {
    HelloWorld,
  },
  data() {
    return {
      obj: {
        name: 'JavaScript',
      },
      developer: '布兰登·艾奇',
      year: 1995,
      update: '2021年06月',
    }
  },
  provide() {
    return {
      obj: this.obj, // 方式1.传入一个可监听的对象
      developerFn: () => this.developer, // 方式2.通过 computed 来计算注入的值
      year: this.year, // 方式3.直接传值
      app: this, // 4. 提供祖先组件的实例 缺点：实例上挂载很多没有必要的东西 比如：props，methods。
      showMsg(param) {
        console.log(param);
      }
    }
  },
}
```

**子孙组件**
```javascript
export default {
  name: 'HelloWorld',
  data() {
    return {
      msg: "HelloWorld"
    }
  },
  inject: ['obj', 'developerFn', 'year', 'app'],
  methods: {
  },
  computed:{
    developer(){
      return this.developerFn()
    }
  },
}
```

# $attrs/$listeners

> 利用 $attrs 实现祖孙组件间的数据传递， $listeners 实现祖孙组件间的事件监听 。

官网对 $attrs 的解释如下：

> 包含了父作用域中不作为 prop 被识别 (且获取) 的特性绑定 (class 和 style 除外)。当一个组件没有声明任何 prop 时，这里会包含所有父作用域的绑定 (class 和 style 除外)，并且可以通过 v-bind="$attrs"

官网对 $listeners 的解释如下：

> 包含了父作用域中的 (不含 .native 修饰器的) v-on 事件监听器。它可以通过 v-on="$listeners" 传入内部组件——在创建更高层次的组件时非常有用。

我觉得 $attrs 和 $listeners 属性像两个收纳箱，一个负责收纳属性，一个负责收纳事件，都是以对象的形式来保存数据。看下面的代码解释：

```html
<!-- ChildComponent.vue -->
<template>
  <div class="child-component">
    <h1>我是一个 {{ professional }}</h1>
  </div>
</template> 
<script>
export default {
  name: 'ChildComponent',
  props: { 
      professional: { 
          type: String, 
          default: '码农' 
        } 
  },
  created() {
    console.log(this.$attrs, this.$listeners)
    // 调用父组件App.vue中的triggerTwo()方法 
    this.$listeners.two()
  }
}
</script>
```

```html
<!-- App.vue -->
<template>
  <div id="app">
    <img alt="Vue logo" src="./assets/logo.png">
    <ChildComponent 
        :professional="professional" 
        :name="name" 
        one.native="triggerOne" 
        two="triggerTwo" 
    >
  </div>
</template> 

<script>
import ChildComponent from './components/ChildComponent.vue'

export default {
  name: 'app',
  data() {
    return {
      professional: '屌丝码农',
      name: '大漠'
    }
  },
  components: {
    ChildComponent
  },
  inheritAttrs: false,
  methods: {
    triggerOne() { console.log('one') },
    triggerTwo() { console.log('two') }
  }
}
</script>
```

- 如果多个组件嵌套,使用v-bind和v-on来传递参数,把当前组件的事件和属性传递给子组件
  
```javascript
<Component v-bind="$attrs" v-on="$listeners" />
```

- 当我们在组件上赋予了一个非Prop 声明时，编译之后的代码会把这些个属性都当成原始属性对待，添加到 html 原生标签上，看上面的代码编译之后的样子： 

```html
 <h2>parent foo</h2>
```

复制代码这样会很难看，同时也爆了某些东西。如何去掉？这正是 inheritAttrs 属性的用武之地！给组件加上这个属性就行了，一般是配合 $attrs 使用。看代码：

```javascript
 inheritAttrs: false,// 默认是 true
```

# v-slot

> 作用：用于模板内容分发，将内容分发到具名插槽或默认插槽。

```html
<template>
  <div>
    <h1>我是父组件</h1>
    <div>
      <slot name="header">
        <p>默认头部插槽</p>
      </slot>
    </div>
    <div>
      <slot>
        <p>默认内容插槽</p>
      </slot>
    </div>
  </div>
</template>
<script>
export default {
  name: 'ParentComponent',
}
</script>
```

```html
<template>
  <div>
    <h1>我是子组件</h1>
    <div>
      <slot name="header">
        <p>子组件的头部插槽</p>
      </slot>
    </div>
    <div>
      <slot>
        <p>子组件的默认内容插槽</p>
      </slot>
    </div>
  </div>
</template>
<script>
export default {
  name: 'ChildComponent',
}
</script>
```

```html
<template>
  <div>
    <ParentComponent>
      <template v-slot:header>
        <h2>自定义头部插槽</h2>
      </template>
      <p>自定义内容</p>
    </ParentComponent>
  </div>
</template>
<script>
import ParentComponent from './components/ParentComponent.vue'
import ChildComponent from './components/ChildComponent.vue'


export default {
  name: 'App',
  components: {
    ParentComponent,
    ChildComponent
  }
}
</script>
```

- 父组件中，使用 `<slot>` 标签定义了两个插槽，一个默认插槽，一个名为 header 的插槽。
- 子组件中，使用 `<slot>` 标签定义了两个插槽，一个默认插槽，一个名为 header 的插槽。
- 父组件中，使用 `<template>` 标签定义了 header 插槽的具体内容，内容为 `<h2>自定义头部插槽</h2>`。
- 父组件中，使用 `<p>` 标签定义了默认内容插槽的具体内容，内容为 `<p>自定义内容</p>`。
- 最终渲染结果为：

  ```html
  <div>
    <h1>我是父组件</h1>
    <div>
      <h2>自定义头部插槽</h2>
    </div>
    <div>
      <p>自定义内容</p>
    </div>
  </div>
  ```

# eventBus

事件中心管理组件间的通信, 在vue中可以使用它来作为沟通桥梁的概念, 就像是所有组件共用相同的事件中心，可以向该中心注册发送事件或接收事件， 所以组件都可以通知其他组件。

> 注意：eventBus也有不方便之处, 当项目较大,就容易造成难以维护的灾难

## 新的Vue实例

在main.js中定义一个全局的新的Vue实例，**注意要使用export导出**

```javascript
import Vue from 'vue'
export const EventBus = new Vue()
```

```javascript
//App.vue中引入两个兄弟组件
 <template>
  <div>
    <dad></dad>
    <uncle></uncle>
  </div>
</template>
 
 <script>
import dad from "./components/dad.vue";
import uncle from "./components/uncle.vue";

export default {
  components: { dad, uncle },
};
</script>
```

```javascript
 //./components/dad.vue发送事件，点击后num++
<template>
  <div>
    <button @click="additionHandle">+加法器</button>
  </div>
</template>
 
 <script>
import { EventBus } from "../main";

export default {
  data() {
    return {
      num: 1,
    };
  },

  methods: {
    additionHandle() {
      EventBus.$emit("addition", {
        num: this.num++,
      });
    },
  },
};
</script>
```

```javascript
// ./compoents/uncle.vue 中$on监听接收数据
 <template>
  <div>计算和: {{ count }}</div>
</template>
 
 <script>
import { EventBus } from "../main";
export default {
  data() {
    return {
      count: 0,
    };
  },

  mounted() {
    EventBus.$on("addition", (param) => {
      this.count = this.count + param.num;
    });
  },
};
</script>
```

**移除事件监听：**

```javascript
import { eventBus } from 'event-bus.js'

EventBus.$off('addition', {})
```

## 在Vue原型上新建一个全局事件总线

直接在main.js中Vue初始化的时候创建全局事件总线

```javascript
import Vue from 'vue'
import App from './App.vue'

Vue.config.productionTip = false

new Vue({
  render: h => h(App),
  beforeCreate() {
    Vue.prototype.$bus = this;
  }
}).$mount('#app')
```

```javascript
//注册事件
 this.$bus.$emit("showMsg", this.msg);
```

```javascript
//监听事件
this.$bus.$on('showMsg',(val)=>{console.log()})
```

# localStorage/sessinStorage

这种通讯比较简单 ，数据存储在Application中查看，但是数据和状态混乱不易维护。

```javascript
window.localStorage.setItem（key，value）//保存数据

window.localStorage.getItem（key) //获取数据

window.localStorage.removeItem（key）//删除数据
```

# vuex

![alt text](images/image-1.png)


