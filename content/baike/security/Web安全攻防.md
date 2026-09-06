---
title: "Web安全攻防"
tags: []
source: "baike"
source_path: "开发术语 / 安全与加密"
collected: "2026-09-05"
status: "imported"
---

# Web安全攻防

## SQL注入

```python
# 危险！
query = f"SELECT * FROM users WHERE name='{username}' AND pass='{password}'"
# 输入: username = "admin' --"
# 变成: SELECT * FROM users WHERE name='admin' --' AND pass=''

# 安全：参数化查询
cursor.execute("SELECT * FROM users WHERE name=? AND pass=?", (username, password))
```

## XSS（跨站脚本）

| 类型 | 说明 |
|------|------|
| 存储型 | 恶意脚本存入数据库 |
| 反射型 | 脚本在URL参数中 |
| DOM型 | 前端JS操作DOM |

防护：输出转义、CSP头、HttpOnly Cookie。

## CSRF（跨站请求伪造）

```
用户登录bank.com -> 获取Cookie
访问evil.com -> evil.com自动发送请求到bank.com(携带Cookie)
```

防护：CSRF Token、SameSite Cookie、验证Referer。

## SSRF（服务端请求伪造）

```
攻击者通过服务端发起请求 -> 访问内网资源
```

防护：白名单URL、禁用内网IP、限制协议。
