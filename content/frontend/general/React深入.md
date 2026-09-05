---
title: "React深入"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# React深入

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
