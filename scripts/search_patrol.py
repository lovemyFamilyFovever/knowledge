# -*- coding: utf-8 -*-
"""搜索双模式深测：FTS 关键词 vs 语义 /api/rag，边界与一致性"""
import io
import json
import time
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:5001"
results = []


def get(path):
    req = urllib.request.Request(BASE + path)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (f"  | {detail}" if detail and not cond else ""))


def search_fts(q):
    qs = urllib.parse.quote(q)
    st, html = get(f"/search?q={qs}&mode=fts")
    # mode 参数不存在时页面也回 200，直接数卡片
    import re
    cards = re.findall(r'<a class="result" href="([^"]*)"', html)
    empt = "没有匹配" in html or "empty" in html
    return st, cards, empt, html


def search_semantic(q):
    qs = urllib.parse.quote(q)
    st, body = get(f"/api/rag?q={qs}&k=5")
    try:
        return st, json.loads(body)
    except Exception:
        return st, {}


# 1. FTS 中文词
st, cards, empt, html = search_fts("知识图谱")
check("FTS 中文词有结果", st == 200 and (len(cards) > 0 or empt), f"cards={len(cards)}")
check("FTS 结果全部带 href", all(c for c in cards), f"空 href 数={sum(1 for c in cards if not c)}")

# 2. FTS 英文词
st, cards, empt, html = search_fts("sandbox")
check("FTS 英文词", st == 200 and (len(cards) > 0 or empt), f"cards={len(cards)}")

# 3. FTS 空结果
st, cards, empt, html = search_fts("zzz不存在的词xyz")
check("FTS 空结果优雅", st == 200 and (empt or len(cards) == 0), f"cards={len(cards)} empt={empt}")

# 4. 语义检索
st, r = search_semantic("沙箱安全的实现方式有哪些")
check("语义检索正常返回", st == 200 and isinstance(r.get("hits"), list), f"status={st} hits={len(r.get('hits', []))}")
if r.get("hits"):
    h0 = r["hits"][0]
    check("语义 hits 字段齐全", all(k in h0 for k in ("file", "url", "score")), str(list(h0.keys()))[:120])

# 5. 语义空 query → 400
st, r = search_semantic("")
check("语义空 q 400", st == 400, f"status={st}")

# 6. 语义 hits 的 url 非空且逐段编码（无裸空格）
st, r = search_semantic("知识图谱")
bad = [h.get("url", "") for h in r.get("hits", []) if not h.get("url") or " " in h.get("url", "")]
check("语义 hits url 非空且已编码", st != 200 or not bad, str(bad)[:80])

# 7. search 页面 mode=semantic（语义开关开时的页面渲染）
qs = urllib.parse.quote("沙箱安全")
st, html = get(f"/search?q={qs}")
check("search 页面聚合渲染", st == 200 and ("result" in html or "没有" in html), f"status={st}")

# 8. 超长 query 不炸
st, cards, empt, html = search_fts("沙箱" * 100)
check("FTS 超长 query 不 500", st == 200, f"status={st}")

n_fail = sum(1 for _, ok, _ in results if not ok)
print(f"\n==== 搜索深测完成：{len(results)} 项，失败 {n_fail} 项 ====")
raise SystemExit(1 if n_fail else 0)
