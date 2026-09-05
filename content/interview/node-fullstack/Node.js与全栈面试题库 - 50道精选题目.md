---
title: "Node.js与全栈面试题库 - 50道精选题目"
tags: []
source: "baike"
source_path: "技术题库 / Node.js与全栈"
collected: "2026-09-05"
status: "imported"
---

Node.js与全栈面试题库 - 50道精选题目
📦 Node.js与全栈面试题库
50道精选题目 - 从基础到高级的全面覆盖
📚 50道题目
🎯 详细解答
💡 实战技巧
📱 响应式设计
📦 Node.js基础
🚀 Express框架
🗄️ 数据库
🔌 API设计
🔐 认证授权
🚀 部署运维
📦 Node.js基础
1. Node.js是什么？它有哪些核心特性？
简单
Node.js
基础概念
JavaScript
查看答案
回答模板1：概念解释
Node.js是一个基于Chrome V8引擎的JavaScript运行时环境，它允许JavaScript在服务器端运行。
核心特性：
1.
事件驱动
：基于事件循环的非阻塞I/O
2.
单线程
：主线程单线程，但支持异步操作
3.
跨平台
：支持Windows、Linux、macOS
4.
npm生态
：拥有庞大的包管理生态系统
回答模板2：技术架构
Node.js的技术架构：
1.
V8引擎
：Google开发的JavaScript引擎
2.
libuv
：跨平台异步I/O库
3.
事件循环
：处理异步操作的核心机制
4.
Buffer
：处理二进制数据
5.
Stream
：处理流式数据
回答模板3：使用场景
Node.js的使用场景：
1.
Web服务器
：构建高性能Web应用
2.
API服务
：构建RESTful API
3.
实时应用
：聊天、协作工具
4.
工具链
：构建工具、脚本
5.
微服务
：构建微服务架构
2. 请解释Node.js的事件循环机制
困难
事件循环
异步编程
Node.js核心
查看答案
回答模板1：基础概念
事件循环是Node.js处理异步操作的核心机制。它是一个单线程的无限循环，不断检查是否有待处理的事件。
事件循环的阶段：
1.
timers
：执行setTimeout、setInterval回调
2.
pending callbacks
：执行系统级回调
3.
idle, prepare
：内部使用
4.
poll
：获取新的I/O事件
5.
check
：执行setImmediate回调
6.
close callbacks
：执行关闭回调
回答模板2：执行顺序
console.log('1');
setTimeout(() => console.log('2'), 0);
Promise.resolve().then(() => console.log('3'));
process.nextTick(() => console.log('4'));
setImmediate(() => console.log('5'));

// 输出顺序：1, 4, 3, 2, 5
回答模板3：优化建议
事件循环优化建议：
1.
避免阻塞
：不要执行长时间运行的同步代码
2.
使用异步API
：使用fs/promises代替fs
3.
使用Worker Threads
：CPU密集型任务
4.
监控延迟
：使用monitorEventLoopDelay
5.
拆分任务
：将长任务拆分为小任务
3. Node.js中的Buffer是什么？如何使用？
中等
Buffer
二进制数据
Node.js核心
查看答案
回答模板1：概念解释
Buffer是Node.js中处理二进制数据的类。它是一个固定长度的内存区域，用于存储二进制数据。
Buffer的使用场景：
1.
文件读写
：处理文件内容
2.
网络通信
：处理网络数据
3.
图像处理
：处理图像数据
4.
加密解密
：处理加密数据
回答模板2：使用示例
// 创建Buffer
const buf1 = Buffer.alloc(10); // 创建10字节的零填充Buffer
const buf2 = Buffer.from('hello'); // 从字符串创建
const buf3 = Buffer.from([1, 2, 3]); // 从数组创建

// Buffer操作
console.log(buf2.toString()); // 转换为字符串
console.log(buf2.length); // 获取长度
console.log(buf2.slice(0, 2)); // 切片

