# -*- coding: utf-8 -*-
"""语义检索接口：/api/rag（自然语言查询）与 /api/rag/status（就绪状态）。

RAG 是可选依赖（缺 numpy/sqlite-vec 时整体不可用）：create_app 导入失败会把
get_rag / query_rag / rag_status 置为 None 并经 KB_HOOKS 注入，本模块据此如实
上报不可用（503 或 enabled=false），不炸 500。
"""
from flask import Blueprint, current_app, jsonify, request

rag_bp = Blueprint("rag", __name__)


def _hooks() -> dict:
    return current_app.config.get("KB_HOOKS") or {}


@rag_bp.get("/api/rag")
def api_rag():
    """语义检索：自然语言 → 向量 → 最近邻块。组件缺失/未就绪时返回 503。"""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "empty query"}), 400
    get_rag = _hooks().get("get_rag")
    emb, rstore = get_rag() if get_rag else (None, None)
    if emb is None or rstore is None:
        return jsonify({"error": "rag unavailable",
                        "detail": _hooks().get("rag_import_error") or "init failed"}), 503
    try:
        k = min(int(request.args.get("k", 8)), 30)
    except ValueError:
        k = 8
    domain = request.args.get("domain") or None
    sub = request.args.get("sub") or None
    try:
        hits = _hooks()["query_rag"](rstore, emb, q, k=k, domain=domain, sub=sub)
    except Exception as e:
        return jsonify({"error": "rag query failed", "detail": str(e)}), 503
    return jsonify({"q": q, "hits": hits})


@rag_bp.get("/api/rag/status")
def api_rag_status():
    rag_status = _hooks().get("rag_status")
    if rag_status is None:  # rag 组件导入失败：如实上报，不炸 500
        return jsonify({"enabled": False, "chunks": 0, "model": "",
                        "detail": _hooks().get("rag_import_error")})
    get_rag = _hooks().get("get_rag")
    _emb, rstore = get_rag() if get_rag else (None, None)
    st = rag_status(rstore)
    st["detail"] = _hooks().get("rag_import_error")
    return jsonify(st)


def register(app, hooks: dict):
    """由 app.py 调用：注入依赖 + 挂载蓝图。"""
    app.config.setdefault("KB_HOOKS", {}).update(hooks)
    app.register_blueprint(rag_bp)
