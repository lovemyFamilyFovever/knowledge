# -*- coding: utf-8 -*-
"""知库 reader smoke tests — 每条断言一个用户可见行为。

运行：python tests/test_reader.py
在临时目录构造迷你语料，不改真实 content/。
"""
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

        r = c.get("/doc/ai/llm-and-agents/A.html")
        check("纯 HTML 文档可作为文档打开", r.status_code == 200)

        r = c.get("/home")
        home = r.get_data(as_text=True)
        check("/home 渲染统计", r.status_code == 200 and "Markdown 文档" in home)
        check("/home 收件箱计数为 1", "收件箱待归档" in home and ">1<" in home.replace(" ", ""))
        check("/home 最近更新含 B", "职业笔记B" in home)

        r = c.get("/search?q=量子")
        page = r.get_data(as_text=True)
        check("/search 命中正文", r.status_code == 200 and "测试文档" in page and "<mark>" in page)

        r = c.get("/search?q=不存在的词组xyz")
        check("/search 空结果不报错", r.status_code == 200 and "没有匹配" in r.get_data(as_text=True))

        r = c.get("/favorites")
        check("/favorites 列出 favorite 文档", "职业笔记B" in r.get_data(as_text=True))

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

        r = c.post("/api/favorite", json={"path": "ai/llm-and-agents/A.md"})
        check("/api/favorite 置为 true", r.get_json()["favorite"] is True)
        check("favorite 写进 frontmatter", "favorite: true" in (root / "content/ai/llm-and-agents/A.md").read_text(encoding="utf-8"))
        r = c.post("/api/favorite", json={"path": "ai/llm-and-agents/A.md"})
        check("/api/favorite 再点取消", r.get_json()["favorite"] is False)

        r = c.get("/doc/ai/llm-and-agents/deep/Nested")
        check("嵌套目录文档可访问", r.status_code == 200 and "嵌套文档" in r.get_data(as_text=True))

        r = c.get("/browse/projects/dsh-agent")
        check("三级目录子域重定向首篇", r.status_code == 302 and "/doc/projects/dsh-agent/architecture/X" in r.headers["Location"])

        r = c.post("/api/delete", json={"path": "ai/llm-and-agents/A.md"})
        j = r.get_json() if r.status_code == 200 else {"moved": []}
        check("/api/delete 移入 _trash", r.status_code == 200 and not (root / "content/ai/llm-and-agents/A.md").exists())
        check("美化版与备注随删", any("A.html" in m for m in j["moved"]) and any("A.md.notes.md" in m for m in j["moved"]))
        check("_trash 保留原件", any(p.name == "A.md" for p in (root / "content/_trash").rglob("*.md")))
        r = c.get("/doc/ai/llm-and-agents/A")
        check("删除后 404", r.status_code == 404)

        r = c.get("/doc/ai/nope/nope")
        check("不存在的文档 404", r.status_code == 404)

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
