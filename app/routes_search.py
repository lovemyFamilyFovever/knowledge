# -*- coding: utf-8 -*-
"""搜索增强 + 术语门户 路由 —— 命令面板索引、双链补全、术语百科、统一检索。

依赖注入方式同 routes_learn.py：一切通过 flask.current_app.config，
严禁 from app.app import（循环导入）。
"""
import re
import time
from functools import wraps
from pathlib import Path
from urllib.parse import quote

from flask import Blueprint, current_app, jsonify, render_template, request

from app import fts
from app.fts import _clean_snippet
from app.learn import BadParam, BadQuery, LearnError, LearnStore

try:  # RAG 是可选依赖：缺失时语义检索降级为 FTS / 命令面板照常工作
    from app.rag import query_rag
    _RAG_IMPORT_ERROR = None
except Exception as _e:  # pragma: no cover - 视安装情况而定
    query_rag = None
    _RAG_IMPORT_ERROR = str(_e)

search_bp = Blueprint("search", __name__)


# ---------------- 工具 ----------------
def _hooks() -> dict:
    return current_app.config.get("KB_HOOKS") or {}


def _content() -> Path:
    return Path(current_app.config["CONTENT"])


def _indexes() -> Path:
    return Path(current_app.config["INDEXES"])


def _guard(fn):
    """把服务层异常翻译成统一错误信封；未预期的异常留痕，不裸 500。"""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except LearnError as e:
            return jsonify({"ok": False, "error": e.code, "detail": e.detail}), e.http
        except Exception as e:  # pragma: no cover - 兜底
            current_app.logger.warning("search route failed: %s", e, exc_info=True)
            return jsonify({"ok": False, "error": "INTERNAL",
                            "detail": str(e)[:200]}), 500

    return wrapper


def _sub_label(domain: str, sub: str) -> str:
    from app.store import SUB_LABELS, load_taxonomy, sub_label
    try:
        tax = load_taxonomy(_content())
        return sub_label(tax, domain, sub)
    except Exception:
        return SUB_LABELS.get(f"{domain}/{sub}", SUB_LABELS.get(sub, sub))


def _domain_label(domain: str) -> str:
    from app.store import DOMAIN_LABELS, domain_label, load_taxonomy
    try:
        tax = load_taxonomy(_content())
        return domain_label(tax, domain)
    except Exception:
        return DOMAIN_LABELS.get(domain, domain)


def doc_url(rel: str) -> str:
    """与 static/app.js 的 docUrl() 完全一致的两级/三级处理。"""
    segs = [x for x in str(rel or "").split("/") if x]
    if segs and segs[-1].endswith(".md"):
        segs[-1] = segs[-1][:-3]
    if len(segs) == 2:
        segs = [segs[0], "_root", segs[1]]
    return "/doc/" + "/".join(quote(x) for x in segs)


def _doc_meta_map() -> dict:
    """rel -> {title, tags, domain, sub}：来自 domains_cached（唯一事实源的树扫描）。"""
    getter = _hooks().get("domains_cached")
    out: dict = {}
    if not callable(getter):
        return out
    try:
        domains = getter()
    except Exception:
        return out
    for dom in domains:
        for sobj in dom.get("subs", []):
            for d in sobj.get("docs", []):
                rel = f"{dom['id']}/{sobj['id']}/{d['file']}" if sobj["id"] != "_root" \
                    else f"{dom['id']}/{d['file']}"
                out[rel] = {"title": d.get("title") or "",
                            "tags": list(d.get("tags") or []),
                            "domain": dom["id"], "sub": sobj["id"]}
    return out


