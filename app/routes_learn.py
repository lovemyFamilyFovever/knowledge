# -*- coding: utf-8 -*-
"""学习 / 复习 / 门户 路由 —— Blueprint 形式挂在 app.py 上。

统一响应信封：
    成功 {"ok": true, ...业务字段}
    失败 {"ok": false, "error": "CODE", "detail": "人话"} + 对应 HTTP 码

错误码：BAD_PARAM 400 / BAD_Q 400 / BAD_CARD 404 / NOT_SYNCED 503 /
        SYNC_BUSY 409 / CORPUS_EMPTY 404 / PATH_ESCAPE 400 / RAG_UNAVAILABLE 503

路由内只能通过 flask.current_app.config 取依赖（**严禁 from app.app import**，循环导入）：
    config["CONTENT"] / ["INDEXES"] 由 create_app 写入
    config["KB_HOOKS"] 由 register() 注入 domains_cached / safe_rel
"""
import functools
import time
from pathlib import Path
from urllib.parse import quote

from flask import Blueprint, current_app, jsonify, render_template, request

from app.learn import (BadParam, BadQuery, CardNotFound, CorpusEmpty, LearnError,
                       LearnStore, SyncBusy)

learn_bp = Blueprint("learn", __name__)


# ---------------- 依赖注入与通用工具 ----------------
def _hooks() -> dict:
    return current_app.config.get("KB_HOOKS") or {}


def _content() -> Path:
    return Path(current_app.config["CONTENT"])


def _indexes() -> Path:
    return Path(current_app.config["INDEXES"])


def _sub_label(domain: str, sub: str) -> str:
    from app.store import SUB_LABELS, load_taxonomy, sub_label
    try:
        tax = load_taxonomy(_content())
        return sub_label(tax, domain, sub)
    except Exception:
        return SUB_LABELS.get(f"{domain}/{sub}", SUB_LABELS.get(sub, sub))


def doc_url(rel: str) -> str:
    """文档跳转 URL，与 static/app.js 里的 docUrl() 保持完全一致的两级/三级处理。"""
    rel = str(rel or "")
    segs = [x for x in rel.split("/") if x]
    if segs and segs[-1].endswith(".md"):
        segs[-1] = segs[-1][:-3]
    if len(segs) == 2:
        segs = [segs[0], "_root", segs[1]]
    return "/doc/" + "/".join(quote(x) for x in segs)


def _card_public(row: dict) -> dict:
    """卡片 → 前端契约对象（字段名固定，前端按此并行开发）。"""
    import json

    try:
        related = json.loads(row.get("related") or "[]")
    except (ValueError, TypeError):
        related = []
    tags = [x for x in str(row.get("tags") or "").split(",") if x]
    due_ts = float(row.get("due_ts") or 0)
    state = {
        "ef": round(float(row.get("ef") or 2.5), 4),
        "interval": int(row.get("interval") or 0),
        "reps": int(row.get("reps") or 0),
        "lapses": int(row.get("lapses") or 0),
        "due_ts": due_ts,
        "mastered": int(row.get("mastered") or 0),
        "is_new": bool(int(row.get("is_new") or 0)),
    }
    return {
        "card_id": row["card_id"], "kind": row["kind"], "term": row["term"],
        "front": row["front"], "back": row["back"], "hint": row.get("hint") or "",
        "source_rel": row["source_rel"], "anchor": row.get("anchor") or "",
        "url": doc_url(row.get("source_rel") or ""),
        "domain": row.get("domain") or "", "sub": row.get("sub") or "",
        "sub_label": _sub_label(row.get("domain") or "", row.get("sub") or ""),
        "tags": tags, "related": related,
        "difficulty": row.get("difficulty") or "",
        "has_answer": int(row.get("has_answer") or 0),
        "state": state,
    }


def _guard(fn):
    """把服务层异常翻译成统一错误信封；未预期的异常也留痕，不裸 500。"""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except LearnError as e:
            return jsonify({"ok": False, "error": e.code, "detail": e.detail}), e.http
        except Exception as e:  # pragma: no cover - 兜底，正常情况下不该发生
            current_app.logger.warning("learn route failed: %s", e, exc_info=True)
            return jsonify({"ok": False, "error": "INTERNAL",
                            "detail": str(e)[:200]}), 500

    return wrapper


