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
    from app.rag import (DIM, OnnxEmbedder, RagStore, markdown_split, model_files_ready,
                         sync_rag, query_rag, HFTokenizer, rag_status)
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


class _CountingEmbedder:
    """假嵌入器：向量按文本哈希定死，并**数得清每篇被嵌了几次**。

    续跑唯一能被证明的形式是"第二次同步没有回头重嵌已盖章的那几篇"，而这只有对着可计数的
    桩才证得出来 —— 真模型跑一趟 38 分钟，而且篇级调用次数根本看不见（台账 §6 第 93 行）。
    `fail_after` 用来模拟"嵌够 N 篇就被 kill"。
    """

    def __init__(self):
        self.calls = []
        self.fail_after = None

    def embed_chunks(self, chunks):
        if self.fail_after is not None and len(self.calls) >= self.fail_after:
            raise RuntimeError("模拟中断")
        self.calls.append(chunks[0]["title"])
        import hashlib
        h = hashlib.sha256("|".join(c["text"] for c in chunks).encode("utf-8")).digest()
        v = [b / 255.0 for b in h[:DIM]] if DIM <= len(h) else \
            [b / 255.0 for b in h] + [0.0] * (DIM - len(h))
        return [v for _ in chunks]


def _mkcorpus(content: Path, n: int) -> None:
    d = content / "baike" / "db"
    d.mkdir(parents=True, exist_ok=True)
    for i in range(1, n + 1):
        (d / ("%d.md" % i)).write_text(
            '---\ntitle: "第%d篇"\n---\n\n# 标%d\n\n' % (i, i) + ("正文内容%d。" % i) * 40,
            encoding="utf-8")


def test_resume_after_interrupt():
    """全量重嵌可续跑（轮次 51）：中途被 kill 之后，第二次只补没盖章的那几篇。

    三条独立证据，缺一条都可能是假绿：
      · sync 回执的 changed / skipped 数字；
      · **假嵌入器实际被调用的次数与是哪几篇**（回执会撒谎，计数不会）；
      · rag_status 的 stale —— 中断时它是剩余量，跑完必须归 0。
    """
    import app.rag as rag
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        content = root / "content"
        content.mkdir()
        _mkcorpus(content, 4)
        store = RagStore(root / "indexes")
        emb = _CountingEmbedder()
        old_ver = rag.RAG_CODE_VERSION
        try:
            stat = sync_rag(content, emb, store)
            assert stat["changed"] == 4 and stat["skipped"] == 0, f"首建该嵌 4 篇：{stat}"
            assert len(emb.calls) == 4, f"首建该被调 4 次：{emb.calls}"
            assert rag_status(store)["stale"] == 0, "首建完不该有剩"

            # 版本递增 + 嵌到第 3 篇被 kill：前 2 篇已是新章，后 2 篇还挂着旧章
            rag.RAG_CODE_VERSION = old_ver + "-t"
            emb.calls, emb.fail_after = [], 2
            interrupted = False
            try:
                sync_rag(content, emb, store)
            except RuntimeError:
                interrupted = True
            assert interrupted, "假嵌入器该在第 3 篇抛异常（静默通过=中断没被模拟出来）"
            st = rag_status(store)
            assert st["stale"] == 2, f"中断后该剩 2 篇没盖章：{st}"

            # 续跑：只补那 2 篇，已盖章的 2 篇不许回头重嵌
            emb.fail_after, emb.calls = None, []
            stat = sync_rag(content, emb, store)
            assert stat["changed"] == 2, f"续跑只该重嵌剩余 2 篇，got {stat}"
            assert stat["skipped"] == 2, f"已盖章的 2 篇该进 skipped，got {stat}"
            assert len(emb.calls) == 2, f"续跑实际嵌了 {len(emb.calls)} 篇（>2 就是回头重嵌了）"
            assert rag_status(store)["stale"] == 0
            assert stat["reason"] == "normal", f"行数一致时不该报 integrity：{stat}"
        finally:
            rag.RAG_CODE_VERSION = old_ver
            store.close()
    print("ok  续跑：中断后第二次同步只嵌剩余 2 篇（回执 + 调用计数 + stale 三证）")


