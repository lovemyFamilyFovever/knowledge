---
title: "PostgreSQL高级特性"
tags: [数据库, PostgreSQL, SQL, 关系型数据库]
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# PostgreSQL高级特性


> 📌 **导航**：本文是 **PostgreSQL高级特性** 词条，属于 database 术语集。相关枢纽：[[MySQL从入门到架构师]]、[[MySQL深入]]、[[Redis深入]]、[[Redis深度解析与实战指南]]、[[SQL 基础术语]]。

## 定义

**一句话定义：** PostgreSQL（PG）是功能强大的开源**对象-关系型数据库**，以标准兼容、可扩展与丰富的高级特性（JSONB、窗口函数、CTE、全文搜索、GIS、自定义类型等）著称。

**通俗类比：** 若说 MySQL 是「家用轿车」（轻快、够用），PostgreSQL 更像「工程车」——功能全、扩展强、严谨，适合复杂查询与「一库多模」的场景。

> 多义说明：本文汇总 PG 的**高级特性**；SQL 通用语法见 [[SQL 基础术语]]，索引与查询优化见 [[索引与查询优化术语]]。

## 原理与机制

- **MVCC 并发**：PG 用多版本并发控制实现读写不互相阻塞，旧版本由 VACUUM 回收（见 [[多版本并发控制]]）。
- **可扩展架构**：支持自定义数据类型、函数、操作符与扩展（如 PostGIS 地理、pg_trgm 模糊匹配）。
- **丰富索引**：除 B-tree 外，还有 GIN、GiST、BRIN、Hash、SP-GiST，适配 JSONB、全文、地理、时序等。

## 关键特性

### JSONB（二进制 JSON）

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    profile JSONB
);

SELECT profile->>'name' AS name FROM users;              -- ->> 取文本值
SELECT * FROM users WHERE profile @> '{"age": 25}';      -- @> 包含查询
CREATE INDEX idx_profile ON users USING GIN(profile);    -- GIN 索引加速
```
> `json` 原样存文本、`jsonb` 存解析后的二进制（可建索引、查询更快），一般用 **JSONB**。

### 窗口函数（Window Functions）

```sql
-- 排名
SELECT name, score, RANK() OVER (ORDER BY score DESC) AS rank FROM students;
-- 分组内排名
SELECT name, department, salary,
       ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank
FROM employees;
-- 累计求和
SELECT date, amount, SUM(amount) OVER (ORDER BY date) AS running_total FROM transactions;
```

### CTE（公共表表达式）与递归查询

```sql
WITH active_users AS (
    SELECT user_id, COUNT(*) AS order_count
    FROM orders
    WHERE created_at > NOW() - INTERVAL '30 days'
    GROUP BY user_id
)
SELECT u.name, a.order_count
FROM users u JOIN active_users a ON u.id = a.user_id;
-- 还支持 WITH RECURSIVE 做树/图的递归遍历
```

### 全文搜索

```sql
ALTER TABLE articles ADD COLUMN tsv tsvector;
UPDATE articles SET tsv = to_tsvector('english', title || ' ' || content);
CREATE INDEX idx_tsv ON articles USING GIN(tsv);
SELECT * FROM articles WHERE tsv @@ to_tsquery('english', 'machine & learning');
```
> 修正：原文示例用 `to_tsvector('chinese', ...)`，但 **PG 并不内置 `chinese` 分词配置**，中文全文检索需安装扩展（如 zhparser、pg_jieba）；此处改用内置的 `'english'` 作通用示例。

## 应用场景

- 复杂查询与分析、需要「一库多模」（关系 + JSON + 地理 + 全文）、数据完整性与标准兼容要求高的场景（金融、GIS、SaaS）。

## 优点与局限

- 优点：功能全面、标准兼容、扩展性强、复杂查询与并发（MVCC）表现好、开源无商业授权限制。
- 局限：连接为「每连接一进程」，高并发短连接需配连接池（如 PgBouncer）；VACUUM/表膨胀需运维关注；简单读多场景下资源占用可能高于 MySQL。

## 常见误区

- `json` 与 `jsonb` 不分：需要索引/高效查询应用 **jsonb**。
- 忽视 VACUUM：PG 的 MVCC 会产生死元组，需 autovacuum 回收，否则表膨胀、甚至 XID 回卷风险。
- 以为中文全文搜索开箱即用：需装分词扩展（zhparser/pg_jieba）。

## 相关术语

[[SQL 基础术语]]、[[索引与查询优化术语]]、[[多版本并发控制]]、[[数据库设计术语]]、[[MySQL深入]]

## 参考资料

建议人工核验：可参考 PostgreSQL 官方文档（JSON Types、Window Functions、WITH/CTE、Full Text Search、Index Types）与《PostgreSQL 修炼之道》。
