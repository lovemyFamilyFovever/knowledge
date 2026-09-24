# -*- coding: utf-8 -*-
"""学习/复习数据层 —— 卡片库 + SM-2 复习状态 + 门户/搜索辅助查询。

数据与 AGENTS.md 不变量的对齐：
    · 表全部落在 indexes/reading.db（**派生缓存**，删了能自动重建）；
      复用 reading.py 的库文件但**不新增/不修改它的任何表**，表名互不重叠。
    · 复习状态、EF、到期时间一律在这里，**一个字节都不写进 frontmatter**。
    · 卡片下线走 `active=0` 软下线，绝不 DELETE：用户把语料挪进 _trash 或改子域
      时，历史复习事件仍有归属，重新归档后进度自动回来。

删库自愈：所有读接口进入时调 ensure_synced()，删库后首次访问会自动建表 + 全量重扫。
"""
import hashlib
import json
import logging
import re
import sqlite3
import threading
import time
from pathlib import Path

from app import fts
from app import store as kbstore
from app.cards import CARDS_PARSER_VERSION, parse_file
from app.sm2 import (EF_INIT, MASTER_INTERVAL, MASTER_REPS, day_start, schedule)

DDL = """
CREATE TABLE IF NOT EXISTS cards (
  card_id TEXT PRIMARY KEY, kind TEXT NOT NULL, term TEXT NOT NULL,
  front TEXT NOT NULL, back TEXT NOT NULL, hint TEXT NOT NULL DEFAULT '',
  source_rel TEXT NOT NULL, anchor TEXT NOT NULL DEFAULT '',
  domain TEXT NOT NULL DEFAULT '', sub TEXT NOT NULL DEFAULT '',
  tags TEXT NOT NULL DEFAULT '', related TEXT NOT NULL DEFAULT '[]',
  difficulty TEXT NOT NULL DEFAULT '', has_answer INTEGER NOT NULL DEFAULT 1,
  fingerprint TEXT NOT NULL, first_seen REAL NOT NULL, last_seen REAL NOT NULL,
  active INTEGER NOT NULL DEFAULT 1);
CREATE INDEX IF NOT EXISTS idx_cards_kind ON cards(kind);
CREATE INDEX IF NOT EXISTS idx_cards_domsub ON cards(domain, sub);
CREATE INDEX IF NOT EXISTS idx_cards_src ON cards(source_rel);
CREATE INDEX IF NOT EXISTS idx_cards_active ON cards(active);

CREATE TABLE IF NOT EXISTS review_state (
  card_id TEXT PRIMARY KEY, ef REAL NOT NULL DEFAULT 2.5, interval INTEGER NOT NULL DEFAULT 0,
  reps INTEGER NOT NULL DEFAULT 0, lapses INTEGER NOT NULL DEFAULT 0,
  due_ts REAL NOT NULL DEFAULT 0, last_q INTEGER, last_ts REAL,
  mastered INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS idx_rs_due ON review_state(due_ts);
CREATE INDEX IF NOT EXISTS idx_rs_mastered ON review_state(mastered);

CREATE TABLE IF NOT EXISTS review_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, card_id TEXT NOT NULL, kind TEXT NOT NULL DEFAULT '',
  q INTEGER NOT NULL, prev_interval INTEGER, new_interval INTEGER, prev_ef REAL, new_ef REAL,
  elapsed_ms INTEGER NOT NULL DEFAULT 0, ts REAL NOT NULL, day TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_re_card ON review_events(card_id);
CREATE INDEX IF NOT EXISTS idx_re_day ON review_events(day);

CREATE TABLE IF NOT EXISTS learn_meta (k TEXT PRIMARY KEY, v TEXT);
"""

# 命令面板固定命令（前端按 id 渲染，勿改）
PALETTE_COMMANDS = [
    {"id": "go-home", "title": "前往 总览", "hint": "页面", "icon": "i-home", "action": '"/home"'},
    {"id": "toggle-theme", "title": "切换 深色 / 浅色", "hint": "命令", "icon": "i-moon",
     "action": '"kb:toggle-theme"'},
    {"id": "goto-review", "title": "开始 今日复习", "hint": "命令", "icon": "i-progress-ring",
     "action": '"/review"'},
    {"id": "goto-quiz", "title": "进入 面试刷题", "hint": "命令", "icon": "i-interview",
     "action": '"/quiz"'},
    {"id": "goto-glossary", "title": "打开 术语百科门户", "hint": "命令", "icon": "i-sort-alpha",
     "action": '"/glossary"'},
    {"id": "readpref", "title": "阅读偏好：字号 / 行宽 / 字体", "hint": "命令", "icon": "i-palette",
     "action": '"kb:readpref"'},
]

META_SYNCED_AT = "cards_synced_at"
META_PARSER = "parser_version"
META_FILE_COUNT = "cards_files"

# 模块级锁：同一进程内同时只允许一个 sync（第二次进入抛 SYNC_BUSY）
_SYNC_LOCK = threading.Lock()

_LOG = logging.getLogger(__name__)


def _note_if_locked(action: str, exc: sqlite3.Error) -> None:
    """写事务撞锁等满 busy_timeout 后仍失败时留痕，再原样上抛。

    连接已经带了 30s 的 busy_timeout，能等到早就等到了；走到这里说明对面真的
    卡死了（长事务不提交 / 别的进程死握写锁），日志里得留下 action 才查得动。
    """
    if "locked" in str(exc).lower() or "busy" in str(exc).lower():
        _LOG.warning("sqlite 锁等待超时（%ds）后仍失败：action=%s err=%s",
                     kbstore.SQLITE_BUSY_TIMEOUT_S, action, exc)


# ---------------- 错误类型（路由层据此映射 HTTP 码） ----------------
class LearnError(Exception):
    code = "BAD_PARAM"
    http = 400

    def __init__(self, detail: str = "", code: str | None = None, http: int | None = None):
        self.detail = detail or self.code
        if code:
            self.code = code
        if http:
            self.http = http
        super().__init__(self.detail)


class BadParam(LearnError):
    code, http = "BAD_PARAM", 400


class BadQuery(LearnError):
    code, http = "BAD_Q", 400


class CardNotFound(LearnError):
    code, http = "BAD_CARD", 404


class SyncBusy(LearnError):
    code, http = "SYNC_BUSY", 409


class NotSynced(LearnError):
    code, http = "NOT_SYNCED", 503


class CorpusEmpty(LearnError):
    code, http = "CORPUS_EMPTY", 404


# ---------------- 工具 ----------------
def _day_str(ts: float) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(ts))


def _json_list(raw: str) -> list[str]:
    try:
        v = json.loads(raw or "[]")
    except (ValueError, TypeError):
        return []
    return v if isinstance(v, list) else []


def _tag_list(raw: str) -> list[str]:
    return [x for x in str(raw or "").split(",") if x]


def _as_bool(v, default: bool = True) -> bool:
    """把查询串/JSON 里的各种「真」稳当地读成 bool。"""
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off", ""):
        return False
    return default


