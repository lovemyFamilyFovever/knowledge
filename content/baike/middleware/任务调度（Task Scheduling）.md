---
title: "任务调度（Task Scheduling）"
tags: []
source: "baike"
source_path: "开发术语 / 消息与中间件"
collected: "2026-09-05"
status: "imported"
---

# 任务调度（Task Scheduling）

## 分布式任务调度概念

### 一句话定义
分布式任务调度是在**多台服务器上协调、分配和执行定时任务**的系统，确保任务不重复、不遗漏、高可用。

### 通俗类比
像一个学校排课系统：教导主任（调度中心）决定每节课（任务）在哪个教室（服务器）上课，避免两门课排在同一教室同一时间，还要处理请假调课（故障转移）。

### 为什么需要它

| 单机调度的问题 | 分布式调度的解决 |
|----------------|------------------|
| 服务器挂了任务停了 | 自动转移到其他节点 |
| 单点性能瓶颈 | 任务分片，多节点并行 |
| 任务重复执行 | 分布式锁保证唯一性 |
| 运维困难 | 统一管理界面和监控 |

### 核心架构

```
┌─────────────────────────────────────────┐
│            调度中心（Scheduler）          │
│  ┌──────────┐  ┌──────────┐            │
│  │ 任务管理  │  │ 调度引擎  │            │
│  │ CRUD/日志 │  │ Cron触发  │            │
│  └──────────┘  └──────────┘            │
└───────────┬──────────┬──────────────────┘
            │          │
      ┌─────┴──┐  ┌────┴───┐
      │执行器 A │  │执行器 B │
      │分片 0,2 │  │分片 1,3 │
      └────────┘  └────────┘
```

---

## XXL-JOB

### 一句话定义
XXL-JOB 是一个**轻量级分布式任务调度平台**，特点是简单易用、功能全面，国内使用率极高。

### 通俗类比
像一个外卖平台的调度系统：平台（调度中心）决定哪个订单（任务）派给哪个骑手（执行器），骑手完单后回报结果。

### 核心组件

| 组件 | 职责 |
|------|------|
| 调度中心（Admin） | 管理任务、触发调度、查看日志 |
| 执行器（Executor） | 接收调度指令、执行任务、汇报结果 |
| 调度器（Scheduler） | 基于 cron 触发调度 |
| 路由策略 | 轮询/随机/故障转移/分片广播 |

### 任务分片示例

```java
@XxlJob("orderSyncHandler")
public void execute() {
    // 获取分片参数
    int shardIndex = XxlJobHelper.getShardIndex();   // 当前分片序号
    int shardTotal = XxlJobHelper.getShardTotal();   // 总分片数

    // 按分片查询数据
    List<Order> orders = orderMapper.selectByShard(shardIndex, shardTotal);

    // 处理数据
    for (Order order : orders) {
        processOrder(order);
    }

    XxlJobHelper.log("分片 {}/{}，处理 {} 条订单", shardIndex, shardTotal, orders.size());
}
```

### 失败重试机制

```
任务执行失败
    │
    ▼
是否启用重试？──否──▶ 标记失败，发送告警
    │
    是
    │
    ▼
重试次数 < 最大重试次数？
    │
    是 ──▶ 等待重试间隔 ──▶ 重新执行
    │
    否
    │
    ▼
标记最终失败，发送告警
```

### 任务日志

| 日志类型 | 说明 |
|----------|------|
| 调度日志 | 何时触发、路由到哪个执行器 |
| 执行日志 | 任务执行过程的业务日志 |
| 错误日志 | 异常堆栈、失败原因 |

---

## Elastic-JOB

### 一句话定义
Elastic-JOB 是**当当网开源**的分布式任务调度框架，基于 ZooKeeper 实现弹性扩容和任务分片。

### 通俗类比
像一个智能快递柜：快递（任务）来了，系统根据柜子（节点）数量自动分配格子（分片），柜子坏了自动把格子迁移到其他柜子。

### Sharding 概念

| 概念 | 说明 |
|------|------|
| Sharding（分片） | 将一个任务拆分成多个子任务并行执行 |
| Sharding Context | 执行时的分片上下文，包含分片参数 |
| 分片策略 | 均匀分配、自定义分配 |

### 对比 XXL-JOB

| 维度 | XXL-JOB | Elastic-JOB |
|------|---------|-------------|
| 注册中心 | 内置/可选ZK | 强依赖 ZooKeeper |
| 弹性扩容 | 手动配置 | 自动感知节点变化 |
| 任务分片 | 路由策略实现 | 原生分片支持 |
| 学习成本 | 低 | 中等 |
| 适用场景 | 中小规模 | 大规模弹性场景 |

