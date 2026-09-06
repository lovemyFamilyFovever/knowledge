---
tags: [网络, HTTP]
source: "myblog"
collected: "2026-09-05"
status: "imported"
source_path: "network/http-headers-analysis.md"
---

# HTTP 请求头分析与脚本问题诊断

## 背景
运行脚本 `hongxiuzhao.py` 时，遇到 `ConnectionResetError (10054, '远程主机强迫关闭了一个现有的连接。')`，表明服务器 (`hongxiuzhao.org`) 拒绝了请求，可能是由于反爬虫机制（如 Cloudflare 保护）、Cookie 失效或请求头不匹配。以下是对提供的浏览器请求头的详细分析，解释每个头的含义，并与脚本中的 `HEADERS` 进行对比，找出问题并提出解决方案。

## 浏览器请求头分析
以下是从浏览器控制台捕获的请求头，针对 `https://hongxiuzhao.org/MjYOJrq.html` 的 GET 请求：

### 1. `:authority: hongxiuzhao.org`
- **含义**：HTTP/2 伪头字段，指定目标域名，等同于 HTTP/1.1 的 `Host` 头，告诉服务器请求的目标主机。
- **脚本对比**：脚本未显式设置 `:authority` 或 `Host`，但 `requests` 库会根据 URL 自动设置 `Host: hongxiuzhao.org`。
- **问题**：无。

### 2. `:method: GET`
- **含义**：HTTP/2 伪头字段，指定请求方法（GET），表示获取资源。
- **脚本对比**：`requests.get()` 隐式使用 GET 方法，与浏览器一致。
- **问题**：无。

### 3. `:path: /MjYOJrq.html`
- **含义**：HTTP/2 伪头字段，指定请求路径（不包括域名）。
- **脚本对比**：脚本请求的是 `/J5XM0nbM.html`，与浏览器路径不同。
- **问题**：URL 不一致，可能导致页面不可访问或触发反爬机制。

### 4. `:scheme: https`
- **含义**：HTTP/2 伪头字段，指定协议（HTTPS），表示通过 TLS 加密连接。
- **脚本对比**：`requests` 使用 HTTPS 协议，自动处理。
- **问题**：无。

### 5. `accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7`
- **含义**：指定客户端接受的响应内容类型，优先级为 HTML、XHTML、XML、图像格式等，`q` 值表示优先级。
- **脚本对比**：脚本的 `Accept` 头完全一致。
- **问题**：无。

### 6. `accept-encoding: gzip, deflate, br, zstd`
- **含义**：指定支持的压缩格式（gzip、deflate、Brotli、zstd）。
- **脚本对比**：脚本的 `Accept-Encoding` 一致，脚本已正确处理 Brotli 压缩。
- **问题**：无。

### 7. `accept-language: en,zh-CN;q=0.9,zh;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5`
- **含义**：指定首选语言，优先级为英语、简体中文等。
- **脚本对比**：脚本的 `Accept-Language` 为 `zh-CN,zh;q=0.9,en;q=0.8`，缺少部分语言选项。
- **问题**：不完整的语言头可能被服务器检测为异常。

### 8. `cookie: __51vcke__3JpfN0uIRLmkKzss=...; cf_clearance=...; ...`
- **含义**：发送客户端 Cookie，用于身份验证和会话跟踪。`cf_clearance` 是 Cloudflare 验证令牌。
- **脚本对比**：脚本的 Cookie 与浏览器部分相似，但 `cf_clearance` 和 `__vtins__3JpfN0uIRLmkKzss` 的值不同，表明 Cookie 已过期或不匹配。
- **问题**：Cookie 失效（尤其是 `cf_clearance`）会导致连接被拒绝。

### 9. `priority: u=0, i`
- **含义**：HTTP/3 优先级头，`u=0` 表示默认优先级，`i` 表示增量加载。
- **脚本对比**：脚本的 `Priority` 一致。
- **问题**：无。

### 10. `referer: https://hongxiuzhao.org/author/%e7%88%86%e7%82%b8%e5%b0%8f%e6%8b%bf%e9%93%81`
- **含义**：指示请求的来源页面 URL。
- **脚本对比**：脚本的 `Referer` 为 `https://hongxiuzhao.org/MjYOJrq.html`，不匹配。
- **问题**：不正确的 `Referer` 可能触发服务器验证失败。

