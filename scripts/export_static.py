# -*- coding: utf-8 -*-
"""导出静态只读站（合并方案 §4.1 · 本阶段只做本地可跑，不发布）。

设计依据：`docs/superpowers/specs/2026-10-07-merge-publish-design.md` §4.1。
产物 `site/` 是**派生缓存**（不变量 3 同款口径：`.gitignore` 已忽略，可删可重建，不进 git）。

核心硬约束（§4.1）：**导出的 JSON 必须与 Flask 读端点逐字段同构**，否则同一份前端
会精神分裂。本导出器因此**不照抄任何 payload 结构**，而是就地起一个应用实例、
经 `app.test_client()` 直接调用端点、把响应体原样落盘 —— 端点内部自己就复用了
`app/store.py` / `app/fts.py` / `app/palette.py` 的产 payload 函数，同构由构造保证。
契约断言见 `tests/test_export_static.py`（同一临时语料下导出 JSON == 端点响应）。

产物结构（§4.1 草案）：
    site/index.html            阅读器壳（同一模板 + 注入 KB_STATIC.readonly / KB_BASE）
    site/404.html              index 的副本（GH Pages 深链兜底）
    site/data/tree.json        ← /api/tree
    site/data/doc/…            ← /api/doc（逐篇）
    site/data/links.json       ← /api/links（逐篇聚合）
    site/data/dir-tree.json    ← /api/dir/tree（单列树 + 内联文档清单）
    site/data/meta.json        ← 分类学标签/HUES + /api/globalstats
    site/data/palette/index.json ← /api/palette/index
    site/data/search/<域>.json  客户端 CJK bigram 检索索引（分域懒加载）
    site/raw/…                 正文引用的图片（公开白名单内）
    site/static/…              复用现有静态资产（含 kb-static.js）+ vendored 字体

用法：
    python scripts/export_static.py [--root R] [--out site] [--base ""] [--no-git]
    python scripts/export_static.py --dry-run     # 只打印将产出的清单，不落盘
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.app import create_app  # noqa: E402
from app.routes_search import doc_url  # noqa: E402  （与 app.js docUrl 同源的唯一实现）
from app.store import LIBRARY_EXTS, load_taxonomy  # noqa: E402

# ---------------- 公开面契约（沿用 scripts/publish_site.py 的排除清单） ----------------
EXCLUDE_DIRS = {"漫画", "projects", "小说"}
PUBLISH_SUFFIXES = {".md", ".html"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".bmp", ".avif"}

# KB_BASE：静态站被托管在子路径（如 GH Pages 项目页 `/knowledge-site/`）时的前缀。
# **待拍板**（规格 §7-1：产物仓名与接线方式未定）—— 默认空串 = 根路径托管，
# 本阶段本地 `python -m http.server -d site` 预览用的就是空前缀。
KB_BASE_DEFAULT = ""

# ---------------- 读端点分诊表（规格 §4.4 · 唯一权威） ----------------
# 类别：
#   map      → 映射到 site/data/*.json
#   readonly → 写端点，适配器一律回 {ok:false,error:"READ_ONLY"}
#   noop     → 静默 no-op（阅读心跳等统计性副作用）
#   cut      → 只读档已裁剪（统计/目录统计/双链补全），产物不生成、适配器回不可用
#   retired  → 已下线端点（代码残留的字面量），一律不可用
# 判据（§4.4）：产物 JS 里出现的任何 `/api/` 字面量必须 ⊆ 本表；见 tests/test_export_static.py。
ENDPOINT_TRIAGE: dict[str, tuple[str, str]] = {
    # —— 映射：只读档必须能查到 ——
    "/api/tree": ("map", "data/tree.json"),
    "/api/doc": ("map", "data/doc/…"),
    "/api/links": ("map", "data/links.json"),
    "/api/palette/index": ("map", "data/palette/index.json"),
    "/api/search": ("map", "data/search/<域>.json（客户端 bigram 检索）"),
    "/api/globalstats": ("map", "data/meta.json 的 stats 段"),
    # —— no-op：副作用型，只读档静默吞掉 ——
    "/api/track": ("noop", "阅读心跳，只读档不上报"),
    "/api/recent_read": ("noop", "侧栏近 7 日阅读，只读档隐藏"),
    "/api/docmark": ("noop", "GET 恒回未标记；POST 归 readonly 处理"),
    # —— readonly：一切写回文件系统的入口 ——
    "/api/save": ("readonly", "写回正文"),
    "/api/note": ("readonly", "写备注"),
    "/api/favorite": ("readonly", "切收藏"),
    "/api/tags": ("readonly", "改标签"),
    "/api/move": ("readonly", "移动/重命名"),
    "/api/move/batch": ("readonly", "批量移动"),
    "/api/delete": ("readonly", "软删除"),
    "/api/mkdir": ("readonly", "新建目录"),
    "/api/rmdir": ("readonly", "删除目录"),
    "/api/rename-sub": ("readonly", "重命名子域"),
    "/api/rename-domain": ("readonly", "重命名域"),
    "/api/import": ("readonly", "导入文档"),
    "/api/inbox/ignore": ("readonly", "收件箱忽略"),
    "/api/inbox/purge": ("readonly", "收件箱物理删除"),
    "/api/wikilink/check": ("readonly", "编辑器断链检查（编辑器在只读档不存在）"),
    # —— cut：只读档不生成对应页面，端点一并裁掉 ——
    "/api/stats": ("cut", "文档统计（/stats 页不生成）"),
    "/api/substats": ("cut", "目录统计"),
    "/api/dir/tree": ("map", "data/dir-tree.json"),
    "/api/wikilink/suggest": ("cut", "双链补全（编辑器用）"),
    # —— retired：已下线端点（仅注释里残留字面量） ——
    "/api/ask": ("retired", "轮次 53/54 已下线的问吧链路"),
}

TRIAGE_READ_MAP = {p for p, (k, _) in ENDPOINT_TRIAGE.items() if k == "map"}
TRIAGE_WRITE = {p for p, (k, _) in ENDPOINT_TRIAGE.items() if k == "readonly"}

_QUOTE_SAFE = ""


def doc_key(domain: str, sub: str, name: str) -> str:
    """单篇文档的稳定标识（前端适配器同构用）：domain/sub/name。"""
    return f"{domain}/{sub}/{name}"


def doc_data_rel(domain: str, sub: str, name: str) -> str:
    """单篇文档静态数据文件的相对路径（data/doc/…）。

    用 sha1(key)[:16] 做文件名：**不把文档名写进路径**。原因：Windows MAX_PATH 260，
    中文文档名经百分号编码后膨胀 3 倍（实测 `interview/ai-agent/AI Agent 技术面试题库…`
    直接超长 FileNotFoundError）。前端经 `data/doc/index.json`（key → 路径）查表。

    目录段（domain/sub）保持原样、**不做百分号编码**：写 %-编码的目录名时，
    GH Pages / http.server 都会先把请求路径解码再找文件（%E6%… → 提示词），
    与 %-字面量目录名对不上 —— 2026-10-07 线上实测 404（148/1002 篇中文子目录文档受影响）。
    浏览器端请求时自动做百分号编码，磁盘端保持原文即可（sub 目录名本身是合法文件名）。
    """
    h = hashlib.sha1(doc_key(domain, sub, name).encode("utf-8")).hexdigest()[:16]
    return f"data/doc/{domain}/{sub}/{h}.json"


# ============================ 公开白名单 ============================
def git_tracked_public(root: Path) -> set[str] | None:
    """git 跟踪的公开白名单（content/ 下的相对 posix 路径）；非 git 根返回 None。

    只认 `content/` 前缀、且非排除目录（排除项在 .gitignore 已是硬边界，这里再断言一次）。
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "-c", "core.quotepath=false", "ls-files", "-z", "--", "content"],
            capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    rels = {r for r in out.stdout.decode("utf-8", "replace").split("\0") if r}
    keep = set()
    for rel in rels:
        parts = rel.split("/")
        if len(parts) < 2 or parts[0] != "content":
            continue
        sub = parts[1:]
        if any(p.startswith("_") for p in sub):
            continue
        if sub[0] in EXCLUDE_DIRS:
            continue
        if Path(rel).suffix.lower() not in PUBLISH_SUFFIXES | IMAGE_EXTS:
            continue
        keep.add("/".join(sub))
    return keep