class LearnStore:
    """卡片库 + 复习状态的持久层。库文件：indexes/reading.db（与 reading.py 共用文件、表不重叠）。"""

    def __init__(self, indexes: Path, content: Path | None = None):
        indexes = Path(indexes)
        indexes.mkdir(parents=True, exist_ok=True)
        self.indexes = indexes
        self.content = Path(content) if content else None
        self.con = sqlite3.connect(indexes / "reading.db",
                                   timeout=kbstore.SQLITE_BUSY_TIMEOUT_S,
                                   check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self._ensure_schema()
        self.con.commit()

    def _ensure_schema(self) -> None:
        """建表（幂等）。

        看着可以无脑 `executescript(DDL)`，实测不行：DDL 有 18 条语句，逐条各自成事务，
        在 Windows 上新建库时合计约 2s，会直接吃掉「删库自愈 < 5s」的大半预算。
        因此：① 表齐全就跳过；② 真要建表时用一个显式事务把 18 次提交收敛成 1 次。
        """
        row = self.con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='review_events'"
        ).fetchone()
        if row is not None:
            return
        self.con.executescript("BEGIN;" + DDL + "COMMIT;")

    # ---------- 元信息 ----------
    def meta_get(self, key: str) -> str | None:
        row = self.con.execute("SELECT v FROM learn_meta WHERE k=?", (key,)).fetchone()
        return row[0] if row else None

    def meta_set(self, key: str, value: str) -> None:
        self.con.execute("INSERT OR REPLACE INTO learn_meta(k,v) VALUES(?,?)", (key, str(value)))
        self.con.commit()

    def close(self) -> None:
        try:
            self.con.close()
        except Exception:
            pass

    # ---------- 同步 ----------
    def _candidate_files(self, content: Path) -> list[tuple[Path, str]]:
        """参与抽卡的语料：只取 baike / interview 两个域的 md。

        其余域（articles/projects/career/handbook/ai-assets）按设计不抽卡，
        因此不计入 coverage —— coverage 只回答「候选语料里抽出了多少」。
        """
        out = []
        for p, rel in kbstore.md_files(content):
            parts = rel.split("/")
            if not parts or parts[0] not in ("baike", "interview"):
                continue
            if any(part.startswith("_") for part in parts):
                continue
            out.append((p, rel))
        return out

    def sync(self, content: Path | None = None, force: bool = False) -> dict:
        """扫描语料重建卡片库。

        - 新出现的 card_id → added
        - card_id 已存在但 fingerprint 变了 → updated（first_seen 不动）
        - 本轮没被 touch 到的旧卡 → active=0 软下线（**绝不 DELETE**）

        Args:
            content: content/ 根目录；缺省用构造时传入的。
            force: 仅影响是否跳过「看起来没变」的判断（当前实现里 sync 总是全量重解析，
                   force 只用于未来增量优化与日志语义）。

        Returns:
            {added, updated, retired, total, by_kind, coverage, elapsed_ms, synced_at}

        Raises:
            SyncBusy: 已有 sync 在跑。
            CorpusEmpty: 候选语料为空。
        """
        content = Path(content or self.content)
        if content is None or not content.is_dir():
            raise CorpusEmpty("content/ 不存在或为空")
        if not _SYNC_LOCK.acquire(blocking=False):
            raise SyncBusy("上一次抽卡同步尚未结束，请稍后再试")

        t0 = time.perf_counter()
        try:
            now = time.time()
            candidates = self._candidate_files(content)
            if not candidates:
                raise CorpusEmpty("候选语料为空（baike / interview 域没有 md）")

            added = updated = 0
            files = parsed = 0
            cur = self.con.cursor()
            for p, rel in candidates:
                files += 1
                try:
                    raw = p.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                try:
                    cards = parse_file(rel, raw)
                except Exception:
                    cards = []
                if not cards:
                    continue
                parsed += 1
                for card in cards:
                    row = cur.execute(
                        "SELECT fingerprint FROM cards WHERE card_id=?", (card.card_id,)).fetchone()
                    if row is None:
                        added += 1
                        cur.execute(
                            "INSERT INTO cards(card_id,kind,term,front,back,hint,source_rel,anchor,"
                            "domain,sub,tags,related,difficulty,has_answer,fingerprint,"
                            "first_seen,last_seen,active) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
                            (*card.row(), now, now))
                    else:
                        if row[0] != card.fingerprint:
                            updated += 1
                        cur.execute(
                            "UPDATE cards SET kind=?,term=?,front=?,back=?,hint=?,source_rel=?,"
                            "anchor=?,domain=?,sub=?,tags=?,related=?,difficulty=?,has_answer=?,"
                            "fingerprint=?,last_seen=?,active=1 WHERE card_id=?",
                            (card.kind, card.term, card.front, card.back, card.hint,
                             card.source_rel, card.anchor, card.domain, card.sub, card.tags,
                             card.related, card.difficulty, card.has_answer,
                             card.fingerprint, now, card.card_id))

            cur.execute("UPDATE cards SET active=0 WHERE last_seen < ? AND active=1", (now,))
            retired = cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
            self.con.commit()

            by_kind: dict[str, int] = {}
            for _k, n in self.con.execute(
                    "SELECT kind, count(*) FROM cards WHERE active=1 GROUP BY kind"):
                by_kind[_k] = n
            total = int(self.con.execute(
                "SELECT count(*) FROM cards WHERE active=1").fetchone()[0])
            # B17：card_id 刻意不含路径（改名不丢进度），但 baike_def 的 front 由
            # term 模板生成 —— 同一术语出现在两个文件时 id 相同，后扫到者静默改写
            # 前者的 back/source_rel。改 ID 方案会重置全部复习进度，这里先把碰撞
            # 数量如实暴露到同步结果，处置策略留给用户定夺。
            term_collisions = int(self.con.execute(
                "SELECT COUNT(*) FROM (SELECT term FROM cards WHERE active=1 "
                "AND kind='baike_def' GROUP BY term HAVING COUNT(DISTINCT source_rel) > 1)"
            ).fetchone()[0])

            self.meta_set(META_SYNCED_AT, str(now))
            self.meta_set(META_PARSER, str(CARDS_PARSER_VERSION))
            self.meta_set(META_FILE_COUNT, str(files))

            return {
                "added": added, "updated": updated, "retired": retired, "total": total,
                "by_kind": by_kind, "term_collisions": term_collisions,
                "coverage": {"files": files, "parsed": parsed, "skipped": files - parsed},
                "elapsed_ms": round((time.perf_counter() - t0) * 1000),
                "synced_at": now,
            }
        except sqlite3.OperationalError as e:
            _note_if_locked("sync", e)
            _safe_rollback(self.con)
            raise
        finally:
            _SYNC_LOCK.release()

    def ensure_synced(self, content: Path | None = None) -> dict | None:
        """读接口的进入钩子：库是空的/过期了/解析器升版了 → 自动重建。

        判据：
            ① learn_meta.cards_synced_at 不存在；② cards 表为空；
            ③ max(md mtime) > cards_synced_at（增量）；④ parser_version 变了（全量）；
            ⑤ 候选 md 篇数变了（只看 mtime 感知不到「删除」，这是 mtime 判据的盲区）。

        Returns: 触发了同步则返回 sync() 的结果，否则 None。
        """
        content = Path(content or self.content)
        try:
            total = int(self.con.execute(
                "SELECT count(*) FROM cards WHERE active=1").fetchone()[0])
        except sqlite3.Error:
            total = 0
        synced_at = self.meta_get(META_SYNCED_AT)
        version = self.meta_get(META_PARSER)
        file_count = self.meta_get(META_FILE_COUNT)

        need = False
        if synced_at is None or total == 0:
            need = True
        elif version != str(CARDS_PARSER_VERSION):
            need = True
        else:
            candidates = self._candidate_files(content)
            if str(len(candidates)) != str(file_count or ""):
                need = True
            else:
                newest = max((p.stat().st_mtime for p, _ in candidates), default=0.0)
                if newest > float(synced_at):
                    need = True
        if need:
            try:
                return self.sync(content)
            except SyncBusy:
                return None  # 别人正在同步：读旧数据继续服务，不阻塞用户
        return None

    # ---------- 查询辅助 ----------
    def _filter(self, kind: str | None = None, domain: str | None = None,
                sub: str | None = None) -> tuple[str, list]:
        clauses = ["c.active=1"]
        args: list = []
        if kind:
            clauses.append("c.kind=?")
            args.append(kind)
        if domain:
            clauses.append("c.domain=?")
            args.append(domain)
        if sub:
            clauses.append("c.sub=?")
            args.append(sub)
        return " AND ".join(clauses), args

    _STATE_COLS = (
        "COALESCE(rs.ef,2.5) AS ef, COALESCE(rs.interval,0) AS interval, "
        "COALESCE(rs.reps,0) AS reps, COALESCE(rs.lapses,0) AS lapses, "
        "COALESCE(rs.due_ts,0) AS due_ts, COALESCE(rs.mastered,0) AS mastered, "
        "rs.last_q, rs.last_ts"
    )

    @staticmethod
    def _state(row: dict) -> dict:
        return {
            "ef": float(row.get("ef") or EF_INIT),
            "interval": int(row.get("interval") or 0),
            "reps": int(row.get("reps") or 0),
            "lapses": int(row.get("lapses") or 0),
            "due_ts": float(row.get("due_ts") or 0),
            "due_in_days": int(row.get("due_in_days") or 0),
            "mastered": int(row.get("mastered") or 0),
            "is_new": bool(row.get("is_new", 0)),
        }

    def due(self, kind: str | None = None, domain: str | None = None,
            sub: str | None = None, limit: int = 20, include_new: bool = True,
            new_ratio: float = 0.3) -> dict:
        """到期队列：到期的按 due_ts 升序，新卡排在最后且占比不超过 new_ratio。"""
        limit = max(1, min(int(limit or 20), 200))
        new_ratio = max(0.0, min(float(new_ratio if new_ratio is not None else 0.3), 1.0))
        now = time.time()
        where, args = self._filter(kind, domain, sub)
        join = "FROM cards c LEFT JOIN review_state rs ON rs.card_id=c.card_id WHERE "

        due_where = f"{where} AND rs.card_id IS NOT NULL AND rs.due_ts>0 AND rs.due_ts<=?"
        new_where = (f"{where} AND (rs.card_id IS NULL OR "
                     f"(COALESCE(rs.reps,0)=0 AND COALESCE(rs.due_ts,0)=0))")

        due_n = int(self.con.execute(
            f"SELECT count(*) {join}{due_where}", (*args, now)).fetchone()[0])
        new_n = int(self.con.execute(
            f"SELECT count(*) {join}{new_where}", tuple(args)).fetchone()[0])

        n_new_cap = 0 if not include_new else min(new_n, int(limit * new_ratio))
        if include_new and due_n == 0:
            # 一份到期卡都没有时（典型：首次使用，全库都是新卡）不再按 new_ratio 打折 ——
            # 否则 limit=20 只返回 6 张、limit=5 只返回 1 张，复习页根本刷不动。
            # ratio 的语义是「别让新卡挤占到期卡」，没有到期卡可挤时它不该生效。
            n_new_cap = min(new_n, limit)
        n_due_cap = limit - n_new_cap
        # 允许「新卡不足」时用到期卡补足，保证一次总是拿满一片可复习的牌
        due_rows = [dict(r) for r in self.con.execute(
            f"SELECT c.*, {self._STATE_COLS}, 0 AS is_new {join}{due_where} "
            f"ORDER BY rs.due_ts ASC LIMIT ?", (*args, now, n_due_cap + n_new_cap))]
        new_rows = [dict(r) for r in self.con.execute(
            f"SELECT c.*, {self._STATE_COLS}, 1 AS is_new {join}{new_where} "
            f"ORDER BY RANDOM() LIMIT ?", (*args, n_new_cap))]

        take_due = due_rows[:max(0, limit - len(new_rows))]
        slate = list(take_due) + list(new_rows)
        slate = _interleave_kinds(slate)
        return {
            "cards": slate, "due_n": due_n, "new_n": new_n,
            "total_n": due_n + new_n, "limit": limit,
        }

    def mock_cards(self, n: int = 10) -> list[dict]:
        """模拟面试：从面试卡全库随机抽 n 张（不看排期，纯随机，可重复抽到复习过的）。"""
        n = max(1, min(int(n or 10), 50))
        return [dict(r) for r in self.con.execute(
            f"SELECT c.*, {self._STATE_COLS}, 0 AS is_new FROM cards c "
            "LEFT JOIN review_state rs ON rs.card_id=c.card_id "
            "WHERE c.active=1 AND c.kind='interview_qa' "
            "ORDER BY RANDOM() LIMIT ?", (n,))]

    def submit_review(self, card_id: str, q: int, elapsed_ms: int = 0) -> dict:
        """提交一次评分：写事件 + 推进 SM-2 状态，单事务。

        同一 (card_id, 秒级 ts) 重复提交视为幂等：不重复写事件、不二次推进间隔
        （前端抖动/重试双击不应该把进度推两次）。
        """
        if not card_id:
            raise BadParam("card_id 必填")
        try:
            q = int(q)
        except (TypeError, ValueError):
            raise BadQuery("q 必须是 0..5 的整数") from None
        if not 0 <= q <= 5:
            raise BadQuery("q 必须是 0..5 的整数")
        try:
            elapsed_ms = max(0, min(int(elapsed_ms or 0), 3_600_000))
        except (TypeError, ValueError):
            elapsed_ms = 0

        now = time.time()
        day = _day_str(now)
        con = self.con
        con.execute("BEGIN IMMEDIATE")
        try:
            card = con.execute(
                "SELECT card_id, kind FROM cards WHERE card_id=?", (card_id,)).fetchone()
            if card is None:
                raise CardNotFound(f"没有这张卡片：{card_id}")

            row = con.execute(
                "SELECT ef, interval, reps, lapses, mastered, due_ts FROM review_state "
                "WHERE card_id=?", (card_id,)).fetchone()
            prev = dict(row) if row else {
                "ef": EF_INIT, "interval": 0, "reps": 0, "lapses": 0, "mastered": 0,
                "due_ts": 0}
            prev.setdefault("due_ts", 0)
            prev_mastered = int(prev["mastered"] or 0)

            # 幂等窗口 1 秒。用「时间差」而不是 CAST(ts AS INTEGER) 判定：后者按整秒截断，
            # 两次提交若恰好跨过整秒边界（1000.9 / 1001.1）会被算成两次，双击去重就失效了。
            dup = con.execute(
                "SELECT id FROM review_events WHERE card_id=? AND ABS(ts - ?) < 1.0 LIMIT 1",
                (card_id, now)).fetchone()
            if dup is not None:
                # 幂等：同一秒的重复提交视为重试，原样返回当前状态，不二次推进间隔
                con.execute("ROLLBACK")
                same = {
                    "ef": round(float(prev["ef"]), 4), "interval": int(prev["interval"]),
                    "reps": int(prev["reps"]), "lapses": int(prev["lapses"]),
                    "due_ts": float(prev["due_ts"] or 0),
                    "due_in_days": max(0, int((float(prev["due_ts"] or 0) - day_start(now))
                                              / 86400) if prev["due_ts"] else 0),
                }
                return self._review_response(
                    card_id, str(card["kind"]), q, dict(prev), same,
                    prev_mastered, prev_mastered, 0, now)

            nxt = schedule(
                {"ef": float(prev["ef"]), "interval": int(prev["interval"]),
                 "reps": int(prev["reps"]), "lapses": int(prev["lapses"])}, q, now)
            con.execute(
                "INSERT INTO review_events(card_id,kind,q,prev_interval,new_interval,prev_ef,"
                "new_ef,elapsed_ms,ts,day) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (card_id, str(card["kind"]), q, int(prev["interval"]), nxt["interval"],
                 float(prev["ef"]), nxt["ef"], elapsed_ms, now, day))
            con.execute(
                "INSERT OR REPLACE INTO review_state(card_id,ef,interval,reps,lapses,due_ts,"
                "last_q,last_ts,mastered) VALUES(?,?,?,?,?,?,?,?,?)",
                (card_id, nxt["ef"], nxt["interval"], nxt["reps"], nxt["lapses"],
                 nxt["due_ts"], q, now, nxt["mastered"]))
            con.commit()
            return self._review_response(
                card_id, str(card["kind"]), q, prev, nxt, prev_mastered,
                nxt["mastered"], elapsed_ms, now)
        except LearnError:
            _safe_rollback(con)
            raise
        except sqlite3.OperationalError as e:
            _note_if_locked("submit_review", e)
            _safe_rollback(con)
            raise
        except Exception:
            _safe_rollback(con)
            raise

    def _review_response(self, card_id: str, kind: str, q: int, prev: dict, nxt: dict,
                         prev_mastered: int, new_mastered: int, elapsed_ms: int,
                         now: float) -> dict:
        """组装 review 响应：`prev` / `next` 两个快照 + 掌握度增量 + 连续天数。"""
        return {
            "card_id": card_id, "kind": kind, "q": q,
            "prev": {"ef": round(float(prev["ef"]), 4), "interval": int(prev["interval"]),
                     "reps": int(prev["reps"]), "lapses": int(prev["lapses"]),
                     "due_ts": float(prev.get("due_ts") or 0), "mastered": prev_mastered},
            "next": {"ef": round(float(nxt["ef"]), 4), "interval": int(nxt["interval"]),
                     "reps": int(nxt["reps"]), "lapses": int(nxt["lapses"]),
                     "due_ts": float(nxt["due_ts"]),
                     "due_in_days": int(nxt.get("due_in_days") or 0),
                     "mastered": int(new_mastered)},
            "mastery_delta": int(new_mastered) - int(prev_mastered),
            "streak_days": self.streak_days(),
        }

    def streak_days(self) -> int:
        """连续复习天数：从今天（或昨天）起往回数，断一天即止。

        「今天还没复习」不算断签 —— 否则每到零点就显示 0，很打击人。
        """
        days = [r[0] for r in self.con.execute(
            "SELECT DISTINCT day FROM review_events ORDER BY day DESC LIMIT 400")]
        if not days:
            return 0
        today = _day_str(time.time())
        yesterday = _day_str(time.time() - 86400)
        idx = 0
        if days[0] == today:
            idx = 0
        elif days[0] == yesterday:
            idx = 0  # 今天尚未开始，从昨天起算
        else:
            return 0
        streak = 1
        cur = days[idx]
        for d in days[idx + 1:]:
            expect = _day_str(_day_to_ts(cur) - 86400)
            if d == expect:
                streak += 1
                cur = d
            else:
                break
        return streak

    def mastery(self, scope: str = "sub", domain: str | None = None,
                all: bool = False) -> dict:
        """掌握度面板：已掌握 / 学习中 / 未学 的分布。

        判定与 app/sm2.py 保持同一套公式：interval>=21 且 reps>=3 ⇒ 已掌握。
        """
        scope = "domain" if str(scope).strip().lower() == "domain" else "sub"
        where, args = ["c.active=1"], []
        if domain:
            where.append("c.domain=?")
            args.append(domain)
        w = " AND ".join(where)
        rows = self.con.execute(
            f"""SELECT c.domain AS domain, c.sub AS sub, COUNT(*) AS total,
                       SUM(CASE WHEN rs.card_id IS NULL OR COALESCE(rs.reps,0)=0 THEN 1 ELSE 0 END) AS n_new,
                       SUM(CASE WHEN COALESCE(rs.reps,0)>0 AND NOT (
                            COALESCE(rs.interval,0)>={MASTER_INTERVAL}
                            AND COALESCE(rs.reps,0)>={MASTER_REPS}) THEN 1 ELSE 0 END) AS n_learn,
                       SUM(CASE WHEN COALESCE(rs.interval,0)>={MASTER_INTERVAL}
                            AND COALESCE(rs.reps,0)>={MASTER_REPS} THEN 1 ELSE 0 END) AS n_master,
                       SUM(CASE WHEN rs.card_id IS NOT NULL THEN 1 ELSE 0 END) AS n_reviewed,
                       AVG(CASE WHEN rs.card_id IS NOT NULL THEN rs.ef END) AS ef_avg
                FROM cards c LEFT JOIN review_state rs ON rs.card_id=c.card_id
                WHERE {w} GROUP BY c.domain, c.sub""", tuple(args)).fetchall()

        now = time.time()
        grouped: dict[tuple[str, str], dict] = {}
        for r in rows:
            key = (r["domain"], r["sub"] if scope == "sub" else "")
            g = grouped.setdefault(key, {"total": 0, "mastered": 0, "learning": 0, "new": 0,
                                         "due_n": 0, "ef_sum": 0.0, "ef_n": 0})
            g["total"] += int(r["total"] or 0)
            g["mastered"] += int(r["n_master"] or 0)
            g["learning"] += int(r["n_learn"] or 0)
            g["new"] += int(r["n_new"] or 0)
            if r["ef_avg"] is not None and int(r["n_reviewed"] or 0) > 0:
                # 组内再合并：按「已复习篇数」加权还原平均 EF
                g["ef_sum"] += float(r["ef_avg"]) * int(r["n_reviewed"] or 0)
                g["ef_n"] += int(r["n_reviewed"] or 0)

        due_rows = self.con.execute(
            f"""SELECT c.domain AS domain, c.sub AS sub, COUNT(*) AS n
                FROM cards c JOIN review_state rs ON rs.card_id=c.card_id
                WHERE {w} AND rs.due_ts>0 AND rs.due_ts<=?
                GROUP BY c.domain, c.sub""", (*args, now)).fetchall()
        for r in due_rows:
            key = (r["domain"], r["sub"] if scope == "sub" else "")
            if key in grouped:
                grouped[key]["due_n"] += int(r["n"] or 0)

        def _pct(group: dict) -> int:
            return round(100 * group["mastered"] / max(1, group["total"]))

        items = []
        for (dom, sub), g in grouped.items():
            if scope == "sub":
                _id = f"{dom}/{sub}"
                label = self._sub_label(dom, sub)
            else:
                _id = dom
                label = self._domain_label(dom)
            items.append({
                "id": _id, "label": label, "domain": dom, "sub": sub,
                "total": g["total"], "mastered": g["mastered"], "learning": g["learning"],
                "new": g["new"], "pct": _pct(g), "hue": self._hue(dom),
                # 一张都还没复习过时，平均 EF 报初始值 2.5 —— 报 0.0 会让人以为组件坏了
                "ef_avg": round(g["ef_sum"] / g["ef_n"], 3) if g["ef_n"] else EF_INIT,
                "due_n": g["due_n"],
            })
        items.sort(key=lambda x: (x["domain"], -x["total"], x["label"]))

        totals = {"total": 0, "mastered": 0, "learning": 0, "new": 0, "due_n": 0}
        for it in items:
            for k in ("total", "mastered", "learning", "new", "due_n"):
                totals[k] += int(it[k])
        totals["pct"] = round(100 * totals["mastered"] / max(1, totals["total"]))
        totals["items"] = len(items)
        # C3：all=True 且 scope=domain 时，以 taxonomy 域为骨架补零行——
        # GROUP BY 只产出有卡域，7 域全景视图需要无卡域也可见（未建卡态）。
        # 默认 False 走原路径，既有消费（learn.js 子域 chips / 测试）零变化。
        if all and scope == "domain":
            have = {it["domain"] for it in items}
            tax = self._tax()
            doms = list((tax or {}).get("domains", {}).keys())
            if not doms:
                doms = list(kbstore.GRAPH_HUES.keys())
            for dom in doms:
                if dom in have:
                    continue
                items.append({
                    "id": dom, "label": self._domain_label(dom), "domain": dom, "sub": "",
                    "total": 0, "mastered": 0, "learning": 0, "new": 0, "pct": 0,
                    "hue": self._hue(dom), "ef_avg": EF_INIT, "due_n": 0,
                })
            items.sort(key=lambda x: (x["domain"], -x["total"], x["label"]))

        return {"scope": scope, "items": items, "totals": totals}

    def today_stats(self, domain: str | None = None) -> dict:
        """今日面板的统计部分。"""
        now = time.time()
        today = _day_str(now)
        where, args = self._filter(None, domain, None)
        join = "FROM cards c LEFT JOIN review_state rs ON rs.card_id=c.card_id WHERE "
        due_n = int(self.con.execute(
            f"SELECT count(*) {join}{where} AND rs.card_id IS NOT NULL AND rs.due_ts>0 "
            f"AND rs.due_ts<=?", (*args, now)).fetchone()[0])
        new_left = int(self.con.execute(
            f"SELECT count(*) {join}{where} AND (rs.card_id IS NULL OR "
            f"(COALESCE(rs.reps,0)=0 AND COALESCE(rs.due_ts,0)=0))", tuple(args)).fetchone()[0])
        done_today = int(self.con.execute(
            "SELECT COUNT(DISTINCT card_id) FROM review_events WHERE day=?", (today,)).fetchone()[0])
        mastered_total = int(self.con.execute(
            f"SELECT count(*) {join}{where} AND COALESCE(rs.interval,0)>={MASTER_INTERVAL} "
            f"AND COALESCE(rs.reps,0)>={MASTER_REPS}", tuple(args)).fetchone()[0])
        total = int(self.con.execute(
            f"SELECT count(*) {join}{where}", tuple(args)).fetchone()[0])
        return {
            "due_n": due_n, "done_today": done_today, "new_left": new_left,
            "streak_days": self.streak_days(), "mastered": mastered_total,
            "mastered_total": total,
            "mastered_pct": round(100 * mastered_total / max(1, total)),
        }

    def today_card(self, domain: str | None = None) -> dict:
        """「今日一张」：① 到期的最旧一张定义卡 → ② 随机新卡 → ③ 最近复习过的一张 + tip。

        三个分支都限定 `kind='baike_def'`：这张卡是首页「今日术语」位，必须是一句
        「xx 是什么」。若放误区卡（back 以「✗ 这是常见误区。正解：」开头）或面试题
        进去，语义完全不对 —— 读者会以为首页在教他一个错误说法。
        整库一张定义卡都没有时才回退到不限定，并在 tip 里说明。
        """
        now = time.time()
        where, args = self._filter(None, domain, None)
        join = ("FROM cards c JOIN review_state rs ON rs.card_id=c.card_id WHERE ")

        def _pick(kind_sql: str) -> tuple[sqlite3.Row | None, str]:
            """按 ①→②→③ 三级瀑布挑一张；返回 (行, tip)。"""
            row = self.con.execute(
                f"SELECT c.*, {self._STATE_COLS}, 0 AS is_new {join}{where}{kind_sql} "
                f"AND rs.due_ts>0 AND rs.due_ts<=? AND rs.reps>0 "
                f"ORDER BY rs.due_ts ASC LIMIT 1", (*args, now)).fetchone()
            if row is not None:
                return row, ""
            row = self.con.execute(
                "SELECT c.*, " + self._STATE_COLS + ", 1 AS is_new "
                "FROM cards c LEFT JOIN review_state rs ON rs.card_id=c.card_id WHERE "
                + where + kind_sql + " AND (rs.card_id IS NULL OR (COALESCE(rs.reps,0)=0 "
                                      "AND COALESCE(rs.due_ts,0)=0)) "
                "ORDER BY RANDOM() LIMIT 1", tuple(args)).fetchone()
            if row is not None:
                return row, "今天没有到期复习 —— 顺手认一张新卡。"
            row = self.con.execute(
                f"SELECT c.*, {self._STATE_COLS}, 0 AS is_new {join}{where}{kind_sql} "
                f"AND rs.last_ts IS NOT NULL ORDER BY rs.last_ts DESC LIMIT 1",
                tuple(args)).fetchone()
            if row is not None:
                return row, "全部卡片都还没到期 —— 这是你最近复习过的一张。"
            return None, ""

        row, tip = _pick(" AND c.kind='baike_def'")
        if row is None:
            # 理论不可能（实测 662 张定义卡）：整库没有定义卡时也不让首页开天窗
            row, _ = _pick("")
            if row is not None:
                tip = "库里暂未抽出术语定义卡 —— 先拿一张别的顶上。"
        if row is None:
            return {"card": None, "tip": "还没有卡片，先去「同步抽卡」。", "stats": {}}
        return {"card": dict(row), "tip": tip, "stats": {}}

    def roam(self, term: str, n: int = 6, only_new: bool = False) -> dict:
        """漫游：从起点术语沿 [[相关术语]] 做 BFS，未学的优先。"""
        n = max(1, min(int(n or 6), 50))
        start = self.con.execute(
            "SELECT * FROM cards WHERE active=1 AND term=? "
            "ORDER BY (kind='baike_def') DESC LIMIT 1", (term,)).fetchone()
        if start is None:
            start = self.con.execute(
                "SELECT * FROM cards WHERE active=1 AND term LIKE ? LIMIT 1",
                (f"%{term}%",)).fetchone()
        if start is None:
            return {"start": term, "path": [], "n": 0, "dead_ends": [term]}

        def card_of(name: str):
            return self.con.execute(
                "SELECT c.*, COALESCE(rs.reps,0) AS reps FROM cards c "
                "LEFT JOIN review_state rs ON rs.card_id=c.card_id "
                "WHERE c.active=1 AND c.term=? ORDER BY (c.kind='baike_def') DESC LIMIT 1",
                (name,)).fetchone()

        seen_cards: set[str] = {start["card_id"]}
        seen_terms: set[str] = {start["term"]}  # B16：related 是术语名，旧实现拿
        # card_id 集合去比名字（恒不命中），同一张卡可经多条 related 路径重复入队，
        # path 里出现重复节点。名字与 card_id 现在分别去重。
        path: list[dict] = []
        dead_ends: list[str] = []
        queue: list[tuple[sqlite3.Row, int]] = [(start, 0)]
        while queue and len(path) < n:
            node, depth = queue.pop(0)
            reps_row = node["reps"] if "reps" in node.keys() else None
            if reps_row is None:
                reps_row = self.con.execute(
                    "SELECT COALESCE(reps,0) FROM review_state WHERE card_id=?",
                    (node["card_id"],)).fetchone()
                reps_row = reps_row[0] if reps_row else 0
            path.append({
                "term": node["term"], "card_id": node["card_id"], "front": node["front"],
                "back": node["back"], "kind": node["kind"], "source_rel": node["source_rel"],
                "is_new": int(reps_row or 0) == 0, "depth": depth,
            })
            neighbours = [x for x in _json_list(node["related"]) if x not in seen_terms]
            ranked: list[sqlite3.Row] = []
            for name in neighbours:
                if name in seen_terms:
                    continue
                seen_terms.add(name)
                c = card_of(name)
                if c is None:
                    if name not in dead_ends:
                        dead_ends.append(name)
                    continue
                if c["card_id"] in seen_cards:
                    continue
                seen_cards.add(c["card_id"])
                seen_terms.add(c["term"])
                ranked.append(c)
            ranked.sort(key=lambda r: 0 if int(r["reps"] or 0) == 0 else 1)
            if only_new:
                ranked = [r for r in ranked if int(r["reps"] or 0) == 0]
            for c in ranked:
                if len(path) + len(queue) >= n:
                    break
                queue.append((c, depth + 1))
        return {"start": term, "path": path, "n": len(path), "dead_ends": dead_ends}

    def search_cards(self, q: str | None = None, kind: str | None = None,
                     domain: str | None = None, sub: str | None = None,
                     active: bool = True, offset: int = 0, limit: int = 30) -> dict:
        """卡片检索（后台/刷题筛选用）。"""
        offset = max(0, int(offset or 0))
        limit = max(1, min(int(limit or 30), 200))
        clauses = [f"c.active={1 if _as_bool(active, True) else 0}"]
        args: list = []
        if q:
            clauses.append("(c.front LIKE ? OR c.back LIKE ? OR c.term LIKE ?)")
            like = f"%{q}%"
            args += [like, like, like]
        if kind:
            clauses.append("c.kind=?")
            args.append(kind)
        if domain:
            clauses.append("c.domain=?")
            args.append(domain)
        if sub:
            clauses.append("c.sub=?")
            args.append(sub)
        w = " AND ".join(clauses)
        total = int(self.con.execute(
            f"SELECT count(*) FROM cards c WHERE {w}", tuple(args)).fetchone()[0])
        rows = self.con.execute(
            f"SELECT c.*, {self._STATE_COLS}, "
            f"CASE WHEN rs.card_id IS NULL OR COALESCE(rs.reps,0)=0 THEN 1 ELSE 0 END AS is_new "
            f"FROM cards c LEFT JOIN review_state rs ON rs.card_id=c.card_id WHERE {w} "
            f"ORDER BY c.domain, c.sub, c.card_id LIMIT ? OFFSET ?",
            (*args, limit, offset)).fetchall()
        return {"total": total, "offset": offset, "limit": limit,
                "items": [dict(r) for r in rows]}

    # ---------- 术语门户 ----------
    def glossary(self, domain: str = "baike", sub: str | None = None,
                 letter: str | None = None, sort: str = "alpha",
                 q: str | None = None) -> dict:
        """术语百科门户：词条按子域分组 + A–Z 分桶。

        分桶规则（**不引入 pypinyin**，离线零依赖是硬约束）：
            ASCII 字母开头 → 对应大写字母桶；其余（中文/数字/符号）→ `#` 桶，
            `#` 桶内部按首字 Unicode 码点稳定排序。
        """
        domain = domain or "baike"
        sort = (sort or "alpha").strip().lower()
        if sort not in ("alpha", "count", "recent"):
            sort = "alpha"
        clauses = ["c.active=1", "c.kind='baike_def'", "c.domain=?"]
        args: list = [domain]
        if sub:
            clauses.append("c.sub=?")
            args.append(sub)
        if q:
            clauses.append("(c.term LIKE ? OR c.front LIKE ? OR c.back LIKE ?)")
            like = f"%{q}%"
            args += [like, like, like]
        w = " AND ".join(clauses)
        card_rows = self.con.execute(
            f"SELECT c.*, {self._STATE_COLS}, "
            f"CASE WHEN rs.card_id IS NULL OR COALESCE(rs.reps,0)=0 THEN 1 ELSE 0 END AS is_new "
            f"FROM cards c LEFT JOIN review_state rs ON rs.card_id=c.card_id WHERE {w}",
            tuple(args)).fetchall()

        trap_terms = {r[0] for r in self.con.execute(
            "SELECT DISTINCT term FROM cards WHERE active=1 AND kind='baike_trap' "
            "AND domain=?", (domain,))}
        if sub:
            trap_terms &= {r[0] for r in self.con.execute(
                "SELECT DISTINCT term FROM cards WHERE active=1 AND kind='baike_trap' "
                "AND domain=? AND sub=?", (domain, sub))}

        def bucket_of(term: str) -> str:
            head = term[:1].upper() if term else "#"
            return head if "A" <= head <= "Z" and head.isascii() else "#"

        def initial_of(term: str) -> str:
            return (term[:1].upper() if term else "#")

        items: list[dict] = []
        for r in card_rows:
            term = r["term"]
            items.append({
                "term": term, "card_id": r["card_id"], "initial": initial_of(term),
                "sub": r["sub"], "source_rel": r["source_rel"], "anchor": r["anchor"],
                "mastered": int(r["mastered"] or 0),
                "is_new": bool(r["is_new"]),
                "due_ts": float(r["due_ts"] or 0),
                "has_trap": term in trap_terms,
                "back": r["back"],
                "def_brief": (r["back"] or "").strip().replace("\n", " "),
            })

        buckets: dict[str, int] = {}
        for it in items:
            b = bucket_of(it["term"])
            it["bucket"] = b
            buckets[b] = buckets.get(b, 0) + 1
        bucket_list = [{"letter": k, "n": v} for k, v in sorted(buckets.items())]

        if letter and letter != "all":
            want = str(letter).strip().upper()
            if want == "#":
                items = [x for x in items if x["bucket"] == "#"]
            else:
                items = [x for x in items if x["bucket"] == want]

        if sort == "alpha":
            items.sort(key=lambda x: (ord(x["term"][0]) if x["term"] else 0, x["term"]))
        elif sort == "count":
            items.sort(key=lambda x: (-int(x["mastered"]), x["term"]))
        else:
            items.sort(key=lambda x: (x["source_rel"], x["term"]))

        groups: dict[str, dict] = {}
        for it in items:
            g = groups.setdefault(it["sub"], {
                "sub": it["sub"], "sub_label": self._sub_label(domain, it["sub"]),
                "hue": self._hue(domain), "items": []})
            g["items"].append(it)
        group_list = sorted(groups.values(), key=lambda g: g["sub_label"])

        flat: list[dict] = []
        for it in items:
            row = {k: v for k, v in it.items() if k != "back"}
            flat.append(row)
        return {"total": len(items), "domain": domain, "sub": sub or "", "sort": sort,
                "letter": letter or "all", "buckets": bucket_list,
                "groups": group_list, "items_flat": flat}

    # ---------- 命令面板 / 双链补全 ----------
    def palette_index(self, sig: str | None, content: Path, hooks: dict | None = None) -> dict:
        """命令面板索引：术语 / 文档 / 子域 / 命令 / 计数。

        sig 与当前语料指纹一致时返回 {"ok":True,"fresh":True}，前端可据此跳过重绘。
        """
        hooks = hooks or {}
        current = self._palette_sig(content)
        if sig and str(sig) == current:
            return {"fresh": True, "sig": current}

        # 不加 LIMIT：命令面板的卖点是「单一入口」，静默截断会让文档压根搜不到，
        # 且与 _palette_sig（按全量语料算）不一致 —— sig 变了列表却没变，前端重绘后仍缺项。
        terms = [{"name": _tidy(r[0]), "kind": "term", "n": int(r[1])} for r in self.con.execute(
            "SELECT term, COUNT(*) n FROM cards WHERE active=1 AND kind='baike_def' "
            "GROUP BY term ORDER BY term")]
        docs: list[dict] = []
        try:
            con = fts.open_db(self.indexes)
            try:
                for path_, _title in con.execute("SELECT path, title FROM docs ORDER BY path"):
                    docs.append({"name": _tidy(_title or ""), "rel": path_, "kind": "doc"})
            finally:
                con.close()
        except sqlite3.Error:
            docs = []
        subs: list[dict] = []
        getter = hooks.get("domains_cached")
        if callable(getter):
            try:
                for dom in getter():
                    for s in dom.get("subs", []):
                        subs.append({"id": f"{dom['id']}/{s['id']}", "name": s["label"],
                                     "kind": "sub", "domain": dom["id"]})
            except Exception:
                subs = []
        return {
            "sig": current, "fresh": False, "terms": terms, "docs": docs, "subs": subs,
            "commands": [dict(c) for c in PALETTE_COMMANDS],
            "counts": {"terms": len(terms), "docs": len(docs), "subs": len(subs),
                       "commands": len(PALETTE_COMMANDS)},
        }

    def _palette_sig(self, content: Path) -> str:
        try:
            treesig = kbstore._tree_sig(content)
        except OSError:
            treesig = ""
        try:
            n_cards = int(self.con.execute(
                "SELECT count(*) FROM cards WHERE active=1").fetchone()[0])
        except sqlite3.Error:
            n_cards = 0
        return hashlib.md5(f"{treesig}|{n_cards}".encode("utf-8")).hexdigest()[:16]

    def _suggest_pool(self) -> list[tuple[str, str, str]]:
        """双链补全/断链检查共用的候选集 [(name, rel, kind)]。

        B10：旧 wikilink_check 对每个断链调一次 wikilink_suggest —— 每次重开 FTS
        连接、全表扫 docs + 全量 GROUP BY cards 再取 Top1。一篇 12 处断链的草稿，
        编辑器一轮 400ms 防抖 = 全库扫 12 遍。现在候选集一次构建、逐断链本地打分。"""
        cands: list[tuple[str, str, str]] = []
        try:
            con = fts.open_db(self.indexes)
            try:
                for path_, _title in con.execute("SELECT path, title FROM docs"):
                    cands.append((_tidy(_title or ""), path_, "doc"))
            finally:
                con.close()
        except sqlite3.Error:
            pass
        for term, _freq in self.con.execute(
                "SELECT term, COUNT(*) n FROM cards WHERE active=1 AND kind='baike_def' "
                "GROUP BY term"):
            cands.append((term, "", "term"))
        return cands

    def wikilink_suggest(self, q: str, exclude: str | None = None, limit: int = 8) -> list[dict]:
        """双链补全候选：FTS 的 docs(path,title) + cards.term 去重合并。

        排序：精确相等 100 > 前缀 90 > 包含 70 > 子序列 50；同分按标题长度升序。
        """
        limit = max(1, min(int(limit or 8), 30))
        qn = str(q or "").strip()
        excluded = {x.strip() for x in str(exclude or "").split(",") if x.strip()}
        ql = qn.lower()
        seen_names: set[str] = set()
        scored: list[tuple[int, int, str, dict]] = []
        for name, rel, kind in self._suggest_pool():
            if not name or name in excluded:
                continue
            score = _wl_score(name, ql)
            if score < 0:
                continue
            if name in seen_names:
                continue
            seen_names.add(name)
            scored.append((-score, len(name), name,
                           {"name": name, "rel": rel, "kind": kind, "score": score,
                            "sub_label": self._rel_sub_label(rel)}))
        scored.sort(key=lambda x: (x[0], x[1], x[2]))
        return [x[3] for x in scored[:limit]]

    def wikilink_check(self, body: str) -> dict:
        """正文([[双链]]) 健康度检查：未解析项 + Top1 建议 + 行列坐标。"""
        raw_text = str(body or "")
        links = fts.extract_wikilinks(raw_text)
        if not links:
            return {"total": 0, "dead": [], "dead_n": 0}
        try:
            con = fts.open_db(self.indexes)
            try:
                maps = fts.resolve_maps_from_db(con)
            finally:
                con.close()
        except sqlite3.Error:
            maps = ({}, {}, {})
        # by_path 已由 fts.resolve_maps_from_db 统一成「去掉 .md 的完整相对路径 → 路径」，
        # 与 build_index / upsert_doc_in_index 同构（旧版这里要自己补一张别名表）
        by_path, by_stem, by_title = maps
        pool = self._suggest_pool()  # B10：整篇只构建一次候选集
        # 同名断链可能出现多次：建议按 raw 缓存，避免重复打分
        sug_cache: dict[str, tuple[str, int]] = {}
        dead: list[dict] = []
        for raw in links:
            target = fts.resolve_wikilink(raw, by_path, by_stem, by_title)
            if target:
                continue
            if raw not in sug_cache:
                sug_cache[raw] = _top_suggestion(raw, pool)
            sug_name, sug_score = sug_cache[raw]
            line, col = _locate(raw_text, raw)
            dead.append({"raw": raw, "line": line, "col": col,
                         "suggest": sug_name, "suggest_score": sug_score})
        return {"total": len(links), "dead": dead, "dead_n": len(dead)}

    # ---------- 标签/色相 ----------
    def _tax(self) -> dict | None:
        if self.content is None:
            return None
        try:
            return kbstore.load_taxonomy(self.content)
        except Exception:
            return None

    def _sub_label(self, domain: str, sub: str) -> str:
        tax = self._tax()
        if tax:
            return kbstore.sub_label(tax, domain, sub)
        return kbstore.SUB_LABELS.get(f"{domain}/{sub}", kbstore.SUB_LABELS.get(sub, sub))

    def _domain_label(self, domain: str) -> str:
        tax = self._tax()
        if tax:
            return kbstore.domain_label(tax, domain)
        return kbstore.DOMAIN_LABELS.get(domain, domain)

    def _hue(self, domain: str) -> int:
        tax = self._tax()
        if tax:
            return int(tax["hues"].get(domain, 158))
        return int(kbstore.GRAPH_HUES.get(domain, 158))

    def _rel_sub_label(self, rel: str) -> str:
        if not rel:
            return ""
        parts = rel.split("/")
        if len(parts) >= 3:
            return self._sub_label(parts[0], parts[1])
        if len(parts) == 2:
            return self._domain_label(parts[0])
        return ""


