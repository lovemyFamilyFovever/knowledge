"""双链补全与断链检查（编辑器与统计页共用）。

2026-10-07 从 app/learn.py 拆出：原实现把候选集建在「FTS docs + cards.term」两路
来源上，而 cards 属于随复习系统一起退场的子系统。本模块只保留文档候选。

行为变化（用户已知并选定「全删，接受双链补全变弱」）：
- 候选池从约 4421 项（1264 docs + 3157 术语）降到仅 docs 一路；术语名不再出现在
  [[ 补全里。
- 打分规则、排序、坐标计算、Top1 建议语义与拆出前逐字符一致，未做任何"顺手优化"。

依赖方向：只读 indexes/index.db 与 taxonomy，严禁 import app.app（循环导入）。
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from app import fts
from app import store as kbstore

_CJK_PUNCT_CLASS = "，。；、！？：”’）】》%…·—"
_RE_SPACE_BEFORE_PUNCT = re.compile(rf"\s+([{_CJK_PUNCT_CLASS}])")
_RE_MULTI_SPACE = re.compile(r"\s{2,}")


def _tidy(text: str) -> str:
    """把 FTS 里「逐字插空格」的标题还原成能直接展示的样子。

    三步都不能省（2026-10-07 瘦身时漏了第一步，`[[ 补全会吐出「排 版 约 定 样 本」`，
    被 tests/test_ui_behavior.py 的三条双链断言抓红）：
      ① `fts.cjk_clean` 收掉「汉字 空格 汉字」——逐字 token 化的产物；
      ② 标点前的空格（cjk_clean 只管汉字之间，标点前的会留下，如 "AI 资产  · "）；
      ③ 收掉剩余多空格。
    """
    s = fts.cjk_clean(str(text or ""))
    s = _RE_SPACE_BEFORE_PUNCT.sub(r"\1", s)
    return _RE_MULTI_SPACE.sub(" ", s).strip()


def _is_subsequence(needle: str, hay: str) -> bool:
    it = iter(hay)
    return all(ch in it for ch in needle)


def _wl_score(name: str, ql: str) -> int:
    """双链候选统一打分：精确 100 > 前缀 90 > 包含 70 > 子序列 50 > 不匹配 -1。

    ql 为空（编辑器刚输入 [[ 就聚焦候选）返回 10 —— 与拆出前行为一致。
    """
    nl = str(name or "").lower()
    if not ql:
        return 10
    if nl == ql:
        return 100
    if nl.startswith(ql):
        return 90
    if ql in nl:
        return 70
    if _is_subsequence(ql, nl):
        return 50
    return -1


def _locate(text: str, target: str) -> tuple[int, int]:
    """返回 [[target 在正文里的 (行号, 列号)，均从 1 起；找不到返回 (0,0)。"""
    idx = text.find(f"[[{target}")
    if idx < 0:
        idx = text.find(target)
    if idx < 0:
        return 0, 0
    head = text[:idx]
    line = head.count("\n") + 1
    col = idx - (head.rfind("\n") + 1) + 1
    return line, col


def suggest_pool(indexes: Path) -> list[tuple[str, str, str]]:
    """候选集 [(name, rel, kind)]，一次构建、逐查询本地打分（B10 的性能结论保留）。"""
    cands: list[tuple[str, str, str]] = []
    try:
        con = fts.open_db(indexes)
        try:
            for path_, _title in con.execute("SELECT path, title FROM docs"):
                cands.append((_tidy(_title or ""), path_, "doc"))
        finally:
            con.close()
    except sqlite3.Error:
        pass
    return cands


def _rel_sub_label(content: Path, rel: str) -> str:
    if not rel:
        return ""
    parts = rel.split("/")
    try:
        tax = kbstore.load_taxonomy(content)
    except Exception:
        tax = None
    if len(parts) >= 3:
        if tax:
            return kbstore.sub_label(tax, parts[0], parts[1])
        return kbstore.SUB_LABELS.get(f"{parts[0]}/{parts[1]}", kbstore.SUB_LABELS.get(parts[1], parts[1]))
    if len(parts) == 2:
        return kbstore.domain_label(tax, parts[0]) if tax else kbstore.DOMAIN_LABELS.get(parts[0], parts[0])
    return ""


def top_suggestion(raw: str, pool: list[tuple[str, str, str]]) -> tuple[str, int]:
    """在候选集里为断链 raw 找 Top1 建议（纯本地，无 IO）。返回 (name, score)。"""
    ql = str(raw or "").strip().lower()
    best: tuple[str, int] = ("", 0)
    for name, _rel, _kind in pool:
        s = _wl_score(name, ql)
        if s > best[1] or (s == best[1] and best[0] and s > 0 and len(name) < len(best[0])):
            best = (name, s)
    return best


def wikilink_suggest(indexes: Path, content: Path, q: str,
                     exclude: str | None = None, limit: int = 8) -> list[dict]:
    """双链补全候选。排序：精确 100 > 前缀 90 > 包含 70 > 子序列 50；同分按标题长度升序。"""
    limit = max(1, min(int(limit or 8), 30))
    qn = str(q or "").strip()
    excluded = {x.strip() for x in str(exclude or "").split(",") if x.strip()}
    ql = qn.lower()
    seen_names: set[str] = set()
    scored: list[tuple[int, int, str, dict]] = []
    for name, rel, kind in suggest_pool(indexes):
        if not name or name in excluded or name in seen_names:
            continue
        score = _wl_score(name, ql)
        if score < 0:
            continue
        seen_names.add(name)
        scored.append((-score, len(name), name,
                       {"name": name, "rel": rel, "kind": kind, "score": score,
                        "sub_label": _rel_sub_label(content, rel)}))
    scored.sort(key=lambda x: (x[0], x[1], x[2]))
    return [x[3] for x in scored[:limit]]


def wikilink_check(indexes: Path, body: str) -> dict:
    """正文([[双链]]) 健康度检查：未解析项 + Top1 建议 + 行列坐标。"""
    raw_text = str(body or "")
    links = fts.extract_wikilinks(raw_text)
    if not links:
        return {"total": 0, "dead": [], "dead_n": 0}
    try:
        con = fts.open_db(indexes)
        try:
            maps = fts.resolve_maps_from_db(con)
        finally:
            con.close()
    except sqlite3.Error:
        maps = ({}, {}, {})
    by_path, by_stem, by_title = maps
    pool = suggest_pool(indexes)
    sug_cache: dict[str, tuple[str, int]] = {}
    dead: list[dict] = []
    for raw in links:
        if fts.resolve_wikilink(raw, by_path, by_stem, by_title):
            continue
        if raw not in sug_cache:
            sug_cache[raw] = top_suggestion(raw, pool)
        sug_name, sug_score = sug_cache[raw]
        line, col = _locate(raw_text, raw)
        dead.append({"raw": raw, "line": line, "col": col,
                     "suggest": sug_name, "suggest_score": sug_score})
    return {"total": len(links), "dead": dead, "dead_n": len(dead)}
