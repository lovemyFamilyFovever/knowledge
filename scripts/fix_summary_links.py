# -*- coding: utf-8 -*-
"""摘要文档「五、文件索引」死链修复：/doc/数字（旧百科 ID，三段路由下必 404）
→ [[同目录兄弟文档名]] 双链。dry-run 默认，--apply 写盘后重建 FTS。"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "content" / "projects" / "dsh-agent" / "architecture" / "DeepSeek Harness 架构分析摘要.md"
ARCH = TARGET.parent

# slug 关键词 → 同目录文档名匹配词
MAP = {
    "part1-module-responsibilities": "第一部分",
    "part2-session-scope-events": "第二部分",
    "part3-patterns-improvements": "第三部分",
    "part4-tool-pipeline-prompt": "第四部分",
    "part5-subagent-compaction": "第五部分",
    "part6-llm-adapter-layer": "第六部分：LLM",
    "part7-sandbox-security": "第七部分",
    "part8-code-runtime": "第八部分",
    "part9-settings-credentials-storage": "第九部分",
    "part10-client-extension": "第十部分",
    "summary-architecture-overview": "摘要",
}


def resolve(slug: str) -> str | None:
    kw = MAP.get(slug.strip())
    if not kw:
        return None
    hits = list(ARCH.glob(f"*{kw}*.md"))
    return hits[0].stem if hits else None


def main():
    apply = "--apply" in sys.argv
    t = TARGET.read_text(encoding="utf-8")
    n_before = len(re.findall(r"\]\(/doc/\d+\)", t))

    def sub(mm):
        target = resolve(mm.group(1))
        return f"[[{target}]]" if target else mm.group(0)

    new = re.sub(r"\[([a-z0-9-]+)\]\(/doc/\d+\)", sub, t)
    n_after = len(re.findall(r"\]\(/doc/\d+\)", new))
    n_wikilink = len(re.findall(r"\[\[DeepSeek[^\]]+\]\]", new))
    print(f"dead links before={n_before} after={n_after}, wikilinks={n_wikilink}")
    if apply and new != t:
        TARGET.write_text(new, encoding="utf-8")
        subprocess.run([str(ROOT / ".python" / "python.exe"), str(ROOT / "scripts" / "build_index.py")], check=False)
        print("APPLIED + FTS rebuilt")
    elif not apply:
        print("(dry-run; add --apply to write)")


if __name__ == "__main__":
    main()
