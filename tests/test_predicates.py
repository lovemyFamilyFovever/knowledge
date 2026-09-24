# -*- coding: utf-8 -*-
"""知库**判定谓词层** smoke tests —— 专测"一个布尔/边界判错就静默坏掉"的那类逻辑。

运行：python tests/test_predicates.py

来历：P6 变异测试（覆盖台账 §10）把这层的断言空白量化了出来——`app/store.py` 与 `app/fts.py`
的判定性变异各 13 条存活，存活原因几乎全是「那行判定 8 套 smoke 一次都没执行到」。
本文件按那 26 条存活体逐条回填（台账 §10.10），每条断言都注明它焊住哪个变异（文件:行 + 算子 +
变异体编号），复跑命令见 §10.10 末。轮次 9 又补进 `learn.py`（重扫判据）与 `cards.py`（抽卡边界）。

全程只读真实 `content/`：语料一律在 `tempfile.TemporaryDirectory()` 里现造，
不写、不删任何真实文件（AGENTS 不变量 1/4）。
"""
import json
import logging as _logging
import os
import sqlite3 as _sq
import sys
import tempfile
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import cards, store  # noqa: E402
from app.cards import (CARDS_PARSER_VERSION, _collect_following, _MIN_DEF_LEN,  # noqa: E402
                       _next_heading_at_most, parse_file)
from app.fts import (_clean_snippet, build_index, index_is_stale, open_db,  # noqa: E402
                     resolve_maps_from_db, resolve_wikilink)
from app.learn import (META_FILE_COUNT, META_PARSER, META_SYNCED_AT, CorpusEmpty,  # noqa: E402
                       LearnStore, _note_if_locked, _tag_list)
from app.store import (add_inbox_ignore, inbox_count, inbox_ignore_rules,  # noqa: E402
                       inbox_iter, load_taxonomy, md_files, obsidian_vault_connected,
                       parse_frontmatter, prepend_original_fm, set_fm_scalar)

passed = failed = 0


def check(name: str, cond: bool, extra="") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS {name}")
    else:
        failed += 1
        print(f"  FAIL {name} {extra}")


def mk(content: Path, rel: str, text: str = "") -> Path:
    p = content / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text or f"---\ntitle: {p.stem}\n---\n\n正文\n", encoding="utf-8")
    return p


def bump_mtime(p: Path, delta: float = 100.0) -> None:
    """显式把 mtime 推后，避免文件系统时间戳精度把「缓存该失效」这类断言跑成偶发。"""
    st = p.stat()
    os.utime(p, (st.st_atime + delta, st.st_mtime + delta))


# ---------------------------------------------------------------- store：解码与 frontmatter 手术
def test_decode_and_frontmatter() -> None:
    """焊住 `_decode_md` / `parse_frontmatter` / `set_fm_scalar` / `prepend_original_fm`。"""
    # #44 store.py:198 `raw[:3] == b"\\xef\\xbb\\xbf"` → `!=`：带 BOM 的 md 按裸 utf-8 解，
    # \ufeff 混进正文首字符 → 标题、FM_RE、首行匹配全部错位
    check("_decode_md：带 BOM 的 utf-8 解出的正文不含 \\ufeff",
          store._decode_md("﻿标题".encode("utf-8")) == "标题")
    check("_decode_md：无 BOM 的正文原样解出",
          store._decode_md("普通正文".encode("utf-8")) == "普通正文")

    # #48 store.py:163 `startswith("[") and endswith("]")` → `or`：只「起头是方括号」的
    # 残缺值被当成列表按逗号切，整行语义被切碎
    fm, _ = parse_frontmatter('---\ntitle: T\ntags: [A, B\nt: [X, Y]\n---\n\n正文\n')
    check("parse_frontmatter：未闭合的 `[A, B` 按字符串保留（不当列表切）",
          fm["tags"] == "[A, B", f"got {fm['tags']!r}")
    check("parse_frontmatter：配对的 `[X, Y]` 才解析成列表",
          fm["t"] == ["X", "Y"], f"got {fm['t']!r}")

    # #71 store.py:224 `"---..." + text` → `-`：无 frontmatter 的文档（刚拖进收件箱的裸 md）
    # 一收藏就字符串相减 → TypeError → 500
    try:
        out = set_fm_scalar("# 无块文档\n\n正文\n", "favorite", "true")
        check("set_fm_scalar：无 frontmatter 的文档会补一个最小块",
              out.startswith("---\nfavorite: true\n---\n\n"), f"got {out[:40]!r}")
        check("set_fm_scalar：补出的块能被解析回来（不是装饰性文本）",
              parse_frontmatter(out)[0].get("favorite") is True, f"got {out[:60]!r}")
        check("set_fm_scalar：补块后原正文一字不动地跟在后面",
              out.endswith("# 无块文档\n\n正文\n"), f"got {out[-30:]!r}")
    except TypeError as e:
        check("set_fm_scalar：无 frontmatter 的文档会补一个最小块", False, f"TypeError: {e}")

    # #70 store.py:269 `if not head.endswith("\\n")` → 去掉 not：反向补换行 →
    # original 块与正文之间多出一层空行，写回后整块 diff 被弄脏
    with tempfile.TemporaryDirectory() as td:
        p = mk(Path(td) / "content" / "ai", "x.md", "---\ntitle: 原始块\n---\n\n旧正文\n")
        got = prepend_original_fm(p, "新正文")
        check("prepend_original_fm：原块与正文之间只留一层空行（不重复补 \\n）",
              got == "---\ntitle: 原始块\n---\n\n新正文", f"got {got!r}")


