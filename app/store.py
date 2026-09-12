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
# sqlite3 的 busy_timeout（秒）：所有连向 indexes/*.db 的连接统一用这个值。
# 背景：`_index_watcher` 每 30s 会重建/增量 FTS，写事务期间会独占锁；此时用户
# 保存文档或刷页面就会撞上 `database is locked`。给 30s 等待窗口后，这类碰撞
# 变成「多等一会儿」而不是 500。真等满 30s 仍拿不到锁才会抛，且调用方会记日志。
SQLITE_BUSY_TIMEOUT_S = 30

# frontmatter 块匹配：容忍 BOM 与 CRLF。Windows autocrlf 检出的语料在盘上是 CRLF
# （687/690 篇），Obsidian/记事本还可能写入 BOM；旧写法 \A---\n 对这两类文件静默
# 失配 → frontmatter 被当正文读（tags/title 丢）、写回时再叠一块新 frontmatter（双块损坏）。
# JS 侧 fetchFmRaw 一直是 \uFEFF? + \r?\n 的宽口径，这里对齐。
FM_RE = re.compile(r"\A\ufeff?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n)(?:\r?\n)?", re.S)
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
        elif val is False:
            # 旧写法把 False 写进字符串分支 → `favorite: "False"`（带引号的布尔污染语料，
            # 工作区已出现实例）。只允许在「新建文件补 stamp」这类全量重建场景使用本函数。
            lines.append(f"{key}: false")
        elif isinstance(val, list):
            lines.append(f"{key}: [{', '.join(str(x) for x in val)}]")
        else:
            lines.append(f'{key}: "{val}"')
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body


# ---------------- frontmatter 单键行级手术（B1 修复核心） ----------------
# favorite 切换、标签合并历史上用 parse→dump 整块重建：嵌套 YAML（hero:/features:
# 多行块，语料实测 41 篇）会被压平毁结构、注释丢失、布尔被引号化。
# 以下助手只改动目标键所在的一行（或插一行），其余字节原样保留；
# 结构超出「顶层单行 key: value」的能力范围时宁可抛错，绝不猜。

def _decode_md(raw: bytes) -> str:
    """解码语料字节（BOM 保留在文本内由 FM_RE 容忍；\r\n 不转换——写回按字节保真）。"""
    return raw.decode("utf-8-sig", errors="replace") if raw[:3] == b"\xef\xbb\xbf" \
        else raw.decode("utf-8", errors="replace")


def _encode_md(text: str, had_bom: bool) -> bytes:
    return (("﻿" + text) if had_bom else text).encode("utf-8")


def _fm_region(text: str):
    """返回 (inner_start, inner_end)：frontmatter 内部文本的区间；无块返回 (None, None)。"""
    m = FM_RE.match(text)
    if not m:
        return None, None
    return m.span(1)


def set_fm_scalar(text: str, key: str, value: str) -> str:
    """行级设置 frontmatter 顶层标量键。无块时给文件补一个最小块（LF，新文件风格）。

    Raises:
        ValueError: key 以缩进形式出现在嵌套结构中（无法安全判定它是否就是目标键）。
    """
    start, end = _fm_region(text)
    # 插入行必须随文档换行风格（autocrlf 语料是 CRLF，混入裸 \n 会让 git diff 脏整块）
    eol = "\r\n" if "\r\n" in text[:400] else "\n"
    if start is None:
        return f"---{eol}{key}: {value}{eol}---{eol}{eol}" + text
    inner = text[start:end]
    if re.search(r"^[ \t]+" + re.escape(key) + r"[ \t]*:", inner, re.M):
        raise ValueError(f"frontmatter 中「{key}」出现在缩进结构中，拒绝行级改写")
    line_re = re.compile(r"(?m)^" + re.escape(key) + r"[ \t]*:.*$")
    m = line_re.search(inner)
    if m:
        inner2 = inner[:m.start()] + f"{key}: {value}" + inner[m.end():]
    elif inner.strip():
        inner2 = f"{inner}{eol}{key}: {value}"
    else:
        inner2 = f"{key}: {value}"
    return text[:start] + inner2 + text[end:]


def toggle_fm_bool(path: Path, key: str) -> bool:
    """按字节保真地切换 frontmatter 布尔键；返回新值。解析用扁平器只读当前值。"""
    raw = path.read_bytes()
    had_bom = raw[:3] == b"\xef\xbb\xbf"
    text = _decode_md(raw)
    fm, _ = parse_frontmatter(text)
    new_val = not (fm.get(key) is True)
    out = set_fm_scalar(text, key, "true" if new_val else "false")
    path.write_bytes(_encode_md(out, had_bom))
    return new_val


