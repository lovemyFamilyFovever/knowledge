---
title: "GraphQL从入门到精通"
tags: []
source: "baike"
source_path: "技术文章 / Web开发框架"
collected: "2026-09-05"
status: "imported"
---

# GraphQL从入门到精通

# GraphQL 从入门到精通完全指南

## 1. GraphQL vs REST：深度对比与适用场景

### 1.1 架构哲学对比

REST（Representational State Transfer）基于资源和HTTP动词，而GraphQL基于类型系统和查询语言。

```javascript
// REST典型的端点设计
GET /api/users/1          // 获取用户
GET /api/users/1/posts    // 获取用户的帖子
GET /api/users/1/friends  // 获取用户的好友

// GraphQL只需一个端点
POST /graphql
query {
  user(id: "1") {
    name
    posts {
      title
      comments {
        content
      }
    }
    friends {
      name
      avatar
    }
  }
}
```

### 1.2 数据获取效率

REST面临的主要问题是**过度获取（Over-fetching）和不足获取（Under-fetching）**：

```javascript
// REST过度获取示例 - 我们只需要用户名和头像
// 但会获取用户的所有字段
fetch('/api/users/1')
  .then(res => res.json())
  .then(user => {
    // 只用了两个字段，但获取了所有数据
    renderUser(user.name, user.avatar);
  });

// GraphQL精确获取
query {
  user(id: "1") {
    name
    avatar
  }
}
```

### 1.3 版本控制与演进

REST通常需要版本控制（v1, v2），GraphQL可以通过字段弃用优雅处理：

```graphql
type User {
  id: ID!
  name: String!
  # 标记字段为弃用，但仍然可用
  oldName: String @deprecated(reason: "Use `name` instead")
}
```

### 1.4 性能与监控

```javascript
// REST监控 - 简单但粒度粗
app.get('/api/users', (req, res) => {
  console.time('GET /api/users');
  // 处理逻辑
  console.timeEnd('GET /api/users');
});

// GraphQL监控 - 可以按字段级别监控
const resolvers = {
  Query: {
    users: async () => {
      console.time('users resolver');
      const users = await User.findAll();
      console.timeEnd('users resolver');
      return users;
    }
  },
  User: {
    posts: async (user) => {
      console.time(`posts for user ${user.id}`);
      const posts = await Post.findByUserId(user.id);
      console.timeEnd(`posts for user ${user.id}`);
      return posts;
    }
  }
};
```

### 1.5 适用场景对比

**选择REST的场景**：
- 简单的CRUD应用
- 缓存要求高的场景（HTTP缓存）
- 文件上传/下载
- 微服务间的简单通信
- 团队对GraphQL不熟悉

**选择GraphQL的场景**：
- 复杂的关联数据查询
- 移动应用（需要优化数据传输）
- 需要高度灵活的前端
- 多个客户端（Web、iOS、Android）使用相同API
- 微服务聚合层（BFF - Backend for Frontend）

---

## 2. Schema定义语言（SDL）深入解析

### 2.1 核心类型系统

```graphql
# 标量类型
scalar Date
scalar JSON

# 枚举类型
enum Role {
  ADMIN
  USER
  MODERATOR
}

# 接口类型
interface Node {
  id: ID!
}

# 联合类型
union SearchResult = User | Post | Comment

# 输入类型
input CreateUserInput {
  name: String!
  email: String!
  age: Int
  role: Role = USER
}

# 对象类型
type User implements Node {
  id: ID!
  name: String!
  email: String!
  age: Int
  role: Role!
  posts: [Post!]!
  createdAt: Date!
  
  # 计算字段
  fullName: String!
  
  # 带参数的字段
  friends(limit: Int = 10): [User!]!
}
```

### 2.2 查询（Query）类型

```graphql
type Query {
  # 单个资源查询
  user(id: ID!): User
  
  # 列表查询与分页
  users(
    filter: UserFilter
    sort: UserSort
    pagination: PaginationInput
  ): UserConnection!
  
  # 搜索查询
  search(term: String!, types: [SearchType!]): [SearchResult!]!
  
  # 当前用户
  me: User @auth
}

# 分页游标实现
type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type UserEdge {
  node: User!
  cursor: String!
}

type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}
```

