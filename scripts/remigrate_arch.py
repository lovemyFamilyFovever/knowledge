# -*- coding: utf-8 -*-
"""重迁移 projects/dsh-agent/architecture/ 下 10+2 篇 md：
源 = 同目录同名 .html（结构完整：h2/h3/table/pre），产物 = 覆盖同名 .md 正文。
frontmatter 保留原文件不动。转换规则：
  h1-h4 → #..####；table → Markdown 管道表；pre>code → ``` 围栏；
  code → `；b/strong → **；i/em → *；a → [text](href)（保留相对 href）；
  li → -；br → 换行；其余标签剥壳。
摘要文件的「文件索引」表补双链：partN → 同目录对应 md。
dry-run 默认预览 diff 统计，--apply 才写盘。"""
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "content" / "projects" / "dsh-agent" / "architecture"
FM_RE = re.compile(r"\A---\n([\s\S]*?)\n---\n\n?")


def inline(html: str) -> str:
    """行内标签 → Markdown 行内格式"""
    s = html
    s = re.sub(r"<(br|/p|/li|/tr|/h[1-6])[^>]*>", " ", s)
    s = re.sub(r"<(b|strong)[^>]*>([\s\S]*?)</\1>", r"**\2**", s)
    s = re.sub(r"<(i|em)[^>]*>([\s\S]*?)</\1>", r"*\2*", s)
    s = re.sub(r"<code[^>]*>([\s\S]*?)</code>", r"`\1`", s)
    s = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>([\s\S]*?)</a>', r"[\2](\1)", s)
    s = re.sub(r"<[^>]+>", "", s)  # 剩余标签剥壳
    s = unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def convert_table(tb: str) -> str:
    head = re.search(r"<thead>([\s\S]*?)</thead>", tb)
    body = re.search(r"<tbody>([\s\S]*?)</tbody>", tb)
    def cells(row_html: str) -> list[str]:
        return [inline(c) for c in re.findall(r"<t[hd][^>]*>([\s\S]*?)</t[hd]>", row_html)]
    lines = []
    header_cells = []
    if head:
        rows = re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", head.group(1))
        if rows:
            header_cells = cells(rows[0])
    if not header_cells:  # 无 thead：首行当表头
        all_rows = re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", tb)
        if all_rows:
            header_cells = cells(all_rows[0])
            all_rows = all_rows[1:]
        body_rows = all_rows
    else:
        body_rows = re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", body.group(1)) if body else []
    if not header_cells:
        return ""
    lines.append("| " + " | ".join(header_cells) + " |")
    lines.append("|" + "|".join([" --- "] * len(header_cells)) + "|")
    for r in body_rows:
        cs = cells(r)
        cs += [""] * (len(header_cells) - len(cs))
        lines.append("| " + " | ".join(cs[: len(header_cells)]) + " |")
    return "\n".join(lines)


def html_to_md(html: str) -> str:
    # 取 body
    m = re.search(r"<body[^>]*>([\s\S]*?)</body>", html)
    s = m.group(1) if m else html
    s = re.sub(r"<(script|style|nav)\b[\s\S]*?</\1>", "", s)  # 脚本/样式/目录导航剔除
    # 代码块先行保护（占位符，避免内部标签被行内规则误伤）
    code_blocks = []
    def stash_pre(mm):
        code = re.sub(r"<[^>]+>", "", mm.group(1))
        code_blocks.append(unescape(code))
        return f"\x00CB{len(code_blocks)-1}\x00"
    s = re.sub(r"<pre[^>]*>(?:<code[^>]*>)?([\s\S]*?)</code></pre>", stash_pre, s)
    s = re.sub(r"<pre[^>]*>([\s\S]*?)</pre>", stash_pre, s)
    # 表格 → Markdown 表
    s = re.sub(r"<table[^>]*>[\s\S]*?</table>", lambda mm: "\n\n" + convert_table(mm.group(0)) + "\n\n", s)
    # 标题
    for lv in range(1, 5):
        s = re.sub(rf"<h{lv}[^>]*>([\s\S]*?)</h{lv}>", lambda mm, lv=lv: "\n\n" + "#" * lv + " " + inline(mm.group(1)) + "\n\n", s)
    # 列表
    s = re.sub(r"<li[^>]*>([\s\S]*?)</li>", lambda mm: "\n- " + inline(mm.group(1)), s)
    s = re.sub(r"</?(ul|ol)[^>]*>", "\n", s)
    # 段落分隔
    s = re.sub(r"<(p|div|section)[^>]*>", "\n", s)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<hr\s*/?>", "\n\n---\n\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = unescape(s)
    # 代码块还原
    def unstash(mm):
        return "\n\n```\n" + code_blocks[int(mm.group(1))] + "\n```\n\n"
    s = re.sub(r"\x00CB(\d+)\x00", unstash, s)
    # 清理：连续空行压一、行尾空白
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip() + "\n"


