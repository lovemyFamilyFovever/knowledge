---
title: "Function Calling 与 Tool Use"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Function Calling 与 Tool Use

## 概述

**Function Calling** 和 **Tool Use** 是让 LLM 从'只会说话'变为'能做事情'的关键技术。LLM 可以自动选择合适的工具、构造参数、执行并整合结果。

## OpenAI Function Calling

```python
from openai import OpenAI
import json

client = OpenAI()
tools = [
    {
        'type': 'function',
        'function': {
            'name': 'get_weather',
            'description': '获取指定城市的当前天气',
            'parameters': {
                'type': 'object',
                'properties': {
                    'city': {'type': 'string', 'description': '城市名称'},
                },
                'required': ['city']
            }
        }
    }
]

messages = [{'role': 'user', 'content': '北京天气怎么样？'}]
response = client.chat.completions.create(
    model='gpt-4o', messages=messages, tools=tools, tool_choice='auto',
)

message = response.choices[0].message
if message.tool_calls:
    for tc in message.tool_calls:
        func_args = json.loads(tc.function.arguments)
        result = get_weather(**func_args)
        messages.append(message)
        messages.append({'role': 'tool', 'tool_call_id': tc.id,
                        'content': json.dumps(result, ensure_ascii=False)})
    final = client.chat.completions.create(model='gpt-4o', messages=messages, tools=tools)
```

## 工具定义最佳实践

| 原则 | 说明 | 示例 |
|------|------|------|
| **清晰描述** | 工具用途明确 | '获取**当前**天气' |
| **合理参数** | 只包含必要参数 | 不暴露api_key |
| **枚举约束** | 有限选项用enum | temperature: ['c','f'] |
| **类型标注** | 明确参数类型 | string/number |
| **默认值** | 非必填设默认 | unit: 'celsius' |

## 工具类型总览

| 工具类型 | 功能 | 应用场景 |
|---------|------|--------|
| **搜索工具** | 互联网搜索 | 信息检索 |
| **计算工具** | 数学运算 | 数据分析 |
| **代码工具** | 执行代码 | 数据处理 |
| **数据库工具** | SQL查询 | 数据查询 |
| **API工具** | 调用外部服务 | 天气、股票 |
| **文件工具** | 读写文件 | 文档处理 |

## Anthropic Tool Use

```python
import anthropic
client = anthropic.Anthropic()
tools = [{
    'name': 'get_stock_price',
    'description': '获取股票最新价格',
    'input_schema': {
        'type': 'object',
        'properties': {'symbol': {'type': 'string', 'description': '股票代码'}},
        'required': ['symbol'],
    },
}]
response = client.messages.create(
    model='claude-sonnet-4-20250514', max_tokens=1024, tools=tools,
    messages=[{'role': 'user', 'content': '苹果公司股价？'}],
)
```

## 小结

Function Calling和Tool Use是AI Agent的核心能力，将LLM从文本生成器转变为能与外部世界交互的智能系统。