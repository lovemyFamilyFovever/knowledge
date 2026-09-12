---
title: "分布式ID与缓存术语百科"
tags: [分布式与并行计算, 分布式缓存, 分布式ID, 术语合集]
source: "baike"
source_path: "开发术语 / 分布式系统"
collected: "2026-09-05"
status: "imported"
---

# 分布式ID与缓存术语百科


> 📌 **导航**：本文是 **分布式ID与缓存术语百科** 词条，属于 distributed 术语集。相关枢纽：[[BASE 理论]]、[[CAP 定理]]、[[MapReduce]]、[[Saga 与 TCC]]、[[一致性哈希]]。

> 本文档是分布式 **ID 生成**与**缓存设计**的深度参考合集：ID 方案选型，以及缓存穿透/击穿/雪崩、缓存一致性、多级缓存、热点与冷热数据等核心问题及解决方案。体系化概述见 [[分布式缓存]]，本文侧重实战细节与代码。
>
> **三大缓存问题一句话辨析**：穿透 = 查**根本不存在**的数据（缓存和库都没有，请求直达 DB）；击穿 = **单个热点 Key 过期**瞬间大量并发回源；雪崩 = **大量 Key 同时过期或缓存宕机**导致请求洪峰打库。

---

## 1. 分布式ID生成方案对比（UUID/数据库自增/Redis/雪花算法/Leaf）

### 一句话定义
分布式ID生成是在多节点环境下全局唯一地生成标识符的方案，需满足唯一性、有序性、高性能等要求。

### 通俗类比
就像全国身份证号码系统：18位数字，每个人唯一，有区域编码（前缀），有时间信息（中间部分），全国范围内绝不重复。

### 具体示例
```java
// UUID示例
String uuid = UUID.randomUUID().toString();
// "550e8400-e29b-41d4-a716-446655440000"
// 无序、太长（36字符）、不适合做主键

// 数据库自增
CREATE TABLE orders (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_no VARCHAR(32)
);
// 分库分表后会重复

// Redis自增
Long id = redisTemplate.opsForValue().increment("order:id");
// 需要保证Redis高可用

// 雪花算法
// | 1位符号 | 41位时间戳 | 10位机器ID | 12位序列号 |
// 64位Long类型，趋势递增

// 美团Leaf（号段模式+双Buffer）
// 数据库号段 + 本地缓存，性能极高
```

### 为什么需要它
数据库自增ID在分库分表后会重复，UUID无序且太长影响性能，需要全局唯一且有序的ID方案。

### 五大方案对比
| 方案 | 唯一性 | 有序性 | 性能 | 可用性 | 依赖 |
|------|--------|--------|------|--------|------|
| UUID | 全局 | 无序 | 高 | 高 | 无 |
| 数据库自增 | 单库 | 递增 | 中 | 低 | MySQL |
| Redis | 全局 | 递增 | 高 | 中 | Redis |
| 雪花算法 | 全局 | 递增 | 高 | 高 | 时钟 |
| Leaf | 全局 | 递增 | 极高 | 高 | MySQL |

### 方案选择建议
- **UUID**：适合非主键场景，如文件名、关联ID
- **数据库自增**：单库场景，简单可靠
- **Redis**：需要简单有序ID，可用性要求不高
- **雪花算法**：互联网项目首选，趋势递增
- **Leaf**：高性能要求，美团开源方案

---

## 2. 缓存穿透（布隆过滤器/缓存空值）

### 一句话定义
缓存穿透是查询一定不存在的数据，导致请求每次都打到数据库，可能压垮数据库。

### 通俗类比
就像你去图书馆找一本根本不存在的书：每次都问管理员，管理员每次都去书架找，最后发现没有。如果很多人同时找不同的不存在的书，管理员就忙不过来了。

### 具体示例
```java
// 问题代码：缓存穿透
public User getUserById(Long id) {
    // 1. 查缓存
    String cacheKey = "user:" + id;
    User user = redis.get(cacheKey);
    if (user != null) {
        return user; // 缓存命中
    }
    // 2. 查数据库
    user = db.selectById(id);
    if (user != null) {
        redis.set(cacheKey, user, 3600);
    }
    return user; // id不存在时，每次都会查库
}

// 解决方案1：布隆过滤器
BloomFilter<Long> bloomFilter = BloomFilter.create(
    Funnels.longFunnel(), 1000000, 0.01
);

public User getUserById(Long id) {
    // 先判断是否存在
    if (!bloomFilter.mightContain(id)) {
        return null; // 一定不存在，直接返回
    }
    // 可能存在，继续查缓存和数据库
    return getUserFromCacheOrDb(id);
}

// 解决方案2：缓存空值
public User getUserById(Long id) {
    String cacheKey = "user:" + id;
    User user = redis.get(cacheKey);
    if (user != null) {
        if ("NULL".equals(user)) return null; // 空值标记
        return user;
    }
    
    user = db.selectById(id);
    if (user != null) {
        redis.set(cacheKey, user, 3600);
    } else {
        redis.set(cacheKey, "NULL", 300); // 缓存空值，较短过期
    }
    return user;
}
```