// Buffer与字符串转换
const utf8Buffer = Buffer.from('你好', 'utf8');
const base64String = utf8Buffer.toString('base64');
回答模板3：最佳实践
Buffer使用最佳实践：
1.
使用alloc
：避免使用Buffer()构造函数
2.
指定编码
：明确指定字符编码
3.
内存管理
：及时释放不再使用的Buffer
4.
使用Stream
：处理大文件时使用Stream
5.
安全考虑
：验证输入数据
4. Node.js中的Stream是什么？有哪些类型？
中等
Stream
流处理
大数据
查看答案
回答模板1：概念解释
Stream是Node.js中处理流式数据的抽象接口。它允许你以块的方式处理数据，而不是一次性加载整个数据。
Stream的四种类型：
1.
Readable
：可读流，如fs.createReadStream
2.
Writable
：可写流，如fs.createWriteStream
3.
Duplex
：双工流，可读可写，如TCP socket
4.
Transform
：转换流，如zlib.createGzip
回答模板2：使用示例
// 可读流
const readable = fs.createReadStream('file.txt', {
    encoding: 'utf8',
    highWaterMark: 1024
});

readable.on('data', (chunk) => {
    console.log(`收到 ${chunk.length} 字节数据`);
});

// 可写流
const writable = fs.createWriteStream('output.txt');
writable.write('第一行\n');
writable.write('第二行\n');
writable.end();

// 管道流
readable.pipe(writable);
回答模板3：使用场景
Stream的使用场景：
1.
文件处理
：读取/写入大文件
2.
网络通信
：HTTP请求/响应
3.
数据压缩
：gzip、zlib
4.
数据转换
：数据格式转换
5.
实时数据
：日志处理、数据流
5. 什么是Node.js的模块系统？CommonJS和ES Modules有什么区别？
中等
模块系统
CommonJS
ES Modules
查看答案
回答模板1：概念解释
Node.js的模块系统允许你将代码组织成可重用的模块。主要有两种模块系统：
1.
CommonJS
：Node.js原生的模块系统
2.
ES Modules
：ECMAScript标准的模块系统
回答模板2：语法对比
// CommonJS
const fs = require('fs');
module.exports = {
    readFile: fs.readFileSync
};

// ES Modules
import fs from 'fs';
export const readFile = fs.readFileSync;

// 区别：
// 1. 加载方式：CommonJS同步加载，ES Modules异步加载
// 2. 导出方式：CommonJS使用module.exports，ES Modules使用export
// 3. 导入方式：CommonJS使用require，ES Modules使用import
// 4. 编译时：CommonJS运行时解析，ES Modules编译时解析
回答模板3：选择建议
选择建议：
1.
新项目
：推荐使用ES Modules
2.
Node.js项目
：可以使用CommonJS或ES Modules
3.
浏览器项目
：必须使用ES Modules
4.
兼容性
：CommonJS兼容性更好
5.
工具链
：现代工具链通常支持ES Modules
🚀 Express框架
21. Express是什么？它有哪些核心概念？
简单
Express
Web框架
Node.js
查看答案
回答模板1：概念解释
Express是Node.js最流行的Web应用框架，它提供了一系列强大的功能来构建Web和移动应用。
核心概念：
1.
路由
：处理HTTP请求
2.
中间件
：处理请求和响应
3.
模板引擎
：渲染HTML页面
4.
静态文件
：提供静态资源服务
回答模板2：基本使用
const express = require('express');
const app = express();

// 中间件
app.use(express.json());
app.use(express.static('public'));

// 路由
app.get('/', (req, res) => {
    res.send('Hello World!');
});

app.get('/users/:id', (req, res) => {
    res.json({ userId: req.params.id });
});

// 启动服务器
app.listen(3000, () => {
    console.log('服务器运行在端口3000');
});
回答模板3：最佳实践
Express最佳实践：
1.
项目结构
：按功能组织路由和中间件
2.
错误处理
：使用集中式错误处理
3.
安全性
：使用helmet、cors等中间件
4.
性能
：使用压缩、缓存等优化
5.
测试
：编写单元测试和集成测试
22. 什么是Express中间件？如何自定义中间件？
中等
中间件
Express
请求处理
查看答案
回答模板1：概念解释
中间件是Express中处理请求和响应的函数。它可以访问请求对象（req）、响应对象（res）和下一个中间件函数（next）。
中间件的功能：
1.
执行代码
：执行任何代码
2.
修改请求/响应
：修改req和res对象
3.
结束请求-响应循环
：不调用next
4.
调用下一个中间件
：调用next()
回答模板2：使用示例
// 全局中间件
app.use((req, res, next) => {
    console.log(`${req.method} ${req.url}`);
    next();
});

