---
title: "NeRF与3D生成"
tags: []
source: "baike"
source_path: "开发术语 / AI与大模型"
collected: "2026-09-05"
status: "imported"
---

# NeRF与3D生成

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
