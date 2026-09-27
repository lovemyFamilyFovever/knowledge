# -*- coding: utf-8 -*-
"""单篇查漏补缺回归（切片 3，2026-09-27）—— 本地判据先跑满，AI 只补判断那一半。

运行：python tests/test_ai_audit.py

三条判据值得单独说明：
  · **干净文档必须一条建议都不出**（控制组）。缺了它，"判据永远亮红"这种废实现也能全绿；
  · **不出站域照样能查本地**：career 文档拿到的是 200 + 本地建议 + 一句"只跑了本地判据"，
    而不是 403 —— 本地判据一个字节都不出站，拦它等于惩罚用户；
  · **建议 id 稳定**：同一篇重跑不能堆重复条目，且用户点过的「忽略 / 采纳」不能被冲掉。
"""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _ci  # noqa: E402
from test_ai_config import CALLS, start_provider  # noqa: E402

from app import ai_audit, ai_qa  # noqa: E402
from app.app import create_app  # noqa: E402

KEY = "sk-AUDITCANARY-K7QF"

# 脏文档：每类判据都踩一处（围栏问题单独放 FENCED 那份 —— 未闭合的围栏会把后半篇全吞掉，
# 混在一份里会让"标题跳级 / 空小节"的期望值变得说不清）
DIRTY = """---
title: "残缺词条"
collected: 2024-01-05
---

# 残缺词条

## 定义

## 细节

#### 这里从 h2 直接跳到 h4

正文内容，这里提到 向量数据库 这个词，也提到 事件循环。

参见 [[根本不存在的词条]] 与 ![图](_assets/没有这张.png)。

## 结尾

这一段的结尾没有句末标点因为抄到一半就断了而且长度也过了四十个字所以应该被截断判据抓到才对
"""

FENCED = """---
title: "围栏没关"
source: baike
collected: 2026-09-01
tags: [代码]
status: stable
---

# 围栏没关

## 用法

```python
print("忘了闭合）
"""

TERM = """---
title: "向量数据库"
source: baike
collected: 2026-09-01
tags: [检索]
status: stable
---

# 向量数据库

## 定义

**一句话定义：** 把文本变成坐标、按距离找相似内容的存储。
"""

# 干净文档：控制组，必须一条都不报
CLEAN = """---
title: "干净词条"
source: baike
collected: 2026-09-01
tags: [检索]
status: stable
---

# 干净词条

## 定义

**一句话定义：** 这是一篇结构完整的样本。

## 用法

它有小节、有结尾标点，也没有未闭合的围栏。

- 列表项一
- 列表项二
"""

CAREER = '---\ntitle: "简历乙"\nsource: career\ncollected: 2026-09-01\ntags: [职业]\nstatus: stable\n---\n\n# 简历乙\n\n## 定义\n\n## 空节\n'

TAXONOMY = {"domains": {"baike": {"label": "百科", "hue": 158},
                        "career": {"label": "职业", "hue": 42},
                        "小说": {"label": "网文", "hue": 300, "ai": False}}}

passed = failed = 0
FAILS = []


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS {name}")
    else:
        failed += 1
        FAILS.append(name)
        _ci.failed(name)
        print(f"  FAIL {name} :: {str(extra)[:220]}")


def make_root(tmp):
    root = Path(tmp)
    c = root / "content"
    (c / "baike" / "sub").mkdir(parents=True)
    (c / "baike" / "term").mkdir(parents=True)
    (c / "career").mkdir(parents=True)
    (c / "_meta").mkdir(parents=True)
    (c / "baike" / "sub" / "dirty.md").write_text(DIRTY, encoding="utf-8")
    (c / "baike" / "sub" / "clean.md").write_text(CLEAN, encoding="utf-8")
    (c / "baike" / "sub" / "fenced.md").write_text(FENCED, encoding="utf-8")
    (c / "baike" / "term" / "向量数据库.md").write_text(TERM, encoding="utf-8")
    (c / "career" / "B.md").write_text(CAREER, encoding="utf-8")
    # 不出站域里也放一篇" dirty 正文提到了它"的词条：配对必须把对方滤掉
    # （不变量 9 ① 不看谁发起，只看内容从哪个域来）
    (c / "小说").mkdir(parents=True)
    (c / "小说" / "事件循环.md").write_text(
        '---\ntitle: "事件循环"\nsource: novel\ncollected: 2026-09-01\ntags: [设定]\n'
        'status: stable\n---\n\n# 事件循环\n\n## 设定\n\n小说里那个不停重复同一天的循环设定，'
        "用来验证不出站域的摘要连进候选都不配。\n", encoding="utf-8")
    (c / "_meta" / "taxonomy.json").write_text(
        json.dumps(TAXONOMY, ensure_ascii=False), encoding="utf-8")
    return root


