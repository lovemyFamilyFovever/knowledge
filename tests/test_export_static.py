# -*- coding: utf-8 -*-
"""静态导出器契约测试（合并方案 §4.1 / §4.6，纯 Python、合成语料、无浏览器）。

三条判据（照规格 §4.6 第 1 条）：
  ① 同构：同一临时语料下，导出 JSON **逐字段等于** Flask 端点响应；
  ② 重写：非 fetch 的资源引用（模板 `/raw/`、CSS `url(/static/…)`）按 §4.1 清单改写；
  ③ 分诊覆盖：产物 JS 里出现的任何 `/api/` 字面量必须 ⊆ `ENDPOINT_TRIAGE`（§4.4）。

运行：python tests/test_export_static.py
语料一律 tempfile 现造，不读真实书库、不写仓库 indexes/。
"""
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from app.app import create_app  # noqa: E402
from export_static import (  # noqa: E402
    ENDPOINT_TRIAGE, TRIAGE_READ_MAP, TRIAGE_WRITE, doc_data_rel, export_site,
)

DOC_A = """---
title: "测试文档A"
tags: [AI, Agent]
source: "baike"
status: "imported"
---

# 测试文档A

## 第一节

这里讨论量子纠缠与贝尔不等式，配一张图：

![示意图](img/pic.png)

参见 [[职业笔记B]] 与 [[不存在的链接]]。
"""
DOC_A_HTML = "<!DOCTYPE html><html><body><h1>美化版A</h1></body></html>"
DOC_B = """---
title: "职业笔记B"
favorite: true
---

# 职业笔记B

简历要与岗位关键词对齐。
"""
PNG_1x1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000154a24f5e0000000049454e44ae426082")


def seed(root: Path) -> None:
    d = root / "content" / "ai" / "llm-and-agents"
    d.mkdir(parents=True)
    (d / "A.md").write_text(DOC_A, encoding="utf-8")
    (d / "A.html").write_text(DOC_A_HTML, encoding="utf-8")   # 美化版旁挂（has_html=True）
    (d / "img").mkdir()
    (d / "img" / "pic.png").write_bytes(PNG_1x1)              # 正文引用的图片
    c = root / "content" / "career"
    c.mkdir(parents=True)
    (c / "B.md").write_text(DOC_B, encoding="utf-8")
    inbox = root / "content" / "_inbox"
    inbox.mkdir()
    (inbox / "junk.md").write_text("x", encoding="utf-8")     # `_` 前缀：不进产物
    pr = root / "content" / "projects" / "dsh"
    pr.mkdir(parents=True)
    (pr / "secret.md").write_text("---\ntitle: 内部\n---\n\n凭据 cli_abcdef012345\n", encoding="utf-8")
    # 静态资产（真实仓里是仓库 static/；临时根里造最小实体 + 复制只读适配器，
    # 供拷贝、CSS 前缀与分诊审计断言）
    st = root / "static"
    (st / "pages").mkdir(parents=True)
    (st / "kb-core.js").write_text("window.KB={};\n", encoding="utf-8")
    (st / "reader.css").write_text(
        '@font-face{src:url("/static/vendor/fonts/x.woff2")}\n', encoding="utf-8")
    real_kbs = ROOT / "static" / "kb-static.js"
    if real_kbs.is_file():
        (st / "kb-static.js").write_text(real_kbs.read_text(encoding="utf-8"), encoding="utf-8")


passed = failed = 0


def check(name: str, cond: bool, extra="") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS {name}")
    else:
        failed += 1
        print(f"  FAIL {name} {extra}")


def _strip_js_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", "", text)


