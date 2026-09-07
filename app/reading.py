# -*- coding: utf-8 -*-
"""知库月度阅读统计（v1）—— 设计定稿见 docs/统计数据模型-定稿.md。

数据模型：
    reading_events(id, path, title, event, seconds, ts, ym, day)
event ∈ {open, read_minute, finish}；库文件 indexes/reading.db 是派生数据，
与语料完全隔离（frontmatter 永远不存运行时数据 —— AGENTS.md 不变量 6）。
"""
import sqlite3
import time
from pathlib import Path

DDL = """
CREATE TABLE IF NOT EXISTS reading_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    title TEXT,
    event TEXT NOT NULL,
    seconds INTEGER DEFAULT 0,
    ts REAL NOT NULL,
    ym TEXT NOT NULL,
    day TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_ym ON reading_events(ym);
CREATE INDEX IF NOT EXISTS idx_events_path ON reading_events(path);
"""

VALID_EVENTS = {"open", "read_minute", "finish"}
OPEN_DEDUP_SECONDS = 600  # 同文档 open 事件 10 分钟去重


class ReadingStore:
    def __init__(self, indexes: Path):
        indexes.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(indexes / "reading.db", check_same_thread=False)
        self.con.executescript(DDL)  # DDL 含多条语句，须用 executescript
        self.con.commit()

    def track(self, path: str, title: str, event: str, seconds: int = 0) -> bool:
        """记录一条事件；同文档 open 去重窗口内返回 False。"""
        if event not in VALID_EVENTS:
            raise ValueError(f"invalid event: {event}")
        now = time.time()
        if event == "open":
            row = self.con.execute(
                "SELECT ts FROM reading_events WHERE path=? AND event='open' ORDER BY id DESC LIMIT 1",
                (path,)).fetchone()
            if row and now - float(row[0]) < OPEN_DEDUP_SECONDS:
                return False
        ym = time.strftime("%Y-%m", time.localtime(now))
        day = time.strftime("%Y-%m-%d", time.localtime(now))
        self.con.execute(
            "INSERT INTO reading_events(path,title,event,seconds,ts,ym,day) VALUES(?,?,?,?,?,?,?)",
            (path, title, event, int(seconds), now, ym, day))
        self.con.commit()
        return True

    def monthly(self, ym: str, limit: int = 50) -> dict:
        """月度报表：KPI + 文档榜（时长降序）。"""
        kpi = self.con.execute(
            """SELECT COUNT(DISTINCT day),
                      COALESCE(SUM(seconds),0)/60.0,
                      COUNT(DISTINCT CASE WHEN event='open' THEN path END),
                      COUNT(DISTINCT CASE WHEN event='finish' THEN path END)
               FROM reading_events WHERE ym=?""", (ym,)).fetchone()
        docs = self.con.execute(
            """SELECT path, MAX(title), COUNT(CASE WHEN event='open' THEN 1 END),
                      SUM(seconds)/60.0
               FROM reading_events WHERE ym=? GROUP BY path
               ORDER BY 4 DESC LIMIT ?""", (ym, limit)).fetchall()
        daily = self.con.execute(
            """SELECT day, SUM(seconds)/60.0, COUNT(DISTINCT path)
               FROM reading_events WHERE ym=? GROUP BY day ORDER BY day""", (ym,)).fetchall()
        return {
            "ym": ym,
            "active_days": int(kpi[0] or 0),
            "total_minutes": round(float(kpi[1] or 0), 1),
            "opened_docs": int(kpi[2] or 0),
            "finished_docs": int(kpi[3] or 0),
            "docs": [{"path": d[0], "title": d[1], "opens": int(d[2]),
                      "minutes": round(float(d[3] or 0), 1)} for d in docs],
            "daily": [{"day": d[0], "minutes": round(float(d[1] or 0), 1),
                       "docs": int(d[2])} for d in daily],
        }

    def close(self):
        try:
            self.con.close()
        except Exception:
            pass