# ---------------------------------------------------------------- store：缓存判据（改了就生效）
def test_caches_respond_to_mtime() -> None:
    """taxonomy / inbox-ignore 的 mtime 缓存命中判据。

    判据被改成永不成立 → 每次调用都重读重算（进页变慢、统计口径抖动）；
    改成反向（`!=`）→ 改了文件却不生效，正是「分类学是权威」这条不变量的执行层漏洞。
    用「同一对象」断言把命中本身钉住：未命中必然返回新 dict。
    """
    with tempfile.TemporaryDirectory() as td:
        content = Path(td) / "content"
        (content / "_meta").mkdir(parents=True)
        tax = mk(content / "_meta", "taxonomy.json",
                 json.dumps({"domains": {"ai": {"label": "AI"}}}, ensure_ascii=False))
        store._TAX_CACHE.clear()
        a = load_taxonomy(content)
        b = load_taxonomy(content)
        check("load_taxonomy：mtime 未变 → 命中缓存返回同一对象（store.py:104 判据）",
              a is b, "第二次调用重算了 → 命中判据失效")
        check("load_taxonomy：命中缓存时口径仍正确（不是返回了空壳）",
              a["domains"].get("ai") == "AI", f"got {a['domains'].get('ai')!r}")
        mk(content / "_meta", "taxonomy.json",
           json.dumps({"domains": {"ai": {"label": "人工智能"}}}, ensure_ascii=False))
        bump_mtime(tax)
        c = load_taxonomy(content)
        check("load_taxonomy：改了 taxonomy.json → 立刻读到新口径（不误命中旧缓存）",
              c["domains"].get("ai") == "人工智能", f"got {c['domains'].get('ai')!r}")
        check("load_taxonomy：新口径不是旧对象（确实重算了）", c is not a)

    with tempfile.TemporaryDirectory() as td:
        content = Path(td) / "content"
        (content / "_meta").mkdir(parents=True)
        ig = mk(content / "_meta", "inbox-ignore.json", json.dumps({"files": ["a.md"], "dirs": []}))
        store._IGNORE_CACHE["rules"] = None
        store._IGNORE_CACHE["t"] = 0.0
        r1 = inbox_ignore_rules(content)
        r2 = inbox_ignore_rules(content)
        check("inbox_ignore_rules：mtime 未变 → 命中缓存返回同一对象（store.py:360 判据）",
              r1 is r2, "第二次调用重读了 → 命中判据失效")
        mk(content / "_meta", "inbox-ignore.json", json.dumps({"files": ["b.md"], "dirs": []}))
        bump_mtime(ig)
        r3 = inbox_ignore_rules(content)
        check("inbox_ignore_rules：改规则后立刻读到新规则",
              r3["files"] == ["b.md"] and r3 is not r1, f"got {r3}")