### 2.3 变更（Mutation）类型

```graphql
type Mutation {
  # 创建
  createUser(input: CreateUserInput!): CreateUserPayload!
  
  # 更新
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
  
  # 删除
  deleteUser(id: ID!): DeleteUserPayload!
  
  # 批量操作
  batchDeleteUsers(ids: [ID!]!): BatchDeletePayload!
  
  # 复杂业务逻辑
  transferFunds(fromId: ID!, toId: ID!, amount: Float!): TransferPayload!
}

# 统一的Payload设计
type CreateUserPayload {
  user: User
  errors: [UserError!]!
}

type UserError {
  field: String
  message: String!
  code: ErrorCode!
}

enum ErrorCode {
  ALREADY_EXISTS
  INVALID_INPUT
  PERMISSION_DENIED
}
```

### 2.4 订阅（Subscription）类型

```graphql
type Subscription {
  # 实时消息
  messageAdded(roomId: ID!): Message!
  
  # 状态变更
  userStatusChanged(userId: ID!): UserStatus!
  
  # 系统事件
  systemNotification: Notification!
  
  # 带过滤的订阅
  orderStatusUpdated(filter: OrderFilter): Order!
}
```

---

## 3. Resolver设计模式与最佳实践

### 3.1 基础Resolver结构

```javascript
// resolver组织模式
const resolvers = {
  // 标量类型解析
  Date: new GraphQLScalarType({
    name: 'Date',
    description: 'Date custom scalar type',
    parseValue(value) {
      return new Date(value); // 从客户端接收
    },
    serialize(value) {
      return value.toISOString(); // 发送到客户端
    },
    parseLiteral(ast) {
      if (ast.kind === Kind.INT) {
        return parseInt(ast.value, 10);
      }
      return null;
    },
  }),
  
  // 查询解析
  Query: {
    user: async (parent, args, context, info) => {
      // parent: 父解析器的返回值
      // args: 查询参数
      // context: 请求上下文（认证信息、数据加载器等）
      // info: 查询信息（字段、片段、变量等）
      
      const { id } = args;
      const user = await context.dataSources.userAPI.getUserById(id);
      
      if (!user) {
        throw new UserInputError('User not found', {
          invalidArgs: { id }
        });
      }
      
      return user;
    }
  },
  
  // 字段级解析器
  User: {
    fullName: (parent) => {
      // parent是User对象
      return `${parent.firstName} ${parent.lastName}`;
    },
    
    posts: async (parent, args, context) => {
      // 使用DataLoader避免N+1问题
      return context.dataLoaders.postLoader.load(parent.id);
    },
    
    // 条件字段解析
    email: async (parent, args, context) => {
      if (!context.user || 
          context.user.id !== parent.id && 
          context.user.role !== 'ADMIN') {
        return null; // 隐藏敏感信息
      }
      return parent.email;
    }
  }
};
```

### 3.2 高级Resolver模式

