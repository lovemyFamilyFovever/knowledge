---
title: "Redis深入"
tags: []
source: "baike"
source_path: "开发术语 / 数据库"
collected: "2026-09-05"
status: "imported"
---

# Redis深入

## 数据结构

| 类型 | 底层实现 | 用途 |
|------|----------|------|
| String | SDS | 缓存、计数器 |
| List | quicklist | 消息队列 |
| Hash | ziplist/hashtable | 对象存储 |
| Set | intset/hashtable | 去重、交并差 |
| ZSet | ziplist/skiplist | 排行榜 |
| Stream | radix tree | 消息队列(持久化) |

## 持久化

| 方式 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| RDB | 定时快照 | 恢复快 | 可能丢数据 |
| AOF | 追加写命令 | 数据安全 | 文件大、恢复慢 |

## 集群模式

| 模式 | 特点 |
|------|------|
| 主从复制 | 读写分离 |
| 哨兵Sentinel | 自动故障转移 |
| Cluster | 数据分片(16384个slot) |

## Lua脚本

```lua
-- 原子操作：限流
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
if current > tonumber(ARGV[2]) then
    return 0
end
return 1
```

## Stream消息队列

```bash
# 生产者
XADD mystream * name "hello" value "world"

# 消费者组
XGROUP CREATE mystream mygroup $
XREADGROUP GROUP mygroup consumer1 COUNT 1 BLOCK 0 STREAMS mystream >
```
