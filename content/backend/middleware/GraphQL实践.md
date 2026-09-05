---
title: "GraphQL实践"
tags: []
source: "baike"
source_path: "开发术语 / 消息与中间件"
collected: "2026-09-05"
status: "imported"
---

# GraphQL实践

## Schema定义

```graphql
type User {
    id: ID!
    name: String!
    posts: [Post!]!
}

type Query {
    user(id: ID!): User
    users(first: Int, after: String): UserConnection!
}

type Mutation {
    createUser(input: CreateUserInput!): User!
}
```

## N+1问题

```graphql
# 查询10个用户及其帖子
# 可能产生: 1次查用户 + 10次查帖子 = 11次查询
```

解决：DataLoader批处理

```python
class PostLoader(DataLoader):
    async def batch_load_fn(self, user_ids):
        posts = await db.posts.find({"user_id": {"$in": user_ids}})
        # 按user_id分组返回
        return group_by(posts, user_ids)
```

## GraphQL vs REST

| 特性 | GraphQL | REST |
|------|---------|------|
| 数据获取 | 精确获取所需 | 可能过度/不足 |
| 版本管理 | 无需版本 | 需要v1/v2 |
| 缓存 | 复杂 | HTTP缓存简单 |
| 学习曲线 | 陡峭 | 平缓 |
| 适用 | 复杂前端 | 简单CRUD |