// 路由中间件
const authMiddleware = (req, res, next) => {
    if (req.headers.authorization) {
        next();
    } else {
        res.status(401).json({ error: 'Unauthorized' });
    }
};

app.get('/protected', authMiddleware, (req, res) => {
    res.json({ message: 'Protected route' });
});

// 自定义中间件
const logger = (options) => {
    return (req, res, next) => {
        console.log(`[${options.level}] ${req.method} ${req.url}`);
        next();
    };
};

app.use(logger({ level: 'info' }));
回答模板3：最佳实践
中间件最佳实践：
1.
单一职责
：每个中间件只做一件事
2.
顺序重要
：中间件按顺序执行
3.
错误处理
：专门的错误处理中间件
4.
性能考虑
：避免在中间件中执行耗时操作
5.
测试
：为中间件编写单元测试
23. 如何处理Express中的错误？
中等
错误处理
Express
异常处理
查看答案
回答模板1：错误处理方法
Express中的错误处理方法：
1.
try-catch
：捕获同步错误
2.
next(err)
：传递错误到下一个中间件
3.
错误处理中间件
：专门处理错误
4.
异步错误处理
：使用async/await
回答模板2：代码示例
// try-catch处理
app.get('/user/:id', async (req, res, next) => {
    try {
        const user = await User.findById(req.params.id);
        if (!user) {
            return res.status(404).json({ error: 'User not found' });
        }
        res.json(user);
    } catch (err) {
        next(err);
    }
});

// 错误处理中间件
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Something went wrong!' });
});

// 异步错误处理包装器
const asyncHandler = (fn) => (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
};

app.get('/user/:id', asyncHandler(async (req, res) => {
    const user = await User.findById(req.params.id);
    res.json(user);
}));
回答模板3：最佳实践
错误处理最佳实践：
1.
集中式处理
：使用统一的错误处理中间件
2.
错误分类
：区分不同类型的错误
3.
日志记录
：记录错误信息
4.
用户友好
：返回用户友好的错误信息
5.
测试
：测试错误处理逻辑
24. Express中如何处理文件上传？
中等
文件上传
multer
文件处理
查看答案
回答模板1：基础方法
Express中处理文件上传通常使用multer中间件。
multer的功能：
1.
处理multipart/form-data
：处理表单数据
2.
文件过滤
：过滤文件类型
3.
存储控制
：控制文件存储位置
4.
文件大小限制
：限制文件大小
回答模板2：使用示例
const multer = require('multer');

// 配置存储
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, 'uploads/');
    },
    filename: (req, file, cb) => {
        cb(null, Date.now() + '-' + file.originalname);
    }
});

// 文件过滤
const fileFilter = (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) {
        cb(null, true);
    } else {
        cb(new Error('只能上传图片文件'), false);
    }
};

const upload = multer({ 
    storage,
    fileFilter,
    limits: { fileSize: 1024 * 1024 * 5 } // 5MB
});

// 路由
app.post('/upload', upload.single('image'), (req, res) => {
    res.json({ file: req.file });
});
回答模板3：最佳实践
文件上传最佳实践：
1.
验证文件类型
：只允许特定类型的文件
2.
限制文件大小
：防止上传大文件
3.
安全存储
：将上传目录放在public之外
4.
异步处理
：使用异步操作处理文件
5.
错误处理
：处理上传失败的情况
25. Express中如何实现路由分组？
中等
路由分组
路由组织
Express
查看答案
回答模板1：基础方法
Express中可以使用Router对象实现路由分组。
路由分组的好处：
1.
代码组织
：按功能组织路由
2.
中间件共享
：组内路由共享中间件
3.
前缀管理
：统一添加路由前缀
4.
模块化
：便于维护和测试
回答模板2：使用示例
// userRoutes.js
const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
    res.json({ users: [] });
});

router.get('/:id', (req, res) => {
    res.json({ user: req.params.id });
});

module.exports = router;

// app.js
const userRoutes = require('./userRoutes');
const postRoutes = require('./postRoutes');

