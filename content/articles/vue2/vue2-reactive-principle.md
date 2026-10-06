---
outline: [1,3]
head:
  - - meta
    - name: description
      content: 手写vue2响应式原理
  - - meta
    - name: keywords
      content: 手写vue2响应式原理
tags: [Vue2, 响应式]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/vue2-reactive-principle.md"
---

## 写在前面

这道题目是面试中相当高频的一道题目了，但凡你简历上有写：“熟练使用Vue并阅读过其部分源码”，那么这道题目十有八九面试官都会去问你。

>什么？你简历上不写阅读过源码，那面试官也很有可能会问你是否阅读过响应式相关的源码

## 整体流程

作为一个前端的MVVM框架，Vue的基本思路和Angular、React并无二致，其核心就在于: 当数据变化时，自动去刷新页面DOM，这使得我们能从繁琐的DOM操作中解放出来，从而专心地去处理业务逻辑。

这就是Vue的数据双向绑定（又称响应式原理）。数据双向绑定是Vue最独特的特性之一。此处我们用官方的一张流程图来简要地说明

![Vue双向绑定](https://imgconvert.csdnimg.cn/aHR0cHM6Ly9tbWJpei5xcGljLmNuL21tYml6L0xOcldsNG41WElKTFRwTThNYXhGZW9EcVZVN0Q3cFM5UTFVN2ZhV09XbjZpYjRSVjNUVmljbUwyZFB2cnE1MzZpYmliYkZZY2lhYlZmc0d1WFoyV3RDcUxwMGcvNjQw?x-oss-process=image/format,png "Vue双向绑定")


<html>
<center>Vue双向绑定</center>
</html>


Vue响应式系统的整个流程：

在Vue中，每个组件实例都有相应的watcher实例对象，它会在组件渲染的过程中把属性记录为依赖，之后当依赖项的setter被调用时，会通知watcher重新计算，从而致使它关联的组件得以更新。

><html><p style="background:#eef0f0;color:black">这是一个典型的观察者模式。</p></html>


## 关键角色

在 Vue 数据双向绑定的实现逻辑里，有这样三个关键角色：

- Observer: 它的作用是给对象的属性添加getter和setter，用于依赖收集和派发更新
- Dep: 用于收集当前响应式对象的依赖关系,每个响应式对象包括子对象都拥有一个Dep实例（里面subs是Watcher实例数组）,当数据有变更时,会通过dep.notify()通知各个watcher。

+ Watcher: 观察者对象 , 实例分为渲染 watcher (render watcher),计算属性 watcher (computed watcher),侦听器 watcher（user watcher）三种。
+ 

## Watcher 和 Dep 的关系

为什么要单独拎出来一小节专门来说这个问题呢？因为大部分同学只是知道：**Vue的响应式原理是通过Object.defineProperty实现的。被Object.defineProperty绑定过的对象，会变成「响应式」化。也就是改变这个对象的时候会触发get和set事件。**

但是对于里面具体的对象依赖关系并不是很清楚，这样也就给了面试官一种：你只是背了答案，对于响应式的内部实现细节，你并不是很清楚的印象。

关于Watcher 和 Dep 的关系这个问题，其实刚开始我也不是很清楚，在查阅了相关资料后，才逐渐对里面的具体实现有了清晰的理解。

![Watcher和Dep的关系](./images/Watcher和Dep的关系.png)

刚接触Dep这个词的同学都会比较懵:

Dep究竟是用来做什么的呢？我们通过defineReactive方法将data中的数据进行响应式后，虽然可以监听到数据的变化了，那我们怎么处理通知视图就更新呢？

Dep就是帮我们依赖管理的。

如上图所示：**一个属性可能有多个依赖，每个响应式数据都有一个Dep来管理它的依赖。**

## 一段话总结原理

上面说了那么多，下面我总结一下Vue响应式的核心设计思路：

当创建Vue实例时,vue会遍历data选项的属性,利用Object.defineProperty为属性添加getter和setter对数据的读取进行劫持（getter用来依赖收集,setter用来派发更新）,并且在内部追踪依赖,在属性被访问和修改时通知变化。

每个组件实例会有相应的watcher实例,会在组件渲染的过程中记录依赖的所有数据属性（进行依赖收集,还有computed watcher,user watcher实例）,之后依赖项被改动时,setter方法会通知依赖与此data的watcher实例重新计算（派发更新）,从而使它关联的组件重新渲染。

到这里，我们已经了解了“套路”，下面让我们用伪代码来实现一下Vue的响应式吧！

## 核心实现

``` javascript
/**
 * @name Vue数据双向绑定（响应式系统）的实现原理
 */
 
// observe方法遍历并包装对象属性
function observe(target) {
  // 若target是一个对象，则遍历它
  if (target && typeof target === "Object") {
    Object.keys(target).forEach((key) => {
      // defineReactive方法会给目标属性装上“监听器”
      defineReactive(target, key, target[key]);
    });
  }
}
// 定义defineReactive方法
function defineReactive(target, key, val) {
  const dep = new Dep();
  // 属性值也可能是object类型，这种情况下需要调用observe进行递归遍历
  observe(val);
  // 为当前属性安装监听器
  Object.defineProperty(target, key, {
    // 可枚举
    enumerable: true,
    // 不可配置
    configurable: false,
    get: function () {
      return val;
    },
    // 监听器函数
    set: function (value) {
      dep.notify();
    },
  });
}
 
class Dep {
  constructor() {
    this.subs = [];
  }
 
  addSub(sub) {
    this.subs.push(sub);
  }
 
  notify() {
    this.subs.forEach((sub) => {
      sub.update();
    });
  }
}
```

## 另外一种实现的办法，比较简洁直观。

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
</head>
<body>
    <span id="harry" style="line-height: 32px;">&nbsp;</span>
    <br>
    <input type="text" id="trigger">

</body>

<script>
    let harry=document.getElementById("harry");
    let trigger=document.getElementById("trigger");
    let key='profile';
    let store={};
    let obj={
        profile:''
    }
    Object.defineProperty(obj,key,{
        set(value){
            harry.innerText=value;
            store[key]=value;
        },
        get(){
            return store[key];    
        }
    })
    trigger.addEventListener('keyup',function(){
        obj[key]=this.value;
        console.log(obj[key]);
    })
</script>

</html>
```
[![sj8f74.jpg](https://s3.ax1x.com/2021/01/26/sj8f74.jpg)](https://imgchr.com/i/sj8f74)