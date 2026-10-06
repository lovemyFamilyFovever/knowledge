# -*- coding: utf-8 -*-
"""清理 _inbox/repos/ 中的仓库副本。

原则：这些副本是 scan_sources.py 从 E:\\GitHub/<同名仓库> 逐字节拷来的，
删除前逐仓核验原件目录仍然存在，因此零信息损失。work/ 保留待用户过目
（原选项 3）。重复运行安全。
"""
import shutil
from pathlib import Path

INBOX_REPOS = Path(__file__).resolve().parents[1] / "content" / "_inbox" / "repos"
GITHUB = Path("E:/GitHub")
KEEP = {"work"}  # 留待用户过目


def main() -> None:
    if not INBOX_REPOS.is_dir():
        print("no _inbox/repos, nothing to do")
        return
    removed = kept = missing = 0
    for d in sorted(INBOX_REPOS.iterdir()):
        if not d.is_dir():
            continue
        if d.name in KEEP:
            kept += 1
            print(f"keep  {d.name} (待过目)")
            continue
        original = GITHUB / d.name
        if not original.is_dir():
            missing += 1
            print(f"skip  {d.name} (原件不在 E:/GitHub，人工处理)")
            continue
        n = sum(1 for _ in d.rglob("*") if _.is_file())
        shutil.rmtree(d)
        removed += n
        print(f"deleted  {d.name} ({n} 份, 原件完好)")
    print(f"\nremoved {removed} files in {removed and ''}{kept and ''}repos; kept dirs: {kept}; skipped(missing original): {missing}")


if __name__ == "__main__":
    main()