// 路由分组
app.use('/api/users', userRoutes);
app.use('/api/posts', postRoutes);
回答模板3：最佳实践
路由分组最佳实践：
1.
按功能分组
：按功能模块组织路由
2.
使用前缀
：统一API前缀
3.
中间件共享
：组内共享认证中间件
4.
版本控制
：使用API版本前缀
5.
文档
：为每个路由组编写文档
🗄️ 数据库
31. MongoDB是什么？它有哪些核心概念？
简单
MongoDB
NoSQL
数据库
查看答案
回答模板1：概念解释
MongoDB是一个基于文档的NoSQL数据库，它使用JSON-like文档存储数据。
核心概念：
1.
数据库
：容器，包含集合
2.
集合
：类似关系数据库的表
3.
文档
：类似关系数据库的行
4.
字段
：类似关系数据库的列
回答模板2：使用示例
// 连接MongoDB
const mongoose = require('mongoose');
mongoose.connect('mongodb://localhost:27017/myapp');

// 定义Schema
const userSchema = new mongoose.Schema({
    name: String,
    email: String,
    age: Number,
    createdAt: { type: Date, default: Date.now }
});

// 创建Model
const User = mongoose.model('User', userSchema);

// 创建文档
const user = new User({
    name: 'John',
    email: 'john@example.com',
    age: 25
});
await user.save();

// 查询
const users = await User.find({ age: { $gte: 18 } });
回答模板3：使用场景
MongoDB的使用场景：
1.
内容管理系统
：灵活的文档结构
2.
实时分析
：高写入性能
3.
物联网
：处理大量传感器数据
4.
移动应用
：灵活的数据模型
5.
原型开发
：快速迭代
32. SQL和NoSQL数据库有什么区别？
中等
SQL
NoSQL
数据库对比
查看答案
回答模板1：核心区别
SQL和NoSQL数据库的主要区别：
1.
数据模型
：SQL使用表，NoSQL使用文档/键值对等
2.
Schema
：SQL需要预定义Schema，NoSQL灵活
3.
查询语言
：SQL使用SQL语言，NoSQL使用各自API
4.
扩展性
：SQL垂直扩展，NoSQL水平扩展
回答模板2：详细对比
SQL数据库
：
• 数据结构：表、行、列
• Schema：固定Schema
• 查询：SQL语言
• 事务：ACID事务
• 扩展：垂直扩展
NoSQL数据库
：
• 数据结构：文档、键值、列族、图
• Schema：动态Schema
• 查询：各数据库自己的API
• 事务：最终一致性（部分支持ACID）
• 扩展：水平扩展
回答模板3：选择建议
选择建议：
1.
使用SQL
：需要复杂查询、事务、数据一致性
2.
使用NoSQL
：需要灵活Schema、高扩展性、快速开发
3.
混合使用
：不同场景使用不同数据库
4.
考虑团队
：团队熟悉哪种技术
5.
考虑成本
：运维成本和开发成本
33. 什么是Redis？它有哪些使用场景？
中等
Redis
缓存
内存数据库
查看答案
回答模板1：概念解释
Redis是一个开源的内存数据结构存储系统，可用作数据库、缓存和消息中间件。
Redis的特点：
1.
高性能
：基于内存，读写速度快
2.
数据结构丰富
：支持字符串、哈希、列表等
3.
持久化
：支持RDB和AOF持久化
4.
分布式
：支持集群和哨兵模式
回答模板2：使用场景
Redis的使用场景：
1.
缓存
：缓存数据库查询结果
2.
会话存储
：存储用户会话
3.
消息队列
：使用List或Stream
4.
排行榜
：使用Sorted Set
5.
计数器
：使用INCR命令
6.
分布式锁
：使用SETNX命令
回答模板3：使用示例
// Node.js中使用Redis
const redis = require('redis');
const client = redis.createClient();

// 连接
client.connect();

// 基本操作
await client.set('key', 'value');
const value = await client.get('key');

// 哈希操作
await client.hSet('user:1', 'name', 'John');
await client.hSet('user:1', 'age', '25');
const user = await client.hGetAll('user:1');

