# -*- coding: utf-8 -*-
"""知库 **P3 · 性质测试**（零依赖）—— 测"对任意输入都成立"的断言，而不是几个手挑样例。

运行：python tests/test_properties.py

不用 hypothesis 的理由：本机没装，也不该为一套测试引入新依赖（AGENTS 的脚本风格 + 离线取向）。
这里是手搓的确定性性质测试器：**固定种子 → 反例可复现**（打印 seed + 样本序号），
每条性质跑 `N_EXAMPLES` 个样本；任何反例都必须补进文件末尾的 `PINNED` 固化区。

靶面按彻查手册 §P3-A 的历史 bug 密度排序，另加一条 P6 期间发现的"同一规则两份实现"一致性：

    ① `/raw` 路径校验（app.py::safe_rel）：任意恶意输入只能"落在 content/ 内"或"被明确拒绝"，不得 500
    ② frontmatter 解析 <-> 写回 round-trip：任意 title/tags/status 写进去读出来等价，正文零污染
    ③ taxonomy 子域改名：dry-run 不动盘；apply 后文件数守恒、无丢失
    ④ fts 双链与 CJK 空格：任意文本不抛异常；围栏/行内 code 里的 [[...]] 不算链接；cjk_clean 可逆
    ⑤ rag 切块：任意输入不崩、块长不越界、正文不丢字（缺依赖时整条 SKIP）
    ⑥ sm2 排程：任意评分序列不出现负数/NaN/越界，非法评分必须被拒
    ⑦ 一致性：`md_files()` 与 `is_visible_doc()` 两份独立实现对同一棵树必须给同一个答案

全程只读写 `tempfile.TemporaryDirectory()`，绝不碰真实 `content/`（AGENTS 不变量 1/4）。
"""
import random
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import itertools

from app import fts  # noqa: E402
from app.app import create_app  # noqa: E402
from app.fts import FENCE_RE, INLINE_CODE_RE
from app.sm2 import (EF_MAX, EF_MIN, MAX_INTERVAL, DEFAULT_STATE,  # noqa: E402
                     is_mastered, schedule)
from app.store import (dump_frontmatter, is_visible_doc, md_files,  # noqa: E402
                       parse_frontmatter, rename_sub)

SEED = 20260924
N = 240
passed = failed = skipped = 0
FOUNDS: list = []
BODY = "正文" + chr(10)   # 固化区复用，避免在源码里嵌换行字面量


# ---------------------------------------------------------------- 迷你性质测试器
def prop(name, gen, check):
    """gen(i) 造第 i 个样本；check(case) 返回 (bool, 说明)。只打印前 3 条反例但跑满 N 个。"""
    global passed, failed
    bad = []
    for i in range(N):
        case = gen(i)
        try:
            ok, why = check(case)
        except Exception as e:                                   # noqa: BLE001
            ok, why = False, f"抛异常 {type(e).__name__}: {e}"
        if not ok:
            bad.append((i, case, why))
            if len(bad) >= 3:
                break
    if bad:
        failed += 1
        print(f"  FAIL {name}")
        for i, case, why in bad:
            line = f"       反例 seed={SEED} idx={i} 输入={case!r} → {why}"
            print(line[:400])
            FOUNDS.append(line)
    else:
        passed += 1
        print(f"  PASS {name}（{N} 例全过）")


def skip(name, why):
    global skipped
    skipped += 1
    print(f"  SKIP {name}：{why}")


# ---------------------------------------------------------------- ① 路径校验（走真实路由）
def _app_on(temp_root):
    import logging
    logging.getLogger("app").setLevel(logging.CRITICAL)
    content = temp_root / "content"
    (content / "ai" / "llm").mkdir(parents=True)
    (content / "ai" / "llm" / "A.md").write_text("---\ntitle: A\n---\n\n正文\n", encoding="utf-8")
    (content / "_inbox").mkdir()
    (content / "_inbox" / "secret.md").write_text("收件箱草稿\n", encoding="utf-8")
    (content / "_trash").mkdir()
    (content / "_trash" / "gone.md").write_text("回收站\n", encoding="utf-8")
    (temp_root / "outside.md").write_text("仓库根之外\n", encoding="utf-8")
    return create_app(temp_root).test_client()


