# -*- coding: utf-8 -*-
"""AI 调用账本（切片 1）—— 每次出站调用落一行，/api/ai/usage 读它。

库文件 indexes/ai.db 是**派生缓存**（AGENTS 不变量 3）：删了可重建，绝不 git 跟踪，
也绝不放进 content/。这里只放账本表；切片 2 的问答缓存将复用同一个库文件。

为什么每次操作现开连接（和 reading.py 的长句柄不一样）：长句柄在 Windows 上会把
`indexes/ai.db` 锁住，任何"临时实例 + tempfile 根 + 结束就删"的测试都得记得先 close()
—— 实测忘了就 PermissionError（切片 1 第一版就踩了）。账本一秒写一行、读一次聚合，
现开连接的代价是亚毫秒级，换来的是"没有跨请求状态可漏"。这是派生缓存该有的样子。

为什么要账本而不是内存计数：用户要求消耗可追溯（"这次花了多少"必须事后能查），
而进程重启就什么都没了。单价默认 0（MIMO 价目未知）→ 花费字段如实标 price_configured=false，
不给假数字。
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
-- 切片 2：问答缓存。key 里含文档 hash 与 prompt 版本，所以"文档改了/提示词改版"自动失效，
-- 不需要额外的失效逻辑；删表 = 只是重新计费，语料零影响（派生缓存，不变量 3）。
CREATE TABLE IF NOT EXISTS ai_qa (
    key TEXT PRIMARY KEY,
    ts REAL NOT NULL,
    path TEXT NOT NULL,
    selection TEXT NOT NULL,
    mode TEXT NOT NULL,
    model TEXT,
    prompt_ver INTEGER NOT NULL DEFAULT 1,
    ok INTEGER NOT NULL DEFAULT 1,
    answer TEXT,
    confidence TEXT,
    terms TEXT,
    sources TEXT,
    usage TEXT,
    sent_chars INTEGER NOT NULL DEFAULT 0,
    error TEXT
);
CREATE INDEX IF NOT EXISTS idx_ai_qa_path ON ai_qa(path);
"""

KINDS = {"test", "ask", "select", "audit"}


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

    # ---- 切片 2：问答缓存（同一库文件，删表只是重新计费，语料零影响） -------------
    def qa_get(self, key: str):
        with closing(self._con()) as con:
            row = con.execute(
                "SELECT ts,ok,answer,confidence,terms,sources,usage,sent_chars,error,mode,"
                "selection FROM ai_qa WHERE key=?", (key,)).fetchone()
        if not row:
            return None
        return {"ts": row[0], "ok": bool(row[1]), "answer": row[2], "confidence": row[3],
                "terms": json.loads(row[4] or "[]"), "sources": json.loads(row[5] or "[]"),
                "usage": json.loads(row[6] or "{}"), "sent_chars": row[7], "error": row[8],
                "mode": row[9], "selection": row[10], "cached": True}

    def qa_put(self, key: str, *, path: str, selection: str, mode: str, model: str,
               prompt_ver: int, ok: bool, answer: str = "", confidence: str = "",
               terms=None, sources=None, usage=None, sent_chars: int = 0,
               error: str = "") -> None:
        with closing(self._con()) as con, con:
            con.execute(
                "INSERT OR REPLACE INTO ai_qa(key,ts,path,selection,mode,model,prompt_ver,ok,"
                "answer,confidence,terms,sources,usage,sent_chars,error) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (key, time.time(), path, selection[:400], mode, model, int(prompt_ver),
                 1 if ok else 0, answer, confidence,
                 json.dumps(terms or [], ensure_ascii=False),
                 json.dumps(sources or [], ensure_ascii=False),
                 json.dumps(usage or {}, ensure_ascii=False), int(sent_chars), error[:200]))

    def qa_list_for_doc(self, path: str, n: int = 50) -> list:
        """侧栏「本篇问过的」：只回成功的条目（失败的没有回看价值，也不该占位）。"""
        with closing(self._con()) as con:
            rows = con.execute(
                "SELECT ts,selection,mode,answer,confidence,sent_chars FROM ai_qa "
                "WHERE path=? AND ok=1 ORDER BY ts DESC LIMIT ?",
                (path, max(1, min(int(n), 200)))).fetchall()
        return [{"ts": r[0], "selection": r[1], "mode": r[2], "answer": r[3],
                 "confidence": r[4], "sent_chars": r[5]} for r in rows]

    def cost_summary(self, month: str, price_in: float, price_out: float) -> dict:
        with closing(self._con()) as con:
            rows = con.execute(
                "SELECT COALESCE(SUM(prompt_tokens),0), COALESCE(SUM(completion_tokens),0) "
                "FROM ai_calls WHERE ym=?", (month,)).fetchone()
        return {"prompt_tokens": int(rows[0]), "completion_tokens": int(rows[1]),
                "est_cost": self.estimate_cost(int(rows[0]), int(rows[1]), price_in, price_out)}