// 列表操作
await client.lPush('queue', 'task1');
const task = await client.rPop('queue');
🔌 API设计
41. 什么是RESTful API？它有哪些设计原则？
中等
RESTful
API设计
Web服务
查看答案
回答模板1：概念解释
RESTful API是一种基于REST架构风格的API设计方法。它使用HTTP协议的标准方法来操作资源。
REST的核心原则：
1.
资源导向
：每个URL代表一个资源
2.
统一接口
：使用标准HTTP方法
3.
无状态
：服务器不保存客户端状态
4.
可缓存
：响应可缓存
回答模板2：设计示例
// RESTful API设计
GET    /api/users          // 获取用户列表
POST   /api/users          // 创建用户
GET    /api/users/:id      // 获取单个用户
PUT    /api/users/:id      // 更新用户
DELETE /api/users/:id      // 删除用户

// 嵌套资源
GET    /api/users/:id/posts    // 获取用户的帖子
POST   /api/users/:id/posts    // 为用户创建帖子

// 状态码
200 OK                    // 成功
201 Created               // 创建成功
204 No Content            // 删除成功
400 Bad Request           // 请求错误
401 Unauthorized          // 未授权
404 Not Found             // 未找到
500 Internal Server Error // 服务器错误
回答模板3：最佳实践
RESTful API设计最佳实践：
1.
使用名词
：URL使用名词而不是动词
2.
使用复数
：资源名称使用复数
3.
版本控制
：使用URL或Header版本控制
4.
分页
：返回分页数据
5.
过滤排序
：支持查询参数过滤排序
6.
错误处理
：返回统一的错误格式
42. GraphQL和RESTful API有什么区别？
中等
GraphQL
RESTful
API对比
查看答案
回答模板1：核心区别
GraphQL和RESTful API的主要区别：
1.
数据获取
：REST固定数据结构，GraphQL按需获取
2.
端点
：REST多个端点，GraphQL单个端点
3.
类型系统
：GraphQL有强类型系统
4.
版本控制
：REST需要版本，GraphQL不需要
回答模板2：详细对比
RESTful API
：
• 多个端点，每个资源一个端点
• 固定的数据结构
• 使用HTTP方法表示操作
• 需要版本控制
GraphQL
：
• 单个端点
• 客户端指定需要的数据
• 强类型系统
• 不需要版本控制
回答模板3：选择建议
选择建议：
1.
使用REST
：简单CRUD应用、缓存需求高
2.
使用GraphQL
：复杂数据需求、移动应用
3.
混合使用
：不同场景使用不同技术
4.
考虑团队
：团队熟悉哪种技术
5.
考虑性能
：GraphQL可能有N+1问题
43. 如何设计安全的API？
中等
API安全
认证授权
安全设计
查看答案
回答模板1：基础安全
API基础安全措施：
1.
HTTPS
：使用HTTPS加密通信
2.
认证
：验证用户身份
3.
授权
：控制用户权限
4.
输入验证
：验证所有输入
回答模板2：高级安全
API高级安全措施：
1.
速率限制
：防止暴力攻击
2.
输入过滤
：防止SQL注入、XSS
3.
CORS
：控制跨域请求
4.
安全头
：设置安全响应头
5.
日志监控
：记录安全事件
回答模板3：实现示例
// Express安全中间件
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const cors = require('cors');

// 安全头
app.use(helmet());

// 速率限制
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15分钟
    max: 100 // 限制每个IP 100个请求
});
app.use('/api/', limiter);

// CORS
app.use(cors({
    origin: 'https://example.com',
    methods: ['GET', 'POST'],
    allowedHeaders: ['Content-Type', 'Authorization']
}));
🔐 认证授权
44. 什么是JWT？它如何工作？
中等
JWT
认证
Token
查看答案
回答模板1：概念解释
JWT（JSON Web Token）是一种开放标准（RFC 7519），用于在各方之间安全地传输信息。
JWT的结构：
1.
Header
：包含算法和类型
2.
Payload
：包含声明（claims）
3.
Signature
：用于验证签名
回答模板2：使用示例
const jwt = require('jsonwebtoken');

// 生成Token
const token = jwt.sign(
    { userId: 123, role: 'admin' },
    'secret-key',
    { expiresIn: '1h' }
);

// 验证Token
const decoded = jwt.verify(token, 'secret-key');
console.log(decoded);