# ---------------------------------------------------------------- store：收件箱忽略与计数
def test_inbox_ignore() -> None:
    """`add_inbox_ignore` 的 scope 分支 + `inbox_iter` 的忽略匹配。"""
    with tempfile.TemporaryDirectory() as td:
        content = Path(td) / "content"
        inbox = content / "_inbox"
        mk(inbox, "keep.md")
        mk(inbox, "junk/a.md")
        mk(inbox, "junk/sub/deep.md")
        mk(inbox, "keep2.md")
        store._IGNORE_CACHE["rules"] = None
        store._IGNORE_CACHE["t"] = 0.0

        rules = add_inbox_ignore(content, "junk", "dir")
        check('add_inbox_ignore：scope="dir" 落到 dirs 而不是 files（store.py:387 判据）',
              rules["dirs"] == ["junk"] and rules["files"] == [], f"got {rules}")
        rels = sorted(r for _, r in inbox_iter(content))
        check("inbox_iter：目录级忽略滤掉整棵子树（store.py:426 判据）",
              rels == ["keep.md", "keep2.md"], f"got {rels}")

        rules = add_inbox_ignore(content, "keep.md", "file")
        check('add_inbox_ignore：scope="file" 落到 files',
              "keep.md" in rules["files"] and rules["dirs"] == ["junk"], f"got {rules}")
        rels = sorted(r for _, r in inbox_iter(content))
        check("inbox_iter：文件级忽略只命中这一个，不误伤同前缀的 keep2.md",
              rels == ["keep2.md"], f"got {rels}")


def test_inbox_count_ttl() -> None:
    """#64 store.py:442 `now - _INBOX_CACHE["t"] > 60` → `>=`：60 秒整点被判成过期，
    徽标每 60 秒无谓重扫全库；反向改（`<`）则永不刷新，新落收件箱的文件被吞掉。
    用假时钟把这一刻度钉死，不靠 sleep。"""
    with tempfile.TemporaryDirectory() as td:
        content = Path(td) / "content"
        inbox = content / "_inbox"
        mk(inbox, "a.md")
        mk(inbox, "b.md")
        store._IGNORE_CACHE["rules"] = None
        store._IGNORE_CACHE["t"] = 0.0
        real_time, real_cache = store.time, store._INBOX_CACHE
        try:
            store.time = types.SimpleNamespace(time=lambda: 1_000_000.0)
            store._INBOX_CACHE = {"n": 999, "t": 1_000_000.0 - 60}   # 恰好到点（差 60 秒整）
            check("inbox_count：TTL 恰好 60 秒整仍算新鲜（用缓存值，不重扫）",
                  inbox_count(content) == 999, f"got {inbox_count(content)}")
            store.time = types.SimpleNamespace(time=lambda: 1_000_000.0 + 0.1)
            check("inbox_count：过点 0.1 秒立刻重算（新文件不会被吞 60 秒）",
                  inbox_count(content) == 2, f"got {inbox_count(content)}")
        finally:
            store.time, store._INBOX_CACHE = real_time, real_cache


# ---------------------------------------------------------------- store：可见文档口径
def test_md_files_excludes_sidecars() -> None:
    """#67 store.py:291 `endswith(".md") and not endswith(".notes.md")` → `or`：
    备注旁挂会被当成正式文档进树、进索引、进统计（旁挂件是 sidecar，不是语料）。"""
    with tempfile.TemporaryDirectory() as td:
        content = Path(td) / "content"
        mk(content, "ai/llm/A.md", "---\ntitle: 正式篇\n---\n\n正文\n")
        mk(content, "ai/llm/A.notes.md", "备注内容\n")
        mk(content, "_inbox/B.md", "收件箱里的\n")
        mk(content, "projects/_tmp/C.md", "临时目录里的\n")
        rels = sorted(r for _, r in md_files(content))
        check("md_files：只收正式 .md（.notes.md 旁挂不入）",
              rels == ["ai/llm/A.md"], f"got {rels}")


