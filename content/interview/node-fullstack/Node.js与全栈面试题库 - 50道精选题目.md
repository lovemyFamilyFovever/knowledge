---
title: "Node.js与全栈面试题库 - 50道精选题目"
tags: []
source: "baike"
source_path: "技术题库 / Node.js与全栈"
collected: "2026-09-05"
status: "imported"
---

本页覆盖 Node.js 运行时、异步并发与多进程、流与 I/O、Web 框架、数据库与 ORM、API 设计、认证授权到部署运维全链路共 50 道面试题，难度从初级到高级分布，可作为全栈 Node.js 岗位的系统复习清单。

## Node.js 运行时基础（10 题）

### 1. Node.js是什么？它有哪些核心特性？｜初级

Node.js 是一个基于 Chrome V8 引擎的 JavaScript 运行时，本质是「用 JS 写服务端」，靠事件驱动 + 非阻塞 I/O 在单线程上扛住高并发网络请求。

- 事件驱动：所有 I/O 走事件循环（event loop），回调在合适阶段被调度，主线程不会被磁盘/网络阻塞。
- 非阻塞 I/O：读文件、查库、发请求都返回异步结果（回调 / Promise / async-await），而非同步等待。
- 单线程模型：JS 执行在主线程单线程，CPU 密集与部分 I/O 由 libuv 线程池兜底，避免多线程锁竞争。
- 跨平台：同一份代码跑在 Windows / Linux / macOS，底层差异由 libuv 抽象。
- 生态：npm 是全球最大的包仓库，模块复用成本极低。

技术分层上，Node 由 V8（执行 JS）、libuv（异步 I/O 与事件循环）、内置模块（fs / net / crypto 等）与 Buffer / Stream 抽象组成。

> 💡 提示
> 面试常把「单线程」误解为「不能并行」——准确说法是：JS 执行单线程，但 I/O 与计算可由底层多线程并行完成。

> 🎯 关键要点
> - 运行时 ≠ 框架，Node 提供的是语言执行环境与系统能力封装
> - 事件循环是异步调度的核心，而非「多线程」
> - 非阻塞 I/O 适合高并发、低计算密度的网络服务
> - libuv 屏蔽了操作系统底层的异步差异
> - npm 生态是 Node 普及的关键推动力

> 🔍 追问
> - 为什么 Node 比传统多线程服务器更省内存？
> - 哪些场景不适合用 Node 做主服务？

### 2. 请解释Node.js的事件循环机制｜高级

事件循环是 Node 处理异步的核心：一个单线程无限循环，按固定阶段依次消费各自的任务队列，所有异步回调都在这些阶段被调度执行。

Node 的事件循环分为六个阶段，每轮循环依次经过：

1. **timers**：执行 `setTimeout` / `setInterval` 到期的回调（注意是「到期」，不是精确时间）。
2. **pending callbacks**：执行上一轮延迟到本节的系统级回调（如 TCP 错误）。
3. **idle, prepare**：内部使用，开发者基本无感。
4. **poll**：检索新的 I/O 事件（文件、网络），执行相关回调；此阶段会计算阻塞时长以决定何时回到 timers。
5. **check**：执行 `setImmediate` 回调。
6. **close callbacks**：执行 `socket.on('close')` 等关闭类回调。

每两个阶段之间会清空一遍**微任务队列**（`Promise.then` / `queueMicrotask` / `process.nextTick` 的回调）。其中 `process.nextTick` 不属于事件循环阶段，它有自己的「nextTick 队列」，会在每个阶段切换前、微任务之前优先清空。

```js
console.log('1');
setTimeout(() => console.log('2'), 0);
Promise.resolve().then(() => console.log('3'));
process.nextTick(() => console.log('4'));
setImmediate(() => console.log('5'));

// 输出顺序：1, 4, 3, 2, 5
```

原因：同步代码先打印 `1`；接着 `nextTick` 队列先于微任务清空 → 打印 `4`；然后微任务 `Promise.then` → 打印 `3`；同步栈与微任务清空后进入事件循环，timers 阶段执行 `setTimeout` → 打印 `2`；之后 check 阶段执行 `setImmediate` → 打印 `5`。

> ⚠️ 注意
> `setTimeout(…, 0)` 实际最小延迟约 1ms，且受 poll 阶段时长影响；它与 `setImmediate` 的相对先后在不同阶段调用时并不固定，只有「在 I/O 回调内」时 `setImmediate` 才稳定先于 `setTimeout`。

> 🎯 关键要点
> - 六个阶段顺序固定：timers → pending → idle/prepare → poll → check → close
> - 微任务（含 nextTick）在每个阶段之间清空，nextTick 优先于 Promise
> - poll 阶段决定何时切回 timers，是延迟的关键
> - setImmediate 属于 check 阶段，setTimeout 属于 timers 阶段
> - 长同步代码会阻塞整个循环，拖垮所有阶段

> 🔍 追问
> - 为什么 `process.nextTick` 递归调用会导致 I/O 饥饿？
> - 如何测量一次事件循环迭代的真实耗时？

### 3. Node.js中的Buffer是什么？如何使用？｜中级

Buffer 是 Node 用来直接操作二进制数据的类，底层是一段固定长度的原生内存（C++ 分配，不在 V8 堆里），用于在 JS 与文件系统、网络、加密等二进制接口之间搬运数据。

常用创建方式：

```js
// 推荐：分配时清零，避免读到脏内存
const buf1 = Buffer.alloc(10);

// 从字符串/数组/TypedArray 创建
const buf2 = Buffer.from('hello');
const buf3 = Buffer.from([1, 2, 3]);

// 危险的旧写法，可能包含历史残留数据，禁止使用
// const unsafe = new Buffer('x');

console.log(buf2.toString());            // 'hello'
console.log(buf2.length);                // 5
console.log(buf2.slice(0, 2).toString()); // 'he'

const utf8Buffer = Buffer.from('你好', 'utf8');
const base64 = utf8Buffer.toString('base64'); // 编码转换
```

- `Buffer.alloc(size)`：分配并清零，安全。
- `Buffer.allocUnsafe(size)`：只分配不清零，更快但有泄露旧数据风险，必须用 `.fill(0)` 处理敏感场景。
- `Buffer.from(...)`：从已有数据复制生成。

适用场景：文件读写、网络报文、图片/音视频处理、加密解密、序列化协议（protobuf 等）。

> 💡 提示
> 大 Buffer 不计入 V8 堆内存，但计入进程 RSS；大量 Buffer 也会造成「内存上涨」假象，排查时要区分堆内与堆外内存。

> 🎯 关键要点
> - Buffer 是堆外二进制容器，默认 UTF-8 编码
> - 永远用 alloc / from，禁用已废弃的 Buffer() 构造函数
> - allocUnsafe 快但需手动清零，禁止用于敏感数据
> - 大文件处理应配合 Stream，避免一次性 Buffer 占满内存
> - 跨编码转换用 toString(encoding) / Buffer.from(str, encoding)

> 🔍 追问
> - 为什么说 allocUnsafe 可能泄露密码？
> - Buffer 与 TypedArray 的底层关系是什么？

### 4. Node.js中的Stream是什么？有哪些类型？｜中级

Stream 是 Node 处理流式数据的抽象接口，让数据以「分块（chunk）」方式流动，而不是一次性加载进内存，因此能处理远超内存大小的数据。

Node 内置四种流：

1. **Readable（可读流）**：数据源，如 `fs.createReadStream`、`http.IncomingMessage`。
2. **Writable（可写流）**：数据汇，如 `fs.createWriteStream`、`http.ServerResponse`。
3. **Duplex（双工流）**：可读可写，如 TCP socket。
4. **Transform（转换流）**：读写同时做转换，如 `zlib.createGzip`、`crypto.createCipher`。

```js
const fs = require('fs');

// 可读流：逐块读取
const readable = fs.createReadStream('file.txt', {
  encoding: 'utf8',
  highWaterMark: 1024, // 每次最多读 1KB
});

readable.on('data', (chunk) => {
  console.log(`收到 ${chunk.length} 字节数据`);
});

// 可写流
const writable = fs.createWriteStream('output.txt');
writable.write('第一行\n');
writable.write('第二行\n');
writable.end();

// 管道：把可读流接到可写流，自动处理背压
readable.pipe(writable);
```

常见用途：大文件拷贝、HTTP 请求/响应体、gzip 压缩、日志流、音视频转码。

> 🎯 关键要点
> - 四种类型：Readable / Writable / Duplex / Transform
> - 流以 chunk 为单位，内存占用恒定，与文件大小无关
> - highWaterMark 控制内部缓冲水位，影响背压触发时机
> - pipe 会自动桥接背压，比手写 data/ write 更安全
> - 流错误必须监听 'error' 事件，否则进程可能崩溃

> 🔍 追问
> - 为什么不用 pipe 时 write 可能丢数据？
> - Transform 和 Duplex 的本质区别是什么？

### 5. 什么是Node.js的模块系统？CommonJS和ES Modules有什么区别？｜中级

Node 的模块系统把代码拆成可复用单元，并通过封装作用域避免全局污染。Node 同时支持两套方案：CommonJS（CJS，原生默认）与 ES Modules（ESM，标准）。

```js
// CommonJS
const fs = require('fs');
module.exports = { readFile: fs.readFileSync };

// ES Modules
import fs from 'fs';
export const readFile = fs.readFileSync;
```

核心差异对照：

| 维度 | CommonJS | ES Modules |
| --- | --- | --- |
| 语法 | `require` / `module.exports` | `import` / `export` |
| 加载时机 | 运行时同步加载 | 编译期静态解析 |
| 导出本质 | 导出值的拷贝（对象引用） | 导出实时只读绑定 |
| 顶层 this | 指向 `module.exports` | `undefined` |
| 条件加载 | 可写在 if 里 | 必须顶层静态（动态用 `import()`） |
| 文件标识 | `.js` 默认 CJS | `.mjs` 或 `package.json` 设 `"type":"module"` |

- CJS 是 Node 历史默认，依赖在 `require` 时执行，适合服务端脚本与大量旧生态。
- ESM 是语言标准，支持静态分析、tree-shaking、顶层 `await` 与 `import()` 动态导入。
- 同一项目可混用：用 `import` 导入 CJS 包时，Node 会将其 `module.exports` 作为默认导出。

> 💡 提示
> 包作者可用 `package.json` 的 `exports` 字段同时提供 CJS 与 ESM 入口（如 `require` 走 `./cjs`，`import` 走 `./esm`），让两种消费方式都兼容。

> 🎯 关键要点
> - Node 原生两套模块系统：CommonJS 与 ES Modules
> - CJS 运行时同步加载，ESM 编译期静态解析
> - ESM 导出是实时绑定，CJS 是值拷贝
> - package.json 的 type 字段决定 .js 的默认解析方式
> - 互操作：import 可引入 CJS，反过来 require 不支持 ESM 静态语法

> 🔍 追问
> - 为什么 ESM 里 `require` 不可用？
> - 顶层 await 在 CJS 里能用吗，为什么？

### 6. process.nextTick、setImmediate、Promise.then、setTimeout 的执行顺序是怎样的？请给出下面这段代码的输出顺序并解释原因（给出代码示例）｜高级

结论：在同一轮同步代码中，执行优先级为 `process.nextTick` > `Promise.then`（微任务）> `setTimeout`（timers 阶段）> `setImmediate`（check 阶段），但这个顺序只在「同步代码内触发」时稳定。

```js
setTimeout(() => console.log('timeout'), 0);
setImmediate(() => console.log('immediate'));
Promise.resolve().then(() => console.log('promise'));
process.nextTick(() => console.log('nextTick'));

console.log('sync');

// 输出：sync → nextTick → promise → timeout → immediate
```

原因拆解：

1. `console.log('sync')` 属于同步栈，最先执行。
2. 同步栈清空后，先清空 **nextTick 队列** → `nextTick`。
3. 再清空**微任务队列**（Promise） → `promise`。
4. 进入事件循环 **timers 阶段** → `timeout`。
5. 再到 **check 阶段** → `immediate`。

要注意 `setTimeout(..., 0)` 与 `setImmediate` 的相对顺序在「非 I/O 回调内」并不保证：二者都近似「下一轮」，谁先取决于 poll 阶段耗时。只有在 I/O 回调（如 `fs.readFile` 的回调）内部，`setImmediate` 才稳定先于 `setTimeout` 执行，因为 I/O 回调运行在 poll 阶段之后、check 阶段之前。

```js
const fs = require('fs');
fs.readFile(__filename, () => {
  setTimeout(() => console.log('timeout'), 0);
  setImmediate(() => console.log('immediate'));
});
// 稳定输出：immediate → timeout
```

> ⚠️ 注意
> `process.nextTick` 不在事件循环阶段里，它有自己的队列且优先级最高。若在 nextTick 回调里无限递归调用 `process.nextTick`，会饿死 I/O 回调，导致事件循环永远到不了 poll 阶段。

> 🎯 关键要点
> - 顺序：sync → nextTick → Promise 微任务 → setTimeout → setImmediate
> - nextTick 队列独立于事件循环，每阶段切换前优先清空
> - setTimeout 属 timers 阶段，setImmediate 属 check 阶段
> - 二者相对顺序仅在 I/O 回调内才稳定（immediate 先）
> - 递归 nextTick 会阻塞 I/O，应避免

> 🔍 追问
> - 为什么 setTimeout 0 实际上不会是 0 毫秒？
> - 如何用 nextTick 实现「在当前操作完成后、I/O 前」的逻辑？

### 7. Node.js 号称单线程，为什么还能处理高并发 I/O？libuv 线程池承担了什么，默认线程数是多少，哪些 API 走线程池？｜高级

结论：Node 的「单线程」指 JS 执行在单线程，但异步 I/O 由 libuv 借助操作系统能力 + 一个**线程池**并行完成，主线程只负责调度回调，因此能在少量线程上并发处理成千上万连接。

libuv 的线程池（`uv_threadpool`）默认 **4 个线程**（可通过环境变量 `UV_THREADPOOL_SIZE` 调整，上限通常 1024）。它承担的是「操作系统没有提供真正异步接口」或「需要计算」的任务：

