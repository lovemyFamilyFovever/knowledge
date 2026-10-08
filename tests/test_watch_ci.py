# -*- coding: utf-8 -*-
"""scripts/watch_ci.py 的行为回归 —— 四类「读不到」必须分开点名。

来历（2026-09-29）：用户让跑 watch_ci 查 CI 结果，脚本回一句
HTTP 0 读不到 run 列表 就退了。真因是它把代理 127.0.0.1:10810 写死在源码里，
而代理客户端当时**没监听**；同一天实测这台机直连 github.com 是通的
（git -c http.proxy= ls-remote origin main，1.16 秒拿到远端 tip）。
于是那句文案把「工具够不着 API」说成了听起来像「CI 有问题 / 没跑」——
而下一个人（或另一个 AI）会照着它去查 CI，而不是去查代理。本套钉住四件事：

  1. **代理不通自动改直连**，并把「走了直连」打在输出里；反证用服务端请求计数：
     代理那一趟根本到不了 API，直连那三趟（列表 / jobs / annotations）到了 —— 计数恰为 3
     （既不靠文案自证，也顺带证明降级没把每个端点请求两遍）；
  2. **显式直连时不得出现「已改直连」** —— 否则第 1 条的标记是句恒真的废话；
  3. **限流 / 两边都够不着 / 真没有 run / 200 但正文不是 JSON** 四种读不到走**不同退出码 + 不同文案**，
     且彼此的关键词互不出现在对方的输出里（分类互斥，这才叫分开点名）。
     第 4 类是 2026-09-29 推上去之后第一次实跑撞到的：走 CONNECT 代理时 `-D -`
     会把隧道应答一起吐进 stdout，正文里混着响应头 → 解析不出 JSON → 旧版 `d.get(...)` 直接崩栈；
  4. 降级之后**报告仍然完整**（run 号、job conclusion、annotation 一条都不能少），
     免得「能读到」退化成「只读到第一屏」；
  5. **钩子那侧的控制台是 GBK，不是我这台终端的 UTF-8**（轮次 50 实录：本套第一次进 pre-commit
     就被抓红 —— 子进程按 locale 编码中文、父侧按 utf-8 解码，「已改直连」这类标记全变成替换符；
     紧接着一条 FAIL 的详情把套件自己打印崩在 UnicodeEncodeError 上）。
     所以子进程出口编码显式钉 utf-8，本套自己的 stdout 走 errors=replace（H 组 + 对照组钉住）。

零外网：API 一律指向本进程的假 GitHub（现挑端口），「够不着」那组指向已关闭的端口。
运行：python tests/test_watch_ci.py
"""
import io
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "watch_ci.py"
SHA_SHORT = "deadbeef"
SHA_FULL = SHA_SHORT + "0" * (40 - len(SHA_SHORT))

# 控制台兜底（轮次 50 的实录）：本套件第一次进 pre-commit 就被钩子抓红 —— 钩子那侧的控制台是
# GBK，而一条 FAIL 的详情里带着解码失败的替换符 \ufffd，`print` 自己炸成 UnicodeEncodeError，
# 于是"报名"这件事把套件崩了、门禁只看到一个 rc=1（同 §6 第 46 行那一族）。
# 编不出来就替换，绝不抛 —— 与 tests/_ci.py::_safe、scripts/check_ledger_counts.py 同口径。
try:
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except Exception:
    pass

passed = failed = 0


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print("  PASS " + name)
    else:
        failed += 1
        print("  FAIL " + name + " " + str(extra))


def closed_port():
    """绑一个端口再立刻释放 —— 拿「必然连不上」的代理/API 地址用。"""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


RUN = {"run_number": 99, "head_sha": SHA_FULL, "status": "completed",
       "conclusion": "success", "id": 7}
JOBS = {"jobs": [{"name": "gate", "conclusion": "success", "id": 9,
                  "steps": [{"number": 1, "name": "Run tests", "conclusion": "success"}]}]}
ANN = [{"annotation_level": "notice", "message": "reader STARTED"}]

