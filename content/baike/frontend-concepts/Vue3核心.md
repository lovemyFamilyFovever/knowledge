---
title: "Vue3核心"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# Vue3核心


> 📌 **导航**：本文是 **Vue3核心** 词条，属于 frontend-concepts 术语集。相关枢纽：[[HTML & CSS 核心概念]]、[[JavaScript 基础核心概念]]、[[React深入]]、[[Vue3核心]]、[[前端工程化核心概念]]。

## Composition API

```javascript
import { ref, computed, watch } from 'vue';

export default {
    setup() {
        const count = ref(0);
        const double = computed(() => count.value * 2);

        watch(count, (newVal, oldVal) => {
            console.log(`count: ${oldVal} -> ${newVal}`);
        });

        return { count, double };
    }
};
```

## 响应式原理（Proxy）

```javascript
const state = new Proxy(target, {
    get(target, key, receiver) {
        track(target, key);  // 依赖收集
        return Reflect.get(target, key, receiver);
    },
    set(target, key, value, receiver) {
        const result = Reflect.set(target, key, value, receiver);
        trigger(target, key);  // 触发更新
        return result;
    }
});
```

## 编译优化

- 静态提升(HoistStatic)
- PatchFlag标记动态节点
- Block Tree扁平化
- 事件缓存

## 相关术语

[[HTML & CSS 核心概念]]、[[JavaScript 基础核心概念]]、[[React深入]]、[[前端工程化]]、[[前端工程化核心概念]]、[[前端框架核心概念]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