def _rank_title(title: str, query: str) -> tuple[float, str]:
    """按「置顶规则」给命中定级：(score, match)。

    精确相等 > 标题前缀 > 标题包含 > 标签命中 > 正文命中。
    这里的「精确」含两种情形（都算用户显然在找这篇）：
        ① 整个查询词 == 标题（去空白/大小写后）
        ② 查询词 == 标题的**首个完整词条** —— 搜 "KMP" 命中 "KMP 算法" 就属此类，
           否则这条语料永远只能落到 prefix，与直觉不符。
    """
    tl = re.sub(r"\s+", " ", str(title or "")).strip().lower()
    ql = re.sub(r"\s+", " ", str(query or "")).strip().lower()
    if not tl or not ql:
        return 0.45, "body"
    if tl == ql:
        return 1.0, "exact"
    head = re.match(r"([0-9A-Za-z_+\-#.]+)", tl)
    if head and head.group(1).lower() == ql:
        return 1.0, "exact"
    ct, cq = tl.replace(" ", ""), ql.replace(" ", "")
    if ct == cq:
        return 1.0, "exact"
    if tl.startswith(ql) or ct.startswith(cq):
        return 0.90, "prefix"
    if ql in tl or cq in ct:
        return 0.75, "contains"
    return 0.45, "body"


_RE_SPACE_BEFORE_PUNCT = re.compile(r"\s+([，。；、！？：”’）】》%…·—])")
_RE_MULTI_SPACE = re.compile(r"\s{2,}")


def _snippet(text: str, n: int = 140) -> str:
    s = (text or "").replace("\n", " ").strip()
    return s[:n] + ("…" if len(s) > n else "")


# hybrid 归一化权重（阶段5 授权默认值）：FTS 相关性权重 0.6 / 语义相似 0.4。
# 归一化：两路分数各自 min-max 到 [0,1] 后加权求和；分母带 ε 防 0 除。
HYBRID_W_FTS = 0.6
HYBRID_W_SEM = 0.4
_HYBRID_EPS = 1e-9


def _tidy(text: str) -> str:
    """还原 FTS「逐字插空格」留下的空格（保留 <mark> 高亮标签本身）。"""
    s = _RE_SPACE_BEFORE_PUNCT.sub(r"\1", str(text or ""))
    return _RE_MULTI_SPACE.sub(" ", s).strip()


# ---------------- 双链补全 ----------------
@search_bp.get("/api/wikilink/suggest")
@_guard
def api_wikilink_suggest():
    q = (request.args.get("q") or "").strip()
    limit = 8
    try:
        limit = max(1, min(int(request.args.get("limit", 8)), 30))
    except (TypeError, ValueError):
        pass
    exclude = request.args.get("exclude") or None
    ls = LearnStore(_indexes(), _content())
    try:
        items = ls.wikilink_suggest(q, exclude=exclude, limit=limit)
    finally:
        ls.close()
    return jsonify({"ok": True, "items": items, "q": q})


@search_bp.post("/api/wikilink/check")
@_guard
def api_wikilink_check():
    """检查正文里的 [[双链]] 哪些没落到文档上，并给 Top1 建议。"""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = request.form.to_dict() if request.form else {}
    body = str(data.get("body") or "").strip()
    if not body:
        raise BadParam("body 必填（待检查的正文）")
    path = str(data.get("path") or "").strip()
    if path:
        safe_rel = _hooks().get("safe_rel")
        if not callable(safe_rel):
            raise BadParam("当前服务未提供 safe_rel，无法校验 path")
        try:
            safe_rel(path)
        except Exception as e:
            raise BadParam(f"path 越出了 content/：{e}") from None
    ls = LearnStore(_indexes(), _content())
    try:
        r = ls.wikilink_check(body)
    finally:
        ls.close()
    if path:
        # 自指（文档链自己）不算断链：改名后 [[旧标题]] 解析不到自己是预期内的噪音，
        # 不该出现在「顺手修掉断链」的提示里。旧实现这行是 `if True` 占位死代码。
        own = path.replace("\\", "/").rstrip("/").rsplit(".md", 1)[0].rsplit("/", 1)[-1].strip()
        r["dead"] = [d for d in r["dead"] if str(d.get("raw") or "").strip() != own]
        r["dead_n"] = len(r["dead"])
    return jsonify({"ok": True, "total": r["total"], "dead": r["dead"],
                    "dead_n": r["dead_n"]})