def assert_gate(rel: str) -> None:
    """排除断言（与 publish_site.py 同契约）：排除目录 / `_` 前缀一律不许出现。"""
    parts = rel.split("/")
    if not parts or parts[0] in EXCLUDE_DIRS or any(p.startswith("_") for p in parts):
        raise RuntimeError(f"排除断言触发，禁止导出: {rel}")


def select_public_files(root: Path, tracked: set[str] | None) -> list[str]:
    """待发布的公开文件（content/ 相对 posix）：排除目录与 `_` 前缀一律剔除。

    tracked 非空时以 git 跟踪白名单为准（§4.1 基准集）；否则取磁盘上全部可见的
    md/html/图片。排除契约（EXCLUDE_DIRS / `_` 前缀）在两种模式下都生效。
    """
    content = root / "content"
    out: list[str] = []
    for p in content.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(content).as_posix()
        parts = rel.split("/")
        if any(seg.startswith("_") for seg in parts) or parts[0] in EXCLUDE_DIRS:
            continue
        if p.suffix.lower() not in PUBLISH_SUFFIXES | IMAGE_EXTS:
            continue
        if tracked is not None and rel not in tracked:
            continue
        out.append(rel)
    return sorted(out)


def stage_corpus(root: Path, rels: list[str], dest: Path) -> Path:
    """把公开文件 + content/_meta（分类学权威）复制进一个干净的 staging 语料根。

    为什么要 staging：真实 content/ 盘上还有 gitignore 的 `projects/` 等（不变量 10
    的硬边界），直接在原根上跑 create_app 会把它们读进 tree / stats——只靠事后过滤
    既易漏又难证。staging 让“公开面”从输入侧就是白名单，所有派生 payload 自然干净。
    用 copy2 保留 mtime（tree 签名与 doc mtime 与源一致，同构断言才有意义）。
    """
    src_content = root / "content"
    content = dest / "content"
    content.mkdir(parents=True, exist_ok=True)
    for rel in rels:
        assert_gate(rel)
        dst = content / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_content / rel, dst)
    meta = src_content / "_meta"
    if meta.is_dir():
        shutil.copytree(meta, content / "_meta", dirs_exist_ok=True)
    return dest