def prepend_original_fm(path: Path, body: str) -> str | None:
    """B6 修复支撑：body 丢了 frontmatter 而磁盘原文件有时，把原块补回头部。

    返回拼接后的全文；文件不存在 / 原文件无可解析 frontmatter 时返回 None
    （交给调用方走「新文件补 stamp」路径）。
    原块统一转成 LF：调用方随后 write_text（newline=None 会把 \n 转 \r\n），
    混入 \r\n 片段会被二次转换成 \r\r\n。
    """
    if not path.is_file():
        return None
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    m = FM_RE.match(_decode_md(raw))
    if not m:
        return None
    head = m.group(0).replace("\r\n", "\n")
    if not head.endswith("\n"):
        head += "\n"
    return head + body.lstrip("\r\n")


# ---------------- 语料扫描 ----------------
def is_visible_doc(rel_posix: str) -> bool:
    """树 / FTS / RAG / 签名共用的可见性谓词（B2/B3 修复）：

    · 路径任一 `_` 前缀段（_inbox/_trash/_assets/_meta/嵌套 _tmp…）不可见 —— 不变量 2；
    · `.notes.md` 备注旁挂不是文档 —— 否则写第一条备注就凭空多出一篇可路由的幽灵文档。
    """
    parts = [x for x in str(rel_posix).split("/") if x]
    return not (any(p.startswith("_") for p in parts)
                or (parts and parts[-1].endswith(".notes.md")))


def md_files(content: Path):
    """全库 md 文件迭代器（(abs_path, rel_posix)）；跳过 _ 前缀与 SKIP_DIRS 与备注旁挂。"""
    for dirpath, dirnames, filenames in os.walk(content):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith("_")]
        for fn in filenames:
            if fn.endswith(".md") and not fn.endswith(".notes.md"):
                p = Path(dirpath) / fn
                yield p, p.relative_to(content).as_posix()


def _visible_sub_files(sdir: Path) -> list[Path]:
    """子域目录内可见文件（B2/B3）：os.walk 剪掉嵌套 `_` 目录，排除备注旁挂。
    替代旧 rglob —— 它会把 baike/algorithms/_tmp/x.md 之类当成文档列进树。"""
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(sdir):
        dirnames[:] = [d for d in dirnames if not d.startswith("_")]
        for fn in filenames:
            if fn.endswith(".notes.md"):
                continue
            if fn.endswith(tuple(SERVABLE_EXTS)):
                out.append(Path(dirpath) / fn)
    return sorted(out)