STATE = {"mode": "ok", "hits": [], "reset": 0}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, payload, headers=None, raw=None):
        body = raw if raw is not None else json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        STATE["hits"].append(self.path)
        m = STATE["mode"]
        p = self.path
        if m == "ratelimited":
            self._send(403, None, headers={"x-ratelimit-reset": str(STATE["reset"])},
                       raw=b'{"message":"API rate limit exceeded for IP"}')
            return
        if m == "html":
            # 2026-09-29 真机形状：走 CONNECT 代理时 curl 的 `-D -` 会把隧道应答
            # "HTTP/1.1 200 Connection established" 一起吐进 stdout，头部/正文的切分点
            # 落在错位置 → 正文里混着响应头，JSON 解析失败。旧版此时 st 仍是 200，
            # 于是 `d.get("workflow_runs")` 直接 AttributeError 崩栈（退出码 1、零句人话）。
            self._send(200, None, raw=b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n<html>proxy ate it</html>")
            return
        # 按子串匹配 —— KB_CI_API 里带着 /repos/o/r 前缀，路径不是从根开始的
        if "/annotations" in p:
            self._send(200, ANN)
        elif "/jobs" in p:
            self._send(200, JOBS)
        elif "/actions/runs" in p:
            runs = [RUN] if m != "noruns" else [dict(RUN, head_sha="a" * 40)]
            self._send(200, {"total_count": len(runs), "workflow_runs": runs})
        else:
            self._send(404, {"message": "no such route"})


def serve():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def run_script(api, proxy, budget="2"):
    env = dict(os.environ)
    env["KB_CI_API"] = api
    env["KB_CI_PROXY"] = proxy          # 空串 = 不要代理
    # 必须显式钉住子进程的出口编码：钩子那侧没设 PYTHONIOENCODING，脚本往管道里打印时
    # Python 按 locale（GBK）编码中文，而这里按 utf-8 解码 —— 结果「已改直连」这类中文标记
    # 全部变成替换符，断言就在钩子里红、在我这台终端里绿（轮次 50 提交被这条抓下来）。
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, str(SCRIPT), SHA_SHORT, budget],
                       cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env=env, timeout=180)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    if not SCRIPT.is_file():
        print("SKIP watch_ci: " + str(SCRIPT) + " 不存在")
        return 0
    if subprocess.run(["curl", "--version"], capture_output=True).returncode != 0:
        print("SKIP watch_ci: 本机没有 curl")
        return 0

    srv, port = serve()
    api_ok = "http://127.0.0.1:%d/repos/o/r" % port
    dead = closed_port()

    print("== A：代理不通 -> 自动改直连，且报告完整 ==")
    STATE.update(mode="ok", hits=[])
    rc, out = run_script(api_ok, "http://127.0.0.1:%d" % dead)
    check("A1 代理不通时退出码仍为 0（没把工具故障当结论）", rc == 0, "rc=%s %s" % (rc, out[:200]))
    check("A2 输出点名「已改直连」", "已改直连" in out, out[:200])
    check("A3 假 API 恰好收到 3 次请求（代理那趟没到，降级也没重复请求）",
          len(STATE["hits"]) == 3, "hits=%s" % STATE["hits"])
    check("A4 第一趟打的是 run 列表端点",
          bool(STATE["hits"]) and "/actions/runs?" in STATE["hits"][0]
          and "/jobs" not in STATE["hits"][0],
          "hits=%s" % STATE["hits"])
    check("A5 降级后仍报出 run 号与结论", "#99" in out and "success" in out, out[:300])
    check("A6 降级后 annotation 照旧回显", "reader STARTED" in out, out[-300:])

    print("== B：显式直连（没配代理）不得谎报「已改直连」 ==")
    STATE.update(mode="ok", hits=[])
    rc, out = run_script(api_ok, "")
    check("B1 直连可用时退出码 0", rc == 0, "rc=%s %s" % (rc, out[:200]))
    check("B2 未发生降级就不出现「已改直连」（A2 的恒真护栏）", "已改直连" not in out, out[:200])
    check("B3 直连确实到达了 API（同样 3 趟）", len(STATE["hits"]) == 3, "hits=%s" % STATE["hits"])

    print("== C：限流必须说成限流 ==")
    STATE.update(mode="ratelimited", hits=[], reset=int(time.time()) + 900)
    rc, out = run_script(api_ok, "http://127.0.0.1:%d" % dead)
    check("C1 限流走专属退出码 3", rc == 3, "rc=%s %s" % (rc, out[:200]))
    check("C2 文案含「限流」", "限流" in out, out[:200])
    check("C3 文案带出配额重置时刻", bool(re.search(r"\d{1,2}:\d{2}", out)), out[:250])
    check("C4 限流不得被读成「没有 run」", "没有" not in out, out[:250])
    check("C5 限流也不得被读成「够不着」", "够不着" not in out, out[:250])

    print("== D：真没有 run（CI 确实还没跑）==")
    STATE.update(mode="noruns", hits=[])
    rc, out = run_script(api_ok, "")
    check("D1「没有 run」走专属退出码 5", rc == 5, "rc=%s %s" % (rc, out[:200]))
    check("D2 文案里带着查的 sha", SHA_SHORT in out, out[:200])
    check("D3 说的是 run 列表里没有它", "没有" in out, out[:200])
    check("D4 此路不报限流", "限流" not in out, out[:200])

    print("== E：代理与直连都够不着 ==")
    rc, out = run_script("http://127.0.0.1:%d/repos/o/r" % closed_port(),
                         "http://127.0.0.1:%d" % dead)
    check("E1 两边都不通走专属退出码 4", rc == 4, "rc=%s %s" % (rc, out[:200]))
    check("E2 文案含「够不着」", "够不着" in out, out[:250])
    check("E3 此路不谎报限流", "限流" not in out, out[:250])
    check("E4 此路不谎报「没有 run」（读不到不等于没有）", "没有" not in out, out[:250])

    print("== I：HTTP 200 但正文不是 JSON（真机第一次 push 就撞上的形状）==")
    STATE.update(mode="html", hits=[])
    rc, out = run_script(api_ok, "")
    check("I1 200+坏正文走专属退出码 6（既不是崩栈也不是通用读不到）", rc == 6,
          "rc=%s %s" % (rc, out[:250]))
    check("I2 文案含「不是 JSON」", "不是 JSON" in out, out[:250])
    check("I3 不许崩栈 —— 输出里没有 Traceback", "Traceback" not in out, out[:250])
    check("I4 此路不谎报限流", "限流" not in out, out[:250])
    check("I5 此路不谎报「没有 run」", "没有" not in out, out[:250])
    check("I6 此路不谎报「够不着」（连接其实是通的）", "够不着" not in out, out[:250])

    print("== F：形态断言（不靠跑出来、但会被忘掉的那几条）==")
    src = SCRIPT.read_text(encoding="utf-8")
    check("F1 代理地址可由 KB_CI_PROXY 覆盖（不许再写死）", "KB_CI_PROXY" in src)
    check("F2 API 地址可由 KB_CI_API 覆盖（本套的零外网前提）", "KB_CI_API" in src)
    check("F3 每次 curl 都带 --max-time（读不到要限时退，不能挂住）", src.count("--max-time") >= 1)
    check("F4 响应头单独取（-D 指到文件），不许与正文共用一条 stdout",
          '"-D", "-"' not in src and "-D" in src, "还在用 -D -（隧道应答会混进正文）")

    print("== G：控制组 —— 假 API 自己得是可信的 ==")
    STATE.update(mode="ok", hits=[])
    got = json.loads(subprocess.run(
        ["curl", "-s", "--noproxy", "*", api_ok + "/actions/runs?per_page=3"],
        capture_output=True, text=True, encoding="utf-8", errors="replace").stdout)
    check("G1 桩按预期回 run 列表", got.get("total_count") == 1
          and got["workflow_runs"][0]["head_sha"] == SHA_FULL, str(got)[:200])
    check("G2 桩记录了请求（A3/B3 的计数不是编的）", len(STATE["hits"]) == 1,
          "hits=%s" % STATE["hits"])

    print("== H：钩子那侧的控制台是 GBK（轮次 50 第一次进 pre-commit 就是被这条抓红的）==")
    os.environ["PYTHONIOENCODING"] = "gbk"          # 模拟钩子环境；run_script 必须盖过它
    STATE.update(mode="ok", hits=[])
    rc, out = run_script(api_ok, "http://127.0.0.1:%d" % dead)
    check("H1 外层 GBK 时中文标记仍读得出来（子进程出口编码被钉死）",
          rc == 0 and "已改直连" in out, "rc=%s %s" % (rc, out[:200]))
    check("H2 换编码没换出重试（依旧恰好 3 趟）", len(STATE["hits"]) == 3,
          "hits=%s" % STATE["hits"])
    os.environ.pop("PYTHONIOENCODING", None)
    boom = False
    try:
        strict = io.TextIOWrapper(io.BytesIO(), encoding="gbk", errors="strict")
        strict.write("解码失败的替换符在这里 \ufffd")
        strict.flush()
    except UnicodeEncodeError:
        boom = True
    check("H3 对照组：不兜底的 GBK 打印确实会炸（H4 的护栏不是空转）", boom)
    check("H4 本套件自己的 stdout 是 errors=replace —— 报名不许把自己崩掉",
          getattr(sys.stdout, "errors", "") == "replace",
          repr(getattr(sys.stdout, "errors", "")))

    srv.shutdown()
    print("\n%d passed, %d failed" % (passed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
