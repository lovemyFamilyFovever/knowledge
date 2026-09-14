# -*- coding: utf-8 -*-
"""阅读器页面路由：首页 / 浏览 / 文档页 / 原文件 / 收件箱 / 收藏 / 标签 / 全文搜索 / 月度统计。

依赖注入方式同 routes_learn.py：一切通过 flask.current_app.config
（KB_HOOKS / CONTENT / INDEXES / ROOT），严禁 from app.app import（循环导入）。
本模块还持有 /raw 的 HTML 依赖重写（mermaid 缩放查看器注入 + 本地 vendored 替换）。
"""
import calendar
import json
import re
import time
from pathlib import Path

from flask import (Blueprint, abort, current_app, redirect, render_template,
                   request, send_file)

from app.fts import open_db, search
from app.store import (LIBRARY_EXTS, MEDIA_EXTS, SERVABLE_EXTS, SKIP_DIRS, domain_label, inbox_count, load_taxonomy,
                       md_files, parse_frontmatter)

pages_bp = Blueprint("pages", __name__)


# ---------------- 依赖注入与通用工具 ----------------
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


def _collect_doc(domain, sub, name, domains):
    return _hooks()["collect_doc"](domain, sub, name, domains)


def _corpus_stats() -> dict:
    """语料概览：域树 + md/html 篇数 + 收藏数 + 收件箱数（/home 用）。"""
    content = _content()
    domains = _domains_cached()
    n_md = sum(1 for _, _ in md_files(content))
    n_html = sum(1 for p in content.rglob("*.html")
                 if not any(part in SKIP_DIRS or part.startswith("_") for part in p.parts))
    fav = sum(1 for d in (doc for dom in domains for s in dom["subs"] for doc in s["docs"])
              if d["favorite"])
    inbox = inbox_count(content)
    return {"domains": domains, "n_md": n_md, "n_html": n_html, "n_fav": fav, "inbox": inbox}


def _fts_count() -> int:
    """FTS 索引内实际篇数；库缺失/损坏按 0 呈现（pill 不再拿文件数谎报「已就绪」）。"""
    try:
        con = open_db(_indexes())
        try:
            return int(con.execute("SELECT count(*) FROM docs").fetchone()[0])
        finally:
            con.close()
    except Exception:
        return 0


def _chrome_counts() -> dict:
    content = _content()
    return {"n_md": sum(1 for _ in md_files(content)), "inbox_n": inbox_count(content),
            "fts_n": _fts_count()}


# ---------------- 首页 / 总览 ----------------
@pages_bp.route("/")
def index():
    domains = _domains_cached()
    if not domains:
        abort(404, "content/ 语料为空")
    d0, s0 = domains[0]["id"], domains[0]["subs"][0]
    if s0["docs"]:
        return redirect(f"/doc/{d0}/{s0['id']}/{s0['docs'][0]['name']}")
    return redirect(f"/browse/{d0}/{s0['id']}")


@pages_bp.route("/home")
def home():
    content = _content()
    stats = _corpus_stats()
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
                           inbox_n=stats["inbox"], n_md=stats["n_md"], fts_n=_fts_count(),
                           date=time.strftime("%m 月 %d 日 %A", now).replace("Monday", "周一").replace(
                               "Tuesday", "周二").replace("Wednesday", "周三").replace("Thursday", "周四").replace(
                               "Friday", "周五").replace("Saturday", "周六").replace("Sunday", "周日"))


# ---------------- 浏览 / 文档页 ----------------
@pages_bp.route("/browse/<domain>/<sub>")
def browse(domain, sub):
    domains = _domains_cached()
    dom = next((d for d in domains if d["id"] == domain), None)
    sobj = next((s for s in dom["subs"] if s["id"] == sub), None) if dom else None
    if not sobj:
        abort(404)
    if not sobj["docs"]:
        # 空目录（如新建后未放文档）：渲染工作台空态而不是 404，否则用户以为创建无效
        return _workbench_empty(domain, sub, sobj)
    first = sobj["docs"][0]
    return redirect(f"/doc/{domain}/{sub}/{first['name']}")


def _workbench_empty(domain, sub, sobj):
    """空子域工作台：左树/列表照常渲染，正文区给空态占位 + 新建文档入口。"""
    content = _content()
    domains = _domains_cached()
    n_fav = sum(1 for d in domains for s in d["subs"] for dd in s["docs"] if dd["favorite"])
    con = open_db(_indexes())
    try:
        fts_n = con.execute("SELECT count(*) FROM docs").fetchone()[0]
    except Exception:
        fts_n = 0
    finally:
        con.close()
    empty_doc = {
        "rel": f"{domain}/{sub}/", "title": sobj["label"], "fm": {}, "md": None,
        "is_html": False, "has_html": False, "html_rel": None, "favorite": False,
        "domain": domain, "sub": sub, "domain_label": domain_label(load_taxonomy(content), domain),
        "sub_label": sobj["label"], "source_label": "空目录", "notes": [], "info_rows": [],
        "mtime": 0, "size": "0 KB", "empty": True,
    }
    return render_template("workbench.html", domains=domains,
                           cur={"domain": domain, "sub": sub, "name": ""},
                           docs=[], sub_label=sobj["label"], doc=empty_doc, n_fav=n_fav,
                           info_rows=[], doc_json=json.dumps(empty_doc, ensure_ascii=False).replace("<", "\\u003c"),
                           fts_n=fts_n, inbox_n=inbox_count(content))


