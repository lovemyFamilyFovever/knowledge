# -*- coding: utf-8 -*-
"""One-shot migration: 百科大全 SQLite -> knowledge content tree.

Reads docs.db, writes each document as Markdown (content column) and, when a
rendered page exists (html_content column), as a sibling .html file kept
byte-for-byte. Documents whose content is a full HTML page are written as
.html only. Category chains map onto the two-level taxonomy via CATEGORY_MAP;
unmapped chains fall back to content/_unfiled/<chain>/ so nothing is lost.
The 89 DSH Agent analysis docs are personal study material on DeepSeek's
open-source harness; they land in projects/dsh-agent/.
"""
import json
import re
import sqlite3
from pathlib import Path

BAKE_DB = Path(r"C:/Users/Administrator/Desktop/百科大全/docs.db")
ROOT = Path(__file__).resolve().parents[1] / "content"
COLLECTED = "2026-09-05"

# 完整分类链（顶级 / 子级 [/ 叶级]）-> 目标子目录（相对 content/）。
CATEGORY_MAP = {
    # 职业管理
    "职业管理 / 项目管理实战": "career/management",
    "职业管理 / 项目经历简历": "career/resume",
    "职业管理 / 项目管理简历": "career/resume",
    "开发术语 / 职业发展与管理": "career",
    # 开发术语
    "开发术语 / 安全与加密": "cs-fundamentals/security",
    "开发术语 / 数据库": "cs-fundamentals/database",
    "开发术语 / AI与大模型": "ai/llm-and-agents",
    "开发术语 / 软件工程与测试": "engineering/software-engineering",
    "开发术语 / 架构与设计": "engineering/architecture",
    "开发术语 / 网络与协议": "cs-fundamentals/network",
    "开发术语 / 前端开发": "frontend/general",
    "开发术语 / 操作系统与Linux": "cs-fundamentals/os",
    "开发术语 / DevOps与云原生": "engineering/devops",
    "开发术语 / 编程语言基础": "cs-fundamentals/programming-languages",
    "开发术语 / 数据结构与算法": "cs-fundamentals/algorithms",
    "开发术语 / 设计模式": "engineering/design-patterns",
    "开发术语 / 分布式系统": "cs-fundamentals/distributed",
    "开发术语 / 消息与中间件": "backend/middleware",
    "开发术语 / 测试与质量": "engineering/testing",
    "开发术语 / 计算机硬件基础": "cs-fundamentals/hardware",
    "开发术语 / 计算机科学基础": "cs-fundamentals/general",
    "开发术语 / 开发工具与环境": "engineering/tools",
    "开发术语 / Web后端开发": "backend/general",
    "开发术语 / 移动开发": "frontend/mobile",
    "开发术语 / 数据科学与大数据": "ai/data-science",
    "开发术语 / 区块链与Web3": "cs-fundamentals/blockchain",
    "开发术语 / 物联网与嵌入式": "cs-fundamentals/iot",
    # 技术题库 -> interview/*
    "技术题库 / JavaScript核心": "interview/javascript",
    "技术题库 / React与Vue框架": "interview/frameworks",
    "技术题库 / CSS与HTML": "interview/css-html",
    "技术题库 / 性能优化": "interview/performance",
    "技术题库 / Node.js与全栈": "interview/node-fullstack",
    "技术题库 / 工程化与工具链": "interview/engineering",
    "技术题库 / 系统架构设计": "interview/architecture",
    "技术题库 / 团队管理": "interview/management",
    "技术题库 / AI技术应用": "interview/ai",
    "技术题库 / 行为面试": "interview/behavioral",
    "技术题库 / 职业发展": "interview/career",
    "技术题库 / 行业洞察": "interview/industry",
    "技术题库 / AI Agent面试专题": "interview/ai-agent",
    # 技术文章
    "技术文章 / 编程语言": "cs-fundamentals/programming-languages",
    "技术文章 / Web开发框架": "frontend/frameworks",
    "技术文章 / 数据库与存储": "cs-fundamentals/database",
    "技术文章 / 架构与设计": "engineering/architecture",
    "技术文章 / AI与机器学习": "ai/ml",
    "技术文章 / DevOps与运维": "engineering/devops",
    "技术文章 / 数据工程与分析": "ai/data-science",
    "技术文章 / 职业发展": "career",
    "技术文章 / 跨界视野": "career/insights",
    "技术文章 / 开发者技能": "engineering/developer-skills",
    # AI Agent 开发实战
    "AI Agent 开发实战 / 理论基础与核心架构": "ai/agent-in-action",
    "AI Agent 开发实战 / 框架生态与开发实战": "ai/agent-in-action",
    "AI Agent 开发实战 / 高级主题与未来展望": "ai/agent-in-action",
    "AI Agent 开发实战 / 完整版与单文件": "ai/agent-in-action/single-file",
    # 项目分析（个人项目复盘）
    "项目分析 / 抖音Vue项目": "projects/retrospectives",
    "项目分析 / 我的本地项目": "projects/retrospectives",
}
# DSH Agent 项目分析（对 DeepSeek 开源 harness 的个人研究材料）
DSH_LEAF_MAP = {
    "沙箱执行机制": "sandbox",
    "模型接入层": "llm",
    "API参考手册": "api",
    "核心架构分析": "architecture",
    "Cordis框架分析": "cordis",
    "前端架构分析": "frontend",
    "协议适配层": "protocol",
    "知识图谱": "knowledge-graph",
    "插件体系图谱": "plugins",
    "Agent框架生态调研": "research",
    "MCP协议调研": "research",
    "LLM能力对比": "research",
    "RAG技术调研": "research",
    "开发者入门指南": "guides",
    "插件开发教程": "guides",
    "架构设计文档": "architecture",
    "技术深度解析": "deep-dives",
    "技术栈图谱": "stack",
    "会话产出清单": "artifacts",
}