### 为什么需要它
恶意请求或业务漏洞可能导致大量不存在的查询直接打到数据库，造成数据库压力过大甚至崩溃。

### 解决方案对比
| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 布隆过滤器 | 判断元素是否存在 | 空间小、性能高 | 有误判率 |
| 缓存空值 | 缓存null结果 | 简单 | 占用缓存空间 |
| 参数校验 | 过滤非法请求 | 简单 | 只能防简单攻击 |

---

## 3. 缓存雪崩（随机过期时间/多级缓存/熔断降级）

### 一句话定义
缓存雪崩是大量缓存同时过期或缓存服务宕机，导致请求全部打到数据库，造成数据库压力骤增。

### 通俗类比
就像高速公路：平时车流分散在各条路上（缓存），如果所有路突然封闭（缓存失效），所有车都涌向备用道路（数据库），导致交通瘫痪。

### 具体示例
```java
// 问题代码：大量Key同时过期
public void initCache() {
    // 所有商品缓存同时设置1小时过期
    for (Product product : products) {
        redis.set("product:" + product.getId(), product, 3600);
    }
    // 1小时后，所有Key同时失效
}

// 解决方案1：随机过期时间
public void initCache() {
    for (Product product : products) {
        // 基础过期时间 + 随机时间
        int expire = 3600 + RandomUtils.nextInt(600); // 3600-4200秒
        redis.set("product:" + product.getId(), product, expire);
    }
}

// 解决方案2：多级缓存
@Component
public class MultiLevelCache {
    @Autowired
    private LocalCache localCache; // 本地缓存（Caffeine）
    @Autowired
    private RedisTemplate redis;
    
    public Object get(String key) {
        // L1: 本地缓存
        Object value = localCache.get(key);
        if (value != null) return value;
        
        // L2: Redis缓存
        value = redis.opsForValue().get(key);
        if (value != null) {
            localCache.put(key, value, 60); // 本地缓存1分钟
            return value;
        }
        
        // L3: 数据库
        value = db.query(key);
        if (value != null) {
            redis.opsForValue().set(key, value, 3600);
            localCache.put(key, value, 60);
        }
        return value;
    }
}

// 解决方案3：熔断降级
@CircuitBreaker(name = "cache", fallbackMethod = "fallback")
public Object get(String key) {
    return redis.opsForValue().get(key);
}

public Object fallback(String key, Throwable t) {
    // Redis不可用时，直接查库
    return db.query(key);
}
```

### 为什么需要它
缓存是数据库的保护层，缓存大面积失效会导致保护层消失，数据库承受不住瞬间涌入的请求。

### 解决方案对比
| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 随机过期 | 分散失效时间 | 简单 | 仍有概率集中 |
| 多级缓存 | 本地+分布式 | 可靠 | 架构复杂 |
| 熔断降级 | 快速失败 | 保护数据库 | 用户体验差 |
| 缓存预热 | 提前加载 | 无雪崩 | 需要预测 |

---

## 4. 缓存击穿（互斥锁/永不过期/逻辑过期）

### 一句话定义
缓存击穿是某个热点Key突然失效，大量并发请求同时打到数据库，造成瞬间压力。

### 通俗类比
就像明星演唱会门票：平时大家网上买票（缓存），但如果售票系统突然崩溃，所有人涌向窗口（数据库），瞬间挤爆窗口。

