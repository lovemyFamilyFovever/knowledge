---
title: "React与Vue框架面试题库 - 80道精选题目"
tags: []
source: "baike"
source_path: "技术题库 / React与Vue框架"
collected: "2026-09-05"
status: "imported"
---

# React与Vue框架面试题库 - 80道精选题目

> 80 道精选面试题 | 涵盖组件设计、状态管理、响应式原理、diff、性能优化与框架选型

## React基础（10题）

### 1. 请解释 React 中的虚拟 DOM 是什么？它如何提升性能？｜中级

> 🎯 关键要点
> - 虚拟 DOM 是 React 在内存中维护的轻量 DOM 表示（JS 对象树）。状态变化时先生成新虚拟 DOM 树，diff 出最小操作集，再批量更新真实 DOM
> - 性能收益来自三点：减少真实 DOM 操作次数、多次状态变化合并为一次批量更新、diff 结果最小化改动
> - diff 算法（Reconciliation）时间复杂度 O(n)，靠两条策略达成：不同类型元素直接重建子树；同层节点用 key 识别是否可复用
> - 虚拟 DOM 不一定比手动操作 DOM 快，它的真正价值是「声明式编程 + 跨平台渲染」（Web / Native / SSR）

```jsx
function App() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(count + 1)}>计数: {count}</button>;
}
// 内部流程：setCount → 生成新虚拟DOM树 → diff新旧树 → 计算最小变更 → 批量更新真实DOM
```

> 🔍 追问
> - 「虚拟 DOM 一定比直接操作 DOM 快吗？」——不是，框架的价值是用可维护的声明式代码换来接近手写优化的性能，而非绝对更快

### 2. JSX 是什么？它与 HTML 有什么区别？｜初级

> 🎯 关键要点
> - JSX 是 JavaScript 的语法扩展，编译后（Babel/SWC）是 `React.createElement()` 调用，产物是 JS 对象而非 HTML 字符串
> - 属性命名差异：`class` → `className`、`for` → `htmlFor`、`tabindex` → `tabIndex`
> - 事件是函数引用 `onClick={handleClick}`，不是字符串绑定；内联样式是对象 `style={{ color: 'red' }}`
> - JSX 里可以嵌任意 JS 表达式（`{condition ? <A/> : <B/>}`、`{list.map(...)}`），注释用 `{/* */}`

```jsx
function App() {
  const isLoggedIn = true;
  return (
    <div>
      {isLoggedIn ? <p>欢迎回来</p> : <p>请登录</p>}
      {[1, 2, 3].map(item => <li key={item}>{item}</li>)}
      <span style={{ color: 'red' }}>红色文字</span>
    </div>
  );
}
```

> ⚠️ 注意
> - `.map()` 渲染列表必须给 key；JSX 中 `&&` 短路渲染要小心数字 0 会被渲染出来（`{count && <Badge/>}` 在 count 为 0 时显示 "0"）

### 3. 从 setState 到屏幕更新，React 内部完整流程是怎样的？（Fiber 架构）｜高级

> 🎯 关键要点
> - 流程：触发更新（setState/dispatch）→ 创建带有优先级（Lane 模型）的 Update → 调度器 Scheduler 按优先级排序 → Render 阶段（可中断，构建 WorkInProgress Fiber 树 + diff）→ Commit 阶段（同步不可中断，执行 DOM 操作和生命周期副作用）
> - Fiber 把渲染拆成一个个 Fiber 节点的工作单元，Scheduler 借助浏览器 `requestIdleCallback` 思想的切片机制，在每帧空闲时间做渲染，高优先级输入可打断低优先级更新
> - 双缓冲：current 树（已上屏）与 workInProgress 树（构建中），commit 时指针交换，避免重复创建
> - Render 阶段可中断可重做（必须无副作用），Commit 阶段不可中断（有 DOM/生命周期副作用）

> 🔍 追问
> - 「为什么 Render 阶段不能有副作用？」——因为它随时可能被打断重跑，副作用会被重复执行
> - 「并发模式下的 tearing（撕裂）问题是什么？」——一次渲染中读取到不一致的外部状态，需要 external store 的 `useSyncExternalStore` 保证

### 4. Fiber 架构解决了什么问题？时间切片是如何实现的？｜高级

> 🎯 关键要点
> - React 15 的 Stack Reconciler 递归渲染不可中断，大组件树一次更新可能阻塞主线程几十毫秒，造成输入卡顿掉帧
> - Fiber 用链表结构（child/sibling/return）替代递归树，渲染变成循环处理一个个工作单元，每个单元做完检查是否该让出主线程
> - 时间切片：Scheduler 把长任务切成 ≤5ms 的小片，每片结束用 MessageChannel 宏任务让出线程，让浏览器有机会处理输入、绘制
> - 配合优先级（Lane），用户输入 > 过渡更新，`startTransition` 标记的低优先级更新可被中断

> ⚠️ 注意
> - 时间切片不是让渲染变快，而是让「长渲染不阻塞交互」；总耗时甚至可能略增，换来的是可感知的流畅度

### 5. 说一下 React class 组件的生命周期，16 之后哪些被废弃了，为什么？｜中级

> 🎯 关键要点
> - 挂载：constructor → getDerivedStateFromProps → render → componentDidMount
> - 更新：getDerivedStateFromProps → shouldComponentUpdate → render → getSnapshotBeforeUpdate → componentDidUpdate
> - 卸载：componentWillUnmount；错误边界：getDerivedStateFromError / componentDidCatch
> - 废弃：componentWillMount / componentWillReceiveProps / componentWillUpdate（16.3 起加 UNSAFE_ 前缀）。原因是它们在 Fiber 可中断渲染下会被多次调用，副作用写法容易出错
> - 替代关系：componentWillReceiveProps → getDerivedStateFromProps + componentDidUpdate；componentWillMount → componentDidMount 或 constructor

> 🔍 追问
> - 「getSnapshotBeforeUpdate 的典型场景？」——更新前读取滚动位置/DOM 尺寸，更新后恢复（聊天窗口保持滚动到底部）

### 6. React 的事件机制是什么？合成事件与原生事件有何区别？｜中级

> 🎯 关键要点
> - React 自己实现了一套合成事件（SyntheticEvent）：在 root 容器上统一委托监听（React 17 前挂在 document，17 起改挂 root），模拟捕获/冒泡分发
> - 为什么要委托：减少监听器数量、抹平浏览器差异、统一事件池与调度优先级
> - React 17 变化：事件委托从 document 改到 root——多版本 React 共存页面事件不再互相污染；onScroll 不再冒泡
> - 原生事件与合成事件混用时注意：`e.stopPropagation()` 在合成事件里只阻止合成事件流；`e.nativeEvent` 才是原生对象；document 级原生监听要提防与 React 事件的触发顺序问题

> ⚠️ 注意
> - React 17+ 移除了事件池（event pooling），不再需要 `e.persist()`；老项目面试常考这个差异

### 7. 受控组件与非受控组件的区别？各自适用场景？｜初级

> 🎯 关键要点
> - 受控：表单值由 React state 驱动，`value` + `onChange` 配对使用，每次输入都走一遍状态更新，数据流单向可追踪
> - 非受控：值存在 DOM 内部，用 `ref` 在需要时读取（`defaultValue` 只设初值），不随输入触发重渲染，性能开销小
> - 场景：需要实时校验/联动/受用户输入驱动的表单用受控；文件上传 `<input type="file">` 只能非受控；超长表单或性能敏感场景可用非受控
> - 大型表单库（react-hook-form 默认非受控 + 按需注册）正是利用非受控减少重渲染

### 8. key 的作用是什么？为什么不能用数组索引作 key？｜中级

> 🎯 关键要点
> - key 是给 diff 算法的「身份证」：同层比较时 React 靠 key 判断节点是移动、复用还是销毁重建
> - 用 index 作 key 的问题：列表头部插入/删除、或列表项带输入框等内部状态时，index 对应关系错乱——节点被错误复用，状态串位（第 2 项的输入框内容跑到第 1 项）
> - 列表纯静态展示且不会重排时，index 作 key 勉强可接受；有增删、排序、拖拽的列表必须用稳定唯一 ID
> - key 只需兄弟节点间唯一，不需全局唯一

```js
// 反例：在头部 unshift 一条数据，index 作 key 导致所有项 diff 结果错位
{items.map((item, index) => <Row key={index} item={item} />)}
// 正解：key 用业务稳定 ID
{items.map(item => <Row key={item.id} item={item} />)}
```

### 9. React 18 的并发特性有哪些？startTransition 和 useDeferredValue 怎么选？｜高级

> 🎯 关键要点
> - 自动批处理（Automatic Batching）：Promise/setTimeout/原生事件里的多次 setState 合并为一次渲染（18 前只有 React 事件回调里才批处理）
> - startTransition：把更新标记为「可中断的过渡更新」，高优先级输入可以插队，适合搜索框输入 + 结果列表的分离渲染
> - useDeferredValue：返回值的「延迟副本」，让旧值先渲染、新值后台渲染，适合对「一个派生值」做降优先级
> - Suspense 与流式 SSR（renderToPipeableStream）：HTML 分块发送，hydration 也可选择性进行（Selective Hydration）
> - 选择：控制「更新触发时机」用 startTransition；只有值可用、触发时机不可控（如父组件传下来的 props）用 useDeferredValue