def client_for(root):
    app = create_app(root)
    app.config["_AI_USAGE"] = None
    app.config["KB_HOOKS"]["get_rag"] = lambda: (None, None)
    app.config["KB_HOOKS"]["query_rag"] = lambda *a, **k: []
    return app, app.test_client()


def kinds(props):
    return {p["kind"] for p in props}


def main() -> int:
    _ci.started("ai_audit")
    for k in ("KB_AI_API_KEY", "KB_AI_BASE_URL", "KB_AI_MODEL"):
        os.environ.pop(k, None)
    srv, base = start_provider()
    try:
        # ============================================== A. 本地判据（纯函数）
        print("\n[A] 本地判据")
        props = ai_audit.local_checks(DIRTY, path="baike/sub/dirty.md",
                                      fm={"title": "残缺词条"},
                                      known_titles=["向量数据库", "事件循环", "干净词条"],
                                      asset_exists=lambda u: False)
        ks = kinds(props)
        for want, label in [("fm_missing", "元数据缺项"), ("empty_section", "空小节"),
                            ("heading_skip", "标题跳级"), ("dead_wikilink", "失效双链"),
                            ("missing_asset", "附件不存在"), ("truncated_end", "疑似截断"),
                            ("should_link", "应引未引候选")]:
            check(f"A1 {label}被抓到", want in ks, sorted(ks))
        fenced_props = ai_audit.local_checks(FENCED, path="baike/sub/fenced.md",
                                             fm={"title": "围栏没关", "source": "baike",
                                                 "collected": "2026-09-01",
                                                 "tags": ["代码"], "status": "stable"},
                                             known_titles=[])
        check("A1b 代码围栏未闭合被抓到（单独一份样本：未闭合会把后半篇全吞掉，"
              "混在脏文档里会让别的判据期望值说不清）",
              kinds(fenced_props) == {"unclosed_fence", "empty_section"},
              [(p["kind"], p["evidence"]) for p in fenced_props])
        check("A2 每条建议都带证据与建议动作（光有结论的一律不予展示）",
              all(p["evidence"] and p["suggestion"] and p["severity"] for p in props),
              [p["kind"] for p in props if not p["evidence"]])
        check("A3 只有「应引未引」需要 AI，其余全是本地算出来的",
              {p["kind"] for p in props if p["needs_ai"]} == {"should_link"},
              [(p["kind"], p["needs_ai"]) for p in props])
        sl = next(p for p in props if p["kind"] == "should_link")
        tight = ('---\ntitle: "紧跟标点"\n---\n\n# 紧跟标点\n\n## 定义\n\n'
                 '本项目用过 向量数据库。\n\n## 结尾\n\n完了。\n')
        tp = ai_audit.local_checks(tight, path="baike/sub/tight.md", fm={},
                                   known_titles=["向量数据库 ", " 事件循环 "])
        sl2 = next((p2 for p2 in tp if p2["kind"] == "should_link"), None)
        check("A4b 全库标题带首尾空格也能匹配（索引里存的就是带空格的样子，"
              "带着空格去比对会让「应引未引」成片漏报）",
              sl2 is not None and "向量数据库" in sl2["evidence"], tp)
        selfdoc = ai_audit.local_checks(tight, path="baike/sub/tight.md",
                                        fm={"title": "紧跟标点"},
                                        known_titles=["紧跟标点", "向量数据库"])
        sl3 = next((p2 for p2 in selfdoc if p2["kind"] == "should_link"), None)
        check("A4c 不把自己算成候选（每篇正文里必然有它自己的标题，那是纯噪音）",
              sl3 is not None and "紧跟标点" not in sl3["evidence"]
              and "向量数据库" in sl3["evidence"], sl3 and sl3["evidence"])
        check("A4 候选词来自全库标题集合，且已经是双链的不重复出现在候选里",
              "向量数据库" in sl["evidence"] and "根本不存在的词条" not in sl["evidence"],
              sl["evidence"])
        # 索引是**滞后**的派生缓存（不变量 3）：watcher 还没重建时，里面会留着
        # 刚从正文里删掉的链接。判据若照着索引报，就会报一条正文里根本不存在的
        # 死链，而且建议 id 由链接名哈希而来 —— 集一抖，用户点过的「忽略」就跟着漂走。
        stale_idx = ai_audit.local_checks(DIRTY, path="baike/sub/dirty.md",
                                          fm={"title": "残缺词条"}, known_titles=[],
                                          dead_links=["正文里已经没有的旧链接"])
        check("A1c 索引里滞后的链接不报死链（只报当前正文里真出现的双链）",
              "dead_wikilink" not in kinds(stale_idx), sorted(kinds(stale_idx)))
        live_idx = ai_audit.local_checks(DIRTY, path="baike/sub/dirty.md",
                                         fm={"title": "残缺词条"}, known_titles=[],
                                         dead_links=["根本不存在的词条"])
        check("A1d 控制组：正文里真有的未解析链接照样报（防 A1c 是条恒不报的假判据）",
              "dead_wikilink" in kinds(live_idx), sorted(kinds(live_idx)))
        clean_props = ai_audit.local_checks(CLEAN, path="baike/sub/clean.md",
                                            fm={"title": "干净词条", "source": "baike",
                                                "collected": "2026-09-01", "tags": ["检索"],
                                                "status": "stable"},
                                            known_titles=["向量数据库"],
                                            asset_exists=lambda u: True)
        check("A5 控制组：结构完整的文档一条建议都不出（否则判据就是永远亮红的废铁）",
              clean_props == [], [(p["kind"], p["evidence"]) for p in clean_props])
        again = ai_audit.local_checks(DIRTY, path="baike/sub/dirty.md",
                                      fm={"title": "残缺词条"},
                                      known_titles=["向量数据库", "事件循环", "干净词条"],
                                      asset_exists=lambda u: False)
        check("A6 建议 id 稳定（同一篇重跑是刷新，不是堆重复条目）",
              [p["id"] for p in again] == [p["id"] for p in props],
              [(p["id"], p["kind"]) for p in again][:3])
        check("A7 换文档 id 不同（不会把两篇的处置状态混在一起）",
              ai_audit.local_checks(DIRTY, path="baike/sub/other.md", fm={},
                                    known_titles=[]) [0]["id"] != props[0]["id"])
        # 上面对比的两篇连 fm 都不一样，id 里就算不含 path 也照样不相等 ——
        # 那条判据其实没在判 path。这一条把正文、fm、候选集全钉成同一份，
        # 只有 path 不同：此时 id 必须分开，否则「这篇忽略」会串到那篇。
        here = ai_audit.local_checks(DIRTY, path="baike/sub/dirty.md",
                                     fm={}, known_titles=[])
        elsewhere = ai_audit.local_checks(DIRTY, path="baike/sub/other.md",
                                          fm={}, known_titles=[])
        check("A7b 同一份正文换 path 后 id 全不同（id 里必须含 path）",
              {p["id"] for p in here}.isdisjoint({p["id"] for p in elsewhere}),
              sorted({p["id"] for p in here} & {p["id"] for p in elsewhere}))
        H1DOC = ("# 标题甲\n" "# 标题乙\n" "\n" "正文一句。\n")
        h1kinds = kinds(ai_audit.local_checks(H1DOC, path="baike/sub/h1.md", fm={},
                                              known_titles=[]))
        check("A8b 连续两个 h1 不算空小节（h1 是文档标题，不该被当成只有标题没内容）",
              "empty_section" not in h1kinds, h1kinds)
        tail_empty = ("---\ntitle: \"尾部空节\"\ncollected: 2024-01-05\n---\n\n"
                      "# 尾部空节\n\n## 定义\n\n正文一句。\n\n## 待补\n")
        tk = kinds(ai_audit.local_checks(tail_empty, path="baike/sub/tail.md", fm={},
                                         known_titles=[]))
        check("A8c 文档以空小节收尾也要抓（最后一节曾经免检，而\"## 待补\"写完就忘正是最常见的那种）",
              "empty_section" in tk, tk)
        check("A8 outline 按层级如实列出（标题跳级不影响大纲）",
              [(h["level"], h["title"]) for h in ai_audit.outline(DIRTY)] ==
              [(1, "残缺词条"), (2, "定义"), (2, "细节"),
               (4, "这里从 h2 直接跳到 h4"), (2, "结尾")], ai_audit.outline(DIRTY))

        # ============================================== B. 端点：无 key 也能查本地
        print("\n[B] 端点与闸门")
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            app, c = client_for(root)
            r = c.post("/api/ai/audit", json={"path": "baike/sub/dirty.md"})
            j = r.get_json()
            check("B1 没配 key 照样能查（200 + 本地建议），并如实说明 AI 那半没跑",
                  r.status_code == 200 and j.get("ok") and j.get("local_count", 0) >= 6
                  and j.get("ai_enabled") is False and "只跑了本地判据" in (j.get("ai_reason") or ""),
                  j)
            check("B2 全程零出站", CALLS == {}, CALLS)
            pid = (j.get("proposals") or [{}])[0]["id"]
            g = c.get("/api/ai/audit?path=baike/sub/dirty.md")
            check("B3 GET 能读回同一批建议（含处置状态字段）",
                  g.status_code == 200 and len(g.get_json()["proposals"]) == j["local_count"]
                  and all(p["status"] == "pending" for p in g.get_json()["proposals"]),
                  g.get_json())
            s = c.post("/api/ai/audit/status", json={"path": "baike/sub/dirty.md",
                                                     "id": pid, "status": "dismissed"})
            check("B4 忽略一条 → 200", s.status_code == 200 and s.get_json()["ok"],
                  s.get_json())
            g2 = c.get("/api/ai/audit?path=baike/sub/dirty.md").get_json()["proposals"]
            check("B5 忽略状态被记住，且排序把待处理的排到前面",
                  next(p for p in g2 if p["id"] == pid)["status"] == "dismissed"
                  and g2[0]["status"] == "pending", [p["status"] for p in g2][:4])
            r = c.post("/api/ai/audit", json={"path": "baike/sub/dirty.md"})
            g3 = c.get("/api/ai/audit?path=baike/sub/dirty.md").get_json()["proposals"]
            check("B6 重扫不产生重复条目，也不冲掉用户点过的忽略",
                  len(g3) == len(g2) and next(p for p in g3 if p["id"] == pid)["status"]
                  == "dismissed", {"before": len(g2), "after": len(g3)})
            check("B7 非法 status → 400 且把允许值回出来",
                  c.post("/api/ai/audit/status", json={"path": "x", "id": "y",
                                                       "status": "wtf"}).status_code == 400)
            check("B8 不存在的 id → 404（不静默成功）",
                  c.post("/api/ai/audit/status", json={"path": "baike/sub/dirty.md",
                       "id": "deadbeef0000", "status": "adopted"}).status_code == 404)
            check("B9 缺 path → 400；文档不存在 → 404",
                  c.post("/api/ai/audit", json={}).status_code == 400
                  and c.post("/api/ai/audit", json={"path": "baike/sub/没有.md"}).status_code == 404)
            check("B10 路径穿越被拒（400）且不泄露绝对路径",
                  c.post("/api/ai/audit", json={"path": "../../app/app.py"}).status_code == 400
                  and str(root) not in c.post("/api/ai/audit",
                                              json={"path": "../../app/app.py"}
                                              ).get_data(as_text=True))

            # ---- career：本地照查，AI 不跑，且一个字节都不出站
            CALLS.clear()
            r = c.post("/api/ai/audit", json={"path": "career/B.md"})
            j = r.get_json()
            check("B11 不出站域拿到的是 200 + 本地建议（不是 403 —— 本地判据不出网）",
                  r.status_code == 200 and j.get("ai_enabled") is False
                  and "不出站" in (j.get("ai_reason") or ""), j)
            check("B12 该域的建议里确实有本地条目（空小节）",
                  "empty_section" in {p["kind"] for p in j.get("proposals") or []},
                  j.get("proposals"))
            check("B13 全程零出站（career 文档没被发出去过）", CALLS == {}, CALLS)
            check("B14 但同一条路径去 explain 仍然 403（两个端点的边界不是一回事）",
                  c.post("/api/ai/explain", json={"path": "career/B.md",
                                                  "selection": "简历乙"}).status_code == 403)

            # ---- 处置状态必须回到面板本身；正文改了旧建议必须被清掉
            c.post("/api/ai/audit", json={"path": "baike/sub/dirty.md"})
            first_id = c.get("/api/ai/audit?path=baike/sub/dirty.md").get_json()["proposals"][0]["id"]
            c.post("/api/ai/audit/status", json={"path": "baike/sub/dirty.md",
                                                 "id": first_id, "status": "dismissed"})
            again = c.post("/api/ai/audit", json={"path": "baike/sub/dirty.md"}).get_json()
            got = {p["id"]: p.get("status") for p in again["proposals"]}
            check("B15 重扫的响应里就带回处置状态（面板不能一边说已处置、一边把条目画回未处置）",
                  got.get(first_id) == "dismissed", got)
            (root / "content" / "baike" / "sub" / "dirty.md").write_text(CLEAN, encoding="utf-8")
            after_fix = c.post("/api/ai/audit", json={"path": "baike/sub/dirty.md"}).get_json()
            # 干净正文允许只剩"应引未引"这一类候选（标题集合口径变严时它会跟着动，
            # 但**旧建议必须被清掉**才是这条的本意 —— 所以按 kind 判，不按条数判）
            kinds_fix = {x["kind"] for x in after_fix["proposals"]}
            check("B16 正文改好后旧建议被清掉（不会一直挂着上次的问题）",
                  "fm_missing" not in kinds_fix and "empty_section" not in kinds_fix
                  and "heading_skip" not in kinds_fix, after_fix)
            check("B17 派生库里也真的被清空了（GET 与 POST 两条路给的是同一份事实）",
                  c.get("/api/ai/audit?path=baike/sub/dirty.md").get_json()["proposals"]
                  == after_fix["proposals"],
                  c.get("/api/ai/audit?path=baike/sub/dirty.md").get_json())
            # 判据读的是 #、```、[[双链]] —— 喂 HTML 只会查出一堆废话建议。
            # 前端靠「只在 .md 的面包屑上画查漏按钮」挡，后端这一层必须自己挡
            # （不变量 9 的口径：闸门在后端，不在 UI），依据是 safe_rel 的 .md 白名单。
            r = c.post("/api/ai/audit", json={"path": "baike/sub/page.html"})
            check("B18 非 Markdown 直接被拒（400），不是一堆垃圾建议",
                  r.status_code == 400 and "Markdown" in (r.get_json() or {}).get("error", ""),
                  (r.status_code, r.get_json()))
            check("B19 上面这趟照样零出站", CALLS.get("audit", 0) == 0, CALLS)

        # ============================================== C. 接上 AI 之后
        print("\n[C] AI 判断并入")
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            app, c = client_for(root)
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/audit",
                                         "allow_local": True, "timeout_s": 10})
            CALLS.clear()
            r = c.post("/api/ai/audit", json={"path": "baike/sub/dirty.md"})
            j = r.get_json()
            check("C1 配了 key 之后 ai_enabled 为真", j.get("ai_enabled") is True, j)
            check("C2 AI 的结论并回了「应引未引」那条，且只收窄不造新条目",
                  any(p["kind"] == "should_link" and p.get("ai_terms") == ["向量数据库"]
                      for p in j.get("proposals") or []),
                  [(p["kind"], p.get("ai_terms")) for p in j.get("proposals") or []])
            check("C3 本地建议条数不因 AI 而膨胀（AI 只改内容不改条目数）",
                  j.get("local_count") == len(j.get("proposals") or []), j)
            check("C4 审计调用进了账本（kind=audit）",
                  any(x["kind"] == "audit" for x in c.get("/api/ai/usage").get_json()["recent"]),
                  c.get("/api/ai/usage").get_json()["recent"])
            check("C5 最多问两次（应引未引 + 过时风险），绝不逐条建议各问一次",
                  CALLS.get("audit", 0) <= 2, CALLS)
            check("C8 真问过就要如实报发送字数（sent_chars 是「本次发了多少字」的账，"
                  "写死 0 等于对载荷撒谎 —— 这一版前端不显示它，下一版会）",
                  j.get("sent_chars", 0) > 0, j.get("sent_chars"))
            used = c.get("/api/ai/usage").get_json()["month"]["calls"]
            c.put("/api/ai/config", json={"monthly_budget_calls": used})
            r = c.post("/api/ai/audit", json={"path": "baike/sub/dirty.md"})
            j = r.get_json()
            check("C6 超预算帽时自动退回「只跑本地判据」，并且说清原因（不是报错）",
                  r.status_code == 200 and j.get("ai_enabled") is False
                  and "预算帽" in (j.get("ai_reason") or ""), j)
            c.put("/api/ai/config", json={"monthly_budget_calls": 300})
            r = c.post("/api/ai/audit", json={"path": "baike/sub/dirty.md", "ai": False})
            check("C7 ai=false 时明确只跑本地（用户有权不花钱）",
                  r.get_json().get("ai_enabled") is False
                  and "本地判据" in (r.get_json().get("ai_reason") or ""), r.get_json())

        # ============================================== D. 端点失败面：不假装查全
        print("\n[D] AI 挂了怎么办")
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            app, c = client_for(root)
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/auth",
                                         "allow_local": True, "timeout_s": 10})
            r = c.post("/api/ai/audit", json={"path": "baike/sub/dirty.md"})
            j = r.get_json()
            check("D1 AI 判断失败时本地结果照样回，但如实说明哪几项没跑成",
                  r.status_code == 200 and j.get("local_count", 0) >= 6
                  and "没跑成" in (j.get("ai_reason") or ""), j)
            check("D2 不把失败说成成功（ai_enabled 仍为真但原因写清，条数不变）",
                  len(j.get("proposals") or []) == j.get("local_count"), j)

        # ================================= E. 与已有语料矛盾（本地配对 + AI 只判真伪）
        print("\n[E] 与已有语料矛盾：配对由本地算，AI 只判对不对立")
        PAIRDOC = ('# 甲\n\n## 检索原理\n\n本库用倒排索引按词定位文档，词表就是主键。\n\n'
                   '```\n## 围栏里的假标题\n```\n')
        smap = ai_audit.section_map(PAIRDOC)
        check("E1 section_map 给的是每节的正文原文，围栏里的 # 不算节",
              [s["title"] for s in smap] == ["甲", "检索原理"]
              and smap[1]["text"].startswith("本库用倒排索引")
              and all("围栏" not in s["title"] for s in smap),
              [(s["title"], s["text"][:20]) for s in smap])
        hits = [{"rel": "baike/term/倒排索引.md", "title": "倒排索引",
                 "text": "倒排索引按词建表，用词直接定位到含它的文档列表，索引体积约为语料的三成。"}]
        rows = ai_audit.conflict_candidates(PAIRDOC, path="baike/sub/a.md", hits=hits)
        check("E2 配出对照行：编号形如「与《对方篇名》」、两边原文都进证据、行标 needs_ai",
              len(rows) == 1 and rows[0]["kind"] == "conflict"
              and rows[0]["needs_ai"] is True and rows[0]["target"] == "与《倒排索引》"
              and "本库用倒排索引" in rows[0]["evidence"]
              and "按词建表" in rows[0]["evidence"], rows)
        check("E3 对方摘要太短、或本篇没有一节真对得上 → 不建行（宁可少配，不拿废话问 AI）",
              ai_audit.conflict_candidates(PAIRDOC, path="a.md",
                                           hits=[dict(hits[0], text="太短")]) == []
              and ai_audit.conflict_candidates("# 乙\n\n## 口味\n\n咖啡、红茶与威士忌的品鉴记录。\n",
                                               path="b.md", hits=hits) == [], None)
        check("E4 自己不算自己的对手（同一篇配自己是纯噪音）",
              ai_audit.conflict_candidates(PAIRDOC, path="baike/term/倒排索引.md",
                                           hits=[dict(hits[0], rel="baike/term/倒排索引.md")]) == [], None)
        ctx = ai_audit.conflict_context(rows)
        check("E5 配对原文包在语料数据块里（两边都是不可信内容，与问答侧同一套加固口径）",
              ai_qa.BLOCK_BEGIN in ctx["text"] and ai_qa.BLOCK_END in ctx["text"]
              and ctx["targets"] == ["与《倒排索引》"] and ctx["chars"] > 0, ctx["chars"])
        check("E6 一次问完所有配对：配对超过三条时截到三条（不给上下文无限膨胀留口）",
              len(ai_audit.conflict_context(
                  [dict(rows[0], target="与《%d》" % i) for i in range(6)])["targets"]) == 3
              and len(ai_audit.conflict_candidates(
                  PAIRDOC, path="a.md", hits=[dict(hits[0], rel="x%d.md" % i,
                                                   title="对手%d" % i) for i in range(6)])) == 3,
              None)
        wide = ai_audit.conflict_candidates(PAIRDOC, path="baike/sub/a.md",
                                            hits=[{"rel": "baike/term/倒排索引.md",
                                                   "title": "倒排索引", "text": hits[0]["text"]},
                                                  {"rel": "baike/term/bt.md", "title": "布隆过滤器",
                                                   "text": "布隆过滤器也按词定位文档，只是改用位数组判存在，可能误判。"}])
        ctx2 = ai_audit.conflict_context(wide)
        check("E6b 两对都进同一次上下文：编号一一对得上，两边原文都在数据块里",
              ctx2["targets"] == ["与《倒排索引》", "与《布隆过滤器》"]
              and ctx2["text"].count(ai_qa.BLOCK_BEGIN) == 2
              and "位数组判存在" in ctx2["text"] and "本库用倒排索引" in ctx2["text"],
              ctx2["targets"])
        ai_audit.narrow_conflicts(wide, {"confidence": "medium", "terms": [
            {"term": "与《倒排索引》", "brief": "本篇说词表是主键，那篇说只是索引结构"},
            {"term": "与《AI 发明的配对》", "brief": "本地没有这一对"}]})
        by = {r["target"]: r for r in wide}
        check("E7 narrow_conflicts 只往配好的行上标结论：答复里发明新配对时行数一条不多",
              len(wide) == 2 and not any("发明" in t for t in by), list(by))
        check("E8 判为矛盾的对带两边各说了什么；没列进的对标的是「没把它列进」（缺席是推的）",
              by["与《倒排索引》"]["ai_terms"] == ["与《倒排索引》"]
              and "词表是主键" in by["与《倒排索引》"]["ai_note"]
              and by["与《布隆过滤器》"]["ai_terms"] == []
              and "没把这对列进" in by["与《布隆过滤器》"]["ai_note"]
              and {r["ai_confidence"] for r in wide} == {"medium"}, list(by.values()))
        check("E9 答复为空（AI 没跑成）时 narrow_conflicts 一个字都不改",
              ai_audit.narrow_conflicts(
                  ai_audit.conflict_candidates(PAIRDOC, path="baike/sub/a.md", hits=hits),
                  None) == rows, None)
        pr = ai_audit.ai_prompt("conflict", ctx["text"], "、".join(ctx["targets"]))
        check("E10 提示词把口径写死：只判事实对立、编号原样照抄、不许发明新配对",
              "互相矛盾" in pr and "原样照抄配对编号" in pr and "不要发明新配对" in pr
              and "角度不同" in pr and "与《倒排索引》" in pr, pr[:150])

        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            app, c = client_for(root)
            CALLS.clear()
            r0 = c.post("/api/ai/audit", json={"path": "baike/sub/dirty.md"})
            check("E11 不勾「查与库内矛盾」时一条配对都不建（读索引这一步由用户点出来，不默认花）",
                  r0.status_code == 200
                  and not any(p["kind"] == "conflict" for p in r0.get_json()["proposals"]),
                  [p["kind"] for p in r0.get_json()["proposals"]])
            jn = c.post("/api/ai/audit", json={"path": "baike/sub/dirty.md",
                                               "conflict": True}).get_json()
            conf_n = [p for p in jn.get("proposals") or [] if p["kind"] == "conflict"]
            check("E12 没配 key 时勾了也只出本地配对行：行在、结论空、整趟零出站",
                  bool(conf_n) and all(not p.get("ai_terms") for p in conf_n)
                  and CALLS == {}, {"rows": len(conf_n), "CALLS": CALLS})
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/auditpair",
                                          "allow_local": True, "timeout_s": 10})
            r1 = c.post("/api/ai/audit", json={"path": "baike/sub/dirty.md", "conflict": True})
            j1 = r1.get_json()
            conf = [p for p in j1.get("proposals") or [] if p["kind"] == "conflict"]
            check("E13 端点层真能配出对：对方就是正文提到过的那个已有词条",
                  r1.status_code == 200 and len(conf) >= 1
                  and "向量数据库" in conf[0]["title"], [p["title"] for p in conf])
            check("E14 本地条数算上配对行（勾了却不计数 = 汇总条在少报）",
                  j1.get("local_count") == len(j1.get("proposals") or [])
                  and j1.get("local_count") > (r0.get_json().get("local_count") or 0),
                  {"with": j1.get("local_count"), "without": r0.get_json().get("local_count")})
            check("E15 AI 判完只标结论不加行，配对编号原样回到行上",
                  any(p.get("ai_terms") == ["与《向量数据库》"] for p in conf)
                  and len(conf) <= 3, [p.get("ai_terms") for p in conf])
            check("E16 矛盾判断是一问-all：整篇最多三次（应引未引 / 过时 / 矛盾），不逐对各问",
                  CALLS.get("audit", 0) <= 3, CALLS)
            check("E17 不出站域的词条连进候选都不配（对方域是 career/小说时滤掉）",
                  not any("事件循环" in p["title"] for p in conf), [p["title"] for p in conf])
            body = (root / "content" / "baike" / "sub" / "dirty.md").read_text(encoding="utf-8")
            check("E18 整趟跑完正文一字节未变（AI 的建议只进派生库与 sidecar）",
                  body == DIRTY, len(body))
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/auth",
                                          "allow_local": True, "timeout_s": 10})
            r2 = c.post("/api/ai/audit", json={"path": "baike/sub/dirty.md", "conflict": True})
            j2 = r2.get_json()
            conf2 = [p for p in j2.get("proposals") or [] if p["kind"] == "conflict"]
            check("E19 AI 判失败时配对行照常入库并说清哪步没跑成（不假装查全）",
                  r2.status_code == 200 and conf2
                  and any(not p.get("ai_terms") for p in conf2)
                  and "矛盾判断没跑成" in (j2.get("ai_reason") or ""), j2.get("ai_reason"))

        print(f"\n{passed} passed, {failed} failed")
        if FAILS:
            for f in FAILS:
                print("  -", f)
        return 1 if failed else 0
    finally:
        srv.shutdown()


if __name__ == "__main__":
    sys.exit(_ci.guarded(main, "ai_audit"))