def _workbench(domain, sub, name):
    content = _content()
    indexes = _indexes()
    domains = _domains_cached()
    data = _collect_doc(domain, sub, name, domains)
    if data is None:
        abort(404)
    doc, info_rows, sobj = data["doc"], data["info_rows"], data["sobj"]
    n_fav = sum(1 for d in domains for s in d["subs"] for dd in s["docs"] if dd["favorite"])
    con = open_db(indexes)
    try:
        fts_n = con.execute("SELECT count(*) FROM docs").fetchone()[0]
    except Exception:
        fts_n = 0
    finally:
        con.close()
    inbox_n = inbox_count(content)
    return render_template("workbench.html", domains=domains,
                           cur={"domain": domain, "sub": sub, "name": name},
                           docs=sobj["docs"], sub_label=sobj["label"], doc=doc, n_fav=n_fav,
                           info_rows=info_rows,
                           doc_json=json.dumps(doc, ensure_ascii=False).replace("<", "\\u003c"),
                           fts_n=fts_n, inbox_n=inbox_n)


@pages_bp.route("/doc/<domain>/<sub>/<path:name>")
def doc(domain, sub, name):
    return _workbench(domain, sub, name)


# ---------------- 原文件服务（响应时改写 HTML 依赖，语料不动） ----------------
@pages_bp.route("/raw/<path:rel>")
def raw(rel):
    """服务语料原文件；美化版 HTML 在响应时做依赖重写（不改语料）：
    ① /static/echarts.min.js 等本地引用 → /static/ 真实文件（绝对路径在 iframe 下本就命中）；
    ② ./_shared/js/* 相对引用 → /static/（语料内并无 _shared/ 目录，iframe 下必 404）；
    ③ 公网 CDN（jsdelivr 等）→ 本地 vendored 副本，离线可用。
    需求#6：图片扩展名（MEDIA_EXTS）同样直服，供正文相对图片 /raw 直通。
    需求#12：书库格式直服（.txt/.epub/.pdf/.xlsx）—— 阅读器前端按类型分流渲染。"""
    p = _safe_rel(rel, SERVABLE_EXTS | MEDIA_EXTS | LIBRARY_EXTS)
    if p.suffix == ".html":
        html = p.read_text(encoding="utf-8", errors="replace")
        html = _rewrite_html_assets(html)
        return current_app.response_class(html, mimetype="text/html")
    return send_file(p)


# mermaid 图点击放大查看器：仅当页面含 mermaid 容器时注入；不写进语料文件
_ZOOM_SNIPPET = """<script>(function(){
 function ready(fn){if(document.readyState!=='loading')fn();else document.addEventListener('DOMContentLoaded',fn)}
 ready(function(){
  var css=document.createElement('style');css.textContent="\n#kb-zoom-ov{position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.82);display:none;align-items:center;justify-content:center;cursor:zoom-out}\n#kb-zoom-ov.show{display:flex}\n#kb-zoom-ov .kbz-inner{background:#fff;border-radius:10px;padding:10px;max-width:96vw;max-height:94vh;overflow:auto;cursor:grab}\n#kb-zoom-ov svg{transform-origin:top left;transition:transform .15s}\n#kb-zoom-hint{position:fixed;left:12px;bottom:10px;color:#8b949e;font:12px/1.6 sans-serif;z-index:100000}\n";document.head.appendChild(css);
  var ov=document.createElement('div');ov.id='kb-zoom-ov';
  ov.innerHTML='<div class="kbz-inner"></div><div id="kb-zoom-hint">滚轮缩放 · 点击空白关闭</div>';
  document.body.appendChild(ov);
  var inner=ov.querySelector('.kbz-inner'),scale=1,drag=null;
  function close(){ov.classList.remove('show');inner.innerHTML='';scale=1}
  ov.addEventListener('click',function(e){if(e.target===ov||e.target.id==='kb-zoom-hint')close()});
  inner.addEventListener('wheel',function(e){e.preventDefault();scale*= (e.deltaY<0?1.15:0.87);scale=Math.max(.3,Math.min(8,scale));var sv=inner.querySelector('svg');if(sv)sv.style.transform='scale('+scale+')'},{passive:false});
  inner.addEventListener('mousedown',function(e){drag={x:e.clientX,y:e.clientY,l:inner.scrollLeft,t:inner.scrollTop};inner.style.cursor='grabbing'});
  window.addEventListener('mousemove',function(e){if(!drag)return;inner.scrollLeft=drag.l-(e.clientX-drag.x);inner.scrollTop=drag.t-(e.clientY-drag.y)});
  window.addEventListener('mouseup',function(){drag=null;inner.style.cursor='grab'});
  function bind(){
   var nodes=document.querySelectorAll('.mermaid>svg, pre.mermaid>svg, div.mermaid svg');
   nodes.forEach(function(sv){
    if(sv.dataset.kbZoom)return;sv.dataset.kbZoom='1';
    sv.style.cursor='zoom-in';
    sv.addEventListener('click',function(ev){
     ev.stopPropagation();scale=1;
     inner.innerHTML='';inner.appendChild(sv.cloneNode(true));
     var c=inner.querySelector('svg');if(c)c.style.transform='scale(1)';
     ov.classList.add('show');
    });
   });
  }
  bind();
  if(window.mermaid&&window.mermaid.run){try{var pb=window.mermaid.run({});if(pb&&pb.then)pb.then(function(){setTimeout(bind,300)})}catch(e){}}
  new MutationObserver(function(){setTimeout(bind,200)}).observe(document.body,{childList:true,subtree:true});
 });
})();</script>"""

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
    has_mm = bool(re.search(r'class="mermaid|pre\.mermaid|class="mermaid-code"', html))
    if has_mm:
        # 非标准容器名归一：mermaid-code → mermaid（mermaid@11 startOnLoad 只认 .mermaid）
        html = html.replace('class="mermaid-code"', 'class="mermaid"')
        # 注入点击放大查看器（滚轮缩放 + 拖拽平移，语料文件不动）
        if "</body>" in html:
            html = html.replace("</body>", _ZOOM_SNIPPET + "</body>", 1)
    return html


