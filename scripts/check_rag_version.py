# -*- coding: utf-8 -*-
"""不变量 7 静态门禁：改了切块/分词逻辑，RAG_CODE_VERSION 必须同时递增。

为什么需要（AGENTS.md 不变量 7）：rag.db 是派生缓存，失效判据是 RAG_CODE_VERSION
（app/rag.py::sync_rag 里与文件 mtime 一起比对）。切块规则或分词口径改了却忘了递增
版本号，索引会带着按旧代码算出的向量继续服务 —— 表现为"语义检索结果莫名其妙变了"
且无法自查，属于最难发现的一类回归。

判据（纯标准库：ast + 文本 diff，不依赖 numpy/tokenizers，可在任何机器上跑）：
  ① 从 HEAD 版与"新版"各取「切块/分词目标函数」的**函数体行区间**；
  ② 解析 `git diff -U0` 的 hunk，得到本次改动的旧行号集 / 新行号集 / 新增行文本；
  ③ 改动行落在任一目标函数区间内 = 命中；
  ④ 命中时必须看到新增行里有 `RAG_CODE_VERSION = "..."`，否则 exit 1。

范围刻意收紧到**函数体**而不是整个 rag.py：改注释、改 rag_status 文案、加日志都不该
被拦。拦不住的假阳性会让人开始 --no-verify 绕过，门禁就废了（同 check_dangling_tokens
的取舍）。

用法：python scripts/check_rag_version.py
缺 git / 非仓库 / 无 diff 一律 exit 0（打印 SKIP 或 ok）——绝不因环境问题挂钩子。
"""
import ast
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAG_REL = "app/rag.py"

# 切块 + 分词 + 嵌入前处理：改了它们，既有向量就不再对应当前代码
TARGET_FUNCS = {
    "markdown_split", "_flush", "_merge_short",              # 切块
    "_norm", "_pre", "_wordpiece", "encode", "token_count",   # 分词（HFTokenizer）
}
VERSION_RE = re.compile(r"^\s*RAG_CODE_VERSION\s*=")
HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def func_ranges(src: str) -> dict:
    """{函数名: (起始行, 结束行)}，行号从 1 起；同名只取第一次出现。

    解析失败时**不**吞异常：源码语法错误 → 调用方必须判定为"无法验证"而非"没改动"。
    （写成 try/except 返回 {} 会让语法错误静默变成放行。）
    """
    out: dict = {}
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in TARGET_FUNCS:
            out.setdefault(node.name, (node.lineno, node.end_lineno or node.lineno))
    return out


def changed_lines(diff_text: str):
    """返回 (旧文件改动行号集, 新文件改动行号集, 新增行文本列表)。"""
    old: set = set()
    new: set = set()
    added: list = []
    old_no = new_no = None
    for line in diff_text.splitlines():
        m = HUNK_RE.match(line)
        if m:
            old_no, new_no = int(m.group(1)), int(m.group(3))
            continue
        if old_no is None or line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("\\"):        # "\ No newline at end of file"
            continue
        if line.startswith("+"):
            new.add(new_no)
            added.append(line[1:])
            new_no += 1
        elif line.startswith("-"):
            old.add(old_no)
            old_no += 1
        else:                             # 上下文行（含空行）
            old_no += 1
            new_no += 1
    return old, new, added


def analyze(head_src: str, new_src: str, diff_text: str) -> dict:
    """纯函数判定，供 tests/test_invariants.py 用合成 diff 单测。"""
    old_lines, new_lines, added = changed_lines(diff_text)
    try:
        head_ranges, new_ranges = func_ranges(head_src), func_ranges(new_src)
    except SyntaxError as e:
        return {"hits": [], "version_bumped": False, "ok": False, "parse_failed": True,
                "error": str(e)}
    hits = [name for name, (a, b) in head_ranges.items()
            if any(a <= ln <= b for ln in old_lines)]
    hits += [name for name, (a, b) in new_ranges.items()
             if name not in hits and any(a <= ln <= b for ln in new_lines)]
    bumped = any(VERSION_RE.match(l) for l in added)
    return {"hits": sorted(hits), "version_bumped": bumped, "ok": not hits or bumped,
            "parse_failed": False}


def _git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + [str(a) for a in args], cwd=str(ROOT),
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def main() -> int:
    if not shutil.which("git"):
        print("[rag-version] SKIP: 未找到 git，跳过 RAG_CODE_VERSION 检查")
        return 0

    head = _git("show", f"HEAD:{RAG_REL}")
    if head.returncode != 0:
        print("[rag-version] SKIP: 读不到 HEAD:app/rag.py（首次提交或非 git 仓库）")
        return 0
    head_src = head.stdout

    diff = _git("diff", "--cached", "-U0", "--", RAG_REL)
    staged = bool(diff.stdout.strip())
    if not staged:
        diff = _git("diff", "HEAD", "-U0", "--", RAG_REL)
    if diff.returncode != 0:
        print("[rag-version] SKIP: git diff 失败（工作区状态异常），跳过")
        return 0
    if not diff.stdout.strip():
        print("[rag-version] ok: app/rag.py 本次无改动")
        return 0

    # 新版源码必须与上面选用的 diff 同源：
    #   有暂存改动 → diff 是 --cached，源码取暂存区 blob（`:path`）；
    #   无暂存改动 → diff 是工作区 vs HEAD，源码必须取**工作区文件**。
    # 曾经无条件优先取 `:path`：未暂存时索引即 HEAD 版，于是拿 HEAD 的行号去套
    # 工作区 diff 的新行号，错位命中相邻函数 → 误报（实测 _flush 被误判）。
    wt = ROOT / RAG_REL
    if staged:
        idx = _git("show", f":{RAG_REL}")
        new_src = idx.stdout if idx.returncode == 0 else wt.read_text(
            encoding="utf-8", errors="replace")
    else:
        new_src = wt.read_text(encoding="utf-8", errors="replace")

    res = analyze(head_src, new_src, diff.stdout)
    if res["parse_failed"]:
        print("[rag-version] 拒绝提交：app/rag.py 无法解析，改动是否触及切块/分词无法判定。")
        print(f"[rag-version]   {res['error']}")
        return 1
    if res["ok"]:
        if res["hits"]:
            print(f"[rag-version] ok: 命中 {', '.join(res['hits'])} 且已递增 RAG_CODE_VERSION")
        else:
            print("[rag-version] ok: 切块/分词函数体未改动")
        return 0

    print("[rag-version] 拒绝提交：切块/分词逻辑改动，但 RAG_CODE_VERSION 未变。")
    print(f"[rag-version]   命中函数：{', '.join(res['hits'])}")
    print("[rag-version]   请递增 app/rag.py 顶部的 RAG_CODE_VERSION，"
          "它会触发向量索引全量重建（不变量 7）。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
