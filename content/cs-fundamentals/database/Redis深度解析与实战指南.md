---
title: "Redis深度解析与实战指南"
tags: []
source: "baike"
source_path: "技术文章 / 数据库与存储"
collected: "2026-09-05"
status: "imported"
---

# Redis深度解析与实战指南

# Redis深度解析与实战指南

## 1) Redis数据结构详解

### 1.1 String（字符串）
**底层实现**：SDS（Simple Dynamic String）
**特点**：二进制安全，可存储任意数据（图片、序列化对象等）

```bash
# 基本操作
SET user:1:name "张三" EX 3600  # 设置带过期时间
GET user:1:name
MSET user:1:age 25 user:1:city "北京"  # 批量设置
INCR article:1:count  # 原子计数器
INCRBY user:1:score 10  # 原子自增
```

**实战场景**：
- 缓存对象：`SET cache:user:1001 "{name:'张三', age:25}"`
- 分布式Session：`SET session:token_abc123 user_data EX 1800`
- 限流计数：`INCR rate_limit:ip:192.168.1.1 EXPIRE rate_limit:ip:192.168.1.1 60`

### 1.2 Hash（哈希表）
**底层实现**：ziplist或hashtable（超过阈值自动转换）
**特点**：适合存储对象，可部分更新

```bash
# 存储用户信息
HSET user:1001 name "张三" age 25 city "北京"
HGET user:1001 name
HGETALL user:1001
HINCRBY user:1001 age 1  # 原子自增字段
HSETNX user:1001 email "zhangsan@example.com"  # 不存在时才设置
```

**实战场景**：
- 购物车：`HSET cart:user_123 product_456 2 product_789 1`
- 配置管理：`HSET config:app theme "dark" language "zh-CN"`
- 对象缓存：比String节省内存，支持部分更新

### 1.3 List（列表）
**底层实现**：quicklist（ziplist + 链表的混合结构）
**特点**：有序、可重复，支持两端操作

```bash
# 消息队列模拟
LPUSH queue:order "order_1001"
LPUSH queue:order "order_1002"
RPOP queue:order  # 消费消息
BRPOP queue:order 30  # 阻塞式弹出，超时30秒

# 最新消息列表
LPUSH timeline:user_123 "post_456"
LTRIM timeline:user_123 0 49  # 保留最新50条
```

**实战场景**：
- 简单消息队列（注意：不支持ACK机制）
- 最新动态列表
- 任务排队系统

### 1.4 Set（集合）
**底层实现**：intset（整数）或hashtable（非整数）
**特点**：无序、唯一，支持集合运算

```bash
# 标签系统
SADD tags:article:1 "redis" "database" "nosql"
SADD tags:article:2 "redis" "python"
SINTER tags:article:1 tags:article:2  # 交集：共同标签
SUNION tags:article:1 tags:article:2  # 并集：所有标签
SDIFF tags:article:1 tags:article:2   # 差集：独有标签

# 好友关系
SADD friends:user_123 user_456 user_789
SISMEMBER friends:user_123 user_456  # 判断是否是好友
SINTER friends:user_123 friends:user_456  # 共同好友
```

**实战场景**：
- 社交网络关系
- 标签系统
- 随机抽奖：`SRANDMEMBER participants 3`（随机抽3个）

### 1.5 ZSet（有序集合）
**底层实现**：ziplist或skiplist + hashtable
**特点**：有序、唯一，每个元素关联score

```bash
# 排行榜
ZADD leaderboard 1500 "player_A" 1200 "player_B" 1800 "player_C"
ZRANGE leaderboard 0 -1 WITHSCORES  # 按分数升序
ZREVRANGE leaderboard 0 9 WITHSCORES  # Top10降序
ZINCRBY leaderboard 50 "player_A"  # 加分
ZRANK leaderboard "player_A"  # 排名（从0开始）

# 延迟队列
ZADD delay_queue 1625097600 "task_1001"  # 执行时间戳作为score
ZRANGEBYSCORE delay_queue 0 current_timestamp  # 获取到期任务
```

**实战场景**：
- 游戏排行榜
- 延迟队列
- 带权重的优先级队列

### 1.6 Stream（流）
**底层实现**：基数树（radix tree）+ 链表
**特点**：类似Kafka的消息日志，支持消费者组