> 🔍 追问
> - 「useDeferredValue 和防抖的区别？」——防抖是固定延迟丢弃中间态，deferredValue 不丢中间态且渲染完立即响应，无固定延迟

### 10. useId 是做什么的？解决了什么问题？｜中级

> 🎯 关键要点
> - 生成稳定且服务端/客户端一致的唯一 ID，用于表单控件 label/htmlFor、aria 属性关联
> - 为什么不用 `Math.random()`/自增计数器：SSR 水合时服务端和客户端生成的序列必须一致，随机数会导致 hydration mismatch
> - useId 的产物与组件树位置绑定，且对冒号 `:` 做了替换（`:r0:` 格式），避免干扰 CSS 选择器
> - 不能拿来当列表 key 或数据库 ID——它的稳定性以组件树结构不变为前提

## React Hooks（10题）

### 11. 请解释 React Hooks 的工作原理，为什么不能写在条件语句里？｜高级

> 🎯 关键要点
> - Hooks 的工作原理：每个函数组件对应一个 Fiber 节点，其 `memoizedState` 是一条 Hook 链表；每次渲染按调用顺序从链表头逐个对应取状态
> - 因为按「调用顺序」匹配而不是按名字匹配，条件/循环里的 Hook 会导致某次渲染链表长度或顺序对不上，取错状态直接崩
> - 为什么需要 Hooks：跨组件复用状态逻辑（替代 HOC/render props 嵌套地狱）、把相关逻辑聚在一起（替代生命周期切片）、摆脱 this 绑定困惑
> - 常用 Hooks 心智地图：useState/useReducer（状态）、useEffect/useLayoutEffect（副作用）、useContext（跨层）、useRef（可变值/DOM）、useMemo/useCallback（缓存）

```jsx
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then(r => r.json())
      .then(setUser);
  }, [userId]); // 依赖数组决定何时重新执行
  return <div>{user?.name}</div>;
}
```

### 12. 什么是 useState 的闭包陷阱？怎么解决？｜中级

> 🎯 关键要点
> - 本质：每次渲染都是一次独立的函数执行，内部所有回调捕获的是「本次渲染的 state 快照」。定时器/异步回调里读到的永远是注册那一刻的值
> - 典型场景：`setTimeout(() => setCount(count + 1), 3000)` 三秒内连续点击，最终只 +1
> - 解法一：函数式更新 `setCount(c => c + 1)`，基于最新值计算
> - 解法二：useRef 保存最新值（`.current` 不受渲染快照限制）；解法三：`useEffect` 正确声明依赖，让回调随依赖重建

```jsx
// 闭包陷阱
useEffect(() => {
  const timer = setInterval(() => setCount(count + 1), 1000); // 永远 +1 一次
  return () => clearInterval(timer);
}, []);
// 正解：函数式更新
useEffect(() => {
  const timer = setInterval(() => setCount(c => c + 1), 1000);
  return () => clearInterval(timer);
}, []);
```

### 13. useEffect 和 useLayoutEffect 的区别？｜中级

> 🎯 关键要点
> - useEffect：异步、在 commit 后、浏览器绘制之后执行，不阻塞渲染
> - useLayoutEffect：同步、在 DOM 变更后、浏览器绘制前执行，会阻塞绘制
> - 场景：数据请求、订阅、日志用 useEffect；需要在用户看到之前测量并修改 DOM（防闪烁）用 useLayoutEffect，如 Tooltip 位置计算：先量 DOM 尺寸再定位
> - SSR 下 useLayoutEffect 会告警（服务端没有「绘制前」概念），通用组件库要注意

> ⚠️ 注意
> - 滥用 useLayoutEffect 会把异步渲染退化成同步阻塞，长任务直接卡帧，默认用 useEffect

### 14. useEffect 依赖数组写了会死循环？如何正确处理依赖？｜中级

> 🎯 关键要点
> - 死循环根源：effect 里 set 的值又出现在依赖里，且每次 set 产生新引用（对象/数组/函数），渲染 → effect → set → 渲染无限循环
> - 依赖数组的语义是「本次 effect 捕获的渲染快照中，哪些外部值变了才重跑」——不是提示，是保证一致性的契约
> - 引用类型依赖的正确处理：依赖具体字段（`deps: [obj.id]`）；或 useMemo 稳定引用；或把对象拆成原始值依赖
> - 别用 `[]` 逃逸 lint、别用 eslint-disable 掩盖问题——那是在把 bug 埋进下一次渲染

```jsx
// 反例：每次渲染 data 都是新引用 → effect 每轮都跑
useEffect(() => { send(data); }, [data]);
// 正解：依赖稳定字段
useEffect(() => { send(data); }, [data.id, data.version]);
```

### 15. useMemo 和 useCallback 该用还是不该用？｜中级

> 🎯 关键要点
> - useCallback(fn, deps) 等价于 useMemo(() => fn, deps)：前者缓存函数引用，后者缓存计算结果
> - 三个正当理由：① 子组件被 React.memo 包裹，需要稳定 props 引用避免连带重渲染；② 计算本身昂贵（大数组排序/过滤）；③ 依赖了引用相等性的 effect 防抖
> - 滥用的代价：缓存本身有比较成本和内存成本，处处 memo 反而更慢、代码更难读
> - 默认不 memo，Profiler 定位到真实重渲染热点后再精准 memo——这是「先测量后优化」

> 🔍 追问
> - 「React Compiler（原 React Forget）解决什么？」——编译期自动做依赖分析与记忆化，让手写 useMemo/useCallback 逐步退出历史舞台

### 16. useRef 的两个用途分别是什么？改 ref.current 会触发渲染吗？｜初级

> 🎯 关键要点
> - 用途一：持有 DOM 节点或组件实例（`<input ref={inputRef}>`），做聚焦、测量、滚动
> - 用途二：跨渲染保存任意可变值（timer id、上一次的值、「是否已卸载」标记），像实例字段一样读写
> - 修改 `ref.current` 不触发重渲染——这是它和 state 的本质区别；也正因此不能用它渲染界面数据
> - 渲染期间读写 ref 是违反规则的（并发模式下行为未定义），只在事件回调和 effect 里读写

### 17. useContext 有什么性能问题？如何优化？｜中级

> 🎯 关键要点
> - Context 的更新是「广播式」的：Provider 的 value 变化，所有消费该 Context 的组件（无论用到 value 的哪个字段）全部重渲染
> - value 是内联对象字面量时，每次渲染都是新引用，消费组件跟着全量重渲染——第一层优化是 useMemo 包 value
> - 进一步优化：① 拆分 Context（状态 Context + 派发 Context，dispatch 引用天然稳定）；② Context 只放低频变化数据；③ 高频数据改用订阅式状态库（Zustand/Jotai 的 selector 订阅）
> - `useSyncExternalStore` 是做「外部订阅式状态」的官方原语

### 18. 如何设计一个可靠的自定义 Hook（比如 useFetch）？｜高级

> 🎯 关键要点
> - 状态建模完整：data / loading / error 三态之外还要考虑 abort、stale 竞态（快速切换参数时旧请求覆盖新请求）
> - 竞态处理：每次请求带序号或 AbortController，effect cleanup 里取消上一次
> - 卸载安全：setState 前检查已卸载（ref 标记）或依赖 cleanup 取消
> - 依赖透明：参数变更要正确触发重新请求；对外暴露 refetch 能力

```jsx
function useFetch(url) {
  const [state, setState] = useState({ data: null, loading: true, error: null });
  useEffect(() => {
    const controller = new AbortController();
    setState(s => ({ ...s, loading: true }));
    fetch(url, { signal: controller.signal })
      .then(r => r.json())
      .then(data => setState({ data, loading: false, error: null }))
      .catch(error => { if (error.name !== 'AbortError') setState({ data: null, loading: false, error }); });
    return () => controller.abort(); // cleanup 防竞态
  }, [url]);
  return state;
}
```

> 💡 提示
> - 生产项目优先 TanStack Query，它把缓存、去重、重试、失效、乐观更新都处理好了；手写 useFetch 的价值是面试展示对边界情况的完整思考

### 19. useReducer 和 useState 怎么选？｜中级

> 🎯 关键要点
> - useState 适合独立简单状态；useReducer 适合「多个状态字段联动」「下一次状态依赖上一次」「更新逻辑复杂需集中管理」
> - useReducer 把变更逻辑收敛为纯函数 reducer，便于测试（不依赖组件）、配合 Context 做轻量状态管理（dispatch 引用稳定）
> - dispatch 是稳定的，不随渲染变化，可作为 props 下传而不引起 memo 失效
> - 与 Redux 的关系：useReducer 是组件内建版；Redux 加了全局 store、中间件、DevTools、跨组件订阅优化

### 20. forwardRef 和 useImperativeHandle 是干什么的？｜高级

