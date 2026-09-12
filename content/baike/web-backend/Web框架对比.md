---
title: "Web框架对比"
tags: []
source: "baike"
source_path: "开发术语 / Web后端开发"
collected: "2026-09-05"
status: "imported"
---

# Web框架对比


> 📌 **导航**：本文是 **Web框架对比** 词条，属于 web-backend 术语集。相关枢纽：[[Web框架对比]]、[[缓存策略]]、[[认证与安全实践]]。

## 主流Web框架

**一句话定义：** Web框架是快速开发网站/应用的工具箱，提供了路由、模板、数据库等开箱即用的功能。

**通俗类比：** 框架就像"毛坯房+基础装修"——你不需要自己打地基、铺水电，直接在里面做个性化装修（业务逻辑）就行。

### 框架对比

| 框架 | 语言 | 特点 | 适用场景 |
|------|------|------|----------|
| Django | Python | 全家桶，ORM/Admin自带 | 快速开发、CMS |
| Flask | Python | 轻量灵活，自选组件 | 小项目、API |
| FastAPI | Python | 异步、自动文档、类型提示 | 高性能API |
| Spring Boot | Java | 企业级、生态完善 | 大型企业应用 |
| Express | Node.js | 极简、中间件模式 | Node.js API |
| Gin | Go | 高性能、简洁 | 高并发服务 |
| Laravel | PHP | 优雅语法、功能丰富 | PHP Web应用 |
| Rails | Ruby | 约定优于配置 | 快速原型 |

### MVC模式

```
用户请求 → 路由 → 控制器(Controller)
                    ↓
              模型(Model) ← 数据库
                    ↓
              视图(View) → 返回HTML/JSON
```

- **Model**：数据和业务逻辑
- **View**：用户界面
- **Controller**：接收请求，调用Model，选择View

### ORM（对象关系映射）

```python
# 不用ORM（原生SQL）
cursor.execute("SELECT * FROM users WHERE age > ?", (18,))

# 用ORM
users = User.query.filter(User.age > 18).all()
```

**优点：** 不用写SQL、跨数据库、类型安全
**缺点：** 复杂查询性能可能差、学习成本

### 中间件（Middleware）

请求和响应之间的处理链：
```
请求 → 认证中间件 → 日志中间件 → CORS中间件 → 路由处理
响应 ← 压缩中间件 ← 缓存中间件 ←
```

### 选择建议

| 场景 | 推荐 |
|------|------|
| 快速原型 | Django/Rails/Laravel |
| 高性能API | FastAPI/Gin |
| 大型企业项目 | Spring Boot |
| 全栈JS | Express/Next.js |
| 微服务 | Gin/FastAPI |

## 相关术语

[[缓存策略]]、[[认证与安全实践]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