```javascript
// 模式1：Resolver链（Composition）
const resolvers = {
  Query: {
    dashboard: async (parent, args, context) => {
      // 并行执行多个解析器
      const [stats, recentOrders, notifications] = await Promise.all([
        context.resolvers.Query.stats(parent, args, context),
        context.resolvers.Query.recentOrders(parent, args, context),
        context.resolvers.Query.notifications(parent, args, context)
      ]);
      
      return { stats, recentOrders, notifications };
    }
  }
};

// 模式2：中间件模式（使用Apollo Server插件）
const loggingPlugin = {
  async requestDidStart() {
    return {
      async executionDidStart() {
        return {
          willResolveField({ source, args, context, info }) {
            const start = process.hrtime.bigint();
            return (error, result) => {
              const end = process.hrtime.bigint();
              const duration = Number(end - start) / 1e6;
              console.log(`${info.parentType.name}.${info.fieldName} took ${duration}ms`);
            };
          }
        };
      }
    };
  }
};

// 模式3：装饰器模式（TypeGraphQL示例）
import { Resolver, Query, Arg, Authorized, Ctx } from 'type-graphql';

@Resolver()
export class UserResolver {
  @Query(() => User, { nullable: true })
  @Authorized(['ADMIN', 'USER'])
  async user(
    @Arg('id') id: string,
    @Ctx() ctx: Context
  ): Promise<User | undefined> {
    return ctx.userService.findById(id);
  }
  
  @Query(() => UserConnection)
  @Authorized(['ADMIN'])
  async users(
    @Args() { filter, pagination }: UserQueryArgs,
    @Ctx() ctx: Context
  ): Promise<UserConnection> {
    return ctx.userService.findAll(filter, pagination);
  }
}
```

### 3.3 错误处理模式

```javascript
// 统一错误处理
class GraphQLValidationError extends ApolloError {
  constructor(message, field, code) {
    super(message, 'GRAPHQL_VALIDATION_FAILED');
    this.field = field;
    this.code = code;
  }
}

// 在resolver中使用
const resolvers = {
  Mutation: {
    updateUser: async (parent, { id, input }, context) => {
      try {
        // 验证输入
        if (!isValidEmail(input.email)) {
          throw new GraphQLValidationError(
            'Invalid email format',
            'email',
            'INVALID_INPUT'
          );
        }
        
        // 业务逻辑
        const user = await context.userService.update(id, input);
        
        return {
          user,
          errors: []
        };
      } catch (error) {
        if (error instanceof GraphQLValidationError) {
          return {
            user: null,
            errors: [{
              field: error.field,
              message: error.message,
              code: error.code
            }]
          };
        }
        throw error; // 重新抛出非预期错误
      }
    }
  }
};
```

---

## 4. N+1问题与DataLoader深度解析

### 4.1 问题重现

```graphql
# 查询：获取10个用户及其帖子
query {
  users {
    id
    name
    posts {
      id
      title
    }
  }
}

# 不使用DataLoader时的SQL查询
SELECT * FROM users LIMIT 10;
-- 对于每个用户：
SELECT * FROM posts WHERE user_id = 1;
SELECT * FROM posts WHERE user_id = 2;
-- ... 共执行11次查询（1 + 10）
```

### 4.2 DataLoader实现原理

```javascript
import DataLoader from 'dataloader';

// 创建DataLoader实例
const userLoader = new DataLoader(async (userIds) => {
  // 批量查询
  const users = await User.findAll({
    where: { id: userIds }
  });
  
  // 必须按照userIds顺序返回结果
  const userMap = new Map();
  users.forEach(user => userMap.set(user.id, user));
  
  return userIds.map(id => userMap.get(id) || null);
});

// 使用示例
async function getUserWithPosts(userId) {
  const user = await userLoader.load(userId);
  const posts = await postLoader.load(userId);
  return { user, posts };
}

// 在GraphQL上下文中配置
const server = new ApolloServer({
  context: () => ({
    loaders: {
      user: new DataLoader(batchUsers),
      post: new DataLoader(batchPosts),
      comment: new DataLoader(batchComments)
    }
  })
});
```

### 4.3 高级DataLoader模式

