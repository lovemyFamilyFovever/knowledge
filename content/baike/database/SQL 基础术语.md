---
title: "SQL 基础术语"
tags: []
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# SQL 基础术语

---

## DDL（Data Definition Language，数据定义语言）

**一句话定义（大白话）：** 用来创建、修改、删除数据库和表结构的 SQL 命令，相当于"装修房子时拆墙、砌墙"。

**通俗类比（生活场景）：** 你搬进新房子，需要先打隔断（CREATE TABLE）、拆掉多余的墙（DROP TABLE）、在墙上开个门洞（ALTER TABLE ADD COLUMN）。DDL 就是干这些"结构性改造"的。

**具体示例：**

```sql
-- 创建数据库
CREATE DATABASE my_shop;

-- 创建表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 修改表结构：加字段
ALTER TABLE users ADD phone VARCHAR(20);

-- 修改字段类型
ALTER TABLE users MODIFY phone VARCHAR(30);

-- 删除表
DROP TABLE users;

-- 删除数据库
DROP DATABASE my_shop;
```

**为什么需要它：** 没有 DDL，你就没法告诉数据库"我要存什么数据、数据长什么样"。DDL 是所有数据操作的地基。

**与相关术语的对比和区分：** DDL 管的是"结构"（表、库、索引），DML 管的是"数据"（增删改查记录）。DDL 改的是骨架，DML 改的是血肉。

---

## DML（Data Manipulation Language，数据操作语言）

**一句话定义（大白话）：** 对表里的数据进行增、删、改操作的 SQL 命令。

**通俗类比（生活场景）：** 书架（表结构）已经搭好了，DML 就是往书架上放书（INSERT）、把书拿走（DELETE）、换一本新的（UPDATE）。

**具体示例：**

```sql
-- 插入数据
INSERT INTO users (username, email) VALUES ('张三', 'zhangsan@example.com');

-- 批量插入
INSERT INTO users (username, email) VALUES
    ('李四', 'lisi@example.com'),
    ('王五', 'wangwu@example.com');

-- 更新数据
UPDATE users SET email = 'zhangsan_new@example.com' WHERE id = 1;

-- 删除数据
DELETE FROM users WHERE id = 2;

-- 删除所有数据（不推荐，保留表结构）
DELETE FROM users;
```

**为什么需要它：** 数据库光有结构没用，得往里塞数据、改数据、删数据，DML 就是干这个的。它是日常开发中用得最多的 SQL 类型。

**与相关术语的对比和区分：** DML 操作的是表中的**行（记录）**，DDL 操作的是表的**结构**。INSERT/UPDATE/DELETE 是 DML，CREATE/ALTER/DROP 是 DDL。

---

## DCL（Data Control Language，数据控制语言）

**一句话定义（大白话）：** 管理数据库用户权限的 SQL 命令，决定"谁能访问什么、能做什么"。

**通俗类比（生活场景）：** 公司门禁系统——管理员（DBA）给员工发门禁卡（GRANT），员工离职就注销卡（REVOKE），不同级别的人能进不同的房间。

**具体示例：**

```sql
-- 创建用户
CREATE USER 'dev_user'@'localhost' IDENTIFIED BY 'password123';

-- 授予权限：只允许查询 my_shop 库
GRANT SELECT ON my_shop.* TO 'dev_user'@'localhost';

-- 授予全部权限
GRANT ALL PRIVILEGES ON my_shop.* TO 'dev_user'@'localhost';

-- 撤销权限
REVOKE DELETE ON my_shop.* FROM 'dev_user'@'localhost';

-- 查看权限
SHOW GRANTS FOR 'dev_user'@'localhost';

-- 删除用户
DROP USER 'dev_user'@'localhost';
```

**为什么需要它：** 生产环境不可能让所有人都有 root 权限。DCL 让 DBA 能精确控制每个用户能干什么，防止误操作和数据泄露。

**与相关术语的对比和区分：** DCL 管"人"（用户和权限），DDL 管"结构"，DML 管"数据"。三者职责完全不同。

---

## DQL（Data Query Language，数据查询语言）

**一句话定义（大白话）：** 从数据库里查数据的 SQL 命令，核心就是 SELECT。

**通俗类比（生活场景）：** 你去图书馆找书——告诉管理员"我要找所有科幻类的书"（SELECT），管理员帮你翻目录找出来。

**具体示例：**