# ---------------------------------------------------------------- store：Obsidian 接入判定
def test_obsidian_vault_connected() -> None:
    """#49 store.py:137 的 `not` 与 #43 store.py:146 的 `==`：判错会让没装 Obsidian 时
    按钮照常出现（点了没反应），或把**别的库**认成本库（打开别的项目）。"""
    exe_saved, cfg_saved = store.OBSIDIAN_EXE_CANDIDATES, store.OBSIDIAN_CONFIG
    try:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            content = root / "content"
            content.mkdir(parents=True)
            exe = root / "Obsidian.exe"
            cfg = mk(root, "obsidian.json", "{}")
            store.OBSIDIAN_CONFIG = cfg

            store.OBSIDIAN_EXE_CANDIDATES = [root / "不存在.exe"]
            mk(root, "obsidian.json", json.dumps({"vaults": {"1": {"path": str(content.resolve())}}}))
            check("obsidian_vault_connected：没装程序本体 → False（store.py:137 的 not 判据）",
                  obsidian_vault_connected(content) is False)

            exe.touch()
            store.OBSIDIAN_EXE_CANDIDATES = [exe]
            check("obsidian_vault_connected：装了且注册了本语料 → True",
                  obsidian_vault_connected(content) is True)

            mk(root, "obsidian.json", json.dumps({"vaults": {"1": {"path": str(root / "别的库")}}}))
            check("obsidian_vault_connected：注册的是别的库 → False（store.py:146 的 == 判据）",
                  obsidian_vault_connected(content) is False)

            mk(root, "obsidian.json", "{ 坏 JSON")
            check("obsidian_vault_connected：配置文件坏了 → False 而不是抛错",
                  obsidian_vault_connected(content) is False)
    finally:
        store.OBSIDIAN_EXE_CANDIDATES, store.OBSIDIAN_CONFIG = exe_saved, cfg_saved


# ---------------------------------------------------------------- fts：双链解析
def test_wikilink_resolution() -> None:
    """双链三种写法（完整相对路径 / 文件名 / 标题）各自都要落地；重名文件名必须**不猜**。"""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        content, indexes = root / "content", root / "indexes"
        mk(content, "ai/llm/目标篇.md", "---\ntitle: 目标标题\n---\n\n正文\n")
        mk(content, "career/目标篇.md", "---\ntitle: 另一个目标\n---\n\n正文\n")
        mk(content, "ai/llm/独一份.md", "---\ntitle: 独一份\n---\n\n正文\n")
        mk(content, "ai/llm/src.md", "---\ntitle: 源文档\n---\n\n"
                                    "[[ai/llm/目标篇]] [[独一份]] [[目标篇]]\n")
        n = build_index(content, indexes)
        check("build_index 扫到全部正式文档", n == 4, f"got {n}")

        con = open_db(indexes)
        try:
            rows = {(r[0], r[1]): r[2] for r in
                    con.execute("SELECT src, raw, resolved FROM links")}
            # #79/#80 fts.py:60 `rel.rsplit(".md", 1)[0]` → [-1]/[1]：路径式链接的键被换空
            check("路径式 [[ai/llm/目标篇]] 解析成功（fts.py:60 去扩展名的下标）",
                  rows.get(("ai/llm/src.md", "ai/llm/目标篇")) == 1,
                  f"got {rows.get(('ai/llm/src.md', 'ai/llm/目标篇'))}")
            # #94 fts.py:116 `len(by_stem.get(raw, [])) == 1` → `== 2`：唯一命中反而不解析、
            # 重名反而随便挑一个（点进错的文档）
            check("文件名重名（两个 目标篇）→ 判未解析，不猜（fts.py:116 唯一性判据）",
                  rows.get(("ai/llm/src.md", "目标篇")) == 0,
                  f"got {rows.get(('ai/llm/src.md', '目标篇'))}")
            check("文件名唯一命中 → 解析成功（同一判据的另一侧）",
                  rows.get(("ai/llm/src.md", "独一份")) == 1,
                  f"got {rows.get(('ai/llm/src.md', '独一份'))}")

            by_path, by_stem, by_title = resolve_maps_from_db(con)
            # #101/#102 fts.py:131 `path_.rsplit("/", 1)[-1]` → [0]/[2]：从库里重建映射时
            # 把整条路径当文件名（或崩）；#103 fts.py:133 `stem[:-3]` → `[:-2]`：留下 "d" 尾巴
            check("resolve_maps_from_db：by_stem 用「去目录 + 去 .md」的文件名做键",
                  "独一份" in by_stem and "ai/llm" not in by_stem and "独一份d" not in by_stem,
                  f"got {sorted(by_stem)[:6]}")
            # 轮次 9 统一口径后的契约：三处（build_index / upsert_doc_in_index / 这里）都是
            # 「去掉 .md 的完整相对路径 → 该路径」。旧版本这里键带 .md、值是标题，
            # 于是 learn.py 与 upsert 各自补了一张别名表来绕开它（重复实现 + 口径分叉）。
            check("resolve_maps_from_db：by_path 去掉 .md 且值是路径（与 build_index 同构）",
                  by_path.get("ai/llm/目标篇") == "ai/llm/目标篇.md"
                  and "ai/llm/目标篇.md" not in by_path, f"got {sorted(by_path)[:5]}")
            check("DB 版映射可直接解路径式双链（调用方不必再自建别名表）",
                  resolve_wikilink("ai/llm/目标篇", by_path, by_stem, by_title)
                  == "ai/llm/目标篇.md")
            check("resolve_maps_from_db 重建的映射与 build_index 内的歧义判定一致",
                  resolve_wikilink("目标篇", by_path, by_stem, by_title) is None
                  and resolve_wikilink("独一份", by_path, by_stem, by_title) == "ai/llm/独一份.md")
        finally:
            con.close()