```bash
# 生产消息
XADD mystream * name "张三" action "login"
XADD mystream * name "李四" action "purchase" amount 99.9

# 消费消息
XREAD COUNT 10 STREAMS mystream 0  # 从头读
XREAD BLOCK 0 COUNT 1 STREAMS mystream $  # 阻塞读取新消息

# 消费者组
XGROUP CREATE mystream mygroup $ MKSTREAM
XREADGROUP GROUP mygroup consumer1 COUNT 1 STREAMS mystream >
XACK mystream mygroup 1625097600000-0  # 确认消息
```

**实战场景**：
- 消息队列（比List更可靠）
- 事件溯源（Event Sourcing）
- 实时数据流处理

### 1.7 HyperLogLog
**底层实现**：概率算法，固定内存占用（12KB）
**特点**：近似计数，误差0.81%

```bash
# 统计UV
PFADD daily:uv:20230701 "user_1" "user_2" "user_3"
PFADD daily:uv:20230701 "user_2" "user_4"  # 重复用户只计一次
PFCOUNT daily:uv:20230701  # 返回近似基数
PFMERGE monthly:uv:202307 daily:uv:20230701 daily:uv:20230702  # 合并
```

**实战场景**：
- 网站UV统计
- 去重计数（适合大数据量）

### 1.8 Bitmap（位图）
**底层实现**：String
**特点**：极致节省空间，支持位操作

```bash
# 用户签到系统
SETBIT sign:user_123:202307 0 1  # 7月1日签到
SETBIT sign:user_123:202307 1 1  # 7月2日签到
GETBIT sign:user_123:202307 0    # 查询某天签到
BITCOUNT sign:user_123:202307    # 签到总天数

# 在线用户统计
SETBIT online:20230701 1001 1   # 用户1001在线
SETBIT online:20230701 1002 1   # 用户1002在线
BITCOUNT online:20230701        # 在线人数
```

**实战场景**：
- 用户行为记录（签到、点赞、阅读）
- 布隆过滤器基础
- 在线状态统计

### 1.9 Geo（地理位置）
**底层实现**：ZSet（使用Geohash编码）
**特点**：支持地理位置计算

```bash
# 添加地理位置
GEOADD restaurants 116.397128 39.916527 "restaurant_1"
GEOADD restaurants 116.405285 39.904989 "restaurant_2"

# 计算距离
GEODIST restaurants "restaurant_1" "restaurant_2" km

# 附近商家
GEOSEARCH restaurants FROMLONLAT 116.397 39.916 BYRADIUS 2 km ASC
```

**实战场景**：
- 附近的人/店铺
- 距离计算
- 地理围栏

---

## 2) 底层数据结构实现

### 2.1 SDS（Simple Dynamic String）
**结构定义**：
```c
struct sdshdr {
    int len;      // 已使用长度
    int free;     // 剩余可用空间
    char buf[];   // 字符数组
};
```

**相比C字符串的优势**：
1. **O(1)时间获取长度**：不需要遍历
2. **杜绝缓冲区溢出**：自动扩容
3. **减少内存重分配**：空间预分配和惰性释放
4. **二进制安全**：可以存储任意二进制数据

```c
// Redis中的字符串创建示例
robj *createStringObject(const char *ptr, size_t len) {
    // 根据长度选择编码方式
    if (len <= OBJ_ENCODING_EMBSTR_SIZE_LIMIT)
        return createEmbeddedStringObject(ptr, len);
    else
        return createRawStringObject(ptr, len);
}
```

### 2.2 ziplist（压缩列表）
**结构特点**：
- 连续内存存储
- 节省指针开销
- 存储效率高

**节点结构**：
```
previous_entry_length | encoding | data
```

**连锁更新问题**：
当插入或删除节点导致多个节点的previous_entry_length需要更新时，可能引起级联更新，最坏情况时间复杂度O(N²)。

```c
// Redis 7.0+ 使用listpack替代ziplist
// listpack的节点结构
typedef struct {
    uint32_t total_size;  // 总大小
    uint8_t encoding;     // 编码方式
    uint8_t data[];       // 数据
} listpackNode;
```

### 2.3 quicklist
**设计思想**：ziplist + 链表的结合体

