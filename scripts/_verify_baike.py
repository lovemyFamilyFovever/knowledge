# -*- coding: utf-8 -*-
import os, re
BASE = r"E:/GitHub/knowledge/content/baike"
total = 0
miss_nav = miss_rel = miss_ref = miss_h1 = miss_fence = 0
examples = []
files = []
for d in os.listdir(BASE):
    dp = os.path.join(BASE, d)
    if not os.path.isdir(dp) or d.startswith("_"):
        continue
    for f in os.listdir(dp):
        if f.endswith(".md"):
            fn = os.path.splitext(f)[0]
            files.append((d, fn, os.path.join(dp, f)))
total = len(files)
for d, fn, p in files:
    txt = open(p, encoding="utf-8-sig").read()
    lines = txt.splitlines()
    if "> 📌 **导航**" not in txt:
        miss_nav += 1; examples.append(("nav", d, fn))
    if "## 相关术语" not in txt:
        miss_rel += 1; examples.append(("rel", d, fn))
    if "## 参考资料" not in txt:
        miss_ref += 1; examples.append(("ref", d, fn))
    title = next((re.match(r'^title:\s*"(.*)"', l).group(1) for l in lines if l.startswith("title:")), None)
    inf = False; h1 = []
    for l in lines:
        if l.strip().startswith("```"):
            inf = not inf; continue
        if inf:
            continue
        if re.match(r"^#\s+\S", l):
            h1.append(l)
    if not (len(h1) == 1 and h1[0] == "# " + title):
        miss_h1 += 1; examples.append(("h1", d, fn))
    fences = sum(1 for l in lines if l.strip().startswith("```"))
    if fences % 2 == 1:
        miss_fence += 1; examples.append(("fence", d, fn))
print("TOTAL files:", total)
print("miss_nav:", miss_nav, "miss_rel:", miss_rel, "miss_ref:", miss_ref,
      "miss_h1:", miss_h1, "miss_fence:", miss_fence)
for e in examples[:20]:
    print("  ", e)
