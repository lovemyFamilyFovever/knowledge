# -*- coding: utf-8 -*-
"""知库语料层 —— frontmatter、分类树扫描、备注、Obsidian 连接、分类学装载。

content/ 的 Markdown/HTML 是唯一事实源；本模块只读语料 + 写回元数据，
不含任何路由与索引逻辑（FTS 见 fts.py，向量见 rag.py，路由见 app.py）。

分类学（taxonomy）权威：content/_meta/taxonomy.json（_ 前缀目录不进索引）。
装载策略：JSON 覆盖内置缺省；JSON 缺失/损坏时全部走内置缺省，阅读器不炸。
"""
import json
import os
import re
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
