# 人工客服（飞书 Bot）运维指南

> 最后更新：2026-07-27

## 概述

StyleMint 页面的「人工客服」通过飞书 Bot 实现网页访客与客服人员的双向实时通讯。客服人员在飞书 IM 中回复消息，实时推送到网页端。

## 架构

```
网页访客 ←─ SSE ─→ NestJS (ChatModule) ←─ 飞书 Bot WSClient ─→ 客服飞书
               ↑                        ↑
          POST /api/chat/*      FEISHU_CHAT_APP_ID
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `FEISHU_CHAT_APP_ID` | 聊天专用应用 App ID（留空则复用 `FEISHU_APP_ID`） |
| `FEISHU_CHAT_APP_SECRET` | 聊天专用应用 Secret |
| `CHAT_AGENT_USER_ID` | 客服人员的飞书 open_id |

## 飞书应用配置

聊天应用 `cli_aaac3d51a2fa5cb3` 所需权限和能力：

| 配置 | 说明 |
|------|------|
| 机器人能力 | 应用功能 → 机器人 |
| `im:message` | 获取与发送单聊、群组消息 |
| `im:message.p2p_msg:readonly` | 读取用户发给机器人的单聊消息 |
| `im:message:send_as_bot` | 以应用的身份发消息 |
| `contact:contact.base:readonly` | 通讯录基本信息只读（查 open_id 用） |
| 事件订阅 `im.message.receive_v1` | 使用长连接接收事件 |
| 可见范围 | 全员或指定部门 |

## 更换客服人员

### 步骤一：查询 open_id

打开 **PowerShell**，整段复制粘贴回车：

```powershell
[Console]::OutputEncoding = [Text.UTF8Encoding]::new()
$appId = "cli_aaac3d51a2fa5cb3"
$appSecret = "8Rhv2tNt5utsg0MpRSavlSaaV07bfFp8"
$r1 = Invoke-RestMethod -Uri "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" -Method Post -ContentType "application/json" -Body "{""app_id"":""$appId"",""app_secret"":""$appSecret""}"
$r2 = Invoke-RestMethod -Uri "https://open.feishu.cn/open-apis/contact/v3/users?page_size=50" -Headers @{Authorization="Bearer $($r1.tenant_access_token)"}
$r2.data.items | ForEach-Object { Write-Host "$($_.name)  open_id=$($_.open_id)" }
```

输出示例：

```
张三  open_id=ou_aabbccdd11223344
李四  open_id=ou_5566778899aabbcc
```

### 步骤二：更新配置

1. 复制目标客服的 `open_id`（`ou_` 开头的一串）
2. 修改 `.env`：
   ```env
   CHAT_AGENT_USER_ID=ou_5566778899aabbcc
   ```
3. 重启后端服务

### 注意事项

- `open_id` 是绑定到具体应用的，更换聊天应用 App ID 后必须重新查询
- 查询命令无需修改任何变量，`$appId` 和 `$appSecret` 已内置
- 查询结果只显示「可见范围」内的用户（飞书控制台可调整）

## 消息格式

### 客服收到的飞书消息

- 首条消息：`【新会话 #abc12345】\n访客位置：广东深圳\nIP：1.2.3.4\n\n访客内容`
  - 省市通过 ip-api.com 查询（免费、无需 key、限 45 次/分钟，仅 HTTP）
  - 本地回环 / 内网 IP 不查询，降级为 `访客 IP：x.x.x.x`
  - 查询失败或超时（3 秒）也降级为只显示 IP
- 后续消息：`【#abc12345】访客内容`

### 客服回复规则

- **直接回复**：自动路由到最近活跃会话
- **指定会话**：`#abc12345 回复内容`（多会话并存时使用）

## 后端模块

`server/modules/chat/`

| 文件 | 职责 |
|------|------|
| `chat.module.ts` | 模块定义 |
| `chat.controller.ts` | REST API：session / message / stream / close |
| `chat.service.ts` | 会话管理（内存 Map）+ 消息转发 |
| `chat-sse.service.ts` | SSE 事件推送（EventEmitter） |
| `feishu-bot.service.ts` | 飞书 Bot WSClient 长连接 + 消息收发 + 回复路由 |
