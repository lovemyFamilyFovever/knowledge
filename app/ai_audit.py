# -*- coding: utf-8 -*-
"""单篇查漏补缺（切片 3）—— 本地判据先跑，AI 只做"本地算不出来、又必须判断"的那部分。

分工是刻意的（AGENTS 不变量 9 + 用户对成本透明度的要求）：
  · **本地能算的一律不问 API**：frontmatter 缺项、标题层级跳跃、围栏未闭合、空小节、
    疑似截断、失效双链、超长段落、图片路径不存在 —— 这些都有确定答案，问 AI 只会花钱和引入噪声。
  · **本地给候选，AI 只判相关性**：「应引未引」用全库标题集合算出候选词，AI 判断
    "这里到底该不该做成链接"（同一个词可能是普通用语）。
  · **求职域也能查，但只查本地**：career/interview 不出站（不变量 9 ①），
    所以这些文档拿到的是"本地那一半"结果 + 一条"AI 判断未启用"的如实说明，
    而不是假装查全了。

每条建议都带 **evidence**（本地算出来的那个数字/那一行），光有结论的建议不予展示 ——
这是 spec 第 9 节写下的规矩：AI 判定天然有噪声，用户必须能核对它凭什么这么说。
"""
import hashlib
import re
from pathlib import Path

from app import ai_qa

AI_CHECK_KINDS = {"should_link", "possibly_outdated"}

# 句末标点：中日英混排都算，避免把正常的英文句号判成"截断"
_END_PUNCT = "。！？!?”\"'）)】]》>·…—-、,，;；:：`|*"

_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
_MD_LINK_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")

FM_FIELDS = ("title", "source", "collected", "tags", "status")

SEVERITY = {"high": "会影响阅读或检索", "medium": "结构/完整性问题", "low": "可选优化"}
# 域级建议（覆盖空白）挂在派生库的"作用域键"下，而不是某一篇文档上：
# 真实相对路径永远不会以 @ 开头，所以两类条目天然同住一表而不串台。
DOMAIN_PREFIX = "@domain:"


def domain_scope(domain: str) -> str:
    return DOMAIN_PREFIX + str(domain or "").strip().strip("/")


def is_domain_scope(rel: str) -> bool:
    return str(rel or "").startswith(DOMAIN_PREFIX)


def _pid(kind: str, path: str, key: str = "") -> str:
    """建议 id：稳定、可重入 —— 采纳/忽略状态靠它跨次运行对上号。"""
    return hashlib.sha1(f"{kind}|{path}|{key}".encode("utf-8")).hexdigest()[:12]


def _proposal(kind, path, title, evidence, suggestion, severity="medium",
              needs_ai=False, key=""):
    return {"id": _pid(kind, path, key), "kind": kind, "title": title,
            "evidence": evidence, "suggestion": suggestion, "severity": severity,
            "needs_ai": needs_ai}


def _strip_fences(md: str) -> list:
    """返回 [(行号, 文本, 是否在围栏内)] —— 代码块里的 # 不是标题，``` 也不是正文。"""
    out, fenced = [], False
    for i, line in enumerate(md.splitlines(), 1):
        if _FENCE_RE.match(line):
            out.append((i, line, True))
            fenced = not fenced
            continue
        out.append((i, line, fenced))
    return out


def sections(md: str) -> list:
    """[{level, title, line, body_chars}]，围栏内的 # 不算标题。"""
    heads = []
    for ln, text, in_fence in _strip_fences(md):
        if in_fence:
            continue
        m = _HEADING_RE.match(text.strip())
        if m:
            heads.append({"level": len(m.group(1)), "title": m.group(2).strip(),
                          "line": ln, "body_chars": 0})
        elif heads and text.strip():
            heads[-1]["body_chars"] += len(text.strip())
    return heads


def outline(md: str, limit: int = 60) -> list:
    return [{"level": h["level"], "title": h["title"]} for h in sections(md)[:limit]]


