# -*- coding: utf-8 -*-
"""复习抽卡器 —— 把 content/ 下的 Markdown 语料解析成复习卡片（**纯函数**）。

设计约束（AGENTS.md 不变量）：
    ① content/ 是唯一事实源：本模块只读 MD 文本，一个字节都不写；
    ② 复习状态禁止写进 frontmatter → 全部落在 indexes/reading.db（见 app/learn.py）；
    ③ _ 前缀目录（_inbox/_trash/_meta/_unfiled）不扫描 —— 调用方 LearnStore.sync
       用 store.md_files 迭代，该迭代器已在源头跳过，此处不再重复判断。

本模块零 IO（除 import app.store 的 frontmatter 解析）、零 Flask 依赖，
parse_file(rel, raw) 是纯函数：同样输入永远得到同样输出，便于单测与重放。

卡片 ID 只由 (kind, term, front) 决定，**不含路径**：文件改名/移动后复习进度不丢，
这是刻意为之（用户整理语料是常态，进度是长期资产）。

支持的语料形态（均已在真实语料上逐份勘察确认）：
    baike A  单术语词条：## 定义 + **一句话定义：** / ## 常见误区 / ## 相关术语
    baike B  多词条汇篇：## <术语> 下挂 **一句话定义（大白话）** 小节（一文件 8~20 词条）
    baike C  教程长文：既无 ## 定义 又无粗体小节 → 整篇不抽卡（记 coverage.skipped）
    interview I-1  章节题目式：`### 题目N：xxx` + **题目描述：** / **思路分析：**
    interview I-2  表格清单式：`| 1 | 题面 | 中级 |`（全篇只有题面没有答案）
    interview I-3  扁平纯文本式：`1. 题面？` … `查看答案` … 答案正文
"""
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Sequence

from app.store import parse_frontmatter

# 抽卡解析器的版本。改动解析规则必须 +1 —— LearnStore.ensure_synced 依据它触发全量重建。
CARDS_PARSER_VERSION = 1

# 只有这两个域会产出卡片；其余域（articles/projects/career/…）不抽。
CARD_DOMAINS: tuple[str, ...] = ("baike", "interview")

KIND_BAIKE_DEF = "baike_def"
KIND_BAIKE_TRAP = "baike_trap"
KIND_INTERVIEW_QA = "interview_qa"
VALID_KINDS: tuple[str, ...] = (KIND_BAIKE_DEF, KIND_BAIKE_TRAP, KIND_INTERVIEW_QA)

DIFF_MAP = {"初级": "easy", "简单": "easy", "中级": "medium", "中等": "medium",
            "高级": "hard", "困难": "hard"}

# back 短于此长度的要点，一律降级成「无答案」（护栏③），避免把标签行当成答案
_MIN_BACK_LEN = 20
# baike_def 的 back 短于此长度 → 不建卡（见 _parse_baike_a）
_MIN_DEF_LEN = 8

# ---------------- 通用正则 ----------------
RE_H1 = re.compile(r"^#\s+(.+?)\s*$", re.M)
RE_H2 = re.compile(r"^##\s+(.+?)\s*$", re.M)
RE_H2_DEF = re.compile(r"^##\s*定义\s*$", re.M)
RE_ANY_H2 = re.compile(r"^##\s+", re.M)
RE_ANY_H3 = re.compile(r"^#{2,4}\s+", re.M)
RE_DEF = re.compile(r"^\*\*一句话定义[^\n*]*?\*\*\s*[:：]?\s*(.*)$", re.M)
RE_ANA = re.compile(r"^\*\*通俗类比[^\n*]*?\*\*\s*[:：]?\s*(.*)$", re.M)
RE_TRAPH = re.compile(r"^##\s*常见误区\s*$", re.M)
RE_RELH = re.compile(r"^##\s*相关术语\s*$", re.M)
RE_BULLET = re.compile(r"^\s*[-*]\s+(.+?)\s*$", re.M)
RE_SEC = re.compile(
    r"^\*\*(一句话定义|通俗类比|常见误区|与相关术语[^\n*]*|为什么需要它|具体示例)"
    r"[^\n*]*?\*\*\s*[:：]?\s*(.*)$", re.M)
