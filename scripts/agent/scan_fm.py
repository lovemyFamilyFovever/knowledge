# -*- coding: utf-8 -*-
"""扫描 content/ 全库：正文中又嵌了一层 frontmatter 的「双 fm 污染」。常驻工具，可重复跑。"""
import os
import re
import sys

# 仓库根按脚本位置推导（scripts/agent/ 的上两级），换机器/换盘符都可用；argv[1] 可显式覆盖
root = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "content")
fm_start = re.compile(r"\A---\s*\n")
fm_block = re.compile(r"\A---\s*\n[\s\S]*?\n---\s*\n")
fm_open = re.compile(r"\s*---\s*\n[\s\S]*?\n---\s*\n")

bad = []
checked = 0
for dp, dn, fn in os.walk(root):
    dn[:] = [d for d in dn if not d.startswith("_")]
    for f in fn:
        if not f.endswith(".md") or f.endswith(".notes.md"):
            continue
        p = os.path.join(dp, f)
        try:
            t = open(p, encoding="utf-8").read()
        except Exception:
            continue
        checked += 1
        if not fm_start.match(t):
            continue
        m = fm_block.match(t)
        if not m:
            continue
        rest = t[m.end():]
        if fm_open.match(rest[:400]):
            bad.append(os.path.relpath(p, root))

print(f"checked: {checked}")
print(f"POLLUTED: {len(bad)}")
for b in bad:
    print(" ", b)
