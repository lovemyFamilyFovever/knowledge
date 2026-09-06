---
title: "RAG系统工程化实践"
tags: []
source: "baike"
source_path: "技术文章 / AI与机器学习"
collected: "2026-09-05"
status: "imported"
---

# RAG系统工程化实践

# RAG系统工程化实践指南

## 1. RAG架构演进

### 1.1 Naive RAG（基础RAG）
基础RAG是最简单的检索增强生成架构，采用“检索-阅读”的线性流程：

```python
# 基础RAG实现示例
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA

# 1. 文档加载
documents = load_documents("knowledge_base/")

# 2. 文本分割
from langchain.text_splitter import RecursiveCharacterTextSplitter
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_documents(documents)

# 3. 向量化存储
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(chunks, embeddings)

# 4. 检索与生成
qa_chain = RetrievalQA.from_chain_type(
    llm=OpenAI(),
    chain_type="stuff",
    retriever=vectorstore.as_retriever()
)

# 5. 查询
response = qa_chain.run("什么是机器学习？")
```

**优点**：实现简单、延迟低
**缺点**：检索精度有限、无法处理复杂查询、上下文窗口限制

### 1.2 Advanced RAG（高级RAG）
高级RAG在基础架构上增加了预处理和后处理步骤：

```python
# Advanced RAG 核心改进
class AdvancedRAG:
    def __init__(self):
        self.query_rewriter = QueryRewriter()  # 查询改写
        self.hybrid_retriever = HybridRetriever()  # 混合检索
        self.reranker = Reranker()  # 重排序
        self.prompt_optimizer = PromptOptimizer()  # 提示优化
    
    def answer(self, query):
        # 1. 查询优化
        optimized_queries = self.query_rewriter.rewrite(query)
        
        # 2. 多路检索
        retrieval_results = []
        for q in optimized_queries:
            results = self.hybrid_retriever.retrieve(q)
            retrieval_results.extend(results)
        
        # 3. 重排序
        reranked_results = self.reranker.rerank(query, retrieval_results)
        
        # 4. 上下文构建
        context = self._build_context(reranked_results[:5])
        
        # 5. 优化提示词
        prompt = self.prompt_optimizer.optimize(query, context)
        
        # 6. 生成答案
        return self.llm.generate(prompt)
```

### 1.3 Modular RAG（模块化RAG）
模块化RAG将系统分解为可插拔组件：

```python
# 模块化架构设计
class ModularRAGSystem:
    def __init__(self, config):
        self.modules = {
            "document_processor": DocumentProcessor(config),
            "indexer": Indexer(config),
            "retriever": Retriever(config),
            "analyzer": Analyzer(config),
            "generator": Generator(config)
        }
        self.pipeline = self._build_pipeline(config['pipeline'])
    
    def _build_pipeline(self, pipeline_config):
        # 根据配置构建处理流水线
        pipeline = []
        for stage in pipeline_config:
            module = self.modules[stage['module']]
            pipeline.append((module, stage['params']))
        return pipeline
    
    def process_query(self, query):
        # 动态执行流水线
        context = {"query": query}
        for module, params in self.pipeline:
            context = module.process(context, **params)
        return context["answer"]
```

### 1.4 Agentic RAG（智能体RAG）
智能体RAG引入自主决策和任务分解能力：

```python
# Agentic RAG 核心实现
class AgenticRAG:
    def __init__(self):
        self.planner = QueryPlanner()  # 查询规划器
        self.tool_manager = ToolManager()  # 工具管理器
        self.memory = ConversationMemory()  # 对话记忆
    
    def execute(self, query, session_id):
        # 1. 查询分析与规划
        plan = self.planner.create_plan(query, self.memory.get_history(session_id))
        
        # 2. 任务分解
        sub_tasks = self._decompose_task(plan)
        
        # 3. 并行执行子任务
        results = {}
        for task in sub_tasks:
            if task.requires_retrieval:
                tool = self.tool_manager.get_retrieval_tool(task.source)
                results[task.id] = tool.execute(task.query)
            elif task.requires_computation:
                tool = self.tool_manager.get_computation_tool(task.type)
                results[task.id] = tool.execute(task.params)
        
        # 4. 结果聚合与推理
        final_answer = self._synthesize_answer(query, results)
        
        # 5. 更新记忆
        self.memory.add_interaction(session_id, query, final_answer)
        
        return final_answer

# 智能体工具注册示例
tool_manager.register_tool("wikipedia", WikipediaRetriever())
tool_manager.register_tool("calculator", CalculatorTool())
tool_manager.register_tool("sql_executor", SQLExecutorTool())
```