# ============================ 静态路径重写 ============================
_DOC_DATA_RE = re.compile(r'<script[^>]*id="doc-data"[^>]*>.*?</script>', re.S)
_ATTR_RE = re.compile(r'\b(href|src|action)=(["\'])/(static|raw|doc|browse)/')
_CSS_URL_RE = re.compile(r'url\(\s*(["\']?)/(static|raw)/')


def prefix_html(text: str, base: str) -> str:
    """把 HTML 里的绝对资源/站内路径加上 KB_BASE 前缀。

    **跳过 `<script id="doc-data">` 内嵌 JSON**：正文里可能恰好出现 `/static/…` 字样，
    那不是资源引用，重写它会污染数据。
    """
    if not base:
        return text
    holes: list[str] = []

    def _stash(m: re.Match) -> str:
        holes.append(m.group(0))
        return f"\x00KBHOLE{len(holes) - 1}\x00"

    text = _DOC_DATA_RE.sub(_stash, text)
    text = _ATTR_RE.sub(lambda m: f'{m.group(1)}={m.group(2)}{base}/{m.group(3)}/', text)
    for i, hole in enumerate(holes):
        text = text.replace(f"\x00KBHOLE{i}\x00", hole)
    return text


def prefix_css(text: str, base: str) -> str:
    """CSS `url("/static/…")` / `url("/raw/…")` → 加 KB_BASE 前缀。"""
    if not base:
        return text
    return _CSS_URL_RE.sub(lambda m: f"url({m.group(1)}{base}/{m.group(2)}/", text)


# ============================ 正文引用的图片 ============================
_MD_IMG_RE = re.compile(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)")
_HTML_IMG_RE = re.compile(r"<img\b[^>]*?\bsrc=[\"']([^\"']+)[\"']", re.I)
_SRCSET_RE = re.compile(r"\bsrcset=[\"']([^\"']+)[\"']", re.I)


