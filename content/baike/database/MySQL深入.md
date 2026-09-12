---
title: "MySQL深入"
tags: [数据库, MySQL, InnoDB, 索引]
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# MySQL深入


> 📌 **导航**：本文是 **MySQL深入** 词条，属于 database 术语集。相关枢纽：[[MySQL从入门到架构师]]、[[MySQL深入]]、[[Redis深入]]、[[Redis深度解析与实战指南]]、[[SQL 基础术语]]。

## 定义

**一句话定义：** 本文聚焦 MySQL（InnoDB 引擎）的核心机制——B+ 树索引、事务隔离、MVCC、锁与慢查询优化，是理解 MySQL 高性能与一致性的关键。

**通俗类比：** MySQL 像一座大型图书馆——B+ 树索引是高效的目录卡片，事务隔离与 MVCC 保证多人同时借还不互相干扰，锁机制防止同一本书被同时涂改。

> 多义说明：本文是 MySQL 的**原理速览**；更完整的入门到架构见 [[MySQL从入门到架构师]]。索引、事务、MVCC 各有专门词条：[[B+树]]、[[索引与查询优化术语]]、[[事务隔离级别]]、[[多版本并发控制]]、[[事务与并发控制术语]]。

## 原理与机制

### 索引原理（B+ 树）

```
       [10 | 20 | 30]              <- 非叶子只存索引键
      /    |    |    \
 [1,5,8] [12,15] [22,25] [31,35]   <- 叶子存数据/主键
     <->    <->    <->    <->       <- 叶子双向链表，范围查询高效
```

- 非叶子只存键、叶子存数据（聚簇索引）或主键（二级索引，需回表）。
- 矮胖的多叉树使磁盘 I/O 次数少；一棵 3 层 B+ 树可支撑千万级行。详见 [[B+树]]。

### 事务隔离级别

| 级别 | 脏读 | 不可重复读 | 幻读 | 说明 |
|------|------|-----------|------|------|
| READ UNCOMMITTED | 有 | 有 | 有 | 读未提交，最低隔离 |
| READ COMMITTED | 无 | 有 | 有 | 读已提交（Oracle 默认） |
| REPEATABLE READ | 无 | 无 | InnoDB 基本消除 | **MySQL 默认**，靠 MVCC + 间隙锁 |
| SERIALIZABLE | 无 | 无 | 无 | 串行化，最高隔离、最低并发 |

> 详见 [[事务隔离级别]]。

### MVCC（多版本并发控制）

```
每行隐藏列：DB_TRX_ID(最后修改事务ID)、DB_ROLL_PTR(指向 undo log)、DB_ROW_ID
ReadView：m_ids(活跃事务)、min_trx_id、max_trx_id、creator_trx_id
可见性：trx_id < min_trx_id → 可见；trx_id ≥ max_trx_id → 不可见；
        min_trx_id ≤ trx_id < max_trx_id → 查 m_ids 判断是否活跃
```
> 详见 [[多版本并发控制]]。RC 每次查询生成新 ReadView、RR 事务首次查询生成后复用——这是两者行为差异的根源。

### InnoDB 锁机制

| 锁类型 | 说明 |
|--------|------|
| 记录锁(Record) | 锁单行索引记录 |
| 间隙锁(Gap) | 锁索引间隙，防幻读 |
| 临键锁(Next-Key) | 记录锁 + 间隙锁（RR 默认加锁单位） |
| 意向锁(IS/IX) | 表级，标记行锁意向，加速表锁判断 |
| 共享锁(S) / 排他锁(X) | `LOCK IN SHARE MODE` / `FOR UPDATE` |

### 慢查询优化

```sql
SET GLOBAL slow_query_log = ON;         -- 开启慢查询日志
SET GLOBAL long_query_time = 1;         -- 超过 1s 记录
EXPLAIN SELECT * FROM orders WHERE user_id = 123;
-- 关注：type(ALL 全表→index→range→ref→const)、key(实际用的索引)、
--       rows(预估扫描行)、Extra(Using filesort/temporary 需优化)
```

## 应用场景

- OLTP 业务系统的主流关系型数据库；配合索引优化、读写分离（见 [[读写分离]]）、分库分表（见 [[分库分表]]）支撑高并发。

## 优点与局限

- 优点：成熟稳定、生态完善、InnoDB 支持事务与行锁、性能够用且调优空间大。
- 局限：单机写扩展有限（需分库分表）；大表 DDL、深分页、热点行锁等需专门优化。

## 常见误区

- 「REPEATABLE READ 完全不防幻读」：InnoDB 通过 MVCC（快照读）+ 间隙锁（当前读）**基本消除**幻读，但与 SQL 标准定义有差异。
- 「加索引一定快」：索引占空间、拖慢写入；选择性低的列或失效场景（列上用函数、隐式类型转换、前导模糊 `LIKE '%x'`）用不上索引。
- 以为二级索引查询无需回表：非覆盖索引需回表，可用覆盖索引避免。

## 相关术语

[[MySQL从入门到架构师]]、[[B+树]]、[[索引与查询优化术语]]、[[事务隔离级别]]、[[多版本并发控制]]、[[事务与并发控制术语]]、[[分库分表]]、[[读写分离]]

## 参考资料

建议人工核验：可参考 MySQL 官方文档（InnoDB 存储引擎、EXPLAIN、事务与锁）、《高性能 MySQL》、《MySQL 技术内幕：InnoDB 存储引擎》。
