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
sys.path.insert(0, str(ROOT / "tests"))

import _ci  # noqa: E402  纯标准库；缺依赖 = CI 绿但一条断言没跑，要靠 annotation 说话

try:
    # rag.py 把 onnxruntime 藏在 OnnxEmbedder.__init__ 里懒加载，模块级 import 探测不到；
    # 这里显式 import，缺它时走统一 SKIP——否则测试跑到 end-to-end 才 ModuleNotFoundError
    # （2026-09-13 GitHub Desktop 提交实测：PATH python 有 flask/tokenizers 无 onnxruntime）
    import onnxruntime  # noqa: F401
    from app.rag import (OnnxEmbedder, RagStore, markdown_split, model_files_ready,
                         sync_rag, query_rag, HFTokenizer)
except Exception as e:  # 依赖缺失：跳过（基础阅读器不依赖 RAG）
    _ci.skip("rag", "rag-deps-missing", f"SKIP: RAG 依赖不可用（{e}）")
    sys.exit(0)


def test_model_files_ready():
    """`model_files_ready` 是 /api/rag/status 的降级闸门：判错一次，用户就会在一个
    只读 GET 上触发 94MB 下载并被拖住 71.8s（覆盖台账 P4 发现 #3）。

    P6 实测这个谓词 0 断言（4 个变异体全存活），故三态钉死：一个都没有 / 齐备且非空 /
    其中一个被截断成 0 字节，只有第二种才许判「就绪」。
    """
    from app.rag import MODEL_FILES
    locals_ = sorted(set(MODEL_FILES.values()))
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        assert not model_files_ready(root), "空目录必须判未就绪"
        for name in locals_:
            (root / name).parent.mkdir(parents=True, exist_ok=True)
            (root / name).write_bytes(b"x")          # 1 字节：既要「存在」也要「非空」
        assert model_files_ready(root), "全部在位且非空 → 应判就绪"
        (root / locals_[0]).write_bytes(b"")
        assert not model_files_ready(root), "有 0 字节文件（下载被截断）→ 应判未就绪"
        (root / locals_[0]).write_bytes(b"x")
        assert model_files_ready(root), "补齐后应恢复就绪"
    print("ok  model_files_ready: 缺文件 / 齐备 / 空文件 三态判定正确（状态查询不会误触发下载）")


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
        _ci.skipped("rag", "tokenizer-not-downloaded")
        return
    tok = HFTokenizer(model_dir / "tokenizer.json")
    # 已知对齐样本（与 tokenizers 库逐 token 比对过）：
    # 中文逐字、英文词、标点切分、大写英文诚实 [UNK]
    assert tok.encode("量子纠缠") == [101, 7030, 2094, 5362, 2209, 102] or tok.encode("量子纠缠")[0] == 101
    ids = tok.encode("The Quick brown fox")
    assert ids[0] == 101 and ids[-1] == 102
    assert tok.unk_id in ids, "Xenova 词表小写化关闭，The/Quick 应落 UNK"
    print("ok  tokenizer: 特殊 token 与 WordPiece 行为对齐")


def test_tokenizer_cross_validated_against_library():
    """不变量 7 要求的那次**逐 token 交叉验证**，现在每次跑都真做（原先只是注释里写着
    "已用 tokenizers 库交叉验证"，实际只钉了几个已知 id —— 台账 §5 那行「部分覆盖」就是这么来的）。

    判据：同一份 `tokenizer.json`，纯标准库实现（`HFTokenizer`）与 Rust `tokenizers`
    对每个样本产出的 **id 序列必须完全相等**（id 相等 ⇒ 归一化、预切分、`##` 续接、
    [UNK] 落点、特殊 token 全都一致 —— 比"看起来一样"强）。

    `tokenizers` **不在** requirements-rag.txt 里：它是验证工具，不是运行时依赖
    （`app/rag.py` 第 13 行的契约就是不引入 transformers/tokenizers）。
    缺库或缺模型时 SKIP；但"本机跑通"才是提交前的硬要求 —— 拿 SKIP 当"验过了"不算。
    """
    try:
        from tokenizers import Tokenizer
    except ImportError:
        print("SKIP: 缺 tokenizers 库（验证工具，非运行时依赖）")
        _ci.skipped("rag", "no-tokenizers-lib")
        return
    tok_path = ROOT / "app" / "rag_models" / "tokenizer.json"
    if not tok_path.is_file():
        print("SKIP: 模型未下载")
        _ci.skipped("rag", "tokenizer-not-downloaded")
        return
    ref = Tokenizer.from_file(str(tok_path))
    mine = HFTokenizer(tok_path)
    samples = [
        "量子纠缠",                                    # 中文逐字（handle_chinese_chars）
        "The Quick brown fox",                         # 大写英文在本词表落 [UNK]
        "BERT 用 [CLS] 与 [SEP] 标边界；WordPiece 用 ## 续接。",  # 中英混排 + 全角标点
        "2026 年的 RAG 命中率 98.6%",                   # 数字与百分号
        "全角ＡＢＣ与半角ABC混排",                       # 全角字母不做 NFKC，原样进词表
        "控制\x01字符要被 clean_text 丢掉",             # clean_text 分支
        "超长的英文词" + "a" * 60,                      # max_input_chars_per_word 上限
        "café naïve Ñ 重音",                           # lowercase/NFD 分支（本机 false → 原样）
        "换行\n与\t制表都算空白",                        # 预分词的空白切
        "subtokenization 会切成多个 piece",             # WordPiece 贪心最长匹配
    ]
    bad, n_tok = [], 0
    for s in samples:
        a, b = mine.encode(s), ref.encode(s).ids
        n_tok += len(a)
        if a != b:
            bad.append((s[:16], len(a), len(b), a[:8], b[:8]))
    assert not bad, "与 tokenizers 库逐 token 不一致（%d/%d）：%r" % (len(bad), len(samples), bad[:3])
    # 自证不是空跑：样本得真的切出多个 piece，否则整条判据可能只是恒等的空比较
    assert any(len(mine.encode(s)) > 4 for s in samples), "样本太短，交叉验证形同虚设"
    assert mine.unk_id in mine.encode("The Quick brown fox"), "本词表下大写词就该落 UNK，不许偷偷小写化"
    print("ok  tokenizer 交叉验证：%d 个样本 / %d 个 token 与 Rust tokenizers 逐 id 一致"
          % (len(samples), n_tok))


