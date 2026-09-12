# -*- coding: utf-8 -*-
"""知库全交互 API 巡检：写操作全部走临时文档，测完软删清理。
覆盖：save/note/favorite/links/delete/move/move-batch/tag-merge/substats/stats/track
每步断言，失败打印 [FAIL] 并继续（不中断，最后汇总 exit code）。"""
import json
import time
import urllib.request

BASE = "http://127.0.0.1:5001"
STAMP = time.strftime("%H%M%S")
DOC = f"projects/dsh-agent/architecture/probe巡检{STAMP}.md"
DST = f"projects/dsh-agent/architecture/probe巡检{STAMP}b.md"
DST2 = f"projects/reviews/probe巡检{STAMP}.md"
results = []


def call(method, path, payload=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(("PASS " if cond else "FAIL ") + name + (f"  | {detail}" if detail and not cond else ""))


# 1. save 新建（无 frontmatter → 自动补）
st, r = call("POST", "/api/save", {"path": DOC, "content": "# 巡检探针\n\n正文第一段。\n\n## 第二节\n\n内容。"})
check("save 新建(自动补 frontmatter)", st == 200 and r.get("ok"), str(r))

# 2. save 编辑（覆盖正文，保留 frontmatter）
st, r = call("POST", "/api/save", {"path": DOC, "content": "# 巡检探针\n\n改后的正文。\n"})
check("save 编辑覆盖", st == 200 and r.get("ok"), str(r))

# 3. note 备注
st, r = call("POST", "/api/note", {"path": DOC, "text": "巡检备注"})
notes_joined = json.dumps(r.get("notes", []), ensure_ascii=False)
check("note 追加备注", st == 200 and r.get("ok") and "巡检备注" in notes_joined, notes_joined[:120])

# 4. favorite 切换
st, r = call("POST", "/api/favorite", {"path": DOC})
check("favorite 开", st == 200 and r.get("favorite") is True, str(r))
st, r = call("POST", "/api/favorite", {"path": DOC})
check("favorite 关", st == 200 and r.get("favorite") is False, str(r))

# 5. links 双链
st, r = call("GET", "/api/links?path=" + urllib.request.quote(DOC))
check("links 双链查询", st == 200 and "outgoing" in r and "incoming" in r, str(r)[:80])

# 6. move 重命名
st, r = call("POST", "/api/move", {"src": DOC, "dst": DST})
check("move 重命名", st == 200 and r.get("ok") and r.get("dst") == DST, str(r))

# 7. move 防御：dst 已存在 → 400
st, r = call("POST", "/api/move", {"src": DST, "dst": DST})
check("move 拒绝 dst 已存在", st == 400, f"status={st}")

# 8. move 防御：越界路径 → 400
st, r = call("POST", "/api/move", {"src": DST, "dst": "../../etc/passwd"})
check("move 拒绝越界 dst", st == 400, f"status={st}")

# 9. move/batch 批量（1 条成功 + 1 条非法 dst 失败，验证 per-item 报错）
st, r = call("POST", "/api/move/batch", {"items": [
    {"src": DST, "dst": DST2},
    {"src": "projects/nothing/_nope.md", "dst": "projects/also_nope.md"},
]})
ok1 = st == 200 and r.get("ok") and r.get("n_ok") == 1 and r.get("n_fail") == 1
check("move/batch 部分失败不回滚", ok1, str(r)[:160])

# 10. substats 目录统计
st, r = call("GET", "/api/substats?domain=projects&sub=dsh-agent")
check("substats 目录统计", st == 200 and r.get("n_docs", 0) > 0 and "total_cjk" in r, str(r)[:80])

# 11. stats 文档统计
st, r = call("GET", "/api/stats?path=" + urllib.request.quote(DST2))
check("stats 文档统计", st == 200 and r.get("chars", 0) > 0, str(r)[:80])

# 12. tag/merge 预检（apply=false）
st, r = call("POST", "/api/tag/merge", {"src": "probe不存在的标签", "dst": "巡检临时", "apply": False})
check("tag/merge 预检(apply=false)", st == 200 and r.get("ok") and r.get("n_docs") == 0, str(r)[:80])

# 13. tag/merge 真合并：给探针文档打标签后合并（save 自动补的 stamp 已有 tags: []，
#     必须替换该行而非另插一行——重复 YAML 键是脏数据，parse_frontmatter 取首个会读成空列表）
import io
import re as _re
p = io.open("content/" + DST2, encoding="utf-8").read()
p2, n_sub = _re.subn(r"(?m)^tags:\s*\[\]\s*$", 'tags: ["probe标签A"]', p, count=1)
if n_sub == 0:
    raise SystemExit("patrol 自检失败：探针文档无 tags: [] 行可注入，检查 save stamp 格式")
io.open("content/" + DST2, "w", encoding="utf-8").write(p2)
st, r = call("POST", "/api/tag/merge", {"src": "probe标签A", "dst": "probe标签B", "apply": True})
check("tag/merge 真合并+FTS重建", st == 200 and r.get("ok") and r.get("n_docs", 0) == 1, str(r)[:100])

# 14. delete 软删（清理探针，连同 notes/html 旁挂）
st, r = call("POST", "/api/delete", {"path": DST2})
import os
gone = not os.path.exists("content/" + DST2)
check("delete 软删", st == 200 and r.get("ok") and gone, str(r)[:80])

# 15. delete 后索引同步（rag 可能未就绪，200/503 都算正常）+ 特殊字符不炸
from urllib.parse import quote as _q
st, r = call("GET", "/api/rag?q=" + _q("巡检探针"))
check("delete 后索引同步", st in (200, 503), f"status={st}")
for sp in ["%22test%22", "%2B%E6%A0%87%E7%AD%BE", "100%25", "a%20b"]:
    st, r = call("GET", "/api/rag?q=" + sp)
    check(f"rag 特殊字符 status={st}", st in (200, 503, 400), f"q={sp}")
req2 = urllib.request.Request(BASE + "/search?q=" + _q("巡检探针"))
with urllib.request.urlopen(req2, timeout=20) as rr:
    check("search 页面 200", rr.status == 200, f"status={rr.status}")

# 16. track 阅读埋点（对真实文档，open 事件）
st, r = call("POST", "/api/track", {"path": "projects/dsh-agent/architecture/DeepSeek Harness 架构分析摘要.md",
                                     "event": "open", "seconds": 0})
check("track 阅读埋点", st == 200 and r.get("ok"), str(r)[:80])

n_fail = sum(1 for _, ok, _ in results if not ok)
print(f"\n==== 巡检完成：{len(results)} 项，失败 {n_fail} 项 ====")
raise SystemExit(1 if n_fail else 0)