---

## SchedulerX（阿里云）

### 一句话定义
SchedulerX 是**阿里云提供的分布式任务调度服务**，深度集成阿里云生态，支持复杂工作流。

### 通俗类比
像阿里云版的"超级工厂调度员"：不仅管任务调度，还能协调多个工序（工作流）、处理异常（故障恢复）、提供大屏监控。

### 核心能力

| 功能 | 说明 |
|------|------|
| 可视化编排 | 拖拽式 DAG 工作流 |
| 多集群管理 | 跨地域、跨集群调度 |
| 故障自愈 | 自动故障转移和重试 |
| 大盘监控 | 实时任务运行状态大屏 |
| 任务血缘 | 任务依赖关系可视化 |

---

## 延迟队列

### 一句话定义
延迟队列是一种**消息在指定时间后才能被消费**的队列，用于实现定时任务和延迟处理。

### 通俗类比
像一个预约取件柜：你把快递放进去，设好明天下午3点取，之前别人打不开，到时间了才能取。

### Redis 实现方案

```python
# 使用 Redis Sorted Set 实现延迟队列
import redis
import time

r = redis.Redis()

def add_delay_task(task_id, delay_seconds):
    execute_at = time.time() + delay_seconds
    r.zadd("delay_queue", {task_id: execute_at})

def poll_delay_queue():
    while True:
        now = time.time()
        tasks = r.zrangebyscore("delay_queue", 0, now, start=0, num=1)
        if tasks:
            task_id = tasks[0]
            r.zrem("delay_queue", task_id)
            process_task(task_id)
        time.sleep(0.1)
```

### RocketMQ 延迟消息

```
发送延迟消息 ──▶ Broker 存储 ──▶ 到期自动投递 ──▶ 消费者处理

支持18个延迟级别：
1s  5s  10s  30s  1m  2m  3m  4m  5m  6m  7m  8m  9m  10m  20m  30m  1h  2h
```

### 方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| Redis ZSet | 简单高效 | 重启可能丢数据 |
| RocketMQ 延迟消息 | 可靠、支持持久化 | 延迟级别固定 |
| 时间轮算法 | 高精度 | 实现复杂 |
| 数据库轮询 | 简单 | 性能差、精度低 |

---

## 优先级队列

### 一句话定义
优先级队列按照**任务优先级**来决定执行顺序，高优先级任务优先处理。

### 通俗类比
像医院的分诊台：不是先来先看，而是危重病人（高优先级）优先，普通感冒（低优先级）排队等。

### 堆实现

```python
import heapq

class PriorityQueue:
    def __init__(self):
        self._queue = []
        self._index = 0

    def push(self, priority, item):
        heapq.heappush(self._queue, (-priority, self._index, item))
        self._index += 1

    def pop(self):
        return heapq.heappop(self._queue)[-1]

# 使用示例
pq = PriorityQueue()
pq.push(10, "紧急修复")
pq.push(1, "日常维护")
pq.push(5, "功能开发")
print(pq.pop())  # 输出: 紧急修复
```

### 数据库实现

```sql
-- 优先级队列表
CREATE TABLE task_queue (
    id BIGINT PRIMARY KEY,
    task_type VARCHAR(50),
    priority INT DEFAULT 0,
    status ENUM('pending', 'processing', 'completed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_priority_status (priority DESC, status, created_at)
);

-- 获取最高优先级任务
SELECT * FROM task_queue
WHERE status = 'pending'
ORDER BY priority DESC, created_at ASC
LIMIT 1;
```

---

## 分布式定时任务

### 一句话定义
分布式定时任务需要解决**多节点协调执行、避免重复、故障转移**等问题。

### 避免重复执行

| 方案 | 原理 | 适用场景 |
|------|------|----------|
| 分布式锁 | Redis/ZK 锁，同一时间只有一个节点执行 | 简单任务 |
| 调度中心统一调度 | 由调度中心决定执行哪个节点 | XXL-JOB/Elastic-JOB |
| 数据库唯一索引 | 通过唯一约束防止重复记录 | 批处理任务 |
| 乐观锁 | 版本号控制，更新失败则跳过 | 高并发场景 |

### 任务锁实现