- 文件系统：`fs.readFile` / `fs.writeFile` 等（注意 `fs.read`/`fs.write` 对已是异步 fd 的可能走不同路径）。
- 加密：`crypto.pbkdf2`、`crypto.scrypt`、`crypto.randomBytes` 等 CPU/系统调用密集操作。
- DNS：`dns.lookup`（底层 `getaddrinfo`，走线程池）；而 `dns.resolve` 走 UDP，不走线程池。
- 压缩：`zlib` 相关压缩/解压。
- 其他需要阻塞系统调用的地方。

网络 I/O（TCP/HTTP、UDP）本身由 libuv 的事件机制（epoll/kqueue/IOCP）在单线程上多路复用，**不走线程池**。

```bash
UV_THREADPOOL_SIZE=8 node server.js  # 调大线程池，适合大量并发文件/加密操作
```

含义：纯网络服务（如 API 网关）几乎用不到线程池，瓶颈在事件循环单线程；而「高并发 + 大量文件/加密」的服务若线程池过小，会出现任务排队（libuv 队列积压），此时调大 `UV_THREADPOOL_SIZE` 才有意义。

> ⚠️ 注意
> 线程池是「有限的共享资源」。若一个请求里同步调用 `crypto.pbkdf2` 且迭代次数很高，会占满线程池导致其他文件的读写也排队，表现为整体变慢但 CPU 不高——这是典型的线程池饥饿。

> 🎯 关键要点
> - 单线程指 JS 执行，I/O 由 libuv 并行处理
> - 线程池默认 4 个线程，由 UV_THREADPOOL_SIZE 控制
> - fs、crypto、dns.lookup、zlib 走线程池
> - 网络 I/O 走事件多路复用，不走线程池
> - 线程池饥饿会让 CPU 不高的服务整体变慢

> 🔍 追问
> - 为什么 dns.lookup 和 dns.resolve 性能特征不同？
> - 线程池满了之后新任务会怎样？

### 8. Node 的模块解析算法是怎样的（相对/绝对/核心/第三方、package.json 的 exports 字段）？require 出现循环依赖时会发生什么？｜高级

结论：CommonJS 的 `require` 按「核心模块 → 文件/相对路径 → node_modules 向上查找」的顺序解析，且会缓存已加载模块；`package.json` 的 `exports` 字段可精细控制对外暴露的子路径。`require` 出现循环依赖时，得到的是「尚未初始化完成」的部分导出对象，不会报错但可能拿到 `undefined`。

解析顺序：

1. **核心模块**：如 `require('fs')`，最高优先级，编译进二进制。
2. **绝对/相对路径**：`/a/b.js` 或 `./c.js`，直接定位文件。
3. **第三方模块**：从当前目录的 `node_modules` 开始，逐级向上直到根目录查找。
4. **文件补全**：尝试 `.js` / `.json` / `.node`，以及目录下的 `package.json` 的 `main` 字段，或目录 `index.js`。
5. **exports 字段**：若包有 `exports`，则对外路径被它限制，未声明的子路径会被拒绝访问（增强封装，也避免目录遍历）。

```json
{
  "name": "pkg",
  "exports": {
    ".": "./dist/index.js",
    "./utils": "./dist/utils.js"
  }
}
```

循环依赖示例：

```js
// a.js
const b = require('./b');
console.log('a 中 b.foo =', b.foo); // undefined（b 还没执行完）
exports.foo = 'a-foo';

// b.js
const a = require('./a');
console.log('b 中 a.foo =', a.foo); // undefined（a 还没执行到导出）
exports.foo = 'b-foo';
```

执行 `node a.js` 时：加载 a → 遇到 `require('./b')` → 转去加载 b → b 里 `require('./a')` 命中**缓存中的半成品 a**（此时 `a.exports` 还是 `{}`）→ a.foo 为 undefined → b 执行完返回 → 回到 a 继续，`a.foo` 此刻仍是 undefined（a 的导出语句在 require 之后）。

> ⚠️ 注意
> 循环依赖不报错，但很容易产生 `undefined` 导出，排查困难。ESM 因「实时绑定」在多数情况下表现更好，但同样需避免强循环。

> 🎯 关键要点
> - 解析顺序：核心 → 相对/绝对 → node_modules 向上
> - 文件补全尝试 .js/.json/.node，再读 main/index
> - exports 字段限制可访问子路径，提升封装与安全性
> - 循环依赖返回半成品缓存模块，导出可能是 undefined
> - 模块加载有缓存，重复 require 不会二次执行

> 🔍 追问
> - 如何用延迟 require 或函数化解循环依赖？
> - exports 与 main 字段的优先级谁高？

### 9. Node 的错误处理体系：错误分类（操作错误 vs 程序错误）、uncaughtException/unhandledRejection 为什么不能当兜底、domain 为何被废弃、正确的收尾方式｜高级

结论：Node 把错误分为「操作错误（可预期、可恢复）」与「程序错误（代码 bug，不可恢复）」；`uncaughtException` / `unhandledRejection` 只能做最后的日志与清理，绝不能当正常控制流；`domain` 因掩盖错误、与异步上下文错配已被废弃；正确做法是让错误沿调用链上抛、就近处理、对程序错误直接崩溃重启。

- **操作错误（Operational）**：如网络超时、文件不存在、参数非法。可预期，应捕获后重试/降级/返回 4xx。
- **程序错误（Programmer）**：如读了 undefined 的属性、调用了不存在的函数。属 bug，进程处于不确定状态，应让进程退出由守护进程（PM2/systemd）重启。

为什么不能把 `uncaughtException` 当兜底：

```js
process.on('uncaughtException', (err) => {
  console.error('捕获到未处理异常', err);
  // 危险：进程内存/状态可能已损坏，继续运行会悄悄产出错误结果
});
```

此时事件循环可能已损坏（某个回调栈被破坏），继续服务等于在定时炸弹上运行。`unhandledRejection` 同理：未处理的 Promise 拒绝若不处理，Node 默认会直接退出（历史版本是警告），说明官方也不建议「吞掉」它。

- **domain 被废弃**：`domain` 试图自动绑定异步上下文来捕获错误，但它无法正确跟踪 Promise 链与后续引入的 `async_hooks` 语义，还会静默吞错，官方明确标记为 deprecated。
- **正确收尾**：
  1. 同步错误用 `try/catch`，异步用 `async/await + try/catch` 或 `.catch()`。
  2. 框架层用集中式错误处理中间件（Express 的 4 参中间件）。
  3. 程序错误：在 `uncaughtException` / `unhandledRejection` 里只做日志 + 优雅关闭 + 退出（`process.exit(1)`）。
  4. 用进程管理器保证崩溃后自动拉起。

> ⚠️ 注意
> 监听了 `unhandledRejection` 却什么都不做（不退出）会让 Node 认为你「已处理」，从而不再强制退出，潜在错误被永久掩盖。

> 🎯 关键要点
> - 区分操作错误（可恢复）与程序错误（应崩溃重启）
> - uncaughtException 只能做日志+退出，不能当兜底逻辑
> - unhandledRejection 默认应导致进程退出
> - domain 已废弃，原因是对异步上下文追踪不可靠
> - 进程管理器负责崩溃后的自动恢复

> 🔍 追问
> - 为什么 PM2 集群模式下崩溃重启比自己 catch 一切更好？
> - async_hooks 与 AsyncLocalStorage 如何取代 domain？

### 10. Node 的内存管理与垃圾回收：堆的分代结构、常见内存泄漏形态（全局缓存、闭包、事件监听器、定时器未清理）、如何用 heap snapshot 定位｜高级

结论：Node 的堆沿用 V8 分代式 GC——新对象在「新生代」用 Scavenge 快速回收，存活较久的对象晋升到「老生代」用 Mark-Sweep / Mark-Compact 回收；内存上涨通常来自堆外引用未释放或老生代对象堆积，用 heap snapshot 对比差值即可定位泄漏点。

堆结构：

- **新生代（Young Generation）**：存放短命对象，分 from/to 两空间，Scavenge 复制存活对象，速度快、频率高。
- **老生代（Old Generation）**：存放长期存活对象，用标记-清除/标记-整理，频率低但停顿长（可通过 `--max-old-space-size` 调整上限，默认约 2GB）。

常见泄漏形态：

1. **全局缓存无限增长**：如 `global.cache[uid] = data` 只增不删。
2. **闭包持有大对象**：函数返回闭包长期持有外部大数组/连接。
3. **事件监听器重复绑定**：`emitter.on(...)` 在每次请求里绑定却从不 `off`，监听器数量线性增长（可用 `emitter.setMaxListeners` 预警）。
4. **定时器未清理**：`setInterval` 在请求内创建却无 `clearInterval`，回调闭包与依赖对象常驻。

定位方法：

```bash
node --inspect server.js  # 启动时开启调试端口；用 Chrome DevTools → Memory 拍快照对比
```

或在代码里用 `v8` / `heapdump` 库在峰值时抓取对比：

```js
const heapdump = require('heapdump');
setInterval(() => heapdump.writeSnapshot(`/tmp/heap-${Date.now()}.heapsnapshot`), 60000);
```

> 💡 提示
> RSS 上涨不等于堆泄漏：Buffer、Map/Set 的底层、C++ 对象、线程池结果都可能在堆外。要看 `process.memoryUsage()` 的 `heapUsed` 与 `external` 分别判断。

> 🎯 关键要点
> - 堆分新生代（Scavenge）与老生代（Mark-Sweep/Compact）
> - 老生代上限由 --max-old-space-size 控制
> - 四大泄漏源：全局缓存、闭包、监听器、定时器
> - heap snapshot 对比差值定位增长对象最有效
> - RSS 上涨需区分堆内与堆外（Buffer/external）

> 🔍 追问
> - 老生代 GC 停顿如何影响事件循环延迟？
> - 为什么 Map 比普通对象更容易悄悄泄漏？

## 异步、并发与多进程（8 题）

### 11. Node 的事件循环与浏览器事件循环有什么区别（宏任务/微任务的划分与执行时机）？｜高级

结论：两者都基于「宏任务队列 + 微任务队列」，但 Node 把宏任务进一步拆成**六个阶段**（timers/poll/check…），而浏览器只有「一个宏任务队列按先进先出执行」；微任务的触发时机也因此不同——浏览器每执行完一个宏任务就清空微任务，Node 在每个阶段切换之间才清空微任务。

| 维度 | 浏览器 | Node.js |
| --- | --- | --- |
| 宏任务结构 | 单一队列（task queue） | 多阶段队列（timer / poll / check …） |
| 微任务时机 | 每个宏任务后清空 | 每个阶段之间清空 |
| 典型宏任务 | setTimeout、setInterval、I/O、UI 渲染 | 同上，但 I/O 回调集中在 poll 阶段 |
| 特殊 API | requestAnimationFrame | setImmediate、process.nextTick |
| 微任务 | Promise.then、queueMicrotask | 同左，外加 nextTick（优先级更高） |

关键差异点：

- 浏览器中 `setTimeout` 与 `Promise` 的相对顺序稳定（先宏后微）；Node 中 `setTimeout` 与 `setImmediate` 的相对顺序在同步栈里不稳定，只在 I/O 回调内才有确定关系。
- `process.nextTick` 是 Node 独有，优先级高于所有微任务，且不属于事件循环阶段。
- 浏览器有 `requestAnimationFrame`、渲染管线；Node 没有 UI，I/O 由 libuv 统一抽象。

> 🎯 关键要点
> - 浏览器用单一宏任务队列，Node 用多阶段队列
> - 微任务清空时机不同：浏览器每宏任务后，Node 每阶段间
> - setImmediate 是 Node 独有，对应 check 阶段
> - nextTick 优先级高于 Promise 微任务
> - 二者 I/O 回调调度位置不同（Node 集中在 poll）

> 🔍 追问
> - 为什么同一个 setTimeout(0) 在两个环境延迟感知不同？
> - Node 的 nextTick 在浏览器里近似对应什么？

### 12. cluster 模块的原理是什么？它如何做负载均衡？如何实现零停机重启与多核利用？｜高级

结论：`cluster` 模块让一个主进程（master）`fork` 出多个工作进程（worker），共享同一个 TCP 端口；master 负责「接收连接并分发」实现多核利用，worker 各自是独立事件循环。配合 `worker.disconnect()` 可实现零停机重启。

原理：master 创建服务器并监听端口，新连接到来时由 master 通过 IPC 把 socket 句柄交给某个 worker 处理；这样多个 worker 并行处理请求，充分利用多核。

负载均衡策略（默认随 Node 版本演进）：

- 旧版 round-robin：master 轮询把连接分给各 worker，均衡且可控。
- 新版（部分平台）直接由操作系统内核在 `SO_REUSEPORT` 层面分发，master 只负责 fork，吞吐更高但均衡性略差。

零停机重启（graceful reload）示例：

```js
const cluster = require('cluster');
const os = require('os');

if (cluster.isMaster) {
  os.cpus().forEach(() => cluster.fork());

  cluster.on('message', (worker, msg) => {
    if (msg === 'reload') {
      // 逐个重启 worker
      const workers = Object.values(cluster.workers);
      const restart = (i) => {
        if (i >= workers.length) return;
        workers[i].disconnect(); // 停止接收新连接，处理完存量后退出
        workers[i].on('exit', () => cluster.fork());
        workers[i].on('exit', () => restart(i + 1));
      };
      restart(0);
    }
  });
} else {
  require('./server'); // 每个 worker 启动独立 HTTP 服务
}
```

要点：重启时先 `disconnect` 让 worker 不再接收新连接，等存量请求处理完自然退出，再 `fork` 新进程顶上，全程端口不释放、请求不丢。

> 💡 提示
> 用 PM2 的 `pm2 reload` 已封装了上述逻辑（`--no-daemon` 之外），日常生产直接用 PM2 集群模式更省心。

> 🎯 关键要点
> - master fork 多个 worker 共享同一端口实现多核
> - 负载均衡默认 round-robin，新内核走 SO_REUSEPORT
> - 零停机靠 disconnect + fork 逐个替换 worker
> - worker 崩溃 master 可监听 exit 自动拉起
> - 端口由 master 持有，worker 间不冲突

> 🔍 追问
> - 为什么多个 worker 能 bind 同一个端口不报错？
> - 共享内存/状态在 cluster 下如何设计？

### 13. worker_threads 与主线程如何通信？什么样的任务适合用它、什么样的任务不适合？｜高级

结论：`worker_threads` 提供真正的并行线程，通过 `MessagePort` 传递「可克隆数据」或 `SharedArrayBuffer` 共享内存与主线程通信；适合 CPU 密集计算，不适合 I/O 密集（I/O 本来就该走异步事件循环）。