```javascript
// 模式1：带缓存的DataLoader
const createCacheKey = (id, args) => `${id}:${JSON.stringify(args)}`;

const userLoaderWithCache = new DataLoader(
  async (ids) => {
    // 批量获取
    const users = await fetchUsers(ids);
    
    // 更新缓存
    users.forEach(user => {
      const cacheKey = createCacheKey(user.id, {});
      cache.set(cacheKey, user, { ttl: 3600 });
    });
    
    return users;
  },
  {
    cacheKeyFn: (key) => createCacheKey(key, {})
  }
);

// 模式2：条件批处理
const conditionalLoader = new DataLoader(
  async (queries) => {
    // queries是数组，每个元素是查询参数
    // 分组处理不同类型的查询
    const groups = {
      byId: queries.filter(q => q.type === 'byId'),
      byEmail: queries.filter(q => q.type === 'byEmail')
    };
    
    const results = [];
    
    // 批量处理byId查询
    if (groups.byId.length > 0) {
      const ids = groups.byId.map(q => q.value);
      const users = await User.findAll({ where: { id: ids } });
      results.push(...users);
    }
    
    // 批量处理byEmail查询
    if (groups.byEmail.length > 0) {
      const emails = groups.byEmail.map(q => q.value);
      const users = await User.findAll({ where: { email: emails } });
      results.push(...users);
    }
    
    // 按顺序映射结果
    return queries.map(query => 
      results.find(r => {
        if (query.type === 'byId') return r.id === query.value;
        if (query.type === 'byEmail') return r.email === query.value;
        return false;
      })
    );
  },
  {
    maxBatchSize: 100 // 限制批量大小
  }
);
```

### 4.4 性能优化策略

```javascript
// 1. 请求级DataLoader实例（避免缓存冲突）
const context = ({ req }) => ({
  loaders: {
    user: new DataLoader(batchUsers),
    post: new DataLoader(batchPosts)
  },
  user: req.user
});

// 2. 嵌套查询优化
const resolvers = {
  User: {
    posts: async (user, args, { loaders }) => {
      // 第一层：获取帖子
      const posts = await loaders.post.loadMany(user.postIds);
      
      // 第二层：为每个帖子预加载作者信息
      const authorIds = [...new Set(posts.map(p => p.authorId))];
      await loaders.user.loadMany(authorIds);
      
      return posts;
    }
  }
};

// 3. 批量更新优化
const resolvers = {
  Mutation: {
    updateMultipleUsers: async (_, { updates }, { loaders }) => {
      // 重置DataLoader缓存
      loaders.user.clearAll();
      
      // 批量更新
      const updatedUsers = await Promise.all(
        updates.map(async ({ id, data }) => {
          const user = await User.update(data, { where: { id } });
          return user;
        })
      );
      
      // 更新DataLoader缓存
      updatedUsers.forEach(user => {
        loaders.user.prime(user.id, user);
      });
      
      return updatedUsers;
    }
  }
};
```

---

## 5. 认证与授权系统

### 5.1 JWT认证实现

```javascript
// 1. 服务器配置
import { ApolloServer } from 'apollo-server-express';
import jwt from 'jsonwebtoken';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: ({ req }) => {
    // 从请求头获取token
    const token = req.headers.authorization || '';
    
    // 验证token
    try {
      const user = jwt.verify(token.replace('Bearer ', ''), SECRET_KEY);
      return { user };
    } catch (error) {
      return { user: null };
    }
  }
});

// 2. 自定义指令实现认证
import { mapSchema, getDirective, MapperKind } from '@graphql-tools/utils';
import { defaultFieldResolver } from 'graphql';

function authDirectiveTransformer(schema) {
  return mapSchema(schema, {
    [MapperKind.OBJECT_FIELD]: (fieldConfig) => {
      const authDirective = getDirective(schema, fieldConfig, 'auth')?.[0];
      
      if (authDirective) {
        const { resolve = defaultFieldResolver } = fieldConfig;
        
        fieldConfig.resolve = async function (source, args, context, info) {
          if (!context.user) {
            throw new AuthenticationError('Not authenticated');
          }
          
          return resolve(source, args, context, info);
        };
      }
      
      return fieldConfig;
    }
  });
}

// 3. 使用自定义指令
const typeDefs = `
  directive @auth(requires: Role = ADMIN) on OBJECT | FIELD_DEFINITION
  
  type Query {
    publicData: String!
    privateData: String! @auth
    adminData: String! @auth(requires: ADMIN)
  }
  
  enum Role {
    ADMIN
    USER
  }
`;
```

### 5.2 基于角色的访问控制（RBAC）

