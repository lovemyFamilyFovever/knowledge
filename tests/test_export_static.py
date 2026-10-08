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
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from app.app import create_app  # noqa: E402
from export_static import (  # noqa: E402
    ENDPOINT_TRIAGE, TRIAGE_READ_MAP, TRIAGE_WRITE, check_base, doc_data_rel, export_site,
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
    # PWA 三件：sw 源 + 注册件 + 图标（临时根照抄真实仓，否则测的是"缺件"而不是契约）
    # 整个 static/ 都照抄：预热清单是**从产物壳扫出来的**，缺了 style.css 就只会测到"丢了"，
    # 测不到"一条不丢"这条真正要守的不变量。
    shutil.copytree(ROOT / "static", st, dirs_exist_ok=True)


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
        for rel in ("index.html", "404.html", "data/tree.json", "data/dir-tree.json", "data/links.json",
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

        dir_exp = json.loads((out / "data" / "dir-tree.json").read_text(encoding="utf-8"))
        check("/api/dir/tree 同构", dir_exp == c.get("/api/dir/tree").get_json())
        check("dir-tree 内联文档清单可用",
              any(bool(s.get("docs")) for d in dir_exp.get("domains", []) for s in d.get("subs", [])))

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
        check("doc_data_rel 不在产物路径里写百分号编码（否则 GH Pages 解码后 404）",
              "%" not in doc_data_rel("ai", "提示词", "X"))
        check("产物 data/ 下不存在百分号编码文件名",
              not any("%" in p.name for p in (out / "data").rglob("*")))

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
        # av() 在导出时 stat 不到 static/（渲染发生在拷贝之前，KB_ROOT 是只含语料的 staging），
        # 必须退回构建号。全站 ?v=0 等于**没有 cache-busting**：SW 的 static 档是缓存优先，
        # 于是"新壳 + 上一版 CSS/JS"的混血状态会一直留着（2026-10-08 用户实拍改了不生效）。
        vers = set(re.findall(r"[?&]v=([0-9a-zA-Z]+)", html))
        check("公网每个资源都带同一个非零构建号 ?v=<sha>",
              len(vers) == 1 and vers != {"0"} and "" not in vers, sorted(vers))
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
        check("「继续上次阅读」的数据源就是 app.js 每次开文档写的 kb-last-doc"
              "（适配器不再有第二份最近阅读，见下面那条 137 组的断言）",
              '"kb-last-doc"' in kbs and "lsGet(RKEY" not in kbs)
        check("适配器含路由桥（bridgeClicks/bridgeRouting）",
              "bridgeClicks" in kbs and "bridgeRouting" in kbs)
        check("适配器改写根相对链接为 KB_BASE 前缀",
              'a[href^="/"]' in kbs)

        # ---------------- ④ 只读裁剪与公网口径（§4.3 · A1+A2） ----------------
        appjs = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
        kbc = (ROOT / "static" / "kb-core.js").read_text(encoding="utf-8")
        base_html = (ROOT / "app" / "templates" / "base.html").read_text(encoding="utf-8")
        check("只读判据只有一个来源（app.js 读 KB_STATIC.readonly）",
              "const KB_READ_ONLY = !!(window.KB_STATIC && window.KB_STATIC.readonly);" in appjs)
        check("右键菜单在 openCtxMenu 单点过滤 roHide，且空菜单不弹",
              "if (KB_READ_ONLY)" in appjs and "!it.roHide" in appjs
              and "if (!items.some(it => it !== \"-\")) return;" in appjs)
        for lab in ["移动到…", "重命名…", "删除…", "在此新建文档…", "新建子目录…",
                    "导入文档…", "重命名目录…", "删除目录…", "新增二级目录…",
                    "重命名域…", "删除域…", "统计信息"]:
            check(f"写操作菜单项「{lab}」带 roHide",
                  ('label: "' + lab + '", roHide: true') in appjs)
        check("复制类菜单项不受只读裁剪（公网仍可复制原文/链接）",
              'label: "复制 Markdown 原文", fn:' in appjs and 'label: "复制域名", fn:' in appjs)
        check("拖拽移动与近 7 日阅读图在只读档不接线",
              appjs.count("if (KB_READ_ONLY) return;") >= 2)
        check("树内文档的 draggable 随只读档关闭",
              # 曾经有第二处（第二列文档列表 renderDocList），随需求 #11 一起删了；
              # 计数写死就是为了让"再抄一份渲染"或"删掉一处忘了改这里"都当场红
              appjs.count('draggable="${KB_READ_ONLY ? "false" : "true"}"') == 1)
        check("编辑器快捷键在只读档不进帮助（registry 单点过滤）",
              'scope: "editor", roHide: true' in kbc and "VISIBLE_KEYS" in kbc
              and "keys.registry = VISIBLE_KEYS;" in kbc)
        check("引擎钮选择器用 class 不用 id（id 版从未命中，公网实测语义钮照样在）",
              '#kb-search-engines [data-eng' not in kbs
              and '.kb-search-engines [data-eng="semantic"]' in kbs
              and '.kb-search-engines [data-eng="hybrid"]' in kbs)
        check("状态栏四段各留一个类名钩子供适配器定位",
              all(c in base_html for c in ["sb-acc", "sb-src", "sb-fts", "sb-host"]))
        check("钩子类名活到产物里（导出没把它丢掉）",
              all(c in html for c in ["sb-acc", "sb-src", "sb-fts", "sb-host"]))
        check("适配器换成公网口径（本地阅读器 / localhost / 冻结标题都不留）",
              all(x in kbs for x in ["公网只读档", "location.host", ".sb-host",
                                     "篇可全文检索", "fixTitle"]))
        check("域筛选钮按导出树裁剪（不抄第二份域名单）",
              "pruneScopeChips" in kbs and "tree.domains" in kbs)

        # ---------------- ⑤ 两颗空转钮清除 + 全库快照恢复（2026-10-07 用户拍板） ----------------
        check("模板里再无 fav / unmastered 两颗空转钮",
              'data-scope="fav"' not in base_html and 'data-scope="unmastered"' not in base_html)
        check("app.js 里为它们留的特判一并删除",
              'unmastered' not in appjs)
        check("全库快照按钮不再被只读层隐藏",
              "#global-stats-btn" not in kbs)
        check("快照面板内两处本地专属被挡（月度趋势跳 /stats、收件箱待归档）",
              '.kbm-stats a[href$="/stats"]' in kbs and ".gs-inbox" in kbs
              and 'class="gs-inbox"' in appjs)
        check("/api/globalstats 仍走映射（恢复按钮的前提：公网拿得到真数字）",
              ENDPOINT_TRIAGE["/api/globalstats"][0] == "map")

        # ---------------- ⑥ 公网首页片段（方案 B：与本地 landing 同一份模板） ----------------
        home = (out / "data" / "home.html").read_text(encoding="utf-8")
        check("产物含首页片段 data/home.html", (out / "data" / "home.html").is_file())
        check("片段就是本地那一屏（标题与搜索框在）",
              "从一次检索开始" in home and 'class="land-box"' in home
              and 'id="land-continue"' in home)
        check("片段带只读标记类（适配器靠它收成单列）", "kb-home-frag" in home)
        check("公网首页不出现本地专属三件：收件箱 / 本月统计 / 架构图取景框",
              "/inbox" not in home and "/stats" not in home and "land-view" not in home)
        check("公网首页的搜索框不发 /search（交给适配器开浮层）",
              'action="/search"' not in home)
        panel = (ROOT / "app" / "templates" / "landing_panel.html").read_text(encoding="utf-8")
        check("本地那一屏三件入口仍在（同一份模板，只准 gate 不准删）",
              all(x in panel for x in ["进入收件箱", "本月阅读统计", "land-view",
                                       'action="/search"']))
        check("landing.html 改成 include（不留第二份首页标记）",
              '{% include "landing_panel.html" %}' in (ROOT / "app" / "templates" / "landing.html")
              .read_text(encoding="utf-8"))
        check("适配器在根路径注入首页、开文档时让位",
              all(x in kbs for x in ["showHome", "hideHome", "data/home.html",
                                     "kb-home-on", "kb-last-doc"]))
        # 首页面板自己也必须跟着首页态收起：只收正文列/右栏的话，点开文档后它会继续
        # 占住中间那一列、把正文挤到右栏去（用户实拍就是这个形状）。
        check("首页面板本身受首页态控制（不是注入后就常驻）",
              "#kb-home{display:none" in kbs and ".kb-home-on #kb-home{display:flex}" in kbs)
        # 首页态收右栏**只能对宽屏生效**：≤860 那一档右栏就是贴底工具栏，而首页上「分类」抽屉
        # 唯一的入口是工具栏里那一页签 —— 一并藏掉等于手机上 1002 篇没有导航（用户实拍：PWA
        # 打开后底部什么都没有。这条正是当时没有任何断言管住而溜出去的）。
        check("首页态的右栏收起只写在 ≥861 那档；≤860 留工具栏且只挂「分类」一页签",
              "@media (min-width:861px){.kb-home-on #p-rail{display:none!important}}" in kbs
              and "@media (max-width:860px){.kb-home-on .rtab:not(.kb-nav-tab)"
                  "{display:none!important}}" in kbs
              and ".kb-home-on #p-article,.kb-home-on #p-rail" not in kbs)
        check("打开文档 → 左树自动展开并聚焦（renderTree 末尾单点调用）",
              "function revealCurInTree()" in appjs and "revealCurInTree();" in appjs
              and "setTreeOpen(CUR.domain, true)" in appjs)
        check("树展开态的读取函数只有一份定义（曾复制成两个同名 treeOpenSet）",
              appjs.count("function treeOpenSet()") == 1)
        # 窄屏右栏 = 贴底工具栏（用户实拍：旧写法把那一坨卡在正文中段）
        kbc_css = (ROOT / "static" / "kb-core.css").read_text(encoding="utf-8")
        check("窄屏工具栏固定在底部并压在状态栏之上；收起态面板真的不在流里，" 
              "展开态是贴右边缘的侧边抽屉",
              "position:fixed;left:0;right:0;bottom:28px" in kbc_css
              and "main>section.rail .rpane{display:none}" in kbc_css
              # style.css:607 的 `#pane-toc.active{display:flex}` 是 id 级，收起态必须用同级别的
              # :is() 才压得住 —— 压不住就是"工具栏下面挂一坨目录"（用户实拍）。
              and "main>section.rail:not(.rail-open) :is(#pane-toc,#pane-info,#pane-links,#pane-notes).active{display:none}" in kbc_css
              and "position:fixed;right:0;top:0;left:auto" in kbc_css
              and "animation:kb-rail-side" in kbc_css)
        check("抽屉的开合只在 app.js 一处实现（railSheet），Esc 链引用它",
              appjs.count("function railSheet(") == 1
              and "window.railSheetClose" in appjs
              and "window.railSheetClose === \"function\"" in kbc)
        # 窄屏左树入口：style.css ≤860 把左树整块隐藏，工具栏第一颗「分类」是唯一的翻目录路径
        wb_tpl = (ROOT / "app" / "templates" / "workbench.html").read_text(encoding="utf-8")
        base_tpl = (ROOT / "app" / "templates" / "base.html").read_text(encoding="utf-8")
        check("「分类」页签只有一份标记，且排在四枚面板页签之前",
              wb_tpl.count('id="kb-nav-tab"') == 1
              and wb_tpl.find('kb-nav-tab') < wb_tpl.find('data-pane="toc"'))
        check("抽屉与页签的实现各只有一处，Esc 链两环都在",
              appjs.count("function navSheet(") == 1 and "window.navSheetClose" in appjs
              and "window.navSheetClose === \"function\"" in kbc)
        check("唤出左树的规则与隐藏它的是同一档断点（860），且抽屉压在工具栏之上",
              "@media (max-width:860px)" in kbc_css
              and ".rtab.kb-nav-tab{display:inline-flex}" in kbc_css
              and "main.kb-nav-on>section.panel#p-left" in kbc_css
              and "bottom:calc(28px + var(--kb-bar) + 1px" in kbc_css
              and "@media (min-width:861px){\n  .rtab.kb-nav-tab{display:none}" in kbc_css)
        # 窄屏贴底工具栏只留三颗（用户 2026-10-08 拍板：备注/双链手机上不给入口，宽屏照旧）
        check("窄屏藏掉「备注」「双链」两颗页签，且面板展开不再走 max-height 过渡（半开帧就是红框那张）",
              'main>section.rail .rtab[data-pane="notes"],' in kbc_css
              and 'main>section.rail .rtab[data-pane="links"]{display:none}' in kbc_css
              and "transition:max-height" not in kbc_css.split("@media (max-width:980px)")[1]
                  .split("@media (max-width:860px)")[0]
              and "width:min(86vw,380px)" in kbc_css)
        # 窄屏搜索入口：常驻搜索框让位给右上角那颗钮（两档都要有，缺一个就是假入口/双入口）
        check("窄屏收掉顶栏搜索框并放出那颗搜索钮；宽屏反过来（.pill 两个类才压得住 .pill.icon-only）",
              ".searchbox{display:none}" in kbc_css and ".pill.kb-so-btn{display:inline-flex}" in kbc_css
              and ".pill.kb-so-btn{display:none}" in kbc_css)
        check("搜索钮与浮层入口是同一个 soOpen（不做第二套搜索 UI）",
              'id="kb-so-btn" onclick="soOpen()"' in base_tpl)
        # 阅读历史：左栏那条常驻列表已按用户要求撤掉，实现收在 app.js 一份，两边共用
        check("公网适配器不再自己实现「最近阅读」（那份与本地各写各的，已并成 app.js 一份）",
              "kb-recent" not in kbs and "RKEY" not in kbs and "renderRecent" not in kbs)
        check("阅读历史的记录点挂在 setDoc 上（首屏内嵌 doc-data 那一趟也要记到）",
              "if (v && v.rel) histRecord(v.rel, v.title);" in appjs
              and appjs.count("function histRecord(") == 1)
        check("「阅读历史」钮只在阅读工作台出现（模板 block，不在收件箱/统计页长假入口）",
              '{% block nav_tail %}' in base_tpl and '{% block nav_tail %}' in wb_tpl
              and wb_tpl.count('id="kb-hist-btn"') == 1)
        check("工具栏那一档跟的是 style.css「收右遥测轨」的 980，不是随手挑的数"
              "（861~980 之间网格只有两轨，右栏不 fixed 就会被甩到第二行）",
              "@media (max-width:980px)" in kbc_css
              and 'const RAIL_SHEET = () => MQ(980);' in appjs
              and 'const NAV_SHEET = () => MQ(860);' in appjs)

        # ---------------- ⑦ PWA：manifest + 站根 sw（只属于导出产物） ----------------
        man_p = out / "manifest.webmanifest"
        sw_p = out / "sw.js"
        check("产物有 manifest.webmanifest 与站根 sw.js",
              man_p.is_file() and sw_p.is_file())
        check("sw 源文件不在 static/ 里留第二份（作用域由 URL 决定，只能待站根）",
              not (out / "static" / "kb-sw.js").is_file()
              and (ROOT / "static" / "kb-sw.js").is_file())
        man = json.loads(man_p.read_text(encoding="utf-8"))
        check("manifest 的 id/start_url/scope 三者同为站根（空前缀档）",
              man.get("id") == "/" and man.get("start_url") == "/" and man.get("scope") == "/")
        check("manifest 是可安装的：standalone + 有 512 图标 + 有主题色",
              man.get("display") == "standalone"
              and any(i["sizes"] == "512x512" for i in man["icons"])
              and str(man.get("theme_color", "")).startswith("#"))
        check("manifest 里每个图标都真在产物里（清单指向 404 就是装不上）",
              all((out / i["src"].lstrip("/")).is_file() for i in man["icons"]),
              str([i["src"] for i in man["icons"]]))
        check("maskable 图标单独标 purpose（Android 蒙版会裁掉边缘）",
              any(i.get("purpose") == "maskable" for i in man["icons"]))
        sw = sw_p.read_text(encoding="utf-8")
        check("sw 的三个占位符都被替换（漏一个就是整站白屏级事故）",
              not re.search(r"__KB_[A-Z]+__", sw), sw[:200])
        check("sw 空前缀档的 KB_BASE 是空串", 'var KB_BASE = "";' in sw)
        check("sw 缓存名带构建号（换版本靠它清旧库）",
              re.search(r'var CACHE_SHELL = "zhiku-shell-" \+ KB_BUILD;', sw) is not None
              and re.search(r'var KB_BUILD = "[^"]+";', sw) is not None)
        _pc = re.search(r"var PRECACHE = (\[[^\n]*\]);", sw)
        precache = json.loads(_pc.group(1)) if _pc else []
        check("预热清单来自产物壳（style.css / app.js 都在，且带 ?v= 查询以对上缓存键）",
              any("style.css" in u for u in precache) and any("app.js" in u for u in precache)
              and any(u.startswith("/static/") for u in precache), str(precache[:4]))
        check("预热清单里每一条都真在产物里（清单指向 404 = 离线照样白屏）",
              all((out / u.lstrip("/").split("?")[0]).is_file() for u in precache),
              str([u for u in precache if not (out / u.lstrip("/").split("?")[0]).is_file()]))
        check("预热清单不含语料与图片（只 1.5MB 的壳，不是 32MB 的 data）",
              not any("/data/doc" in u or "/raw/" in u for u in precache), str(precache[:4]))
        check("一条都没丢（模板指到不存在的资源 = 离线白屏的根因，这里必须为 0）",
              summary["pwa"]["dropped"] == [], str(summary["pwa"]["dropped"][:6]))
        _inst = sw[sw.find('"install"'):sw.find('"activate"')]
        check("install 只预热壳 + 首页片段 + 那份清单（不 addAll 语料）",
              len(_inst) > 0 and _inst.count(".add(") == 3 and "addAll" not in _inst
              and "PRECACHE.forEach" in _inst and "c.add(HOME)" in _inst
              and 'var HOME = KB_BASE + "/data/home.html"' in sw
              and "data/doc" not in _inst, _inst)
        check("sw 对跨源请求一律放行（本仓零出站，不给例外开门）",
              "if (!underBase(u)) return;" in sw)
        kbhtml = (out / "index.html").read_text(encoding="utf-8")
        check("壳里注了 manifest 链接、主题色与注册脚本",
              'rel="manifest"' in kbhtml and 'name="theme-color"' in kbhtml
              and "/static/kb-pwa.js" in kbhtml)
        check("PWA 那几行排在 <meta charset> 之后（排前面会按 Windows-1252 解中文）",
              kbhtml.find('<meta charset="UTF-8">') < kbhtml.find('rel="manifest"'))
        check("404.html 与 index.html 同壳（离线深链回落到同一份）",
              (out / "404.html").read_text(encoding="utf-8") == kbhtml)
        kbhtml2 = (with_base / "index.html").read_text(encoding="utf-8")
        man2 = json.loads((with_base / "manifest.webmanifest").read_text(encoding="utf-8"))
        check("带前缀档：manifest 的 scope/start_url 与图标 src 都带 /kb",
              man2["scope"] == "/kb/" and man2["start_url"] == "/kb/"
              and all(i["src"].startswith("/kb/static/icons/") for i in man2["icons"]),
              str(man2["scope"]))
        check("带前缀档：href 不被 prefix_html 二次加前缀",
              'href="/kb/manifest.webmanifest"' in kbhtml2 and "/kb/kb/" not in kbhtml2)
        check("带前缀档：sw 里的 KB_BASE 与构建号都替换成 /kb",
              'var KB_BASE = "/kb";' in (with_base / "sw.js").read_text(encoding="utf-8"))
        local_tpl = (ROOT / "app" / "templates" / "base.html").read_text(encoding="utf-8")
        check("本地阅读器不加载 PWA（模板里没有 manifest / sw.js / kb-pwa）",
              "manifest" not in local_tpl and "sw.js" not in local_tpl
              and "kb-pwa" not in local_tpl)
        check("注册件只认只读档（KB_STATIC.readonly 为假就直接返回）",
              "if (!S || !S.readonly) return;" in (ROOT / "static" / "kb-pwa.js").read_text(encoding="utf-8"))
        # 负向：图标缺件必须响亮失败，而不是产出一个装不上的 manifest
        noicon = root / "site-noicon"
        (root / "static" / "icons").rename(root / "icons-off")
        try:
            export_site(root, noicon, base="", tracked_only=False, include_search=False)
            refused_ok = False
        except SystemExit:
            refused_ok = True
        finally:
            (root / "icons-off").rename(root / "static" / "icons")
        check("负向：static/icons 缺件时导出直接拒绝（不产出指向 404 的 manifest）", refused_ok)

        literals = _api_literals(out / "static")
        unknown = sorted(l for l in literals if l not in ENDPOINT_TRIAGE)
        check("产物 JS 的 /api/ 字面量全部在分诊表内", not unknown, f"未分诊: {unknown}")
        repo_literals = _api_literals(ROOT / "static")
        repo_unknown = sorted(l for l in repo_literals if l not in ENDPOINT_TRIAGE)
        check("仓库产品 JS 的 /api/ 字面量全部在分诊表内", not repo_unknown, f"未分诊: {repo_unknown}")
        check("分诊表恒定覆盖前端实际调用的读端点",
              TRIAGE_READ_MAP >= {"/api/tree", "/api/doc", "/api/links",
                                  "/api/palette/index", "/api/search", "/api/dir/tree"})
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
            "/api/dir/tree": out / "data" / "dir-tree.json",
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

    # ---------------- KB_BASE 只认 URL 前缀（Git Bash 会把 /knowledge 改写成盘符路径） ----------------
    check("check_base 接受空前缀（根路径托管）", check_base("") == "")
    check("check_base 接受 /knowledge", check_base("/knowledge") == "/knowledge")
    for bad in ("C:/Program Files/Git/knowledge", "knowledge", "/knowledge/", "/a//b",
                "D:\\knowledge"):
        try:
            check_base(bad)
            ok = False
        except SystemExit:
            ok = True
        check(f"check_base 拒绝 {bad!r}", ok)
    refused = corpus / "site-refused"
    try:
        export_site(corpus, refused, base="C:/Program Files/Git/knowledge",
                    tracked_only=False, include_search=False)
        raised = False
    except SystemExit:
        raised = True
    check("export_site 在落盘之前就拒绝坏 KB_BASE", raised and not refused.exists())

    import shutil as _sh
    _sh.rmtree(corpus, ignore_errors=True)

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
