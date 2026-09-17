# -*- coding: utf-8 -*-
"""扫描「抓取残留副本」：xxx-<数字>.md 且存在 xxx.md（去掉数字后缀后同名）。常驻工具，可重复跑。"""
import re
import sys
from pathlib import Path

# 仓库根按脚本位置推导（scripts/agent/ 的上两级），换机器/换盘符都可用；argv[1] 可显式覆盖
root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "content"
pat = re.compile(r"^(.*)-(\d{1,4})$")
dupes = []
for p in root.rglob("*.md"):
    if any(part.startswith("_") for part in p.parts):
        continue
    m = pat.match(p.stem)
    if not m:
        continue
    full = p.parent / (m.group(1) + ".md")
    if full.exists():
        dupes.append((p, full, p.stat().st_size, full.stat().st_size))

print(f"residual copies: {len(dupes)}")
for dup, full, s1, s2 in dupes:
    print(f"  {dup.relative_to(root)}  ({s1//1024}KB)  <--  complete: {full.relative_to(root)} ({s2//1024}KB)")
