---
title: "Vue3核心"
tags: []
source: "baike"
source_path: "开发术语 / 前端开发"
collected: "2026-09-05"
status: "imported"
---

# Vue3核心

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
