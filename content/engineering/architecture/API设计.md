---
title: "API设计"
tags: []
source: "baike"
source_path: "开发术语 / 架构与设计"
collected: "2026-09-05"
status: "imported"
---

# API设计

## 1. RESTful API设计规范

**一句话定义：** 基于HTTP协议，用URL表示资源，用HTTP方法表示操作的设计风格。

**通俗类比：** 像图书馆的索书系统，书架号（URL）定位书籍，借/还/查（HTTP方法）操作书籍。

**具体示例：**
```
GET    /api/v1/users          # 获取用户列表
GET    /api/v1/users/1001     # 获取单个用户
POST   /api/v1/users          # 创建用户
PUT    /api/v1/users/1001     # 更新用户（全量）
PATCH  /api/v1/users/1001     # 更新用户（部分）
DELETE /api/v1/users/1001     # 删除用户
```

**为什么需要它：** 统一API设计风格，降低沟通成本，提高开发效率。

**与GraphQL对比：** REST用多个端点表示不同资源，GraphQL用单个端点按需查询数据。

---

## 2. HTTP方法语义

**一句话定义：** 不同HTTP方法代表不同的操作类型，具有特定语义和约束。

**通俗类比：** 像银行操作，查询（GET）不改变账户，转账（POST/PUT）会改变余额。

**具体示例：**
```
GET     - 幂等，安全，可缓存    - 查询资源
POST    - 非幂等，不安全        - 创建资源
PUT     - 幂等，不安全          - 替换资源
PATCH   - 非幂等，不安全        - 部分更新
DELETE  - 幂等，不安全          - 删除资源
HEAD    - 幂等，安全            - 只获取响应头
OPTIONS - 幂等，安全            - 获取支持的方法
```

**为什么需要它：** 明确每个方法的语义，让API行为可预期，便于缓存和安全控制。

**幂等性解释：** 幂等意味着多次执行结果相同，GET/PUT/DELETE天然幂等，POST需要额外设计。

---

## 3. 状态码使用规范

**一句话定义：** 用标准HTTP状态码表示请求处理结果，让客户端快速理解响应。

**通俗类比：** 像交通信号灯，绿灯（2xx）通行，黄灯（3xx）注意，红灯（4xx/5xx）停止。

**具体示例：**
```
200 OK                  - 成功
201 Created             - 创建成功
204 No Content          - 删除成功，无返回体
301 Moved Permanently   - 永久重定向
304 Not Modified        - 缓存未过期
400 Bad Request         - 请求参数错误
401 Unauthorized        - 未认证
403 Forbidden           - 无权限
404 Not Found           - 资源不存在
429 Too Many Requests   - 请求过于频繁
500 Internal Error      - 服务器内部错误
503 Service Unavailable - 服务不可用
```

**为什么需要它：** 标准化错误处理，让客户端根据状态码快速判断下一步操作。

**常见错误：** 不要所有错误都返回200再在body中标记错误，这违背了HTTP语义。

---

## 4. 资源命名

**一句话定义：** 用名词复数形式命名资源，用路径层级表示资源关系。

**通俗类比：** 像文件系统的目录结构，/动物/猫 表示猫属于动物类别。

**具体示例：**
```
/users                          # 用户集合
/users/1001                     # 单个用户
/users/1001/orders              # 该用户的订单
/users/1001/orders/5001         # 该用户的某个订单
/users/1001/orders/5001/items   # 该订单的商品项
```

**为什么需要它：** 统一的命名规范让API直观易懂，降低学习成本。

**常见错误：** 使用动词（如/getUsers）、单数形式（如/user）、层级过深（超过3层）。

---

## 5. 分页设计（offset/cursor）

**一句话定义：** 将大量数据分批返回，避免一次性加载过多数据。

**通俗类比：** 像翻书，每次只看一页，而不是把整本书摊开。

**具体示例：**
```
# Offset分页
GET /api/users?page=2&size=20
Response: {
  "data": [...],
  "total": 1000,
  "page": 2,
  "size": 20
}

# Cursor分页
GET /api/users?cursor=eyJpZCI6MTAwMX0&size=20
Response: {
  "data": [...],
  "next_cursor": "eyJpZCI6MTAyMH0",
  "has_more": true
}
```

**为什么需要它：** 减少单次响应数据量，提升性能，避免内存溢出。

**Offset vs Cursor：** Offset简单但大数据集翻页慢且有数据漂移问题，Cursor性能稳定但实现复杂。

---

## 6. GraphQL

**一句话定义：** 一种API查询语言，客户端可以精确请求所需的数据结构。

**通俗类比：** 像点餐自助餐，你想要什么菜、多少量，完全自己搭配。

**具体示例：**
```graphql
# 查询
query {
  user(id: "1001") {
    name
    email
    orders(first: 5) {
      id
      total
      items {
        product { name }
        quantity
      }
    }
  }
}

# 修改
mutation {
  createUser(input: { name: "张三", email: "zhang@example.com" }) {
    id
    name
  }
}
```

