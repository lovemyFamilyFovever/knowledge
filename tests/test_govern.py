# -*- coding: utf-8 -*-
"""知库治理与统计 smoke —— 临时语料/临时库，不碰真实 content/。

覆盖：标签普查/合并（dry-run 与 apply）、疑似重叠降噪、阅读统计事件与月度聚合。
运行：.python\\python.exe tests/test_govern.py
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.store import (tag_census, find_similar_tags, merge_tag,  # noqa: E402
                       parse_frontmatter)
from app.reading import ReadingStore  # noqa: E402

DOC1 = "---\ntitle: \"A\"\ntags: [AI, 提示词]\n---\n\n# A\n内容"
DOC2 = "---\ntitle: \"B\"\ntags: [ai, 修正]\n---\n\n# B\n内容"
DOC3 = "---\ntitle: \"C\"\ntags: [CSS]\n---\n\n# C\n内容"


def seed(root: Path) -> Path:
    d = root / "content" / "baike" / "ai-and-llm"
    d.mkdir(parents=True)
    (d / "a.md").write_text(DOC1, encoding="utf-8")
    (d / "b.md").write_text(DOC2, encoding="utf-8")
    (d / "c.md").write_text(DOC3, encoding="utf-8")
    return root / "content"


def test_tag_census_and_similar():
    with tempfile.TemporaryDirectory() as td:
        content = seed(Path(td))
        census = tag_census(content)
        # census 保留原大小写键（AI 与 ai 分开计数），聚合在 merge 阶段做
        assert sum(census.values()) == 5, f"census 应含 5 个标签实例：{census}"
        assert census.get("AI") == 1 and census.get("ai") == 1
        pairs = find_similar_tags(census)
        case_pairs = [p for p in pairs if p[2] == 1.0]
        assert case_pairs and {case_pairs[0][0].lower(), case_pairs[0][1].lower()} == {"ai"}, \
            "应检出 AI/ai 大小写对"
        # 中文双字词不应被编辑距离误报（提示词 vs 修正 无 ASCII，距离>1）
        assert not any({p[0], p[1]} == {"提示词", "修正"} for p in pairs)
    print("ok  tag_census + find_similar_tags（含大小写聚合与降噪）")


def test_merge_tag_dryrun_then_apply():
    with tempfile.TemporaryDirectory() as td:
        content = seed(Path(td))
        r = merge_tag(content, "ai", "AI 资产", apply=False)
        assert r["n_docs"] == 2, f"dry-run 应命中 2 篇：{r['n_docs']}"
        raw = (content / "baike" / "ai-and-llm" / "a.md").read_text(encoding="utf-8")
        assert "tags: [AI" in raw, "dry-run 不应写盘"
        r2 = merge_tag(content, "ai", "AI 资产", apply=True)
        assert r2["n_docs"] == 2
        fm, _ = parse_frontmatter((content / "baike" / "ai-and-llm" / "a.md").read_text(encoding="utf-8"))
        assert fm["tags"] == ["AI 资产", "提示词"], f"合并后 tags 应正确：{fm['tags']}"
        fm2, _ = parse_frontmatter((content / "baike" / "ai-and-llm" / "b.md").read_text(encoding="utf-8"))
        assert fm2["tags"] == ["AI 资产", "修正"], "小写 ai 也应被并入且去重"
    print("ok  merge_tag：dry-run 预览 → apply 写盘 → 大小写不敏感 + 去重")


def test_merge_tag_crlf_bytes():
    """CRLF 语料回归锁：真实语料 100% 是 CRLF（tags 行后还有其他键），
    行尾锚若不容 \r 则 merge 全库跳过且夹具测不出（夹具 tags 恰为 FM 末行）。
    同时锁字节保真：改写后该行行尾仍为 \r\n，其余字节不动。"""
    with tempfile.TemporaryDirectory() as td:
        content = Path(td) / "content"
        d = content / "baike" / "ai-and-llm"
        d.mkdir(parents=True)
        f = d / "crlf.md"
        raw = ("---\r\n"
               "title: \"CRLF 样本\"\r\n"
               "tags: [AI, 随笔]\r\n"
               "source: \"test\"\r\n"
               "---\r\n"
               "\r\n"
               "正文段落。\r\n").encode("utf-8")
        f.write_bytes(raw)
        r = merge_tag(content, "AI", "AI资产", apply=False)
        assert r["n_docs"] == 1, f"CRLF 语料应命中 1 篇：n_docs={r['n_docs']} skipped={r['skipped']}"
        assert r["n_skipped"] == 0, f"不应有形态类跳过：{r['skipped']}"
        merge_tag(content, "AI", "AI资产", apply=True)
        after = f.read_bytes()
        assert b"tags: [AI\xe8\xb5\x84\xe4\xba\xa7, \xe9\x9a\x8f\xe7\xac\x94]\r\n" in after, \
            f"tags 行应改写且保留 CRLF：{after!r}"
        assert after.count(b"\n") == after.count(b"\r\n"), "不得引入裸 LF（字节保真破坏）"
        fm, _ = parse_frontmatter(after.decode("utf-8"))
        assert fm["tags"] == ["AI资产", "随笔"], f"合并后 tags 应正确：{fm['tags']}"
    print("ok  merge_tag CRLF 回归：命中 + 行尾字节保真")


def test_reading_stats():
    with tempfile.TemporaryDirectory() as td:
        rs = ReadingStore(Path(td) / "indexes")
        assert rs.track("a.md", "A", "open") is True
        assert rs.track("a.md", "A", "open") is False, "10 分钟内 open 应去重"
        for _ in range(3):
            rs.track("a.md", "A", "read_minute", seconds=60)
        rs.track("b.md", "B", "open")
        ym = rs.monthly(rs.con.execute("SELECT ym FROM reading_events LIMIT 1").fetchone()[0])
        assert ym["opened_docs"] == 2
        assert ym["docs"][0]["path"] == "a.md", "a.md 时长最高应排第一"
        assert ym["total_minutes"] == 3.0, f"总分钟应 3.0：{ym['total_minutes']}"
        assert ym["daily"] and ym["daily"][0]["minutes"] == 3.0
        try:
            rs.track("a.md", "A", "hack")
            assert False, "非法事件应抛错"
        except ValueError:
            pass
        rs.close()
    print("ok  reading stats：open 去重 + 分钟累计 + 月度聚合")


def test_globalstats_links_and_cjk_cache():
    """bug 评估报告 2026-09-17 的回归护栏：
    1) /api/globalstats 的双链计数必须与 FTS links 表一致
       （曾因重构删掉模块级 open_db 导入，NameError 被 except Exception
       吞成“双链永远 0”的静默错数）；
    2) _corpus_agg 的 stats_cjk.json 磁盘缓存：首轮必须落盘，
       次轮全命中重算的总字数必须与首轮一致（曾因命中分支不累加丢数）。"""
    from app.app import create_app
    from app.fts import open_db
    import app.routes_stats as rst

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        d = root / "content" / "baike" / "ai-and-llm"
        d.mkdir(parents=True)
        (d / "a.md").write_text(
            "---\ntitle: \"A\"\n---\n# A\n这里引用了 [[B]] 和一个不存在的 [[缺页词条]]，共四十余个汉字。\n",
            encoding="utf-8")
        (d / "b.md").write_text(
            "---\ntitle: \"B\"\n---\n# B\n被引用的中文正文若干部。\n", encoding="utf-8")
        rst._AGG["sig"] = rst._AGG["data"] = None
        app = create_app(root)
        c = app.test_client()

        body = c.get("/api/globalstats").get_json()
        con = open_db(root / "indexes")
        n_total = con.execute("SELECT count(*) FROM links").fetchone()[0]
        n_dead = con.execute("SELECT count(*) FROM links WHERE resolved=0").fetchone()[0]
        con.close()
        assert (n_total, n_dead) == (2, 1), f"夹具应有 2 链/1 断：{n_total}/{n_dead}"
        assert body["links"]["total"] == n_total, \
            f"globalstats 双链数须与 links 表一致：{body['links']} vs {n_total}"
        assert body["links"]["dead"] == n_dead and body["links"]["dead_docs"] == 1
        assert body["total_cjk"] > 0

        cache_file = root / "indexes" / "stats_cjk.json"
        assert cache_file.is_file(), "首轮 _corpus_agg 应落盘 stats_cjk.json"
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        assert set(cached["files"]) == {"baike/ai-and-llm/a.md", "baike/ai-and-llm/b.md"}, \
            f"缓存键应为全量 md 相对路径：{set(cached['files'])}"
        first_total = body["total_cjk"]

        # 清内存层→强制重算：此次全部命中磁盘缓存（不读全文），字数必须分毫不差
        rst._AGG["sig"] = rst._AGG["data"] = None
        body2 = c.get("/api/globalstats").get_json()
        assert body2["total_cjk"] == first_total, \
            f"缓存命中重算不得丢字数：{first_total} -> {body2['total_cjk']}"
        rst._AGG["sig"] = rst._AGG["data"] = None
    print("ok  globalstats 双链一致 + stats_cjk 缓存落盘/命中无损（报告 2026-09-17 护栏）")


if __name__ == "__main__":
    test_tag_census_and_similar()
    test_merge_tag_dryrun_then_apply()
    test_merge_tag_crlf_bytes()
    test_reading_stats()
    test_globalstats_links_and_cjk_cache()
    print("\nGOVERN+STATS TESTS OK")