GEN_HOSTILE = {
    "空串": "", "仅斜杠": "/", "双斜杠": "//", "点": ".", "点点": "..",
    "点点斜杠": "../", "穿越到根": "../outside.md", "深层穿越": "ai/llm/../../outside.md",
    "编码穿越": "%2e%2e/outside.md", "混分隔符": "ai\\..\\outside.md",
    "绝对路径": "/etc/passwd", "盘符": "C:/Windows/win.ini", "NUL": "ai/llm/A.md\x00.png",
    "超长": "ai/llm/" + "x" * 300 + ".md", "空字节尾巴": "ai/llm/A.md ",
    "非白名单扩展": "ai/llm/A.exe", "无扩展": "ai/llm/A",
    "索引库": "../indexes/index.db", "源码": "../app/app.py",
    "_inbox 直取": "_inbox/secret.md", "_trash 直取": "_trash/gone.md",
    "正常文档": "ai/llm/A.md",
}


def test_path_validation():
    global passed, failed
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        try:
            c = _app_on(root)
        except Exception as e:                                    # noqa: BLE001
            skip("① 路径校验", f"临时实例起不来：{e}")
            return
        print("  —— 手挑样本全过 + 随机拼接样本")

        bad = []
        for label, rel in GEN_HOSTILE.items():
            r = c.get("/raw/" + rel.replace("%", "%25") if "%" in rel else rel)
            served = r.status_code == 200
            leaks = (b"outside.md" in r.data or "仓库根之外" in r.get_data(as_text=True)
                     or "回收站" in r.get_data(as_text=True))
            if r.status_code >= 500 or leaks:
                bad.append((label, rel, r.status_code,
                            "500" if r.status_code >= 500 else "内容泄露", served))
        if bad:
            failed += 1
            for b in bad[:3]:
                print(f"  FAIL ① 路径校验 手挑样本 {b[0]!r} rel={b[1]!r} → status={b[2]} {b[3]}")
                FOUNDS.append(f"① 路径校验 手挑样本 {b[0]!r} rel={b[1]!r}")
        else:
            passed += 1
            print(f"  PASS ① 路径校验 手挑 {len(GEN_HOSTILE)} 例（无 500、无越界内容泄露）")

        rng = random.Random(SEED)
        frags = ["..", ".", "%2e", "ai", "llm", "_trash", "_inbox", "", "x" * 20, "\\", "//"]
        bad2 = []
        for i in range(N):
            rel = "/".join(rng.choice(frags) for _ in range(rng.randint(1, 5)))
            r = c.get("/raw/" + rel)
            if r.status_code >= 500:
                bad2.append((i, rel, r.status_code))
                if len(bad2) >= 3:
                    break
            elif r.status_code == 200 and "仓库根之外" in r.get_data(as_text=True):
                bad2.append((i, rel, "200 但吐出了 content/ 之外的文件"))
                break
        if bad2:
            failed += 1
            for b in bad2[:3]:
                print(f"  FAIL ① 路径校验 随机样本 idx={b[0]} rel={b[1]!r} → {b[2]}")
                FOUNDS.append(f"① 路径校验 随机 idx={b[0]} rel={b[1]!r}")
        else:
            passed += 1
            print(f"  PASS ① 路径校验 随机拼接 {N} 例（无 500、无越界内容泄露）")


# ---------------------------------------------------------------- ② frontmatter round-trip
ATOMS = ['普通标题', 'a "b" c', "单引号 'x'", "含: 冒号", "含 # 井号", "[AI, Agent]", "[未闭合",
         "true", "False", "None", "\\", "路径\\name", "中文，全角：标点", "emoji \U0001f600",
         "前后  空格", "", "a" * 60, "- 列表项", "## 二级标题", "[[双链]]", "两个\n换行",
         "反斜杠结尾\\"]