def local_checks(md: str, *, path: str, fm: dict, known_titles=None,
                 dead_links=None, asset_exists=None) -> list:
    """全部本地判据，一条 API 都不发。"""
    out = []
    body = md
    # 1) frontmatter 缺项（不变量 6 的白名单字段）
    missing = [f for f in FM_FIELDS if not (fm or {}).get(f)]
    if missing:
        out.append(_proposal(
            "fm_missing", path, "元数据不完整",
            "缺少的字段：" + "、".join(missing),
            "补齐身世信息（source/collected 决定它从哪来、什么时候采的；tags 决定标签页能不能被归拢）",
            "low", key=",".join(missing)))

    heads = sections(md)
    prose_chars = sum(h["body_chars"] for h in heads)

    # 2) 长文却没有 ## 小节
    if prose_chars > 800 and not any(h["level"] == 2 for h in heads):
        out.append(_proposal(
            "no_h2", path, "长文没有分节",
            f"正文约 {prose_chars} 字，标题层级里没有任何 ## 小节（现有标题：{len(heads)} 个）",
            "按内容切 2~4 个 ## 小节：阅读器会把每个小节渲染成卡片，也是目录与检索的抓手",
            key="no-h2"))

    # 3) 标题层级跳跃（h1 → h3）
    skips = []
    prev = None
    for h in heads:
        if prev is not None and h["level"] - prev >= 2:
            skips.append(f"第 {h['line']} 行 {h['title']}（上一级是 h{prev}）")
        prev = h["level"]
    if skips:
        out.append(_proposal(
            "heading_skip", path, "标题层级跳跃",
            "；".join(skips[:5]),
            "层级连续（h2 下面是 h3）：跳级会让目录树和大纲出现空层，也影响导出到公开站",
            "low", key=";".join(skips[:5])))

    # 4) 空小节（标题后没有正文，且它不是"只是给子节分组"的父标题）
    #    两条豁免都是实测出来的假阳性来源：h1 就是文档标题（正文天然从第一个 h2 开始）；
    #    h2 紧跟 h3 是在给子节分组（"## 章节"下面直接分小节是正常写法，不是空节）。
    #    最后一节也要判：文档以"## 待补"收尾然后没下文，是最典型的那种空节。
    empties = []
    for i, h in enumerate(heads):
        if h["body_chars"] or h["level"] == 1:
            continue
        if i + 1 < len(heads) and heads[i + 1]["level"] > h["level"]:
            continue
        empties.append(h["title"])
    if empties:
        out.append(_proposal(
            "empty_section", path, "有空小节（只有标题没有内容）",
            "以下小节正文为空：" + "、".join(empties[:6]),
            "补内容，或先把空小节删掉 —— 空标题会进目录、进检索摘要，点进去却是空的",
            key=",".join(empties[:6])))

    # 5) 代码围栏未闭合
    fences = sum(1 for line in body.splitlines() if _FENCE_RE.match(line))
    if fences % 2:
        out.append(_proposal(
            "unclosed_fence", path, "代码围栏没有闭合",
            f"围栏标记（``` 或 ~~~）出现 {fences} 次（奇数）",
            "补上闭合的一行 —— 未闭合会让后半篇全被当成代码",
            "high", key="fence"))

    # 6) 末段疑似截断
    tail_lines = [l.strip() for l in body.rstrip().splitlines() if l.strip()]
    if tail_lines:
        last = tail_lines[-1]
        if (len(last) > 40 and last[-1] not in _END_PUNCT
                and not last.startswith(("#", "|", "-", "*", "!", ">"))):
            out.append(_proposal(
                "truncated_end", path, "结尾疑似被截断",
                "末段（" + str(len(last)) + " 字）以「…" + last[-12:] + "」收尾，没有句末标点",
                "确认是抄录时掉了尾巴，还是本来就这样；缺段落的话这条最值钱",
                key="tail"))

    # 7) 超长单段
    long_paras = 0
    for block in re.split(r"\n\s*\n", body):
        if _FENCE_RE.match(block.strip()):
            continue
        flat = block.strip()
        if "\n" not in flat and len(flat) > 600:
            long_paras += 1
    if long_paras:
        out.append(_proposal(
            "long_paragraph", path, f"有 {long_paras} 处超长段落",
            f"单段超过 600 字且中间不换行：{long_paras} 处",
            "拆段或改列表：整屏不换行的段落基本没人读完",
            "low", key="long"))

    # 8) 失效双链 + 应引未引候选（都用全库标题集合）
    #    集合先 strip 再用：索引里的标题经 cjk_clean 会带一个尾空格，
    #    而正文里的中文提及通常是"用过 向量数据库。"这样紧跟标点的 ——
    #    带着尾空格去比对就永远匹配不上，「应引未引」会成片漏报（切片 4 钓出）。
    titles = {t for t in (str(x).strip() for x in (known_titles or [])) if t}
    links = [m.group(1).strip() for m in _WIKILINK_RE.finditer(body)]
    if dead_links is not None:
        # 索引给的未解析清单口径与阅读器里的红链一致，但它是**滞后的**（watcher 才重建）。
        # 所以必须与"当前正文里真实存在的链接"取交集：否则刚把 [[X]] 删掉，
        # 面板还会拿着索引里的旧行报一条不存在的死链（切片 3 实测踩到，且会让建议 id 漂）。
        present = {l for l in links if l}
        dead = sorted({l for l in dead_links
                       if l and l.strip() in present and l.strip() not in titles})
    else:
        dead = sorted({l for l in links if l and l not in titles})
    if dead:
        out.append(_proposal(
            "dead_wikilink", path, f"{len(dead)} 条双链指向不存在的标题",
            "、".join(dead[:6]),
            "改名或建词条；也可以先转成普通文本，别让目录里一直挂着红链",
            key=",".join(dead[:6])))

    # 9) 正文里出现了全库已有词条、却没写成双链 → 只给候选，判断交给 AI
    plain = re.sub(r"\[\[[^\]]*\]\]", " ", body)   # 已经是双链的先排除
    # 自己不算候选：一篇文档的正文里必然出现它自己的标题与 h1，把它们当"该引未引"
    # 是纯粹的噪音（让人去给自己建双链毫无意义），所以先按三种身份排除：
    # frontmatter 标题、文件名、正文里的第一个 h1。
    mine = {str(fm.get("title") or "").strip().lower(),
            Path(str(path or "")).stem.strip().lower()}
    for h in heads:
        if h["level"] == 1:
            mine.add(str(h["title"]).strip().lower())
    cands = []
    for t in sorted(titles, key=len, reverse=True):
        if len(t) < 2 or t in ("index", "README") or t.lower() in mine:
            continue
        if t in plain:
            cands.append(t)
        if len(cands) >= 12:
            break
    if cands:
        out.append(_proposal(
            "should_link", path, f"{len(cands)} 个词可能该做成双链",
            "候选：" + "、".join(cands[:12]),
            "让 AI 判断哪些是真引用（同一个词可能只是普通用语），确认后再改成 [[...]]",
            "low", needs_ai=True, key=",".join(cands[:12])))

    # 10) 本地图片路径失效（需要文件系统探针，路由会给一个 exists 回调）
    if asset_exists:
        broken = [u for u in _MD_LINK_RE.findall(body)
                  if not u.startswith(("http://", "https://", "data:", "/static/"))
                  and not asset_exists(u)]
        if broken:
            out.append(_proposal(
                "missing_asset", path, f"{len(broken)} 个本地附件找不到",
                "、".join(broken[:5]),
                "图可能被搬走过；补回文件，或把引用改成实际路径（附件规范位置是 content/_assets/）",
                "high", key=",".join(broken[:5])))
    return out


