---
title: "Linux 性能分析工具"
tags: []
source: "baike"
source_path: "技术文章 / DevOps与运维"
collected: "2026-09-05"
status: "imported"
---

# Linux 性能分析工具

> 📌 **导航**：本文是 **Linux 性能分析工具** 词条，属 [[Linux系统管理高级指南]] 子词条。内核机制（调度器/内存/IO）见 [[操作系统内核原理]]，本文讲运维下钻手段。

## 定义

**一句话定义：** Linux 性能分析工具是定位 CPU、内存、IO、网络瓶颈的一组观测手段——先用 dstat/sar 全局扫异常，再用 perf（硬件事件与热点）、strace（系统调用）、tcpdump（抓包）、sysdig（系统活动）逐层下钻。

**通俗类比：** 像体检分科：先量血压体温（dstat/sar 看全局），发现异常再做 CT、胃镜（perf 看 CPU 热点、strace 看 syscall、tcpdump 看网络），而不是一个 X 光片想看清所有病。

## 为什么需要它

"系统变慢"是个笼统症状，根因可能在 CPU 饱和、锁竞争、IO 等待、丢包或某次慢系统调用。凭直觉重启或瞎调参数往往治标不治本。分层观测配合 USE 方法（利用率/饱和度/错误），能把"到底卡在哪一环"用数据定位出来。

## 核心机制

| 工具 | 看什么 | 典型用法 |
|---|---|---|
| dstat / sar | 全局资源实时/历史 | `dstat -cdnmsg` 看 CPU/磁盘/网络 |
| perf | CPU 计数器与热点 | `perf stat` 统计、`perf record -g`+`perf report` 看火焰/热点 |
| strace | 进程的系统调用 | `strace -c` 统计耗时、`strace -p <PID>` 附着 |
| tcpdump | 网络包 | `tcpdump -i eth0 port 80 -w x.pcap` |
| sysdig | 系统活动（融合 strace+tcpdump，可进容器） | `sysdig -c topprocs_cpu` |

方法：从全局（dstat/sar/vmstat）到局部（perf/strace/tcpdump），按 USE 逐资源查利用率/饱和度/错误。

## 具体示例

先用 `perf` 找 CPU 热点、再用 `strace -c` 看是不是大量慢系统调用——两步覆盖"计算慢"与"卡在 syscall"两类常见根因：

```bash
perf stat ./prog            # 看 IPC、缓存未命中、分支预测失败
perf record -g ./prog && perf report   # 定位热点函数
strace -c ./prog            # 汇总各系统调用次数与耗时占比
```

## 何时用与何时不用

- **用**：CPU 高、响应慢、IO 等待大、丢包等线上/压测排障；上线前用 `perf`/`strace` 找热点。
- **不用**：长期趋势与告警交给 [[监控与日志详解]]（Prometheus/Grafana），别拿 strace 当常驻监控（开销大）。

## 优劣与代价

✅ 从宏观到微观逐层定位，避免凭猜优化。
✅ perf/strace 等能精确到函数/系统调用级别。
⚠️ 多为短时高开销工具（strace/perf record），生产常驻会拖慢、可能改变时序。
⚠️ 需 root 与内核符号，学习曲线陡、输出信息量大。

## 与相关概念的区别

- **一次性下钻 vs 持续监控**：perf/strace/tcpdump 是"出事时深挖"；[[监控与日志详解]] 是"7×24 看趋势与告警"，二者互补。
- **strace vs ltrace**：strace 追系统调用（与内核交互），ltrace 追库函数调用。
- **perf 计数 vs 采样**：`perf stat` 统计总量、`perf record` 采样定位热点。

## 常见误区

- top 一个工具就能看到所有瓶颈的根本原因。
- strace 抓的是网络数据包，tcpdump 抓的是系统调用。
- 线上排查就该把 strace 一直挂着当监控用。

## 面试速答

> 🎯 Linux 性能分析按"全局→局部 + USE 方法"下钻：dstat/sar/vmstat 看全局资源，perf 找 CPU 热点/计数器，strace 追系统调用，tcpdump 抓网络包，sysdig 综合且能进容器。多为短时深挖工具，长期趋势交给 [[监控与日志详解]]。
> 🔍 追问：USE 方法指什么、怎么用？
> 🔍 追问：strace 和 tcpdump 分别定位哪类问题？

## 相关术语

[[Linux系统管理高级指南]]、[[操作系统内核原理]]、[[监控与日志详解]]、[[调试与性能分析]]

## 参考资料

建议人工核验：工具用法以 Brendan Gregg《Systems Performance》及各工具 man 页为准；未编造文献编号。