# baike B 的术语 H2：排除通用小节标题（这些不是术语名）
RE_H2_TERM = re.compile(
    r"^##\s+(?!定义|原理|关键|应用|优点|常见误区|相关术语|参考|目录|小结|总结)"
    r"(.+?)\s*$", re.M)
# baike B 的对比小节（误区卡来源）
RE_CONTRAST_HEAD = re.compile(r"^\*\*与相关术语[^\n*]*?\*\*\s*$", re.M)
# interview I-1 的题块内小节（题目卡片正反面来源）
RE_I1_SEC = re.compile(r"^\*\*(题目描述|思路分析|复杂度分析)[^\n*]*?\*\*\s*[:：]?\s*(.*)$", re.M)
RE_I1_Q = re.compile(r"^#{2,4}\s*题目\s*(\d+)\s*[:：]\s*(.+?)\s*$", re.M)
RE_I2_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*(初级|中级|高级|简单|中等|困难)\s*\|", re.M)
RE_I2_THEME = re.compile(r"^#{2,4}\s*主题\s*(\d+)[^\n]*$", re.M)
RE_I3_Q = re.compile(r"^\s*(\d+)\s*[.、]\s*(.{8,200}?[？?])\s*$", re.M)
RE_I3_ANS = re.compile(r"^(查看答案|展开答案|查看解答)\s*$", re.M)
RE_I3_DIFF = re.compile(r"^(简单|中等|困难|初级|中级|高级)$")
RE_I3_TEMPLATE = re.compile(r"^💡?\s*回答模板\s*[\d一二三四五六七八九十]+\s*[:：]?\s*(.*)$")
WIKILINK = re.compile(r"!?\[\[([^\[\]|#]+)(?:#[^\[\]|]*)?(?:\|[^\[\]]*)?\]\]")
# 行首粗体小节（收集多行值时到此为止）
RE_BOLD_HEAD = re.compile(r"^\*\*")
# 围栏代码块：抽卡前一律剔除（代码块里的伪题面/伪小节不算数）
FENCE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.S)
# 中文标点（判定「有句子味的正文」而非标签行）
CJK_PUNCT = re.compile(r"[，。；：、！？“”‘’（）【】《》,.;:!?()\[\]]")

NO_ANSWER_HINT = "（原文未附答案，点击「跳转原文」定位到该题所在章节）"


# ---------------- 归一化与 ID ----------------
def norm(s: str) -> str:
    """粗归一化：剥离 markdown 标记符与空白后 NFKC + 小写，用于 ID 与去重。"""
    s = re.sub(r"[*`_>\s]+", "", s)
    return unicodedata.normalize("NFKC", s).lower()


def make_card_id(kind: str, term: str, front: str) -> str:
    """卡片 ID 只取 (kind, term, front) —— 不含路径，改名/移动后进度不丢。"""
    payload = f"{kind}|{norm(term)}|{norm(front)}"
    return "c_" + hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def fingerprint(front: str, back: str) -> str:
    """正反面指纹：语料编辑后判定「内容是否真的变了」，决定是否计为 updated。"""
    payload = f"{norm(front)}|{norm(back)}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


# ---------------- 卡片数据类 ----------------
@dataclass(frozen=True)
class Card:
    """一张复习卡片。字段顺序固定（LearnStore 按此顺序批量 UPSERT）。"""

    card_id: str
    kind: str
    term: str
    front: str
    back: str
    hint: str
    source_rel: str
    anchor: str
    domain: str
    sub: str
    tags: str
    related: str
    difficulty: str
    has_answer: int
    fingerprint: str

    def row(self) -> tuple:
        """按字段声明顺序展开成元组，供 executemany 使用。"""
        return (
            self.card_id, self.kind, self.term, self.front, self.back, self.hint,
            self.source_rel, self.anchor, self.domain, self.sub, self.tags,
            self.related, self.difficulty, self.has_answer, self.fingerprint,
        )


