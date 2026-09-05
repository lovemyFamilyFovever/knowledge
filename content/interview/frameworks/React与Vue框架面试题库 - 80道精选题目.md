---
title: "React与Vue框架面试题库 - 80道精选题目"
tags: []
source: "baike"
source_path: "技术题库 / React与Vue框架"
collected: "2026-09-05"
status: "imported"
---

React与Vue框架面试题库 - 80道精选题目
React与Vue框架
80道精选面试题 | 涵盖组件设计、状态管理、性能优化等
⚛️ React 40题
💚 Vue 40题
💡 240+回答模板
🎯 框架对比
⚛️ React基础
🪝 React Hooks
⚡ React性能
📦 React生态
💚 Vue基础
🔄 Vue响应式
🧩 Vue组件
📦 Vue生态
⚔️ 框架对比
📊 状态管理
⚛️ React基础（15题）
1
请解释React中的虚拟DOM（Virtual DOM）是什么？它如何提升性能？
中等
React核心概念
虚拟DOM
性能优化
diff算法
展开答案
💡 回答模板一：概念解释型
"虚拟DOM是React在内存中维护的一个轻量级的DOM表示。当组件状态改变时，React会创建新的虚拟DOM树，通过diff算法与旧的虚拟DOM进行比较，计算出最小的DOM操作集合，然后批量更新真实DOM。
                            
                            性能提升原理：
                            1. 减少不必要的DOM操作：DOM操作代价较高，虚拟DOM通过比较只更新变化的部分
                            2. 批量更新：将多次状态变化合并为一次DOM更新
                            3. 声明式编程：让React优化渲染过程
                            4. 跨平台：虚拟DOM可以渲染到不同平台（Web、Native等）
                            
                            React使用高效的diff算法（Reconciliation），时间复杂度为O(n)，通过以下策略优化：
                            - 不同类型的元素会产生不同的树
                            - 通过key属性标识哪些元素在不同渲染中是稳定的"
// 虚拟DOM示例
function App() {
  const [count, setCount] = useState(0);
  
  return (
计数器: {count}
setCount(count + 1)}>
        增加
);
}

// React内部处理流程：
// 1. 状态改变 (setCount)
// 2. 创建新的虚拟DOM树
// 3. 与旧的虚拟DOM比较 (Reconciliation)
// 4. 计算最小DOM操作
// 5. 批量更新真实DOM
💡 回答模板二：实际应用型
"在实际项目中，我深刻体会到虚拟DOM的价值。我们有一个复杂表单页面，用户输入会频繁触发重渲染。
                            
                            优化措施：
                            1. 使用React.memo避免不必要的重渲染
                            2. 使用useMemo缓存计算结果
                            3. 使用useCallback缓存函数引用
                            4. 合理拆分组件，减少重渲染范围
                            
                            这些优化让页面性能提升了40%以上，特别是在低端设备上效果明显。虚拟DOM的核心思想是'预测性优化'，让框架替我们处理底层的DOM操作。"
💡 面试提示
这个问题考察你对React核心原理的理解。回答时要结合实际项目经验，展示你不仅知道概念，还能在实际场景中应用。如果提到diff算法的具体策略，会显得更专业。
2
JSX是什么？它与HTML有什么区别？
简单
React语法
JSX
语法
展开答案
💡 回答模板一：基础概念型
"JSX是JavaScript的语法扩展，允许我们在JavaScript中编写类似HTML的结构。它不是HTML，而是JavaScript对象（React元素）。
                            
                            JSX与HTML的主要区别：
                            1. 属性名：
                            - HTML: class, for, tabindex
                            - JSX: className, htmlFor, tabIndex
                            
                            2. 事件处理：
                            - HTML: onclick="handleClick()"
                            - JSX: onClick={handleClick}
                            
                            3. 内联样式：
                            - HTML: style="color: red"
                            - JSX: style={{ color: 'red' }}
                            
                            4. 自闭合标签：
                            - HTML:
,
- JSX:
,
5. 条件渲染：
                            - HTML: 无直接支持
                            - JSX: 使用JavaScript表达式"
// JSX示例
function App() {
  const name = 'React';
  const isLoggedIn = true;
  
  return (
{/* 注释 */}
Hello, {name}!
{/* 条件渲染 */}
      {isLoggedIn ? (
欢迎回来！
) : (
请登录
)}
      
      {/* 列表渲染 */}
{[1, 2, 3].map(item => (
{item}
))}
{/* 内联样式 */}
红色文字
);
}
🪝 React Hooks（12题）
1
请解释React Hooks的工作原理，以及为什么需要Hooks？
困难
Hooks核心
Hooks
状态管理
副作用
展开答案
💡 回答模板一：基础概念型
"React Hooks是React 16.8引入的特性，允许在函数组件中使用状态和其他React特性。
                            
                            为什么需要Hooks：
                            1. 复用状态逻辑：在组件之间共享状态逻辑
                            2. 复杂组件变简单：将生命周期逻辑拆分为更小的函数
                            3. 使用class的困惑：this绑定、生命周期方法等
                            4. 更好的TypeScript支持：函数组件更容易类型推断
                            
                            常用Hooks：
                            - useState：状态管理
                            - useEffect：副作用处理
                            - useContext：Context使用
                            - useRef：引用DOM或保存可变值
                            - useMemo：缓存计算结果
                            - useCallback：缓存函数引用
                            
                            Hooks的工作原理基于链表结构，每次渲染时按顺序调用Hooks。"
// Hooks基础示例
import { useState, useEffect, useCallback } from 'react';

