---
outline: [1,3]
head:
  - - meta
    - name: description
      content: 前端bug汇总
  - - meta
    - name: keywords
      content: 前端 疑难杂症 前端开发 前端框架 前端工程师 bug
tags: [Bug]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/bugs/index.md"
---

# 为什么textarea会有默认的value啊 而且这个value是空白的字符

如果你不想在`<textarea>`标签中有默认的空白字符，可以采取以下解决方案： 
`
1. 将`<textarea>`标签的起始标签和结束标签写在同一行，而不是分行写。这样可以避免默认的空白字符。例如： `html <textarea class="form-control required" id="rem" name="rem"></textarea>`

2.  使用JavaScript或其他脚本语言，在页面加载完成后，通过脚本将`<textarea>`标签的value属性设置为空字符串。这样可以清除默认的空白字符。例如：

```javascript
document.getElementById("rem").value = "";
```

# vite+vue3+ts 项目搭建时的@符号路径不识别问题

在使用vite+vue3+ts项目搭建时，如果路径中含有@符号，则会报错，提示路径不正确。

解决方案：

在vite.config.ts文件中配置resolve.alias，将@符号路径映射到项目根目录。

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})

```


这样就可以正确解析@符号路径了。