# ---------------- 文本工具 ----------------
def strip_fences(text: str) -> str:
    """剔除围栏代码块（``` / ~~~），保留行数以免错位影响后续按行处理。"""
    def _keep(match: re.Match) -> str:
        return "\n" * match.group(0).count("\n")

    return FENCE_RE.sub(_keep, text)


def _section_after(body: str, start: int) -> str:
    """从 start 处到下一个 `^## ` 标题（或文末）之间的区块文本。"""
    m = RE_ANY_H2.search(body, start)
    return body[start:m.start()] if m else body[start:]


def _next_heading(body: str, pos: int, rx: re.Pattern) -> int:
    m = rx.search(body, pos)
    return m.start() if m else len(body)


def _collect_following(lines: Sequence[str], start: int, allow_bullets: bool = False) -> str:
    """某一行之后的值：收集后续非空行，直到空行 / 下一个粗体小节 / 标题 / 围栏 / 表格。

    协程两种实参形态（真实语料都存在，必须都支持）：
        **一句话定义（大白话）：** 值在同一行        → group(2) 非空，调用方直接取
        **一句话定义（大白话）**\n值在下一行        → group(2) 为空，由此函数采集
    """
    out: list[str] = []
    for ln in lines[start:]:
        s = ln.strip()
        if not s:
            if out:
                break
            continue  # 连续的空行先跳过（语料里标题与正文间常隔多个空行）
        if s.startswith("#") or s.startswith("```") or s.startswith("~~~") or s.startswith("|"):
            break
        if RE_BOLD_HEAD.match(s):
            break
        if not allow_bullets and (s.startswith("- ") or s.startswith("* ")):
            break
        out.append(s)
        if len(out) >= 12:
            break
    return " ".join(out)


def _match_value(text: str, rx: re.Pattern, allow_bullets: bool = False) -> str:
    """按 rx 找小节取值：同行有值用它，否则采集后续行。返回 '' 表示未命中。"""
    lines = text.splitlines()
    last_idx = rx.groups
    for i, ln in enumerate(lines):
        m = rx.match(ln)
        if not m:
            continue
        val = (m.group(last_idx) or "").strip()
        if val:
            return val
        collected = _collect_following(lines, i + 1, allow_bullets=allow_bullets)
        if collected:
            return collected
    return ""


def _all_sec_values(text: str, rx: re.Pattern = RE_SEC,
                    allow_bullets: bool = False) -> list[tuple[str, str]]:
    """返回 [(小节键名原文, 值)]，按出现顺序；用于 baike B / interview I-1 一次扫完所有小节。"""
    lines = text.splitlines()
    out: list[tuple[str, str]] = []
    skip_to = -1
    n_groups = rx.groups
    for i, ln in enumerate(lines):
        if i <= skip_to:
            continue
        m = rx.match(ln)
        if not m:
            continue
        key = m.group(1)
        val = (m.group(n_groups) or "").strip()
        if not val:
            val = _collect_following(lines, i + 1, allow_bullets=allow_bullets)
        out.append((key, val))
        skip_to = i
    return out


def _term_of(fm: dict, clean: str, rel: str) -> str:
    """术语名优先级：frontmatter title → # H1 → 文件名（无扩展名）。"""
    t = str(fm.get("title") or "").strip()
    if t:
        return t
    m = RE_H1.search(clean)
    if m:
        return m.group(1).strip()
    return rel.rsplit("/", 1)[-1].rsplit(".md", 1)[0]


def _tags_of(fm: dict) -> str:
    tags = fm.get("tags")
    if isinstance(tags, list):
        return ",".join(str(x).strip() for x in tags if str(x).strip())
    return str(tags or "").strip()


