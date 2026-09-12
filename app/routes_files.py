# -*- coding: utf-8 -*-
"""文件操作接口：软删除（/api/delete）、移动/重命名（/api/move）、批量移动（/api/move/batch）。

移动需同步级联三处：① 磁盘主文件 + 旁挂；② FTS docs/links；③ 向量索引 rag.db。
RagStore 是可选依赖，由 create_app 经 KB_HOOKS 注入（可能为 None）。
"""
import logging
import time
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from app.fts import remove_doc_from_index, upsert_doc_in_index
from app.store import WRITABLE_EXTS

logger = logging.getLogger("kb.reader")

files_bp = Blueprint("files", __name__)


def _hooks() -> dict:
    return current_app.config.get("KB_HOOKS") or {}


def _content() -> Path:
    return Path(current_app.config["CONTENT"])


def _indexes() -> Path:
    return Path(current_app.config["INDEXES"])


def _safe_rel(rel: str, exts):
    return _hooks()["safe_rel"](rel, exts)


@files_bp.post("/api/delete")
def api_delete():
    """软删除：文档与其美化版、备注一起移入 content/_trash/<时间戳>/，
    保持相对结构，可随时手动恢复；git 历史是第二重保险。"""
    indexes = _indexes()
    content = _content()
    data = request.get_json(force=True)
    p = _safe_rel(data.get("path", ""), WRITABLE_EXTS)
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


def _do_move(src: Path, dst: Path, dst_rel: str, s_rel: str) -> list[str]:
    """执行一次已校验的搬移：① 磁盘 + 旁挂 ② FTS ③ 向量索引；返回搬走的旁挂后缀。"""
    indexes = _indexes()
    RagStore = _hooks().get("RagStore")
    dst.parent.mkdir(parents=True, exist_ok=True)
    # ① 磁盘：主文件 + 旁挂一起搬
    src.rename(dst)
    moved_sibs: list[str] = []
    for sib, sib_suffix in ((src.with_name(src.name + ".notes.md"), ".notes.md"),
                            (src.with_name(src.stem + ".html"), ".html")):
        if sib.is_file():
            sib_dst = dst.with_name(dst.name + ".notes.md") if sib_suffix == ".notes.md" \
                else dst.with_name(dst.stem + ".html")
            sib.rename(sib_dst)
            moved_sibs.append(sib_suffix)
    # ② FTS：外科手术式重建该文档行 + 双链（src 方向重写，dst 方向靠 resolve 重算）
    body = dst.read_text(encoding="utf-8", errors="replace")
    remove_doc_from_index(indexes, s_rel)
    upsert_doc_in_index(indexes, dst_rel, dst, body)
    # ③ 向量索引：换路径（块内容未变，mtime 未变，直接搬 files 表元数据与 chunk 归属）
    if RagStore is not None:
        try:
            rstore = RagStore(indexes)
            if rstore.known_files().get(s_rel) is not None:
                rstore.con.execute("UPDATE vec_docs SET file=? WHERE file=?", (dst_rel, s_rel))
                rstore.con.execute(
                    "UPDATE vec_docs SET chunk_id=?||'::'||chunk_ix WHERE file=? AND chunk_id LIKE ?",
                    (dst_rel, s_rel, s_rel + ":%"))
                rstore.con.execute("UPDATE files SET path=? WHERE path=?", (dst_rel, s_rel))
                rstore.con.commit()
            rstore.close()
        except Exception:
            # 搬移失败不阻塞移动本身；留痕后由下轮 sync_rag 全量对齐
            logger.warning("向量索引搬移失败（%s → %s），待 sync_rag 对齐", s_rel, dst_rel,
                           exc_info=True)
    return moved_sibs


def _resolve_dst(dst_rel: str):
    """校验并解析目标路径；非法时抛 ValueError（调用方翻译成 400 / per-item 失败）。"""
    if not dst_rel or not dst_rel.endswith(".md") or dst_rel.startswith("/") or ".." in dst_rel:
        raise ValueError("invalid dst")
    content = _content()
    root_resolved = content.resolve()
    dst = (content / dst_rel)
    dst_resolved = dst.resolve()
    if root_resolved not in dst_resolved.parents or dst_resolved.exists():
        raise ValueError("dst outside content/ or already exists")
    return dst


@files_bp.post("/api/move")
def api_move():
    """移动/重命名文档（含层级调整）。同步级联：
    ① 磁盘文件 + 旁挂（.notes.md / .html）；② FTS docs+links 表；
    ③ 向量索引 rag.db。src/dst 均为 content/ 相对 posix 路径。"""
    data = request.get_json(force=True)
    src = _safe_rel(data.get("src", ""), WRITABLE_EXTS)
    dst_rel = (data.get("dst", "") or "").strip().replace("\\", "/")
    if not dst_rel or not dst_rel.endswith(".md") or dst_rel.startswith("/") or ".." in dst_rel:
        return jsonify({"ok": False, "error": "invalid dst"}), 400
    dst = _resolve_dst(dst_rel)
    src_rel = src.relative_to(_content().resolve()).as_posix()
    moved_sibs = _do_move(src, dst, dst_rel, src_rel)
    return jsonify({"ok": True, "src": src_rel, "dst": dst_rel, "moved_sibs": moved_sibs})


@files_bp.post("/api/move/batch")
def api_move_batch():
    """批量移动（收件箱批量归档用）。items: [{src,dst},...]；逐条独立执行，
    返回 per-item 成败清单，部分失败不回滚（前一条已成功者保持）。"""
    data = request.get_json(force=True)
    items = data.get("items") or []
    if not isinstance(items, list) or not items or len(items) > 50:
        return jsonify({"ok": False, "error": "items required (1-50)"}), 400
    results = []
    for it in items:
        src_rel = str(it.get("src", ""))
        dst_rel = str(it.get("dst", "")).strip().replace("\\", "/")
        try:
            src = _safe_rel(src_rel, WRITABLE_EXTS)
            dst = _resolve_dst(dst_rel)
            s_rel = src.relative_to(_content().resolve()).as_posix()
            _do_move(src, dst, dst_rel, s_rel)
            results.append({"src": s_rel, "dst": dst_rel, "ok": True})
        except Exception as e:
            results.append({"src": src_rel, "dst": dst_rel, "ok": False, "error": str(e)[:120]})
    return jsonify({"ok": True, "results": results,
                    "n_ok": sum(1 for r in results if r["ok"]),
                    "n_fail": sum(1 for r in results if not r["ok"])})


def register(app, hooks: dict):
    """由 app.py 调用：注入依赖 + 挂载蓝图。"""
    app.config.setdefault("KB_HOOKS", {}).update(hooks)
    app.register_blueprint(files_bp)
