---
outline: [2,3]
head:
  - - meta
    - name: description
      content: 防抖节流
  - - meta
    - name: keywords
      content: 防抖节流 前端开发 前端框架 前端工程师
tags: [JavaScript, 性能优化]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/javascript/debounce-throttle.md"
---

# 防抖和节流

## 防抖

防抖是指在事件被触发 n 秒后再执行回调，如果在这 n 秒内又被触发，则重新计时。

```javascript
function debounce(func, wait) {
  let timeout;
  return function() {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      func.apply(this, arguments);
    }, wait);
  };
}
```

## 节流

节流是指连续触发事件，但是在 n 秒内只执行一次回调。

```javascript
function throttle(func, wait) {
  let timeout;
  return function() {
    if (!timeout) {
      timeout = setTimeout(() => {
        timeout = null;
        func.apply(this, arguments);
      }, wait);
    }
  };
}
```

## 应用

防抖和节流的应用场景：

- 防抖：在输入框输入时，防止用户输入过快，将输入内容合并为一次请求。
- 节流：在滚动页面时，防止频繁触发事件，将事件合并为一次请求。
  
- 按钮点击：防止用户重复点击按钮，导致多次提交请求。
- 表单提交：防止用户频繁提交表单，导致服务器压力过大。
- 图片懒加载：在页面滚动时，只加载当前可视区域的图片。