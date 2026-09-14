---
title: "Agent 安全与对齐"
tags: [人工智能, Agent]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Agent 安全与对齐 

> 📌 **导航**：本文是 **Agent 安全与对齐** 词条，属于 ai-and-llm 术语集（Agent 方向）。相关枢纽：[[AI Agent 概述与核心架构]]、[[Agent 架构模式详解]]、[[多 Agent 协作系统]]、[[大模型基础术语详解]]、[[RAG 与检索技术详解]]。

## 概述
Agent安全关注如何确保AI系统按照人类意图行事，避免有害行为。随着Agent自主性增强，安全问题日益重要。

## 主要安全风险

| 风险类型 | 说明 | 示例 |
|---------|------|------|
| **Prompt注入** | 恶意输入改变Agent行为 | 忽略之前的指令 |
| **工具滥用** | Agent误用工具造成危害 | 删除重要文件 |
| **数据泄露** | Agent泄露敏感信息 | 输出训练数据 |
| **过度自主** | Agent超出预期范围行动 | 未经确认的购买 |
| **社会工程** | Agent被操纵欺骗用户 | 伪造信息 |

## 防护措施

| 措施 | 说明 | 实现方式 |
|------|------|---------|
| **输入过滤** | 检测恶意输入 | 关键词/模型检测 |
| **输出审核** | 检查输出安全性 | 内容过滤器 |
| **权限控制** | 限制工具使用权限 | 白名单/沙箱 |
| **人类确认** | 关键操作需人类确认 | 审批流程 |
| **日志审计** | 记录所有操作 | 完整日志 |

## Constitutional AI
基于一组宪法原则来约束AI行为：
```python
principles = [
    "不应生成有害内容",
    "应诚实承认不确定",
    "应尊重用户隐私",
    "应拒绝非法请求",
]

def constitutional_check(response, principles, llm):
    for principle in principles:
        judgment = llm.evaluate(f"内容是否违反原则'{principle}': {response}")
        if '违反' in judgment:
            return llm.revise(response, principle)
    return response
```

## Red Teaming（红队测试）
```python
class RedTeamAgent:
    def __init__(self, target_agent):
        self.target = target_agent
        self.attack_prompts = self.load_attacks()

    def run_tests(self):
        results = []
        for prompt in self.attack_prompts:
            response = self.target.run(prompt)
            results.append({
                'attack': prompt,
                'response': response,
                'safe': self.evaluate_safety(response),
            })
        return results

    def evaluate_safety(self, response):
        # 检查是否包含有害内容
        return not self.contains_harmful(response)
```

## Agent 防护栏（Guardrails）
```python
class AgentGuardrails:
    def __init__(self):
        self.input_filters = []
        self.output_filters = []
        self.tool_restrictions = {}

    def check_input(self, user_input):
        for f in self.input_filters:
            if not f(user_input):
                raise SafetyError("输入被过滤")

    def check_tool_use(self, tool_name, args):
        if tool_name in self.tool_restrictions:
            return self.tool_restrictions[tool_name](args)
        return True

    def check_output(self, output):
        for f in self.output_filters:
            output = f(output)
        return output
```

## 小结
Agent安全需要多层防护：输入过滤、权限控制、输出审核和人类确认。Constitutional AI提供原则约束，Red Teaming持续发现漏洞。

## 相关术语

[[AI Agent 概述与核心架构]]、[[Agent 架构模式详解]]、[[Agent 规划与推理]]、[[Agent 记忆系统]]、[[Agent 评估与基准]]、[[多 Agent 协作系统]]、[[大模型基础术语详解]]、[[RAG 与检索技术详解]]、[[Prompt 工程与 Agent 详解]]

## 参考资料

建议人工核验：可参考各框架官方文档（LangChain / AutoGPT / CrewAI 等）、*AI Agents in Action* (Michael Landsman)、Anthropic 工程博客 *Building Effective Agents*，以及 OpenAI / Anthropic 官方 Agent 开发文档。