> 🎯 关键要点
> - 函数组件默认没有实例，父组件想拿到子组件内部节点/方法需要 forwardRef 转发 ref
> - useImperativeHandle 自定义暴露给父组件的 ref 内容：不暴露整个 DOM，只暴露受控的命令式 API（如 `focus()`、`scrollToBottom()`）
> - 价值：封装边界——父组件只能调用声明的接口，不能随意操作子组件内部结构，避免耦合
> - 第二个参数依赖数组决定何时重建暴露对象；React 19 中 ref 已可作为普通 props 传递，forwardRef 逐步退场

```jsx
const FancyInput = forwardRef((props, ref) => {
  const inputRef = useRef();
  useImperativeHandle(ref, () => ({
    focus: () => inputRef.current.focus(),
    clear: () => { inputRef.current.value = ''; },
  }), []);
  return <input ref={inputRef} />;
});
```

## React性能优化（6题）

### 21. React.memo 的原理与局限是什么？｜中级

> 🎯 关键要点
> - 原理：对 props 做浅比较（Object.is 逐个比对），全部相等则跳过本次渲染直接复用上次结果
> - 局限一：浅比较对对象/数组/函数无效——父组件每次渲染新建的内联对象和回调会击穿 memo
> - 局限二：memo 挡不住「自身状态/hooks 内部变化」引起的重渲染，它只拦截 props 变化
> - 配套要求：父侧用 useMemo/useCallback 稳定引用，或子组件接受 children（children 元素引用由父侧 JSX 决定）
> - shallowEqual 不够时可用自定义比较函数 `memo(Comp, areEqual)`，但要警惕维护成本

> 🔍 追问
> - 「为什么不能默认全部 memo？」——比较本身有成本，绝大多数组件重渲染开销远低于比较+心智负担，热点组件才值得

### 22. 万条数据的列表怎么渲染？虚拟滚动的原理是什么？｜高级

> 🎯 关键要点
> - 核心思想：只渲染可视区 ± overscan 范围内的条目，用绝对定位/padding 撑起总高度，滚动时按 scrollTop 换算 startIndex/endIndex 重算渲染窗口
> - 定高列表 O(1) 换算；不定高需要「预估高度 + 渲染后实测回写 + 高度缓存表」，或二次预估修正偏移
> - 窗口切换会闪：overscan 预渲染缓冲 + 滚动方向感知
> - 生产直接用 react-window / react-virtuoso；配合 key 稳定、行组件 memo、滚动节流

> ⚠️ 注意
> - 虚拟滚动只是解决「渲染节点多」，解决不了「单条渲染贵」；两者要分开优化

### 23. React 首屏加载慢，如何做代码分割与预加载？｜中级

> 🎯 关键要点
> - 路由级分割是第一优先级：`React.lazy(() => import('./Page'))` + `<Suspense fallback>`，配合打包器的自动 chunk 拆分
> - 组件级分割：重型弹窗、图表、编辑器按需加载，首屏不进 bundle
> - 预加载策略：路由 hover 时 `import()` 预取（webpackPrefetch / 手动 preload），把懒加载的白屏压到无感
> - 配合手段：骨架屏占位、SSR/SSG 消除首屏 JS 依赖、bundle 分析（source-map-explorer）找体积大头
> - 防止过度分割：chunk 太碎导致请求数暴增，HTTP/1.1 下反而更慢

### 24. 一个高频输入的大表单页面很卡，你怎么优化？｜高级

> 🎯 关键要点
> - 先定位：Profiler 记录一次输入触发了哪些组件重渲染、各自耗时，找到热点而不是瞎猜
> - 状态隔离：把输入 state 下沉到最小叶子组件，父级不感知输入变化（受控下沉）
> - 非受控替代：输入值不需要驱动 UI 联动时改用 defaultValue + ref，输入过程零重渲染
> - 联动降频：startTransition/useDeferredValue 把联动 UI 更新降优先级；节流把校验/请求频率降到合理值
> - 大组件拆分 + memo：让每次输入只重渲染真正依赖该值的组件

### 25. 如何用 React DevTools Profiler 定位性能问题？｜中级

> 🎯 关键要点
> - Record 一段交互，Flame Graph 看每个组件的渲染耗时，灰色的组件表示「因父组件重渲染而重渲染，但 props 没变」——memo 候选
> - 「Why did this render?」功能直接列出重渲染原因：state 变化/hooks 变化/父组件渲染/props 引用变化，精确到具体 hook 下标
> - 开启「Highlight updates」实时高亮重渲染区域，一眼看出输入框打字引发的连带渲染范围
> - 注意 Profiler 自身有开销，结论要在关闭录制或生产 profile 构建（`react-profiling`）下复核

### 26. 状态提升（lifting state up）和状态下推（colocation）如何权衡？｜中级

> 🎯 关键要点
> - 状态提升：多个组件共享的状态放到最近公共父级——代价是父组件变重、每次更新重渲染范围变大
> - 状态下推：把状态放到唯一消费它的组件里——重渲染范围最小，但跨组件共享需要再往上提
> - 判断标准：状态的真实消费者是谁？只有「真正需要读它的组件」的最近公共祖先才配持有它
> - 中间态：下推 + 按需回调上抛；或订阅式 store 让「持有位置」与「重渲染范围」解耦——这也是 Zustand/Jotai 存在的理由之一

## React生态（4题）

### 27. Next.js 的 SSG / SSR / ISR / CSR 各适用什么场景？｜高级

> 🎯 关键要点
> - CSR：纯客户端渲染，适合登录后内网系统，首屏 SEO 无要求
> - SSG：构建时生成静态 HTML，CDN 直发，适合文档、博客、营销页——性能天花板
> - SSR：请求时服务端渲染，适合内容因人而异、需要 SEO 的页面（电商详情、社交 feed），代价是服务端计算与 TTFB
> - ISR：静态页 + 后台定时/按需再生，兼顾 SSG 性能与内容新鲜度（`revalidate: 60`、on-demand revalidation）
> - 混合路由是常态：一个站点内不同页面各选各的模式；Hydration 要注意 SSR HTML 与客户端首次渲染必须一致，否则 hydration mismatch 报错

> 🔍 追问
> - 「RSC（React Server Components）和 SSR 的区别？」——SSR 是把初始 HTML 发给浏览器再水合；RSC 是组件本身在服务端执行、不进客户端 bundle，可直连数据库且零 JS 传输成本

### 28. TanStack Query（React Query）解决什么问题？和 Redux 怎么分工？｜中级

> 🎯 关键要点
> - 核心洞察：服务端数据和客户端状态是两类东西。服务端数据有缓存、会失效、可重取——不该塞进 Redux 手动搬运
> - React Query 提供：请求去重（同 key 并发只发一次）、缓存与后台刷新（staleTime/gcTime）、窗口聚焦重新拉取、分页/无限加载、乐观更新、mutation 失效联动（invalidateQueries）
> - 分工：服务端数据归 React Query；纯客户端状态（UI 开关、表单草稿、本地偏好）归 useState/Zustand；Redux 只在需要严格单向数据流+时间旅行的场景保留
> - 迁移效果常见收益：删掉大量「请求 loading/error/handoff」样板代码和手写缓存逻辑

### 29. React Router 6 相比 5 的关键变化？loader 数据加载怎么用？｜中级

> 🎯 关键要点
> - 嵌套路由 `createBrowserRouter` + `<Outlet/>` 替代 Switch/嵌套 Route 渲染 props；路由成为对象配置而非 JSX 树
> - loader：路由级数据加载，导航开始就并发取数，`useLoaderData` 直接消费——消除「先渲染空壳再 effect 里取数」的双跳水
> - action：配合 `<Form>` 做数据变更 + revalidate；`useNavigation` 暴露 pending 状态做 loading UI
> - 相对路径导航、`useNavigate` 替代 useHistory；错误边界 `errorElement` 按路由分段捕获

### 30. 什么是 React Server Components？它改变了什么？｜高级

> 🎯 关键要点
> - RSC：组件在服务端运行，输出序列化后的 RSC Payload（不是 HTML），客户端按需组合渲染
> - 能力：Server Component 可直接访问数据库/文件系统/密钥，产物不进客户端 bundle——数据获取零瀑布、零 JS 成本
> - 区分规则：'use client' 标记客户端组件边界；Server 组件不能有 state/事件/浏览器 API；客户端组件可以 import 服务端组件作 children
> - 交互边界思维：把「静态展示 + 数据获取」留在服务端，只有真正需要交互的最小叶子才 'use client'，bundle 体积断崖式下降
> - 生态：Next.js App Router 是主流实现，配合 Suspense 做流式传输（streaming + selective hydration）

## Vue基础（10题）

### 31. Vue 3 的响应式系统是如何工作的？与 Vue 2 有什么区别？｜高级

> 🎯 关键要点
> - Vue 3 基于 Proxy：读取时 track（收集当前副作用函数到 target→key→effects 的依赖桶），修改时 trigger（取出依赖重新执行），惰性代理、按需追踪
> - Vue 2 基于 Object.defineProperty：初始化时递归遍历所有属性做 getter/setter 拦截，开局成本高且先天缺陷多
> - Vue 2 的限制（Vue 3 全部解决）：无法检测属性新增/删除（需要 Vue.set/Vue.delete）、数组索引直接赋值与 length 修改不触发更新、Map/Set 不支持
> - Proxy 的取舍：支持全类型对象与动态属性，但嵌套对象是访问时才代理（惰性），且无法被 polyfill（这是放弃 IE 的直接原因）