## 2. 文档解析

### 2.1 PDF文档解析
```python
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from unstructured.partition.pdf import partition_pdf

class PDFParser:
    def __init__(self, ocr_enabled=True):
        self.ocr_enabled = ocr_enabled
        
    def parse(self, file_path):
        """解析PDF文档，支持文本和图像PDF"""
        elements = partition_pdf(
            filename=file_path,
            strategy="hi_res",
            ocr_strategy=self.ocr_strategy(),
            table_strategy="fast",
            chunking_strategy="by_title"
        )
        
        return self._process_elements(elements)
    
    def _ocr_strategy(self):
        if self.ocr_enabled:
            return "auto"
        return "none"
    
    def _process_elements(self, elements):
        processed = []
        for element in elements:
            if element.type == "Table":
                # 特殊处理表格
                processed.append({
                    "type": "table",
                    "content": self._extract_table(element),
                    "metadata": element.metadata
                })
            elif element.type == "Image":
                # 图像描述
                processed.append({
                    "type": "image_description",
                    "content": self._describe_image(element),
                    "metadata": element.metadata
                })
            else:
                processed.append({
                    "type": "text",
                    "content": str(element),
                    "metadata": element.metadata
                })
        return processed
    
    def _extract_table(self, table_element):
        """提取表格数据并转换为结构化格式"""
        import pandas as pd
        # 尝试直接转换表格
        try:
            df = pd.read_html(str(table_element.metadata.html))[0]
            return df.to_markdown()
        except:
            return str(table_element)
```

### 2.2 Word文档解析
```python
from docx import Document
import mammoth
from bs4 import BeautifulSoup

class WordParser:
    def parse_docx(self, file_path):
        """解析.docx文件"""
        doc = Document(file_path)
        content = []
        
        for para in doc.paragraphs:
            if para.text.strip():
                content.append({
                    "text": para.text,
                    "style": para.style.name,
                    "level": self._get_heading_level(para)
                })
        
        # 提取表格
        for table in doc.tables:
            table_data = self._extract_table(table)
            content.append({
                "type": "table",
                "data": table_data
            })
        
        return content
    
    def parse_doc(self, file_path):
        """解析旧版.doc文件"""
        with open(file_path, "rb") as docx_file:
            result = mammoth.convert_to_html(docx_file)
            html = result.value
            soup = BeautifulSoup(html, 'html.parser')
            
            content = []
            for elem in soup.find_all(['p', 'h1', 'h2', 'h3', 'table']):
                if elem.name == 'table':
                    content.append(self._parse_html_table(elem))
                else:
                    content.append({
                        "text": elem.get_text(),
                        "tag": elem.name
                    })
            
            return content
    
    def _extract_table(self, table):
        """提取Word表格数据"""
        data = []
        for row in table.rows:
            row_data = [cell.text for cell in row.cells]
            data.append(row_data)
        return data
```

### 2.3 HTML文档解析
```python
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin

class HTMLParser:
    def __init__(self, base_url=None):
        self.base_url = base_url
        
    def parse_url(self, url):
        """从URL解析HTML"""
        response = requests.get(url)
        response.raise_for_status()
        return self._parse_html(response.text, url)
    
    def parse_file(self, file_path):
        """从本地文件解析HTML"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return self._parse_html(f.read(), file_path)
    
    def _parse_html(self, html_content, source):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 移除脚本和样式
        for script in soup(["script", "style"]):
            script.decompose()
        
        content = []
        
        # 提取主要文本内容
        main_content = soup.find('main') or soup.find('article') or soup
        for elem in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
            text = elem.get_text(strip=True)
            if text:
                # 处理相对URL
                if elem.name == 'a':
                    href = elem.get('href', '')
                    if href and self.base_url:
                        absolute_url = urljoin(self.base_url, href)
                        text = f"{text} (链接: {absolute_url})"
                
                content.append({
                    "text": text,
                    "tag": elem.name,
                    "source": source
                })
        
        # 提取表格
        for table in soup.find_all('table'):
            table_data = self._parse_html_table(table)
            content.append({
                "type": "table",
                "data": table_data,
                "source": source
            })
        
        return content
```