# ---------------- 命令面板 ----------------
@search_bp.get("/api/palette/index")
@_guard
def api_palette_index():
    """命令面板索引。sig 与语料指纹一致时返回 {"ok":true,"fresh":true}，前端可跳过重绘。"""
    sig = request.args.get("sig") or None
    ls = LearnStore(_indexes(), _content())
    try:
        r = ls.palette_index(sig, _content(), _hooks())
    finally:
        ls.close()
    return jsonify({"ok": True, **r})


# ---------------- 术语门户 ----------------
@search_bp.get("/api/glossary")
@_guard
def api_glossary():
    """术语百科：A–Z 分桶 + 按子域分组。无 pypinyin 依赖（离线是硬约束）。"""
    domain = request.args.get("domain") or "baike"
    sub = request.args.get("sub") or None
    letter = request.args.get("letter") or None
    sort = request.args.get("sort") or "alpha"
    q = request.args.get("q") or None
    ls = LearnStore(_indexes(), _content())
    try:
        ls.ensure_synced(_content())
        r = ls.glossary(domain=domain, sub=sub, letter=letter, sort=sort, q=q)
    finally:
        ls.close()

    def _enrich(item: dict) -> dict:
        row = dict(item)
        row["url"] = doc_url(row.get("source_rel") or "")
        row.pop("back", None)
        return row

    for g in r["groups"]:
        g["items"] = [_enrich(x) for x in g["items"]]
    r["items_flat"] = [_enrich(x) for x in r["items_flat"]]
    r.pop("back", None)
    return jsonify({"ok": True, **r})


@search_bp.get("/glossary")
def page_glossary():
    from app.store import inbox_count, md_files
    return render_template("glossary.html", page="glossary",
                           inbox_n=inbox_count(_content()),
                           n_md=sum(1 for _ in md_files(_content())))


