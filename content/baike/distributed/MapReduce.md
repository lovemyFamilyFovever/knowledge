---
title: "MapReduce"
tags: [分布式与并行计算, 大数据, 计算模型]
source: "baike"
source_path: "开发术语 / 分布式与并行计算"
collected: "2026-09-12"
status: "imported"
---

# MapReduce


> 📌 **导航**：本文是 **MapReduce** 词条，属于 distributed 术语集。相关枢纽：[[BASE 理论]]、[[CAP 定理]]、[[MapReduce]]、[[Saga 与 TCC]]、[[一致性哈希]]。

## 定义

**一句话定义：** MapReduce 是一种面向大规模数据集的**并行计算编程模型**,它把计算抽象为 Map(映射,将输入拆分为键值对并处理)和 Reduce(归约,对相同键的值进行汇总)两个阶段,由框架自动完成并行化、任务调度、容错与数据分发,使开发者无需操心底层集群细节。

**通俗类比：** 像统计一整个图书馆各作者的书数量:先让很多管理员分头翻各自负责的书堆,写下"(作者, 1)"的小纸条(Map);再把所有纸条按作者归拢到一起,每人负责把某作者的纸条数加起来(Reduce),最后得到每位作者的总数。

> 多义说明:本文讨论**编程模型/计算范式**;Apache Hadoop MapReduce 是其最著名的开源实现,但模型本身独立于具体实现。

## 原理与机制

执行流程(含中间的 Shuffle):

1. **Input/Split:** 输入被切分为若干分片,分发给多个 Map 任务。
2. **Map:** 用户定义的 map 函数处理每条记录,输出中间键值对 (k, v)。
3. **Shuffle & Sort:** 框架按 key 对中间结果分组、排序,并把相同 key 的数据搬到同一 Reduce 节点(这是最耗 I/O 的阶段)。
4. **Reduce:** 用户定义的 reduce 函数对每个 key 的值集合做聚合,输出最终结果。
5. **Output:** 写入分布式文件系统(如 HDFS)。

框架负责并行调度、节点故障重试(把失败任务重新分配)、数据本地性优化(把计算调度到数据所在节点)与负载均衡。

## 关键组成

| 组成 | 角色 |
|------|------|
| Map 函数 | 用户逻辑:输入 → 中间键值对 |
| Partition 函数 | 决定中间键发往哪个 Reduce(默认按 hash) |
| Shuffle/Sort | 框架按 key 分组、传输、排序 |
| Reduce 函数 | 用户逻辑:相同 key 的值 → 聚合结果 |
| 主/工作节点 | 调度与执行(如 Hadoop 的 JobTracker/TaskTracker 或 YARN) |

## 应用场景

- 大规模日志统计、词频统计(WordCount 是经典示例)
- 倒排索引构建、分布式排序(grep/sort)
- ETL 与批量数据清洗
- 机器学习特征计算等可分解为 map/reduce 的批处理任务

## 优点与局限

- 优点:编程模型简单、天然可扩展(scale-out)、内置容错、屏蔽分布式复杂性;适合离线大规模批处理。
- 局限:仅适合可表达为两阶段归约的问题;中间结果落盘导致延迟高,不适合低延迟/迭代计算(催生了 Spark 等内存计算);Shuffle 是性能瓶颈;难以表达复杂的 DAG 计算与实时流处理。

## 常见误区

- 认为 MapReduce 能做任意并行计算:它适合"可分解 + 可归约"的批任务,不擅长迭代/图计算(后者用 Spark/Pregel 等更合适)。
- 把 MapReduce 等同于 Hadoop:MapReduce 是模型,Hadoop 是包含 HDFS/YARN/MapReduce 的生态。
- 忽视 Shuffle 成本:大量跨节点数据传输常是作业变慢的主因。

## 相关术语

[[大数据技术栈]]、[[分布式基础术语百科]]、[[分布式存储术语百科]]、[[数据工程完全指南]]、[[一致性算法]]

## 参考资料

可参考 Jeffrey Dean 与 Sanjay Ghemawat 的论文《MapReduce: Simplified Data Processing on Large Clusters》(OSDI 2004);Apache Hadoop 为其开源实现;建议人工核验会议、年份与出处细节。