**为什么需要它：** 解决REST的过度获取和不足获取问题，一次请求获取精确需要的数据。

**与REST对比：** REST每个端点返回固定结构，GraphQL单个端点返回任意结构，由客户端决定。

---

## 7. gRPC（protobuf/流式调用）

**一句话定义：** 基于HTTP/2和Protocol Buffers的高性能RPC框架。

**通俗类比：** 像对讲机通信，比电话（HTTP）更快更省流量，但需要约定暗号（protobuf）。

**具体示例：**
```protobuf
// 用户服务定义
service UserService {
  rpc GetUser (GetUserRequest) returns (User);
  rpc ListUsers (ListUsersRequest) returns (stream User);  // 服务端流
}

message GetUserRequest {
  string id = 1;
}

message User {
  string id = 1;
  string name = 2;
  string email = 3;
}
```

**为什么需要它：** 提供比REST更高的性能，强类型契约，支持流式通信。

**与REST对比：** gRPC使用二进制协议更高效，但浏览器支持有限，调试不如REST直观。

---

## 8. WebSocket全双工通信

**一句话定义：** 建立持久连接，支持客户端和服务端双向实时通信。

**通俗类比：** 像电话通话，双方可以同时说话和听，而不是像对讲机轮流发言。

**具体示例：**
```javascript
// 客户端
const ws = new WebSocket('ws://localhost:8080/chat');
ws.onmessage = (event) => {
  console.log('收到消息:', event.data);
};
ws.send('你好服务器');

// 服务端（Node.js）
wss.on('connection', (ws) => {
  ws.on('message', (message) => {
    ws.send(`收到: ${message}`);
  });
});
```

**为什么需要它：** 实现实时通信场景，如聊天、股票行情、在线游戏等。

**与HTTP轮询对比：** 轮询是客户端定时询问，WebSocket是服务端主动推送，延迟更低、效率更高。

---

## 9. API版本控制（URL/Header/Query）

**一句话定义：** 当API发生不兼容变更时，通过版本号让新旧版本共存。

**通俗类比：** 像软件版本，Windows 10和Windows 11可以同时使用。

**具体示例：**
```
# URL版本（推荐）
GET /api/v1/users
GET /api/v2/users

# Header版本
GET /api/users
Accept: application/vnd.myapi.v2+json

# Query参数版本
GET /api/users?version=2
```

**为什么需要它：** 保证向后兼容，让现有客户端不受新版本影响。

**三种方式对比：** URL最直观易用，Header更RESTful但调试不便，Query参数灵活但不够规范。

---

## 10. 幂等性设计

**一句话定义：** 同一个请求执行多次，结果与执行一次相同。

**通俗类比：** 像设置闹钟，设置10次和设置1次效果一样。

**具体示例：**
```java
// 幂等性设计示例
@PostMapping("/orders")
public Order createOrder(@RequestHeader("Idempotency-Key") String key) {
    // 检查是否已处理过
    Order existing = orderService.findByIdempotencyKey(key);
    if (existing != null) {
        return existing;  // 直接返回之前的结果
    }
    // 首次执行，创建订单
    return orderService.create(key, orderRequest);
}
```

**为什么需要它：** 防止网络重试、消息重复消费导致数据不一致。

**天然幂等的方法：** GET（查询）、PUT（全量替换）、DELETE（删除）天然幂等，POST需要额外设计。

---

## 11. HATEOAS

**一句话定义：** 在响应中包含相关操作的链接，客户端通过链接发现可用操作。

**通俗类比：** 像导航网站，每个页面都提供相关页面的链接，你不需要记住所有网址。

**具体示例：**
```json
{
  "id": "1001",
  "name": "张三",
  "links": [
    { "rel": "self", "href": "/users/1001" },
    { "rel": "orders", "href": "/users/1001/orders" },
    { "rel": "edit", "href": "/users/1001", "method": "PUT" },
    { "rel": "delete", "href": "/users/1001", "method": "DELETE" }
  ]
}
```

**为什么需要它：** 让API具有可发现性，客户端不需要硬编码所有URL。

**与普通REST对比：** 普通REST需要客户端知道所有URL，HATEOAS通过响应中的链接引导客户端。

---

## 12. OpenAPI/Swagger

**一句话定义：** 用标准化格式描述REST API，便于文档生成、测试和代码生成。

**通俗类比：** 像建筑蓝图，描述API的结构、参数和返回值，施工方按图施工。

**具体示例：**
```yaml
openapi: 3.0.0
info:
  title: 用户API
  version: 1.0.0
paths:
  /users/{id}:
    get:
      summary: 获取用户
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
```

**为什么需要它：** 自动生成文档、生成客户端SDK、验证API契约是否一致。

**与Postman对比：** OpenAPI是标准规范，Postman是工具；OpenAPI可以作为Postman集合的来源。
