# -*- coding: utf-8 -*-
"""知库 reader smoke tests — 每条断言一个用户可见行为。

运行：python tests/test_reader.py
在临时目录构造迷你语料，不改真实 content/。
"""
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.app import create_app  # noqa: E402

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

代码里的 `[[忽略我]]` 不算双链。

```python
print("hello")
```
"""

DOC_HTML = "<!DOCTYPE html><html><body><h1>美化版A</h1></body></html>"
DOC_B = """---
title: "职业笔记B"
favorite: true
---

# 职业笔记B

简历要与岗位关键词对齐。
"""


def seed(root: Path) -> None:
    d = root / "content" / "ai" / "llm-and-agents"
    d.mkdir(parents=True)
    (d / "A.md").write_text(DOC_A, encoding="utf-8")
    (d / "A.html").write_text(DOC_HTML, encoding="utf-8")
    nest = d / "deep"
    nest.mkdir()
    (nest / "Nested.md").write_text("---\ntitle: \"嵌套文档\"\n---\n\n# 嵌套\n", encoding="utf-8")
    p2 = root / "content" / "projects" / "dsh-agent" / "architecture"
    p2.mkdir(parents=True)
    (p2 / "X.md").write_text("---\ntitle: \"架构分析\"\n---\n\n# X\n", encoding="utf-8")
    c = root / "content" / "career"
    c.mkdir(parents=True)
    (c / "B.md").write_text(DOC_B, encoding="utf-8")
    (root / "content" / "_inbox").mkdir()
    (root / "content" / "_inbox" / "junk.md").write_text("x", encoding="utf-8")


passed = failed = 0


def check(name: str, cond: bool, extra="") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS {name}")
    else:
        failed += 1
        print(f"  FAIL {name} {extra}")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        seed(root)
        app = create_app(root)
        c = app.test_client()

        r = c.get("/")
        check("/ 重定向到首篇", r.status_code == 302 and "/doc/ai/llm-and-agents/A" in r.headers["Location"])

        r = c.get("/doc/ai/llm-and-agents/A")
        body = r.get_data(as_text=True)
        check("/doc 渲染标题", r.status_code == 200 and "测试文档A" in body)
        check("/doc 携带 doc-data JSON", 'id="doc-data"' in body)
        check("/doc 面包屑含分类", "ai/llm-and-agents" in body)
        check("/doc 保留客户端渲染锚点 id", 'id="list-title"' in body and 'id="tree"' in body
              and 'id="doc-data"' in body and 'id="doclist"' in body and 'id="article"' in body)

        r = c.get("/doc/ai/llm-and-agents/A.html")
        check("纯 HTML 文档可作为文档打开", r.status_code == 200)

        r = c.get("/home")
        home = r.get_data(as_text=True)
        check("/home 渲染统计", r.status_code == 200 and "个域入口" in home)  # 领域数已动态化：{{ stats.domains|length }} 个域入口
        # 顶栏重排（交互方案问题12）后收件箱 pill 降级为图标 badge，计数断言改锚 home 的「去收件箱 · N」
        check("/home 收件箱计数为 1", bool(re.search(r"去收件箱\s*·\s*1", home)))
        check("/home 最近更新含 B", "职业笔记B" in home)

        r = c.get("/search?q=量子")
        page = r.get_data(as_text=True)
        check("/search 命中正文", r.status_code == 200 and "测试文档" in page and "<mark>" in page)

        r = c.get("/search?q=不存在的词组xyz")
        check("/search 空结果不报错", r.status_code == 200 and "没有匹配" in r.get_data(as_text=True))

        r = c.get("/favorites")
        check("/favorites 列出 favorite 文档", "职业笔记B" in r.get_data(as_text=True))

        r = c.get("/tags")
        tags_body = r.get_data(as_text=True)
        check("/tags 页面可访问", r.status_code == 200)
        check("/tags 列出标签", "AI" in tags_body and "Agent" in tags_body)

        r = c.get("/raw/ai/llm-and-agents/A.html")
        check("/raw 直通美化版", r.status_code == 200 and "美化版A" in r.get_data(as_text=True))

        r = c.get("/raw/../app/app.py")
        check("/raw 拒绝目录穿越", r.status_code in (400, 404))

        r = c.post("/api/save", json={"path": "ai/llm-and-agents/A.md", "content": DOC_A + "\n新追加段落。\n"})
        check("/api/save 写回成功", r.status_code == 200 and r.get_json()["ok"])
        saved = (root / "content/ai/llm-and-agents/A.md").read_text(encoding="utf-8")
        check("写回内容落盘且补尾换行", saved.endswith("新追加段落。\n"))

        r = c.post("/api/save", json={"path": "../../etc/passwd", "content": "x"})
        check("/api/save 拒绝穿越", r.status_code == 400)

        r = c.post("/api/save", json={"path": "ai/llm-and-agents/A.html", "content": "x"})
        check("/api/save 拒绝非 md 扩展", r.status_code == 400)

        r = c.get("/search?q=新追加段落")
        check("保存后索引立即可搜", "测试文档" in r.get_data(as_text=True))

        r = c.post("/api/note", json={"path": "ai/llm-and-agents/A.md", "text": "第一条备注"})
        check("/api/note 写入旁挂", r.status_code == 200 and (root / "content/ai/llm-and-agents/A.md.notes.md").is_file())

        # ── B2/B3 回归：备注旁挂与嵌套 _ 目录不得进树 / 不得可路由 ──
        tree = c.get("/api/tree").get_json()
        names = [doc["name"] for d in tree["domains"] for s in d["subs"] for doc in s["docs"]]
        check("备注旁挂不进分类树", not any("notes" in n for n in names),
              str([n for n in names if "notes" in n]))
        r = c.get("/doc/ai/llm-and-agents/A.md.notes")
        check("备注旁挂直连 URL 404", r.status_code == 404, f"got {r.status_code}")
        hid = root / "content/ai/llm-and-agents/_tmp"
        hid.mkdir(parents=True, exist_ok=True)
        (hid / "leak.md").write_text("---\ntitle: 泄漏\n---\n\nx\n", encoding="utf-8")
        tree = c.get("/api/tree").get_json()
        names2 = [doc["name"] for d in tree["domains"] for s in d["subs"] for doc in s["docs"]]
        check("嵌套 _ 目录文档不进树", not any("_tmp" in n for n in names2),
              str([n for n in names2 if "_tmp" in n]))
        r = c.get("/doc/ai/llm-and-agents/_tmp/leak")
        check("嵌套 _ 目录文档直连 URL 404", r.status_code == 404, f"got {r.status_code}")

        r = c.post("/api/favorite", json={"path": "ai/llm-and-agents/A.md"})
        check("/api/favorite 置为 true", r.get_json()["favorite"] is True)
        check("favorite 写进 frontmatter", "favorite: true" in (root / "content/ai/llm-and-agents/A.md").read_text(encoding="utf-8"))
        r = c.post("/api/favorite", json={"path": "ai/llm-and-agents/A.md"})
        check("/api/favorite 再点取消", r.get_json()["favorite"] is False)

        # ── B1/B21 回归：嵌套 YAML + CRLF 语料的收藏切换必须字节保真 ──
        # 放 _ 前缀目录（不进树、不进索引），避免扰动依赖树序的既有断言
        hb = root / "content/_fmprobe"
        hb.mkdir(parents=True, exist_ok=True)
        NESTED_DOC = ("---\nlayout: home\nhero:\n  name: \"播客录\"\n  tagline: 思想足迹\n"
                      "tags: [播客]\n---\n\n# 手册\n").replace("\n", "\r\n")
        (hb / "index.md").write_bytes(NESTED_DOC.encode("utf-8"))
        from app.store import set_fm_scalar, _decode_md, parse_frontmatter  # 行级助手直测（绕过路由的 safe_rel）
        text = _decode_md((hb / "index.md").read_bytes())
        out = set_fm_scalar(text, "favorite", "true")
        check("嵌套 YAML 行级手术保留结构与 CRLF（无 \\r\\r、无块丢失）",
              'hero:\r\n  name: "播客录"' in out and "tagline: 思想足迹" in out
              and "favorite: true" in out and "\r\r" not in out
              and out.count("---") == 2, out[:120])
        check("行级手术后 favorite 可被正常读回",
              parse_frontmatter(out)[0].get("favorite") is True)
        # /api/favorite 全链路（普通扁平 fm 文档）：取消收藏写 false 而非带引号 "False"
        r = c.post("/api/favorite", json={"path": "career/B.md"})   # B.md 种子即 favorite: true
        after_b = (root / "content/career/B.md").read_text(encoding="utf-8")
        check("取消收藏写 false 而非带引号 \"False\"",
              r.get_json()["favorite"] is False and "favorite: false" in after_b
              and 'favorite: "False"' not in after_b)

        # ── B6 回归：清空正文后保存，原 frontmatter 必须找回而非被 stamp 覆盖 ──
        r = c.post("/api/save", json={"path": "ai/llm-and-agents/A.md", "content": "# 新开头\n"})
        saved_a = (root / "content/ai/llm-and-agents/A.md").read_text(encoding="utf-8")
        check("空正文保存保留原 frontmatter 身世",
              r.status_code == 200 and 'title: "测试文档A"' in saved_a
              and saved_a.startswith("---") and "# 新开头" in saved_a)
        # 恢复 A 原文（本检查清空了正文/双链，后面的 /api/links 断言依赖它们）
        c.post("/api/save", json={"path": "ai/llm-and-agents/A.md", "content": DOC_A})

        # 无 frontmatter 的新文档（Obsidian 直接创建）：保存时自动补齐身世信息
        nf = root / "content/cookbook/fragment"
        nf.mkdir(parents=True, exist_ok=True)
        (nf / "newfile.md").write_text("随手记的内容", encoding="utf-8")
        r = c.post("/api/save", json={"path": "cookbook/fragment/newfile.md", "content": "随手记的内容"})
        check("无 fm 文档保存成功", r.status_code == 200)
        saved = (root / "content/cookbook/fragment/newfile.md").read_text(encoding="utf-8")
        check("保存时自动补齐 frontmatter",
              saved.startswith("---") and 'title: "newfile"' in saved and 'source: "reader-edit"' in saved
              and "随手记的内容" in saved)

        r = c.get("/api/links?path=career/B.md")
        j = r.get_json()
        check("/api/links 反向链找到 A", any("测试文档A" in x["title"] for x in j["incoming"]))

        r = c.get("/api/links?path=ai/llm-and-agents/A.md")
        j = r.get_json()
        check("/api/links 正向含已解析目标", any(x["resolved"] and "职业笔记" in x["title"] for x in j["outgoing"]))
        check("/api/links 标记未解析目标", any(not x["resolved"] and "不存在的链接" in x["raw"] for x in j["outgoing"]))
        check("/api/links 剔除代码内假双链", not any("忽略我" in x["raw"] for x in j["outgoing"]))

        r = c.get("/doc/ai/llm-and-agents/deep/Nested")
        check("嵌套目录文档可访问", r.status_code == 200 and "嵌套文档" in r.get_data(as_text=True))

        # 域根文档（直接躺在域目录下的 md，树里 sub 为 _root 哨兵）：
        # 前端 docUrl() 会把两段 rel 补成 /doc/<domain>/_root/<name>，
        # 后端必须能解析，否则命令面板点进去就是 404。
        r = c.get("/doc/career/_root/B")
        check("域根文档 /doc/career/_root/B 可访问",
              r.status_code == 200 and "职业笔记B" in r.get_data(as_text=True),
              f"got {r.status_code}")
        r = c.get("/api/doc?domain=career&sub=_root&name=B")
        # 该接口不套 {ok:true} 信封，直接给 doc / info_rows / docs
        check("/api/doc 对 _root 也能取到文档",
              r.status_code == 200
              and (r.get_json() or {}).get("doc", {}).get("title") == "职业笔记B",
              f"got {r.status_code} {str(r.get_json())[:120]}")

        # 契约测试：树接口给的每一个 path，都要能被 /doc/ 路由解析（否则还是 404）
        from urllib.parse import quote
        tree = c.get("/api/tree").get_json()
        root_docs = [(d["id"], doc["name"]) for d in tree["domains"]
                     for s in d["subs"] if s["id"] == "_root" for doc in s["docs"]]
        check("树里能列出域根文档", root_docs == [("career", "B")], f"got {root_docs}")
        bad = [(dm, nm) for dm, nm in root_docs
               if c.get(f"/doc/{quote(dm)}/_root/{quote(nm)}").status_code != 200]
        check("树给的 path 都能被 /doc/ 路由解析", not bad, f"404 的有 {bad}")

        # 放行 _root 之后，真正的下划线目录仍必须被拒（不变量 2）
        for bad_url in ("/doc/_inbox/_root/junk", "/doc/_trash/_root/A",
                        "/doc/ai/_inbox/B", "/doc/ai/_trash/B"):
            check(f"下划线目录仍 404：{bad_url}", c.get(bad_url).status_code == 404)

        r = c.get("/browse/projects/dsh-agent")
        check("三级目录子域重定向首篇", r.status_code == 302 and "/doc/projects/dsh-agent/architecture/X" in r.headers["Location"])

        r = c.post("/api/delete", json={"path": "ai/llm-and-agents/A.md"})
        j = r.get_json() if r.status_code == 200 else {"moved": []}
        check("/api/delete 移入 _trash", r.status_code == 200 and not (root / "content/ai/llm-and-agents/A.md").exists())
        check("美化版与备注随删", any("A.html" in m for m in j["moved"]) and any("A.md.notes.md" in m for m in j["moved"]))
        check("_trash 保留原件", any(p.name == "A.md" for p in (root / "content/_trash").rglob("*.md")))
        r = c.get("/doc/ai/llm-and-agents/A")
        check("删除后 404", r.status_code == 404)

        # ── B7/B8/B22 回归 ──
        r = c.post("/api/delete", json={"path": "ai/llm-and-agents/A.md"})
        check("再删已不存在的文档 → 404 而非 500", r.status_code == 404, f"got {r.status_code}")
        from app.routes_files import _free_path  # 碰撞加后缀是纯路径逻辑，直测保证确定性（不赌秒界）
        coll = root / "content/_trash/20260101-000000/ai/llm-and-agents"
        coll.mkdir(parents=True, exist_ok=True)
        (coll / "A.md").write_text("x", encoding="utf-8")
        check("回收站同名碰撞 → ~2 后缀不覆盖", _free_path(coll / "A.md").name == "A~2.md")
        # B8：已读标记随移动迁移
        (root / "content/career/C.md").write_text("---\ntitle: C 文\n---\n\n正文\n", encoding="utf-8")
        r = c.post("/api/docmark", json={"path": "career/C.md", "mark": "read", "on": True})
        check("标记已读成功", (r.get_json() or {}).get("read") is True)
        r = c.post("/api/move", json={"src": "career/C.md", "dst": "career/C2.md"})
        check("移动成功", r.status_code == 200 and (r.get_json() or {}).get("ok") is True)
        gm = c.get("/api/docmark?path=career/C2.md").get_json()
        check("已读标记随移动随迁（B8）", gm.get("read") is True, str(gm))
        # B22：path 主键拒绝越界字符串
        check("docmark GET 拒绝越界 path", c.get("/api/docmark?path=../../etc/passwd").status_code == 400)
        check("docmark POST 拒绝越界 path",
              c.post("/api/docmark", json={"path": "../x.md", "mark": "read", "on": True}).status_code == 400)
        # 不变量 2：/api/move 不得成为搬进 _ 目录的后门
        r = c.post("/api/move", json={"src": "career/C2.md", "dst": "_trash/C3.md"})
        check("移动进 _ 前缀目录被拒 400", r.status_code == 400, f"got {r.status_code}")

        r = c.get("/doc/ai/nope/nope")
        check("不存在的文档 404", r.status_code == 404)

        # ── C4 回归：treesig 失效判据（B11）+ 路径式双链即时解析（B12）──
        from app.fts import build_index, index_is_stale
        content_dir = root / "content"
        idx_dir = root / "indexes"
        build_index(content_dir, idx_dir)
        check("刚重建的索引不判为过期", not index_is_stale(content_dir, idx_dir))
        gone = content_dir / "career" / "gone.md"
        gone.write_text("---\ntitle: 将被外部删除\n---\n\n正文\n", encoding="utf-8")
        build_index(content_dir, idx_dir)
        gone.unlink()  # 模拟 Obsidian/外部删除：不改任何残留文件的 mtime
        check("外部删除新文件后立即可判过期（旧 mtime 判据的盲区）", index_is_stale(content_dir, idx_dir))
        # 路径式 [[domain/sub/name]] 双链：外科手术式 upsert 当场解析，不等 30s 全量重建
        r = c.post("/api/save", json={"path": "career/linker.md",
                                      "content": "---\ntitle: 链入者\n---\n\n见 [[projects/dsh-agent/architecture/X]]。\n"})
        check("保存引用路径式双链的文档", r.status_code == 200)
        j = c.get("/api/links?path=career/linker.md").get_json()
        check("路径式双链即时解析（B12）",
              any(x["resolved"] and x["path"].endswith("architecture/X.md") for x in j["outgoing"]),
              str(j["outgoing"]))

        # ── B18 回归：聚合缓存端点 + 写后签名失效一致性 ──
        g1 = c.get("/api/globalstats").get_json()
        check("globalstats 端点可用且计数非零",
              g1.get("n_docs", 0) > 0 and isinstance(g1.get("domains"), list)
              and "tagged_pct" in g1, str(g1)[:120])
        before = int(g1["n_docs"])
        (content_dir / "career" / "extra.md").write_text("---\ntitle: 新增篇\ntags: [x]\n---\n\n正文\n", encoding="utf-8")
        g2 = c.get("/api/globalstats").get_json()
        check("语料新增后聚合缓存即时跟进（B18 签名失效）",
              int(g2["n_docs"]) == before + 1, f"{before} -> {g2['n_docs']}")
        dt = c.get("/api/dir/tree").get_json()
        check("dir/tree 聚合结构完整", bool(dt.get("domains")) and "cjk" in dt["domains"][0])

    # 回归：脚本直启（python app\app.py / start.bat）的导入路径 —— 2026-09-09 启动报错修复
    import subprocess
    r = subprocess.run(
        [sys.executable, "app/app.py", "--import-check"],
        cwd=str(Path(__file__).resolve().parents[1]),
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    check("脚本直启导入路径可用（app.py --import-check）", r.returncode == 0)

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
