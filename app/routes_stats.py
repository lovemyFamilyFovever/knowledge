# -*- coding: utf-8 -*-
"""统计类接口：目录聚合树 / 全库统计 / 目录统计 / 单篇统计 / 标签合并 / 阅读上报。

统计只读语料 + 派生索引，写入的仅 /api/tag/merge（复用 store.merge_tag）与
/api/track（落 indexes/reading.db）。依赖经 flask.current_app.config 注入。
"""
import re
import time
from pathlib import Path

from flask import Blueprint, abort, current_app, jsonify, request

from app import store
from app.fts import build_index, extract_wikilinks, open_db
from app.store import (SKIP_DIRS, WRITABLE_EXTS, _tree_sig, domain_label,
                       find_doc, inbox_count, load_taxonomy, parse_frontmatter)

stats_bp = Blueprint("stats", __name__)


def _hooks() -> dict:
    return current_app.config.get("KB_HOOKS") or {}


def _content() -> Path:
    return Path(current_app.config["CONTENT"])


def _indexes() -> Path:
    return Path(current_app.config["INDEXES"])


def _domains_cached() -> list[dict]:
    return _hooks()["domains_cached"]()


def _safe_rel(rel: str, exts):
    return _hooks()["safe_rel"](rel, exts)


# ---------------- 语料聚合（B18）：按树签名缓存，三个统计端点共用 ----------------
_AGG: dict = {"sig": None, "data": None}


def _corpus_agg() -> dict:
    """{(domain, sub): {"cjk": int, "untagged": int, "tags": {tag:n},
    "newest": (title, mtime), "mtime": float}}

    旧实现里 /api/globalstats、/api/dir/tree、/api/substats 各自全库逐篇
    read_text + parse（2000+ 文件 IO，弹窗打开卡数秒；目录统计里每切一个
    兄弟目录再来一轮）。字数只需在语料变化后重算：树签名一致时直接复用缓存，
    标签/收藏/未打标/mtime 全部取自内存中的分类树，不再读盘。"""
    content = _content()
    try:
        sig = _tree_sig(content)
    except OSError:
        sig = None
    if sig is not None and _AGG["sig"] == sig and _AGG["data"] is not None:
        return _AGG["data"]
    data: dict[tuple[str, str], dict] = {}
    for dom in _domains_cached():
        for sobj in dom["subs"]:
            cjk = 0
            untagged = 0
            tag_map: dict[str, int] = {}
            newest: tuple[str, float] = ("", 0.0)
            for d in sobj["docs"]:
                tags = d.get("tags") or []
                if tags:
                    for t in tags:
                        tag_map[str(t)] = tag_map.get(str(t), 0) + 1
                else:
                    untagged += 1
                mt = float(d.get("mtime") or 0.0)
                if mt > newest[1]:
                    newest = (str(d.get("title") or ""), mt)
                p = find_doc(content, dom["id"], sobj["id"], d["name"])
                if p:
                    try:
                        _, body = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
                    except OSError:
                        continue
                    cjk += len(re.findall(r"[\u4e00-\u9fff]", body))
            data[(dom["id"], sobj["id"])] = {"cjk": cjk, "untagged": untagged,
                                             "tags": tag_map, "newest": newest}
    if sig is not None:
        _AGG["sig"], _AGG["data"] = sig, data
    return data


@stats_bp.get("/api/dir/tree")
def api_dir_tree():
    """移动弹窗/统计弹窗共用的目录聚合树：一次返回各域与子目录的
    篇数/总字数(CJK)/未打标数/最近更新时间，供前端渲染可展开树与排行。"""
    tax = load_taxonomy(_content())
    agg = _corpus_agg()
    domains = []
    for dom in _domains_cached():
        subs, dom_cjk, dom_untagged, dom_mtime = [], 0, 0, 0.0
        for sobj in dom["subs"]:
            a = agg.get((dom["id"], sobj["id"]), {"cjk": 0, "untagged": 0})
            cjk = a["cjk"]
            untagged = a["untagged"]
            mt = max((d["mtime"] for d in sobj["docs"]), default=0.0)
            subs.append({"id": sobj["id"], "label": sobj["label"], "n": sobj["n"],
                         "cjk": cjk, "untagged": untagged, "mtime": int(mt)})
            dom_cjk += cjk
            dom_untagged += untagged
            dom_mtime = max(dom_mtime, mt)
        domains.append({"id": dom["id"], "label": domain_label(tax, dom["id"]), "n": dom["n"],
                        "cjk": dom_cjk, "untagged": dom_untagged, "mtime": int(dom_mtime),
                        "subs": sorted(subs, key=lambda x: -x["n"])})
    return jsonify({"domains": domains})