```sql
-- 基础查询
SELECT * FROM users;

-- 条件查询
SELECT username, email FROM users WHERE id > 10;

-- 排序 + 分页
SELECT * FROM users ORDER BY created_at DESC LIMIT 10 OFFSET 20;

-- 聚合查询
SELECT COUNT(*) AS total_users FROM users;

-- 多条件组合
SELECT username, email
FROM users
WHERE email LIKE '%@example.com'
  AND created_at >= '2025-01-01'
ORDER BY username;
```

**为什么需要它：** 存数据的目的是用数据，DQL 是把数据"拿出来"的手段。90% 的数据库操作都是查询。

**与相关术语的对比和区分：** DQL 只管"读"（SELECT），DML 管"写"（INSERT/UPDATE/DELETE）。有些分类把 DQL 归入 DML，但严格来说它们职责不同。

---

## TCL（Transaction Control Language，事务控制语言）

**一句话定义（大白话）：** 管理事务提交和回滚的 SQL 命令，保证一组操作"要么全做，要么全不做"。

**通俗类比（生活场景）：** 转账操作——从 A 账户扣钱和给 B 账户加钱必须同时成功。如果中途出错，就得全部撤销（ROLLBACK），不能钱扣了但对方没收到。

**具体示例：**

```sql
-- 开启事务
START TRANSACTION;

-- 或者用 BEGIN
BEGIN;

-- 执行一系列操作
UPDATE accounts SET balance = balance - 100 WHERE user_id = 1;
UPDATE accounts SET balance = balance + 100 WHERE user_id = 2;

-- 确认无误，提交
COMMIT;

-- 如果出错了，回滚
-- ROLLBACK;

-- 设置保存点（可以部分回滚）
SAVEPOINT sp1;
DELETE FROM temp_data;
ROLLBACK TO sp1;  -- 只回滚到保存点
```

**为什么需要它：** 没有事务，转账时扣钱成功但加钱失败就会导致数据不一致。TCL 保证数据操作的原子性和一致性。

**与相关术语的对比和区分：** TCL 管的是"事务边界"（提交/回滚），DML 管的是"具体操作"（增删改）。TCL 是 DML 操作的安全网。

---

## SELECT 语句完整流程

**一句话定义（大白话）：** 一条 SELECT 语句从写下到返回结果，内部执行的完整步骤链。

**通俗类比（生活场景）：** 你去餐厅点菜——先看菜单（FROM 找表）→ 选菜系（WHERE 过滤）→ 选具体菜（SELECT 列）→ 摆盘（ORDER BY 排序）→ 上几道（LIMIT 分页）。

**具体示例：**

```sql
-- 执行顺序演示
SELECT
    department,
    COUNT(*) AS emp_count,          -- 第6步：在 SELECT 阶段计算聚合
    AVG(salary) AS avg_salary
FROM employees                       -- 第1步：确定数据来源
WHERE hire_date >= '2024-01-01'      -- 第2步：过滤行
GROUP BY department                   -- 第3步：分组
HAVING COUNT(*) > 5                  -- 第4步：过滤分组
ORDER BY avg_salary DESC             -- 第6步：排序
LIMIT 10;                            -- 第7步：限制返回数量
```

**执行顺序：**
1. **FROM** → 确定从哪个表取数据
2. **JOIN** → 连接其他表
3. **WHERE** → 过滤行
4. **GROUP BY** → 分组
5. **HAVING** → 过滤分组
6. **SELECT** → 选择要返回的列
7. **DISTINCT** → 去重
8. **ORDER BY** → 排序
9. **LIMIT** → 限制返回条数

**为什么需要它：** 理解执行顺序是写对复杂 SQL 的前提。很多人写不出正确的 GROUP BY，就是因为不清楚执行顺序。

**与相关术语的对比和区分：** 这不是一种 SQL 类型，而是 SELECT 语句的**执行机制**。它解释了为什么 WHERE 里不能用聚合函数（因为聚合在后面才执行）。

---

## JOIN（INNER/LEFT/RIGHT/FULL）

**一句话定义（大白话）：** 把两张或多张表按照某个关联条件"拼"在一起查询。

**通俗类比（生活场景）：** 你有一份学生名单和一份成绩单，想"按学号把两个表拼起来"看每个学生的成绩——这就是 JOIN。

**具体示例：**

