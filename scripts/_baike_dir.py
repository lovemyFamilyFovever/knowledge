# -*- coding: utf-8 -*-
"""通用外科提质：对指定 baike 子目录，给缺导航/相关术语的旧稿补 导航块 + 相关术语 + 参考资料。
规则：
- 不改动 front matter 其余字段、不改动已填好的 tags、不改动正文。
- 每个 [[双链]] 目标必须是目录下真实存在的文件名（脚本断言校验）。
- 仅当真实（围栏外）H1 不唯一时，把多余顶层 # 降级为 ##；仅当代码围栏奇数时闭合。
- 幂等：已有导航块/相关术语则跳过。
用法：python _baike_dir.py <dir名> [--commit]
"""
import os, re, sys, glob

BASE = r"E:/GitHub/knowledge/content/baike"
ALL = set()  # 全局真实词条名（跨目录），供断链校验
REF_LINE = ("建议人工核验：本词条内容建议对照相关技术官方文档、权威教材与论文做准确性复核；"
            "未编造文献编号、标准号或 URL，如需引用请补充具体出处。")

# 用于挑选中心枢纽的文件名关键词（命中优先）
HUB_PAT = re.compile(r"(通用|基础|核心|概念|完全指南|入门|详解|概述|总览|实战指南|技术架构|模式|系统设计|架构|原理|深入|进阶)")

def tokenize(name):
    # 拆出中英文/数字片段作为关键词
    return set(re.findall(r"[\u4e00-\u9fff]+|[A-Za-z][A-Za-z0-9+#]*", name))

def pick_hubs(files, k=5):
    scored = []
    for f in files:
        if HUB_PAT.search(f):
            scored.append(f)
    if len(scored) >= 3:
        hubs = scored[:k]
    else:
        hubs = files[:k]
    return hubs[:k] if hubs else files[:k]

def overlap(a, b):
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb: return 0
    return len(ta & tb) / len(ta | tb)

def extract_links(lines):
    """只取围栏外（正文）的 [[双链]] 目标，避免把代码块里的 [['...']] 误判为断链。"""
    out = []
    inf = False
    for l in lines:
        if l.strip().startswith("```"):
            inf = not inf
            continue
        if inf:
            continue
        out += [m for m in re.findall(r"\[\[([^\]]+)\]\]", l) if m.strip()]
    return out

def related_for(fn, files, k=6):
    others = [f for f in files if f != fn]
    scored = sorted(others, key=lambda o: -overlap(fn, o))
    # 至少保留 k 个；若关键词重叠为 0 的也纳入尾部，保证有链接
    top = scored[:k]
    if len(top) < k and len(others) >= k:
        top = (top + others)[:k]
    return top

