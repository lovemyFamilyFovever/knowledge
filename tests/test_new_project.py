# -*- coding: utf-8 -*-
"""项目骨架脚手架 smoke tests。运行：python tests/test_new_project.py"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.new_project import scaffold, sanitize  # noqa: E402

passed = failed = 0


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS {name}")
    else:
        failed += 1
        print(f"  FAIL {name} {extra}")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        t = scaffold("AI金", company="某公司", period="2024-2026", role="前端负责人", root=root)
        check("骨架目录建立", (t / "docs").is_dir() and (t / "retrospective").is_dir() and (t / "pitfalls").is_dir())
        card = (t / "README.md").read_text(encoding="utf-8")
        check("项目卡含 frontmatter 字段", 'company: "某公司"' in card and 'period: "2024-2026"' in card)
        check("项目卡含导航", "docs/说明.md" in card and "复盘.md" in card)
        check("文档区说明落位", "保持原有子目录结构" in (t / "docs" / "说明.md").read_text(encoding="utf-8"))
        check("复盘模板落位", "做得好的" in (t / "retrospective" / "复盘.md").read_text(encoding="utf-8"))
        check("踩坑模板落位", (t / "pitfalls" / "踩坑.md").is_file())

        try:
            scaffold("AI金", root=root)
            check("重复创建被拒绝", False)
        except FileExistsError:
            check("重复创建被拒绝", True)

        check("非法字符被清洗", sanitize('a/b:c*"?<>|') == "a b c")
        try:
            sanitize("  ")
            check("空名报错", False)
        except SystemExit:
            check("空名报错", True)

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