def ai_prompt(kind: str, ctx_text: str, selection: str) -> str:
    """AI 只回答"这些候选里哪些是真的"，输出仍是固定 JSON schema。"""
    if kind == "coverage_gap":
        return ("下面给出一个域的标题全景（数据块内）与一批「有引用没词条」的候选空白。"
                "请逐个判断：这个概念是否**值得单独立一篇**（而不是某篇里顺带一句、"
                "或已经由现有某篇覆盖）。只把值得补的写进 terms，"
                "term 必须原样照抄候选名（不要发明新主题），brief=为什么值得补或建议并入哪一篇"
                "（不超过 60 字）；answer 用一句话说整体结论。\n\n"
                f"候选空白：{selection}\n\n{ctx_text}")
    if kind == "should_link":
        return ("下面给出本篇正文（数据块内）与一批候选词（这些词在知识库里已有同名词条）。"
                "请逐个判断：本篇里出现该词的地方，是否**确实是在指那个词条**"
                "（而不是普通用语或巧合）。只把判断为「是」的写进 terms，"
                "每项 term=候选词、brief=本篇中出现该词的那一句原文（不超过 60 字）；"
                "answer 用一句话说清整体结论。\n\n"
                f"候选词：{selection}\n\n{ctx_text}")
    return ("下面给出本篇的大纲与采集日期。请判断这篇内容里**最可能已经过时**的具体知识点"
            "（技术版本、价格、时间线、政策），逐条写进 terms（term=知识点，"
            "brief=为什么可能过时，不超过 60 字）。没有就明确说没有，不要凑数。\n\n"
            + ctx_text)


def wikilinks(md: str) -> list:
    """正文里出现过的 [[双链]] 目标原文（不去重、不判存在）。

    判定留给 `coverage_gaps` —— 这里只负责"抄下来"，好让批量线程读一篇就能同时
    喂给两个用途（本篇的死链、整个域的空白）。
    """
    return [m.group(1).strip() for m in _WIKILINK_RE.finditer(md) if m.group(1).strip()]