### 具体示例
```java
// 问题代码：缓存击穿
public Product getProduct(Long id) {
    String cacheKey = "product:" + id;
    Product product = redis.get(cacheKey);
    if (product == null) {
        // 热点Key过期，100个并发同时查库
        product = db.selectById(id);
        redis.set(cacheKey, product, 3600);
    }
    return product;
}

// 解决方案1：互斥锁
public Product getProduct(Long id) {
    String cacheKey = "product:" + id;
    Product product = redis.get(cacheKey);
    if (product == null) {
        String lockKey = "lock:" + cacheKey;
        try {
            // 尝试获取锁
            if (redis.opsForValue().setIfAbsent(lockKey, "1", 10, TimeUnit.SECONDS)) {
                // 获取锁成功，查库
                product = db.selectById(id);
                redis.set(cacheKey, product, 3600);
            } else {
                // 未获取锁，等待后重试
                Thread.sleep(100);
                return getProduct(id);
            }
        } finally {
            redis.delete(lockKey);
        }
    }
    return product;
}

// 解决方案2：逻辑过期
public Product getProduct(Long id) {
    String cacheKey = "product:" + id;
    Product product = redis.get(cacheKey);
    if (product == null) {
        product = db.selectById(id);
        // 设置逻辑过期时间
        CacheObject cacheObject = new CacheObject();
        cacheObject.setData(product);
        cacheObject.setExpireTime(System.currentTimeMillis() + 3600 * 1000);
        redis.set(cacheKey, cacheObject); // 永不过期
    } else {
        CacheObject cacheObject = (CacheObject) product;
        if (cacheObject.isExpired()) {
            // 逻辑过期，异步更新
            asyncUpdateCache(id);
            return (Product) cacheObject.getData(); // 返回旧数据
        }
    }
    return product;
}
```

### 为什么需要它
热点数据的并发极高，一旦缓存失效，大量请求同时打到数据库，造成瞬间压力。

### 解决方案对比
| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 互斥锁 | 只允许一个线程查库 | 数据一致 | 性能下降 |
| 永不过期 | 不设置过期时间 | 无击穿 | 数据可能过期 |
| 逻辑过期 | 业务层判断过期 | 性能好 | 实现复杂 |

---

## 5. 缓存一致性（先更新DB再删缓存/延迟双删/Canal监听）

### 一句话定义
缓存一致性是保证数据库和缓存中数据在更新操作后保持一致的策略。

### 通俗类比
就像银行账户：你在ATM机改了密码（更新数据库），还要通知手机银行同步更新（删除缓存），否则两边密码不一致。

### 具体示例
```java
// 方案1：先更新DB，再删缓存（推荐）
public void updateProduct(Product product) {
    // 1. 先更新数据库
    db.update(product);
    // 2. 再删除缓存
    redis.delete("product:" + product.getId());
    // 注意：不是更新缓存，而是删除！
}

// 方案2：延迟双删
public void updateProduct(Product product) {
    // 1. 先删缓存
    redis.delete("product:" + product.getId());
    // 2. 更新数据库
    db.update(product);
    // 3. 异步延迟再删一次（清理此间可能被回填的旧值）；❌ 不要用同步 Thread.sleep 阻塞写线程
    delayExecutor.schedule(() -> redis.delete("product:" + product.getId()),
            500, TimeUnit.MILLISECONDS);
}

// 方案3：Canal 订阅 MySQL binlog，异步失效缓存（业务解耦、最终一致）
@CanalTable("product")
public void onProductChange(CanalEntry.RowData rowData) {
    // Canal 的 Column 是列表，需按列名匹配取主键，而非 Map.get("id")
    String productId = rowData.getAfterColumnsList().stream()
            .filter(c -> "id".equals(c.getName()))
            .map(CanalEntry.Column::getValue)
            .findFirst().orElse(null);
    if (productId != null) {
        redis.delete("product:" + productId);
    }
}

// 方案4：Read-Through（读时加载）
public Product getProduct(Long id) {
    String cacheKey = "product:" + id;
    return redis.opsForValue().get(cacheKey, 
        key -> db.selectById(id)); // 缓存未命中时自动加载
}
```

> 注：上方方案 4 的 `get(key, loader)` 是 Read-Through 的**示意**写法——RedisTemplate 并无此 API，工程上应由 Caffeine 的 LoadingCache 或自封装缓存组件实现「未命中自动回源」。

### 为什么需要它
数据库和缓存是两套系统，更新时可能不一致，导致用户看到脏数据。

### 方案对比
| 方案 | 一致性 | 性能 | 复杂度 | 适用场景 |
|------|--------|------|--------|----------|
| 先更新DB再删缓存 | 高 | 高 | 低 | 大多数场景 |
| 延迟双删 | 很高 | 中 | 中 | 强一致要求 |
| Canal监听 | 很高 | 高 | 高 | 实时性要求高 |
| Read-Through | 最终 | 高 | 中 | 读多写少 |

---

## 6. 多级缓存架构（本地缓存+分布式缓存）

### 一句话定义
多级缓存架构是将本地缓存和分布式缓存组合使用，兼顾性能和一致性的缓存方案。

### 通俗类比
就像厨房调料：常用调料放在灶台旁（本地缓存），不常用的放在储藏室（分布式缓存），实在没有再去超市买（数据库）。

