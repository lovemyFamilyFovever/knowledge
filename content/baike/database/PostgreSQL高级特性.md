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

**通俗类比：** 若说 MySQL 是"家用轿车"（轻快、够用），PostgreSQL 更像"工程车"——功能全、扩展强、严谨，适合复杂查询与"一库多模"的场景。

> 多义说明：本文汇总 PG 的**高级特性**；SQL 通用语法见 [[SQL 基础术语]]，索引与查询优化见 [[索引与查询优化术语]]。

## 为什么需要它

很多"关系型 + NoSQL"混合需求，其实一个 PG 就能扛：既要事务与强约束，又要半结构化 JSON、地理空间、全文检索、复杂分析查询。PG 用统一引擎和可扩展架构覆盖这些"一库多模"诉求，省去多套存储同步的复杂度，同时严格遵循 SQL 标准、支持复杂查询优化器，适合金融、GIS、SaaS 等对完整性要求高的系统。

## 核心机制

- **MVCC 并发：** PG 用多版本并发控制让读写不互相阻塞，旧版本由 VACUUM 回收（见 [[多版本并发控制]]）。
- **可扩展架构：** 支持自定义数据类型、函数、操作符与扩展（如 PostGIS 地理、pg_trgm 模糊匹配）。
- **丰富索引：** 除 B-tree 外还有 GIN、GiST、BRIN、Hash、SP-GiST，适配 JSONB、全文、地理、时序等；GIN 让 JSONB 与全文检索可被高效索引。
- **JSONB：** 存解析后的二进制（可建 GIN 索引、`@>` 包含查询），一般优于原样存文本的 `json`。
- **CTE 与递归：** `WITH` 抽子查询、`WITH RECURSIVE` 做树/图递归遍历。
- **全文搜索：** `to_tsvector`/`tsquery` + GIN 索引实现词组检索。注意 PG **不内置 `chinese` 分词配置**，中文全文需装扩展（zhparser、pg_jieba）。

## 具体示例

JSONB 的取值、包含查询与 GIN 索引：

```sql
SELECT profile->>'name' AS name FROM users;          -- ->> 取文本值
SELECT * FROM users WHERE profile @> '{"age": 25}';  -- @> 包含查询
CREATE INDEX ON users USING GIN(profile);            -- GIN 加速 JSONB
```

窗口函数在不出组的前提下做排名、组内排名与累计：

```sql
SELECT name, score, RANK() OVER (ORDER BY score DESC) AS rank FROM students;
SELECT name, salary,
       ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC) AS r FROM emp;
SELECT date, SUM(amount) OVER (ORDER BY date) AS running_total FROM tx;
```

## 何时用 / 何时不用

- **用：** 复杂查询与分析、需要"一库多模"（关系 + JSON + 地理 + 全文）、数据完整性与标准兼容要求高的场景（金融、GIS、SaaS）。
- **不用：** 极致简单的读多写少缓存/点查（用 Redis）；团队生态与工具链完全绑定 MySQL 且无高级特性需求时，迁移收益有限。

## 优劣与代价

✅ 功能全面、标准兼容、扩展性强，复杂查询与 MVCC 并发表现好，开源无授权限制。
⚠️ 连接为"每连接一进程"，高并发短连接需配连接池（如 PgBouncer）。
⚠️ MVCC 产生死元组，VACUUM/表膨胀需运维关注；简单场景资源占用可能高于 MySQL。

## 与相关概念的区别

- **vs MySQL：** PG 偏"全能工程车"（GIN/JSONB/窗口/CTE/GIS、扩展与类型系统更强），MySQL 偏"轻快家用轿车"（生态成熟、读多场景资源更省）。
- **vs 专门的 NoSQL：** PG 用关系模型 + JSONB/GIN 兼顾半结构化，不必为"能存 JSON"再上一套文档库。

## 常见误区

- PostgreSQL 里 json 和 jsonb 没有区别，用哪个都行。
- 用了 PG 就不用管 VACUUM，死元组会自动清掉。
- PostgreSQL 内置中文分词，中文全文检索开箱即用。

## 面试速答

> 🎯 PG=开源对象-关系库，靠 MVCC+VACUUM 做无锁读写、GIN/GiST/BRIN 等多索引支撑 JSONB/全文/GIS，加窗口函数、CTE 与可扩展类型系统实现"一库多模"；代价是每连接一进程需连接池、死元组需 autovacuum 治理。
> 🔍 追问：jsonb 相比 json 好在哪？
> 🔍 追问：为什么 PG 高并发短连接要上 PgBouncer？
> 🔍 追问：MVCC 留下的死元组不清理会怎样？

## 相关术语

[[SQL 基础术语]]、[[索引与查询优化术语]]、[[多版本并发控制]]、[[数据库设计术语]]、[[MySQL深入]]

## 参考资料

建议人工核验：可参考 PostgreSQL 官方文档（JSON Types、Window Functions、WITH/CTE、Full Text Search、Index Types）与《PostgreSQL 修炼之道》。