```js
import { reactive, ref, computed } from 'vue';
const state = reactive({ count: 0, user: { name: '张三' } });
const count = ref(0);                    // 原始值需要 ref 包装
const double = computed(() => count.value * 2);
state.newProp = 'x';                     // 动态新增：Vue3 直接响应，Vue2 需要 $set
const arr = reactive([1, 2, 3]);
arr[0] = 100;                            // 索引赋值：Vue3 直接响应，Vue2 失效
```

### 32. v-if 和 v-show 的区别？｜初级

> 🎯 关键要点
> - v-if：真实的条件渲染——切换时销毁/重建组件与 DOM，有编译层优化（分支不进渲染函数），初始条件为假时不渲染
> - v-show：始终渲染，只是切换 `display: none`，初始一定渲染，切换零销毁成本
> - 选择：高频切换用 v-show（如 tab 切换）；条件大概率不变、组件树重、含初始化副作用用 v-if
> - 组合规则：v-if 可以和 v-for 同标签时优先级不同（Vue 3 中 v-if 优先，Vue 2 中 v-for 优先），但两者同标签本身就是坏味道，用 computed 过滤代替

### 33. computed、watch、watchEffect 三者怎么选？｜中级

> 🎯 关键要点
> - computed：由其他响应式数据「派生」值，有缓存（依赖不变不重算），必须同步返回值，禁止副作用——模板显示、过滤排序首选
> - watch：显式声明「监听谁、做什么」，支持 deep/immediate/flush 选项，可拿到新旧值，适合异步副作用（请求、localStorage 写入）
> - watchEffect：立即执行一次并自动收集回调内用到的依赖，代码更短，但依赖是隐式的、拿不到旧值，多个响应式源时不如 watch 显式可读
> - 陷阱：watch 监听 reactive 对象整体时自动 deep；监听 reactive 的属性要写 getter 函数 `() => obj.key`，直接传属性值是监听一个普通值

### 34. Vue 3 组合式 API 的生命周期钩子与选项式如何对应？onMounted 何时触发？｜初级

> 🎯 关键要点
> - 对应关系：beforeCreate/created → setup 本身；mounted → onMounted；updated → onUpdated；unmounted → onUnmounted；beforeUnmount → onBeforeUnmount
> - 没有组合式版本的：errorCaptured 有（onErrorCaptured），但 activated/deactivated（keep-alive）对应 onActivated/onDeactivated 都有——注意 setup 里没有 beforeRouteEnter 等路由内联守卫
> - onMounted 在组件 DOM 挂载完成后触发；父组件 mounted 晚于所有子组件 mounted（和选项式一致）
> - 请求放 onMounted 还是 setup 直接发：setup 同步执行时组件未必挂载，直接发请求反而更早开始，非 DOM 依赖的逻辑不必等 mounted

### 35. Vue 3 模板编译做了哪些优化？patchFlag 和 Block Tree 是什么？｜高级

> 🎯 关键要点
> - 编译期分析模板结构，给动态节点打 patchFlag（TEXT/CLASS/PROPS 等位标记），运行时 diff 只比对被标记的字段，跳过静态部分
> - Block Tree：把嵌套结构中的动态节点「拍平」收集进 block 的 dynamicChildren 数组，diff 时直接遍历这个扁平数组，不再递归整棵树
> - 静态提升（hoistStatic）：纯静态节点/属性提升到 render 函数外只创建一次；大段连续静态内容直接 innerHTML 缓存
> - 效果：更新时 diff 复杂度从「整棵树全比对」降到「只碰动态节点」，模板写法反而比手写 JSX 在 Vue 中更快（Vue 的 JSX 拿不到这些编译期信息）
> - cacheHandler 缓存事件处理器，避免内联函数每次渲染创建新引用导致子组件无效更新

### 36. ref 和 reactive 的区别？解构会丢响应式吗？｜中级

> 🎯 关键要点
> - reactive：Proxy 代理对象，只能包对象类型；ref：内部包一层 `{ value }` 的 RefImpl，通过 value 的 getter/setter 收集触发，任何类型都能包
> - ref 需要写 `.value`；模板中自动解包，但嵌套在普通对象/数组里不解包，reactive 里会解包
> - 解构 reactive 对象会丢失响应式——解构出来的是当时快照的原始值，脱离了 Proxy 追踪；修复用 `toRefs(obj)` 或 `toRef(obj, 'key')`
> - 官方风格建议：组合式函数统一返回 ref（解构友好、类型清晰）；reactive 适合聚合一组强相关状态，不要跨函数传递后解构

```js
const state = reactive({ count: 0 });
let { count } = state;      // ❌ 丢了响应式，count 是普通数字
const { count } = toRefs(state); // ✅ count 仍是 ref
```

### 37. v-model 在组件上是怎么实现的？Vue 3 支持多个 v-model 吗？｜中级

> 🎯 关键要点
> - 本质是语法糖：`v-model="title"` 展开为 `:modelValue="title"` + `@update:modelValue="title = $event"`（Vue 3）；Vue 2 是 value/input 对
> - Vue 3 支持参数化 v-model：`v-model:title="t"` `v-model:content="c"`，一个组件双向绑定多个字段，替代了 Vue 2 的 .sync 修饰符
> - 修饰符处理：`v-model.trim/.number/.lazy` 会作为 `modelModifiers` prop 传入组件内自行实现
> - 组件内正确姿势：props 接收 modelValue，不能直接改 props——通过 `emit('update:modelValue', v)` 回传；表单库通常做 computed get/set 包装

### 38. 为什么 Vue 3 废弃了 mixin？组合式函数好在哪？｜中级

> 🎯 关键要点
> - mixin 三宗罪：来源不明（模板里用到的方法不知道来自哪个 mixin）、命名冲突静默覆盖（合并策略隐晦）、属性类型不安全（this 上凭空出现的字段 TS 无法推断）
> - 组合式函数（composable）：普通函数 `useXxx()`，调用即使用——来源显式（看 import）、命名在解构时可重命名、类型自然推断、依赖关系（参数传递）一目了然
> - 逻辑组织差异：选项式按「选项类型」切割代码（一个功能的 data/methods/watch 分散四处），组合式按「功能」聚合，复杂组件可读性质变
> - 迁移建议：mixin 逐步改写为 composable，全局 mixin（影响所有组件）改为 provide/inject 或显式引入

### 39. 作用域插槽的原理是什么？slot 上为什么能拿到子组件数据？｜高级

> 🎯 关键要点
> - 普通插槽：父组件传「渲染结果」，在父作用域编译；作用域插槽：父组件传「函数 `(scope) => VNode`」，子组件渲染时把自己的数据作为参数调用这个函数
> - 所以作用域插槽本质是「参数化的渲染函数」——这就是为什么它的编译作用域仍在父组件，却能消费子组件运行时数据
> - 编译产物：子组件把 `$slots.default` 存为函数，渲染时 `slots.default({ item, index })` 调用
> - 性能注意：作用域插槽让父组件内容随子组件渲染，打破「子组件更新不影响插槽内容」的优化，Vue 3 中非作用域插槽内容被编译为函数后缓存

```vue
<!-- 子组件 MyList -->
<ul>
  <li v-for="(item, i) in items" :key="item.id">
    <slot :item="item" :index="i">{{ item.name }}</slot>
  </li>
</ul>
<!-- 父组件 -->
<MyList :items="list">
  <template #default="{ item, index }">
    <strong>{{ item.name }}</strong>（第 {{ index }} 项）
  </template>
</MyList>
```

### 40. nextTick 的原理是什么？为什么修改数据后立刻读 DOM 拿到旧值？｜中级

> 🎯 关键要点
> - Vue 的更新是异步批处理的：响应式变更只把渲染 effect 排进队列（去重），在同一轮微任务里统一 flush——所以同步代码里 DOM 还没更新
> - nextTick 把回调推入当前 flush 之后的微任务队列，保证在 DOM 更新完成后执行；实现基于 Promise.then（降级 MutationObserver/setTimeout）
> - 批处理收益：一轮事件里改 100 次状态只渲染 1 次
> - 场景：读取更新后的 DOM 尺寸、操作新生成的节点、 mounted 里依赖「父组件传入后才出现的 DOM」的初始化
> - Vue 3 更优解：`await nextTick()` 写法；而 useLayoutEffect 同类需求（绘制前测量）在 Vue 里用 onUpdated 或 flush: 'post' 的 watchEffect

## Vue响应式（8题）

### 41. 详细讲讲 Proxy 依赖收集的完整链路：track、trigger、effect 如何协作？｜高级

> 🎯 关键要点
> - 数据结构：`WeakMap<target, Map<key, Set<effect>>>`——WeakMap 保证对象被回收时依赖随之释放；Set 内 effect 去重
> - track：get 拦截时，若当前存在「正在运行的副作用」（activeEffect），把 activeEffect 存入 target→key 的依赖集合
> - trigger：set 拦截时取出该 key 的依赖集合执行；区分 add/delete 与 set（新属性只通知 iterate 依赖），数组区分索引与 length 联动
> - 防无限循环：effect 执行前拷贝依赖集合并 cleanup（删除所有自身依赖），执行中重新收集——解决「分支条件变化导致的过期依赖」
> - activeEffect 的切换由 effect 栈管理，支持嵌套 effect（这也是 computed 能嵌套的原因）

