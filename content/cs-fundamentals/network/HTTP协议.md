---
title: "HTTP协议"
tags: []
source: "baike"
source_path: "开发术语 / 网络与协议"
collected: "2026-09-05"
status: "imported"
---

# HTTP协议

## 一句话定义（大白话）

HTTP（超文本传输协议）是浏览器和服务器之间互相沟通的"语言规则"，你访问网页、调用API时，底层都在用它。

---

## 通俗类比

想象你在餐厅点餐：你（客户端）递一份菜单请求给服务员（服务器），服务员把菜（网页数据）端给你。HTTP就是那张"菜单+餐具"的标准格式——规定了怎么写请求、怎么返回响应。

---

## HTTP方法（GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS）

### 一句话定义

HTTP方法告诉服务器你要对资源做什么操作，就像动词告诉别人你要"拿、放、改、删"什么东西。

### 通俗类比

- **GET**：去图书馆"查阅"一本书（只读，不动原书）
- **POST**：向图书馆"提交"一本新书（创建）
- **PUT**：把一本书"整本替换"（全量更新）
- **PATCH**：在书上"涂改"几页（部分更新）
- **DELETE**：从图书馆"删除"一本书
- **HEAD**：只问图书馆"这本书在不在"，不取内容
- **OPTIONS**：问图书馆"我能不能做这些操作"

### 具体示例

```http
# GET请求：获取用户列表
GET /api/users?page=1 HTTP/1.1
Host: example.com

# POST请求：创建新用户
POST /api/users HTTP/1.1
Host: example.com
Content-Type: application/json

{
  "name": "张三",
  "email": "zhangsan@example.com"
}

# PUT请求：更新用户全部信息
PUT /api/users/1 HTTP/1.1
Host: example.com
Content-Type: application/json

{
  "name": "张三丰",
  "email": "zhangsan@example.com",
  "phone": "13800138000"
}

# PATCH请求：只改邮箱
PATCH /api/users/1 HTTP/1.1
Host: example.com
Content-Type: application/json

{
  "email": "new@example.com"
}

# DELETE请求：删除用户
DELETE /api/users/1 HTTP/1.1
Host: example.com
```

### 为什么需要它

不同操作需要不同语义：GET必须是幂等的（多次调用结果一样），POST不是幂等的（每次可能创建新资源）。用对方法，服务器和中间件才能正确处理。

### 与相关术语的对比

| 方法 | 幂等 | 安全 | 用途 |
|------|------|------|------|
| GET | 是 | 是 | 查询 |
| POST | 否 | 否 | 创建 |
| PUT | 是 | 否 | 全量替换 |
| PATCH | 否 | 否 | 部分更新 |
| DELETE | 是 | 否 | 删除 |

---

## HTTP状态码分类（1xx/2xx/3xx/4xx/5xx）

### 一句话定义

状态码是服务器给客户端的"回复编号"，告诉你请求是成功了、出错了、还是需要额外操作。

### 通俗类比

就像快递回执单：2xx = "已签收"，3xx = "包裹转寄到新地址"，4xx = "收件地址有误"，5xx = "快递公司内部出问题"。

### 具体示例

```
1xx：信息性（如 100 Continue，服务器已收到请求头，继续发body）
2xx：成功（如 200 OK，一切正常）
3xx：重定向（如 301 Moved Permanently，资源永久搬家）
4xx：客户端错误（如 404 Not Found，你要找的页面不存在）
5xx：服务端错误（如 500 Internal Server Error，服务器炸了）
```

### 为什么需要它

让客户端不用解析响应体就能快速判断结果类型，也方便日志统计和监控告警。

---

## 常用状态码详解（200/201/301/302/304/400/401/403/404/405/429/500/502/503）

### 一句话定义

每个状态码代表一种具体场景的"标准答案"，是HTTP协议定义好的全球通用代码。

### 具体示例

```http
# 200 OK
HTTP/1.1 200 OK
Content-Type: application/json
{"users": [{"id": 1, "name": "张三"}]}

# 201 Created（POST创建成功）
HTTP/1.1 201 Created
Location: /api/users/2
{"id": 2, "name": "李四"}

# 301 Moved Permanently（永久重定向）
HTTP/1.1 301 Moved Permanently
Location: https://new-domain.com

# 304 Not Modified（缓存可用）
HTTP/1.1 304 Not Modified

# 400 Bad Request（参数错误）
HTTP/1.1 400 Bad Request
{"error": "email字段格式不正确"}

# 401 Unauthorized（未登录）
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer

# 403 Forbidden（无权限）
HTTP/1.1 403 Forbidden
{"error": "您没有管理员权限"}

# 404 Not Found（资源不存在）
HTTP/1.1 404 Not Found
{"error": "用户不存在"}

# 429 Too Many Requests（限流）
HTTP/1.1 429 Too Many Requests
Retry-After: 60

# 500 Internal Server Error（服务器异常）
HTTP/1.1 500 Internal Server Error

# 503 Service Unavailable（服务不可用）
HTTP/1.1 503 Service Unavailable
Retry-After: 30
```