def _bool_arg(name: str, default: bool = True) -> bool:
    v = request.args.get(name)
    if v is None:
        return default
    s = str(v).strip().lower()
    return default if s in ("", "true", "1", "yes", "on") else s in ("false", "0", "no", "off")


def _int_arg(name: str, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(int(request.args.get(name, default)), hi))
    except (TypeError, ValueError):
        return default


def _page_context(page: str) -> dict:
    """三个新页面共用的最小渲染上下文。"""
    content = _content()
    from app.store import inbox_count, md_files
    return {"page": page, "inbox_n": inbox_count(content),
            "n_md": sum(1 for _ in md_files(content))}


# ---------------- 接口 ----------------
@learn_bp.post("/api/learn/sync")
@_guard
def api_sync():
    """抽卡同步：扫描 baike/interview 语料重建卡片库（幂等，可反复调用）。"""
    data = request.get_json(silent=True) or {}
    force = str(data.get("force", request.args.get("force", ""))).strip().lower() in (
        "1", "true", "yes", "on")
    t0 = time.perf_counter()
    ls = LearnStore(_indexes(), _content())
    try:
        r = ls.sync(_content(), force=force)
    except SyncBusy:
        raise
    except CorpusEmpty:
        raise
    finally:
        ls.close()  # sync 是唯一会长期持锁的写路径，必须显式释放（Windows 文件锁）
    return jsonify({"ok": True, **{k: v for k, v in r.items()},
                    "took_ms": round((time.perf_counter() - t0) * 1000)})


@learn_bp.get("/api/learn/due")
@_guard
def api_due():
    """到期复习队列：到期卡按 due_ts 升序，新卡排最后且占比不超 new_ratio。"""
    kind = request.args.get("kind") or None
    domain = request.args.get("domain") or None
    sub = request.args.get("sub") or None
    if kind and kind not in ("baike_def", "baike_trap", "interview_qa"):
        raise BadParam(f"未知的卡片类型：{kind}")
    limit = _int_arg("limit", 20, 1, 200)
    try:
        new_ratio = float(request.args.get("new_ratio", 0.3))
    except (TypeError, ValueError):
        raise BadParam("new_ratio 必须是 0..1 的数") from None
    if not 0.0 <= new_ratio <= 1.0:
        raise BadParam("new_ratio 必须是 0..1 的数")
    include_new = _bool_arg("include_new", True)

    ls = LearnStore(_indexes(), _content())
    try:
        ls.ensure_synced(_content())
        r = ls.due(kind=kind, domain=domain, sub=sub, limit=limit,
                   include_new=include_new, new_ratio=new_ratio)
    finally:
        ls.close()
    cards = [_card_public(c) for c in r["cards"]]
    return jsonify({"ok": True, "cards": cards, "due_n": r["due_n"],
                    "new_n": r["new_n"], "total_n": r["total_n"], "limit": limit})


@learn_bp.get("/api/learn/mock")
@_guard
def api_mock():
    """模拟面试：从面试卡全库随机抽 n 张（不看排期，纯随机）。
    作答仍走 /api/learn/review —— 模拟即复习，会/不会照常推进 SM-2 排期。"""
    n = _int_arg("n", 10, 1, 50)
    ls = LearnStore(_indexes(), _content())
    try:
        ls.ensure_synced(_content())
        rows = ls.mock_cards(n)
    finally:
        ls.close()
    return jsonify({"ok": True, "n": len(rows), "cards": [_card_public(c) for c in rows]})


@learn_bp.post("/api/learn/review")
@_guard
def api_review():
    """提交一次 SM-2 评分。同一 (card_id, 秒级 ts) 幂等。"""
    data = request.get_json(silent=True) or {}
    card_id = str(data.get("card_id") or "").strip()
    if not card_id:
        raise BadParam("card_id 必填")
    if "q" not in data:
        raise BadQuery("q 必填（0..5）")
    try:
        q = int(data.get("q"))
    except (TypeError, ValueError):
        raise BadQuery("q 必须是 0..5 的整数") from None
    try:
        elapsed_ms = int(data.get("elapsed_ms") or 0)
    except (TypeError, ValueError):
        elapsed_ms = 0

    ls = LearnStore(_indexes(), _content())
    try:
        r = ls.submit_review(card_id, q, elapsed_ms)
    except CardNotFound:
        raise
    finally:
        ls.close()
    return jsonify({"ok": True, **r})


