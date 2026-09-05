---
outline: [1,3]
tags: [Vue3]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue3/leak-filling.md"
---

# vue3+ts+pinia创建项目遇到的坑

## vue3加ts出现 --找不到模块“../views/admin/Pro/ProList.vue”或其相应的类型声明。ts(2307) 

`vite`+`vue3`+`ts`+`pinia创建项目遇到这个问题，虽然不影响代码运行，但看着恶心人。`

原因：`ts`只支持导出导入模块，但是`vue`不是模块，我们需要申明一下`vue`是个模块，`ts`可以导入        

解决方法：在目录下`env.d.ts`文件中添加（目录下没有的话就新建一个）

``` typescript
declare module "*.vue" {
  import { DefineComponent } from "vue";
  const component: DefineComponent<{}, {}, any>;
  export default component;
}
```

这样就可以在`ts`文件中导入`vue`组件了,但是还是需要添加文件后缀名`.vue`

## 配置路径别名@

**注意这个只支持js文件的自动补全路径别名**

```javascript
// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  }
})
```

如果需要ts文件自动补全@路径别名，需要在`tsconfig.json`文件中配置如下：

```json
// tsconfig.app.json
// tsconfig.json
// tsconfig.node.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  }
}
```