def gen_fm(i):
    rng = random.Random(SEED + i * 104729)
    fm = {"title": rng.choice(ATOMS), "source": rng.choice(ATOMS), "status": rng.choice(ATOMS)}
    n_tags = rng.randint(0, 3)
    # 刻意排除空串元素：`tags: [a, ]` 是退化写法，解析端丢弃空项是**有意的清洗**
    # （真语料里空标签会被治理脚本清掉），把它放进随机空间只会制造假反例。
    atoms = [a for a in ATOMS if a]
    fm["tags"] = [rng.choice(atoms) for _ in range(n_tags)]
    if rng.random() < .5:
        fm["favorite"] = rng.choice([True, False])
    body = rng.choice(["正文。\n", "# H\n\n内容\n", "带 --- 的正文\n---\n再来一段\n", "",
                       "引用 > [[链接]] 与 `code`\n"])
    return fm, body


def check_fm(case):
    fm, body = case
    text = dump_frontmatter(fm, body)
    got, got_body = parse_frontmatter(text)
    # 只对「写得出、也读得回」的键要求等价：值里带换行的本来就写不进单行 fm（写回时会破坏结构）
    def lossy(v):
        return isinstance(v, str) and "\n" in v
    for k, want in fm.items():
        if lossy(want) or (isinstance(want, list) and any(lossy(x) for x in want)):
            continue
        have = got.get(k)
        if isinstance(want, str) and want.lower() in ("true", "false", "none"):
            # 写回会加引号 → 读回应仍是字符串；若被转成 bool/None 就是污染
            if not isinstance(have, str):
                return False, f"{k}={want!r} 被解析成 {type(have).__name__} {have!r}"
        if isinstance(want, list) and want and any(x.startswith("[") for x in want):
            continue                                            # 值本身像列表，扁平语法无法无损表达
        if have != want:
            return False, f"{k} 期望 {want!r} 实得 {have!r}（序列化串 {text!r}）"
    if got_body != body:
        return False, f"正文被改动：期望 {body!r} 实得 {got_body!r}"
    if text.count("---") < 2:
        return False, f"frontmatter 边界丢失：{text!r}"
    return True, ""


# ---------------------------------------------------------------- ③ taxonomy 改名守恒
def gen_rename(i):
    rng = random.Random(SEED + i * 15485863)
    n_docs = rng.randint(0, 6)
    names = [f"doc{k}" for k in range(n_docs)]
    side = rng.random() < .4
    new_sub = rng.choice(["新子域", "renamed", "a-b_c", "含 空格", "_leading", "with/slash",
                          "", "老"])
    return names, side, new_sub


def check_rename(case):
    names, with_side, new_sub = case
    with tempfile.TemporaryDirectory() as td:
        content = Path(td) / "content"
        src = content / "ai" / "old"
        src.mkdir(parents=True)
        for n in names:
            (src / f"{n}.md").write_text(f"---\ntitle: {n}\n---\n\n{n} 正文\n", encoding="utf-8")
        if with_side:
            (src / "doc0.notes.md").write_text("备注\n", encoding="utf-8")
        (content / "_meta").mkdir()
        (content / "_meta" / "taxonomy.json").write_text('{"domains": {"ai": {"label": "AI"}}}',
                                                         encoding="utf-8")
        before = sorted(p.relative_to(content).as_posix() for p in content.rglob("*") if p.is_file())
        try:
            plan = rename_sub(content, "ai", "old", new_sub, apply=False)
        except ValueError:
            return True, ""                                     # 非法名被拒 = 正确行为
        except Exception as e:                                    # noqa: BLE001
            return False, f"dry-run 抛 {type(e).__name__}: {e}"
        after_dry = sorted(p.relative_to(content).as_posix() for p in content.rglob("*") if p.is_file())
        if after_dry != before:
            return False, f"dry-run 竟然动了盘：{before} -> {after_dry}"
        if not isinstance(plan, dict):
            return False, f"dry-run 返回不是 dict：{plan!r}"
        try:
            rename_sub(content, "ai", "old", new_sub, apply=True)
        except Exception as e:                                    # noqa: BLE001
            return False, f"apply 抛 {type(e).__name__}: {e}"
        md_now = sorted(p for _, p in md_files(content))
        n_md_before = len([x for x in before if x.endswith(".md") and not x.endswith(".notes.md")])
        if len(md_now) != n_md_before:
            return False, f"改名前后正式篇数不守恒：{n_md_before} -> {len(md_now)}（{md_now}）"
        if (content / "ai" / "old").exists():
            return False, "源目录还在（改名没搬完）"
        for _, rel in md_files(content):
            if not is_visible_doc(rel):
                return False, f"改名后产出了不可见文档 {rel}"
    return True, ""


