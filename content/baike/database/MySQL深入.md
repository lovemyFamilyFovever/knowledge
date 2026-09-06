---
title: "MySQL深入"
tags: []
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# MySQL深入

## 索引原理（B+树）

```
       [10 | 20 | 30]
      /    |    |    \
 [1,5,8] [12,15] [22,25] [31,35]
     <->    <->    <->    <->  (叶子链表)
```

- 非叶子节点只存索引，叶子节点存数据
- 叶子节点双向链表，范围查询高效
- 一棵3层B+树约可存2000万行数据

## 事务隔离级别

| 级别 | 脏读 | 不可重复读 | 幻读 | 性能 |
|------|------|-----------|------|------|
| READ UNCOMMITTED | 有 | 有 | 有 | 最高 |
| READ COMMITTED | 无 | 有 | 有 | 高 |
| REPEATABLE READ(默认) | 无 | 无 | 有(InnoDB无) | 中 |
| SERIALIZABLE | 无 | 无 | 无 | 最低 |

## MVCC（多版本并发控制）

```
每行数据有隐藏列:
- DB_TRX_ID: 最后修改的事务ID
- DB_ROLL_PTR: 指向undo log的回滚指针
- DB_ROW_ID: 自增行ID

ReadView:
- m_ids: 活跃事务列表
- min_trx_id: 最小活跃事务ID
- max_trx_id: 下一个分配的事务ID
- creator_trx_id: 创建者事务ID

可见性判断：
trx_id < min_trx_id -> 可见(事务已提交)
trx_id >= max_trx_id -> 不可见(事务在快照后开始)
min_trx_id <= trx_id < max_trx_id -> 查m_ids
```

## InnoDB锁机制

| 锁类型 | 说明 |
|--------|------|
| 行锁 | 记录锁(Record Lock)、间隙锁(Gap Lock)、临键锁(Next-Key Lock) |
| 表锁 | 意向锁(IS/IX) |
| 共享锁(S) | SELECT ... LOCK IN SHARE MODE |
| 排他锁(X) | SELECT ... FOR UPDATE |

## 慢查询优化

```sql
-- 1. 开启慢查询日志
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 1;

-- 2. EXPLAIN分析
EXPLAIN SELECT * FROM orders WHERE user_id = 123;

-- 关注的字段：
-- type: ALL(全表扫描) -> index -> range -> ref -> const
-- key: 使用的索引
-- rows: 预估扫描行数
-- Extra: Using filesort / Using temporary (需要优化)
```
