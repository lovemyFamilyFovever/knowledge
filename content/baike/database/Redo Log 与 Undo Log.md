---
title: "Redo Log 与 Undo Log"
tags: []
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# Redo Log 与 Undo Log

> 📌 **导航**：本文是 **Redo Log 与 Undo Log** 词条，属于 database 术语集。相关枢纽：[[事务与并发控制术语]]、[[InnoDB 存储引擎结构]]、[[事务与 ACID]]、[[多版本并发控制]]、[[LSM 树]]。

## 定义

**一句话定义：** Redo Log 记录"对数据页做了什么物理修改"用于崩溃后重做、保证已提交事务不丢（持久性）；Undo Log 记录"修改前的旧值"用于回滚与构建 MVCC 历史版本（原子性/隔离）；两者一正一反，支撑事务的可靠与并发。

**通俗类比：** 装修施工：Undo Log 像"动工前给原状拍的照片"，砸错了能照照片恢复原样；Redo Log 像"已干的活逐笔记进施工日志"，哪怕工地断电，照日志能把已做的砖重新砌齐，不会白干。

## 为什么需要它

数据页真正写盘是随机 I/O、慢，且事务不能等全部落盘才返回。靠 WAL（先写顺序日志再改数据页），Redo Log 让"提交"只需日志落盘即可、崩溃后重放恢复，兼得性能与持久性。而回滚不能凭空还原——Undo Log 存旧值，既服务 ROLLBACK，又给 [[多版本并发控制]] 提供版本链，让快照读看到"过去某时刻的值"。

## 核心机制

- **Redo Log：** InnoDB 物理、循环写日志组；采用 WAL——先写 Redo 再改 Buffer Pool 脏页；`innodb_flush_log_at_trx_commit=1` 每次提交刷盘最安全。崩溃后按 redo 重做到"已提交"状态。
- **Undo Log：** 每行改动记旧版本，形成版本链（由行的回滚指针 DB_ROLL_PTR 串联），供回滚回退，也供 MVCC ReadView 判定可见版本；事务无人需要后再 purge 清理。
- **Binlog（对照）：** Server 层逻辑日志（归档/复制），与引擎层 Redo 通过两阶段提交保持一致（见 [[InnoDB 存储引擎结构]]）。

## 具体示例

一个 UPDATE 把余额 500 改成 800：先在 Undo 记旧值 500（回滚/别的快照读要用），再把新值写入 Buffer Pool 脏页并追加 Redo。提交时按 `flush_log_at_trx_commit` 决定 Redo 是否立即 fsync。若此刻宕机，数据页可能还没落盘，重启用 Redo 把 800 重做回来（不丢）；若事务未提交就崩溃，则用 Undo 把 500 还原（不脏）。

## 何时用 / 何时不用

- **用：** 理解持久性/回滚/MVCC 与调参——设 `trx_commit=1` 换安全、`=2` 折中吞吐；关心崩溃恢复、长事务为何拖大 undo 时。
- **注意：** 长事务使 Undo 无法回收、回滚段膨胀；关闭或放宽 Redo 刷盘会增大崩溃丢数据窗口，非可随意。

## 优劣与代价

✅ WAL 让顺序写换随机写、提交可不等数据页落盘；Undo 同时支撑回滚与一致性快照。
⚠️ 日志带来额外写与空间；`trx_commit` 三档是"性能 vs 丢数据窗口"的取舍。
⚠️ 长事务/大事务会让 undo 膨胀、purge 压力升高。

## 与相关概念的区别

- **Redo vs Undo：** Redo 面向"已做的向前恢复（别丢）"、Undo 面向"撤销旧值与历史版本（别脏/可读旧）"。
- **vs Binlog：** Binlog 是 Server 层逻辑日志、用于复制/时间点恢复；Redo 是 InnoDB 物理日志、用于崩溃恢复。
- **WAL vs [[LSM 树]] 的 WAL：** 都"先写日志"，LSM 用 WAL + 内存表 + 合并换写吞吐，InnoDB 用 Redo 保证原地更新的崩溃一致性。

## 常见误区

- Redo Log 和 Binlog 是同一个东西，留一个就行。
- 把 innodb_flush_log_at_trx_commit 设成 0 或 2，崩溃时也绝不会丢数据。
- Undo Log 只用于事务回滚，与并发下的快照读无关。

## 面试速答

> 🎯 Redo Log：InnoDB 物理循环日志，WAL 先写日志再改脏页、崩溃后重做保已提交不丢(持久性)，trx_commit 控刷盘换安全/性能；Undo Log：存旧值成版本链，供 ROLLBACK(原子性)与 MVCC 快照读，长事务令其膨胀。区别 Server 层 Binlog(复制/归档)。

## 相关术语

[[事务与并发控制术语]]、[[InnoDB 存储引擎结构]]、[[事务与 ACID]]、[[多版本并发控制]]、[[LSM 树]]

## 参考资料

建议人工核验：可参考 MySQL 官方文档（InnoDB Redo/Undo、flush_log_at_trx_commit）与《MySQL 技术内幕：InnoDB 存储引擎》(姜承尧)。
