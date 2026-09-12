# -*- coding: utf-8 -*-
"""知库 FTS 层 —— sqlite FTS5 全文索引 + [[双链]] 解析 + 关键词搜索。

index.db 是纯派生缓存：可随时删除，启动/后台按 mtime 增量重建。
外科手术式更新（单文档 REPLACE / DELETE）供路由层在写回时调用。
"""
import re
import sqlite3
import time
from pathlib import Path

from app.store import SKIP_DIRS, SQLITE_BUSY_TIMEOUT_S, _tree_sig, md_files, parse_frontmatter

# unicode61 分词器把连续中文当作单个长 token, 导致"量子"搜不到"量子纠缠"。
# 索引侧给每个中文字符后插空格(逐字 token), 查询侧把中文词构造成逐字短语,
# 展示前再把字符间空格清掉 —— 这是无外部分词依赖时的标准做法。
CJK_RUN = re.compile(r"[\u4e00-\u9fff]+")
CJK_CHAR = re.compile(r"([\u4e00-\u9fff])")
CJK_GAP = re.compile(r"([\u4e00-\u9fff]) (?=[\u4e00-\u9fff])")
# [[双链]]：剔除代码块与行内代码后提取，目标支持 别名/锚点 后缀
FENCE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.S)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
WIKILINK_RE = re.compile(r"!?\[\[([^\[\]|#]+)(?:#[^\[\]|]*)?(?:\|[^\[\]]*)?\]\]")


def open_db(indexes: Path) -> sqlite3.Connection:
    indexes.mkdir(parents=True, exist_ok=True)
    # timeout= 即 busy_timeout：撞上 _index_watcher 的重建事务时排队等，而不是立刻炸
    con = sqlite3.connect(indexes / "index.db", timeout=SQLITE_BUSY_TIMEOUT_S)
    con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(path UNINDEXED, title, tags, body)")
    con.execute("CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)")
    con.execute("""CREATE TABLE IF NOT EXISTS links(
        src TEXT, dst TEXT, raw TEXT, resolved INTEGER,
        src_title TEXT, dst_title TEXT)""")
    return con


def build_index(content: Path, indexes: Path) -> int:
    """Full rebuild; 500+ docs rebuild in well under a second."""
    sig = _tree_sig(content)  # 扫描开始时的快照；扫描期间的改动会让存的签名落后 → 下轮判 stale 自动补建
    con = open_db(indexes)
    try:
        con.execute("DELETE FROM docs")
        con.execute("DELETE FROM links")
        docs_seen: dict[str, dict] = {}  # path -> {title, stem}
        pending: list[tuple[str, str, list[str]]] = []  # (path, title, raw links)
        n = 0
        for p, rel in md_files(content):
            fm, body = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
            title = str(fm.get("title") or p.stem)
            tags = fm.get("tags")
            tag_str = " ".join(tags) if isinstance(tags, list) else str(tags or "")
            con.execute("INSERT INTO docs(path,title,tags,body) VALUES(?,?,?,?)",
                        (rel, cjk_space(title), cjk_space(tag_str), cjk_space(body)))
            docs_seen[rel] = {"title": title, "stem": p.stem}
            pending.append((rel, title, extract_wikilinks(body)))
            n += 1

        # 双链解析：目标依次匹配 完整相对路径(不带扩展名) / 文件名 / 标题
        by_path = {rel.rsplit(".md", 1)[0]: rel for rel in docs_seen}
        by_stem: dict[str, list[str]] = {}
        by_title: dict[str, list[str]] = {}
        for rel, info in docs_seen.items():
            by_stem.setdefault(info["stem"], []).append(rel)
            by_title.setdefault(info["title"], []).append(rel)

        for src, src_title, raws in pending:
            for raw in raws:
                dst = resolve_wikilink(raw, by_path, by_stem, by_title)
                dst_title = docs_seen[dst]["title"] if dst else ""
                con.execute("INSERT INTO links(src,dst,raw,resolved,src_title,dst_title) VALUES(?,?,?,?,?,?)",
                            (src, dst or "", raw, 1 if dst else 0, src_title, dst_title))
        con.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('built_at',?)", (str(time.time()),))
        con.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('doc_n',?)", (str(n),))
        con.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('treesig',?)", (sig,))
        con.commit()
        return n
    finally:
        con.close()


def index_is_stale(content: Path, indexes: Path) -> bool:
    """B11：以「文件清单+逐文件 mtime_ns」的树签名为准 —— 旧的最大 mtime 比较
    只看前进：外部删除不碰任何 mtime（幽灵行长期残留），从 _trash rename 恢复
    保留旧 mtime（恢复的文档永远搜不到）。旧库无 treesig 时回退 mtime 判据。"""
    con = open_db(indexes)
    try:
        row = con.execute("SELECT v FROM meta WHERE k='treesig'").fetchone()
        if row is not None:
            try:
                return row[0] != _tree_sig(content)
            except OSError:
                return True
        row = con.execute("SELECT v FROM meta WHERE k='built_at'").fetchone()
        if not row:
            return True
        newest = max((p.stat().st_mtime for p, _ in md_files(content)), default=0)
        return newest > float(row[0])
    finally:
        con.close()


def extract_wikilinks(body: str) -> list[str]:
    clean = INLINE_CODE_RE.sub("", FENCE_RE.sub("", body))
    return [m.group(1).strip() for m in WIKILINK_RE.finditer(clean)]


