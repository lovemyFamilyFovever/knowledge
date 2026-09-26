# -*- coding: utf-8 -*-
"""自探测型套件的**可见性**：SKIP、STARTED、以及失败与崩溃都要报名（轮次 37 + 轮次 39）。

为什么要有它：`test_js_props` / `test_ui_behavior` / `test_ui_regress` / `test_rag` 都是
「缺依赖就打 SKIP 然后返回 0」—— 这是刻意的（钩子挂 = 没有钩子），但同一个 0 让 CI 的绿有了
两种含义：**真跑了 360 条断言**，还是**一条都没跑**。而 GitHub 的匿名 API 读不到日志正文
（`/logs` 与日志 zip 都要登录），事后无法从 run 反推。GitHub Actions 的 **annotation** 是
公开 API 可读的（`GET /repos/<o>/<r>/check-runs/<id>/annotations`），所以把状态打成 annotation。

轮次 37 打的是「跑没跑」：`::notice::<suite> STARTED` + `::warning::<suite> SKIPPED reason=<码>`。
轮次 39 补的是另一半 —— **失败更要报名**：run #46 红在第 18 步，匿名 API 能看到的只有
一句 `Process completed with exit code 1`，没有断言名、没有异常类型，谁也无法判断是真回归还是
runner 抖动（台账 §6 第 53 行的勘误块记的就是这次查案的无力）。现在：
  · `check()` 判红 → `::error::<suite> FAILED #<序号> <断言名>`（只报前 `_MAX_FAIL_ANN` 条，
    annotation 多了会被 GitHub 截断，且会把人淹死）；
  · 未捕获异常（那正是 #46 的形状）→ `::error::<suite> ABORTED <异常类型> at <file:line> <消息>`，
    **打完照样往上抛**，步骤该红还是红，只是从此可诊断。

三条纪律（改这个文件前必读）：
  1. 只在 `GITHUB_ACTIONS=true` 时才打：本地跑测试的 stdout 必须干净（`test_js_props` 还要解析
     自己 stdout 里的 JSON）。
  2. SKIPPED 的 `reason=` 走 ASCII 短码（属性位置容不下中文与空格）；**FAILED/ABORTED 的正文
     允许中文** —— 因为作业级 `PYTHONIOENCODING=utf-8` 已在 §6 第 46 行修好后设上了，
     而这里再兜一层：编码失败就退回 ASCII 化，绝不让"报名"这件事本身把测试崩掉（§6 第 46 行的教训）。
  3. workflow command 的正文必须转义 `%`、CR、LF，否则 `%` 之后的内容会被当属性解析掉。
"""
import os
import re
import sys
import traceback

_ASCII = re.compile(r"[^A-Za-z0-9_.-]+")
_MAX_FAIL_ANN = 8          # 每套最多报 8 条失败断言名（GitHub 对 annotation 也有上限）
_SUITE = ""                # started()/guarded() 记下当前套件名，供 failed() 用
_failed_ann = 0            # 已报出的 FAILED annotation 数
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _on_actions() -> bool:
    return os.environ.get("GITHUB_ACTIONS", "").lower() == "true"


def _code(text: str) -> str:
    """把原因压成 ASCII 短码；纯中文原因会塌成空串，此时回退 unspecified。"""
    return (_ASCII.sub("", text).strip() or "unspecified")[:60]


def _msg(text: str, limit: int = 200) -> str:
    """annotation 正文：转义 workflow command 的保留字符，兜住编码问题，再截断。"""
    s = str(text).replace("%", "%25").replace("\r", "%0D").replace("\n", " ")
    return s[:limit]


def _emit(level: str, body: str) -> None:
    if not _on_actions():
        return
    line = f"::{level}::{body}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:                 # 控制台编码不吃中文时：退回 ASCII，绝不崩在这里
        print(line.encode("ascii", "ignore").decode(), flush=True)


def started(suite: str) -> None:
    """依赖齐了、真要跑：记下套件名并留一行正证据。"""
    global _SUITE
    _SUITE = suite
    _emit("notice", f"{suite} STARTED")


def skipped(suite: str, code: str, reason: str = "") -> None:
    """只登记"这一支没跑"（套件里局部跳过时用，不接管退出码）。"""
    _emit("warning", f"{suite} SKIPPED reason={_code(code)}")


def skip(suite: str, code: str, reason: str) -> int:
    """整套 SKIP：打人类可读的中文行 + annotation，返回 0 供调用方 `return`。"""
    print(reason)
    skipped(suite, code)
    return 0


def failed(name: str) -> None:
    """一条断言判红。由各套件的 check() 调用；只在 Actions 上产生 annotation，本地零噪声。"""
    global _failed_ann
    if not _on_actions() or _failed_ann >= _MAX_FAIL_ANN:
        return
    _failed_ann += 1
    more = "" if _failed_ann < _MAX_FAIL_ANN else "（后续失败不再逐条报名）"
    _emit("error", f"{_SUITE or '?'} FAILED #{_failed_ann} {_msg(name)}{more}")


def guarded(fn, suite: str = ""):
    """包一层 main()：未捕获异常先报名再原样抛出。

    #46 那次红就是这条形状 —— 崩在半路（20s 退出），步骤只留下 `exit code 1`。
    报出**异常类型 + 抛出点 + 消息**，红才有机会被远程读懂；抛出去保证判定不变（该红还是红）。
    """
    global _SUITE
    if suite:
        _SUITE = suite
    try:
        return fn()
    except SystemExit:
        raise                                   # 测试自己的 sys.exit(0/1) 不算崩溃
    except BaseException as e:                  # noqa: BLE001  报名后必须原样上抛
        frames = [f for f in traceback.extract_tb(e.__traceback__) if f.filename.startswith(ROOT)]
        where = (f"{os.path.relpath(frames[-1].filename, ROOT)}:{frames[-1].lineno}" if frames else "?")
        where = where.replace(os.sep, "/")   # CI 日志与台账里一律正斜杠
        _emit("error", f"{_SUITE or '?'} ABORTED {type(e).__name__} at {where} {_msg(e)}")
        raise
