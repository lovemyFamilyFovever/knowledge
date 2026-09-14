# -*- coding: utf-8 -*-
"""文档编辑接口：保存（/api/save）、备注（/api/note）、收藏（/api/favorite）、双链（/api/links）。

写入一律走 safe_rel 校验（防目录穿越 / 非可写扩展名 / _ 前缀目录），
依赖通过 flask.current_app.config 注入，严禁 from app.app import（循环导入）。
"""
import json
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
    # 已有 frontmatter 的原文照写，不做任何改写。
    # B6 修复：编辑器里全选删除正文再保存，body 不含 fm —— 旧逻辑直接落 stamp，
    # 把原文档的 title/tags/source/collected 全部抹掉。现在先尝试从磁盘原文件
    # 找回 frontmatter 块补回头部；找不回（新文件/原文件本就无 fm）才补 stamp。
    fm, _ = parse_frontmatter(body)
    if not fm:
        merged = store.prepend_original_fm(p, body)
        if merged is not None:
            body = merged
            fm, _ = parse_frontmatter(body)
        else:
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
    """收藏切换。B1 修复：旧实现 parse→dump 整块重建 frontmatter，对含嵌套
    YAML 结构的语料（实测 41 篇，如 handbook/index.md 的 hero:/features: 块）
    会压平毁结构、把布尔写成带引号字符串。现改为行级手术：只动 favorite 一行，
    其余字节原样；结构无法安全判定时拒绝改写并给出人话错误。"""
    data = request.get_json(force=True)
    p = _safe_rel(data.get("path", ""), WRITABLE_EXTS)
    if not p.is_file():
        abort(404, "not found: 文件不存在（可能已被删除或移动）")
    try:
        new_val = store.toggle_fm_bool(p, "favorite")
    except ValueError as e:
        abort(422, f"该文档的 frontmatter 结构无法安全切换收藏：{e}")
    return jsonify({"ok": True, "favorite": new_val})


@edit_bp.post("/api/tags")
def api_tags():
    """标签编辑（需求 #2）：set 全量覆写 / add 追加去重 / remove 逐个移除。

    与 favorite 同一套行级手术纪律：只动 tags 一行，其余字节原样；
    tags 出现在嵌套结构中时拒绝改写（422）。写回后外科手术式更新 FTS
    （tags 参与搜索权重），并清 taxonomy 标签缓存。
    契约：{path, op: set|add|remove, tags: [..]}
    返回：{ok, tags}（操作后的全量标签列表，服务端为准）。
    """
    data = request.get_json(force=True)
    p = _safe_rel(data.get("path", ""), WRITABLE_EXTS)
    if not p.is_file():
        abort(404, "not found: 文件不存在（可能已被删除或移动）")
    op = data.get("op") or "set"
    incoming = data.get("tags", [])
    if not isinstance(incoming, list):
        abort(400, "tags 必须是数组")
    # 规范化：去空白、去空串、去重、每枚 ≤32 字（防手滑粘一整段）
    incoming = list(dict.fromkeys(
        str(t).strip() for t in incoming if str(t).strip()
    ))
    for t in incoming:
        if len(t) > 32:
            abort(400, f"标签过长（>32 字）：{t}")

    raw = p.read_bytes()
    had_bom = raw[:3] == b"\xef\xbb\xbf"
    text = store._decode_md(raw)
    fm, _ = store.parse_frontmatter(text)
    cur = fm.get("tags")
    if cur is None:
        cur = []
    elif isinstance(cur, list):
        cur = [str(t) for t in cur]
    else:
        # 标量写法 `tags: 随笔` → 当作单标签
        cur = [str(cur)] if str(cur).strip() else []

    if op == "set":
        new_tags = incoming
    elif op == "add":
        new_tags = cur + [t for t in incoming if t not in cur]
    elif op == "remove":
        drop = set(incoming)
        new_tags = [t for t in cur if t not in drop]
    else:
        abort(400, f"未知 op：{op}（可选 set / add / remove）")

    # 行级写回：无块/空值时写 tags: []，非空写 [a, b, c]（与 dump_frontmatter 同风格）
    value = "[" + ", ".join(new_tags) + "]" if new_tags else "[]"
    try:
        out = store.set_fm_scalar(text, "tags", value)
    except ValueError as e:
        abort(422, f"该文档的 frontmatter 结构无法安全编辑标签：{e}")
    p.write_bytes(store._encode_md(out, had_bom))

    # FTS 同步（同 /api/save 的外科手术，但不改正文/双链——tags 行变了而已）
    content = _content()
    rel_posix = p.relative_to(content.resolve()).as_posix()
    upsert_doc_in_index(_indexes(), rel_posix, p, out)
    return jsonify({"ok": True, "tags": new_tags})


@edit_bp.post("/api/mkdir")
def api_mkdir():
    """新建子域目录（需求 #4）：domain 下一级，或 domain/sub 下嵌套一级。
    磁盘建目录 + 可选写入 taxonomy.json 显示名（不变量 5：分类学权威在 JSON）。
    空目录也会入树（n=0，第二轮 #2）；建完必清 _TAX_CACHE（三轮 #6，
    移出 if label:），_tree_sig 已含目录 → 树立即刷新。返回 created 路径供前端直接跳转。"""
    data = request.get_json(force=True)
    domain = str(data.get("domain") or "").strip().strip("/")
    parent = str(data.get("parent") or "").strip().strip("/")  # "" = 域根下；否则 "domain/sub"
    name = str(data.get("name") or "").strip()
    label = str(data.get("label") or "").strip()

    from app.store import SKIP_DIRS
    if not name or any(ch in name for ch in "\\/") or name.startswith("_") or name in SKIP_DIRS:
        return jsonify({"ok": False, "error": "目录名不合法（不能含斜杠、不能下划线开头）"}), 400
    if "/" in domain or not domain or domain.startswith("_"):
        return jsonify({"ok": False, "error": "invalid domain"}), 400
    if parent:
        pp = parent.split("/")
        if len(pp) != 2 or pp[0] != domain or any(x.startswith("_") for x in pp):
            return jsonify({"ok": False, "error": "parent 必须是 domain/sub 形式"}), 400

    content = _content()
    base = content / domain / parent.split("/")[1] if parent else content / domain
    target = base / name
    try:
        target.resolve().relative_to(content.resolve())
    except ValueError:
        return jsonify({"ok": False, "error": "路径越界"}), 400
    if target.exists():
        return jsonify({"ok": False, "error": "目录已存在"}), 400

    try:
        target.mkdir(parents=True, exist_ok=False)
    except OSError as e:
        return jsonify({"ok": False, "error": f"创建失败：{e}"}), 500

    rel_created = target.relative_to(content).as_posix()
    if label:
        tax_path = content / "_meta" / "taxonomy.json"
        try:
            tax = json.loads(tax_path.read_text(encoding="utf-8")) if tax_path.exists() else {}
            subs = tax.setdefault("subs", {})
            subs[rel_created] = label
            tax_path.write_text(json.dumps(tax, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
        except (OSError, ValueError):
            pass  # taxonomy 写失败不回滚磁盘目录：目录仍可用，仅显示名为目录 id
    # 第三轮 #6：无条件清缓存 —— 此前清 _TAX_CACHE 写在 if label: 里，不填显示名时
    # 新目录虽落盘但 taxonomy/scan 缓存未失效，树不刷新；_tree_sig 已纳入目录，
    # 这里补齐 taxonomy 缓存这一半。
    store._TAX_CACHE.clear()

    return jsonify({"ok": True, "created": rel_created})


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
