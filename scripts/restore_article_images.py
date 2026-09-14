# -*- coding: utf-8 -*-
"""需求#6：articles 域（原 myblog）的图片回源。

扫描 content/articles/**/*.md 里的相对图片引用（![](...) / <img src>），
按 frontmatter source_path 定位 E:/GitHub/myblog/docs 下的原文件，
把引用到的图片拷回 content/articles 同相对路径，让 /raw 直服可命中。

可重复执行（幂等，已存在跳过）；跑完打印仍缺失清单。
"""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
ARTICLES = CONTENT / "articles"
BLOG = Path(r"E:/GitHub/myblog/docs")

IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)|<img[^>]+src=\"([^\"]+)\"", re.I)


def frontmatter_source(text: str) -> str:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return ""
    fm = m.group(1)
    sm = re.search(r'^source_path:\s*"?([^"\n]+)"?', fm, re.M)
    return sm.group(1).strip() if sm else ""


def find_source_md(md: Path, text: str) -> Path | None:
    sp = frontmatter_source(text)
    cands = []
    if sp:
        cands.append(BLOG / sp)
    rel = md.relative_to(ARTICLES)
    cands.append(BLOG / "frontend" / rel)  # articles 根 = myblog/docs/frontend
    for c in cands:
        if c.is_file():
            return c
    return None


def resolve_ref(ref: str, base_dir: Path) -> Path | None:
    ref = ref.strip().split()[0]
    if ref.startswith(("http://", "https://", "data:", "blob:", "/")):
        return None
    p = (base_dir / ref).resolve()
    try:
        p.relative_to(BLOG)
    except ValueError:
        return None
    return p


def main() -> int:
    copied, missing = 0, []
    for md in sorted(ARTICLES.rglob("*.md")):
        if md.name.endswith(".notes.md"):
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        src_md = find_source_md(md, text)
        if not src_md:
            continue
        src_dir = src_md.parent
        for m in IMG_RE.finditer(text):
            ref = (m.group(1) or m.group(2) or "").strip()
            sp = resolve_ref(ref, src_dir)
            if not sp or not sp.is_file():
                if ref and not ref.startswith(("http", "data:", "blob:", "/")):
                    missing.append(f"{md.relative_to(CONTENT)} -> {ref}")
                continue
            # 目标位置：content md 同目录下的同相对引用路径
            dst_base = md.parent
            rel_ref = Path(ref.strip().split()[0])
            dst = (dst_base / rel_ref).resolve() if not ref.startswith("/") else None
            if dst is None:
                continue
            try:
                dst.relative_to(CONTENT)
            except ValueError:
                continue
            if dst.is_file() and dst.stat().st_size == sp.stat().st_size:
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sp, dst)
            copied += 1
    print(f"copied {copied} images")
    if missing:
        print(f"still missing {len(missing)}:")
        for x in missing[:40]:
            print("  ", x)
    else:
        print("no missing relative images remain")
    return 0


if __name__ == "__main__":
    sys.exit(main())