### 2.4 代码文档解析
```python
import ast
import re
from pathlib import Path

class CodeParser:
    SUPPORTED_LANGUAGES = {
        '.py': self._parse_python,
        '.js': self._parse_javascript,
        '.java': self._parse_java,
        '.ts': self._parse_typescript
    }
    
    def parse_codebase(self, repo_path):
        """解析代码仓库"""
        code_docs = []
        
        for file_path in Path(repo_path).rglob('*'):
            if file_path.suffix in self.SUPPORTED_LANGUAGES:
                parser = self.SUPPORTED_LANGUAGES[file_path.suffix]
                docs = parser(file_path)
                code_docs.extend(docs)
        
        return code_docs
    
    def _parse_python(self, file_path):
        """解析Python代码"""
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        try:
            tree = ast.parse(source)
            docs = []
            
            # 提取模块文档字符串
            if ast.get_docstring(tree):
                docs.append({
                    "type": "module_doc",
                    "content": ast.get_docstring(tree),
                    "file": str(file_path)
                })
            
            # 提取函数和类
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    doc = self._extract_function_doc(node, source)
                    docs.append(doc)
                elif isinstance(node, ast.ClassDef):
                    doc = self._extract_class_doc(node, source)
                    docs.append(doc)
            
            return docs
        except SyntaxError:
            return []
    
    def _extract_function_doc(self, func_node, source):
        """提取函数文档"""
        docstring = ast.get_docstring(func_node)
        
        # 提取函数签名
        start_line = func_node.lineno - 1
        end_line = func_node.body[0].lineno - 1
        signature_lines = source.splitlines()[start_line:end_line]
        signature = '\n'.join(signature_lines).strip()
        
        return {
            "type": "function",
            "name": func_node.name,
            "signature": signature,
            "docstring": docstring,
            "line_number": func_node.lineno,
            "decorators": [ast.dump(d) for d in func_node.decorator_list]
        }
```

## 3. Chunking策略

### 3.1 固定大小分割
```python
class FixedSizeChunker:
    def __init__(self, chunk_size=512, overlap=50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        
    def chunk_text(self, text):
        """固定大小分割"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # 处理边界情况
            if end > len(text):
                end = len(text)
            
            chunk = text[start:end]
            
            # 尝试在句子边界分割
            if end < len(text):
                last_period = chunk.rfind('。')
                last_newline = chunk.rfind('\n')
                last_boundary = max(last_period, last_newline)
                
                if last_boundary > self.chunk_size * 0.3:
                    chunk = chunk[:last_boundary + 1]
                    end = start + last_boundary + 1
            
            chunks.append({
                "text": chunk,
                "start": start,
                "end": end,
                "size": len(chunk)
            })
            
            start = end - self.overlap
        
        return chunks
```

### 3.2 语义分割
```python
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class SemanticChunker:
    def __init__(self, model_name='all-MiniLM-L6-v2', threshold=0.8):
        self.model = SentenceTransformer(model_name)
        self.threshold = threshold
        
    def chunk_by_semantics(self, text):
        """基于语义相似度分割"""
        sentences = self._split_sentences(text)
        
        if len(sentences) <= 1:
            return [{"text": text, "sentences": sentences}]
        
        # 计算句子嵌入
        embeddings = self.model.encode(sentences)
        
        # 计算相似度矩阵
        similarity_matrix = cosine_similarity(embeddings)
        
        # 识别分割点
        split_points = []
        for i in range(1, len(sentences)):
            # 检查当前句子与前一个句子的相似度
            if similarity_matrix[i][i-1] < self.threshold:
                split_points.append(i)
        
        # 根据分割点分组
        chunks = []
        start = 0
        
        for point in split_points:
            chunk_text = ' '.join(sentences[start:point])
            chunks.append({
                "text": chunk_text,
                "sentences": sentences[start:point],
                "size": len(sentences[start:point])
            })
            start = point
        
        # 处理最后一块
        if start < len(sentences):
            chunk_text = ' '.join(sentences[start:])
            chunks.append({
                "text": chunk_text,
                "sentences": sentences[start:],
                "size": len(sentences[start:])
            })
        
        return chunks
```