### 为什么需要它

状态码是API设计的"契约语言"，前后端、网关、监控系统都依赖它做自动化处理。

### 与相关术语的对比

| 状态码 | 含义 | 客户端应 |
|--------|------|---------|
| 200 | 成功 | 处理响应体 |
| 301 | 永久重定向 | 更新书签URL |
| 304 | 未修改 | 使用缓存 |
| 401 | 未认证 | 去登录 |
| 403 | 无权限 | 联系管理员 |
| 404 | 不存在 | 检查URL |
| 429 | 超限流 | 等待后重试 |
| 500 | 服务端异常 | 稍后重试 |

---

## 请求头与响应头

### 一句话定义

请求头和响应头是HTTP报文的"附带信息"，用key-value格式传递元数据，就像信封上的备注栏。

### 通俗类比

寄快递时你在包裹上贴了"易碎品""三天内送达"等标签——这些就是头部信息。

### 具体示例

```http
# 请求头
GET /api/data HTTP/1.1
Host: api.example.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
Cache-Control: no-cache
Cookie: session_id=abc123; theme=dark

# 响应头
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 256
Cache-Control: max-age=3600
Set-Cookie: session_id=abc123; HttpOnly; Secure
X-Request-Id: req-789xyz
```

### 为什么需要它

头部承载了认证、缓存、编码、内容协商等关键信息，是HTTP协议"可扩展性"的核心机制。

---

## Content-Type

### 一句话定义

Content-Type告诉对方"我的body是什么格式"，就像你在信封里写了"里面是照片还是文件"。

### 通俗类比

你寄了一个包裹，贴了标签"内有衣物"或"内有文件"——对方拆包前就知道该用什么方式处理。

### 具体示例

```http
# JSON数据
Content-Type: application/json

# 表单提交
Content-Type: application/x-www-form-urlencoded

# 文件上传
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

# HTML页面
Content-Type: text/html; charset=utf-8

# XML数据
Content-Type: application/xml
```

### 为什么需要它

服务器根据Content-Type决定如何解析body，缺少或错误会导致数据解析失败。

### 与相关术语的对比

- **Content-Type**：描述请求/响应body的格式
- **Accept**：描述客户端"想要"什么格式
- **Accept-Encoding**：描述客户端支持什么压缩方式

---

## Accept

### 一句话定义

Accept是客户端告诉服务器"我想要什么格式的响应"，用于内容协商。

### 具体示例

```http
# 只接受JSON
Accept: application/json

# 优先JSON，也可以XML
Accept: application/json, application/xml;q=0.9

# 接受任何格式
Accept: */*

# 只接受中文内容
Accept-Language: zh-CN,zh;q=0.9
```

### 为什么需要它

同一个资源可以有多种格式（JSON/XML/HTML），客户端用Accept告诉服务器返回最适合的格式。

---

## Cache-Control

### 一句话定义

Cache-Control控制浏览器和CDN的缓存策略，告诉中间节点"这个响应能缓存多久、谁能缓存"。

### 通俗类比

像在食物包装上标注"保质期3天，需冷藏"——告诉你能不能存、存哪里、存多久。

### 具体示例

```http
# 允许缓存1小时
Cache-Control: max-age=3600

# 完全不缓存
Cache-Control: no-store

# 每次必须回源验证
Cache-Control: no-cache

# 只能CDN缓存，用户浏览器不缓存
Cache-Control: private

# 公共缓存（CDN/代理）
Cache-Control: public

# 强缓存+协商缓存组合
Cache-Control: max-age=3600, must-revalidate
```

### 为什么需要它

减少重复请求，提升加载速度，降低服务器压力。

### 与相关术语的对比

| 头部 | 层级 | 作用 |
|------|------|------|
| Cache-Control | HTTP层 | 控制缓存策略 |
| ETag | HTTP层 | 资源版本标识 |
| Last-Modified | HTTP层 | 资源最后修改时间 |
| Expires | HTTP层（旧） | 过期时间点 |

---

## Cookie与Session

### 一句话定义

Cookie存在浏览器里，Session存在服务器上——它们配合实现"记住用户登录状态"。

### 通俗类比

Cookie是超市给你的会员卡（你拿着），Session是超市后台的会员档案（超市存着）。卡号（Session ID）把两者关联起来。

### 具体示例

```http
# 服务器设置Cookie
HTTP/1.1 200 OK
Set-Cookie: session_id=abc123; Path=/; HttpOnly; Secure; SameSite=Lax

# 浏览器后续请求自动带上Cookie
GET /dashboard HTTP/1.1
Cookie: session_id=abc123; theme=dark

# Session存储在服务器（伪代码）
session_store = {
  "abc123": {
    "user_id": 1001,
    "username": "zhangsan",
    "role": "admin",
    "login_time": "2026-08-20T10:00:00Z"
  }
}
```

### 为什么需要它

HTTP是无状态协议，每次请求都像"初次见面"。Cookie+Session让服务器能"认出你"。

### 与相关术语的对比

