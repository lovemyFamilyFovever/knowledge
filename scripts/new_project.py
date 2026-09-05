# -*- coding: utf-8 -*-
"""项目骨架脚手架：在 content/projects/ 下建一个项目的标准格子。

用法：
  python scripts/new_project.py 项目名 [--company 公司] [--period 2018-2020]
                                       [--role 前端负责人] [--desc 一句话描述]
  python scripts/new_project.py --list

骨架结构（数据由用户自行填入/迁入，本脚本绝不导入内容）：
  content/projects/<项目名>/
    README.md            项目卡（frontmatter: company/period/role/status）
    docs/说明.md         文档区约定
    retrospective/复盘.md 复盘模板
    pitfalls/踩坑.md      踩坑模板
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "content" / "projects"
TODAY_HINT = "迁入或填写后把 status 改为 stable"


def sanitize(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', " ", name).strip()
    if not cleaned:
        sys.exit("项目名不能为空")
    return cleaned


def project_card(name: str, company: str, period: str, role: str, desc: str) -> str:
    return f"""---
title: "{name} · 项目卡"
tags: [项目]
type: project-card
company: "{company}"
period: "{period}"
role: "{role}"
status: "整理中"
---

# {name}

> {desc or "（一句话定位，待填）"}

## 基本信息

| 维度 | 内容 |
|---|---|
| 公司 / 归属 | {company or "（待填）"} |
| 周期 | {period or "（待填）"} |
| 我的角色 | {role or "（待填）"} |
| 技术栈 | （待填） |
| 关联仓库 / 链接 | （待填） |

## 文档导航

- [docs/](docs/说明.md) — 项目文档（按子系统保持原结构迁入）
- [retrospective/](retrospective/复盘.md) — 项目复盘
- [pitfalls/](pitfalls/踩坑.md) — 本项目踩坑

## 状态

整理中。{TODAY_HINT}。
"""


def docs_readme(name: str) -> str:
    return f"""---
title: "{name} · 文档区说明"
tags: [项目]
---

# docs/ 项目文档区

本目录存放 {name} 的项目文档。约定：

1. 迁入时**保持原有子目录结构**（子系统/模块各自成目录），不要打散；
2. 每篇 frontmatter 保留 `source` / `source_path`（来源与原始路径），可追溯；
3. 重复、过时的版本在迁入前清理，正式版才进正式库；
4. 手动放入即可，阅读器与索引会在下次启动时自动发现。
"""


def retro_tpl(name: str) -> str:
    return f"""---
title: "{name} · 复盘"
tags: [项目, 复盘]
---

# {name} 复盘

## 做得好的

- 

## 做得不好的

- 

## 下次怎么做

- 
"""


def pitfall_tpl(name: str) -> str:
    return f"""---
title: "{name} · 踩坑记录"
tags: [项目, 踩坑]
---

# {name} 踩坑记录

| 日期 | 问题 | 原因 | 解法 |
|---|---|---|---|
|  |  |  |  |
"""


def scaffold(name: str, company: str = "", period: str = "", role: str = "", desc: str = "",
             root: Path = ROOT) -> Path:
    """建项目骨架；目标已存在时抛 FileExistsError（绝不覆盖）。"""
    projects = root / "content" / "projects"
    target = projects / name
    if target.exists():
        raise FileExistsError(f"项目已存在：{target}")
    (target / "docs").mkdir(parents=True)
    (target / "retrospective").mkdir()
    (target / "pitfalls").mkdir()
    (target / "README.md").write_text(project_card(name, company, period, role, desc), encoding="utf-8")
    (target / "docs" / "说明.md").write_text(docs_readme(name), encoding="utf-8")
    (target / "retrospective" / "复盘.md").write_text(retro_tpl(name), encoding="utf-8")
    (target / "pitfalls" / "踩坑.md").write_text(pitfall_tpl(name), encoding="utf-8")
    return target


def list_projects() -> None:
    if not PROJECTS.is_dir():
        print("（尚无项目）")
        return
    entries = sorted(p for p in PROJECTS.iterdir() if p.is_dir() and not p.name.startswith("_"))
    if not entries:
        print("（尚无项目）")
        return
    for p in entries:
        card = p / "README.md"
        company = period = ""
        if card.is_file():
            for line in card.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith("company:"):
                    company = line.split(":", 1)[1].strip().strip('"')
                elif line.startswith("period:"):
                    period = line.split(":", 1)[1].strip().strip('"')
        print(f"{p.name}  [{company or '—'} {period or '—'}]")


def main() -> None:
    ap = argparse.ArgumentParser(description="项目骨架脚手架")
    ap.add_argument("name", nargs="?", help="项目名")
    ap.add_argument("--company", default="")
    ap.add_argument("--period", default="")
    ap.add_argument("--role", default="")
    ap.add_argument("--desc", default="")
    ap.add_argument("--list", action="store_true", help="列出现有项目")
    args = ap.parse_args()

    if args.list:
        list_projects()
        return
    if not args.name:
        ap.error("请提供项目名，或使用 --list")
    name = sanitize(args.name)
    target = scaffold(name, args.company, args.period, args.role, args.desc)
    print(f"项目骨架已创建：{target}")
    print(f"阅读路径：http://127.0.0.1:5001/doc/projects/{name}/README")


if __name__ == "__main__":
    main()