def _tree_sig(content: Path) -> str:
    """仅 stat 不读内容的树签名：毫秒级，作为扫描/索引缓存的失效依据。
    含文件清单（含删除），比单纯 max(mtime) 更可靠：删除也能立即感知。"""
    parts = []
    for dirpath, dirnames, filenames in os.walk(content):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith("_")]
        for fn in filenames:
            if fn.endswith(".notes.md"):
                continue  # 旁挂备注不可见（B2），计入签名会让每次记备注都白白失效一轮缓存
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
        loose = sorted(p for p in ddir.iterdir()
                       if p.is_file() and p.suffix in SERVABLE_EXTS
                       and not p.name.endswith(".notes.md"))  # B2：域根文档的备注旁挂同样不可见
        sdirs = sorted(p for p in ddir.iterdir()
                       if p.is_dir() and p.name not in SKIP_DIRS and not p.name.startswith("_"))
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
    以子路径作为文档名（<path:name> 路由支持带斜杠的 name）。
    B2/B3：默认文件清单走 _visible_sub_files（剪嵌套 _ 目录、排除备注旁挂）。"""
    files = files if files is not None else _visible_sub_files(sdir)
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
    if str(domain).startswith("_"):
        return None  # 拒绝 _inbox/_trash/_meta 等下划线域（不变量 2）
    # `_root` 是「域根散文件」的哨兵子域 id（scan_corpus 给 `career/xx.md` 这类
    # 两段 rel 用的），**不是**真实目录，必须在下面的守卫之前放行 —— 否则它会被
    # 和 _trash/_assets 一起拒掉，凡直接躺在域目录下的文档一律 404。
    # 分类树和前端 docUrl() 两头都是 `_root`（app.js / kb-core.js 同款），
    # 所以这里是唯一该改的地方，改完「树给的 path」和「路由能解析的 path」就一致了。
    if sub != "_root" and str(sub).startswith("_"):
        return None  # 拒绝 _trash/_inbox/_meta/_assets 等下划线子域（不变量 2）
    base = content / domain
    sdir = base if sub == "_root" else base / sub
    if not base.is_dir() or not sdir.is_dir():
        return None
    # B2/B3 纵深防御：树已不再列出的不可见文件（嵌套 _ 目录、备注旁挂），
    # 直接构造 URL 也一律 404 —— 「树给的 path」与「路由能解析的 path」必须同集合。
    nm = str(name)
    if any(seg.startswith("_") for seg in nm.split("/") if seg):
        return None
    for cand in (sdir / f"{name}.md", sdir / name, sdir / f"{name}.html"):
        if cand.name.endswith(".notes.md"):
            continue  # 旁挂备注永远不是文档（不误伤恰以 .notes 命名的正常文件）
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


# tags 行只认这一种形态：顶层、单行、内联列表。多行 block 列表 / 缩进结构一律跳过不改。
_TAGS_INLINE_RE = re.compile(r"(?m)^tags[ \t]*:[ \t]*\[([^\]\r\n]*)\][ \t]*$")


def _merge_tags_line(inner: str, src: str, dst: str):
    """在 frontmatter 内部文本上做一次标签替换。

    返回 (new_inner, hit, skip_reason)：
      hit=True → tags 行已改写（其余字节原样）；
      skip_reason 非空 → 该文件的 tags 形态不安全，不改；
      两者皆 False/None → 该文件的 tags 里没有 src。
    """
    m = _TAGS_INLINE_RE.search(inner)
    if not m:
        if re.search(r"(?m)^tags[ \t]*:[ \t]*$", inner):
            return inner, False, "tags 为多行 block 列表（行级改写不安全）"
        if re.search(r"(?m)^tags[ \t]*:", inner):
            return inner, False, "tags 形态非内联列表"
        return inner, False, None
    items = [x.strip().strip("\"'") for x in m.group(1).split(",") if x.strip()]
    if not any(t.lower() == src.lower() for t in items):
        return inner, False, None
    if any(re.search(r"^[ \t]+\S", ln) for ln in inner.splitlines()):
        # 块内存在缩进行 = 有嵌套结构，tags 行虽在顶层但整块形态存疑，保守跳过
        return inner, False, "frontmatter 含缩进结构，保守跳过"
    new_items: list[str] = []
    for t in items:
        if t.lower() == src.lower():
            if not any(x.lower() == dst.lower() for x in new_items):
                new_items.append(dst)  # 大小写不敏感去重（原实现区分大小写，可留 AI/ai 双胞胎）
        elif not any(x.lower() == t.lower() for x in new_items):
            new_items.append(t)
    replaced = "tags: [" + ", ".join(new_items) + "]"
    return inner[:m.start()] + replaced + inner[m.end():], True, None


def merge_tag(content: Path, src: str, dst: str, apply: bool = False) -> dict:
    """把标签 src 并入 dst（大小写不敏感匹配 src）。默认 dry-run。

    行级手术只改 tags 行：嵌套 YAML / 注释 / 其余字节不动（旧实现 parse→dump
    整块重建，实测 41 篇带多行结构的语料会被压平毁结构 —— B1 修复）。
    无法安全改写的文件进 skipped 清单并给原因，绝不硬写。
    返回受影响文档清单（old_tags/new_tags）与 skipped。
    """
    affected: list[dict] = []
    skipped: list[dict] = []
    for p, rel in md_files(content):
        try:
            raw = p.read_bytes()
        except OSError:
            continue
        text = _decode_md(raw)
        start, end = _fm_region(text)
        if start is None:
            continue
        inner = text[start:end]
        old_fm, _ = parse_frontmatter(text)
        old_tags = old_fm.get("tags")
        if not isinstance(old_tags, list) or not old_tags:
            continue
        new_inner, hit, why = _merge_tags_line(inner, src, dst)
        if why:
            skipped.append({"path": rel, "reason": why,
                            "tags": [str(t) for t in old_tags]})
            continue
        if not hit:
            continue
        new_raw = text[:start] + new_inner + text[end:]
        new_tags, _ = parse_frontmatter(new_raw)
        affected.append({"path": p, "rel": rel, "raw": raw,
                         "new_text": new_raw, "had_bom": raw[:3] == b"\xef\xbb\xbf",
                         "old_tags": [str(t) for t in old_tags],
                         "new_tags": [str(t) for t in (new_tags.get("tags") or [])]})
    if apply:
        for a in affected:
            a["path"].write_bytes(_encode_md(a["new_text"], a["had_bom"]))
    return {"src": src, "dst": dst, "apply": apply,
            "n_docs": len(affected),
            "docs": [{"path": a["rel"], "old_tags": a["old_tags"],
                      "new_tags": a["new_tags"]} for a in affected],
            "n_skipped": len(skipped), "skipped": skipped}


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