```c
typedef struct quicklist {
    quicklistNode *head;
    quicklistNode *tail;
    unsigned long count;        // 元素总数
    unsigned long len;          // 节点数量
    // ... 其他字段
} quicklist;

typedef struct quicklistNode {
    struct quicklistNode *prev;
    struct quicklistNode *next;
    unsigned char *zl;          // 指向ziplist/listpack
    size_t sz;                  // ziplist大小
    // ... 其他字段
} quicklistNode;
```

**优点**：
- 减少链表指针开销
- 限制ziplist大小，避免连锁更新
- 支持两端快速操作

### 2.4 skiplist（跳表）
**为什么用跳表而不是红黑树**：
1. 实现简单，代码易维护
2. 范围查询更高效
3. 并发友好（可通过局部加锁）

```c
// 跳表节点定义
typedef struct zskiplistNode {
    sds ele;                    // 成员对象
    double score;               // 分值
    struct zskiplistNode *backward;  // 后退指针
    struct zskiplistLevel {
        struct zskiplistNode *forward;  // 前进指针
        unsigned long span;             // 跨度
    } level[];                  // 层
} zskiplistNode;

// 跳表定义
typedef struct zskiplist {
    struct zskiplistNode *header, *tail;
    unsigned long length;
    int level;
} zskiplist;
```

### 2.5 intset（整数集合）
**特点**：
- 有序、无重复
- 节省内存
- 自动升级（当插入更大整数时）

```c
typedef struct intset {
    uint32_t encoding;    // 编码方式（16/32/64位）
    uint32_t length;      // 元素数量
    int8_t contents[];    // 柔性数组
} intset;

// 升级示例
intset *intsetUpgradeAndAdd(intset *is, int64_t value) {
    // 1. 计算新编码方式
    uint8_t newencoding = _intsetValueEncoding(value);
    
    // 2. 重新分配内存
    // 3. 将原有元素按新编码重新排列
    // 4. 插入新元素
}
```

### 2.6 hashtable（哈希表）
**渐进式rehash**：
```c
typedef struct dictht {
    dictEntry **table;      // 哈希桶数组
    unsigned long size;     // 大小
    unsigned long sizemask; // 大小掩码
    unsigned long used;     // 已使用数量
} dictht;

typedef struct dict {
    dictType *type;
    void *privdata;
    dictht ht[2];          // 两个哈希表，用于rehash
    long rehashidx;        // rehash进度（-1表示不在rehash）
    // ... 其他字段
} dict;
```

**rehash过程**：
1. 分配新哈希表（通常为原大小的2倍）
2. 逐渐将旧表数据迁移到新表
3. 每次CRUD操作迁移一个桶
4. 完成后交换新旧表

---

## 3) 内存管理

### 3.1 内存淘汰策略8种
Redis 4.0+ 提供8种淘汰策略：

```conf
# redis.conf 配置
maxmemory 4gb
maxmemory-policy allkeys-lru  # 默认策略
```

**策略详解**：

1. **noeviction**：不淘汰，内存满时返回错误
   ```bash
   SET test value  # OOM时返回(error) OOM command not allowed
   ```

2. **allkeys-lru**：所有键LRU淘汰
   ```bash
   # 使用近似LRU算法（采样）
   maxmemory-samples 10  # 采样数量
   ```

3. **volatile-lru**：仅淘汰有过期时间的键（LRU）

4. **allkeys-random**：随机淘汰所有键

5. **volatile-random**：随机淘汰有过期时间的键

6. **volatile-ttl**：淘汰TTL最短的键
   ```bash
   # 设置不同TTL
   SET key1 value1 EX 100
   SET key2 value2 EX 200
   # volatile-ttl会优先淘汰key1
   ```

7. **allkeys-lfu**：所有键LFU淘汰（Redis 4.0+）
   ```bash
   # LFU配置
   lfu-log-factor 10      # 计数器对数因子
   lfu-decay-time 1       # 衰减时间（分钟）
   ```

8. **volatile-lfu**：仅淘汰有过期时间的键（LFU）

**LRU vs LFU**：
- **LRU**（Least Recently Used）：最近最少使用
- **LFU**（Least Frequently Used）：最不经常使用

```bash
# 查看淘汰统计
INFO stats
evicted_keys:0  # 已淘汰键数量

# 监控内存使用
INFO memory
used_memory:1073741824
used_memory_human:1.00G
```

