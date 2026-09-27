# -*- coding: utf-8 -*-
"""批量查漏补缺（切片 4）：先预估、再异步跑、前端轮询进度。

三条硬约束（每条都在 tests/test_ai_batch.py 里锁着）：

1. **预估零出站**。`estimate` 只读本地语料 + 跑本地判据 —— 它必须知道"有几篇真的需要问
   AI"才谈得上估算调用数，而这件事本地就能算出来，一次 fetch 都不该发。
2. **长任务绝不挂在一次 fetch 上**。`start` 立刻返回作业快照，真正的扫描在 daemon 线程里跑，
   前端靠 `/api/ai/batch/status` 轮询。（同台账 §6 第 3 行那次 `/api/rag` 首次 71.8s 阻塞的教训。）
3. **预算帽是硬门**。预估调用数超过本月剩余额度时，带 AI 的批量一律不开；
   纯本地批量（零调用）不受限 —— 它不出网，就没有"超支"这回事。

字数 → token 的换算刻意**取高不取低**（中文实际多半 1 字 < 1 token）：
预估偏低的代价是账单吓人，偏高的代价只是少问几篇，两者不对等。
"""
from __future__ import annotations

import threading
import time

# 一次批量的硬上限：防手滑（scope 写错 = 全库）。真扫更多请分批。
MAX_DOCS = 500
# 单篇正文的字节上限，与 explain 的 400KB 同口径（超了直接跳过，不拖垮整批）。
MAX_DOC_BYTES = 400_000
# token 粗估系数：1 字 ≈ 1 token（取高），外加每次调用的固定开销（系统提示 + schema）。
TOKENS_PER_CHAR = 1.0
PROMPT_OVERHEAD_TOKENS = 900
# 单次回答的字数上限（与 ai_audit 里 terms≤8 的量级相称），估的是输出侧。
EST_OUT_TOKENS = 320


class BatchBusy(Exception):
    """已有一个批量在跑 —— 一次只允许一个，两个线程抢同一份派生库没有意义。"""


def needs_ai(proposals: list) -> bool:
    """这批本地判据里有没有"只有 AI 能答"的那几类。"""
    return any(p.get("needs_ai") for p in proposals)


def estimate(items: list, *, budget_left, price_in_per_1k: float = 0.0,
             price_out_per_1k: float = 0.0, sample: dict | None = None) -> dict:
    """把逐篇扫出来的结果汇总成一份**开跑前**的估算。

    items: [{"path", "bytes", "count", "need_ai"}] —— 由调用方跑本地判据得到（零出站）。
    budget_left: 本月还剩多少次调用额度（None = 没设预算帽；0 = 已用尽）。
    sample: {"from": 总篇数, "measured": 实扫篇数} —— 大范围的本地判据要读全盘，
            那种规模下只抽样，报数按抽样放大，并如实标 sampled。
            **放大出来的数用来给用户看花费；拦钱包的判据用不上它**（见 calls_upper_bound）。
    """
    docs = len(items)
    measured = docs
    scale = 1
    if sample:
        docs = int(sample.get("from") or 0) or docs
        measured = int(sample.get("measured") or 0) or docs
        scale = docs / measured if measured else 1

    def grow(n):
        return int(n) if scale == 1 else int(round(n * scale))

    need = [it for it in items if it.get("need_ai")]
    chars = sum(int(it.get("bytes") or 0) for it in need)
    findings = grow(sum(int(it.get("count") or 0) for it in items))
    # 精确扫过时 calls == 上限；抽样时 calls 是放大值，可能偏低 ——
    # 所以过不过帽看**上限**（每篇都可能问一次），花费看放大值（给人看的预算感）。
    calls = grow(len(need)) if scale == 1 else min(docs, grow(len(need)))
    upper = docs if scale != 1 else calls
    tokens_in = int(chars * TOKENS_PER_CHAR * (scale if sample else 1)) \
        + calls * PROMPT_OVERHEAD_TOKENS
    tokens_out = calls * EST_OUT_TOKENS
    return {
        "docs": docs,
        "docs_with_findings": grow(len([it for it in items if it.get("count")])),
        "findings": findings,
        "docs_needing_ai": calls,
        "calls_expected": calls,
        "calls_upper_bound": upper,
        "sampled": bool(sample),
        "sample": sample or None,
        "tokens_in_est": tokens_in,
        "tokens_out_est": tokens_out,
        "cost_est": round(tokens_in / 1000.0 * float(price_in_per_1k or 0)
                          + tokens_out / 1000.0 * float(price_out_per_1k or 0), 4),
        "budget_left": budget_left,
        "over_budget": budget_left is not None and upper > max(0, int(budget_left)),
        "truncated": docs > MAX_DOCS,
        # 一次批量真正会扫的篇数（上限是 MAX_DOCS）：估算报的是"整个范围多少篇"，
        # 而作业只会跑前 MAX_DOCS 篇 —— 两个数都摆出来，别让人以为 2000 篇全跑了。
        "will_scan": min(docs, MAX_DOCS),
        "per_doc_calls": 1,
    }