# 摘要文件索引 → 兄弟文档双链映射（按 partN slug → 实际文件名关键词）
PART_LINKS = {
    "part1-module-responsibilities": "第一部分",
    "part2-session-scope-events": "第二部分",
    "part3-patterns-improvements": "第三部分",
    "part4-tool-pipeline-prompt": "第四部分",
    "part5-subagent-compaction": "第五部分",
    "part6-llm-adapter-layer": "第六部分",
    "part7-sandbox-security": "第七部分",
    "part8-code-runtime": "第八部分",
    "part9-settings-credentials-storage": "第九部分",
    "part10-client-extension": "第十部分",
    "summary-architecture-overview": "摘要",
}


def rebuild_summary_links(md: str) -> str:
    """摘要文档「五、文件索引」表格：partN 文本 → [[对应文档]] 双链"""

    def link_cell(mm):
        slug = mm.group(1).strip()
        for key, kw in PART_LINKS.items():
            if slug == key:
                # 找同目录以该关键词开头的 md
                targets = list(DIR.glob(f"*{kw}*.md"))
                if targets:
                    name = targets[0].stem
                    return f"[[{name}]]"
                return slug
        return slug

    # 表格单元格里出现裸 slug 的位置替换（仅在文件索引表格行内）
    lines = md.split("\n")
    out = []
    in_index = False
    for ln in lines:
        if "五、文件索引" in ln or "文件索引" in ln and ln.startswith("#"):
            in_index = True
        elif ln.startswith("#"):
            in_index = False
        if in_index and ln.startswith("|") and "---" not in ln:
            ln = re.sub(r"\|\s*([a-z0-9-]+)\s*(?=\|)", lambda mm: "|" + (link_cell(type("M", (), {"group": lambda self, i: mm.group(i)})) if mm.group(1) in PART_LINKS else mm.group(1)) + " ", ln)
        out.append(ln)
    return "\n".join(out)


def main():
    apply = "--apply" in sys.argv
    htmls = sorted(DIR.glob("*.html"))
    changed = []
    for h in htmls:
        md_path = h.with_suffix(".md")
        if not md_path.is_file():
            continue
        old = md_path.read_text(encoding="utf-8")
        fm = FM_RE.match(old)
        fm_text = fm.group(0) if fm else ""
        new_body = html_to_md(h.read_text(encoding="utf-8"))
        if "摘要" in md_path.stem:
            new_body = rebuild_summary_links(new_body)
        new = fm_text + new_body
        # 统计结构增量
        h2n = len(re.findall(r"(?m)^## ", new))
        tbn = len(re.findall(r"(?m)^\| --- ", new))
        if new != old:
            changed.append((md_path.name, len(old), len(new), h2n, tbn))
            if apply:
                md_path.write_text(new, encoding="utf-8")
    print(f"{'APPLIED' if apply else 'DRY-RUN'}: {len(changed)} files changed")
    for name, lo, ln, h2n, tbn in changed:
        print(f"  {name}: {lo} -> {ln} chars, h2={h2n}, tables={tbn}")
    if not apply:
        print("(add --apply to write)")


if __name__ == "__main__":
    main()
