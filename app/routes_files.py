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


def _free_path(target: Path) -> Path:
    """回收站同日秒级碰撞时加 ~N 后缀（B7：旧实现同秒二次删除直接 rename 冲突 500，
    从 _trash 恢复后又删不掉的场景同理）。"""
    if not target.exists():
        return target
    i = 2
    while True:
        cand = target.with_name(f"{target.stem}~{i}{target.suffix}")
        if not cand.exists():
            return cand
        i += 1


@files_bp.post("/api/delete")
def api_delete():
    """软删除：文档与其美化版、备注一起移入 content/_trash/<时间戳>/，
    保持相对结构，可随时手动恢复；git 历史是第二重保险。"""
    indexes = _indexes()
    content = _content()
    data = request.get_json(force=True)
    p = _safe_rel(data.get("path", ""), WRITABLE_EXTS)
    if not p.is_file():
        return jsonify({"ok": False, "error": "not found"}), 404
    root_resolved = content.resolve()
    rel = p.relative_to(root_resolved)
    trash = content / "_trash" / time.strftime("%Y%m%d-%H%M%S")
    moved = [rel.as_posix()]
    target = _free_path(trash / rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    p.rename(target)
    for sib in (p.with_name(p.name + ".notes.md"), p.with_name(p.stem + ".html")):
        if sib.is_file():
            s = _free_path(trash / sib.relative_to(root_resolved))
            s.parent.mkdir(parents=True, exist_ok=True)
            sib.rename(s)
            moved.append(sib.relative_to(root_resolved).as_posix())
    # 外科手术式索引删除：只移除本文档的正文与双链行（毫秒级）
    remove_doc_from_index(indexes, rel.as_posix())
    return jsonify({"ok": True, "moved": moved})


def _side_plan(src: Path, dst: Path) -> list[tuple[Path, Path]]:
    """旁挂文件（备注 / 美化版）的目标映射；与主文件同一预检清单搬。"""
    plan: list[tuple[Path, Path]] = []
    sib = src.with_name(src.name + ".notes.md")
    if sib.is_file():
        plan.append((sib, dst.with_name(dst.name + ".notes.md")))
    sib = src.with_name(src.stem + ".html")
    if sib.is_file():
        plan.append((sib, dst.with_name(dst.stem + ".html")))
    return plan


def _do_move(src: Path, dst: Path, dst_rel: str, s_rel: str) -> list[str]:
    """执行一次已校验的搬移：① 磁盘 + 旁挂 ② FTS ③ 阅读状态 ④ 向量索引；
    返回搬走的旁挂后缀。"""
    indexes = _indexes()
    RagStore = _hooks().get("RagStore")
    dst.parent.mkdir(parents=True, exist_ok=True)
    # ① 磁盘：主文件 + 旁挂。B7：先预检全部目标再动盘 —— 旧实现主文件先搬、
    # 旁挂目标已存在时 sib.rename 抛 FileExistsError，留下「主文件已走、索引未更新」
    # 的半迁移状态并回 500。
    plan = [(src, dst)] + _side_plan(src, dst)
    for _s, d in plan:
        if d.exists():
            raise ValueError(f"目标目录已存在同名文件：{d.name}（先处理冲突再移动）")
    moved_sibs: list[str] = []
    for s, d in plan:
        s.rename(d)
        if s != src:
            moved_sibs.append(".notes.md" if d.name.endswith(".notes.md") else ".html")
    # ② FTS：外科手术式重建该文档行 + 双链（src 方向重写，dst 方向靠 resolve 重算）
    body = dst.read_text(encoding="utf-8", errors="replace")
    remove_doc_from_index(indexes, s_rel)
    upsert_doc_in_index(indexes, dst_rel, dst, body)
    # ③ 阅读状态：doc_marks / reading_events 的 path 主键随迁（B8：旧实现漏掉，
    # 整理语料一移动「已读完/已掌握」就丢，与卡片进度刻意路径无关的设计自相矛盾）
    ReadingStore = _hooks().get("ReadingStore")
    if ReadingStore is not None:
        try:
            rs = ReadingStore(indexes)
            try:
                rs.migrate_path(s_rel, dst_rel)
            finally:
                rs.close()
        except Exception:
            logger.warning("阅读状态随迁失败（%s → %s），标记不会跟随但不影响移动", s_rel, dst_rel,
                           exc_info=True)
    # ④ 向量索引：换路径（块内容未变，mtime 未变，直接搬 files 表元数据与 chunk 归属）
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


def _dst_rel_ok(dst_rel: str) -> bool:
    """目标路径合法性：.md、不含 ..、且任何段不得以 _ 开头（不变量 2：
    /api/move 不能成为把文档搬进 _trash/_inbox 的后门）。"""
    if not dst_rel or not dst_rel.endswith(".md") or dst_rel.startswith("/"):
        return False
    if ".." in dst_rel:
        return False
    return not any(seg.startswith("_") for seg in dst_rel.split("/") if seg)


def _resolve_dst(dst_rel: str):
    """校验并解析目标路径；非法时抛 ValueError（调用方翻译成 400 / per-item 失败）。"""
    if not _dst_rel_ok(dst_rel):
        raise ValueError("invalid dst（.md、不得含 .. 或 _ 前缀目录）")
    content = _content()
    root_resolved = content.resolve()
    dst = (content / dst_rel)
    dst_resolved = dst.resolve()
    if root_resolved not in dst_resolved.parents or dst_resolved.exists():
        raise ValueError("dst outside content/ or already exists")
    return dst


@files_bp.post("/api/inbox/ignore")
def api_inbox_ignore():
    """收件箱忽略（需求 #3）：把文件或其所在目录加入忽略清单，不再出现在待归档。
    body: {path: "_inbox/desktop/code/dev-output/x.md", scope: "file"|"dir"}
    scope=dir 时忽略该文件所在目录。清单落 _meta/inbox-ignore.json（可手工编辑回滚）。"""
    from app.store import add_inbox_ignore
    data = request.get_json(force=True)
    rel = str(data.get("path") or "")
    scope = str(data.get("scope") or "file")
    if scope not in ("file", "dir"):
        return jsonify({"ok": False, "error": "scope must be file|dir"}), 400
    if not rel.startswith("_inbox/"):
        return jsonify({"ok": False, "error": "path must start with _inbox/"}), 400
    if scope == "dir":
        inner = rel[len("_inbox/"):]
        if "/" in inner:
            rel = "_inbox/" + inner.rsplit("/", 1)[0]
        else:
            scope = "file"  # 根级文件无父目录可忽略，退化为忽略文件本身
    try:
        rules = add_inbox_ignore(_content(), rel, scope)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    return jsonify({"ok": True, "ignored": rel, "scope": scope, "rules": rules})


@files_bp.post("/api/move")
def api_move():
    """移动/重命名文档（含层级调整）。同步级联：
    ① 磁盘文件 + 旁挂（.notes.md / .html）；② FTS docs+links 表；
    ③ 阅读状态 reading.db；④ 向量索引 rag.db。src/dst 均为 content/ 相对 posix 路径。"""
    data = request.get_json(force=True)
    src = _safe_rel(data.get("src", ""), WRITABLE_EXTS)
    dst_rel = (data.get("dst", "") or "").strip().replace("\\", "/")
    if not _dst_rel_ok(dst_rel):
        return jsonify({"ok": False, "error": "invalid dst"}), 400
    try:
        dst = _resolve_dst(dst_rel)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    src_rel = src.relative_to(_content().resolve()).as_posix()
    try:
        moved_sibs = _do_move(src, dst, dst_rel, src_rel)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
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
