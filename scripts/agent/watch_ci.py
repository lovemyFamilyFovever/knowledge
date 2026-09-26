# -*- coding: utf-8 -*-
"""盯 GitHub Actions 到结论：run 状态 → 逐步 conclusion → annotations。

用法：`python scripts/agent/watch_ci.py <sha 前缀> [等待秒数=420]`（push 走代理时本脚本也走）。
为什么要有它（台账 §6 第 47 行）：CI 一步绿有两种含义 —— 真跑了断言，或者自探测失败打了 SKIP；
而匿名 API 读不到日志正文（/logs 与日志 zip 都 404），**能读的只有 jobs 的逐步 conclusion 与 annotations**，
所以本脚本固定回这两样。第二条纪律（§6 第 48 行）：403 限流必须单独报，绝不把"读不到"说成"没有 run"；
匿名配额 60 次/小时且按出口 IP 计算，轮询默认 75s 一轮、只在未完成时继续。
"""
import json
import subprocess
import sys
import time

PROXY = ["--proxy", "http://127.0.0.1:10810"]
API = "https://api.github.com/repos/lovemyFamilyFovever/knowledge"
SHA = sys.argv[1]
BUDGET = int(sys.argv[2]) if len(sys.argv) > 2 else 420


def get(path):
    """回 (HTTP 码, 解析结果)。状态码必须分路报 —— 把 403 读成"没有 run"是本轮踩过的坑。"""
    r = subprocess.run(["curl", "-s", "-w", "\n%{http_code}"] + PROXY + [API + path],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    body, _, code = (r.stdout or "").rpartition("\n")
    try:
        st = int(code.strip())
    except ValueError:
        st = 0
    if st != 200:
        return st, None
    try:
        return st, json.loads(body or "{}")
    except Exception:
        return st, None


end = time.time() + BUDGET
hit = None
while True:
    st, d = get("/actions/runs?per_page=3")
    if st == 403:
        print("403 匿名 API 限流（按出口 IP 60 次/小时）—— 不是没有 run，稍后再跑")
        sys.exit(3)
    if st != 200:
        print(f"HTTP {st} 读不到 run 列表")
        sys.exit(4)
    hit = next((r for r in d.get("workflow_runs", []) if r["head_sha"].startswith(SHA)), None)
    if hit is None:
        print(f"最近 3 个 run 里没有 {SHA}")
        sys.exit(5)
    print(f"#{hit['run_number']} {hit['head_sha'][:7]} {hit['status']} {hit.get('conclusion')}", flush=True)
    if hit["status"] == "completed" or time.time() >= end:
        break
    time.sleep(75)

if hit["status"] != "completed":
    print("仍在跑，稍后重跑本脚本")
    sys.exit(2)

st, jobs = get(f"/actions/runs/{hit['id']}/jobs")
if st != 200:
    print(f"HTTP {st} 读不到 jobs")
    sys.exit(4)
for j in jobs.get("jobs", []):
    steps = j.get("steps", [])
    bad = [f"#{s['number']} {s['name'][:40]} -> {s['conclusion']}"
           for s in steps if s.get("conclusion") not in (None, "success")]
    print(f"job {j['name']}: {j.get('conclusion')}，{len(steps)} 步，非 success：", bad or "无")
    st, ann = get(f"/check-runs/{j['id']}/annotations")
    if st != 200:
        print(f"  HTTP {st} 读不到 annotations")
        continue
    items = ann if isinstance(ann, list) else (ann or {}).get("annotations", [])
    for a in items:
        m = a.get("message", "")
        if "Node.js 20" in m:
            continue
        print(f"  [{a.get('annotation_level')}] {m}")
