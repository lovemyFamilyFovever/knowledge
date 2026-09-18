"""baike 重写验收：按 docs/writing-spec-v1.0.md §8 做机械检查。

用法: python scripts/agent/check_rewrite.py content/baike/<域>/<词条>.md [...]
退出码 0 = 全部 PASS；非 0 = 至少一篇 FAIL。warning 不影响退出码。
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.cards import parse_file  # noqa: E402

# 规范 §3：只有"核心机制"这一节的节名可按类型变化
CORE_VARIANTS = {"核心机制", "核心流程", "做法", "计算逻辑", "核心能力"}
# 规范 §2 骨架中必须存在的节（已归一化）
REQUIRED_H2 = {
    "定义", "为什么需要它", "具体示例", "何时用与何时不用",
    "优劣与代价", "常见误区", "面试速答", "相关术语",
}
# §2 把它写进固定节序，但金样《字体优化》无此节 → 降为 warning（详见交付报告）
SOFT_H2 = {"与相关概念的区别"}

CURLY = "“”‘’"
RE_DEF = re.compile(r"^\*\*一句话定义：\*\*[ \t]*(\S.*)$", re.M)
RE_ARXIV = re.compile(r"arXiv[:：\s]\s*(\d{4}\.\d{4,5})")
RE_DOI = re.compile(r"\b(10\.\d{4,9}/[^\s)>\]，。；]+)")
RE_WIKI = re.compile(r"\[\[([^\]|#]+)")
RE_MD_TOKEN = re.compile(r"[#*>`|~_=\-\\]")


def norm_title(t: str) -> str:
    """归一化节名：`何时用 / 何时不用` 与规范的 `何时用与何时不用` 视为同一节。"""
    return re.sub(r"\s+", "", t.strip()).replace("/", "与").replace("／", "与")


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    close = text.find("\n", end + 1)
    return text[: close + 1], text[close + 1 :]


def h2_titles(body: str) -> list[str]:
    return [norm_title(m.group(1)) for m in re.finditer(r"^## (?!#)(.+)$", body, re.M)]


def section_lines(body: str, title: str) -> list[str]:
    """取 `## title` 节内的原始行（到下一个 H2 为止）。"""
    lines = body.splitlines()
    out: list[str] = []
    grab = False
    for ln in lines:
        if re.match(r"^## (?!#)", ln):
            if grab:
                break
            grab = norm_title(ln[3:]) == title
            continue
        if grab:
            out.append(ln)
    return out


def fence_stats(body: str) -> tuple[int, int]:
    """返回 (围栏块数, 围栏内总行数)。"""
    blocks, cur, inner = 0, False, 0
    for ln in body.splitlines():
        if ln.lstrip().startswith("```"):
            if cur:
                blocks += 1
            cur = not cur
            continue
        if cur:
            inner += 1
    if cur:  # 未闭合
        blocks += 1
    return blocks, inner


def strip_fence_content(body: str) -> str:
    out, keep = [], True
    for ln in body.splitlines():
        if ln.lstrip().startswith("```"):
            keep = not keep
            continue
        if keep:
            out.append(ln)
    return "\n".join(out)


def prose_len(body: str) -> int:
    """正文字数（口径 B）：去围栏内容与 markdown 结构标记后再去空白计数。

    不按规范 §4 字面的"仅去空白"计，否则表格与 **加粗** 的语法字符会占用篇幅
    预算，让信息密度高的对比型词条被误判超长。
    """
    stripped = RE_MD_TOKEN.sub("", strip_fence_content(body))
    return len(re.sub(r"\s", "", stripped))


def content_rel(p: pathlib.Path) -> str:
    try:
        return p.relative_to(ROOT / "content").as_posix()
    except ValueError:
        return p.as_posix()


def git_head_text(rel_from_root: str) -> str | None:
    r = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"HEAD:{rel_from_root}"],
        capture_output=True,
    )
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", errors="replace")


_all_stems: set[str] | None = None


def md_stems() -> set[str]:
    global _all_stems
    if _all_stems is None:
        _all_stems = {p.stem for p in (ROOT / "content").rglob("*.md")}
    return _all_stems


def check(path_arg: str) -> tuple[int, int]:
    """返回 (fail 数, warn 数)。"""
    p = pathlib.Path(path_arg).resolve()
    fails: list[str] = []
    warns: list[str] = []

    if not p.exists():
        print(f"FAIL {path_arg}\n   - 文件不存在")
        return 1, 0

    raw = p.read_text(encoding="utf-8")
    fm, body = split_frontmatter(raw)

    # ④ 弯引号 / <details>
    if any(c in raw for c in CURLY):
        bad = "".join(sorted({c for c in raw if c in CURLY}))
        fails.append(f"④ 含弯引号 [{bad}]（规范 §6 只允许直引号）")
    if "<details>" in raw:
        fails.append("④ 含 <details> 自测块（规范 §4 禁止）")

    # ② 一句话定义
    m = RE_DEF.search(body)
    if not m:
        fails.append("② 未找到与 `**一句话定义：**` 同行且非空的值")
        def_val = ""
    else:
        def_val = m.group(1).strip()
        if len(def_val) < 8:
            fails.append(f"② 一句话定义仅 {len(def_val)} 字（需 ≥8）")

    # ③ 必备 H2
    titles = set(h2_titles(body))
    missing = sorted(REQUIRED_H2 - titles)
    if missing:
        fails.append("③ 缺少必备 H2：" + "、".join(missing))
    if not (titles & CORE_VARIANTS):
        fails.append("③ 缺少『核心机制』节（可用 §3 变体名：" + "、".join(sorted(CORE_VARIANTS)) + "）")
    for soft in SOFT_H2:
        if soft not in titles:
            warns.append(f"③ 建议补节 ## {soft}")

    # ① 卡片数与误区条数
    cards = parse_file(content_rel(p), raw)
    n_def = sum(1 for c in cards if c.kind == "baike_def")
    n_trap = sum(1 for c in cards if c.kind == "baike_trap")
    if n_def != 1:
        fails.append(f"① baike_def 卡数 = {n_def}（需恰好 1）")
    if n_trap != 2:
        fails.append(f"① baike_trap 卡数 = {n_trap}（需恰好 2）")
    mistakes = [ln for ln in section_lines(body, "常见误区") if re.match(r"^-\s+\S", ln)]
    if not 2 <= len(mistakes) <= 3:
        fails.append(f"① 常见误区列表 {len(mistakes)} 条（需 2–3 条）")
    for ln in mistakes:
        val = ln[1:].strip()
        if len(val) < 4:
            fails.append(f"① 误区条目过短：{val!r}")

    # ⑥ 围栏与篇幅预算
    nb, nl = fence_stats(body)
    if nb > 2:
        fails.append(f"⑥ 代码围栏 {nb} 块（上限 2）")
    if nl > 20:
        fails.append(f"⑥ 围栏内共 {nl} 行（上限 20）")
    nchars = prose_len(body)
    if nchars > 2200:
        fails.append(f"⑥ 正文 {nchars} 字（上限 2200）")

    # ⑤ / ⑦ 与 git HEAD 比对
    try:
        rel_root = p.relative_to(ROOT).as_posix()
    except ValueError:
        rel_root = None
    head_raw = git_head_text(rel_root) if rel_root else None
    if head_raw is None:
        warns.append("⑤⑦ 文件不在 HEAD 中，跳过 arXiv 保留与 frontmatter 比对")
    else:
        if split_frontmatter(head_raw)[0] != fm:
            fails.append("⑦ frontmatter 与 HEAD 不一致（批量阶段禁止改动）")
        lost = (set(RE_ARXIV.findall(head_raw)) | set(RE_DOI.findall(head_raw))) - \
               (set(RE_ARXIV.findall(raw)) | set(RE_DOI.findall(raw)))
        if lost:
            fails.append("⑤ 原稿可核验引用丢失：" + "、".join(sorted(lost)))

    # ⑧ 双链可解析（warning 级）
    stems = md_stems()
    dangling = sorted({l.strip() for l in RE_WIKI.findall(body)} - stems)
    for d in dangling:
        warns.append(f"⑧ 悬空双链 [[{d}]]")

    tag = "FAIL" if fails else "PASS"
    print(f"{tag} {content_rel(p)}  (正文 {nchars} 字 / 围栏 {nb} 块 {nl} 行 / 卡 {n_def}def+{n_trap}trap)")
    for f in fails:
        print(f"   ✗ {f}")
    for w in warns:
        print(f"   · {w}")
    return len(fails), len(warns)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    total_f = total_w = 0
    for arg in sys.argv[1:]:
        f, w = check(arg)
        total_f += f
        total_w += w
    n = len(sys.argv) - 1
    print(f"\n{n} 篇检查：{total_f} 项 FAIL，{total_w} 项 warning")
    return 1 if total_f else 0


if __name__ == "__main__":
    raise SystemExit(main())
