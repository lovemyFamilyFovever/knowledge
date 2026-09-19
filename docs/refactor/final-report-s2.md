# baike 二期拆分 · 分片 2/5（系统线）收尾报告

规范依据 `docs/writing-spec-v1.2.md`。物理隔离：只处理 distributed/os/network/hardware/cs-basics 5 子域；台账只改 `s2.md`、`split-candidates.md`；报告只写本文件。

## 第二轮（本次）

队首为中小型（≤8000 字）→ 按规则最多处理 3 篇；遇下一篇巨型即停手。本轮完成 2 篇，停在巨型 `network/TCP深入.md`(8090字) 前。

### 1. network/HTTP协议.md（7815 字 / 13 围栏，中小）
- 父 → 枢纽页：§8.1 索引（5 条粗体子概念各含 [[双链]] 满足②b收紧 + 版本对比表满足① + 三版演进散文），1863 字，1 def + 2 trap，保留 RFC 9110–9114 / MDN 与原有全部双链。
- 新建 3 子词条：`HTTP请求方法`、`HTTP头部与内容协商`、`Cookie与Session`。
- §8.2 去重：状态码→[[HTTP 状态码]]、缓存→[[缓存策略]]、TLS→[[HTTPS 与 TLS]]、长连接→[[WebSocket]]、HTTP/3→[[QUIC]]，均双链不重复立条。

### 2. distributed/微服务治理术语百科.md（7925 字 / 12 围栏，中小）
- 父 → 枢纽页：§8.1 索引表 + mermaid 请求生命周期图，1446 字，1 def + 2 trap。
- 新建 3 子词条：`配置中心`、`API网关`、`灰度发布`。
- 去重：服务发现 / 负载均衡 / 熔断与降级 / 限流 / 服务网格 双链已有专条；链路追踪双链 architecture/可观测性工程实战（他片，不重复立条）。

### check_rewrite --strict（本轮新建/改写共 8 篇）：全 PASS，0 FAIL。
（唯一 warning 为新文件"⑤⑦ 不在 HEAD"，提交后自动消；HTTP头部 🎯 曾 195 字按 §4 压缩该行至 ≤150 后 PASS。）

### 剩余本分片 pending
- 巨型（各需独占一会话）：network/TCP深入.md(8090)、network/应用层协议.md(9411)、network/网络基础.md(8389)、network/网络安全协议.md(9247)
- 中小：os/进程管理详解.md(6581)
- 已排除：os/Linux 命令速查手册.md（改判 exempt-reference）
- **下一篇建议：network/TCP深入.md（8090 字 / 14 围栏，巨型 → 独占一会话）**

### 并发纪律复盘
本轮改用 `git commit -- <显式 pathspec>`（含先 `git add` 新文件），规避了上一轮"裸 commit 扫入他片暂存内容"的事故。提交前 §0.1 断言发现共享 index 中另有 database/*、s3.md、final-report-s4 等他片暂存项，遂不提交它们；另遇他片崩溃遗留的 ~19 分钟陈旧 index.lock（确认无 git.exe 持有后按 git 自身提示移除）。

**本会话 S2 拆分提交（git log 机器追加）：**
- 68fa370 docs: 二期拆分[S2]——HTTP协议 (枢纽+3子词条)
- a123657 docs: 二期拆分[S2]——微服务治理术语百科 (枢纽+3子词条)
- f8fdd48 docs: 二期拆分[S2]——分布式ID与缓存术语百科 (枢纽+2子词条)
