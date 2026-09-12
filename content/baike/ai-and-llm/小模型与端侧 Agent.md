---
title: "小模型与端侧 Agent"
tags: [人工智能, Agent]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# 小模型与端侧 Agent


> 📌 **导航**：本文是 **小模型与端侧 Agent** 词条，属于 ai-and-llm 术语集。相关枢纽：[[大模型基础术语详解]]、[[Transformer架构深度解析]]、[[RAG 与检索技术详解]]、[[多 Agent 协作系统]]、[[Prompt 工程与 Agent 详解]]。

## 概述
**端侧Agent** 在本地设备上运行，保护隐私、降低延迟、减少成本。小模型的进步使端侧AI成为可能。

## 主流小模型

| 模型 | 参数量 | 发布方 | 特点 |
|------|--------|--------|------|
| **Phi-3** | 3.8B | Microsoft | 高质量小模型 |
| **Gemma 2** | 2B/9B/27B | Google | 多尺寸选择 |
| **Llama 3.2** | 1B/3B | Meta | 轻量级 |
| **Qwen2.5** | 0.5B-72B | Alibaba | 中文优化 |
| **Mistral** | 7B | Mistral | 高效架构 |
| **DeepSeek** | 7B | DeepSeek | 强推理能力 |

## 端侧部署技术

| 技术 | 说明 | 工具 |
|------|------|------|
| **ONNX Runtime** | 跨平台推理引擎 | onnxruntime |
| **llama.cpp** | CPU优化推理 | GGUF格式 |
| **MLC LLM** | 移动端推理 | Android/iOS |
| **Core ML** | Apple设备优化 | Apple |
| **TensorRT** | NVIDIA GPU优化 | NVIDIA |

## ONNX 导出和优化
```python
from optimum.onnxruntime import ORTModelForCausalLM

# 导出为ONNX
model = ORTModelForCausalLM.from_pretrained(
    'microsoft/Phi-3-mini-4k-instruct',
    export=True,
)
model.save_pretrained('./phi3-onnx')

# ONNX推理
import onnxruntime as ort
session = ort.InferenceSession('./phi3-onnx/model.onnx')
```

## llama.cpp 部署
```bash
# 量化模型为GGUF格式
python convert_hf_to_gguf.py model-name --outtype q4_k_m

# 运行推理
./llama-cli -m model.gguf -p "什么是AI Agent?" -n 256

# 启动API服务
./llama-server -m model.gguf --host 0.0.0.0 --port 8080
```

## 量化对比

| 格式 | 位数 | 大小(7B) | 速度 | 质量 |
|------|------|---------|------|------|
| FP16 | 16-bit | 14GB | 基准 | 100% |
| Q8_0 | 8-bit | 7GB | 1.5x | 99% |
| Q4_K_M | 4-bit | 4GB | 2.5x | 97% |
| Q2_K | 2-bit | 2.5GB | 3x | 90% |

## 端侧Agent架构
```python
class EdgeAgent:
    def __init__(self, model_path):
        self.model = load_model(model_path)  # 本地模型
        self.tools = [local_calc, local_file, local_db]  # 本地工具

    def run(self, task):
        # 优先本地处理
        result = self.model.generate(task)
        if self.needs_cloud(result):
            # 仅在必要时调用云端API
            result = self.fallback_to_cloud(task)
        return result
```

## 应用场景

| 场景 | 设备 | 价值 |
|------|------|------|
| **手机助手** | 智能手机 | 离线可用、低延迟 |
| **车载AI** | 汽车 | 实时响应、安全隐私 |
| **IoT设备** | 嵌入式 | 低成本、低功耗 |
| **桌面助手** | PC/Mac | 本地隐私保护 |

## 模型能力对比

| 任务 | Phi-3(3.8B) | GPT-4o | 差距 |
|------|-------------|--------|------|
| 简单问答 | 85% | 95% | 10% |
| 代码生成 | 70% | 90% | 20% |
| 数学推理 | 75% | 92% | 17% |
| 中文理解 | 72% | 93% | 21% |

## 小结
小模型的进步使端侧Agent成为现实。通过量化和优化，3B参数的模型已在手机上流畅运行。隐私敏感场景应优先考虑端侧部署。

## 相关术语

[[AI Agent 概述与核心架构]]、[[多 Agent 协作系统]]、[[多模态 Agent]]、[[大模型基础术语详解]]、[[LLM 推理优化]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