```javascript
// 权限定义
const permissions = {
  Query: {
    users: ['ADMIN', 'MANAGER'],
    user: ['ADMIN', 'MANAGER', 'SELF']
  },
  Mutation: {
    createUser: ['ADMIN'],
    updateUser: ['ADMIN', 'SELF'],
    deleteUser: ['ADMIN']
  },
  User: {
    email: ['ADMIN', 'SELF'],
    salary: ['ADMIN', 'HR']
  }
};

// 权限检查中间件
const permissionsMiddleware = async (resolve, source, args, context, info) => {
  const { user } = context;
  
  // 获取字段路径
  const path = info.path.typename + '.' + info.fieldName;
  
  // 检查权限
  const requiredRoles = permissions[path] || [];
  if (requiredRoles.length === 0) {
    return resolve(source, args, context, info);
  }
  
  // 检查用户角色
  if (!requiredRoles.includes(user.role)) {
    // SELF特殊处理：检查是否操作自己的数据
    if (requiredRoles.includes('SELF')) {
      if (info.fieldName === 'email' && source.id === user.id) {
        return resolve(source, args, context, info);
      }
      if (info.fieldName === 'updateUser' && args.id === user.id) {
        return resolve(source, args, context, info);
      }
    }
    
    throw new ForbiddenError('Not authorized');
  }
  
  return resolve(source, args, context, info);
};

// 使用graphql-middleware
import { applyMiddleware } from 'graphql-middleware';
import { makeExecutableSchema } from '@graphql-tools/schema';

const schema = applyMiddleware(
  makeExecutableSchema({ typeDefs, resolvers }),
  permissionsMiddleware
);
```

### 5.3 数据级权限控制

```javascript
// 数据过滤器
const resolvers = {
  Query: {
    users: async (parent, args, context) => {
      const { user } = context;
      
      // 根据用户权限构建查询条件
      let where = {};
      
      if (user.role === 'ADMIN') {
        // 管理员可以看到所有用户
        where = {};
      } else if (user.role === 'MANAGER') {
        // 经理可以看到同部门的用户
        where = { departmentId: user.departmentId };
      } else {
        // 普通用户只能看到自己
        where = { id: user.id };
      }
      
      return User.findAll({ where });
    }
  },
  
  User: {
    // 字段级数据过滤
    sensitiveField: async (user, args, context) => {
      if (context.user.role === 'ADMIN') {
        return user.sensitiveField;
      }
      
      // 对于非管理员，检查是否查看自己的数据
      if (context.user.id === user.id) {
        return user.sensitiveField;
      }
      
      return null; // 隐藏敏感数据
    }
  }
};
```

---

## 6. 文件上传实现

### 6.1 标准文件上传

```graphql
# Schema定义
type Mutation {
  # 单文件上传
  uploadFile(file: Upload!): File!
  
  # 多文件上传
  uploadFiles(files: [Upload!]!): [File!]!
  
  # 带额外数据的文件上传
  createPostWithImage(
    title: String!
    content: String!
    image: Upload!
  ): Post!
}

type File {
  id: ID!
  filename: String!
  mimetype: String!
  encoding: String!
  url: String!
  size: Int!
}
```

```javascript
// Apollo Server配置
import { ApolloServer } from 'apollo-server-express';
import express from 'express';
import { graphqlUploadExpress } from 'graphql-upload';

const app = express();

// 配置文件上传中间件
app.use(graphqlUploadExpress({
  maxFileSize: 10000000, // 10MB
  maxFiles: 5
}));

const server = new ApolloServer({
  typeDefs,
  resolvers,
  uploads: false // 禁用内置上传处理
});

// Resolver实现
const resolvers = {
  Mutation: {
    uploadFile: async (parent, { file }) => {
      const { createReadStream, filename, mimetype, encoding } = await file;
      
      // 创建文件流
      const stream = createReadStream();
      
      // 保存到本地
      const path = `./uploads/${filename}`;
      await new Promise((resolve, reject) => {
        const writeStream = fs.createWriteStream(path);
        stream.pipe(writeStream);
        writeStream.on('finish', resolve);
        writeStream.on('error', reject);
      });
      
      // 或上传到云存储
      const url = await uploadToS3(stream, filename, mimetype);
      
      return {
        id: generateId(),
        filename,
        mimetype,
        encoding,
        url,
        size: fs.statSync(path).size
      };
    },
    
    createPostWithImage: async (parent, { title, content, image }) => {
      const { createReadStream, filename } = await image;
      const stream = createReadStream();
      
      // 上传图片
      const imageUrl = await uploadToS3(stream, filename, 'image/jpeg');
      
      // 创建帖子
      const post = await Post.create({
        title,
        content,
        imageUrl,
        createdAt: new Date()
      });
      
      return post;
    }
  }
};
```

