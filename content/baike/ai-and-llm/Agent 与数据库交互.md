---
title: "Agent 与数据库交互"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# Agent 与数据库交互

## 概述
**数据库Agent** 能够理解自然语言查询，自动生成SQL，并分析查询结果。

## Text2SQL
将自然语言转换为SQL查询：
```python
class Text2SQLAgent:
    def __init__(self, llm, db_connection):
        self.llm = llm
        self.db = db_connection

    def query(self, question: str) -> str:
        # 1. 获取数据库schema
        schema = self.db.get_schema()

        # 2. LLM生成SQL
        prompt = f"""
        基于以下数据库结构，将问题转换为SQL：

        数据库结构：
        {schema}

        问题：{question}

        只输出SQL语句："""

        sql = self.llm.generate(prompt).strip()

        # 3. 执行SQL
        try:
            result = self.db.execute(sql)
            return self.format_result(question, sql, result)
        except Exception as e:
            return f"SQL执行错误: {e}"

    def format_result(self, question, sql, result):
        prompt = f"""
        问题：{question}
        SQL：{sql}
        查询结果：{result}

        请用自然语言总结查询结果。"""
        return self.llm.generate(prompt)
```

## 数据查询Agent
```python
class DataQueryAgent:
    def __init__(self, llm, data_sources):
        self.llm = llm
        self.sources = data_sources

    def analyze(self, question: str) -> dict:
        # 1. 确定数据源
        source = self.select_source(question)

        # 2. 获取数据
        if source.type == 'sql':
            data = self.query_sql(source, question)
        elif source.type == 'api':
            data = self.call_api(source, question)

        # 3. 分析数据
        analysis = self.analyze_data(question, data)

        # 4. 生成可视化建议
        viz = self.suggest_visualization(data)

        return {'data': data, 'analysis': analysis, 'visualization': viz}
```

## 数据分析Agent
```python
class DataAnalysisAgent:
    def __init__(self, llm):
        self.llm = llm

    def explore(self, df):
        prompt = f"""
        数据集信息：
        - 行数: {len(df)}
        - 列: {list(df.columns)}
        - 数据类型: {df.dtypes.to_dict()}
        - 前5行: {df.head().to_dict()}

        请建议：1) 值得分析的问题 2) 推荐的分析方法 3) 需要的数据清洗"""
        return self.llm.generate(prompt)
```

## 安全考虑

| 风险 | 防护措施 |
|------|---------|
| **SQL注入** | 参数化查询/只读权限 |
| **数据泄露** | 行级权限控制 |
| **资源滥用** | 查询超时限制 |
| **误操作** | 只允许SELECT |

## 小结
数据库Agent通过自然语言接口让非技术人员也能查询和分析数据。核心挑战是SQL生成的准确性和安全性。