def coverage_gaps(refs: dict, known_titles, scope: str) -> list:
    """覆盖空白：某处写了 `[[X]]`，可全库根本没有 X 这一篇。

    全本地、零调用 —— "引用集合 − 标题集合"是算得出来的，值不值得补由人看。
    只认同名（路径式 / 别名式双链留给用户自己敲）：宁可少报，不冤枉一条好链。
    """
    titles = {str(t).strip().lower() for t in (known_titles or []) if t}
    out = []
    # 被引用越多的先报：三条以上说明"这个概念真的被用到了"，值得先补
    for target in sorted(refs, key=lambda t: (-len(set(refs[t])), t.lower())):
        norm = str(target).strip().lower()
        if not norm or norm in titles:
            continue
        srcs = sorted(set(refs[target]))
        n = len(srcs)
        row = _proposal(
            "coverage_gap", scope, f"有引用没词条：{target}",
            f"{n} 篇里写了 [[{target}]]：" + "、".join(srcs[:5]) + ("…" if n > 5 else ""),
            f"补一篇「{target}」，或者把那几处的 [[{target}]] 改回普通文字",
            "medium" if n >= 3 else "low", key=target)
        # target 只在本次请求内用于 AI 复核对号，不进派生库（库里没这一列）
        row["target"] = target
        out.append(row)
    return out


def gap_context(domain: str, titles, gaps, max_titles: int = 60) -> dict:
    """域全景复核的上下文：本域标题清单 + 候选空白名（全本地拼，不再读第二份数据）。

    标题清单包在语料数据块里 —— 它和正文一样是不可信内容，AI 侧的注入加固同一口径。
    """
    names = [str(g.get("target") or "").strip() for g in (gaps or [])]
    names = [n for n in names if n]
    tl = [str(t).strip() for t in (titles or []) if str(t).strip()]
    body = (f"域：{domain}\n本域现有篇章标题（共 {len(tl)} 篇，最多列 {max_titles} 个）：\n"
            + ai_qa.BLOCK_BEGIN + "\n" + "、".join(tl[:max_titles]) + "\n" + ai_qa.BLOCK_END
            + "\n\n候选空白：" + "、".join(names[:20]))
    return {"text": body, "chars": len(body.encode("utf-8")), "targets": names[:20]}


def narrow_gaps(gaps: list, parsed) -> list:
    """AI 复核覆盖空白：**只能在本地候选里挑**，把结论标到行上，绝不新增行。

    挑中的行带 ai_terms/ai_note；没被挑中的行如实写"AI 复核没把它列进值得补的清单"——
    这是从答复里推出来的缺席判断，不是 AI 明说的，所以措辞里点明来源。
    """
    if not parsed:
        return gaps
    picked = {}
    for it in (parsed.get("terms") or []):
        term = str(it.get("term", "")).strip()
        if term:
            picked[term.lower()] = str(it.get("brief", ""))[:120]
    conf = parsed.get("confidence", "low")
    for g in gaps:
        tgt = str(g.get("target") or "").strip().lower()
        if tgt and tgt in picked:
            g["ai_terms"] = [g.get("target")]
            g["ai_note"] = picked[tgt] or "AI 认为值得单独立一篇"
        else:
            g["ai_terms"] = []
            g["ai_note"] = "AI 复核没把它列进值得补的清单（可能是并入现有篇章，也可能只是顺带一提）"
        g["ai_confidence"] = conf
    return gaps


def merge_ai(local: list, parsed, kind: str, path: str) -> list:
    """把 AI 的结构化回答并回本地候选。

    约束：AI 只能对本地已经算出的候选**收窄**（挑出哪些是真的），不许凭空造条目 ——
    所以这条建议的 id 由本地候选集决定，AI 换一次回答不会让"已忽略"的状态失效。
    """
    if not parsed:
        return local
    hits = []
    for it in (parsed.get("terms") or []):
        term = str(it.get("term", "")).strip()
        if term:
            hits.append({"term": term[:60], "brief": str(it.get("brief", ""))[:120]})
    titles = [h["term"] for h in hits]
    cand = next((p for p in local if p["kind"] == kind), None)
    if cand:
        cand["ai_terms"] = titles
        cand["ai_note"] = parsed.get("answer", "")[:400]
        cand["ai_confidence"] = parsed.get("confidence", "low")
    return local