### 11. `sec-ch-ua: "Chromium";v="140", "Not=A?Brand";v="24", "Microsoft Edge";v="140"`
- **含义**：提供浏览器标识（Chromium 140、Not A Brand 24、Microsoft Edge 140）。
- **脚本对比**：脚本的 `Sec-Ch-Ua` 一致。
- **问题**：无。

### 12. `sec-ch-ua-arch: "x86"`
- **含义**：指定 CPU 架构（x86）。
- **脚本对比**：脚本未设置。
- **问题**：缺少此头可能使请求看起来不像真实浏览器。

### 13. `sec-ch-ua-bitness: "64"`
- **含义**：指定 CPU 位数（64 位）。
- **脚本对比**：脚本未设置。
- **问题**：缺少此头可能影响验证。

### 14. `sec-ch-ua-full-version: "140.0.3485.66"`
- **含义**：提供浏览器的完整版本号。
- **脚本对比**：脚本未设置。
- **问题**：缺少版本信息可能被检测为异常。

### 15. `sec-ch-ua-full-version-list: "Chromium";v="140.0.7339.133", "Not=A?Brand";v="24.0.0.0", "Microsoft Edge";v="140.0.3485.66"`
- **含义**：提供所有浏览器的完整版本列表。
- **脚本对比**：脚本未设置。
- **问题**：缺少此头可能导致请求不完整。

### 16. `sec-ch-ua-mobile: ?0`
- **含义**：指示是否为移动设备（`?0` 表示非移动设备）。
- **脚本对比**：脚本一致。
- **问题**：无。

### 17. `sec-ch-ua-model: ""`
- **含义**：指定设备型号（空表示无特定型号）。
- **脚本对比**：脚本未设置。
- **问题**：缺少此头可能影响请求完整性。

### 18. `sec-ch-ua-platform: "Windows"`
- **含义**：指定操作系统（Windows）。
- **脚本对比**：脚本一致。
- **问题**：无。

### 19. `sec-ch-ua-platform-version: "10.0.0"`
- **含义**：指定操作系统版本（Windows 10）。
- **脚本对比**：脚本未设置。
- **问题**：缺少此头可能使请求不完整。

### 20. `sec-fetch-dest: document`
- **含义**：指示请求目标类型（HTML 页面）。
- **脚本对比**：脚本一致。
- **问题**：无。

### 21. `sec-fetch-mode: navigate`
- **含义**：指示请求模式（页面导航）。
- **脚本对比**：脚本一致。
- **问题**：无。

### 22. `sec-fetch-site: same-origin`
- **含义**：指示请求是否同源（来自同一域名）。
- **脚本对比**：脚本一致。
- **问题**：无。

### 23. `sec-fetch-user: ?1`
- **含义**：指示请求是否由用户交互触发（`?1` 表示用户导航）。
- **脚本对比**：脚本一致。
- **问题**：无。

### 24. `upgrade-insecure-requests: 1`
- **含义**：支持将 HTTP 请求升级到 HTTPS。
- **脚本对比**：脚本一致。
- **问题**：无。

### 25. `user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0`
- **含义**：标识浏览器和操作系统（Microsoft Edge 140 on Windows 10 64-bit）。
- **脚本对比**：脚本一致。
- **问题**：无。

## 问题总结
脚本与浏览器请求头的关键差异可能导致 `ConnectionResetError`：
1. **URL 不一致**：脚本请求 `/J5XM0nbM.html`，浏览器请求 `/MjYOJrq.html`。
2. **Cookie 失效**：`cf_clearance` 等 Cookie 已过期或不匹配。
3. **缺失头信息**：缺少 `sec-ch-ua-arch`、`sec-ch-ua-bitness`、`sec-ch-ua-full-version` 等。
4. **Referer 不匹配**：脚本的 `Referer` 与浏览器不同。
5. **Accept-Language 不完整**：脚本缺少部分语言选项。
6. **Cloudflare 保护**：`cf_clearance` 表明网站使用 Cloudflare，`requests` 无法处理动态挑战。

## 解决方案
以下是针对问题的修改建议：