通信方式：

```js
// main.js
const { Worker } = require('worker_threads');
const worker = new Worker(`
  const { parentPort } = require('worker_threads');
  parentPort.on('message', (n) => {
    parentPort.postMessage(fib(n)); // 计算后回传
  });
  function fib(n){ return n < 2 ? n : fib(n-1)+fib(n-2); }
`, { eval: true });

worker.on('message', (result) => console.log('结果', result));
worker.postMessage(40);
```

- **结构化克隆**：`postMessage` 默认深拷贝数据，无共享。
- **SharedArrayBuffer**：多线程共享同一段内存，需配合 `Atomics` 避免竞态。
- **MessageChannel**：线程间可建独立双向通道，不只限父子。

适合用 worker 的任务：

- 大数组排序、图像处理、加密/压缩、复杂数学（如斐波那契、模型推理预处理）。
- 需要长期占用 CPU、会阻塞事件循环的逻辑。

不适合：

- 网络 I/O、文件读写——这些异步 API 本就非阻塞，丢给 worker 反而多一次线程切换开销。
- 大量共享可变状态——加锁复杂度上升，往往不如拆服务。

> ⚠️ 注意
> worker 不是越多越好，线程有创建与上下文切换成本；一般按下限 `os.cpus().length` 控制池大小，并用队列复用 worker，避免每次任务都新建。

> 🎯 关键要点
> - worker 是真并行线程，靠 MessagePort 通信
> - postMessage 默认结构化克隆，SharedArrayBuffer 可共享
> - 适合 CPU 密集，不适合 I/O 密集
> - 用线程池复用 worker，别每任务新建
> - 共享内存需 Atomics 保证可见性与原子性

> 🔍 追问
> - worker_threads 与 child_process 的本质区别？
> - 如何用 worker 实现一个计算线程池？

### 14. child_process 的 spawn/fork/exec/execFile 有什么区别，各自适用什么场景？｜中级

结论：四者都用来启动子进程，区别在于「是否走 shell、输入输出处理方式、通信能力」。选错会导致注入风险或内存爆炸。

| API | 是否经 shell | 参数方式 | 输出处理 | 典型场景 |
| --- | --- | --- | --- | --- |
| `spawn` | 否 | 数组传参，安全 | 流式（stdout 是流） | 大输出、实时管道 |
| `exec` | 是（默认 `/bin/sh`） | 字符串命令 | 缓冲到回调（有上限） | 简单命令、需 shell 特性 |
| `execFile` | 否 | 数组传参 | 缓冲到回调 | 执行可执行文件、避免 shell |
| `fork` | 否 | 模块路径 | 内置 IPC 通道 | 跑 Node 子脚本、双向通信 |

```js
const { spawn, exec, execFile, fork } = require('child_process');

// 大输出、流式：用 spawn，避免内存爆
const ls = spawn('ls', ['-lh', '/usr']);
ls.stdout.on('data', (d) => process.stdout.write(d));

// 简单命令、输出小：用 exec（注意命令拼接风险）
exec('ls -lh /usr', { maxBuffer: 1024 * 1024 }, (err, stdout) => {
  console.log(stdout);
});

// 跑另一个 Node 脚本并双向通信：用 fork
const child = fork('./worker.js');
child.send({ task: 'compute' });
child.on('message', (r) => console.log(r));
```

- `exec`/`execFile` 用 `maxBuffer` 限制输出，超出会报错并杀进程，防止被大输出拖垮。
- `exec` 走 shell，拼接用户输入会命令注入；优先 `execFile` 或 `spawn` 的数组参数。

> 🎯 关键要点
> - spawn 流式、无 shell、适合大输出
> - exec 走 shell、有注入风险、输出有上限
> - execFile 无 shell、传参安全
> - fork 专跑 Node、带 IPC 通信
> - 永远用数组参数而非字符串拼接命令

> 🔍 追问
> - 为什么 exec 的输出过大进程会被杀？
> - fork 的 IPC 通道底层是什么？

### 15. 如何发现和诊断事件循环阻塞（event loop lag）？有哪些监控指标与工具？｜高级

结论：事件循环阻塞指「某一轮循环耗时过长」，表现为请求延迟突增但 CPU 不一定高。用 `monitorEventLoopDelay` 量化延迟，用 `blocked-at` / 火焰图定位具体慢函数，从「减少同步耗时、拆分大任务」入手治理。

量化延迟：

```js
const { monitorEventLoopDelay } = require('perf_hooks');
const h = monitorEventLoopDelay({ resolution: 10 });
h.enable();

setInterval(() => {
  // p99 延迟（毫秒），超过数十毫秒即明显阻塞
  console.log('event loop lag p99 =', h.percentile(99).toFixed(2), 'ms');
}, 1000);
```

诊断工具：

- `blocked-at`：记录每次阻塞发生的堆栈，直接指出哪一行同步代码耗时。
- `clinic.js` / `0x`：采集火焰图，看热点函数。
- `--prof` + `node --prof-process`：生成 V8 性能 profile。
- APM（Datadog / New Relic）：采集 `event loop latency` 指标并告警。

治理手段：

1. 把大循环拆成 `setImmediate` / `process.nextTick` 分片执行。
2. CPU 密集逻辑移到 `worker_threads`。
3. 避免正则灾难性回溯、大 JSON 同步 `parse`、同步文件读取。
4. JSON 序列化等热点改用更快实现（如 `simdjson` 思路的库）。

> ⚠️ 注意
> `monitorEventLoopDelay` 的 `resolution` 越小越精确但开销越大；生产用 10–20ms 即可。它测的是「循环迭代间隔」，不是单次回调耗时。

> 🎯 关键要点
> - lag 表现为延迟升、CPU 未必高
> - monitorEventLoopDelay 量化 p99 延迟
> - blocked-at 能定位阻塞代码行
> - 火焰图（0x/clinic）找热点函数
> - 治理靠分片、worker、避免同步重活

> 🔍 追问
> - lag 高但 CPU 低的典型原因有哪些？
> - 如何在生产低开销地持续观测 lag？

### 16. Node 进程内存持续上涨如何排查？heap snapshot 对比、--inspect 调试、常见修复手段｜高级

结论：内存上涨先区分「堆内（JS 对象）」还是「堆外（Buffer/原生）」，再用 `--inspect` + DevTools 拍多张 heap snapshot 做差值对比，锁定增长的对象类型与引用链，最后删除根引用或加清理逻辑。

排查流程：

```bash
node --inspect server.js   # 1. 开启调试，Chrome DevTools 连上抓快照
npx clinic heap -- node server.js   # 2. 也可用 clinic 自动采样
```

- 看 `process.memoryUsage()`：`heapUsed` 持续涨 → 堆泄漏；`external`/`rss` 涨而 `heapUsed` 稳定 → 堆外（Buffer、Map 底层、C++ 对象）。
- DevTools Memory 面板拍 3 张快照（启动后、跑一段业务后、再跑一段后），用 Comparison 视图看「新增 + 留存」的对象，定位到具体构造函数（如 `User`、闭包、`Buffer`）。
- 引用链（Retainers）会告诉你谁还持有它——往往是全局对象、未解绑的监听器、未清的定时器。

常见修复：

1. 给缓存加上限（LRU：`lru-cache`）或 TTL 自动过期。
2. `emitter.off` / `removeListener` 对称解绑，或用 `once`。
3. 请求级 `setInterval` 必须 `clearInterval`。
4. 大对象及时置 `null` 断开引用，让 GC 回收。

> 💡 提示
> 老生代涨到 `--max-old-space-size` 上限会抛 `FATAL ERROR: Reached heap limit` 崩溃；临时调大只是延后爆炸，根因必须修。

> 🎯 关键要点
> - 先分堆内/堆外，再选工具
> - 多张 snapshot 差值对比定位增长对象
> - Retainers 还原引用链找根因
> - LRU/过期/解绑/清定时器是常规修复
> - 调大内存上限只是治标

> 🔍 追问
> - heapUsed 稳定但 rss 涨说明什么？
> - 如何用 --inspect-brk 在启动时断点查泄漏？

### 17. AsyncLocalStorage 是什么？它如何实现跨异步链路的请求上下文（traceId/事务）传递？｜高级

结论：`AsyncLocalStorage`（ALS）基于 `async_hooks`，能在一次异步调用链（无论中间经过多少 `await`、Promise、回调）中保持同一份上下文对象，非常适合在无侵入情况下为每个请求绑定 `traceId`、数据库连接、事务等，取代已废弃的 `domain`。

基本用法：

```js
const { AsyncLocalStorage } = require('async_hooks');
const als = new AsyncLocalStorage();

function requestHandler(req, res) {
  const ctx = { traceId: req.headers['x-trace-id'] || genId(), userId: null };
  als.run(ctx, () => {
    // 在 run 内部（含其下所有异步调用）都能读到 ctx
    handle(req, res);
  });
}

function handle(req, res) {
  const ctx = als.getStore(); // 拿到当前请求的 ctx，无需逐层传参
  logger.info('处理请求', { traceId: ctx.traceId });
}
```

原理：`async_hooks` 跟踪每个异步资源的创建/销毁，ALS 在 `run` 时记录当前上下文，异步资源继承父资源的存储，因此跨 `await` 后仍能取到同一份。

数据库事务场景：

```js
als.run({ tx: await db.begin() }, async () => {
  await serviceA(); // 内部 db.query 自动用同一事务
  await serviceB();
  await als.getStore().tx.commit();
});
```

- 优势：上下文隐式传递，业务代码零侵入，比在 `req` 上挂属性更通用（也覆盖非 HTTP 场景如消息消费）。
- 代价：`async_hooks` 有性能开销，高频路径注意压测。

> ⚠️ 注意
> ALS 的 `getStore()` 只有在 `run` 的异步上下文内调用才有效；在 `run` 之外的顶层调用会返回 `undefined`。它不能跨进程、跨网络——微服务间仍需把 `traceId` 显式放进请求头。

> 🎯 关键要点
> - ALS 基于 async_hooks，跨异步链路保持上下文
> - 用 run 包裹，内部任意 await 后都能 getStore
> - 典型用途：traceId、请求级事务、租户上下文
> - 比 domain 安全，比逐层传参无侵入
> - 有性能开销，高频路径需压测

> 🔍 追问
> - ALS 与把 ctx 挂在 req 对象上相比有何优劣？
> - 为什么 ALS 无法跨微服务传递？

### 18. 如何实现 Node 服务的优雅退出（graceful shutdown）？信号处理、连接排空、超时强杀要注意什么？｜高级

结论：优雅退出 = 收到终止信号后「停止接收新连接 → 等待存量请求处理完 → 释放资源（DB 连接、消息订阅）→ 再退出」，并设超时兜底强杀，避免请求被硬切断或进程僵死。

标准实现：

```js
const server = require('./server');
const db = require('./db');

let shuttingDown = false;

async function shutdown(signal) {
  if (shuttingDown) return;
  shuttingDown = true;
  console.log(`收到 ${signal}，开始优雅退出`);

  // 1. 停止接收新连接（存量请求仍可处理）
  server.close(() => console.log('HTTP 连接已排空'));

  // 2. 关闭数据库/消息等外部资源
  await db.close();

  // 3. 超时强杀兜底
  setTimeout(() => {
    console.error('超时未退出，强制结束');
    process.exit(1);
  }, 10000).unref();
}

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
```

要点：

- `server.close()` 只拒绝新连接，已建立的请求继续处理，回调触发即「排空完成」。
- K8s/容器发送 `SIGTERM` 后通常给 30s 宽限期（`terminationGracePeriodSeconds`），强杀超时（如上 10s）应小于该值。
- `keep-alive` 连接在 `server.close` 后可能长期不关闭，可用 `server.closeIdleConnections()`（Node 18+）加速。
- 超时兜底必须 `setTimeout(...).unref()`，否则进程因该定时器永不退出。

> ⚠️ 注意
> 不要监听 `uncaughtException` 后继续运行来「避免退出」；程序错误应快速失败由编排器重启。优雅退出只处理「正常的关停」信号。

> 🎯 关键要点
> - 顺序：停收新连接 → 排空存量 → 释放资源 → 退出
> - SIGTERM/SIGINT 触发关停，K8s 用 SIGTERM
> - server.close 排空存量，closeIdleConnections 加速
> - 强杀超时需小于编排器宽限期
> - 兜底定时器要 unref 防止阻止退出
> - `unref()` 让句柄不阻止进程退出；`listen`、未清定时器、活跃连接都会让进程存活

> 🔍 追问
> - 为什么强杀超时必须大于连接排空时间？
> - 长连接（WebSocket）如何优雅关闭？
> - `unref()` 与 `ref()` 的区别是什么？为什么后台心跳定时器要 unref？
> - Node 进程在什么条件下才会自行退出？哪些句柄会阻止退出？

## 流与 I/O（5 题）

### 19. 流的背压（backpressure）机制是什么？write() 返回 false 时该怎么办？pipeline 为什么优于 pipe？｜高级

结论：背压是「生产快于消费」时流自动节流的保护机制。`writable.write(chunk)` 返回 `false` 表示内部缓冲已达 `highWaterMark`，此时应暂停读取（等 `drain` 事件再继续），否则内存会被无限堆积。`pipeline` 相比 `pipe` 自动处理错误传播、清理与回调，是官方推荐写法。

背压流程：

```js
const fs = require('fs');
const read = fs.createReadStream('big.iso');
const write = fs.createWriteStream('copy.iso');

read.on('data', (chunk) => {
  const ok = write.write(chunk);
  if (!ok) {
    read.pause();              // 缓冲满了，暂停读取
    write.once('drain', () => read.resume()); // 排空后恢复
  }
});
read.on('end', () => write.end());
```

- `write()` 返回 `false`：写缓冲超过 `highWaterMark`，数据虽已入队但应暂停上游。
- `drain` 事件：缓冲降到水位以下，恢复读取的时机。
- 不处理背压的后果：可读流一直 `data` 推送，可写流缓冲无限增长 → 内存爆炸。

为什么用 `pipeline`：

```js
const { pipeline } = require('stream/promises');

await pipeline(
  fs.createReadStream('big.iso'),
  zlib.createGzip(),
  fs.createCreateWriteStream('big.iso.gz')
);
```

- `pipeline` 自动在任一段出错时销毁整条链路，避免「源还在写、目标已崩」的半开状态。
- 支持 Promise，可 `try/catch` 统一处理。
- `pipe` 不会自动销毁源/目标，错误容易泄漏，已被官方标注为底层 API。

