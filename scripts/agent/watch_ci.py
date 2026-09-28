# -*- coding: utf-8 -*-
"""盯 GitHub Actions 到结论：run 状态 → 逐步 conclusion → annotations。

用法：`python scripts/agent/watch_ci.py <sha 前缀> [等待秒数=420]`
环境变量（`tests/test_watch_ci.py` 靠这三个把本脚本指到本进程的假 GitHub，零外网）：
  `KB_CI_PROXY`    代理地址，缺省 `http://127.0.0.1:10810`；**传空串 = 从头就直连**。
  `KB_CI_API`      API 根，缺省本仓。
  `KB_CI_MAX_TIME` 单次 curl 的限时秒数，缺省 25。

为什么要有它（台账 §6 第 47 行）：CI 一步绿有两种含义 —— 真跑了断言，或者自探测失败打了 SKIP；
而匿名 API 读不到日志正文（/logs 与日志 zip 都 404），**能读的只有 jobs 的逐步 conclusion 与 annotations**，
所以本脚本固定回这两样。第二条纪律（§6 第 48 行）：403 限流必须单独报，绝不把"读不到"说成"没有 run"；
匿名配额 60 次/小时且按出口 IP 计算，轮询默认 75s 一轮、只在未完成时继续。

第三条纪律（2026-09-29 补，由 `tests/test_watch_ci.py` 钉着）：**"读不到"有三种，分开点名**——
① 代理与直连都够不着（工具/网络问题，退出 4）② 匿名配额限流（退出 3，并报恢复时刻）
③ API 正常但列表里没有这个 sha（CI 真没跑到，退出 5）。
旧版把代理写死、代理一不通就回一句 `HTTP 0 读不到 run 列表` 然后退，于是"我的脚本连不上"
听起来像"CI 有问题"—— 而当天实测这台机 10810 没监听时**直连是通的**
（`git -c http.proxy= ls-remote origin main` 1.16 秒拿到远端 tip）。所以现在多一层：
**代理不通自动改直连重试一次**，并在输出里点名降级发生过（只在真发生时打，防恒真）。
"""
import datetime
import json
import os
import subprocess
import sys
import time

PROXY = os.environ.get("KB_CI_PROXY", "http://127.0.0.1:10810")
API = os.environ.get("KB_CI_API",
                     "https://api.github.com/repos/lovemyFamilyFovever/knowledge")
MAX_TIME = os.environ.get("KB_CI_MAX_TIME", "25")
SHA = sys.argv[1]
BUDGET = int(sys.argv[2]) if len(sys.argv) > 2 else 420
FELL_BACK = False          # 是否发生过"代理不通 -> 降级直连"；只在真发生时点名一次


def _split(raw):
    """把 curl 的 `-D -` 输出切成（响应头块, 正文）。切不出来 = 这趟谁都没答。"""
    for sep in ("\r\n\r\n", "\n\n"):
        i = raw.find(sep)
        if i >= 0:
            return raw[:i], raw[i + len(sep):]
    return None, None


def _curl(path, proxy):
    """一趟 curl。回 (HTTP 码, json 或 None, 头字典)；码 0 = 连都没连上。"""
    cmd = ["curl", "-s", "-D", "-", "--max-time", str(MAX_TIME)]
    cmd += ["--proxy", proxy] if proxy else ["--noproxy", "*"]   # 直连得是真的直连，不吃环境代理
    cmd += ["-w", "\n%{http_code}", API + path]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    head, rest = _split(r.stdout or "")
    if head is None:
        return 0, None, {}
    body, _, code = rest.rpartition("\n")
    try:
        st = int(code.strip())
    except ValueError:
        st = 0
    hdr = {}
    for line in head.splitlines():
        k, sep, v = line.partition(":")
        if sep and k.strip():
            hdr[k.strip().lower()] = v.strip()
    data = None
    if st == 200:
        try:
            data = json.loads(body or "{}")
        except Exception:
            data = None
    return st, data, hdr


def get(path):
    """回 (码, json, 走了哪条路, 头)。代理不通时自动直连重试一次；两条都不通才是码 0。"""
    global FELL_BACK
    if not PROXY:
        st, d, h = _curl(path, None)
        return st, d, "direct", h
    st, d, h = _curl(path, PROXY)
    if st:                       # 代理拿到了真实 HTTP 码（含 403/404）就别换路
        return st, d, "proxy", h
    st2, d2, h2 = _curl(path, None)
    FELL_BACK = True
    if st2:
        return st2, d2, "direct（代理不通已降级）", h2
    return 0, None, "proxy+direct 两趟都没答", h2


def reset_text(hdr):
    """把 x-ratelimit-reset 换成本地时刻；头里没有就直说未知，不编一个时间给人等。"""
    raw = hdr.get("x-ratelimit-reset")
    if not raw:
        return "恢复时刻未知"
    try:
        t = datetime.datetime.fromtimestamp(int(raw))
    except (ValueError, OSError):
        return "恢复时刻未知"
    return "配额 %02d:%02d 恢复" % (t.hour, t.minute)


def die(msg, code):
    print(msg, flush=True)
    sys.exit(code)


end = time.time() + BUDGET
hit = None
while True:
    st, d, via, hdr = get("/actions/runs?per_page=3")
    if FELL_BACK and st == 200:
        print("（代理 %s 不通，已改直连）" % PROXY, flush=True)
    if st == 403:
        die("匿名 API 限流（按出口 IP 60 次/小时，本轮走 %s）—— %s；这是工具读不到，不是 CI 的结论"
            % (via, reset_text(hdr)), 3)
    if st == 0:
        die("代理（%s）与直连都够不着 API —— 工具/网络问题，与 CI 结果无关；先修这条路再来读结论"
            % (PROXY or "未配置"), 4)
    if st != 200:
        die("HTTP %s 读不到 run 列表（走 %s）—— 这是 API 的回话，仍不是 CI 的结果" % (st, via), 4)
    hit = next((r for r in d.get("workflow_runs", []) if r["head_sha"].startswith(SHA)), None)
    if hit is None:
        die("最近 3 个 run 里没有 %s —— API 是通的，是 CI 真的还没跑到这个 sha" % SHA, 5)
    print(f"#{hit['run_number']} {hit['head_sha'][:7]} {hit['status']} {hit.get('conclusion')}", flush=True)
    if hit["status"] == "completed" or time.time() >= end:
        break
    time.sleep(75)

if hit["status"] != "completed":
    print("仍在跑，稍后重跑本脚本")
    sys.exit(2)

st, jobs, via, hdr = get("/actions/runs/%s/jobs" % hit["id"])
if st == 403:
    die("读 jobs 时被限流 —— %s" % reset_text(hdr), 3)
if st != 200:
    die("HTTP %s 读不到 jobs（走 %s）" % (st, via), 4)
for j in jobs.get("jobs", []):
    steps = j.get("steps", [])
    bad = [f"#{s['number']} {s['name'][:40]} -> {s['conclusion']}"
           for s in steps if s.get("conclusion") not in (None, "success")]
    print(f"job {j['name']}: {j.get('conclusion')}，{len(steps)} 步，非 success：", bad or "无")
    st, ann, via2, hdr2 = get("/check-runs/%s/annotations" % j["id"])
    if st != 200:
        print(f"  HTTP {st} 读不到 annotations（走 {via2}）—— 这一步的结论仍以上面那行为准")
        continue
    items = ann if isinstance(ann, list) else (ann or {}).get("annotations", [])
    for a in items:
        m = a.get("message", "")
        if "Node.js 20" in m:
            continue
        print(f"  [{a.get('annotation_level')}] {m}")