### 3.3 递归分割
```python
class RecursiveChunker:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";"]
        
    def recursive_split(self, text, separators=None):
        """递归分割文本"""
        if separators is None:
            separators = self.separators
            
        final_chunks = []
        
        # 如果文本足够短，直接返回
        if len(text) <= self.chunk_size:
            return [text]
        
        # 尝试用不同的分隔符分割
        for separator in separators:
            if separator in text:
                splits = text.split(separator)
                
                current_chunk = []
                current_size = 0
                
                for split in splits:
                    # 处理空字符串
                    if not split.strip():
                        continue
                    
                    split_size = len(split)
                    
                    # 如果单个分割块已经超大，需要递归处理
                    if split_size > self.chunk_size:
                        # 先处理当前累积的块
                        if current_chunk:
                            final_chunks.append(separator.join(current_chunk))
                            current_chunk = []
                            current_size = 0
                        
                        # 递归处理大块
                        sub_chunks = self.recursive_split(
                            split, 
                            separators[separators.index(separator)+1:]
                        )
                        final_chunks.extend(sub_chunks)
                        continue
                    
                    # 检查是否可以添加到当前块
                    if current_size + split_size + len(separator) <= self.chunk_size:
                        current_chunk.append(split)
                        current_size += split_size + len(separator)
                    else:
                        # 保存当前块
                        if current_chunk:
                            final_chunks.append(separator.join(current_chunk))
                        
                        # 开始新块
                        current_chunk = [split]
                        current_size = split_size
                
                # 处理剩余内容
                if current_chunk:
                    final_chunks.append(separator.join(current_chunk))
                
                return final_chunks
        
        # 如果所有分隔符都不适用，使用固定大小分割
        return self._fixed_size_split(text)
```

### 3.4 文档结构分割
```python
class StructuralChunker:
    def __init__(self, max_chunk_size=1500):
        self.max_chunk_size = max_chunk_size
        
    def chunk_by_structure(self, document_elements):
        """基于文档结构分割"""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for element in document_elements:
            element_size = len(element['text'])
            
            # 检查是否应该开始新块
            should_split = (
                current_size + element_size > self.max_chunk_size or
                self._is_heading(element) or
                self._is_new_section(element)
            )
            
            if should_split and current_chunk:
                # 保存当前块
                chunks.append({
                    "text": "\n".join([e['text'] for e in current_chunk]),
                    "elements": current_chunk,
                    "size": current_size,
                    "type": "section"
                })
                current_chunk = []
                current_size = 0
            
            # 处理单个元素过大的情况
            if element_size > self.max_chunk_size:
                # 先保存当前累积的内容
                if current_chunk:
                    chunks.append({
                        "text": "\n".join([e['text'] for e in current_chunk]),
                        "elements": current_chunk,
                        "size": current_size,
                        "type": "section"
                    })
                    current_chunk = []
                    current_size = 0
                
                # 大元素单独处理
                sub_chunks = self._split_large_element(element)
                chunks.extend(sub_chunks)
            else:
                current_chunk.append(element)
                current_size += element_size
        
        # 处理最后一块
        if current_chunk:
            chunks.append({
                "text": "\n".join([e['text'] for e in current_chunk]),
                "elements": current_chunk,
                "size": current_size,
                "type": "section"
            })
        
        return chunks
    
    def _is_heading(self, element):
        """判断是否为标题"""
        return element.get('tag', '').startswith('h')
    
    def _is_new_section(self, element):
        """判断是否为新章节开始"""
        section_indicators = ['第一章', '第二章', 'Part', 'Chapter', '##']
        text = element['text'][:50]
        return any(indicator in text for indicator in section_indicators)
```

## 4. Embedding模型选型和微调

