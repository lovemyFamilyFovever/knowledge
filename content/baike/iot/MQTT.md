---
title: "MQTT"
tags: [物联网, MQTT, 消息协议]
source: "baike"
source_path: "开发术语 / 物联网"
collected: "2026-09-12"
status: "imported"
---

# MQTT


> 📌 **导航**：本文是 **MQTT** 词条，属于 iot 术语集。相关枢纽：[[MQTT]]、[[物联网与嵌入式基础]]。

## 定义

**一句话定义：** MQTT(Message Queuing Telemetry Transport)是一种轻量级的发布/订阅消息传输协议,基于 TCP,专为低带宽、高延迟、网络不稳定、设备资源受限的物联网场景设计,是 IoT 设备通信的事实标准之一。

**通俗类比：** 像订阅杂志/关注频道——设备(publisher)把数据"发布"到某个主题(topic),需要这些数据的一方(subscriber)"订阅"该主题即可收到;中间有个"邮局"(broker)按主题分发,发布者与订阅者互不相识、彼此解耦。

> 多义说明:MQTT 是发布/订阅协议(区别于 HTTP 的请求/响应);有 MQTT 3.1.1 与 5.0,另有面向受限设备的 MQTT-SN。本文讨论 MQTT。

## 为什么需要它

弱网 M2M 链路上 HTTP 两头吃亏:客户端不知道"有没有新消息"只能轮询,文本头又远大于有效载荷;设备侧算力与电量撑不起频繁握手。MQTT 把方向反过来——长连接常驻、极小二进制报文头、按主题订阅由 broker 推送,把"谁要找谁"从两端挪到中间层,让 1 字节载荷也值得发一条。

## 核心机制

- **角色**:发布者、订阅者、代理 broker(如 Mosquitto / EMQX)。发布与订阅互不认识,只认主题。
- **主题 topic**:斜杠分层(`home/livingroom/temp`);订阅端通配符 `+` 匹配单层、`#` 匹配多层。主题设计即隐式契约,定坏难改。
- **QoS 三级**:0 至多一次(发完不管,可能丢)、1 至少一次(PUBACK 重传,可能重复)、2 恰好一次(PUBREC/PUBREL/PUBCOMP 四次握手,RTT 翻倍)。保证粒度是"每一跳",不等于全局端到端(见 [[消息投递语义]])。
- **保活与会话**:KEEPALIVE 心跳判定掉线;持久会话由 broker 保存未确认的 QoS 1/2 消息,重连后续传(5.0 用 Session Expiry Interval 控制时长)。
- **broker 侧三件套**:遗嘱消息 LWT(设备异常掉线时由 broker 代发预设的离线通知)、保留消息 retained(新订阅者立刻拿到该主题最后一条)、共享订阅(5.0,多消费者水平分摊)。

## 具体示例

智能家居温湿度:设备发布 `home/livingroom/temp`,QoS 1 + retained,App 打开即见最新值;App 订阅 `home/+/temp` 覆盖所有房间。设备掉线由遗嘱自动发 `home/livingroom/status` = offline。若要求"同一条控制指令绝不执行两次",QoS 2 仍不够——消息体要带幂等 ID 由消费端去重。

## 何时用与何时不用

- **用**:海量设备、带宽差电量小、消息小而频繁、上报/订阅式遥测、需要服务端反向下发控制指令。
- **不用**:低延迟请求-应答式 RPC、大文件与批量传输、消费者全是服务端且要高吞吐回放(该上 Kafka)、两端可直接对等通信。
- 移动端弱网推送可用,但依赖 App 常驻长连接与后台保活权限;iOS 前台外仍要走 APNs。

## 优劣与代价

✅ 报文极轻省电量带宽、发布订阅彻底解耦、QoS 分级可摊到不同可靠性需求、天然适配海量设备。
⚠️ broker 是中心节点:可用性、吞吐与水平扩展都要自己设计;QoS 2 弱网下时延翻倍;默认明文,需 TLS(惯例 1883 明文 / 8883 TLS,称 MQTTS)。
⚠️ 主题无 schema 约束,载荷格式靠约定,设备量上来后易长成乱麻;协议本身不做请求-响应,要自己做 request/reply 主题对。

## 与相关概念的区别

- **vs HTTP**:方向相反——HTTP 由客户端发起请求,MQTT 由 broker 推给订阅者;HTTP 适合拉取,MQTT 适合推送与遥测。
- **vs 消息队列(Kafka/RabbitMQ)**:同族不同位——MQTT 是"设备到云"的轻量传输协议,主题即路由、不保证分区顺序;Kafka 是服务端高吞吐事件流,靠分区与偏移量回放(见 [[消息队列（Message Queue）]])。
- **vs CoAP**:CoAP 跑 UDP、是受限设备上的类 REST 请求/响应,安全用 DTLS;MQTT 跑 TCP、靠长连接推送。
- **vs WebSocket**:后者只是双向通道,不定义 QoS/retained/LWT 等消息语义。

## 常见误区

- MQTT 的 QoS 2 能保证端到端 exactly-once,业务侧不用再处理重复消息。
- MQTT 默认对报文加密,和 HTTPS 一样直接可用。
- 有 broker 兜底就行,broker 可以单点部署,retained 消息能当数据库用。

## 面试速答

> 🎯 跑在 TCP 上的发布/订阅协议：2 字节报文头 + 长连接心跳 + 主题通配符，QoS 0/1/2 分级，broker 解耦两端。
> 🔍 追问：QoS 1 与 QoS 2 的报文交互和各自代价?
> 🔍 追问：为什么 QoS 2 仍不满足业务级 exactly-once?
> 🔍 追问：retained 与遗嘱消息分别解决什么问题?

## 相关术语

[[物联网与嵌入式基础]]、[[消息队列（Message Queue）]]、[[消息投递语义]]、[[应用层协议]]

## 参考资料

建议人工核验:MQTT 由 IBM 的 Andy Stanford-Clark 与 Arlen Nipper 于 1999 年提出;已标准化为 OASIS / ISO(MQTT 3.1.1、5.0);具体标准编号建议人工核验。
