---
title: "AI Agent 技术面试题库 - 扩展部分7：大模型应用开发实战"
tags: []
source: "baike"
source_path: "技术题库 / AI Agent面试专题"
collected: "2026-09-05"
status: "imported"
---

# AI Agent 技术面试题库 - 扩展部分7：大模型应用开发实战

> 大模型应用开发实战（10 题）｜涵盖 API 使用、流式输出、对话管理、应用架构等核心领域。
> 每题标注难度（初级 / 中级 / 高级），编号 1–10 连续，附参考解答与关键要点。

## 主题1：API 开发与调用（5 题）

### 1. 如何设计一个好的 LLM API 接口？｜中级

好的 API 设计应该简洁、一致、易于使用。

**设计原则：**

- **简洁性**：参数清晰，必填项最少
- **一致性**：与其他 API 风格一致
- **可扩展**：支持未来功能扩展
- **向后兼容**：新版本兼容旧版本

```json
# 好的API设计示例
POST /v1/chat/completions
{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "你好"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": true
}
```

> 🎯 关键要点：OpenAI API 已成为事实标准。
> messages 格式支持多轮对话。
> stream 参数支持流式输出。

### 2. 如何实现流式输出（Streaming）？｜中级

流式输出逐 token 返回结果，改善用户体验。

**实现方式：**

```python
# Python实现流式输出
import openai

stream = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "你好"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

**前端处理：**

```javascript
// JavaScript处理SSE
const eventSource = new EventSource('/api/chat');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  appendToChat(data.content);
};
```

> 🎯 关键要点：流式输出显著改善用户感知延迟。
> 使用 SSE（Server-Sent Events）协议。
> 前端需要逐 token 渲染。

### 3. 如何实现多轮对话管理？｜中级

多轮对话需要维护上下文，管理对话历史。

**实现方式：**

```python
# 对话管理示例
class ConversationManager:
    def __init__(self, max_history=10):
        self.history = []
        self.max_history = max_history

    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})
        # 保持历史长度
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_messages(self):
        return [{"role": "system", "content": "你是一个助手"}] + self.history
```

**优化策略：**

- 历史摘要：压缩长对话历史
- 滑动窗口：只保留最近 N 轮
- 重要性排序：保留重要信息

> 🎯 关键要点：上下文窗口限制是主要挑战。
> 需要平衡历史长度和成本。
> 摘要压缩是常用策略。

### 4. 如何处理 LLM 的错误和重试？｜中级

LLM 调用可能遇到各种错误，需要完善的错误处理机制。

**常见错误：**

- **限流错误**：请求过多被拒绝
- **超时错误**：响应时间过长
- **服务错误**：服务器内部错误
- **内容过滤**：输出被安全过滤

```python
# 重试机制示例
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def call_llm_with_retry(prompt):
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response
    except openai.RateLimitError:
        raise  # 让tenacity处理重试
    except openai.APIError as e:
        logger.error(f"API错误: {e}")
        raise
```

> 🎯 关键要点：指数退避是常用的重试策略。
> 需要设置最大重试次数。
> 限流错误需要特别处理。

### 5. 如何优化 LLM 调用的成本？｜中级

LLM 调用成本是生产应用的重要考量。

**优化策略：**

- **缓存**：缓存相同请求的响应
- **提示压缩**：减少不必要的 token
- **模型选择**：简单任务用小模型
- **批量处理**：合并请求

```python
# 缓存实现示例
import hashlib
import redis

class LLMCache:
    def __init__(self):
        self.redis = redis.Redis()

    def get(self, prompt, model):
        key = hashlib.md5(f"{model}:{prompt}".encode()).hexdigest()
        return self.redis.get(key)

    def set(self, prompt, model, response, ttl=3600):
        key = hashlib.md5(f"{model}:{prompt}".encode()).hexdigest()
        self.redis.setex(key, ttl, response)
```

> 🎯 关键要点：缓存是最有效的成本优化手段。
> 需要根据场景选择缓存策略。
> 模型路由可以进一步降低成本。

## 主题2：应用架构设计（5 题）

### 6. 如何设计一个聊天机器人应用的架构？｜高级

**核心组件：**

```text
用户界面 → API网关 → 对话管理服务 → LLM服务
                    ↓
              ┌─────┴─────┐
              │           │
          知识库RAG    工具集成
              │           │
              └─────┬─────┘
                    ↓
              数据库/缓存
```

**设计要点：**

- 微服务架构，独立扩展
- 异步处理长时间任务
- 完善的监控和日志
- 支持多模型切换

> 🎯 关键要点：架构应该支持水平扩展。
> 对话状态需要持久化。
> 需要考虑容错和降级。

### 7. 如何实现多模型路由和降级？｜高级

多模型路由根据请求特点选择最合适的模型，降级机制保证服务可用性。

```python
# 模型路由器示例
class ModelRouter:
    def __init__(self):
        self.models = {
            "fast": "gpt-3.5-turbo",
            "balanced": "gpt-4",
            "powerful": "gpt-4-turbo"
        }

    def route(self, request):
        # 根据复杂度选择模型
        complexity = self.analyze_complexity(request)
        model = self.models.get(complexity, "gpt-3.5-turbo")

        try:
            return call_model(model, request)
        except Exception:
            # 降级到更稳定的模型
            return call_model("gpt-3.5-turbo", request)
```

> 🎯 关键要点：路由策略需要根据业务场景设计。
> 降级机制保证服务可用性。
> 需要监控各模型的性能。

### 8. 如何实现 LLM 应用的可观测性？｜中级

可观测性包括日志、指标和链路追踪三大支柱。

**日志：**

- 记录每次 LLM 调用的输入输出
- 记录 token 使用量和成本

**指标：**

- 延迟分布
- 错误率
- token 使用量

**链路追踪：**

- 跟踪请求的完整处理流程
- 识别性能瓶颈

> 🎯 关键要点：LangSmith 是 LLM 专用的可观测性平台。
> 日志需要脱敏处理。
> 实时监控是必要的。

### 9. 如何处理长文档的分块和检索？｜高级

长文档处理是 RAG 系统的核心挑战。

**分块策略：**

- 按段落/章节分块
- 固定大小 + 重叠
- 语义分块

**检索优化：**

- 混合检索（向量 + 关键词）
- 重排序（Reranking）
- 多级索引

```python
# 分块示例
def chunk_document(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks
```

> 🎯 关键要点：分块大小需要根据任务调整。
> 重叠保持上下文连续性。
> Reranking 显著提升效果。

### 10. 如何评估 LLM 应用的效果？｜中级

LLM 应用评估需要多维度、多方法综合进行。

**评估维度：**

- **准确性**：回答是否正确
- **相关性**：回答是否相关
- **完整性**：回答是否完整
- **安全性**：是否产生有害内容

**评估方法：**

- **自动评估**：使用指标自动计算
- **LLM-as-Judge**：用强模型评估
- **人工评估**：人工标注评分
- **A/B 测试**：在线对比测试

> 🎯 关键要点：评估是持续优化的基础。
> 需要建立评估数据集。
> 多种方法结合使用。
