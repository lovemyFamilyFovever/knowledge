"""把 content/ 白名单子集同步到公开站仓（Quartz）的 content/ 目录。

发布契约：排除 漫画/、projects/、小说/ 三棵目录（外加 _ 前缀系统目录），
其余语料一律公开。同步为镜像式（多余文件会被清除），并对排除目录做
双重断言——任何情况下排除项不得出现在目标仓。

用法：
    python scripts/publish_site.py [--dest <站仓content路径>] [--dry-run]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "content"
DEFAULT_DEST = ROOT.parent / "knowledge-site" / "content"

# 小说/ 实为盗版 epub/txt 书库与成人同人（2026-09-20 发布核查发现），公开 = DMCA 风险，禁发
EXCLUDE_DIRS = {"漫画", "projects", "小说"}
PUBLISH_SUFFIXES = {".md", ".html"}
ASSET_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".avif",
    ".mp4",
    ".webm",
    ".mp3",
}


def collect_source() -> dict[Path, Path]:
    """返回 {源文件绝对路径: 相对 content/ 的路径}。"""
    out: dict[Path, Path] = {}
    for p in SRC.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(SRC)
        if any(part.startswith("_") for part in rel.parts):
            continue
        if rel.parts and rel.parts[0] in EXCLUDE_DIRS:
            continue
        if p.suffix.lower() not in PUBLISH_SUFFIXES | ASSET_SUFFIXES:
            continue
        out[p] = rel
    return out


def assert_gate(rel: Path) -> None:
    parts = set(rel.parts)
    bad = parts & (EXCLUDE_DIRS | {".git"})
    has_underscore = any(part.startswith("_") for part in rel.parts)
    if bad or has_underscore or not rel.parts:
        raise RuntimeError(f"排除断言触发，禁止发布: {rel}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    dest: Path = args.dest.resolve()
    if dest.exists() and not any(
        (dest.parent / name).exists()
        for name in ("quartz.config.yaml", "quartz.config.default.yaml", "quartz.config.ts")
    ):
        print(f"目标 {dest} 不像 Quartz 站仓（缺 quartz.config.*），中止", file=sys.stderr)
        return 1

    files = collect_source()
    rels = set()
    for rel in files.values():
        assert_gate(rel)
        rels.add(rel)

    # 发布前置门禁：待发布 md 的 frontmatter 必须过严格 YAML 检查。
    # 本地阅读器容错，站侧 Quartz 不容错——缺这一步时，一次 `title:"x"` 就能让
    # 整站构建红在 GitHub Actions 上（2026-09-25 实测踩过）。
    from check_frontmatter import lint_file  # 同目录；延迟导入避开 E402

    bad = []
    for src, rel in files.items():
        if src.suffix.lower() != ".md":
            continue
        probs = lint_file(src)
        if probs:
            bad.append((rel, probs))
    if bad:
        print(f"frontmatter 门禁未过，拒绝同步（{len(bad)} 篇）：", file=sys.stderr)
        for rel, probs in bad[:40]:
            for ln, msg in probs:
                print(f"  {rel}:{ln}  {msg}", file=sys.stderr)
        print("先修语料头，或跑 python scripts/check_frontmatter.py 看全量清单。", file=sys.stderr)
        return 1

    existing = (
        {p.relative_to(dest) for p in dest.rglob("*") if p.is_file()} if dest.exists() else set()
    )
    to_copy = {src: rel for src, rel in files.items() if rel not in existing}
    to_refresh = {
        src: rel
        for src, rel in files.items()
        if rel in existing and src.stat().st_mtime > (dest / rel).stat().st_mtime
    }
    to_prune = sorted(existing - rels - {Path("index.md")})  # index.md 为脚本自管的落地页

    print(f"目标: {dest}")
    print(f"源文件 {len(files)}｜新增 {len(to_copy)}｜刷新 {len(to_refresh)}｜清除 {len(to_prune)}")
    if args.dry_run:
        for r in to_prune[:10]:
            print(f"  prune: {r}")
        return 0

    for src, rel in {**to_copy, **to_refresh}.items():
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    for rel in to_prune:
        (dest / rel).unlink(missing_ok=True)

    if not (dest / "index.md").exists():
        sections = sorted(p.name for p in dest.iterdir() if p.is_dir())
        body = ["---", "title: 知库 · 技术花园", "---", "", "公开知识库。按主题浏览：", ""]
        body += [f"- [{s}](/{s}/)" for s in sections]
        (dest / "index.md").write_text("\n".join(body) + "\n", encoding="utf-8")
        print("已生成落地页 index.md")

    # 事后复查：目标仓内绝不允许出现排除目录
    for p in dest.rglob("*"):
        rel = p.relative_to(dest)
        if rel.parts and (rel.parts[0] in EXCLUDE_DIRS or rel.parts[0].startswith("_")):
            raise RuntimeError(f"发布后泄漏复检失败: {rel}")
    print("同步完成，排除项复检通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
