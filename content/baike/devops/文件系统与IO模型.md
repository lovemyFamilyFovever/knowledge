---
title: "文件系统与 I/O 模型"
tags: []
source: "baike"
source_path: "技术文章 / DevOps与运维"
collected: "2026-09-05"
status: "imported"
---

# 文件系统与 I/O 模型

> 📌 **导航**：本文是 **文件系统与 I/O 模型** 词条，属 [[操作系统内核原理]] 子词条。文件系统如何选型见 [[Linux 文件系统选型]]。

## 定义

**一句话定义：** 内核用 VFS 把不同磁盘文件系统统一成"文件/目录"接口（inode/dentry/superblock），用日志保证崩溃一致；而 I/O 模型（阻塞、非阻塞、select/poll/epoll 多路复用、io_uring）定义了进程与内核交换数据的等待方式。

**通俗类比：** VFS 是统一收银台——不管哪家供应商（ext4/XFS），你都用同一套动作结账；I/O 模型是"怎么等上菜"：干等、反复去看、还是叫号（epoll 只喊做好的）。

## 为什么需要它

上层程序只想要"打开/读/写文件"，不该关心底下是哪种文件系统——VFS 提供这层抽象。而高并发服务器若对成千上万连接各起线程阻塞等待会耗尽资源——I/O 多路复用让单线程高效等待大量描述符就绪。

## 核心机制

- **VFS 关键对象**：superblock（已挂载文件系统）、inode（文件元数据与数据块指针）、dentry（文件名→inode，缓存加速路径解析）、file（某进程打开的文件，含偏移）。`read()` 经系统调用进 VFS 再派发到具体 fs。
- **日志（Journaling）**：先写"意图"到日志区再提交主元数据，崩溃后重放/丢弃即可快速恢复；模式 `journal`/`ordered`(默认)/`writeback`。
- **I/O 模型**：阻塞、非阻塞（轮询耗 CPU）、多路复用 select（位图、上限 1024、每次拷贝+全遍历）→ poll（无上限、仍拷贝遍历）→ epoll（fd 存内核、回调只返回就绪、O(1) 级）→ io_uring（SQ/CQ 共享环形缓冲、批量、少系统调用）。

## 具体示例

epoll 把"监听的 fd 集合"常驻内核、只回就绪项，避免 select 的重复拷贝与全量遍历：

```c
int ep = epoll_create1(0);
epoll_ctl(ep, EPOLL_CTL_ADD, listenfd, &ev);      // fd 存进内核红黑树
int n = epoll_wait(ep, events, MAX, -1);          // 只返回就绪的 fd
for (i = 0; i < n; i++) handle(events[i].data.fd);
```

## 何时用与何时不用

- **用**：写网络服务器用 epoll（或新式 io_uring）做高并发；关心数据一致性用带日志的文件系统。
- **不用**：连接数极少时阻塞模型最简单；别用忙轮询非阻塞 fd 空烧 CPU。

## 优劣与代价

✅ VFS 统一各文件系统接口、日志保崩溃一致；epoll/io_uring 支撑高并发 IO。
✅ 从阻塞到异步的分层选择可匹配不同吞吐/延迟需求。
⚠️ 多路复用有边缘/水平触发、fd 生命周期等易错点；io_uring 有安全面与复杂度。
⚠️ 日志换一致性牺牲部分写性能；VFS 层也引入间接开销。

## 与相关概念的区别

- **select vs poll vs epoll**：前两者每次把 fd 集拷进内核并全量遍历，epoll 注册一次、事件回调只报就绪，规模大时优势明显。
- **同步多路复用 vs io_uring**：epoll 仍逐个 syscall 收发；io_uring 用共享环形队列批量提交/完成、大幅减少陷入开销。
- **VFS vs 具体 fs**：VFS 是抽象接口层，ext4/XFS 等是其实现。

## 常见误区

- epoll 比 select 快，主要因为它能监视更多 fd。
- 非阻塞轮询不消耗 CPU，只是不阻塞而已。
- VFS 是真正存在磁盘上的文件系统。

## 面试速答

> 🎯 VFS 用 superblock/inode/dentry/file 统一各文件系统接口、日志保崩溃一致；I/O 模型从阻塞→select/poll→epoll(只报就绪)→io_uring(SQ/CQ 共享环、少 syscall)演进，解决高并发高效等待。
> 🔍 追问：epoll 相比 select 快在哪、为什么？
> 🔍 追问：io_uring 想解决 epoll 的什么痛点？

## 相关术语

[[操作系统内核原理]]、[[Linux 文件系统选型]]、[[Linux 网络管理]]、[[进程与调度]]、[[Linux 性能分析工具]]

## 参考资料

建议人工核验：以《Linux 内核》VFS/IO 子系统文档与 epoll/io_uring man 页为准；未编造文献编号。
