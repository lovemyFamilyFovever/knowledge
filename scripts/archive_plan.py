# -*- coding: utf-8 -*-
"""生成收件箱归档计划：ARCHIVE-PLAN.md

按来源分组统计，套用分拣规则给出建议（收编 / 待确认 / 建议清理），
用户确认后按批执行。计划文件随语料变化可重复生成。
"""
import os
import time
from collections import Counter
from pathlib import Path

INBOX = Path(__file__).resolve().parents[1] / "content" / "_inbox"
OUT = INBOX / "ARCHIVE-PLAN.md"

# 来源前缀 → (分类, 建议)
RULES = [
    ("repos/deepseek-harness/", "上游仓库文档",
     "不建议收编：这是 deepseek-harness 开源仓库的克隆内容，上游文档随时可查原仓库；你自己的 89 篇研究笔记已在 projects/dsh-agent。建议整目录从 _inbox 删除（原件在 E:\\GitHub\\deepseek-harness）。"),
    ("repos/work/", "工作仓库文档",
     "待你过目：108 份里若有你写的踩坑/总结/方案，指给我，我收进对应子域；纯上游模板部分建议清理。"),
    ("repos/frontend-dev-bookmarks/", "上游仓库文档",
     "同上：开源书签合集，建议不收编或整目录删除。"),
    ("repos/", "上游/学习仓库",
     "多数是克隆仓库的 README 与示例，建议逐仓快速确认后清理；确有价值的单篇指给我收编。"),
    ("desktop/2.md", "个人散件", "已收编（批次1）。"),
    ("desktop/AGENTS.md", "个人散件", "已收编（批次1）。"),
    ("desktop/feishu.txt", "个人散件", "已收编（批次1）。"),
    ("desktop/token_report.txt", "个人散件", "已收编（批次1）。"),
    ("desktop/飞书大模型对话.md", "个人散件", "已收编（批次1）。"),
    ("desktop/", "桌面项目区",
     "待你过目：桌面 code/ dsh/ feishu_code/ pg-tools/ work/ 素材/ .agent-teams/ 下的文档，需要按项目逐个归位；我可以在你确认后逐目录处理。"),
    ("dsh/", "agent 运行时数据",
     "不收编：~/.dsh 下仅 3 个非 Markdown 运行时文件（memory/graph-memory/light-memory），是 agent 状态不是文档。"),
]


def classify(rel: str) -> tuple[str, str]:
    best = ("未分类", "待定")
    for prefix, cat, advice in RULES:
        if rel.startswith(prefix):
            return cat, advice
        best = (cat, advice)
    return best


def main() -> None:
    rows = []
    counter: Counter = Counter()
    for dirpath, dirnames, filenames in os.walk(INBOX):
        dirnames[:] = [d for d in dirnames if d not in SKIP] if (SKIP := {"__pycache__"}) else dirnames
        for fn in filenames:
            p = Path(dirpath) / fn
            rel = p.relative_to(INBOX).as_posix()
            if rel == "ARCHIVE-PLAN.md" or rel == "INVENTORY.md":
                continue
            cat, advice = classify(rel)
            top = "/".join(rel.split("/")[:2])
            counter[(top, cat)] += 1
            rows.append((rel, cat, p.stat().st_size))

    lines = [
        "# 收件箱归档计划",
        "",
        f"生成时间：{time.strftime('%Y-%m-%d %H:%M')} · 共 {len(rows)} 个文件",
        "",
        "## 分组统计",
        "",
        "| 来源（前两级） | 分类 | 文件数 |",
        "|---|---|---|",
    ]
    for (top, cat), n in sorted(counter.items(), key=lambda x: -x[1]):
        lines.append(f"| {top} | {cat} | {n} |")

    lines += ["", "## 各来源建议", ""]
    seen = set()
    for _, cat, advice in RULES:
        if cat in seen:
            continue
        seen.add(cat)
        lines.append(f"- **{cat}**：{advice}")

    lines += [
        "",
        "## 批次 1（已执行）",
        "",
        "桌面顶层 5 个散件已收编：",
        "",
        "- 飞书大模型对话.md → projects/妙搭平台/",
        "- AGENTS.md → projects/不锈钢市场/",
        "- feishu.txt → cookbook/pitfalls/",
        "- token_report.txt → cookbook/fragments/",
        "- 2.md → cookbook/fragments/",
        "",
        "## 执行方式",
        "",
        "你按编号确认，我按批执行；每一批执行后跑 build_index 并 git commit。",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"plan written: {OUT} ({len(rows)} files classified)")


if __name__ == "__main__":
    main()