# ---------------- 统一检索 ----------------
@search_bp.get("/api/search")
@_guard
def api_search():
    """统一检索（阶段5 STEP2 引擎参数化）。

    engine=fts|semantic|hybrid（默认 hybrid）；显式 `?` 前缀仍强制语义。
    hybrid：FTS 与语义两路各自 min-max 归一化后按 HYBRID_W_FTS/HYBRID_W_SEM
    加权合并，每条并列输出 score_fts / score_semantic（原始分保留在各自字段）。
    置顶规则不变：title 精确相等 > 前缀 > 包含 > body；精确命中进 exact[]。
    """
    t0 = time.perf_counter()
    q = (request.args.get("q") or "").strip()
    if not q:
        raise BadQuery("q 必填")
    engine = (request.args.get("engine") or "fts").strip().lower()
    if engine not in ("fts", "semantic", "hybrid"):
        engine = "hybrid"
    try:
        limit = max(1, min(int(request.args.get("limit", 30)), 100))
    except (TypeError, ValueError):
        limit = 30
    domain = request.args.get("domain") or None
    sub = request.args.get("sub") or None
    tag = request.args.get("tag") or None
    # B19：分面筛选支持逗号多值（domain=a,b / sub=dom/x,dom/y / tag=t1,t2），
    # 前端多选全部传给服务端，过滤计数只有一个真相。旧实现只认单值，
    # 多选时前端本地过滤、meta 却显示服务端总数，两头口径对不上。
    f_doms = {x.strip() for x in (domain or "").split(",") if x.strip()}
    f_subs = {x.strip() for x in (sub or "").split(",") if x.strip()}
    f_tags = {x.strip() for x in (tag or "").split(",") if x.strip()}

    def _pass(d: str, s: str, tags: list) -> bool:
        if f_doms and d not in f_doms:
            return False
        if f_subs and s not in f_subs and f"{d}/{s}" not in f_subs:
            return False
        if f_tags and not (f_tags & {str(t) for t in tags}):
            return False
        return True

    raw_is_sem = q.startswith("?")
    engine = "semantic" if raw_is_sem else engine  # ? 前缀强制语义（向后兼容）
    query = q[1:].strip() if raw_is_sem else q
    if not query:
        raise BadQuery("q 只有 `?` 没有实质查询词")

    meta = _doc_meta_map()
    emb = rstore = None
    rag_error = None
    semantic_available = False
    if engine in ("semantic", "hybrid"):
        get_rag = _hooks().get("get_rag")
        if callable(get_rag):
            try:
                emb, rstore = get_rag()
            except Exception as e:
                rag_error = f"RAG 初始化失败：{e}"
        if emb is None or rstore is None:
            rag_error = rag_error or _RAG_IMPORT_ERROR or "语义检索不可用"
        else:
            semantic_available = True

    items: list[dict] = []
    mode = "fts"
    rag_ms = None
    fts_ms = None
    sem_items: list[dict] = []
    if engine in ("semantic", "hybrid") and emb is not None and rstore is not None:
        rag_t0 = time.perf_counter()
        try:
            hits = query_rag(rstore, emb, query, k=limit * 2)
        except Exception as e:
            rag_error = f"语义检索失败：{e}"
        else:
            rag_ms = round((time.perf_counter() - rag_t0) * 1000)
            if engine == "semantic":
                mode = "semantic"
            seen: set[str] = set()
            for h in hits:
                f = h.get("file") or ""
                if f in seen:
                    continue
                seen.add(f)
                info = meta.get(f, {})
                d = info.get("domain") or f.split("/")[0]
                s = info.get("sub") or (f.split("/")[1] if f.count("/") > 1 else "_root")
                tags = list(info.get("tags") or [])
                if not _pass(d, s, tags):
                    continue
                sem_items.append({
                    "path": f,
                    "title": info.get("title") or h.get("title") or f,
                    "url": h.get("url") or doc_url(f),
                    "snippet": _clean_snippet(_snippet(h.get("contents") or "", 160)),
                    "score_label": f"{float(h.get('score') or 0):.2f}",
                    "score": round(float(h.get("score") or 0), 4),
                    "domain": d,
                    "sub": s,
                    "sub_label": _sub_label(info.get("domain") or "", info.get("sub") or ""),
                    "tags": tags,
                    "match": "semantic",
                })
    if engine in ("semantic", "hybrid") and sem_items and mode != "semantic":
        # hybrid：语义路成功但 engine 仍是 hybrid → 记账后继续走 FTS 路
        pass
    elif sem_items and mode == "semantic":
        items = sem_items
    if mode == "fts":
        fts_t0 = time.perf_counter()
        rows = fts.search(_indexes(), query, limit=limit * 4) or []
        fts_ms = round((time.perf_counter() - fts_t0) * 1000)
        needle = query.lower()
        for r in rows:
            p = r.get("path") or ""
            info = meta.get(p, {})
            d = info.get("domain") or (p.split("/")[0] if p else "")
            s = info.get("sub") or (p.split("/")[1] if p.count("/") > 1 else "_root")
            tags = list(info.get("tags") or [])
            if not _pass(d, s, tags):
                continue
            # 优先用树扫描里的原始标题（FTS 的 title 列做过 CJK 逐字插空格，比对前需还原）
            title = (info.get("title") or r.get("title") or "").strip()
            score, match = _rank_title(title, query)
            if match == "body" and any(needle in str(t).lower() for t in tags):
                score, match = 0.60, "tag"
            items.append({
                "path": p, "title": title, "url": doc_url(p),
                "snippet": _tidy(r.get("snippet") or ""),
                "score_label": f"{score:.2f}", "score": score,
                "domain": d, "sub": s, "sub_label": _sub_label(d, s),
                "tags": tags, "match": match,
                "hit_in_snippet": r.get("hit_in_snippet", -1),
            })
        items.sort(key=lambda x: (-float(x.get("score") or 0), str(x.get("title") or "")))

    # ---- hybrid 合并（阶段5 授权范围 #1）：两路归一化 + 加权 ----
    if engine == "hybrid" and (items or sem_items):
        def _norm(pairs: list[tuple[str, float]]) -> dict[str, float]:
            if not pairs:
                return {}
            vals = [v for _, v in pairs]
            lo, hi = min(vals), max(vals)
            span = (hi - lo) or _HYBRID_EPS
            return {k: (v - lo) / span for k, v in pairs}

        fts_n = _norm([(x["path"], float(x.get("score") or 0)) for x in items])
        sem_n = _norm([(x["path"], float(x.get("score") or 0)) for x in sem_items])

        merged: dict[str, dict] = {}

        def _absorb(item: dict, road: str):
            """把一路结果并进 merged：首到者建档，后到者补另一路分数/摘要。"""
            path_ = item["path"]
            score_raw = float(item.get("score") or 0)
            if path_ not in merged:
                it = dict(item)
                it.pop("_w", None)
                it["score_fts"] = score_raw if road == "fts" else None
                it["score_semantic"] = score_raw if road == "sem" else None
                merged[path_] = it
                return
            cur = merged[path_]
            if road == "fts":
                if cur.get("score_fts") is None:
                    cur["score_fts"] = score_raw
                # FTS snippet 带 <mark>，信息量更高 → 覆盖
                if item.get("snippet"):
                    cur["snippet"] = item["snippet"]
                if cur.get("hit_in_snippet") in (None, -1):
                    cur["hit_in_snippet"] = item.get("hit_in_snippet", -1)
                if item.get("match") in ("exact", "prefix", "contains") and cur.get("match") in ("semantic", "body", None):
                    cur["match"] = item["match"]
            else:
                if cur.get("score_semantic") is None:
                    cur["score_semantic"] = score_raw

        for it in sem_items:
            _absorb(it, "sem")
        for it in items:
            _absorb(it, "fts")

        items = list(merged.values())
        for it in items:
            wf = HYBRID_W_FTS * fts_n.get(it["path"], 0.0) if it.get("score_fts") is not None else 0.0
            ws = HYBRID_W_SEM * sem_n.get(it["path"], 0.0) if it.get("score_semantic") is not None else 0.0
            it["score"] = round(wf + ws, 4)
            parts = []
            if it.get("score_fts") is not None:
                parts.append(f"FTS {it['score_fts']:.2f}")
            if it.get("score_semantic") is not None:
                parts.append(f"语义 {it['score_semantic']:.2f}")
            if parts:
                it["score_label"] = " + ".join(parts)
            if it.get("match") == "semantic":
                it["match"] = "body"
        items.sort(key=lambda x: (-float(x.get("score") or 0), str(x.get("title") or "")))
        mode = "hybrid"

    exact = [x for x in items if x.get("match") == "exact"]
    hits_out = [x for x in items if x.get("match") != "exact"]
    total = len(items)

    facets = {"domains": {}, "subs": {}, "tags": {}}
    for x in items:
        facets["domains"][x["domain"]] = facets["domains"].get(x["domain"], 0) + 1
        key = f"{x['domain']}/{x['sub']}"
        facets["subs"][key] = facets["subs"].get(key, 0) + 1
        for t in x["tags"]:
            facets["tags"][t] = facets["tags"].get(t, 0) + 1
    facets["domains"] = [{"id": k, "label": _domain_label(k), "n": v}
                         for k, v in sorted(facets["domains"].items(), key=lambda kv: -kv[1])]
    facets["subs"] = [{"id": k, "n": v}
                      for k, v in sorted(facets["subs"].items(), key=lambda kv: -kv[1])[:20]]
    facets["tags"] = [{"tag": k, "n": v}
                      for k, v in sorted(facets["tags"].items(), key=lambda kv: -kv[1])[:20]]

    payload = {
        "q": query, "raw_q": q, "mode": mode, "engine": engine, "total": total,
        "took_ms": round((time.perf_counter() - t0) * 1000),
        "exact": exact[:limit], "hits": hits_out[:max(0, limit - len(exact[:limit]))],
        "facets": facets, "semantic_available": semantic_available,
        "engines": {"fts_ms": fts_ms, "rag_ms": rag_ms},
    }
    if rag_error:
        payload["rag_error"] = rag_error
    return jsonify({"ok": True, **payload})


def register(app, hooks: dict):
    """由 app.py 调用：注入依赖 + 挂载蓝图。"""
    app.config.setdefault("KB_HOOKS", {}).update(hooks)
    app.register_blueprint(search_bp)
