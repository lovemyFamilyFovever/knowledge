---
title: Vue2 Render Function
tags: [Vue2, 源码]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue2/Details/render.md"
---

# Vue2 Render Function  

## `createElement` 参数  

`createElement` 接收三个参数：  

```javascript
createElement(
  type,
  [props],
  [children]
)
```

1. `type`：一个字符串或一个组件构造器，表示要创建的元素的类型。

2. `props`：一个对象，包含元素的属性。

3. `children`：一个数组，包含子元素。


## 示例  

```javascript
const h = Vue.createElement;

const app = h('div', {  
  attrs: { id: 'app' },
  class: { 'app-container': true },
  style: { backgroundColor: 'red' },
  on: { click: () => console.log('clicked') }
}, [
  h('h1', {
    style: { color: 'blue' }
  }, 'Hello World'),
  h('p', 'This is a paragraph')
]);


new Vue({
  el: '#app',
  render: (h) => app
});
```


## 注意事项  

- `createElement` 是一个全局函数，可以通过 `Vue.createElement` 访问。

- `createElement` 接收三个参数，第一个参数是元素的类型，第二个参数是元素的属性，第三个参数是子元素。

- `props` 对象可以包含 `class`、`style`、`attrs`、`on`、`directives`、`slot` 等属性。

- `children` 数组可以包含多个子元素。   

- `h` 函数可以简化 `createElement` 的调用。  

- `h` 函数可以接收多个参数，第一个参数是元素的类型，第二个参数是元素的属性，第三个参数是子元素。
  

## 官方文档  
```javascript
// @returns {VNode}
createElement(
  // {String | Object | Function}
  // 一个 HTML 标签名、组件选项对象，或者
  // resolve 了上述任何一种的一个 async 函数。必填项。
  'div',

  // {Object}
  // 一个与模板中 attribute 对应的数据对象。可选。
  {
    //
  },

  // {String | Array}
  // 子级虚拟节点 (VNodes)，由 `createElement()` 构建而成，
  // 也可以使用字符串来生成“文本虚拟节点”。可选。
  [
    '先写一些文字',
    createElement('h1', '一则头条'),
    createElement(MyComponent, {
      props: {
        someProp: 'foobar'
      }
    })
  ]
)
```


---