# ---------------- 模块级小工具 ----------------
def _safe_rollback(con: sqlite3.Connection) -> None:
    """回滚，且在没有活动事务时不炸（幂等的重试路径可能已提交过）。"""
    try:
        con.execute("ROLLBACK")
    except sqlite3.Error:
        pass


_CJK_PUNCT_CLASS = "，。；、！？：”’）】》%…·—"

_RE_SPACE_BEFORE_PUNCT = re.compile(rf"\s+([{_CJK_PUNCT_CLASS}])")
_RE_MULTI_SPACE = re.compile(r"\s{2,}")


def _tidy(text: str) -> str:
    """把 FTS 里「逐字插空格」的标题还原成能直接展示的样子。

    fts.cjk_clean 只处理「汉字 汉字」之间的空格，、
    trailing space 跟着汉字后面的标点前的空格留了下来（如 "KMP 算法 " / "AI 资产  · "），
    直接吐给前端会出现尾随空格与双空格。
    """
    s = fts.cjk_clean(str(text or ""))
    s = _RE_SPACE_BEFORE_PUNCT.sub(r"\1", s)
    s = _RE_MULTI_SPACE.sub(" ", s)
    return s.strip()


def _interleave_kinds(rows: list[dict]) -> list[dict]:
    """同 kind 的牌不要连着出：按原始顺序做稳定的轮转，避免复习变成「连续 5 张同款」。"""
    if len(rows) <= 2:
        return rows
    buckets: dict[str, list[dict]] = {}
    order: list[str] = []
    for r in rows:
        k = r.get("kind", "")
        if k not in buckets:
            buckets[k] = []
            order.append(k)
        buckets[k].append(r)
    if len(order) == 1:
        return rows
    out: list[dict] = []
    i = 0
    while len(out) < len(rows):
        for k in order:
            bucket = buckets[k]
            if i < len(bucket):
                out.append(bucket[i])
        i += 1
    return out