# ---------------- 收件箱 / 收藏 / 标签 ----------------
@pages_bp.route("/inbox")
def inbox_page():
    """收件箱：content/_inbox/ 是新内容的唯一入口，此页列出待归档项。"""
    content = _content()
    inbox = content / "_inbox"
    items = []
    if inbox.is_dir():
        from app.store import inbox_iter
        for p, rel in inbox_iter(content):
            if p.suffix.lower() in (".md", ".html"):
                fm, _ = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace")) \
                    if p.suffix == ".md" else ({}, None)
                items.append({"rel": "_inbox/" + rel, "title": str(fm.get("title") or p.stem),
                              "size": f"{p.stat().st_size / 1024:.1f} KB"})
        items.sort(key=lambda x: x["rel"])
    return render_template("inbox.html", items=items, **_chrome_counts())


@pages_bp.route("/favorites")
def favorites():
    domains = _domains_cached()
    items = [{"domain": d["id"], "domain_label": d["label"], "sub": s["id"], **doc}
             for d in domains for s in d["subs"] for doc in s["docs"] if doc["favorite"]]
    return render_template("favorites.html", items=items, **_chrome_counts())


@pages_bp.route("/tags")
def tags():
    domains = _domains_cached()
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
    return render_template("tags.html", tags=tags_sorted, **_chrome_counts())


# ---------------- 搜索页（FTS / 语义） ----------------
@pages_bp.route("/search")
def search_route():
    indexes = _indexes()
    q = request.args.get("q", "").strip()
    semantic = q.startswith("?")
    if semantic:
        q = q[1:].strip()
    results = []
    rag_error = None
    if q:
        if semantic:
            get_rag = _hooks().get("get_rag")
            query_rag = _hooks().get("query_rag")
            emb, rstore = get_rag() if get_rag else (None, None)
            if emb is None or rstore is None or query_rag is None:
                rag_error = _hooks().get("rag_import_error") or "初始化失败"
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
            # FTS 结果同样需要可跳转 URL：模板读 r.url，缺失时 href 为空导致整卡不可点
            from urllib.parse import quote as _urlquote
            for r in results:
                p = r.get("path", "")
                seg = lambda s: "/".join(_urlquote(x) for x in s.split("/"))  # noqa: E731
                if p.endswith(".md") and not p.startswith("_inbox/"):
                    r["url"] = "/doc/" + seg(p[:-3])
                else:  # .html 美化版 / _inbox 文件 / 其他可服务文件 → 直通原文件
                    r["url"] = "/raw/" + seg(p)
    return render_template("search.html", q=q, results=results,
                           semantic=semantic, rag_error=rag_error,
                           **_chrome_counts())


# ---------------- 月度阅读报表 ----------------
@pages_bp.route("/stats")
def stats_page():
    """月度阅读报表（默认当月）。库缺失时引导文案。"""
    indexes = _indexes()
    ReadingStore = _hooks().get("ReadingStore")
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
                           **_chrome_counts())


def register(app, hooks: dict):
    """由 app.py 调用：注入依赖 + 挂载蓝图。"""
    app.config.setdefault("KB_HOOKS", {}).update(hooks)
    app.register_blueprint(pages_bp)