> ⚠️ 注意
> `pipe` 的坑：目标流报错时源流不会被自动销毁，会导致文件描述符与内存泄漏。`pipeline` 解决了这点。

> 🎯 关键要点
> - 背压=生产快于消费时的自动节流
> - write 返回 false 要 pause，等 drain 再 resume
> - 不处理背压会内存爆炸
> - pipeline 自动销毁整链、支持 Promise、更安全
> - pipe 不会自动清理，已被官方弱化

> 🔍 追问
> - highWaterMark 设太小会有什么性能问题？
> - pipeline 中某一阶段抛错，其他阶段如何被清理？

### 20. 如何用流实现大文件上传/下载而不把内存打爆？断点续传与 Range 请求怎么配合？｜高级

结论：大文件传输必须走流，边读边写、零整文件驻留内存；下载端用 HTTP `Range` 请求按字节区间分片拉取，配合服务端「根据 `Range` 头返回 206 + 对应字节流」，即可实现断点续传。

下载（服务端支持 Range）：

```js
const fs = require('fs');
const http = require('http');

http.createServer((req, res) => {
  const filePath = './big.iso';
  const stat = fs.statSync(filePath);
  const range = req.headers.range;

  if (range) {
    const [start, end] = range.replace(/bytes=/, '').split('-').map(Number);
    const to = end || stat.size - 1;
    res.writeHead(206, {
      'Content-Range': `bytes ${start}-${to}/${stat.size}`,
      'Accept-Ranges': 'bytes',
      'Content-Length': to - start + 1,
    });
    fs.createReadStream(filePath, { start, end: to }).pipe(res);
  } else {
    res.writeHead(200, { 'Content-Length': stat.size });
    fs.createReadStream(filePath).pipe(res);
  }
}).listen(3000);
```

上传（客户端用流把本地大文件切片推给服务端）：

```js
const fs = require('fs');
const http = require('http');

const file = fs.createReadStream('./big.iso'); // 不整文件读入内存
const req = http.request({ method: 'POST', host: 'localhost', port: 3000, path: '/upload' });
file.pipe(req); // 流式上传
```

断点续传配合：

1. 客户端记录已下载字节数 `downloaded`。
2. 下次请求带 `Range: bytes=downloaded-`。
3. 服务端识别 `Range` 返回 206 与对应区间流。
4. 客户端以 `a`（append）模式把新片段追加到本地文件。

> 💡 提示
> 上传也可在客户端先按固定大小（如 5MB）切片，逐片带 `Content-Range` 上传，服务端按偏移拼回，既支持续传也便于并发与失败重试。

> 🎯 关键要点
> - 大文件必须流式读写，避免整文件进内存
> - 下载靠 Range + 206 + Accept-Ranges 实现续传
> - 服务端用 createReadStream({start,end}) 截取区间
> - 上传可用分片 + Content-Range 拼回
> - 客户端记录偏移，断点后从断处续拉

> 🔍 追问
> - 如何校验续传后文件完整性（哈希/分片校验）？
> - 多片并发上传时服务端如何安全拼接？

### 21. 流的错误处理有哪些坑？为什么 pipe 不会自动销毁源/目标？destroy/abort 与 finally 清理怎么写？｜高级

结论：流错误必须显式监听 `'error'`，否则未处理的流错误会让进程崩溃；`pipe` 不会在任一端出错时自动 `destroy` 另一端，导致资源泄漏；应使用 `pipeline` 或在错误时手动 `destroy`，并在 `finally` 中清理临时资源。

`pipe` 的陷阱：

```js
// 危险：目标 write 流出错时，源 read 流不会被自动销毁
readStream.pipe(res);
readStream.on('error', (e) => console.error(e)); // 只打印，源仍在跑
```

正确做法一：用 `pipeline`（自动清理整链）：

```js
const { pipeline } = require('stream/promises');
try {
  await pipeline(readStream, transform, res);
} catch (err) {
  console.error('流处理失败', err);
  res.destroy(); // 必要时关闭响应
}
```

正确做法二：手动成对销毁：

```js
readStream.on('error', (err) => {
  writeStream.destroy(err); // 把错误传给另一端并销毁
});
writeStream.on('error', (err) => {
  readStream.destroy(err);
});
```

临时资源清理（`finally`）：

```js
const tmp = fs.createWriteStream('/tmp/part');
try {
  await pipeline(readStream, tmp);
  await fs.promises.rename('/tmp/part', '/data/final');
} catch (err) {
  await fs.promises.unlink('/tmp/part').catch(() => {});
  throw err;
} finally {
  // 任何需要释放的句柄在这里收尾
}
```

- `stream.destroy(err)` 会触发 `'error'` 与 `'close'`。
- `AbortController` 可用于在取消请求时 `abort()` 中断流（Node 16+ 的流支持 `signal` 选项）。
- 忘记 `unlink` 临时文件会造成磁盘堆积。

> ⚠️ 注意
> 在生产中，未监听 `error` 的流一旦出错会向上抛到进程级 `uncaughtException`，导致整个服务崩。这就是为什么 `pipeline` 优于手写 `pipe`。

> 🎯 关键要点
> - 流必须监听 error，否则进程崩溃
> - pipe 不自动销毁另一端，会导致 fd/内存泄漏
> - 优先用 pipeline 自动清理
> - 手写时错误要成对 destroy
> - 临时文件在 finally/unlink 中清理

> 🔍 追问
> - AbortController 如何中断一个进行中的流？
> - 为什么 destroy 之后再 write 会报错？

### 22. 如何自定义一个 Transform 流？objectMode、highWaterMark、flush、错误传播要注意什么？｜高级

结论：自定义 Transform 流通过继承 `stream.Transform` 并实现 `_transform(chunk, encoding, cb)`，把输入逐块转换为输出；`objectMode` 用于传输 JS 对象而非 Buffer；`highWaterMark` 控制缓冲水位；`flush(cb)` 用于末尾收尾；错误用 `cb(err)` 或 `destroy` 传播。

```js
const { Transform } = require('stream');

// 把输入按行累积，objectMode 下每输出一行对象
class LineSplitter extends Transform {
  constructor() {
    super({ objectMode: true, highWaterMark: 16 });
    this.buffer = '';
  }

  _transform(chunk, encoding, cb) {
    this.buffer += chunk.toString();
    const lines = this.buffer.split('\n');
    this.buffer = lines.pop(); // 最后一段可能不完整，留到下次
    for (const line of lines) {
      this.push({ text: line, len: line.length });
    }
    cb(); // 或 cb(null) 表示成功
  }

  _flush(cb) {
    if (this.buffer) this.push({ text: this.buffer, len: this.buffer.length });
    cb(); // 收尾，输出剩余内容
  }
}
```

关键参数与坑：

- **objectMode**：开启后 `push` / `write` 接受任意 JS 值（含对象），不再强制 Buffer/String；水位按「对象个数」而非字节算。
- **highWaterMark**：`objectMode` 下默认 16（个对象），普通模式默认 16KB（字节）。
- **_transform 必须调用 cb**：`cb()` 表示成功继续，`cb(err)` 表示出错中断；忘了 `cb` 流会「卡死」不再处理。
- **_flush**：流输入结束时触发，用于把缓冲里的残留数据（如上例最后半行）输出。
- **错误传播**：用 `cb(new Error(...))` 或 `this.destroy(err)`，下游 `pipeline` 会捕捉并销毁整链。

> ⚠️ 注意
> `objectMode` 下 `highWaterMark` 是对象数量，不是字节数；若每个对象很大，设太小会频繁触发背压、设太大则内存占用高，需按对象实际大小估算。

> 🎯 关键要点
> - 实现 _transform 逐块转换，必须调用 cb
> - objectMode 传输对象，水位按个数计
> - highWaterMark 控制背压触发阈值
> - _flush 做末尾收尾输出残留
> - 错误用 cb(err) 或 destroy 向上传播

> 🔍 追问
> - _transform 里忘了调用 cb 会发生什么？
> - 为什么 objectMode 下 highWaterMark 语义变了？

### 23. Node 的 HTTP 连接复用：keep-alive 的原理、Agent 配置、socket 超时与连接泄漏如何排查？｜高级

结论：HTTP keep-alive 复用底层 TCP socket 避免每次请求三次握手，Node 通过 `http.Agent` 管理连接池；连接泄漏常因「不读响应体 / 不释放 socket / 超时设置缺失」导致文件描述符耗尽，排查看 `agent.sockets` / `agent.requests` 与 `lsof`。

原理：客户端 `http.request` 默认 `agent: http.globalAgent`，它维护到各 host 的 socket 池，请求完不立即关，下次同 host 复用。服务端通过 `Connection: keep-alive` 头保持。

```js
const http = require('http');

const agent = new http.Agent({
  keepAlive: true,          // 启用连接复用
  maxSockets: 50,           // 单 host 最大并发 socket
  maxFreeSockets: 10,       // 空闲保留数
  timeout: 60000,           // socket 空闲超时（毫秒）
  keepAliveMsecs: 1000,     // keep-alive 探活间隔
});

http.get('http://api.internal/data', { agent }, (res) => {
  res.resume(); // 必须消费完响应体，否则 socket 不释放
});
```

连接泄漏排查：

- 必须**完整消费响应体**（`res.resume()` 或读完），否则 socket 永远占着不放回池。
- 看 `agent.sockets`（已建立）与 `agent.requests`（排队中）数量，若持续只增不减即泄漏。
- `lsof -p <pid> | grep TCP | wc -l` 看进程 fd 数；`ECONNRESET` / `socket hang up` 常是池打满或远端关连接。
- 设 `timeout` 与请求级 `AbortController` 超时，避免死等。

> ⚠️ 注意
> `http.get` 拿到 `res` 后若不读 body，即使不 `pipe`，socket 也不会归还到 free 列表，数万请求后会 `EMFILE`（文件描述符耗尽）。

> 🎯 关键要点
> - keep-alive 复用 TCP，省握手开销
> - http.Agent 是连接池，globalAgent 默认开启
> - maxSockets 控制单 host 并发上限
> - 不消费响应体会造成连接泄漏
> - 排查看 agent.sockets/requests 与 lsof

> 🔍 追问
> - 为什么 res 不读完 body 就关会泄漏连接？
> - maxSockets 设太小会触发什么现象？

## Web 框架：Express 与 Koa（6 题）

### 24. Express是什么？它有哪些核心概念？｜初级

Express 是 Node 最流行的轻量级 Web 框架，在原生 `http` 之上提供路由、中间件、静态服务与模板渲染等能力，让构建 Web/API 服务变得简单。

核心概念：

- **路由（Routing）**：把不同 HTTP 方法 + URL 映射到处理函数，如 `app.get('/users', handler)`。
- **中间件（Middleware）**：可插拔的请求处理单元，能访问 `req/res` 并决定是否调用 `next()` 传递控制权。
- **模板引擎**：渲染 HTML（如 EJS、Pug），适合传统服务端渲染。
- **静态文件**：`express.static('public')` 直接托管 CSS/JS/图片。
- **错误处理中间件**：统一捕获与格式化错误。

```js
const express = require('express');
const app = express();

app.use(express.json());           // 解析 JSON 请求体
app.use(express.static('public')); // 托管静态资源

app.get('/', (req, res) => res.send('Hello World!'));
app.get('/users/:id', (req, res) => res.json({ userId: req.params.id }));

app.listen(3000, () => console.log('服务器运行在端口3000'));
```

> 🎯 关键要点
> - Express 是 Node 生态最主流的 Web 框架
> - 四大支柱：路由、中间件、静态服务、错误处理
> - express.json / static 是常用内置中间件
> - 路由支持路径参数（:id）
> - 轻量、约定少，适合从单体到微服务的各种规模

> 🔍 追问
> - Express 与直接用 http 模块相比省了什么？
> - 为什么说 Express 是「非侵入、最小核心」？

### 25. 什么是Express中间件？如何自定义中间件？｜中级

中间件是 Express 处理请求的函数，签名 `(req, res, next)`；它能在请求到达路由前/后执行任意逻辑、修改 `req/res`、决定是否终结响应或调用 `next()` 交给下一个中间件。

中间件能力：

- 执行任意代码（日志、鉴权、计时）。
- 读写 `req` / `res`（如解析 body、注入用户信息）。
- 终结响应（如返回 401，不再 `next`）。
- 调用 `next()` 把控制权交下游。

```js
// 全局中间件：打印每个请求
app.use((req, res, next) => {
  console.log(`${req.method} ${req.url}`);
  next();
});

// 路由级中间件：鉴权
const auth = (req, res, next) => {
  if (req.headers.authorization) return next();
  res.status(401).json({ error: 'Unauthorized' });
};

app.get('/protected', auth, (req, res) => res.json({ message: 'ok' }));

// 工厂式中间件（可配置）
const logger = (options) => (req, res, next) => {
  console.log(`[${options.level}] ${req.method} ${req.url}`);
  next();
};
app.use(logger({ level: 'info' }));
```

执行顺序严格遵守**注册顺序**：先 `app.use` 的先跑，路由匹配的中间件按声明顺序。错误若不走 `next(err)` 会跳过后续正常中间件，直接命中错误处理中间件。

> 💡 提示
> 中间件「顺序即一切」：把 `express.json()` 放在需要 `req.body` 的路由之前，否则 `req.body` 是 `undefined`。

> 🎯 关键要点
> - 中间件是 (req,res,next) 函数，控制请求生命周期
> - 调用 next() 才往下走，否则响应须在此终结
> - 按注册顺序执行，顺序决定可用数据
> - 可全局、路由级、工厂式配置
> - 不调用 next 且不返回响应会挂起请求

> 🔍 追问
> - 中间件里忘记调用 next 也不响应会怎样？
> - 错误中间件为什么要 4 个参数？

### 26. 如何处理Express中的错误？｜中级

核心结论：Express 错误处理靠「业务层 `try/catch` + `next(err)` 上抛 + 专门的 4 参错误处理中间件统一收口」，异步路由要用 `asyncHandler` 或 `.catch(next)` 把 Promise 拒绝转成 `next(err)`。

