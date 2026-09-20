---
title: "AI金项目知识图谱"
tags: []
source: "baike"
source_path: "项目分析 / 我的本地项目"
collected: "2026-09-05"
status: "imported"
---

AI金项目知识图谱
AI金项目知识图谱
不锈钢智能伙伴平台 - 项目架构与关系可视化
0
实体节点
0
关系连接
0
分类类型
6
核心模块
筛选分类：
全部显示
布局方式：
力量导向
环形布局
重置视图
技术栈知识库
点击上方图谱中的技术栈节点，或浏览下方的技术卡片，了解项目中使用的各种技术。
Vue 3
^3.5.35
核心特性：
组合式API(Composition API)、响应式系统(Proxy)、组件化开发、TypeScript支持
项目应用：
58个页面文件、37个组件文件，覆盖主应用、ERP、数据大屏三端
配套生态：
Vue Router(Hash模式)、Pinia状态管理、Element Plus UI、Lucide Icons
前端框架
响应式
组件化
TypeScript
^5.9.2
核心特性：
静态类型检查、接口定义、泛型支持、装饰器
项目应用：
前后端统一语言，shared目录共享类型定义，class-validator DTO校验
优势：
提升代码质量、IDE智能提示、重构安全性、团队协作效率
类型系统
全栈
类型安全
NestJS
^10.4.20
核心特性：
模块化架构、依赖注入、守卫/过滤器/拦截器、装饰器驱动
项目应用：
12个业务模块、RESTful API、Drizzle ORM、定时任务(@nestjs/schedule)
设计模式：
洋葱模型、控制反转(IoC)、面向切面编程(AOP)
后端框架
Node.js
模块化
PostgreSQL
Drizzle ORM
核心特性：
关系型数据库、ACID事务、JSON支持、全文检索
项目应用：
39张业务表、52个SQL迁移脚本、手工维护schema、表前缀命名规范
ORM选型：
Drizzle ORM - 类型安全、SQL优先、轻量级、无运行时开销
数据库
ORM
39张表
阿里云百炼
qwen-plus/turbo
核心能力：
大语言模型(LLM)、知识库检索、SSE流式响应、结构化图表生成
应用场景：
AI问答(双模式)、AI配单(LLM直通)、AI测价(8步思考)、AI客服、用户画像
模型选择：
qwen-turbo(快速模式)、qwen-plus(专家模式)、qwen3.7-plus(最新)
AI
LLM
大模型
Tailwind CSS
v4
核心特性：
原子化CSS、@theme语义色系统、JIT编译、响应式设计
项目规范：
定义完整语义色(brand/text/border/success/warning/danger)、禁止预设色
配套工具：
PostCSS处理、自定义tailwind.config.ts、暗色模式(预留)
样式
CSS
原子化
飞书开放平台
@lark-apaas
核心能力：
企业协作、多维表格、消息通知、Bot机器人、OAuth认证
项目集成：
飞书工作台部署、VIP数据存储(5张表)、CSRF适配、isLocal双环境
数据方案：
无DB方案，牺牲行数上限(3.8万行)换取零运维，双环境统一存储
企业
协作
多维表格
Chrome MV3
Manifest V3
核心特性：
Service Worker、Content Scripts、MAIN World注入、Native Messaging
项目应用：
内容分发助手、6平台适配、反自动化检测绕过、Cookie备份
版本适配：
Chrome 137+移除--load-extension，改为手动加载持久化方案
插件
浏览器
自动化
技术栈关系
前端
Vue 3
→
TypeScript
→
Tailwind CSS
→
Element Plus
后端
NestJS
→
TypeScript
→
Drizzle ORM
→
PostgreSQL
AI
阿里云百炼
→
qwen-plus/turbo
→
SSE流式
→
知识库
外部
51bxg
/
秀吗
→
WAF绕过
→
Proxy代理
基于项目代码仓库、上线工作计划、会议纪要自动生成
Generated on 2026-08-28