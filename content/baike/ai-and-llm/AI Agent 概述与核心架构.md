---
title: "AI Agent 概述与核心架构"
tags: [人工智能, Agent]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# AI Agent 概述与核心架构

> 📌 **导航**：本文是 **AI Agent 概述与核心架构** 词条，属于 ai-and-llm 术语集（Agent 方向）。相关枢纽：[[AI Agent 概述与核心架构]]、[[Agent 架构模式详解]]、[[多 Agent 协作系统]]、[[大模型基础术语详解]]、[[RAG 与检索技术详解]]。

## 什么是 AI Agent

**AI Agent（人工智能代理）** 是一种能够感知环境、进行推理并自主采取行动以实现特定目标的智能系统。与传统的 AI 模型仅返回单次响应不同，Agent 能够持续与环境交互，根据反馈动态调整策略，最终完成复杂任务。

用一个通俗的类比：如果 LLM 是一位博学的「顾问」，那么 Agent 就是一位能独立执行任务的「助手」——它不仅会思考，还会动手操作。

### Agent 的三个核心能力

1. **感知能力**：接收来自环境的多种输入信号，包括文本、图像、API数据、传感器信号等
2. **推理能力**：利用大语言模型进行理解、分析、规划和决策
3. **行动能力**：通过调用工具、执行代码、发送请求等方式在环境中产生实际影响

## Agent 的核心架构——感知-推理-行动循环

AI Agent 的核心架构可以概括为 **感知-推理-行动（Perception-Reasoning-Action）** 循环。这个循环不断运转，驱动 Agent 一步步接近目标。

```
┌──────────────────────────────────────────────────┐
│                  AI Agent 核心循环                 │
│                                                   │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│   │  感知层   │ →  │  推理层   │ →  │  行动层   │   │
│   │Perception│    │Reasoning │    │ Action   │   │
│   └────┬─────┘    └──────────┘    └─────┬────┘   │
│        │          记忆系统              │         │
│        └───────── Memory ──────────────┘         │
│                    ↑ 反馈                         │
└──────────────────────────────────────────────────┘
```

| 组件 | 职责 | 典型技术 |
|------|------|----------|
| **感知层** | 接收和解析外部输入 | 文本解析、OCR、语音识别 |
| **推理层** | 基于输入进行分析和决策 | LLM推理、Chain-of-Thought |
| **行动层** | 执行具体操作 | 工具调用、代码执行、API请求 |
| **记忆系统** | 存储历史信息和上下文 | 短期记忆、长期记忆（向量DB） |
| **工具集** | 扩展 Agent 的能力边界 | 搜索引擎、计算器、代码解释器 |

## Agent 与传统 AI 的区别

| 维度 | 传统 AI 模型 | AI Agent |
|------|-------------|----------|
| **交互模式** | 单轮请求-响应 | 多轮自主交互 |
| **决策能力** | 被动响应 | 主动规划与决策 |
| **工具使用** | 无 | 可调用外部工具 |
| **环境感知** | 仅处理输入数据 | 持续感知环境变化 |
| **任务复杂度** | 单一子任务 | 端到端复杂任务 |
| **自我修正** | 无 | 可根据反馈修正行为 |
| **记忆能力** | 有限上下文 | 短期+长期记忆 |

## Agent 工作流示例

```python
class Agent:
    def __init__(self, llm, tools, memory):
        self.llm = llm
        self.tools = tools
        self.memory = memory

    def run(self, task: str) -> str:
        self.memory.add('user', task)
        while not self.is_done():
            context = self.memory.get_context()
            thought, action = self.llm.think(context, self.tools)
            if action:
                result = self.execute_tool(action)
                self.memory.add('tool_result', result)
            if self.should_finish(thought):
                return self.get_final_answer()
        return self.get_final_answer()
```

## Agent 分类体系

| 分类维度 | 类型 | 说明 |
|---------|------|------|
| **自主程度** | 半自主 / 全自主 | 是否需要人类确认 |
| **Agent 数量** | 单Agent / 多Agent | 独立工作还是协作 |
| **交互方式** | 对话式 / 任务式 | 对话驱动还是目标驱动 |
| **应用领域** | 代码 / 研究 / 办公 | 面向特定场景优化 |
| **部署位置** | 云端 / 端侧 | 服务器还是本地设备 |

## 主流 Agent 框架概览

| 框架 | 核心特点 | 适用场景 | 社区活跃度 |
|------|---------|---------|------------|
| **LangChain** | 模块化、生态丰富 | 通用Agent开发 | ★★★★★ |
| **LlamaIndex** | 数据索引和检索 | RAG和知识问答 | ★★★★☆ |
| **AutoGPT** | 全自主执行 | 探索性任务 | ★★★★☆ |
| **CrewAI** | 多Agent协作 | 团队协作任务 | ★★★★☆ |
| **LangGraph** | 图结构工作流 | 复杂有状态流程 | ★★★★☆ |
| **AutoGen** | 微软多Agent对话 | 研究和对话式任务 | ★★★★☆ |

## Agent 发展趋势

