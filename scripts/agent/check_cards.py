# scripts/agent/check_cards.py
# 用法: python scripts/agent/check_cards.py content/baike/data-science/推荐系统.md [...]
# -- coding: utf-8 --
"""抽卡自检：输出语料文件可被解析出的卡片（kind/卡面/卡背摘），重写后验收用。"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from app.cards import parse_file  # noqa: E402

def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    for arg in sys.argv[1:]:
        p = pathlib.Path(arg).resolve()
        rel = p.relative_to(ROOT / "content").as_posix()
        cards = parse_file(rel, p.read_text(encoding="utf-8"))
        print(f"== {rel} -> {len(cards)} 张卡")
        for c in cards:
            print(f"   [{c.kind}] {c.front}")
            print(f"       back: {c.back.replace(chr(10), ' ')[:60]}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