def process(fn, files, hubs):
    D = os.path.join(BASE, DIR)
    p = os.path.join(D, fn + ".md")
    txt = open(p, encoding="utf-8-sig").read()
    lines = txt.splitlines()
    title = next((re.match(r'^title:\s*"(.*)"', l).group(1) for l in lines if l.startswith("title:")), None)
    assert title, f"[{fn}] 无 title"

    # 结构：统计围栏外 H1
    inf = False; h1out = []
    for i, l in enumerate(lines):
        if l.strip().startswith("```"):
            inf = not inf; continue
        if inf: continue
        if re.match(r"^#\s+\S", l): h1out.append(i)
    # 真实 H1 不唯一 → 降级多余顶层 #
    if len(h1out) > 1:
        new = []
        for i, l in enumerate(lines):
            if i in h1out[1:]:
                new.append(re.sub(r"^#\s", "## ", l))
            else:
                new.append(l)
        lines = new
    # 标题一致性：真实 H1 必须唯一且等于 title（[[双链]] 用文件名，不要求文件名==title）
    if len(h1out) == 0:
        # 缺 H1：在 frontmatter 结束后补一个
        k = 0
        if lines and lines[0].strip() == "---":
            for k in range(1, len(lines)):
                if lines[k].strip() == "---":
                    k += 1
                    break
        lines = lines[:k] + ["", "# " + title, ""] + lines[k:]
        h1out = [k + 1]
    else:
        # 唯一真实 H1 必须等于 title；不符则修正正文标题（frontmatter title 为权威）
        if lines[h1out[0]] != "# " + title:
            lines[h1out[0]] = "# " + title
    assert h1out and lines[h1out[0]] == "# " + title, f"[{fn}] H1({lines[h1out[0]] if h1out else None}) != title({title})"
    # 围栏奇数 → 闭合
    fences = sum(1 for l in lines if l.strip().startswith("```"))
    if fences % 2 == 1:
        lines = lines + ["```"]

    # 导航块（幂等）
    if not any(l.startswith("> 📌 **导航**") for l in lines):
        nav = (f"> 📌 **导航**：本文是 **{title}** 词条，属于 {DIR} 术语集。"
               f"相关枢纽：{('、'.join('[[' + h + ']]' for h in hubs))}。")
        h1_idx = next(i for i, l in enumerate(lines) if re.match(r"^#\s+\S", l))
        j = h1_idx + 1
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        lines = lines[:j] + ["", nav, ""] + lines[j:]

    # 相关术语 + 参考资料（幂等）
    body = "\n".join(lines)
    if "## 相关术语" not in body:
        rel = related_for(fn, files)
        rel_line = "、".join("[[" + t + "]]" for t in rel)
        tail = f"\n\n## 相关术语\n\n{rel_line}\n\n## 参考资料\n\n{REF_LINE}\n"
        body = body.rstrip("\n") + tail
    else:
        body = body.rstrip("\n") + "\n"

    # 校验目标真实（跨目录均有效；读者按全树解析 [[双链]]；仅校验围栏外正文双链）
    for t in set(extract_links(lines)):
        assert t in ALL, f"[{fn}] 断链: {t}"
    open(p, "w", encoding="utf-8").write(body)

def validate(fn, files):
    p = os.path.join(BASE, DIR, fn + ".md")
    lines = open(p, encoding="utf-8-sig").read().splitlines()
    inf = False; h1out = []
    for l in lines:
        if l.strip().startswith("```"):
            inf = not inf; continue
        if inf: continue
        if re.match(r"^#\s+\S", l): h1out.append(l)
    title = next(re.match(r'^title:\s*"(.*)"', l).group(1) for l in lines if l.startswith("title:"))
    h1_ok = (len(h1out) == 1 and h1out[0] == "# " + title)
    fences = sum(1 for l in lines if l.strip().startswith("```"))
    nav_ok = any(l.startswith("> 📌 **导航**") for l in lines)
    rel_ok = any("## 相关术语" in l for l in lines)
    ref_ok = any("## 参考资料" in l for l in lines)
    links_ok = all(t in ALL for t in set(extract_links(lines)))
    ok = h1_ok and fences % 2 == 0 and nav_ok and rel_ok and ref_ok and links_ok
    if not ok:
        print(f"  FAIL {fn}: h1={h1_ok} fence={fences%2==0} nav={nav_ok} rel={rel_ok} ref={ref_ok} links={links_ok}")
    return ok

def build_all():
    s = set()
    for d in os.listdir(BASE):
        dp = os.path.join(BASE, d)
        if not os.path.isdir(dp) or d.startswith("_"): continue
        for f in glob.glob(os.path.join(dp, "*.md")):
            s.add(os.path.splitext(os.path.basename(f))[0])
    return s

if __name__ == "__main__":
    DIR = sys.argv[1]
    do_commit = "--commit" in sys.argv
    ALL.update(build_all())
    D = os.path.join(BASE, DIR)
    files = sorted(os.path.splitext(os.path.basename(f))[0] for f in glob.glob(os.path.join(D, "*.md")))
    hubs = pick_hubs(files)
    print(f"[{DIR}] files={len(files)} hubs={hubs}")
    for fn in files:
        process(fn, files, hubs)
    allok = all(validate(fn, files) for fn in files)
    print("VALIDATE:", "ALL PASS" if allok else "HAS FAILURES")
    if do_commit and allok:
        print("（提交由外部脚本执行）")
