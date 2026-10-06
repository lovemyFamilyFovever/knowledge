# -*- coding: utf-8 -*-
"""One-shot ingest: myblog VitePress docs -> knowledge content tree.

Copies Markdown posts into the taxonomy, merging source-provenance fields
into each file's existing frontmatter. Infra files (site index, 404, tags,
public assets, VitePress config) and the four empty section shells
(react/angular/vite/node) are skipped.
"""
import json
from pathlib import Path

BLOG = Path(r"E:/GitHub/myblog/docs")
ROOT = Path(__file__).resolve().parents[1] / "content"
COLLECTED = "2026-09-05"

# 相对 docs/ 的路径前缀（按最长前缀匹配）-> 目标目录；空壳栏目跳过。
DIR_MAP = {
    "frontend/javascript": "frontend/javascript",
    "frontend/vue2": "frontend/vue2",
    "frontend/vue3": "frontend/vue3",
    "frontend/css": "frontend/css",
    "frontend/html": "frontend/html",
    "frontend/TypeScript": "frontend/typescript",
    "frontend/bugs": "frontend/debugging",
    "frontend/pinia": "frontend/pinia",
    "frontend/optimization": "frontend/optimization",
    "frontend": "frontend",
    "backend": "backend",
    "artificialIntelligence": "ai/general",
    "interview": "interview",
    "network": "cs-fundamentals/network",
    "tools": "engineering/tools",
    "project": "projects",
    "article": "cookbook",
    "blog": "career/journal",
}
SKIP_PREFIXES = {"frontend/react", "frontend/angular", "frontend/vite", "frontend/node"}
SKIP_FILES = {"index.md", "404.md"}
SKIP_DIRS = {".vitepress", "public", "tags", "node_modules", ".vscode"}
SOURCE_FIELDS = {
    "source": json.dumps("myblog", ensure_ascii=False),
    "collected": json.dumps(COLLECTED, ensure_ascii=False),
    "status": json.dumps("imported", ensure_ascii=False),
}


def merge_frontmatter(text: str, rel: str) -> str:
    fields = dict(SOURCE_FIELDS)
    fields["source_path"] = json.dumps(rel, ensure_ascii=False)
    additions = "".join(f"{key}: {value}\n" for key, value in fields.items())
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            head = text[: end + 1]
            tail = text[end + 1:].lstrip("-\n").lstrip()
            return head + additions + "---\n\n" + tail
    title = Path(rel).stem
    block = "---\n" + f"title: {json.dumps(title, ensure_ascii=False)}\n" + additions + "---\n\n"
    return block + text


def target_for(rel_parts: tuple[str, ...]) -> tuple[str, ...] | None:
    joined = "/".join(rel_parts)
    if any(joined.startswith(skip) for skip in SKIP_PREFIXES):
        return None
    for depth in range(len(rel_parts), 0, -1):
        prefix = "/".join(rel_parts[:depth])
        if prefix in DIR_MAP:
            mapped = DIR_MAP[prefix]
            remainder = "/".join(rel_parts[depth:])
            return tuple((mapped + "/" + remainder).split("/")) if remainder else tuple(mapped.split("/"))
    return None


def main() -> None:
    copied: dict[str, int] = {}
    for path in sorted(BLOG.rglob("*.md")):
        rel_parts = path.relative_to(BLOG).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        if rel_parts[-1] in SKIP_FILES and len(rel_parts) == 1:
            continue
        target = target_for(rel_parts)
        if target is None:
            continue
        dest = ROOT.joinpath(*target)
        dest.parent.mkdir(parents=True, exist_ok=True)
        merged = merge_frontmatter(path.read_text(encoding="utf-8"), "/".join(rel_parts))
        dest.write_text(merged, encoding="utf-8")
        key = "/".join(target[:-1]) if target[:-1] else "(root)"
        copied[key] = copied.get(key, 0) + 1

    total = sum(copied.values())
    print(f"ingested {total} markdown files from myblog")
    for key in sorted(copied):
        print(f"  {key}: {copied[key]}")


if __name__ == "__main__":
    main()