1. **从单Agent到多Agent协作**：多个专业Agent组成团队分工协作
2. **从文本到多模态**：理解图像、音频、视频
3. **从云端到端侧**：本地Agent保护隐私并降低延迟
4. **从工具使用到环境交互**：直接操作电脑、浏览器等
5. **从简单任务到长期目标**：处理数小时甚至数天的任务

## 小结

AI Agent 是 LLM 能力的自然延伸。它将语言模型的「思考」能力与工具使用、环境交互、记忆系统等「行动」能力相结合，创造出能够自主完成复杂任务的智能系统。
## AI Agent 核心架构图

<svg viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;font-family:Arial,sans-serif">
  <rect width="800" height="500" fill="#f8fafc" rx="12"/>
  <text x="400" y="35" text-anchor="middle" font-size="20" font-weight="bold" fill="#1e293b">AI Agent 核心架构</text>
  <rect x="50" y="60" width="150" height="80" rx="10" fill="#dbeafe" stroke="#3b82f6" stroke-width="2"/>
  <text x="125" y="95" text-anchor="middle" font-size="14" font-weight="bold" fill="#1e40af">感知模块</text>
  <text x="125" y="115" text-anchor="middle" font-size="11" fill="#3b82f6">文本/图像/语音</text>
  <text x="125" y="130" text-anchor="middle" font-size="11" fill="#3b82f6">工具返回结果</text>
  <rect x="300" y="60" width="200" height="80" rx="10" fill="#fef3c7" stroke="#f59e0b" stroke-width="2"/>
  <text x="400" y="95" text-anchor="middle" font-size="14" font-weight="bold" fill="#92400e">LLM 推理引擎</text>
  <text x="400" y="115" text-anchor="middle" font-size="11" fill="#b45309">规划 / 推理 / 决策</text>
  <text x="400" y="130" text-anchor="middle" font-size="11" fill="#b45309">Chain-of-Thought</text>
  <rect x="600" y="60" width="150" height="80" rx="10" fill="#dcfce7" stroke="#22c55e" stroke-width="2"/>
  <text x="675" y="95" text-anchor="middle" font-size="14" font-weight="bold" fill="#166534">行动模块</text>
  <text x="675" y="115" text-anchor="middle" font-size="11" fill="#15803d">API调用 / 代码执行</text>
  <text x="675" y="130" text-anchor="middle" font-size="11" fill="#15803d">工具使用</text>
  <rect x="250" y="200" width="300" height="80" rx="10" fill="#f3e8ff" stroke="#a855f7" stroke-width="2"/>
  <text x="400" y="235" text-anchor="middle" font-size="14" font-weight="bold" fill="#6b21a8">记忆系统 (Memory)</text>
  <text x="400" y="255" text-anchor="middle" font-size="11" fill="#7c3aed">短期记忆(上下文) | 长期记忆(向量库) | 工作记忆</text>
  <rect x="100" y="330" width="600" height="60" rx="10" fill="#fce7f3" stroke="#ec4899" stroke-width="2"/>
  <text x="400" y="360" text-anchor="middle" font-size="14" font-weight="bold" fill="#9d174d">工具箱 (Tools)</text>
  <text x="400" y="378" text-anchor="middle" font-size="11" fill="#be185d">搜索引擎 | 代码执行 | 数据库查询 | API调用 | 文件操作 | 浏览器</text>
  <defs><marker id="ah" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0,10 3.5,0 7" fill="#64748b"/></marker></defs>
  <line x1="200" y1="100" x2="300" y2="100" stroke="#64748b" stroke-width="2" marker-end="url(#ah)"/>
  <line x1="500" y1="100" x2="600" y2="100" stroke="#64748b" stroke-width="2" marker-end="url(#ah)"/>
  <path d="M 675 140 L 675 170 L 125 170 L 125 140" stroke="#64748b" stroke-width="2" fill="none" marker-end="url(#ah)"/>
  <text x="400" y="185" text-anchor="middle" font-size="11" fill="#64748b">环境反馈循环</text>
  <line x1="400" y1="140" x2="400" y2="200" stroke="#a855f7" stroke-width="2" marker-end="url(#ah)"/>
  <line x1="400" y1="280" x2="400" y2="330" stroke="#ec4899" stroke-width="2" marker-end="url(#ah)"/>
  <text x="400" y="430" text-anchor="middle" font-size="13" fill="#475569">感知 → 推理 → 行动 → 反馈 → 感知（循环执行直到完成任务）</text>
</svg>

## 相关术语

[[AI Agent 概述与核心架构]]、[[Agent 架构模式详解]]、[[Agent 规划与推理]]、[[Agent 记忆系统]]、[[Agent 评估与基准]]、[[多 Agent 协作系统]]、[[大模型基础术语详解]]、[[RAG 与检索技术详解]]、[[Prompt 工程与 Agent 详解]]

## 参考资料

建议人工核验：可参考各框架官方文档（LangChain / AutoGPT / CrewAI 等）、*AI Agents in Action* (Michael Landsman)、Anthropic 工程博客 *Building Effective Agents*，以及 OpenAI / Anthropic 官方 Agent 开发文档。