### 具体示例
```java
@Component
public class MultiLevelCacheManager {
    @Autowired
    private Cache<String, Object> localCache; // Caffeine
    @Autowired
    private RedisTemplate<String, Object> redis;
    
    // 三级缓存架构
    // L1: 本地缓存（Caffeine）- 毫秒级
    // L2: Redis缓存 - 毫秒级
    // L3: 数据库 - 秒级
    
    public Object get(String key) {
        // L1: 查本地缓存
        Object value = localCache.getIfPresent(key);
        if (value != null) {
            return value;
        }
        
        // L2: 查Redis
        value = redis.opsForValue().get(key);
        if (value != null) {
            localCache.put(key, value); // 回填本地缓存
            return value;
        }
        
        // L3: 查数据库
        value = db.query(key);
        if (value != null) {
            redis.opsForValue().set(key, value, 3600);
            localCache.put(key, value);
        }
        return value;
    }
    
    // 多级缓存失效策略
    public void invalidate(String key) {
        localCache.invalidate(key); // 删除本地缓存
        redis.delete(key); // 删除Redis缓存
    }
}

// Caffeine配置
@Bean
public Cache<String, Object> localCache() {
    return Caffeine.newBuilder()
        .maximumSize(10000)
        .expireAfterWrite(60, TimeUnit.SECONDS)
        .build();
}
```

### 为什么需要它
单级缓存要么性能不够（只有Redis），要么一致性不够（只有本地），多级缓存兼顾两者。

### 多级缓存架构图
```
┌─────────────────────────────────────────────┐
│                 应用服务器                    │
│  ┌─────────────────────────────────────┐   │
│  │         L1: 本地缓存 (Caffeine)      │   │
│  │         容量: 1000条                  │   │
│  │         过期: 60秒                    │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│              L2: Redis集群                  │
│         容量: 100万条                       │
│         过期: 1小时                         │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│              L3: 数据库                     │
│         MySQL / PostgreSQL                 │
└─────────────────────────────────────────────┘
```

### 各级缓存对比
| 级别 | 类型 | 性能 | 容量 | 一致性 |
|------|------|------|------|--------|
| L1 | 本地缓存 | 极高 | 小 | 弱 |
| L2 | Redis | 高 | 大 | 中 |
| L3 | 数据库 | 低 | 最大 | 强 |

---

## 7. 热点数据处理（永不过期/提前刷新/互斥锁）

### 一句话定义
热点数据处理是针对访问频率极高的数据采用特殊策略，防止缓存击穿和数据库压力。

### 通俗类比
就像超市的热门商品：把可乐、矿泉水放在收银台旁（热点数据），随时补货（永不过期），避免缺货。

### 具体示例
```java
// 方案1：热点数据永不过期
public Product getHotProduct(Long id) {
    String cacheKey = "hot:product:" + id;
    Product product = redis.opsForValue().get(cacheKey);
    if (product == null) {
        // 首次加载，设置较长过期时间
        product = db.selectById(id);
        redis.opsForValue().set(cacheKey, product, 24, TimeUnit.HOURS);
    }
    return product;
}

// 方案2：提前刷新
@Component
public class HotDataRefresher {
    @Scheduled(fixedRate = 3600000) // 每小时执行
    public void refreshHotProducts() {
        List<Long> hotProductIds = getHotProductIds();
        for (Long id : hotProductIds) {
            Product product = db.selectById(id);
            redis.opsForValue().set("hot:product:" + id, product, 24, TimeUnit.HOURS);
        }
    }
}

// 方案3：互斥锁保护热点Key
public Product getHotProduct(Long id) {
    String cacheKey = "hot:product:" + id;
    Product product = redis.opsForValue().get(cacheKey);
    if (product == null) {
        String lockKey = "lock:" + cacheKey;
        try {
            if (redis.opsForValue().setIfAbsent(lockKey, "1", 5, TimeUnit.SECONDS)) {
                // 双重检查
                product = redis.opsForValue().get(cacheKey);
                if (product == null) {
                    product = db.selectById(id);
                    redis.opsForValue().set(cacheKey, product, 24, TimeUnit.HOURS);
                }
            } else {
                Thread.sleep(100);
                return getHotProduct(id); // 重试
            }
        } finally {
            redis.delete(lockKey);
        }
    }
    return product;
}
```

### 为什么需要它
普通缓存策略对热点数据效果有限，需要特殊处理防止并发问题。

### 热点数据处理策略对比
| 策略 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 永不过期 | 不设置过期时间 | 无击穿 | 数据可能过期 |
| 提前刷新 | 定时更新 | 数据新鲜 | 有时间窗口 |
| 互斥锁 | 控制并发 | 数据一致 | 性能下降 |

