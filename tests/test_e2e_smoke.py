# -*- coding: utf-8 -*-
"""知库端到端冒烟（彻查 P4）—— 把覆盖台账 §1 的 58 个端点全部打一遍。

运行：python tests/test_e2e_smoke.py

设计约束（AGENTS.md 不变量与彻查手册 §2 护栏）：
  · 全部请求打向 tempfile 迷你语料，**绝不读写真实 content/**；
  · 只读端点断 2xx / 预期重定向；写类端点断 ok:true **且磁盘状态真的变**；
  · 非法 / 越界入参断 4xx，且响应体不得泄露服务端绝对路径（本仓库历史 bug
    高发在 `_guard` 的 `detail: str(e)[:200]` —— 异常串里常带绝对路径）。
"""
import io
import json
import logging
import re
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.app import create_app  # noqa: E402

# 夹具故意用砧模型文件触发降级分支，app 会打一条带栈的 warning —— 那是被测行为，
# 不是测试出错，压掉以免淹没断言输出。
logging.getLogger("app").setLevel(logging.CRITICAL)

# ---------------------------------------------------------------- 迷你语料

DOC_A = """---
title: "测试文档A"
tags: [AI, Agent]
source: "baike"
status: "imported"
---

# 测试文档A

## 第一节

这里讨论量子纠缠与贝尔不等式。

参见 [[职业笔记B]] 与 [[不存在的链接]]。

## 第二节

补充内容，用于字数与切块。
"""

DOC_B = """---
title: "职业笔记B"
favorite: true
tags: [职业]
---

# 职业笔记B

简历要与岗位关键词对齐。
"""

TERM = """---
title: "术语甲"
tags: [AI]
source: "baike"
status: "imported"
---

# 术语甲

## 定义

**一句话定义：** 这是术语甲的一句话定义，用于复习抽卡。

## 常见误区

- 误区一：把术语甲当成术语乙。
"""

QUESTION = """---
title: "题目甲"
tags: [interview]
source: "interview"
status: "imported"
---

# 题目甲

### 1. 什么是指针｜初级

指针是保存变量地址的变量，解引用即访问该地址。

### 2. 什么是引用｜中级

引用是变量的别名，必须初始化且不可重新绑定。
"""

TAXONOMY = {
    "domains": {
        "ai": {"label": "人工智能", "hue": 210},
        "baike": {"label": "百科", "hue": 158},
        "interview": {"label": "面试", "hue": 340},
        "career": {"label": "职业", "hue": 30},
        "projects": {"label": "项目", "hue": 260},
        # 小说域全是 .txt/.epub/.pdf（FTS 只收 .md/.html，fts.py:110），
        # "search": false → 不进浮层筛选钮。真实 taxonomy.json 里也是这么标的，
        # 所以这条夹具既验"派生"，也验"过滤"。
        "小说": {"label": "小说", "hue": 0, "search": False},
    },
    "subs": {
        "llm-and-agents": "大模型与智能体",
        "algorithms": "算法与数据结构",
        "bigtech": "大厂面试",
        "dsh-agent": "DSH Agent",
        "architecture": "架构设计",
    },
    "sources": {"baike": "百科"},
    "status": {"imported": "已导入"},
}


