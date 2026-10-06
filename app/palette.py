"""命令面板索引（前端单一入口）。

2026-10-07 从 app/learn.py 拆出：原实现的 terms 段来自 cards 表，而 cards 随复习
系统一起退场，故本模块只索引「文档 + 子域 + 固定命令」。_palette_sig 也随之从
md5(treesig|n_cards) 改为 md5(treesig) —— 指纹口径变了，前端缓存会在第一次打开时
自动整体重绘一次，属预期。
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from app import fts
from app import store as kbstore
from app.wikilink import _tidy

# 命令面板固定命令（前端按 id 渲染，勿改）
# 2026-10-07 删：goto-review / goto-quiz / goto-glossary（复习与术语门户已下线）
PALETTE_COMMANDS = [
    {"id": "go-home", "title": "前往 总览", "hint": "页面", "icon": "i-home", "action": '"/home"'},
    {"id": "toggle-theme", "title": "切换 深色 / 浅色", "hint": "命令", "icon": "i-moon",
     "action": '"kb:toggle-theme"'},
    {"id": "readpref", "title": "阅读偏好：字号 / 行宽 / 字体", "hint": "命令", "icon": "i-palette",
     "action": '"kb:readpref"'},
]


def palette_sig(content: Path) -> str:
    try:
        treesig = kbstore._tree_sig(content)
    except OSError:
        treesig = ""
    return hashlib.md5(str(treesig).encode("utf-8")).hexdigest()[:16]


def palette_index(indexes: Path, content: Path, sig: str | None = None,
                  hooks: dict | None = None) -> dict:
    """命令面板索引：文档 / 子域 / 命令 / 计数。

    sig 与当前语料指纹一致时返回 {"fresh": True}，前端可据此跳过重绘。
    indexes / content 一律由调用方（路由层读 flask config）注入，本模块不猜目录。
    """
    hooks = hooks or {}
    current = palette_sig(content)
    if sig and str(sig) == current:
        return {"fresh": True, "sig": current}

    # 不加 LIMIT：命令面板的卖点是「单一入口」，静默截断会让文档压根搜不到，
    # 且与 palette_sig（按全量语料算）不一致 —— sig 变了列表却没变，前端重绘后仍缺项。
    docs: list[dict] = []
    try:
        con = fts.open_db(indexes)
        try:
            for path_, _title in con.execute("SELECT path, title FROM docs ORDER BY path"):
                docs.append({"name": _tidy(_title or ""), "rel": path_, "kind": "doc"})
        finally:
            con.close()
    except sqlite3.Error:
        docs = []

    subs: list[dict] = []
    getter = hooks.get("domains_cached")
    if callable(getter):
        try:
            for dom in getter():
                for s in dom.get("subs", []):
                    subs.append({"id": f"{dom['id']}/{s['id']}", "name": s["label"],
                                 "kind": "sub", "domain": dom["id"]})
        except Exception:
            subs = []

    return {
        "sig": current, "fresh": False, "terms": [], "docs": docs, "subs": subs,
        "commands": [dict(c) for c in PALETTE_COMMANDS],
        "counts": {"terms": 0, "docs": len(docs), "subs": len(subs),
                   "commands": len(PALETTE_COMMANDS)},
    }
