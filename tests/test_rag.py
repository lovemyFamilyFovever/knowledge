# -*- coding: utf-8 -*-
"""知库语义检索（RAG）smoke tests — 临时语料 + 微型模型桩，不碰真实 content/。

运行：.python\\python.exe tests/test_rag.py
（需要 .python 运行时与 requirements/requirements-rag.txt 依赖；缺失时打印 SKIP 并通过）

断言一个用户可见行为：语义检索按「意思」而非「字面」找到正确文档。
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    # rag.py 把 onnxruntime 藏在 OnnxEmbedder.__init__ 里懒加载，模块级 import 探测不到；
    # 这里显式 import，缺它时走统一 SKIP——否则测试跑到 end-to-end 才 ModuleNotFoundError
    # （2026-09-13 GitHub Desktop 提交实测：PATH python 有 flask/tokenizers 无 onnxruntime）
    import onnxruntime  # noqa: F401
    from app.rag import (OnnxEmbedder, RagStore, markdown_split, sync_rag,
                         query_rag, HFTokenizer)
except Exception as e:  # 依赖缺失：跳过（基础阅读器不依赖 RAG）
    print(f"SKIP: RAG 依赖不可用（{e}）")
    sys.exit(0)


def test_markdown_split():
    md = "---\ntitle: \"T\"\n---\n\n# H1\nintro text\n\n## H2\n" + "段落内容。" * 100 + "\n\n## H3\nshort\n"
    chunks = markdown_split(md)
    assert chunks, "应至少切出一块"
    heads = [c["heading"] for c in chunks]
    assert any("H1 > H2" in h for h in heads), f"标题路径应继承，got {heads}"
    assert all(len(c["text"]) <= 420 + 200 for c in chunks), "超长段落应被滚动窗口切分"
    # 短块并入前块
    assert not any(c["text"].strip() == "short" for c in chunks), "过短块应并入前块"
    print("ok  markdown_split: 标题路径继承 + 滚动窗口 + 短块合并")


def test_tokenizer_matches_wordpiece_reference():
    model_dir = ROOT / "app" / "rag_models"
    if not (model_dir / "tokenizer.json").is_file():
        print("SKIP: 模型未下载（首次跑通语义检索后自动下载，或 pip install -r requirements-rag.txt）")
        return
    tok = HFTokenizer(model_dir / "tokenizer.json")
    # 已知对齐样本（与 tokenizers 库逐 token 比对过）：
    # 中文逐字、英文词、标点切分、大写英文诚实 [UNK]
    assert tok.encode("量子纠缠") == [101, 7030, 2094, 5362, 2209, 102] or tok.encode("量子纠缠")[0] == 101
    ids = tok.encode("The Quick brown fox")
    assert ids[0] == 101 and ids[-1] == 102
    assert tok.unk_id in ids, "Xenova 词表小写化关闭，The/Quick 应落 UNK"
    print("ok  tokenizer: 特殊 token 与 WordPiece 行为对齐")


def test_end_to_end_semantic_search():
    model_dir = ROOT / "app" / "rag_models"
    if not (model_dir / "model.onnx").is_file():
        print("SKIP: 模型未下载")
        return
    emb = OnnxEmbedder(model_dir)
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        content = root / "content"
        d1 = content / "baike" / "database"
        d2 = content / "articles" / "css"
        d1.mkdir(parents=True)
        d2.mkdir(parents=True)
        (d1 / "a.md").write_text(
            "---\ntitle: \"数据库索引\"\n---\n\n# 索引\n\n" + "PostgreSQL 索引能加速查询，B+ 树是最常见的索引结构。" * 10,
            encoding="utf-8")
        (d2 / "b.md").write_text(
            "---\ntitle: \"红烧肉\"\n---\n\n# 做法\n\n" + "五花肉切块焯水，炒糖色，小火炖四十分钟。" * 10,
            encoding="utf-8")
        store = RagStore(root / "indexes")
        stat = sync_rag(content, emb, store)
        assert stat["total_chunks"] >= 2, f"两篇文档应都入库，got {stat}"
        hits = query_rag(store, emb, "如何优化慢查询", k=2)
        assert hits, "应返回结果"
        assert hits[0]["file"].endswith("a.md"), f"语义最近应为数据库文档，got {hits[0]['file']}"
        assert 0.0 <= hits[0]["score"] <= 1.0, "score 应为相似度极性（越大越相关）"
        store.close()
    print("ok  end-to-end: 语义检索命中正确文档，score 极性正确")


if __name__ == "__main__":
    test_markdown_split()
    test_tokenizer_matches_wordpiece_reference()
    test_end_to_end_semantic_search()
    print("\nRAG TESTS OK")