@stats_bp.get("/api/globalstats")
def api_globalstats():
    """全库聚合统计（顶栏全局「统计」按钮）：总量 / 总字数 / 各域分布 /
    标签覆盖率与 Top 标签 / 双链健康度。与目录统计共用同一套 .ss-* 视觉。"""
    content = _content()
    domains = _domains_cached()
    tax = load_taxonomy(content)
    agg = _corpus_agg()
    n_docs = n_tagged = total_cjk = untagged = fav = 0
    tag_count: dict[str, int] = {}
    per_domain = []
    for dom in domains:
        dom_cjk = dom_untag = 0
        for sobj in dom["subs"]:
            a = agg.get((dom["id"], sobj["id"]),
                        {"cjk": 0, "untagged": 0, "tags": {}})
            total_cjk += a["cjk"]
            dom_cjk += a["cjk"]
            untagged += a["untagged"]
            dom_untag += a["untagged"]
            for t, n in (a.get("tags") or {}).items():
                tag_count[t] = tag_count.get(t, 0) + n
            for d in sobj["docs"]:
                n_docs += 1
                if d.get("favorite"):
                    fav += 1
                if d.get("tags"):
                    n_tagged += 1
        per_domain.append({"id": dom["id"], "label": domain_label(tax, dom["id"]),
                           "n": dom["n"], "cjk": dom_cjk, "untagged": dom_untag})
    n_html = sum(1 for p in content.rglob("*.html")
                 if not any(part in SKIP_DIRS or part.startswith("_") for part in p.parts))
    n_links = n_dead = dead_docs = 0
    try:
        con = open_db(_indexes())
        try:
            n_links, = con.execute("SELECT count(*) FROM links").fetchone()
            n_dead, = con.execute("SELECT count(*) FROM links WHERE resolved=0").fetchone()
            dead_docs, = con.execute("SELECT count(DISTINCT src) FROM links WHERE resolved=0").fetchone()
        finally:
            con.close()
    except Exception:
        pass  # FTS 索引缺失/损坏时双链健康度缺省为 0，不阻塞统计弹窗
    top_tags = [{"tag": t, "n": n} for t, n in sorted(tag_count.items(), key=lambda kv: -kv[1])[:10]]
    marks = {"read_done": 0, "mastered_docs": 0}
    ReadingStore = _hooks().get("ReadingStore")
    if ReadingStore is not None:
        try:
            rs = ReadingStore(_indexes())
            try:
                marks = rs.marks_counts()
            finally:
                rs.close()
        except Exception:
            pass  # 统计弹窗不因标记表缺失而失败
    return jsonify({
        "n_docs": n_docs, "n_html": n_html, "n_fav": fav, "inbox": inbox_count(content),
        "total_cjk": total_cjk, "untagged": untagged,
        "tagged_pct": round(100 * n_tagged / max(1, n_docs)),
        "top_tags": top_tags, "n_tag_types": len(tag_count),
        "domains": per_domain,
        "links": {"total": n_links, "dead": n_dead, "dead_docs": dead_docs},
        "marks": marks,
    })


@stats_bp.get("/api/substats")
def api_substats():
    """目录级统计：某 domain/sub 下所有文档的篇数/字数(CJK)/标签分布/最近更新。"""
    content = _content()
    domains = _domains_cached()
    tax = load_taxonomy(content)
    dom = next((d for d in domains if d["id"] == request.args.get("domain", "")), None)
    sobj = next((s for s in dom["subs"] if s["id"] == request.args.get("sub", "")), None) if dom else None
    if not sobj:
        return jsonify({"error": "not found"}), 404
    a = _corpus_agg().get((dom["id"], sobj["id"]),
                          {"cjk": 0, "untagged": 0, "tags": {}, "newest": ("", 0.0)})
    total_cjk = a["cjk"]
    newest = a["newest"]
    tags_sorted = sorted(a["tags"].items(), key=lambda x: -x[1])[:12]
    return jsonify({
        "domain": dom["id"], "domain_label": domain_label(tax, dom["id"]),
        "sub": sobj["id"], "label": sobj["label"],
        "n_docs": sobj["n"], "total_cjk": total_cjk,
        "avg_cjk": round(total_cjk / max(1, sobj["n"])),
        "tags": [{"tag": t, "n": n} for t, n in tags_sorted],
        "n_untagged": a["untagged"],
        "newest": {"title": newest[0],
                   "when": time.strftime("%Y-%m-%d %H:%M", time.localtime(newest[1])) if newest[1] else "—"},
    })


