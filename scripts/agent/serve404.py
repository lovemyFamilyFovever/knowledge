"""GitHub Pages 本机模拟器：以第二参数为文档根，把 <某前缀>/404.html 当作该前缀下的
404 回落页（GH Pages SUBDIRECTORY 部署的行为），用来验深链与 kb-static.js 的路由桥。
一次性诊断工具，放在 .qa/（不进 git）。用法：python .qa/serve404.py <端口> <文档根>
"""
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = None


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    # Windows 的注册表把 .js 映射成 text/plain，Chrome 会**拒绝执行**（strict MIME），
    # 于是本机验 PWA 时 SW 永远注册不上 —— 这里按 GH Pages 的实际口径钉死类型。
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".js": "application/javascript",
        ".css": "text/css",
        ".json": "application/json",
        ".webmanifest": "application/manifest+json",
        ".html": "text/html",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".woff2": "font/woff2",
    }

    def send_error(self, code, message=None, explain=None):
        """404 时若该 URL 的第一段前缀下有 404.html，就用它当正文（状态仍是 404）。"""
        if code == 404:
            path = self.path.split("?", 1)[0].split("#", 1)[0].strip("/")
            if path:
                fallback = os.path.join(ROOT, path.split("/")[0], "404.html")
                if os.path.isfile(fallback):
                    with open(fallback, "rb") as fh:
                        body = fh.read()
                    self.send_response(404)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    if self.command != "HEAD":
                        self.wfile.write(body)
                    return
        super().send_error(code, message, explain)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8112
    ROOT = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(".qa", "serve-root"))
    print("serving", ROOT, "on", port, flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
