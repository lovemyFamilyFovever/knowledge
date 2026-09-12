# -*- coding: utf-8 -*-
"""文档编辑接口：保存（/api/save）、备注（/api/note）、收藏（/api/favorite）、双链（/api/links）。

写入一律走 safe_rel 校验（防目录穿越 / 非可写扩展名 / _ 前缀目录），
依赖通过 flask.current_app.config 注入，严禁 from app.app import（循环导入）。
"""
import time
from pathlib import Path

from flask import Blueprint, abort, current_app, jsonify, request

from app import store
from app.fts import open_db, upsert_doc_in_index
from app.store import (WRITABLE_EXTS, notes_path, parse_frontmatter,
                       read_notes)

edit_bp = Blueprint("edit", __name__)


def _hooks() -> dict:
    return current_app.config.get("KB_HOOKS") or {}


def _content() -> Path:
    return Path(current_app.config["CONTENT"])


def _indexes() -> Path:
    return Path(current_app.config["INDEXES"])


def _safe_rel(rel: str, exts):
    return _hooks()["safe_rel"](rel, exts)


@edit_bp.post("/api/save")
def api_save():
    content = _content()
    indexes = _indexes()
    data = request.get_json(force=True)
    p = _safe_rel(data.get("path", ""), WRITABLE_EXTS)
    if any(part.startswith("_") for part in p.relative_to(content.resolve()).parts):
        abort(400, "不能写入 _ 前缀目录（回收站/暂存/元数据）")
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


@edit_bp.post("/api/note")
def api_note():
    data = request.get_json(force=True)
    p = _safe_rel(data.get("path", ""), WRITABLE_EXTS)
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "empty note"}), 400
    np = notes_path(p)
    with np.open("a", encoding="utf-8") as f:
        f.write(f"- [{time.strftime('%Y-%m-%d %H:%M')}] {text}\n")
    return jsonify({"ok": True, "notes": read_notes(p)})


@edit_bp.post("/api/favorite")
def api_favorite():
    data = request.get_json(force=True)
    p = _safe_rel(data.get("path", ""), WRITABLE_EXTS)
    fm, body = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
    fm["favorite"] = not (fm.get("favorite") is True)
    p.write_text(store.dump_frontmatter(fm, body), encoding="utf-8")
    return jsonify({"ok": True, "favorite": fm["favorite"]})


@edit_bp.get("/api/links")
def api_links():
    """双链查询：正向(它引用谁，含未解析)与反向(谁引用它)。"""
    content = _content()
    indexes = _indexes()
    p = _safe_rel(request.args.get("path", ""), WRITABLE_EXTS)
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


def register(app, hooks: dict):
    """由 app.py 调用：注入依赖 + 挂载蓝图。"""
    app.config.setdefault("KB_HOOKS", {}).update(hooks)
    app.register_blueprint(edit_bp)
