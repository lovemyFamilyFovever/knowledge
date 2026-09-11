# -*- coding: utf-8 -*-
"""知库语料层 —— frontmatter、分类树扫描、备注、Obsidian 连接、分类学装载。

content/ 的 Markdown/HTML 是唯一事实源；本模块负责读语料 + 写回元数据 +
语料变更原语（移动/重命名/标签治理），不含路由与索引逻辑
（FTS 见 fts.py，向量见 rag.py，路由见 app.py）。

分类学（taxonomy）权威：content/_meta/taxonomy.json（_ 前缀目录不进索引）。
装载策略：JSON 覆盖内置缺省；JSON 缺失/损坏时全部走内置缺省，阅读器不炸。
"""
import json
import os
import re
import shutil
import time
from pathlib import Path

# ---------------- 常量与缺省分类学（被 _meta/taxonomy.json 覆盖） ----------------
FM_RE = re.compile(r"\A---\n(.*?)\n---\n\n?", re.S)
SKIP_DIRS = {"_inbox", "_assets", "_unfiled"}
WRITABLE_EXTS = {".md"}
SERVABLE_EXTS = {".md", ".html"}
DOMAIN_LABELS = {
    "baike": "百科", "articles": "文章", "interview": "面试", "projects": "项目",
    "handbook": "手册", "career": "职业", "ai-assets": "AI 资产",
}
GRAPH_HUES = {"baike": 158, "articles": 200, "interview": 340, "projects": 22,
              "handbook": 96, "career": 42, "ai-assets": 262}
SUB_LABELS = {
    # 百科
    "programming-languages": "编程语言", "database": "数据库", "security": "安全与加密",
    "network": "网络与协议", "os": "操作系统", "algorithms": "算法与数据结构",
    "distributed": "分布式系统", "hardware": "计算机硬件", "blockchain": "区块链",
    "iot": "物联网", "cs-basics": "计算机科学基础", "software-engineering": "软件工程",
    "architecture": "架构设计", "design-patterns": "设计模式", "devops": "DevOps 与云原生",
    "testing": "测试与质量", "tools": "工具链", "developer-skills": "开发者技能",
    "ai-and-llm": "AI 与大模型", "machine-learning": "机器学习", "data-science": "数据科学与大数据",
    "frontend-concepts": "前端概念", "frontend-frameworks": "前端框架", "mobile": "移动开发",
    "middleware": "消息与中间件", "web-backend": "Web 后端",
    # 文章
    "javascript": "JavaScript", "vue2": "Vue2", "vue3": "Vue3", "css": "CSS", "html": "HTML",
    "typescript": "TypeScript", "debugging": "调试", "pinia": "Pinia", "optimization": "性能优化",
    "tutorials": "教程", "single-file": "单文件版", "git": "Git",
    # 手册
    "pitfalls": "踩坑", "fragments": "碎片", "skills": "技能", "prompts": "Prompt 库",
    # 项目
    "dsh-agent": "DeepSeek Harness 研究", "retrospectives": "项目复盘",
    "妙搭平台": "妙搭平台", "不锈钢市场": "不锈钢市场",
    # 职业
    "insights": "洞见", "journal": "随笔", "resume": "简历", "management": "管理",
    # 面试（域内 scoped，键为 域/子域）
    "interview/ai-agent": "AI Agent 面试", "interview/business": "业务面",
    "interview/css-html": "CSS 与 HTML 面", "interview/engineering": "工程面",
    "interview/node-fullstack": "Node 与全栈面", "interview/performance": "性能面",
    "interview/javascript": "JavaScript 面试", "interview/frameworks": "框架面",
    "interview/ai": "AI 面试", "interview/behavioral": "行为面", "interview/career": "职业面",
    "interview/industry": "行业面", "interview/management": "管理面",
    "interview/architecture": "架构面", "interview/algorithms": "算法面试",
    # AI 资产
    "ai-assets/_root": "总览",
    "_root": "总览",
}
SOURCE_LABELS = {
    "baike": "百科大全", "myblog": "博客", "desktop": "桌面",
    "knowledge": "知识库自产", "dsh-memory": "Agent 记忆",
}
STATUS_LABELS = {"imported": "已导入", "reviewed": "已复查", "stable": "已整理"}
OBSIDIAN_EXE_CANDIDATES = [
    Path("D:/Obsidian/Obsidian.exe"),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Obsidian" / "Obsidian.exe",
    Path("C:/Program Files/Obsidian/Obsidian.exe"),
]
OBSIDIAN_CONFIG = Path(os.environ.get("APPDATA", "")) / "obsidian" / "obsidian.json"