def resolve_wikilink(raw: str, by_path: dict, by_stem: dict, by_title: dict) -> str | None:
    raw = raw.strip()
    for suffix in (".md", ".html"):
        if raw.endswith(suffix):
            raw = raw[: -len(suffix)]
            break
    if raw in by_path:
        return by_path[raw]
    if len(by_stem.get(raw, [])) == 1:
        return by_stem[raw][0]
    hit = by_title.get(raw) or by_title.get(raw.replace(" ", ""))
    if hit and len(hit) == 1:
        return hit[0]
    return None


def resolve_maps_from_db(con):
    # 从 docs 索引表构建解析映射；标题字段已 cjk_space，需 cjk_clean 还原后再匹配
    by_path: dict = {}
    by_stem: dict = {}
    by_title: dict = {}
    for path_, db_title in con.execute("SELECT path, title FROM docs"):
        by_path[path_] = db_title
        stem = path_.rsplit("/", 1)[-1]
        if stem.endswith(".md"):
            stem = stem[:-3]
        by_stem.setdefault(stem, []).append(path_)
        by_title.setdefault(cjk_clean(db_title).replace(" ", ""), []).append(path_)
    return by_path, by_stem, by_title


def cjk_space(text: str) -> str:
    return CJK_CHAR.sub(r"\1 ", text)


def cjk_clean(text: str) -> str:
    return CJK_GAP.sub(r"\1", text)


def build_match(q: str) -> str:
    terms = re.findall(r"\w+", q)
    phrases = []
    for t in terms:
        runs = re.findall(r"[\u4e00-\u9fff]+|[^\u4e00-\u9fff]+", t)
        parts = [cjk_space(r).strip() if CJK_RUN.fullmatch(r) else r for r in runs]
        phrases.append('"' + " ".join(parts) + '"*')
    return " OR ".join(phrases)


def search(indexes: Path, q: str, limit: int = 50) -> list[dict]:
    if not re.findall(r"\w+", q):
        return []
    match = build_match(q)
    con = open_db(indexes)
    try:
        rows = con.execute(
            "SELECT path, title, snippet(docs, 3, '<mark>', '</mark>', 12, 24) "
            "FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT ?",
            (match, limit),
        ).fetchall()
        return [{"path": r[0], "title": cjk_clean(r[1]), "snippet": cjk_clean(r[2])} for r in rows]
    finally:
        con.close()


def upsert_doc_in_index(indexes: Path, rel_posix: str, p: Path, body: str) -> None:
    """单文档外科手术式更新：仅替换本文档的正文与双链行（毫秒级）。"""
    fm2, body2 = parse_frontmatter(body)
    title = str(fm2.get("title") or p.stem)
    tags = fm2.get("tags")
    tag_str = " ".join(tags) if isinstance(tags, list) else str(tags or "")
    con = open_db(indexes)
    try:
        con.execute("DELETE FROM docs WHERE path=?", (rel_posix,))
        con.execute("INSERT INTO docs(path,title,tags,body) VALUES(?,?,?,?)",
                    (rel_posix, cjk_space(title), cjk_space(tag_str), cjk_space(body2)))
        con.execute("DELETE FROM links WHERE src=?", (rel_posix,))
        _, by_stem, by_title = resolve_maps_from_db(con)
        # B12：与 build_index 同构 —— 完整相对路径键（不带 .md）。
        # 旧实现用「文件名去扩展名」当键，[[career/journal/xxx]] 这类路径式目标
        # 在每次保存后的 30s 窗口里被标成未解析（双链面板/全局统计读数失真）。
        by_path = {(p.rsplit(".md", 1)[0]): p
                   for (p,) in con.execute("SELECT path FROM docs")}
        for raw in extract_wikilinks(body2):
            dst = resolve_wikilink(raw, by_path, by_stem, by_title)
            dst_title = ""
            if dst:
                row = con.execute("SELECT title FROM docs WHERE path=?", (dst,)).fetchone()
                dst_title = cjk_clean(row[0]) if row else ""
            con.execute("INSERT INTO links(src,dst,raw,resolved,src_title,dst_title) VALUES(?,?,?,?,?,?)",
                        (rel_posix, dst or "", raw, 1 if dst else 0, title, dst_title))
        # 本次保存可能新建/改名了某篇文档，让其它文档此前的未解析链接就地复活，
        # 不必等 watcher 全量重建（外科手术更新的另一半：全局未解析行重解析）。
        pending = con.execute("SELECT rowid, src, raw FROM links WHERE resolved=0").fetchall()
        for rid, src_doc, raw in pending:
            dst = resolve_wikilink(raw, by_path, by_stem, by_title)
            if not dst:
                continue
            row = con.execute("SELECT title FROM docs WHERE path=?", (dst,)).fetchone()
            con.execute("UPDATE links SET dst=?, resolved=1, dst_title=? WHERE rowid=?",
                        (dst, cjk_clean(row[0]) if row else "", rid))
        con.commit()
    finally:
        con.close()


def remove_doc_from_index(indexes: Path, rel_posix: str) -> None:
    """单文档外科手术式删除：正文 + 双链（作为 src 与 dst 两个方向）。"""
    con = open_db(indexes)
    try:
        con.execute("DELETE FROM docs WHERE path=?", (rel_posix,))
        con.execute("DELETE FROM links WHERE src=?", (rel_posix,))
        con.execute("DELETE FROM links WHERE dst=?", (rel_posix,))
        con.commit()
    finally:
        con.close()