def seed(root: Path) -> None:
    c = root / "content"
    # app/rag_models 必须存在非空文件：OnnxEmbedder.__init__ 会调 download_model()，
    # 缺文件时**联网拉 94MB 模型**（实测阻塞 71.8s，见覆盖台账 P4 发现 #3）。
    # 这里放砧文件让下载短路，再让 onnxruntime 加载失败 → 走"降级"分支。
    models = root / "app" / "rag_models"
    models.mkdir(parents=True)
    (models / "model.onnx").write_bytes(b"not-a-real-onnx")
    (models / "tokenizer.json").write_bytes(b"{}")
    meta = c / "_meta"
    meta.mkdir(parents=True)
    (meta / "taxonomy.json").write_text(
        json.dumps(TAXONOMY, ensure_ascii=False, indent=2), encoding="utf-8")

    inbox = c / "_inbox"
    inbox.mkdir()
    (inbox / "pending.md").write_text("---\ntitle: 待归档\n---\n\n正文\n", encoding="utf-8")
    (inbox / "keep.md").write_text("---\ntitle: 保留\n---\n\n正文\n", encoding="utf-8")
    assets = c / "_assets"
    assets.mkdir()
    (assets / "pic.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    ai = c / "ai" / "llm-and-agents"
    ai.mkdir(parents=True)
    (ai / "A.md").write_text(DOC_A, encoding="utf-8")
    (ai / "A.html").write_text("<!DOCTYPE html><html><body><h1>美化版A</h1></body></html>",
                               encoding="utf-8")
    (ai / "Only.html").write_text("<!DOCTYPE html><html><body><h1>独立美化版</h1></body></html>",
                                  encoding="utf-8")
    deep = ai / "deep"
    deep.mkdir()
    (deep / "Nested.md").write_text("---\ntitle: \"嵌套文档\"\n---\n\n# 嵌套\n", encoding="utf-8")

    (c / "ai" / "algorithms").mkdir()
    (c / "ai" / "algorithms" / "E.md").write_text(
        "---\ntitle: \"算法文档\"\ntags: [AI]\n---\n\n# 算法\n", encoding="utf-8")

    (c / "baike" / "algorithms").mkdir(parents=True)
    (c / "baike" / "algorithms" / "术语甲.md").write_text(TERM, encoding="utf-8")
    (c / "interview" / "bigtech").mkdir(parents=True)
    (c / "interview" / "bigtech" / "题目甲.md").write_text(QUESTION, encoding="utf-8")

    (c / "career").mkdir()
    (c / "career" / "B.md").write_text(DOC_B, encoding="utf-8")

    proj = c / "projects" / "dsh-agent" / "architecture"
    proj.mkdir(parents=True)
    (proj / "X.md").write_text("---\ntitle: \"架构分析\"\n---\n\n# X\n", encoding="utf-8")

    lib = c / "小说"
    lib.mkdir()
    (lib / "tiny.txt").write_text("第一章 开端\n\n正文内容。\n\n第二章 发展\n\n正文内容。\n",
                                  encoding="utf-8")
    (lib / "tiny.epub").write_bytes(b"PK\x03\x04fake-epub-placeholder")
    (lib / "tiny.pdf").write_bytes(b"%PDF-1.4\n%fake\n")
    (lib / "tiny.xlsx").write_bytes(b"PK\x03\x04fake-xlsx-placeholder")
    (lib / "tiny.mobi").write_bytes(b"BOOKMOBI\x00fake")


# ---------------------------------------------------------------- 断言基建

passed = failed = 0
FAILS: list[str] = []


def check(name: str, cond: bool, extra="") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS {name}")
    else:
        failed += 1
        FAILS.append(name)
        print(f"  FAIL {name} {extra}")


_DRIVE_RE = re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/]")


def leaks(text: str, root: Path) -> list[str]:
    """响应体里是否泄露服务端绝对路径 / 栈回溯。

    `(?<![A-Za-z])` 是必需的：否则 `http://www.w3.org/...`、`data:image/svg+xml`
    这类 URL scheme 会被误判成盘符（实测 error.html 头部的 svg xmlns 就是这么撞上的）。
    """
    hits = []
    for marker in (str(root), str(root).replace("\\", "/"), str(root.parent)):
        if marker and marker in text:
            hits.append(marker)
    if _DRIVE_RE.search(text):
        hits.append("drive-path")
    if "Traceback (most recent call last)" in text:
        hits.append("traceback")
    if 'File "' in text and ".py" in text:
        hits.append("source-frame")
    return hits


def body4xx(name: str, r, root: Path) -> None:
    """非法入参：断 4xx 且不泄露绝对路径。"""
    txt = r.get_data(as_text=True)
    lk = leaks(txt, root)
    check(f"{name} 非法入参 4xx", 400 <= r.status_code < 500, f"got {r.status_code}")
    check(f"{name} 非法入参不泄露绝对路径", not lk, f"leaked={lk} body={txt[:200]}")


def jget(r):
    try:
        return r.get_json() or {}
    except Exception:
        return {}


