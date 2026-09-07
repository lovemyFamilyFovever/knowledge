# -*- coding: utf-8 -*-
"""标签与子域治理 CLI —— 默认 dry-run，--apply 才写盘。

用法：
    # 标签普查（全部标签按文档数排序）
    python scripts/govern_tags.py census

    # 疑似重叠标签对（大小写/包含/近拼写）
    python scripts/govern_tags.py similar

    # 把一个标签并入另一个（先预览，确认后加 --apply）
    python scripts/govern_tags.py merge --src "ai" --dst "AI 与大模型"
    python scripts/govern_tags.py merge --src "ai" --dst "AI 与大模型" --apply

    # 子域重命名/移动（整个目录 + 旁挂 + taxonomy.json 级联）
    python scripts/govern_tags.py rename-sub --domain baike --old cs-basics --new cs
    python scripts/govern_tags.py rename-sub --domain baike --old cs-basics --new cs --apply

合并/重命名后建议重启应用或在应用内任意保存一次（触发 FTS/向量增量同步）。
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import fts  # noqa: E402
from app.store import (tag_census, find_similar_tags, merge_tag,  # noqa: E402
                       rename_sub)


def cmd_census(_args):
    census = tag_census(ROOT / "content")
    print(f"全库标签 {len(census)} 个（按文档数降序）：\n")
    for t, n in census.items():
        print(f"  {n:>4}  {t}")


def cmd_similar(_args):
    census = tag_census(ROOT / "content")
    pairs = find_similar_tags(census)
    if not pairs:
        print("未发现疑似重叠标签。")
        return
    print(f"疑似重叠 {len(pairs)} 对（置信度降序，1.0=大小写差异）：\n")
    for a, b, conf in pairs:
        print(f"  [{conf:.1f}] {a!r}  <->  {b!r}   ({census.get(a, 0)} / {census.get(b, 0)} 篇)")
    print("\n合并示例：python scripts/govern_tags.py merge --src '小标签' --dst '大标签'")


def cmd_merge(args):
    r = merge_tag(ROOT / "content", args.src, args.dst, apply=args.apply)
    mode = "已写入" if args.apply else "dry-run 预览（加 --apply 执行）"
    print(f"标签合并 {r['src']!r} -> {r['dst']!r} · 影响 {r['n_docs']} 篇 · {mode}\n")
    for d in r["docs"][:30]:
        print(f"  {d['path']}")
        print(f"    旧: {d['old_tags']}")
        print(f"    新: {d['new_tags']}")
    if len(r["docs"]) > 30:
        print(f"  … 其余 {len(r['docs']) - 30} 篇略")
    if args.apply:
        n = fts.build_index(ROOT / "content", ROOT / "indexes")
        print(f"\nFTS 索引已重建（{n} 篇）。向量索引将在应用后台 30s 内自动对齐。")


def cmd_rename_sub(args):
    try:
        r = rename_sub(ROOT / "content", args.domain, args.old, args.new,
                       apply=args.apply)
    except (ValueError, FileNotFoundError) as e:
        print(f"错误：{e}")
        return 1
    mode = "已执行" if args.apply else "dry-run 预览（加 --apply 执行）"
    print(f"子域重命名 {args.domain}/{args.old} -> {args.domain}/{args.new} · "
          f"{r['n_docs']} 篇 · {mode}\n")
    for i in r["plan"][:30]:
        print(f"  {i['src']}  ->  {i['dst']}")
    if len(r["plan"]) > 30:
        print(f"  … 其余 {len(r['plan']) - 30} 篇略")
    if args.apply:
        n = fts.build_index(ROOT / "content", ROOT / "indexes")
        print(f"\nFTS 索引已重建（{n} 篇）。向量索引将在应用后台 30s 内自动对齐。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="知库标签/子域治理工具")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("census", help="标签普查")
    sub.add_parser("similar", help="疑似重叠标签对")
    m = sub.add_parser("merge", help="合并标签（默认 dry-run）")
    m.add_argument("--src", required=True, help="被并入的标签（大小写不敏感）")
    m.add_argument("--dst", required=True, help="目标标签")
    m.add_argument("--apply", action="store_true", help="真正写入（默认只预览）")
    m2 = sub.add_parser("rename-sub", help="子域重命名/移动（默认 dry-run）")
    m2.add_argument("--domain", required=True)
    m2.add_argument("--old", required=True)
    m2.add_argument("--new", required=True)
    m2.add_argument("--apply", action="store_true", help="真正执行（默认只预览）")
    args = ap.parse_args()
    return {"census": cmd_census, "similar": cmd_similar,
            "merge": cmd_merge, "rename-sub": cmd_rename_sub}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main() or 0)