// Express中间件
const authMiddleware = (req, res, next) => {
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) {
        return res.status(401).json({ error: 'No token provided' });
    }
    
    try {
        const decoded = jwt.verify(token, 'secret-key');
        req.user = decoded;
        next();
    } catch (err) {
        res.status(401).json({ error: 'Invalid token' });
    }
};
回答模板3：最佳实践
JWT使用最佳实践：
1.
密钥安全
：使用强密钥，定期更换
2.
过期时间
：设置合理的过期时间
3.
刷新机制
：实现Token刷新
4.
存储安全
：安全存储Token
5.
撤销机制
：实现Token撤销
45. 什么是OAuth 2.0？它有哪些授权流程？
困难
OAuth 2.0
授权
第三方登录
查看答案
回答模板1：概念解释
OAuth 2.0是一个授权框架，允许第三方应用获取对HTTP服务的有限访问权限。
OAuth 2.0的授权流程：
1.
授权码模式
：最安全，适用于Web应用
2.
隐式模式
：适用于SPA
3.
密码模式
：适用于信任的客户端
4.
客户端凭证模式
：适用于机器对机器
回答模板2：授权码流程
// 1. 客户端重定向到授权服务器
GET /authorize?
    response_type=code&
    client_id=CLIENT_ID&
    redirect_uri=CALLBACK_URL&
    scope=read&
    state=xyz123

// 2. 用户授权后，授权服务器重定向回客户端
GET /callback?code=AUTH_CODE&state=xyz123

// 3. 客户端用授权码换取Access Token
POST /token
    grant_type=authorization_code&
    code=AUTH_CODE&
    redirect_uri=CALLBACK_URL&
    client_id=CLIENT_ID&
    client_secret=CLIENT_SECRET

// 4. 使用Access Token访问资源
GET /api/user
Authorization: Bearer ACCESS_TOKEN
回答模板3：使用场景
OAuth 2.0的使用场景：
1.
第三方登录
：使用Google、GitHub登录
2.
API访问
：允许第三方应用访问API
3.
微服务
：服务间授权
4.
移动应用
：移动应用授权
5.
企业应用
：企业内部应用授权
🚀 部署运维
46. 如何部署Node.js应用？
中等
部署
Node.js
运维
查看答案
回答模板1：部署方式
Node.js应用的部署方式：
1.
传统部署
：直接在服务器上运行
2.
Docker部署
：使用容器化部署
3.
云平台
：Heroku、AWS、Azure
4.
Serverless
：AWS Lambda、Vercel
回答模板2：Docker部署
# Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["node", "server.js"]

# docker-compose.yml
version: '3'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - MONGODB_URI=mongodb://mongo:27017/myapp
  mongo:
    image: mongo
    ports:
      - "27017:27017"
回答模板3：最佳实践
Node.js部署最佳实践：
1.
使用PM2
：进程管理和监控
2.
使用Nginx
：反向代理和负载均衡
3.
环境变量
：使用环境变量配置
4.
日志管理
：集中式日志管理
5.
监控告警
：应用性能监控
47. 什么是PM2？如何使用PM2管理Node.js应用？
中等
PM2
进程管理
Node.js
查看答案
回答模板1：概念解释
PM2是Node.js应用的进程管理器，它提供了进程守护、负载均衡、日志管理等功能。
PM2的功能：
1.
进程守护
：自动重启崩溃的进程
2.
负载均衡
：利用多核CPU
3.
日志管理
：集中式日志管理
4.
监控
：实时监控应用状态
回答模板2：使用示例
# 安装PM2
npm install -g pm2

# 启动应用
pm2 start app.js --name my-app

# 查看状态
pm2 status

# 查看日志
pm2 logs

# 重启应用
pm2 restart my-app

# 停止应用
pm2 stop my-app

# 删除应用
pm2 delete my-app

# 集群模式
pm2 start app.js -i max --name my-app

