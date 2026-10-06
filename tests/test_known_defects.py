# -*- coding: utf-8 -*-
"""已知缺陷复现探针（P4 发现 → 修复轮的回归锚点）——现已全绿，挂进 pre-commit 与 ci.yml。

来历：P4 轮先在这里写下两条红断言（D1 空子域 /browse 500、D2 resolve 前缀分歧致
/api/rmdir · /api/import 500）。按手册「先写红断言、修复留待单独一轮」的纪律，
当时**故意不挂钩子**（红断言挂上去会让每次提交都被已知缺陷卡死，钩子一挂等于没有钩子）。
修复轮把两条改绿后，本文件接入钩子与 CI —— 从此这两个缺陷若被重新引入，提交即被拦下。

用法：python tests/test_known_defects.py
退出码：0 = 两条都已修复；1 = 缺陷回归。

不含任何对真实 content/ 的读写：全部用 tempfile 迷你语料。
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.app import create_app  # noqa: E402

results = []


def record(code, name, ok, detail=""):
    results.append((code, name, ok, detail))
    print(("  PASS " if ok else "  FAIL ") + f"[{code}] {name}" + (f"  | {detail}" if detail else ""))


def seed(root: Path) -> None:
    c = root / "content"
    (c / "ai" / "llm-and-agents").mkdir(parents=True)
    (c / "ai" / "llm-and-agents" / "A.md").write_text(
        "---\ntitle: \"A\"\n---\n\n# A\n\n正文。\n", encoding="utf-8")
    # 空子域：无任何文档（真实语料里 articles/backend、career/resume 就是这种）
    (c / "ai" / "空子域").mkdir(parents=True)
    (c / "_meta").mkdir()
    (c / "_meta" / "taxonomy.json").write_text(
        '{"domains":{"ai":{"label":"AI"}},"subs":{"llm-and-agents":"大模型","空子域":"空子域"}}',
        encoding="utf-8")
    # 砧模型：避免 OnnxEmbedder 走联网下载（P4 发现 #3 / 94MB）
    m = root / "app" / "rag_models"
    m.mkdir(parents=True)
    (m / "model.onnx").write_bytes(b"x")
    (m / "tokenizer.json").write_bytes(b"{}")


def d1_empty_sub() -> None:
    """D1：空子域的 /browse 页 500（_workbench_empty 缺 doc.name → Jinja UndefinedError）。"""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        root = Path(td).resolve()
        seed(root)
        c = create_app(root).test_client()
        r = c.get("/browse/ai/空子域")
        record("D1", "空子域 /browse 不应 5xx（代码注释明说要渲染空态工作台）",
               r.status_code < 500,
               f"status={r.status_code} {'UndefinedError: dict has no attribute name' if r.status_code == 500 else ''}")
        record("D1", "/browse/ai/llm-and-agents（有文档）仍应 302 到首篇",
               c.get("/browse/ai/llm-and-agents").status_code == 302,
               f"status={c.get('/browse/ai/llm-and-agents').status_code}")
        # 空子域在树上可见（0 篇也会入树）→ 用户点得到，才构成可达缺陷
        # 注意 jsonify 默认 ensure_ascii=True，中文被转义，必须解析后再判
        tree = c.get("/api/tree").get_json()
        record("D1", "空子域确实出现在树里（证明缺陷可达）",
               "空子域" in json.dumps(tree, ensure_ascii=False))


def d2_resolve_prefix() -> None:
    """D2：content 与 content.resolve() 前缀分歧时 /api/rmdir、/api/import 500。

    触发条件：KB_ROOT 的祖先链含 junction / 软链 / 8.3 短名。
    同仓 app.py::safe_rel 已按 resolve() 比较（注释明写 8.3 短路径），
    但这两个接口自己用未解析的 content 拼路径又去 relative_to(content.resolve())。
    """
    td = tempfile.mkdtemp()
    link = Path(td) / "link"
    try:
        real = Path(td) / "real"
        real.mkdir()
        seed(real)
        if os.name == "nt":
            r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(real)],
                               capture_output=True, text=True)
            ok_link = r.returncode == 0 and link.exists()
        else:
            try:
                link.symlink_to(real, target_is_directory=True)
                ok_link = True
            except OSError:
                ok_link = False
        if not ok_link:
            record("D2", "构造 junction/symlink（缺陷路径可达性前置）", False, "本机无法创建链接")
            return
        if str(link / "content") == str((link / "content").resolve()):
            record("D2", "路径产生 resolve 分歧（复现前置）", False, "该环境不产生分歧，无法复现")
            return

        c = create_app(link).test_client()
        r1 = c.post("/api/rmdir", json={"domain": "ai", "sub": "llm-and-agents"})
        r2 = c.post("/api/import", data={
            "domain": "ai",
            "files": (io.BytesIO("# 探针\n".encode("utf-8")), "探针.md"),
        }, content_type="multipart/form-data")
        record("D2", "/api/rmdir 在 resolve 前缀分歧下不应 5xx", r1.status_code < 500,
               f"status={r1.status_code}")
        record("D2", "/api/import 在 resolve 前缀分歧下不应 5xx", r2.status_code < 500,
               f"status={r2.status_code}")
        # 修复后的契约：接口成功 ⇒ 文件恰好落一份（旧缺陷是"文件已落盘却报 500"，
        # 用户重试后每试一次多一个 ~2/~3 副本）。这里断言成功与份数一致，
        # 若有人把"先落盘后抛错"重新引入，要么状态非 200、要么副本堆积，两条都会红。
        dup = sorted(p.name for p in (real / "content" / "ai").rglob("探针*.md"))
        record("D2", "/api/import 成功且只落一份（无 ~2/~3 副本堆积）",
               r2.status_code == 200 and len(dup) == 1, f"已落盘={dup}")
    finally:
        if link.exists() or link.is_symlink():
            try:
                os.rmdir(link)   # junction 必须摘链，rmtree 会穿透删真实目录
            except OSError:
                pass
        shutil.rmtree(td, ignore_errors=True)


def main() -> int:
    print("== 已知缺陷复现探针（P4 发现，修复轮的目标）==")
    print("\n[D1] 空子域 /browse 500")
    d1_empty_sub()
    print("\n[D2] resolve 前缀分歧 → /api/rmdir · /api/import 500")
    d2_resolve_prefix()

    bad = [r for r in results if not r[2]]
    print(f"\n{len(results) - len(bad)} passed, {len(bad)} failed（failed 即缺陷仍在）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