def _api_literals(js_dir: Path) -> set[str]:
    """扫描产品 JS（top-level *.js + pages/*.js，排除 vendor/min）里的 /api/ 字面量。"""
    out: set[str] = set()
    if not js_dir.is_dir():
        return out
    files = list(js_dir.glob("*.js")) + list((js_dir / "pages").glob("*.js"))
    for js in files:
        if js.name.endswith(".min.js"):
            continue
        text = _strip_js_comments(js.read_text(encoding="utf-8", errors="replace"))
        for m in re.finditer(r"/api/[A-Za-z0-9_/\-]*", text):
            v = m.group(0).rstrip("/")
            if v == "/api":
                continue  # 适配器的前缀探测（path.indexOf("/api/")），不是端点引用
            out.add(v)
    return out


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        seed(root)
        out = root / "site"

        summary = export_site(root, out, base="", tracked_only=False, keep_corpus=True)
        corpus = Path(summary["corpus_root"])
        check("导出返回摘要且文档数=2", summary["docs"] == 2, str(summary.get("docs")))

        # 生产者用同语料（staged）的另一个实例取端点响应做对照（同一份代码 === 端点响应）
        app = create_app(corpus)
        c = app.test_client()

        # ---------------- 产物结构（§4.1 / §4.6） ----------------
        for rel in ("index.html", "404.html", "data/tree.json", "data/links.json",
                    "data/meta.json", "data/palette/index.json", "data/doc/index.json",
                    "static/kb-core.js"):
            check(f"产物存在 {rel}", (out / rel).is_file())
        check("404.html == index.html（深链兜底）",
              (out / "404.html").read_text(encoding="utf-8")
              == (out / "index.html").read_text(encoding="utf-8"))
        check("_ 前缀目录不进产物（_inbox 不出现）",
              not [p.as_posix() for p in (out / "data").rglob("*") if "_inbox" in p.as_posix()])
        # 公开面硬边界（§4.1 / 不变量 10）：projects/ 这种 gitignore 目录从输入侧就不进产物
        _tree_ids = {d["id"] for d in json.loads(
            (out / "data" / "tree.json").read_text(encoding="utf-8"))["domains"]}
        check("projects/ 域不进树", "projects" not in _tree_ids)
        check("projects/ 不进 staging 语料", not (corpus / "content" / "projects").exists())
        check("内部文档内容不出现在任何产物里",
              not any("cli_abcdef012345" in p.read_text(encoding="utf-8", errors="replace")
                      for p in out.rglob("*") if p.is_file()))

        # ---------------- ① 逐字段同构：导出 JSON == Flask 端点响应 ----------------
        tree_exp = json.loads((out / "data" / "tree.json").read_text(encoding="utf-8"))
        check("/api/tree 同构", tree_exp == c.get("/api/tree").get_json())

        doms = {d["id"] for d in tree_exp["domains"]}
        check("树含 ai / career 两域", doms == {"ai", "career"}, str(doms))

        checked_docs = 0
        for dom in tree_exp["domains"]:
            for sobj in dom["subs"]:
                for d in sobj["docs"]:
                    rel = doc_data_rel(dom["id"], sobj["id"], d["name"])
                    got = json.loads((out / rel).read_text(encoding="utf-8"))
                    exp = c.get("/api/doc", query_string={
                        "domain": dom["id"], "sub": sobj["id"], "name": d["name"]}).get_json()
                    if got != exp:
                        check(f"/api/doc 同构 {rel}", False, f"\n got={str(got)[:160]}\n exp={str(exp)[:160]}")
                        break
                    checked_docs += 1
        check(f"/api/doc 逐篇同构（{checked_docs} 篇）", checked_docs == 2, str(checked_docs))

        links_exp = json.loads((out / "data" / "links.json").read_text(encoding="utf-8"))
        check("links.json 含两篇 md", set(links_exp) == {"ai/llm-and-agents/A.md", "career/B.md"},
              str(sorted(links_exp)))
        ok_links = all(
            links_exp[rel] == c.get("/api/links", query_string={"path": rel}).get_json()
            for rel in links_exp)
        check("/api/links 逐篇同构", ok_links)
        check("links.json 保留未解析双链标记",
              any(not x["resolved"] and "不存在的链接" in x["raw"]
                  for x in links_exp["ai/llm-and-agents/A.md"]["outgoing"]))
        check("links.json 已解析双链指向 B",
              any(x["resolved"] and "职业笔记" in x["title"]
                  for x in links_exp["ai/llm-and-agents/A.md"]["outgoing"]))
        check("/api/links 反向链：B 被 A 引用",
              any("测试文档A" in x["title"]
                  for x in links_exp["career/B.md"]["incoming"]))

        pal_exp = json.loads((out / "data" / "palette" / "index.json").read_text(encoding="utf-8"))
        check("/api/palette/index 同构", pal_exp == c.get("/api/palette/index").get_json())

        meta = json.loads((out / "data" / "meta.json").read_text(encoding="utf-8"))
        from app.store import load_taxonomy  # 同源：context processor 用的就是它
        tax = load_taxonomy(root / "content")
        check("meta.stats == /api/globalstats",
              meta["stats"] == c.get("/api/globalstats").get_json())
        check("meta.labels == taxonomy domains", meta["labels"] == tax["domains"])
        check("meta.hues == taxonomy hues", meta["hues"] == tax["hues"])
        check("meta 记录 kb_base", "kb_base" in meta)

        doc_index = json.loads((out / "data" / "doc" / "index.json").read_text(encoding="utf-8"))
        check("doc/index.json 把 domain/sub/name 映射到数据文件",
              doc_index.get("ai/llm-and-agents/A") == doc_data_rel("ai", "llm-and-agents", "A")
              and len(doc_index) == 2, str(doc_index))

        # ---------------- 检索索引（CJK bigram、分域懒加载） ----------------
        sp = out / "data" / "search" / "ai.json"
        check("生成分域检索索引 data/search/ai.json", sp.is_file())
        sidx = json.loads(sp.read_text(encoding="utf-8"))
        check("检索索引有 docs 与 index 两段",
              isinstance(sidx.get("docs"), list) and isinstance(sidx.get("index"), dict))
        check("检索索引含正文 bigram「量子」",
              "量子" in sidx["index"], str(list(sidx["index"])[:12]))
        check("检索索引 doc 指向 /doc 规范化 url",
              all(str(x["url"]).startswith("/doc/") for x in sidx["docs"]))

        # ---------------- ② 重写：/raw 与 CSS 绝对路径 ----------------
        check("正文引用的图片落到 site/raw/",
              (out / "raw" / "ai" / "llm-and-agents" / "img" / "pic.png").is_file())
        with_base = root / "site-kb"
        export_site(root, with_base, base="/kb", tracked_only=False)
        html = (with_base / "index.html").read_text(encoding="utf-8")
        check("KB_STATIC.readonly 注入 index.html", '"readonly":true' in html)
        check("KB_STATIC.base 注入为 /kb", '"base":"/kb"' in html)
        check("静态资源加 KB_BASE 前缀", 'src="/kb/static/kb-core.js' in html)
        check("模板 /raw 链接加 KB_BASE 前缀（新标签页打开美化版）",
              'href="/kb/raw/ai/llm-and-agents/A.html"' in html)
        check("不再出现裸 /static 引用", '"/static/' not in html)
        check("不再出现裸 /raw 引用", '"/raw/' not in html)
        css = (with_base / "static" / "reader.css").read_text(encoding="utf-8")
        check("CSS url(/static/…) 加前缀", 'url("/kb/static/vendor/fonts/' in css)
        check("空前缀档不改写（幂等）", '="/static/' in (out / "index.html").read_text(encoding="utf-8"))

        # ---------------- ③ 分诊覆盖：产物 JS 的 /api/ 字面量 ⊆ 分诊表（§4.4） ----------------
        check("静态产物含只读适配器 kb-static.js", (out / "static" / "kb-static.js").is_file())
        kbs = (out / "static" / "kb-static.js").read_text(encoding="utf-8")
        check("适配器把写端点归为 READ_ONLY", 'READ_ONLY' in kbs and 'WRITE' in kbs)
        check("适配器单点覆盖 docUrl/rawUrl", "KB.util.docUrl" in kbs and "KB.util.rawUrl" in kbs)

        literals = _api_literals(out / "static")
        unknown = sorted(l for l in literals if l not in ENDPOINT_TRIAGE)
        check("产物 JS 的 /api/ 字面量全部在分诊表内", not unknown, f"未分诊: {unknown}")
        repo_literals = _api_literals(ROOT / "static")
        repo_unknown = sorted(l for l in repo_literals if l not in ENDPOINT_TRIAGE)
        check("仓库产品 JS 的 /api/ 字面量全部在分诊表内", not repo_unknown, f"未分诊: {repo_unknown}")
        check("分诊表恒定覆盖前端实际调用的读端点",
              TRIAGE_READ_MAP >= {"/api/tree", "/api/doc", "/api/links",
                                  "/api/palette/index", "/api/search"})
        check("分诊表恒定覆盖全部写端点",
              TRIAGE_WRITE >= {"/api/save", "/api/note", "/api/favorite", "/api/move",
                               "/api/move/batch", "/api/delete", "/api/mkdir", "/api/rmdir",
                               "/api/rename-sub", "/api/rename-domain", "/api/tags",
                               "/api/import", "/api/inbox/ignore", "/api/inbox/purge"})
        check("readonly 缺失即测试红（负向：删一个写端点会掉出覆盖）",
              "/api/save" in ENDPOINT_TRIAGE and ENDPOINT_TRIAGE["/api/save"][0] == "readonly")

        # ---------------- 每个 map 端点都有产物背书 ----------------
        backing = {
            "/api/tree": out / "data" / "tree.json",
            "/api/doc": out / doc_data_rel("ai", "llm-and-agents", "A"),
            "/api/links": out / "data" / "links.json",
            "/api/palette/index": out / "data" / "palette" / "index.json",
            "/api/search": sp,
            "/api/globalstats": out / "data" / "meta.json",
        }
        missing = [p for p, f in backing.items() if not f.is_file()]
        check("每个 map 端点都有产物背书", not missing, str(missing))

        # ---------------- dry-run 不落盘 ----------------
        dry = root / "site-dry"
        export_site(root, dry, tracked_only=False, dry_run=True)
        check("--dry-run 不落盘", not dry.exists())

        import shutil as _sh
        _sh.rmtree(corpus, ignore_errors=True)

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