### 6.2 分片上传与进度跟踪

```javascript
// 前端分片上传实现
import { useMutation } from '@apollo/client';
import { useCallback } from 'react';

const UPLOAD_MUTATION = gql`
  mutation UploadChunk($chunk: Upload!, $uploadId: String!, $index: Int!) {
    uploadChunk(chunk: $chunk, uploadId: $uploadId, index: $index) {
      uploadId
      index
      status
    }
  }
`;

const COMPLETE_UPLOAD = gql`
  mutation CompleteUpload($uploadId: String!) {
    completeUpload(uploadId: $uploadId) {
      url
      filename
    }
  }
`;

function FileUploader() {
  const [uploadChunk] = useMutation(UPLOAD_MUTATION);
  const [completeUpload] = useMutation(COMPLETE_UPLOAD);
  
  const uploadFile = useCallback(async (file) => {
    const chunkSize = 1024 * 1024; // 1MB
    const totalChunks = Math.ceil(file.size / chunkSize);
    const uploadId = generateUploadId();
    
    for (let i = 0; i < totalChunks; i++) {
      const start = i * chunkSize;
      const end = Math.min(start + chunkSize, file.size);
      const chunk = file.slice(start, end);
      
      await uploadChunk({
        variables: {
          chunk,
          uploadId,
          index: i
        }
      });
      
      // 更新进度
      const progress = Math.round(((i + 1) / totalChunks) * 100);
      setProgress(progress);
    }
    
    // 完成上传
    const result = await completeUpload({
      variables: { uploadId }
    });
    
    return result.data.completeUpload;
  }, [uploadChunk, completeUpload]);
  
  return (
    <input 
      type="file" 
      onChange={e => uploadFile(e.target.files[0])} 
    />
  );
}

// 服务端分片上传处理
const resolvers = {
  Mutation: {
    uploadChunk: async (_, { chunk, uploadId, index }) => {
      const { createReadStream } = await chunk;
      const stream = createReadStream();
      
      // 保存分片
      const chunkPath = `/tmp/uploads/${uploadId}/${index}`;
      await saveStreamToFile(stream, chunkPath);
      
      return { uploadId, index, status: 'uploaded' };
    },
    
    completeUpload: async (_, { uploadId }) => {
      const chunkDir = `/tmp/uploads/${uploadId}`;
      const files = fs.readdirSync(chunkDir);
      
      // 合并分片
      const outputPath = `/tmp/uploads/${uploadId}.mp4`;
      const writeStream = fs.createWriteStream(outputPath);
      
      for (const file of files.sort()) {
        const chunkPath = path.join(chunkDir, file);
        const readStream = fs.createReadStream(chunkPath);
        await new Promise((resolve) => {
          readStream.pipe(writeStream, { end: false });
          readStream.on('end', resolve);
        });
      }
      
      writeStream.end();
      
      // 上传到云存储
      const url = await uploadToS3(outputPath, `${uploadId}.mp4`);
      
      // 清理临时文件
      fs.rmdirSync(chunkDir, { recursive: true });
      fs.unlinkSync(outputPath);
      
      return { url, filename: `${uploadId}.mp4` };
    }
  }
};
```

---

## 7. 实时数据（Subscription）

### 7.1 基础Subscription实现