```java
// Redis 分布式锁实现
public boolean tryLock(String taskKey) {
    String lockKey = "task:lock:" + taskKey;
    String requestId = UUID.randomUUID().toString();

    Boolean locked = redisTemplate.opsForValue()
        .setIfAbsent(lockKey, requestId, 30, TimeUnit.SECONDS);

    if (Boolean.TRUE.equals(locked)) {
        lockResources.put(taskKey, requestId);
        return true;
    }
    return false;
}

public void releaseLock(String taskKey) {
    String requestId = lockResources.get(taskKey);
    String script = "if redis.call('get', KEYS[1]) == ARGV[1] then "
                  + "return redis.call('del', KEYS[1]) else return 0 end";
    redisTemplate.execute(new DefaultRedisScript<>(script, Long.class),
        List.of("task:lock:" + taskKey), requestId);
}
```

---

## Crontab 表达式详解

### 一句话定义
Crontab 是一种**时间表达式语法**，用于指定任务的执行时间规则。

### 表达式格式

```
┌───────────── 分钟 (0-59)
│ ┌───────────── 小时 (0-23)
│ │ ┌───────────── 日 (1-31)
│ │ │ ┌───────────── 月 (1-12)
│ │ │ │ ┌───────────── 星期 (0-7, 0和7都是周日)
│ │ │ │ │
* * * * * command
```

### 常用示例

| 表达式 | 含义 |
|--------|------|
| `0 2 * * *` | 每天凌晨 2:00 |
| `*/5 * * * *` | 每 5 分钟 |
| `0 9-18 * * 1-5` | 工作日每小时整点 |
| `0 0 1 * *` | 每月 1 号 0:00 |
| `30 8 * * 1` | 每周一 8:30 |
| `0 0 * * 0,3,6` | 每周日、三、六 0:00 |

### 特殊符号

| 符号 | 含义 | 示例 |
|------|------|------|
| `*` | 每 | `* * * * *` 每分钟 |
| `,` | 列表 | `1,3,5` 在1、3、5点 |
| `-` | 范围 | `9-18` 9到18点 |
| `/` | 步长 | `*/10` 每10分钟 |

---

## 任务编排（DAG 任务流）

### 一句话定义
DAG（有向无环图）任务编排将**多个任务按依赖关系组织**，确保前置任务完成后才执行后续任务。

### 通俗类比
像做菜的流程：先洗菜（任务A），再切菜（任务B），然后炒菜（任务C）。B 依赖 A 完成，C 依赖 B 完成，但 A 的配菜（任务D）可以和 B 并行。

### DAG 示例

```
        ┌──────┐
        │  A   │ (数据提取)
        └──┬───┘
           │
      ┌────┴────┐
      ▼         ▼
  ┌──────┐  ┌──────┐
  │  B   │  │  D   │ (并行执行)
  │ 转换 │  │ 清洗 │
  └──┬───┘  └──┬───┘
     │         │
     └────┬────┘
          ▼
      ┌──────┐
      │  C   │ (数据加载)
      └──────┘
```

### 工作流引擎

| 引擎 | 特点 |
|------|------|
| Apache Airflow | Python 生态，社区活跃 |
| DolphinScheduler | 国产，可视化强，适合大数据 |
| Azkaban | LinkedIn 开源，简单轻量 |
| XXL-JOB | 支持简单 DAG，适合业务调度 |

### Airflow DAG 示例

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

with DAG('order_pipeline', start_date=datetime(2024, 1, 1),
         schedule_interval='@daily') as dag:

    extract = PythonOperator(task_id='extract', python_callable=extract_data)
    transform = PythonOperator(task_id='transform', python_callable=transform_data)
    load = PythonOperator(task_id='load', python_callable=load_data)

    extract >> transform >> load
```

---

## 任务监控与告警

### 一句话定义
任务监控实时跟踪任务的**运行状态、执行耗时、失败率**等指标，异常时自动触发告警。

### 监控指标

| 指标 | 说明 |
|------|------|
| 执行成功率 | 成功次数 / 总执行次数 |
| 平均耗时 | 任务平均执行时间 |
| 调度延迟 | 从触发到实际执行的延迟 |
| 失败率趋势 | 失败率是否持续上升 |
| 死信任务 | 多次重试仍失败的任务 |

### 告警方式

```
任务执行失败
    │
    ├──▶ 钉钉/企业微信通知
    ├──▶ 邮件告警
    ├──▶ 短信告警（严重级别）
    └──▶ 监控大屏标红
```

### 常见监控方案

| 方案 | 适用场景 |
|------|----------|
| XXL-JOB 内置监控 | 中小规模，简单运维 |
| Prometheus + Grafana | 可视化强，指标丰富 |
| SkyWalking 链路追踪 | 需要追踪任务上下游 |
| 自建监控平台 | 大规模、定制化需求 |