def test_index_is_stale_boundary() -> None:
    """#77 fts.py:98 `newest > float(row[0])` → `>=`：最新文档 mtime 恰等于 built_at 时
    被判"永远过期" → 每次进页都全量重建索引（读盘 + 分词白跑，语料一大就卡）。"""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        content, indexes = root / "content", root / "indexes"
        p = mk(content, "ai/llm/A.md")
        build_index(content, indexes)
        con = open_db(indexes)
        try:
            con.execute("DELETE FROM meta WHERE k='treesig'")   # 逼到 mtime 判据那一支
            con.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('built_at',?)",
                        (str(p.stat().st_mtime),))              # 令 newest == built_at
            con.commit()
        finally:
            con.close()
        check("index_is_stale：newest 恰等于 built_at → 判新鲜（用 > 不用 >=）",
              index_is_stale(content, indexes) is False)
        bump_mtime(p, 500.0)
        check("index_is_stale：文档确实被改过 → 判过期（不能反向失效）",
              index_is_stale(content, indexes) is True)


def test_snippet_wiki_alias() -> None:
    """#82 fts.py:178 `m.group(2) or m.group(1)` → `and`：无别名的 [[目标]] 会被替换成
    None（搜索命中片段里直接冒出方括号噪声）。"""
    check("snippet：[[目标|别名]] 只留别名",
          _clean_snippet("前 [[目标|别名]] 后") == "前 别名 后",
          f"got {_clean_snippet('前 [[目标|别名]] 后')!r}")
    check("snippet：[[目标]] 无别名时留目标（or 改 and 后这一支返回 None）",
          _clean_snippet("前 [[目标]] 后") == "前 目标 后",
          f"got {_clean_snippet('前 [[目标]] 后')!r}")


# ---------------------------------------------------------------- learn：卡片库重扫判据
def _baike_md(term: str, def_len: int = 20, traps=()) -> str:
    body = "".join(f"- {t}\n" for t in traps)
    tail = f"\n## 常见误区\n\n{body}" if traps else ""
    return (f'---\ntitle: "{term}"\n---\n\n# {term}\n\n## 定义\n\n'
            f"**一句话定义：** {'定' * def_len}\n{tail}")


