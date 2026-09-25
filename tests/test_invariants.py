# -*- coding: utf-8 -*-
"""知库不变量门禁 —— 把 AGENTS.md 的 8 条不变量编译成可执行断言。

运行：python tests/test_invariants.py   （失败非 0 退出；无 pytest 依赖）
每条的结论只有两种：可执行断言（本文件里能跑）或"不可执行 + 原因"（写在该条注释里）。
用 tempfile 造迷你语料，**绝不读写真实 content/**；只对仓库做只读的 git 查询。

I1 content/ 是唯一事实源：编辑/备注/收藏写回文件系统，不存在第二真相
I2 `_` 前缀目录不进分类树、不进 FTS/RAG 索引
I3 indexes/ 是纯派生缓存：git 忽略、可删、删后自动重建且结果一致
I4 删除必走软删 → content/_trash/；另有全仓物理删除调用点白名单审计
I5 分类学权威 = content/_meta/taxonomy.json，代码内字典仅缺省兜底
I6 frontmatter 只存身世元数据（title/source/collected/tags/favorite/status）
I7 切块/分词逻辑变更必须递增 RAG_CODE_VERSION（静态检查脚本的自测）
I8 不依赖 cwd：从任意工作目录用绝对路径直启 app/app.py --import-check 必过
I9 待发布语料的 frontmatter 必须过严格 YAML 门禁（发布侧与 pre-commit 共用同一道闸）
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.app import create_app  # noqa: E402
from app import fts, store  # noqa: E402

try:
    from app import rag as rag_mod
except Exception:  # pragma: no cover - 缺 numpy 等依赖时降级
    rag_mod = None

FM_WHITELIST = {"title", "source", "collected", "tags", "favorite", "status"}

DOC_A = (
    '---\ntitle: "可见甲"\nsource: "baike"\nstatus: "imported"\ntags: [AI]\n---\n'
    "\n# 可见甲\n\n可见正文 zzvisiblemark。\n"
)

passed = failed = skipped = 0


def check(name: str, cond: bool, extra="") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS {name}")
    else:
        failed += 1
        print(f"  FAIL {name} {extra}")


def skip(name: str, why: str) -> None:
    global skipped
    skipped += 1
    print(f"  SKIP {name}（{why}）")


def group(title: str) -> None:
    print(f"== {title} ==")


def seed(root: Path) -> Path:
    """迷你语料：1 篇可见文档 + 4 处 `_` 前缀/嵌套 `_` 的诱饵。"""
    c = root / "content"
    (c / "ai" / "topic").mkdir(parents=True)
    (c / "ai" / "topic" / "A.md").write_text(DOC_A, encoding="utf-8")
    (c / "ai" / "_tmp").mkdir()
    (c / "ai" / "_tmp" / "NESTED.md").write_text("# n\nzznestedmark\n", encoding="utf-8")
    for name, fn in (("_foo", "ZFOO.md"), ("_inbox", "ZINBOX.md"), ("_assets", "ZASSETS.md")):
        (c / name).mkdir()
        (c / name / fn).write_text(f"# {name}\nzz{name.strip('_')}mark\n", encoding="utf-8")
    return c


# ---------------------------------------------------------------- I1
def test_i1() -> None:
    group("I1 content/ 是唯一事实源（无第二真相）")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        c = seed(root)
        cl = create_app(root).test_client()
        doc = c / "ai" / "topic" / "A.md"

        r = cl.post("/api/save", json={"path": "ai/topic/A.md",
                                       "content": '---\ntitle: "可见甲"\n---\n\n新正文标记 zznewbody\n'})
        check("I1 api_save 返回 ok", r.get_json().get("ok") is True, r.get_json())
        check("I1 api_save 后磁盘文件含新正文",
              "zznewbody" in doc.read_text(encoding="utf-8"))

        cl.post("/api/note", json={"path": "ai/topic/A.md", "text": "备注标记 zznotemark"})
        side = c / "ai" / "topic" / "A.md.notes.md"
        check("I1 api_note 落盘旁挂 .notes.md 且含备注文本",
              side.is_file() and "zznotemark" in side.read_text(encoding="utf-8"))

        cl.post("/api/favorite", json={"path": "ai/topic/A.md"})
        # 关键：不看进程内状态，重新从磁盘解析 —— 磁盘才是真相
        fm, _ = store.parse_frontmatter(doc.read_text(encoding="utf-8"))
        check("I1 api_favorite 写进磁盘 frontmatter（独立复读可见）", fm.get("favorite") is True, fm)

        # 写入产物只允许落在 content/ 与 indexes/，别处出现文件 = 第二真相落点
        stray = [p.relative_to(root).as_posix() for p in root.rglob("*")
                 if p.is_file() and p.relative_to(root).parts[0] not in ("content", "indexes")]
        check("I1 无 content//indexes/ 之外的落盘（无第二真相存储）", stray == [], stray[:5])
        check("I1 content/ 下无派生的 .db 文件", not list(c.rglob("*.db")))

        # 静态：app/ 里所有 sqlite 连接都指向 indexes/ 派生缓存
        bad = []
        for f in sorted((ROOT / "app").glob("*.py")):
            src = f.read_text(encoding="utf-8")
            for m in re.finditer(r"sqlite3\.connect\((.{0,200}?)[,)]", src, re.S):
                arg = m.group(1)
                if "indexes" not in arg and "db_path" not in arg:
                    bad.append(f"{f.name}: {arg.strip()[:60]}")
        check("I1 app/ 的 sqlite 连接全部落在 indexes/（无独立数据库）", bad == [], bad)
        check("I1 RagStore 的 db_path 由 indexes/ 拼出（唯一间接层可核）",
              'indexes / "rag.db"' in (ROOT / "app" / "rag.py").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- I2
def test_i2() -> None:
    group("I2 `_` 前缀目录不进树/不进城/不进索引")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        c = seed(root)
        app = create_app(root)
        cl = app.test_client()
        idx = root / "indexes"

        rels = sorted(r for _, r in store.md_files(c))
        check("I2 md_files 不含任何 _ 前缀段", rels == ["ai/topic/A.md"], rels)
        check("I2 is_visible_doc 拒绝 _foo / 嵌套 _tmp / .notes.md",
              store.is_visible_doc("_foo/ZFOO.md") is False
              and store.is_visible_doc("ai/_tmp/NESTED.md") is False
              and store.is_visible_doc("ai/topic/A.md") is True
              and store.is_visible_doc("ai/topic/A.md.notes.md") is False)

        dt = json.loads(cl.get("/api/dir/tree").get_data(as_text=True))
        names = []

        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    if k in ("id", "name", "title", "label") and isinstance(v, str):
                        names.append(v)
                    walk(v)
            elif isinstance(o, list):
                for x in o:
                    walk(x)
        walk(dt)
        check("I2 /api/dir/tree 含可见文档标题且不含 _ 诱饵",
              "可见甲" in names and not [n for n in names if n.startswith("_") and n != "_root"]
              and "ZFOO" not in names and "NESTED" not in names, names)

        check("I2 find_doc 直接构造 URL 也拒绝 _ 目录",
              store.find_doc(c, "_inbox", "_root", "ZINBOX") is None
              and store.find_doc(c, "ai", "_tmp", "NESTED") is None)
        check("I2 路由 /doc/_foo/... 不可达", cl.get("/doc/_foo/_root/ZFOO").status_code == 404)

        hits = fts.search(idx, "zzvisiblemark")
        check("I2 FTS 命中可见文档", len(hits) >= 1, hits)
        check("I2 FTS 不命中 _foo / _inbox / _assets / 嵌套 _tmp 的内容",
              all(fts.search(idx, m) == []
                  for m in ("zzfoomark", "zzinboxmark", "zzassetsmark", "zznestedmark")))

        if rag_mod is None:
            skip("I2 RAG 语料集不含 _ 前缀", "app.rag 导入失败（缺依赖）")
        else:
            corpus = sorted(rag_mod.md_corpus_files(c))
            check("I2 RAG 语料集不含 _ 前缀段", corpus == ["ai/topic/A.md"], corpus)


# ---------------------------------------------------------------- I3
def test_i3() -> None:
    group("I3 indexes/ 是纯派生缓存（git 忽略 / 可删 / 可重建且结果一致）")
    if shutil.which("git") is None:
        skip("I3 git 忽略检查", "未找到 git")
    else:
        for rel in ("indexes/index.db", "indexes/rag.db", "indexes/reading.db"):
            r = subprocess.run(["git", "check-ignore", "-q", rel], cwd=str(ROOT),
                               capture_output=True, text=True)
            check(f"I3 git check-ignore 判定 {rel} 被忽略", r.returncode == 0)
        r = subprocess.run(["git", "ls-files", "--", "indexes"], cwd=str(ROOT),
                           capture_output=True, text=True, encoding="utf-8")
        check("I3 indexes/ 下无任何被跟踪文件", r.stdout.strip() == "", r.stdout[:200])

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        seed(root)
        cl = create_app(root).test_client()
        cl.post("/api/save", json={"path": "ai/topic/A.md", "content": DOC_A})
        idx = root / "indexes"
        before = json.dumps(fts.search(idx, "zzvisiblemark"), sort_keys=True, ensure_ascii=False)
        check("I3 重建前能命中（基线非空）", before not in ("[]", "null"), before[:120])

        shutil.rmtree(idx)
        check("I3 删光 indexes/ 后目录确实消失", not idx.exists())
        create_app(root)  # 重启：应自动全量重建
        check("I3 重启后 index.db 自动重建", (idx / "index.db").is_file())
        after = json.dumps(fts.search(idx, "zzvisiblemark"), sort_keys=True, ensure_ascii=False)
        check("I3 重建后检索结果与删除前一致", before == after,
              f"\n    before={before[:120]}\n    after ={after[:120]}")


# ---------------------------------------------------------------- I4
DELETE_RE = re.compile(
    r"(?P<os_remove>\bos\.remove\()|(?P<os_unlink>\bos\.unlink\()|(?P<os_rmdir>\bos\.rmdir\()"
    r"|(?P<rmtree>\bshutil\.rmtree\()|(?P<move>\bshutil\.move\()|(?P<unlink>\.unlink\()"
)
# 白名单：每个物理删除/搬移调用点都要有人判定过"会不会删到真实语料"。
# 新增调用点 → 计数变化 → 本断言失败（逼作者写清楚为什么它是安全的）；
# 删掉调用点也要同步改这里（否则 stale 也报失败），避免白名单腐烂。
AUDIT_ALLOWED = {
    ("app/routes_files.py", "unlink"): 1,              # api_inbox_purge：仅 _inbox/（resolve 后双重前缀校验）
    ("app/routes_files.py", "move"): 1,                # api_rmdir：整树搬进 _trash（软删）
    ("app/store.py", "move"): 1,                       # rename_domain/rename_sub：content/ 内迁移，非删除
    ("scripts/backup_reading.py", "unlink"): 1,        # 轮转删旧备份（backups/reading/ 下，非语料）
    ("scripts/clean_inbox_clones.py", "rmtree"): 1,    # _inbox/repos 副本，原件目录存在才删
    ("scripts/file_inbox_batch1.py", "unlink"): 1,     # 入库成功后删桌面源文件（content/ 外）
    ("scripts/publish_site.py", "unlink"): 1,          # prune 站仓（dest）里已不在白名单的文件；有"缺 quartz.config 即中止"的守卫
    ("scripts/remap_taxonomy.py", "move"): 1,          # taxonomy 重映射搬目录
    ("tests/test_learn.py", "unlink"): 2,              # 临时语料 / 派生库自清理
    ("tests/test_reader.py", "unlink"): 2,             # 临时语料：模拟外部删除 + 探针清理
    ("tests/test_known_defects.py", "os_rmdir"): 1,    # 摘 junction 链（不穿透删目标，是 rmtree 前的安全前置）
    ("tests/test_known_defects.py", "rmtree"): 1,      # 临时目录（tempfile.mkdtemp）自清理
    # P3-B JS 性质测试：删的是 tempfile.mkdtemp 起的临时 KB_ROOT（内含自建的 content/ 与
    # 从仓库复制过去的 static/ 副本），且尾部有一条断言亲自证明"删除目标在系统临时目录下、
    # 仓库 content/ 完好"，不是随手一把梭。
    ("tests/test_js_props.py", "rmtree"): 1,
    # P5 视觉回归：两处 —— ① .qa/p5/actual* 截图目录重截前清空（.qa 不进 git、非语料）；
    # ② tempfile.mkdtemp 的临时 KB_ROOT 自清理（同 test_js_props 的判定，尾部同样有断言）。
    ("tests/test_ui_regress.py", "rmtree"): 2,
    # UI 行为回归（轮次 24）：一处 —— tempfile.mkdtemp 起的临时 KB_ROOT 自清理（内含自建的
    # content/ 与从仓库复制的 static/ 副本）。本套会真的删语料（crumb 删除 / #ed-del /
    # 收件箱 del+purge），但全部落在临时根上，尾部有一条断言亲自证明删除目标在系统临时
    # 目录下、仓库 content/ 完好。
    ("tests/test_ui_behavior.py", "rmtree"): 1,
}
AUDIT_SELF = "tests/test_invariants.py"   # 本文件自身含这些字面量，排除以免自指


def audit_delete_sites() -> dict:
    found: dict = {}
    for sub in ("app", "scripts", "tests"):
        for f in sorted((ROOT / sub).rglob("*.py")):
            rel = f.relative_to(ROOT).as_posix()
            if rel == AUDIT_SELF:
                continue
            for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if line.lstrip().startswith("#"):
                    continue
                for m in DELETE_RE.finditer(line):
                    kind = next(k for k, v in m.groupdict().items() if v)
                    found.setdefault((rel, kind), []).append(i)
    return found


def test_i4() -> None:
    group("I4 删除必走软删 → content/_trash/，且全仓物理删除有白名单")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        c = seed(root)
        cl = create_app(root).test_client()
        doc = c / "ai" / "topic" / "A.md"
        (c / "ai" / "topic" / "A.html").write_text("<h1>twin</h1>", encoding="utf-8")
        cl.post("/api/note", json={"path": "ai/topic/A.md", "text": "备注"})

        r = cl.post("/api/delete", json={"path": "ai/topic/A.md"})
        j = r.get_json()
        check("I4 /api/delete 返回 ok", j.get("ok") is True, j)
        check("I4 主文件 + 2 件旁挂一起搬走", sorted(j.get("moved", [])) ==
              ["ai/topic/A.html", "ai/topic/A.md", "ai/topic/A.md.notes.md"], j)
        check("I4 原路径已消失", not doc.exists()
              and not (c / "ai" / "topic" / "A.md.notes.md").exists()
              and not (c / "ai" / "topic" / "A.html").exists())

        trash = c / "_trash"
        tds = [d for d in trash.iterdir() if d.is_dir()]
        check("I4 回收站目录名是 <YYYYmmdd-HHMMSS>",
              len(tds) == 1 and re.fullmatch(r"\d{8}-\d{6}", tds[0].name) is not None,
              [d.name for d in tds])
        moved_files = sorted(p.relative_to(tds[0]).as_posix().replace("\\", "/")
                             for p in tds[0].rglob("*") if p.is_file())
        check("I4 三件都在 _trash/<ts>/ 下、相对结构保留",
              moved_files == ["ai/topic/A.html", "ai/topic/A.md", "ai/topic/A.md.notes.md"],
              moved_files)
        check("I4 软删后索引不再命中", fts.search(root / "indexes", "zzvisiblemark") == [])

        # 唯一允许物理删除的接口：/api/inbox/purge。它的代码注释记载曾因路径穿越
        # 误删 1 篇正式树文档（"_inbox/../../content/x.md"），修复后一直**没有**回归
        # 断言 —— 这是全仓唯一能把正式语料删掉的地方，必须锁死。
        victim = c / "ai" / "topic" / "VICTIM.md"
        victim.write_text('---\ntitle: "V"\n---\n\nvictim zzvictimmark\n', encoding="utf-8")
        r = cl.post("/api/inbox/purge", json={"path": "_inbox/../ai/topic/VICTIM.md"})
        check("I4 purge 拒绝穿越到正式树的路径，且目标文件完好",
              r.status_code == 400 and victim.is_file(), (r.status_code, r.get_json()))
        r = cl.post("/api/inbox/purge", json={"path": "ai/topic/VICTIM.md"})
        check("I4 purge 拒绝一切非 _inbox/ 路径（正式文档不可物理删）",
              r.status_code == 400 and victim.is_file(), (r.status_code, r.get_json()))
        junk = c / "_inbox" / "JUNK.md"
        junk.write_text("# junk\n", encoding="utf-8")
        r = cl.post("/api/inbox/purge", json={"path": "_inbox/JUNK.md"})
        check("I4 purge 仍能彻底删除 _inbox/ 下的文件（功能未被防护误伤）",
              r.get_json().get("ok") is True and not junk.exists(), r.get_json())
        check("I4 边界校验后语料树仍完整（正式文档未被 purge 波及）",
              sorted(p.name for p in (c / "ai" / "topic").iterdir()) == ["VICTIM.md"],
              sorted(p.name for p in (c / "ai" / "topic").iterdir()))

    group("I4 专项：全仓物理删除调用点审计（白名单）")
    found = audit_delete_sites()
    flat = {(rel, kind): len(lines) for (rel, kind), lines in found.items()}
    print("  --- 审计表（rel, 调用类型, 次数, 行号） ---")
    for (rel, kind), lines in sorted(found.items()):
        verdict = "白名单内" if (rel, kind) in AUDIT_ALLOWED else "白名单外"
        print(f"  {rel:38s} {kind:12s} x{len(lines)}  L{lines}  [{verdict}]")
    missing = {k: v for k, v in AUDIT_ALLOWED.items() if flat.get(k, 0) != v}
    extra = {k: v for k, v in flat.items() if k not in AUDIT_ALLOWED}
    check("I4 无白名单外的物理删除/搬移调用点", extra == {}, extra)
    check("I4 白名单无腐烂条目（计数与现状一致）", missing == {},
          f"expected={ {k: AUDIT_ALLOWED[k] for k in missing} } actual={ {k: flat.get(k, 0) for k in missing} }")


# ---------------------------------------------------------------- I5
def test_i5() -> None:
    group("I5 分类学权威在 _meta/taxonomy.json，代码字典仅兜底")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        c = seed(root)
        tax0 = store.load_taxonomy(c)
        check("I5 无 JSON 时回退到代码内置字典（baike→百科）",
              tax0["domains"].get("baike") == "百科", tax0["domains"].get("baike"))

        meta = c / "_meta"
        meta.mkdir()
        (meta / "taxonomy.json").write_text(json.dumps({
            "domains": {"ai": {"label": "人工智能甲", "hue": 7}},
            "subs": {"topic": "题目甲"},
        }, ensure_ascii=False), encoding="utf-8")
        tax1 = store.load_taxonomy(c)
        check("I5 JSON 里的域显示名生效（覆盖同一键）", tax1["domains"].get("ai") == "人工智能甲")
        check("I5 JSON 里的 hue 生效", tax1["hues"].get("ai") == 7)
        check("I5 JSON 里的子域显示名生效", tax1["subs"].get("topic") == "题目甲")
        check("I5 JSON 未声明的键仍用代码缺省（兜底生效）",
              tax1["domains"].get("baike") == "百科" and tax1["subs"].get("pitfalls") == "踩坑")

        # 运行中的 app 认到新标签（不是只有函数层认）
        dt = json.loads(create_app(root).test_client().get("/api/dir/tree").get_data(as_text=True))
        labels = [d.get("label") for d in dt.get("domains", [])]
        check("I5 /api/dir/tree 输出新域显示名", "人工智能甲" in labels, labels)

        # JSON 损坏时不得炸，回退内置缺省
        (meta / "taxonomy.json").write_text("{ 这不是 json", encoding="utf-8")
        os.utime(meta / "taxonomy.json", (time_now(), time_now()))
        tax2 = store.load_taxonomy(c)
        check("I5 JSON 损坏时静默回退内置缺省（不抛异常）", tax2["domains"].get("baike") == "百科")

        defs = [f.name for f in (ROOT / "app").glob("*.py")
                if re.search(r"^DOMAIN_LABELS\s*=", f.read_text(encoding="utf-8"), re.M)]
        check("I5 域字典全仓只有 store.py 一处定义（无第二份权威）", defs == ["store.py"], defs)

        # 搜索浮层的域筛选钮以前是**模板里手抄的第三份域清单**（taxonomy.json 与
        # store.DOMAIN_LABELS 之外），键名一漂移点了就是 0 结果 —— 2026-09-24 实测
        # 「AI 资产」发 domain=ai 而 JSON 里的键是 ai-assets（台账 §6 第 27 行）。
        # 2026-09-25 起 base.html 改成 {% for k, lab in LABELS.items() %} 派生，门禁口径跟着换：
        #   ① 模板里不许再出现"域字面量 data-scope"（只准 {{ k }} 与 fav/unmastered 两个特殊值）；
        #   ② JSON 的 "search": false 必须真被 load_taxonomy 读成 search_hidden ——
        #      否则恒 0 的钮会随派生一起复活（小说域全是 .txt/.epub，FTS 不收）。
        # 只读模板与 taxonomy 元数据，不读任何语料正文。
        tpl = (ROOT / "app" / "templates" / "base.html").read_text(encoding="utf-8")
        literal = [m for m in re.findall(r'data-scope="([^"{}]*)"', tpl)
                   if m and m not in {"fav", "unmastered"}]
        check("I5 浮层域钮无第二份硬编码清单（模板里只准派生 + fav/unmastered）",
              not literal, f"literal={literal}")
        tax_json = json.loads((ROOT / "content" / "_meta" / "taxonomy.json")
                              .read_text(encoding="utf-8"))
        want_hidden = {k for k, v in tax_json["domains"].items() if v.get("search") is False}
        got_hidden = store.load_taxonomy(ROOT / "content")["search_hidden"]
        check("I5 JSON 的 search:false 被 load_taxonomy 读成 search_hidden",
              got_hidden == want_hidden, f"got={sorted(got_hidden)} want={sorted(want_hidden)}")


def time_now() -> float:
    import time
    return time.time() + 5  # 显式推后 mtime，确保 mtime 缓存失效（避免同秒写覆盖）


# ---------------------------------------------------------------- I6
def test_i6() -> None:
    group("I6 frontmatter 只存身世元数据（阅读统计走 indexes/）")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        c = seed(root)
        cl = create_app(root).test_client()

        # 走一遍所有会写 frontmatter 的接口，再统一收口检查磁盘上的键
        cl.post("/api/save", json={"path": "ai/topic/NEW.md", "content": "无 fm 的新文档\n"})
        cl.post("/api/save", json={"path": "ai/topic/A.md", "content": DOC_A})
        cl.post("/api/favorite", json={"path": "ai/topic/A.md"})
        cl.post("/api/tags", json={"path": "ai/topic/A.md", "op": "add", "tags": ["新标签"]})
        cl.post("/api/docmark", json={"path": "ai/topic/A.md", "mark": "read", "on": True})

        keys: dict = {}
        for f in sorted(c.rglob("*.md")):
            if f.name.endswith(".notes.md"):
                continue
            fm, _ = store.parse_frontmatter(f.read_text(encoding="utf-8"))
            for k in fm:
                keys.setdefault(k, []).append(f.relative_to(c).as_posix())
        check("I6 磁盘 frontmatter 键全部在白名单内", set(keys) <= FM_WHITELIST, keys)
        new_fm, _ = store.parse_frontmatter((c / "ai" / "topic" / "NEW.md").read_text(encoding="utf-8"))
        check("I6 新建文档补的 stamp 恰好是白名单键集",
              set(new_fm) == {"title", "tags", "source", "collected", "status"}, new_fm)

        # 静态：行级手术接口的键名参数也只能是白名单键
        bad = []
        for f in sorted((ROOT / "app").glob("*.py")):
            src = f.read_text(encoding="utf-8")
            for pat in (r"set_fm_scalar\(\s*[^,]+,\s*\"([^\"]+)\"", r"toggle_fm_bool\(\s*[^,]+,\s*\"([^\"]+)\""):
                for k in re.findall(pat, src):
                    if k not in FM_WHITELIST:
                        bad.append(f"{f.name}:{k}")
        check("I6 行级手术（set_fm_scalar/toggle_fm_bool）只用白名单键", bad == [], bad)

        # 核心：阅读统计不得污染语料（一个字节都不能动）
        doc = c / "ai" / "topic" / "A.md"
        before = doc.read_bytes()
        for ev in ("open", "read_minute", "finish"):
            cl.post("/api/track", json={"path": "ai/topic/A.md", "event": ev, "seconds": 60})
        check("I6 阅读事件不改变语料文件字节", doc.read_bytes() == before)
        check("I6 阅读统计落在 indexes/reading.db（派生库而非 frontmatter）",
              (root / "indexes" / "reading.db").is_file())
        check("I6 语料 frontmatter 未混入阅读统计键",
              not ({"read", "read_minute", "read_count", "views", "last_read"} &
                   set(store.parse_frontmatter(doc.read_text(encoding="utf-8"))[0])))


# ---------------------------------------------------------------- I7
def test_i7() -> None:
    group("I7 切块/分词变更必须递增 RAG_CODE_VERSION（静态检查自测）")
    spec = importlib.util.spec_from_file_location("crv", str(ROOT / "scripts" / "check_rag_version.py"))
    crv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(crv)

    L = chr(10)
    src = (L.join([
        'RAG_CODE_VERSION = "3"', "", "def _flush(buf, heading, out):",
        '    out.append({"t": x})', "", "def markdown_split(md_text):", "    chunks = []",
        "    for line in md_text.split(y):", "        chunks.append(line)", "    return chunks",
        "", "def rag_status(store):", '    return {"ok": True}',
    ]) + L)
    chunk_hunk = (L.join(["@@ -6,3 +6,4 @@", "     chunks = []", "     for line in md_text.split(y):",
                          "+        line = line.strip()", "         chunks.append(line)"]) + L)
    bump_hunk = (L.join(["@@ -1,2 +1,2 @@", '-RAG_CODE_VERSION = "3"', '+RAG_CODE_VERSION = "4"']) + L)
    other_hunk = (L.join(["@@ -13,2 +13,3 @@", " def rag_status(store):",
                          "+    store = store or None", '     return {"ok": True}']) + L)

    r1 = crv.analyze(src, src, chunk_hunk)
    check("I7 命中切块函数体且未递增版本 → 拒绝", r1["ok"] is False and r1["hits"] == ["markdown_split"], r1)
    r2 = crv.analyze(src, src, bump_hunk + chunk_hunk)
    check("I7 命中切块函数体且递增大版本 → 放行", r2["ok"] is True, r2)
    r3 = crv.analyze(src, src, other_hunk)
    check("I7 只改非目标函数 → 放行（不误伤）", r3["ok"] is True and r3["hits"] == [], r3)
    r4 = crv.analyze(src, src, bump_hunk)
    check("I7 只动版本号本身 → 放行", r4["ok"] is True, r4)
    r5 = crv.analyze("def broken(:", "def broken(:", chunk_hunk)
    check("I7 源码语法错误 → 判定为无法验证（拒绝，而非静默放行）",
          r5["ok"] is False and r5.get("parse_failed") is True, r5)

    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_rag_version.py")],
                       cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=120)
    # 只断言"可运行、不崩、给出明确判定"——不断言 exit 0：工作区恰好改了 rag.py 时
    # 它本就该拒绝，那种情况由 pre-commit 的 rag-version 步骤报出来，不是本测试的失败。
    check("I7 脚本对真实仓库可运行且给出明确判定（不崩溃）",
          r.returncode in (0, 1) and "Traceback" not in (r.stdout + r.stderr)
          and ("[rag-version]" in r.stdout), r.stdout + r.stderr)


# ---------------------------------------------------------------- I8
def test_i8() -> None:
    group("I8 不依赖 cwd（绝对路径直启 + 陌生工作目录）")
    with tempfile.TemporaryDirectory() as td:
        foreign = Path(td) / "somewhere-else"
        foreign.mkdir()
        kb_root = Path(td) / "kb"
        kb_root.mkdir()
        env = dict(os.environ, KB_ROOT=str(kb_root))
        r = subprocess.run([sys.executable, str(ROOT / "app" / "app.py"), "--import-check"],
                           cwd=str(foreign), capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=env, timeout=180)
        check("I8 从项目根之外以绝对路径直启 --import-check 通过", r.returncode == 0,
              f"rc={r.returncode} out={r.stdout[-300:]} err={r.stderr[-300:]}")
        check("I8 输出 IMPORT-CHECK OK", "IMPORT-CHECK OK" in r.stdout, r.stdout[-200:])
        check("I8 陌生 cwd 下未在 cwd 里生成任何文件",
              list(foreign.iterdir()) == [], [p.name for p in foreign.iterdir()])


# ---------------------------------------------------------------- I9
# 只测"闸本身灵不灵"，不在这里扫真实 content/：语料扫描归 scripts/check_frontmatter.py
# 与 publish_site.py，测试若绑语料，并发分片会把它顶红（learn smoke 的前车之鉴）。
def test_i9() -> None:
    group("I9 frontmatter 严格 YAML 门禁（scripts/check_frontmatter.py）")
    spec = importlib.util.spec_from_file_location(
        "cfm", str(ROOT / "scripts" / "check_frontmatter.py"))
    cfm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cfm)
    scan = cfm.scan_frontmatter

    # 每条都是能让 js-yaml 直接抛错的形态；第一条是 2026-09-25 的真实事故
    bad = {
        "冒号后缺空格": 'tags: [a]\ntitle:"写作"\nsource_path: "x"\n',
        "引号未闭合": 'title: "写作\n',
        "值里裸冒号": "title: 时间: 10点\n",
        "键重复": "title: a\ntitle: b\n",
        "顶层行无冒号": "title: a\n随便一行\n",
        "缩进用Tab": "head:\n\t- meta\n",
    }
    for name, fm in bad.items():
        check(f"I9 {name} 被拦下", bool(scan(fm)), fm)

    # 语料里真实存在的合法形态：注释 / 带冒号的引号值 / flow 序列 / 块标量 / 嵌套列表
    ok = ('# outline: [1,3]\n'
          'title: "带: 冒号的标题"\n'
          'tags: [前端, vue]\n'
          'description: >-\n'
          '  这段里有 冒号: 也不算\n'
          'head:\n'
          '  - - meta\n'
          '    - name: description\n'
          '      content: 任意文本\n')
    check("I9 合法复杂头不误杀", scan(ok) == [], scan(ok))

    with tempfile.TemporaryDirectory() as td:
        plain = Path(td) / "plain.md"
        plain.write_text("正文里没有 fm\n", encoding="utf-8")
        check("I9 无 frontmatter 的文件不报错", cfm.lint_file(plain) == [])
        broken = Path(td) / "broken.md"
        broken.write_text("---\ntitle: a\n正文\n", encoding="utf-8")
        check("I9 缺闭合 --- 被拦下", bool(cfm.lint_file(broken)),
              cfm.lint_file(broken))
        good = Path(td) / "good.md"
        good.write_text('---\ntitle: "好"\ntags: [a]\n---\n\n正文\n', encoding="utf-8")
        check("I9 正常文件整链放行", cfm.lint_file(good) == [], cfm.lint_file(good))


def main() -> int:
    for fn in (test_i1, test_i2, test_i3, test_i4, test_i5, test_i6, test_i7, test_i8, test_i9):
        fn()
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