class BatchJob:
    """一个批量作业的可变状态。所有读经 `snapshot()`，所有写经内部方法。"""

    def __init__(self, scope: dict, total: int):
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self.scope = dict(scope or {})
        self.total = int(total)
        self.state = "queued"          # queued / running / done / stopped / failed
        self.done = 0
        self.current = ""
        self.findings = 0
        self.ai_calls = 0
        self.ai_stopped_reason = ""
        # 收尾的域全景复核：跑没跑、挑中几个、没跑的原因
        self.gap_review = {"ran": False, "picked": 0, "total": 0, "reason": ""}
        self.errors = []
        self.per_doc = []
        self.started_at = time.time()
        self.finished_at = None

    # ---- 写 --------------------------------------------------------------
    def begin(self):
        with self._lock:
            self.state = "running"

    def note_ai_blocked(self, reason: str):
        """预算帽到了：之后的篇只跑本地判据，作业不失败，但要留下为什么少跑了。"""
        with self._lock:
            if not self.ai_stopped_reason:
                self.ai_stopped_reason = reason

    def note_gap_review(self, picked: int, total: int, reason: str = ""):
        """收尾的"域全景复核"记账：AI 从本地候选里挑中了几个（没跑就写原因）。"""
        with self._lock:
            self.gap_review = {"ran": not reason, "picked": int(picked),
                               "total": int(total), "reason": reason}

    def tick(self, path: str, count: int, asked_ai: bool, error: str = ""):
        with self._lock:
            self.done += 1
            self.current = path
            self.findings += int(count)
            if asked_ai:
                self.ai_calls += 1
            rec = {"path": path, "count": int(count), "ai": bool(asked_ai)}
            if error:
                rec["error"] = error[:200]
                self.errors.append(f"{path}: {error[:160]}")
            # 只留前 200 条明细：状态接口是给进度条用的，不是把整本账拖回前端。
            if len(self.per_doc) < 200:
                self.per_doc.append(rec)

    def error(self, text: str):
        """框架层的一条注：批还在跑，但"收尾那一步坏了"必须看得见，
        不能只留在服务端日志里（面板上的数字少了却没有任何解释 = 撒谎）。"""
        with self._lock:
            self.errors.append(text[:200])

    def finish(self, state: str = "done"):
        with self._lock:
            self.state = state
            self.current = ""
            self.finished_at = time.time()

    # ---- 读 --------------------------------------------------------------
    def stop_requested(self) -> bool:
        return self._stop.is_set()

    def request_stop(self):
        self._stop.set()

    def snapshot(self) -> dict:
        with self._lock:
            elapsed = (self.finished_at or time.time()) - self.started_at
            return {
                "state": self.state,
                "scope": self.scope,
                "total": self.total,
                "done": self.done,
                "current": self.current,
                "findings": self.findings,
                "ai_calls": self.ai_calls,
                "ai_stopped_reason": self.ai_stopped_reason,
                "gap_review": dict(self.gap_review),
                "errors": list(self.errors),
                "error_count": len(self.errors),
                "per_doc": [dict(d) for d in self.per_doc],
                "elapsed_s": round(elapsed, 1),
                "running": self.state in ("queued", "running"),
            }


class BatchRunner:
    """把"逐篇做什么"交给回调，自己只管一次一个、可停、可查。

    回调在 daemon 线程里跑，所以它**不能碰 flask.current_app** —— 所有要用的配置、
    路径、句柄都由 `start()` 时在请求上下文里取好再传进来（这是本模块存在的另一半理由：
    把这条约束变成签名上的显式参数，而不是让写线程的人去踩）。
    """

    def __init__(self):
        self._mutex = threading.Lock()
        self._job: BatchJob | None = None

    def current(self) -> BatchJob | None:
        with self._mutex:
            return self._job

    def start(self, items: list, per_doc, scope: dict, finalizer=None) -> BatchJob:
        """启动作业。per_doc(job, item) 负责一篇，返回 (发现条数, 是否问了 AI, 错误)。

        finalizer(job) 在所有篇跑完**之后、收尾之前**于同一线程里执行 —— 给"要看完全部
        篇章才能算的那一步"（域级覆盖空白）用的。它坏了只记一条错，不把整批的结果带走。
        """
        with self._mutex:
            if self._job is not None and self._job.snapshot()["running"]:
                raise BatchBusy("已经有一个批量扫描在跑，请等它结束或先停掉")
            job = BatchJob(scope, min(len(items), MAX_DOCS))
            self._job = job
        threading.Thread(target=self._run,
                         args=(job, items[:MAX_DOCS], per_doc, finalizer),
                         daemon=True, name="ai-batch").start()
        return job

    def stop(self) -> bool:
        job = self.current()
        if job is None:
            return False
        job.request_stop()
        return True

    def _run(self, job: BatchJob, items: list, per_doc, finalizer=None):
        job.begin()
        state = "done"
        try:
            for it in items:
                if job.stop_requested():
                    state = "stopped"
                    break
                try:
                    count, asked, err = per_doc(job, it)
                except Exception as e:      # 一篇坏了不能拖垮整批
                    count, asked, err = 0, False, f"{type(e).__name__}: {e}"
                job.tick(str(it.get("rel") or it.get("path") or "?"), count, asked, err)
            if finalizer is not None and state == "done":
                # 收尾算的是"看完全部篇章才算得出"的那一步（域级覆盖空白）。
                # 它坏了不把整批结果带走 —— 逐篇的建议已经入库了，只补一条错。
                try:
                    finalizer(job)
                except Exception as e:
                    job.error(f"收尾（域级覆盖空白）没跑成：{type(e).__name__}")
        except Exception as e:               # 到这里只能是框架自己坏了
            job.note_ai_blocked(f"作业异常：{type(e).__name__}: {e}"[:200])
            state = "failed"
        job.finish(state)


# 进程内单例：派生库只有一份，同时开两个批量只会互相踩。
RUNNER = BatchRunner()