```js
const express = require('express');
const app = express();

// 1. 同步/async 路由中捕获后上抛
app.get('/user/:id', async (req, res, next) => {
  try {
    const user = await User.findById(req.params.id);
    if (!user) return res.status(404).json({ error: 'User not found' });
    res.json(user);
  } catch (err) {
    next(err); // 交给错误中间件
  }
});

// 2. 通用 async 包装器，避免每层重复 try/catch
const asyncHandler = (fn) => (req, res, next) =>
  Promise.resolve(fn(req, res, next)).catch(next);

// 3. 错误处理中间件：必须 4 个参数 (err, req, res, next)
app.use((err, req, res, next) => {
  console.error(err.stack);
  const status = err.status || 500;
  res.status(status).json({ error: err.message || 'Something went wrong!' });
});
```

要点：

- 4 参中间件必须**参数个数恰好 4 个**，Express 据此识别为错误处理器，放最后注册。
- 异步拒绝若不用 `next(err)` 传递，Express 捕获不到，会触发 `unhandledRejection`。
- 生产环境不要向客户端泄露 `err.stack`（含路径与代码），按状态码返回统一错误体。
- 区分「已知业务错误」（404、校验失败）与「未知 500」，分别处理并告警。

> ⚠️ 注意
> 错误处理中间件的 4 个参数是硬性约定，少写一个参数（如写成 3 参）它会被当作普通中间件，永远不触发，错误随之泄漏。

> 🎯 关键要点
> - 业务错误用 next(err) 上抛，不自己吞
> - 4 参中间件统一收口，参数个数必须精确
> - async 路由用 asyncHandler 或 .catch(next)
> - 生产不泄露 stack，按状态码返回
> - 区分业务错误与系统错误

> 🔍 追问
> - 为什么 async 路由不包 try/catch 时 Express 抓不到错误？
> - 如何在错误中间件里做告警上报？

### 27. Express中如何处理文件上传？｜中级

结论：Express 自身不解析 `multipart/form-data`，文件上传用社区中间件 `multer`，它负责把表单里的文件写入磁盘或内存，并提供 `req.file` / `req.files`；通过 `diskStorage` 控制路径与文件名、`fileFilter` 过滤类型、`limits` 限制大小。

```js
const multer = require('multer');

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, 'uploads/'),
  filename: (req, file, cb) => cb(null, Date.now() + '-' + file.originalname),
});

// 只允许图片，并限制 5MB
const upload = multer({
  storage,
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith('image/')) cb(null, true);
    else cb(new Error('只能上传图片文件'), false);
  },
  limits: { fileSize: 1024 * 1024 * 5 },
});

// 单文件：字段名 'image'
app.post('/upload', upload.single('image'), (req, res) => {
  res.json({ file: req.file });
});
// 多文件：upload.array('images', 5)；多字段：upload.fields([...])
```

要点：

- `upload.single` / `array` / `fields` 对应不同表单结构，决定 `req.file` 还是 `req.files`。
- 把上传目录放在 `public` 之外，避免用户直接通过 URL 访问他人文件；必要时做权限校验 + 随机文件名防遍历。
- `fileFilter` 中 `cb(err, false)` 会触发错误中间件；若 `cb(null, false)` 则静默跳过该文件。
- 大文件建议直接用流（`busboy` / `formidable`）边读边处理，`multer` 默认先落盘。
- 校验真实类型不能只信 `mimetype`，应结合魔数（文件头）或后置扫描。

> ⚠️ 注意
> `limits.fileSize` 超限会抛 `MulterError`，务必在错误处理中间件里捕获并返回友好提示，否则默认 500。

> 🎯 关键要点
> - Express 不内置 multipart 解析，用 multer
> - diskStorage 控制落盘路径与文件名
> - fileFilter 过滤类型、limits 限制大小
> - 上传目录应隔离在 public 之外
> - 大文件优先流式解析而非先整文件落盘

> 🔍 追问
> - multer 与 busboy 的底层差异？
> - 如何防止用户上传可执行文件被直接访问执行？

### 28. Express中如何实现路由分组？｜中级

结论：路由分组用 `express.Router` 把同一模块的路由收进独立文件，再用 `app.use('/api/users', userRouter)` 挂载，从而共享前缀与组内中间件（如鉴权），实现模块化与可维护。

```js
// routes/userRoutes.js
const express = require('express');
const router = express.Router();

// 组内共享鉴权中间件
router.use((req, res, next) => {
  req.user ? next() : res.status(401).end();
});

router.get('/', (req, res) => res.json({ users: [] }));
router.get('/:id', (req, res) => res.json({ user: req.params.id }));

module.exports = router;

// app.js
const userRoutes = require('./routes/userRoutes');
const postRoutes = require('./routes/postRoutes');

app.use('/api/users', userRoutes);
app.use('/api/posts', postRoutes);
// 组内路由自动获得 /api/users 前缀与鉴权
```

好处与约定：

- **代码组织**：按业务域（user/post/order）拆分文件，单一职责。
- **前缀管理**：统一加 `/api/v1` 之类前缀，便于版本控制。
- **中间件共享**：组内路由共用鉴权/日志，不必每条重复声明。
- **可测性**：Router 可单独 `supertest` 测试，不依赖主 app。
- **版本控制**：`/api/v1/users`、`/api/v2/users` 分别挂不同 Router。

> 💡 提示
> 用 Router 后，`router.get('/:id')` 实际路径是挂载前缀 + `/:id`，即 `/api/users/:id`；Router 内部看到的是相对路径。

> 🎯 关键要点
> - 用 express.Router 拆分模块路由
> - app.use(prefix, router) 挂载并共享前缀
> - 组内中间件（鉴权/日志）统一声明
> - 便于版本控制与独立测试
> - Router 内路径是相对挂载点的

> 🔍 追问
> - 多个 Router 挂载同一前缀时中间件顺序如何？
> - 如何在 Router 层做 API 版本管理？

### 29. Koa 与 Express 的核心差异是什么？洋葱模型、ctx、async 中间件与错误冒泡分别解决了什么问题？｜高级

结论：Koa 是 Express 原班人马打造的下一代框架，用 **async 函数中间件 + 洋葱模型**取代 Express 的回调式 `next()`，把「请求/响应」统一封装为 `ctx`，错误通过 `try/catch` 自然冒泡，解决了 Express 中异步错误难捕获、逻辑嵌套深的问题。

洋葱模型对比：

```js
// Koa：async 中间件，await next() 形成洋葱（进/出两层）
const Koa = require('koa');
const app = new Koa();

app.use(async (ctx, next) => {
  const start = Date.now();
  await next();                       // 进入内层
  ctx.set('X-Response-Time', `${Date.now() - start}ms`);
});

app.use(async (ctx) => {
  ctx.body = 'Hello';
});
```

而 Express 的中间件是线性「穿透」式：靠 `next()` 往下走，但 `next()` 是回调，异步错误必须用 `next(err)` 显式传递，Promise 拒绝不会自动上抛。

核心差异：

| 维度 | Express | Koa |
| --- | --- | --- |
| 中间件 | `(req,res,next)` 回调式 | `async (ctx,next)`，await next() |
| 上下文 | `req` / `res` 分离 | 统一 `ctx`（含 request/response） |
| 错误处理 | 4 参中间件 + next(err) | `try/catch` 冒泡到 `app.on('error')` |
| 内置功能 | 含路由、静态等 | 极小核心，靠中间件生态 |
| 异步友好 | 需 asyncHandler 包裹 | 原生 await，错误自然上抛 |

Koa 解决的问题：

- **异步错误捕获**：`await next()` 抛错能直接在 `try/catch` 里抓到，无需 `next(err)` 仪式。
- **洋葱双向逻辑**：`await next()` 前后都能写代码（如「请求前计时、响应后写头」），Express 需拆成两个中间件。
- **ctx 统一**：`ctx.request` / `ctx.response` / `ctx.state` 集中，中间件间传数据用 `ctx.state`，比挂 `req` 更清晰。

> ⚠️ 注意
> Koa 把很多能力（路由、body 解析）外置成中间件（如 `koa-router`、`koa-bodyparser`），上手比 Express 多一步装配，但核心更轻、更可控。

> 🎯 关键要点
> - Koa 用 async 中间件 + 洋葱模型
> - ctx 统一封装 req/res，state 跨中间件传值
> - await next() 让错误自然 try/catch 冒泡
> - 洋葱模型支持「前后」双向切面逻辑
> - Koa 核心极简，能力靠中间件组装

> 🔍 追问
> - 为什么 Koa 中间件里 throw 能被全局 error 捕获？
> - Express 能否用 async 中间件达到同样效果？

## 数据库与 ORM（10 题）

### 30. MongoDB是什么？它有哪些核心概念？｜初级

MongoDB 是文档型 NoSQL 数据库，用类 JSON 的 BSON 文档存储数据， schema 灵活，适合结构多变、写入频繁的场景。

核心概念（层级从大到小）：

- **数据库（Database）**：最外层容器。
- **集合（Collection）**：相当于关系库的「表」，但不需要预定义列。
- **文档（Document）**：相当于「行」，是 JSON-like 的 BSON 结构，字段可不同。
- **字段（Field）**：文档里的键值对，相当于「列」。

```js
const mongoose = require('mongoose');
mongoose.connect('mongodb://localhost:27017/myapp');

const userSchema = new mongoose.Schema({
  name: String,
  email: String,
  age: Number,
  createdAt: { type: Date, default: Date.now },
});
const User = mongoose.model('User', userSchema);

const user = new User({ name: 'John', email: 'john@example.com', age: 25 });
await user.save();

const users = await User.find({ age: { $gte: 18 } }); // 查询年龄>=18
```

特点：文档可嵌套（子文档/数组），读写无需 join 但支持聚合管道；水平扩展靠分片（sharding）。适合 CMS、物联网、实时分析、快速原型。

> 🎯 关键要点
> - 文档型 NoSQL，数据以 BSON 文档存储
> - 层级：数据库 → 集合 → 文档 → 字段
> - schema 灵活，字段不必统一
> - Mongoose 提供 Schema/Model 封装
> - 适合结构多变、高写入场景

> 🔍 追问
> - MongoDB 的 _id 默认是什么类型，为什么不用自增？
> - 文档嵌套与引用（join）该如何取舍？

### 31. SQL和NoSQL数据库有什么区别？｜中级

结论：SQL（关系型）用表 + 固定 schema + SQL + ACID 事务，适合强一致、复杂关联；NoSQL 用文档/键值/列族/图等灵活模型，弱 schema、水平扩展好，适合高并发、结构易变场景。二者并非替代，常混合使用。

| 维度 | SQL | NoSQL |
| --- | --- | --- |
| 数据模型 | 表、行、列，二维结构 | 文档/键值/列族/图 |
| Schema | 预定义、强约束 | 动态、灵活 |
| 查询 | 标准 SQL，表达力强 | 各库自有 API/查询语言 |
| 事务 | 完整 ACID | 多数最终一致，部分支持事务 |
| 扩展 | 纵向扩展为主 | 横向扩展（分片）天然友好 |
| 关联 | JOIN 原生支持 | 多靠冗余/嵌套，少 join |

选型：

- 用 SQL：需要复杂查询、多表关联、严格一致性（订单、账务、权限）。
- 用 NoSQL：海量写入、schema 频繁变、低延迟 KV（会话、缓存、日志、画像）。
- 混合：主数据用 Postgres/MySQL，缓存/会话/画像用 Redis/MongoDB。

> 💡 提示
> 现在很多 SQL 库也支持 JSON 字段（Postgres `jsonb`），NoSQL（MongoDB 4.0+）也支持多文档事务——边界在模糊，但「默认心智模型」仍如上表。

> 🎯 关键要点
> - SQL 固定 schema + ACID + 强关联
> - NoSQL 灵活 schema + 易水平扩展
> - 事务能力 SQL 更强更成熟
> - 扩展方式：SQL 纵向、NoSQL 横向
> - 实际常混合：关系库存核心，NoSQL 补场景

> 🔍 追问
> - 什么场景用文档库比关系库更吃亏？
> - NewSQL 如何尝试兼顾两者？

### 32. 什么是Redis？它有哪些使用场景？｜中级

Redis 是开源的内存数据结构存储，可作数据库、缓存、消息中间件，因数据在内存而读写极快，并通过 RDB/AOF 持久化防止重启丢数据。

核心特性：

- **高性能**：内存操作，单机可达十万级 QPS。
- **丰富结构**：String、Hash、List、Set、Sorted Set、Stream、Bitmap 等。
- **持久化**：RDB（快照）+ AOF（追加日志），可权衡性能与可靠性。
- **高可用**：主从复制、哨兵（Sentinel）、Cluster 分片。

典型场景：

```js
const redis = require('redis');
const client = redis.createClient();
await client.connect();

// 缓存
await client.set('key', 'value', { EX: 300 }); // 5 分钟过期
const v = await client.get('key');

// 哈希（用户档案）
await client.hSet('user:1', 'name', 'John');
const user = await client.hGetAll('user:1');

// 队列（LPUSH + RPOP）
await client.lPush('queue', 'task1');
const task = await client.rPop('queue');
```

- **缓存**：挡在数据库前，降低 DB 压力（注意一致性）。
- **会话存储**：分布式下共享登录态。
- **排行榜**：Sorted Set（`ZADD` / `ZREVRANGE`）。
- **计数器**：`INCR`，限流、点赞数。
- **分布式锁**：`SET key val NX EX` 实现互斥。
- **消息队列**：List 或 Stream。

> ⚠️ 注意
> Redis 是「缓存」不是「真相源」：默认数据可能丢（纯内存/RDB 间隔），关键数据必须落盘库或开启 AOF `appendfsync always`。

> 🎯 关键要点
> - 内存存储，极快，支持多种数据结构
> - 持久化 RDB 快照 + AOF 日志
> - 场景：缓存、会话、排行榜、计数、锁、MQ
> - 分布式锁用 SET NX EX
> - 高可用靠主从 + 哨兵 + Cluster

> 🔍 追问
> - AOF 的 always/everysec/no 三种策略分别意味着什么？
> - Redis 做分布式锁有哪些坑（ expiry/误删）？

### 33. ORM 选型：Sequelize、TypeORM、Prisma、Drizzle、Mongoose 各自的定位与取舍是什么？｜高级

结论：选 ORM 本质是选「开发范式」——Sequelize 是老牌通用 CJS 派、TypeORM 是装饰器+实体派、Prisma 是「schema 优先+生成客户端」派、Drizzle 是「SQL 优先的轻量类型安全」派、Mongoose 是 MongoDB 专用 ODM。按语言（JS/TS）、数据库（SQL/Mongo）、团队偏好取舍。

