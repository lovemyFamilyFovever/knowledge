---
outline: [1,3]
head:
  - - meta
    - name: description
      content: html5 bugs
  - - meta
    - name: keywords
      content: html5 bugs
tags: [HTML, Bug]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/html/bugs.md"
---

火狐浏览器input设置为number的时候有个bug，输入一个正整数，比如说2，点击浏览器默认自带的数字上下箭头，当input框内的提示文字变成placeholder还原后，再输入数字placeholder不会消失，会叠在底部


解决方案
1. 使用CSS和JavaScript
   ``` javascript
    <input type="number" id="numberInput" placeholder="请输入数字">

    <script>
    document.getElementById('numberInput').addEventListener('input', function() {
        if (this.value) {
            this.placeholder = '';
        } else {
            this.placeholder = '请输入数字';
        }
    });
    </script>

    <style>
    /* 确保输入框的样式一致 */
    input[type="number"]::placeholder {
        color: #999;
        opacity: 1; /* 确保placeholder的颜色在所有浏览器中一致 */
    }
    </style>
```
