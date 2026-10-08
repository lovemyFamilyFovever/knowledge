# -*- coding: utf-8 -*-
"""知库**判定谓词层** smoke tests —— 专测"一个布尔/边界判错就静默坏掉"的那类逻辑。

运行：python tests/test_predicates.py

来历：P6 变异测试（覆盖台账 §10）把这层的断言空白量化了出来——`app/store.py` 与 `app/fts.py`
的判定性变异各 13 条存活，存活原因几乎全是「那行判定 8 套 smoke 一次都没执行到」。
本文件按那 26 条存活体逐条回填（台账 §10.10），每条断言都注明它焊住哪个变异（文件:行 + 算子 +
变异体编号），复跑命令见 §10.10 末。

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

from app import store  # noqa: E402
from app.fts import (_clean_snippet, build_index, index_is_stale, open_db,  # noqa: E402
                     resolve_maps_from_db, resolve_wikilink)
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
            # 于是调用方各自补了一张别名表来绕开它（重复实现 + 口径分叉）。
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


def test_rag_cfg_and_stream() -> None:
    """轮次 10：把 `tokenizer.json` 的解析与下载写盘拆成纯函数后，两条原先杀不掉的判据可测了。

    - #135 `nrm.get("type") == "BertNormalizer"`：真模型那份恰好 `lowercase=false`，
      所以"取反"在真数据上分不出来；现在用假 cfg 各测一次。
    - #139 `cls_id is None or sep_id is None`：真 vocab 两个都在位；现在缺一个就必须抛。
    - #140 `if not block: break`：真下载才会走到；现在喂假 resp 即可，**不联网**。
    """
    try:
        from app.rag import drain_stream, parse_tokenizer_json
    except Exception as e:                                     # numpy 缺失
        print(f"  SKIP rag 配置/写盘断言（依赖不可用：{e}）")
        return
    vocab = {"[UNK]": 0, "[CLS]": 1, "[SEP]": 2, "他": 3}
    ok = {"model": {"type": "WordPiece", "vocab": vocab},
          "normalizer": {"type": "BertNormalizer", "lowercase": True}}
    cfg = parse_tokenizer_json(ok)
    check("parse_tokenizer_json：BertNormalizer 的 lowercase=true 会被忠实读取",
          cfg["lowercase"] is True and cfg["unk_id"] == 0 and cfg["cls_id"] == 1
          and cfg["sep_id"] == 2, f"got {cfg}")
    check("parse_tokenizer_json：缺省项按文档默认（cont=## / clean_text / handle_chinese）",
          cfg["cont"] == "##" and cfg["clean_text"] is True
          and cfg["handle_chinese_chars"] is True
          and cfg["max_input_chars_per_word"] == 100, f"got {cfg}")
    not_bert = {"model": ok["model"], "normalizer": {"type": "Sequence", "lowercase": True}}
    check("parse_tokenizer_json：非 BertNormalizer 时 lowercase 必须为 False（== 判据不能反）",
          parse_tokenizer_json(not_bert)["lowercase"] is False)
    check("parse_tokenizer_json：BertNormalizer 但没写 lowercase → False（不能默认成要小写）",
          parse_tokenizer_json({"model": ok["model"],
                                "normalizer": {"type": "BertNormalizer"}})["lowercase"] is False)
    for name, bad in (("BPE 模型", {"model": {"type": "BPE", "vocab": vocab}}),
                      ("缺 [CLS]", {"model": {"type": "WordPiece",
                                              "vocab": {"[UNK]": 0, "[SEP]": 2}}}),
                      ("缺 [SEP]", {"model": {"type": "WordPiece",
                                              "vocab": {"[UNK]": 0, "[CLS]": 1}}})):
        try:
            parse_tokenizer_json(bad)
            check(f"parse_tokenizer_json：{name} → 抛 ValueError", False, "没抛错")
        except ValueError:
            check(f"parse_tokenizer_json：{name} → 抛 ValueError（不是 KeyError）", True)

    class _Resp:
        def __init__(self, chunks):
            self._c = list(chunks)

        def read(self, _n):
            return self._c.pop(0) if self._c else b""

    # ---- added_tokens：正文里的 [CLS] 是一个整 token，不是三个碎片（轮次 49 交叉验证抓出来的）
    with tempfile.TemporaryDirectory() as td:
        fake = {
            "model": {"type": "WordPiece", "unk_token": "[UNK]",
                      "max_input_chars_per_word": 100,
                      "continuing_subword_prefix": "##",
                      "vocab": {"[PAD]": 0, "[UNK]": 1, "[CLS]": 2, "[SEP]": 3, "[MASK]": 4,
                                "用": 10, "与": 11, "[": 12, "]": 13, "un": 14, "##known": 15}},
            "normalizer": {"type": "BertNormalizer", "clean_text": True,
                           "handle_chinese_chars": True, "lowercase": False},
            "pre_tokenizer": {"type": "BertPreTokenizer"},
            "added_tokens": [
                {"id": 0, "content": "[PAD]", "special": True},
                {"id": 1, "content": "[UNK]", "special": True},
                {"id": 2, "content": "[CLS]", "special": True},
                {"id": 3, "content": "[SEP]", "special": True},
                {"id": 4, "content": "[MASK]", "special": True},
                {"id": 9, "content": "[不在词表]", "special": True},
            ],
        }
        p = Path(td) / "tokenizer.json"
        p.write_text(json.dumps(fake, ensure_ascii=False), encoding="utf-8")
        cfg2 = parse_tokenizer_json(fake)
        check("parse_tokenizer_json：added_tokens 里 special=True 且在词表里的才进 special_tokens（长的排前面）",
              {n for n, _ in cfg2["special_tokens"]} == {"[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"}
              and all(len(a) >= len(b) for a, b in zip(cfg2["special_tokens"],
                                                       cfg2["special_tokens"][1:])),
              cfg2["special_tokens"])
        from app.rag import HFTokenizer
        tok = HFTokenizer(p)
        got = tok.encode("用[CLS]与")
        check("HFTokenizer：正文里的 [CLS] 落成一个整 token（不再被拆成 [ + [UNK] + ]）",
              got == [2, 10, 2, 11, 3], f"got {got}")
        check("HFTokenizer：special 只吃字面量，普通词照旧走 WordPiece 贪心最长匹配（un + ##known）",
              tok.encode("unknown 与") == [2, 14, 15, 11, 3], f"got {tok.encode('unknown 与')}")
        plain = {"model": fake["model"], "normalizer": fake["normalizer"],
                 "pre_tokenizer": fake["pre_tokenizer"]}
        p2 = Path(td) / "no_added.json"
        p2.write_text(json.dumps(plain, ensure_ascii=False), encoding="utf-8")
        check("HFTokenizer：没有 added_tokens 的 json 退化成整段处理（不许因为新分支崩掉）",
              HFTokenizer(p2).encode("用与") == [2, 10, 11, 3],
              f"got {HFTokenizer(p2).encode('用与')}")

    with tempfile.TemporaryDirectory() as td:
        dest = Path(td) / "part.bin"
        n = drain_stream(_Resp([b"abc", b"de"]), dest)
        check("drain_stream：分块写全并返回总长（读到空块才停）",
              n == 5 and dest.read_bytes() == b"abcde", f"got {n}")
        empty = Path(td) / "empty.bin"
        check("drain_stream：首块即空 → 写 0 字节而不是死循环",
              drain_stream(_Resp([]), empty) == 0 and empty.read_bytes() == b"",
              f"got {empty.read_bytes()!r}")
        parts = Path(td) / "big.bin"
        blob = bytes(bytearray(range(256))) * 700          # >64KB，跨多个读块
        n2 = drain_stream(_Resp([blob[i:i + 30000] for i in range(0, len(blob), 30000)]), parts)
        check("drain_stream：跨多块拼接后字节完全一致（下载不被截断）",
              n2 == len(blob) and parts.read_bytes() == blob, f"got {n2}")



# ---------------------------------------------------------------- learn：卡片库重扫判据
def _baike_md(term: str, def_len: int = 20, traps=()) -> str:
    body = "".join(f"- {t}\n" for t in traps)
    tail = f"\n## 常见误区\n\n{body}" if traps else ""
    return (f'---\ntitle: "{term}"\n---\n\n# {term}\n\n## 定义\n\n'
            f"**一句话定义：** {'定' * def_len}\n{tail}")


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


# ---------------------------------------------------------------- rag：全量重建的「逐篇续跑」判据
def test_rag_resume_plan() -> None:
    """`plan_sync` / `stamp_legacy`：把"这次到底该重嵌哪些文件"从 sqlite 与模型里剥出来。

    来历（轮次 51）：`sync_rag` 的全量重建**没有中间态**——`meta.code_version` 只在函数
    最后一把提交，所以任何一次中途 kill 都把已嵌入的上千块全作废，下一趟自检仍判"版本不符"
    → 从第 0 块重来（台账 §6 第 93 行，实测一趟 38 分钟 / 22006 块）。改成逐篇盖章 `embed_ver`
    之后，判定必须**只看每篇自己的章**，不能再留一道"全局版本不符就全量"的闸门 ——
    同一规则两处实现，拆掉任一处另一处都兜得住，变异必存活（§6 第 87 行那条教训）。
    这几条不依赖 numpy 之外的东西，也不需要模型与 sqlite-vec。
    """
    try:
        from app import rag as _rag
    except Exception as e:                             # numpy / tokenizers 缺失
        print(f"  SKIP rag 续跑判据（依赖不可用：{e}）")
        return
    check("plan_sync 与 stamp_legacy 存在（判定剥出 sqlite，无模型也能测）",
          hasattr(_rag, "plan_sync") and hasattr(_rag, "stamp_legacy"))
    if not (hasattr(_rag, "plan_sync") and hasattr(_rag, "stamp_legacy")):
        return
    plan, V = _rag.plan_sync, "4"

    r = plan(known={}, current={"a.md": 1.0, "b.md": 1.0}, code_version=V,
             n_vec=0, sum_chunks=0)
    check("新库首建：两篇都要嵌，skipped 是 0（不是「全都被跳过」）",
          r["changed"] == ["a.md", "b.md"] and r["skipped"] == 0, f"got {r}")
    check("新库首建：reason 是 normal（索引还没内容，谈不上不完整）",
          r["reason"] == "normal", f"got {r['reason']}")

    known = {"a.md": (1.0, V), "b.md": (1.0, V)}
    r = plan(known=known, current={"a.md": 2.0, "b.md": 1.0}, code_version=V,
             n_vec=6, sum_chunks=6)
    check("mtime 变新：只重嵌那一篇，另一篇进 skipped",
          r["changed"] == ["a.md"] and r["skipped"] == 1, f"got {r}")

    r = plan(known={"a.md": (2.0, "3"), "b.md": (1.0, V)}, current={"a.md": 2.0, "b.md": 1.0},
             code_version=V, n_vec=6, sum_chunks=6)
    check("mtime 没变但章是旧版本 → 仍然重嵌它（版本递增就靠这一路生效）",
          r["changed"] == ["a.md"], f"got {r}")

    r = plan(known={"a.md": (1.0, "3"), "b.md": (1.0, "3"), "c.md": (1.0, "3")},
             current={"a.md": 1.0, "b.md": 1.0, "c.md": 1.0}, code_version=V,
             n_vec=9, sum_chunks=9)
    check("RAG_CODE_VERSION 递增 = 全量重算（不需要第二道全局闸门也照样全中）",
          len(r["changed"]) == 3 and r["skipped"] == 0, f"got {r}")

    half = {f"{i}.md": (1.0, V if i < 3 else None) for i in range(8)}
    r = plan(known=half, current={f"{i}.md": 1.0 for i in range(8)}, code_version=V,
             n_vec=6, sum_chunks=6)
    check("中断续跑：已盖章的 3 篇跳过、没章的 5 篇重嵌（省掉的就是这 5 篇之前的全部）",
          len(r["changed"]) == 5 and r["skipped"] == 3, f"got {r}")
    check("续跑时 skipped 是真数字（写成常量 0 的实现必须在这里红）",
          r["skipped"] == 3, f"got {r['skipped']}")

    r = plan(known={"a.md": (1.0, V), "b.md": (1.0, V)}, current={"a.md": 1.0, "b.md": 1.0},
             code_version=V, n_vec=10, sum_chunks=12)
    check("vec 行数与元数据不符：索引不可信 → 全部重算且 reason=integrity",
          len(r["changed"]) == 2 and r["reason"] == "integrity", f"got {r}")

    r = plan(known={"a.md": (1.0, V), "gone.md": (1.0, V)}, current={"a.md": 1.0},
             code_version=V, n_vec=3, sum_chunks=3)
    check("语料里被删掉的文件进 deleted（known 有、current 没有）",
          r["deleted"] == ["gone.md"], f"got {r}")
    check("deleted 的那篇不出现在 changed 里，也没进 skipped",
          "gone.md" not in r["changed"] and r["skipped"] == 1, f"got {r}")

    import inspect
    names = list(inspect.signature(plan).parameters)
    check("plan_sync 的参数里不许再有全局版本闸门（防「同一规则两处实现」复活）",
          not any("meta" in n for n in names), f"got {names}")

    check("stamp_legacy：meta 版本相符 + 行数一致 → 才给旧库盖章（免白嵌 22006 块）",
          _rag.stamp_legacy("4", V, 22006, 22006) is True)
    check("stamp_legacy：meta 版本不符 → 不盖章（来历不明就重嵌）",
          _rag.stamp_legacy("3", V, 22006, 22006) is False)
    check("stamp_legacy：行数与元数据不符 → 不盖章（and 写成 or 就在这里红）",
          _rag.stamp_legacy("4", V, 20000, 22006) is False)
    check("stamp_legacy：meta 里没有版本（全新库/被删过的派生缓存）→ 不盖章",
          _rag.stamp_legacy(None, V, 0, 0) is False)


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
    print("== rag：切块与分词纯函数 ==")
    test_rag_pure_helpers()
    print("== rag：全量重建的逐篇续跑判据 ==")
    test_rag_resume_plan()
    print("== rag：tokenizer 配置与写盘 ==")
    test_rag_cfg_and_stream()
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