# ---------------- 分类学装载（JSON 权威 + 内置缺省回退） ----------------
_TAX_CACHE: dict = {}


def load_taxonomy(content: Path) -> dict:
    """返回 {domains, hues, subs, sources, status} 五张字典。
    _meta/taxonomy.json 按 mtime 缓存；缺失/损坏回退内置缺省。"""
    path = content / "_meta" / "taxonomy.json"
    key = str(path)
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0.0
    hit = _TAX_CACHE.get(key)
    if hit and hit[0] == mtime:
        return hit[1]
    data: dict = {}
    if mtime:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
    doms = data.get("domains") or {}
    tax = {
        "domains": {**DOMAIN_LABELS, **{k: (str(v.get("label", k)) if isinstance(v, dict) else str(v))
                                        for k, v in doms.items()}},
        "hues": {**GRAPH_HUES, **{k: (int(v.get("hue", 158)) if isinstance(v, dict) else 158)
                                  for k, v in doms.items()}},
        "subs": {**SUB_LABELS, **{k: str(v) for k, v in (data.get("subs") or {}).items()}},
        "sources": {**SOURCE_LABELS, **{k: str(v) for k, v in (data.get("sources") or {}).items()}},
        "status": {**STATUS_LABELS, **{k: str(v) for k, v in (data.get("status") or {}).items()}},
    }
    _TAX_CACHE[key] = (mtime, tax)
    return tax


def domain_label(tax: dict, dom_id: str) -> str:
    return tax["domains"].get(dom_id, dom_id)


def sub_label(tax: dict, dom_id: str, sub_id: str) -> str:
    return tax["subs"].get(f"{dom_id}/{sub_id}", tax["subs"].get(sub_id, sub_id))