def _day_to_ts(day: str) -> float:
    return time.mktime(time.strptime(day + " 12:00:00", "%Y-%m-%d %H:%M:%S"))


def _is_subsequence(needle: str, hay: str) -> bool:
    it = iter(hay)
    return all(ch in it for ch in needle)


def _wl_score(name: str, ql: str) -> int:
    """双链候选统一打分：精确 100 > 前缀 90 > 包含 70 > 子序列 50 > 不匹配 -1。

    ql 为空（编辑器刚输入 [[ 就聚焦候选）返回 10 —— 与旧 wikilink_suggest 行为一致。"""
    nl = str(name or "").lower()
    if not ql:
        return 10
    if nl == ql:
        return 100
    if nl.startswith(ql):
        return 90
    if ql in nl:
        return 70
    if _is_subsequence(ql, nl):
        return 50
    return -1


def _top_suggestion(raw: str, pool: list[tuple[str, str, str]]) -> tuple[str, int]:
    """在共享候选集里为断链 raw 找 Top1 建议（纯本地，无 IO）。返回 (name, score)。"""
    ql = str(raw or "").strip().lower()
    best: tuple[str, int] = ("", 0)
    for name, _rel, _kind in pool:
        s = _wl_score(name, ql)
        if s > best[1] or (s == best[1] and best[0] and s > 0 and len(name) < len(best[0])):
            best = (name, s)
    return best


def _locate(text: str, target: str) -> tuple[int, int]:
    """返回 [[target 在正文里的 (行号, 列号)，均从 1 起；找不到返回 (0,0)。"""
    idx = text.find(f"[[{target}")
    if idx < 0:
        idx = text.find(target)
    if idx < 0:
        return 0, 0
    head = text[:idx]
    line = head.count("\n") + 1
    col = idx - (head.rfind("\n") + 1) + 1
    return line, col
