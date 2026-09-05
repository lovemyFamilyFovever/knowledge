# -*- coding: utf-8 -*-
"""归档批次 1：桌面顶层散件 → taxonomy。

这批文件明确属于用户本人产出，直接落位到最贴切的子域；
frontmatter 记录原始桌面路径，随时可在阅读器里再移动。
"""
import shutil
from pathlib import Path

INBOX_DESKTOP = Path(__file__).resolve().parents[1] / "content" / "_inbox" / "desktop"
CONTENT = Path(__file__).resolve().parents[1] / "content"
TODAY = "2026-09-06"

# 源文件 → (目标子域, 目标文件名, 标题)
PLAN = [
    ("飞书大模型对话.md", "projects/妙搭平台", "飞书大模型对话-数据库切换记录.md", "飞书大模型对话：数据库切换记录"),
    ("AGENTS.md", "projects/不锈钢市场", "项目说明-AGENTS.md", "不锈钢市场使用中心：项目说明"),
    ("feishu.txt", "cookbook/pitfalls", "feishu-precommit-hook失败记录.md", "踩坑：feishu pre-commit hook 失败记录"),
    ("token_report.txt", "cookbook/fragments", "agent-token-report.md", "Agent 会话 Token 消耗报告"),
    ("2.md", "cookbook/fragments", "GitHub仓库抓取脚本-想法.md", "想法：GitHub 冷门仓库抓取脚本"),
]


def frontmatter(title: str, source_path: str) -> str:
    return ("---\n"
            f'title: "{title}"\n'
            'tags: []\n'
            'source: "desktop"\n'
            f'source_path: "桌面/{source_path}"\n'
            f'collected: "{TODAY}"\n'
            'status: "imported"\n'
            "---\n\n")


def main() -> None:
    for src, dest_dir, dest_name, title in PLAN:
        src_path = INBOX_DESKTOP / src
        if not src_path.is_file():
            print(f"skip (missing): {src}")
            continue
        dest = CONTENT / dest_dir
        dest.mkdir(parents=True, exist_ok=True)
        body = src_path.read_text(encoding="utf-8", errors="replace")
        if src.endswith(".txt"):
            body = "```\n" + body.rstrip("\n") + "\n```\n"  # 纯文本日志按代码块渲染
        (dest / dest_name).write_text(frontmatter(title, src) + body, encoding="utf-8")
        src_path.unlink()
        print(f"filed: 桌面/{src} -> {dest_dir}/{dest_name}")


if __name__ == "__main__":
    main()