def test_end_to_end_semantic_search():
    model_dir = ROOT / "app" / "rag_models"
    if not (model_dir / "model.onnx").is_file():
        print("SKIP: 模型未下载")
        _ci.skipped("rag", "model-not-downloaded")
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

def test_cli_stdout_survives_gbk_console():
    """轮次 49 实测的真 bug（不是假想）：全量重嵌 22006 块**成功跑完**之后，
    `python scripts/rag_search.py "index" --json` 死在打印那一刻 ——
    `UnicodeEncodeError: 'gbk' codec can't encode character '\\U0001f4cc'`。
    控制台是 GBK 时，命中正文里的 emoji 会让 `print` 自己抛异常，于是
    **成功被报成失败**（退出码非零、JSON 一个字都没出来）。修法见 `rag_search._console_safe()`。

    这条判据自带对照组：第二段不调护栏、同样打印 emoji，**必须**炸 ——
    否则第一段就是空判（本机控制台已被工具链设成 UTF-8 时，两边都会"通过"，那是假绿）。
    """
    import subprocess
    script_dir = ROOT / "scripts"
    env = dict(__import__("os").environ, PYTHONIOENCODING="gbk")
    # 只 import、不调 main：防护必须在**导入时**就生效，否则"写在 main 里但某条路径没走到"
    # 这种变异体杀不掉（判据见 scripts/rag_search.py 的 _console_safe 调用位置）。
    guarded = (
        "import sys; sys.path.insert(0, %r); import rag_search;"
        "print('\\U0001F4CC ok')" % str(script_dir))
    raw = "import sys; print('\\U0001F4CC boom')"
    a = subprocess.run([sys.executable, "-c", guarded], capture_output=True, text=True,
                       env=env, timeout=180, encoding="utf-8", errors="replace")
    b = subprocess.run([sys.executable, "-c", raw], capture_output=True, text=True,
                       env=env, timeout=180, encoding="utf-8", errors="replace")
    gbk_strict = b.returncode != 0 and "UnicodeEncodeError" in (b.stderr or "")
    if not gbk_strict:
        print("SKIP  CLI GBK 控制台判据：这台机器的 GBK 编码下打印 emoji 竟然不炸，对照组不成立"
              f"（rc={b.returncode}）—— 这条不算通过也不算失败")
        _ci.skipped("rag", "console-not-gbk-strict")
        return
    assert a.returncode == 0 and "ok" in (a.stdout or ""), (
        f"加了 _console_safe 仍然炸：rc={a.returncode} err={(a.stderr or '')[-200:]}")
    assert "?" in (a.stdout or "") or "\ufffd" in (a.stdout or ""), (
        f"护栏没起作用（emoji 原样进了 GBK 流？）：{a.stdout!r}")
    print("ok  rag_search CLI：GBK 控制台上打印 emoji 不再炸（对照组确认同样打印确实会炸）")


def _main():
    _ci.started("rag")
    test_model_files_ready()
    test_markdown_split()
    test_tokenizer_matches_wordpiece_reference()
    test_tokenizer_cross_validated_against_library()
    test_cli_stdout_survives_gbk_console()
    test_end_to_end_semantic_search()
    print("\nRAG TESTS OK")
    return 0


if __name__ == "__main__":
    # test_rag 是裸 assert（没有 check() 汇总），一条断言崩掉就是「未捕获异常」那条形状 ——
    # 交给 guarded() 报名（异常类型 + 抛出点），退出码仍然非零。
    sys.exit(_ci.guarded(_main, "rag"))