def main() -> int:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        # 必须 resolve()：本机 %TEMP% 是 8.3 短路径（C:\Users\ADMINI~1\...），
        # 而 create_app 内部多处用 content.resolve() 做前缀比较。两者混用时
        # /api/rmdir 与 /api/import 会 500 —— 那是**产品缺陷**，已单独固化为
        # tests/test_path_shortname.py 的复现探针，不该让本冒烟网跟着红。
        root = Path(td).resolve()
        seed(root)
        app = create_app(root)
        c = app.test_client()
        content = root / "content"

        # ================================================ A. 页面 GET（13 条）
        print("\n[A] 页面路由")
        for rule, needle, nm in [
            ("/", "从一次检索开始", "/ 占位页"),
            ("/home", "个域入口", "/home"),
            ("/favorites", "职业笔记B", "/favorites"),
            ("/tags", "AI", "/tags"),
            ("/glossary", None, "/glossary"),
            ("/governance", None, "/governance"),
            ("/inbox", None, "/inbox"),
            ("/quiz", None, "/quiz"),
            ("/review", None, "/review"),
            ("/search?q=量子", "测试文档", "/search 命中"),
            ("/stats", None, "/stats"),
        ]:
            r = c.get(rule)
            ok = r.status_code == 200 and (needle is None or needle in r.get_data(as_text=True))
            check(f"GET {rule} 200", ok, f"status={r.status_code}")
        r = c.get("/search?q=绝不存在词组zzz")
        check("GET /search 空结果不报错", r.status_code == 200 and "没有匹配" in r.get_data(as_text=True))
        r = c.get("/browse/ai/llm-and-agents")
        check("GET /browse/<domain>/<sub> 重定向到首篇",
              r.status_code == 302 and "/doc/ai/llm-and-agents/" in r.headers.get("Location", ""),
              f"status={r.status_code} loc={r.headers.get('Location')}")
        r = c.get("/doc/ai/llm-and-agents/A")
        check("GET /doc/... 200 且含标题", r.status_code == 200 and "测试文档A" in r.get_data(as_text=True))
        r = c.get("/doc/ai/llm-and-agents/Only.html")
        check("GET /doc/... 纯 HTML 独立篇可打开", r.status_code == 200)

        # ---- 浮层筛选钮 = taxonomy 的派生物（P8 清单第 3 条，2026-09-25）----
        # 以前 base.html 里手抄了一份域名单，是 taxonomy.json / store.DOMAIN_LABELS
        # 之外的第三份，键名一漂移就复现 §6 第 27 行（点了恒 0 结果）。
        # 现在名单从 JSON 派生，断言口径也跟着变成"派生结果 == 权威"：
        #   ① 钮的键必须是 JSON 里 search≠false 的那些域（小说域全是书库格式、FTS 不收，
        #      给钮就是骗人，所以过滤掉）；② 夹具里新增的域不用改模板就会自己出现（③）。
        shell = c.get("/").get_data(as_text=True)
        chip_keys = set(re.findall(r'kb-scope-chip" data-scope="([^"]*)"', shell))
        # 允许出现的键：JSON 里 search≠false 的域 ∪ 代码缺省回退（不变量 5："代码里的字典
        # 只是缺省回退"，临时实例的 JSON 不含 baike 之外的键，回退项仍会并入 LABELS）
        # ∪ 三个非域钮（全部/收藏/未掌握）。
        from app.store import DOMAIN_LABELS  # noqa: PLC0415
        allowed = ({k for k, v in TAXONOMY["domains"].items() if v.get("search") is not False}
                   | set(DOMAIN_LABELS) | {"", "fav", "unmastered"})
        check("浮层域钮由 taxonomy 派生（search:false 的域不给钮）",
              chip_keys <= allowed and "小说" not in chip_keys
              and {k for k, v in TAXONOMY["domains"].items()
                   if v.get("search") is not False} <= chip_keys,
              f"chip={sorted(chip_keys)} allowed={sorted(allowed)}")
        check("夹具里那个域键 ai 没在模板出现过，照样渲染出了钮（证明是派生不是抄写）",
              'data-scope="ai"' in shell and "人工智能" in shell)
        # 状态栏右端从写死 localhost:5001 改成 request.host：测试客户端的 Host 头是
        # localhost（无端口），所以正确渲染就是 "localhost"；写死时这里是 "localhost:5001"，
        # 摘掉动态化改动 → 本断言立刻红（变异验证过）。
        m_host = re.search(r'<span class="right"><span>([^<]+)</span></span>', shell)
        check("状态栏右端渲染的是当前请求的 host（不再写死 5001）",
              m_host is not None and m_host.group(1) == "localhost",
              f"got={m_host.group(1) if m_host else None}")
        r = c.get("/doc/ai/llm-and-agents/NOPE")
        check("GET /doc 不存在 → 404", r.status_code == 404, f"status={r.status_code}")

        # /raw 服务面（SERVABLE | MEDIA | LIBRARY）
        for rel, nm in [
            ("ai/llm-and-agents/A.html", "美化版"),
            ("ai/llm-and-agents/A.md", "md"),
            ("小说/tiny.txt", "txt"),
            ("小说/tiny.epub", "epub"),
            ("小说/tiny.pdf", "pdf"),
            ("小说/tiny.xlsx", "xlsx"),
            ("小说/tiny.mobi", "mobi"),
            ("_assets/pic.png", "media"),
        ]:
            r = c.get("/raw/" + rel)
            check(f"GET /raw/{nm} 直服 200", r.status_code == 200, f"status={r.status_code}")
        r = c.get("/raw/../app/app.py")
        check("GET /raw 目录穿越被拒", r.status_code in (400, 404), f"status={r.status_code}")
        r = c.get("/raw/ai/llm-and-agents/A.py")
        check("GET /raw 非白名单后缀被拒", r.status_code in (400, 404), f"status={r.status_code}")

        # ================================================ B. 只读 API
        print("\n[B] 只读 API")
        r = c.get("/api/tree")
        check("GET /api/tree 200 且有域", r.status_code == 200 and bool(jget(r).get("domains") or jget(r).get("tree")), str(jget(r))[:120])

        r = c.get("/api/dir/tree")
        d = jget(r)
        check("GET /api/dir/tree 200 含 cjk 标记", r.status_code == 200 and "cjk" in json.dumps(d, ensure_ascii=False))
        check("GET /api/dir/tree 不含 _ 前缀域", "_inbox" not in json.dumps(d, ensure_ascii=False))

        r = c.get("/api/doc?domain=ai&sub=llm-and-agents&name=A.md")
        d = jget(r)
        check("GET /api/doc 200 且正文非空",
              r.status_code == 200 and bool(d.get("content") or d.get("body") or d.get("doc")),
              str(d)[:120])

        r = c.get("/api/globalstats")
        d = jget(r)
        check("GET /api/globalstats 200 篇数>0", r.status_code == 200 and int(d.get("n_docs", 0)) > 0, str(d)[:120])

        r = c.get("/api/stats?path=ai/llm-and-agents/A.md")
        check("GET /api/stats 200", r.status_code == 200, f"status={r.status_code} {r.get_data(as_text=True)[:120]}")

        r = c.get("/api/substats?domain=ai&sub=llm-and-agents")
        check("GET /api/substats 200", r.status_code == 200, f"status={r.status_code}")

        r = c.get("/api/search?q=量子")
        d = jget(r)
        check("GET /api/search 200 有命中", r.status_code == 200 and int(d.get("total", 0)) >= 1, str(d)[:120])

        # §6 第 27 行的口径锁：domain 分面是**精确集合过滤**（routes_search.py:291），
        # 筛选钮发出的键一旦和 taxonomy 漂移，点它就是恒 0。这里必须"对的键有命中"，
        # 再补一条"别的键没命中"当对照——只断前者会因"过滤器根本没生效"而假绿。
        r = c.get("/api/search?q=量子&domain=ai")
        check("GET /api/search 带正确 domain 仍有命中（分面不是空过滤器）",
              r.status_code == 200 and int(jget(r).get("total", 0)) >= 1, str(jget(r))[:120])
        r = c.get("/api/search?q=量子&domain=baike")
        check("GET /api/search 换 domain 后过滤真的生效（0 命中，作上一条的对照组）",
              r.status_code == 200 and int(jget(r).get("total", 0)) == 0, str(jget(r))[:120])

        r = c.get("/api/search?q=量子&engine=fts")
        check("GET /api/search engine=fts 200", r.status_code == 200)

        r = c.get("/api/glossary?domain=baike")
        d = jget(r)
        check("GET /api/glossary 200 语义可用", r.status_code == 200 and d.get("ok") is not False, str(d)[:120])

        r = c.get("/api/palette/index")
        check("GET /api/palette/index 200", r.status_code == 200 and jget(r).get("ok") is not False, str(jget(r))[:120])

        r = c.get("/api/links?path=ai/llm-and-agents/A.md")
        d = jget(r)
        check("GET /api/links 200 含 outgoing/incoming",
              r.status_code == 200 and "outgoing" in d and "incoming" in d, str(d)[:120])

        r = c.get("/api/wikilink/suggest?q=职业")
        check("GET /api/wikilink/suggest 200", r.status_code == 200 and jget(r).get("ok") is not False, str(jget(r))[:120])

        r = c.get("/api/governance/scan")
        check("GET /api/governance/scan 200", r.status_code == 200 and jget(r).get("ok") is not False, str(jget(r))[:160])

        r = c.get("/api/docmark?path=ai/llm-and-agents/A.md")
        check("GET /api/docmark 200", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:120])

        # 本夹具里 app/rag_models 是砧文件 → 模型加载失败 → 断言"优雅降级"契约
        # （AGENTS：模型加载失败不拖垮阅读器）。**能用**的那条分支由 tests/test_rag.py 覆盖。
        t0 = time.time()
        r = c.get("/api/rag/status")
        dt = time.time() - t0
        check("GET /api/rag/status 200 且优雅降级 enabled=false",
              r.status_code == 200 and jget(r).get("enabled") is False, str(jget(r))[:160])
        check("GET /api/rag/status 不阻塞（无模型时不联网下载）", dt < 5.0, f"{dt:.1f}s")

        r = c.get("/api/rag?q=量子")
        check("GET /api/rag 组件不可用时 503（不炸 500）", r.status_code == 503, f"status={r.status_code}")
        check("GET /api/rag 503 不泄露绝对路径", not leaks(r.get_data(as_text=True), root))

        r = c.get("/api/ask/status")
        check("GET /api/ask/status 200", r.status_code == 200)

        # ---- learn 只读（先 sync 才有卡）----
        r = c.post("/api/learn/sync", json={"force": True})
        check("POST /api/learn/sync ok", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:160])

        cards = jget(c.get("/api/learn/cards")).get("items") or []
        check("GET /api/learn/cards 有卡", bool(cards), f"n={len(cards)}")
        card_id = cards[0]["card_id"] if cards else ""

        r = c.get("/api/learn/due")
        check("GET /api/learn/due 200", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:120])

        r = c.get("/api/learn/mastery")
        check("GET /api/learn/mastery 200", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:120])

        r = c.get("/api/learn/mock")
        check("GET /api/learn/mock 200", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:120])

        r = c.get("/api/learn/today")
        check("GET /api/learn/today 200", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:120])

        r = c.get("/api/learn/recent_read?days=7")
        check("GET /api/learn/recent_read 200", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:120])

        r = c.get("/api/learn/roam?from=" + "术语甲")
        check("GET /api/learn/roam 200", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:120])

        r = c.post("/api/learn/review", json={"card_id": card_id, "q": 4, "elapsed_ms": 1200})
        check("POST /api/learn/review ok", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:160])

        r = c.post("/api/wikilink/check", json={"body": "见 [[职业笔记B]] 与 [[没有这个]]。"})
        d = jget(r)
        check("POST /api/wikilink/check 200 且识别死链",
              r.status_code == 200 and d.get("ok") is True and int(d.get("dead_n", 0)) >= 1, str(d)[:160])

        # ================================================ C. 写类 API（磁盘断言）
        print("\n[C] 写类 API（含磁盘状态断言）")

        # /api/save 新建（自动补 frontmatter，写回唯一事实源）
        r = c.post("/api/save", json={"path": "career/新文档C.md",
                                      "content": "# 新文档C\n\n正文段落。\n"})
        p = content / "career" / "新文档C.md"
        src = p.read_text(encoding="utf-8") if p.is_file() else ""
        check("POST /api/save 新建 ok", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:160])
        check("POST /api/save 磁盘真落盘且补 fm", p.is_file() and src.startswith("---") and "新文档C" in src)

        # /api/save 编辑覆盖
        r = c.post("/api/save", json={"path": "career/新文档C.md",
                                      "content": "---\ntitle: \"新文档C\"\n---\n\n改后正文。\n"})
        check("POST /api/save 覆盖 ok", r.status_code == 200 and "改后正文" in p.read_text(encoding="utf-8"))

        # /api/favorite 切换（写 fm，不改正文）
        before = p.read_text(encoding="utf-8")
        r = c.post("/api/favorite", json={"path": "career/新文档C.md"})
        after = p.read_text(encoding="utf-8")
        check("POST /api/favorite 开 ok", r.status_code == 200 and jget(r).get("favorite") is True, str(jget(r))[:120])
        check("POST /api/favorite 磁盘 fm 真变", before != after and "favorite" in after)
        r = c.post("/api/favorite", json={"path": "career/新文档C.md"})
        check("POST /api/favorite 关 ok", r.status_code == 200 and jget(r).get("favorite") is False)

        # /api/tags set/add/remove
        r = c.post("/api/tags", json={"path": "career/新文档C.md", "op": "add", "tags": ["甲", "乙"]})
        check("POST /api/tags add ok", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:120])
        check("POST /api/tags 磁盘 tags 真写入", "甲" in p.read_text(encoding="utf-8"))
        r = c.post("/api/tags", json={"path": "career/新文档C.md", "op": "remove", "tags": ["甲"]})
        t = p.read_text(encoding="utf-8")
        check("POST /api/tags remove ok", r.status_code == 200 and "甲" not in t and "乙" in t, t[:160])

        # /api/note 追加 sidecar
        r = c.post("/api/note", json={"path": "career/新文档C.md", "text": "一条备注"})
        npath = content / "career" / "新文档C.md.notes.md"
        check("POST /api/note ok", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:120])
        check("POST /api/note sidecar 落盘且主文件未被污染",
              npath.is_file() and "一条备注" in npath.read_text(encoding="utf-8")
              and "一条备注" not in p.read_text(encoding="utf-8"))

        # /api/docmark set
        r = c.post("/api/docmark", json={"path": "career/新文档C.md", "mark": "read", "on": True})
        check("POST /api/docmark read ok", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:120])
        d = jget(c.get("/api/docmark?path=career/新文档C.md"))
        check("POST /api/docmark 状态可读回 read=True", d.get("read") is True, str(d)[:120])
        r = c.post("/api/docmark", json={"path": "career/新文档C.md", "mark": "mastered", "on": True})
        check("POST /api/docmark mastered ok", r.status_code == 200 and jget(r).get("mastered") is True, str(jget(r))[:120])

        # /api/track 阅读事件（不得污染语料）
        b4 = p.read_bytes()
        r = c.post("/api/track", json={"path": "career/新文档C.md", "event": "open"})
        check("POST /api/track open ok", r.status_code == 200 and jget(r).get("ok") is True)
        r = c.post("/api/track", json={"path": "career/新文档C.md", "event": "read_minute", "seconds": 60})
        check("POST /api/track read_minute ok", r.status_code == 200)
        r = c.post("/api/track", json={"path": "career/新文档C.md", "event": "finish"})
        check("POST /api/track finish ok", r.status_code == 200)
        check("POST /api/track 语料字节零变化（不变量 6）", p.read_bytes() == b4)

        # /api/mkdir
        r = c.post("/api/mkdir", json={"domain": "ai", "parent": "", "name": "新建子域",
                                       "label": "新建子域显示名"})
        check("POST /api/mkdir ok", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:160])
        check("POST /api/mkdir 目录真创建", (content / "ai" / "新建子域").is_dir())

        # /api/move
        r = c.post("/api/move", json={"src": "ai/llm-and-agents/deep/Nested.md",
                                      "dst": "ai/新建子域/Nested.md"})
        check("POST /api/move ok", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:160])
        check("POST /api/move 源消失目标出现",
              (content / "ai" / "新建子域" / "Nested.md").is_file()
              and not (content / "ai" / "llm-and-agents" / "deep" / "Nested.md").exists())

        # /api/move/batch
        r = c.post("/api/move/batch", json={"items": [
            {"src": "ai/algorithms/E.md", "dst": "ai/新建子域/E.md"}]})
        d = jget(r)
        check("POST /api/move/batch ok", r.status_code == 200 and d.get("ok") is True, str(d)[:160])
        check("POST /api/move/batch 落盘", (content / "ai" / "新建子域" / "E.md").is_file())

        # /api/tag/merge
        r = c.post("/api/tag/merge", json={"src": "乙", "dst": "AI", "apply": False})
        d = jget(r)
        check("POST /api/tag/merge dry-run ok", r.status_code == 200 and d.get("ok") is True, str(d)[:160])
        r = c.post("/api/tag/merge", json={"src": "乙", "dst": "AI", "apply": True})
        check("POST /api/tag/merge apply ok", r.status_code == 200 and jget(r).get("ok") is True)
        check("POST /api/tag/merge 磁盘标签真改写",
              "乙" not in p.read_text(encoding="utf-8") and "AI" in p.read_text(encoding="utf-8"))

        # /api/rename-sub（目录改名 + taxonomy 迁移）
        r = c.post("/api/rename-sub", json={"domain": "ai", "sub": "新建子域", "new": "改名子域"})
        check("POST /api/rename-sub ok", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:160])
        check("POST /api/rename-sub 目录真改名且文档随行",
              (content / "ai" / "改名子域" / "Nested.md").is_file()
              and not (content / "ai" / "新建子域").exists())

        # /api/rmdir（整树软删进 _trash）
        r = c.post("/api/rmdir", json={"domain": "ai", "sub": "改名子域"})
        d = jget(r)
        trash_rel = d.get("to_trash", "")
        check("POST /api/rmdir ok", r.status_code == 200 and d.get("ok") is True, str(d)[:160])
        check("POST /api/rmdir 进 _trash 且原路径消失",
              bool(trash_rel) and (content / trash_rel / "Nested.md").is_file()
              and not (content / "ai" / "改名子域").exists())

        # /api/rename-domain（整域改名）
        r = c.post("/api/rename-domain", json={"domain": "career", "new": "career2"})
        check("POST /api/rename-domain ok", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:160])
        check("POST /api/rename-domain 目录真改名",
              (content / "career2" / "新文档C.md").is_file() and not (content / "career").exists())

        # /api/import（multipart）
        import io
        r = c.post("/api/import", data={
            "domain": "ai", "sub": "llm-and-agents",
            "files": (io.BytesIO("# 导入文档\n\n正文。\n".encode("utf-8")), "导入文档.md"),
        }, content_type="multipart/form-data")
        check("POST /api/import ok", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:160])
        check("POST /api/import 磁盘真落盘",
              (content / "ai" / "llm-and-agents" / "导入文档.md").is_file())
        # 同名不覆盖 → ~2 避让（_free_md 从 2 起编号）
        r = c.post("/api/import", data={
            "domain": "ai", "sub": "llm-and-agents",
            "files": (io.BytesIO("# 导入文档2\n".encode("utf-8")), "导入文档.md"),
        }, content_type="multipart/form-data")
        check("POST /api/import 同名不覆盖（~2 避让）",
              (content / "ai" / "llm-and-agents" / "导入文档~2.md").is_file(), str(jget(r))[:160])
        check("POST /api/import 原文件未被覆盖",
              "导入文档2" not in (content / "ai" / "llm-and-agents" / "导入文档.md").read_text(encoding="utf-8"))

        # /api/inbox/ignore
        r = c.post("/api/inbox/ignore", json={"path": "_inbox/pending.md", "scope": "file"})
        d = jget(r)
        ig = content / "_meta" / "inbox-ignore.json"
        check("POST /api/inbox/ignore ok", r.status_code == 200 and d.get("ok") is True, str(d)[:160])
        check("POST /api/inbox/ignore 忽略清单落盘",
              ig.is_file() and "pending.md" in ig.read_text(encoding="utf-8"))
        # scope=dir 的契约（轮次 27 修）：path **就是**要被忽略的目录本身，
        # 后端不许再往上取一层父目录 —— 旧实现会把 "_inbox/开发产物" 记成
        # 它的上一级（根级时甚至退化成一条匹配不到的 file 规则），于是"点了忽略、行还在、
        # 清单里躺着假规则"（台账 §6 第 34 行）。
        r = c.post("/api/inbox/ignore", json={"path": "_inbox/开发产物", "scope": "dir"})
        d = jget(r)
        rules = d.get("rules") or {}
        check("POST /api/inbox/ignore scope=dir 记的是我给的那个目录（不再上溯一层）",
              r.status_code == 200 and "开发产物" in (rules.get("dirs") or [])
              and "开发产物" not in (rules.get("files") or []), str(d)[:200])
        r = c.post("/api/inbox/ignore", json={"path": "_inbox", "scope": "dir"})
        check("POST /api/inbox/ignore 拒绝忽略整个 _inbox（那等于让收件箱从此不进任何索引）",
              r.status_code == 400 and jget(r).get("ok") is False, str(jget(r))[:160])

        # /api/inbox/purge（全仓唯一物理删除接口）
        r = c.post("/api/inbox/purge", json={"path": "_inbox/keep.md"})
        check("POST /api/inbox/purge ok", r.status_code == 200 and jget(r).get("ok") is True, str(jget(r))[:160])
        check("POST /api/inbox/purge 物理删除生效",
              not (content / "_inbox" / "keep.md").exists())

        # /api/delete（软删 → _trash，含旁挂）
        r = c.post("/api/delete", json={"path": "career2/新文档C.md"})
        d = jget(r)
        check("POST /api/delete ok", r.status_code == 200 and d.get("ok") is True, str(d)[:200])
        check("POST /api/delete 主文件与 notes 旁挂都进 _trash",
              not (content / "career2" / "新文档C.md").exists()
              and not (content / "career2" / "新文档C.md.notes.md").exists()
              and len(list((content / "_trash").rglob("新文档C.md"))) >= 1
              and len(list((content / "_trash").rglob("新文档C.md.notes.md"))) >= 1)

        # ================================================ D. 非法入参 + 路径泄露
        print("\n[D] 非法入参（4xx + 不泄露绝对路径）")

        bad_posts = [
            ("/api/save", {"path": "../../etc/passwd", "content": "x"}),
            ("/api/save", {"path": "_inbox/x.md", "content": "x"}),
            ("/api/save", {"path": "ai/llm-and-agents/A.html", "content": "x"}),
            ("/api/delete", {"path": "../../etc/passwd"}),
            ("/api/delete", {"path": "小说/tiny.txt"}),
            ("/api/delete", {"path": "ai/llm-and-agents/A.html"}),
            ("/api/move", {"src": "../../x.md", "dst": "ai/x.md"}),
            ("/api/move", {"src": "ai/llm-and-agents/A.md", "dst": "../escape.md"}),
            ("/api/move", {"src": "ai/llm-and-agents/NOEXIST.md", "dst": "ai/x.md"}),
            ("/api/move/batch", {"items": []}),
            ("/api/mkdir", {"domain": "_inbox", "name": "x"}),
            ("/api/mkdir", {"domain": "ai", "name": ""}),
            ("/api/rmdir", {"domain": "_inbox", "sub": ""}),
            ("/api/rmdir", {"domain": "ai", "sub": "不存在的目录"}),
            ("/api/rename-sub", {"domain": "ai", "sub": "llm-and-agents", "new": "algorithms"}),
            ("/api/rename-sub", {"domain": "ai", "sub": "_inbox", "new": "x"}),
            ("/api/rename-domain", {"domain": "no-such-domain", "new": "x"}),
            ("/api/rename-domain", {"domain": "ai", "new": "_bad"}),
            ("/api/inbox/purge", {"path": "ai/llm-and-agents/A.md"}),
            ("/api/inbox/purge", {"path": "_inbox/../../ai/llm-and-agents/A.md"}),
            ("/api/inbox/purge", {"path": "_inbox/不存在.md"}),
            ("/api/favorite", {"path": "../../x.md"}),
            ("/api/note", {"path": "../../x.md", "text": "x"}),
            ("/api/tags", {"path": "../../x.md", "tags": ["a"]}),
            ("/api/docmark", {"path": "../../x.md", "mark": "read"}),
            ("/api/docmark", {"path": "ai/llm-and-agents/A.md", "mark": "bogus"}),
            ("/api/tag/merge", {"src": "", "dst": "x"}),
            ("/api/learn/review", {"card_id": "", "q": 3}),
            ("/api/learn/review", {"card_id": "nope", "q": 3}),
            ("/api/learn/review", {"card_id": "nope"}),
            ("/api/wikilink/check", {"body": ""}),
            ("/api/ask", {"q": ""}),
        ]
        for path, payload in bad_posts:
            body4xx(f"POST {path} {json.dumps(payload, ensure_ascii=False)[:48]}",
                    c.post(path, json=payload), root)

        bad_gets = [
            "/api/docmark?path=../../x.md",
            "/api/stats?path=../../x.md",
            "/api/links?path=../../x.md",
            "/api/learn/due?kind=bogus",
            "/api/learn/due?new_ratio=abc",
            "/api/learn/due?new_ratio=9",
            "/api/learn/cards?kind=bogus",
            "/api/learn/roam",
            "/api/raw/../app/app.py",
        ]
        for path in bad_gets:
            body4xx(f"GET {path}", c.get(path), root)

        # 无入参校验但无害的只读端点：断「不 5xx、不泄露路径」而非强求 4xx
        for path in ("/api/glossary?domain=../", "/api/wikilink/suggest?limit=abc",
                     "/api/palette/index?sig=../.."):
            r = c.get(path)
            txt = r.get_data(as_text=True)
            check(f"GET {path} 不 5xx 且不泄露路径",
                  r.status_code < 500 and not leaks(txt, root), f"status={r.status_code}")

        # 合法但无名额：/api/ask 无 key → 503（不得联网）
        r = c.post("/api/ask", json={"q": "量子"})
        check("POST /api/ask 未配置 key → 503 not_configured",
              r.status_code == 503 and jget(r).get("error") == "not_configured", str(jget(r))[:160])

        # ================================================ E. 不变量旁证
        print("\n[E] 不变量旁证")
        check("content/ 下无 .db 落地", not list(content.rglob("*.db")))
        d = c.get("/api/dir/tree").get_json()
        dump = json.dumps(d, ensure_ascii=False)
        for hidden in ("_inbox", "_assets", "_trash", "_meta"):
            check(f"/api/dir/tree 不含 {hidden}", hidden not in dump)
        check("删除后的文档不再被 FTS 命中",
              int(jget(c.get("/api/search?q=改后正文")).get("total", 0)) == 0)

    print(f"\n{passed} passed, {failed} failed")
    if FAILS:
        print("FAILED CASES:")
        for f in FAILS:
            print("  -", f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