> 🔍 追问
> - 「为什么用 WeakMap 不用 Map？」——Map 强引用会阻止响应式对象被 GC，长期运行的应用会内存泄漏

### 42. 为什么需要 ref？直接用 reactive 包所有数据不行吗？｜中级

> 🎯 关键要点
> - reactive 基于 Proxy，只能代理对象类型——对 number/string/boolean 等原始值无法拦截赋值（原始值按值传递，引用丢失）
> - ref 用对象包装 `{ value }`，靠 value 的存取器实现任意类型的响应式；组合式函数返回 ref 也让解构不丢响应式
> - ref 内部对对象类型会自动调用 reactive 深层代理（`ref({a:1}).value.a` 仍是响应式）
> - unref/isRef 工具函数统一处理「可能是 ref 的值」；模板自动解包规则是高频出错点（数组/Map 中嵌套的 ref 不解包）

### 43. shallowRef / shallowReactive 什么时候用？｜高级

> 🎯 关键要点
> - shallow 系列只代理第一层：`shallowReactive` 的嵌套对象变更不触发更新；`shallowRef` 只在 `.value` 整体替换时触发
> - 典型场景一：大型不可变数据（地图实例、ECharts option、第三方类实例）——深层代理开销大且第三方对象被 Proxy 包装后可能行为异常
> - 典型场景二：整体替换式状态管理——`list.value = [...list.value, item]` 每次替换引用，不需要深层追踪
> - 配合 `triggerRef` 手动强制触发；大列表性能优化常见手段：shallowRef + 不可变更新
> - 陷阱：混用深层修改与 shallowRef 会「改了但不更新」，团队要统一状态更新风格

### 44. Vue 3 是如何让数组和 Map/Set 保持响应式的？｜中级

> 🎯 关键要点
> - 对数组：拦截 `includes/indexOf/lastIndexOf`（找不到时用原始对象再查一遍，解决代理对象与原始值比较不等的问题）；重写 push/pop/shift/unshift/splice——它们会同时读写 length 与索引，直接调用会重复触发，先暂存 paused 状态避免双重 track/trigger
> - 对 Map/Set：Proxy 原生支持，拦截 get 转发到 `Reflect.get` 并对迭代方法（forEach/keys/values/entries、size）做 track
> - 与 Vue 2 对比：索引赋值 `arr[0] = x`、`arr.length = 0` 都直接响应，不再需要 Vue.set
> - 注意：Object.freeze 的数据不做响应式代理（Vue 检测后直接返回原对象），大批只读数据可用此跳过代理成本

### 45. effect 的 cleanup 与嵌套问题怎么解决？｜高级

> 🎯 关键要点
> - 过期依赖问题：`if (a) use(b) else use(c)`——条件分支切换后，旧分支的依赖（b）已不再需要，不 cleanup 会导致无效更新
> - 解法：每次 effect 重新执行前先把它从所有旧依赖集合中删除（cleanup），执行过程中重新 track——保证依赖集始终精确匹配本次执行实际读取的数据
> - 嵌套 effect：单变量 activeEffect 会被内层覆盖导致外层依赖收集错乱；解法是 effect 栈（effectStack），执行时入栈、结束出栈，track 时取栈顶
> - computed 的 dirty 标记建立在 effect cleanup 之上：依赖变化只标脏不立即重算，读取时才真正执行（惰性求值）

### 46. computed 为什么能缓存？依赖不变时怎么做到不重算？｜高级

> 🎯 关键要点
> - computed 内部是一个带 dirty 标记的特殊 effect：依赖变更时 trigger 只把 dirty 置为 true（不立即执行求值函数）
> - 下次读取 `.value` 时检查 dirty：true 才执行求值并重新收集依赖，false 直接返回缓存值——惰性求值 + 脏检查
> - 与 watch 的区别：watch 是「数据变就执行回调」（推模式），computed 是「读取时按需计算」（拉模式），没人读取就完全不执行
> - 关键约束：getter 必须是纯函数且同步返回；在 getter 里改状态、发请求都是错误用法
> - Vue 3.4+ 优化：依赖级脏检查（valueIsChanged 比较），上游变了但值没变时下游 computed 不再连锁失效

### 47. watch 的 flush: 'pre' | 'post' | 'sync' 分别什么时机执行？｜中级

> 🎯 关键要点
> - pre（默认）：组件更新前执行——回调里读 DOM 拿到的是旧状态；大多数「监听数据做请求」场景
> - post：组件更新后执行——需要读取更新后的 DOM 时用；等价于把 watchEffect 换成 watchPostEffect
> - sync：数据变更立即同步执行（不再批处理）——只有需要逐次感知每次变更（如自实现输入同步）才用，高频触发有性能风险
> - deep 与 immediate 语义：deep 递归追踪对象内部（大对象慎用）；immediate 让回调在创建时先执行一次（替代「初始化 + watch」二段式）
> - 多个源监听：`watch([a, b], ([na, nb]) => {})` 数组形式，一次 watcher 管理 N 个源

### 48. Vue 2 的 defineProperty 响应式具体有哪些缺陷？各举一个触发案例｜中级

> 🎯 关键要点
> - 对象新增属性不响应：`obj.newKey = 1` → 需要 `Vue.set(obj, 'newKey', 1)`，因为 defineProperty 只能劫持「初始化时已存在」的属性
> - 数组索引与 length：`arr[5] = x`、`arr.length = 0` 不触发——defineProperty 按索引逐个定义成本过高，Vue 2 选择重写 7 个变异方法（push/pop/shift/unshift/splice/sort/reverse）折中
> - 初始化成本：data 里所有属性递归 defineProperty，大对象首屏开销明显；Vue 3 Proxy 是访问时才代理（惰性）
> - Map/Set 无法劫持；getter 里动态条件导致依赖漏收的边界问题
> - 本质对比：defineProperty 劫持「属性」，Proxy 劫持「对象的全部操作」（get/set/has/deleteProperty/iterate），能力位差一个量级

## Vue组件（6题）

### 49. Vue 组件通信的所有方式，各自适用场景？｜中级

> 🎯 关键要点
> - 父→子：props；子→父：emit；这两者是默认正道
> - 跨层级：provide/inject（适合组件库/主题/深层注入，业务代码慎用——隐式耦合难追踪）；Pinia 全局状态（跨页面共享）
> - 兄弟/任意组件：共同父级中转（简单场景）；事件总线 mitt（Vue 3 移除 $on/$off 后需第三方库，小型工具场景）；Pinia（正式项目）
> - 模板引用：ref + defineExpose（命令式，调用子组件方法）；v-model（表单双向）
> - 选择原则：数据流向清晰优先——props/emit > Pinia > provide/inject > mitt；能用单向数据流就不要用双向总线

### 50. keep-alive 的实现原理是什么？LRU 缓存策略怎么做的？｜高级

> 🎯 关键要点
> - keep-alive 是抽象组件：不渲染真实 DOM，缓存 vnode 到 Map（key → vnode），命中缓存直接复用缓存组件实例，跳过重新创建
> - 生命周期：被缓存的组件激活/失活触发 onActivated/onDeactivated，而不是销毁重建；所以缓存组件不会触发 mounted/unmounted
> - LRU 策略：缓存数量超 max 时淘汰「最久未访问」的条目——访问时把 key 移到最新位置（删除再插入），淘汰取最旧
> - include/exclude 按组件 name 过滤缓存范围；配合 router-view 缓存页面状态（表单草稿、滚动位置）
> - 陷阱：缓存组件里的定时器/事件监听不会自动清理，要在 onActivated/onDeactivated 里挂载/卸载，否则后台组件持续耗资源

### 51. 异步组件 defineAsyncComponent 怎么用？和路由懒加载什么关系？｜中级

> 🎯 关键要点
> - `defineAsyncComponent(() => import('./Heavy.vue'))`：组件在真正渲染时才加载 chunk，Vue 内部处理加载/加载中/失败重试三态
> - 配置项：loadingComponent（加载中占位）、errorComponent（失败占位）、delay（延迟显示 loading 防闪烁）、timeout（超时报错）、retry 次数
> - Vue Router 的路由懒加载 `component: () => import(...)` 内部就是异步组件机制，路由切换触发 chunk 请求
> - 场景：重型图表/编辑器/弹窗按需加载；与 Suspense 搭配可以做更优雅的加载边界

### 52. Teleport 解决什么问题？挂到 body 后样式和上下文怎么处理？｜中级

> 🎯 关键要点
> - 问题：Modal/Toast/下拉面板写在深层组件里，受父级 `overflow: hidden`、`transform`、z-index 层叠上下文影响，fixed 定位失效或被裁剪
> - Teleport 把渲染结果「传送」到指定容器（`to="body"` 或任意选择器），组件逻辑状态仍在原组件树中，props/emit 正常工作
> - 样式问题：scoped 样式仍生效（编译期 scope id 跟着走）；但依赖父级的后代选择器样式会断——弹窗样式要自包含
> - `disabled` 属性可以动态关闭传送（回落到原位置）；多个 Teleport 按顺序 append，可用 order 控制挂载次序
> - 搭配：Transition 包裹 Teleport 做进出场动画；SSR 下用 `Teleport` 的 SSR 支持避免水合警告