| 工具 | 定位 | 数据库 | 范式 | 适合 |
| --- | --- | --- | --- | --- |
| Sequelize | 老牌通用 ORM | MySQL/PG/SQLite/MSSQL | 模型类（CJS/ESM 均可） | 传统 JS 项目、需要成熟生态 |
| TypeORM | 装饰器实体 | 同上 + 多 | 实体+装饰器，Active Record/DataMapper | TS 企业项目 |
| Prisma | Schema 优先 | 多（含 Mongo） | `schema.prisma` + 生成类型安全 client | 新项目、重视 DX 与迁移 |
| Drizzle | SQL 优先 | PG/MySQL/SQLite | 用 TS 写 query builder，贴近 SQL | 想要类型安全又不愿放弃 SQL |
| Mongoose | MongoDB ODM | Mongo | Schema/Model | 文档库项目 |

取舍要点：

- **Prisma**：迁移与类型生成极强，但运行时靠查询引擎（二进制），自定义 SQL 受限，大团队 DX 好。
- **Drizzle**：几乎零抽象，SQL 即代码，包小、性能好，但需要你懂 SQL；不适合「完全不想写 SQL」。
- **TypeORM**：装饰器对 TS 友好，功能全，但历史包袱多、大表性能与复杂关联偶有坑。
- **Sequelize**：最稳、文档多，但 TS 体验弱于后辈。
- **Mongoose**：Mongo 事实标准，提供校验、中间件、聚合封装，但锁死在文档模型。

> 💡 提示
> 「类型安全」和「灵活写 SQL」通常负相关：Prisma/Drizzle 偏类型安全，原生 `pg`/`mysql2` + 手写 SQL 偏灵活。选边要问「团队是否愿意为类型牺牲底层控制」。

> 🎯 关键要点
> - Sequelize 老牌通用，TypeORM 装饰器派
> - Prisma schema 优先、DX 好、抽象厚
> - Drizzle SQL 优先、轻量类型安全
> - Mongoose 是 Mongo 专用 ODM
> - 选型看语言/数据库/对 SQL 控制欲

> 🔍 追问
> - Prisma 的查询引擎二进制在 serverless 下有什么坑？
> - 什么场景应放弃 ORM 直接写原生 SQL？

### 34. 什么是 N+1 查询问题？ORM 里的 eager loading / include / dataloader 分别怎么解决？｜高级

结论：N+1 指「查列表 1 次 + 每条记录再查关联 N 次」的灾难性查询放大；解决思路是「预加载（一次 IN 查全）」或「批量合并（DataLoader 按批收集后一次查）」。

问题复现：

```js
const posts = await Post.findAll();      // 1 次查询
for (const p of posts) {
  p.author = await User.findByPk(p.authorId); // 每条再 1 次 → N 次
}
// 共 1 + N 次查询，N 大时数据库被打爆
```

解法一：Eager Loading（预加载），ORM 用 `JOIN` 或 `IN` 一次取回：

```js
// Sequelize
const posts = await Post.findAll({ include: [{ model: User, as: 'author' }] });

// TypeORM
const posts = await postRepo.find({ relations: ['author'] });

// Prisma
const posts = await prisma.post.findMany({ include: { author: true } });
```

解法二：DataLoader（Facebook 出品），把同一事件循环里对同一个关联的多笔请求**批处理**成一条 `WHERE id IN (...)`：

```js
const userLoader = new DataLoader(async (ids) => {
  const users = await User.findByIds(ids);
  return ids.map((id) => users.find((u) => u.id === id)); // 按请求顺序返回
});

// 循环里调用，DataLoader 自动合并成一次查询
for (const p of posts) {
  p.author = await userLoader.load(p.authorId);
}
```

- Eager loading 适合「已知就要关联」的场景；若关联是条件性的，盲目 include 会过度查询。
- DataLoader 适合 GraphQL 等「多处分散取关联」的场景，靠批处理 + 缓存去重。

> ⚠️ 注意
> `include` 不当会产生笛卡尔积（多对多关联 JOIN 后行数膨胀），需用 `distinct` 或分页子查询规避；这不是 N+1，但是伴随的「过多行」问题。

> 🎯 关键要点
> - N+1 = 1 次列表 + N 次关联查询
> - 预加载用 JOIN/IN 一次取回关联
> - include/relations 是各 ORM 的 eager loading 写法
> - DataLoader 按批合并 + 缓存去重
> - 过度 include 会带来笛卡尔积膨胀

> 🔍 追问
> - 为什么 GraphQL 特别容易踩 N+1？
> - 多对多关联下 include 如何避免笛卡尔积？

### 35. 数据库事务与隔离级别：四种隔离级别分别解决什么异常？乐观锁与悲观锁怎么选？｜高级

结论：事务 ACID 靠隔离级别平衡「一致性」与「并发度」；SQL 标准四种级别渐进解决脏读、不可重复读、幻读。乐观锁适合冲突少的读多写少，悲观锁适合冲突频繁、必须强一致的短事务。

四种隔离级别（Postgres/MySQL 通用语义）：

| 级别 | 脏读 | 不可重复读 | 幻读 |
| --- | --- | --- | --- |
| 读未提交 Read Uncommitted | 可能 | 可能 | 可能 |
| 读已提交 Read Committed | 杜绝 | 可能 | 可能 |
| 可重复读 Repeatable Read | 杜绝 | 杜绝 | 可能（PG 实际杜绝） |
| 串行化 Serializable | 杜绝 | 杜绝 | 杜绝 |

- **脏读**：读到别人未提交的事务。
- **不可重复读**：同一事务内两次读同一行结果不同（被别人修改提交）。
- **幻读**：同一查询两次返回的行集合不同（别人增删了行）。

Node 里用事务（以 `pg` 为例）：

```js
const client = await pool.connect();
try {
  await client.query('BEGIN');
  await client.query('UPDATE accounts SET balance = balance - $1 WHERE id=$2', [100, 'A']);
  await client.query('UPDATE accounts SET balance = balance + $1 WHERE id=$2', [100, 'B']);
  await client.query('COMMIT');
} catch (e) {
  await client.query('ROLLBACK');
  throw e;
} finally {
  client.release();
}
```

乐观锁 vs 悲观锁：

- **乐观锁**：加 `version` 字段，`UPDATE ... SET version=version+1 WHERE id=? AND version=?`，版本不符则重试；无锁、并发高，冲突时才失败。
- **悲观锁**：`SELECT ... FOR UPDATE` 在事务内锁住行，别人改不了；强一致但降低并发、易死锁。

> 💡 提示
> 多数业务用「乐观锁 + 重试」足够；只有「扣库存/转账」这种必须互斥且冲突频繁的场景才上 `FOR UPDATE`，并注意事务要短、按固定顺序加锁以避免死锁。

> 🎯 关键要点
> - 四级隔离逐步解决脏读/不可重复读/幻读
> - 默认多用 Read Committed，强一致用 Serializable
> - 事务要 BEGIN/COMMIT/ROLLBACK + finally 释放连接
> - 乐观锁靠 version 字段，冲突重试
> - 悲观锁 FOR UPDATE 强一致但易死锁

> 🔍 追问
> - Repeatable Read 在 MySQL 与 Postgres 行为差异？
> - SELECT FOR UPDATE 没提交会阻塞多久？

### 36. 数据库连接池的原理与配置：连接数怎么定、连接泄漏怎么排查、事务与连接的关系｜高级

结论：连接池预先维护一组到数据库的 TCP 连接，请求「借」连接用完「还」，避免每次新建连接的三次握手/认证开销；池大小应略小于数据库 `max_connections`，连接泄漏表现为池被打满、请求排队，排查看借出未还。

原理：应用启动时池创建 N 条空闲连接；查询时 `acquire` 一条，执行完 `release` 回池。连接数有限，超额请求在队列等待（`acquireTimeout` 超时则报错）。

配置（以 `pg` 为例）：

```js
const { Pool } = require('pg');
const pool = new Pool({
  max: 20,                  // 最大连接数
  min: 2,                   // 最小空闲保持
  idleTimeoutMillis: 30000, // 空闲回收
  connectionTimeoutMillis: 5000,
  // acquireTimeoutMillis（部分库）控制借出等待上限
});
```

- **连接数怎么定**：经验公式 `connections ≈ ((core_count * 2) + effective_spindle_count)`，但更稳妥是按压测与数据库上限反推，通常单实例 10–50。Postgres 默认 `max_connections=100`，要给管理/其他服务留余量。
- **泄漏排查**：出现 `Timeout acquiring client` 或 `remaining connection slots are reserved` → 一定有「借了没还」。常见原因：事务没 `finally release`、长事务占着连接、忘记 `await` 导致连接一直占用。
- **事务与连接**：一个事务必须绑定同一条连接，从 BEGIN 到 COMMIT/ROLLBACK 都在该连接上；中途 release 会破坏事务。ORM 的 `transaction()` 已封装「取连接→事务→释放」。

> ⚠️ 注意
> 在 `async` 里忘记 `await` 查询就继续往下，连接可能一直没归还；或者在 `try` 里 `await` 但 `catch` 没 `release`，连接就泄漏了。务必 `finally { client.release() }`。

> 🎯 关键要点
> - 池复用连接，省握手/认证开销
> - max 应小于数据库 max_connections 留余量
> - 泄漏=借出未还，报 acquire 超时
> - 事务必须占用同一条连接直到结束
> - finally 中 release 是防泄漏铁律

> 🔍 追问
> - 为什么连接数不是越大越好？
> - serverless 下连接池为何特别容易打满？

### 37. 索引的原理与慢查询优化：B+ 树、联合索引最左前缀、覆盖索引、回表、如何读 EXPLAIN｜高级

结论：关系库索引多用 B+ 树，提供有序、低高度的查找；联合索引遵循「最左前缀」，查询只用左边连续字段才命中；「覆盖索引」能在索引里取齐所需列避免回表；`EXPLAIN` 是定位慢查询的核心工具。

核心概念：

- **B+ 树**：平衡多路树，叶子节点有序串联，范围查询与排序极快；树高通常 3–4 层，一次查询只需几次磁盘 IO。
- **最左前缀**：联合索引 `(a,b,c)` 能加速 `a`、`(a,b)`、`(a,b,c)`，但不能跳过 `a` 直接用 `b`。
- **回表**：普通索引只存「索引列+主键」，查非索引列需拿主键回主键索引再取，多一次 IO。
- **覆盖索引**：查询的所有列都在索引里，`Using index` 直接返回，无需回表。

```sql
-- 建联合索引
CREATE INDEX idx_user_city_age ON users(city, age);

-- 命中（用到 city, age）
SELECT * FROM users WHERE city='BJ' AND age>20;

-- 不命中最左前缀（跳过了 city）
SELECT * FROM users WHERE age>20;

-- 覆盖索引示例：只查索引列
SELECT city, age FROM users WHERE city='BJ';
```

读 `EXPLAIN`（以 MySQL 为例）：

```sql
EXPLAIN SELECT * FROM users WHERE city='BJ' AND age>20;
```

关注：

- **type**：`ALL`（全表扫描，差）→ `index` → `range` → `ref` → `const`（好）。
- **key**：实际用了哪个索引。
- **rows**：估算扫描行数，越小越好。
- **Extra**：`Using where`、`Using index`（覆盖，好）、`Using filesort`（额外排序，差）、`Using temporary`（临时表，差）。

> ⚠️ 注意
> 索引不是越多越好：每个索引拖慢写入并占空间；低区分度字段（如 `gender`）单独建索引几乎无效，应放进联合索引的左侧或放弃。

> 🎯 关键要点
> - B+ 树提供有序、低高度查找
> - 联合索引必须最左前缀才命中
> - 覆盖索引避免回表，性能最佳
> - EXPLAIN 看 type/key/rows/Extra
> - 索引过多拖慢写、低区分度无效

> 🔍 追问
> - 为什么 LIKE '%abc' 用不上索引？
> - filesort 在什么情况下不可避免？

### 38. 分页怎么优化？OFFSET 深分页为什么慢？游标（keyset）分页怎么实现？｜高级

结论：传统 `LIMIT offset, size` 在 offset 很大时要扫描并丢弃前面所有行，越翻越慢；深分页应改用「游标/keyset 分页」，基于上一页最后一条的有序键继续取，避免丢数据。

OFFSET 慢在哪：

```sql
-- offset=100000 时，数据库要先定位并跳过 10 万行再取 20 行
SELECT * FROM orders ORDER BY id DESC LIMIT 20 OFFSET 100000;
```

数据库仍需扫描前 100020 行再丢弃，I/O 与排序成本随 offset 线性增长。

Keyset（游标）分页：

```sql
-- 用上一页最后一条的 id 作为游标
SELECT * FROM orders
WHERE id < :lastId          -- 上一页最小 id
ORDER BY id DESC
LIMIT 20;
```

- 依赖「有序唯一键」（如自增 id 或 `(created_at, id)` 组合），`WHERE key < lastKey` 直接走索引区间，复杂度恒定。
- 前端把「上一页末条 id」回传作为 cursor，无需传页码。
- 缺点：不支持「跳到第 N 页」，只能「上一页/下一页」，但恰好是绝大多数列表场景的真实需求。

组合游标（时间+ID 防并列）：

```sql
SELECT * FROM events
WHERE (created_at, id) < (:lastCreated, :lastId)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

> 💡 提示
> 若业务硬要「跳页」（如后台管理），可限制最大 offset（如 5000），或对 `ORDER BY` 字段建覆盖索引 + `WHERE` 过滤把扫描量压下来，而不是裸 `OFFSET 大数`。

> 🎯 关键要点
> - OFFSET 深分页要扫并丢弃前序行，线性变慢
> - keyset 用上一页末键做 WHERE 区间，走索引
> - 游标需有序唯一键（id 或 时间+id）
> - 游标分页不支持任意跳页，但覆盖多数场景
> - 跳页需求应加 offset 上限保护

> 🔍 追问
> - 为什么 keyset 分页在数据实时插入时更稳定？
> - 组合游标如何解决 created_at 相同导致的漏/重？

### 39. 缓存与数据库如何保持一致性？Cache Aside、先删缓存还是先更库、延迟双删的适用边界｜高级

结论：最常见的「Cache Aside」模式是「读时回填、写时删缓存」，但「先删缓存还是先更库」有并发竞态，常用「先更库再删缓存 + 延迟双删 + 过期兜底」把不一致窗口压到最小；强一致场景则要放弃缓存或加分布式锁。

Cache Aside（旁路缓存）基本读写：

```js
// 读：缓存没有则查库并回填
async function get(key) {
  let val = await cache.get(key);
  if (!val) {
    val = await db.get(key);
    await cache.set(key, val, { EX: 300 });
  }
  return val;
}

