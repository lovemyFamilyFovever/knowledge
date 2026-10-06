# -*- coding: utf-8 -*-
"""文档数据接口：语料分类树（/api/tree）与单篇文档详情（/api/doc）。

依赖注入同 routes_learn.py：通过 flask.current_app.config 取 CONTENT 与 KB_HOOKS，
严禁 from app.app import（循环导入）。
"""
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from app.store import _tree_sig

doc_bp = Blueprint("doc", __name__)


def _hooks() -> dict:
    return current_app.config.get("KB_HOOKS") or {}


def _content() -> Path:
    return Path(current_app.config["CONTENT"])


@doc_bp.get("/api/tree")
def api_tree():
    domains = _hooks()["domains_cached"]()
    return jsonify({"sig": _tree_sig(_content()), "domains": domains})


@doc_bp.get("/api/doc")
def api_doc():
    domains = _hooks()["domains_cached"]()
    data = _hooks()["collect_doc"](request.args.get("domain", ""),
                                   request.args.get("sub", ""),
                                   request.args.get("name", ""), domains)
    if data is None:
        return jsonify({"error": "not found"}), 404
    docs = data["sobj"]["docs"]
    return jsonify({"doc": data["doc"], "info_rows": data["info_rows"], "docs": docs})


def register(app, hooks: dict):
    """由 app.py 调用：注入依赖 + 挂载蓝图。"""
    app.config.setdefault("KB_HOOKS", {}).update(hooks)
    app.register_blueprint(doc_bp)
