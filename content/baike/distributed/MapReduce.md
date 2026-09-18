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

**一句话定义：** MapReduce 是面向大规模数据集的并行计算编程模型，把计算抽象为 Map（拆分处理成键值对）与 Reduce（按相同键汇总）两阶段，框架自动完成并行、调度、容错与数据分发。

**通俗类比：** 统计一整个图书馆各作者的书：先让管理员分头翻各自书堆写下"(作者,1)"的纸条（Map），再把纸条按作者归拢、每人把某作者的纸条数加总（Reduce）。

> 多义说明：本文讲编程模型 / 计算范式；Apache Hadoop MapReduce 是最著名的开源实现，模型本身独立于具体实现。

## 为什么需要它

单机处理不了 TB/PB 级数据，手写分布式并行又要自己管分片、调度、容错和数据搬运。MapReduce 把这些交给框架，开发者只写 map、reduce 两个函数，就能把任务摊到上千台机器并容忍节点故障。

## 核心流程

1. **Split：** 输入切成分片，分发给多个 Map 任务。
2. **Map：** 用户 map 函数处理每条记录，输出中间键值对 (k,v)。
3. **Shuffle & Sort：** 框架按 Partition 函数（默认 hash）决定 key 发往哪个 Reduce，分组、跨节点传输并排序——最耗 I/O 的阶段。
4. **Reduce：** 用户 reduce 函数对每个 key 的值集合做聚合，输出最终结果。
5. **Output：** 写入分布式文件系统（如 HDFS）。

框架同时负责并行调度、失败任务重试、数据本地性优化（把计算调度到数据所在节点）与负载均衡。

## 具体示例

WordCount：Map 把每行文本拆成 (单词,1)，Shuffle 把相同单词的 1 聚到一起，Reduce 求和得到词频——最经典的入门示例。

## 何时用与何时不用

- **用：** 可表达为"分解 + 归约"的离线大规模批处理（日志统计、倒排索引构建、ETL 清洗、分布式排序）。
- **不用：** 低延迟 / 交互式查询、迭代式计算（机器学习、图计算）与复杂 DAG——中间结果落盘使延迟高，这些场景 Spark 等内存引擎更合适。

## 优劣与代价

✅ 模型简单、天然 scale-out、内置容错、屏蔽分布式复杂性，适合离线批处理。
⚠️ 中间结果落盘、延迟高；Shuffle 是性能瓶颈；难表达复杂 DAG 与实时流处理。

## 与相关概念的区别

vs Spark：Spark 把中间结果留在内存、以 DAG 表达多阶段计算，迭代与交互式场景远快于 MapReduce 的"两阶段 + 落盘"模型。

## 常见误区

- MapReduce 能胜任任意类型的并行计算。
- MapReduce 就等于 Hadoop。
- MapReduce 适合低延迟的迭代式计算。

## 面试速答

> 🎯 MapReduce = Map 拆成键值对 + Shuffle 按 key 分组 + Reduce 汇总的批处理模型，框架自动并行 / 容错 / 数据本地化；强在离线大规模，弱在延迟（中间结果落盘）。
> 🔍 追问：为什么 Shuffle 是性能瓶颈？
> 🔍 追问：哪些场景该改用 Spark 而非 MapReduce？

## 相关术语

[[大数据技术栈]]、[[分布式基础术语百科]]、[[分布式存储术语百科]]、[[数据工程完全指南]]、[[一致性算法]]

## 参考资料

Jeffrey Dean 与 Sanjay Ghemawat《MapReduce: Simplified Data Processing on Large Clusters》(OSDI 2004)；Apache Hadoop 为其开源实现。