def sanitize(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', " ", name).strip()
    return (cleaned or "untitled")[:80]


def yaml_value(value):
    return json.dumps(value, ensure_ascii=False)


def frontmatter(title: str, source_path: str, favorite: bool) -> str:
    lines = [
        "---",
        f"title: {yaml_value(title)}",
        f"tags: {yaml_value([])}",
        f"source: {yaml_value('baike')}",
        f"source_path: {yaml_value(source_path)}",
        f"collected: {yaml_value(COLLECTED)}",
        f"status: {yaml_value('imported')}",
    ]
    if favorite:
        lines.append("favorite: true")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def main() -> None:
    con = sqlite3.connect(BAKE_DB)
    parents = dict(
        con.execute("select id, name from categories")
    )
    parent_of = dict(
        con.execute("select id, parent_id from categories where parent_id is not null")
    )

    def chain(cat_id: int) -> list[str]:
        names: list[str] = []
        while cat_id is not None:
            names.append(parents[cat_id])
            cat_id = parent_of.get(cat_id)
        return list(reversed(names))

    used_names: set[Path] = set()
    stats: dict[str, int] = {}
    unmapped: set[str] = set()

    rows = con.execute(
        "select id, category_id, title, content, html_content, favorite "
        "from documents order by id"
    ).fetchall()
    for doc_id, cat_id, title, content, html_content, favorite in rows:
        parts = chain(cat_id)
        chain_str = " / ".join(parts)
        if len(parts) >= 2 and parts[1] == "DSH Agent 项目分析":
            leaf = parts[-1]
            target = f"projects/dsh-agent/{DSH_LEAF_MAP.get(leaf, 'misc')}"
        elif chain_str in CATEGORY_MAP:
            target = CATEGORY_MAP[chain_str]
        else:
            target = f"_unfiled/{sanitize('/'.join(parts))}"
            unmapped.add(chain_str)

        base = sanitize(title)
        dest_dir = ROOT / target
        dest_dir.mkdir(parents=True, exist_ok=True)

        stem = base
        while (dest_dir / f"{stem}.md") in used_names or (
            dest_dir / f"{stem}.html"
        ).exists():
            stem = f"{base}-{doc_id}"
        used_names.add(dest_dir / f"{stem}.md")

        is_full_html = bool(content) and content.lstrip().lower().startswith(
            ("<!doctype", "<html")
        )
        if is_full_html:
            (dest_dir / f"{stem}.html").write_text(content, encoding="utf-8")
        elif content is not None:
            body = frontmatter(title, chain_str, bool(favorite)) + content
            (dest_dir / f"{stem}.md").write_text(body, encoding="utf-8")
        if html_content:
            (dest_dir / f"{stem}.html").write_text(html_content, encoding="utf-8")

        stats[target] = stats.get(target, 0) + 1

    print(f"migrated {len(rows)} documents")
    for target in sorted(stats):
        print(f"  {target}: {stats[target]}")
    if unmapped:
        print("unmapped chains -> _unfiled/:")
        for chain_str in sorted(unmapped):
            print(f"  {chain_str}")


if __name__ == "__main__":
    main()
