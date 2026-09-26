# -*- coding: utf-8 -*-
"""自探测型套件的 SKIP 可见性（轮次 37；台账 §6 第 46 行留下的口子）。

问题：`test_js_props` / `test_ui_behavior` / `test_ui_regress` / `test_rag` 都是
「缺依赖就打 SKIP 然后返回 0」——这是刻意的（钩子挂 = 没有钩子）。但同一个 0 让
CI 的绿有了两种完全不同的含义：**真跑了 360 条断言**，还是**一条都没跑**。
而 GitHub 的匿名 API 读不到日志正文（`/logs` 与日志 zip 都 404），事后没法从 run 反推。

修法：SKIP 时多打一行 GitHub Actions workflow command（`::warning::`），它会变成 run 页上的
**annotation**，而 annotation 是公开 API 可读的
（`GET /repos/<o>/<r>/check-runs/<id>/annotations`）。真跑起来时再打一行 `::notice::… STARTED`，
于是"这一步到底跑没跑"在 API 里有**正证据**，不靠"没有报错"反推。

两条纪律（改这个文件前必读）：
  · annotation 正文**纯 ASCII**：runner 的默认控制台是 cp1252，中文 print 正是 §6 第 46 行
    把 CI 崩红的那把刀；人类可读的中文原因照旧走普通 print。
  · 只在 `GITHUB_ACTIONS=true` 时才打：本地跑测试不该被 `::` 噪声污染 stdout
    （`test_js_props` 的调用方会解析 stdout 里的 JSON）。
"""
import os
import re

_ASCII = re.compile(r"[^A-Za-z0-9_.-]+")


def _on_actions() -> bool:
    return os.environ.get("GITHUB_ACTIONS", "").lower() == "true"


def _code(text: str) -> str:
    """把原因压成 ASCII 短码；纯中文原因会塌成空串，此时回退 unspecified。"""
    return (_ASCII.sub("", text).strip() or "unspecified")[:60]


def started(suite: str) -> None:
    """依赖齐了、真要跑：留一行正证据。"""
    if _on_actions():
        print(f"::notice::{suite} STARTED", flush=True)


def skipped(suite: str, code: str, reason: str = "") -> None:
    """只登记"这一支没跑"（套件里局部跳过时用，不接管退出码）。"""
    if _on_actions():
        print(f"::warning::{suite} SKIPPED reason={_code(code)}", flush=True)


def skip(suite: str, code: str, reason: str) -> int:
    """整套 SKIP：打人类可读的中文行 + annotation，返回 0 供调用方 `return`。"""
    print(reason)
    skipped(suite, code)
    return 0