def referenced_media(content: Path, doc_abs: Path, text: str) -> dict[str, Path]:
    """从一篇正文里抽出引用的图片 → {相对 content 的 posix 路径: 绝对路径}。

    只收真实存在、且落在 content/ 内的图片；外链（http/https/data:）一律跳过。
    """
    refs: list[str] = []
    refs += _MD_IMG_RE.findall(text)
    refs += _HTML_IMG_RE.findall(text)
    for ss in _SRCSET_RE.findall(text):
        for part in ss.split(","):
            url = part.strip().split(" ")[0]
            if url:
                refs.append(url)
    out: dict[str, Path] = {}
    content_res = content.resolve()
    for raw in refs:
        src = raw.strip().strip("<>")
        if not src or src.startswith(("http://", "https://", "data:", "//", "#")):
            continue
        src = src.split("#", 1)[0].split("?", 1)[0]
        cand = (doc_abs.parent / src) if not src.startswith("/") else (content / src.lstrip("/"))
        try:
            cand = cand.resolve()
        except OSError:
            continue
        if content_res not in cand.parents or not cand.is_file():
            continue
        if cand.suffix.lower() not in IMAGE_EXTS:
            continue
        out[cand.relative_to(content_res).as_posix()] = cand
    return out


# ============================ 静态检索索引（CJK bigram） ============================
_CJK_RUN = re.compile(r"[\u4e00-\u9fff]+")
_ASCII_WORD = re.compile(r"[A-Za-z0-9_]{2,}")


def _tokens(text: str) -> set[str]:
    toks: set[str] = set()
    for run in _CJK_RUN.findall(text or ""):
        if len(run) == 1:
            toks.add(run)
        else:
            for i in range(len(run) - 1):
                toks.add(run[i:i + 2])
    for w in _ASCII_WORD.findall(text or ""):
        toks.add(w.lower())
    return toks


def build_domain_search_index(domain: str, docs: list[dict]) -> dict:
    """单个域的懒加载检索索引：{token: [docIdx,...]}；分片粒度=域（规格 §4.1）。"""
    index: dict[str, list[int]] = {}
    entries: list[dict] = []
    for i, d in enumerate(docs):
        for tok in _tokens(d.pop("_body", "")):
            index.setdefault(tok, []).append(i)
    for d in docs:
        entries.append({k: v for k, v in d.items() if not k.startswith("_")})
    return {"v": 1, "domain": domain, "n": len(entries), "docs": entries, "index": index}


# ============================ 导出主体 ============================
def _write_json(path: Path, obj) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    path.write_text(data, encoding="utf-8")
    return len(data.encode("utf-8"))