### 3.2 内存碎片整理
**问题产生**：
- 频繁创建不同大小的键
- 删除操作导致内存空洞

**解决方案**：

```conf
# 启用自动碎片整理
activedefrag yes

# 碎片整理触发条件
active-defrag-enabled yes
active-defrag-ignore-bytes 100mb      # 碎片大小阈值
active-defrag-threshold-lower 10      # 碎片率百分比下限
active-defrag-threshold-upper 100     # 碎片率百分比上限
active-defrag-cycle-min 1             # CPU占用最小百分比
active-defrag-cycle-max 25            # CPU占用最大百分比
```

**手动检查和整理**：
```bash
# 查看碎片率
INFO memory
mem_fragmentation_ratio:1.5  # >1.5表示碎片较多

# Redis 4.0+ 在线碎片整理
MEMORY PURGE  # 释放内存碎片

# 使用jemalloc（Redis默认内存分配器）
# 可以通过MEMORY DOCTOR命令获取建议
MEMORY DOCTOR
```

**最佳实践**：
1. 监控`mem_fragmentation_ratio`
2. 设置合理的`maxmemory`
3. 避免存储大量小对象
4. 考虑使用Hash聚合小字段

---

## 4) 持久化机制

### 4.1 RDB（Redis Database）
**触发方式**：
```conf
# redis.conf 配置
save 900 1      # 900秒内至少1个key变化
save 300 10     # 300秒内至少10个key变化
save 60 10000   # 60秒内至少10000个key变化

dbfilename dump.rdb
dir /var/lib/redis
```

**手动触发**：
```bash
# 后台异步保存
BGSAVE

# 同步保存（阻塞）
SAVE

# 查看上次保存状态
LASTSAVE
```

**RDB文件结构**：
```
REDIS | db_version | databases | EOF | check_sum
```

**优缺点**：
```bash
# 优点
- 文件紧凑，适合备份
- 恢复速度快（直接加载到内存）
- 对性能影响小（fork子进程）

# 缺点
- 可能丢失最后一次快照后的数据
- 数据量大时fork可能耗时
- 不适合实时持久化
```

### 4.2 AOF（Append Only File）
**配置选项**：
```conf
# 开启AOF
appendonly yes
appendfilename "appendonly.aof"

# 同步策略
# appendfsync always    # 每个写命令同步（最安全，最慢）
appendfsync everysec    # 每秒同步（推荐）
# appendfsync no        # 由操作系统决定（最快）

# AOF重写
auto-aof-rewrite-percentage 100  # 增长百分比触发
auto-aof-rewrite-min-size 64mb   # 最小大小触发

# Redis 7.0 多部分AOF
aof-use-rdb-preamble yes  # 混合持久化
```

**AOF重写**：
```bash
# 手动触发
BGREWRITEAOF

# 重写过程
1. fork子进程
2. 子进程写入新AOF文件（基于当前内存数据）
3. 主进程缓冲新写命令
4. 子进程完成后，主进程追加缓冲
5. 替换旧文件
```

### 4.3 混合持久化（Redis 4.0+）
```conf
# 开启混合持久化
aof-use-rdb-preamble yes
```

**工作原理**：
1. AOF重写时，先以RDB格式写入全量数据
2. 然后追加AOF格式的增量命令
3. 文件结构：`RDB头 + AOF尾`

**恢复流程**：
```bash
# Redis加载AOF文件
1. 识别RDB部分，快速加载
2. 重放AOF增量命令
3. 完整恢复数据
```

**持久化策略选择**：
```bash
# 生产环境推荐
# 1. 开启AOF（appendfsync everysec）
# 2. 开启混合持久化
# 3. 定期RDB备份（cron定时BGSAVE）
# 4. 主从复制（从节点关闭持久化）

# 备份脚本示例
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BGSAVE
sleep 5  # 等待保存完成
cp /var/lib/redis/dump.rdb /backup/redis/dump_${DATE}.rdb
```

---

## 5) 主从复制原理

### 5.1 复制过程
```bash
# 配置从节点
# 1. 配置文件
replicaof 192.168.1.100 6379
masterauth "password"

# 2. 命令行
SLAVEOF 192.168.1.100 6379
```

