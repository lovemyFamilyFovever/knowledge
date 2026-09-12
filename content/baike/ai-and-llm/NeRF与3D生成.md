---
title: "NeRF与3D生成"
tags: [人工智能, 3D生成]
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# NeRF与3D生成


> 📌 **导航**：本文是 **NeRF与3D生成** 词条，属于 ai-and-llm 术语集。相关枢纽：[[大模型基础术语详解]]、[[Transformer架构深度解析]]、[[RAG 与检索技术详解]]、[[多 Agent 协作系统]]、[[Prompt 工程与 Agent 详解]]。

## NeRF

用神经网络表示3D场景：`(x, y, z, theta, phi) -> (r, g, b, sigma)`

## 3D Gaussian Splatting

用3D高斯椭球表示场景，比NeRF快100倍+，实时渲染>30 FPS。

## 文生3D

| 方法 | 原理 | 质量 |
|------|------|------|
| DreamFusion | SDS Loss + NeRF | 中 |
| Point-E | 点云生成 | 低 |
| Shap-E | 隐式3D | 中 |
| Instant3D | 多视角扩散 | 高 |

## 相关术语

[[Diffusion扩散模型]]、[[多模态大模型]]、[[大模型基础术语详解]]、[[机器学习基础]]、[[Transformer架构深度解析]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