### 4.1 模型选型策略
```python
class EmbeddingModelSelector:
    def __init__(self):
        self.models = {
            "multilingual": {
                "name": "paraphrase-multilingual-MiniLM-L12-v2",
                "dimensions": 384,
                "performance": {"mteb_avg": 56.5},
                "use_case": "多语言场景",
                "memory": "600MB"
            },
            "english": {
                "name": "all-MiniLM-L6-v2",
                "dimensions": 384,
                "performance": {"mteb_avg": 58.8},
                "use_case": "英文为主",
                "memory": "300MB"
            },
            "large": {
                "name": "text-embedding-3-large",
                "dimensions": 3072,
                "performance": {"mteb_avg": 64.6},
                "use_case": "高精度需求",
                "memory": "API服务"
            },
            "fast": {
                "name": "bge-small-zh-v1.5",
                "dimensions": 512,
                "performance": {"mteb_avg": 54.2},
                "use_case": "中文快速推理",
                "memory": "200MB"
            }
        }
    
    def select_model(self, requirements):
        """根据需求选择模型"""
        candidates = []
        
        for model_id, model_info in self.models.items():
            score = 0
            
            # 语言匹配
            if requirements.get('language') == 'multilingual' and 'multilingual' in model_id:
                score += 30
            elif requirements.get('language') == 'chinese' and 'zh' in model_info['name']:
                score += 30
            
            # 性能要求
            perf_score = model_info['performance']['mteb_avg']
            if requirements.get('precision') == 'high' and perf_score > 60:
                score += 25
            elif requirements.get('precision') == 'medium' and perf_score > 55:
                score += 20
            
            # 资源限制
            if requirements.get('memory') == 'limited':
                if 'small' in model_id or 'mini' in model_info['name']:
                    score += 20
            
            # 维度要求
            if requirements.get('dimensions'):
                if model_info['dimensions'] == requirements['dimensions']:
                    score += 15
            
            candidates.append((model_id, score, model_info))
        
        # 按分数排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        return candidates[0] if candidates else None
```

### 4.2 模型微调实践
```python
import torch
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
import json

class EmbeddingFineTuner:
    def __init__(self, base_model_name, output_dir="./fine_tuned_model"):
        self.model = SentenceTransformer(base_model_name)
        self.output_dir = output_dir
        
    def prepare_training_data(self, data_path):
        """准备微调数据"""
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        train_examples = []
        
        for item in data:
            # 查询-正例对
            for positive in item['positives']:
                train_examples.append(
                    InputExample(texts=[item['query'], positive], label=1.0)
                )
            
            # 查询-负例对
            for negative in item['negatives']:
                train_examples.append(
                    InputExample(texts=[item['query'], negative], label=0.0)
                )
        
        return train_examples
    
    def fine_tune(self, training_data, epochs=3, batch_size=16):
        """执行微调"""
        train_dataloader = DataLoader(training_data, shuffle=True, batch_size=batch_size)
        
        # 使用对比损失
        train_loss = losses.CosineSimilarityLoss(self.model)
        
        # 训练配置
        warmup_steps = int(len(train_dataloader) * epochs * 0.1)
        
        # 开始训练
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=epochs,
            warmup_steps=warmup_steps,
            output_path=self.output_dir,
            show_progress_bar=True
        )
        
        return self.output_dir
    
    def evaluate_model(self, test_data):
        """评估模型性能"""
        from sentence_transformers import evaluation
        
        sentences1 = [item['query'] for item in test_data]
        sentences2 = [item['positive'] for item in test_data]
        scores = [1.0] * len(test_data)  # 假设都是正例
        
        evaluator = evaluation.EmbeddingSimilarityEvaluator(
            sentences1, sentences2, scores
        )
        
        return evaluator(self.model)
```

### 4.3 对比学习训练
```python
class ContrastiveTrainer:
    def __init__(self, model):
        self.model = model
        
    def create_contrastive_pairs(self, dataset, num_negatives=5):
        """创建对比学习数据对"""
        pairs = []
        
        for item in dataset:
            anchor = item['query']
            positive = item['positive_doc']
            
            # 硬负例挖掘
            hard_negatives = self._mine_hard_negatives(
                anchor, 
                item['candidate_docs'], 
                num_negatives
            )
            
            for negative in hard_negatives:
                pairs.append((anchor, positive, negative))
        
        return pairs
    
    def train_with_contrastive_loss(self, pairs, batch_size=32, temperature=0.05):
        """使用对比损失训练"""
        from sentence_transformers import losses
        
        # 准备数据
        train_data = []
        for anchor, positive, negative in pairs:
            train_data.append(InputExample(
                texts=[anchor, positive, negative]
            ))
        
        # 使用三重损失
        train_loss = losses.TripletLoss(
            model=self.model,
            distance_metric=losses.TripletDistanceMetric.COSINE,
            triplet_margin=temperature
        )
        
        # 训练
        train_dataloader = DataLoader(train_data, shuffle=True, batch_size=batch_size)
        
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=5,
            warmup_steps=1000
        )
```

