---
title: "容器化与Docker"
tags: []
source: "baike"
source_path: "开发术语 / 开发工具与环境"
collected: "2026-09-05"
status: "imported"
---

# 容器化与Docker

> 📌 **导航**：本文是 **容器化与Docker** 词条，属于 tools 术语集。相关枢纽：[[包管理器与构建工具]]、[[容器化与Docker]]、[[版本控制与Git深入]]、[[调试与性能分析]]。

## 定义

**一句话定义：** Docker 用镜像把应用连同其依赖打包成标准化容器，保证"在我机器上能跑"在任何装了 Docker 的地方都能一致运行。

**通俗类比：** Docker 像一个标准化的集装箱——不管里面装什么货物（应用），箱子的尺寸和接口都是统一的，任何港口（服务器）都能吊装处理。

## 为什么需要它

同一份代码在开发机、测试机、生产机常因环境差异而"我这好好的"；传统虚拟机虽隔离彻底，但每个都带一整个 OS，启动慢、资源重。Docker 用"打包依赖 + 共享宿主内核"这两点，同时拿到环境一致性与秒级轻量启动，把"部署一个应用"变成"跑一个镜像"。

## 核心能力

| 概念 | 说明 |
|------|------|
| 镜像（Image） | 应用的只读打包模板，分层构建 |
| 容器（Container） | 镜像运行起来的实例，顶层可写 |
| Dockerfile | 构建镜像的配方 |
| 仓库（Registry） | 存放 / 分发镜像（如 Docker Hub） |

- **镜像分层**：Dockerfile 每条指令生成一个只读层，可缓存、可复用——只有变动的层及其后续层需要重建。
- **常用命令**：`docker build -t myapp:1.0 .` 构建、`docker run -d -p 5000:5000 web myapp:1.0` 运行、`docker ps` 看状态、`docker exec -it web bash` 进容器、`docker logs -f` 看日志。
- **Compose**：用一份 YAML 声明并一条命令拉起多服务栈。

## 具体示例

Dockerfile 描述"基于什么镜像、装什么、怎么起"：

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

Compose 则把 web + 数据库 + 缓存三个服务一次编排起来（`docker compose up -d`）：

```yaml
services:
  web:   { build: ., ports: ["5000:5000"], depends_on: [db, redis] }
  db:    { image: postgres:15 }
  redis: { image: redis:7 }
```

## 何时用与何时不用

- **用**：容器化交付、统一开发/CI/生产环境、本地一键起多服务依赖栈。
- **不用**：需要强内核隔离的多租户不可信负载、依赖特定内核模块的场景——这些更适合虚拟机。

## 优劣与代价

✅ 环境一致、启动快、镜像可复用分发，部署标准化。
✅ Compose 让多服务本地开发开箱即用。
⚠️ 共享宿主内核，隔离强度低于虚拟机。
⚠️ 编排、镜像体积、数据持久化等在规模化后仍需 K8s 等专门方案。

## 与相关概念的区别

- **容器 vs 虚拟机**：容器共享宿主内核、秒级启动、镜像小；虚拟机自带客户机内核、隔离强但更重更慢。
- **镜像 vs 容器**：镜像是只读模板，容器是镜像运行时的实例（顶层可写、跑起来才有进程）。
- **Docker vs 编排平台**：Docker 构建并运行单个容器；多容器跨主机调度、自愈由 Kubernetes 等编排器负责（见 [[容器与编排技术详解]]）。

## 常见误区

- 容器就是轻量虚拟机，也有自己的操作系统内核。
- 改 Dockerfile 任意一行，都会导致整个镜像所有层重新构建。
- 用了 Docker 就能获得虚拟机级别的强隔离。

## 面试速答

> 🎯 Docker 把应用连依赖打成只读镜像，运行时成为容器，共享宿主内核、秒级启动；Dockerfile 分层构建可缓存复用，Compose 一条命令编排多服务，Registry 负责镜像分发。
> 🔍 追问：容器和虚拟机有何本质区别？
> 🔍 追问：Dockerfile 的分层缓存是怎么回事？

## 相关术语

[[包管理器与构建工具]]、[[版本控制与Git深入]]、[[调试与性能分析]]

## 参考资料

建议人工核验：本词条内容建议对照 Docker 官方文档（Dockerfile 指令、Compose）做准确性复核；未编造文献编号、标准号或 URL。
