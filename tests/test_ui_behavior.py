# -*- coding: utf-8 -*-
"""知库 UI 行为回归（第 13 套）—— 台账 §2 那 9 行「未测」控件的交互后状态。

运行：python tests/test_ui_behavior.py   （缺 node/Chrome 自动 SKIP）

为什么单独一套而不是塞进 P5：P5 的判据是"和上次像素一样吗"，而"点下去有没有反应"是
另一类问题 —— 重叠、恒 0 结果、点了没反应这类缺陷在像素基线里是**稳定地错**（台账 §6 第 29 行）。
本套也不与 test_js_props 合并：那套管的是**解析器**（zip/txt/切块），语义不同，混在一起
会让"改了书库解析"和"改了按钮行为"都顶起同一套红。

覆盖的 9 行（台账 §2）：
  1 问吧 showAsk()          2 空态入口 #kb-empty-newdoc    3 编辑器 #ed-del
  4 [[ 双链补全浮层         5 标签补全浮层                  6 mermaid 点击放大 #kb-zoom-ov
  7 crumb 删除              8 收件箱 del / purge            9 标签页看板抽屉 #drawer-h/#drawer-docs

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
}


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
