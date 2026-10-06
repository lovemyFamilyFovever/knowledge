---
tags: [Vue3, Vue Router]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "frontend/vue3/vue-router.md"
---

# vue-router 工作模式

路由有两种工作模式：

1. `createWebHistory()` `history` 模式
   
   优点：`URL`更加美观，不带有`#`，更接近传统的网站`URL`。

   缺点：后期项目上线，需要服务端配合处理路径问题，否则刷新会有`404`错误。

   ```javascript
   const router = createRouter({
      history:createWebHistory(), //history模式
      /******/
    })
   ```

2. `createWebHashHistory()` ` hash` 模式

  优点：兼容性更好，因为不需要服务器端处理路径。

  缺点：`URL`带有`#`不太美观，且在`SEO`优化方面相对较差。刷新页面会导致页面回到顶部，比较适合内部系统。

  ```javascript
  const router = createRouter({
    history:createWebHashHistory(), //hash模式
    /******/
  })
```
