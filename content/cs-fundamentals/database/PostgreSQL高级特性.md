---
title: "PostgreSQL高级特性"
tags: []
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# PostgreSQL高级特性

## JSONB

```sql
-- 创建JSONB列
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    profile JSONB
);

-- 查询JSONB
SELECT profile->>'name' as name FROM users;
SELECT * FROM users WHERE profile @> '{"age": 25}';

-- GIN索引加速JSONB查询
CREATE INDEX idx_profile ON users USING GIN(profile);
```

## 窗口函数

```sql
-- 排名
SELECT name, score, RANK() OVER (ORDER BY score DESC) as rank FROM students;

-- 分组排名
SELECT name, department, salary,
       ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as dept_rank
FROM employees;

-- 累计求和
SELECT date, amount, SUM(amount) OVER (ORDER BY date) as running_total
FROM transactions;
```

## CTE（公共表表达式）

```sql
WITH active_users AS (
    SELECT user_id, COUNT(*) as order_count
    FROM orders
    WHERE created_at > NOW() - INTERVAL '30 days'
    GROUP BY user_id
)
SELECT u.name, a.order_count
FROM users u JOIN active_users a ON u.id = a.user_id;
```

## 全文搜索

```sql
-- tsvector + tsquery
ALTER TABLE articles ADD COLUMN tsv tsvector;
UPDATE articles SET tsv = to_tsvector('chinese', title || ' ' || content);
CREATE INDEX idx_tsv ON articles USING GIN(tsv);

SELECT * FROM articles WHERE tsv @@ to_tsquery('chinese', '机器 & 学习');
```