### 5.2 PSYNC机制（Redis 2.8+）
**解决断线重连的全量同步问题**：
```bash
# PSYNC命令格式
PSYNC <runid> <offset>

# 复制积压缓冲区（repl-backlog）
repl-backlog-size 256mb  # 建议：主节点写入速度 × 平均断线时间
repl-backlog-ttl 3600    # 缓冲区保留时间
```

**复制过程详解**：

1. **全量同步（首次连接或缓冲区不足）**：
   ```bash
   # 从节点 -> 主节点
   PSYNC ? -1
   
   # 主节点响应
   +FULLRESYNC <runid> <offset>
   
   # 主节点操作
   1. 执行BGSAVE生成RDB
   2. 记录期间的写命令到缓冲区
   3. 发送RDB文件
   4. 发送缓冲区命令
   ```

2. **增量同步（断线重连）**：
   ```bash
   # 从节点 -> 主节点
   PSYNC <runid> <offset>
   
   # 如果缓冲区有对应数据
   +CONTINUE
   
   # 主节点只发送差异命令
   ```

### 5.3 复制配置优化
```conf
# 主节点配置
# 1. 开启无盘复制（减少磁盘IO）
repl-diskless-sync yes
repl-diskless-sync-delay 5

# 2. 调整缓冲区
client-output-buffer-limit replica 256mb 64mb 60

# 3. 节点超时
repl-timeout 60

# 从节点配置
# 1. 只读模式
replica-read-only yes

# 2. 延迟持久化（主节点负责持久化）
replica-lazy-flush yes

# 3. 配置过期策略
replica-ignore-maxmemory yes
```

### 5.4 复制监控
```bash
# 主节点查看复制状态
INFO replication
role:master
connected_slaves:2
slave0:ip=192.168.1.101,port=6379,state=online,offset=12345,lag=0
slave1:ip=192.168.1.102,port=6379,state=online,offset=12345,lag=1

# 从节点查看复制状态
INFO replication
role:slave
master_host:192.168.1.100
master_port:6379
master_link_status:up
master_last_io_seconds_ago:0
master_sync_in_progress:0
```

---

## 6) Sentinel高可用

### 6.1 架构设计
```
客户端 -> Sentinel集群 -> Master/Slave集群
```

### 6.2 配置部署
```conf
# sentinel.conf
port 26379
daemonize yes
logfile "/var/log/redis/sentinel.log"

# 监控主节点
sentinel monitor mymaster 192.168.1.100 6379 2
sentinel auth-pass mymaster "password"

# 故障检测（主观下线）
sentinel down-after-milliseconds mymaster 30000

# 故障转移（客观下线）
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 180000

# 通知脚本
sentinel notification-script mymaster /var/redis/notify.sh
sentinel client-reconfig-script mymaster /var/redis/reconfig.sh
```

### 6.3 故障转移流程
1. **主观下线（SDOWN）**：
   ```bash
   # Sentinel每秒发送PING
   # 超时未响应标记为SDOWN
   sentinel is-master-down-by-addr mymaster 192.168.1.100 6379
   ```

2. **客观下线（ODOWN）**：
   ```bash
   # 达到quorum数量的Sentinel同意
   # 开始选举领导Sentinel（Raft算法）
   ```

3. **领导选举**：
   ```bash
   # Sentinel之间通过Raft协议选举
   # 获得多数票的成为领导
   ```

4. **故障转移**：
   ```bash
   # 领导Sentinel选择最优从节点
   # 1. 优先级（replica-priority）
   # 2. 复制偏移量
   # 3. runid排序
   
   # 执行故障转移
   # 1. 将选中的从节点提升为主
   # 2. 让其他从节点复制新主
   # 3. 通知客户端新主地址
   ```

### 6.4 客户端连接
```python
# Python示例
from redis.sentinel import Sentinel

sentinel = Sentinel([
    ('192.168.1.101', 26379),
    ('192.168.1.102', 26379),
    ('192.168.1.103', 26379)
], socket_timeout=0.5)

# 获取主节点
master = sentinel.master_for('mymaster', socket_timeout=0.5, password='password')
master.set('key', 'value')

# 获取从节点（读写分离）
slave = sentinel.slave_for('mymaster', socket_timeout=0.5, password='password')
slave.get('key')
```

---

## 7) Cluster集群