# ---------------- Obsidian ----------------
def obsidian_vault_connected(content: Path) -> bool:
    """双条件：程序本体存在，且 Obsidian 配置里注册了指向本语料的 vault。"""
    if not any(p.is_file() for p in OBSIDIAN_EXE_CANDIDATES):
        return False
    try:
        data = json.loads(OBSIDIAN_CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    me = str(content.resolve()).lower().rstrip("\\/")
    for v in data.get("vaults", {}).values():
        p = str(v.get("path", "")).lower().rstrip("\\/")
        if p == me:
            return True
    return False


# ---------------- frontmatter ----------------
def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse the leading `---` block into a dict; unknown keys are preserved."""
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm: dict = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            fm[key] = [x.strip().strip("\"'") for x in inner.split(",") if x.strip()] if inner else []
        elif val.lower() in ("true", "false"):
            fm[key] = val.lower() == "true"
        else:
            fm[key] = val.strip("\"'")
    return fm, text[m.end():]


def dump_frontmatter(fm: dict, body: str) -> str:
    lines = ["---"]
    for key, val in fm.items():
        if val is True:
            lines.append(f"{key}: true")
        elif isinstance(val, list):
            lines.append(f"{key}: [{', '.join(val)}]")
        else:
            lines.append(f'{key}: "{val}"')
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body


# ---------------- 语料扫描 ----------------
def md_files(content: Path):
    """全库 md 文件迭代器（(abs_path, rel_posix)）；跳过 _ 前缀与 SKIP_DIRS。"""
    for dirpath, dirnames, filenames in os.walk(content):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith("_")]
        for fn in filenames:
            if fn.endswith(".md"):
                p = Path(dirpath) / fn
                yield p, p.relative_to(content).as_posix()


def _tree_sig(content: Path) -> str:
    """仅 stat 不读内容的树签名：毫秒级，作为扫描/索引缓存的失效依据。
    含文件清单（含删除），比单纯 max(mtime) 更可靠：删除也能立即感知。"""
    parts = []
    for dirpath, dirnames, filenames in os.walk(content):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith("_")]
        for fn in filenames:
            if fn.endswith((".md", ".html")):
                p = Path(dirpath) / fn
                parts.append(f"{p.relative_to(content).as_posix()}:{p.stat().st_mtime_ns}")
    return "|".join(parts)


_INBOX_CACHE = {"t": 0.0, "n": 0}


def inbox_count(content: Path) -> int:
    d = content / "_inbox"
    if not d.is_dir():
        return 0
    now = time.time()
    if now - _INBOX_CACHE["t"] > 60:
        _INBOX_CACHE["n"] = sum(1 for _ in d.rglob("*"))
        _INBOX_CACHE["t"] = now
    return _INBOX_CACHE["n"]


def scan_corpus(content: Path) -> list[dict]:
    """扫描分类树：域 → 子域 → 文档元数据（含 frontmatter 提取）。带树签名缓存。"""
    tax = load_taxonomy(content)
    sig = _tree_sig(content)
    hit = _TAX_CACHE.get(f"scan:{content}")
    if hit and hit[0] == sig:
        return hit[1]
    domains = []
    for ddir in sorted(content.iterdir()):
        if not ddir.is_dir() or ddir.name in SKIP_DIRS or ddir.name.startswith("_"):
            continue
        dom = {"id": ddir.name, "label": domain_label(tax, ddir.name), "subs": [], "n": 0}
        loose = sorted(p for p in ddir.iterdir() if p.is_file() and p.suffix in SERVABLE_EXTS)
        sdirs = sorted(p for p in ddir.iterdir() if p.is_dir() and p.name not in SKIP_DIRS)
        for sdir in sdirs:
            label = sub_label(tax, ddir.name, sdir.name)
            dom["subs"].append(_scan_sub(sdir, sdir.name, label))
        if loose:
            dom["subs"].append(_scan_sub(ddir, "_root", "总览", loose))
        dom["n"] = sum(s["n"] for s in dom["subs"])
        if dom["subs"]:
            domains.append(dom)
    _TAX_CACHE[f"scan:{content}"] = (sig, domains)
    return domains


def _scan_sub(sdir: Path, sid: str, label: str, files=None) -> dict:
    """递归收集：嵌套目录（如 dsh-agent/architecture、vue2/Details）的文档
    以子路径作为文档名（<path:name> 路由支持带斜杠的 name）。"""
    files = files if files is not None else sorted(
        p for p in sdir.rglob("*") if p.is_file() and p.suffix in SERVABLE_EXTS
    )
    md_rel = {p.relative_to(sdir).with_suffix("").as_posix() for p in files if p.suffix == ".md"}
    docs = []
    for p in files:
        relp = p.relative_to(sdir).as_posix()
        fm: dict = {}
        if p.suffix == ".html":
            if relp[:-5] in md_rel:
                continue  # 同名 .md 的美化版旁挂
            name, title, is_html = relp, p.stem + ".html", True
        else:
            name, title, is_html = relp[:-3], p.stem, False
            fm, _ = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
            title = str(fm.get("title") or title)
        docs.append({
            "name": name,
            "file": relp,
            "title": title,
            "tags": fm.get("tags", []) if isinstance(fm.get("tags"), list) else [],
            "favorite": fm.get("favorite") is True,
            "is_html": is_html,
            "has_html": (sdir / (name + ".html")).is_file() if not is_html else False,
            "mtime": p.stat().st_mtime,
        })
    return {"id": sid, "label": label, "n": len(docs), "docs": docs}


def find_doc(content: Path, domain: str, sub: str, name: str):
    """Locate a document; returns (abs_path, rel_posix) or None."""
    if str(domain).startswith("_") or str(sub).startswith("_"):
        return None  # 拒绝 _trash/_inbox/_meta/_assets 等下划线目录（不变量 2）
    base = content / domain
    sdir = base / sub if sub != "_root" else base
    if not base.is_dir() or not sdir.is_dir():
        return None
    for cand in (sdir / f"{name}.md", sdir / name, sdir / f"{name}.html"):
        if cand.is_file() and cand.suffix in SERVABLE_EXTS:
            return cand
    return None


# ---------------- 备注（sidecar .notes.md） ----------------
def notes_path(doc_path: Path) -> Path:
    return doc_path.with_name(doc_path.name + ".notes.md")


def read_notes(doc_path: Path) -> list[dict]:
    np = notes_path(doc_path)
    if not np.is_file():
        return []
    out = []
    for line in np.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"- \[(.+?)\] (.*)", line.strip())
        if m:
            out.append({"when": m.group(1), "text": m.group(2)})
    return list(reversed(out))  # newest first


# ---------------- 语料变更原语（治理工具共用；一切变更先 dry-run） ----------------
def sidecars_of(doc_path: Path) -> list[Path]:
    """文档的旁挂文件（备注、美化版），移动/重命名时必须随行。"""
    out = []
    for sib in (doc_path.with_name(doc_path.name + ".notes.md"),
                doc_path.with_name(doc_path.stem + ".html")):
        if sib.is_file():
            out.append(sib)
    return out


def rename_doc(doc_path: Path, new_path: Path) -> dict:
    """移动/重命名单个文档及其旁挂；目标存在时拒绝。返回实际移动清单。"""
    if new_path.exists():
        raise FileExistsError(f"dst exists: {new_path}")
    new_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.rename(new_path)
    moved = [str(doc_path)]
    for sib in sidecars_of(doc_path):
        if ".notes.md" in sib.name:
            sib_new = new_path.with_name(new_path.name + ".notes.md")
        else:
            sib_new = new_path.with_name(new_path.stem + ".html")
        sib.rename(sib_new)
        moved.append(str(sib))
    return {"src": str(doc_path), "dst": str(new_path), "moved": moved}


def iter_doc_frontmatter(content: Path):
    """迭代全库文档：yield (abs_path, fm, body)。只读。"""
    for p, _rel in md_files(content):
        raw = p.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_frontmatter(raw)
        yield p, fm, body


def tag_census(content: Path) -> dict[str, int]:
    """全库标签普查：{tag: 文档数}（保留原大小写，聚合时大小写不敏感）。"""
    census: dict[str, int] = {}
    seen_per_doc: set = set()
    for _p, fm, _b in iter_doc_frontmatter(content):
        tags = fm.get("tags")
        if not isinstance(tags, list):
            continue
        seen_per_doc.clear()
        for t in tags:
            t = str(t).strip()
            if t and t.lower() not in seen_per_doc:
                seen_per_doc.add(t.lower())
                census[t] = census.get(t, 0) + 1
    return dict(sorted(census.items(), key=lambda x: -x[1]))


def find_similar_tags(census: dict[str, int]) -> list[tuple[str, str, float]]:
    """疑似重叠标签对，按可疑度排序。
    降噪规则（中文短词编辑距离普遍小，直接比会误导）：
    - 大小写差异（1.0）：照报；
    - 包含关系（0.9）：仅当短词含 ASCII 字母/数字（AI/AI资产、git/GitHub
      这类有词根价值的），纯中文双字包含对（如 源码/源码分析）也报但置信降
      一档 0.7，避免浩劫；
    - 编辑距离（0.6）：仅 ASCII 词且阈值 ≤1（Vue2/Vue3 这类），中文词不比。"""
    tags = list(census.keys())
    pairs: list[tuple[str, str, float]] = []

    def lev(a: str, b: str) -> int:
        if abs(len(a) - len(b)) > 1:
            return 99
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            cur = [i]
            for j, cb in enumerate(b, 1):
                cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
            prev = cur
        return prev[-1]

    def has_ascii(s: str) -> bool:
        return any(c.isascii() and c.isalnum() for c in s)

    for i, a in enumerate(tags):
        for b in tags[i + 1:]:
            al, bl = a.lower(), b.lower()
            if al == bl:
                pairs.append((a, b, 1.0))
            elif al in bl or bl in al:
                short = a if len(al) <= len(bl) else b
                pairs.append((a, b, 0.9 if has_ascii(short) else 0.7))
            elif has_ascii(a) and has_ascii(b) and lev(al, bl) <= 1:
                pairs.append((a, b, 0.6))
    return sorted(pairs, key=lambda x: -x[2])


def merge_tag(content: Path, src: str, dst: str, apply: bool = False) -> dict:
    """把标签 src 并入 dst（大小写不敏感匹配 src）。默认 dry-run。
    dst 不存在时等价于重命名。返回受影响文档清单与预览 diff。"""
    affected: list[dict] = []
    for p, fm, body in iter_doc_frontmatter(content):
        tags = fm.get("tags")
        if not isinstance(tags, list):
            continue
        new_tags: list[str] = []
        hit = False
        for t in tags:
            if str(t).strip().lower() == src.lower():
                hit = True
                if dst not in new_tags:
                    new_tags.append(dst)
            else:
                if str(t) not in new_tags:
                    new_tags.append(str(t))
        if not hit:
            continue
        old_fm = list(tags)
        fm2 = dict(fm)
        fm2["tags"] = new_tags
        new_raw = dump_frontmatter(fm2, body)
        affected.append({"path": p, "old_tags": old_fm, "new_tags": new_tags,
                         "new_raw": new_raw})
    if apply:
        for a in affected:
            a["path"].write_text(a["new_raw"], encoding="utf-8")
    return {"src": src, "dst": dst, "apply": apply,
            "n_docs": len(affected),
            "docs": [{"path": a["path"].relative_to(content).as_posix(),
                      "old_tags": a["old_tags"], "new_tags": a["new_tags"]} for a in affected]}


def rename_sub(content: Path, domain: str, old_sub: str, new_sub: str,
               apply: bool = False) -> dict:
    """重命名/移动整个子域目录：逐文档搬移（含旁挂），更新 taxonomy.json。
    默认 dry-run。返回计划/执行的文件清单。调用方负责随后重建 FTS 索引
    （build_index 全量 <1s）并触发 sync_rag（mtime 未变但路径变化，
    sync_rag 会把新路径当新增、旧路径当删除自然对齐）。"""
    if "/" in new_sub or new_sub.startswith("_") or new_sub in SKIP_DIRS:
        raise ValueError(f"invalid new sub name: {new_sub}")
    src_dir = content / domain / (old_sub if old_sub != "_root" else "")
    if not src_dir.is_dir():
        raise FileNotFoundError(f"sub dir not found: {src_dir}")
    docs = sorted(p for p in src_dir.rglob("*")
                  if p.is_file() and p.suffix in SERVABLE_EXTS)
    plan = []
    tax_path = content / "_meta" / "taxonomy.json"
    for p in docs:
        rel_old = p.relative_to(content)
        rel_new = Path(new_sub) / rel_old.relative_to(old_sub) \
            if old_sub != "_root" else Path(rel_old.parent.name) / rel_old.name
        # _root 重命名 = 把域根散文件收进新子域
        if old_sub == "_root":
            rel_new = Path(new_sub) / p.name
        plan.append({"src": rel_old.as_posix(), "dst": rel_new.as_posix(),
                     "abs": p})
    if apply:
        for item in plan:
            p = item["abs"]
            new_path = content / item["dst"]
            new_path.parent.mkdir(parents=True, exist_ok=True)
            p.rename(new_path)
            for sib in sidecars_of(p):
                sib.rename(new_path.with_name(sib.name))
        # taxonomy.json：scoped 键 域/旧子域 → 域/新子域；普通键同步改名
        if tax_path.is_file():
            tax = json.loads(tax_path.read_text(encoding="utf-8"))
            subs = tax.get("subs", {})
            scoped_old, scoped_new = f"{domain}/{old_sub}", f"{domain}/{new_sub}"
            if old_sub == "_root":
                # 域根散文件收进新子域：scoped 键直接新增
                subs.setdefault(scoped_new, new_sub)
            else:
                subs = {(scoped_new if k == scoped_old else k): v
                        for k, v in subs.items()}
                if old_sub in subs:
                    subs = {(new_sub if k == old_sub else k): v
                            for k, v in subs.items()}
            tax["subs"] = subs
            tax_path.write_text(json.dumps(tax, ensure_ascii=False, indent=2),
                                encoding="utf-8")
        # 清理空的旧目录（_root 场景无独立目录）
        if old_sub != "_root":
            try:
                src_dir.rmdir()
            except OSError:
                pass  # 尚有旁挂/隐藏文件，留待人工
    return {"domain": domain, "old_sub": old_sub, "new_sub": new_sub,
            "apply": apply, "n_docs": len(plan),
            "plan": [{"src": i["src"], "dst": i["dst"]} for i in plan]}
