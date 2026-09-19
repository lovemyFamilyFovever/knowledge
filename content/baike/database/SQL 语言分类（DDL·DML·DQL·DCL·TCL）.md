---
title: "SQL 语言分类（DDL·DML·DQL·DCL·TCL）"
tags: []
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# SQL 语言分类（DDL·DML·DQL·DCL·TCL）

> 📌 **导航**：本文是 **SQL 语言分类** 词条，属于 database 术语集。相关枢纽：[[SQL 基础术语]]、[[SQL 查询与连接]]、[[数据库设计术语]]、[[数据库范式]]、[[事务与并发控制术语]]。

## 定义

**一句话定义：** SQL 按用途分五类语言——DDL 定义结构、DML 增删改数据、DQL 查询、DCL 管权限、TCL 控事务边界，共同覆盖"建表→读写→查→授权→提交回滚"的完整操作面。

**通俗类比：** 盖一栋楼：DDL 是砌墙浇筑定户型（建/改/删表结构），DML 是搬进搬出家具（增删改记录），DQL 是"我要找哪间房"（查询），DCL 是发门禁卡决定谁能进（授权），TCL 是"这步做完算数、出事整体撤销"（提交/回滚）。

## 为什么需要它

把 SQL 语句按职责归类，能让"改结构 vs 改数据 vs 管权限 vs 管事务"各归其位，避免概念混淆（例如把 DELETE 当成 DDL、把事务控制当成查询）。分类也对应不同权限与安全面：DDL 通常最敏感、DCL 管访问、TCL 管一致性边界，是数据库权限设计与审计的基础切分。

## 核心机制

| 类别 | 关键字 | 作用对象 | 典型语句 |
|------|--------|----------|----------|
| DDL | CREATE / ALTER / DROP / TRUNCATE | 库、表、索引等结构 | `CREATE TABLE ...` |
| DML | INSERT / UPDATE / DELETE | 表中的行（数据） | `UPDATE t SET ... WHERE ...` |
| DQL | SELECT | 读取数据 | `SELECT ... FROM ... WHERE ...` |
| DCL | GRANT / REVOKE | 用户与权限 | `GRANT SELECT ON db.* TO u` |
| TCL | COMMIT / ROLLBACK / SAVEPOINT | 事务边界 | `BEGIN ... COMMIT` |

- **DDL 会隐式提交**：多数数据库里执行 DDL 会触发自动提交，事务里混 DDL 要小心。
- **TRUNCATE vs DELETE**：TRUNCATE 是 DDL、通常不逐行记日志、快且难回滚；DELETE 是 DML、可带 WHERE、可回滚。
- **DQL 常被单列**：严格看 SELECT 也属数据操作，但因只读、最高频而单列一类。

## 具体示例

建表与放数据分两步：先 `CREATE TABLE orders(...)`（DDL 定结构）→ `INSERT INTO orders VALUES(...)`（DML 写行）→ `SELECT ... WHERE`（DQL 查）→ `GRANT SELECT ON orders TO readonly_role`（DCL 授权）→ 一组改价操作 `BEGIN; UPDATE...; UPDATE...; COMMIT`（TCL 保证两条一起成功，出错则 ROLLBACK）。分类清楚后，权限与审计就能精确到"谁能改结构、谁只能查"。

## 何时用 / 何时不用

- **用：** 做权限最小化（业务账号只给 DML/DQL、不给 DCL/DDL）、评审 SQL 类型以判断是否可回滚、排查"为什么事务里 DDL 直接提交了"。
- **注意：** 生产 DDL 需走变更流程（锁表/在线改表工具）；TRUNCATE/DELETE 语义不同别混用。

## 优劣与代价

✅ 分类清晰职责与安全边界，便于授权、审计与选择可回滚手段。
⚠️ DDL 隐式提交易踩坑；TRUNCATE 不可回滚需慎。
⚠️ 不同 DBMS 归类细节略有差异（如有的把 SELECT 归 DML）。

## 与相关概念的区别

- **DML vs DDL：** DML 改"数据行"、DDL 改"结构"；DELETE（DML 可回滚）vs TRUNCATE（DDL 更快难回滚）。
- **TCL vs DML：** DML 做具体增删改，TCL 圈定这些操作何时整体生效或撤销。
- **vs [[事务与并发控制术语]]：** TCL 是事务语句，隔离/回滚的底层机制在那篇展开。

## 常见误区

- DELETE 和 TRUNCATE 是一回事，都能随时回滚。
- 在事务中执行 DDL 也会随事务一起回滚。
- SELECT 和 UPDATE 都属于 DML，权限上不必区分。

## 面试速答

> 🎯 SQL 五类：DDL 改结构(常隐式提交)、DML 改行(可回滚)、DQL 查询、DCL 授权、TCL 事务。关键：DELETE 可回滚，TRUNCATE 属 DDL、快而难回滚；事务里跑 DDL 会立即提交、不随事务回滚。

## 相关术语

[[SQL 基础术语]]、[[SQL 查询与连接]]、[[数据库设计术语]]、[[数据库范式]]、[[事务与并发控制术语]]

## 参考资料

建议人工核验：可参考 ANSI SQL 标准与各数据库官方文档（DDL/DML/DCL/TCL 归类以 MySQL/PostgreSQL 文档为准）。
