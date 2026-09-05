---
title: "Agent 记忆系统"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Agent 记忆系统

## 概述

记忆系统是AI Agent的'大脑存储'，决定Agent能否从经验中学习、保持上下文连贯性。就像人类有工作记忆、短期记忆、长期记忆，Agent也有多层设计。

## 记忆分类

| 类型 | 容量 | 持久性 | 实现方式 | 类比 |
|------|------|--------|---------|------|
| **工作记忆** | 小 | 临时 | 上下文窗口 | 手中纸条 |
| **短期记忆** | 中 | 会话级 | 对话历史 | 今天日记 |
| **长期记忆** | 大 | 永久 | 向量DB | 图书馆 |

## 工作记忆

```python
class WorkingMemory:
    def __init__(self, max_tokens=4000):
        self.max_tokens = max_tokens
        self.items = []

    def add(self, content: str):
        self.items.append(content)
        self._truncate()

    def get_context(self) -> str:
        return '\n'.join(self.items)

    def _truncate(self):
        total = sum(len(item) for item in self.items)
        while total > self.max_tokens * 3 and self.items:
            total -= len(self.items.pop(0))
```

## 短期记忆

```python
from collections import deque

class ShortTermMemory:
    def __init__(self, max_turns=20):
        self.history = deque(maxlen=max_turns)

    def add_turn(self, role: str, content: str):
        self.history.append({'role': role, 'content': content})

    def get_recent(self, n=None):
        turns = list(self.history)
        return turns[-n:] if n else turns

    def get_summary(self, llm) -> str:
        prompt = f'请压缩以下对话为摘要:\n{self.get_recent()}'
        return llm.generate(prompt)
```

## 长期记忆

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

class LongTermMemory:
    def __init__(self, persist_dir='./memory_store'):
        self.vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=OpenAIEmbeddings(),
        )

    def store(self, content: str, metadata: dict = None):
        self.vectorstore.add_texts([content], metadatas=[metadata or {}])

    def recall(self, query: str, k: int = 5) -> list:
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return [{'content': d.page_content, 'score': s} for d, s in results]
```

## 综合记忆系统

```python
class AgentMemorySystem:
    def __init__(self, llm):
        self.working = WorkingMemory(max_tokens=4000)
        self.short_term = ShortTermMemory(max_turns=20)
        self.long_term = LongTermMemory()

    def add(self, role: str, content: str):
        self.working.add(f'{role}: {content}')
        self.short_term.add_turn(role, content)
        if len(content) > 100:
            self.long_term.store(content, {'role': role})

    def get_context(self) -> str:
        working_ctx = self.working.get_context()
        long_term_ctx = self.long_term.recall(working_ctx, k=3)
        return f'{working_ctx}\n\n相关历史:\n{long_term_ctx}'
```

## 压缩策略对比

| 策略 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| **截断** | 保留最近N条 | 简单高效 | 丢失重要信息 |
| **摘要** | LLM生成摘要 | 保留核心 | 有信息损失 |
| **滑动窗口** | 最近N个token | 平滑过渡 | 可能截断 |
| **重要性排序** | 按重要性保留 | 智能筛选 | 额外计算 |
| **层次化** | 详情→摘要分层 | 平衡详略 | 实现复杂 |

## 小结

三层记忆的协调配合，让Agent能够像人类一样'记住'过去经验并应用于当前任务。