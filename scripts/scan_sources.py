# -*- coding: utf-8 -*-
"""Collect every scattered Markdown/text source on this machine into
content/_inbox/, staged for later filing into the taxonomy.

Scope (user directive: collect everything, no filtering):
  - loose *.md / *.txt on the Desktop
  - agent memory trees under ~/.dsh (memory, graph-memory, light-memory)
  - every *.md / *.txt in every E:\\GitHub repo (except this repo and
    myblog, which is ingested into the taxonomy directly)

_bin/.git/node_modules and other build junk are never copied. A written
INVENTORY.md lists per-source counts so nothing on disk stays invisible.
"""
import os
import shutil
import time
from pathlib import Path

HOME = Path(r"C:/Users/Administrator")
DESKTOP = HOME / "Desktop"
GITHUB = Path(r"E:/GitHub")
DSH = HOME / ".dsh"
SELF = GITHUB / "knowledge"
SKIP_DIR_NAMES = {
    ".git", "node_modules", "dist", "build", "coverage", "cache",
    ".vitepress", "__pycache__", "vendor",
}
TEXT_EXTS = {".md", ".txt"}
MARKDOWN_ONLY = {".md"}
# 桌面上的完整项目目录：百科大全已全量迁移，重扫纯重复
EXCLUDE_ROOTS = {DESKTOP / "百科大全"}


def iter_files(src_root: Path, exts: set[str]):
    """Yield files under src_root whose extension is in exts, pruning
    SKIP_DIR_NAMES subtrees during the walk instead of filtering afterwards."""
    for dirpath, dirnames, filenames in os.walk(src_root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        here = Path(dirpath)
        if any(here == ex or ex in here.parents for ex in EXCLUDE_ROOTS):
            dirnames[:] = []
            continue
        for name in filenames:
            path = Path(dirpath) / name
            if path.suffix.lower() in exts:
                yield path


def copy_tree(src_root: Path, dest_root: Path, exts: set[str]) -> tuple[int, int]:
    count = 0
    total_bytes = 0
    for path in iter_files(src_root, exts):
        rel = path.relative_to(src_root)
        dest = dest_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        count += 1
        total_bytes += path.stat().st_size
    return count, total_bytes


def dir_stats(root: Path, exts: set[str]) -> tuple[int, int]:
    count = 0
    total_bytes = 0
    for path in iter_files(root, exts):
        count += 1
        total_bytes += path.stat().st_size
    return count, total_bytes


def main() -> None:
    inbox = SELF / "content" / "_inbox"
    report: list[str] = [
        "# 散落知识源收集清单",
        "",
        f"生成时间：{time.strftime('%Y-%m-%d %H:%M')}",
        "",
        "| 来源 | 已复制 | 字节 | 位置 |",
        "|---|---|---|---|",
    ]

    # 1. 桌面散件
    dest = inbox / "desktop"
    n, size = copy_tree(DESKTOP, dest, TEXT_EXTS)
    report.append(f"| 桌面散件 | {n} | {size} | {dest} |")

    # 2. ~/.dsh agent 记忆（只搬 Markdown，其余类型先盘点不动）
    for name in ("memory", "graph-memory", "light-memory"):
        src = DSH / name
        if not src.exists():
            continue
        dest = inbox / "dsh" / name
        n, size = copy_tree(src, dest, MARKDOWN_ONLY)
        all_n, all_size = dir_stats(src, {p.suffix.lower() for p in src.rglob("*") if p.is_file()})
        report.append(
            f"| ~/.dsh/{name}（markdown 已复制） | {n} | {size} | {dest}；原目录共 {all_n} 文件 {all_size} 字节 |"
        )

    # 3. E:\GitHub 全部仓库
    for repo in sorted(GITHUB.iterdir()):
        if not repo.is_dir() or repo in (SELF, GITHUB / "myblog"):
            continue
        dest = inbox / "repos" / repo.name
        n, size = copy_tree(repo, dest, TEXT_EXTS)
        report.append(f"| 仓库 {repo.name} | {n} | {size} | {dest} |")

    out = inbox / "INVENTORY.md"
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    print(f"\nreport: {out}")


if __name__ == "__main__":
    main()
