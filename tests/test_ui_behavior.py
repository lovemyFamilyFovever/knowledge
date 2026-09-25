# -*- coding: utf-8 -*-
"""知库 UI 行为回归（第 13 套）—— 台账 §2 那些控件的"点了到底有没有反应"。

运行：python tests/test_ui_behavior.py   （缺 node/Chrome 自动 SKIP）
      python tests/test_ui_behavior.py mock   开发期单跑某一探针

为什么单独一套而不是塞进 P5：P5 的判据是"和上次像素一样吗"，而"点下去有没有反应"是
另一类问题 —— 重叠、恒 0 结果、点了没反应这类缺陷在像素基线里是**稳定地错**（台账 §6 第 29 行）。
本套也不与 test_js_props 合并：那套管的是**解析器**（zip/txt/切块），语义不同，混在一起
会让"改了书库解析"和"改了按钮行为"都顶起同一套红。

已把台账 §2 的 33 行从"控件在位"升到 `E2E`（轮次 24 起，每轮加一组探针）：
  轮次 24（9 行）问吧 / 空态新建 / #ed-del / crumb 删除 / [[ 双链补全（CM + textarea 两支）
                / 标签补全 / mermaid 放大 / 收件箱 del+purge / 标签页看板抽屉
  轮次 25（9 行）一级导航 4 项 + brand→总览 + 收藏 + 标签 + 治理 + 收件箱入口（**点了真的换页**）
  轮次 26（7 行）设置抽屉·阅读排版那一组（CSS 变量 + localStorage + 恢复默认 + 刷新后仍生效）
  轮次 27（2 行）收件箱批量归档 / 单篇 move / 忽略（真落盘 + 规则对下次扫描生效）
  轮次 28（6 行）首页今日卡 / 术语过滤 / 术语分桶·子域·内联详情 / 串学漫游 / 模拟面试+精确命中
                / 治理孤儿折叠·豁免 —— 顺手抓到「模拟面试从上线起就没出过题」（§6 第 35 行）

护栏（AGENTS 不变量与手册）：
  · 只打 tempfile 里的合成语料，**绝不读写真实 content/**；写类断言全部落在临时根上；
  · 端口现挑，绝不占用户的 5001/5000/5031；
  · **不联网**：探针跑之前把 KB_AI_API_KEY 从环境里摘掉，让 /api/ask 恒走 503 降级分支
    （否则这台机器哪天配了 key，本套就会真的去请求外部 LLM）；
  · 语料一律合成，不读 content/小说（禁区）。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from urllib.parse import quote  # noqa: E402

from _tmpapp import (chrome_path, free_port, kill_instance, node_available,  # noqa: E402
                     port_open, start_instance)
import test_ui_regress as p5  # noqa: E402  复用它的合成语料与 taxonomy，不造第二份

QA = ROOT / ".qa"
# 开发期单跑某一探针用（`python tests/test_ui_behavior.py nav`）；门禁不带参数 = 全跑
ONLY = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
PORT = None
passed = 0
failed = 0
FAILURES = []


def _safe(s):
    """控制台是 GBK，样本/页面文本里的 emoji（💡）与非常规字符会把 print 崩掉
    （P5/P3-B 都踩过）。一律按 stdout 的编码 replace 掉，绝不抛异常。"""
    s = str(s)
    enc = getattr(sys.stdout, "encoding", None) or "ascii"
    try:
        return s.encode(enc, "replace").decode(enc, "replace")
    except (LookupError, UnicodeEncodeError, ValueError):
        return s.encode("ascii", "replace").decode("ascii", "replace")


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS {_safe(name)}")
    else:
        failed += 1
        FAILURES.append(name)
        print(f"  FAIL {_safe(name)} {_safe(extra)}")


# ---------------------------------------------------------------- 合成语料补充
# P5 的语料是为"像素确定"挑的，本套要的是"控件存在且可点"，所以在它之上再加三样：
#   · 一篇**预渲染**的 mermaid HTML（内联 <svg>，不引 CDN —— 本仓库不联网），
#     用来打 /raw 的放大浮层；
#   · 两个收件箱条目，其中一个带 sidecar `.notes.md` 与同名 `.html` 挂件，
#     用来验 purge 是否把三件一起物理删掉。
EXTRA = {
    "content/ui-r/notes/mermaid样本.html": """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>Mermaid 样本</title></head><body>
<div class="mermaid"><svg viewBox="0 0 120 40" width="120" height="40" role="img">
<rect width="110" height="30" x="4" y="4" fill="#dbeafe" stroke="#1d4ed8"></rect>
<text x="14" y="24" font-size="12">A 到 B</text></svg></div>
<p>上面这张图是预渲染的内联 SVG，用来验 /raw 注入的点击放大浮层。</p>
</body></html>
""",
    "content/_inbox/待丢弃条目.md": "---\ntitle: 待丢弃条目\n---\n\n收件箱 del 按钮的靶子。\n",
    "content/_inbox/待彻底删除条目.md": "---\ntitle: 待彻底删除条目\n---\n\npurge 按钮的靶子。\n",
    "content/_inbox/待彻底删除条目.md.notes.md": "---\ntitle: 待彻底删除条目 的备注\n---\n\n旁挂备注。\n",
    "content/_inbox/待彻底删除条目.html": "<!DOCTYPE html><html><body><p>同名挂件美化版</p></body></html>\n",
    # 收件箱"归档 / 忽略"两条动作的靶子（探针 8 的第三段用）：
    # 两篇走批量归档、一篇走单篇 move、一个目录走忽略、一个根级文件走"没有目录可忽略"的护栏。
    "content/_inbox/归档样本甲.md": "---\ntitle: 归档样本甲\n---\n\n批量归档靶子甲。\n",
    "content/_inbox/归档样本乙.md": "---\ntitle: 归档样本乙\n---\n\n批量归档靶子乙。\n",
    "content/_inbox/单篇归档.md": "---\ntitle: 单篇归档\n---\n\n单篇 move 靶子。\n",
    "content/_inbox/开发产物/说明.md": "---\ntitle: 开发产物说明\n---\n\n整个目录要被忽略。\n",
    "content/_inbox/根级忽略.md": "---\ntitle: 根级忽略\n---\n\n根级文件，没有目录可忽略。\n",
    # 美化版 HTML 里常见的公网 CDN 引用：`_rewrite_html_assets` 必须把它们换成仓库内的
    # vendored 副本（离线可用是这仓库的硬要求）。这一篇同时补上台账 §5 那一格
    # （`routes_pages._rewrite_html_assets` 此前"模块私有、无人测"）。
    "content/ui-r/notes/cdn样本.html": """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>CDN 样本</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
</head><body><div class="mermaid-code">graph TD;A--&gt;B;</div>
<script src="./_shared/js/mermaid.min.js"></script></body></html>
""",
    # 第二个 baike 词条，专为**串学漫游**造一条真的能走通的路径：
    # `cards.py::_related_of` 只认 `## 相关术语` 区块里的 [[双链]]（正文别处的不算），
    # 所以这里既挂一个**有卡片**的目标（向量数据库 → path 里的真节点），
    # 也挂一个**没有卡片**的目标（→ dead_ends，页面上渲染成虚线"无卡片"）。
    "content/baike/term/倒排索引.md": """---
title: 倒排索引
source: knowledge
collected: 2026-01-12
tags: [检索]
status: stable
---

# 倒排索引

## 定义

**一句话定义：** 按词建表、用词直接定位到含它的文档列表的索引结构。

## 常见误区

**误区：** 倒排索引只能做精确匹配。

**正解：** 前缀、模糊与 BM25 排序都建立在它之上，和向量检索是互补关系。

## 相关术语

- [[向量数据库]]
- [[尚不存在的术语]]
""",
    # 第三个词条**故意放进另一个子域**（baike/db）：术语页的「子域切换」只有一个子域时
    # 点了等于没点，断不出"只剩该子域"这件事。
    "content/baike/db/布隆过滤器.md": """---
title: 布隆过滤器
source: knowledge
collected: 2026-01-13
tags: [检索]
status: stable
---

# 布隆过滤器

## 定义

**一句话定义：** 用若干个哈希位图判断元素是否可能存在，说"不存在"一定准、说"存在"可能误判。

## 分析