# 配置文件
pm2 ecosystem.config.js
回答模板3：最佳实践
PM2使用最佳实践：
1.
使用集群模式
：利用多核CPU
2.
设置环境变量
：使用ecosystem.config.js
3.
监控告警
：使用PM2监控
4.
日志管理
：配置日志轮转
5.
自动重启
：设置重启策略
48. 如何监控Node.js应用性能？
中等
性能监控
APM
Node.js
查看答案
回答模板1：监控指标
Node.js应用监控指标：
1.
系统指标
：CPU、内存、磁盘
2.
应用指标
：请求量、响应时间、错误率
3.
业务指标
：用户数、转化率
4.
依赖指标
：数据库、外部API
回答模板2：监控工具
Node.js监控工具：
1.
PM2
：进程监控
2.
Node Clinic
：性能分析
3.
New Relic
：APM工具
4.
Datadog
：全栈监控
5.
Prometheus + Grafana
：开源监控
回答模板3：实现示例
// 使用prom-client
const client = require('prom-client');

// 创建指标
const httpRequestDuration = new client.Histogram({
    name: 'http_request_duration_seconds',
    help: 'Duration of HTTP requests in seconds',
    labelNames: ['method', 'route', 'status_code'],
    buckets: [0.1, 0.5, 1, 2, 5]
});

// 中间件
app.use((req, res, next) => {
    const end = httpRequestDuration.startTimer();
    res.on('finish', () => {
        end({ method: req.method, route: req.route?.path, status_code: res.statusCode });
    });
    next();
});

// 暴露指标
app.get('/metrics', async (req, res) => {
    res.set('Content-Type', client.register.contentType);
    res.end(await client.register.metrics());
});
49. 如何实现Node.js应用的日志管理？
中等
日志管理
日志库
Node.js
查看答案
回答模板1：基础日志
Node.js基础日志方法：
1.
console.log
：最简单的日志
2.
文件日志
：写入文件
3.
结构化日志
：JSON格式日志
4.
日志级别
：debug、info、warn、error
回答模板2：使用Winston
const winston = require('winston');

// 创建logger
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new winston.transports.File({ filename: 'error.log', level: 'error' }),
        new winston.transports.File({ filename: 'combined.log' })
    ]
});

// 开发环境添加控制台输出
if (process.env.NODE_ENV !== 'production') {
    logger.add(new winston.transports.Console({
        format: winston.format.simple()
    }));
}

// 使用
logger.info('User logged in', { userId: 123 });
logger.error('Error occurred', { error: new Error('Something went wrong') });
回答模板3：最佳实践
日志管理最佳实践：
1.
结构化日志
：使用JSON格式
2.
日志级别
：合理使用日志级别
3.
日志轮转
：避免日志文件过大
4.
集中式日志
：使用ELK Stack等
5.
敏感信息
：避免记录敏感信息
50. 如何实现Node.js应用的健康检查？
中等
健康检查
监控
可靠性
查看答案
回答模板1：基础概念
健康检查是监控应用状态的重要机制，用于检测应用是否正常运行。
健康检查的类型：
1.
存活检查
：检查应用是否运行
2.
就绪检查
：检查应用是否准备好接收请求
3.
深度检查
：检查依赖服务是否正常
回答模板2：实现示例
// 基础健康检查
app.get('/health', (req, res) => {
    res.status(200).json({ status: 'ok' });
});

// 深度健康检查
app.get('/health/deep', async (req, res) => {
    const checks = {
        database: await checkDatabase(),
        redis: await checkRedis(),
        memory: checkMemory(),
        disk: checkDisk()
    };
    
    const isHealthy = Object.values(checks).every(check => check.status === 'ok');
    
    res.status(isHealthy ? 200 : 503).json({
        status: isHealthy ? 'ok' : 'error',
        checks
    });
});

// 检查函数
async function checkDatabase() {
    try {
        await mongoose.connection.db.admin().ping();
        return { status: 'ok', message: 'Database is accessible' };
    } catch (error) {
        return { status: 'error', message: error.message };
    }
}

function checkMemory() {
    const used = process.memoryUsage();
    const threshold = 1024 * 1024 * 100; // 100MB
    return {
        status: used.heapUsed < threshold ? 'ok' : 'warning',
        used: used.heapUsed,
        threshold
    };
}
回答模板3：最佳实践
健康检查最佳实践：
1.
定期检查
：设置定期检查
2.
超时设置
：设置合理的超时时间
3.
依赖检查
：检查关键依赖服务
4.
告警
：健康检查失败时告警
5.
文档
：记录健康检查端点
📚 Node.js与全栈面试题库 - 50道精选题目
持续更新中... | 支持移动端访问