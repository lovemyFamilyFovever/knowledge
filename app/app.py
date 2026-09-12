# -*- coding: utf-8 -*-
"""知库 reader — Flask 应用工厂：把 content/ 语料读成可浏览的知识库。

content/ 的 Markdown/HTML 文件是唯一事实源；indexes/（index.db / rag.db /
reading.db）只是派生缓存，随时可删可重建。编辑、收藏、备注全部写回文件系统，
Obsidian 与本应用共享同一份语料。

分层（2026-09-07 拆分 create_app）：
    app/store.py         语料层：frontmatter / 分类树 / 笔记 / 分类学装载
    app/fts.py           FTS5 全文索引 + [[双链]] 解析（派生，外科手术式更新）
    app/rag.py           语义检索：切块 / 嵌入 / sqlite-vec（派生）
    app/reading.py       月度阅读统计（派生，与语料隔离）
    app/cards.py         baike/interview 抽卡（纯函数）
    app/learn.py         卡片库与复习状态（派生）
    app/app.py           本文件：只做装配（配置 / 索引引导 / RAG 惰性接入 /
                         watcher / 缓存门面 / 上下文 / 错误处理 / 蓝图注册）
    app/routes_pages.py  页面：/ /home /browse /doc /raw /inbox /favorites /tags /search /stats
    app/routes_doc.py    数据：/api/tree /api/doc
    app/routes_edit.py   编辑：/api/save /api/note /api/favorite /api/links
    app/routes_files.py  文件：/api/delete /api/move /api/move/batch
    app/routes_stats.py  统计：/api/dir/tree /api/globalstats /api/substats /api/stats
                         /api/tag/merge /api/track
    app/routes_rag.py    语义：/api/rag /api/rag/status
    app/routes_learn.py  学习/复习/术语门户接口
    app/routes_search.py 搜索增强（命令面板 / 双链补全 / 术语门户 / 统一检索）

工厂模式：create_app(root) 便于测试指向临时语料目录。
依赖注入：业务路由只通过 flask.current_app.config 取依赖（KB_HOOKS / CONTENT /
INDEXES / ROOT），严禁 from app.app import（循环导入）。
"""
import logging
import sys
import threading
import time
from pathlib import Path

from flask import Flask, abort, render_template, request

logger = logging.getLogger("kb.reader")

# 直接以脚本方式运行（python app\app.py）时 sys.path[0] 是 app/ 目录而非项目根，
# 补上项目根保证 from app.xxx import 在两种启动方式下都能命中
_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app.store import (  # noqa: F401  兼容旧引用（tests/scripts 直接 import app.app 的符号）
    DOMAIN_LABELS, GRAPH_HUES, SKIP_DIRS, SOURCE_LABELS, STATUS_LABELS,
    WRITABLE_EXTS, SERVABLE_EXTS, FM_RE,
    domain_label, dump_frontmatter, find_doc, inbox_count, load_taxonomy, md_files,
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

# ---------------- 路由蓝图（全部走 register(app, hooks) 统一注入） ----------------
from app.routes_pages import register as register_pages
from app.routes_doc import register as register_doc
from app.routes_edit import register as register_edit
from app.routes_files import register as register_files
from app.routes_stats import register as register_stats
from app.routes_rag import register as register_rag
from app.routes_learn import register as register_learn
from app.routes_search import register as register_search


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
            logger.warning("RAG 初始化失败，语义检索降级纯 FTS", exc_info=True)
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
                # 重建失败不拖垮服务，但必须留痕：否则表现为“搜索不到新文档”而无处排查
                logger.warning("FTS 索引重建失败", exc_info=True)
            if rag_state["embedder"] is not None and rag_state["store"] is not None:
                try:
                    sync_rag(content, rag_state["embedder"], rag_state["store"])
                except Exception:
                    logger.warning("RAG 同步失败（下轮重试）", exc_info=True)

    _watcher = threading.Thread(target=_index_watcher, daemon=True)
    _watcher.start()

    # 语料树请求间缓存：_tree_sig 仅 stat 不读内容（毫秒级），签名未变时复用上次扫描结果，
    # 消除 10 处热点路由每请求全量 rglob 的开销。文件增删改均会改变签名，不存陈旧风险。
    _scan_cache = {"sig": None, "domains": None}

    def domains_cached() -> list[dict]:
        """scan_corpus 的缓存门面：签名命中直接复用，未命中重扫。"""
        sig = _tree_sig(content)
        if _scan_cache["sig"] != sig or _scan_cache["domains"] is None:
            _scan_cache["domains"] = scan_corpus(content)
            _scan_cache["sig"] = sig
        return _scan_cache["domains"]

    def safe_rel(rel: str, exts=SERVABLE_EXTS) -> Path:
        # Windows 上 content 可能经 8.3 短路径传入, 统一以 resolve() 后的形式比较
        root_resolved = content.resolve()
        p = (content / rel).resolve()
        if root_resolved not in p.parents or p.suffix not in exts:
            abort(400, "path escapes content/ or has a non-servable extension")
        return p

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
        dom_obj = next((d for d in domains if d["id"] == domain), None)
        if not dom_obj:
            return None
        subs = dom_obj["subs"]
        sobj = next((s for s in subs if s["id"] == sub), None)
        if not sobj:
            return None
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

    @app.context_processor
    def chrome():
        tax = load_taxonomy(content)

        def av(name):
            """静态资源版本号：按文件 mtime 自动失效，改完刷新即生效，免手动 ?v=。"""
            try:
                return int((root / "static" / name).stat().st_mtime)
            except OSError:
                return 0

        return {"LABELS": tax["domains"], "SUB_LABELS": tax["subs"],
                "SOURCE_LABELS": tax["sources"], "STATUS_LABELS": tax["status"],
                "HUES": tax["hues"],
                "av": av,
                "obsidian_connected": obsidian_vault_connected(content)}

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

    # 蓝图注册：全部业务路由在 routes_*.py，这里只把装配期的闭包/配置注入进去
    _hooks = {
        "domains_cached": domains_cached,
        "safe_rel": safe_rel,
        "collect_doc": collect_doc,
        "get_rag": get_rag,
        "query_rag": query_rag,
        "rag_status": rag_status,
        "rag_import_error": _RAG_IMPORT_ERROR,
        "RagStore": RagStore,
        "ReadingStore": ReadingStore,
    }
    for _register in (register_pages, register_doc, register_edit, register_files,
                      register_stats, register_rag, register_learn, register_search):
        _register(app, _hooks)

    return app


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
app = create_app()

if __name__ == "__main__":
    if "--import-check" in sys.argv:
        # 回归测试入口（tests/test_reader.py）：验证脚本直启导入链 + create_app 完整走通
        # 后即退出；不绑端口、不进服务循环（watcher 为 daemon 线程，随进程退出）
        print("IMPORT-CHECK OK")
        raise SystemExit(0)
    app.run(host="127.0.0.1", port=5001, debug=False)