def export_site(root: Path, out: Path, base: str = KB_BASE_DEFAULT,
                tracked_only: bool = True, include_search: bool = True,
                dry_run: bool = False, keep_corpus: bool = False) -> dict:
    """把 root/content 的公开白名单导出成静态只读站到 out/。返回统计摘要。

    实现要点：先把白名单语料 staged 到一个干净语料根，再在其上跑 `create_app`，
    因此 tree/doc/links/palette/globalstats 全都是“公开白名单语料”的端点响应——
    既满足 §4.1 的同构硬约束，又天然不含 gitignore 的 projects/ 等。
    keep_corpus=True 时保留 staging 语料根（供测试用同一语料对账）。
    """
    root = Path(root).resolve()
    out = Path(out).resolve()
    tracked = git_tracked_public(root) if tracked_only else None
    rels = select_public_files(root, tracked)

    stage = Path(tempfile.mkdtemp(prefix="kb-export-"))
    corpus = stage_corpus(root, rels, stage)
    content = corpus / "content"
    try:
        app = create_app(corpus)
        client = app.test_client()
        tree = client.get("/api/tree").get_json()
        domains = tree.get("domains", [])

        # ---------------- 逐篇 /api/doc + rel + 引用图片 ----------------
        doc_files: list[tuple[str, str, str, str]] = []   # (domain, sub, name, out_rel)
        rel2doc: dict[str, Path] = {}
        media: dict[str, Path] = {}
        from app.store import find_doc  # 复用：树给的 (domain,sub,name) → 磁盘路径
        for dom in domains:
            for sobj in dom["subs"]:
                for d in sobj["docs"]:
                    name = d["name"]
                    abs_p = find_doc(content, dom["id"], sobj["id"], name)
                    if not abs_p:
                        continue
                    rel = abs_p.relative_to(content).as_posix()
                    assert_gate(rel)
                    rel2doc[rel] = abs_p
                    doc_files.append((dom["id"], sobj["id"], name,
                                      doc_data_rel(dom["id"], sobj["id"], name)))
                    if abs_p.suffix in PUBLISH_SUFFIXES:
                        try:
                            media.update(referenced_media(content, abs_p, abs_p.read_text(
                                encoding="utf-8", errors="replace")))
                        except OSError:
                            pass

        summary = {
            "root": str(root), "out": str(out), "base": base,
            "corpus_root": str(corpus), "files": len(rels),
            "tracked": None if tracked is None else len(tracked),
            "docs": len(doc_files), "media": sorted(media), "bytes": {},
        }
        if dry_run:
            return summary

        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True, exist_ok=True)
        b: dict[str, int] = summary["bytes"]

        # ---------------- data/tree.json ----------------
        b["tree.json"] = _write_json(out / "data" / "tree.json", tree)

        # ---------------- data/doc/…（逐篇严格等于 /api/doc 响应） ----------------
        total = 0
        doc_index: dict[str, str] = {}
        for did, sid, name, out_rel in doc_files:
            r = client.get("/api/doc", query_string={"domain": did, "sub": sid, "name": name})
            total += _write_json(out / out_rel, r.get_json())
            doc_index[doc_key(did, sid, name)] = out_rel
        b["doc/*.json"] = total
        b["doc/index.json"] = _write_json(out / "data" / "doc" / "index.json", doc_index)

        # ---------------- data/links.json（逐篇 /api/links 聚合；仅 .md） ----------------
        links: dict[str, dict] = {}
        for rel in sorted(rel2doc):
            if not rel.endswith(".md"):
                continue
            r = client.get("/api/links", query_string={"path": rel})
            if r.status_code == 200:
                links[rel] = r.get_json()
        b["links.json"] = _write_json(out / "data" / "links.json", links)

        # ---------------- data/palette/index.json ----------------
        pal = client.get("/api/palette/index").get_json()
        b["palette/index.json"] = _write_json(out / "data" / "palette" / "index.json", pal)

        # ---------------- data/dir-tree.json（单列树：域/子域/内联文档清单）----------------
        dirtree = client.get("/api/dir/tree").get_json()
        b["dir-tree.json"] = _write_json(out / "data" / "dir-tree.json", dirtree)

        # ---------------- data/meta.json（分类学标签 + /api/globalstats） ----------------
        tax = load_taxonomy(content)
        stats = client.get("/api/globalstats").get_json()
        meta = {
            "labels": tax["domains"], "sub_labels": tax["subs"],
            "sources": tax["sources"], "status": tax["status"],
            "hues": tax["hues"], "search_hidden": sorted(tax.get("search_hidden", set())),
            "stats": stats,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "kb_base": base,
        }
        b["meta.json"] = _write_json(out / "data" / "meta.json", meta)

        # ---------------- data/search/<域>.json（分域懒加载） ----------------
        if include_search:
            total = 0
            for dom in domains:
                did = dom["id"]
                docs: list[dict] = []
                for sobj in dom["subs"]:
                    for d in sobj["docs"]:
                        abs_p = find_doc(content, did, sobj["id"], d["name"])
                        if not abs_p:
                            continue
                        rel = abs_p.relative_to(content).as_posix()
                        body = ""
                        if abs_p.suffix == ".md":
                            from app.store import parse_frontmatter
                            try:
                                _, body = parse_frontmatter(abs_p.read_text(
                                    encoding="utf-8", errors="replace"))
                            except OSError:
                                body = ""
                        docs.append({
                            "rel": rel, "title": d.get("title") or d["name"],
                            "url": doc_url(rel), "tags": list(d.get("tags") or []),
                            "excerpt": " ".join(body.split())[:140],
                            "_body": body,
                        })
                idx = build_domain_search_index(did, docs)
                total += _write_json(
                    out / "data" / "search" / f"{did}.json", idx)
            b["search/*.json"] = total

        # ---------------- 阅读器壳 index.html / 404.html ----------------
        first = None
        for dom in domains:
            for sobj in dom["subs"]:
                for d in sobj["docs"]:
                    if find_doc(content, dom["id"], sobj["id"], d["name"]):
                        first = (dom["id"], sobj["id"], d["name"])
                        break
                if first:
                    break
            if first:
                break
        if first:
            shell = client.get(
                f"/doc/{quote(first[0])}/{quote(first[1])}/{quote(first[2])}").get_data(as_text=True)
        else:
            shell = client.get("/").get_data(as_text=True)
        inject = (
            '<script>window.KB_STATIC=%s;</script>\n'
            '<script src="%s/static/kb-static.js" defer></script>\n'
            % (json.dumps({"readonly": True, "base": base}, separators=(",", ":")), base)
        )
        # 注入点：紧接 <head>（在任何 defer 脚本之前，保证 kb-static 先于 app.js 执行）
        shell = shell.replace("<head>", "<head>\n" + inject, 1)
        shell = prefix_html(shell, base)
        (out / "index.html").write_text(shell, encoding="utf-8")
        (out / "404.html").write_text(shell, encoding="utf-8")   # 深链兜底（§4.1 / §5-1）

        # ---------------- site/raw/…（正文引用的图片） ----------------
        total = 0
        raw_skipped: list[str] = []
        for rel, src in sorted(media.items()):
            dst = out / "raw" / rel
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                total += dst.stat().st_size
            except OSError:
                raw_skipped.append(rel)   # 超长路径等：记账不外抛
        b["raw/*"] = total
        summary["raw_skipped"] = raw_skipped

        # ---------------- site/static/…（复用现有静态资产；CSS 加前缀） ----------------
        src_static = root / "static"
        dst_static = out / "static"
        if src_static.is_dir():
            shutil.copytree(src_static, dst_static, dirs_exist_ok=True)
            if base:
                for css in dst_static.rglob("*.css"):
                    css.write_text(prefix_css(css.read_text(encoding="utf-8"), base),
                                   encoding="utf-8")

        summary["bytes_total"] = sum(b.values())
        return summary
    finally:
        if not keep_corpus:
            shutil.rmtree(stage, ignore_errors=True)