### 53. transition 组件的工作原理是什么？｜中级

> 🎯 关键要点
> - 在元素插入/移除时机的 DOM 节点上自动添加/移除过渡 class（v-enter-from → v-enter-active → v-enter-to，离开同理），过渡结束后移除
> - 过渡时机侦测：监听 transitionend/animationend，或显式传 `duration`；JavaScript 钩子（@before-enter 等）配合 GSAP 做 JS 动画
> - 列表过渡 `<TransitionGroup>`：给每个子项加 key，移动用 `v-move` class（FLIP 技术：First-Last-Invert-Play，先记录新旧位置再 transform 回去）
> - 模式：`mode="out-in"/"in-out"` 控制进出场顺序；appear 处理首次渲染过渡
> - 注意：必须有单一根元素和稳定 key；display:none 与 v-show 也能触发过渡

### 54. 如何设计一个高质量的可复用业务组件？｜高级

> 🎯 关键要点
> - API 设计三原则：数据下行用 props（含类型与默认值）、事件上行用 emit 且事件名语义化、扩展点用插槽——做到「不改源码能满足 80% 变化」
> - 受控/非受控双模式：内部维护非受控默认值，同时支持 `v-model` 外部接管；表单类组件是标配
> - 组合优于配置：props 数量超过 ~10 个是坏味道，用插槽/作用域插槽把「每项怎么渲染」的控制权交给使用者，避免配置爆炸
> - 样式边界：不依赖外部 DOM 结构（防止 Teleport/scoped 断裂）、CSS 变量暴露可定制项、组件根不写死布局（宽高交给使用方）
> - 工程配套：Props/Emits/Expose 类型完整导出、文档示例、边界用例测试（空数据/超长文本/极端宽度）

## Vue生态（4题）

### 55. Pinia 相比 Vuex 4 好在哪？核心概念有哪些变化？｜中级

> 🎯 关键要点
> - 去掉 mutation：直接改 state 或在 action 里改——简化心智负担，DevTools 依然能追踪（基于 Proxy 记录）
> - 天然模块化：每个 store 独立定义、按需引入，没有 Vuex 的 modules 嵌套与命名空间问题；store 之间可以互相引用组合
> - 完整 TS 支持：state/getters/actions 全链路类型推断，不需要 Vuex 那套复杂的泛型包装
> - 两种写法：Options Store（state/getters/actions 对应 data/computed/methods）与 Setup Store（组合式函数风格，更灵活可复用 composable）
> - 插件生态兼容：持久化插件 pinia-plugin-persistedstate、SSR 支持内建

```js
// Setup Store 写法
export const useCartStore = defineStore('cart', () => {
  const items = ref([]);
  const total = computed(() => items.value.reduce((s, i) => s + i.price, 0));
  function add(item) { items.value.push(item); }
  return { items, total, add };
});
```

### 56. Vue Router 4 的路由守卫体系怎么用？如何做权限控制？｜中级

> 🎯 关键要点
> - 三层守卫：全局（beforeEach/beforeResolve/afterEach）→ 路由独享（beforeEnter，写进路由配置）→ 组件内（onBeforeRouteUpdate/onBeforeRouteLeave）
> - 完整执行顺序：beforeRouteLeave（离开组件）→ 全局 beforeEach → beforeEnter（目标路由）→ beforeRouteEnter → 全局 beforeResolve → 导航确认 → afterEach → DOM 更新 → beforeRouteEnter 的 next 回调
> - 权限控制实践：登录态在全局 beforeEach 拦截重定向；动态路由用 `router.addRoute()` 按角色注册；返回 false/cancel 取消导航，返回路由对象执行重定向
> - 注意：动态添加路由后当前地址不会自动匹配，需要 `router.replace` 一次；beforeRouteEnter 没有 this（组件未创建），通过 next(vm => {}) 访问实例

### 57. Nuxt 3 的渲染模式和自动导入了解吗？｜高级

> 🎯 关键要点
> - 渲染模式按路由可配：SSR（默认）/ SSG（`nuxt generate`）/ ISR（routeRules 里 revalidate）/ SPA（ssr: false），混合渲染用 routeRules 按路径精确指定
> - 自动导入：components/composables/utils 目录及 Nuxt API（useFetch/useAsyncData）无需 import——基于扫描生成类型声明，开发效率高但要防「来源不明」滥用
> - useAsyncData/useFetch：服务端执行一次、payload 序列化传给客户端、水合时不重复请求——这是 SSR 数据获取的正确姿势，比 onMounted 里 fetch 早且不闪
> - Nitro 服务端引擎：server/api 目录写接口，同一仓库全栈开发；文件路由约定（pages 目录即路由）
> - 部署形态：输出为 Node 服务、静态托管或边缘函数（Cloudflare/Vercel Edge），一套代码多形态

### 58. Vite 为什么快？和 Webpack 的本质区别是什么？｜中级

> 🎯 关键要点
> - Dev 阶段：Webpack 要先把全量模块打包成 bundle 再启动；Vite 直接起一个 dev server，按浏览器原生 ESM 请求「按需编译」——访问哪个文件编译哪个，启动与模块数解耦
> - 依赖预构建（esbuild）：node_modules 的 CJS 包提前用 Go 编译器转 ESM 并合并请求，快一个数量级
> - HMR：精确到模块的热替换，改一个文件只重编译它自己，不受项目规模影响
> - 生产构建：Vite 用 Rollup（未来 Rolldown）做 tree-shaking 更优的打包，与 dev 的双引擎差异曾是痛点，Rolldown 目标是统一
> - 本质区别一句话：Webpack 是「打包优先」，Vite 是「原生 ESM 优先 + 按需编译」

## 框架对比（10题）

### 59. React 和 Vue 有什么主要区别？什么场景选哪个？｜中级

> 🎯 关键要点
> - 更新机制根本差异：React 是「推」模型——setState 默认从根重渲染（靠 memo 手动挡）；Vue 是「拉」+ 细粒度——响应式系统精确知道哪个组件的哪个依赖变了，组件级精准更新
> - 心智模型：React 是 UI = f(state) 的函数式心智，一切皆 JS（JSX）；Vue 是模板 + 响应式的心智，渐进式、官方全家桶（Router/Pinia/DevTools）统一
> - 生态：React 社区更大、方案更多但需要选型（路由/数据请求/状态管理各挑）；Vue 官方方案齐全、少纠结，中文生态好
> - TypeScript：React 更成熟；Vue 3 组合式 API 后大幅改善，模板内类型支持靠 Volar
> - 选型建议：团队熟悉度 > 项目需求 > 生态偏好——React 适合大型复杂应用与 RN 跨端；Vue 适合快速交付、中后台与渐进迁移

| 维度 | React | Vue |
|------|-------|-----|
| 更新粒度 | 默认子树重渲染 | 组件级精准更新 |
| 语法 | JSX（全 JS 能力） | 模板 + 可选 JSX |
| 响应式 | 不可变 state + 显式 setState | Proxy 自动追踪 |
| 官方全家桶 | 社区方案为主 | Router/Pinia 官方统一 |
| 学习曲线 | 概念少但约束弱 | 上手快、约定强 |

### 60. React、Vue 2、Vue 3 的 diff 算法有什么区别？｜高级

> 🎯 关键要点
> - 共同前提：都放弃了跨层移动（跨层视为删除+重建），复杂度从 O(n³) 降到 O(n)
> - React：单向遍历（从左到右），.old vs .new 依次比对，节点移动时只向后插——最坏多一次移动，但实现简单；React 18 仍是单端 + key 复用
> - Vue 2：双端比较——新旧列表各设头尾四个指针，头头、尾尾、头尾、尾头四种比对都命中就复用，命中不了的乱序部分再建 key→index 映射；多数真实场景（往中间插/反转）命中率高，移动次数少
> - Vue 3：双端思想 + 最长递增子序列（LIS）——先处理头尾（patchKeyedChildren 前置/后置预处理），中间乱序部分用 LIS 算出「不需要动的最长稳定序列」，只移动其余节点，移动次数理论最优
> - 面试表达要点：先讲 O(n) 前提，再讲三种策略的取舍——React 简单可靠、Vue2 双端均衡、Vue3 LIS 极致优化，背后都是「移动 DOM 成本远高于比对」的认知

### 61. 同样是「父组件改一个状态」，React 和 Vue 各自重渲染多少东西？｜高级

> 🎯 关键要点
> - React：state 变更 → 该组件及其整个子树默认全部重新执行渲染函数（即使 props 没变），靠 memo/useMemo 手动建立屏障；JSX 不可变重建，成本在「重算」
> - Vue：响应式系统在依赖收集阶段就记录了「哪个组件的 render effect 读了哪个数据」，更新时只触发受影响的组件重渲染，props 未变的子组件直接跳过
> - 结果：React 的优化思路是「默认多算，手动少算」；Vue 是「默认少算，深挖模板优化」（patchFlag/block tree 进一步只比动态节点）
> - 连带讨论：React 的/hooks 心智成本 vs Vue 的 Proxy 运行时开销；两者都在向对方学习（React Compiler 自动记忆化、Vapor Mode 去虚拟 DOM）