@stats_bp.get("/api/stats")
def api_stats():
    """文档统计：字数/行数/标题数/代码块数/双链数/标签/收录日期/文件大小。"""
    content = _content()
    p = _safe_rel(request.args.get("path", ""), WRITABLE_EXTS)
    if not p.is_file():
        abort(404, "文档不存在")
    raw = p.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(raw)
    headings = len(re.findall(r"^#{1,6}\s+", body, re.M))
    code_blocks = len(re.findall(r"^```", body, re.M)) // 2
    links = len(extract_wikilinks(body))
    cjk_n = len(re.findall(r"[\u4e00-\u9fff]", body))
    words = len(re.findall(r"[A-Za-z0-9_]+", body))
    st = p.stat()
    return jsonify({
        "path": p.relative_to(content.resolve()).as_posix(),
        "title": str(fm.get("title") or p.stem),
        "tags": fm.get("tags", []) if isinstance(fm.get("tags"), list) else [],
        "source": str(fm.get("source", "")),
        "collected": str(fm.get("collected", "")),
        "chars": len(body), "cjk": cjk_n, "words": words,
        "lines": body.count("\n") + 1,
        "headings": headings, "code_blocks": code_blocks, "wikilinks": links,
        "size": st.st_size,
        "mtime": int(st.st_mtime),
    })


def _rel_key(path: str):
    """统计/标记的 path 主键归一（B22）：空、绝对路径、含 .. 一律拒绝。

    刻意不校验「文件必须存在于语料树」——移动前的历史事件引用的就是旧 path，
    仍需可查；这里只挡注入/越界字符串。"""
    s = str(path or "").strip().replace("\\", "/")
    if not s or s.startswith("/") or ".." in s.split("/"):
        return None
    return s


@stats_bp.get("/api/docmark")
def api_docmark_get():
    """单篇文档的已读/已掌握标记（存 indexes/reading.db 的 doc_marks，不进 frontmatter）。"""
    path = _rel_key(request.args.get("path", ""))
    if not path:
        return jsonify({"ok": False, "error": "BAD_PARAM", "detail": "path 必填且不得越界"}), 400
    ReadingStore = _hooks().get("ReadingStore")
    if ReadingStore is None:
        return jsonify({"ok": True, "read": False, "mastered": False})
    rs = ReadingStore(_indexes())
    try:
        m = rs.get_mark(path)
    finally:
        rs.close()
    return jsonify({"ok": True, **m})


@stats_bp.post("/api/docmark")
def api_docmark_set():
    """切换已读(read)/已掌握(mastered)。掌握蕴含已读；取消已读连掌握一起取消。"""
    ReadingStore = _hooks().get("ReadingStore")
    if ReadingStore is None:
        return jsonify({"ok": False, "error": "UNAVAILABLE", "detail": "阅读统计组件不可用"}), 503
    data = request.get_json(force=True, silent=True) or {}
    path = _rel_key(data.get("path", ""))
    kind = str(data.get("mark", ""))
    on = bool(data.get("on", True))
    if not path or kind not in ("read", "mastered"):
        return jsonify({"ok": False, "error": "BAD_PARAM", "detail": "path 与 mark(read|mastered) 必填"}), 400
    rs = ReadingStore(_indexes())
    try:
        m = rs.set_mark(path, kind, on)
    finally:
        rs.close()
    return jsonify({"ok": True, **m})


@stats_bp.post("/api/tag/merge")
def api_tag_merge():
    """标签合并（复用 store.merge_tag；apply=true 才写盘并重建 FTS）。
    返回受影响文档清单供前端确认框展示。"""
    content = _content()
    data = request.get_json(force=True)
    src = str(data.get("src", "")).strip()
    dst = str(data.get("dst", "")).strip()
    if not src or not dst:
        return jsonify({"ok": False, "error": "src/dst required"}), 400
    r = store.merge_tag(content, src, dst, apply=bool(data.get("apply")))
    if r["apply"]:
        build_index(content, _indexes())
    return jsonify({"ok": True, **r})


@stats_bp.post("/api/track")
def api_track():
    """阅读事件上报；组件缺失/非法入参一律静默成功（统计永不妨碍阅读）。"""
    ReadingStore = _hooks().get("ReadingStore")
    if ReadingStore is None:
        return jsonify({"ok": True, "tracked": False})
    data = request.get_json(force=True, silent=True) or {}
    path = _rel_key(data.get("path", ""))
    event = str(data.get("event", ""))
    if not path or event not in ("open", "read_minute", "finish"):
        return jsonify({"ok": True, "tracked": False})
    title = ""
    # 从路径安全地取标题：仅当该路径确实在语料树内
    try:
        pp = _safe_rel(path, WRITABLE_EXTS)
        if pp.is_file():
            fm2, _ = parse_frontmatter(pp.read_text(encoding="utf-8", errors="replace"))
            title = str(fm2.get("title") or pp.stem)
    except Exception:
        title = path.rsplit("/", 1)[-1][:-3] if path.endswith(".md") else path
    seconds = max(0, min(int(data.get("seconds") or 0), 3600))
    rs = ReadingStore(_indexes())
    try:
        tracked = rs.track(path, title, event, seconds)
    finally:
        rs.close()
    return jsonify({"ok": True, "tracked": bool(tracked)})


def register(app, hooks: dict):
    """由 app.py 调用：注入依赖 + 挂载蓝图。"""
    app.config.setdefault("KB_HOOKS", {}).update(hooks)
    app.register_blueprint(stats_bp)