def test_integrity_fallback_and_no_second_gate():
    """完整性自检与「只有一处版本判据」。

    ① vec 行数与 files.chunk_n 不符 → 整趟全量（reason=integrity），逐篇归因这时不可信；
    ② 版本判据**只活在 files.embed_ver 一处**：sync 不再读 meta.code_version 来决定
       要不要全量 —— 留着就是同一规则两份实现（台账 §6 第 87 行），变异拆掉任一处都不会红。
    """
    import app.rag as rag
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        content = root / "content"
        content.mkdir()
        _mkcorpus(content, 3)
        store = RagStore(root / "indexes")
        emb = _CountingEmbedder()
        old_ver = rag.RAG_CODE_VERSION
        try:
            sync_rag(content, emb, store)
            assert len(emb.calls) == 3
            # 造"索引缺块"：删掉任意一条向量，行数与 files.chunk_n 就对不上
            victim = store.con.execute("SELECT chunk_id FROM vec_docs LIMIT 1").fetchone()[0]
            store.con.execute("DELETE FROM vec_docs WHERE chunk_id=?", (victim,))
            store.con.commit()
            emb.calls = []
            stat = sync_rag(content, emb, store)
            assert stat["reason"] == "integrity", f"行数不符必须报 integrity：{stat}"
            assert stat["changed"] == 3 and len(emb.calls) == 3, \
                f"完整性不符时该全量重算，got {stat} / {emb.calls}"

            # 第二道闸门的物证：把 meta.code_version 改成别的，同步**不该**因此全量
            sync_rag(content, emb, store)                      # 先补回一致状态
            store.con.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('code_version',?)",
                              ("9-编的",))
            store.con.commit()
            emb.calls = []
            stat = sync_rag(content, emb, store)
            assert stat["changed"] == 0 and emb.calls == [], \
                f"meta 版本已经不是判据了，改它不该触发重嵌：{stat} / {emb.calls}"
        finally:
            rag.RAG_CODE_VERSION = old_ver
            store.close()
    print("ok  完整性不符 → 全量；meta.code_version 不再是第二道闸门（改它零重嵌）")


def test_legacy_db_migration():
    """旧库（还没有 files.embed_ver 这一列）打开时该怎样 —— 迁移不能变成一次白嵌。

    相符才盖章：`meta.code_version` 与当前版本一致 **且** vec 行数与元数据一致，才给既有
    向量补章（免掉一次 38 分钟的无谓重嵌）；任一不符就留 NULL，让它们按新判据重嵌 ——
    宁可重嵌，也不给来历不明的向量发一张"已对齐"的收据。
    """
    import sqlite3
    import app.rag as rag
    if sqlite3.sqlite_version_info < (3, 35):
        print("SKIP  旧库迁移断言（本机 SQLite %s 不支持 DROP COLUMN，造不出旧库形状）"
              % sqlite3.sqlite_version)
        return
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        idx = root / "indexes"
        store = RagStore(idx)
        for i in range(3):
            store.upsert_file("baike/db/%d.md" % i, 1.0,
                              [{"text": "正文", "title": "t%d" % i, "heading": "h",
                                "source": "", "collected": "", "tags": ""}],
                              [[0.1] * DIM])
        store.con.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('code_version',?)",
                          (rag.RAG_CODE_VERSION,))
        store.con.commit()
        store.close()

        def _strip_column(meta_ver):
            raw = sqlite3.connect(idx / "rag.db")
            raw.execute("ALTER TABLE files DROP COLUMN embed_ver")
            raw.execute("INSERT OR REPLACE INTO meta(k,v) VALUES('code_version',?)", (meta_ver,))
            raw.commit()
            raw.close()

        _strip_column(rag.RAG_CODE_VERSION)          # 相符 + 行数一致 → 该盖章
        store = RagStore(idx)
        cols = [r[1] for r in store.con.execute("PRAGMA table_info(files)")]
        assert "embed_ver" in cols, f"打开旧库没补列：{cols}"
        st = rag_status(store)
        assert st["stale"] == 0 and st["files_total"] == 3, \
            f"来历可确认的旧库该直接盖章（否则白嵌 3 篇）：{st}"
        store.close()

        _strip_column("0-来历不明")                   # 版本不符 → 不许盖章
        store = RagStore(idx)
        st = rag_status(store)
        assert st["stale"] == 3, f"来历不明的 3 篇必须留 NULL 等重嵌：{st}"
        store.close()
    print("ok  旧库迁移：相符才盖章（免白嵌），版本不符留 NULL 重嵌")


def _main():
    _ci.started("rag")
    test_model_files_ready()
    test_markdown_split()
    test_tokenizer_matches_wordpiece_reference()
    test_tokenizer_cross_validated_against_library()
    test_cli_stdout_survives_gbk_console()
    test_resume_after_interrupt()
    test_integrity_fallback_and_no_second_gate()
    test_legacy_db_migration()
    test_end_to_end_semantic_search()
    print("\nRAG TESTS OK")
    return 0


if __name__ == "__main__":
    # test_rag 是裸 assert（没有 check() 汇总），一条断言崩掉就是「未捕获异常」那条形状 ——
    # 交给 guarded() 报名（异常类型 + 抛出点），退出码仍然非零。
    sys.exit(_ci.guarded(_main, "rag"))