> 🔍 追问
> - 「Vue 3 Vapor Mode 是什么？」——编译时生成直接操作 DOM 的代码，跳过虚拟 DOM，对标 Solid.js 的细粒度更新

### 62. 模板和 JSX 的取舍怎么看？｜中级

> 🎯 关键要点
> - 模板：约束换取优化空间——语法固定所以编译器可静态分析（Vue 3 的 patchFlag/静态提升都建立在模板可静态分析上）；上手快、结构一目了然、设计师可读
> - JSX：图灵完备的表达力——复杂条件/动态组件/高阶抽象更顺手；类型推断更自然（TS 体验好）；但编译器无法静态优化
> - 团队维度：模板对新人友好、review 时结构清晰；JSX 对有 React 经验的团队零成本
> - Vue 双修是常态：常规业务组件用模板吃编译优化，复杂动态渲染（递归树、表格引擎）局部用 JSX/渲染函数
> - 不要把「哪个更强」当结论，答案是「在各自框架内的适用边界」

### 63. React Hooks 的依赖数组 vs Vue 的自动依赖收集，怎么评价？｜高级

> 🎯 关键要点
> - React：组件是每次重新执行的函数，无状态留存于执行过程——hooks 只能靠「显式声明依赖」让运行时知道何时重跑 effect。代价是依赖数组心智负担 + 手写错误（依赖遗漏）是 bug 重灾区
> - Vue：setup 只执行一次，后续更新由响应式系统在 effect 内自动追踪——依赖是运行时真实读取的数据，不需要声明，天然准确
> - 依赖数组不是缺陷是约束：它保证了可重复执行性，也换来 React Compiler 自动记忆化的可能性；Vue 的自动追踪则要求所有读取必须经过 Proxy（脱离追踪的写法会静默失效）
> - 工程视角：React 靠 eslint 插件兜底依赖正确性；Vue 靠约定（避免解构、统一 ref 访问）保证追踪完整性——两种框架的「易错点」正好互为镜像

### 64. Redux Toolkit 和 Pinia 的设计哲学差异？｜中级

> 🎯 关键要点
> - RTK：不可变 + 单向数据流是铁律——createSlice 内置 Immer 让你「写可变代码、产出不可变结果」；dispatch action → reducer 纯函数，一切变更可追溯可时间旅行
> - Pinia：可变直改（响应式系统天然支持），没有 action 之外的第二条变更通道，依赖 Proxy 自动追踪而非手动 dispatch
> - 心智差异：RTK 用「纪律」换可预测性（状态变更必须显式声明意图）；Pinia 用「响应式」换简洁（读改即生效）
> - 生态位：RTK 自带 RTK Query 管服务端状态；Pinia 管客户端状态，服务端状态通常交 TanStack Query（Vue Query）
> - 选型其实跟框架绑定：React 团队选 Zustand/RTK，Vue 团队选 Pinia，跨框架哲学之争意义大于实操意义

### 65. React 和 Vue 的 TypeScript 体验差在哪？｜中级

> 🎯 关键要点
> - React：函数组件即函数，props 泛型、hooks 泛型推断天然；JSX 是 TS 一等公民，社区类型生态最全
> - Vue 3：组合式 API 全链路推断（defineProps 泛型、ref/computed 类型自动推导）；模板内的类型检查靠 Volar（vue-tsc）实现——体验已接近 React，但模板表达式类型覆盖仍弱于纯 TSX
> - 差距点：Vue 的 SFC 需要独立工具链支持（编辑器插件、vue-tsc 构建）；复杂泛型组件（Table 列定义）在模板里表达不如 TSX 自然
> - 实践建议：逻辑复杂、类型要求高的组件库/工具组件用 TSX 写；页面级业务组件用 SFC

### 66. React Native 与 uni-app / Weex 这类跨端方案怎么选？｜初级

> 🎯 关键要点
> - React Native：JS 写逻辑 + 原生组件渲染（新架构 Fabric/TurboModules），性能与原生体验好，生态成熟；要求会 React
> - uni-app：Vue 语法一套代码出多端（App/小程序/H5），小程序生态支持是强项；性能依赖各端实现，深度原生能力需插件开发
> - Flutter 虽非本题主角但常被拿来对比：自绘引擎不依赖原生控件，一致性最好，包体较大、Dart 语言门槛
> - 选型逻辑：目标端决定方案——需要多端覆盖（含小程序）选 uni-app/Taro；只有 App 且团队是 React 选 RN；强图形/一致 UI 选 Flutter
> - 别忽略维护成本：跨端方案的「一套代码」理想很美，「一套代码处处踩坑」是常态，评估团队对目标端的熟悉度权重最高

### 67. 大型团队选型 React 还是 Vue，你的论证框架是什么？｜高级

> 🎯 关键要点
> - 论证维度一：团队现状——现有技术栈、招聘市场供给（React 岗位与人才池更大）、团队学习成本曲线
> - 论证维度二：业务形态——中后台/多端小程序生态偏 Vue 系（Element Plus/uni-app）；全球化产品、复杂交互、RN 需求偏 React
> - 论证维度三：工程约束——TS 严格程度、微前端方案（qiankun 对两者都友好）、组件库与设计系统沉淀
> - 结论表达：没有客观最优，只有约束下的最优；给出决策矩阵并明确「如果 X 条件成立就选 Y」的条件式结论，比站队更有说服力
> - 反模式：用「社区热度」当唯一论据——热度不等于匹配你的业务与团队

### 68. 一个应用一半 React 一半 Vue，如何渐进迁移或共存？｜高级

> 🎯 关键要点
> - 微前端是共存主线：qiankun/single-spa 把子应用按技术栈隔离，各自独立构建部署，主应用做容器与路由分发；Web Components 做跨框架组件封装是更轻的路线
> - 共存代价要讲清：样式隔离（shadow DOM/scoped 前缀）、公共依赖重复加载（externals + 共享依赖）、全局事件/Context 不互通、路由拼接
> - 渐进迁移策略：新页面用目标框架写，旧页面按业务模块逐步改写，微前端容器兜底过渡期；设定迁移完成时间线，避免「永久共存」变成技术债固化
> - 备选方案：iframe 隔离（简单粗暴，通信与体验差，内部低频系统可接受）；Module Federation 共享运行时（Webpack/Vite 支持，依赖版本管理复杂）
> - 决策前提：先问「为什么必须共存」——如果重写成本可控，直接统一技术栈比长期共存便宜

## 状态管理（12题）

### 69. 请解释 Redux 的工作原理，以及如何在 React 中使用 Redux？｜高级

> 🎯 关键要点
> - 核心概念：Store（单一状态树）、Action（描述变更的普通对象 `{type, payload}`）、Reducer（`(state, action) => newState` 纯函数）、Dispatch（触发变更的唯一入口）
> - 三原则：单一数据源、状态只读（只能 dispatch 改）、变更只能由纯函数 reducer 完成
> - 数据流：组件 dispatch(action) → 中间件处理副作用 → reducer 计算新状态 → store 通知订阅者 → connect/useSelector 的组件按需重渲染
> - React 绑定：Provider 注入 store；useSelector 订阅切片（引用未变则不重渲染）；useDispatch 取派发函数

```js
const todosReducer = (state = [], action) => {
  switch (action.type) {
    case 'ADD_TODO': return [...state, action.payload];
    case 'TOGGLE_TODO':
      return state.map(t => t.id === action.payload.id
        ? { ...t, done: !t.done } : t);
    default: return state; // 未知 action 必须返回原 state
  }
};

function TodoList() {
  const todos = useSelector(s => s.todos);
  const dispatch = useDispatch();
  return <button onClick={() => dispatch(addTodo('新任务'))}>添加</button>;
}
```

> 🔍 追问
> - 「为什么 reducer 必须是纯函数？」——可预测（同输入同输出）、可时间旅行调试、可对比新旧引用做更新优化

### 70. Redux Toolkit 相比传统 Redux 简化了什么？｜中级

> 🎯 关键要点
> - createSlice：一个函数定义 state + reducers + 自动生成 action creators 与 action types，消灭 actionType 常量与手写 switch 的样板
> - 内置 Immer：reducer 里直接「可变」写法（state.push(item)），Immer 代理产出正确的不可变新状态——不可变规则保留，心智负担卸掉
> - configureStore：一站式组装（默认集成 thunk 中间件 + DevTools），替代手写 createStore/applyMiddleware/compose
> - RTK Query：服务端状态层，自动缓存/去重/失效/重取，对标 React Query
> - 迁移现实：RTK 解决的是「样板代码劝退」问题，Redux 的核心价值（可预测、可调试）全部保留

### 71. Redux 中间件的工作原理是什么？thunk 和 saga 怎么选？｜高级

