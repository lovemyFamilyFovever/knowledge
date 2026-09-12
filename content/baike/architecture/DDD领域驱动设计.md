---
title: "DDD领域驱动设计"
tags: []
source: "baike"
source_path: "开发术语 / 架构与设计"
collected: "2026-09-05"
status: "imported"
---

# DDD领域驱动设计


> 📌 **导航**：本文是 **DDD领域驱动设计** 词条，属于 architecture 术语集。相关枢纽：[[SaaS产品技术架构]]、[[事件驱动架构]]、[[云原生与多云架构实战指南]]、[[分布式系统设计完全指南]]、[[微服务架构]]。

## 核心概念

| 概念 | 说明 | 示例 |
|------|------|------|
| 实体(Entity) | 有唯一标识 | 用户、订单 |
| 值对象(Value Object) | 无标识，不可变 | 地址、金额 |
| 聚合(Aggregate) | 一组相关对象的边界 | 订单+订单项 |
| 聚合根(Aggregate Root) | 聚合的入口 | 订单 |
| 限界上下文(Bounded Context) | 业务边界 | 用户上下文 vs 订单上下文 |
| 领域事件(Domain Event) | 领域中发生的事件 | 订单已支付 |
| 领域服务(Domain Service) | 不属于任何实体的业务逻辑 | 转账服务 |

## 战略设计

```
统一语言(Ubiquitous Language)
    ↓
限界上下文划分
    ↓
上下文映射(Context Mapping)
    - 共享内核(Shared Kernel)
    - 客户-供应商(Customer-Supplier)
    - 防腐层(Anti-Corruption Layer)
    - 开放主机服务(Open Host Service)
```

## 战术设计

```python
# 聚合根示例
class Order(AggregateRoot):
    def __init__(self, order_id, customer_id):
        self.order_id = order_id
        self.customer_id = customer_id
        self.items = []
        self.status = OrderStatus.CREATED

    def add_item(self, product_id, quantity, price):
        if self.status != OrderStatus.CREATED:
            raise DomainException("已确认的订单不能添加商品")
        self.items.append(OrderItem(product_id, quantity, price))
        self.add_event(ItemAdded(self.order_id, product_id, quantity))

    def confirm(self):
        if not self.items:
            raise DomainException("空订单不能确认")
        self.status = OrderStatus.CONFIRMED
        self.add_event(OrderConfirmed(self.order_id))
```

## 相关术语

[[领域驱动设计DDD完全指南]]、[[API设计]]、[[SaaS产品技术架构]]、[[事件驱动架构]]、[[云原生与多云架构实战指南]]、[[分布式系统设计完全指南]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