| 存储方式 | 位置 | 安全性 | 容量 | 持久性 |
|---------|------|--------|------|--------|
| Cookie | 客户端 | 低（可被窃取） | 4KB | 可设过期时间 |
| Session | 服务端 | 高 | 无限制 | 关闭浏览器失效 |
| JWT | 客户端 | 中 | 4KB | 可设过期时间 |

---

## HTTP/2多路复用

### 一句话定义

HTTP/2允许在一个TCP连接上同时发送多个请求/响应，不用排队等一个完成再发下一个。

### 通俗类比

HTTP/1.1像单车道公路——一辆车走完另一辆才能走。HTTP/2像多车道高速——多辆车同时并行行驶。

### 具体示例

```
HTTP/1.1（队头阻塞）：
  请求1 → 等待响应1 → 请求2 → 等待响应2 → 请求3 → 等待响应3

HTTP/2（多路复用）：
  请求1 ──┐
  请求2 ──┼──→ 同时发送，各自独立返回响应
  请求3 ──┘
```

### 为什么需要它

HTTP/1.1每个连接同时只能处理一个请求，浏览器需要开6-8个TCP连接。HTTP/2一个连接搞定，减少握手开销和内存占用。

### 与相关术语的对比

| 特性 | HTTP/1.1 | HTTP/2 | HTTP/3 |
|------|----------|--------|--------|
| 连接数 | 多个 | 1个 | 1个 |
| 多路复用 | 否 | 是（基于TCP） | 是（基于QUIC） |
| 头部压缩 | 否 | HPACK | QPACK |
| 服务器推送 | 否 | 是 | 是 |
| 队头阻塞 | 有 | TCP层有 | 无 |

---

## HTTP/3 QUIC

### 一句话定义

HTTP/3基于QUIC协议（底层用UDP），解决了HTTP/2在TCP层的队头阻塞问题，是HTTP的最新一代。

### 通俗类比

HTTP/2修了高速公路（TCP连接复用），但遇到一个车道堵车（TCP丢包）所有车都停。HTTP/3把地基从铁路（TCP）换成了磁悬浮（QUIC/UDP），彻底不堵。

### 具体示例

```
# QUIC协议特点
- 基于UDP，内建TLS 1.3
- 连接建立只需1个RTT（TCP+TLS需要2-3个RTT）
- 连接迁移（Wi-Fi切4G不断连）
- 无队头阻塞（单个流丢包不影响其他流）

# 检测是否使用HTTP/3
curl -v https://example.com 2>&1 | grep "Alt-Svc"
# 响应头会包含：Alt-Svc: h3=":443"; ma=86400
```

### 为什么需要它

移动网络下TCP丢包率高，HTTP/2的一个丢包会阻塞所有请求。HTTP/3让每个流独立，大幅提升弱网体验。

---

## Keep-Alive

### 一句话定义

Keep-Alive让TCP连接在发送完响应后保持打开状态，后续请求可以复用，不用每次都重新握手。

### 通俗类比

打电话时，每次说完一句话就挂断再重拨很麻烦。Keep-Alive就是"先别挂电话"，保持通话线路畅通。

### 具体示例

```http
# 请求头
Connection: keep-alive
Keep-Alive: timeout=5, max=100

# 含义：连接保持5秒空闲超时，最多处理100个请求后关闭
```

### 为什么需要它

TCP三次握手+TLS握手需要2-3个RTT，Keep-Alive避免了重复握手的开销。

### 与相关术语的对比

- **HTTP/1.1**：默认开启Keep-Alive
- **HTTP/2**：连接复用是内置特性，不需要这个头
- **HTTP/3**：基于QUIC，连接天然复用

---

## Content-Length

### 一句话定义

Content-Length告诉对方"body有多长"，让接收方知道什么时候算接收完毕。

### 通俗类比

寄快递时你在包裹上写了"内有500克物品"——对方知道拆完500克就算拆完了。

### 具体示例

```http
# 响应头中声明body长度
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 42

{"name": "张三", "age": 25}

# 分块传输（不知道总长度时）
HTTP/1.1 200 OK
Transfer-Encoding: chunked

1a
{"name": "张三", "age": 25}
0
```

### 为什么需要它

没有Content-Length，接收方不知道body何时结束，会导致连接挂起或数据不完整。

### 与相关术语的对比

| 头部 | 场景 | 说明 |
|------|------|------|
| Content-Length | 固定长度 | 明确声明字节数 |
| Transfer-Encoding: chunked | 动态长度 | 分块传输，最后发0长度块 |

---

## 完整HTTP请求/响应示例

```
=== 请求 ===
GET /api/users/1 HTTP/1.1
Host: api.example.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)
Accept: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxMDAxfQ...
Accept-Encoding: gzip, deflate
Connection: keep-alive

=== 响应 ===
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 85
Cache-Control: max-age=60
ETag: "a1b2c3d4"
X-Request-Id: req-xyz-789

{
  "id": 1,
  "name": "张三",
  "email": "zhangsan@example.com",
  "created_at": "2026-01-01T00:00:00Z"
}
```