def test_ensure_synced_criteria() -> None:
    """`ensure_synced` 的「什么时候该重扫」四条判据 + `sync` 的空语料守卫 + 两个小工具函数。

    P6 实测这四条判据全裸（#106/#114/#115/#116 存活），而名义上守卫它的
    `test_learn.py::test_parser_version_bumped` 只断言常量 `CARDS_PARSER_VERSION >= 2`
    ——读常量不等于跑行为，把判据整个取反都不会红。这里逐条跑行为，
    **该重扫时必须重扫，不该重扫时绝不能重扫**，两侧都测。
    """
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        content, idx = root / "content", root / "indexes"
        d = content / "baike" / "algorithms"
        d.mkdir(parents=True)
        a = mk(d, "a.md", _baike_md("甲"))
        ls = LearnStore(idx, content)
        try:
            check("首次 ensure_synced 会建库（库为空 → 必须重扫）",
                  ls.ensure_synced(content) is not None)
            check("什么都没改时**不**重扫（四条判据反向都不能成立）",
                  ls.ensure_synced(content) is None)

            # #116 `newest > float(synced_at)` → `>=`：mtime 恰等于同步时刻就被判过期
            # → 每次打开复习页都全量重扫（语料上千篇就是几秒白等）
            ls.meta_set(META_SYNCED_AT, str(a.stat().st_mtime))
            check("重扫判据：newest 恰等于 synced_at → 判新鲜（用 > 不用 >=）",
                  ls.ensure_synced(content) is None)
            bump_mtime(a, 900.0)
            check("重扫判据：文档 mtime 真的前进了 → 重扫",
                  ls.ensure_synced(content) is not None)

            def _mark_fresh():
                """把 synced_at 推到未来，隔离出「只测这一条判据」的干净现场
                （上一轮的 bump_mtime 会让 newest 一直大于 now，不先归零就没法测反向）。"""
                ls.meta_set(META_SYNCED_AT, str(time.time() + 10_000))

            # #115 篇数判据（只看 mtime 感知不到「删除」，这是 mtime 判据的盲区补位）
            _mark_fresh()
            mk(d, "b.md", _baike_md("乙"))
            check("重扫判据：新增一篇（篇数变了）→ 重扫",
                  ls.ensure_synced(content) is not None)
            _mark_fresh()
            check("重扫判据：篇数一致时不重扫（`!=` 不能被写成 `==`）",
                  ls.ensure_synced(content) is None)

            # #114 解析器版本判据
            _mark_fresh()
            ls.meta_set(META_PARSER, str(CARDS_PARSER_VERSION - 1))
            check("重扫判据：解析器版本落后 → 必须重扫（否则旧卡永不更新）",
                  ls.ensure_synced(content) is not None)
            _mark_fresh()   # 重扫会把 synced_at 写回 now，先归零才谈得上「版本一致 → 不重扫」
            check("重扫判据：版本一致时不重扫（`!=` 取反后这条会红）",
                  ls.ensure_synced(content) is None)

            # #106 `total == 0`：活跃卡被掏空时即使同步时刻很新也要重建
            _mark_fresh()
            ls.con.execute("UPDATE cards SET active=0")
            ls.con.commit()
            check("重扫判据：活跃卡为 0（库被掏空）→ 重扫",
                  ls.ensure_synced(content) is not None)

            # #119 `_candidate_files`：`not parts or parts[0] not in (baike, interview)` → `and`
            # → articles/projects 也会被抽卡（统计口径与"哪些域参与复习"全错）
            mk(content / "articles" / "css", "note.md",
               "---\ntitle: CSS 笔记\n---\n\n## 定义\n\n**一句话定义：** " + "定" * 20 + "\n")
            cands = sorted(r for _, r in ls._candidate_files(content))
            check("_candidate_files：只有 baike/interview 参与抽卡（其它域不入 coverage）",
                  cands and all(r.startswith(("baike/", "interview/")) for r in cands),
                  f"got {cands}")
            n_before = len(cands)
            check("_candidate_files：`_` 前缀目录不参与（不变量 2）",
                  all("_" not in r.split("/")[1:2] for r in cands), f"got {cands}")

            # #120 `content is None or not content.is_dir()` → `and`：语料目录不在时应报
            # CorpusEmpty，而不是继续往下走去 walk 一个不存在的路径
            try:
                ls.sync(content / "不存在")
                check("sync：语料目录不存在 → 抛 CorpusEmpty", False, "没抛错")
            except CorpusEmpty:
                check("sync：语料目录不存在 → 抛 CorpusEmpty（不静默扫空）", True)
            check("_candidate_files 仍按域过滤（新增非候选域后候选数不变）",
                  len(ls._candidate_files(content)) == n_before)

            # #110 `_tag_list` 的 `str(raw or "")` → `and`：任何非空 tags 都会被切成空列表
            check("_tag_list：逗号分隔正常拆开（`raw or \"\"` 改成 `and` 后这里会变空列表）",
                  _tag_list("AI,Agent") == ["AI", "Agent"], f"got {_tag_list('AI,Agent')}")
            check("_tag_list：None / 空串 → 空列表（不抛、不产出 \"None\"）",
                  _tag_list(None) == [] and _tag_list("") == [], f"got {_tag_list(None)!r}")

            # #109 `_note_if_locked` 的 `or`→`and`：只有「locked 且 busy」才留痕 →
            # 真撞锁时日志里什么都没有，事后查不到是谁卡死了写锁
            recs: list = []
            h = _logging.Handler()
            h.emit = lambda rec: recs.append(rec.getMessage())  # type: ignore[method-assign]
            log = sys.modules["app.learn"]._LOG
            log.addHandler(h)
            try:
                _note_if_locked("写卡片库", _sq.OperationalError("database is locked"))
                _note_if_locked("写复习状态", _sq.OperationalError("database table is busy"))
            finally:
                log.removeHandler(h)
            check("_note_if_locked：locked 与 busy 两种措辞都要留痕（or 不是 and）",
                  len(recs) == 2 and "写卡片库" in recs[0] and "写复习状态" in recs[1],
                  f"got {recs}")
        finally:
            ls.close()


