---
title: "React深入"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# React深入


> 📌 **导航**：本文是 **React深入** 词条，属于 frontend-concepts 术语集。相关枢纽：[[HTML & CSS 核心概念]]、[[JavaScript 基础核心概念]]、[[React深入]]、[[Vue3核心]]、[[前端工程化核心概念]]。

## Hooks原理

```javascript
// useState简化实现
let state;
let index = 0;
function useState(initialValue) {
    state = state ?? initialValue;
    const currentIndex = index++;
    function setState(newValue) {
        state = newValue;
        render(); // 触发重新渲染
    }
    return [state, setState];
}
```

## Fiber架构

```
React 16之前：递归渲染，不可中断
React 16之后：Fiber树，可中断，优先级调度

Virtual DOM -> Fiber Tree -> Commit阶段 -> DOM更新
```

## Concurrent Mode

```javascript
// 低优先级更新可以被高优先级打断
startTransition(() => {
    setSearchResults(filterData(query)); // 低优先级
});
setInputValue(query); // 高优先级
```

## Server Components

```javascript
// 服务端组件：不发送JS到客户端
async function ArticleList() {
    const articles = await db.articles.findMany();
    return <div>{articles.map(a => <Article key={a.id} {...a} />)}</div>;
}

// 客户端组件：交互逻辑
'use client';
function LikeButton({ id }) {
    const [liked, setLiked] = useState(false);
    return <button onClick={() => setLiked(!liked)}>{liked ? '❤️' : '🤍'}</button>;
}
```

## 相关术语

[[HTML & CSS 核心概念]]、[[JavaScript 基础核心概念]]、[[Vue3核心]]、[[前端工程化]]、[[前端工程化核心概念]]、[[前端框架核心概念]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
