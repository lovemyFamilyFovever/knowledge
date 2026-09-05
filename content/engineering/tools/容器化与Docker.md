---
title: "容器化与Docker"
tags: []
source: "baike"
source_path: "开发术语 / 开发工具与环境"
collected: "2026-09-05"
status: "imported"
---

# 容器化与Docker

## Docker

**一句话定义：** Docker是把应用和它的依赖打包在一起运行的工具，保证"在我机器上能跑"在任何地方都能跑。

**通俗类比：** Docker就像一个标准化的集装箱——不管里面装什么货物（应用），集装箱的尺寸和接口是统一的，任何港口（服务器）都能处理。

### 核心概念

| 概念 | 说明 |
|------|------|
| 镜像(Image) | 应用的打包模板（只读）|
| 容器(Container) | 镜像运行起来的实例 |
| Dockerfile | 构建镜像的配方 |
| 仓库(Registry) | 存放镜像的地方(Docker Hub) |

### Dockerfile示例

```dockerfile
# 基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "app.py"]
```

### 常用命令

```bash
# 构建镜像
docker build -t myapp:1.0 .

# 运行容器
docker run -d -p 5000:5000 --name web myapp:1.0

# 查看运行中的容器
docker ps

# 进入容器
docker exec -it web bash

# 查看日志
docker logs -f web

# 停止/删除容器
docker stop web && docker rm web
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    depends_on:
      - db
      - redis
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secret
  redis:
    image: redis:7
```

```bash
docker-compose up -d    # 启动所有服务
docker-compose down     # 停止并删除
docker-compose logs -f  # 查看日志
```

### 镜像分层

```
FROM ubuntu:22.04          # 基础层
RUN apt install python3    # 新增层
COPY . /app                # 新增层
CMD ["python", "app.py"]   # 配置层
```

每一层是只读的，容器层是可写的。层可以缓存和复用。
