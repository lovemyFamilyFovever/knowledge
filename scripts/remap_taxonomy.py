# -*- coding: utf-8 -*-
"""方案A 体裁顶层迁移：主题域 → 百科/文章 双轨 + 体裁域保留。

用法：
  python scripts/remap_taxonomy.py           # dry-run：打印映射摘要
  python scripts/remap_taxonomy.py --apply   # 执行移动 + 清理空目录

规则：
  - source=baike 的参考条目 → baike/<知识域>/（百科）
  - 教程类长文（ai/agent-in-action）→ articles/tutorials/（教程归文章）
  - 其余我的内容（myblog/reader-edit/desktop）→ articles/ 或 handbook/ 或 career/
  - 体裁域不动：interview/ projects/ career/
  - 美化版 .html 与 .notes.md 随主文档一起迁移
"""
import json
import re
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
FM_RE = re.compile(r"\A---\n(.*?)\n---\n\n?", re.S)

# source=baike 的参考条目映射（长前缀优先）
BAIKE_RULES = [
    ("cs-fundamentals/programming-languages/", "baike/programming-languages/"),
    ("cs-fundamentals/database/", "baike/database/"),
    ("cs-fundamentals/security/", "baike/security/"),
    ("cs-fundamentals/network/", "baike/network/"),
    ("cs-fundamentals/os/", "baike/os/"),
    ("cs-fundamentals/algorithms/", "baike/algorithms/"),
    ("cs-fundamentals/distributed/", "baike/distributed/"),
    ("cs-fundamentals/hardware/", "baike/hardware/"),
    ("cs-fundamentals/blockchain/", "baike/blockchain/"),
    ("cs-fundamentals/iot/", "baike/iot/"),
    ("cs-fundamentals/general/", "baike/cs-basics/"),
    ("engineering/software-engineering/", "baike/software-engineering/"),
    ("engineering/architecture/", "baike/architecture/"),
    ("engineering/design-patterns/", "baike/design-patterns/"),
    ("engineering/devops/", "baike/devops/"),
    ("engineering/testing/", "baike/testing/"),
    ("engineering/tools/", "baike/tools/"),
    ("engineering/developer-skills/", "baike/developer-skills/"),
    ("ai/llm-and-agents/", "baike/ai-and-llm/"),
    ("ai/ml/", "baike/machine-learning/"),
    ("ai/data-science/", "baike/data-science/"),
    ("frontend/general/", "baike/frontend-concepts/"),
    ("frontend/frameworks/", "baike/frontend-frameworks/"),
    ("frontend/mobile/", "baike/mobile/"),
    ("backend/middleware/", "baike/middleware/"),
    ("backend/general/", "baike/web-backend/"),
]

# 覆写规则（优先于来源规则，任意来源都生效）
OVERRIDE_RULES = [
    ("ai/agent-in-action/single-file/", "articles/tutorials/single-file/"),
    ("ai/agent-in-action/", "articles/tutorials/"),
]

# 我的内容映射（长前缀优先）
BLOG_RULES = [
    ("cs-fundamentals/network/", "articles/network/"),
    ("frontend/javascript/", "articles/javascript/"),
    ("frontend/vue2/", "articles/vue2/"),
    ("frontend/vue3/", "articles/vue3/"),
    ("frontend/css/", "articles/css/"),
    ("frontend/html/", "articles/html/"),
    ("frontend/typescript/", "articles/typescript/"),
    ("frontend/bugs/", "articles/debugging/"),
    ("frontend/pinia/", "articles/pinia/"),
    ("frontend/optimization/", "articles/optimization/"),
    ("frontend/", "articles/"),
    ("backend/", "articles/backend/"),
    ("ai/general/", "articles/ai/"),
    ("ai/agent-in-action/single-file/", "articles/tutorials/single-file/"),
    ("ai/agent-in-action/", "articles/tutorials/"),
    ("engineering/tools/git/", "articles/git/"),
    ("tools/git/", "articles/git/"),
    ("cookbook/pitfalls/", "handbook/pitfalls/"),
    ("cookbook/skill/", "handbook/skills/"),
    ("cookbook/fragment/", "handbook/fragments/"),
    ("cookbook/", "handbook/"),
    # interview/ projects/ career/ 体裁域不动
]


def source_of(text: str) -> str:
    m = FM_RE.match(text)
    if not m:
        return "none"
    for line in m.group(1).splitlines():
        if line.startswith("source:"):
            return line.split(":", 1)[1].strip().strip('"')
    return "none"


def map_rel(rel: str, source: str) -> str:
    """返回新相对路径；体裁域与未匹配路径保持原位。"""
    if rel.startswith(("interview/", "projects/", "career/")):
        return rel
    for old, new in OVERRIDE_RULES:
        if rel.startswith(old):
            return new + rel[len(old):]
    rules = BAIKE_RULES if source == "baike" else BLOG_RULES
    for old, new in rules:
        if rel.startswith(old):
            return new + rel[len(old):]
    return rel


def collect_moves() -> list[tuple[Path, Path]]:
    moves = []
    for p in sorted(CONTENT.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(CONTENT).as_posix()
        if rel.startswith(("_", "baike/", "articles/", "handbook/")):
            continue
        if not (rel.endswith(".md") or rel.endswith(".html") or rel.endswith(".notes.md")):
            continue
        if rel.endswith(".notes.md"):
            main = rel[:-len(".notes.md")]
            src = source_of((CONTENT / main).read_text(encoding="utf-8", errors="replace")) \
                if (CONTENT / main).is_file() else "none"
        elif rel.endswith(".html") and (CONTENT / (rel[:-5] + ".md")).is_file():
            src = source_of((CONTENT / (rel[:-5] + ".md")).read_text(encoding="utf-8", errors="replace"))
        else:
            src = source_of(p.read_text(encoding="utf-8", errors="replace"))
        new_rel = map_rel(rel, src)
        if new_rel != rel:
            moves.append((p, CONTENT / new_rel))
    return moves


def main(apply: bool) -> None:
    moves = collect_moves()
    counter = Counter(dst.parent.as_posix() for _, dst in moves)
    print(f"待迁移 {len(moves)} 个文件：")
    for dst, n in sorted(counter.items()):
        print(f"  → {dst}: {n}")
    stay = sum(1 for p, rel in ((p, p.relative_to(CONTENT).as_posix()) for p in CONTENT.rglob("*.md")
                               if not any(seg.startswith("_") for seg in p.parts))
               if map_rel(rel, source_of(p.read_text(encoding="utf-8", errors="replace"))) == rel)
    print(f"保持原位（体裁域）：约 {stay} 个")

    if not apply:
        print("\n(dry-run，未执行。加 --apply 落盘)")
        return
    for src, dst in moves:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    # 清理空目录
    for dirpath, dirnames, filenames in sorted(
            [(d, ds, fs) for d, ds, fs in os.walk(CONTENT)], reverse=True):
        p = Path(dirpath)
        if p == CONTENT:
            continue
        try:
            p.rmdir()
        except OSError:
            pass
    print("迁移完成")


if __name__ == "__main__":
    import os
    main("--apply" in sys.argv)