```javascript
// 使用WebSocket
import { PubSub } from 'graphql-subscriptions';
import { WebSocketServer } from 'ws';
import { useServer } from 'graphql-ws/lib/use/ws';
import { ApolloServer } from 'apollo-server-express';

const pubsub = new PubSub();

// WebSocket服务器
const wsServer = new WebSocketServer({
  server: httpServer,
  path: '/graphql',
});

const serverCleanup = useServer(
  {
    schema,
    context: async (ctx, msg, args) => {
      // 从连接参数获取认证信息
      const token = ctx.connectionParams?.authToken;
      const user = await validateToken(token);
      return { user, pubsub };
    },
    onConnect: async (ctx) => {
      // 连接时验证
      const token = ctx.connectionParams?.authToken;
      if (!token) {
        throw new Error('Auth token missing');
      }
    },
    onDisconnect(ctx, code, reason) {
      console.log('Disconnected!');
    },
  },
  wsServer
);

// Apollo Server配置
const server = new ApolloServer({
  schema,
  plugins: [
    {
      async serverWillStart() {
        return {
          async drainServer() {
            await serverCleanup.dispose();
          },
        };
      },
    },
  ],
});

// Resolver实现
const resolvers = {
  Subscription: {
    messageAdded: {
      subscribe: withFilter(
        () => pubsub.asyncIterator(['MESSAGE_ADDED']),
        (payload, variables, context) => {
          // 过滤：只接收特定房间的消息
          return payload.messageAdded.roomId === variables.roomId;
        }
      ),
    },
    
    userStatusChanged: {
      subscribe: withFilter(
        () => pubsub.asyncIterator(['USER_STATUS_CHANGED']),
        (payload, variables, context) => {
          // 检查权限：只接收关注用户的状态
          return context.user.following.includes(variables.userId);
        }
      ),
    },
  },
  
  Mutation: {
    sendMessage: async (_, { roomId, content }, context) => {
      const message = await Message.create({
        roomId,
        content,
        userId: context.user.id,
        createdAt: new Date(),
      });
      
      // 发布事件
      pubsub.publish('MESSAGE_ADDED', {
        messageAdded: message,
      });
      
      return message;
    },
  },
};
```

### 7.2 高级Subscription模式

```javascript
// 1. 实时订单状态更新
const resolvers = {
  Subscription: {
    orderStatusUpdated: {
      subscribe: withFilter(
        () => pubsub.asyncIterator(['ORDER_STATUS']),
        (payload, variables, context) => {
          const { order } = payload.orderStatusUpdated;
          
          // 多种过滤条件
          const matchesFilter = !variables.filter || 
            (!variables.filter.status || order.status === variables.filter.status) &&
            (!variables.filter.userId || order.userId === variables.filter.userId);
          
          // 权限检查
          const hasPermission = 
            context.user.role === 'ADMIN' || 
            order.userId === context.user.id ||
            context.user.managedOrders.includes(order.id);
          
          return matchesFilter && hasPermission;
        }
      ),
      
      // 解析器：可以转换数据格式
      resolve: (payload, args, context) => {
        const { order } = payload.orderStatusUpdated;
        
        // 根据用户角色返回不同数据
        if (context.user.role === 'ADMIN') {
          return order; // 完整数据
        } else {
          // 返回过滤后的数据
          return {
            id: order.id,
            status: order.status,
            updatedAt: order.updatedAt,
            // 不返回敏感信息
          };
        }
      }
    },
    
    // 2. 实时分析数据流
    analyticsDashboard: {
      subscribe: async function* (_, args, context) {
        // 使用异步生成器
        while (true) {
          const data = await collectAnalyticsData();
          yield { analyticsDashboard: data };
          
          // 等待下一个时间间隔
          await new Promise(resolve => setTimeout(resolve, 5000));
        }
      }
    },
    
    // 3. 频率限制的订阅
    frequentUpdates: {
      subscribe: withFilter(
        () => pubsub.asyncIterator(['UPDATE']),
        (payload, variables, context) => {
          // 简单的频率限制
          const now = Date.now();
          const lastUpdate = context.userLastUpdate.get(context.user.id) || 0;
          
          if (now - lastUpdate < 1000) { // 每秒最多一次
            return false;
          }
          
          context.userLastUpdate.set(context.user.id, now);
          return true;
        }
      )
    }
  }
};

// 前端订阅组件
import { useSubscription, gql } from '@apollo/client';

const ORDER_SUBSCRIPTION = gql`
  subscription OnOrderUpdate($orderId: ID!) {
    orderStatusUpdated(orderId: $orderId) {
      id
      status
      updatedAt
      statusMessage
    }
  }
