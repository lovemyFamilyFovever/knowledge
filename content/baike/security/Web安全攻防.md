---
title: "Web安全攻防"
tags: []
source: "baike"
source_path: "开发术语 / 安全与加密"
collected: "2026-09-05"
status: "imported"
---

# Web安全攻防


> 📌 **导航**：本文是 **Web安全攻防** 词条，属于 security 术语集。相关枢纽：[[公钥基础设施]]、[[密码学基础篇]]、[[零信任安全架构]]。

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

## 相关术语

[[OAuth 与 JWT]]、[[SQL注入与XSS]]、[[中间人攻击]]、[[供应链安全]]、[[公钥基础设施]]、[[分布式拒绝服务攻击]]

## 参考资料

建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；未编造文献编号、标准号或 URL，如需引用请补充具体出处。