### 1. 更新 INDEX_URL
```python
INDEX_URL = "https://hongxiuzhao.org/MjYOJrq.html"
```
- **原因**：确保请求正确的目录页 URL。

### 2. 更新 Cookie
- 从浏览器获取最新 Cookie，替换 `RAW_COOKIE`：
```python
RAW_COOKIE = '__51vcke__3JpfN0uIRLmkKzss=a88f497a-23b5-51cf-97ce-4fd7751785a1; __51vuft__3JpfN0uIRLmkKzss=1758552347647; _ga=GA1.1.866018080.1758552348; __51uvsct__3JpfN0uIRLmkKzss=2; __vtins__3JpfN0uIRLmkKzss=%7B%22sid%22%3A%20%2279ba7a2d-61cb-5614-a6d3-50721fb15b6f%22%2C%20%22vd%22%3A%2014%2C%20%22stt%22%3A%201959713%2C%20%22dr%22%3A%201608531%2C%20%22expires%22%3A%201758916850441%2C%20%22ct%22%3A%201758915050441%7D; cf_clearance=7YvI03gS4Cq90w42ZCoSxdUzl4qT520ejpwg9ho5alE-1758915045-1.2.1.1-DOw9QEAUN1bFnvC2BNGVLevNCAI8zsNuYnOnOn3CxaOl9_hzJ.E__gayxNYvPzSKfSZAocpfmLbhTTxPSKxexqDFVRjG8boMsdWykmStGOiPUQjBM2z.rYMV7QeBzFR6U7qL75PiDyX37jcJYC0womA91TlD8NmIlNg4adlxFtOblbAEoXXw1GuHocVq0Rcjz4CrOUR3YH7rJCteiVyckKbNP6ThngeX08Pr6PiG24TPeip273SGorSxqTSt3Y9R; _ga_MPYSL3RQH1=GS2.1.s1758913090$o2$g1$t1758915050$j59$l0$h0'
```
- **步骤**：
  1. 打开浏览器，访问 `https://hongxiuzhao.org/MjYOJrq.html`。
  2. 打开开发者工具（F12 → 网络 → 选择请求 → 复制 Cookie）。
  3. 更新脚本。

### 3. 更新 HEADERS
```python
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en,zh-CN;q=0.9,zh;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Referer': 'https://hongxiuzhao.org/author/%e7%88%86%e7%82%b8%e5%b0%8f%e6%8b%bf%e9%93%81',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Microsoft Edge";v="140"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Ch-Ua-Arch': 'x86',
    'Sec-Ch-Ua-Bitness': '64',
    'Sec-Ch-Ua-Full-Version': '140.0.3485.66',
    'Sec-Ch-Ua-Full-Version-List': '"Chromium";v="140.0.7339.133", "Not=A?Brand";v="24.0.0.0", "Microsoft Edge";v="140.0.3485.66"',
    'Sec-Ch-Ua-Model': '',
    'Sec-Ch-Ua-Platform-Version': '10.0.0',
    'Priority': 'u=0, i',
}
```

### 4. 使用 cloudscraper
- 安装：
  ```bash
  pip install cloudscraper
  ```
- 修改 `setup_session`：
  ```python
  import cloudscraper
  def setup_session():
      session = cloudscraper.create_scraper()
      session.headers.update(HEADERS)
      session.cookies.update(COOKIES)
      retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
      session.mount('http://', HTTPAdapter(max_retries=retries))
      session.mount('https://', HTTPAdapter(max_retries=retries))
      return session
  ```

### 5. 增加请求间隔
```python
DELAY_RANGE = (5.0, 10.0)
```

### 6. 添加日志
```python
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
```

### 7. 使用代理（可选）
```python
PROXIES = {
    'http': 'http://your_proxy:port',
    'https': 'https://your_proxy:port',
}
```

## 下一步
1. 更新 `INDEX_URL`、`RAW_COOKIE` 和 `HEADERS`，运行脚本。
2. 检查日志输出，分享新的错误信息（状态码、响应头等）。
3. 如果仍失败，尝试 `cloudscraper` 或 Selenium（需安装 ChromeDriver）。
4. 确保爬取行为符合网站条款和法律。