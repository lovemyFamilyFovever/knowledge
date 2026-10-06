---
title: "Prometheus 指标与告警"
tags: []
source: "baike"
source_path: "技术文章 / 架构与设计"
collected: "2026-09-05"
status: "imported"
---

# Prometheus 指标与告警

> 📌 **导航**：本文是 **Prometheus 指标与告警** 词条，属于 architecture 术语集。相关枢纽：[[可观测性工程实战]]、[[监控与日志详解]]、[[微服务架构设计与实践]]、[[时序数据库 InfluxDB]]、[[高并发系统设计]]。

## 定义

**一句话定义：** 指标体系是把服务与资源状态聚合成**带标签的时间序列**，用 PromQL 求速率与分位数，再按规则判定告警、交给 Alertmanager 分组路由与抑制的整套落地方法——它用"牺牲个体换密度"回答"现在是否正常、什么时候该叫人"。

**通俗类比：** 像体检单上的血压与体温：一个数字概括全身，能看出趋势与异常，但查不出哪根血管在堵——那要靠更细的检查。

## 为什么需要它

日志逐条记录、链路逐请求记录，两者都太贵，无法高频回答"这五分钟错误率多少、P99 有没有劣化"。指标把计数压进时间序列：一条序列就覆盖全年趋势，因而可高频评估、可作告警输入。代价是聚合必然丢个体，所以要守住基数纪律，并留好下钻到日志与链路的出口。

## 核心机制

- **拉取与服务发现**：服务端按 scrape_interval（示例 15s）抓 /metrics；K8s 下用 kubernetes_sd_configs 发现 pod / node，再靠 relabel 以 pod annotation 改写 __address__ 与 __metrics_path__。
- **类型选型**只看两点——要不要算分位数、能不能跨实例聚合：

| 类型 | 语义 | 能算什么 | 典型坑 |
|---|---|---|---|
| Counter | 只增，重启归零 | rate / increase 求速率 | 直接看绝对值无意义 |
| Gauge | 可增可减 | 当前值与变化 | 当 Counter 用导致速率失真 |
| Histogram | 按预设 buckets 分桶 | 服务端算任意分位数、可跨实例聚合 | buckets 选错则 P99 不准 |
| Summary | 客户端算好分位数 | 直接读分位数 | 不能跨实例聚合，多实例下无解 |

- **基数控制**：序列数约等于各标签取值数的乘积。method / endpoint / status 可控；把 user_id、order_id 放进标签会让序列数随用户数爆掉。
- **查询与预聚合**：错误率 = 5xx 速率 / 总速率，分位数由 histogram_quantile 在 le 维度上聚合求得；反复出现的表达式固化成 recording rule，大盘与告警共用同一预聚合结果。
- **告警规则四要素**：表达式 + `for` 持续窗口去抖（避免瞬时抖动叫人）+ 标签（severity、team 供路由）+ annotations（summary、description、runbook 链接，让人一接手就能动作）。
- **告警管理**：group_by（alertname / cluster / service）聚合同源告警，group_wait 等首次成组、group_interval 控同组追加、repeat_interval 抑制重复轰炸；路由树按 severity → team → service 逐级分流，critical 推值班并 `continue: true` 抄送群，send_resolved 通知恢复。
- **设计准则 GOOD**：可操作、基于客观数据、覆盖关键路径、阈值动态调整。

## 具体示例

```text
埋点：REQUEST_COUNT{method,endpoint,status}.inc()
      REQUEST_LATENCY{method,endpoint}.observe(latency)   # Histogram
规则：5xx 速率 / 总速率 > 0.05  for: 2m   severity: critical → 值班, warning → 群
```

埋点决定能问什么，规则决定何时叫人，路由决定叫谁——三段各管一段，缺一都不可。

## 何时用与何时不用

- **用**：SLO 与容量趋势、需高频评估的告警条件、RED（服务）与 USE（资源）口径落地（见 [[监控与日志详解]]）。
- **不用**：按用户或订单回溯是日志与链路的职责；要精确到每一笔就别拿 rate 反推。
- **别忘**：拉取模型要求目标可被抓取，推送式与短生命周期任务改走 OTel（见 [[可观测性工程实战]]）。

## 优劣与代价

✅ 聚合存储便宜、查询快，标签即维度；recording rule 让同一算法全组织复用。
⚠️ 高基数标签会把时序库变成日志库，成本与查询延迟同时失控。
⚠️ 告警是放大器：过松漏报、过紧则造成告警风暴，对噪声的漠视会顺带吞掉真信号。

## 与相关概念的区别

- **Prometheus vs Grafana**：前者采集存储指标并跑 PromQL，后者只做可视化与多数据源聚合。
- **指标 vs SLI / SLO / SLA**：指标是测量值，SLO 是内部目标，SLA 是对外承诺（见 [[监控与日志详解]]）。
- **告警规则 vs 告警管理**：规则决定何时算异常，Alertmanager 决定叫谁、合并还是重复、静默多久。

## 常见误区

- 把 user_id 加进标签，就能既看趋势又按用户下钻，一举两得。
- 告警阈值定得越低越安全，多报几条没坏处。
- 平均响应时间升高，就足以说明服务在劣化。

## 面试速答

> 🎯 指标用聚合换密度：四类指标按"要不要分位数、能否跨实例聚合"选型，rate 与 histogram_quantile 出速率和 P99；高基数标签踢回日志与链路；告警要有 for 去抖、severity 路由与 runbook，Alertmanager 管分组与重复抑制。
> 🔍 追问：Histogram 与 Summary 在聚合上的区别？
> 🔍 追问：为什么要 for 窗口而不是超阈值立即告警？

## 相关术语

[[可观测性工程实战]]、[[监控与日志详解]]、[[日志管道与结构化采集]]、[[分布式链路追踪]]、[[时序数据库 InfluxDB]]、[[Kubernetes深入]]、[[服务发现]]、[[微服务治理术语百科]]、[[高并发系统设计]]、[[混沌工程]]

## 参考资料

建议人工核验：Prometheus / Alertmanager 字段（relabel 动作、route 的 group_wait 与 repeat_interval、recording rule 命名）与客户端库 API 以官方文档当前版本为准。原稿 §3 的 prometheus.yml、Flask 埋点、Grafana JSON、告警规则与 alertmanager.yml 清单依 v1.2 §8.1 收敛为机制叙述与类型表，不逐行保留配置。