## 5. 向量数据库实战

### 5.1 Milvus实战
```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

class MilvusManager:
    def __init__(self, host="localhost", port="19530"):
        connections.connect(host=host, port=port)
        
    def create_collection(self, collection_name, dimension):
        """创建向量集合"""
        # 定义字段
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
            FieldSchema(name="metadata", dtype=DataType.JSON)
        ]
        
        schema = CollectionSchema(fields, description="RAG知识库")
        
        # 创建集合
        collection = Collection(collection_name, schema)
        
        # 创建索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "HNSW",
            "params": {"M": 16, "efConstruction": 200}
        }
        collection.create_index("embedding", index_params)
        
        return collection
    
    def insert_documents(self, collection_name, documents):
        """批量插入文档"""
        collection = Collection(collection_name)
        
        data = [
            [doc["text"] for doc in documents],
            [doc["embedding"] for doc in documents],
            [doc.get("metadata", {}) for doc in documents]
        ]
        
        insert_result = collection.insert(data)
        collection.flush()
        
        return insert_result
    
    def search(self, collection_name, query_embedding, top_k=10, filters=None):
        """向量检索"""
        collection = Collection(collection_name)
        collection.load()
        
        search_params = {
            "metric_type": "COSINE",
            "params": {"ef": 100}
        }
        
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filters,
            output_fields=["text", "metadata"]
        )
        
        return results[0]
```

### 5.2 Qdrant实战
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition

class QdrantManager:
    def __init__(self, host="localhost", port=6333):
        self.client = QdrantClient(host=host, port=port)
        
    def create_collection(self, collection_name, vector_size):
        """创建Qdrant集合"""
        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        
        # 创建payload索引以提高过滤性能
        self.client.create_payload_index(
            collection_name=collection_name,
            field_name="category",
            field_schema="keyword"
        )
        
    def insert_vectors(self, collection_name, points):
        """插入向量点"""
        qdrant_points = []
        
        for point in points:
            qdrant_point = PointStruct(
                id=point["id"],
                vector=point["vector"],
                payload=point.get("payload", {})
            )
            qdrant_points.append(qdrant_point)
        
        self.client.upsert(
            collection_name=collection_name,
            points=qdrant_points
        )
    
    def search_with_filter(self, collection_name, query_vector, filter_conditions=None, top_k=10):
        """带过滤的向量检索"""
        search_filter = None
        
        if filter_conditions:
            conditions = []
            for field, value in filter_conditions.items():
                conditions.append(
                    FieldCondition(key=field, match={"value": value})
                )
            search_filter = Filter(must=conditions)
        
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=search_filter,
            limit=top_k
        )
        
        return results
```

### 5.3 Chroma实战
```python
import chromadb
from chromadb.config import Settings

class ChromaManager:
    def __init__(self, persist_directory="./chroma_db"):
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
    def create_collection(self, collection_name):
        """创建Chroma集合"""
        collection = self.client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        return collection
    
    def add_documents(self, collection_name, documents):
        """添加文档到集合"""
        collection = self.client.get_collection(collection_name)
        
        ids = [f"doc_{i}" for i in range(len(documents))]
        texts = [doc["text"] for doc in documents]
        embeddings = [doc["embedding"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        
        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
    
    def query_documents(self, collection_name, query_text=None, query_embedding=None, 
                       n_results=10, filters=None):
        """查询文档"""
        collection = self.client.get_collection(collection_name)
        
        query_params = {
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"]
        }
        
        if filters:
            query_params["where"] = filters
        
        if query_embedding:
            query_params["query_embeddings"] = [query_embedding]
        elif query_text:
            query_params["query_texts"] = [query_text]
        
        results = collection.query(**query_params)
        
        return results
```

### 5.4 数据库对比与选型
```python
class VectorDBComparator:
    def __init__(self):
        self.criteria = {
            "performance": {
                "milvus": {"qps": 5000, "latency": "2ms", "scalability": "excellent"},
                "qdrant": {"qps": 3000, "latency": "5ms", "scalability": "good"},
                "chroma": {"qps": 1000, "latency": "10ms", "scalability": "limited"}
            },
            "features": {
                "milvus": ["distributed", "GPU", "multi-vector", "hybrid