function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // 副作用：获取用户数据
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await fetch(`/api/users/${userId}`);
        const data = await response.json();
        setUser(data);
      } catch (error) {
        console.error('获取用户失败:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchUser();
  }, [userId]); // 依赖数组
  
  // 缓存函数引用
  const handleRefresh = useCallback(() => {
    setLoading(true);
    // 重新获取数据
  }, []);
  
  if (loading) return
加载中...
;
  
  return (
{user?.name}
{user?.email}
刷新
);
}
💚 Vue基础（15题）
1
Vue 3的响应式系统是如何工作的？与Vue 2有什么区别？
困难
Vue核心
响应式
Proxy
Vue 3
展开答案
💡 回答模板一：基础概念型
"Vue 3的响应式系统基于Proxy实现，替代了Vue 2的Object.defineProperty。
                            
                            Vue 3响应式原理：
                            1. 使用Proxy拦截对象的get和set操作
                            2. 自动收集依赖（track）
                            3. 数据变化时自动触发更新（trigger）
                            4. 支持动态新增/删除属性
                            5. 支持Map、Set等数据结构
                            
                            与Vue 2的区别：
                            1. 实现方式：Proxy vs Object.defineProperty
                            2. 性能：Proxy是惰性代理，按需拦截
                            3. 支持的数据结构：Proxy支持更多
                            4. 初始化性能：Vue 3更优
                            5. 内存占用：Vue 3更少
                            
                            Vue 2的限制：
                            - 无法检测属性添加/删除
                            - 无法检测数组索引修改
                            - 需要Vue.set/Vue.delete"
// Vue 3响应式示例
import { reactive, ref, computed } from 'vue';

// 使用reactive创建响应式对象
const state = reactive({
  count: 0,
  user: {
    name: '张三',
    age: 25
  }
});

// 使用ref创建响应式引用
const count = ref(0);

// 计算属性
const doubleCount = computed(() => count.value * 2);

// 修改数据会自动触发更新
function increment() {
  state.count++;
  count.value++;
}

// 访问响应式数据
console.log(state.user.name); // 自动收集依赖
console.log(count.value);     // 需要.value访问

// Vue 2的限制在Vue 3中解决
const arr = reactive([1, 2, 3]);
arr[0] = 100; // 可以直接修改数组索引

const obj = reactive({});
obj.newProp = 'new'; // 可以动态添加属性
⚔️ 框架对比（8题）
1
React和Vue有什么主要区别？在什么场景下选择哪个框架？
中等
框架选型
React
Vue
对比
展开答案
💡 回答模板一：全面对比型
"React和Vue的主要区别：
                            
                            1. 学习曲线：
                            - Vue：更平缓，模板语法直观，适合初学者
                            - React：JSX需要适应，但更灵活
                            
                            2. 状态管理：
                            - Vue：内置响应式系统，简单直接
                            - React：需要setState或Hooks，更显式
                            
                            3. 生态系统：
                            - React：更大更成熟，选择更多
                            - Vue：官方解决方案更统一
                            
                            4. 性能：
                            - 两者性能相当，都使用虚拟DOM
                            - Vue 3性能优化更好
                            
                            5. TypeScript支持：
                            - React：更好，类型推断更准确
                            - Vue 3：大幅改进，但仍有差距
                            
                            场景选择：
                            - 新项目、快速开发：Vue
                            - 大型项目、复杂状态：React
                            - 团队技术栈：根据团队经验选择
                            - 需要React Native：React"
📊 状态管理（10题）
1
请解释Redux的工作原理，以及如何在React中使用Redux？
困难
状态管理
Redux
状态管理
Flux
展开答案
💡 回答模板一：基础概念型
"Redux是一个可预测的状态容器，基于Flux架构，用于管理应用状态。
                            
                            Redux核心概念：
                            1. Store：单一状态树，存储整个应用状态
                            2. Action：描述状态变化的普通对象
                            3. Reducer：纯函数，根据action计算新状态
                            4. Dispatch：触发action的方法
                            
                            工作流程：
                            1. 组件通过dispatch触发action
                            2. Reducer根据action计算新状态
                            3. Store更新状态
                            4. 订阅的组件重新渲染
                            
                            Redux原则：
                            1. 单一数据源：整个应用状态存储在单个store中
                            2. 状态只读：只能通过dispatch action改变状态
                            3. 纯函数修改：Reducer必须是纯函数"
// Redux示例
// action types
const ADD_TODO = 'ADD_TODO';
const TOGGLE_TODO = 'TOGGLE_TODO';

// action creators
const addTodo = (text) => ({
  type: ADD_TODO,
  payload: { text, completed: false }
});

// reducer
const todosReducer = (state = [], action) => {
  switch (action.type) {
    case ADD_TODO:
      return [...state, action.payload];
    case TOGGLE_TODO:
      return state.map(todo =>
        todo.id === action.payload.id
          ? { ...todo, completed: !todo.completed }
          : todo
      );
    default:
      return state;
  }
};

// 在React组件中使用
import { useSelector, useDispatch } from 'react-redux';

function TodoList() {
  const todos = useSelector(state => state.todos);
  const dispatch = useDispatch();
  
  const handleAdd = () => {
    dispatch(addTodo('新任务'));
  };
  
  return (
添加
{todos.map(todo => (
{todo.text}
))}
);
}
📚 React与Vue框架面试题库 | 80道精选题目
💡 每个问题提供2-3个回答模板，请根据实际情况选择和调整
🎯 建议：结合个人项目经验，用具体案例支撑观点
🔗
上一章：JavaScript核心
|
下一章：CSS与HTML