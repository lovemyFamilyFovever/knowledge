---
title: "DNS深入解析"
tags: []
source: "baike"
source_path: "开发术语 / 网络与协议"
collected: "2026-09-05"
status: "imported"
---

# DNS深入解析

## DNS（Domain Name System）域名系统

**一句话定义：** DNS是把域名翻译成IP地址的系统，是互联网的"电话簿"。

**通俗类比：** DNS就像手机通讯录——你只需要记住名字（域名），通讯录自动帮你找到号码（IP地址）。

### 解析过程

```
用户输入 www.example.com
    ↓
1. 浏览器缓存
    ↓ (没有)
2. 操作系统缓存(/etc/hosts)
    ↓ (没有)
3. 本地DNS服务器(运营商)
    ↓ (没有)
4. 根DNS → 返回.com服务器地址
    ↓
5. .com服务器 → 返回example.com的DNS地址
    ↓
6. example.com的DNS → 返回www.example.com的IP
    ↓
7. 缓存结果，返回给用户
```

### 记录类型

| 类型 | 说明 | 示例 |
|------|------|------|
| A | 域名→IPv4 | 93.184.216.34 |
| AAAA | 域名→IPv6 | 2606:2800:220:1:: |
| CNAME | 别名指向 | www→cdn.example.com |
| MX | 邮件服务器 | mail.example.com |
| TXT | 文本记录 | SPF/DKIM验证 |
| NS | 权威DNS服务器 | ns1.example.com |

### DNS负载均衡

同一个域名解析到多个IP：
```
www.example.com → A: 1.2.3.4
                → A: 5.6.7.8
                → A: 9.10.11.12
```
用户被分配到不同服务器，实现负载均衡。

### DNS安全

**DNS劫持：** 篡改DNS响应，把用户引到假网站
**DNS缓存投毒：** 污染DNS缓存
**防护：** DNS over HTTPS(DOH)、DNSSEC签名验证