代价是误判率与位图大小此消彼长，所以它只做第一道闸，不做判据。
""",
}

# 治理页「展开全部」的靶子：`governance.js::renderOrphans` 的折叠线写死在 **30 篇**
# （`items.slice(0, 30)` + `hidden = items.length <= 30`），而 P5 的合成语料一共才 6 篇
# —— 那一档**从来没能进过**，所以钮的展开/收起态一直无人断言。补 34 篇无入链 md。
ORPHAN_COUNT = 34
EXTRA.update({
    f"content/ui-r/orphans/孤{i:02d}.md": (
        "---\ntitle: 孤儿样本%02d\n---\n\n没有任何文档链向它，"
        "用来把孤儿列表撑过 30 篇的折叠线。\n" % i)
    for i in range(1, ORPHAN_COUNT + 1)
})


def build_root(tmp: Path):
    p5.build_corpus(tmp)                      # 同一份合成语料，不抄第二份
    for rel, content in EXTRA.items():
        f = tmp / rel.replace("/", os.sep)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------- CDP 驱动
# 为什么用 geom.mjs 而不是 evalcdp.mjs：evalcdp 的视口只有 ~764px 宽，
# 右栏（标签页签、补全浮层的锚点）在那一档里**根本没被渲染** ——
# 实测 `#tag-inputrow` 的 rect 全 0、input.focus() 之后 activeElement 仍是 BODY，
# 于是"浮层弹不出来"其实是测试环境把面板挤没了，不是产品缺陷。
# 本套一律钉在 1600×900（真人桌面窗口），每档求值前留重排时间。
PROBE_WIDTH = 1600


def run_expr(url, js, width=PROBE_WIDTH, click="", click_wait=1800, init=""):
    """在指定视口宽度下求值一个 async 表达式（表达式须 return 一个 JSON 字符串）。

    `click` 非空时先点这些选择器（逗号分隔）再求值 —— 点击引发整页导航也没关系，
    geom.mjs 等的是 readyState，求值发生在导航之后的新文档里，所以"点了到底换没换页"
    能直接断出来（这是本套能覆盖"一级导航"那 8 行的关键）。
    `init` 非空时在页面任何脚本执行**之前**注入（验"刷新后偏好仍然生效"用）。
    """
    QA.mkdir(parents=True, exist_ok=True)
    f = QA / "behavior-expr.js"
    f.write_text(js, encoding="utf-8")
    env = dict(os.environ)
    if click:
        env["KB_GEOM_CLICK"] = click
        env["KB_GEOM_CLICK_WAIT"] = str(click_wait)
    if init:
        env["KB_GEOM_INIT"] = init
    r = subprocess.run(
        ["node", str(ROOT / "scripts" / "agent" / "geom.mjs"), url, str(width), "@" + str(f)],
        cwd=str(ROOT), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300, env=env)
    lines = [l for l in (r.stdout or "").splitlines() if l.strip().startswith("{")]
    if not lines:
        check("CDP 探针有回值", False, f"rc={r.returncode} {(r.stdout or '')[:160]} {(r.stderr or '')[-200:]}")
        return {}
    try:
        row = json.loads(lines[-1])
    except ValueError as e:
        check("CDP 探针返回值能解析", False, f"{e} / {lines[-1][:200]}")
        return {}
    if "error" in row:
        check("CDP 探针表达式执行无异常", False, _safe(row))
    return row


PRELUDE = """(async () => {
  const out = {};
  const q = s => document.querySelector(s);
  const txt = s => ((q(s) && (q(s).innerText || q(s).textContent)) || '').replace(/\\s+/g, ' ').trim();
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const cls = (s, c) => !!(q(s) && q(s).classList.contains(c));
"""

# ---------------------------------------------------------------- 探针 0：一级导航与收件箱徽标
# 口径写清楚（免得后来人以为每行都做了点击）：9 个导航项是**同一个机制**（服务端渲染的
# `<a href>`），所以"点了真的换页 + 换页后高亮态跟着变"用一次真点击代表（复习），
# 而每一行各自的**目的地正确性**（页面渲染出该页特征元素、且只有它自己带 .on）
# 逐行用 HTTP 面断言 —— 那才是每行真正不同的部分。
NAV_TARGETS = [
    # (href, 标题前缀, 行名, 该页特征元素, 该页上应当带 .on 的导航项)
    ("/", "知库", "阅读", 'id="tree"', ["/"]),
    ("/review", "今日复习", "复习", 'id="kb-learn"', ["/review"]),
    ("/glossary", "术语百科", "术语", 'id="kb-glossary"', ["/glossary"]),
    # 统计页在**没有阅读数据的实例里**只渲染骨架：KPI 卡、图表、复习卡覆盖区全部有条件
    # （has_chart 为假时连 canvas 都不存在）。所以特征元素取那张永远在的数据载荷
    # `#st-daily-data` —— 它证明"这页真的按 stats.html 渲染了"，而不是被别的模板顶替。
    # 图表本体的覆盖缺口另记在台账 §14.3 第 7 条。
    ("/stats", "阅读统计", "统计", 'id="st-daily-data"', ["/stats"]),
    ("/favorites", "收藏", "收藏", 'class="result fav-card"', ["/favorites"]),
    ("/tags", "标签", "标签", 'id="tag-cloud"', ["/tags"]),
    ("/governance", "治理驾驶舱", "治理", 'id="gov-scan-btn"', ["/governance"]),
    # 收件箱与总览是**图标入口**（顶栏没有对应的文字导航项），所以 .on 恒空。
    # 这不是断言写松了 —— 现状就是"从图标进这两页时，一级导航没有任何一项高亮"，
    # 要不要给它算归属属产品决定，本条只把事实钉住（改了这个行为，这条会红）。
    ("/inbox", "收件箱", "收件箱", 'id="inbox-kanban"', []),
    ("/home", "总览", "brand→总览", 'id="view-home"', []),
]

NAV_BEFORE_JS = PRELUDE + """
  out.path = location.pathname;
  out.title = document.title;
  const a = q('.topnav a[href="/review"]');
  out.link_present = !!a;
  out.on_now = [...document.querySelectorAll('.topnav .tn.on')].map(x => x.getAttribute('href'));
  out.learn = !!q('#kb-learn');
  return JSON.stringify(out);
})()"""

NAV_AFTER_JS = PRELUDE + """
  out.path = location.pathname;
  out.title = document.title;
  out.on_now = [...document.querySelectorAll('.topnav .tn.on')].map(x => x.getAttribute('href'));
  out.learn = !!q('#kb-learn');
  return JSON.stringify(out);
})()"""


def probe_nav(base, tmp):
    print("== 0 一级导航（点了换页 + 高亮跟着变）与收件箱徽标 ==")
    before = run_expr(base + "/", NAV_BEFORE_JS)
    # 第二趟：同一个 URL 起步，由 geom.mjs 先点「复习」再求值 —— 求值发生在导航之后的新文档里
    after = run_expr(base + "/", NAV_AFTER_JS, click=".topnav a[href='/review']")
    check("导航：出发页是阅读页、高亮在「阅读」、没有复习主体",
          before.get("path") == "/" and before.get("on_now") == ["/"]
          and before.get("learn") is False, before)
    check("导航：阅读页上「复习」这个链接在位", before.get("link_present") is True, before)
    check("导航：点「复习」之后浏览器真的换了页（pathname=/review）",
          after.get("path") == "/review", after)
    check("导航：换页后标题跟着变（今日复习 · 知库）",
          str(after.get("title") or "").startswith("今日复习"), after.get("title"))
    check("导航：换页后高亮态从「阅读」搬到「复习」", after.get("on_now") == ["/review"], after)
    check("导航：目标页真的渲染出自己的主体（#kb-learn）", after.get("learn") is True, after)

    import re as _re
    for href, title, name, marker, want_on in NAV_TARGETS:
        body = urllib_get(base + href)
        # 高亮项的 class 有两种写法：文字导航是 `class="tn on"`，动作项是 `class="tn tn-act on"`
        # —— 所以匹配的是"类列表里有 on"，不是某个固定串（固定串会把后一种全判成没高亮）。
        on = [h for cls, h in _re.findall(r'<a class="([^"]*)"[^>]*href="([^"]+)"', body)
              if "on" in cls.split() and "tn" in cls.split()]
        check(f"导航 {name}：{href} 渲染出该页特征元素", marker in body, body[:120])
        check(f"导航 {name}：{href} 的高亮归属是 {want_on}（现状：图标入口两页无高亮）",
              on == want_on, f"on={on} want={want_on}")
        check(f"导航 {name}：{href} 的标题前缀是「{title}」",
              f"<title>{title}" in body or f"{title} · 知库" in body, body[:160])

    # 收件箱徽标：顶栏那个数字必须是**真在 _inbox 里的篇数**。三处口径一起断，
    # 因为"徽标 vs 列表 vs 磁盘"两两不同都算界面对自己撒谎（本轮就是这么抓到旁挂混进来的，
    # 见 §6 第 33 行）。
    shell = urllib_get(base + "/")
    inbox_html = urllib_get(base + "/inbox")
    badge = _re.search(r'href="/inbox"[^>]*>.*?<span class="n">(\d+)</span>', shell, _re.S)
    rows = _re.findall(r'<div class="kan-item"[^>]*data-rel="([^"]+)"', inbox_html)
    real = sorted(p.relative_to(tmp / "content" / "_inbox").as_posix()
                  for p in (tmp / "content" / "_inbox").rglob("*")
                  if p.is_file() and not p.name.endswith(".notes.md")
                  and not p.name.startswith(".") and p.suffix.lower() not in (".txt",))
    check("收件箱徽标：顶栏 badge == 收件箱列表行数",
          badge is not None and int(badge.group(1)) == len(rows),
          f"badge={badge.group(1) if badge else None} rows={len(rows)}")
    check("收件箱徽标：列表行数 == 磁盘上 _inbox 的真篇数",
          sorted(r.replace("_inbox/", "") for r in rows) == real,
          f"rows={sorted(r.replace('_inbox/', '') for r in rows)} disk={real}")
    check("收件箱列表：备注旁挂 .notes.md 不算待归档条目（与分类树 B2 同一口径）",
          not any(r.endswith(".notes.md") for r in rows), rows)


# ---------------------------------------------------------------- 探针 10：阅读排版偏好
# 这一组是"改了到底生效没有"最典型的地方：七个控件各自写一个 CSS 变量到 documentElement，
# 偏好落 localStorage，刷新后要仍然生效，恢复默认要能全部退回。历史上 B18 就是"签名失效"
# 让偏好改了当下看起来有效、刷新就回退 —— 所以**驱动**与**刷新后应用**必须分开各断一次。
PREF_CASES = [
    # (偏好键, 控件 id, 事件, 设的值, CSS 变量, 期望变量值, 期望 output 文本)
    ("scale", "kb-pref-scale", "input", "1.45", "--kb-fs-scale", "1.45", "1.45×"),
    ("line", "kb-pref-line", "input", "2.1", "--kb-line", "2.1", "2.10"),
    ("h1s", "kb-pref-h1s", "input", "2.2", "--kb-h1-size", "2.2rem", "2.20"),
    ("h2s", "kb-pref-h2s", "input", "1.6", "--kb-h2-size", "1.6rem", "1.60"),
    ("h3s", "kb-pref-h3s", "input", "1.2", "--kb-h3-size", "1.2rem", "1.20"),
    ("code", "kb-pref-code", "input", "16", "--kb-code-size", "16px", "16px"),
    ("halign", "kb-pref-halign", "change", "left", "--kb-h1-align", "left", None),
    ("font", "kb-pref-font", "change", "serif", "--kb-font", "var(--f-disp)", None),
]
PREF_DEFAULTS = {"--kb-fs-scale": "1", "--kb-line": "1.75", "--kb-h1-size": "1.55rem",
                 "--kb-h2-size": "1.3rem", "--kb-h3-size": "1.12rem", "--kb-code-size": "13px",
                 "--kb-h1-align": "center", "--kb-font": "var(--f-body)"}

PREF_JS = PRELUDE + """
  const CASES = __CASES__;
  const VARS = CASES.map(c => c[4]);
  // 读**内联**写的值（apply() 就是写到 documentElement.style）：getComputedStyle 会把
  // var(--f-body) 展开成真实字体栈，那已经不是偏好写进去的东西了（第一轮就因此误判"字体没生效"）。
  const cs = () => document.documentElement.style;
  const readVars = () => {
    const o = {};
    for (const v of VARS) o[v] = cs().getPropertyValue(v).trim();
    return o;
  };
  out.vars_before = readVars();
  q('#kb-settings-btn').click();
  await sleep(700);
  out.drawer_open = !!q('#kb-set-tabs');
  const tab = q('#kb-set-tabs [data-sec="type"]');
  out.tab_present = !!tab;
  if (tab) tab.click();
  await sleep(400);
  const sec = q('section[data-sec="type"]');
  out.type_section_shown = !!sec && sec.hidden === false;
  out.driven = {};
  for (const [key, id, ev, val, cssVar, want, outText] of CASES) {
    const el = q('#' + id);
    if (!el) { out.driven[key] = { missing: true }; continue; }
    el.value = val;
    el.dispatchEvent(new Event(ev, { bubbles: true }));
    await sleep(220);
    const o = q('#' + id + '-o');
    out.driven[key] = {
      var_now: cs().getPropertyValue(cssVar).trim(),
      out_now: o ? (o.textContent || '').trim() : null,
      ls: (JSON.parse(localStorage.getItem('kb-readpref') || '{}')[key] !== undefined)
          ? String(JSON.parse(localStorage.getItem('kb-readpref'))[key]) : null,
    };
  }
  // 恢复默认：所有变量必须退回 PREF_DEF（style.css [8] 区的原始硬值），localStorage 也要写回默认
  const rb = q('#kb-pref-reset');
  out.reset_btn = !!rb;
  if (rb) rb.click();
  await sleep(500);
  out.vars_after_reset = readVars();
  // 强制动效：勾一下，localStorage 要落 '1'（刷新才生效，所以这里只断写入）
  const mb = q('#kb-pref-motion');
  out.motion_present = !!mb;
  if (mb) { mb.checked = true; mb.dispatchEvent(new Event('change', { bubbles: true })); }
  await sleep(300);
  out.motion_ls = localStorage.getItem('kb-force-motion');
  // 读取系统字体：无头环境没有 queryLocalFonts，必须走"提示不支持"的降级而不是静默
  const fb = q('#kb-pref-fontsys');
  out.fontsys_btn = !!fb;
  out.has_local_fonts = !!window.queryLocalFonts;
  if (fb) fb.click();
  await sleep(600);
  out.fontsys_toast = txt('#toast');
  out.fontsys_optgroups = document.querySelectorAll('#kb-pref-font optgroup').length;
  return JSON.stringify(out);
})()"""

PREF_RELOAD_JS = PRELUDE + """
  const cs = document.documentElement.style;   // 同 PREF_JS：读 apply() 写的内联原值
  out.vars = {
    scale: cs.getPropertyValue('--kb-fs-scale').trim(),
    line: cs.getPropertyValue('--kb-line').trim(),
    h1: cs.getPropertyValue('--kb-h1-size').trim(),
    code: cs.getPropertyValue('--kb-code-size').trim(),
    halign: cs.getPropertyValue('--kb-h1-align').trim(),
    font: cs.getPropertyValue('--kb-font').trim(),
  };
  const h1 = q('.a-body h1, #article h1, .sec-card h2');
  out.h1_align_applied = h1 ? getComputedStyle(h1).textAlign : null;
  out.ls = localStorage.getItem('kb-readpref');
  return JSON.stringify(out);
})()"""


def probe_prefs(base):
    print("== 10 阅读排版偏好（七个控件 + 恢复默认 + 刷新后仍然生效） ==")
    cases_json = json.dumps([[c[0], c[1], c[2], c[3], c[4], c[5], c[6]] for c in PREF_CASES])
    d = run_expr(base + "/doc/ui-r/notes/alpha.md", PREF_JS.replace("__CASES__", cases_json))
    check("排版偏好：设置抽屉能打开、且有「排版」分区", d.get("drawer_open") and d.get("tab_present"), d)
    check("排版偏好：切到「排版」后该分区可见（不是只换了按钮高亮）",
          d.get("type_section_shown") is True, d)
    before = d.get("vars_before") or {}
    check("排版偏好：没动过偏好时，八个变量等于 PREF_DEF（渲染零变化）",
          all(before.get(k) == v for k, v in PREF_DEFAULTS.items()),
          {k: (before.get(k), v) for k, v in PREF_DEFAULTS.items() if before.get(k) != v})
    driven = d.get("driven") or {}
    for key, _cid, _ev, _val, css_var, want, out_text in PREF_CASES:
        got = driven.get(key) or {}
        check(f"排版偏好 {key}：驱动控件后 CSS 变量真的变成 {want}",
              not got.get("missing") and got.get("var_now") == want, got)
        if out_text is not None:
            check(f"排版偏好 {key}：滑杆旁的读数同步更新为 {out_text}",
                  got.get("out_now") == out_text, got)
        check(f"排版偏好 {key}：写进了 localStorage（不写语料文件）",
                  got.get("ls") is not None, got)
    check("排版偏好：「恢复默认」把所有变量退回原值",
          d.get("reset_btn") and all((d.get("vars_after_reset") or {}).get(k) == v
                                    for k, v in PREF_DEFAULTS.items()),
          d.get("vars_after_reset"))
    check("强制动效：勾选写进 localStorage kb-force-motion",
          d.get("motion_present") and d.get("motion_ls") == "1",
          f"present={d.get('motion_present')} ls={d.get('motion_ls')!r}")
    # 「读取系统字体」在两种环境里走两条路：能枚举 → 往 select 里加分组；被拒/不支持 → 弹提示。
    # 无头 Chrome 是后者（有 window.queryLocalFonts，但调用被拒 → SecurityError → toast）。
    # 断言只要求"点了必须有反馈"，静默才算坏；两条分支都算通过，但必须显式说出走了哪条。
    check("读取系统字体：点了必有反馈（枚举出分组，或被拒时给失败提示），不许静默无反应",
          d.get("fontsys_btn") and (d.get("fontsys_optgroups", 0) >= 1
                                    or "失败" in (d.get("fontsys_toast") or "")
                                    or "不支持" in (d.get("fontsys_toast") or "")),
          {"api": d.get("has_local_fonts"), "groups": d.get("fontsys_optgroups"),
           "toast": d.get("fontsys_toast")})

    # 刷新后仍然生效：把偏好**预先写进 localStorage** 再加载页面，验 apply() 在启动时就应用
    seeded = json.dumps({"scale": 1.45, "line": 2.1, "h1s": 2.2, "h2s": 1.3, "h3s": 1.12,
                         "code": 16, "halign": "left", "font": "serif"})
    init = ("try{localStorage.setItem('kb-readpref', %s);}catch(e){}" % json.dumps(seeded))
    r = run_expr(base + "/doc/ui-r/notes/alpha.md", PREF_RELOAD_JS, init=init)
    v = r.get("vars") or {}
    check("排版偏好刷新后生效：正文字号/行高/一级标题/代码 都按 localStorage 应用",
          v.get("scale") == "1.45" and v.get("line") == "2.1"
          and v.get("h1") == "2.2rem" and v.get("code") == "16px", v)
    check("排版偏好刷新后生效：标题对齐与字体也应用（halign=left / font=serif）",
          v.get("halign") == "left" and v.get("font") == "var(--f-disp)", v)
    check("排版偏好真的落到渲染结果上：一级标题 text-align 是 start/left",
          (r.get("h1_align_applied") or "") in ("left", "start"), r.get("h1_align_applied"))


# ---------------------------------------------------------------- 探针 1：问吧
ASK_JS = PRELUDE + """
  const btn = q('button[onclick="showAsk()"]');
  out.btn_present = !!btn;
  if (btn) btn.click();
  await sleep(700);
  out.opened = !!q('#ask-in') && !!q('#ask-go') && !!q('#ask-body');
  out.cards = document.querySelectorAll('#ask-empty .ask-card').length;
  const inp = q('#ask-in'), go = q('#ask-go');
  inp.value = '什么是向量数据库';
  go.click();
  // pending 必须**同步**读：ask() 里 showPending() 在 `await fetch` 之前跑完，
  // 而本机 503 常在 150ms 内就返回 —— 先 sleep 再读会读到"已经撤掉"的那一侧（实测假红）。
  out.pending_seen = !!q('#ask-pending');
  out.empty_gone = !q('#ask-empty');
  out.me = txt('.ask-me');
  for (let i = 0; i < 70 && q('#ask-pending'); i++) await sleep(200);
  out.pending_gone = !q('#ask-pending');
  out.err = txt('.ask-err');
  out.reenabled = go.disabled === false;
  return JSON.stringify(out);
})()"""


def probe_ask(base):
    print("== 1 问吧 showAsk() ==")
    d = run_expr(base + "/doc/ui-r/notes/alpha.md", ASK_JS)
    check("问吧：顶栏按钮在位", d.get("btn_present") is True, d)
    check("问吧：点击后浮层开出 #ask-in/#ask-go/#ask-body", d.get("opened") is True, d)
    check("问吧：空态先渲染出 4 张推荐卡", d.get("cards") == 4, f"cards={d.get('cards')}")
    check("问吧：发出问题后进入 pending 态（#ask-pending 出现）", d.get("pending_seen") is True, d)
    check("问吧：发送后空态被撤下", d.get("empty_gone") is True, d)
    check("问吧：我说的话回显在气泡里", "什么是向量数据库" in (d.get("me") or ""), d.get("me"))
    check("问吧：响应落地后 pending 被移除（不残留转圈）", d.get("pending_gone") is True, d)
    check("问吧：无 key 时走 503 降级、给出 KB_AI_API_KEY 提示而不是空白",
          "KB_AI_API_KEY" in (d.get("err") or ""), d.get("err"))
    check("问吧：结束后发送钮重新可用", d.get("reenabled") is True, d)


# ---------------------------------------------------------------- 探针 2：双链补全
WIKILINK_JS = PRELUDE + """
  const SAMPLE = '参见 [[排版';
  q('#crumb [onclick="openEditor()"]').click();
  for (let i = 0; i < 40 && !(q('#editor') && q('#editor').classList.contains('show')); i++) await sleep(150);
  out.editor_open = !!(q('#editor') && q('#editor').classList.contains('show'));
  const ta = q('#ed-text');
  out.ta_present = !!ta;
  await sleep(700);   // KBED.attach() 在 openEditor 里跑，给 CM 一点接管时间
  out.cm_mode = !!(window.KBED && KBED.active && KBED.active());
  const boxOpen = () => { const b = q('div.wl-suggest'); return !!b && b.style.display !== 'none'; };
  const boxItems = () => { const b = q('div.wl-suggest'); return b ? b.querySelectorAll('.wl-item').length : 0; };
  const waitBox = async () => {
    for (let i = 0; i < 50; i++) {
      if (boxOpen() && boxItems() >= 1) return true;
      await sleep(150);
    }
    return false;
  };

  // ---- 分支 A：CodeMirror 接管（真用户在编辑器里走的就是这条）----
  const v = window.KBED.view;
  v.dispatch({ changes: { from: 0, to: v.state.doc.length, insert: SAMPLE },
               selection: { anchor: SAMPLE.length }, scrollIntoView: true });
  out.cm_box = await waitBox();
  out.cm_items = boxItems();
  out.cm_first = txt('.wl-suggest .wl-name');
  // 采纳走补全框自己的 mousedown 路径。CM 的 Enter 由 CM 内部 keymap 消费，
  // 合成 keydown 不可靠（实测不生效），所以键盘采纳放到分支 B 的 textarea 路径上验 ——
  // 两条分支各验一种真实输入方式，而不是假装一条覆盖了另一条。
  const it = document.querySelector('div.wl-suggest .wl-item[data-idx="0"]');
  if (it) it.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
  await sleep(500);
  out.cm_value = window.KBED.view.state.doc.toString();
  out.cm_closed = !boxOpen();

  // ---- 分支 B：textarea 回落（CM 未接管时 wikilink-suggest 绑的是原生事件）----
  window.KBED.detach();
  await sleep(300);
  out.ta_mode_after_detach = !(window.KBED.active && window.KBED.active());
  ta.focus();
  ta.value = SAMPLE;
  ta.setSelectionRange(ta.value.length, ta.value.length);
  ta.dispatchEvent(new Event('input', { bubbles: true }));
  out.ta_box = await waitBox();
  ta.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13,
                                                  bubbles: true, cancelable: true }));
  await sleep(500);
  out.ta_value = ta.value;
  out.ta_closed = !boxOpen();
  return JSON.stringify(out);
})()"""


def probe_wikilink(base):
    print("== 2 [[ 双链补全浮层（CM 分支 + textarea 回落分支） ==")
    d = run_expr(base + "/doc/ui-r/notes/alpha.md", WIKILINK_JS)
    check("双链补全：编辑器打开后 #ed-text 在位", d.get("editor_open") and d.get("ta_present"), d)
    check("双链补全：本次 A 分支跑的确实是 CM 接管（换分支会被这条报出来）",
          d.get("cm_mode") is True, d.get("cm_mode"))
    check("双链补全：CM 分支敲 [[ 后浮层弹出且有候选项",
          d.get("cm_box") and d.get("cm_items", 0) >= 1, d)
    check("双链补全：候选来自索引里的真标题（含「排版约定样本」）",
          "排版约定样本" in (d.get("cm_first") or ""), d.get("cm_first"))
    check("双链补全：CM 分支点候选把 [[名字]] 插回文档",
          "[[排版约定样本" in (d.get("cm_value") or "") and "]]" in (d.get("cm_value") or ""),
          d.get("cm_value"))
    check("双链补全：CM 分支采纳后浮层收起", d.get("cm_closed") is True, d)
    check("双链补全：detach 之后确实回到 textarea 分支（否则下面测的是空气）",
          d.get("ta_mode_after_detach") is True, d)
    check("双链补全：textarea 分支同样弹浮层", d.get("ta_box") is True, d)
    check("双链补全：textarea 分支回车采纳生效",
          "[[排版约定样本" in (d.get("ta_value") or "") and "]]" in (d.get("ta_value") or ""),
          d.get("ta_value"))
    check("双链补全：textarea 分支采纳后收起", d.get("ta_closed") is True, d)


# ---------------------------------------------------------------- 探针 3：标签补全
TAG_JS = PRELUDE + """
  q('.rtab[data-pane="info"]').click();
  await sleep(600);
  const add = q('#tag-add-btn');
  out.add_present = !!add;
  if (add) add.click();
  await sleep(400);
  const row = q('#tag-inputrow'), inp = q('#tag-in');
  out.lib_present = !!window.TagSuggest;
  out.row_visible = !!inp && !!row && row.hidden === false;
  const boxOpen = () => { const b = q('div.tag-suggest'); return !!b && b.style.display !== 'none'; };
  const boxItems = () => { const b = q('div.tag-suggest'); return b ? b.querySelectorAll('.wl-item').length : 0; };
  if (inp) {
    // 关键时序：headless 里 `document.hasFocus()` 是 false，`.focus()` 只把 activeElement
    // 挪过去、**不会把 focus 事件送到 addEventListener('focus')** —— 而 app.js 的标签补全
    // 是懒绑定（首次 focus 才 TagSuggest.bind，app.js:1208）。实测打桩计数：focus() 之后
    // bind 调用数仍是 0，补一次 dispatchEvent(new FocusEvent('focus')) 才变 1、浮层才弹得出来。
    // 这不是把产品测"通过"：真人用鼠标点进去时浏览器一定发 focus 事件，这里补的是无头环境的缺口。
    inp.blur();
    await sleep(120);
    inp.focus();
    inp.dispatchEvent(new FocusEvent('focus'));
    await sleep(200);
    inp.value = '渲';
    inp.dispatchEvent(new Event('input', { bubbles: true }));
    // 标签索引是**异步**预热的（tag-suggest.js:130 ensureIndex 打 /api/globalstats）：
    // 第一次 input 时索引常常还没到，浮层按"空过滤→close"关掉。等它到位后再敲一次，
    // 这才是真人打字的时序（先 focus、隔半秒才敲完前缀）。
    await sleep(1800);
    inp.dispatchEvent(new Event('input', { bubbles: true }));
    for (let i = 0; i < 40; i++) { if (boxOpen() && boxItems() >= 1) break; await sleep(150); }
    out.box_created = !!q('div.tag-suggest');
    out.box_visible = boxOpen();
    out.items = boxItems();
    out.first = txt('.tag-suggest .wl-name');
    inp.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13,
                                                     which: 13, bubbles: true, cancelable: true }));
    await sleep(500);
    out.value_after = inp.value;
    out.box_closed = !boxOpen();
  }
  return JSON.stringify(out);
})()"""


def probe_tag_suggest(base):
    print("== 3 标签补全浮层（tag-suggest.js） ==")
    d = run_expr(base + "/doc/ui-r/notes/alpha.md", TAG_JS)
    check("标签补全：标签页签里的「添加标签」入口在位", d.get("add_present") is True, d)
    check("标签补全：TagSuggest 模块已加载", d.get("lib_present") is True, d)
    check("标签补全：点入口后 #tag-in 输入行可见", d.get("row_visible") is True, d)
    check("标签补全：输入前缀后浮层弹出且有候选",
          d.get("box_created") and d.get("box_visible") and d.get("items", 0) >= 1, d)
    check("标签补全：候选是语料里已有的标签（渲染）", "渲染" in (d.get("first") or ""), d.get("first"))
    check("标签补全：回车采纳把标签填进输入框（而不是直接提交）",
          "渲染" in (d.get("value_after") or ""), d.get("value_after"))
    check("标签补全：采纳后浮层收起", d.get("box_closed") is True, d)


# ---------------------------------------------------------------- 探针 4：mermaid 放大
MERMAID_JS = PRELUDE + """
  out.svg_present = !!q('.mermaid svg');
  const svg = q('.mermaid svg');
  out.zoomable = !!(svg && svg.dataset.kbZoom === '1');
  out.overlay_in_dom = !!q('#kb-zoom-ov');
  if (svg) svg.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  await sleep(400);
  out.shown = cls('#kb-zoom-ov', 'show');
  out.cloned_svg = !!q('#kb-zoom-ov .kbz-inner svg');
  const ov = q('#kb-zoom-ov');
  if (ov) ov.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  await sleep(400);
  out.closed_again = !cls('#kb-zoom-ov', 'show');
  return JSON.stringify(out);
})()"""


def probe_mermaid(base, tmp):
    print("== 4 mermaid 点击放大 #kb-zoom-ov（含注入条件对照组） ==")
    raw_url = base + "/raw/ui-r/notes/" + quote("mermaid样本.html")
    # 服务端注入是**有条件的**（routes_pages._rewrite_html_assets 只在 HTML 里有 mermaid 时注入）。
    # 对照组必须一起断：只断"有 mermaid 的被注入"会因为"无条件注入"而假绿。
    with_html = urllib_get(raw_url)
    without = urllib_get(base + "/raw/ui-r/notes/beta.html")
    check("mermaid 注入：含 mermaid 的 HTML 被注入放大浮层片段", "kb-zoom-ov" in with_html,
          with_html[-120:])
    check("mermaid 注入对照组：不含 mermaid 的 HTML **不**被注入（条件成立而非无条件）",
          "kb-zoom-ov" not in without, without[-120:])
    # 静态一层：注入的必须是一段**能解析的 JS**。这条不是形式主义 —— 轮次 24 就是它抓到
    # `_ZOOM_SNIPPET` 用普通字符串写、Python 把 "\n" 先解析成真换行，落到页面就是
    # `css.textContent="<未闭合`，整段 script 语法错，**放大功能从来没生效过**（台账 §6 第 32 行）。
    import re as _re
    m = _re.search(r"<script>(.*)</script>", with_html, _re.S)
    snippet = m.group(1) if m else ""
    QA.mkdir(parents=True, exist_ok=True)
    (QA / "zoom-snippet.js").write_text(snippet, encoding="utf-8")
    chk = subprocess.run(["node", "--check", str(QA / "zoom-snippet.js")],
                         cwd=str(ROOT), capture_output=True, text=True,
                         encoding="utf-8", errors="replace", timeout=90)
    check("mermaid 注入片段本身是合法 JS（node --check；防的是字符串转义把脚本咬断）",
          chk.returncode == 0, (chk.stderr or chk.stdout)[-200:])
    d = run_expr(raw_url, MERMAID_JS)
    check("mermaid 放大：/raw 页面里 mermaid 的内联 SVG 渲染出来了", d.get("svg_present") is True, d)
    check("mermaid 放大：片段把 SVG 标成可放大（dataset.kbZoom=1）", d.get("zoomable") is True, d)
    check("mermaid 放大：点 SVG 后浮层加 show、并把 SVG 克隆进放大容器",
          d.get("shown") is True and d.get("cloned_svg") is True, d)
    check("mermaid 放大：再点遮罩能关掉（show 撤掉）", d.get("closed_again") is True, d)


def probe_asset_rewrite(base):
    """`routes_pages._rewrite_html_assets`：美化版 HTML 的依赖重写（台账 §5 那一格）。

    这一格此前是"模块私有函数，要测得先导出"。不用导出：它是 /raw 的必经之路，
    从 HTTP 面打进去断的是**同一份代码**，而且顺带把"重写后页面还能用"一起验了。
    """
    print("== 4b 美化版依赖重写（CDN → 本地 vendored · _rewrite_html_assets） ==")
    body = urllib_get(base + "/raw/ui-r/notes/" + quote("cdn样本.html"))
    check("依赖重写：公网 jsdelivr 的 mermaid 被换成仓库内 vendored 副本",
          "cdn.jsdelivr.net" not in body and "/static/mermaid.min.js" in body, body[:200])
    check("依赖重写：chart.js 的 CDN 同样落到本地 /static/chart.umd.min.js",
          "/static/chart.umd.min.js" in body, body[:200])
    check("依赖重写：语料里不存在的 ./_shared/ 相对引用也归一到本地副本",
          "_shared/js/mermaid" not in body, body[:200])
    check("容器名归一：class=\"mermaid-code\" 被改成 mermaid（mermaid@11 只认 .mermaid）",
          'class="mermaid-code"' not in body and 'class="mermaid"' in body, body[:240])
    check("归一之后放大浮层照样注入（两条规则串起来不能断链）", "kb-zoom-ov" in body, body[-160:])


def urllib_get(url):
    r = subprocess.run(["node", "-e",
                        f"fetch({json.dumps(url)}).then(x=>x.text()).then(t=>console.log(t)).catch(e=>console.log('ERR'+e))"],
                       cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=90)
    return (r.stdout or "").strip()


# ---------------------------------------------------------------- 探针 5：空态新建入口
NEWDOC_JS = PRELUDE + """
  const btn = q('#kb-empty-newdoc');
  out.present = !!btn;
  out.empty_hint = txt('.kb-empty-dir');
  if (btn) btn.click();
  await sleep(600);
  const inp = q('.kbm-input[data-k="nm"]');
  out.modal = !!inp;
  if (inp) { inp.value = '空态新建样本'; q('.kbm-ok').click(); }
  for (let i = 0; i < 40 && location.pathname.indexOf('/doc/') < 0; i++) await sleep(200);
  await sleep(600);
  out.path_after = location.pathname;
  out.title_after = txt('#article h1');
  return JSON.stringify(out);
})()"""


def probe_newdoc(base, tmp):
    print("== 5 空态入口 #kb-empty-newdoc（写盘：新建文档） ==")
    target = tmp / "content" / "ui-r" / "empty-sub" / "空态新建样本.md"
    check("空态新建：动手之前那个子域确实是空的",
          not any((tmp / "content" / "ui-r" / "empty-sub").iterdir()),
          list((tmp / "content" / "ui-r" / "empty-sub").iterdir()))
    d = run_expr(base + "/browse/ui-r/empty-sub", NEWDOC_JS)
    check("空态新建：空子域页给出「新建第一篇文档」入口", d.get("present") is True, d)
    check("空态新建：点入口弹出带输入框的命名弹窗", d.get("modal") is True, d)
    check("空态新建：确认后真的写盘了（不变量 1：写回文件系统）", target.is_file(), str(target))
    written = target.read_text(encoding="utf-8") if target.is_file() else ""
    check("空态新建：落盘是「frontmatter + 正文」两份都有，且标题就是输入的名字",
          written.startswith("---") and 'title: "空态新建样本"' in written
          and "# 空态新建样本" in written, _safe(written[:120]))
    check("空态新建：前端随后跳到新文档（不是停在空态）",
          "/doc/ui-r/empty-sub/" in (d.get("path_after") or ""), d.get("path_after"))


# ---------------------------------------------------------------- 探针 6：crumb 删除
CRUMB_DEL_JS = PRELUDE + """
  const b = q('#crumb .seg-btn.danger');
  out.present = !!b;
  if (b) b.click();
  await sleep(600);
  out.modal = !!q('.kbm-ok');
  const ok = q('.kbm-ok');
  if (ok) ok.click();
  for (let i = 0; i < 40 && txt('#crumb').indexOf('已删除') < 0; i++) await sleep(200);
  out.crumb = txt('#crumb');
  out.undo = !!q('.undo-del');
  out.toast = txt('#toast');
  return JSON.stringify(out);
})()"""


def probe_crumb_delete(base, tmp):
    print("== 6 读数头 crumb 删除 deleteDoc()（软删：进 _trash） ==")
    src = tmp / "content" / "ui-r" / "notes" / "gamma.md"
    check("crumb 删除：动手前 gamma.md 在正式树里", src.is_file(), str(src))
    d = run_expr(base + "/doc/ui-r/notes/gamma.md", CRUMB_DEL_JS)
    check("crumb 删除：非 html 文档的 crumb 上有删除钮", d.get("present") is True, d)
    check("crumb 删除：点击弹确认框（不是直接删）", d.get("modal") is True, d)
    check("crumb 删除：确认后 crumb 文案变成「已删除」", "已删除" in (d.get("crumb") or ""), d.get("crumb"))
    check("crumb 删除：给出撤销入口 .undo-del", d.get("undo") is True, d)
    check("crumb 删除：原路径文件已不在正式树（不变量 4：必须走软删）", not src.exists(), str(src))
    trash = list((tmp / "content" / "_trash").rglob("gamma.md"))
    check("crumb 删除：文件确实躺在 content/_trash/ 下（可再生，不是物理删）", bool(trash), trash[:2])


# ---------------------------------------------------------------- 探针 7：编辑器删除（含旁挂）
ED_DEL_JS = PRELUDE + """
  q('#crumb [onclick="openEditor()"]').click();
  for (let i = 0; i < 40 && !(q('#editor') && q('#editor').classList.contains('show')); i++) await sleep(150);
  const d = q('#ed-del');
  out.present = !!d;
  if (d) d.click();
  await sleep(600);
  const ok = q('.kbm-ok');
  if (ok) ok.click();
  for (let i = 0; i < 40 && txt('#article').indexOf('回收站') < 0; i++) await sleep(200);
  out.article = txt('#article');
  out.editor_still_open = !!(q('#editor') && q('#editor').classList.contains('show'));
  return JSON.stringify(out);
})()"""


def probe_editor_delete(base, tmp):
    print("== 7 编辑器 #ed-del 删除（连带 sidecar 旁挂一起走） ==")
    src = tmp / "content" / "ui-r" / "notes" / "alpha.md"
    side = tmp / "content" / "ui-r" / "notes" / "alpha.md.notes.md"
    check("编辑器删除：动手前正文与备注旁挂都在", src.is_file() and side.is_file(), (str(src), str(side)))
    d = run_expr(base + "/doc/ui-r/notes/alpha.md", ED_DEL_JS)
    check("编辑器删除：编辑条上的 #ed-del 在位", d.get("present") is True, d)
    check("编辑器删除：确认后正文区提示「已移入回收站」",
          "回收站" in (d.get("article") or ""), d.get("article"))
    check("编辑器删除：删除后编辑器被强制收起（不留一个指向已删文档的编辑框）",
          d.get("editor_still_open") is False, d)
    check("编辑器删除：正文与 sidecar 都不在正式树了", not src.exists() and not side.exists(),
          (src.exists(), side.exists()))
    moved = [p.name for p in (tmp / "content" / "_trash").rglob("alpha*")]
    check("编辑器删除：备注旁挂跟着正文一起进 _trash（不是被丢下）",
          "alpha.md" in moved and "alpha.md.notes.md" in moved, moved[:6])


# ---------------------------------------------------------------- 探针 8：收件箱 del / purge
# 分两趟跑，中间由 Python 查磁盘。为什么不能一趟跑完再查：
# "确认词写错 → 不该删"这条断言要看的是**第一次尝试之后**的磁盘状态，
# 而第二次（正确词）尝试就在同一个表达式里紧接着把它删了 —— 合成一趟时
# 磁盘检查永远看到最终态，那条护栏断言就成了恒假（轮次 24 第一版就这么假红过一次）。
INBOX_GUARD_JS = PRELUDE + """
  const row = n => q(`.kan-item[data-rel$="${n}"]`);
  out.rows_before = document.querySelectorAll('.kan-item').length;
  const del = row('待丢弃条目.md');
  out.del_btn_present = !!(del && del.querySelector('[data-act="del"]'));
  if (del) del.querySelector('[data-act="del"]').click();
  await sleep(600);
  const ok1 = q('.kbm-ok');
  if (ok1) ok1.click();
  for (let i = 0; i < 40 && row('待丢弃条目.md'); i++) await sleep(200);
  out.del_row_gone = !row('待丢弃条目.md');
  const p1 = row('待彻底删除条目.md');
  out.purge_btn_present = !!(p1 && p1.querySelector('[data-act="purge"]'));
  if (p1) p1.querySelector('[data-act="purge"]').click();
  await sleep(600);
  const cin = q('.kbm-input[data-k="c"]');
  out.purge_needs_word = !!cin;
  if (cin) { cin.value = '删除'; q('.kbm-ok').click(); }
  for (let i = 0; i < 20 && txt('#toast').indexOf('不匹配') < 0; i++) await sleep(200);
  out.wrong_word_row_still = !!row('待彻底删除条目.md');
  out.wrong_word_toast = txt('#toast');
  return JSON.stringify(out);
})()"""

INBOX_PURGE_JS = PRELUDE + """
  const row = n => q(`.kan-item[data-rel$="${n}"]`);
  const p = row('待彻底删除条目.md');
  out.row_before = !!p;
  if (p) p.querySelector('[data-act="purge"]').click();
  await sleep(600);
  const cin = q('.kbm-input[data-k="c"]');
  if (cin) { cin.value = '彻底删除'; q('.kbm-ok').click(); }
  for (let i = 0; i < 40 && row('待彻底删除条目.md'); i++) await sleep(200);
  out.row_gone = !row('待彻底删除条目.md');
  out.rows_after = document.querySelectorAll('.kan-item').length;
  return JSON.stringify(out);
})()"""


INBOX_FLOW_JS = PRELUDE + """
  const row = n => q(`.kan-item[data-rel$="${n}"]`);
  const rowsNow = () => [...document.querySelectorAll('.kan-item')].map(x => x.dataset.rel);
  out.rows_at_start = document.querySelectorAll('.kan-item').length;
  out.go_disabled_at_start = q('#ib-go').disabled;
  // 1) 勾两篇 → 选择态与计数
  for (const n of ['归档样本甲.md', '归档样本乙.md']) {
    const c = row(n) && row(n).querySelector('.ib-check');
    if (c) { c.checked = true; c.dispatchEvent(new Event('change', { bubbles: true })); }
  }
  await sleep(400);
  out.sel_count = document.querySelectorAll('.kan-item.sel').length;
  out.count_text = txt('#ib-count');
  out.go_enabled = q('#ib-go').disabled === false;
  // 2) 批量归档 → 弹窗填目标目录
  q('#ib-go').click();
  await sleep(600);
  const dirIn = q('.kbm-input[data-k="dir"]');
  out.archive_modal = !!dirIn;
  if (dirIn) { dirIn.value = 'ui-r/已归档'; q('.kbm-ok').click(); }
  for (let i = 0; i < 40 && row('归档样本甲.md'); i++) await sleep(200);
  out.batch_rows_gone = !row('归档样本甲.md') && !row('归档样本乙.md');
  out.batch_toast = txt('#toast');
  await sleep(600);
  // 3) 单篇归档（move）
  const mv = row('单篇归档.md');
  out.move_btn_present = !!(mv && mv.querySelector('[data-act="move"]'));
  if (mv) mv.querySelector('[data-act="move"]').click();
  await sleep(600);
  const dstIn = q('.kbm-input[data-k="dst"]');
  out.move_modal = !!dstIn;
  if (dstIn) { dstIn.value = 'ui-r/已归档/单篇归档.md'; q('.kbm-ok').click(); }
  for (let i = 0; i < 40 && row('单篇归档.md'); i++) await sleep(200);
  out.move_row_gone = !row('单篇归档.md');
  await sleep(500);
  // 4) 根级文件点「忽略」：弹窗文案必须说"忽略这一个文件"（后端确实是这么退化的），
  //    然后**取消** —— 取消不该写任何东西
  const ig0 = row('根级忽略.md');
  out.root_ignore_present = !!(ig0 && ig0.querySelector('[data-act="ignore"]'));
  if (ig0) ig0.querySelector('[data-act="ignore"]').click();
  await sleep(700);
  const m = q('.kbm');
  out.root_modal_title = m ? txt('.kbm-title-t') : '';
  out.root_modal_body = m ? txt('.kbm-body') : '';
  out.root_modal_value = q('.kbm-input[data-k="d"]') ? q('.kbm-input[data-k="d"]').value : null;
  const cancel = q('.kbm-cancel');
  if (cancel) cancel.click();
  await sleep(500);
  out.root_row_still = !!row('根级忽略.md');
  // 5) 目录级忽略：整目录从待归档消失，但**源文件不动**
  const ig1 = row('说明.md');
  if (ig1) ig1.querySelector('[data-act="ignore"]').click();
  await sleep(700);
  const dIn = q('.kbm-input[data-k="d"]');
  out.ignore_modal = !!dIn;
  out.ignore_prefill = dIn ? dIn.value : null;
  out.dir_modal_title = q('.kbm') ? txt('.kbm-title-t') : '';
  if (dIn) { q('.kbm-ok').click(); }
  for (let i = 0; i < 40 && row('说明.md'); i++) await sleep(200);
  out.ignored_row_gone = !row('说明.md');
  await sleep(500);
  // 6) 归档过的条目进「最近归档」列（localStorage 记账，不是数据库）
  out.done_rows = document.querySelectorAll('.kan-col[data-col="done"] .kan-item').length;
  out.recent_ls = (function () { try { return JSON.parse(localStorage.getItem('kb-inbox-recent') || '[]'); } catch (e) { return []; } })();
  out.rows_left = rowsNow().length;
  return JSON.stringify(out);
})()"""


def probe_inbox(base, tmp):
    print("== 8 收件箱 mini-act del / purge ==")
    ib = tmp / "content" / "_inbox"
    drop = ib / "待丢弃条目.md"
    purge = ib / "待彻底删除条目.md"
    purge_side = ib / "待彻底删除条目.md.notes.md"
    purge_html = ib / "待彻底删除条目.html"
    d = run_expr(base + "/inbox", INBOX_GUARD_JS)
    check("收件箱：看板里两行靶子都在", d.get("rows_before", 0) >= 2, d)
    check("收件箱：行内有「丢弃」与「彻底删除」两个动作钮",
          d.get("del_btn_present") and d.get("purge_btn_present"), d)
    check("收件箱：丢弃 → 行从看板移除", d.get("del_row_gone") is True, d)
    check("收件箱：丢弃走软删 —— 文件进 _trash、_inbox 里没了",
          not drop.exists() and bool(list((tmp / "content" / "_trash").rglob("待丢弃条目.md"))),
          str(drop))
    check("收件箱：彻底删除要求输入确认词（不是点一下就物理删）",
          d.get("purge_needs_word") is True, d)
    check("收件箱：确认词写错 → 拒绝执行、行还在、给提示",
          d.get("wrong_word_row_still") is True and "不匹配" in (d.get("wrong_word_toast") or ""), d)
    check("收件箱：确认词写错时一个字节都没删（护栏真的兜住了）",
          purge.exists() and purge_side.exists() and purge_html.exists(),
          [p.name for p in (purge, purge_side, purge_html) if not p.exists()])
    d2 = run_expr(base + "/inbox", INBOX_PURGE_JS)
    check("收件箱：确认词正确 → 行移除", d2.get("row_gone") is True and d2.get("row_before") is True, d2)
    check("收件箱：purge 物理删除正文 + sidecar + 同名美化版三件",
          not any(p.exists() for p in (purge, purge_side, purge_html)),
          [p.name for p in (purge, purge_side, purge_html) if p.exists()])
    check("收件箱：purge 不留 _trash 副本（它和软删是两条路，别混）",
          not list((tmp / "content" / "_trash").rglob("待彻底删除条目*")), "有残留")

    # ---- 第三段：归档 / 忽略（#ib-go 与 mini-act move·ignore）----
    d3 = run_expr(base + "/inbox", INBOX_FLOW_JS)
    check("批量归档：动手前归档按钮是禁用的（没勾任何行）",
          d3.get("go_disabled_at_start") is True, d3)
    check("批量归档：勾两篇 → 两行进入 .sel、计数读数写「已选 2 篇」、按钮转可用",
          d3.get("sel_count") == 2 and "已选 2" in (d3.get("count_text") or "")
          and d3.get("go_enabled") is True,
          {"sel": d3.get("sel_count"), "count": d3.get("count_text")})
    check("批量归档：弹窗要求填目标目录（不是默认丢进某个域）", d3.get("archive_modal") is True, d3)
    check("批量归档：确认后两行都离开看板", d3.get("batch_rows_gone") is True, d3)
    moved = tmp / "content" / "ui-r" / "已归档"
    check("批量归档：两篇真的落盘到目标目录（写文件系统，不是只改前端）",
          (moved / "归档样本甲.md").is_file() and (moved / "归档样本乙.md").is_file(),
          [p.name for p in moved.glob("*")] if moved.is_dir() else "目录不存在")
    check("单篇归档：行内有 move 动作、弹窗要目标路径",
          d3.get("move_btn_present") and d3.get("move_modal"), d3)
    check("单篇归档：确认后行消失且文件落在指定路径",
          d3.get("move_row_gone") is True and (moved / "单篇归档.md").is_file(),
          [p.name for p in moved.glob("*")] if moved.is_dir() else "目录不存在")
    check("忽略：根级文件的弹窗说实话（说「忽略这个文件」，不谎称目录、不加尾斜杠）",
          d3.get("root_ignore_present") and "文件" in (d3.get("root_modal_title") or "")
          and "目录" not in (d3.get("root_modal_title") or "")
          and (d3.get("root_modal_value") or "") == "根级忽略.md"
          and "_inbox/根级忽略.md/" not in (d3.get("root_modal_body") or ""),
          {"title": d3.get("root_modal_title"), "value": d3.get("root_modal_value")})
    check("忽略：点「取消」就真的什么都没发生（行还在、清单没写）",
          d3.get("root_row_still") is True, d3)
    check("忽略：目录级忽略的弹窗预填的就是那个目录、标题说的是目录",
          d3.get("ignore_modal") and (d3.get("ignore_prefill") or "") == "开发产物"
          and "目录" in (d3.get("dir_modal_title") or ""),
          {"prefill": d3.get("ignore_prefill"), "title": d3.get("dir_modal_title")})
    check("忽略：整目录从待归档列表消失", d3.get("ignored_row_gone") is True, d3)
    check("忽略：源文件**没动**（忽略是清单，不是删除）",
          (tmp / "content" / "_inbox" / "开发产物" / "说明.md").is_file()
          and (tmp / "content" / "_inbox" / "根级忽略.md").is_file(), "文件不见了")
    igf = tmp / "content" / "_meta" / "inbox-ignore.json"
    igj = json.loads(igf.read_text(encoding="utf-8")) if igf.is_file() else {}
    check("忽略：清单落盘 content/_meta/inbox-ignore.json 且只记了被确认的那个目录",
          "开发产物" in (igj.get("dirs") or []) and "根级忽略.md" not in (igj.get("files") or []),
          igj)
    # 规则必须**对下一次扫描生效**（不只是当前 DOM 少了一行）：重新拉一次服务端渲染的列表
    again = urllib_get(base + "/inbox")
    check("忽略：重新拉取收件箱，被忽略目录里的那篇真的不再进待归档（规则对下次扫描生效）",
          "说明.md" not in again and "根级忽略.md" in again,
          [n for n in ("说明.md", "根级忽略.md") if (n in again) != (n == "根级忽略.md")])
    check("归档记录：两篇归档过的进「最近归档」列，且是 localStorage 记的账",
          d3.get("done_rows", 0) >= 3 and len(d3.get("recent_ls") or []) >= 3,
          {"done_rows": d3.get("done_rows"), "ls": d3.get("recent_ls")})


# ---------------------------------------------------------------- 探针 9：标签页看板抽屉
DRAWER_JS = PRELUDE + """
  const pill = q('#tag-cloud .t[data-tag="渲染"]');
  out.pill_present = !!pill;
  if (pill) pill.click();
  await sleep(500);
  const dr = q('#tag-drawer');
  out.opened = !!dr && dr.hidden === false;
  out.head = txt('#drawer-h');
  out.docs = document.querySelectorAll('#drawer-docs a.result').length;
  out.first_doc = txt('#drawer-docs a.result .doc-t');
  out.pill_open = cls('#tag-cloud .t[data-tag="渲染"]', 'open');
  const pill2 = q('#tag-cloud .t[data-tag="渲染"]');
  if (pill2) pill2.click();
  await sleep(400);
  out.closed_on_second_click = !dr || dr.hidden === true;
  const pill3 = q('#tag-cloud .t[data-tag="渲染"]');
  if (pill3) pill3.click();
  await sleep(400);
  out.reopened = !!dr && dr.hidden === false;
  return JSON.stringify(out);
})()"""


def probe_drawer(base):
    print("== 9 标签页看板抽屉 #drawer-h / #drawer-docs ==")
    d = run_expr(base + "/tags", DRAWER_JS)
    check("看板抽屉：标签云里有「渲染」胶囊可点", d.get("pill_present") is True, d)
    check("看板抽屉：点胶囊展开抽屉（hidden=false）", d.get("opened") is True, d)
    check("看板抽屉：抽屉标题写着标签名与篇数", "渲染" in (d.get("head") or "") and "篇" in (d.get("head") or ""),
          d.get("head"))
    check("看板抽屉：列出了带链接的文档行", d.get("docs", 0) >= 1, d)
    check("看板抽屉：文档行有标题文字（不是空壳）", bool(d.get("first_doc")), d)
    check("看板抽屉：展开的胶囊带 .open 标记", d.get("pill_open") is True, d)
    check("看板抽屉：再点同一个胶囊收起（toggle 语义）",
          d.get("closed_on_second_click") is True, d)
    check("看板抽屉：第三次点击能重新展开（状态可逆，不是一次性）", d.get("reopened") is True, d)


# ================================================================ 探针 11：首页「今日学习」卡
# 台账 §2 行「复习 · 今日卡 #kb-today*」。home.js 自己写着"接口不可用时给人话提示，
# 绝不写死占位数字"，可**真出数**那一侧没人验过：三格统计、掌握度条、「显示定义」折叠。
HOME_JS = PRELUDE + r"""
  const T = e => ((e && e.textContent) || '').replace(/\s+/g, ' ').trim();
  const host = q('#kb-today');
  out.host_rendered = !!(host && host.querySelector('#kb-today-date'));
  if (host && host.scrollIntoView) host.scrollIntoView({block: 'center'});
  await sleep(400);
  out.date = txt('#kb-today-date');
  out.term = txt('#kb-today-term');
  out.tip = txt('#kb-today-tip');
  const defEl = q('#kb-today-def'), show = q('#kb-today-show'), docA = q('#kb-today-doc');
  out.def_text = T(defEl);
  out.h_before = defEl ? Math.round(defEl.getBoundingClientRect().height) : -1;
  out.btn_before = T(show);
  if (show) show.click();
  await sleep(300);
  out.h_after = defEl ? Math.round(defEl.getBoundingClientRect().height) : -1;
  out.btn_after = T(show);
  if (show) show.click();
  await sleep(300);
  out.h_third = defEl ? Math.round(defEl.getBoundingClientRect().height) : -1;
  out.btn_third = T(show);
  out.doc_href = docA ? (docA.getAttribute('href') || '') : '';
  out.doc_target = docA ? (docA.getAttribute('target') || '') : '';
  out.stats = [...document.querySelectorAll('#kb-today-stats .kb-today-stat')]
    .map(x => ({v: T(x.querySelector('b')), lab: T(x.querySelector('span'))}));
  out.bars = [...document.querySelectorAll('#kb-mastery-bars .kb-mastery-row')].map(x => ({
    lab: T(x.querySelector('.kb-ml')), pct: T(x.querySelector('.kb-mv')),
    w: x.querySelector('.kb-bar i') ? x.querySelector('.kb-bar i').style.width : '',
    dh: x.style.getPropertyValue('--dh')
  }));
  out.cta = [...document.querySelectorAll('#kb-today .kb-today-cta a')].map(a => a.getAttribute('href'));
  return JSON.stringify(out);
})()"""


def probe_home_today(base):
    print("== 11 首页「今日学习」卡 #kb-today*（显示定义 / 跳转原文 / 三格统计 / 掌握度条） ==")
    api = json.loads(urllib_get(base + "/api/learn/today?domain=baike") or "{}")
    cards = json.loads(urllib_get(base + "/api/learn/cards?domain=baike&kind=baike_def&limit=50") or "{}")
    mas = json.loads(urllib_get(base + "/api/learn/mastery?scope=sub&domain=baike") or "{}")
    by_term = {c.get("term"): c for c in (cards.get("items") or [])}
    d = run_expr(base + "/home", HOME_JS)
    st = api.get("stats") or {}
    check("今日卡：home.js 真的把 #kb-today 骨架渲出来（不是停在模板里的占位）",
          d.get("host_rendered") is True, d)
    check("今日卡：日期是服务端下发的 YYYY-MM-DD，与 /api/learn/today 一致",
          d.get("date") == api.get("date") and len(d.get("date") or "") == 10,
          {"dom": d.get("date"), "api": api.get("date")})
    check("今日卡：术语位显示的是真词条（不是「载入中…」/「（暂无卡片）」）",
          d.get("term") in by_term, {"dom": d.get("term"), "api_terms": sorted(by_term)})
    shown = by_term.get(d.get("term")) or {}
    check("今日卡：定义折叠块里的文字就是那张卡的 back（内容真的 flowed 到首页）",
          bool(d.get("def_text")) and (d.get("def_text") == (shown.get("back") or "").strip()
                                       or "这张卡还没有摘录内容" in (d.get("def_text") or "")),
          {"dom": d.get("def_text"), "api": shown.get("back")})
    check("今日卡：没点之前定义是收着的（高度 0 + 钮写「显示定义」）",
          d.get("h_before") == 0 and "显示定义" in (d.get("btn_before") or ""), d)
    check("今日卡：点「显示定义」展开（高度 >0，钮文案翻成「收起定义」）",
          (d.get("h_after") or 0) > 0 and "收起定义" in (d.get("btn_after") or ""), d)
    check("今日卡：再点一次能收回去（状态可逆，不是一次性开关）",
          d.get("h_third") == 0 and "显示定义" in (d.get("btn_third") or ""), d)
    check("今日卡：「跳转原文」指向那张卡的文档 url 且新开标签（不是回退值 /review）",
          bool(shown.get("url")) and (shown.get("url") or "").startswith("/doc/")
          and d.get("doc_href") == shown.get("url") and d.get("doc_target") == "_blank",
          {"dom": d.get("doc_href"), "target": d.get("doc_target"), "api": shown.get("url")})
    want_stats = {"待复习": str(st.get("due_n")), "连续天数": str(st.get("streak_days")),
                  "掌握度": f"{st.get('mastered_pct')}%"}
    got_stats = {x.get("lab"): x.get("v") for x in (d.get("stats") or [])}
    check("今日卡：三格统计逐项等于接口给的数字（待复习/连续天数/掌握度，没有占位符）",
          len(d.get("stats") or []) == 3 and all(got_stats.get(k) == v for k, v in want_stats.items()),
          {"dom": got_stats, "api": want_stats})
    exp_bars = sorted(mas.get("items") or [], key=lambda x: -(x.get("total") or 0))[:6]
    got_bars = d.get("bars") or []
    ok_bars = (len(got_bars) == len(exp_bars)
               and all(b.get("pct") == f"{int(x.get('pct') or 0)}%"
                       and b.get("dh") == str(x.get("hue"))
                       and b.get("w") == f"{int(x.get('pct') or 0)}%"
                       for b, x in zip(got_bars, exp_bars)))
    check("今日卡：掌握度条数 == 接口 items（按 total 排序取前 6），每条的百分比/色相/条宽都对得上",
          ok_bars, {"dom": got_bars,
                    "api": [{"id": x.get("id") or x.get("sub"), "pct": x.get("pct"),
                             "hue": x.get("hue")} for x in exp_bars]})
    check("今日卡：底部两个 CTA 指向 /review 与 /quiz（首页必须能把人送进复习）",
          d.get("cta") == ["/review", "/quiz"], d.get("cta"))


# ================================================================ 探针 12+13：术语门户 + 串学漫游
# 台账 §2 三行：「术语 · #kb-gl-q / #kb-gl-clear」「术语 · #kb-gl-buckets/subs/sub/body」
# 「复习 · 漫游 #kb-roam / #kb-roam-x」。glossary.js 的设计是"全量只拉一次，之后所有过滤
# 都在前端完成"，所以**必须**断"过滤后留下的正好是该留下的那些"，只断"输入框在位"等于没断。
GLOSSARY_JS = PRELUDE + r"""
  const T = e => ((e && e.textContent) || '').replace(/\s+/g, ' ').trim();
  const terms = () => [...document.querySelectorAll('#kb-gl-body .kb-term')].map(b => b.dataset.term);
  for (let i = 0; i < 80 && !q('.kb-term'); i++) await sleep(150);
  out.ready = !!q('.kb-term');
  out.n_all = terms().length;
  out.groups_all = document.querySelectorAll('#kb-gl-body .kb-gl-group').length;
  out.line_all = txt('#kb-gl-sub');
  out.bucket_labels = [...document.querySelectorAll('#kb-gl-buckets .kb-bucket')]
    .map(b => ({L: b.dataset.letter, n: Number(T(b.querySelector('.kb-bn'))),
                zero: b.classList.contains('zero'),
                ad: b.getAttribute('aria-disabled')}));
  out.sub_chips = [...document.querySelectorAll('#kb-gl-subs .kb-gl-sub')].map(b => ({s: b.dataset.sub, t: T(b)}));

  const typeQ = async v => { const e = q('#kb-gl-q'); e.value = v;
                             e.dispatchEvent(new Event('input', {bubbles: true})); await sleep(450); };
  await typeQ('zzz不存在zzz');
  out.n_none = terms().length;
  out.empty_none = txt('.kb-gl-empty');
  await typeQ('向量');
  out.n_q = terms().length; out.q_terms = terms(); out.line_q = txt('#kb-gl-sub');
  const clr = q('#kb-gl-clear');
  out.clear_present = !!clr;
  if (clr) clr.click();
  await sleep(400);
  out.n_cleared = terms().length;
  out.q_value = (q('#kb-gl-q') || {}).value;
  out.focus_after_clear = document.activeElement ? document.activeElement.id : '';

  const nz = [...document.querySelectorAll('#kb-gl-buckets .kb-bucket')]
    .find(b => b.dataset.letter !== 'all' && !b.classList.contains('zero'));
  out.letter = nz ? nz.dataset.letter : null;
  out.letter_n = nz ? Number(T(nz.querySelector('.kb-bn'))) : 0;
  if (nz) nz.click();
  await sleep(350);
  out.n_letter = terms().length; out.letter_terms = terms();
  out.on_letter = (document.querySelector('#kb-gl-buckets .kb-bucket.on') || {dataset: {}}).dataset.letter || null;
  const z = [...document.querySelectorAll('#kb-gl-buckets .kb-bucket.zero')][0];
  out.zero_letter = z ? z.dataset.letter : null;
  if (z) z.click();
  await sleep(350);
  out.n_after_zero = terms().length;
  out.on_after_zero = (document.querySelector('#kb-gl-buckets .kb-bucket.on') || {dataset: {}}).dataset.letter || null;
  const allb = document.querySelector('#kb-gl-buckets .kb-bucket[data-letter="all"]');
  if (allb) allb.click();
  await sleep(350);
  out.n_back_all = terms().length;

  const s1 = [...document.querySelectorAll('#kb-gl-subs .kb-gl-sub')].find(b => b.dataset.sub);
  out.sub_pick = s1 ? s1.dataset.sub : null;
  if (s1) s1.click();
  await sleep(350);
  out.n_sub = terms().length;
  out.groups_sub = document.querySelectorAll('#kb-gl-body .kb-gl-group').length;
  out.sub_terms = terms();
  out.on_sub = (document.querySelector('#kb-gl-subs .kb-gl-sub.on') || {dataset: {}}).dataset.sub || null;
  const sub0 = document.querySelector('#kb-gl-subs .kb-gl-sub[data-sub=""]');
  if (sub0) sub0.click();
  await sleep(350);
  out.n_sub_back = terms().length;

  const tb = document.querySelector('#kb-gl-body .kb-term[data-term="倒排索引"]');
  if (tb) tb.click();
  await sleep(350);
  out.detail_open = !!q('.kb-term-detail');
  out.detail_acts = [...document.querySelectorAll('.kb-term-detail .kb-act')].map(a => a.dataset.act);
  out.detail_text = T(q('.kb-term-detail'));
  out.term_marked_open = !!(tb && tb.classList.contains('open'));
  if (tb) tb.click();
  await sleep(350);
  out.detail_closed = !q('.kb-term-detail');
  out.term_unmarked = !document.querySelector('#kb-gl-body .kb-term.open');

  // ---- 串学漫游：从「倒排索引」出发（它的 ## 相关术语 里挂着一个有卡片的 + 一个没卡片的）
  if (tb) tb.click();
  await sleep(350);
  const roamAct = document.querySelector('.kb-term-detail .kb-act[data-act="roam"]');
  out.roam_act_present = !!roamAct;
  out.roam_hidden_before = q('#kb-roam') ? !!q('#kb-roam').hidden : null;
  if (roamAct) roamAct.click();
  for (let i = 0; i < 60 && !(q('#kb-roam') && !q('#kb-roam').hidden && q('#kb-roam .kb-roam-node')); i++) await sleep(150);
  out.roam_open = !!(q('#kb-roam') && !q('#kb-roam').hidden);
  out.roam_head = txt('.kb-roam-h');
  out.roam_nodes = [...document.querySelectorAll('#kb-roam .kb-roam-node')].map(n => ({
    // dead 节点是 <span>（不可点），glossary.js 没给它 data-term，名字只在文字里
    t: n.dataset.term || T(n).split('·')[0].trim(),
    dead: n.classList.contains('dead'), neu: n.classList.contains('is-new')}));
  out.roam_search = location.search;
  out.roam_search = location.search;
  const reals = [...document.querySelectorAll('#kb-roam .kb-roam-node:not(.dead)')];
  const pick = reals[reals.length - 1];
  out.roam_pick = pick ? pick.dataset.term : null;
  if (pick) pick.click();
  for (let i = 0; i < 60 && txt('.kb-roam-h').indexOf('「' + (out.roam_pick || '~') + '」') < 0; i++) await sleep(150);
  await sleep(700);
  out.roam_head2 = txt('.kb-roam-h');
  out.roam_search2 = location.search;
  const rx = q('#kb-roam-x');
  out.roam_x_present = !!rx;
  if (rx) rx.click();
  await sleep(500);
  out.roam_hidden_after_x = !!(q('#kb-roam') && q('#kb-roam').hidden);
  out.roam_empty_after_x = !!(q('#kb-roam') && q('#kb-roam').innerHTML === '');

  // ---- 加入复习：状态点必须从「未学」翻成「学习中」（这一步真写 learn.db）
  const t2 = document.querySelector('#kb-gl-body .kb-term[data-term="布隆过滤器"]')
    || document.querySelector('#kb-gl-body .kb-term[data-term="向量数据库"]');
  out.review_term = t2 ? t2.dataset.term : null;
  out.dot_class_before = t2 && t2.querySelector('.kb-dotm') ? t2.querySelector('.kb-dotm').className : '';
  if (t2) t2.click();
  await sleep(350);
  const rev = document.querySelector('.kb-term-detail .kb-act[data-act="review"]');
  out.review_act_present = !!rev;
  if (rev) rev.click();
  for (let i = 0; i < 60 && txt('#toast').indexOf('已加入复习') < 0; i++) await sleep(150);
  out.review_toast = txt('#toast');
  await sleep(500);
  const t2b = document.querySelector('#kb-gl-body .kb-term[data-term="' + (out.review_term || '~') + '"]');
  out.dot_class_after = t2b && t2b.querySelector('.kb-dotm') ? t2b.querySelector('.kb-dotm').className : '';
  return JSON.stringify(out);
})()"""


def probe_glossary(base):
    print("== 12 术语门户：过滤 / 清空 / 首字母桶 / 子域 / 内联详情 ==")
    gl = json.loads(urllib_get(base + "/api/glossary?domain=baike") or "{}")
    flat = gl.get("items_flat") or []
    api_buckets = {b.get("letter"): b.get("n") for b in (gl.get("buckets") or [])}
    api_subs = {g.get("sub"): len(g.get("items") or []) for g in (gl.get("groups") or [])}
    d = run_expr(base + "/glossary", GLOSSARY_JS)
    check("术语门户：全量拉完并渲染出术语胶囊（骨架屏被替换掉）", d.get("ready") is True, d)
    check("术语门户：胶囊数 == /api/glossary 的 items_flat 条数（不重复请求，也不漏项）",
          d.get("n_all") == len(flat) and len(flat) >= 3, {"dom": d.get("n_all"), "api": len(flat)})
    check("术语门户：计数行写着总数与当前显示数",
          f"共 {len(flat)} 个术语" in (d.get("line_all") or "")
          and f"当前显示 {len(flat)} 个" in (d.get("line_all") or ""), d.get("line_all"))
    by_letter = {b.get("L"): b.get("n") for b in (d.get("bucket_labels") or [])}
    check("术语门户：每个首字母桶上的数字 == 接口 buckets（接口没列的字母显示 0）",
          all(by_letter.get(k, 0) == v for k, v in api_buckets.items())
          and all(b.get("n") == 0 for b in (d.get("bucket_labels") or [])
                  if b.get("L") != "all" and b.get("L") not in api_buckets),
          {"dom": by_letter, "api": api_buckets})
    check("术语门户：空桶同时带 .zero 与 aria-disabled（点了不该有反应的钮要在无障碍层说清楚）",
          all(b.get("zero") is True and b.get("ad") == "true" for b in (d.get("bucket_labels") or [])
              if b.get("L") != "all" and b.get("n") == 0),
          [b for b in (d.get("bucket_labels") or []) if b.get("n") == 0][:4])
    check("术语过滤：无匹配时渲染空态、并把当前筛选回显出来",
          d.get("n_none") == 0 and "没有符合条件的术语" in (d.get("empty_none") or "")
          and "zzz不存在zzz" in (d.get("empty_none") or ""), d.get("empty_none"))
    want_q = sorted(it.get("term") for it in flat if "向量" in (it.get("term") or "").lower())
    check("术语过滤：输入「向量」只剩真含该词的胶囊（本地过滤口径 = term 子串）",
          sorted(d.get("q_terms") or []) == want_q and 0 < len(want_q) < len(flat),
          {"dom": d.get("q_terms"), "api": want_q})
    check("术语过滤：计数行的「当前显示」跟着变（不是只改网格）",
          f"当前显示 {len(want_q)} 个" in (d.get("line_q") or ""), d.get("line_q"))
    check("术语过滤：清空钮清掉输入、列表复原、焦点回到输入框",
          d.get("clear_present") and d.get("q_value") == ""
          and d.get("n_cleared") == len(flat) and d.get("focus_after_clear") == "kb-gl-q", d)
    check("首字母桶：点非空桶后只显示该桶术语、.on 搬过去、条数等于桶计数",
          d.get("n_letter") == d.get("letter_n") == by_letter.get(d.get("letter"))
          and d.get("on_letter") == d.get("letter") and len(d.get("letter_terms") or []) > 0, d)
    check("首字母桶：点空桶（.zero）必须什么都不变（守卫分支真的在）",
          bool(d.get("zero_letter")) and d.get("n_after_zero") == d.get("n_letter")
          and d.get("on_after_zero") == d.get("letter"), d)
    check("首字母桶：点「全部」回到全量", d.get("n_back_all") == len(flat), d)
    chip_counts = {c.get("s"): int(c.get("t", "").split("·")[-1]) for c in (d.get("sub_chips") or [])[1:]}
    check("子域切换：钮上写着「子域 · 篇数」，篇数与接口 groups 逐项一致",
          chip_counts == api_subs and len(api_subs) >= 2, {"dom": chip_counts, "api": api_subs})
    want_sub = sorted(it.get("term") for it in flat if it.get("sub") == d.get("sub_pick"))
    check("子域切换：选中一个子域后只剩该子域的术语、只剩 1 个分组、.on 跟着搬",
          sorted(d.get("sub_terms") or []) == want_sub and d.get("n_sub") == len(want_sub)
          and d.get("groups_sub") == 1 and d.get("on_sub") == d.get("sub_pick"),
          {"dom": d.get("sub_terms"), "api": want_sub, "pick": d.get("sub_pick")})
    check("子域切换：点「全部子域」复原", d.get("n_sub_back") == len(flat), d)
    check("内联详情：点术语展开详情（三个动作：加入复习 / 跳转原文 / 串学）并给该胶囊打 .open",
          d.get("detail_open") and d.get("detail_acts") == ["review", "doc", "roam"]
          and d.get("term_marked_open") is True, d)
    check("内联详情：里面写着定义摘要与来源路径（不是空壳）",
          "倒排索引" in (d.get("detail_text") or "") and "baike/term" in (d.get("detail_text") or ""),
          d.get("detail_text"))
    check("内联详情：再点同一个术语收起（.open 标记一起撤掉，不留残影）",
          d.get("detail_closed") is True and d.get("term_unmarked") is True, d)

    print("== 13 串学漫游 #kb-roam / #kb-roam-x + 加入复习 ==")
    roam = json.loads(urllib_get(base + "/api/learn/roam?from=" + quote("倒排索引") + "&n=6") or "{}")
    check("串学：详情里的「串学」钮在位，且浮层初始是收着的",
          d.get("roam_act_present") is True and d.get("roam_hidden_before") is True, d)
    check("串学：点后浮层展开，标题写明从哪个术语出发",
          d.get("roam_open") is True and "串学路径" in (d.get("roam_head") or "")
          and "倒排索引" in (d.get("roam_head") or ""), d.get("roam_head"))
    api_path = [p.get("term") for p in (roam.get("path") or [])]
    dom_path = [n.get("t") for n in (d.get("roam_nodes") or []) if not n.get("dead")]
    check("串学：路径节点与 /api/learn/roam 的 path 逐项一致（起点自己 + 沿 [[双链]] 走到的卡）",
          dom_path == api_path and len(api_path) >= 2, {"dom": dom_path, "api": api_path})
    dom_dead = [n.get("t") for n in (d.get("roam_nodes") or []) if n.get("dead")]
    check("串学：语料里没有卡片的术语渲染成虚线「无卡片」节点，而不是被静默吞掉",
          dom_dead == (roam.get("dead_ends") or []) and len(dom_dead) >= 1,
          {"dom": dom_dead, "api": roam.get("dead_ends")})
    check("串学：URL 带 ?roam=（pushState 进了历史，可分享 / 可后退）",
          "roam=" in (d.get("roam_search") or ""), d.get("roam_search"))
    check("串学：点路径上的节点 → 以它为新起点重画（标题跟着换、URL 跟着换）",
          bool(d.get("roam_pick")) and f"「{d.get('roam_pick')}」" in (d.get("roam_head2") or "")
          and quote(d.get("roam_pick") or "") in (d.get("roam_search2") or ""),
          {"pick": d.get("roam_pick"), "head": d.get("roam_head2"), "search": d.get("roam_search2")})
    check("串学：#kb-roam-x 收起后浮层 hidden 且内容清空（不是留一屏旧路径）",
          d.get("roam_x_present") and d.get("roam_hidden_after_x") is True
          and d.get("roam_empty_after_x") is True, d)
    check("加入复习：详情里点它 → toast 回执 + 该术语状态点从「未学」翻成「学习中」",
          "已加入复习" in (d.get("review_toast") or "")
          and "new" in (d.get("dot_class_before") or "")
          and "learning" in (d.get("dot_class_after") or ""),
          {"term": d.get("review_term"), "before": d.get("dot_class_before"),
           "after": d.get("dot_class_after"), "toast": d.get("review_toast")})


# ================================================================ 探针 14：模拟面试 + 精确命中
MOCK_JS = PRELUDE + r"""
  const T = e => ((e && e.textContent) || '').replace(/\s+/g, ' ').trim();
  for (let i = 0; i < 80 && !txt('#kb-card-term'); i++) await sleep(150);
  out.card_term = txt('#kb-card-term');
  out.boot_card_visible = !!(q('#kb-card') && !q('#kb-card').hidden);
  out.foot_normal0 = txt('#kb-learn-foot');
  out.mock_btn_present = !!q('#kb-mock-start');
  out.chips = [...document.querySelectorAll('.kb-mock-choose button')].map(b => b.dataset.n);
  out.chip_on0 = (q('.kb-mock-choose button.on') || {dataset: {}}).dataset.n || null;
  const c5 = document.querySelector('.kb-mock-choose button[data-n="5"]');
  if (c5) c5.click();
  await sleep(200);
  out.chip_on5 = (q('.kb-mock-choose button.on') || {dataset: {}}).dataset.n || null;
  const c10 = document.querySelector('.kb-mock-choose button[data-n="10"]');
  if (c10) c10.click();
  await sleep(200);
  out.chip_on10 = (q('.kb-mock-choose button.on') || {dataset: {}}).dataset.n || null;
  const ms = q('#kb-mock-start');
  out.start_present = !!ms;
  if (ms) ms.click();
  out.mid_sub = txt('#kb-learn-sub');                 // 同步读：出卷中…
  for (let i = 0; i < 60 && txt('#kb-learn-sub').indexOf('计时开始') < 0; i++) await sleep(150);
  out.started_sub = txt('#kb-learn-sub');
  out.started_foot = txt('#kb-learn-foot');
  out.grades_hidden_before = !!(q('#kb-grades') && q('#kb-grades').hidden);
  out.started_term = txt('#kb-card-term');
  out.started_cta = txt('#kb-learn-cta');
  const chip = document.querySelector('#kb-sub-filters .kb-sub-chip[data-sub]:not([data-sub=""])');
  out.sub_chip_pick = chip ? chip.dataset.sub : null;
  out.sub_chip0 = (q('#kb-sub-filters .kb-sub-chip.on') || {dataset: {}}).dataset.sub;
  if (chip) chip.click();
  await sleep(400);
  out.mock_block_toast = txt('#toast');
  out.sub_chip1 = (q('#kb-sub-filters .kb-sub-chip.on') || {dataset: {}}).dataset.sub;
  const rv1 = q('#kb-reveal'); out.reveal1 = !!rv1;
  if (rv1) rv1.click();
  await sleep(250);
  out.grades_shown = !!(q('#kb-grades') && !q('#kb-grades').hidden);
  out.grade_labels = [...document.querySelectorAll('.kb-grade')].map(T);
  const g4 = document.querySelector('.kb-grade[data-q="4"]');
  if (g4) g4.click();
  for (let i = 0; i < 60 && !q('.kb-rep'); i++) await sleep(150);
  out.report1 = !!q('.kb-rep');
  out.score1 = T(q('.kb-rep-score'));
  out.meta1 = T(q('.kb-rep-meta'));
  out.rows1 = [...document.querySelectorAll('.kb-rep-row')].map(T);
  out.report_sub1 = txt('#kb-learn-sub');
  out.again_present = !!q('#kb-mock-again');
  out.exit_present = !!q('#kb-mock-exit');
  const ag = q('#kb-mock-again');
  if (ag) ag.click();
  for (let i = 0; i < 60 && txt('#kb-learn-sub').indexOf('计时开始') < 0; i++) await sleep(150);
  out.again_sub = txt('#kb-learn-sub');
  out.again_foot = txt('#kb-learn-foot');
  out.no_report_mid = !q('.kb-rep');
  const rv2 = q('#kb-reveal'); out.reveal2 = !!rv2;
  if (rv2) rv2.click();
  await sleep(250);
  const g0 = document.querySelector('.kb-grade[data-q="0"]');
  if (g0) g0.click();
  for (let i = 0; i < 60 && !q('.kb-rep'); i++) await sleep(150);
  await sleep(300);
  out.score2 = T(q('.kb-rep-score'));
  out.meta2 = T(q('.kb-rep-meta'));
  const ex = q('#kb-mock-exit');
  if (ex) ex.click();
  for (let i = 0; i < 60 && txt('#kb-learn-sub').indexOf('到期') < 0 && txt('#kb-learn-sub').indexOf('本轮完成') < 0; i++) await sleep(150);
  out.exit_sub = txt('#kb-learn-sub');
  out.exit_no_rep = !q('.kb-rep');
  out.exit_foot = txt('#kb-learn-foot');
  out.exit_card_visible = !!(q('#kb-card') && !q('#kb-card').hidden);
  out.exit_term = txt('#kb-card-term');
  out.card_attached = !!(q('#kb-card') && document.contains(q('#kb-card')));
  return JSON.stringify(out);
})()"""

EXACT_JS = PRELUDE + r"""
  for (let i = 0; i < 60 && !(q('#kb-exact .result') || q('#kb-hits .result')); i++) await sleep(150);
  out.q1 = new URLSearchParams(location.search).get('q');
  out.exact_hidden1 = q('#kb-exact') ? !!q('#kb-exact').hidden : null;
  out.exact_head1 = txt('#kb-exact .rc-head');
  out.exact_cards1 = document.querySelectorAll('#kb-exact .result').length;
  out.exact_badge1 = txt('#kb-exact .kb-badge-exact');
  out.exact_title1 = txt('#kb-exact .result .title');
  out.hits_cards1 = document.querySelectorAll('#kb-hits .result').length;
  out.meta1 = txt('.srch-meta');
  const prev = q('#kb-hits') ? q('#kb-hits').innerHTML : '';
  history.pushState({}, '', '/search?q=' + encodeURIComponent('提示框'));
  window.dispatchEvent(new PopStateEvent('popstate'));
  for (let i = 0; i < 60 && q('#kb-hits') && q('#kb-hits').innerHTML === prev; i++) await sleep(150);
  await sleep(500);
  out.q2 = new URLSearchParams(location.search).get('q');
  out.exact_hidden2 = q('#kb-exact') ? !!q('#kb-exact').hidden : null;
  out.exact_cards2 = document.querySelectorAll('#kb-exact .result').length;
  out.hits_cards2 = document.querySelectorAll('#kb-hits .result').length;
  out.hits_head2 = txt('#kb-hits .rc-head');
  out.first_title2 = txt('#kb-hits .result .title');
  return JSON.stringify(out);
})()"""


def probe_mock(base):
    print("== 14 模拟面试（出卷 → 中途切子域被拦 → 记分 → 成绩单 → 再来一轮 → 返回普通） ==")
    api = json.loads(urllib_get(base + "/api/learn/mock?n=5") or "{}")
    n_paper = len(api.get("cards") or [])
    d = run_expr(base + "/quiz", MOCK_JS)
    check("模拟面试：入口钮由 learn.js 注入在侧栏（不是模板里写死的）",
          d.get("mock_btn_present") is True, d)
    check("模拟面试：卷长可选 5/10/20，默认选中 10",
          d.get("chips") == ["5", "10", "20"] and d.get("chip_on0") == "10", d)
    check("模拟面试：点 5 题 .on 搬到 5、点 10 能搬回来（选择态可逆）",
          d.get("chip_on5") == "5" and d.get("chip_on10") == "10", d)
    check("模拟面试：点「开考」先进出卷态（同步读到「出卷中…」，不许静默）",
          "出卷" in (d.get("mid_sub") or ""), d.get("mid_sub"))
    check("模拟面试：出卷完成后副标题写着题数与计时开始，题数 == /api/learn/mock 实发张数",
          d.get("started_sub") == f"模拟面试 · {n_paper} 题 · 计时开始" and n_paper >= 1,
          {"dom": d.get("started_sub"), "api_n": n_paper})
    check("模拟面试：底部条换成「第 1 / N 题 · 目前答对 0」（不是普通模式那行）",
          "模拟面试 · 第 1 / " in (d.get("started_foot") or "")
          and "目前答对 0" in (d.get("started_foot") or ""), d.get("started_foot"))
    check("模拟面试：中途点子域筛选必须被拦（toast 说明 + .on 不许搬）",
          "模拟面试进行中" in (d.get("mock_block_toast") or "")
          and d.get("sub_chip0") == d.get("sub_chip1") != d.get("sub_chip_pick"),
          {"toast": d.get("mock_block_toast"), "before": d.get("sub_chip0"),
           "after": d.get("sub_chip1"), "pick": d.get("sub_chip_pick")})
    check("模拟面试：翻面前评分区收着，翻面后才出，且面试只有两档（不会 / 会）",
          d.get("grades_hidden_before") is True and d.get("grades_shown") is True
          and len(d.get("grade_labels") or []) == 2, d.get("grade_labels"))
    check("模拟面试：答「会」后交卷出成绩单，分数正确率与「已计入复习排期」都在",
          d.get("report1") is True and d.get("score1") == f"1 / {n_paper}"
          and "正确率" in (d.get("meta1") or "")
          and "本次作答已计入复习排期" in (d.get("meta1") or ""),
          {"score": d.get("score1"), "meta": d.get("meta1")})
    check("模拟面试：成绩单按子域分行统计（答对 / 总数）",
          len(d.get("rows1") or []) >= 1 and "/" in (d.get("rows1") or [""])[0], d.get("rows1"))
    check("模拟面试：成绩单上两个出口钮都在位（再来一轮 / 返回普通刷题）",
          d.get("again_present") is True and d.get("exit_present") is True, d)
    check("模拟面试：「再来一轮」重新出卷并清零答卷（答对回到 0、成绩单消失）",
          "计时开始" in (d.get("again_sub") or "") and "目前答对 0" in (d.get("again_foot") or "")
          and d.get("no_report_mid") is True, {"sub": d.get("again_sub"), "foot": d.get("again_foot")})
    check("模拟面试：这轮答「不会」→ 成绩单 0 / N、正确率 0%",
          d.get("score2") == f"0 / {n_paper}" and "正确率 0%" in (d.get("meta2") or ""),
          {"score": d.get("score2"), "meta": d.get("meta2")})
    check("模拟面试：「返回普通刷题」退出模拟态（副标题回到队列口径、成绩单消失、底部条不再写模拟）",
          ("到期" in (d.get("exit_sub") or "") or "本轮完成" in (d.get("exit_sub") or ""))
          and d.get("exit_no_rep") is True and "模拟面试" not in (d.get("exit_foot") or ""),
          {"sub": d.get("exit_sub"), "foot": d.get("exit_foot")})
    # 这一条是本轮那个真缺陷的**唯一直接证据**：旧实现用 el.stage.innerHTML 写
    # "抽题中 / 成绩单"，把常驻的 #kb-card（连同 CTA / 评分区 / 底部条）一起炸掉了，
    # el.* 变成孤儿引用，之后所有渲染都写在看不见的地方。
    # （退出模拟后卡片是否"可见"取决于队列为空与否 —— 两轮把唯一那道题记分完，
    #   普通队列这时合法地是空的，所以这里断的是**节点还在文档里 + 开局真的可见**。）
    check("模拟面试：答题卡是常驻节点 —— 开局可见、跑完整条模拟后 #kb-card 仍在文档里",
          d.get("boot_card_visible") is True and d.get("card_attached") is True
          and bool(d.get("exit_term")),
          {"boot_visible": d.get("boot_card_visible"), "attached": d.get("card_attached"),
           "term": d.get("exit_term")})

    print("== 14b 搜索页精确命中区 #kb-exact ==")
    e = run_expr(base + "/search?q=" + quote("向量数据库"), EXACT_JS)
    check("精确命中：查询词与标题完全一致时 #kb-exact 不隐藏、标题写着「精确命中」",
          e.get("exact_hidden1") is False and "精确命中" in (e.get("exact_head1") or ""), e)
    check("精确命中：那一块里就是那篇文档，并带「精确命中」徽章",
          e.get("exact_cards1") == 1 and "向量数据库" in (e.get("exact_title1") or "")
          and "精确命中" in (e.get("exact_badge1") or ""), e)
    check("精确命中：命中区自己声明「标题与查询词完全一致」的口径",
          "标题与查询词完全一致" in (e.get("exact_head1") or ""), e.get("exact_head1"))
    check("精确命中：换成只出现在正文里的词，#kb-exact 必须整块收起（不许留空壳）",
          e.get("exact_hidden2") is True and e.get("exact_cards2") == 0, e)
    check("精确命中：切换后常规列表仍有结果（不是把结果一起清没了）",
          (e.get("hits_cards2") or 0) >= 1 and "全部命中" in (e.get("hits_head2") or ""), e)


# ================================================================ 探针 15：治理页孤儿折叠 / 豁免
# 台账 §2 行「治理 · #orphan-expand」。折叠线写死在 30 篇（`items.slice(0, 30)` +
# `hidden = items.length <= 30`），P5 的语料只有几篇 —— 那一档**从来没进过**。
ORPHAN_JS = PRELUDE + r"""
  const T = e => ((e && e.textContent) || '').replace(/\s+/g, ' ').trim();
  const rows = () => document.querySelectorAll('#list-orphans .gov-item').length;
  const eb = q('#orphan-expand');
  const shot = () => ({hidden: !!eb.hidden, text: T(eb), bound: typeof eb.onclick === 'function'});
  out.expand_before_scan = shot();
  q('#gov-scan-btn').click();
  for (let i = 0; i < 120 && !(q('#gov-result') && !q('#gov-result').hidden); i++) await sleep(150);
  out.scanned = !!(q('#gov-result') && !q('#gov-result').hidden);
  out.summary = txt('#gov-summary');
  out.cnt_orphan = T(q('#cnt-orphan'));
  document.querySelector('.gov-tab[data-bucket="orphans"]').click();
  await sleep(300);
  out.pane_on = !!document.querySelector('.gov-tab[data-bucket="orphans"]').classList.contains('on');
  out.rows_collapsed = rows();
  out.more_collapsed = T(q('#list-orphans .gov-more'));
  out.after_scan = shot();
  eb.click();
  await sleep(450);
  out.rows_expanded = rows();
  out.more_expanded = T(q('#list-orphans .gov-more'));
  out.text_expanded = T(eb);
  out.hidden_expanded = !!eb.hidden;
  eb.click();
  await sleep(450);
  out.rows_again = rows();
  out.text_again = T(eb);
  out.more_again = T(q('#list-orphans .gov-more'));
  let clicks = 0;
  eb.click();                                     // 展开态下逐条豁免，保证每篇都在 DOM 里
  await sleep(400);
  while (document.querySelector('#list-orphans .gov-wl') && clicks < 120) {
    document.querySelector('#list-orphans .gov-wl').click();
    clicks++;
    await sleep(50);
  }
  out.wl_clicks = clicks;
  out.ls_wl = JSON.parse(localStorage.getItem('kb-gov-orphan-whitelist') || '[]');
  out.rows_after_wl = rows();
  out.none_text = T(q('#list-orphans .gov-none'));
  out.after_wl = shot();
  out.toast = T(q('#toast'));
  return JSON.stringify(out);
})()"""


ORPHAN_EMPTY_JS = PRELUDE + r"""
  const T = e => ((e && e.textContent) || '').replace(/\s+/g, ' ').trim();
  const eb = q('#orphan-expand');
  out.wl_seeded = JSON.parse(localStorage.getItem('kb-gov-orphan-whitelist') || '[]').length;
  q('#gov-scan-btn').click();
  for (let i = 0; i < 120 && !(q('#gov-result') && !q('#gov-result').hidden); i++) await sleep(150);
  document.querySelector('.gov-tab[data-bucket="orphans"]').click();
  await sleep(350);
  out.rows = document.querySelectorAll('#list-orphans .gov-item').length;
  out.none_text = T(q('#list-orphans .gov-none'));
  out.after_scan = {hidden: !!eb.hidden, text: T(eb), bound: typeof eb.onclick === 'function'};
  return JSON.stringify(out);
})()"""


def probe_orphan_expand(base, tmp):
    print("== 15 治理页孤儿桶：>30 篇折叠 / 展开全部 / 逐条豁免到清空 ==")
    scan = json.loads(urllib_get(base + "/api/governance/scan") or "{}")
    total = len(scan.get("orphans") or [])
    d = run_expr(base + "/governance", ORPHAN_JS)
    check("孤儿折叠：扫描完成后计数 == 接口条数，且必须 >30（否则这一档根本进不去）",
          d.get("cnt_orphan") == str(total) and total > 30,
          {"dom": d.get("cnt_orphan"), "api": total})
    check("孤儿折叠：默认只显示前 30 篇，并写明「还有 N 篇未显示」",
          d.get("rows_collapsed") == 30 and "还有" in (d.get("more_collapsed") or "")
          and str(total - 30) in (d.get("more_collapsed") or ""), d.get("more_collapsed"))
    check("孤儿折叠：>30 时钮可见、文案「展开全部」、且真的绑上了处理函数",
          d.get("after_scan", {}).get("hidden") is False
          and "展开全部" in (d.get("after_scan", {}).get("text") or "")
          and d.get("after_scan", {}).get("bound") is True, d.get("after_scan"))
    check("孤儿折叠：点「展开全部」列出全部 N 篇、折叠提示消失、文案翻成「收起」",
          d.get("rows_expanded") == total and (d.get("more_expanded") or "") == ""
          and "收起" in (d.get("text_expanded") or "") and d.get("hidden_expanded") is False,
          {"rows": d.get("rows_expanded"), "api": total, "text": d.get("text_expanded")})
    check("孤儿折叠：点「收起」回到 30 篇、提示回来（状态可逆）",
          d.get("rows_again") == 30 and "还有" in (d.get("more_again") or "")
          and "展开全部" in (d.get("text_again") or ""), d.get("more_again"))
    check("孤儿豁免：逐条点完的次数 == 孤儿总数（每点一次重画一次，没有点到就消失的空档）",
          d.get("wl_clicks") == total, {"clicks": d.get("wl_clicks"), "api": total})
    check("孤儿豁免：白名单落在 localStorage，条目数 == 豁免数",
          len(d.get("ls_wl") or []) == total, {"ls": len(d.get("ls_wl") or []), "api": total})
    check("孤儿豁免：清空后写明「没有孤儿文档（已豁免 N 篇）」",
          "没有孤儿文档" in (d.get("none_text") or "") and str(total) in (d.get("none_text") or ""),
          d.get("none_text"))
    check("孤儿豁免：列表空了以后「展开全部」必须跟着藏起来（不许留一个点了没反应的钮）",
          d.get("rows_after_wl") == 0 and d.get("after_wl", {}).get("hidden") is True,
          d.get("after_wl"))
    check("豁免只写本地白名单：磁盘上那 34 篇孤儿 md 一篇没少（不改语料）",
          len(list((tmp / "content" / "ui-r" / "orphans").glob("*.md"))) == ORPHAN_COUNT,
          len(list((tmp / "content" / "ui-r" / "orphans").glob("*.md"))))

    # 15b **首屏就 0 孤儿**那一档。`renderOrphans` 在 items 为空时是提前 return 的，
    # 而模板里的 `<button id="orphan-expand">` 没有 hidden 初值 —— 逐条豁免清空时
    # 上一轮已经把 hidden 设过了（所以 15 里那条是绿的），但"扫出来就是 0 篇"
    # 根本走不到那一行。用 KB_GEOM_INIT 在页面脚本之前把全量白名单灌进
    # localStorage，就能把这一档单独造出来测。
    paths = [o.get("path") for o in (scan.get("orphans") or [])]
    seed = ("try{localStorage.setItem('kb-gov-orphan-whitelist', %s);}catch(e){}"
            % json.dumps(json.dumps(paths, ensure_ascii=False)))
    e = run_expr(base + "/governance", ORPHAN_EMPTY_JS, init=seed)
    check("孤儿空态（首屏 0 篇）：空态文案写明「没有孤儿文档（已豁免 N 篇）」",
          "没有孤儿文档" in (e.get("none_text") or "")
          and str(len(paths)) in (e.get("none_text") or ""), e.get("none_text"))
    check("孤儿空态（首屏 0 篇）：「展开全部」不许留成一个点了没反应的死钮",
          e.get("after_scan", {}).get("hidden") is True and (e.get("rows") or 0) == 0,
          e.get("after_scan"))


# ================================================================ 探针 16：crumb 标签 chips / 标签钮 / 编辑器提示 / 左树打开
# 台账 §2 四行：「#crumb-tags 标签 chips」「标签 jumpToTagEdit()」「编辑器 #ed-hint」
# 「域内文档 .doc 打开」。这一组的共同点是"看着在、点了不知道去哪"。
CRUMB_JS = PRELUDE + r"""
  const T = e => ((e && e.textContent) || '').replace(/\s+/g, ' ').trim();
  for (let i = 0; i < 80 && !q('#crumb-tags'); i++) await sleep(150);
  await sleep(600);
  out.chips = [...document.querySelectorAll('#crumb-tags .tag-chip')]
    .map(x => T(x));
  out.chips_html_len = ((q('#crumb-tags') || {}).innerHTML || '').length;
  const tagBtn = [...document.querySelectorAll('#crumb .seg-btn, .crumb .seg-btn')]
    .filter(b => T(b).indexOf('标签') >= 0)[0];
  out.tag_btn = tagBtn ? T(tagBtn) : '';
  out.info_tab_active_before = !!document.querySelector('.rtab[data-pane="info"].active');
  out.inputrow_hidden_before = !!(q('#tag-inputrow') && q('#tag-inputrow').hidden);
  if (tagBtn) tagBtn.click();
  await sleep(700);
  out.info_tab_active = !!document.querySelector('.rtab[data-pane="info"].active');
  out.pane_info_active = !!document.querySelector('#pane-info.active');
  out.inputrow_hidden_after = !!(q('#tag-inputrow') && q('#kb-tag-in, #tag-in') && q('#tag-inputrow').hidden);
  out.focus_after = document.activeElement ? document.activeElement.id : '';
  out.add_btn = !!q('#tag-add-btn');
  // 再点一次：输入框已在 → 走"只聚焦不重开"那一支
  if (tagBtn) tagBtn.click();
  await sleep(500);
  out.focus_second = document.activeElement ? document.activeElement.id : '';
  out.inputrow_still_open = !!(q('#tag-inputrow') && !q('#tag-inputrow').hidden);
  // 元信息表（同一页顺手断，右栏这时已经切到 info 页）
  out.kv = [...document.querySelectorAll('#pane-info .rp-card .kv')]
    .map(x => [T(x.querySelector('.k')), T(x.querySelector('.v'))]);
  // 编辑器提示：开 → 可见；关 → 收起
  out.hint_before = q('#ed-hint') ? (q('#ed-hint').style.display || '(空=跟随CSS)') : null;
  const editBtn = [...document.querySelectorAll('#crumb .seg-btn, .crumb .seg-btn')]
    .filter(b => T(b).indexOf('编辑') >= 0)[0];
  out.edit_btn = editBtn ? T(editBtn) : '';
  if (editBtn) editBtn.click();
  for (let i = 0; i < 40 && !(q('#editor') && q('#editor').classList.contains('show')); i++) await sleep(150);
  out.editor_open = !!(q('#editor') && q('#editor').classList.contains('show'));
  out.hint_open = q('#ed-hint') ? (q('#ed-hint').style.display || '') : null;
  out.hint_text = txt('#ed-hint');
  window.tryCloseEditor ? window.tryCloseEditor() : (document.querySelector('#ed-cancel') || {click() {}}).click();
  await sleep(600);
  out.hint_closed = q('#ed-hint') ? (q('#ed-hint').style.display || '') : null;
  out.editor_closed = !(q('#editor') && q('#editor').classList.contains('show'));
  return JSON.stringify(out);
})()"""

def probe_head_chips(base):
    print("== 16 crumb 标签 chips / jumpToTagEdit / 元信息表 / 编辑器提示 ==")
    doc = json.loads(urllib_get(base + "/api/doc?domain=ui-r&sub=notes&name=alpha") or "{}")
    want_tags = [t for t in ((doc.get("doc") or {}).get("fm") or {}).get("tags", [])] if (doc.get("doc") or {}).get("fm") else []
    want_kv = [[k, v] for k, v in (doc.get("info_rows") or [])]
    d = run_expr(base + "/doc/ui-r/notes/alpha.md", CRUMB_JS)
    chips = [c.strip("#") for c in (d.get("chips") or [])]
    check("crumb 标签：渲染出的 chips 与 frontmatter 的 tags 逐项一致（不是写死三份）",
          d.get("chips_html_len", 0) > 0 and sorted(chips) == sorted(want_tags) and len(want_tags) >= 2,
          {"dom": chips, "api": want_tags})
    check("crumb 标签：「标签」钮在位（它是跳右栏编辑的唯一入口）",
          "标签" in (d.get("tag_btn") or ""), d.get("tag_btn"))
    check("jumpToTagEdit：右栏切到「信息」页签（pane 与 rtab 同时 active）",
          d.get("info_tab_active_before") is False and d.get("info_tab_active") is True
          and d.get("pane_info_active") is True, d)
    check("jumpToTagEdit：标签输入行被自动展开（原来 hidden，点完不 hidden）",
          d.get("inputrow_hidden_before") is True and d.get("inputrow_hidden_after") is False
          and d.get("add_btn") is True, d)
    check("jumpToTagEdit：焦点真的落到输入框（rAF 延后那一帧在无头里也成立）",
          d.get("focus_after") == "tag-in" and d.get("focus_second") == "tag-in",
          {"first": d.get("focus_after"), "second": d.get("focus_second")})
    check("元信息表：来源/原始位置/收录日期/状态/大小 五行都在，值逐项等于 /api/doc 的 info_rows",
          d.get("kv") == want_kv and len(want_kv) == 5, {"dom": d.get("kv"), "api": want_kv})
    check("编辑器提示：开编辑态前是收着的，开完可见且文案讲清了 frontmatter 契约",
          d.get("hint_before") == "none" and (d.get("hint_open") or "") in ("", "block")
          and "frontmatter" in (d.get("hint_text") or "").lower(),
          {"before": d.get("hint_before"), "open": d.get("hint_open"), "text": d.get("hint_text")})
    check("编辑器提示：关编辑器时提示一起收起（不留一块没人认领的说明区）",
          d.get("editor_closed") is True and d.get("hint_closed") == "none", d)


TREE_JS = PRELUDE + r"""
  const T = e => ((e && e.textContent) || '').replace(/\s+/g, ' ').trim();
  for (let i = 0; i < 80 && !q('#tree .doc'); i++) await sleep(150);
  await sleep(700);
  out.path = location.pathname;
  out.doc_title = document.title;
  out.sb = txt('#sb-path');
  out.head = txt('#article h1') || txt('#article .a-title');
  out.active_now = [...document.querySelectorAll('#tree .doc.active')].map(a => a.dataset.name);
  out.tree_has_beta = !!document.querySelector('#tree .doc[data-name="beta"]');
  out.tree_docs = [...document.querySelectorAll('#tree .doc')].map(a => a.dataset.name);
  return JSON.stringify(out);
})()"""


def probe_tree_open(base):
    print("== 16b 左分类树 · 域内文档 .doc 打开（点了真的换文档） ==")
    # 树默认全部收起（app.js 的既定行为），所以先把 ui-r 域"展开"写进 localStorage 再进页面
    init = "try{localStorage.setItem('kb-tree-open', JSON.stringify(['ui-r']));}catch(e){}"
    url = base + "/doc/ui-r/notes/alpha.md"
    before = run_expr(url, TREE_JS, init=init)
    after = run_expr(url, TREE_JS, click='#tree .doc[data-name="beta"]', init=init)
    check("左树：域展开后子域里的文档逐条成节点（alpha/beta/gamma 都在）",
          before.get("tree_has_beta") is True
          and {"alpha", "beta", "gamma"} <= set(before.get("tree_docs") or []), before)
    check("左树：当前打开的那一篇在树上带 .active（本轮修的就是它恒空 —— 见 §6 第 37 行）",
          before.get("active_now") == ["alpha"], {"active": before.get("active_now")})
    # SPA 切页后状态栏那行写的是**不带 .md** 的名字（服务端直载时才是 alpha.md）——
    # 两种形态都算"换到了那一篇"，这里只断它提到了 beta 且不再提 alpha。
    check("左树：点文档节点真的换页（URL 与底部状态栏的路径一起变成那一篇，docUrl 削掉 .md 后缀）",
          (after.get("path") or "").endswith("/doc/ui-r/notes/beta")
          and "beta" in (after.get("sb") or "") and "alpha" not in (after.get("sb") or ""),
          {"path": after.get("path"), "sb": after.get("sb")})
    check("左树：换页后高亮跟着搬到那一条（不是只有画面换了、树还标着旧文档）",
          after.get("active_now") == ["beta"], {"active": after.get("active_now")})


# ================================================================ 探针 17：新标签页 /raw + 美化版只读态
PRETTY_JS = PRELUDE + r"""
  const T = e => ((e && e.textContent) || '').replace(/\s+/g, ' ').trim();
  for (let i = 0; i < 80 && !q('#crumb'); i++) await sleep(150);
  await sleep(700);
  out.path = location.pathname;
  const segT = b => T(b);
  out.segs = [...document.querySelectorAll('#crumb .seg-btn')].map(segT);
  const raw = document.querySelector('#crumb a.seg-btn[href^="/raw/"]');
  out.raw_href = raw ? raw.getAttribute('href') : null;
  out.raw_target = raw ? raw.getAttribute('target') : null;
  out.has_edit = out.segs.some(s => s.indexOf('编辑') >= 0 && s.indexOf('标签') < 0);
  out.has_del = out.segs.some(s => s.indexOf('删除') >= 0);
  out.has_tagbtn = out.segs.some(s => s.indexOf('标签') >= 0);
  const infoTab = document.querySelector('.rtab[data-pane="info"]');
  if (infoTab) infoTab.click();
  await sleep(600);
  out.readonly = !!document.querySelector('#pane-info .tag-edit.readonly');
  out.add_btn = !!document.querySelector('#pane-info #tag-add-btn');
  out.rm_btns = document.querySelectorAll('#pane-info .tagchip-x').length;
  out.tag_state = T(document.querySelector('#pane-info .tag-empty'));
  out.chips_in_crumb = [...document.querySelectorAll('#crumb-tags .tag-chip')].map(T);
  out.pretty_mode = !!(document.querySelector('#article') || {}).classList
    && document.querySelector('#article').classList.contains('pretty-mode');
  // 完整 HTML 文档 → mountHtmlDoc 把 #html-render 整个换成 <iframe class="html-frame" sandbox=…>；
  // 作用域片段 → 换成 .html-inline 的 Shadow DOM 宿主。两种都算"内嵌渲染成功"。
  const fr = document.querySelector('#article iframe.html-frame');
  out.frame_src = fr ? (fr.getAttribute('src') || '') : null;
  out.frame_sandbox = fr ? (fr.getAttribute('sandbox') || '') : null;
  out.inline_host = !!document.querySelector('#article .html-inline');
  out.skeleton_gone = !document.querySelector('#article .kb-skeleton');
  return JSON.stringify(out);
})()"""


def probe_pretty(base):
    print("== 17 同名美化版：新标签页出口 + 美化版只读态 ==")
    md = run_expr(base + "/doc/ui-r/notes/beta.md", PRETTY_JS)
    check("新标签页：有美化版的 .md 在 crumb 上给出 /raw/<同名 .html> 出口且新开标签",
          md.get("raw_href") == "/raw/ui-r/notes/beta.html" and md.get("raw_target") == "_blank", md)
    body = urllib_get(base + md["raw_href"]) if md.get("raw_href") else ""
    check("新标签页指向的那个 /raw 地址真的能取到美化版本体（不是 404 也不是 md 原文）",
          "美化版（iframe 直服）" in body and "排版约定样本-B" not in body, body[:140])
    check("美化版视图默认走内嵌渲染（.pretty-mode + 骨架屏换成 iframe/Shadow，不是停在骨架）",
          md.get("pretty_mode") is True and (md.get("frame_src") == "/raw/ui-r/notes/beta.html"
          or md.get("inline_host") is True) and md.get("skeleton_gone") is True, md)
    check("美化版 iframe 带 sandbox（同域只放行 same-origin + popups，不给脚本）",
          (md.get("frame_src") or "").startswith("/raw/")
          and md.get("frame_sandbox") == "allow-same-origin allow-popups",
          {"src": md.get("frame_src"), "sandbox": md.get("frame_sandbox")})
    check("可写的那一侧（.md）编辑/删除/标签三个钮齐全（对照组：美化版必须没有）",
          md.get("has_edit") is True and md.get("has_del") is True and md.get("has_tagbtn") is True,
          md.get("segs"))
    html = run_expr(base + "/doc/ui-r/notes/beta.html", PRETTY_JS)
    check("美化版只读态：.html 本体不给出「编辑」「删除」「标签」三个写入口",
          html.get("has_edit") is False and html.get("has_del") is False
          and html.get("has_tagbtn") is False, html.get("segs"))
    check("美化版只读态：右栏标签区是 readonly（没有添加钮、没有逐条移除叉）",
          html.get("readonly") is True and html.get("add_btn") is False
          and html.get("rm_btns") == 0, html)
    check("美化版只读态：空态文案说实话（「美化版不支持在线编辑标签」而不是「还没有标签」）",
          "美化版" in (html.get("tag_state") or ""), html.get("tag_state"))


# ================================================================ 探针 18：#kb-finish-bar 读完 / 掌握
FINISH_JS = PRELUDE + r"""
  const T = e => ((e && e.textContent) || '').replace(/\s+/g, ' ').trim();
  const rb = () => q('#mark-read-btn'), mb = () => q('#mark-mastered-bar, #mark-mastered-btn');
  for (let i = 0; i < 80 && !rb(); i++) await sleep(150);
  await sleep(700);
  out.bar_present = !!q('#kb-finish-bar');
  const snap = () => ({r_on: rb().classList.contains('mark-on'), r_txt: T(rb()),
                       m_on: mb().classList.contains('mark-on'), m_txt: T(mb())});
  out.s0 = snap();
  rb().click();
  for (let i = 0; i < 40 && !rb().classList.contains('mark-on'); i++) await sleep(150);
  out.t_read = txt('#toast');
  out.s1 = snap();
  mb().click();
  for (let i = 0; i < 40 && !mb().classList.contains('mark-on'); i++) await sleep(150);
  out.s2 = snap();
  out.t_mastered = txt('#toast');
  rb().click();                        // 取消"读完" —— 契约：掌握一并取消
  for (let i = 0; i < 40 && rb().classList.contains('mark-on'); i++) await sleep(150);
  await sleep(400);
  out.s3 = snap();
  out.t_unread = txt('#toast');
  out.disabled_after = rb().disabled;
  return JSON.stringify(out);
})()"""


def probe_finish_bar(base, tmp):
    print("== 18 正文底部「读完 / 已掌握」条（写 reading.db，不写语料） ==")
    f = tmp / "content" / "ui-r" / "notes" / "alpha.md"
    before = f.read_bytes()
    d = run_expr(base + "/doc/ui-r/notes/alpha.md", FINISH_JS)
    check("读完条：条与两个钮在正文末尾渲染出来", d.get("bar_present") is True, d)
    check("读完条：初始两个钮都是未标记态（文案没有 ✓、没有 .mark-on）",
          d.get("s0", {}).get("r_on") is False and "✓" not in (d.get("s0", {}).get("r_txt") or ""),
          d.get("s0"))
    check("读完条：点「已读完」→ .mark-on + 文案翻成「✓ 已读完」+ toast 回执",
          d.get("s1", {}).get("r_on") is True and "已读完" in (d.get("s1", {}).get("r_txt") or "")
          and "✓" in (d.get("s1", {}).get("r_txt") or "")
          and "已标记读完" in (d.get("t_read") or ""), {"s1": d.get("s1"), "toast": d.get("t_read")})
    check("掌握条：点「已掌握」独立生效（术语门户据此显示已掌握）",
          d.get("s2", {}).get("m_on") is True and "已掌握" in (d.get("t_mastered") or ""),
          {"s2": d.get("s2"), "toast": d.get("t_mastered")})
    check("取消「已读完」必须连带取消「已掌握」（两个标记是一个学习闭环，不能留半截）",
          d.get("s3", {}).get("r_on") is False and d.get("s3", {}).get("m_on") is False
          and "一并取消" in (d.get("t_unread") or ""), {"s3": d.get("s3"), "toast": d.get("t_unread")})
    check("标记写的是派生库：那篇 md 的字节一个都没变",
          f.read_bytes() == before, "frontmatter/正文被标记动作改写过")
    srv = json.loads(urllib_get(base + "/api/docmark?path=" + quote("ui-r/notes/alpha.md")) or "{}")
    check("标记的最终状态与后端一致（服务端 read/mastered 都是 False）",
          srv.get("ok") is True and not srv.get("read") and not srv.get("mastered"), srv)


# ================================================================ 探针 19：#kb-toc-spark 近 7 日阅读
# 台账 §2 行「正文区 · #kb-toc-spark」——轮次 21 曾把它列为"主动放弃"（读 reading.db、
# 像素基线里被 FREEZE_CSS 隐掉）。现在两档都补上：先经 /api/track（应用自己的写路径）
# 造两天的事件断"有数据时画得出、数字对得上"，再用 init 打桩让接口回全 0，断空态文案。
SPARK_SEED_JS = PRELUDE + r"""
  const post = (path, event) => fetch('/api/track', {method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({path, event, seconds: 60})}).then(r => r.json());
  out.a = await post('ui-r/notes/alpha.md', 'open');
  out.b = await post('ui-r/notes/beta.md', 'open');
  out.c = await post('ui-r/notes/gamma.md', 'open');
  out.d = await post('ui-r/notes/gamma.md', 'finish');
  return JSON.stringify(out);
})()"""

SPARK_JS = PRELUDE + r"""
  const T = e => ((e && e.textContent) || '').replace(/\s+/g, ' ').trim();
  for (let i = 0; i < 80 && !q('#kb-toc-spark'); i++) await sleep(150);
  await sleep(1200);
  const host = q('#kb-toc-spark');
  out.host_present = !!host;
  out.meta = txt('.kb-toc-spark-meta');
  out.empty_txt = txt('.kb-toc-spark-empty');
  const cv = host ? host.querySelector('canvas') : null;
  out.canvas = !!cv;
  out.aria = cv ? (cv.getAttribute('aria-label') || '') : '';
  const ch = window.Chart && cv ? window.Chart.getChart(cv) : null;
  out.labels = ch ? ch.data.labels : null;
  out.data = ch ? ch.data.datasets[0].data : null;
  return JSON.stringify(out);
})()"""


def probe_toc_spark(base):
    print("== 19 目录火花 #kb-toc-spark（近 7 日阅读：有数据画柱 / 全 0 说没阅读） ==")
    run_expr(base + "/doc/ui-r/notes/alpha.md", SPARK_SEED_JS)
    api = json.loads(urllib_get(base + "/api/learn/recent_read") or "{}")
    days = api.get("days") or []
    d = run_expr(base + "/doc/ui-r/notes/alpha.md", SPARK_JS)
    counts = [x.get("count") for x in days]
    check("目录火花：右栏目录下方长出了 #kb-toc-spark 容器", d.get("host_present") is True, d)
    check("目录火花：有数据时是 canvas 柱图（带无障碍标签），不是占位文字",
          d.get("canvas") is True and "近 7 日阅读篇数" in (d.get("aria") or ""), d)
    check("目录火花：柱子的 7 个日标签与逐日篇数 == /api/learn/recent_read（不编数、不合并）",
          d.get("labels") == [str(x.get("date", ""))[8:10] for x in days]
          and d.get("data") == counts and len(counts) == 7,
          {"labels": d.get("labels"), "data": d.get("data"), "api": counts})
    peak = max(counts) if counts else 0
    avg = (sum(counts) / len(counts)) if counts else 0
    check("目录火花：meta 那行写着峰值与日均，数字来自同一份序列",
          f"峰值 {peak} 篇" in (d.get("meta") or "") and f"日均 {avg:.1f} 篇" in (d.get("meta") or ""),
          {"meta": d.get("meta"), "peak": peak, "avg": round(avg, 1)})
    # 空态：把 /api/learn/recent_read 打桩成全 0（只动这一条 URL，其余照常）
    stub = ("(function(){const f=window.fetch;window.fetch=function(u,o){"
            "if(String(u).indexOf('/api/learn/recent_read')>=0){"
            "return Promise.resolve(new Response(JSON.stringify({ok:true,days:"
            "Array.from({length:7},(_,i)=>({date:'2026-09-' + (10+i),count:0})),total:0}),"
            "{status:200,headers:{'Content-Type':'application/json'}}));}"
            "return f.apply(window,arguments);};})()")
    e = run_expr(base + "/doc/ui-r/notes/alpha.md", SPARK_JS, init=stub)
    check("目录火花：全 0 序列必须落到「近 7 日暂无阅读」空态（不许留一根空柱子或转圈的省略号）",
          "近 7 日暂无阅读" in (e.get("empty_txt") or "") and e.get("canvas") is False,
          {"empty": e.get("empty_txt"), "canvas": e.get("canvas"), "meta": e.get("meta")})


# ================================================================ 探针 20：左树打开见 probe_tree_open


def only(name) -> bool:
    """开发期单跑某一探针：`python tests/test_ui_behavior.py nav`。
    不带参数 = 全跑（pre-commit / CI 走的就是全跑）。"""
    return not ONLY or ONLY in name


def run_probe(name, fn, *args):
    if only(name):
        fn(*args)
    else:
        print(f"-- 跳过探针 {name}（KB_BEHAVIOR_ONLY={ONLY or '未设'}）")


def main() -> int:
    global PORT
    if not node_available() or not shutil.which("node"):
        print("SKIP: 找不到 node")
        return 0
    if not chrome_path():
        print("SKIP: 找不到 Chrome")
        return 0
    # 探针 1 断的是"无 key 的 503 降级分支"。这台机器哪天配了 KB_AI_API_KEY，
    # 那条断言就会变成"真去请求外部 LLM" —— 既红得没道理，也违反"不联网"。
    os.environ.pop("KB_AI_API_KEY", None)

    tmp = Path(tempfile.mkdtemp(prefix="ui-behavior-"))
    proc = None
    t0 = time.time()
    try:
        build_root(tmp)
        shutil.copytree(ROOT / "static", tmp / "static")   # create_app 的 static_folder 在 KB_ROOT 下
        PORT = free_port()
        check("端口现挑且不落在用户常驻端口", PORT not in (5000, 5001, 5031), f"port={PORT}")
        QA.mkdir(parents=True, exist_ok=True)
        proc = start_instance(tmp, PORT, log_path=QA / "instance-behavior.log")
        check("临时实例起来了", port_open(PORT))
        base = f"http://127.0.0.1:{PORT}"

        # 顺序有讲究：**破坏性探针一律排最后**，且排在"要用到那些文档"的探针之后。
        # 第一版把删除放在看板抽屉之前，结果 /tags 的标签云里已经没有「渲染」这个标签
        # （承载它的 alpha/gamma 都被删了），6 条断言集体假红（轮次 24 实测）。
        run_probe("nav", probe_nav, base, tmp)          # 一级导航 + 徽标（只读，且要在删除类探针之前拿基线数）
        run_probe("ask", probe_ask, base)               # 只读（503 降级分支）
        run_probe("wikilink", probe_wikilink, base)     # 只改编辑器缓冲，不落盘
        run_probe("tag", probe_tag_suggest, base)       # 只读（要右栏渲染出来 → 见 PROBE_WIDTH 注释）
        run_probe("mermaid", probe_mermaid, base, tmp)  # 只读 /raw
        run_probe("asset", probe_asset_rewrite, base)   # 只读 /raw（顺带把 §5 那格补上）
        run_probe("pref", probe_prefs, base)            # 只写 localStorage（不动语料；每趟自带新 profile）
        run_probe("drawer", probe_drawer, base)         # 只读 /tags，但依赖上面的标签还在
        run_probe("home", probe_home_today, base)       # 只读：首页今日学习卡（必须在下面两个记分探针之前）
        run_probe("glossary", probe_glossary, base)     # 读 + 一次「加入复习」记分（baike 卡）
        run_probe("mock", probe_mock, base)             # 读 + 面试卡记分；14b 只读 /search
        run_probe("orphans", probe_orphan_expand, base, tmp)   # 只写 localStorage 白名单
        run_probe("chips", probe_head_chips, base)             # 只读：chips / 右栏跳转 / 元信息 / 编辑提示
        run_probe("tree", probe_tree_open, base)          # 只读：点树里的文档真的换页
        run_probe("pretty", probe_pretty, base)           # 只读：美化版出口与只读态
        run_probe("finish", probe_finish_bar, base, tmp)  # 写 reading.db 的 doc_marks（不动语料）
        run_probe("spark", probe_toc_spark, base)         # 写 reading.db 的事件（派生库，不动语料）
        run_probe("newdoc", probe_newdoc, base, tmp)    # 写：在空子域里建一篇
        run_probe("inbox", probe_inbox, base, tmp)      # 写：_trash 软删 + 物理 purge（只动 _inbox 两个靶子）
        run_probe("crumb", probe_crumb_delete, base, tmp)    # 写：删 gamma
        run_probe("eddel", probe_editor_delete, base, tmp)   # 写：删 alpha + 它的备注旁挂 —— 必须最后
    finally:
        kill_instance(proc)
        shutil.rmtree(tmp, ignore_errors=True)
        # 收尾：本套写的全在临时根里，真实语料与仓库 indexes/ 一个字节都不该动
        check("清理只删掉了系统临时目录下的临时根", not tmp.exists()
              and str(tmp).startswith(tempfile.gettempdir())
              and (ROOT / "content").is_dir(), f"tmp={tmp}")

    print(f"\nUI 行为回归 {passed} 断言全部通过" if not failed
          else f"\n{passed} passed, {failed} failed")
    if failed:
        for n in FAILURES:
            print(f"  - {_safe(n)}")
    print(f"耗时 {round(time.time() - t0)}s")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
