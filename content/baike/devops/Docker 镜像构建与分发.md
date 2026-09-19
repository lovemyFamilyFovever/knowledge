---
title: "Docker 镜像构建与分发"
tags: []
source: "baike"
source_path: "技术文章 / DevOps与运维"
collected: "2026-09-05"
status: "imported"
---

# Docker 镜像构建与分发

> 📌 **导航**：本文是 **Docker 镜像构建与分发** 词条，属 [[Docker容器化完全指南]] 子词条。容器/镜像/Dockerfile 基础见 [[容器与编排技术详解]]，本文聚焦构建优化与分发。

## 定义

**一句话定义：** Docker 镜像构建与分发，指用 Dockerfile 把应用连同依赖打成可复现的只读镜像，经多阶段构建、层优化与瘦身做小做快，再存入公共或私有镜像仓库（如 Harbor）对外分发。

**通俗类比：** 像把一道菜做成"自热速食包"：配料与工序封进包装（镜像），去掉后厨重型设备（编译工具链），贴标签送进冷链仓（registry），各地开袋即食且味道一致。

## 为什么需要它

同一份代码要在任意环境跑出一模一样的结果，靠的是不可变、可寻址的镜像。但默认构建常又大又脏：带全套编译工具、留 apt 缓存、层碎而多——拉取慢、启动慢、漏洞攻击面大。构建优化让镜像更小更快更安全，分发（尤其私有仓库）则解决内网可控、鉴权、扫描与治理。

## 核心机制

- **Dockerfile 实践**：选精简基础镜像（slim/alpine/distroless）、合并 `RUN` 并清理缓存、配 `.dockerignore` 排除无关文件、把不常变的层（如依赖安装）放前面以复用构建缓存。
- **多阶段构建**：`build` 阶段装工具链编译，最终阶段只 `COPY --from=builder` 产物，甚至用 `scratch`/distroless，把编译依赖彻底留在构建期。
- **镜像瘦身**：静态编译（如 Go `CGO_ENABLED=0`）、用 distroless、以 dive 分析层、docker-slim 裁剪。
- **分发与治理**：push 到 registry；Harbor 私有仓库提供项目/命名空间、RBAC 鉴权、镜像扫描、复制与保留策略、签名。

## 具体示例

Go 应用多阶段构建：编译工具链只活在第一阶段，最终镜像近乎空壳：

```dockerfile
FROM golang:1.21-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /app .

FROM scratch              # 运行阶段：只带二进制，无发行版、无工具链
COPY --from=build /app /app
ENTRYPOINT ["/app"]
```

## 何时用与何时不用

- **用**：交付镜像进 CI/生产、镜像体积或启动时间/安全扫描是痛点、需内网私有仓库治理时。
- **不用**：本地一次性调试镜像不必上多阶段/distroless；语言运行时强依赖 glibc/系统库时，`scratch`/Alpine(musl) 兼容性要谨慎。

## 优劣与代价

✅ 更小（拉取/启动快）、攻击面更小、构建可复现、分发可控可扫描。
✅ 多阶段把"编译环境"与"运行环境"彻底分离。
⚠️ 多阶段/Dockerfile 写法更复杂，需理解缓存与层顺序。
⚠️ Alpine(musl) 与 glibc 二进制偶不兼容；私有仓库自身是要运维的组件。

## 与相关概念的区别

- **单阶段 vs 多阶段**：单阶段把工具链和产物混在一个镜像里、又大又险；多阶段只把产物拷进干净运行镜像。
- **slim / alpine / distroless / scratch**：从"删减的 Debian"到"musl 精简"到"Google 无 shell 运行库"到"完全空"，越小越安全但兼容与可调试性越低。
- 与 [[容器与编排技术详解]]：那篇讲 Dockerfile 是什么、分层与隔离原理；本篇讲怎么把镜像做得小且分发好。

## 常见误区

- 每条 RUN 拆得越碎越方便定位问题，是最佳实践。
- 编译用的工具链应留在最终镜像里，方便现场调试。
- 推到公共仓库和搭 Harbor 私有仓库没区别，反正都叫 registry。

## 面试速答

> 🎯 镜像构建优化：精简基础镜像 + 合并 RUN 并清缓存 + .dockerignore + 缓存友好层顺序 + 多阶段构建(只 COPY 产物、甚至 scratch/distroless) + dive 分析瘦身；分发经 registry，Harbor 私有仓库提供鉴权/扫描/复制/保留策略。目标是小、快、可复现、攻击面小。
> 🔍 追问：多阶段构建解决了什么问题？
> 🔍 追问：为什么 alpine/scratch 镜像有时跑不起来？

## 相关术语

[[Docker容器化完全指南]]、[[容器与编排技术详解]]、[[容器运行时安全]]、[[容器网络与数据持久化]]

## 参考资料

建议人工核验：以 Docker 官方 Dockerfile/best-practices 文档与 Harbor 文档为准；未编造文献编号。