# ---------------------------------------------------------------- ④ 双链提取 / CJK 可逆
def gen_links(i):
    rng = random.Random(SEED + i * 40503)
    targets = ["目标", "带 空格", "路径/a", "别名|x", "锚点#s", "空", "]" * rng.randint(1, 3),
               "[", "换\n行", "" * 1]
    parts = []
    seen = itertools.count()
    for _ in range(rng.randint(0, 4)):
        t = rng.choice(targets) + str(next(seen))          # 唯一化：避免"外面也出现同一目标"干扰
        style = rng.random()
        if style < .35:
            parts.append(f"文本 [[{t}]] 尾巴")
        elif style < .55:
            parts.append(f"行内 `[[{t}]]` 不算")
        elif style < .75:
            parts.append("```\n" + f"围栏里 [[{t}]]\n" + "```")
        elif style < .9:
            parts.append(f"图片 ![[{t}]]")
        else:
            parts.append(f"未闭合 [[{t}")
    return "\n\n".join(parts)


def check_links(case):
    try:
        got = fts.extract_wikilinks(case)
    except Exception as e:                                        # noqa: BLE001
        return False, f"抛 {type(e).__name__}: {e}"
    if not isinstance(got, list) or any(not isinstance(x, str) for x in got):
        return False, f"返回不是 str 列表：{got!r}"
    if "```" in case:                                            # 围栏里的链接必须不被算进去
        fence = case.split("```")[1] if case.count("```") >= 2 else ""
        for x in got:
            if x in fence and f"[[{x}]]" in fence:
                return False, f"围栏内的 [[{x}]] 被当成链接（{got!r}）"
    # 只要求"被算进去的链接都能在去掉围栏后的文本里找到 [[目标]]"，
    # 并且围栏/行内独占的那个目标一定不在结果里（唯一化后才能这样判）
    outside = INLINE_CODE_RE.sub("", FENCE_RE.sub("", case))
    for x in got:
        # 提取出的目标已被剥掉 #锚点 / |别名，因此原文里能匹配上的形态有 [[x]] / [[x#..]] / [[x|..]]
        if f"[[{x}]]" not in outside and f"[[{x}#" not in outside and f"[[{x}|" not in outside:
            return False, f"链接 {x!r} 只存在于 code 区域内，却被提取了（结果 {got}）"
    return True, ""


def gen_cjk(i):
    rng = random.Random(SEED + i * 7)
    pool = ["中", "文", "a", "1", " ", "，", "\n", "\U0001f600", "日", "本", "语"]
    return "".join(rng.choice(pool) for _ in range(rng.randint(0, 40)))


def check_cjk(case):
    """索引侧加空格、展示侧去空格，这两步的正确契约是：

    ① 不吞不造非空白字符（去掉所有空格后两边必须一模一样）；
    ② 稳定（再走一遍 clean 复合 space 不变）——否则标题会被改出"抖动的空格"。
    注意 `clean(space(s)) == s` **并不成立**（空格只夹在 CJK 与非 CJK 之间，
    原串里 CJK 紧跟 emoji 时那个空格不会消失），所以不能按字面可逆去断言。
    """
    try:
        spaced = fts.cjk_space(case)
        back = fts.cjk_clean(spaced)
    except Exception as e:                                        # noqa: BLE001
        return False, f"抛 {type(e).__name__}: {e}"
    nospace = lambda t: "".join(t.split())                        # noqa: E731
    if nospace(back) != nospace(case):
        return False, f"字符被吞掉或多出：{case!r} -> {spaced!r} -> {back!r}"
    again = fts.cjk_clean(fts.cjk_space(back))
    if nospace(again) != nospace(back):
        return False, f"二次处理不稳定：{back!r} -> {again!r}"
    return True, ""


# ---------------------------------------------------------------- ⑤ rag 切块
def gen_md(i):
    rng = random.Random(SEED + i * 31)
    parts = []
    for _ in range(rng.randint(0, 6)):
        h = rng.choice(["# ", "## ", "### ", ""])
        parts.append(h + "标题" + "\n\n" + "内容。" * rng.randint(0, 150) + "\n")
        if rng.random() < .3:
            parts.append("```\n代码 " + "x" * rng.randint(0, 900) + "\n```\n")
    return "".join(parts)


