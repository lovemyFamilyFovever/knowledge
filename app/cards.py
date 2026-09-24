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
    interview I-4  编号问答式：`### Q1: xxx` + `**参考答案：**` / `**答案要点：**`
    interview I-5  编号标题式：`### N. 题面｜初级|中级|高级` + 紧随其后的答案正文
                   （阅读器渲染约定，2026-09-18 起面试语料统一采用）
    interview I-5b 无编号单题式：`### 题面｜初级|中级|高级`（一文件一题的短条目）
"""
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Sequence

from app.store import parse_frontmatter

# 抽卡解析器的版本。改动解析规则必须 +1 —— LearnStore.ensure_synced 依据它触发全量重建。
#
# 变更史：
#   v1  首版：baike A/B + interview I-1/I-2/I-3
#   v2  ① 新增 I-4（`### Q1: xxx`）② baike B 术语名前导编号清洗（"1. AI 对话系统" → "AI 对话系统"）
#       ③ I-3 难度回填（题面下一行的 简单/中等/困难 → difficulty）
#       ④ I-3/I-4 答案标记扩展（补 详细解答/参考答案/答案要点 等，此前这些文件的 back 全为空）
#   v2 会改变部分 card_id（术语名变了），旧卡走软下线；此刻尚无真实复习数据，代价为零。
#   v3  ① 新增 I-5（`### N. 题干｜难度`，面试语料 2026-09-18 统一改用的渲染约定）
#       ② front 与 I-3/I-4 同口径（`Q{no}. 题面`），题干未变的题目 card_id 保持不变；
#          题干编号被重排过的题目会换 card_id，旧卡软下线（经查无复习进度落在这些题上）。
#   v4  新增 I-5b：无编号单题式 `### 题干｜难度`（interview/bigtech 一文件一题的导入稿）。
#       题号按出现顺序补 1..n，card_id 口径与 I-5 一致；带难度后缀才认，故既有语料不受影响。
CARDS_PARSER_VERSION = 4

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
# interview I-4：`### Q1: xxx` / `#### 问题2、xxx` / `## Question 3. xxx`
RE_I4_Q = re.compile(r"^#{2,4}\s*(?:Q|问题|Question)\s*(\d+)\s*[:：、.．]?\s*(.{4,200}?)\s*$",
                     re.M | re.I)
# I-4 块内标题（到下一个同级或更高级标题止）
RE_I4_HEAD = re.compile(r"^(#{1,6})\s+", re.M)
# 答案标记行：v1 只认「查看答案/展开答案/查看解答」，实测还有
# 详细解答（扩展部分1-7、60题+详细解答）、**参考答案：**、**答案要点：**（I-4 两篇）
# 这些文件的答案正文此前**全部抽空**（has_answer=0），v2 补齐。
# 形如 `答案：小明现在有6个苹果` 这种「冒号后面还有内容」的行不算标记（它本身就是正文）。
RE_I3_ANS = re.compile(
    r"^\s*[*_]{0,2}(查看答案|展开答案|查看解答|详细解答|详细解析|答案解析|参考答案要点|参考答案"
    r"|答案要点|答案详解|答案分析|答案|解答思路|解答|解析|详解)[*_]{0,2}\s*[:：]?\s*[*_]{0,2}\s*$",
    re.M)
#「完全不含中文」= 纯英文/代码注释，不配当一道中文面试题的卡背
RE_CJK = re.compile(r"[\u4e00-\u9fff]")
# baike B 术语名前导编号：只去前导的「N. / N、/ N)」，不动标题中间的括号
RE_TERM_NUM = re.compile(r"^\s*\d+\s*[.、)）]\s*")
RE_I3_DIFF = re.compile(r"^(简单|中等|困难|初级|中级|高级)$")
# interview I-5：`### N. 题干｜初级|中级|高级`（2026-09-18 面试语料统一排版；
# 竖线允许全角「｜」/半角「|」，难度后缀必须在行尾）
RE_I5_Q = re.compile(r"^###\s+(\d+)\s*[.、]\s*(.+?)\s*$", re.M)
RE_I5_DIFF = re.compile(r"[｜|]\s*(初级|中级|高级)\s*$")
# interview I-5b：无编号单题式 `### 题干｜初级|中级|高级`（v4）。
# 「一文件一题」的短条目（interview/bigtech 导入稿）没有题号，但仍是同一种渲染约定。
# 必须带难度后缀才认——否则答案正文里的普通三级标题会被当成题面。
RE_I5_Q_BARE = re.compile(r"^###\s+(\S.*?[｜|]\s*(?:初级|中级|高级)\s*)$", re.M)
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


def _next_heading_at_most(body: str, pos: int, level: int) -> int:
    """下一个「级别不小于 level」的标题位置（level 3 = `###`，更高级是 `##` / `#`）。

    I-4 按此切块：`### Q1` 的块止于下一个 `###` 或更高级标题，`####` 这类更低级
    的小标题属于答案内部，不应截断。
    """
    for m in RE_I4_HEAD.finditer(body, pos):
        if len(m.group(1)) <= level:
            return m.start()
    return len(body)


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
    n_groups = rx.groups
    # 这里曾有一句 `if i <= skip_to: continue` 配 `skip_to = i`：`i` 单调递增、而 skip_to 只被
    # 设成"刚匹配那一行"的行号，条件永不成立 —— 死守卫，只会给读者一种"已消费行被跳过了"的错觉
    # （P6 变异测试里它是条永远杀不掉的存活体）。真的不需要跳过：多行值是 _collect_following
    # 采的，它以 RE_BOLD_HEAD（^\*\*）为停止标记，而 RE_SEC 必须以 `**` 开头 ——
    # 被采集掉的值行按定义不可能再匹配 RE_SEC，所以不会被重复计成一个小节。
    for i, ln in enumerate(lines):
        m = rx.match(ln)
        if not m:
            continue
        key = m.group(1)
        val = (m.group(n_groups) or "").strip()
        if not val:
            val = _collect_following(lines, i + 1, allow_bullets=allow_bullets)
        out.append((key, val))
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
        # 术语名清洗：只去前导编号（"1. AI 对话系统" → "AI 对话系统"），
        # 不动标题中间的英文括号（"MD5（Message Digest 5）" 必须原样保留）。
        heading = m.group(1).strip()
        term = RE_TERM_NUM.sub("", heading).strip() or heading
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
                def_val, ana_val, rel, domain, sub, tags, [], anchor=heading))
        contrast = _contrast_item(block)
        if contrast:
            cards.append(
                _mk(KIND_BAIKE_TRAP, term, f"判断正误：{contrast}",
                    f"对比要点：{contrast}。定义：{def_val}", ana_val, rel, domain, sub,
                    tags, [], anchor=heading))
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


def _parse_i4(rel: str, domain: str, sub: str, tags: str, fm: dict, clean: str) -> list[Card]:
    """I-4 编号问答式：`### Q1: xxx` + `**参考答案：**` / `**答案要点：**`。

    真实语料里有两种块内形态，都必须出卡：
        **答案要点：** 后紧跟 `- ` 列表（题库版）
        **参考答案：** 后跟成段正文 + 表格 + `**详细解析：**`（详解版）
    """
    term = _term_of(fm, clean, rel)
    heads = list(RE_I4_Q.finditer(clean))
    if not heads:
        return []
    cards: list[Card] = []
    for i, m in enumerate(heads):
        title = m.group(2).strip()
        if len(title) < 4:
            continue  # 护栏①：标题太短（多半是误匹配的分节符）不建卡
        level = len(m.group(0)) - len(m.group(0).lstrip("#"))
        end = _next_heading_at_most(clean, m.end(), max(1, level))
        if i + 1 < len(heads) and heads[i + 1].start() < end:
            end = heads[i + 1].start()
        block = clean[m.end():end]
        if not RE_CJK.search(block):
            continue  # 护栏②：块内完全没有中文（纯英文代码注释）不建卡

        body = _after_answer_marker(block)
        if not RE_CJK.search(body):
            body = block  # 标记之后反而没了中文 → 退回到整块正文
        body = _tidy_answer(body)[:600]

        no = m.group(1)
        anchor = m.group(0).lstrip("# ").strip()
        if len(body) < _MIN_BACK_LEN:
            body = NO_ANSWER_HINT
            has_answer = False
        else:
            has_answer = True
        cards.append(
            _mk(KIND_INTERVIEW_QA, term, f"Q{no}. {title}", body, "", rel, domain, sub,
                tags, [], anchor=anchor, difficulty="medium", has_answer=has_answer))
    return cards


def _after_answer_marker(block: str) -> str:
    """块内存在答案标记行时，只返回标记**之后**的正文；否则返回原块。

    标记行形如 `**参考答案：**` / `**答案要点：**` / `详细解答` —— 它们本身不是答案，
    把它算进卡背会让每张卡的正面 20 个字都长一样。
    """
    lines = block.splitlines()
    for i, ln in enumerate(lines):
        if RE_I3_ANS.match(ln.strip()):
            return "\n".join(lines[i + 1:])
    return block


def _tidy_answer(text: str) -> str:
    """答案正文清洗：去掉分隔线、连续空行与行尾空白，保留列表与表格结构。"""
    out: list[str] = []
    blank = False
    for ln in text.splitlines():
        s = ln.rstrip()
        if not s.strip():
            if out and not blank:
                out.append("")
            blank = True
            continue
        blank = False
        if set(s.strip()) <= {"-", "*", "_"} and len(s.strip()) >= 3:
            continue  # 水平分隔线（--- / ***）
        out.append(s)
    return "\n".join(out).strip()


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
        difficulty = ""
        for ln in region:
            s = ln.strip()
            if RE_I3_ANS.match(s):
                started = True
                continue
            if not started:
                # 题面与「查看答案」之间：难度行回填 difficulty，其余是标签噪声
                if not difficulty:
                    md = RE_I3_DIFF.match(s)
                    if md:
                        difficulty = DIFF_MAP.get(md.group(1), "")
                continue
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
                tags, [], anchor=f"Q{no}", difficulty=difficulty))
    return cards


def _parse_i5(rel: str, domain: str, sub: str, tags: str, fm: dict, clean: str) -> list[Card]:
    """I-5 编号标题式（阅读器渲染约定）：`### N. 题面｜初级|中级|高级` + 正文答案。

    2026-09-18 面试语料统一改为该排版（`##` 小节 + `### N. 题干｜难度` + `> 🎯/🔍` 提示框），
    答案正文直接跟在题干之后；难度后缀行尾剥离后走 DIFF_MAP 回填 difficulty。
    front 与 I-3/I-4 保持同一口径（`Q{no}. {题面}`），使题干未变的题目 card_id 不变。

    v4 起兼容 I-5b「无编号单题式」`### 题干｜难度`：一文件一题的导入稿没有题号，
    按出现顺序补 1..n。为避免把答案里的普通三级标题误判为题面，无编号形态
    **强制要求行尾难度后缀**。
    """
    term = _term_of(fm, clean, rel)
    q_matches = list(RE_I5_Q.finditer(clean))
    numbered = bool(q_matches)
    if not numbered:
        q_matches = list(RE_I5_Q_BARE.finditer(clean))
    if not q_matches:
        return []
    cards: list[Card] = []
    for i, m in enumerate(q_matches):
        no = int(m.group(1)) if numbered else i + 1
        tail = m.group(2) if numbered else m.group(1)
        stem = RE_I5_DIFF.sub("", tail).strip()
        if not stem:
            continue
        end = q_matches[i + 1].start() if i + 1 < len(q_matches) else len(clean)
        region = clean[m.end():end]
        # 该题与下一题之间若夹着 `## 小节名`，截断掉（小节标题不属于答案）
        m_h2 = RE_ANY_H2.search(region)
        if m_h2:
            region = region[:m_h2.start()]

        difficulty = ""
        md = RE_I5_DIFF.search(tail)
        if md:
            difficulty = DIFF_MAP.get(md.group(1), "")

        ans_lines: list[str] = []
        for ln in region.splitlines():
            s = ln.strip()
            if not s:
                continue
            if s.startswith(">"):
                s = s[1:].strip()  # 提示框标记（🎯 关键要点 / 🔍 追问 / 💡 / ⚠️）只去引用符
            if not s or RE_I3_DIFF.match(s):
                continue
            ans_lines.append(s)
        back = _tidy_answer("\n".join(ans_lines))[:800]
        cards.append(
            _mk(KIND_INTERVIEW_QA, term, f"Q{no}. {stem}", back, "", rel, domain, sub,
                tags, [], anchor=f"Q{no}", difficulty=difficulty))
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

    # interview：按 I-1 → I-4 → I-5 → I-2 → I-3 顺序 try，命中即停
    for parser in (_parse_i1, _parse_i4, _parse_i5, _parse_i2, _parse_i3):
        cards = parser(rel, domain, sub, tags, fm, clean)
        if cards:
            return cards
    return []