def _related_of(body: str) -> list[str]:
    """## 相关术语 区块内的 [[双链]] 目标名列表。"""
    m = RE_RELH.search(body)
    if not m:
        return []
    block = _section_after(body, m.end())
    seen: list[str] = []
    for name in WIKILINK.findall(block):
        name = name.strip()
        if name and name not in seen:
            seen.append(name)
    return seen


def _split_rel(rel: str) -> tuple[str, str]:
    """`baike/algorithms/KMP 算法.md` → ('baike', 'algorithms')；域根散文件 → (域, '_root')。

    _root 是 store.py 的既有约定（域根散文件所属子域），保持同一套词汇便于前端拼 URL。
    """
    parts = rel.split("/")
    domain = parts[0] if parts else ""
    sub = parts[1] if len(parts) >= 3 else "_root"
    return domain, sub


# ---------------- 构造函数 ----------------
def _mk(kind: str, term: str, front: str, back: str, hint: str, rel: str,
        domain: str, sub: str, tags: str, related: Iterable[str],
        anchor: str = "", difficulty: str = "", has_answer: bool | None = None) -> Card:
    """构造卡片。has_answer=None 时按护栏③自动判定（back < 20 字 → 0）。"""
    back = (back or "").strip()
    front = (front or "").strip()
    hint = (hint or "").strip()
    if has_answer is None:
        has_answer = len(back) >= _MIN_BACK_LEN
    return Card(
        card_id=make_card_id(kind, term, front),
        kind=kind, term=term, front=front, back=back, hint=hint,
        source_rel=rel, anchor=anchor, domain=domain, sub=sub, tags=tags,
        related=json.dumps(list(related), ensure_ascii=False),
        difficulty=difficulty, has_answer=1 if has_answer else 0,
        fingerprint=fingerprint(front, back),
    )


# ---------------- baike A ----------------
def _parse_baike_a(rel: str, domain: str, sub: str, tags: str,
                   fm: dict, clean: str) -> list[Card]:
    """单术语词条：1 张 baike_def + 至多 2 张 baike_trap。"""
    term = _term_of(fm, clean, rel)
    # 定义：优先只在 `## 定义` 区块内找，避免后文提到同名小节时被串味
    m_def_h2 = RE_H2_DEF.search(clean)
    scope = _section_after(clean, m_def_h2.end()) if m_def_h2 else clean
    def_val = _match_value(scope, RE_DEF)
    if not def_val:
        def_val = _match_value(clean, RE_DEF)
    if len(def_val.strip()) < _MIN_DEF_LEN:
        return []  # 缺定义 = 不成卡（格式 C 的长文走的就是这条退路）
    ana_val = _match_value(clean, RE_ANA)

    cards: list[Card] = [
        _mk(KIND_BAIKE_DEF, term, f"「{term}」是什么？用一句话说清楚。",
            def_val, ana_val, rel, domain, sub, tags, _related_of(clean),
            anchor="## 定义")
    ]

    # 误区卡：取 `## 常见误区` 到下一个 `^## ` 之间区块的前 2 条列表项（有就有，没有不强凑）
    m_trap = RE_TRAPH.search(clean)
    if m_trap:
        block = _section_after(clean, m_trap.end())
        for item in RE_BULLET.findall(block)[:2]:
            item = item.strip()
            if len(item) < 4:
                continue
            cards.append(
                _mk(KIND_BAIKE_TRAP, term, f"判断正误：{item}",
                    f"✗ 这是常见误区。正解：{def_val}", ana_val, rel, domain, sub,
                    tags, [], anchor="## 常见误区"))
    return cards