def check_md_split(case):
    from app.rag import CHUNK_MAX_CHARS, markdown_split
    try:
        chunks = markdown_split(case)
    except Exception as e:                                        # noqa: BLE001
        return False, f"抛 {type(e).__name__}: {e}"
    if not isinstance(chunks, list):
        return False, f"返回不是 list：{type(chunks).__name__}"
    for c in chunks:
        if not isinstance(c, dict) or "text" not in c:
            return False, f"块结构不对：{c!r}"
        if not c["text"].strip():
            return False, "产出空块（检索时会命中到空文本）"
        if len(c["text"]) > CHUNK_MAX_CHARS + 400:
            return False, f"块长 {len(c['text'])} 超上限 {CHUNK_MAX_CHARS} 太多"
    # 纯标题（没有任何正文）零块是设计如此：没内容可检索，硬凑一块会污染命中
    has_body = any(ln.strip() and not ln.lstrip().startswith(("#", "```", "~~~"))
                   for ln in case.splitlines())
    if has_body and not chunks:
        return False, f"有正文却零块：{case[:40]!r}"
    return True, ""


# ---------------------------------------------------------------- ⑥ sm2 排程
def gen_qseq(i):
    rng = random.Random(SEED + i * 65537)
    n = rng.randint(1, 12)
    seq = []
    for _ in range(n):
        r = rng.random()
        if r < .82:
            seq.append(rng.randint(0, 5))
        elif r < .88:
            seq.append(rng.choice([-1, 6, 99, -100]))
        elif r < .94:
            seq.append(rng.choice(["4", None, 3.0, True, False, [], {}]))
        else:
            seq.append(rng.randint(0, 5))
    return seq


def check_schedule(case):
    sch = schedule
    st = dict(DEFAULT_STATE)
    now = 1727000000.0
    for k, q in enumerate(case):
        try:
            nxt = sch(st, q, now)
        except ValueError:
            if isinstance(q, int) and not isinstance(q, bool) and 0 <= q <= 5:
                return False, f"合法评分 {q!r} 被拒（第 {k} 步）"
            continue
        except Exception as e:                                    # noqa: BLE001
            return False, f"非法评分 {q!r} 抛的不是 ValueError：{type(e).__name__}: {e}"
        iv, reps, lapses, ef = nxt["interval"], nxt["reps"], nxt["lapses"], nxt["ef"]
        if not isinstance(iv, int) or iv < 1:
            return False, f"q={q!r} 后 interval={iv!r}（必须是 ≥1 的整数）"
        if iv > MAX_INTERVAL:
            return False, f"q={q!r} 后 interval={iv} 超上限 {MAX_INTERVAL}"
        if not isinstance(reps, int) or reps < 0 or not isinstance(lapses, int) or lapses < 0:
            return False, f"q={q!r} 后 reps/lapses={reps}/{lapses}"
        if not (EF_MIN <= ef <= EF_MAX) or ef != ef:
            return False, f"q={q!r} 后 ef={ef!r} 越界或 NaN"
        if nxt["due_ts"] < now - 86400 * 2:
            return False, f"q={q!r} 后 due_ts={nxt['due_ts']} 早于今天"
        if not isinstance(nxt["mastered"], int) or nxt["mastered"] not in (0, 1):
            return False, f"mastered 非 0/1：{nxt['mastered']!r}"
        if nxt["mastered"] != is_mastered(nxt):
            return False, f"mastered 与 is_mastered 分叉：{nxt}"
        st = {kk: nxt[kk] for kk in ("ef", "interval", "reps", "lapses")}
    return True, ""



# ---------------------------------------------------------------- ⑦ 两份实现一致性
def gen_tree(i):
    rng = random.Random(SEED + i * 2654435761)
    segs = ["ai", "baike", "projects", "_meta", "_trash", "_inbox", "sub", "x y", "中文域"]
    files = []
    for _ in range(rng.randint(1, 8)):
        depth = rng.randint(1, 3)
        parts = [_pick(rng, segs) for _ in range(depth)]
        name = _pick(rng, ["A", "B.notes", "C.notes", "D", "E.notes"]) + ".md"
        files.append("/".join(parts + [name]))
    return files