`;

function OrderStatus({ orderId }) {
  const { data, loading } = useSubscription(ORDER_SUBSCRIPTION, {
    variables: { orderId },
    shouldResubscribe: true,
    onSubscriptionData: ({ subscriptionData }) => {
      // 处理实时数据
      console.log('New order status:', subscriptionData.data.orderStatusUpdated);
      
      // 触发通知
      if (subscriptionData.data.orderStatusUpdated.status === 'DELIVERED') {
        showNotification('Order delivered!');
      }
    }
  });
  
  if (loading) return <Loading />;
  
  return (
    <div>
      <h3>Order Status: {data?.orderStatusUpdated.status}</h3>
      <p>Last updated: {new Date(data?.orderStatusUpdated.updatedAt).toLocaleString()}</p>
    </div>
  );
}
```

---

## 8. 客户端库深度对比

### 8.1 Apollo Client核心功能

```javascript
// 1. 配置与初始化
import { 
  ApolloClient, 
  InMemoryCache, 
  createHttpLink,
  ApolloProvider,
  split
} from '@apollo/client';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { getMainDefinition } from '@apollo/client/utilities';
import { createClient } from 'graphql-ws';

// HTTP链接
const httpLink = createHttpLink({
  uri: '/graphql',
  credentials: 'include' // 包含cookies
});

// WebSocket链接
const wsLink = new GraphQLWsLink(createClient({
  url: 'ws://localhost:4000/graphql',
  connectionParams: () => ({
    authToken: localStorage.getItem('token'),
  }),
}));

// 根据操作类型拆分链接
const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  httpLink,
);

// 缓存配置
const cache = new InMemoryCache({
  typePolicies: {
    Query: {
      fields: {
        // 字段合并策略
        users: {
          keyArgs: ['filter'], // 缓存键包含过滤器
          merge(existing = { edges: [] }, incoming) {
            return {
              ...incoming,
              edges: [...existing.edges, ...incoming.edges],
            };
          },
        },
        
        // 乐观UI更新
        post: {
          read(existing, { args, toReference }) {
            return existing || toReference({
              __typename: 'Post',
              id: args.id,
            });
          },
        },
      },
    },
    
    User: {
      fields: {
        // 字段级别策略
        posts: {
          merge(existing = [], incoming, { args }) {
            if (args?.after) {
              return [...existing, ...incoming];
            }
            return incoming;
          },
        },
      },
    },
  },
});

// 创建客户端
const client = new ApolloClient({
  link: splitLink,
  cache,
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network', // 推荐策略
      nextFetchPolicy: 'cache-first',
    },
  },
});

// 2. 高级查询模式
import { useQuery, useLazyQuery, useMutation } from '@apollo/client';

// 实时查询更新
function UserProfile({ userId }) {
  const { data, loading, error, subscribeToMore } = useQuery(GET_USER, {
    variables: { id: userId },
    pollInterval: 30000, // 轮询（不推荐，优先用Subscription）
  });
  
  // 订阅用户更新
  useEffect(() => {
    const unsubscribe = subscribeToMore({
      document: USER_SUBSCRIPTION,
      variables: { userId },
      updateQuery: (prev, { subscriptionData }) => {
        if (!subscriptionData.data) return prev;
        const newUser = subscriptionData.data.userUpdated;
        
        return {
          ...prev,
          user: newUser,
        };
      },
    });