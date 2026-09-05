---
title: "DeepSeek Harness (DSH) 架构设计文档"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 架构设计文档"
collected: "2026-09-05"
status: "imported"
---

DeepSeek Harness (DSH) 架构设计文档
开源项目
MIT License
DeepSeek Harness (DSH) 架构设计文档
DeepSeek AI 开源的智能 Agent 框架，采用"全插件化"设计理念，基于 Cordis 插件框架构建
技术栈:
TypeScript 6.0+
运行时:
Node.js ≥22.19
包管理:
pnpm monorepo
构建工具:
Vite
目录导航
第一部分：整体架构
1. 整体架构概览
2. 核心模块职责
3. 依赖关系图
深度剖析
4. Cordis 框架
5. 插件系统
6. Session 生命周期
高级主题
7. 沙箱安全模型
8. 并发处理
9. 扩展性设计
10. 错误处理
11. 性能分析
12. 竞品对比
13. 演进方向
1
整体架构与核心模块
1. 整体架构概览
DeepSeek Harness (DSH) 是 DeepSeek AI 开源的智能 Agent 框架，采用"全插件化"设计理念，将所有功能（包括 Agent 循环本身）都设计为可替换的插件。基于 Cordis 插件框架构建，代码完全开源（MIT 协议）。
🏗️
全插件化架构
所有功能都是可替换的插件，包括 Agent 循环本身，实现高度可定制化
💉
依赖注入
基于 Cordis 框架的 IoC 容器，自动管理服务依赖和生命周期
🔄
热重载支持
文件变更时自动重载插件，无需重启，事务性保护确保一致性
🔒
安全隔离
多层沙箱安全模型，包括进程隔离、文件系统隔离和 Landlock 机制
系统分层架构
DSH 采用清晰的分层架构，从底层到顶层分为四个主要层次：
Application Layer
CLI App
Web App
Headless
↓
Profile Layer
dsh-base
dsh-web-app
dsh-headless
↓
Bundle Layer
LLM
Tools
Session
↓
Core Services
Agent
Agent Loop
Context
↓
Cordis Framework
Service
Fiber
Events
核心数据流
用户输入
→
Session 事件日志
→
Agent 循环
→
模型请求
→
工具调用
→
结果返回
→
会话更新
2. 核心模块职责和边界
设计原则
每个模块都有清晰的职责边界，通过 Cordis 事件系统进行通信，避免直接依赖，实现松耦合设计。
2.1 core/agent - Agent 核心逻辑
职责：
定义 Agent 的公共接口和运行时类型
实现
AgentRegistry
服务管理进程内所有活跃 Agent 的生命周期
承载 Inbox（输入队列）和消息处理逻辑
提供
agent/*
事件（inbox、step、status、request 等）
interface
Agent
{
  ctx:
Context
;
// Agent 的 Cordis 上下文
inbox:
Message
[];
// 输入消息队列
status:
AgentStatus
;
// 运行状态
}
class
AgentRegistry
extends
Service
{
register
(agent:
Agent
):
Disposable
;
get
(id:
string
):
Agent
|
undefined
;
}
2.2 core/session - 会话管理
职责：
维护只追加的
SessionEvent
日志（会话事件流）
实现会话的创建、持久化、投影和标题生成
提供会话分叉（Fork）和恢复（Resume）能力
type
SessionEvent
= 
  | { type:
'turn/start'
; timestamp:
number
}
  | { type:
'user/message'
; content:
string
}
  | { type:
'assistant/message'
; content:
string
}
  | { type:
'tool/call'
; name:
string
; args:
any
}
  | { type:
'tool/result'
; result:
any
}
2.3 llm - 模型抽象层
职责：
定义模型适配器接口（Service Definition）
管理多个 LLM Provider 的注册和发现
支持多种模型提供商（DeepSeek、OpenAI 等）
3. 依赖关系图
DSH 的模块依赖关系遵循清晰的层次结构，通过以下策略避免和解决循环依赖：
📡
事件驱动解耦
模块间通过 Cordis 事件系统通信，而不是直接方法调用
🔌
接口隔离
每个模块定义清晰的接口，消费方只依赖接口，不依赖具体实现
💉
依赖注入
通过 Cordis 的 inject 声明依赖，框架自动处理解析和生命周期
📊
分层架构
严格遵守层次边界，上层可以依赖下层，下层不能依赖上层
核心依赖关系
Agent
依赖
LLM
（模型调用）、
Tools
（工具执行）、
Session
（状态管理）
Session
依赖
Context
（事件系统）、
FS
（持久化存储）
LLM
依赖
Context
（服务注册）、
Config
（配置管理）
Tools
依赖
Context
（工具注册）、
Sandbox
（安全执行）
4
Cordis 依赖注入框架深度剖析
Cordis 是 DSH 的基石，一个只有约 2000 行 TypeScript 的元框架，却支撑了 Koishi（4000+ 插件的聊天机器人框架）和 DeepSeek Harness 两个重量级项目。
4.1 IoC 容器的实现
Cordis 的 IoC 容器基于
Context
类实现，通过 Proxy 实现透明的服务访问：
// Context 使用 Proxy 实现透明访问
const
handler:
ProxyHandler
<
Context
> = {
get
(target, prop, receiver) {
// 服务访问
if
(
typeof
prop ===
'string'
&& !prop.startsWith(
'_'
)) {
const
service = target.get(prop);
if
(service !==
undefined
) {
return
service;
      }
    }
return
Reflect.get(target, prop, receiver);
  }
};
4.2 Fiber 生命周期状态机
每个被加载的插件实例都对应一个 Fiber，管理着该插件的完整生命周期：
状态
含义
何时进入
PENDING
等待依赖
所需服务尚未就绪
LOADING
正在加载
apply 函数正在执行
ACTIVE
正常运行
apply 已成功完成
UNLOADING
正在卸载
正在执行 disposers
DISPOSED
已卸载
所有清理已完成
FAILED
加载失败
发生异常
5. 插件系统的运行机制
5.1 插件加载流程
配置解析
→
依赖图构建
→
拓扑排序
→
实例化
→
激活
5.2 热重载机制
热重载特性
文件监控：使用 chokidar 监控文件变更，支持 glob 模式
防抖处理：避免频繁重载
事务性保护：新代码加载失败时自动回滚
副作用自动清理：旧插件的 disposers 按注册逆序执行
6. Session 生命周期管理
6.1 Session 状态机
状态
含义
可转换到
CREATED
已创建，未开始
ACTIVE, TERMINATED
ACTIVE
正在运行
PAUSED, SUSPENDED, COMPLETED, FAILED, TERMINATED
PAUSED
已暂停
ACTIVE, TERMINATED
COMPLETED
正常完成
-
FAILED
执行失败
ACTIVE, TERMINATED
6.2 状态持久化策略
📝
事件日志
只追加的 SessionEvent 数组，支持重放和审计
📸
状态快照
定期保存完整状态，减少重放时间
📋
元数据
会话配置、用户信息等辅助数据
7
沙箱安全模型
DSH 实现了多层安全防护，确保代码执行的安全性和隔离性。
7.1 多层安全架构
🔒
进程级隔离
每个会话在独立进程中运行，使用 Linux 命名空间隔离
📁
文件系统隔离
使用 chroot 或类似技术限制访问范围
🛡️
Landlock 安全
Linux 内核安全模块，实现细粒度的文件系统访问控制
👤
权限控制
最小权限原则，基于角色的访问控制（RBAC）
8. 并发和异步处理模型
8.1 任务调度策略
协作式调度
：任务主动让出控制权
优先级调度
：基于任务重要性分配资源
公平调度
：确保所有任务都能执行
8.2 资源管理
资源类型
计算资源
：CPU、内存
网络资源
：API 调用、带宽
存储资源
：磁盘空间、数据库连接
9. 扩展性设计
9.1 添加新子系统的步骤
定义接口
→
实现提供方
→
创建消费者
→
注册插件
9.2 事件系统
DSH 的事件系统支持五种分发模式：
模式
是否 await
分发顺序
典型用途
emit
否
注册顺序
广播通知
waterfall
否
注册顺序
中间件/拦截器
parallel
是
并行
并发扇出
serial
是
注册顺序
顺序决策
bail
否
注册顺序
短路判断
10. 错误处理和容错机制
10.1 错误分类
🔄
可恢复错误
网络超时、API 限流、临时资源不足
❌
不可恢复错误
配置错误、依赖服务不可用、安全违规
👤
用户错误
无效输入、权限不足、资源不存在
10.2 容错机制
重试机制
：指数退避重试
降级策略
：主逻辑失败时使用备用方案
熔断机制
：防止级联故障
状态持久化
：支持从断点恢复
11. 性能关键路径分析
11.1 瓶颈识别
模型调用延迟
：LLM API 响应时间、网络延迟、限流等待
工具执行开销
：文件系统操作、外部 API 调用
状态管理开销
：事件日志序列化、状态快照创建
11.2 优化策略
⚡
并行化
使用 Promise.all 并行执行多个工具调用
💾
缓存
多级缓存策略，减少重复计算和 API 调用
📦
资源池
连接池管理，复用昂贵的资源创建
12
与竞品的架构对比
12.1 vs LangGraph
维度
DeepSeek Harness
LangGraph
架构模式
全插件化，基于 Cordis
图结构，状态机驱动
依赖管理
IoC 容器，自动依赖解析
手动依赖管理
扩展性
插件热重载，动态替换
需要重新编译图
状态管理
事件日志，只追加
状态快照，可修改
适用场景
复杂 Agent 系统，需要高度定制
流程明确的 Agent 工作流
12.2 vs CrewAI
维度
DeepSeek Harness
CrewAI
定位
通用 Agent 框架
多 Agent 协作框架
架构
底层框架，高度可定制
高层抽象，快速开发
通信机制
事件驱动
消息传递
适用场景
需要精细控制的 Agent 系统
快速构建多 Agent 应用
13. 架构演进方向和建议
13.1 短期改进（0-6 个月）
性能优化
：实现更高效的事件日志存储，优化模型调用批处理
开发者体验
：提供更好的调试工具，完善文档和示例
生态建设
：建立插件市场，提供官方插件模板
13.2 中期发展（6-18 个月）
分布式支持
：实现分布式会话管理，支持多节点 Agent 协作
企业级功能
：增加审计日志，实现细粒度权限控制
多模态扩展
：支持图像、音频、视频处理
13.3 长期愿景（18+ 个月）
自主 Agent
：实现长期记忆和学习，支持目标驱动的自主决策
社会化 Agent
：实现 Agent 间协作协议，支持 Agent 社会和规范
通用智能框架
：支持多种 AI 范式，实现跨领域知识整合
总结
DeepSeek Harness 代表了 Agent 框架设计的先进方向，其全插件化架构、基于 Cordis 的依赖注入、事件驱动的设计模式，为构建复杂、可扩展、可维护的 Agent 系统提供了坚实的基础。
DeepSeek Harness (DSH) 架构设计文档
GitHub 仓库
官方文档
社区论坛
↑