def test_learn_meta_roundtrip() -> None:
    """#107 `meta_get` 的 `row[0] if row else None`：读不存在的键必须给 None 而不是崩。"""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        content = root / "content"
        (content / "baike" / "algorithms").mkdir(parents=True)
        mk(content / "baike" / "algorithms", "a.md", _baike_md("甲"))
        ls = LearnStore(root / "indexes", content)
        try:
            ls.ensure_synced(content)
            check("meta_get：写进去的键能原样读回",
                  ls.meta_get(META_FILE_COUNT) == str(len(ls._candidate_files(content))),
                  f"got {ls.meta_get(META_FILE_COUNT)!r}")
            check("meta_get：不存在的键 → None（不是 IndexError / 空串）",
                  ls.meta_get("没这个键") is None)
        finally:
            ls.close()


# ---------------------------------------------------------------- cards：抽卡切块的边界
def test_cards_boundaries() -> None:
    """`_MIN_DEF_LEN` / 误区条目长度 / 12 行上限 / 停止标记 / 列表项开关 / 标题级别。"""
    # #133 `len(def_val) < _MIN_DEF_LEN` → `<=`：恰好达标的定义被判"太短"→ 整篇不成卡
    ok = parse_file("baike/algorithms/kmp.md", _baike_md("KMP 算法", _MIN_DEF_LEN))
    short = parse_file("baike/algorithms/kmp.md", _baike_md("KMP 算法", _MIN_DEF_LEN - 1))
    check(f"定义恰好 {_MIN_DEF_LEN} 字 → 成卡（边界含等号在「够长」这一侧）",
          any(c.kind == "baike_def" for c in ok), f"got {[c.kind for c in ok]}")
    check(f"定义 {_MIN_DEF_LEN - 1} 字 → 缺定义不成卡",
          not any(c.kind == "baike_def" for c in short), f"got {[c.kind for c in short]}")

    # #134 `len(item) < 4` → `<=`：恰好 4 字的误区条目被丢掉
    kinds = [(c.kind, c.front) for c in parse_file(
        "baike/algorithms/kmp.md", _baike_md("KMP 算法", 20, ["四字误区", "三字错"]))]
    traps = [f for k, f in kinds if k == "baike_trap"]
    check("误区条目恰好 4 字 → 收；3 字 → 丢（边界在 4 这一侧）",
          len(traps) == 1 and "四字误区" in traps[0], f"got {traps}")

    # #122 `_next_heading_at_most` 的 `<= level` → `<`：`###` 块不再止于下一个 `###`，
    # 而是连同下一题一起吃进上一题的答案（抽卡把两题并成一题）
    body = "### Q1\n正文\n#### 子标题\n还是正文\n### Q2\n尾巴\n"
    cut = _next_heading_at_most(body, 7, 3)
    check("I-4 切块：`###` 止于下一个 `###`，而 `####` 属于答案内部不截断",
          body[cut:].startswith("### Q2"), f"cut={cut} got {body[cut:cut + 8]!r}")

    # #123 `len(out) >= 12` → `>`：第 13 行也被收走（答案无限膨胀）
    got = _collect_following([f"第{i}行" for i in range(20)], 0)
    check("答案采集封顶 12 行（`>= 12` 不能写成 `> 12`）",
          len(got.split(" ")) == 12, f"got {len(got.split(' '))}")

    # #127 停止标记 `or` → `and`：要四种前缀同时命中才停 → 标题/围栏/表格被当成答案正文
    check("采集遇标题即止（不是四种标记全命中才止）",
          _collect_following(["正文一", "# 下一节", "正文二"], 0) == "正文一")
    check("采集遇表格即止",
          _collect_following(["正文一", "| 列 | 列 |", "正文二"], 0) == "正文一")
    check("采集遇代码围栏即止",
          _collect_following(["正文一", "```py", "正文二"], 0) == "正文一")

    # #130 `not allow_bullets` → `allow_bullets`：开关整个反向
    check("allow_bullets=False 时列表项截断采集",
          _collect_following(["甲", "- 子项"], 0) == "甲")
    check("allow_bullets=True 时列表项并入答案",
          _collect_following(["甲", "- 子项"], 0, allow_bullets=True) == "甲 - 子项")

    check("CARDS_PARSER_VERSION 是整数且 ≥ 2（I-4 属破坏性解析变更）",
          isinstance(CARDS_PARSER_VERSION, int) and CARDS_PARSER_VERSION >= 2,
          f"got {CARDS_PARSER_VERSION}")
    check("同一篇语料两次解析结果一致（card_id 稳定，重扫不产生重复卡）",
          [c.card_id for c in parse_file("baike/algorithms/kmp.md",
                                         _baike_md("KMP 算法", 20, ["误区一二三四五"]))]
          == [c.card_id for c in parse_file("baike/algorithms/kmp.md",
                                            _baike_md("KMP 算法", 20, ["误区一二三四五"]))])


