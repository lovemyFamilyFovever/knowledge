# -*- coding: utf-8 -*-
"""知库 reader — Flask 应用：从 content/ 文件树直接服务知识语料。

content/ 的 Markdown/HTML 文件是唯一事实源；indexes/（index.db / rag.db）只是
派生缓存，随时可删可重建。编辑、收藏、备注全部写回文件系统，Obsidian 与本
应用共享同一份语料。

分层（2026-09-07 拆分）：
    app/store.py  语料层：frontmatter / 分类树 / 备注 / 分类学装载（_meta/taxonomy.json 为权威）
    app/fts.py    FTS5 全文索引 + [[双链]] 解析（派生，外科手术式更新）
    app/rag.py    语义检索：切块 / 嵌入 / sqlite-vec（派生，RAG_CODE_VERSION 管版本）
    app/app.py    本文件：路由与请求编排 + 单一 watcher 统一驱动两套索引同步

工厂模式：create_app(root) 便于测试指向临时语料目录。
"""
import json
import re
import sys
import threading
import time
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, send_file

# 直接以脚本方式运行（python app\app.py）时 sys.path[0] 是 app/ 目录而非项目根，
# 补上项目根保证 from app.xxx import 在两种启动方式下都能命中
_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app import store
from app.store import (  # noqa: F401  兼容旧引用（tests 直接 import app.app 的符号）
    DOMAIN_LABELS, GRAPH_HUES, SKIP_DIRS, SOURCE_LABELS, STATUS_LABELS,
    WRITABLE_EXTS, SERVABLE_EXTS, FM_RE,
    dump_frontmatter, find_doc, inbox_count, load_taxonomy, md_files,
    notes_path, obsidian_vault_connected, parse_frontmatter, read_notes,
    scan_corpus, _tree_sig,
)
from app.fts import (  # noqa: F401
    build_index, cjk_clean, cjk_space, extract_wikilinks, index_is_stale,
    open_db, remove_doc_from_index, resolve_maps_from_db, resolve_wikilink,
    search, upsert_doc_in_index,
)

# ---------------- 本地向量检索（可选依赖，缺失时自动降级纯 FTS） ----------------
try:
    from app.rag import (OnnxEmbedder, RagStore, query_rag, rag_status,
                         sync_rag)
    _RAG_IMPORT_ERROR = None
except Exception as _e:  # ImportError 及其依赖链上的任何加载失败
    OnnxEmbedder = RagStore = None
    query_rag = sync_rag = rag_status = None
    _RAG_IMPORT_ERROR = str(_e)

# 阅读统计（v1，设计定稿见 docs/统计数据模型-定稿.md；库损坏时静默降级为无统计）
try:
    from app.reading import ReadingStore
except Exception:
    ReadingStore = None