```sql
-- 假设有 users 表和 orders 表
-- users: id, username
-- orders: id, user_id, amount

-- INNER JOIN：只取两边都有匹配的行
SELECT u.username, o.amount
FROM users u
INNER JOIN orders o ON u.id = o.user_id;
-- 结果：只有下过单的用户

-- LEFT JOIN：保留左边全部，右边没有的用 NULL 填
SELECT u.username, o.amount
FROM users u
LEFT JOIN orders o ON u.id = o.user_id;
-- 结果：所有用户，没下过单的显示 NULL

-- RIGHT JOIN：保留右边全部
SELECT u.username, o.amount
FROM users u
RIGHT JOIN orders o ON u.id = o.user_id;
-- 结果：所有订单，没关联用户的不显示

-- FULL OUTER JOIN：两边都保留（MySQL 不直接支持，用 UNION 模拟）
SELECT u.username, o.amount
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
UNION
SELECT u.username, o.amount
FROM users u
RIGHT JOIN orders o ON u.id = o.user_id;
```

**为什么需要它：** 数据库是分散存储的，用户信息在一张表，订单在另一张表。JOIN 让你能在一次查询中同时获取多张表的数据。

**与相关术语的对比和区分：** INNER JOIN 取交集，LEFT JOIN 取左表全集 + 右表匹配，RIGHT JOIN 反之，FULL JOIN 取并集。选哪个取决于你要保留哪些数据。

---

## 子查询（Subquery）

**一句话定义（大白话）：** 把一个 SELECT 查询嵌套在另一个查询里面，先执行内层，再用结果执行外层。

**通俗类比（生活场景）：** 你想找"成绩比全班平均分高的学生"——先算出平均分（内层查询），再拿这个分数去筛选学生（外层查询）。

**具体示例：**

```sql
-- WHERE 子句中的子查询
SELECT username, salary
FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);

-- IN 子查询：找出下过单的用户
SELECT username
FROM users
WHERE id IN (SELECT DISTINCT user_id FROM orders);

-- FROM 子查询（派生表）
SELECT dept, avg_sal
FROM (
    SELECT department AS dept, AVG(salary) AS avg_sal
    FROM employees
    GROUP BY department
) AS dept_stats
WHERE avg_sal > 10000;

-- EXISTS 子查询（通常更快）
SELECT u.username
FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id
);
```

**为什么需要它：** 很多查询需要"先查一个结果，再用这个结果去查"。子查询让你能在一条 SQL 里完成多步逻辑。

**与相关术语的对比和区分：** 子查询是嵌套查询，JOIN 是平铺连接。子查询可读性好但性能不一定优，JOIN 性能通常更好但写法更复杂。实际中根据场景选择。

---

## UNION

**一句话定义（大白话）：** 把两个或多个 SELECT 的结果**纵向合并**成一个结果集。

**通俗类比（生活场景）：** 你从 A 班花名册和 B 班花名册各抄了一份名单，现在把两份名单合在一起变成一份完整名单。

**具体示例：**

```sql
-- UNION：自动去重
SELECT username FROM users_vip
UNION
SELECT username FROM users_normal;

-- UNION ALL：保留重复（性能更好）
SELECT username FROM users_vip
UNION ALL
SELECT username FROM users_normal;

-- 实际场景：按条件分组统计
SELECT
    '高收入' AS category,
    COUNT(*) AS count
FROM employees WHERE salary > 20000
UNION ALL
SELECT
    '中等收入' AS category,
    COUNT(*) AS count
FROM employees WHERE salary BETWEEN 10000 AND 20000
UNION ALL
SELECT
    '低收入' AS category,
    COUNT(*) AS count
FROM employees WHERE salary < 10000;
```

**为什么需要它：** 当你需要把多个查询结果合并到一起展示时，UNION 是最直接的方式。比如合并不同条件下的统计结果。

**与相关术语的对比和区分：** UNION 是纵向合并（行增加），JOIN 是横向合并（列增加）。UNION 合并的是行，JOIN 拼接的是列。

---

## GROUP BY 与 HAVING

**一句话定义（大白话）：** GROUP BY 把数据按某列分组，HAVING 对分组后的结果再过滤。

**通俗类比（生活场景）：** 学校按班级（GROUP BY class）统计每个班的平均分，然后只保留平均分 > 85 的班级（HAVING avg_score > 85）。

**具体示例：**

```sql
-- 按部门统计人数和平均薪资
SELECT
    department,
    COUNT(*) AS emp_count,
    AVG(salary) AS avg_salary
FROM employees
GROUP BY department;

-- HAVING 过滤分组结果
SELECT
    department,
    AVG(salary) AS avg_salary
FROM employees
GROUP BY department
HAVING AVG(salary) > 15000;

-- WHERE + GROUP BY + HAVING 组合
SELECT
    department,
    COUNT(*) AS senior_count
FROM employees
WHERE hire_date < '2023-01-01'   -- 先过滤行
GROUP BY department                -- 再分组
HAVING COUNT(*) > 3;              -- 最后过滤分组
```

