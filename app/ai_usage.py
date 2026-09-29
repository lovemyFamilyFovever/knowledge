# -*- coding: utf-8 -*-
"""AI 调用账本 —— 每次出站调用落一行，/api/ai/usage 读它；问答缓存共用这一个库文件。

库文件 indexes/ai.db 是**派生缓存**（AGENTS 不变量 3）：删了可重建，绝不 git 跟踪，
也绝不放进 content/。

为什么每次操作现开连接（和 reading.py 的长句柄不一样）：长句柄在 Windows 上会把
`indexes/ai.db` 锁住，任何"临时实例 + tempfile 根 + 结束就删"的测试都得记得先 close()
—— 实测忘了就 PermissionError（切片 1 第一版就踩了）。账本一秒写一行、读一次聚合，
现开连接的代价是亚毫秒级，换来的是"没有跨请求状态可漏"。这是派生缓存该有的样子。

为什么要账本而不是内存计数：用户要求消耗可追溯（"这次花了多少"必须事后能查），
而进程重启就什么都没了。单价默认 0（MIMO 价目未知）→ 花费字段如实标 price_configured=false，
不给假数字。

轮次 53（2026-09-29）：查漏 / 批量 / 问吧 三块按用户要求整体移除，所以这里的
`ai_audit` 表、`audit_*` 方法与 `AUDIT_STATUSES` 一并删除；`ai_qa` 从 15 列瘦到 10 列
（没有档位、追问、置信、引用、来源了），并且**不再按文档存**（见 QA_COLUMNS 上方注释）。
"""
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from app.store import SQLITE_BUSY_TIMEOUT_S

DDL = """
CREATE TABLE IF NOT EXISTS ai_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    ym TEXT NOT NULL,
    day TEXT NOT NULL,
    kind TEXT NOT NULL,
    model TEXT,
    ok INTEGER NOT NULL DEFAULT 1,
    error TEXT,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    latency_ms INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_ai_calls_day ON ai_calls(day);
CREATE INDEX IF NOT EXISTS idx_ai_calls_ym ON ai_calls(ym);
-- 问答缓存：一次问 = 一段选中文字 → 一句解释。key 里只有选区 + 模型 + 提示词版本，
-- 所以"提示词改版"自动失效，不需要额外的失效逻辑；删表 = 只是重新计费，语料零影响。
-- path **故意不在键里**：答案不依赖文档（服务端根本不读正文），同一个词换一篇再问
-- 不该再花一次钱 —— 这是轮次 53 用户嫌"问两个字要 30 秒"之后定下来的口径。
CREATE TABLE IF NOT EXISTS ai_qa (
    key TEXT PRIMARY KEY,
    ts REAL NOT NULL,
    selection TEXT NOT NULL,
    model TEXT,
    prompt_ver INTEGER NOT NULL DEFAULT 2,
    ok INTEGER NOT NULL DEFAULT 1,
    answer TEXT,
    usage TEXT,
    sent_chars INTEGER NOT NULL DEFAULT 0,
    error TEXT
);
CREATE INDEX IF NOT EXISTS idx_ai_qa_ts ON ai_qa(ts);
"""

QA_COLUMNS = {"key", "ts", "selection", "model", "prompt_ver", "ok",
              "answer", "usage", "sent_chars", "error"}
KINDS = {"test", "select"}   # 轮次 53：ask（问吧）与 audit（查漏）两条链路已整体移除


