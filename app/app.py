# -*- coding: utf-8 -*-
"""知库 reader — Flask 应用：从 content/ 文件树直接服务知识语料。

content/ 的 Markdown/HTML 文件是唯一事实源；indexes/index.db 只是派生的
FTS5 全文索引，启动时按文件 mtime 增量重建，随时可删可重建。编辑、收藏、
备注全部写回文件系统，Obsidian 与本应用共享同一份语料。

工厂模式：create_app(root) 便于测试指向临时语料目录。
"""
import html as html_mod
import json
import os
import re
import sqlite3
import time
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, send_file

FM_RE = re.compile(r"\A---\n(.*?)\n---\n\n?", re.S)
SKIP_DIRS = {"_inbox", "_assets", "_unfiled"}
WRITABLE_EXTS = {".md"}
SERVABLE_EXTS = {".md", ".html"}
DOMAIN_LABELS = {
    "frontend": "前端", "backend": "后端", "cs-fundamentals": "CS 基础",
    "ai": "AI", "engineering": "工程", "interview": "面试",
    "projects": "项目", "cookbook": "手册", "career": "职业",
}


# ---------------- frontmatter ----------------
def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse the leading `---` block into a dict; unknown keys are preserved."""
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm: dict = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            fm[key] = [x.strip().strip("\"'") for x in inner.split(",") if x.strip()] if inner else []
        elif val.lower() in ("true", "false"):
            fm[key] = val.lower() == "true"
        else:
            fm[key] = val.strip("\"'")
    return fm, text[m.end():]


def dump_frontmatter(fm: dict, body: str) -> str:
    lines = ["---"]
    for key, val in fm.items():
        if val is True:
            lines.append(f"{key}: true")
        elif isinstance(val, list):
            lines.append(f"{key}: [{', '.join(val)}]")
        else:
            lines.append(f'{key}: "{val}"')
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body


# ---------------- corpus scan ----------------
_SCAN_CACHE: dict = {}


def _tree_sig(content: Path) -> str:
    """仅 stat 不读内容的树签名：毫秒级，作为扫描缓存的失效依据。"""
    parts = []
    for dirpath, dirnames, filenames in os.walk(content):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith("_")]
        for fn in filenames:
            if fn.endswith((".md", ".html")):
                p = Path(dirpath) / fn
                parts.append(f"{p.relative_to(content).as_posix()}:{p.stat().st_mtime_ns}")
    return "|".join(parts)


def scan_corpus(content: Path) -> list[dict]:
    sig = _tree_sig(content)
    hit = _SCAN_CACHE.get(str(content))
    if hit and hit[0] == sig:
        return hit[1]
    domains = []
    for ddir in sorted(content.iterdir()):
        if not ddir.is_dir() or ddir.name in SKIP_DIRS or ddir.name.startswith("_"):
            continue
        dom = {"id": ddir.name, "label": DOMAIN_LABELS.get(ddir.name, ddir.name), "subs": [], "n": 0}
        loose = sorted(p for p in ddir.iterdir() if p.is_file() and p.suffix in SERVABLE_EXTS)
        sdirs = sorted(p for p in ddir.iterdir() if p.is_dir() and p.name not in SKIP_DIRS)
        for sdir in sdirs:
            dom["subs"].append(_scan_sub(sdir, sdir.name, sdir.name))
        if loose:
            dom["subs"].append(_scan_sub(ddir, "_root", "总览", loose))
        dom["n"] = sum(s["n"] for s in dom["subs"])
        if dom["subs"]:
            domains.append(dom)
    _SCAN_CACHE[str(content)] = (sig, domains)
    return domains


def _scan_sub(sdir: Path, sid: str, label: str, files=None) -> dict:
    """递归收集：嵌套目录（如 dsh-agent/architecture、vue2/Details）的文档
    以子路径作为文档名（<path:name> 路由支持带斜杠的 name）。"""
    files = files if files is not None else sorted(
        p for p in sdir.rglob("*") if p.is_file() and p.suffix in SERVABLE_EXTS
    )
    md_rel = {p.relative_to(sdir).with_suffix("").as_posix() for p in files if p.suffix == ".md"}
    docs = []
    for p in files:
        relp = p.relative_to(sdir).as_posix()
        fm: dict = {}
        if p.suffix == ".html":
            if relp[:-5] in md_rel:
                continue  # 同名 .md 的美化版旁挂
            name, title, is_html = relp, p.stem + ".html", True
        else:
            name, title, is_html = relp[:-3], p.stem, False
            fm, _ = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
            title = str(fm.get("title") or title)
        docs.append({
            "name": name,
            "file": relp,
            "title": title,
            "tags": fm.get("tags", []) if isinstance(fm.get("tags"), list) else [],
            "favorite": fm.get("favorite") is True,
            "is_html": is_html,
            "has_html": (sdir / (name + ".html")).is_file() if not is_html else False,
            "mtime": p.stat().st_mtime,
        })
    return {"id": sid, "label": label, "n": len(docs), "docs": docs}


def find_doc(content: Path, domain: str, sub: str, name: str):
    """Locate a document; returns (abs_path, rel_posix) or None."""
    base = content / domain
    sdir = base / sub if sub != "_root" else base
    if not base.is_dir() or not sdir.is_dir():
        return None
    for cand in (sdir / f"{name}.md", sdir / name, sdir / f"{name}.html"):
        if cand.is_file() and cand.suffix in SERVABLE_EXTS:
            return cand
    return None


def notes_path(doc_path: Path) -> Path:
    return doc_path.with_name(doc_path.name + ".notes.md")


def read_notes(doc_path: Path) -> list[dict]:
    np = notes_path(doc_path)
    if not np.is_file():
        return []
    out = []
    for line in np.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"- \[(.+?)\] (.*)", line.strip())
        if m:
            out.append({"when": m.group(1), "text": m.group(2)})
    return list(reversed(out))  # newest first


# ---------------- FTS index ----------------
def open_db(indexes: Path) -> sqlite3.Connection:
    indexes.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(indexes / "index.db")
    con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path UNINDEXED, title, tags, body)")
    con.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)")
    return con


def md_files(content: Path):
    for dirpath, dirnames, filenames in os.walk(content):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith("_")]
        for fn in filenames:
            if fn.endswith(".md"):
                p = Path(dirpath) / fn
                yield p, p.relative_to(content).as_posix()


_INBOX_CACHE = {"t": 0.0, "n": 0}


def inbox_count(content: Path) -> int:
    d = content / "_inbox"
    if not d.is_dir():
        return 0
    now = time.time()
    if now - _INBOX_CACHE["t"] > 60:
        _INBOX_CACHE["n"] = sum(1 for _ in d.rglob("*"))
        _INBOX_CACHE["t"] = now
    return _INBOX_CACHE["n"]


def build_index(content: Path, indexes: Path) -> int:
    """Full rebuild; 500+ docs rebuild in well under a second."""
    con = open_db(indexes)
    try:
        con.execute("DELETE FROM docs")
        n = 0
        for p, rel in md_files(content):
            fm, body = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
            title = str(fm.get("title") or p.stem)
            tags = fm.get("tags")
            tag_str = " ".join(tags) if isinstance(tags, list) else str(tags or "")
            con.execute("INSERT INTO docs(path,title,tags,body) VALUES(?,?,?,?)",
                        (rel, cjk_space(title), cjk_space(tag_str), cjk_space(body)))
            n += 1
        con.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('built_at',?)", (str(time.time()),))
        con.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('doc_n',?)", (str(n),))
        con.commit()
        return n
    finally:
        con.close()


def index_is_stale(content: Path, indexes: Path) -> bool:
    con = open_db(indexes)
    try:
        row = con.execute("SELECT v FROM meta WHERE k='built_at'").fetchone()
        if not row:
            return True
        newest = max((p.stat().st_mtime for p, _ in md_files(content)), default=0)
        return newest > float(row[0])
    finally:
        con.close()


# unicode61 分词器把连续中文当作单个长 token, 导致"量子"搜不到"量子纠缠"。
# 索引侧给每个中文字符后插空格(逐字 token), 查询侧把中文词构造成逐字短语,
# 展示前再把字符间空格清掉 —— 这是无外部分词依赖时的标准做法。
CJK_RUN = re.compile(r"[\u4e00-\u9fff]+")
CJK_CHAR = re.compile(r"([\u4e00-\u9fff])")
CJK_GAP = re.compile(r"([\u4e00-\u9fff]) (?=[\u4e00-\u9fff])")


def cjk_space(text: str) -> str:
    return CJK_CHAR.sub(r"\1 ", text)


def cjk_clean(text: str) -> str:
    return CJK_GAP.sub(r"\1", text)


def build_match(q: str) -> str:
    terms = re.findall(r"\w+", q)
    phrases = []
    for t in terms:
        runs = re.findall(r"[\u4e00-\u9fff]+|[^\u4e00-\u9fff]+", t)
        parts = [cjk_space(r).strip() if CJK_RUN.fullmatch(r) else r for r in runs]
        phrases.append('"' + " ".join(parts) + '"*')
    return " OR ".join(phrases)


def search(indexes: Path, q: str, limit: int = 50) -> list[dict]:
    if not re.findall(r"\w+", q):
        return []
    match = build_match(q)
    con = open_db(indexes)
    try:
        rows = con.execute(
            "SELECT path, title, snippet(docs, 3, '<mark>', '</mark>', 12, 24) "
            "FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT ?",
            (match, limit),
        ).fetchall()
        return [{"path": r[0], "title": cjk_clean(r[1]), "snippet": cjk_clean(r[2])} for r in rows]
    finally:
        con.close()


# ---------------- app factory ----------------
def create_app(root: Path | None = None) -> Flask:
    root = Path(root) if root else Path(
        os.environ.get("KB_ROOT") or Path(__file__).resolve().parents[1])
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
        return {"LABELS": DOMAIN_LABELS,
                "HUES": {"ai": 158, "frontend": 200, "cs-fundamentals": 226, "projects": 22,
                         "engineering": 262, "interview": 340, "backend": 12, "career": 42, "cookbook": 96}}

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
                               date=time.strftime("%m 月 %d 日 %A", now).replace("Monday", "周一").replace(
                                   "Tuesday", "周二").replace("Wednesday", "周三").replace("Thursday", "周四").replace(
                                   "Friday", "周五").replace("Saturday", "周六").replace("Sunday", "周日"))

    def workbench(domain, sub, name):
        domains = scan_corpus(content)
        p = find_doc(content, domain, sub, name)
        if not p:
            abort(404)
        rel = p.relative_to(content).as_posix()
        raw = p.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_frontmatter(raw)
        if p.suffix == ".html":
            body = raw
        html_twin = p.with_name(p.stem + ".html")
        doc = {
            "rel": rel, "title": str(fm.get("title") or p.stem), "fm": fm, "md": body
            if p.suffix == ".md" else None,
            "is_html": p.suffix == ".html",
            "has_html": html_twin.is_file() if p.suffix == ".md" else False,
            "html_rel": html_twin.relative_to(content).as_posix() if html_twin.is_file() else None,
            "favorite": fm.get("favorite") is True,
            "notes": read_notes(p),
            "size": f"{p.stat().st_size / 1024:.1f} KB",
        }
        subs = next(d for d in domains if d["id"] == domain)["subs"]
        sobj = next(s for s in subs if s["id"] == sub)
        n_fav = sum(1 for d in domains for s in d["subs"] for dd in s["docs"] if dd["favorite"])
        con = open_db(indexes)
        try:
            fts_n = con.execute("SELECT count(*) FROM docs").fetchone()[0]
        finally:
            con.close()
        inbox_n = inbox_count(content)
        return render_template("workbench.html", domains=domains, cur={"domain": domain, "sub": sub, "name": name},
                               docs=sobj["docs"], sub_label=sobj["label"], doc=doc, n_fav=n_fav,
                               doc_json=json.dumps(doc, ensure_ascii=False), fts_n=fts_n, inbox_n=inbox_n)

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
        p = safe_rel(rel)
        return send_file(p)

    @app.route("/favorites")
    def favorites():
        domains = scan_corpus(content)
        items = [{"domain": d["id"], "domain_label": d["label"], "sub": s["id"], **doc}
                 for d in domains for s in d["subs"] for doc in s["docs"] if doc["favorite"]]
        return render_template("favorites.html", items=items, n_md=sum(1 for _ in md_files(content)),
                               inbox_n=inbox_count(content))

    @app.route("/search")
    def search_route():
        q = request.args.get("q", "").strip()
        results = search(indexes, q) if q else []
        return render_template("search.html", q=q, results=results,
                               n_md=sum(1 for _ in md_files(content)),
                               inbox_n=inbox_count(content))

    @app.post("/api/save")
    def api_save():
        data = request.get_json(force=True)
        p = safe_rel(data.get("path", ""), WRITABLE_EXTS)
        body = data.get("content", "")
        if not body.endswith("\n"):
            body += "\n"
        p.write_text(body, encoding="utf-8")
        build_index(content, indexes)
        return jsonify({"ok": True, "path": p.relative_to(content.resolve()).as_posix()})

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
        p.write_text(dump_frontmatter(fm, body), encoding="utf-8")
        return jsonify({"ok": True, "favorite": fm["favorite"]})

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
        build_index(content, indexes)
        return jsonify({"ok": True, "moved": moved})

    @app.errorhandler(404)
    def not_found(e):
        desc = getattr(e, "description", "页面不存在")
        return render_template("error.html", message=desc), 404

    return app


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
