---
title: "Douyin-Vue 项目知识图谱"
tags: []
source: "baike"
source_path: "项目分析 / 抖音Vue项目"
collected: "2026-09-05"
status: "imported"
---

Douyin-Vue 项目知识图谱
Douyin-Vue 项目知识图谱
抖音移动端短视频 Web 模仿项目 · Vue3 + Vite + Pinia 技术栈
Vue 3.5
Vite 6.4
Pinia
Vue Router 4
TypeScript
Less
Axios
120+
Vue 组件
60+
路由页面
15
API 接口
12
工具模块
📁
代码结构与逻辑
douyin/
├──
src/
│   ├──
api/
← API 接口层
│   │   ├──
user.ts
← 用户相关接口 (7个)
│   │   └──
videos.ts
← 视频相关接口 (8个)
│   ├──
assets/
← 静态资源
│   │   ├──
data/
← 数据文件 (JSON/LRC)
│   │   └──
img/
← 图片资源 (图标/头像)
│   ├──
components/
← 通用组件
│   │   ├──
dialog/
← 弹窗组件 (6个)
│   │   ├──
slide/
← 滑动组件 (12个) ★核心
│   │   └──
*.vue
← 基础UI组件
│   ├──
config/
← 配置文件
│   ├──
mock/
← Mock 数据模拟
│   ├──
pages/
← 页面模块
│   │   ├──
home/
← 首页模块
│   │   ├──
login/
← 登录模块
│   │   ├──
me/
← 个人中心模块
│   │   ├──
message/
← 消息模块
│   │   ├──
people/
← 通讯录模块
│   │   └──
shop/
← 商城模块
│   ├──
router/
← 路由配置
│   ├──
store/
← 状态管理 (Pinia)
│   └──
utils/
← 工具函数
│       ├──
request.ts
← Axios 封装
│       ├──
slide.ts
← 滑动核心逻辑 ★
│       ├──
bus.ts
← 事件总线
│       ├──
dom.ts
← DOM 操作库
│       └──
hooks/
← 组合式函数
├──
public/
← 公共静态资源
│   └──
data/
← 业务数据 (JSON/MD)
├──
node/
← 数据处理脚本
├──
env/
← 环境配置
└──
.github/
← CI/CD 配置
🏗️
系统架构与模块依赖
🧠
项目知识图谱
📦
核心模块详情
🎯
首页模块 (Home)
核心视频播放页面，实现无限滑动浏览、视频播放控制、评论互动、分享功能
包含 15 个组件 · SlideVerticalInfinite 核心
👤
个人中心 (Me)
用户资料编辑、作品管理、收藏夹、浏览历史、设置等功能
包含 18 个组件 · 多级子路由
💬
消息模块 (Message)
聊天功能、系统通知、粉丝动态、访客记录、红包详情
包含 16 个组件 · 实时消息展示
🔐
登录模块 (Login)
多种登录方式、验证码验证、密码找回、帮助中心
包含 8 个组件 · 表单验证
🛍️
商城模块 (Shop)
商品列表展示、商品详情页、瀑布流布局
包含 3 个组件 · 瀑布流列表
👥
通讯录 (People)
好友查找、关注与粉丝管理、通讯录同步、扫码、面对面
包含 6 个组件 · 社交功能
🔄
核心业务流程
视频浏览流程
用户交互流程
数据流架构
1
页面初始化
App.vue 挂载 → Router 初始化 → Store 初始化 → Mock 启动
2
首页加载
Home 组件渲染 → SlideVerticalInfinite 初始化 → 请求推荐视频数据
3
视频滑动
TouchStart → TouchMove (方向判断) → TouchEnd → 动画过渡 → 加载下一条
4
视频播放
BaseVideo 组件 → HTML5 Video → 播放控制 → 进度监听 → 循环播放
5
用户互动
双击点赞 → 评论弹窗 → 分享面板 → 关注用户 → 收藏视频
1
登录流程
选择登录方式 → 输入手机号 → 获取验证码 → 验证成功 → 进入首页
2
资料编辑
进入个人中心 → 编辑资料 → 修改昵称/头像/签名 → 保存到 Store
3
社交互动
查看关注列表 → 发送私信 → 分享内容 → 管理收藏
1
数据存储层
public/data/*.md → JSON 格式数据 → 视频/用户/评论/商品
2
Mock 拦截层
axios-mock-adapter → 拦截 API 请求 → 返回本地 JSON 数据
3
API 封装层
request.ts → Axios 实例 → 统一错误处理 → 响应格式化
4
状态管理层
Pinia Store → 用户信息/视频列表/全局配置 → 响应式更新
5
视图渲染层
Vue 组件 → 响应式数据绑定 → 虚拟 DOM → 真实 DOM 更新
⚡
技术栈与依赖
Douyin-Vue 项目知识图谱 · 自动生成于 2026-08-28
基于 Vue3 + Vite + Pinia 技术栈构建的抖音移动端 Web 模仿项目