class AiUsageStore:
    """轻量句柄：只记路径，不持连接。构造完就可以随手丢，不存在"忘了关"这种状态。"""

    def __init__(self, indexes: Path):
        indexes = Path(indexes)
        indexes.mkdir(parents=True, exist_ok=True)
        self.indexes = indexes

    def _con(self):
        # 库路径写死在这一行的实参里：I1 的静态审计是按 connect 的**字面实参**判
        # "连接是否只指向派生缓存"，抽成 self.path 它就读不出来了（第一版就是这么被误报的）。
        con = sqlite3.connect(self.indexes / "ai.db", timeout=SQLITE_BUSY_TIMEOUT_S)
        con.executescript(DDL)  # DDL 含多条语句，须用 executescript
        # CREATE TABLE IF NOT EXISTS 不会改动**已存在**的表：轮次 53 之前的 ai_qa 还带着
        # path/mode 这类 NOT NULL 列，新的 INSERT 会直接失败。问答缓存是派生缓存，
        # 所以这里整表重建，而不是为了一份旧缓存写迁移。
        cols = {r[1] for r in con.execute("PRAGMA table_info(ai_qa)")}
        if cols != QA_COLUMNS:
            con.execute("DROP TABLE IF EXISTS ai_qa")
            con.executescript(DDL)
        return con

    def record(self, kind: str, *, model: str = "", ok: bool = True, error: str = "",
               usage: dict | None = None, latency_ms: int = 0) -> None:
        """记一笔；kind 不在白名单直接抛（宁可炸也不静默写脏账本）。"""
        if kind not in KINDS:
            raise ValueError(f"invalid kind: {kind}")
        u = usage or {}
        try:
            pt = int(u.get("prompt_tokens") or 0)
            ct = int(u.get("completion_tokens") or 0)
            tt = int(u.get("total_tokens") or (pt + ct))
        except (TypeError, ValueError):
            pt = ct = tt = 0
        now = time.time()
        with closing(self._con()) as con, con:
            con.execute(
                "INSERT INTO ai_calls(ts,ym,day,kind,model,ok,error,prompt_tokens,"
                "completion_tokens,total_tokens,latency_ms) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (now, time.strftime("%Y-%m", time.localtime(now)),
                 time.strftime("%Y-%m-%d", time.localtime(now)), kind, model,
                 1 if ok else 0, (error or "")[:200], pt, ct, tt, max(0, int(latency_ms))))

    def _sum(self, con, where: str, args: tuple = ()) -> tuple:
        row = con.execute(
            f"SELECT COUNT(*), COALESCE(SUM(total_tokens),0), "
            f"COALESCE(SUM(CASE WHEN ok=0 THEN 1 ELSE 0 END),0) FROM ai_calls WHERE {where}",
            args).fetchone()
        return (int(row[0]), int(row[1]), int(row[2]))

    def summary(self, *, month: str | None = None, day: str | None = None) -> dict:
        """按日/月聚合调用数、tokens、失败数。month/day 缺省 = 今天与本月。"""
        now = time.localtime()
        day = day or time.strftime("%Y-%m-%d", now)
        month = month or time.strftime("%Y-%m", now)
        with closing(self._con()) as con:
            d_calls, d_tokens, d_fail = self._sum(con, "day=?", (day,))
            m_calls, m_tokens, m_fail = self._sum(con, "ym=?", (month,))
            by_kind = {r[0]: {"calls": r[1], "tokens": r[2]} for r in con.execute(
                "SELECT kind, COUNT(*), COALESCE(SUM(total_tokens),0) FROM ai_calls "
                "WHERE ym=? GROUP BY kind ORDER BY 2 DESC", (month,))}
        return {"day": day, "ym": month,
                "today": {"calls": d_calls, "tokens": d_tokens, "failed": d_fail},
                "month_usage": {"calls": m_calls, "tokens": m_tokens, "failed": m_fail},
                "by_kind": by_kind}

    def recent(self, n: int = 20) -> list:
        with closing(self._con()) as con:
            rows = con.execute(
                "SELECT ts,kind,model,ok,error,total_tokens,latency_ms FROM ai_calls "
                "ORDER BY id DESC LIMIT ?", (max(1, min(int(n), 200)),)).fetchall()
        return [{"ts": r[0], "kind": r[1], "model": r[2], "ok": bool(r[3]),
                 "error": r[4], "total_tokens": r[5], "latency_ms": r[6]} for r in rows]

    @staticmethod
    def estimate_cost(tokens_in: int, tokens_out: int,
                      price_in_per_1k: float, price_out_per_1k: float) -> float:
        return round(tokens_in / 1000.0 * price_in_per_1k
                     + tokens_out / 1000.0 * price_out_per_1k, 6)

    # ---- 问答缓存（同一库文件，删表只是重新计费，语料零影响） -----------------------
    def qa_get(self, key: str):
        with closing(self._con()) as con:
            row = con.execute(
                "SELECT ts,ok,answer,usage,model,selection,sent_chars,error "
                "FROM ai_qa WHERE key=?", (key,)).fetchone()
        if not row:
            return None
        return {"ts": row[0], "ok": bool(row[1]), "answer": row[2],
                "usage": json.loads(row[3] or "{}"), "model": row[4] or "",
                "selection": row[5], "sent_chars": row[6], "error": row[7], "cached": True}

    def qa_put(self, key: str, *, selection: str, model: str, prompt_ver: int, ok: bool,
               answer: str = "", usage=None, sent_chars: int = 0, error: str = "") -> None:
        with closing(self._con()) as con, con:
            con.execute(
                "INSERT OR REPLACE INTO ai_qa(key,ts,selection,model,prompt_ver,ok,answer,"
                "usage,sent_chars,error) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (key, time.time(), selection[:400], model, int(prompt_ver),
                 1 if ok else 0, answer, json.dumps(usage or {}, ensure_ascii=False),
                 int(sent_chars), error[:200]))

    def cost_summary(self, month: str, price_in: float, price_out: float) -> dict:
        with closing(self._con()) as con:
            rows = con.execute(
                "SELECT COALESCE(SUM(prompt_tokens),0), COALESCE(SUM(completion_tokens),0) "
                "FROM ai_calls WHERE ym=?", (month,)).fetchone()
        return {"prompt_tokens": int(rows[0]), "completion_tokens": int(rows[1]),
                "est_cost": self.estimate_cost(int(rows[0]), int(rows[1]), price_in, price_out)}