// 写：更新数据库，再删缓存
async function update(key, data) {
  await db.update(key, data);
  await cache.del(key); // 让下次读回填最新
}
```

先删 vs 先更库的竞态：

- **先删缓存再更库**：删缓存后、库提交前，若有读请求会回填「旧值」到缓存，造成短期脏数据。
- **先更库再删缓存（推荐）**：少数情况下「删缓存失败」会留脏数据，所以加**延迟双删**：更新后删一次，隔几百毫秒再删一次，清掉期间可能被回填的旧值。
- **过期时间兜底**：所有缓存都设 TTL，即使双删漏了，最终也会因过期而一致。

更强一致的做法：

- **写直读（Write Through）**：写同时更新缓存与库，由缓存层保证原子，但实现复杂、写放大。
- **分布式锁**：更新期间锁住 key，读也走锁，保证串行；性能差，仅用于强一致小热点。
- **binlog 同步**：通过 Canal/Debezium 监听库变更异步删缓存，解耦且可靠，但引入基建。

> ⚠️ 注意
> 缓存与数据库「绝对强一致」在分布式下几乎不可能又无性能代价；多数业务接受「最终一致 + 短窗口」。只有余额、库存等才值得上锁或事务消息。

> 🎯 关键要点
> - Cache Aside：读填空、写删缓存
> - 推荐先更库再删缓存，降低脏读窗口
> - 延迟双删清理并发回填的旧值
> - TTL 过期是最终兜底
> - 强一致需锁/写直读/binlog，代价高

> 🔍 追问
> - 为什么延迟双删的第二次删除要隔一段时间？
> - 缓存穿透/击穿/雪崩分别是什么、怎么防？

## API 设计（4 题）

### 40. 什么是RESTful API？它有哪些设计原则？｜初级

RESTful API 是基于 REST 架构风格的接口设计方法，用 HTTP 标准方法操作「资源」，强调无状态、统一接口与可寻址的资源 URL。

核心原则：

- **资源导向**：每个 URL 代表一个资源（名词），如 `/users`。
- **统一接口**：用标准 HTTP 方法表达操作——`GET` 查、`POST` 建、`PUT` 全量改、`PATCH` 局部改、`DELETE` 删。
- **无状态**：服务端不保存客户端上下文，每次请求自带全部所需信息（如 token）。
- **可缓存**：响应标注缓存头，客户端可缓存 `GET`。

```http
GET    /api/users          # 列表
POST   /api/users          # 新建
GET    /api/users/:id      # 单个
PUT    /api/users/:id      # 全量更新
DELETE /api/users/:id      # 删除
GET    /api/users/:id/posts  # 嵌套资源
```

状态码约定：200 成功、201 创建、204 删除成功、400 参数错、401 未认证、403 无权限、404 不存在、500 服务端错。

最佳实践：URL 用复数名词、加版本前缀（`/api/v1`）、支持过滤/分页/排序查询参数、返回统一错误结构、用 HTTPS。

> 🎯 关键要点
> - REST 以资源为中心，URL 是名词
> - 用 HTTP 方法表达 CRUD 语义
> - 无状态：请求自包含
> - 合理使用状态码与缓存头
> - 复数名词、版本化、统一错误体

> 🔍 追问
> - PUT 与 PATCH 的语义区别？
> - 为什么 REST 强调无状态？

### 41. GraphQL和RESTful API有什么区别？｜中级

结论：REST 是「服务端定结构、多端点」的接口风格，GraphQL 是「单端点、客户端按需取字段」的查询语言；GraphQL 解决了过度获取/获取不足与多轮请求，但带来 N+1、缓存与复杂度成本。

| 维度 | RESTful | GraphQL |
| --- | --- | --- |
| 端点 | 多个（每资源一个） | 单个（通常 `/graphql`） |
| 数据形状 | 服务端固定返回 | 客户端用查询声明所需字段 |
| 版本 | 常靠 URL/Header 版本 | 靠 schema 演进，少版本 |
| 类型系统 | 无强制 | 强类型 Schema |
| 缓存 | 直接利用 HTTP 缓存 | 需额外（ persisted query / APQ） |
| 多资源 | 多次请求或自定义聚合 | 一次查询取多资源 |

- **REST 优势**：简单、可缓存、生态成熟，适合标准 CRUD 与高缓存需求。
- **GraphQL 优势**：前端精确取数、减少往返、强类型自文档，适合字段多变、移动端带宽敏感。
- **GraphQL 代价**：服务端需 resolver，易踩 N+1（配 DataLoader）、查询复杂度需限流防滥用、HTTP 缓存难直接用。

```graphql
query {
  user(id: 1) {
    name
    posts(limit: 5) { title }   # 一次取用户及其帖子，无需多次请求
  }
}
```

> 🎯 关键要点
> - REST 多端点固定结构，GraphQL 单端点按需取
> - GraphQL 解决过度/不足获取与多轮请求
> - GraphQL 有强类型 schema 与自文档
> - REST 更易用 HTTP 缓存
> - GraphQL 需 DataLoader 防 N+1 与查询限流

> 🔍 追问
> - GraphQL 如何做缓存替代 HTTP 缓存？
> - 什么团队/场景不值得上 GraphQL？

### 42. 如何设计安全的API？｜高级

结论：API 安全是「纵深防御」——传输层 HTTPS 加密、认证鉴权验证身份与权限、输入校验与限流防滥用、安全头与 CORS 收敛暴露面、日志审计兜底；任何单点都不应成为唯一防线。

基础防线：

- **HTTPS**：全链路 TLS，禁止明文 HTTP；HSTS 强制。
- **认证（你是谁）**：JWT / Session / OAuth 校验身份。
- **授权（能做什么）**：基于角色/属性的权限（RBAC/ABAC），每个接口校验。

进阶防线：

```js
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const cors = require('cors');

app.use(helmet()); // 注入 CSP、X-Content-Type-Options 等安全头

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 分钟
  max: 100,                  // 单 IP 上限
});
app.use('/api/', limiter);

app.use(cors({
  origin: 'https://example.com',
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));
```

- **输入校验**：所有入参用 schema 校验（Joi / zod / DTO），防 SQL 注入、XSS、命令注入；用参数化查询而非字符串拼接 SQL。
- **速率限制**：防暴力破解与 DDoS，按 IP/用户/令牌分级。
- **CORS 收敛**：显式白名单 origin，不用 `*`。
- **安全头**：`helmet` 提供 CSP、X-Frame-Options、nosniff 等。
- **日志与监控**：记录认证失败、越权尝试等安全事件并告警。

> ⚠️ 注意
> 限流要区分「匿名 IP 限流」与「登录用户限流」：只对 IP 限流易被 NAT/代理后的真实用户共享配额误伤；敏感操作（登录、发短信）应对账号维度限流。

> 🎯 关键要点
> - 传输 HTTPS + HSTS 加密
> - 认证鉴权分离，逐接口校验权限
> - 入参强校验 + 参数化查询防注入
> - 限流、CORS 白名单、安全头三位一体
> - 安全事件日志化并告警

> 🔍 追问
> - 为什么参数化查询能防 SQL 注入？
> - 如何对「登录」做防爆破而不误伤正常用户？

### 43. 大模型/前端时代 API 契约如何管理？OpenAPI、zod 校验、tRPC 的类型安全链路如何落地，与 REST 的取舍是什么？｜高级

结论：在「前端 + 大模型」时代，API 契约的核心诉求是「前后端/客户端与模型调用之间的类型与行为一致」；落地有三条主流路线——OpenAPI（文档即契约）、zod（运行时校验即契约）、tRPC（端到端类型推导即契约），按「是否同源、是否需要对外开放」取舍。

路线一：OpenAPI（对外/跨语言契约）

```yaml
paths:
  /users/{id}:
    get:
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: integer }
      responses:
        '200':
          description: 用户
          content:
            application/json:
              schema: { $ref: '#/components/schemas/User' }
```

- 用 Swagger/Redoc 自动出文档，`openapi-typescript` 把 schema 生成前端类型。
- 适合对外 API、跨团队/跨语言，契约由文档驱动。

路线二：zod（运行时校验即契约）

```ts
import { z } from 'zod';
const UserSchema = z.object({ id: z.number(), name: z.string() });

app.post('/user', (req, res) => {
  const data = UserSchema.parse(req.body); // 运行时校验，失败直接抛
});
```

- schema 同时用于「校验入参」与「推断 TS 类型」（`z.infer`），单源真理。
- 适合内部服务，校验与类型一体，无需额外文档步骤。

路线三：tRPC（端到端类型安全）

```ts
// server
const appRouter = t.router({
  userById: t.procedure.input(z.string()).query(({ input }) => getUser(input)),
});
// client：类型自动推导，调用即得提示与返回值类型
const user = await client.userById.query('123');
```

- 前后端同仓库/同源时，客户端直接拿到服务端过程签名，改接口编译期就报错。
- 不适合「对外公开、异构客户端」场景（需要 HTTP 可调试的 REST/OpenAPI）。

取舍：

- 对外/多语言/需文档 → OpenAPI + 代码生成。
- 内部强类型、想省去手写类型 → zod 或 tRPC。
- 大模型调用：把模型输入/输出也用 zod/`response_format` 结构化，保证「提示契约」稳定，避免自由文本导致下游解析失败。

> 💡 提示
> 「大模型时代」的契约不止 REST：把 LLM 的工具调用（function calling）参数也用 JSON Schema/zod 约束，等价于给模型一份强类型 API，显著提升可解析性与稳定性。

> 🎯 关键要点
> - OpenAPI：文档驱动、跨语言、适合对外
> - zod：运行时校验与类型单源，适合内部
> - tRPC：端到端类型推导，适合同源前后端
> - 三者按「是否对外/是否同源」取舍
> - 大模型工具调用也应用 schema 约束输入输出

> 🔍 追问
> - tRPC 为什么不适合做公开第三方 API？
> - 如何用 OpenAPI 生成前端类型又保证运行时校验？

## 认证与授权（2 题）

### 44. 什么是JWT？它如何工作？｜中级

JWT（JSON Web Token）是 RFC 7519 定义的开放标准，用紧凑的 JSON 在各方间安全传递声明（claims），常用于无状态认证：服务端签发、客户端携带、服务端验签即可信任。

结构（三段，用 `.` 连接）：

1. **Header**：算法与类型，如 `{"alg":"HS256","typ":"JWT"}`。
2. **Payload**：声明（sub、exp、role 等用户数据）。
3. **Signature**：对前两段用密钥签名，防篡改。

```js
const jwt = require('jsonwebtoken');

// 签发
const token = jwt.sign(
  { userId: 123, role: 'admin' },
  'secret-key',
  { expiresIn: '1h' }
);

// 校验
const decoded = jwt.verify(token, 'secret-key'); // 验签失败抛错
```

HTTP 流程：

```js
const auth = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1]; // Bearer xxx
  if (!token) return res.status(401).json({ error: 'No token' });
  try {
    req.user = jwt.verify(token, 'secret-key');
    next();
  } catch {
    res.status(401).json({ error: 'Invalid token' });
  }
};
```

要点：

- **签名保证完整性**：篡改 payload 后签名对不上，`verify` 直接失败（但 payload 仅 base64，不可放敏感明文）。
- **无状态**：服务端不存会话，靠签名自校验，便于水平扩展。
- **过期与刷新**：设短 `expiresIn`，配合 refresh token 续期。
- **撤销难题**：JWT 签发后服务端无法主动失效，需靠短过期 + 黑名单/轮换密钥兜底。

> ⚠️ 注意
> 对称 `HS256` 签名时，签与验用同一密钥，前端/不可信方绝不能拿到密钥；若需「多方验签但不敢给私钥」，应换 `RS256`（公钥验、私钥签）。

> 🎯 关键要点
> - JWT 三段：Header.Payload.Signature
> - 签名防篡改，payload 仅 base64 编码不加密
> - 流程：登录签发 → 请求带 Bearer → 验签
> - 无状态利于扩展，但不易主动撤销
> - 用短过期 + refresh token 续期

> 🔍 追问
> - 如何安全地让 JWT 支持主动登出？
> - HS256 与 RS256 各自适用什么场景？

### 45. 什么是OAuth 2.0？它有哪些授权流程？｜高级

OAuth 2.0 是授权框架，让第三方应用在「用户授权」前提下获取对资源服务器的有限访问，而无需拿到用户密码；核心是「授权」而非「认证」（认证常叠加 OIDC）。

四种授权流程：

1. **授权码模式（Authorization Code）**：最安全，适合有后端的 Web 应用。先拿 code 再换 token，token 不暴露给浏览器。
2. **隐式模式（Implicit）**：token 直接返回前端，已不推荐（被 PKCE 增强的授权码取代），仅历史 SPA 用。
3. **密码模式（Resource Owner Password）**：用户把账号密码给客户端，仅限高度信任的第一方应用。
4. **客户端凭证模式（Client Credentials）**：机器对机器（M2M），用 client_id/secret 拿 token，无用户参与。

授权码流程（含 PKCE 更佳）：

```http
GET /authorize?
    response_type=code&
    client_id=CLIENT_ID&
    redirect_uri=CALLBACK_URL&
    scope=read&
    state=xyz123

GET /callback?code=AUTH_CODE&state=xyz123

POST /token
    grant_type=authorization_code&
    code=AUTH_CODE&
    redirect_uri=CALLBACK_URL&
    client_id=CLIENT_ID&
    client_secret=CLIENT_SECRET

