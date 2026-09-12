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

# 只加这一个常量引用（连库时的 busy_timeout），不动本模块的任何表结构与业务逻辑。
# app.store 只依赖标准库，此处引入不会形成循环导入。
from app.store import SQLITE_BUSY_TIMEOUT_S

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
CREATE TABLE IF NOT EXISTS doc_marks (
    path TEXT PRIMARY KEY,
    read INTEGER NOT NULL DEFAULT 0,
    mastered INTEGER NOT NULL DEFAULT 0,
    ts REAL NOT NULL,
    day TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_doc_marks_mastered ON doc_marks(mastered);
"""

VALID_EVENTS = {"open", "read_minute", "finish"}
OPEN_DEDUP_SECONDS = 600  # 同文档 open 事件 10 分钟去重


class ReadingStore:
    def __init__(self, indexes: Path):
        indexes.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(indexes / "reading.db", timeout=SQLITE_BUSY_TIMEOUT_S,
                                   check_same_thread=False)
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

    def get_mark(self, path: str) -> dict:
        """单篇文档的已读/已掌握标记。"""
        row = self.con.execute(
            "SELECT read, mastered, ts FROM doc_marks WHERE path=?", (path,)).fetchone()
        return {"path": path, "read": bool(row[0]) if row else False,
                "mastered": bool(row[1]) if row else False,
                "ts": float(row[2]) if row else None}

    def set_mark(self, path: str, kind: str, on: bool) -> dict:
        """切换已读(read)/已掌握(mastered)标记。掌握蕴含已读；取消已读则连掌握一起取消。"""
        if kind not in ("read", "mastered"):
            raise ValueError(f"invalid mark kind: {kind}")
        now = time.time()
        day = time.strftime("%Y-%m-%d", time.localtime(now))
        cur = self.con.execute("SELECT read, mastered FROM doc_marks WHERE path=?", (path,)).fetchone()
        read = bool(cur[0]) if cur else False
        mastered = bool(cur[1]) if cur else False
        if kind == "read":
            read = bool(on)
            if not read:
                mastered = False
        else:
            mastered = bool(on)
            if mastered:
                read = True
        self.con.execute(
            """INSERT INTO doc_marks(path,read,mastered,ts,day) VALUES(?,?,?,?,?)
               ON CONFLICT(path) DO UPDATE SET read=excluded.read,
               mastered=excluded.mastered, ts=excluded.ts, day=excluded.day""",
            (path, int(read), int(mastered), now, day))
        self.con.commit()
        return {"path": path, "read": read, "mastered": mastered}

    def marks_counts(self) -> dict:
        """全库已读/已掌握文档数（统计弹窗用）。"""
        row = self.con.execute(
            "SELECT COUNT(*), COALESCE(SUM(mastered),0) FROM doc_marks WHERE read=1").fetchone()
        return {"read_done": int(row[0] or 0), "mastered_docs": int(row[1] or 0)}

    def migrate_path(self, old_rel: str, new_rel: str) -> int:
        """文档移动/重命名后迁移 path 键（B8）：doc_marks 与 reading_events 随迁，
        单一事务；目标 path 已有行时以既有为准，丢弃 old 孤行。返回迁移行数。"""
        n = 0
        self.con.execute("BEGIN IMMEDIATE")
        try:
            cur = self.con.execute(
                "UPDATE OR IGNORE doc_marks SET path=? WHERE path=?", (new_rel, old_rel))
            n += cur.rowcount
            self.con.execute("DELETE FROM doc_marks WHERE path=?", (old_rel,))
            cur = self.con.execute(
                "UPDATE reading_events SET path=? WHERE path=?", (new_rel, old_rel))
            n += cur.rowcount
            self.con.commit()
        except Exception:
            try:
                self.con.execute("ROLLBACK")
            except Exception:
                pass
            raise
        return n

    def close(self):
        try:
            self.con.close()
        except Exception:
            pass