> 🎯 关键要点
> - 中间件本质：对 dispatch 的洋葱式包装——`store.dispatch` 被逐层增强，异步 action 到达 store 前先被中间件拦截处理
> - 实现核心三行：中间件是 `({getState, dispatch}) => next => action => ...` 的三层柯里化，compose 串联；next 是下一个中间件，最后落到原生 dispatch
> - redux-thunk：action 可以是函数， `(dispatch, getState) => {...}` 里自由写异步——简单直接，适合大部分场景
> - redux-saga：用 generator 把副作用抽成独立 saga（take/effect 模型），支持任务取消、竞态（takeLatest）、复杂编排（并行/竞速/轮询）；学习成本高，适合复杂异步流
> - 选型：简单异步 thunk，复杂流程（长事务、多请求编排、取消）saga；新项目更多直接 RTK Query/TanStack Query 收编请求类副作用

### 72. Zustand / Jotai 的原子化思想是什么？为什么比 Redux 轻量？｜高级

> 🎯 关键要点
> - Zustand：一个 store 就是一个 hook，`create(set => ...)` 生成；组件通过 selector 订阅——只有 selector 结果变化才重渲染，天然精准更新，无需 Provider
> - Jotai：状态拆成原子（atom），atom 之间可组合派生，组件订阅各自用到的 atom——依赖关系自动追踪，彻底消灭「一个字段变了整棵树渲染」
> - 与 Redux 的哲学差异：Redux 中心化单 store + 显式 action 流水线（强审计需求）；原子化去中心化 + 直接 setter（灵活优先）
> - 性能根源：订阅粒度从「组件声明」细化到「数据片段」，不再需要 memo/useSelector 的 selector 纪律
> - 适用边界：中小型应用 / 需要脱离 Context 性能陷阱时首选；需要严格变更审计、时间旅行、大型团队协作规范时 Redux 体系仍有价值

### 73. MobX 的响应式和 Redux 的单向数据流，本质区别是什么？｜高级

> 🎯 关键要点
> - MobX：可变状态 + 自动依赖追踪（observable/computed/action），数据改了相关视图自动精准更新——「透明响应式」，和 Vue 同源思想
> - Redux：不可变状态 + 显式派发，所有变更走 action→reducer 管道，可审计可回放——「受控数据流」
> - 对比维度：样板代码（MobX 极少）、变更追踪（Redux 全显式 vs MobX 隐式）、时间旅行（Redux 原生支持，MobX 需要额外约束）、团队规范（Redux 强约定防乱改，MobX 依赖自觉 action）
> - 心智风险：MobX 的隐式依赖在大型团队可能出现「没人知道谁在改这个状态」的问题；Redux 的显式性换来的是协作确定性
> - 结论表达：两者不是性能之争而是「可控性 vs 简洁性」的取舍，选择跟随团队规模与工程文化

### 74. 为什么出现了 TanStack Query / SWR 这类「服务端状态」库？它和客户端状态的区别是什么？｜高级

> 🎯 关键要点
> - 服务端状态的特性：数据的真实来源在服务端、会过期、有并发修改者（别人也在改）、需要缓存与重取策略——这些都不是 Redux 这类客户端状态容器的设计目标
> - 用 Redux 管服务端数据的传统痛点：手写 loading/error、手动缓存失效、重复请求、竞态、聚焦重取、分页去重——全是重复劳动且容易漏
> - TanStack Query 提供：以 queryKey 为粒度的缓存、staleTime/gcTime 双时钟（新鲜度 + 垃圾回收）、窗口聚焦/断网重连自动重取、mutation 后 invalidateQueries 精准失效、乐观更新
> - 架构启示：把状态分成「服务端状态（缓存问题）」与「客户端状态（一致性/交互问题）」两类，分别用专门工具，是现代前端的默认架构
> - 迁移路径：请求类逻辑从 Redux/手写 hooks 迁出后，剩下的真正的客户端状态往往少到 useState/Zustand 就够

### 75. 大型应用的状态应该怎么分层设计？｜高级

> 🎯 关键要点
> - 第一层 URL 状态：可分享、可回退的状态（筛选条件、分页、tab）——放 URL query，不进任何 store
> - 第二层 服务端状态：TanStack Query/SWR 的缓存，生命周期跟着数据走
> - 第三层 全局客户端状态：跨页面共享且低频变化（登录用户、权限、主题、全局配置）——Zustand/Pinia/Redux，宁少勿多
> - 第四层 组件本地状态：默认归属，只有出现共享需求才上提——「提升前先质疑」
> - 反模式：一股脑全塞全局 store（Redux 烂大街的原因）；分层判断题是「谁消费、谁失效、要不要回退分享」，每个状态独立作答

> 🔍 追问
> - 「表单草稿放哪层？」——本地优先；需要跨页恢复才提到 sessionStorage 或服务端草稿接口，别进全局 store

### 76. Context 做状态管理有什么陷阱？订阅式状态库怎么解决的？｜中级

> 🎯 关键要点
> - 陷阱一：广播式更新——Context value 变化，所有 useContext 消费者无条件重渲染，无法按字段订阅
> - 陷阱二：value 引用不稳定——未 memo 的内联对象让每次父渲染都触发全量消费组件更新
> - 陷阱三：Provider 拆分爆炸——为了减少无效更新不得不拆一堆 Provider，嵌套地狱
> - 订阅式方案（Zustand/Jotai/redux 的 useSelector）：状态存组件树外（模块级单例），组件通过 selector + 引用比较自行决定是否重渲染，更新粒度精确到「我订阅的切片变了」
> - Context 的正确定位：低频变化的「配置类」数据（主题、locale、当前用户），高频数据交给订阅式方案

### 77. Pinia 的 store 怎么组织与组合？setup store 的最佳实践？｜中级

> 🎯 关键要点
> - 按「领域」拆 store（cart/user/order），不按「页面」拆——页面 store 会导致跨页共享时互相引用成网
> - store 间组合：一个 store 的 action 里直接 `useOtherStore()` 调用（Pinia 官方支持，避免循环引用用函数内延迟获取）
> - Setup store 写法：ref → state、computed → getters、function → actions，返回它们；组合式函数（composable）可直接复用进 store——这是 Pinia 与 Composition API 的化学反应
> - 生命周期：store 是单例，组件卸载不销毁；需要「会话级重置」写 $reset（setup store 要手写）或显式恢复初始值
> - SSR 注意：每个请求新建 pinia 实例防串状态；有副作用的状态初始化放 action 而不是模块顶层

### 78. 为什么 Redux 要求状态不可变、reducer 必须纯函数？｜中级

> 🎯 关键要点
> - 可预测性：纯函数「同输入必同输出、无副作用」，任何状态变更都可由 action 序列完整重放——时间旅行调试、热重载保持状态都建立在这之上
> - 更新检测：不可变更新让「是否变化」的判断退化为引用比较（===），selector/memo 才能廉价跳过无关重渲染；深比较的成本和正确性都不可接受
> - 并发安全：Redux 18 的并发渲染要求 render 阶段不产生副作用，不可变数据天然免疫「渲染中状态被篡改」的撕裂问题
> - 代价与缓解：手写不可变更新繁琐易错（嵌套深了展开地狱）——Immer 让你写可变语法自动产出不可变结果
> - 面试表达：这三条原因分别对应「调试、性能、并发」三个层面，能分层说清楚才是理解而非背诵

### 79. 状态持久化怎么做才可靠？｜中级

> 🎯 关键要点
> - 选存储介质：localStorage（同步、5MB 上限、无过期）、sessionStorage（会话级）、IndexedDB（大容量/异步/结构化）、Cookie（需要服务端读取的凭证）
> - 写入策略：节流持久化（别每次变更都写）、只持久化「白名单切片」（登录态、偏好、草稿），列表大对象不入 localStorage
> - 版本迁移：持久化数据带 version 字段，读取时按版本做迁移函数链（v1→v2→v3）——没有版本号，结构变更后旧数据会把新代码搞崩
> - 敏感数据：token 长期放 localStorage 有 XSS 窃取风险，优先 httpOnly Cookie；必须在本地存的做最小化与过期清理
> - 一致性：恢复时校验结构（try/catch + schema 校验），损坏数据直接丢弃重置而不是让应用启动崩溃

### 80. 描述一个你经历过的状态管理架构演进案例：什么信号驱动了重构？效果怎么衡量？｜高级

> 🎯 关键要点
> - 演进信号：① store 单文件膨胀（几千行、改一处全应用重渲染）；② 请求状态散落各处手写且互相不一致；③ Context 广播导致的莫名卡顿；④ 新人上手成本（action 流水线太长）
> - 典型路径：Redux 全家桶 → 拆分（服务端状态迁 TanStack Query，客户端状态瘦身）→ 全局 store 只剩用户/权限 → 组件本地化
> - 重构策略：绞杀者模式——新模块用新方案、老模块按修改频率渐进迁移，设置完成里程碑而非「一次性大重构」
> - 衡量指标：请求相关代码行数下降比例、Profiler 下的重渲染次数、bundle 里状态库体积、新人独立开发首个需求的周期
> - 面试表达关键：讲「判断依据」而不只是「用了什么」——架构决策的价值在于为什么这个时机、为什么这个方案、怎么验证它成功了