def _pick(rng, seq):
    return rng.choice(seq)


def check_consistency(case):
    with tempfile.TemporaryDirectory() as td:
        content = Path(td) / "content"
        for rel in case:
            p = content / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("---\ntitle: t\n---\n\n正文\n", encoding="utf-8")
        got = sorted(r for _, r in md_files(content))
        want = sorted({r for r in case if is_visible_doc(r) and (content / r).is_file()})
        if got != want:
            return False, f"两份实现答案不同：md_files={got} vs is_visible_doc={want}（输入 {case}）"
    return True, ""


# ---------------------------------------------------------------- 固化区（反例必须留在这）
PINNED = [
    # (性质, 反例输入, 期望) —— P3 首轮跑出的真反例，修完之后也必须留在这里（手册 §P3 通过标准）
    ("② frontmatter 撇号往返",
     ({"source": "单引号 'x'", "title": "Bob's"}, BODY),
     lambda c: parse_frontmatter(dump_frontmatter(*c))[0] == c[0]),
    ("② frontmatter 列表项撇号",
     ({"tags": ["含'撇号", 'b"']}, BODY),
     lambda c: all(x in parse_frontmatter(dump_frontmatter(*c))[0]["tags"]
                   for x in c[0]["tags"])),
    ("① 路径校验：合法但文件不存在 → 404 不是 500",
     "ai/llm/nope.md",
     lambda rel: _client404().get("/raw/" + rel).status_code == 404),
    ("① 路径校验：.. 绕回 content 内的不存在路径 → 404",
     "ai/llm/../../outside.md",
     lambda rel: _client404().get("/raw/" + rel).status_code == 404),
]

_CLIENT = {}


def _client404():
    """给固化区复用一个临时实例（避免每条反例都起一次 app）。"""
    if "c" not in _CLIENT:
        td = tempfile.mkdtemp()
        root = Path(td)
        (root / "content" / "ai" / "llm").mkdir(parents=True)
        (root / "content" / "ai" / "llm" / "A.md").write_text("x", encoding="utf-8")
        _CLIENT["c"] = create_app(root).test_client()
    return _CLIENT["c"]


def test_pinned():
    global passed, failed
    for name, case, expect in PINNED:
        ok = expect(case)
        if ok:
            passed += 1
            print(f"  PASS 固化：{name} {case!r}")
        else:
            failed += 1
            print(f"  FAIL 固化：{name} {case!r}")


def main():
    print("== ① /raw 路径校验（真实路由 + 随机拼接） ==")
    test_path_validation()
    print("== ② frontmatter 写回 <-> 解析 round-trip ==")
    prop("② frontmatter round-trip", gen_fm, check_fm)
    print("== ③ taxonomy 子域改名守恒 ==")
    prop("③ rename_sub dry-run/apply 守恒", gen_rename, check_rename)
    print("== ④ 双链提取与 CJK 空格可逆 ==")
    prop("④a extract_wikilinks 不抛且忽略 code", gen_links, check_links)
    prop("④b cjk_clean(cjk_space(s)) == s", gen_cjk, check_cjk)
    print("== ⑤ rag 切块 ==")
    try:
        import app.rag  # noqa: F401
        prop("⑤ markdown_split 不崩不越界不丢块", gen_md, check_md_split)
    except Exception as e:                                        # noqa: BLE001
        skip("⑤ rag 切块", f"依赖不可用：{e}")
    print("== ⑥ sm2 排程 ==")
    prop("⑥ schedule 任意评分序列的不变量", gen_qseq, check_schedule)
    print("== ⑦ md_files 与 is_visible_doc 一致性 ==")
    prop("⑦ 两份实现同答案", gen_tree, check_consistency)
    print("== ⑧ 已固化反例 ==")
    test_pinned()
    print(f"\n{passed} 条性质通过 / {failed} 条失败 / {skipped} 条跳过；"
          f"每条 {N} 个样本，种子 {SEED}")
    if FOUNDS:
        print("\n反例（把它们加进 PINNED 固化区再修）：")
        for line in FOUNDS:
            print("  " + line[:300])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