### 7.1 数据分片（Hash Slot）
**16384个槽分配**：
```bash
# 槽计算
CRC16(key) mod 16384

# 分配槽
redis-cli --cluster create 192.168.1.101:6379 192.168.1.102:6379 192.168.1.103:6379 \
  --cluster-replicas 1
```

### 7.2 MOVED/ASK重定向
**MOVED重定向（永久重定向）**：
```bash
# 客户端请求错误节点
GET user:1001
# (error) MOVED 1234 192.168.1.102:6379

# 客户端更新本地槽映射
# 后续请求直接发到正确节点
```

**ASK重定向（临时重定向，槽迁移中）**：
```bash
# 槽迁移过程中
GET user:1001
# (error) ASK 1234 192.168.1.103:6379

# 客户端需要先发送ASKING
ASKING
GET user:1001
```

### 7.3 集群管理
```bash
# 查看集群信息
redis-cli -c -h 192.168.1.101 CLUSTER INFO
cluster_state:ok
cluster_slots_assigned:16384
cluster_slots_ok:16384
cluster_known_nodes:6
cluster_size:3

# 查看节点信息
CLUSTER NODES
# 添加节点
redis-cli --cluster add-node 192.168.1.104:6379 192.168.1.101:6379

# 迁移槽
redis-cli --cluster reshard 192.168.1.101:6379

# 集群缩容
redis-cli --cluster del-node 192.168.1.101:6379 <node-id>
```

### 7.4 故障转移
```bash
# 自动故障转移（类似Sentinel）
cluster-node-timeout 15000  # 超时时间

# 手动故障转移（运维）
CLUSTER FAILOVER

# 模拟故障
DEBUG SLEEP 30  # 节点休眠30秒
```

### 7.5 集群配置优化
```conf
# redis.conf集群配置
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 15000

# 读写分离（从节点可读）
replica-read-only yes

# 槽迁移
cluster-allow-reads-when-down yes

# 集群总线端口（默认：端口+10000）
cluster-port 16379
```

---

## 8) Redis分布式锁

### 8.1 基础实现（SETNX）
```bash
# 获取锁
SET lock:order_123 unique_value NX EX 30
# NX: 不存在时才设置
# EX: 过期时间（秒）

# 释放锁（Lua脚本保证原子性）
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
else
    return 0
end
```

**Python实现**：
```python
import redis
import uuid
import time

class RedisLock:
    def __init__(self, redis_client, key, timeout=30):
        self.redis = redis_client
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.value = str(uuid.uuid4())
    
    def acquire(self):
        end_time = time.time() + self.timeout
        while time.time() < end_time:
            if self.redis.set(self.key, self.value, nx=True, ex=self.timeout):
                return True
            time.sleep(0.001)  # 避免忙等待
        return False
    
    def release(self):
        lua_script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """
        return self.redis.eval(lua_script, 1, self.key, self.value)
    
    def __enter__(self):
        if not self.acquire():
            raise Exception("Lock acquisition failed")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

# 使用示例
r = redis.Redis(host='localhost', port=6379)
with RedisLock(r, "order:123") as lock:
    # 执行业务逻辑
    print("Lock acquired, processing...")
```

### 8.2 Redlock算法
**解决单点Redis分布式锁的可靠性问题**：
```python
import redis
import time
import uuid
import math

class Redlock:
    def __init__(self, redis_nodes, retry_count=3, retry_delay=0.2, clock_drift_factor=0.01):
        self.redis_nodes = redis_nodes
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.clock_drift_factor = clock_drift_factor
        self.quorum = len(redis_nodes) // 2 + 1
    
    def acquire(self, resource, ttl):
        # 计算获取锁需要的时间
        retry = 0
        start_time = time.time()
        
        while retry < self.retry_count:
            n = 0
            start_time = time.time() * 1000
            
            # 在N个节点上尝试获取锁
            for node in self.redis_nodes:
                if self._acquire_node(node, resource, ttl):
                    n += 1
            
            # 计算获取锁花费的时间
            elapsed_time = time.time() * 1000 - start_time
            validity_time = ttl - elapsed_time - (elapsed_time * self.clock_drift_factor)
            
            # 检查是否在大多数节点获取成功
            if n >= self.quorum and validity_time > 0:
                return {
                    'resource': resource,
                    'value': str(uuid.uuid4()),
                    'validity_time