# ============================ CLI ============================
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="导出静态只读站（合并方案 §4.1）")
    ap.add_argument("--root", type=Path, default=ROOT, help="仓库根（默认本脚本所在仓）")
    ap.add_argument("--out", type=Path, default=ROOT / "site", help="产物目录（默认 <root>/site）")
    ap.add_argument("--base", default=KB_BASE_DEFAULT,
                    help="KB_BASE 前缀（托管子路径用；默认空 = 待拍板 §7-1）")
    ap.add_argument("--no-git", action="store_true",
                    help="不按 git 跟踪白名单过滤（临时语料/无 git 根用）")
    ap.add_argument("--no-search", action="store_true", help="跳过检索索引生成")
    ap.add_argument("--dry-run", action="store_true", help="只打印清单，不落盘")
    args = ap.parse_args(argv)

    summary = export_site(args.root, args.out, base=args.base,
                          tracked_only=not args.no_git,
                          include_search=not args.no_search,
                          dry_run=args.dry_run)
    if args.dry_run:
        print(f"[dry-run] 语料 {summary['docs']} 篇｜图片 {len(summary['media'])} 张｜"
              f"公开文件 {summary['files']}｜跟踪白名单 {summary['tracked']}")
        return 0
    top = ", ".join(f"{k}={v}" for k, v in summary["bytes"].items())
    print(f"导出完成 → {summary['out']}")
    print(f"  文档 {summary['docs']} 篇｜图片 {len(summary['media'])} 张｜KB_BASE={summary['base']!r}")
    print(f"  产物体积：{summary['bytes_total'] / 1024:.0f} KB（{top}）")
    print("  本地预览：python -m http.server -d site")
    return 0


if __name__ == "__main__":
    sys.exit(main())
