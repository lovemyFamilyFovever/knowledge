---
title: "语音AI技术"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# 语音AI技术

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