# ---------------- app factory ----------------
def create_app(root: Path | None = None) -> Flask:
    root = Path(root) if root else Path(
        __import__("os").environ.get("KB_ROOT") or Path(__file__).resolve().parents[1])
    content = root / "content"
    indexes = root / "indexes"
    app = Flask(__name__, root_path=str(root / "app"),
                template_folder=str(Path(__file__).parent / "templates"),
                static_folder=str(root / "static"), static_url_path="/static")
    app.config["CONTENT"] = content
    app.config["INDEXES"] = indexes
    app.config["ROOT"] = root
    app.config["TEMPLATES_AUTO_RELOAD"] = True  # 个人工具: 改模板即时生效

    if index_is_stale(content, indexes):
        build_index(content, indexes)

    # 向量检索组件：惰性初始化（首次调用时才加载 ONNX 会话）
    rag_state = {"embedder": None, "store": None, "tried": False}

    def get_rag():
        """返回 (embedder, store) 或 (None, None)。模型加载失败不拖垮阅读器。"""
        if rag_state["tried"]:
            return rag_state["embedder"], rag_state["store"]
        rag_state["tried"] = True
        if OnnxEmbedder is None or RagStore is None:
            return None, None
        try:
            rag_state["embedder"] = OnnxEmbedder(root / "app" / "rag_models")
            rag_state["store"] = RagStore(indexes)
        except Exception:
            rag_state["embedder"] = rag_state["store"] = None
        return rag_state["embedder"], rag_state["store"]

    # 单一 watcher：每 30 秒统一驱动 FTS 与向量索引的增量同步
    # （拆分前是两套独立轮询，失效判据不同步会导致短窗内搜索/语义结果矛盾）
    def _index_watcher():
        while True:
            time.sleep(30)
            try:
                if index_is_stale(content, indexes):
                    build_index(content, indexes)
            except Exception:
                pass  # 静默：索引重建失败不影响服务
            if rag_state["embedder"] is not None and rag_state["store"] is not None:
                try:
                    sync_rag(content, rag_state["embedder"], rag_state["store"])
                except Exception:
                    pass

    _watcher = threading.Thread(target=_index_watcher, daemon=True)
    _watcher.start()

    def corpus_stats() -> dict:
        domains = scan_corpus(content)
        n_md = sum(1 for _, _ in md_files(content))
        n_html = sum(1 for p in content.rglob("*.html")
                     if not any(part in SKIP_DIRS or part.startswith("_") for part in p.parts))
        fav = sum(1 for d in (doc for dom in domains for s in dom["subs"] for doc in s["docs"]) if d["favorite"])
        inbox = inbox_count(content)
        return {"domains": domains, "n_md": n_md, "n_html": n_html, "n_fav": fav, "inbox": inbox}

    def safe_rel(rel: str, exts=SERVABLE_EXTS) -> Path:
        # Windows 上 content 可能经 8.3 短路径传入, 统一以 resolve() 后的形式比较
        root_resolved = content.resolve()
        p = (content / rel).resolve()
        if root_resolved not in p.parents or p.suffix not in exts:
            abort(400, "path escapes content/ or has a non-servable extension")
        return p

    @app.context_processor
    def chrome():
        tax = load_taxonomy(content)
        return {"LABELS": tax["domains"], "SUB_LABELS": tax["subs"],
                "SOURCE_LABELS": tax["sources"], "STATUS_LABELS": tax["status"],
                "HUES": tax["hues"],
                "obsidian_connected": obsidian_vault_connected(content)}

    @app.route("/")
    def index():
        domains = scan_corpus(content)
        if not domains:
            abort(404, "content/ 语料为空")
        d0, s0 = domains[0]["id"], domains[0]["subs"][0]
        if s0["docs"]:
            return redirect(f"/doc/{d0}/{s0['id']}/{s0['docs'][0]['name']}")
        return redirect(f"/browse/{d0}/{s0['id']}")

    @app.route("/home")
    def home():
        stats = corpus_stats()
        recent = sorted(md_files(content), key=lambda x: x[0].stat().st_mtime, reverse=True)[:6]
        tax = load_taxonomy(content)
        recents = []
        for p, rel in recent:
            fm, _ = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
            recents.append({"title": fm.get("title") or p.stem, "rel": rel,
                            "source": fm.get("source", "")})
        now = time.localtime()
        days = max(0, (time.mktime((now.tm_year, 10, 1, 0, 0, 0, 0, 0, -1)) - time.mktime(now)) // 86400)
        leaves = sum(len(d["subs"]) for d in stats["domains"])
        pct = round(100 * stats["n_md"] / max(1, stats["n_md"] + stats["inbox"]))
        hour = now.tm_hour
        greet = "夜深了" if hour < 6 else "早上好" if hour < 11 else "中午好" if hour < 13 else "下午好" if hour < 18 else "晚上好"
        return render_template("home.html", stats=stats, recents=recents, days=int(days),
                               leaves=leaves, pct=pct, greet=greet,
                               inbox_n=stats["inbox"], n_md=stats["n_md"],
                               date=time.strftime("%m 月 %d 日 %A", now).replace("Monday", "周一").replace(
                                   "Tuesday", "周二").replace("Wednesday", "周三").replace("Thursday", "周四").replace(
                                   "Friday", "周五").replace("Saturday", "周六").replace("Sunday", "周日"))

    def collect_doc(domain, sub, name, domains):
        """组装单篇文档视图数据（workbench 渲染与 /api/doc 共用）。"""
        tax = load_taxonomy(content)
        p = find_doc(content, domain, sub, name)
        if not p:
            return None
        rel = p.relative_to(content).as_posix()
        raw = p.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_frontmatter(raw)
        if p.suffix == ".html":
            body = raw
        html_twin = p.with_name(p.stem + ".html")
        subs = next(d for d in domains if d["id"] == domain)["subs"]
        sobj = next(s for s in subs if s["id"] == sub)
        doc_size = f"{p.stat().st_size / 1024:.1f} KB"
        src_raw = str(fm.get("source", ""))
        doc = {
            "rel": rel, "title": str(fm.get("title") or p.stem), "fm": fm, "md": body
            if p.suffix == ".md" else None,
            "is_html": p.suffix == ".html",
            "has_html": html_twin.is_file() if p.suffix == ".md" else False,
            "html_rel": html_twin.relative_to(content).as_posix() if html_twin.is_file() else None,
            "favorite": fm.get("favorite") is True,
            "notes": read_notes(p),
            "size": doc_size,
            "domain": domain, "sub": sub, "name": name,
            "domain_label": tax["domains"].get(domain, domain),
            "sub_label": sobj["label"],
            "source_label": tax["sources"].get(src_raw, src_raw or "未知"),
            "status_label": tax["status"].get(str(fm.get("status", "")), str(fm.get("status", "")) or "未标记"),
        }
        info_rows = [
            ("来源", doc["source_label"]),
            ("原始位置", str(fm.get("source_path", "—"))),
            ("收录日期", str(fm.get("collected", "—"))),
            ("状态", doc["status_label"]),
            ("大小", doc_size),
        ]
        return {"doc": doc, "info_rows": info_rows, "sobj": sobj}

    def workbench(domain, sub, name):
        domains = scan_corpus(content)
        data = collect_doc(domain, sub, name, domains)
        if data is None:
            abort(404)
        doc, info_rows, sobj = data["doc"], data["info_rows"], data["sobj"]
        n_fav = sum(1 for d in domains for s in d["subs"] for dd in s["docs"] if dd["favorite"])
        con = open_db(indexes)
        try:
            fts_n = con.execute("SELECT count(*) FROM docs").fetchone()[0]
        finally:
            con.close()
        inbox_n = inbox_count(content)
        return render_template("workbench.html", domains=domains, cur={"domain": domain, "sub": sub, "name": name},
                               docs=sobj["docs"], sub_label=sobj["label"], doc=doc, n_fav=n_fav,
                               info_rows=info_rows,
                               doc_json=json.dumps(doc, ensure_ascii=False), fts_n=fts_n, inbox_n=inbox_n)

    @app.get("/api/tree")
    def api_tree():
        domains = scan_corpus(content)
        return jsonify({"sig": _tree_sig(content), "domains": domains})

    @app.get("/api/doc")
    def api_doc():
        domains = scan_corpus(content)
        data = collect_doc(request.args.get("domain", ""), request.args.get("sub", ""),
                           request.args.get("name", ""), domains)
        if data is None:
            return jsonify({"error": "not found"}), 404
        docs = data["sobj"]["docs"]
        return jsonify({"doc": data["doc"], "info_rows": data["info_rows"], "docs": docs})

    @app.route("/browse/<domain>/<sub>")
    def browse(domain, sub):
        domains = scan_corpus(content)
        dom = next((d for d in domains if d["id"] == domain), None)
        sobj = next((s for s in dom["subs"] if s["id"] == sub), None) if dom else None
        if not sobj or not sobj["docs"]:
            abort(404)
        first = sobj["docs"][0]
        return redirect(f"/doc/{domain}/{sub}/{first['name']}")

    @app.route("/doc/<domain>/<sub>/<path:name>")
    def doc(domain, sub, name):
        return workbench(domain, sub, name)

    @app.route("/raw/<path:rel>")
    def raw(rel):
        """服务语料原文件；美化版 HTML 在响应时做依赖重写（不改语料）：
        ① /static/echarts.min.js 等本地引用 → /static/ 真实文件（绝对路径在 iframe 下本就命中）；
        ② ./_shared/js/* 相对引用 → /static/（语料内并无 _shared/ 目录，iframe 下必 404）；
        ③ 公网 CDN（jsdelivr 等）→ 本地 vendored 副本，离线可用。"""
        p = safe_rel(rel)
        if p.suffix != ".html":
            return send_file(p)
        html = p.read_text(encoding="utf-8", errors="replace")
        html = _rewrite_html_assets(html)
        return app.response_class(html, mimetype="text/html")

    @app.route("/inbox")
    def inbox_page():
        """收件箱：content/_inbox/ 是新内容的唯一入口，此页列出待归档项。"""
        inbox = content / "_inbox"
        items = []
        if inbox.is_dir():
            for p in sorted(inbox.rglob("*")):
                if p.is_file() and p.suffix.lower() in (".md", ".html"):
                    rel = p.relative_to(content).as_posix()
                    fm, _ = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace")) \
                        if p.suffix == ".md" else ({}, None)
                    items.append({"rel": rel, "title": str(fm.get("title") or p.stem),
                                  "size": f"{p.stat().st_size / 1024:.1f} KB"})
        return render_template("inbox.html", items=items, n_md=sum(1 for _ in md_files(content)),
                               inbox_n=inbox_count(content))

    @app.route("/favorites")
    def favorites():
        domains = scan_corpus(content)
        items = [{"domain": d["id"], "domain_label": d["label"], "sub": s["id"], **doc}
                 for d in domains for s in d["subs"] for doc in s["docs"] if doc["favorite"]]
        return render_template("favorites.html", items=items, n_md=sum(1 for _ in md_files(content)),
                               inbox_n=inbox_count(content))

    @app.route("/tags")
    def tags():
        domains = scan_corpus(content)
        tag_map: dict[str, list[dict]] = {}  # tag -> list of doc info
        for d in domains:
            for s in d["subs"]:
                for doc in s["docs"]:
                    for t in doc.get("tags", []):
                        tag_map.setdefault(t, []).append({
                            "domain": d["id"], "domain_label": d["label"],
                            "sub": s["id"], "sub_label": s["label"],
                            "name": doc["name"], "title": doc["title"],
                        })
        # 按文档数降序排列
        tags_sorted = sorted(tag_map.items(), key=lambda x: -len(x[1]))
        return render_template("tags.html", tags=tags_sorted, n_md=sum(1 for _ in md_files(content)),
                               inbox_n=inbox_count(content))

    @app.route("/search")
    def search_route():
        q = request.args.get("q", "").strip()
        semantic = q.startswith("?")
        if semantic:
            q = q[1:].strip()
        results = []
        rag_error = None
        if q:
            if semantic:
                emb, rstore = get_rag()
                if emb is None or rstore is None:
                    rag_error = _RAG_IMPORT_ERROR or "初始化失败"
                else:
                    try:
                        hits = query_rag(rstore, emb, q, k=20)
                        seen: set[str] = set()
                        for h in hits:
                            if h["file"] in seen:
                                continue  # 同文档多块命中只留最相近块
                            seen.add(h["file"])
                            results.append({
                                "url": h["url"],
                                "title": h["title"],
                                "heading": h["heading"],
                                "path": h["file"],
                                "score_label": f"{h['score']:.2f}",
                                # 摘要直接用块正文前段（无 FTS snippet 高亮需求）
                                "snippet": h["contents"][:140].replace("\n", " ") + "…",
                            })
                    except Exception as e:
                        rag_error = f"检索失败：{e}"
            else:
                results = search(indexes, q)
        return render_template("search.html", q=q, results=results,
                               semantic=semantic, rag_error=rag_error,
                               n_md=sum(1 for _ in md_files(content)),
                               inbox_n=inbox_count(content))

    @app.post("/api/save")
    def api_save():
        data = request.get_json(force=True)
        p = safe_rel(data.get("path", ""), WRITABLE_EXTS)
        body = data.get("content", "")
        if not body.endswith("\n"):
            body += "\n"
        # 新文档（如 Obsidian 里直接创建）没有 frontmatter：首次保存时补齐身世信息；
        # 已有 frontmatter 的原文照写，不做任何改写
        fm, _ = parse_frontmatter(body)
        if not fm:
            stamp = {
                "title": p.stem, "tags": [], "source": "reader-edit",
                "collected": time.strftime("%Y-%m-%d"), "status": "stable",
            }
            body = store.dump_frontmatter(stamp, body)
        p.write_text(body, encoding="utf-8")
        # 外科手术式索引更新：仅替换本文档的正文与双链行（毫秒级，避免全量重建的等待）
        rel_posix = p.relative_to(content.resolve()).as_posix()
        upsert_doc_in_index(indexes, rel_posix, p, body)
        return jsonify({"ok": True, "path": rel_posix})

    @app.post("/api/note")
    def api_note():
        data = request.get_json(force=True)
        p = safe_rel(data.get("path", ""), WRITABLE_EXTS)
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify({"ok": False, "error": "empty note"}), 400
        np = notes_path(p)
        with np.open("a", encoding="utf-8") as f:
            f.write(f"- [{time.strftime('%Y-%m-%d %H:%M')}] {text}\n")
        return jsonify({"ok": True, "notes": read_notes(p)})

    @app.post("/api/favorite")
    def api_favorite():
        data = request.get_json(force=True)
        p = safe_rel(data.get("path", ""), WRITABLE_EXTS)
        fm, body = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        fm["favorite"] = not (fm.get("favorite") is True)
        p.write_text(store.dump_frontmatter(fm, body), encoding="utf-8")
        return jsonify({"ok": True, "favorite": fm["favorite"]})

    @app.get("/api/links")
    def api_links():
        """双链查询：正向(它引用谁，含未解析)与反向(谁引用它)。"""
        p = safe_rel(request.args.get("path", ""), WRITABLE_EXTS)
        rel = p.relative_to(content.resolve()).as_posix()
        con = open_db(indexes)
        try:
            outgoing = [
                {"raw": r[0], "path": r[1] or None, "title": r[2] or r[0], "resolved": bool(r[3])}
                for r in con.execute(
                    "SELECT raw, dst, dst_title, resolved FROM links WHERE src=?", (rel,))
            ]
            incoming = [
                {"path": r[0], "title": r[1]}
                for r in con.execute(
                    "SELECT src, src_title FROM links WHERE dst=? AND resolved=1", (rel,))
            ]
        finally:
            con.close()
        return jsonify({"outgoing": outgoing, "incoming": incoming})

    @app.post("/api/delete")
    def api_delete():
        """软删除：文档与其美化版、备注一起移入 content/_trash/<时间戳>/，
        保持相对结构，可随时手动恢复；git 历史是第二重保险。"""
        data = request.get_json(force=True)
        p = safe_rel(data.get("path", ""), WRITABLE_EXTS)
        root_resolved = content.resolve()
        rel = p.relative_to(root_resolved)
        trash = content / "_trash" / time.strftime("%Y%m%d-%H%M%S")
        moved = [rel.as_posix()]
        target = trash / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        p.rename(target)
        for sib in (p.with_name(p.name + ".notes.md"), p.with_name(p.stem + ".html")):
            if sib.is_file():
                s = trash / sib.relative_to(root_resolved)
                s.parent.mkdir(parents=True, exist_ok=True)
                sib.rename(s)
                moved.append(sib.relative_to(root_resolved).as_posix())
        # 外科手术式索引删除：只移除本文档的正文与双链行（毫秒级）
        remove_doc_from_index(indexes, rel.as_posix())
        return jsonify({"ok": True, "moved": moved})

    @app.post("/api/move")
    def api_move():
        """移动/重命名文档（含层级调整）。同步级联：
        ① 磁盘文件 + 旁挂（.notes.md / .html）；② FTS docs+links 表；
        ③ 向量索引 rag.db。src/dst 均为 content/ 相对 posix 路径。"""
        data = request.get_json(force=True)
        src = safe_rel(data.get("src", ""), WRITABLE_EXTS)
        dst_rel = (data.get("dst", "") or "").strip().replace("\\", "/")
        if not dst_rel or not dst_rel.endswith(".md") or dst_rel.startswith("/") or ".." in dst_rel:
            return jsonify({"ok": False, "error": "invalid dst"}), 400
        root_resolved = content.resolve()
        dst = (content / dst_rel)
        dst_resolved = dst.resolve()
        if root_resolved not in dst_resolved.parents or dst_resolved.exists():
            return jsonify({"ok": False, "error": "dst outside content/ or already exists"}), 400
        src_rel = src.relative_to(root_resolved).as_posix()
        dst.parent.mkdir(parents=True, exist_ok=True)
        # ① 磁盘：主文件 + 旁挂一起搬
        src.rename(dst)
        moved_sibs = []
        for sib, sib_suffix in ((src.with_name(src.name + ".notes.md"), ".notes.md"),
                                (src.with_name(src.stem + ".html"), ".html")):
            if sib.is_file():
                sib_dst = dst.with_name(dst.name + ".notes.md") if sib_suffix == ".notes.md" \
                    else dst.with_name(dst.stem + ".html")
                sib.rename(sib_dst)
                moved_sibs.append(sib_suffix)
        # ② FTS：外科手术式重建该文档行 + 双链（src 方向重写，dst 方向靠 resolve 重算）
        body = dst.read_text(encoding="utf-8", errors="replace")
        remove_doc_from_index(indexes, src_rel)
        upsert_doc_in_index(indexes, dst_rel, dst, body)
        # ③ 向量索引：换路径（块内容未变，mtime 未变，直接搬 files 表元数据与 chunk 归属）
        if RagStore is not None:
            try:
                rstore = RagStore(indexes)
                if rstore.known_files().get(src_rel) is not None:
                    rstore.con.execute("UPDATE vec_docs SET file=? WHERE file=?", (dst_rel, src_rel))
                    rstore.con.execute("UPDATE vec_docs SET chunk_id=?||'::'||chunk_ix WHERE file=? AND chunk_id LIKE ?",
                                       (dst_rel, src_rel, src_rel + ":%"))
                    rstore.con.execute("UPDATE files SET path=? WHERE path=?", (dst_rel, src_rel))
                    rstore.con.commit()
                rstore.close()
            except Exception:
                pass  # 向量索引搬移失败不阻塞；下轮 sync_rag 会全量对齐
        return jsonify({"ok": True, "src": src_rel, "dst": dst_rel, "moved_sibs": moved_sibs})

    @app.get("/api/stats")
    def api_stats():
        """文档统计：字数/行数/标题数/代码块数/双链数/标签/收录日期/文件大小。"""
        p = safe_rel(request.args.get("path", ""), WRITABLE_EXTS)
        if not p.is_file():
            abort(404, "文档不存在")
        raw = p.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_frontmatter(raw)
        headings = len(re.findall(r"^#{1,6}\\s+", body, re.M))
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

    @app.post("/api/tag/merge")
    def api_tag_merge():
        """标签合并（复用 store.merge_tag；apply=true 才写盘并重建 FTS）。
        返回受影响文档清单供前端确认框展示。"""
        data = request.get_json(force=True)
        src = str(data.get("src", "")).strip()
        dst = str(data.get("dst", "")).strip()
        if not src or not dst:
            return jsonify({"ok": False, "error": "src/dst required"}), 400
        r = store.merge_tag(content, src, dst, apply=bool(data.get("apply")))
        if r["apply"]:
            build_index(content, indexes)
        return jsonify({"ok": True, **r})

    @app.get("/api/rag")
    def api_rag():
        """语义检索：自然语言 → 向量 → 最近邻块。组件缺失/未就绪时返回 503。"""
        q = request.args.get("q", "").strip()
        if not q:
            return jsonify({"error": "empty query"}), 400
        emb, rstore = get_rag()
        if emb is None or rstore is None:
            return jsonify({"error": "rag unavailable",
                            "detail": _RAG_IMPORT_ERROR or "init failed"}), 503
        try:
            k = min(int(request.args.get("k", 8)), 30)
        except ValueError:
            k = 8
        domain = request.args.get("domain") or None
        sub = request.args.get("sub") or None
        hits = query_rag(rstore, emb, q, k=k, domain=domain, sub=sub)
        return jsonify({"q": q, "hits": hits})

    @app.get("/api/rag/status")
    def api_rag_status():
        if rag_status is None:  # rag 组件导入失败：如实上报，不炸 500
            return jsonify({"enabled": False, "chunks": 0, "model": "",
                            "detail": _RAG_IMPORT_ERROR})
        emb, rstore = get_rag()
        st = rag_status(rstore)
        st["detail"] = _RAG_IMPORT_ERROR
        return jsonify(st)

    @app.get("/stats")
    def stats_page():
        """月度阅读报表（默认当月）。库缺失时引导文案。"""
        if ReadingStore is None:
            abort(404, "统计组件不可用")
        ym = request.args.get("ym") or time.strftime("%Y-%m")
        if not re.fullmatch(r"\d{4}-\d{2}", ym):
            ym = time.strftime("%Y-%m")
        rs = ReadingStore(indexes)
        try:
            kpi = rs.monthly(ym)
        finally:
            rs.close()
        prev = (lambda y, m: f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}")(
            *(int(x) for x in ym.split("-")))
        nxt = (lambda y, m: f"{y + 1}-01" if m == 12 else f"{y}-{m + 1:02d}")(
            *(int(x) for x in ym.split("-")))
        now_ym = time.strftime("%Y-%m")
        # 增强字段：当月天数 + 与上月的时长环比（组件缺失/首月无数据时优雅缺席）
        import calendar
        kpi["days_in_month"] = calendar.monthrange(*[int(x) for x in ym.split("-")])[1]
        try:
            rs2 = ReadingStore(indexes)
            try:
                kpi["delta_minutes"] = kpi["total_minutes"] - rs2.monthly(prev)["total_minutes"]
            finally:
                rs2.close()
        except Exception:
            kpi["delta_minutes"] = 0
        return render_template("stats.html", ym=ym, kpi=kpi, prev_ym=prev,
                               next_ym=None if nxt > now_ym else nxt,
                               n_md=sum(1 for _ in md_files(content)),
                               inbox_n=inbox_count(content))

    @app.post("/api/track")
    def api_track():
        """阅读事件上报；组件缺失/非法入参一律静默成功（统计永不妨碍阅读）。"""
        if ReadingStore is None:
            return jsonify({"ok": True, "tracked": False})
        data = request.get_json(force=True, silent=True) or {}
        path = str(data.get("path", ""))
        event = str(data.get("event", ""))
        if not path or event not in ("open", "read_minute", "finish"):
            return jsonify({"ok": True, "tracked": False})
        title = ""
        # 从路径安全地取标题：仅当该路径确实在语料树内
        try:
            pp = safe_rel(path, WRITABLE_EXTS)
            if pp.is_file():
                fm2, _ = parse_frontmatter(pp.read_text(encoding="utf-8", errors="replace"))
                title = str(fm2.get("title") or pp.stem)
        except Exception:
            title = path.rsplit("/", 1)[-1][:-3] if path.endswith(".md") else path
        seconds = max(0, min(int(data.get("seconds") or 0), 3600))
        rs = ReadingStore(indexes)
        try:
            tracked = rs.track(path, title, event, seconds)
        finally:
            rs.close()
        return jsonify({"ok": True, "tracked": bool(tracked)})

    @app.after_request
    def static_no_cache(response):
        # 本地工具: 静态资源改动后必须立刻生效, 只允许 304 协商缓存
        if request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache"
        return response

    @app.errorhandler(404)
    def not_found(e):
        desc = getattr(e, "description", "页面不存在")
        return render_template("error.html", message=desc), 404

    return app


# ---------------- 美化版 HTML 依赖重写（响应时改写，语料文件不动） ----------------
_ASSET_REWRITE = [
    # 语料内不存在的 _shared/ 相对引用（美化时遗留的工程目录）→ 本地 vendored
    (re.compile(r'("|\(|=)(\./)?_shared/js/mermaid(\.min)?\.js'),
     r'\1/static/mermaid.min.js'),
    # 公网 CDN → 本地 vendored 副本（离线可用，不依赖网络）
    (re.compile(r'https?://cdn\.jsdelivr\.net/npm/mermaid@[^/"]+/dist/mermaid(\.min)?\.js'),
     '/static/mermaid.min.js'),
    (re.compile(r'https?://cdn\.jsdelivr\.net/npm/chart\.js@[^/"]+/dist/chart(\.umd)?(\.min)?\.js'),
     '/static/chart.umd.min.js'),
]


def _rewrite_html_assets(html: str) -> str:
    for pat, rep in _ASSET_REWRITE:
        html = pat.sub(rep, html)
    return html


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