# ---------------------------------------------------------------- rag：切块与分词的纯函数边界
def test_rag_pure_helpers() -> None:
    """`_is_cjk` 的码点区间边界与 `_merge_short` 的「前块无标题才补标题」判据。

    这两处是纯函数，不需要模型也不触网；P6 实测 #144/#146/#147 三条变异全存活。
    `OnnxEmbedder.__init__` / `download_model` 的存活体不在这里补——那要真模型或真网络，
    属"本机跑不到"，台账里单列。
    """
    try:
        from app.rag import CHUNK_MIN_CHARS, HFTokenizer, _merge_short
    except Exception as e:                                     # numpy/tokenizers 缺失
        print(f"  SKIP rag 纯函数断言（依赖不可用：{e}）")
        return
    is_cjk = HFTokenizer._is_cjk
    lo, hi = chr(0x4E00), chr(0x9FFF)
    check("_is_cjk：CJK 主区间两端点都算汉字（`<=` 改成 `<` 就各漏一个）",
          is_cjk(lo) and is_cjk(hi))
    check("_is_cjk：区间外一个都不算（不能把 ASCII / 假名当汉字）",
          not is_cjk("a") and not is_cjk("0") and not is_cjk(chr(0x304F)))
    check("_is_cjk：扩展 A 区起点也算汉字（多区间不能只测第一个）",
          is_cjk(chr(0x3400)) and not is_cjk(chr(0x33FF - 1)))

    long_txt = "正文" * CHUNK_MIN_CHARS
    a = {"heading": "第一节", "text": long_txt}
    b = {"heading": "第二节", "text": long_txt}
    check("_merge_short：两个都够长的块各自独立（不吞并、不覆盖标题）",
          [c["heading"] for c in _merge_short([dict(a), dict(b)])] == ["第一节", "第二节"])

    short = {"heading": "补位标题", "text": "太短"}
    filled = _merge_short([{"heading": "", "text": long_txt}, dict(short)])
    check("_merge_short：前块无标题时用后块标题补位",
          len(filled) == 1 and filled[0]["heading"] == "补位标题", f"got {filled}")
    kept = _merge_short([dict(a), dict(short)])
    check("_merge_short：前块已有标题则保留原标题（`not prev[heading]` 不能反）",
          len(kept) == 1 and kept[0]["heading"] == "第一节", f"got {kept}")


def main() -> int:
    print("== store：解码与 frontmatter 手术 ==")
    test_decode_and_frontmatter()
    print("== store：缓存判据 ==")
    test_caches_respond_to_mtime()
    print("== store：收件箱忽略 ==")
    test_inbox_ignore()
    print("== store：收件箱计数 TTL ==")
    test_inbox_count_ttl()
    print("== store：可见文档口径 ==")
    test_md_files_excludes_sidecars()
    print("== store：Obsidian 接入判定 ==")
    test_obsidian_vault_connected()
    print("== fts：双链解析 ==")
    test_wikilink_resolution()
    print("== fts：索引新鲜度边界 ==")
    test_index_is_stale_boundary()
    print("== fts：命中片段 wiki 别名 ==")
    test_snippet_wiki_alias()
    print("== learn：卡片库重扫判据 ==")
    test_ensure_synced_criteria()
    print("== learn：meta_get 读写 ==")
    test_learn_meta_roundtrip()
    print("== rag：切块与分词纯函数 ==")
    test_rag_pure_helpers()
    print("== cards：抽卡切块边界 ==")
    test_cards_boundaries()
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
