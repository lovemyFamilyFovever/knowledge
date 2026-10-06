# -*- coding: utf-8 -*-
"""悬空令牌检查（新门禁，落成可复用脚本 scripts/check_dangling_tokens.py 随热修入库）：
全仓 var(--x) 使用集合 - --x: 定义集合，排除带 fallback var(--x,、JS setProperty 运行时注入、
三方库（echarts/mermaid/gsap/xlsx/chart.umd/highlight）。差集必须为空。
用法：python scripts/check_dangling_tokens.py（exit 1 若有悬空）。"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_JS = {"echarts.min.js", "mermaid.min.js", "gsap.min.js", "xlsx.full.min.js",
           "chart.umd.min.js", "highlight.min.js"}

css_files = list((ROOT / "static").glob("*.css")) + list((ROOT / "static/pages").glob("*.css"))
js_files = [p for p in (ROOT / "static").rglob("*.js") if p.name not in SKIP_JS]
js_files += [p for p in (ROOT / "static/pages").rglob("*.js") if p.name not in SKIP_JS]
html_files = list((ROOT / "app/templates").rglob("*.html"))

texts = {}
for p in css_files + js_files + html_files:
    texts[p] = p.read_text(encoding="utf-8", errors="replace")

# 定义集合（CSS 定义 + JS/HTML 内联 style="--x:"）
defs = set()
runtime = set()
for p, t in texts.items():
    if p.suffix == ".css":
        t2 = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
        defs |= set(re.findall(r"(?<![\w-])(--[a-z0-9-]+)\s*:", t2))
    else:
        defs |= set(re.findall(r"style\s*=\s*[\"'][^\"']*?([a-z-]+(?:-[a-z0-9-]+)*)\s*:", t))
        runtime |= set(re.findall(r"setProperty\(\s*[\"'](--[a-z0-9-]+)", t))
        # JS 模板内联动态注入：先取整个 style="..." 值，再解析内层全部 --x:（一行可多个）
        for m in re.finditer(r"style=\s*[\"']([^\"']*)[\"']", t):
            runtime |= set(re.findall(r"(--[a-z0-9-]+)\s*:", m.group(1)))

uses_hard = {}   # token -> [file:line]（无 fallback 硬引用）
uses_fb = {}     # 带 fallback（良性）
for p, t in texts.items():
    body = re.sub(r"/\*.*?\*/", "", t, flags=re.S) if p.suffix == ".css" else t
    for i, l in enumerate(body.split("\n"), 1):
        for m in re.finditer(r"var\((--[a-z0-9-]+)\s*([\),])", l):
            tok, tail = m.group(1), m.group(2)
            # 排除定义行本身
            if re.search(re.escape(tok) + r"\s*:", l) and p.suffix == ".css" and re.match(r"\s*" + re.escape(tok) + r"\s*:", l):
                continue
            if tail == ",":
                uses_fb.setdefault(tok, []).append(f"{p.name}:{i}")
            else:
                uses_hard.setdefault(tok, []).append(f"{p.name}:{i}")

dangling = {}
for tok, refs in uses_hard.items():
    if tok in defs:
        continue
    if tok in runtime:
        continue  # JS 运行时注入
    dangling[tok] = refs

if dangling:
    print("DANGLING TOKENS:", len(dangling))
    for tok, refs in sorted(dangling.items()):
        print(f"  {tok}: {len(refs)} refs @ {', '.join(refs[:4])}")
    sys.exit(1)
print("dangling tokens: 0 (all var() uses resolve to definitions / fallback / runtime-injected)")
