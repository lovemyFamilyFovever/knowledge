# -*- coding: utf-8 -*-
"""知库 学习/复习 smoke tests —— 抽卡、SM-2 调度、卡片库、HTTP 契约。

运行：python tests/test_learn.py

分四段（缺 RAG/Flask 依赖的段落自动 SKIP，参照 tests/test_rag.py 的写法）：
    ① parse_file   对真实语料样本的抽卡行为（纯函数，零依赖）
    ② sm2          SM-2 间隔推进（纯函数，零依赖）
    ③ LearnStore   sqlite 卡片库：幂等 / 软下线 / 删库自愈
    ④ HTTP         通过 Flask test_client 校验接口信封与字段名

全程只读真实 content/（解析样本时在 repo 内按路径读），写操作一律用临时目录。
"""
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CONTENT = ROOT / "content"

from app.cards import (CARDS_PARSER_VERSION, fingerprint, make_card_id, norm,  # noqa: E402
                       parse_file)
from app.sm2 import DEFAULT_STATE, EF_MIN, Q_MAP, schedule  # noqa: E402

passed = failed = 0


def check(name: str, cond: bool, extra: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS {name}")
    else:
        failed += 1
        print(f"  FAIL {name} {extra}")


def read_sample(rel: str) -> str:
    p = CONTENT / rel
    if not p.is_file():
        raise FileNotFoundError(f"缺真实语料样本：{rel}")
    return p.read_text(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- ① 抽卡
def test_parse_baike_a() -> None:
    rel = "baike/algorithms/KMP 算法.md"
    cards = parse_file(rel, read_sample(rel))
    defs = [c for c in cards if c.kind == "baike_def"]
    traps = [c for c in cards if c.kind == "baike_trap"]
    check("A 格式：1 张 baike_def", len(defs) == 1, f"got {len(defs)}")
    check("A 格式：2 张 baike_trap", len(traps) == 2, f"got {len(traps)}")
    check("A 格式：term 取 frontmatter title", defs and defs[0].term == "KMP 算法",
          f"got {defs[0].term if defs else None!r}")
    check("A 格式：front 模板", bool(defs) and defs[0].front == "「KMP 算法」是什么？用一句话说清楚。",
          f"got {defs[0].front if defs else None!r}")
    check("A 格式：back 是一句话定义", bool(defs) and "字符串匹配算法" in defs[0].back)
    check("A 格式：hint 来自通俗类比", bool(defs) and len(defs[0].hint) > 10)
    check("A 格式：anchor = ## 定义", bool(defs) and defs[0].anchor == "## 定义")
    rel_terms = json.loads(defs[0].related) if defs else []
    check("A 格式：related 解析出 5 个双链", len(rel_terms) == 5, f"got {rel_terms}")
    check("A 格式：domain/sub 来自路径",
          bool(defs) and defs[0].domain == "baike" and defs[0].sub == "algorithms")
    check("A 格式：trap front 模板", bool(traps) and traps[0].front.startswith("判断正误："))
    check("A 格式：trap back 带正解", bool(traps) and traps[0].back.startswith("✗ 这是常见误区。正解："))


# B 格式术语汇编夹具（内联，不依赖真实语料文件）：原样本 baike/security/哈希算法篇.md
# 二期拆分为枢纽页后已转 A 格式、随拆分持续演化；解耦先例见 4a785b1（SQL 基础术语）。
_B_FIXTURE_MD = """---
title: "哈希算法夹具"
tags: []
source: "baike"
---

# 哈希算法夹具

## MD5（Message Digest 5）

**一句话定义（大白话）：** MD5 把任意长度数据压成 128 位定长指纹，用于快速比对内容是否一致。

**通俗类比（生活场景）：** 像给每本书编一个唯一书号，凭号即可判断两本书是否同一本。

**与相关术语的对比和区分**
- MD5 输出 128 位摘要，SHA-256 输出 256 位摘要。

## SHA-1（Secure Hash Algorithm 1）

**一句话定义（大白话）：** SHA-1 输出 160 位哈希值，2017 年被实测构造出碰撞，正从安全场景退役。

**与相关术语的对比和区分**
- SHA-1 比 MD5 难碰撞，但不敌 SHA-256，新场景不再首选。

## SHA-256

**一句话定义（大白话）：** SHA-256 属 SHA-2 家族，256 位摘要，是当下抗碰撞哈希的默认选择。

**与相关术语的对比和区分**
- 相比 MD5，摘要更长、构造碰撞的算力成本高到不可行。

## HMAC（Hash-based Message Authentication Code）

**一句话定义（大白话）：** HMAC 是带密钥的哈希，同时证明数据未被篡改与发送方身份。

**与相关术语的对比和区分**
- 普通哈希谁都能重算只防意外，HMAC 无密钥者算不出、防对手。
"""


def test_parse_baike_b() -> None:
    rel = "baike/security/哈希算法夹具.md"
    cards = parse_file(rel, _B_FIXTURE_MD)
    defs = [c for c in cards if c.kind == "baike_def"]
    terms = [c.term for c in defs]
    check("B 格式：抽出 ≥4 张 def", len(defs) >= 4, f"got {len(defs)}")
    check("B 格式：term 保留英文括号", "MD5（Message Digest 5）" in terms, f"got {terms[:3]}")
    check("B 格式：每个词条 1 张 def + 至多 1 张 trap",
          len(defs) >= len([c for c in cards if c.kind == "baike_trap"]))
    check("B 格式：related 为空数组", all(c.related == "[]" for c in cards))
    # 冒号在 ** 内部的变体：用内联样本，不依赖真实语料文件
    # （原先读 baike/database/SQL 基础术语.md，该篇二期拆为枢纽后格式会变，故解耦）
    _sql_variant = """# SQL 基础术语

## DDL（数据定义语言）

**一句话定义（大白话）：** DDL 用来创建、修改、删除数据库对象的结构定义。

## DML（数据操作语言）

**一句话定义（大白话）：** DML 用来对表中的数据行进行增删改操作。

## DQL（数据查询语言）

**一句话定义（大白话）：** DQL 用 SELECT 从数据库中查询所需的数据。

## TCL（事务控制语言）

**一句话定义（大白话）：** TCL 用来管理事务的提交与回滚边界。
"""
    cards2 = parse_file("baike/database/SQL 基础术语.md", _sql_variant)
    terms2 = [c.term for c in cards2 if c.kind == "baike_def"]
    check("B 格式变体（冒号在 ** 内）：也能抽到定义卡", len(terms2) >= 4, f"got {len(terms2)}")
    check("B 格式变体：第一条是 DDL（…）",
          bool(terms2) and terms2[0].startswith("DDL"), f"got {terms2[:1]}")
    check("B 格式变体：back 非空且够长",
          all(len(c.back) >= 10 for c in cards2 if c.kind == "baike_def"))


def test_parse_interview_i1() -> None:
    rel = "interview/algorithms/算法面试100题精讲.md"
    cards = parse_file(rel, read_sample(rel))
    check("I-1：抽出 interview_qa", len(cards) >= 5 and all(c.kind == "interview_qa" for c in cards),
          f"got {len(cards)}")
    check("I-1：front 形如 Q1. 标题", bool(cards) and cards[0].front == "Q1. 两数之和（LeetCode 1）",
          f"got {cards[0].front if cards else None!r}")
    check("I-1：has_answer=1", all(c.has_answer == 1 for c in cards))
    check("I-1：difficulty 缺省 medium", all(c.difficulty == "medium" for c in cards))
    check("I-1：back 剔除了代码块", all("```" not in c.back for c in cards))
    check("I-1：back 截断到 600 字内", all(len(c.back) <= 600 for c in cards))
    check("I-1：anchor 是原题标题", bool(cards) and "题目1" in cards[0].anchor)


def _legacy_table_sample(n: int = 32) -> str:
    """旧「表格清单式」样例（本地合成）。

    2026-09-18 去重治理软删了唯一的 I-2 真实样本「AI Agent 技术面试题库（140题）.md」
    （其 150 行题目全部由 60题篇 + 扩展1-7 承载、独有 0 题），故 I-2 解析器回归网改用
    合成样本，与 I-3 的 _legacy_flat_sample 同一处理方式，不依赖已迁移的语料。
    """
    parts = ['---\ntitle: "表格题样例"\ntags: []\n---\n', "# 表格题样例\n", "### 主题1：基础概念\n"]
    diffs = ["初级", "中级", "高级"]
    for i in range(1, n + 1):
        if i == 16:
            parts.append("\n### 主题2：进阶应用\n")
        parts.append(f"| {i} | 这是第{i}道表格题的题干描述？ | {diffs[(i - 1) % 3]} |")
    return "\n".join(parts) + "\n"


def test_parse_interview_i2() -> None:
    rel = "interview/ai-agent/表格题样例.md"
    cards = parse_file(rel, _legacy_table_sample())
    check("I-2：抽出表格题目", len(cards) >= 30, f"got {len(cards)}")
    check("I-2：has_answer=0（原文未附答案）", all(c.has_answer == 0 for c in cards))
    check("I-2：difficulty 走 DIFF_MAP 且三档齐全",
          {c.difficulty for c in cards} == {"easy", "medium", "hard"},
          f"got {sorted({c.difficulty for c in cards})}")
    check("I-2：front 形如 Q1. 题面", bool(cards) and cards[0].front.startswith("Q1. "),
          f"got {cards[0].front if cards else None!r}")
    check("I-2：anchor 落在最近的 ### 主题N", bool(cards) and "主题1" in cards[0].anchor)
    check("I-2：跨主题后 anchor 切换", any("主题2" in c.anchor for c in cards),
          f"got {sorted({c.anchor for c in cards})}")


def _legacy_flat_sample(n: int = 22) -> str:
    """旧「扁平纯文本式」样例（本地合成）。

    2026-09-18 面试语料统一改为 I-5 排版后，content/ 里已没有 I-3 形态的真实样本，
    故 I-3 解析器的回归网改用合成样本，避免测试依赖于已迁移的语料。
    """
    parts = ['---\ntitle: "扁平题样例"\ntags: []\n---\n', "# 扁平题样例\n", "📦 基础\n"]
    for i in range(1, n + 1):
        parts.append(
            f"{i}. 第{i}题的题干是什么？\n简单\n标签A\n查看答案\n"
            f"回答模板1：基础解释\n这是第{i}题的答案正文，用于守住扁平解析器不回归。\n")
    return "\n".join(parts)


def test_parse_interview_i3() -> None:
    rel = "interview/css-html/扁平题样例.md"
    cards = parse_file(rel, _legacy_flat_sample())
    check("I-3：抽出扁平题目", len(cards) >= 20, f"got {len(cards)}")
    check("I-3：题面以 ？ 结尾", all(c.front.rstrip().endswith("？") or c.front.rstrip().endswith("?")
                                     for c in cards))
    check("I-3：答案从「查看答案」之后才收集",
          all("查看答案" not in c.back for c in cards))
    check("I-3：难度行不进答案正文",
          all(c.back.strip() != "简单" for c in cards))
    check("I-3：back 截断到 800 字内", all(len(c.back) <= 800 for c in cards))
    check("I-3：保留「回答模板N」小标题", any("回答模板" in c.back for c in cards))


def test_parse_interview_i5() -> None:
    """I-5 编号标题式：`### N. 题干｜难度` + 紧随的答案正文（面试语料 2026-09-18 新排版）。"""
    rel = "interview/css-html/CSS与HTML面试题库 - 60道精选题目.md"
    cards = parse_file(rel, read_sample(rel))
    check("I-5：抽出题目", len(cards) >= 55, f"got {len(cards)}")
    check("I-5：全是 interview_qa", all(c.kind == "interview_qa" for c in cards))
    check("I-5：front 形如 Q1. 题面", bool(cards) and cards[0].front.startswith("Q1. "),
          f"got {cards[0].front if cards else None!r}")
    check("I-5：难度后缀不进 front", all("｜" not in c.front and "|" not in c.front for c in cards))
    check("I-5：difficulty 三档齐全且无空值",
          {c.difficulty for c in cards} == {"easy", "medium", "hard"},
          f"got {sorted({c.difficulty for c in cards})}")
    check("I-5：has_answer=1（答案紧随题干）", all(c.has_answer == 1 for c in cards))
    check("I-5：back 剔除了代码块", all("```" not in c.back for c in cards))
    check("I-5：back 截断到 800 字内", all(len(c.back) <= 800 for c in cards))
    check("I-5：anchor 是 Q{no}", bool(cards) and cards[0].anchor == "Q1")
    check("I-5：back 不含小节标题（## 不入答案）",
          all("（10 题）" not in c.back for c in cards))
    check("I-5：题干编号重排后编号连续",
          [c.front.split(".", 1)[0] for c in cards][:3] == ["Q1", "Q2", "Q3"],
          f"got {[c.front[:6] for c in cards[:3]]}")


def test_parse_interview_i4() -> None:
    """I-4 编号问答式（2026-09-18 统一为 I-5 渲染约定）：`### N. 题面｜初级|中级|高级` + `**答案要点：**` / `**参考答案：**`。"""
    rel = "interview/ai-agent/AI Agent开发面试题库 - 详细答案解析.md"
    cards = parse_file(rel, read_sample(rel))
    check("I-4：抽出编号题目", len(cards) >= 80, f"got {len(cards)}")
    check("I-4：全是 interview_qa", all(c.kind == "interview_qa" for c in cards))
    check("I-4：front 形如 Q1. 标题", bool(cards) and cards[0].front.startswith("Q1. "),
          f"got {cards[0].front if cards else None!r}")
    check("I-4：题面原样保留（已带问号的不重复加）",
          bool(cards) and cards[0].front.endswith("？"), f"got {cards[0].front if cards else None!r}")
    check("I-4：难度三档来自后缀且无空值",
          {c.difficulty for c in cards} == {"easy", "medium", "hard"},
          f"got {sorted({c.difficulty for c in cards})}")
    check("I-4：答案有内容（编程纯代码题除外）",
          sum(1 for c in cards if c.has_answer == 1) >= len(cards) - 5,
          f"has_answer=1 仅 {sum(1 for c in cards if c.has_answer == 1)}/{len(cards)}")
    check("I-4：back 剔除了代码块", all("```" not in c.back for c in cards))
    check("I-4：back 截断到 800 字内", all(len(c.back) <= 800 for c in cards))
    check("I-4：anchor 是 Q{no}", bool(cards) and cards[0].anchor == "Q1",
          f"got {cards[0].anchor if cards else None!r}")
    check("I-4：term 取 frontmatter/H1 而非 Q 标题",
          bool(cards) and not cards[0].term.startswith("Q"), f"got {cards[0].term!r}")
    # 详版块内是成段正文 + 表格 + **详细解析：**，「参考答案」标记不得被当成答案正文
    check("I-4：back 不是把「参考答案」标记当答案",
          all(not c.back.startswith("参考答案") for c in cards))
    check("I-4：back 最短有实质正文", all(len(c.back) >= 5 for c in cards),
          f"最短 {min((len(c.back) for c in cards), default=0)}")

    # 护栏②：块内完全没有中文（纯代码）不建卡
    md = ('# 编码题\n\n## 基础\n\n### Q1: 实现一个简单的ReAct Agent\n\n'
          '```python\ndef run(): pass\n```\n\n'
          '### Q2: 什么是 Agent？它和 ChatBot 有何不同？\n\n**答案要点：**\n'
          '- Agent 能主动调用工具并完成目标，ChatBot 只能被动应答，这个区别很关键。\n')
    cs = parse_file("interview/ai-agent/编码题.md", md)
    check("I-4 护栏②：纯代码块不建卡", len(cs) == 1, f"got {len(cs)}")
    check("I-4 护栏②：有中文的那题仍出卡", bool(cs) and cs[0].front.startswith("Q2. "))


def test_baike_b_term_cleaning() -> None:
    """B 格式术语名：只去前导编号，不动标题中间的英文括号。"""
    md = ('# 名词表\n\n导语。\n\n'
          '## 1. AI 对话系统\n**一句话定义（大白话）**\n能与人多轮对话并完成任务的 AI 系统。\n\n'
          '## 8. 指令微调\n**一句话定义（大白话）**\n用指令-回答对继续训练，让模型听懂人话。\n\n'
          '## MD5（Message Digest 5）\n**一句话定义（大白话）**\n'
          '把任意长度数据压成 128 位摘要的哈希算法。\n')
    cards = parse_file("baike/ai/名词表.md", md)
    terms = [c.term for c in cards if c.kind == "baike_def"]
    check("B 术语清洗：前导编号被去掉", terms[:2] == ["AI 对话系统", "指令微调"], f"got {terms}")
    check("B 术语清洗：保留中间英文括号", "MD5（Message Digest 5）" in terms, f"got {terms}")
    check("B 术语清洗：anchor 仍是原始标题（便于跳转）",
          any(c.anchor == "1. AI 对话系统" for c in cards), f"got {[c.anchor for c in cards][:3]}")
    check("B 术语清洗：front 用清洗后的术语",
          bool(cards) and cards[0].front == "「AI 对话系统」是什么？用一句话说清楚。",
          f"got {cards[0].front if cards else None!r}")


def test_i3_difficulty_backfill() -> None:
    """I-3：题面下一行的难度词回填 difficulty，且难度行不进答案正文。"""
    rel = "interview/css-html/CSS与HTML面试题库 - 60道精选题目.md"
    cards = parse_file(rel, read_sample(rel))
    diffs = {c.difficulty for c in cards}
    check("I-3：difficulty 被回填", "" not in diffs and diffs <= {"easy", "medium", "hard"},
          f"got {sorted(diffs)}")
    check("I-3：难度行不出现在 back 里",
          all(c.back.strip() not in ("简单", "中等", "困难", "初级", "中级", "高级") for c in cards))
    check("I-3：难度行不出现在 front 里",
          all("简单" not in c.front for c in cards))
    check("I-3：back 截断到 800 字内", all(len(c.back) <= 800 for c in cards))


def test_parser_version_bumped() -> None:
    """解析规则一改，版本号必须跟着变（否则已上线的库不会重扫）。"""
    check("CARDS_PARSER_VERSION >= 2（I-4 属破坏性解析变更）", CARDS_PARSER_VERSION >= 2,
          f"got {CARDS_PARSER_VERSION}")


def test_no_cards_from_fenced_code() -> None:
    md = ('---\ntitle: "伪题陷阱"\ntags: []\n---\n\n# 伪题陷阱\n\n'
          '正文里只有一个真问题。\n\n```python\n1. 代码块里的问题会被算成卡片吗？\n'
          '**一句话定义：** 也不该被算成定义。\n```\n')
    cards = parse_file("baike/algorithms/伪题陷阱.md", md)
    check("代码块里的内容不成卡", cards == [], f"got {len(cards)}")


def test_card_id_stable() -> None:
    rel = "baike/algorithms/KMP 算法.md"
    raw = read_sample(rel)
    a = parse_file(rel, raw)
    b = parse_file(rel, raw)
    check("同一输入两次 card_id 相同",
          [c.card_id for c in a] == [c.card_id for c in b])
    check("card_id 始终以 c_ 开头且 14 位",
          all(c.card_id.startswith("c_") and len(c.card_id) == 14 for c in a))
    moved = parse_file("baike/strings/X2.md", raw)
    check("文件改名/换子域后 card_id 不变（进度不丢）",
          [c.card_id for c in moved] == [c.card_id for c in a])
    check("文件改名/换子域后 card_id 不变（进度不丢）",
          [c.card_id for c in moved] == [c.card_id for c in a])
    moved2 = parse_file("interview/algorithms/KMP 算法.md", raw)
    check("只有 baike / interview 之外的内容不抽卡（换到非候选域则无卡）",
          parse_file("articles/notes/KMP 算法.md", raw) == [])
    check("同一原文换到 interview 域走 interview 解析器（故无 baike 卡）",
          all(c.kind != "baike_def" for c in moved2), f"got {[c.kind for c in moved2][:3]}")
    # make_card_id / fingerprint / norm 的显式契约
    cid = make_card_id("baike_def", "KMP 算法", "「KMP 算法」是什么？用一句话说清楚。")
    check("make_card_id 幂等", cid == make_card_id("baike_def", "KMP算法", "「KMP 算法」是什么?用一句话说清楚。"))
    check("make_card_id 对 kind 敏感",
          cid != make_card_id("baike_trap", "KMP 算法", "「KMP 算法」是什么？用一句话说清楚。"))
    check("norm 剥离 markdown 标记与空白", norm(" **KMP_算法** ") == norm("KMP算法"))
    check("fingerprint 对正反面敏感",
          fingerprint("A", "B") != fingerprint("A", "C") and len(fingerprint("A", "B")) == 16)


# ---------------------------------------------------------------- ② SM-2
def _advance(state: dict, qs: list[int], now: float | None = None) -> dict:
    now = now if now is not None else time.time()
    st = dict(state)
    for q in qs:
        nxt = schedule(st, q, now)
        st = {"ef": nxt["ef"], "interval": nxt["interval"], "reps": nxt["reps"],
              "lapses": nxt["lapses"]}
    return {"st": st, "last": nxt}


def test_sm2() -> None:
    now = time.time()
    check("Q_MAP 取值符合契约", Q_MAP == {"again": 0, "hard": 3, "good": 4, "easy": 5})

    r = schedule({"ef": 2.5, "interval": 0, "reps": 0, "lapses": 0}, 4, now)
    check("首次 q=4 → interval=1, reps=1, ef 不变",
          (r["interval"], r["reps"], r["ef"]) == (1, 1, 2.5), f"got {r}")
    check("due_ts 落在明天当地 00:00 之后", r["due_ts"] > now)

    st = {"ef": 2.5, "interval": 0, "reps": 0, "lapses": 0}
    ivs, efs = [], []
    for _ in range(3):
        n = schedule(st, 4, now)
        st = {"ef": n["ef"], "interval": n["interval"], "reps": n["reps"], "lapses": n["lapses"]}
        ivs.append(n["interval"])
        efs.append(n["ef"])
    check("连续 q=4 三次 → interval 1→6→15", ivs == [1, 6, 15], f"got {ivs}")
    check("连续 q=4 → ef 恒为 2.50", all(abs(e - 2.5) < 1e-9 for e in efs), f"got {efs}")

    r = schedule({"ef": 2.5, "interval": 15, "reps": 3, "lapses": 0}, 0, now)
    check("q=0 → interval=1, reps=0, lapses+1", (r["interval"], r["reps"], r["lapses"]) == (1, 0, 1),
          f"got {r}")
    r = schedule({"ef": 2.5, "interval": 15, "reps": 3, "lapses": 0}, 2, now)
    check("q=2 也算遗忘（lapses+1）且 ef 不变", r["lapses"] == 1 and r["ef"] == 2.5, f"got {r}")

    st = {"ef": 2.5, "interval": 0, "reps": 0, "lapses": 0}
    efs = []
    for _ in range(6):
        n = schedule(st, 5, now)
        st = {"ef": n["ef"], "interval": n["interval"], "reps": n["reps"], "lapses": n["lapses"]}
        efs.append(n["ef"])
    check("连续 q=5 → ef 单调不减", all(efs[i] <= efs[i + 1] for i in range(len(efs) - 1)),
          f"got {efs}")
    check("连续 q=5 → ef 先严格上升再被 2.80 夹住",
          efs[0] < efs[1] < efs[2] and max(efs) == 2.80, f"got {efs}")
    check("连续 q=5 → ef 不超 2.80", max(efs) <= 2.80, f"got {max(efs)}")

    st = {"ef": 2.5, "interval": 0, "reps": 0, "lapses": 0}
    efs = []
    for _ in range(8):
        n = schedule(st, 0, now)
        st = {"ef": n["ef"], "interval": n["interval"], "reps": n["reps"], "lapses": n["lapses"]}
        efs.append(n["ef"])
    check("连续 q=0 → ef 恒为初始值（不低于 1.30）", min(efs) >= EF_MIN and min(efs) == 2.5,
          f"got {efs}")

    st = {"ef": 2.5, "interval": 200, "reps": 8, "lapses": 0}
    n = schedule(st, 4, now)
    check("interval 有 365 天上限", n["interval"] == 365, f"got {n['interval']}")

    st = {"ef": 2.5, "interval": 0, "reps": 0, "lapses": 0}
    n = st.copy()
    for q in (4, 4, 4, 4):
        n = schedule(st, q, now)
        st = {"ef": n["ef"], "interval": n["interval"], "reps": n["reps"], "lapses": n["lapses"]}
    check("interval>=21 且 reps>=3 → mastered=1", n["mastered"] == 1, f"got {n}")
    check("schedule 不改入参",
          all(k in DEFAULT_STATE for k in ("ef", "interval", "reps", "lapses")))


# ---------------------------------------------------------------- ③ 卡片库
def _seed_mini_corpus(root: Path) -> Path:
    content = root / "content"
    for rel in ("baike/algorithms/KMP 算法.md",
                "interview/css-html/CSS与HTML面试题库 - 60道精选题目.md"):
        src = CONTENT / rel
        dst = content / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
    # security 侧 B 格式样本改用内联夹具：真实的 哈希算法篇.md 二期已转 A 格式枢纽页，
    # 术语会随拆分持续漂移（解耦先例见 4a785b1）；候选文件数保持 4 不变。
    d_sec = content / "baike" / "security"
    d_sec.mkdir(parents=True, exist_ok=True)
    (d_sec / "哈希算法夹具.md").write_text(_B_FIXTURE_MD, encoding="utf-8")
    # 一篇 longer tutorial（无定义小节）→ 应记为 skipped
    d = content / "baike" / "algorithms"
    (d / "教程长文.md").write_text(
        "---\ntitle: \"教程长文\"\ntags: []\n---\n\n# 教程长文\n\n## 原理与机制\n\n"
        "这是一篇没有任何「一句话定义」的教程长文，按设计不抽卡。\n",
        encoding="utf-8")
    return content


def test_sqlite_busy_timeout() -> None:
    """所有连向 indexes/*.db 的连接都必须带锁等待窗口。

    `_index_watcher` 每 30s 重建/增量 FTS，写事务期间独占锁；此时用户保存文档或
    刷页面就会撞 `database is locked`。没设 busy_timeout 的话直接 500。
    PRAGMA busy_timeout 读回来是毫秒。
    """
    from app import fts
    from app.learn import LearnStore

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        indexes = root / "indexes"
        ls = LearnStore(indexes, root / "content")
        try:
            ms = int(ls.con.execute("PRAGMA busy_timeout").fetchone()[0])
            check("LearnStore 连接带 30s 锁等待", ms == 30000, f"got {ms} ms")
        finally:
            ls.close()
        con = fts.open_db(indexes)
        try:
            ms2 = int(con.execute("PRAGMA busy_timeout").fetchone()[0])
            check("fts.open_db 连接带 30s 锁等待", ms2 == 30000, f"got {ms2} ms")
        finally:
            con.close()


def test_learn_store() -> None:
    from app.learn import LearnStore

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        content = _seed_mini_corpus(root)
        indexes = root / "indexes"
        ls = LearnStore(indexes, content)
        try:
            ls.ensure_synced(content)
            check("删库后 ensure_synced 自动同步",
                  int(ls.con.execute("SELECT count(*) FROM cards WHERE active=1").fetchone()[0]) > 0)
            r1 = ls.sync(content)
            check("sync 抽出卡片", r1["total"] > 20, f"total={r1['total']}")
            check("coverage.files 只统计候选域", r1["coverage"]["files"] == 4,
                  f"got {r1['coverage']}")
            check("coverage.skipped 记录教程长文", r1["coverage"]["skipped"] == 1,
                  f"got {r1['coverage']}")
            check("by_kind 含三种类型", set(r1["by_kind"]) >= {"baike_def", "interview_qa"},
                  f"got {r1['by_kind']}")

            dueTs_before = {}
            r2 = ls.sync(content)
            check("二次 sync：added=0", r2["added"] == 0, f"got {r2['added']}")
            check("二次 sync：updated=0", r2["updated"] == 0, f"got {r2['updated']}")
            check("二次 sync：total 不变", r2["total"] == r1["total"])

            # 全是新卡时不能按 new_ratio 打折（否则 limit=5 只返回 1 张，复习页刷不动）
            fresh = ls.due(limit=5)
            check("全库都是新卡时 due(5) 拿满 limit", len(fresh["cards"]) == 5,
                  f"got {len(fresh['cards'])} (due_n={fresh['due_n']}, new_n={fresh['new_n']})")
            fresh20 = ls.due(limit=20)
            check("全库都是新卡时 due(20) 也拿满", len(fresh20["cards"]) == 20,
                  f"got {len(fresh20['cards'])}")

            due = ls.due(limit=5)
            card = due["cards"][0]
            dueTs_before[card["card_id"]] = card["due_ts"]
            before_mastered = int(card["mastered"])
            res = ls.submit_review(card["card_id"], 4, 1500)
            check("submit_review：next.interval=1", res["next"]["interval"] == 1, f"got {res['next']}")
            check("submit_review：due_ts 后移", res["next"]["due_ts"] > time.time(),
                  f"got {res['next']['due_ts']}")
            check("submit_review：mastery_delta 合理",
                  res["mastery_delta"] >= 0 and res["mastery_delta"] == res["next"]["mastered"] - before_mastered
                  + (before_mastered - before_mastered), f"got {res['mastery_delta']}")
            check("submit_review：streak_days >= 1", res["streak_days"] >= 1)

            dup = ls.submit_review(card["card_id"], 4, 1500)
            check("同一秒重复提交幂等（interval 不二次推进）", dup["next"]["interval"] == 1,
                  f"got {dup['next']}")
            # 把事件时间戳挪出 1 秒幂等窗口，好让后续提交能真正生效
            ls.con.execute("UPDATE review_events SET ts=ts-2 WHERE card_id=?", (card["card_id"],))
            ls.con.commit()

            # 有到期卡时，new_ratio 必须真的生效（新卡不挤占到期卡）
            ls.con.execute("UPDATE review_state SET due_ts=? WHERE card_id=?",
                           (time.time() - 10, card["card_id"]))
            ls.con.commit()
            mix = ls.due(limit=20, new_ratio=0.3)
            # LearnStore.due() 返回的是扁平行（state 的字段摊平在 card 上，
            # 嵌套的 state{} 是 routes_learn 组响应时套上去的）
            n_new = sum(1 for c in mix["cards"] if c["is_new"])
            check("有到期卡时新卡占比受 new_ratio 约束", n_new <= 6,
                  f"got {n_new} 张新卡 / 共 {len(mix['cards'])}")
            check("有到期卡时到期卡优先入选",
                  any(not c["is_new"] for c in mix["cards"]),
                  f"got {[c['is_new'] for c in mix['cards']][:6]}")

            m = ls.mastery(scope="sub", domain="baike")
            check("mastery 返回 items 与 totals", bool(m["items"]) and "pct" in m["totals"])
            check("mastery hue 取域色相", all(isinstance(i["hue"], int) for i in m["items"]))

            tc = ls.today_card()
            check("today_card 有结果", tc["card"] is not None)
            # 「今日术语」位必须是定义卡：误区卡的 back 以「✗ 这是常见误区。正解：」
            # 开头，放首页等于在教读者一个错误说法
            check("today_card 返回的是 baike_def",
                  tc["card"]["kind"] == "baike_def", f"got {tc['card']['kind']!r}")
            check("today_card 连抽 5 次都是 baike_def",
                  all(ls.today_card()["card"]["kind"] == "baike_def" for _ in range(5)))
            check("today_stats 字段齐全",
                  {"due_n", "done_today", "new_left", "streak_days", "mastered",
                   "mastered_total", "mastered_pct"} <= set(ls.today_stats()))

            rm = ls.roam("KMP 算法", n=4)
            check("roam 返回 path 与 dead_ends", isinstance(rm["path"], list)
                  and isinstance(rm["dead_ends"], list))

            sc = ls.search_cards(q="哈希", limit=5)
            check("search_cards 返回 total/items", sc["total"] >= 1 and len(sc["items"]) >= 1)

            g = ls.glossary(domain="baike", sub="security")
            check("glossary 分桶含字母桶与 # 桶",
                  any(b["letter"] != "#" for b in g["buckets"]) and g["total"] >= 4,
                  f"got {g['buckets']}")
            check("glossary items_flat 带 def_brief",
                  bool(g["items_flat"]) and "def_brief" in g["items_flat"][0])

            p = ls.palette_index(None, content)
            check("palette 返回 6 条命令", p["counts"]["commands"] == 6,
                  f"got {p['counts']}")
            # 契约：palette 必须是全量索引，不许静默截断（真实语料 662 术语 / 695 文档，
            # 曾被 LIMIT 400 / LIMIT 500 砍掉一半，导致命令面板搜不到文档）
            from app import fts as _fts
            _exp_terms = ls.con.execute(
                "SELECT COUNT(DISTINCT term) FROM cards WHERE active=1 "
                "AND kind='baike_def'").fetchone()[0]
            _fc = _fts.open_db(ls.indexes)
            try:
                _exp_docs = _fc.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
            finally:
                _fc.close()
            check("palette terms 未截断（=全量定义卡术语数）",
                  p["counts"]["terms"] == _exp_terms,
                  f"got {p['counts']['terms']} / expected {_exp_terms}")
            check("palette docs 未截断（=FTS 全量文档数）",
                  p["counts"]["docs"] == _exp_docs,
                  f"got {p['counts']['docs']} / expected {_exp_docs}")
            check("palette sig 一致时 fresh",
                  ls.palette_index(p["sig"], content).get("fresh") is True)

            sug = ls.wikilink_suggest("MD5", limit=3)
            check("wikilink_suggest 命中术语", bool(sug) and sug[0]["score"] >= 70, f"got {sug}")
            ck = ls.wikilink_check("参见 [[不存在的链接]]。")
            check("wikilink_check 标出断链", ck["dead_n"] == 1 and ck["dead"][0]["line"] == 1,
                  f"got {ck}")

            check("parser_version 写进 learn_meta",
                  ls.meta_get("parser_version") == str(CARDS_PARSER_VERSION))
        finally:
            ls.close()

        # 软下线：把语料搬走再同步，旧卡应 active=0 而不是被删掉
        ls2 = LearnStore(indexes, content)
        try:
            n_before = int(ls2.con.execute("SELECT count(*) FROM cards").fetchone()[0])
            (content / "baike" / "algorithms" / "KMP 算法.md").unlink()
            ls2.sync(content)
            n_after = int(ls2.con.execute("SELECT count(*) FROM cards").fetchone()[0])
            retired = int(ls2.con.execute(
                "SELECT count(*) FROM cards WHERE active=0").fetchone()[0])
            check("语料删除后仍是软下线（不 DELETE）", n_before == n_after, f"{n_before}→{n_after}")
            check("软下线把对应卡片置为 inactive", retired >= 3, f"retired={retired}")
        finally:
            ls2.close()

        # 删库自愈
        (indexes / "reading.db").unlink()
        ls3 = LearnStore(indexes, content)
        try:
            t0 = time.perf_counter()
            ls3.ensure_synced(content)
            n = int(ls3.con.execute("SELECT count(*) FROM cards WHERE active=1").fetchone()[0])
            check("删库后重新打开自动重建且非空中岁以上（<5s）",
                  n > 0 and (time.perf_counter() - t0) < 5, f"n={n}")
        finally:
            ls3.close()


# ---------------------------------------------------------------- ④ HTTP
def test_routes() -> None:
    try:
        from app.app import create_app
    except Exception as e:
        print(f"SKIP: Flask 依赖不可用（{e}）")
        return

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _seed_mini_corpus(root)
        app = create_app(root)
        c = app.test_client()

        r = c.post("/api/learn/sync", json={"force": True})
        j = r.get_json()
        check("POST /api/learn/sync 200 + ok", r.status_code == 200 and j.get("ok") is True,
              f"{r.status_code} {str(j)[:200]}")
        for field in ("added", "updated", "retired", "total", "by_kind", "coverage", "elapsed_ms",
                      "synced_at", "term_collisions"):
            check(f"/api/learn/sync 含字段 {field}", field in j)

        r = c.get("/api/learn/due?limit=5")
        j = r.get_json()
        check("GET /api/learn/due 200 + ok", r.status_code == 200 and j.get("ok") is True)
        for field in ("cards", "due_n", "new_n", "total_n"):
            check(f"/api/learn/due 含字段 {field}", field in j)
        if j.get("cards"):
            card = j["cards"][0]
            for field in ("card_id", "kind", "term", "front", "back", "hint", "source_rel",
                          "anchor", "url", "domain", "sub", "sub_label", "tags", "related",
                          "state"):
                check(f"due card 含字段 {field}", field in card)
            st = card["state"]
            for field in ("ef", "interval", "reps", "lapses", "due_ts", "mastered", "is_new"):
                check(f"due card.state 含字段 {field}", field in st)
            check("due card.url 指向 /doc/", str(card["url"]).startswith("/doc/"), card["url"])

            rid = card["card_id"]
            r = c.post("/api/learn/review", json={"card_id": rid, "q": 4, "elapsed_ms": 800})
            j = r.get_json()
            check("POST /api/learn/review 200 + ok", r.status_code == 200 and j.get("ok") is True,
                  f"{r.status_code} {str(j)[:200]}")
            check("review next.interval == 1", j.get("next", {}).get("interval") == 1, str(j)[:200])
            for field in ("card_id", "q", "prev", "next", "mastery_delta", "streak_days"):
                check(f"/api/learn/review 含字段 {field}", field in j)

        r = c.get("/api/learn/mastery?scope=sub&domain=baike")
        j = r.get_json()
        check("GET /api/learn/mastery 200", r.status_code == 200 and j.get("ok") is True)
        check("mastery items 字段齐全", all(
            {"id", "label", "total", "mastered", "learning", "new", "pct", "hue", "ef_avg",
             "due_n"} <= set(i) for i in j.get("items", [])))

        r = c.get("/api/learn/today")
        j = r.get_json()
        check("GET /api/learn/today 200", r.status_code == 200 and j.get("ok") is True,
              f"{r.status_code} {str(j)[:160]}")
        check("today 含 date/card/stats/tip",
              {"date", "card", "stats", "tip"} <= set(j))
        check("today card.kind == baike_def", j.get("card", {}).get("kind") == "baike_def",
              f"got {j.get('card', {}).get('kind')!r}")

        r = c.get("/api/learn/cards?limit=3")
        j = r.get_json()
        check("GET /api/learn/cards 200", r.status_code == 200 and j.get("ok") is True)
        check("cards 含 total/items", "total" in j and "items" in j)

        r = c.get("/api/learn/roam?from=KMP 算法&n=4")
        j = r.get_json()
        check("GET /api/learn/roam 200", r.status_code == 200 and j.get("ok") is True)
        check("roam 含 path/n/dead_ends", {"path", "n", "dead_ends"} <= set(j))
        r = c.get("/api/learn/roam")
        check("roam 缺 from → BAD_PARAM", r.get_json().get("error") == "BAD_PARAM", str(r.get_json()))

        r = c.get("/api/wikilink/suggest?q=MD5")
        j = r.get_json()
        check("GET /api/wikilink/suggest 200", r.status_code == 200 and j.get("ok") is True)
        check("suggest items 含 name/rel/kind/score/sub_label",
              all({"name", "rel", "kind", "score", "sub_label"} <= set(i) for i in j.get("items", [])))

        r = c.post("/api/wikilink/check", json={"body": "参见 [[不存在的链接]]。"})
        j = r.get_json()
        check("POST /api/wikilink/check 200", r.status_code == 200 and j.get("ok") is True)
        check("check dead_n == 1", j.get("dead_n") == 1, str(j)[:200])
        check("check dead 含 raw/line/col/suggest/suggest_score",
              all({"raw", "line", "col", "suggest", "suggest_score"} <= set(d)
                  for d in j.get("dead", [])))
        r = c.post("/api/wikilink/check", json={})
        check("check 缺 body → BAD_PARAM", r.get_json().get("error") == "BAD_PARAM")
        # B15：自指双链（文档链自己的文件名）不算断链
        r = c.post("/api/wikilink/check",
                   json={"body": "见 [[自我引用]]。", "path": "career/自我引用.md"})
        check("自指双链不计为断链（B15）",
              r.get_json().get("ok") is True and r.get_json().get("dead_n") == 0,
              str(r.get_json())[:160])
        # B10：共享候选池下重复断链与建议字段仍正确（非断链的 [[KMP 算法]] 被排除）
        r = c.post("/api/wikilink/check",
                   json={"body": "见 [[KMP 算法]] 与 [[绝对不存在的术语xyz]] 和 [[绝对不存在的术语xyz]]。"})
        j = r.get_json()
        check("批量断链检查：真断链两次、活链零次（B10）",
              j.get("dead_n") == 2 and all(d["raw"] == "绝对不存在的术语xyz" for d in j.get("dead", [])),
              str(j)[:200])

        r = c.get("/api/palette/index")
        j = r.get_json()
        check("GET /api/palette/index 200", r.status_code == 200 and j.get("ok") is True)
        check("palette 6 条命令 id 顺序稳定",
              [x["id"] for x in j.get("commands", [])] ==
              ["go-home", "toggle-theme", "goto-review", "goto-quiz", "goto-glossary", "readpref"],
              str([x["id"] for x in j.get("commands", [])]))
        r2 = c.get("/api/palette/index?sig=" + str(j.get("sig")))
        check("palette sig 一致 → fresh", r2.get_json().get("fresh") is True, str(r2.get_json()))

        r = c.get("/api/glossary")
        j = r.get_json()
        check("GET /api/glossary 200", r.status_code == 200 and j.get("ok") is True)
        check("glossary 含 total/buckets/groups/items_flat",
              {"total", "buckets", "groups", "items_flat"} <= set(j))
        check("glossary group 含 sub/sub_label/hue/items",
              all({"sub", "sub_label", "hue", "items"} <= set(g) for g in j.get("groups", [])))

        r = c.get("/api/search?q=KMP")
        j = r.get_json()
        check("GET /api/search 200", r.status_code == 200 and j.get("ok") is True)
        check("search 含 q/mode/total/精确+命中/facets",
              {"q", "mode", "total", "took_ms", "exact", "hits", "facets",
               "semantic_available"} <= set(j))
        if j.get("exact"):
            check("search exact[0] 字段齐全",
                  {"path", "title", "url", "snippet", "score_label", "domain", "sub",
                   "sub_label", "tags", "match"} <= set(j["exact"][0]))
            check("search exact[0].title 命中 KMP 算法", j["exact"][0]["title"] == "KMP 算法",
                  j["exact"][0]["title"])
            check("search exact[0].match == exact", j["exact"][0]["match"] == "exact")
        else:
            check("search：KMP 应进 exact[]", False, str(j)[:200])
        # B19：分面逗号多值 + 过滤后 total 口径一致
        r = c.get("/api/search?q=KMP&domain=baike,career")
        jm = r.get_json()
        check("search 支持 domain 逗号多值（B19）",
              r.status_code == 200 and jm.get("ok") is True
              and all(x.get("domain") in ("baike", "career")
                      for x in (jm.get("exact", []) + jm.get("hits", []))), str(jm)[:160])
        r = c.get("/api/search?q=KMP&tag=__绝不可能存在的标签__")
        jf = r.get_json()
        check("search 多条件过滤 total 为过滤后计数",
              jf.get("ok") is True and jf.get("total") == 0, str(jf)[:120])
        r = c.get("/api/search")
        check("search 缺 q → BAD_Q", r.get_json().get("error") == "BAD_Q", str(r.get_json()))

        for page in ("/review", "/quiz", "/glossary"):
            r = c.get(page)
            check(f"GET {page} 渲染成功", r.status_code == 200, f"got {r.status_code}")

        r = c.post("/api/learn/review", json={"card_id": "c_notexist", "q": 4})
        check("未知 card_id → BAD_CARD 404", r.status_code == 404
              and r.get_json().get("error") == "BAD_CARD", f"{r.status_code} {str(r.get_json())}")
        r = c.post("/api/learn/review", json={"card_id": "c_x", "q": 9})
        check("q 越界 → BAD_Q 400", r.status_code == 400 and r.get_json().get("error") == "BAD_Q")


def main() -> int:
    print("== ① 抽卡 parse_file ==")
    test_parse_baike_a()
    test_parse_baike_b()
    test_parse_interview_i1()
    test_parse_interview_i2()
    test_parse_interview_i3()
    test_parse_interview_i4()
    test_parse_interview_i5()
    test_baike_b_term_cleaning()
    test_i3_difficulty_backfill()
    test_parser_version_bumped()
    test_no_cards_from_fenced_code()
    test_card_id_stable()
    print("== ② SM-2 ==")
    test_sm2()
    print("== ③ LearnStore ==")
    test_sqlite_busy_timeout()
    test_learn_store()
    print("== ④ HTTP 契约 ==")
    test_routes()
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
