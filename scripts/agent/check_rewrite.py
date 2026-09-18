"""baike 重写验收：按 docs/writing-spec-v1.1.md §9 做机械检查。

用法: python scripts/agent/check_rewrite.py content/baike/<域>/<词条>.md [...]
      python scripts/agent/check_rewrite.py --exempt <path> [...] <待检路径> [...]
退出码 0 = 全部 PASS；非 0 = 至少一篇 FAIL。warning 不影响退出码。

v1.1 变更：
- 枢纽信号② 两条 OR：②a H2/H3 或编号粗体具名子概念 ≥3；②b「核心机制」节内
  粗体领起列表项 ≥3 且各项叙述 ≥100 字（不含表格行与围栏）——折叠式枢纽由此拿到 3400 豁免。
- exempt-reference（v1.1 §5）：--exempt 显式豁免，或自动读 docs/refactor/exempt-reference.md
  （一行一路径，# 为注释）；命中者输出 EXEMPT、跳过全部检查、计入 PASS。

注意两处盲区（v1.1 §9）：⑦ frontmatter 比的是 HEAD，分片提交后即空转，收尾须另与批前基线比；
⑧ 悬空双链是朴素正则，会误报围栏里的 bash `[[ -f x ]]`，权威口径是 index.db 的 links.resolved。
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
    "定义", "为什么需要它", "具体示例", "何时用与何时不用", "优劣与代价",
    "与相关概念的区别", "常见误区", "面试速答", "相关术语",
}
# 骨架节名全集：枢纽型判定时排除，避免任何词条凭骨架节数冒充枢纽
SKELETON = REQUIRED_H2 | CORE_VARIANTS | {"参考资料"}

CURLY = "“”‘’"
RE_DEF = re.compile(r"^\*\*一句话定义：\*\*[ \t]*(\S.*)$", re.M)
RE_ARXIV = re.compile(r"arXiv[:：\s]\s*(\d{4}\.\d{4,5})")
RE_DOI = re.compile(r"\b(10\.\d{4,9}/[^\s)>\]，。；]+)")
RE_WIKI = re.compile(r"\[\[([^\]|#]+)")
RE_NUM_BOLD = re.compile(r"^\s*\d+\.\s+\*\*[^*]+\*\*", re.M)
# 枢纽信号②b：粗体领起的列表项，兼容 `- **名**：` 与 `- **名：**` 两种写法
RE_BOLD_LEAD = re.compile(r"^\s*(?:[-*+]\s+|\d+\.\s+)\*\*([^*]+?)\*\*[：:]?")
# ②b 每项叙述字数下限。取 70 而非 v1.0 ②a 的 100：折叠式枢纽的项普遍 70–110 字，
# 100 会把 ESB 这类正主挡在豁免外（实测其四项为 107/91/75/46）。
BOLD_ITEM_MIN = 70
EXEMPT_LIST = ROOT / "docs" / "refactor" / "exempt-reference.md"


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


def narrative_body(body: str) -> str:
    """规范 §4 字径：剔除 `> 📌` 导航行与 `## 相关术语`/`## 参考资料` 整节。

    出处与双链不占叙述预算——否则越规范的引用列表会挤掉正文配额，
    反向激励 harness 删引用。
    """
    out, skip = [], False
    for ln in body.splitlines():
        if re.match(r"^## (?!#)", ln):
            skip = norm_title(ln[3:]) in {"相关术语", "参考资料"}
        if skip or ln.lstrip().startswith("> 📌"):
            continue
        out.append(ln)
    return "\n".join(out)


def prose_len(body: str) -> int:
    """正文字数：叙述体去空白后的字符数。"""
    return len(re.sub(r"\s", "", narrative_body(body)))


def has_mermaid(body: str) -> bool:
    return bool(re.search(r"^\s*```\s*mermaid\s*$", body, re.I | re.M))


def table_data_rows(body: str) -> int:
    """正文中最长一张表的"数据行"数：表头与 |---| 分隔行不计。"""
    best, group = 0, []

    def flush(g: list[str]) -> int:
        sep = next(
            (i for i, x in enumerate(g) if re.match(r"^\s*\|[\s:|-]+\|?\s*$", x)), None
        )
        return 0 if sep is None else len(g) - sep - 1

    for ln in list(body.splitlines()) + [""]:
        if ln.lstrip().startswith("|"):
            group.append(ln)
            continue
        if group:
            best = max(best, flush(group))
            group = []
    return best


def subconcept_count(body: str) -> int:
    """枢纽信号②：H2/H3 或编号粗体领起、且其后叙述 ≥100 字的具名子概念数。"""
    lines = body.splitlines()
    marks: list[tuple[int, bool, str]] = []
    for i, ln in enumerate(lines):
        m = re.match(r"^#{2,3} (.+)$", ln)
        if m:
            marks.append((i, norm_title(m.group(1)) not in SKELETON, ""))
        elif RE_NUM_BOLD.match(ln):
            # 编号粗体领起的叙述常与标记同行，需把本行残余计入
            marks.append((i, True, re.sub(r"^\s*\d+\.\s+\*\*[^*]+\*\*[：:]?", "", ln)))
    bounds = [i for i, _, _ in marks] + [len(lines)]
    n = 0
    for k, (i, cand, inline) in enumerate(marks):
        if not cand:
            continue
        seg = inline + "\n".join(lines[i + 1 : bounds[k + 1]])
        if len(re.sub(r"\s", "", seg)) >= 100:
            n += 1
    return n


def core_bold_subconcepts(body: str) -> list[str]:
    """枢纽信号②b（v1.1 §2）：核心机制节内粗体领起、自身叙述 ≥BOLD_ITEM_MIN 字的列表项名。

    多定义汇编收敛成折叠式枢纽时子概念写在项目符号里、拿不到 ②a 的 H2/H3 计数，
    本函数补这条路。计数剔除表格行与围栏内容，避免靠塞表格凑豁免。
    """
    seg: list[str] = []
    grab = False
    for ln in body.splitlines():
        if re.match(r"^## (?!#)", ln):
            grab = norm_title(ln[3:]) in CORE_VARIANTS
            continue
        if grab:
            seg.append(ln)

    fenced: list[bool] = []
    cur = False
    for ln in seg:
        if ln.lstrip().startswith("```"):
            cur = not cur
            fenced.append(True)
            continue
        fenced.append(cur)

    marks = [i for i, ln in enumerate(seg) if RE_BOLD_LEAD.match(ln)]
    bounds = marks + [len(seg)]
    out: list[str] = []
    for k, i in enumerate(marks):
        m = RE_BOLD_LEAD.match(seg[i])
        name = m.group(1).strip().rstrip("：:").strip()
        parts = [seg[i][m.end() :]]
        for j in range(i + 1, bounds[k + 1]):
            if fenced[j] or seg[j].lstrip().startswith("|"):
                continue
            parts.append(seg[j])
        if len(re.sub(r"\s", "", "\n".join(parts))) >= BOLD_ITEM_MIN:
            out.append(name)
    return out


def length_limit(body: str, nchars: int) -> tuple[int, str]:
    """规范 v1.1 §2：超 2200 时按枢纽信号①②决定放行到 3400 还是维持原判。"""
    if nchars <= 2200:
        return 2200, ""
    mer, rows, subs = has_mermaid(body), table_data_rows(body), subconcept_count(body)
    bolds = core_bold_subconcepts(body)
    s1 = mer or rows >= 4
    s2 = subs >= 3 or len(bolds) >= 3
    sig2 = f"具名子概念 {subs}" if subs >= 3 else f"折叠式粗体子概念 {len(bolds)}（{'、'.join(bolds[:3])}）"
    if s1 and s2:
        sig1 = "mermaid" if mer else f"对比表 {rows} 数据行"
        return 3400, f"枢纽型（①{sig1} ②{sig2}）"
    return 2200, (
        f"未获枢纽豁免（①{'满足' if s1 else '不满足：无 mermaid 且对比表 <4 数据行'} "
        f"②不满足：具名子概念 {subs} <3 且核心机制粗体项 {len(bolds)} <3）"
    )


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


def check(path_arg: str, exempt: set[str] | None = None) -> tuple[int, int]:
    """返回 (fail 数, warn 数)。"""
    p = pathlib.Path(path_arg).resolve()
    if exempt and p.as_posix() in exempt:
        print(f"EXEMPT {content_rel(p)}  （v1.1 §5 exempt-reference：原样保留，跳过检查）")
        return 0, 0
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
    elif len(m.group(1).strip()) < 8:
        fails.append(f"② 一句话定义仅 {len(m.group(1).strip())} 字（需 ≥8）")

    # ③ 必备 H2
    titles = set(h2_titles(body))
    missing = sorted(REQUIRED_H2 - titles)
    if missing:
        fails.append("③ 缺少必备 H2：" + "、".join(missing))
    if not (titles & CORE_VARIANTS):
        fails.append("③ 缺少『核心机制』节（可用 §3 变体名：" + "、".join(sorted(CORE_VARIANTS)) + "）")

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
    limit, hub_note = length_limit(body, nchars)
    if nchars > limit:
        fails.append(f"⑥ 正文 {nchars} 字 > 上限 {limit}｜{hub_note}")

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
    hub = f" [{hub_note}]" if limit == 3400 else ""
    print(
        f"{tag} {content_rel(p)}  "
        f"(正文 {nchars}/{limit} 字 / 围栏 {nb} 块 {nl} 行 / 卡 {n_def}def+{n_trap}trap){hub}"
    )
    for f in fails:
        print(f"   ✗ {f}")
    for w in warns:
        print(f"   · {w}")
    return len(fails), len(warns)


def _resolve(s: str) -> str:
    p = pathlib.Path(s)
    return (p if p.is_absolute() else ROOT / p).resolve().as_posix()


def load_exempt(cli: list[str]) -> set[str]:
    """v1.1 §5：--exempt 显式豁免 + docs/refactor/exempt-reference.md 清单（缺文件视为空）。"""
    out = {_resolve(s) for s in cli}
    if not EXEMPT_LIST.exists():
        return out
    for ln in EXEMPT_LIST.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            s = cells[0] if cells else ""
        else:
            s = s.lstrip("->* \t").strip("`").strip()
        if s.endswith(".md"):
            out.add(_resolve(s))
    return out


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    paths: list[str] = []
    cli_exempt: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--exempt":
            if i + 1 >= len(args):
                print("--exempt 缺少路径")
                return 2
            cli_exempt.append(args[i + 1])
            i += 2
            continue
        if a.startswith("--"):
            print(f"未知参数：{a}")
            return 2
        paths.append(a)
        i += 1
    if not paths:
        print(__doc__)
        return 2

    exempt = load_exempt(cli_exempt)
    total_f = total_w = n_ex = 0
    for arg in paths:
        if _resolve(arg) in exempt:
            n_ex += 1
        f, w = check(arg, exempt)
        total_f += f
        total_w += w
    ex = f"，其中 EXEMPT {n_ex} 篇" if n_ex else ""
    print(f"\n{len(paths)} 篇检查：{total_f} 项 FAIL，{total_w} 项 warning{ex}")
    return 1 if total_f else 0


if __name__ == "__main__":
    raise SystemExit(main())
