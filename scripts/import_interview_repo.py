# -*- coding: utf-8 -*-
"""把本地 GitHub 面试题仓库整仓导入 `content/interview/bigtech/`（大厂面试题）。

源：E:/Collection/GitHub/interview_internal_reference（2019 年仓库，20 个编号目录
`01.阿里篇`…`20.并发篇`；其中 12 个目录只有 .gitkeep、0 篇 md → 跳过）。

设计要点（都对着代码验过，不是拍脑袋）：
- 结构原样保留 `bigtech/<编号篇>/<原文件名>.md`。三级层级靠 store.py::_scan_sub
  的 os.walk + 路由 `/doc/<domain>/<sub>/<path:name>` 原生支持，侧栏按 name 里的
  斜杠分组渲染（app.js:1031 docsByDir），不需要改任何代码。
- 每个 md 补 frontmatter，正文一字不改 —— AGENTS.md「content/ 是唯一事实源」。
- 图片复制到 md 同目录，**引用不改写**：app.js:175 `enhanceRenderedBody` 会把相对
  `<img src>` 按 DOC.rel 解析成 `/raw/<content相对路径>` 直服（MEDIA_EXTS 白名单）。
- 跳过 `.git/`、`sync_link`、`.gitkeep`、以及 0 篇 md 的空目录。
- 幂等：目标已存在即跳过，重跑只补缺、不覆盖。

跑法：python scripts/import_interview_repo.py
"""
import json
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path("E:/Collection/GitHub/interview_internal_reference")
DST = ROOT / "content" / "interview" / "bigtech"

SKIP_DIR_NAMES = {".git"}
SKIP_FILES = {"sync_link", ".gitkeep"}
MEDIA_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
SOURCE = "github"                       # taxonomy.sources 里登记的来源词
COLLECTED = date.today().isoformat()


def has_frontmatter(text: str) -> bool:
    """对齐 store.FM_RE 的语义：BOM + CRLF 宽口径；有的话就不重复补。"""
    head = text.lstrip("\ufeff")
    if not head.startswith("---\n"):
        return False
    return "\n---\n" in head[:500] or head[:500].find("\n---\r\n") != -1


def frontmatter(title: str, source_path: str) -> str:
    # 标题以 `[` 开头会被 store.parse_frontmatter 当列表解析，源仓无此情况，挡一道。
    if title.startswith("["):
        raise ValueError(f"title 会被误解析成列表: {title!r}")
    return (
        "---\n"
        f"title: {json.dumps(title, ensure_ascii=False)}\n"
        "tags: []\n"
        f"source: {json.dumps(SOURCE, ensure_ascii=False)}\n"
        f"source_path: {json.dumps(source_path, ensure_ascii=False)}\n"
        f"collected: {json.dumps(COLLECTED, ensure_ascii=False)}\n"
        'status: "imported"\n'
        "---\n\n"
    )


def import_md(src: Path, out_dir: Path, source_path: str, stem_title=None) -> tuple[str, str]:
    """返回 (状态, 说明)。状态: new|exists|kept-existing-fm"""
    out = out_dir / src.name
    if out.exists():
        return "exists", out.name
    out_dir.mkdir(parents=True, exist_ok=True)
    body = src.read_text(encoding="utf-8", errors="replace")
    title = stem_title or src.stem
    if has_frontmatter(body):
        out.write_text(body, encoding="utf-8")
        return "kept-existing-fm", out.name
    out.write_text(frontmatter(title, source_path) + body, encoding="utf-8")
    return "new", out.name


def main() -> int:
    if not SRC.is_dir():
        print(f"source not found: {SRC}", file=sys.stderr)
        return 1

    counts: dict[str, int] = {"new": 0, "exists": 0, "kept-existing-fm": 0}
    per_dir: list[tuple[str, int]] = []
    skipped_empty: list[str] = []

    # 根目录：README.md（总目录页）+ arch.jpg
    import_md(SRC / "README.md", DST, SRC.name, stem_title="大厂面试题总目录（2019 汇总）")
    counts["new"] = counts.get("new", 0)  # keep dict shape
    for p in sorted(SRC.iterdir()):
        if p.is_file() and p.name != "README.md" and p.name not in SKIP_FILES \
                and p.suffix.lower() in MEDIA_SUFFIXES:
            DST.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, DST / p.name)

    # 20 个编号篇目录
    for d in sorted(x for x in SRC.iterdir() if x.is_dir() and x.name not in SKIP_DIR_NAMES):
        mds = sorted(d.glob("*.md"))
        if not mds:
            skipped_empty.append(d.name)
            continue
        n_here = 0
        for m in mds:
            state, name = import_md(m, DST / d.name, f"{SRC.name} / {d.name}")
            counts[state] = counts.get(state, 0) + 1
            n_here += 1
        per_dir.append((d.name, n_here))
        # 同目录图片（正文相对引用，必须与 md 同处）
        for a in sorted(d.iterdir()):
            if a.is_file() and a.suffix.lower() in MEDIA_SUFFIXES:
                shutil.copy2(a, DST / d.name / a.name)

    md_total = sum(n for _, n in per_dir)
    print(f"source   : {SRC}")
    print(f"target   : {DST.relative_to(ROOT).as_posix()}")
    print(f"collected: {COLLECTED}")
    print()
    print("导入的篇（md 数）:")
    for name, n in per_dir:
        print(f"  {n:4d}  {name}")
    print(f"  目录内合计 {md_total} + 根 README 1 = {md_total + 1} 篇 md")
    if skipped_empty:
        print(f"跳过的 0 篇空目录（{len(skipped_empty)}）: {', '.join(skipped_empty)}")
    print(f"新建 {counts.get('new', 0)}，已存在跳过 {counts.get('exists', 0)}，"
          f"自带 frontmatter 原样保留 {counts.get('kept-existing-fm', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