**为什么需要它：** 聚合统计是数据分析的核心需求。GROUP BY 让你能按维度（部门、月份、地区等）做汇总，HAVING 让你能对汇总结果做筛选。

**与相关术语的对比和区分：** WHERE 在分组前过滤行，HAVING 在分组后过滤组。WHERE 不能用聚合函数（COUNT、AVG 等），HAVING 可以。

---

## 窗口函数（Window Function）

**一句话定义（大白话）：** 在不合并行的前提下，对"一组行"做计算，同时保留每一行的细节。

**通俗类比（生活场景）：** 班级排名——你知道每个同学的分数、排名、以及班级平均分。窗口函数就是"在不把同学合成一行的情况下，同时看到每个人的分数和排名"。

**具体示例：**

```sql
-- 排名：RANK() 有并列会跳号，DENSE_RANK() 不跳号
SELECT
    username,
    salary,
    RANK() OVER (ORDER BY salary DESC) AS rank_num,
    DENSE_RANK() OVER (ORDER BY salary DESC) AS dense_rank_num,
    ROW_NUMBER() OVER (ORDER BY salary DESC) AS row_num
FROM employees;

-- 分组排名：每个部门内部按薪资排名
SELECT
    username,
    department,
    salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank
FROM employees;

-- 累计求和
SELECT
    order_date,
    amount,
    SUM(amount) OVER (ORDER BY order_date) AS running_total
FROM orders;

-- 移动平均
SELECT
    order_date,
    amount,
    AVG(amount) OVER (ORDER BY order_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS moving_avg
FROM orders;
```

**为什么需要它：** 普通 GROUP BY 会把行合并，丢失细节。窗口函数让你既能做聚合计算，又能保留每行数据，非常适合排名、累计、滑动计算等场景。

**与相关术语的对比和区分：** 聚合函数（GROUP BY）压缩行数，窗口函数保留行数。窗口函数 over 后面的括号定义了"窗口范围"。

---

## CTE（WITH 语句，公用表表达式）

**一句话定义（大白话）：** 给子查询起个名字，让 SQL 更易读、可复用，就像定义一个"临时变量"。

**通俗类比（生活场景）：** 写论文时，你先在草稿纸算出一个中间结论（CTE），然后在正文里直接引用这个结论，而不是每次都重新算一遍。

**具体示例：**

```sql
-- 基础 CTE：先算出各部门平均薪资，再筛选
WITH dept_stats AS (
    SELECT
        department,
        AVG(salary) AS avg_salary,
        COUNT(*) AS emp_count
    FROM employees
    GROUP BY department
)
SELECT *
FROM dept_stats
WHERE avg_salary > 15000;

-- 多个 CTE 链式引用
WITH
active_users AS (
    SELECT * FROM users WHERE status = 'active'
),
recent_orders AS (
    SELECT * FROM orders WHERE order_date >= '2025-01-01'
)
SELECT
    u.username,
    COUNT(o.id) AS order_count
FROM active_users u
LEFT JOIN recent_orders o ON u.id = o.user_id
GROUP BY u.username;

-- 递归 CTE：查询组织架构树
WITH RECURSIVE org_tree AS (
    -- 锚点：顶级领导
    SELECT id, name, manager_id, 1 AS level
    FROM employees
    WHERE manager_id IS NULL

    UNION ALL

    -- 递归：下属
    SELECT e.id, e.name, e.manager_id, t.level + 1
    FROM employees e
    INNER JOIN org_tree t ON e.manager_id = t.id
)
SELECT * FROM org_tree ORDER BY level;
```

**为什么需要它：** 原生子查询嵌套多了可读性极差。CTE 让复杂 SQL 变成"分步定义、逐步引用"，像写文章一样清晰。递归 CTE 还能处理树形结构数据。

**与相关术语的对比和区分：** CTE 是"命名子查询"，只在当前语句中有效。它和派生表（FROM 子查询）功能类似，但 CTE 可以被多次引用，可读性也更好。

## 相关术语

[[事务与并发控制术语]]、[[索引与查询优化术语]]、[[数据库设计术语]]、[[NoSQL 数据库术语]]

## 参考资料

建议人工核验：可参考 ANSI SQL 标准（SQL:2016）及各数据库官方文档（MySQL / PostgreSQL / SQL Server），以及《SQL 必知必会》(Ben Forta)、*Database System Concepts* (Silberschatz 等)。