# ---------------- baike B ----------------
def _parse_baike_b(rel: str, domain: str, sub: str, tags: str,
                   _fm: dict, clean: str) -> list[Card]:
    """多词条汇篇：按 H2 切块，每块出 1 张 def + 至多 1 张 trap。"""
    cards: list[Card] = []
    term_starts = list(RE_H2_TERM.finditer(clean))
    if not term_starts:
        return []
    for idx, m in enumerate(term_starts):
        term = m.group(1).strip()
        end = term_starts[idx + 1].start() if idx + 1 < len(term_starts) else len(clean)
        block = clean[m.start():end]
        # 下一节也可能是不被认定为术语的通用小节 → 仍要在那儿截断
        cut = _next_heading(block, 1, RE_ANY_H2)
        block = block[:cut]

        secs = _all_sec_values(block, RE_SEC, allow_bullets=False)
        def_val = ""
        ana_val = ""
        for key, val in secs:
            if not def_val and key.startswith("一句话定义"):
                def_val = val
            elif not ana_val and key.startswith("通俗类比"):
                ana_val = val
        if len(def_val.strip()) < _MIN_DEF_LEN:
            continue  # 该块没有可用定义 → 不抽（导语/小节 recap 等）

        # 对比小节（兼具误区作用）：原样再取一次，允许收集 `- ` 列表
        cards.append(
            _mk(KIND_BAIKE_DEF, term, f"「{term}」是什么？用一句话说清楚。",
                def_val, ana_val, rel, domain, sub, tags, [], anchor=term))
        contrast = _contrast_item(block)
        if contrast:
            cards.append(
                _mk(KIND_BAIKE_TRAP, term, f"判断正误：{contrast}",
                    f"对比要点：{contrast}。定义：{def_val}", ana_val, rel, domain, sub,
                    tags, [], anchor=term))
    return cards


def _contrast_item(block: str) -> str:
    """`**与相关术语…**` 小节的首条 `- ` 对比要点（没有则 ''）。

    只取首条：后续条目多为同一主题的补充说明，逐条成卡会把「对比」稀释成流水账。
    """
    m = RE_CONTRAST_HEAD.search(block)
    if not m:
        return ""
    lines = block.splitlines()
    # m.end() 停在小节标题那一行内部，+1 才是标题的下一行
    start = block.count("\n", 0, m.end()) + 1
    for ln in lines[start:]:
        s = ln.strip()
        if not s:
            continue  # 标题与列表之间的空行跳过
        bm = RE_BULLET.match(ln)
        if bm:
            return bm.group(1).strip()
        if RE_BOLD_HEAD.match(s) or s.startswith("#"):
            return ""  # 该小节没有列表项（只有一个段落），不成误区卡
    return ""


# ---------------- interview ----------------
def _parse_i1(rel: str, domain: str, sub: str, tags: str, fm: dict, clean: str) -> list[Card]:
    """I-1 章节题目式：`### 题目N：xxx` + **题目描述：** / **思路分析：**。"""
    term = _term_of(fm, clean, rel)
    cards: list[Card] = []
    heads = list(RE_I1_Q.finditer(clean))
    for i, m in enumerate(heads):
        no = int(m.group(1))
        title = m.group(2).strip()
        end = _next_heading(clean, m.end(), RE_ANY_H3)
        if i + 1 < len(heads) and heads[i + 1].start() < end:
            end = heads[i + 1].start()
        block = clean[m.end():end]

        parts: list[str] = []
        secs = _all_sec_values(block, RE_I1_SEC, allow_bullets=True)
        for key in ("题目描述", "思路分析", "复杂度分析"):
            val = next((v for k, v in secs if k.startswith(key)), "")
            if val:
                parts.append(val)
        back = "\n\n".join(parts).strip()[:600]
        cards.append(
            _mk(KIND_INTERVIEW_QA, term, f"Q{no}. {title}", back, "", rel, domain, sub,
                tags, [], anchor=m.group(0).lstrip("# ").strip(), difficulty="medium"))
    return cards


