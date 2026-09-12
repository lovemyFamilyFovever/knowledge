---
title: "语音AI技术"
tags: [人工智能, 语音]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# 语音AI技术


> 📌 **导航**：本文是 **语音AI技术** 词条，属于 ai-and-llm 术语集。相关枢纽：[[大模型基础术语详解]]、[[Transformer架构深度解析]]、[[RAG 与检索技术详解]]、[[多 Agent 协作系统]]、[[Prompt 工程与 Agent 详解]]。

## Whisper语音识别

```
音频 -> Mel频谱 -> Transformer Encoder -> Transformer Decoder -> 文本
```

| 模型 | 参数量 | 速度 |
|------|--------|------|
| tiny | 39M | ~32x |
| base | 74M | ~16x |
| small | 244M | ~6x |
| medium | 769M | ~2x |
| large-v3 | 1.55M | 1x |

```python
import whisper
model = whisper.load_model("base")
result = model.transcribe("audio.mp3", language="zh")
```

## TTS语音合成

| 方案 | 原理 | 特点 |
|------|------|------|
| Tacotron2 | Seq2Seq+注意力 | 经典方案 |
| VITS | 端到端 | 自然度高 |
| XTTS | 大模型 | 多语言+声音克隆 |

## 语音Agent

```
语音输入 -> ASR(识别) -> LLM(理解+推理) -> TTS(合成) -> 语音输出
```

## 相关术语

[[多模态大模型]]、[[多模态 Agent]]、[[大模型基础术语详解]]、[[机器学习基础]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