GET /api/user
Authorization: Bearer ACCESS_TOKEN
```

要点：

- `state` 参数防 CSRF；现代 SPA 用 **PKCE（code_verifier/code_challenge）** 弥补无 secret 的安全缺口。
- `access_token` 短期、`refresh_token` 长期，过期用 refresh 续。
- scope 限制权限范围，遵循最小授权。

> ⚠️ 注意
> 隐式模式把 token 放在 URL 片段易泄露（浏览器历史、日志），OAuth 2.1 已将其废弃，统一推荐「授权码 + PKCE」。

> 🎯 关键要点
> - OAuth 2.0 是授权框架，核心是授权非认证
> - 四种流程：授权码/隐式/密码/客户端凭证
> - 授权码最安全，token 不落前端
> - state 防 CSRF，PKCE 补 SPA 安全
> - access 短期 + refresh 续期，scope 最小授权

> 🔍 追问
> - 为什么授权码模式比隐式模式安全？
> - PKCE 如何解决公共客户端无 secret 的问题？

## 部署、运维与全栈工程（5 题）

### 46. 如何部署Node.js应用？｜中级

结论：Node 部署从「裸机进程」到「容器化 + 编排」演进，核心都是「进程常驻 + 反向代理 + 环境变量配置 + 日志/健康检查」；全栈项目还要区分「SSR/同构」与「纯 API」的构建与静态资源托管差异。

常见方式：

- **传统/云主机**：`pm2` 守护 + `nginx` 反向代理（SSL 终止、静态、负载均衡）。
- **Docker**：打包运行时与依赖，环境一致，便于迁移。
- **云平台**：PaaS（Heroku、Railway）、Serverless（Vercel、Lambda）按需扩缩。

Dockerfile 示例：

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
```

docker-compose 串起依赖：

```yaml
version: '3'
services:
  app:
    build: .
    ports: ["3000:3000"]
    environment:
      - NODE_ENV=production
      - MONGODB_URI=mongodb://mongo:27017/myapp
  mongo:
    image: mongo
    ports: ["27017:27017"]
```

全栈工程视角：

- **SSR/同构（Next.js 等）**：服务端既要跑 Node 渲染又要托管构建产物，`nginx` 把 `/_next/static` 指到 CDN/静态层，动态请求转 Node；注意「构建阶段」与「运行阶段」分离（多阶段 Docker）。
- **纯 API**：Node 只提供 JSON，静态资源（前端 SPA）走 CDN，API 与前端独立部署、独立扩缩。
- **静态资源与 CDN**：把 JS/CSS/图片推到对象存储 + CDN，降低源站压力、提升首屏。
- **灰度与回滚**：用镜像 tag/digest 发布，流量按比例切（如 10% → 100%），异常一键回滚到旧 digest。
- **CI/CD**：提交触发 lint/test/构建，通过后推送镜像并滚动更新，避免手工上机。

> 💡 提示
> 环境变量（数据库地址、密钥）必须走运行时注入（K8s Secret / 平台变量），**绝不能写进镜像**；`npm ci` 比 `npm install` 更快且锁版本，适合生产构建。

> 🎯 关键要点
> - 部署核心：常驻进程 + 反代 + 环境变量 + 日志/健康检查
> - Docker 保证环境一致，compose 管依赖
> - SSR 需分离构建/运行阶段并托管静态产物
> - 静态资源走 CDN，API 与前端可独立扩缩
> - 用镜像 digest 做灰度与一键回滚，CI/CD 自动化

> 🔍 追问
> - 多阶段 Docker 构建对镜像体积有什么帮助？
> - SSR 应用如何做蓝绿/灰度发布？

### 47. 什么是PM2？如何使用PM2管理Node.js应用？｜中级

PM2 是 Node 的生产级进程管理器，提供守护（崩溃自拉起）、集群（多核）、日志聚合、监控与零停机重载，是裸机/云主机部署 Node 的事实标准工具之一。

核心能力：

- **进程守护**：进程崩溃自动重启，配合 ` --restart-delay` 防雪崩。
- **负载均衡**：`cluster` 模式用 `fork` 多实例吃满多核（替代手写 cluster 代码）。
- **日志管理**：集中输出、按大小轮转。
- **监控**：`pm2 monit` 看 CPU/内存。

常用命令：

```bash
npm install -g pm2

pm2 start app.js --name my-app        # 启动并命名
pm2 start app.js -i max --name my-app # 集群模式，按 CPU 数起实例
pm2 status                            # 查看状态
pm2 logs                              # 看日志
pm2 restart my-app
pm2 reload my-app                     # 零停机重载（逐个重启）
pm2 stop my-app
pm2 delete my-app
```

用 `ecosystem.config.js` 声明式管理：

```js
module.exports = {
  apps: [{
    name: 'my-app',
    script: 'server.js',
    instances: 'max',        // 集群模式
    exec_mode: 'cluster',
    env: { NODE_ENV: 'production' },
    max_memory_restart: '512M', // 内存超阈值自动重启，防泄漏拖死
    log_date_format: 'YYYY-MM-DD HH:mm:ss',
  }],
};
```

- **集群模式**：`-i max` 等价于 `instances: 'max'`，自动按 CPU 核数 `fork`，进程间通过 Round-Robin 分发连接。
- **日志轮转**：配合 `pm2-logrotate` 模块避免日志无限增长。
- **健康检查**：PM2 可配 `--wait-ready` + 应用 `process.send('ready')`，确保就绪后再接流量。

> ⚠️ 注意
> `pm2 reload` 是零停机（逐个 disconnect+refork），而 `pm2 restart` 会瞬间全部重启导致短暂不可用；生产用 `reload`/`gracefulReload`。

> 🎯 关键要点
> - PM2 提供守护、集群、日志、监控、零停机重载
> - cluster 模式 -i max 吃满多核
> - ecosystem.config.js 声明式管理环境
> - max_memory_restart 防内存泄漏雪崩
> - reload 零停机，restart 会闪断

> 🔍 追问
> - PM2 集群模式与手动 cluster 模块的关系？
> - 如何在 K8s 环境取舍 PM2 与容器编排？

### 48. 如何监控Node.js应用性能？｜高级

结论：Node 性能监控分「系统层（CPU/内存/磁盘）、应用层（QPS/延迟/错误率）、依赖层（DB/缓存/外部 API）」三维度，用 APM + `/metrics` 暴露指标 + 火焰图定位瓶颈，全栈还要把「前端首屏、SSR 耗时、接口延迟」串成端到端视图。

关键指标：

- **系统**：CPU 使用率、内存 `heapUsed/rss`、事件循环 lag、句柄/fd 数。
- **应用**：请求量、P50/P95/P99 延迟、错误率、并发连接。
- **依赖**：DB 查询耗时、Redis 命中率、下游 API 延迟。

Prometheus 指标暴露：

```js
const client = require('prom-client');
const httpRequestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP 请求耗时',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.1, 0.5, 1, 2, 5],
});
app.use((req, res, next) => {
  const end = httpRequestDuration.startTimer();
  res.on('finish', () => end({
    method: req.method,
    route: req.route?.path,
    status_code: res.statusCode,
  }));
  next();
});
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', client.register.contentType);
  res.end(await client.register.metrics());
});
```

工具栈：

- **PM2 monit**：进程级 CPU/内存快速查看。
- **clinic.js / 0x**：本地/临时性能剖析，出火焰图找热点。
- **APM**：New Relic、Datadog、Elastic APM 做全链路追踪与告警。
- **Prometheus + Grafana**：自建指标面板，配 `alertmanager` 告警。

全栈工程视角：

- **前端/SSR**：监控首屏 LCP、SSR HTML 生成耗时（Node 端）、hydration 失败率，避免「接口快但页面慢」。
- **前后端契约**：监控接口版本调用分布，旧版本调用归零后再下线。
- **灰度期对比**：新/旧实例指标同屏对比，异常立即回滚。

> 💡 提示
> P99 延迟比平均值更有意义——平均值掩盖长尾；告警应基于 P95/P99 而非均值，否则「大多数快」会掩盖「少数用户极慢」。

> 🎯 关键要点
> - 三维度：系统/应用/依赖指标
> - prom-client 暴露 /metrics 给 Prometheus
> - 火焰图（clinic/0x）定位热点函数
> - APM 做全链路追踪与告警
> - 全栈要看首屏+SSR+接口端到端

> 🔍 追问
> - 为什么 P99 比平均值更适合做告警阈值？
> - SSR 耗时该算在「前端」还是「后端」指标里？

### 49. 如何实现Node.js应用的日志管理？｜中级

结论：日志管理要做到「结构化、分级、轮转、集中、脱敏」——用 JSON 格式输出便于采集，按 level 过滤，按大小/时间轮转避免磁盘撑爆，集中到 ELK/Loki 做检索，并严禁记录密码/ token 等敏感信息。

基础与 Winston 实践：

```js
const winston = require('winston');
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json() // 结构化，便于 ES/Loki 解析
  ),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
  ],
});
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({ format: winston.format.simple() }));
}
logger.info('用户登录', { userId: 123 });
logger.error('异常', { error: new Error('x') });
```

要点与最佳实践：

- **结构化日志**：JSON 而非纯文本，字段可被索引检索（如按 `userId`、`traceId` 查）。
- **日志级别**：`debug/info/warn/error`，生产一般 `info`，排查临时调 `debug`。
- **日志轮转**：用 `winston-daily-rotate-file` 或 `pm2-logrotate` 按天/大小切分并保留 N 份，避免单文件无限增长。
- **集中式**：多实例日志汇总到 ELK / Grafana Loki / 云服务，支持跨实例检索与告警。
- **脱敏**：过滤 `password`、`authorization`、`cookie` 等字段，防止敏感信息落盘泄露。
- **关联追踪**：每条日志带 `traceId`，串联一次请求在网关、Node、DB 间的全链路。

全栈工程视角：

- **前后端同构日志**：SSR 报错要带上请求 URL 与 `userAgent`，便于复现前端环境问题。
- **契约/版本日志**：记录接口版本与调用方，辅助「旧版本调用归零再下线」的决策。
- **日志驱动告警**：error 日志突增、特定业务关键字出现即触发告警，比纯指标更早发现问题。

> ⚠️ 注意
> 不要在日志里直接 `JSON.stringify(req)` 或打印整个请求对象——它常含 `headers.authorization`、cookie，违反脱敏且体量大；应白名单式记录必要字段。

> 🎯 关键要点
> - 结构化（JSON）+ 分级 + 轮转 + 集中
> - winston 多 transport 分文件/级别
> - 轮转防磁盘撑爆，集中便于检索
> - 脱敏：绝不记录密码/token/cookie
> - 带 traceId 串联全链路，日志驱动告警

> 🔍 追问
> - 为什么结构化日志比文本日志更适合云原生？
> - 如何用 traceId 把前端报错与后端日志关联？
### 50. 如何实现 Node.js 应用的健康检查？｜中级

结论：健康检查是给编排器（K8s / 负载均衡 / PM2）看的探针端点，用来回答两个不同的问题——「这个进程还活着吗」和「这个实例现在能接流量吗」。因此必须拆成**存活（liveness）**、**就绪（readiness）**和**深度依赖（deep）**三类，各自语义不同，混在一起是会出生产事故的。

| 探针 | 典型端点 | 判断内容 | 失败后果 |
|---|---|---|---|
| 存活 liveness | `GET /healthz` | 进程能否响应、事件循环是否卡死 | 重启容器 |
| 就绪 readiness | `GET /readyz` | 启动预热是否完成、DB/Redis 是否可用、是否处于优雅退出中 | 从负载均衡摘除，**不重启** |
| 深度依赖 deep | `GET /healthz/deep` | 关键依赖逐项探测 + 磁盘/内存/连接池水位 | 触发告警，一般**不用**作探针 |

实现示例（Express）：

```js
const express = require('express');
const { monitorEventLoopDelay } = require('perf_hooks');
const app = express();

// 事件循环延迟直方图：liveness 的可靠依据，比“查 DB”安全得多
const loop = monitorEventLoopDelay({ resolution: 20 });
loop.enable();

let ready = false;
let shuttingDown = false;

// 存活：只证明“进程还能跑”，绝不查外部依赖
app.get('/healthz', (req, res) => {
  const p99 = loop.percentile(99) / 1e6; // 转毫秒
  if (p99 > 1000) return res.status(503).json({ status: 'degraded', loopP99ms: p99 });
  res.json({ status: 'ok', loopP99ms: Number(p99.toFixed(1)), uptime: process.uptime() });
});

// 就绪：不查依赖细节，只回答“能不能接流量”
app.get('/readyz', (req, res) => {
  if (!ready || shuttingDown) return res.status(503).json({ status: 'not-ready' });
  res.json({ status: 'ready' });
});

// 深度：逐项探测关键依赖，带超时与短缓存，避免探针自身打垮依赖
app.get('/healthz/deep', async (req, res) => {
  const checks = {};
  const withTimeout = (p, ms) => Promise.race([
    p, new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), ms).unref()),
  ]);

  checks.db = await withTimeout(db.query('SELECT 1'), 500)
    .then(() => ({ ok: true })).catch(e => ({ ok: false, error: e.message }));
  checks.redis = await withTimeout(redis.ping(), 500)
    .then(() => ({ ok: true })).catch(e => ({ ok: false, error: e.message }));

  const mem = process.memoryUsage();
  checks.heap = { ok: mem.heapUsed < 1.5 * 1024 ** 3, heapUsed: mem.heapUsed };

  const ok = Object.values(checks).every(c => c.ok);
  res.status(ok ? 200 : 503).json({ status: ok ? 'ok' : 'error', checks });
});

// 启动完成后再置 ready；优雅退出时先置 not-ready，等 LB 摘除后再排空
app.listen(3000, () => { ready = true; });
process.on('SIGTERM', () => { shuttingDown = true; });
```

> ⚠️ 注意
> 把 DB 查询写进 **liveness** 探针是经典事故：数据库抖动 → 所有实例被判死 → 集体重启 → 流量雪崩。liveness 只反映“进程自身是否健康”，依赖状态交给 readiness 与 deep 端点。

> 🎯 关键要点
> - 三类探针语义不同：liveness 管重启、readiness 管摘流量、deep 管告警
> - 存活探针只做进程内自检（事件循环延迟、内存水位），不碰外部依赖
> - 任何依赖探测都要有超时（`Promise.race`）与结果缓存/限频，避免探针放大故障
> - 端点响应体不暴露版本号、内部拓扑、连接串等敏感信息
> - 与优雅退出联动：先置 not-ready → 等一轮探针周期让 LB 摘除 → 再排空连接

> 🔍 追问
> - 为什么 readiness 失败只摘流量，而 liveness 失败要重启？两者判据怎么划清？
> - K8s 的 `initialDelaySeconds` / `failureThreshold` / `terminationGracePeriodSeconds` 如何与启动预热、优雅退出配合？
> - 健康检查端点该不该对外暴露或加鉴权？负载均衡健康检查与 K8s 探针冲突时怎么办？