def _parse_i2(rel: str, domain: str, sub: str, tags: str, fm: dict, clean: str) -> list[Card]:
    """I-2 表格清单式：`| N | 题面 | 难度 |`。全篇只有题面，has_answer=0。"""
    term = _term_of(fm, clean, rel)
    lines = clean.splitlines()
    theme_pos: list[tuple[int, str]] = []
    for i, ln in enumerate(lines):
        mt = RE_I2_THEME.match(ln)
        if mt:
            theme_pos.append((i, ln.strip().lstrip("# ").strip()))
    cards: list[Card] = []
    for i, ln in enumerate(lines):
        m = RE_I2_ROW.match(ln)
        if not m:
            continue
        no = int(m.group(1))
        stem = m.group(2).strip()
        diff = DIFF_MAP.get(m.group(3).strip(), "")
        anchor = ""
        for pos, title in theme_pos:
            if pos < i:
                anchor = title
            else:
                break
        cards.append(
            _mk(KIND_INTERVIEW_QA, term, f"Q{no}. {stem}", NO_ANSWER_HINT, "", rel,
                domain, sub, tags, [], anchor=anchor, difficulty=diff,
                has_answer=False))
    return cards


def _parse_i3(rel: str, domain: str, sub: str, tags: str, fm: dict, clean: str) -> list[Card]:
    """I-3 扁平纯文本式：`1. 题面？` … `查看答案` … 答案正文。"""
    term = _term_of(fm, clean, rel)
    q_matches = list(RE_I3_Q.finditer(clean))
    if not q_matches:
        return []
    cards: list[Card] = []
    for i, m in enumerate(q_matches):
        no = int(m.group(1))
        stem = m.group(2).strip()
        end = q_matches[i + 1].start() if i + 1 < len(q_matches) else len(clean)
        region = clean[m.end():end].splitlines()

        ans_lines: list[str] = []
        started = False
        for ln in region:
            s = ln.strip()
            if RE_I3_ANS.match(s):
                started = True
                continue
            if not started:
                continue  # 题面与「查看答案」之间是难度/标签噪声，丢弃
            if not s:
                continue
            if RE_I3_DIFF.match(s):
                continue
            if len(s) < 10 and not CJK_PUNCT.search(s):
                continue  # 标签行（如「CSS选择器」）
            tmpl = RE_I3_TEMPLATE.match(s)
            if tmpl:
                ans_lines.append(f"· {s}")
                continue
            ans_lines.append(s)
        back = "\n".join(ans_lines).strip()[:800]
        cards.append(
            _mk(KIND_INTERVIEW_QA, term, f"Q{no}. {stem}", back, "", rel, domain, sub,
                tags, [], anchor=f"Q{no}"))
    return cards


# ---------------- 入口 ----------------
def parse_file(rel: str, raw: str) -> list[Card]:
    """把一篇语料解析成卡片列表。返回空列表表示该篇不产生卡片。

    Args:
        rel: content/ 相对 posix 路径，如 `baike/algorithms/KMP 算法.md`。
        raw: 文件原文（含 frontmatter）。

    Returns:
        list[Card]，顺序稳定（同的输入 → 同的输出）。
    """
    rel = str(rel).replace("\\", "/")
    parts = rel.split("/")
    if not parts or parts[0] not in CARD_DOMAINS:
        return []
    if any(p.startswith("_") for p in parts):
        return []  # 双保险：_ 前缀目录绝不抽卡
    domain, sub = _split_rel(rel)
    tags = ""
    fm: dict = {}
    body = raw or ""
    try:
        fm, body = parse_frontmatter(raw or "")
    except Exception:
        fm, body = {}, raw or ""
    tags = _tags_of(fm)
    clean = strip_fences(body)

    if domain == "baike":
        if RE_H2_DEF.search(clean):
            cards = _parse_baike_a(rel, domain, sub, tags, fm, clean)
            if cards:
                return cards
        return _parse_baike_b(rel, domain, sub, tags, fm, clean)

    # interview：按 I-1 → I-2 → I-3 顺序 try，命中即停
    for parser in (_parse_i1, _parse_i2, _parse_i3):
        cards = parser(rel, domain, sub, tags, fm, clean)
        if cards:
            return cards
    return []