---

## 8. 冷热数据分离策略

### 一句话定义
冷热数据分离是将访问频率高的热数据和访问频率低的冷数据分开存储，优化资源利用。

### 通俗类比
就像图书馆：热门书籍放在一楼开架区（热数据），冷门书籍放在楼上书库（冷数据），方便读者快速找到热门书。

### 具体示例
```java
// 冷热数据分离策略
@Component
public class HotColdDataSeparator {
    @Autowired
    private RedisTemplate<String, Object> redis;
    
    // 热数据：Redis（高性能）
    // 冷数据：MySQL/冷存储（大容量）
    
    public Object getData(String key) {
        // 先查热数据
        Object value = redis.opsForValue().get("hot:" + key);
        if (value != null) {
            // 访问计数+1
            redis.opsForValue().increment("access:" + key);
            return value;
        }
        
        // 再查冷数据
        value = db.query(key);
        if (value != null) {
            // 如果访问频繁，升级为热数据
            if (isHotData(key)) {
                redis.opsForValue().set("hot:" + key, value, 3600);
            }
        }
        return value;
    }
    
    // 判断是否为热数据
    private boolean isHotData(String key) {
        Long accessCount = redis.opsForValue().increment("access:" + key);
        return accessCount > 100; // 24小时内访问超过100次
    }
    
    // 定时清理冷数据
    @Scheduled(cron = "0 0 3 * * ?") // 每天凌晨3点
    public void cleanColdData() {
        Set<String> hotKeys = redis.keys("hot:*");
        Set<String> allKeys = db.getAllKeys();
        
        for (String key : allKeys) {
            if (!hotKeys.contains("hot:" + key)) {
                // 超过30天未访问，归档到冷存储
                archiveToColdStorage(key);
            }
        }
    }
}
```

### 为什么需要它
冷热数据混合存储浪费资源，分离后热数据用高性能存储，冷数据用大容量存储。

### 冷热数据分离架构
```
┌─────────────────────────────────────────────┐
│              访问请求                        │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│              数据路由层                      │
│  根据访问频率决定存储位置                     │
└─────────────────────────────────────────────┘
         │                         │
         ▼                         ▼
┌─────────────────┐    ┌─────────────────────┐
│  热数据存储      │    │  冷数据存储          │
│  Redis集群       │    │  MySQL/HDFS/S3       │
│  容量: 10GB      │    │  容量: 1TB           │
│  性能: <1ms      │    │  性能: >10ms         │
│  有效期: 24h     │    │  有效期: 永久        │
└─────────────────┘    └─────────────────────┘
```

### 冷热数据对比
| 特性 | 热数据 | 冷数据 |
|------|--------|--------|
| 访问频率 | 高 | 低 |
| 存储介质 | Redis | MySQL/HDFS |
| 容量 | 小 | 大 |
| 性能 | 极高 | 中等 |
| 成本 | 高 | 低 |

---

## 缓存设计全景图

```
┌─────────────────────────────────────────────────────────────┐
│                      客户端请求                              │
└──────────────────────────────┬──────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │      API网关        │
                    │    (限流/认证)      │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼─────────┐ ┌───▼───────────┐ ┌──▼────────────┐
    │  L1: 本地缓存     │ │ L2: Redis     │ │ L3: 数据库    │
    │  (Caffeine)       │ │ (分布式缓存)   │ │ (MySQL)       │
    │  容量: 1万        │ │ 容量: 100万   │ │ 容量: 无限     │
    │  过期: 60秒       │ │ 过期: 1小时   │ │               │
    └───────────────────┘ └───────────────┘ └───────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │     缓存监控        │
                    │  (命中率/延迟/QPS)  │
                    └─────────────────────┘
```

---

## 相关术语

[[分布式缓存]]、[[缓存策略]]、[[Redis深入]]、[[分布式基础术语百科]]、[[高并发系统设计]]

## 参考资料

建议人工核验：可参考《Redis 设计与实现》（黄健宏）、Redis 官方文档（过期/淘汰/持久化）、美团 Leaf 与 Guava BloomFilter 文档，以及 Cache-Aside / Read-Through / Write-Behind 等缓存模式的经典阐述（如 Microsoft Azure Architecture Center）。

> 📌 **学习建议**：建议先掌握分布式ID生成方案（雪花算法最常用），再深入理解缓存穿透、雪崩、击穿的区别。缓存一致性是面试高频考点，建议重点理解"先更新DB再删缓存"策略。多级缓存架构是实际项目中的最佳实践，建议结合业务场景设计。
