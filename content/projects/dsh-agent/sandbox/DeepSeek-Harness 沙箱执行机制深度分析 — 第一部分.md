---
title: "DeepSeek-Harness 沙箱执行机制深度分析 — 第一部分"
tags: []
source: "baike"
source_path: "项目分析 / DSH Agent 项目分析 / 沙箱执行机制"
collected: "2026-09-05"
status: "imported"
---

DeepSeek-Harness 沙箱执行机制深度分析 — 第一部分
☰
目录导航
第一部分
1. 文件系统抽象层
1.1 虚拟文件系统接口设计
1.2 文件操作的原子性保证
1.3 路径规范化和安全检查
2. 本地文件系统实现
2.1 读写操作的实现
2.2 权限管理
2.3 大文件处理
3. 文件系统工具
3.1 Diff 生成和应用
3.2 编辑操作（搜索替换）
3.3 文件读取策略
DeepSeek-Harness 沙箱执行机制深度分析
第一部分：文件系统抽象层、本地文件系统实现与文件系统工具
全部报告：
第一部分
|
第二部分
|
第三部分
1. 文件系统抽象层
1.1 虚拟文件系统接口设计
DeepSeek-Harness 的文件系统抽象采用了经典的
Capability Seam（能力接缝）
设计模式，通过 Cordis 依赖注入框架的 Service 机制实现。核心抽象类
FileSystem
定义在
packages/fs/fs/src/index.ts
中，注册为
ctx.fs
服务，是一个纯抽象的 Service Definition，不包含任何平台相关的实现。
接口层次结构
FsTarget
— 路径解析后的稳定目标标识
由
resolve()
方法返回，包含
targetKey
（不透明的后端标识，Branded 类型）和
displayPath
（面向模型/UI 的显示路径）。远程后端可以用工作区 URI 或文件 ID 作为 key，本地后端使用 realpath 字符串。
FsVersion
— 文件版本令牌
Branded 不透明类型。本地后端从高分辨率
BigIntStats
中派生，格式为
dev:ino:size:mtimeNs:ctimeNs
。策略层记录它用于过期检查，消费者不得解释。
FsObservation
— 观察结果
判别联合类型：
present
（携带版本号）或
absent
。
present
授权受保护的替换操作，
absent
只授权受保护的创建操作，绝不授权编辑。
FsInfo
/
FsPathInfo
— 目标元数据
FsInfo
是
stat
的结果（跟踪符号链接），
FsPathInfo
是
lstat
的结果（不跟踪最终符号链接组件），后者让信任边界规则在
resolve
之前拒绝仓库拥有的链接。
事件驱动的决策机制
抽象层定义了三个关键事件，构成写入/编辑的决策流水线：
fs/write-intent
：单槽决策瀑布事件，用于
writeText
。调用
next()
产生无条件写入；第一个返回意图的监听者拥有决策权。
fs/edit-intent
：单槽决策瀑布事件，用于
editText
。调用
next()
产生无条件编辑。
fs/observed
：火忘记录事件，携带
FsObservation
。监听者必须是同步的纯记录器。
设计优势
：事件驱动的设计将策略（
dsh-fs-observation-policy
）和执行（
dsh-tool-fs
）解耦，策略插件通过监听事件来决定写入/编辑的意图，工具层只负责调度事件和调用
ctx.fs
。
不变量守卫
packages/fs/fs/src/invariant.ts
定义了不变量检查，通过 Cordis 的
internal/dispatch
全局事件拦截器验证所有
fs/*
事件的数据合法性：
targetKey
和
displayPath
必须非空，
fs/observed
的
present
版本必须非空。
1.2 文件操作的原子性保证
原子写入流程
writeFileAtomic
写入操作的原子性通过
暂存-发布（staging-then-publish）
模式实现：
目录创建
：
mkdir(directory, { recursive: true })
确保目标目录存在。
私有暂存目录
：在目标目录下创建以 PID 和 UUID 命名的私有暂存目录（如
.filename.12345.uuid.tmpdir
），权限为
0o700
。
独占创建临时文件
：使用
open(tempPath, 'wx', 0o600)
以独占模式创建——
wx
标志确保在已存在路径上失败，防止竞态条件。
权限和 DACL 复制
：POSIX 上设置
0o600
权限；Windows 上复制目标文件的 DACL 到临时文件。
写入和同步
：
handle.writeFile
写入内容，
handle.sync()
确保数据落盘。
权限恢复
：如果目标文件已存在，恢复其原始权限模式。
原子发布
：
createIfAbsent
使用
link()
硬链接；Windows 替换使用安全的
replaceFile
；默认使用
rename()
原子替换。
清理暂存目录
：发布成功后清理（失败不抛出异常，因为目标已提交）。
原子编辑流程
editText
编辑操作在
per-target 锁
下执行完整的 read→match→write 关键段：
锁获取
：
withLock(targetKey, op)
通过 Promise 链提供 FIFO 排他访问。
过期保护
：检查文件是否仍然存在且版本匹配。
读取内容
：
readForEdit
读取文件，检测二进制，返回 LF 规范化的内容。
应用替换
：
applyLiteralEdit
执行字面量替换——要求恰好一次匹配（除非
replaceAll
）。
行尾恢复
：
restoreLineEndings
恢复原始行尾风格。
原子写回
：调用
writeFileAtomic
原子发布。
关键保证
：并发写入/编辑的确定性排序（一个赢，其余看到新版本并拒绝为过期）；编辑操作不会产生部分写入；版本检查在字面量匹配之前执行。
1.3 路径规范化和安全检查
路径解析策略
路径解析分为两种情况：
文件存在
：直接使用
realpath(displayPath)
解析符号链接得到稳定的 target key。
文件不存在
：逐级向上查找最近存在的祖先目录，对每个祖先执行
realpath
，然后重新拼接缺失的后缀。确保 target key 在文件创建前后保持稳定。
Windows 特殊处理
：Windows 上
realpath
对普通文件成功（而不是 POSIX 的 ENOTDIR），需要额外的
stat
检查来区分。
行尾规范化
所有文本操作都在 LF 规范化的内部表示上工作：
normalizeLineEndings
将
\r\n
替换为
\n
；
restoreLineEndings
写回时恢复原始行尾风格；
detectLineEndings
从前 4096 字节检测。确保 CRLF 文件的编辑不会产生"每行都改变了"的 diff。
2. 本地文件系统实现
2.1 读写操作的实现
LocalFileSystem
（
packages/fs/fs-local/src/index.ts
）是
FileSystem
的本地磁盘实现，注册为
ctx.fs
。
读取策略
readText
：一次性读取整个文件。先
stat
检查是否为普通文件，前 8192 字节包含 NUL 字节则拒绝为二进制（
FS_NOT_TEXT
），使用
TextDecoder('utf-8', { fatal: true })
严格解码。
streamText
：流式读取大文件。使用生成器函数
streamWholeText
，逐块解码 UTF-8，每块都检查前 8192 字节的 NUL。
readBytes
：原始字节读取。
stat
预检查大小 +
createReadStream
带
end: maxBytes
限制。文件在 stat 后增长也不能绕过限制。
listDir
：使用
readdir
读取目录，按名称排序，对每个子项解析目标并获取元数据，不读取文件内容。
2.2 权限管理
本地文件系统本身不强制权限。权限由两个层面提供：
文件系统层面
：POSIX 模式位被保留——写入操作在创建新文件时使用
0o600
，替换时保留原始
mode
。Windows 上通过 DACL 复制实现。
沙箱层面
：
SandboxedFileSystem
（
packages/fs/fs-sandbox/src/index.ts
）在继承的写入/编辑操作前添加策略检查。
2.3 大文件处理
流式读取
：
streamText
返回
AsyncIterable<string>
，后端拥有跨块 UTF-8 解码和二进制拒绝。
有界 diff 基础
：
diffBasisMaxBytes
（默认 10 MiB）限制 diff 基础的大小。
有界原始读取
：
readBytes
的
maxBytes
参数是必需的，stat 预检 + 流读取双重保护。
尾部保留的输出收集器
：
OutputCollector
实现了尾部保留的有界内存缓冲，配合溢出到磁盘的 spill 文件。
3. 文件系统工具
3.1 Diff 生成和应用
packages/fs/tool-fs/src/diff.ts
实现了结果时间的上下文 diff 展示。
Hunk Diff 计算
computeHunkDiffs
使用
diff
库的
structuredPatch
生成统一 diff，上下文行数为 3。对于每个 hunk，解析
-
行和
+
行，上下文行同时出现在两边；跳过
no-newline
标记行；输出
{ path, oldText, newText }
格式——纯插入使用
oldText: null
；散布的替换保持为独立 hunks。
3.2 编辑操作（搜索替换）
packages/fs/tool-fs/src/edit.ts
是面向模型的字面量编辑工具。
执行流程
：解析沙箱策略 → 解析目标路径 → 通过
fs/edit-intent
瀑布获取版本守卫 → 调用
ctx.fs.editText
（后端在锁内执行版本检查→字面量匹配→原子替换）→ 记录
fs/observed
观察 → 如果
FS_SANDBOX_DENIED
则映射为
[sandbox: ...]
标记 + 提升提示。
3.3 文件读取策略
packages/fs/tool-fs/src/read.ts
实现了面向模型的有界文本读取。
读取限制
默认和最大行数：
2000 行
（
READ_LIMIT
）
流式阈值：
10 MiB
（
STREAM_MIN_SIZE
）——大于等于此大小的文件使用流式读取
并发安全性：
isConcurrencySafe: () => true
——观察竞态失败关闭
Write 工具
的实现与 Edit 类似，但支持
createIfAbsent
和
replaceIfVersion
两种写入意图，分别用于新文件创建和现有文件覆盖的场景。
下一部分：沙箱执行环境、终端管理 →
DeepSeek-Harness 沙箱执行机制深度分析 — 第一部分 | 基于源码分析生成
↑