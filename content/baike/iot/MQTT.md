---
title: "MQTT"
tags: [物联网, MQTT, 消息协议]
source: "baike"
source_path: "开发术语 / 物联网"
collected: "2026-09-12"
status: "imported"
---

# MQTT

## 定义

**一句话定义：** MQTT(Message Queuing Telemetry Transport)是一种轻量级的发布/订阅消息传输协议,基于 TCP,专为低带宽、高延迟、网络不稳定、设备资源受限的物联网场景设计,是 IoT 设备通信的事实标准之一。

**通俗类比：** 像订阅杂志/关注频道——设备(publisher)把数据"发布"到某个主题(topic),需要这些数据的一方(subscriber)"订阅"该主题即可收到;中间有个"邮局"(broker)按主题分发,发布者与订阅者互不相识、彼此解耦。

> 多义说明:MQTT 是发布/订阅协议(区别于 HTTP 的请求/响应);有 MQTT 3.1.1 与 5.0,另有面向受限设备的 MQTT-SN。本文讨论 MQTT。

## 原理与机制

- **角色:** 发布者(publisher)、订阅者(subscriber)、代理(broker,如 Mosquitto / EMQX)。
- **主题(topic):** 分层命名(如 `home/livingroom/temp`),支持通配符订阅(`+` 单层、`#` 多层)。
- **QoS 三级:** QoS 0(至多一次)、QoS 1(至少一次)、QoS 2(恰好一次),对应不同投递语义(见 [[消息投递语义]])。
- **轻量特性:** 最小报文头仅 2 字节;支持遗嘱消息(LWT)、保留消息(retained)、心跳保活。

## 关键组成

| 组成 | 说明 |
|------|------|
| broker | 消息代理与分发中心 |
| publisher / subscriber | 发布方与订阅方 |
| topic 与通配符 | 主题分层与订阅匹配 |
| QoS 0/1/2 | 投递可靠性级别 |
| 遗嘱 / 保留消息 | LWT 与 retained |

## 应用场景

- 物联网设备上报与控制
- 智能家居、车联网
- 工业遥测
- 移动端弱网消息推送

## 优点与局限

- 优点:协议轻量(省带宽/电量)、发布订阅解耦、支持弱网与 QoS、适合海量设备。
- 局限:依赖 broker(中心节点);QoS 2 开销大;默认不加密(需配 TLS,即 MQTTS);主题设计影响可维护性;非请求-响应模型(不适合需即时应答的场景)。

## 常见误区

- MQTT 是发布/订阅模型,不是请求/响应。
- 默认不加密,需 TLS(MQTTS)。
- QoS 是"每对发布-订阅"的保证,不等于全局端到端的绝对 exactly-once。
- broker 是中心节点,需保证其可用性与扩展性。
- MQTT ≠ HTTP,适用场景不同。

## 相关术语

[[物联网与嵌入式基础]]、[[消息队列（Message Queue）]]、[[消息投递语义]]、[[应用层协议]]

## 参考资料

建议人工核验:MQTT 由 IBM 的 Andy Stanford-Clark 与 Arlen Nipper 于 1999 年提出;已标准化为 OASIS / ISO(MQTT 3.1.1、5.0);具体标准编号建议人工核验。
