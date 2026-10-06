#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""frontmatter 结构门禁：待发布语料的 YAML 头必须能被严格解析器吃下。

背景（2026-09-25 发布事故）：content/career/journal/写作技巧.md 写成
`title:"写作"`（冒号后缺空格），本地阅读器的解析器是容错的手写版（app/store.py
FM_RE + 自研取值），照样显示；而公开站的 Quartz 用 js-yaml 严格解析，整条
`npx quartz build` 直接 failure，Pages 没更新——缺陷一路漂到 GitHub Actions 才爆。
本门禁把同一类错误提前到「同步前」和「提交前」。

判定口径（只查顶层行，缩进行交给解析器）：
  · 冒号后必须跟空格，否则整行会被当普通标量 → 下一行就成了"多行键"
  · 引号必须成对；值里出现裸的「冒号+空格」须整体加引号（否则 mapping values 报错）
  · 顶层行必须是 key: value；键名合法且不重复
  · 缩进里不许 Tab；`#` 开头是注释；`|`/`>` 块标量内部的行不管
零依赖、纯文本解析（全量 1500+ 篇约 0.5s），所以能同时挂进 pre-commit 与发布管线。

用法：
    python scripts/check_frontmatter.py            # 只查会进公开站的那批
    python scripts/check_frontmatter.py --all      # 连排除域（小说/漫画/projects）一起查
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "content"
# 与 scripts/publish_site.py 的发布契约保持一致
EXCLUDE_DIRS = {"漫画", "projects", "小说"}
PUBLISH_SUFFIXES = {".md", ".html"}

# 容忍 BOM 与 CRLF（Windows autocrlf 检出的语料在盘上是 CRLF）
FM_RE = re.compile(r"\A\ufeff?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(\r?\n|\Z)", re.S)
KEY_RE = re.compile(r"^[A-Za-z_][\w.-]*$")


def scan_frontmatter(fm: str) -> list[tuple[int, str]]:
    """检查 --- 之间的文本，返回 [(行号, 说明)]；空列表 = 通过。"""
    probs: list[tuple[int, str]] = []
    seen: dict[str, list[int]] = {}
    in_block = False  # 上一个顶层键是否是 | / > 块标量（其缩进内容自由书写）
    for i, raw in enumerate(fm.split("\n"), 1):
        line = raw.rstrip()
        if not line.strip():
            continue
        stripped = line.lstrip(" ")
        if stripped.startswith("#"):
            continue  # YAML 注释
        indent = len(line) - len(stripped)
        if in_block:
            if indent:
                continue
            in_block = False
        if indent:
            if "\t" in line[: len(line) - len(stripped)]:
                probs.append((i, "缩进里出现 Tab（YAML 只许空格）"))
            continue
        quote = ""
        colon = -1
        for j, ch in enumerate(line):
            if quote:
                if ch == quote:
                    quote = ""
                continue
            if ch in "\"'":
                quote = ch
                continue
            if ch == ":" and colon < 0:
                colon = j
                # 不 break：整行扫完才能判断引号是否闭合
        if quote:
            probs.append((i, "引号未闭合"))
            continue
        if colon < 0:
            probs.append((i, "顶层行不是 key: value 结构"))
            continue
        key = line[:colon].strip()
        rest = line[colon + 1 :]
        if not KEY_RE.match(key):
            probs.append((i, f"键名不合规范: {key!r}"))
        if rest and not rest[:1].isspace():
            probs.append((i, '冒号后缺空格（YAML 会把整行当标量，下一行变成"多行键"）'))
            continue
        val = rest.strip()
        if val[:1] in {"|", ">"}:
            in_block = True
        if val and val[0] not in "\"'[" and ": " in val:
            probs.append((i, "值里有未加引号的「冒号+空格」，须给值整体加引号"))
        seen.setdefault(key, []).append(i)
    for key, rows in seen.items():
        if len(rows) > 1:
            probs.append((rows[0], f"键 {key!r} 重复出现于第 {rows} 行"))
    return sorted(probs)


def lint_file(path: Path) -> list[tuple[int, str]]:
    try:
        text = io.open(str(path), encoding="utf-8", errors="replace").read()
    except OSError as exc:  # 读不到就别猜内容
        return [(0, f"读取失败: {exc}")]
    if not text.lstrip("\ufeff").startswith("---"):
        return []  # 无 frontmatter：Quartz 按普通正文处理，不报错
    m = FM_RE.match(text)
    if not m:
        return [(1, "frontmatter 有起始 --- 却没有闭合 ---")]
    return scan_frontmatter(m.group(1))


def iter_targets(publishable_only: bool = True) -> list[Path]:
    out: list[Path] = []
    for p in sorted(SRC.rglob("*.md")):
        if not p.is_file():
            continue
        rel = p.relative_to(SRC)
        if any(part.startswith("_") for part in rel.parts):
            continue
        if publishable_only and rel.parts and rel.parts[0] in EXCLUDE_DIRS:
            continue
        out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true", help="连发布排除域一起查")
    args = ap.parse_args()

    files = iter_targets(publishable_only=not args.all)
    bad = [(p, probs) for p in files for probs in [lint_file(p)] if probs]
    scope = "全部语料" if args.all else "待发布语料"
    if bad:
        print(f"frontmatter 门禁：{len(bad)} 篇有问题（{scope}，共扫 {len(files)} 篇）", file=sys.stderr)
        for p, probs in bad[:40]:
            for ln, msg in probs:
                print(f"  {p.relative_to(ROOT)}:{ln}  {msg}", file=sys.stderr)
        if len(bad) > 40:
            print(f"  ...另有 {len(bad) - 40} 篇", file=sys.stderr)
        print("公开站 Quartz 用严格 YAML 解析，这些会让整站构建失败——先修头再提交。", file=sys.stderr)
        return 1
    print(f"frontmatter 门禁：{len(files)} 篇（{scope}）全部可被严格 YAML 解析。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