@learn_bp.get("/api/learn/mastery")
@_guard
def api_mastery():
    """掌握度：已掌握 interval>=21 且 reps>=3；learning=reps>0 未掌握；new=reps==0。"""
    scope = (request.args.get("scope") or "sub").strip().lower()
    if scope not in ("sub", "domain"):
        raise BadParam("scope 只能是 sub 或 domain")
    domain = request.args.get("domain") or None
    all_doms = (request.args.get("all") or "").strip().lower() in ("1", "true", "yes")
    ls = LearnStore(_indexes(), _content())
    try:
        ls.ensure_synced(_content())
        r = ls.mastery(scope=scope, domain=domain, all=all_doms)
    finally:
        ls.close()
    return jsonify({"ok": True, "scope": r["scope"], "items": r["items"],
                    "totals": r["totals"]})


@learn_bp.get("/api/learn/recent_read")
@_guard
def api_recent_read():
    """近 7 日阅读篇数（reading.db 只读派生查询；TOC sparkline 供数）。"""
    try:
        n = int(request.args.get("days", 7))
    except (TypeError, ValueError):
        n = 7
    rs = _hooks().get("ReadingStore")
    if rs is None:
        return jsonify({"ok": True, "days": []})
    rsx = rs(_indexes())
    try:
        days = rsx.recent_days(n)
    finally:
        rsx.close()
    return jsonify({"ok": True, "days": days})


@learn_bp.get("/api/learn/today")
@_guard
def api_today():
    """今日一张：优先到期复习卡 → 否则随机新卡 → 否则最近复习过的一张 + tip。"""
    domain = request.args.get("domain") or None
    ls = LearnStore(_indexes(), _content())
    try:
        ls.ensure_synced(_content())
        res = ls.today_card(domain=domain)
        if res["card"] is None:
            raise CorpusEmpty("还没有任何卡片，先调用 /api/learn/sync 抽卡")
        stats = ls.today_stats(domain=domain)
    finally:
        ls.close()
    return jsonify({"ok": True, "date": time.strftime("%Y-%m-%d"),
                    "card": _card_public(res["card"]), "stats": stats,
                    "tip": res["tip"]})


@learn_bp.get("/api/learn/cards")
@_guard
def api_cards():
    """卡片检索 / 后台浏览。"""
    q = request.args.get("q") or None
    kind = request.args.get("kind") or None
    if kind and kind not in ("baike_def", "baike_trap", "interview_qa"):
        raise BadParam(f"未知的卡片类型：{kind}")
    domain = request.args.get("domain") or None
    sub = request.args.get("sub") or None
    active = _bool_arg("active", True)
    offset = _int_arg("offset", 0, 0, 100000)
    limit = _int_arg("limit", 30, 1, 200)

    ls = LearnStore(_indexes(), _content())
    try:
        ls.ensure_synced(_content())
        r = ls.search_cards(q=q, kind=kind, domain=domain, sub=sub, active=active,
                            offset=offset, limit=limit)
    finally:
        ls.close()
    return jsonify({"ok": True, "total": r["total"], "offset": r["offset"],
                    "limit": r["limit"], "items": [_card_public(x) for x in r["items"]]})


@learn_bp.get("/api/learn/roam")
@_guard
def api_roam():
    """漫游：沿 [[相关术语]] BFS，未学的优先，返回路径与查不到卡片的「断头」术语。"""
    term = (request.args.get("from") or "").strip()
    if not term:
        raise BadParam("from 必填（起始术语）")
    n = _int_arg("n", 6, 1, 50)
    only_new = _bool_arg("only_new", False)

    ls = LearnStore(_indexes(), _content())
    try:
        ls.ensure_synced(_content())
        r = ls.roam(term, n=n, only_new=only_new)
    finally:
        ls.close()
    path = []
    for node in r["path"]:
        row = dict(node)
        row["url"] = doc_url(node.get("source_rel") or "")
        path.append(row)
    return jsonify({"ok": True, "path": path, "n": r["n"], "start": r["start"],
                    "dead_ends": r["dead_ends"]})


# ---------------- 页面 ----------------
@learn_bp.get("/review")
def page_review():
    return render_template("review.html", **_page_context("review"))


@learn_bp.get("/quiz")
def page_quiz():
    return render_template("quiz.html", **_page_context("quiz"))


def register(app, hooks: dict):
    """由 app.py 调用：注入依赖 + 挂载蓝图。"""
    app.config.setdefault("KB_HOOKS", {}).update(hooks)
    app.register_blueprint(learn_bp)
