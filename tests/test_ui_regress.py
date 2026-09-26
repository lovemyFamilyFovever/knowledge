# -*- coding: utf-8 -*-
"""知库 **P5 · 视觉回归批处理**（把"改 A 崩 B"从手工截图对比变成门禁）。

运行：
    python tests/test_ui_regress.py                # 截图 + 与基线比对（无基线则报错并提示 --update）
    python tests/test_ui_regress.py --update       # 用本次截图刷新基线（改完 UI 确认无误后执行）
    python tests/test_ui_regress.py --stability    # 不比对基线，只把同一份代码截两遍互比：
                                                   #   先证明"harness 自己是确定的"，再谈基线有无意义

为什么需要它：AGENTS 的「UI 回归纪律」要求改 css/js/模板后跑 imgdiff，但那句话在过去两个月里
每次都靠人（我）记得。记不住 = 纪律不存在。本轮把「页面 × 主题 × 点击态」的截图矩阵落成一条命令。

三条硬约束（改本文件前先读）：
  · 语料**全部现造**在临时 KB_ROOT 下的合成小库（见 CORPUS），一个字节的真实 content/ 都不进画面
    —— 基线 PNG 要提交进 git，画面里不能出现用户的内容与标题；
  · 实例端口现挑，绝不占用户的 5001（见 tests/_tmpapp.py）；
  · 一切动态内容（时间、阅读统计、耗时计数、动效）必须在截图前被钉死或显式冻结，否则基线每天红。
    `/stats` 只有用 `?ym=` 钉死到**没有阅读数据的过去月**才进得了矩阵；搜索页的 `took_ms`
    一类运行时计数由 FREEZE_CSS 直接隐掉（见那里的注释）。
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ci  # noqa: E402  缺依赖 SKIP 时给 CI 留 annotation（见 tests/_ci.py）
from _tmpapp import (chrome_path, free_port, kill_instance, magick_available,  # noqa: E402
                     node_available, port_open, start_instance)

ROOT = Path(__file__).resolve().parents[1]
BASELINES = ROOT / "tests" / "ui-baselines"
QA = ROOT / ".qa" / "p5"
PORT = None                     # main() 里现挑
# 判定口径：**差异像素数 AE ≤ 2**，不是"差异占比 < 百分之几"。
# 为什么不用 imgdiff 的默认 2% 容差 + 百分比阈值（我第一版就是这么写的）：
#   实测同一份代码截两遍，在 fuzz=0% 下 8 张里有 7 张 AE=0、1 张 AE=1，噪声地板就是 0~1 像素；
#   而把模板里"分类目录"改成别的文字，AE 只有 ~350 像素 = 0.027%，
#   在"占比 ≤0.05%"的口径下**判成绿**——一处真实的小范围文字/样式回归被容差吃掉了。
#   噪声地板既然是 0，容差就该贴着 0 定，而不是照抄"截图对比留点余量"的直觉。
MAX_DIFF_AE = 2                 # 允许的差异像素数（噪声地板实测 0~1px）
FUZZ = "0%"                     # 逐像素严格比较

passed = failed = 0


def _safe(s):
    """控制台（GBK）能印什么就印什么，印不了的换成 ?。详见 test_js_props.py 同款注释。"""
    s = str(s)
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        s.encode(enc)
        return s
    except (UnicodeEncodeError, LookupError, ValueError):
        return s.encode(enc, "replace").decode(enc, "replace")


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS {_safe(name)}")
    else:
        failed += 1
        print(f"  FAIL {_safe(name)} {_safe(extra)}")


# ---------------------------------------------------------------- 合成语料
# 覆盖的都是"渲染层真的会分流"的形态：小节卡片（##）、题干与难度徽章（### …｜中级）、
# 四类提示框（> 💡 ⚠️ 🎯 🔍）、围栏代码、表格、双链、旁挂件、同名美化版、书库 txt、空子域。
DOC_RICH = """---
title: 排版约定样本
source: knowledge
collected: 2026-01-05
tags: [渲染, 基线, 中文标签]
status: stable
---

# 排版约定样本

这一段是导语，用来验证正文首段与行高。

## 小节一 · 卡片与色带

这里是大节正文，`##` 会被 app.js::enhanceArticleDOM 包成 .sec-card，标题色按 hash 取。

> 💡 这是一条提示框。
> ⚠️ 这是一条警告框。
> 🎯 关键要点：渐变条按标题 hash 稳定取色。
> 🔍 追问：为什么 hash 色带必须稳定——否则基线每次都不一样。

| 名称 | 值 | 说明 |
|---|---|---|
| hue | 158 | 色相 |
| scale | 1.0 | 字号倍率 |

```python
def hello():
    return "围栏代码：hljs 克制单色高亮"
```

行内引用另一篇：[[排版约定样本-B]]，以及一条不存在的：[[不存在的目标]]。

## 小节二 · 长中文段落

这是一段刻意写长的中文，用来撑出多行换行、检查右边界不塌：""" + "知库视觉基线" * 12 + """

### 1. 题干示例｜中级

题干下的普通段落。

### 2. 另一题干｜高级

第二段题干正文，用来验证两个徽章不串色。
"""

DOC_B = """---
title: 排版约定样本-B
source: knowledge
collected: 2026-01-06
tags: [双链]
---

# 排版约定样本-B

被 [[排版约定样本]] 反向引用的另一篇，正文很短——短正文能暴露"底部栏浮动到中部"这类布局问题。
"""

DOC_HTML_PRETTY = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>美化版样本</title>
<style>body{font-family:sans-serif;margin:24px}h1{color:#2f6f6a}.box{border:1px solid #ddd;padding:12px}</style>
</head><body><h1>美化版（iframe 直服）</h1>
<p>这是与 <code>beta.md</code> 同名共存的 HTML 美化版，默认视图应是 iframe。</p>
<div class="box">固定高度的盒子，验证 iframe 内不出现意外的滚动条。</div>
</body></html>
"""

DOC_NOTES_SIDE = """---
title: 排版约定样本 的备注
---

这是 sidecar `.notes.md`：它**不该**出现在左侧树与任何索引里（不变量 1/2），
但它会渲染在正文下方的备注区，所以画面里必须能看到它。
"""

NOVEL_TXT = """第一章 长夜将尽
城市的尽头有一片灯火，灯火下面是一条走了很多年的路。
路上的人不多，每个人都带着自己的影子。

第二章 来时路
他记得出发那天早上雾很大，大到看不见前面的山。
于是他就近看，看脚下的石子，看石子上的一点青苔。

第三章 天光
后来雾散了，山还在那里。
山也带着自己的影子，影子比人长。
"""

DOC_FAV = """---
title: 收藏样本
source: knowledge
collected: 2026-01-07
tags: [收藏, 渲染]
favorite: true
status: stable
---

# 收藏样本

`favorite: true` 的样本，专门给 `/favorites` 一行可渲染的东西；正文有一节，让复习队列也收得到它。

## 收藏页要渲染的东西

- 域标签、子域标签、标题、路径都要出现；
- 取消收藏后这页会变空，所以这行的视觉回归是有意义的。
"""

DOC_INBOX = """---
title: 待归档条目
source: desktop
collected: 2026-01-08
---

# 待归档条目

躺在 `content/_inbox/` 里等归档的一条，用来渲染收件箱列表行（含大小与"归档/删除"动作位）。
"""

# I-5 编号标题式（`### N. 题干｜难度`）—— cards.py 只对 baike/interview 抽卡，
# 没有这篇的话 `/quiz` 永远停在空态，那个镜头就白拍。
#
# **只能有一道题**：`learn.py::due_slate` 对新卡是 `ORDER BY RANDOM()`（新卡随机抽是有意的产品行为），
# 两张以上新卡时"第一张卡是谁"每次都不一样，镜头必然闪（实测 quiz_card AE=1174，
# 差异 bbox 正好压在题干那两行）。baike 那份也只出一张卡，才让 review_* 两个镜头稳了 5 轮。
DOC_INTERVIEW = """---
title: 前端面试题样本
source: knowledge
collected: 2026-01-10
tags: [面试, 前端]
status: stable
---

# 前端面试题样本

### 1. 事件循环里微任务和宏任务谁先跑｜中级

微任务先跑完，再取一个宏任务。`Promise.then` 属于微任务，`setTimeout` 属于宏任务。
"""

DOC_BAIKE = """---
title: 向量数据库
source: knowledge
collected: 2026-01-09
tags: [检索]
status: stable
---

# 向量数据库

## 定义

**一句话定义：** 把文本变成坐标、按距离找相似内容的存储。

## 常见误区

**误区：** 向量检索会取代关键词检索。

**正解：** 精确匹配（ID、错误码、函数名）仍是倒排索引更准，两者是互补不是替代。
"""

CORPUS = {
    "content/ui-r/notes/alpha.md": DOC_RICH,
    "content/ui-r/notes/beta.md": DOC_B,
    "content/ui-r/notes/beta.html": DOC_HTML_PRETTY,
    "content/ui-r/notes/gamma.md": DOC_FAV,
    "content/ui-r/notes/alpha.md.notes.md": DOC_NOTES_SIDE,
    "content/ui-r/empty-sub/": None,             # None = 只建目录（空子域工作台）
    "content/nv-r/books/长夜.txt": NOVEL_TXT,
    # `cards.py` 只对 baike / interview 两个域抽卡（CARD_DOMAINS），所以复习页要出卡
    # 就必须有一个 baike 词条 —— 没有它，/review 永远停在"暂时没有可学的卡"空态，
    # 那两张截图测的就不是卡片与记分，而是空态。
    "content/baike/term/向量数据库.md": DOC_BAIKE,
    "content/interview/fe/事件循环.md": DOC_INTERVIEW,
    "content/_inbox/待归档条目.md": DOC_INBOX,
}

TAXONOMY = {
    "domains": {"ui-r": {"label": "视觉基线", "hue": 158},
                # 书库域全是 .txt（不进 FTS），"search": false → 浮层不给它筛选钮。
                # 顺带让"派生 + 过滤"这条链路在基线里是**真的被走过**的：
                # 如果哪天过滤失效，多出来的那颗钮会直接改变 search_overlay 那张截图的像素。
                "nv-r": {"label": "基线书库", "hue": 200, "search": False},
                "baike": {"label": "术语", "hue": 30}, "interview": {"label": "面试", "hue": 340}},
    "subs": {"ui-r/notes": "排版样本", "ui-r/empty-sub": "空子域", "nv-r/books": "长篇",
             "baike/term": "词条", "interview/fe": "前端"},
    "sources": {"knowledge": "知库自建", "desktop": "桌面"},
    "status": {"stable": "已核对"},
}

# ---------------------------------------------------------------- 截图矩阵
# theme 通过 addScriptToEvaluateOnNewDocument 在页面脚本前写 localStorage 钉死，
# 不依赖"上次点击留下的状态"。
#
# FREEZE 里只放**运行时计数器**：
#   · TOC 下方"近 7 日阅读"柱状图读的是 reading.db，而每次截图本身就会往 reading.db 追加一条
#     open 事件 —— 第一次截和第二次截的柱子高度必然不同（实测不冻结时两次截图差 0.0637%，
#     热图整块红都在右下角）。
#   · 搜索页的 `.srch-meta`（"共 N 条 · X ms · 全文"）与结果头 `.rc-head .n` 带后端 `took_ms`，
#     同一查询两次也能差几毫秒 —— 数字一变整行文字重排，AE 直接上 300。
#   · `#toast` 是**按墙上时钟自动消失**的浮层（记分后弹"1 天后再见"）：截图快慢一点，
#     它在与不在就不同，实测让 review_graded 两次差 637 像素。
# 代价说清楚：**这几块的视觉回归由本矩阵放弃**，它们的正确性另有 e2e 断言兜
# （/api/learn/recent_read、/api/search 的 took_ms/total 字段在 test_e2e_smoke 里）。
FREEZE_CSS = ("#kb-toc-spark{display:none!important}"
              ".srch-meta{display:none!important}"
              ".rc-head .n{display:none!important}"
              # 状态栏右端现在是 request.host（2026-09-25 去写死），而临时实例端口每次现挑，
              # 逐像素比对里那个数字必然漂 —— 冻结它，正确性由 test_e2e_smoke 的
              # "状态栏右端渲染的是当前请求的 host" 断言兜。
              ".statusbar .right{display:none!important}"
              "#toast{display:none!important}")
INIT_TMPL = ("try{localStorage.setItem('kb-theme','%s');"
             "localStorage.setItem('kb-force-motion','0');}catch(e){}"
             "document.addEventListener('DOMContentLoaded',function(){"
             "var s=document.createElement('style');s.id='kb-p5-freeze';"
             "s.textContent=%s;(document.head||document.documentElement).appendChild(s);});")


def _shot(name, path, theme="light", click="", settle=3500, why="", click_wait=None, freeze=""):
    return {"name": name, "path": path, "theme": theme, "click": click, "settle": settle,
            "why": why, "click_wait": click_wait, "freeze": freeze}


SHOTS = [
    _shot("doc_md_light", "/doc/ui-r/notes/alpha.md", why="卡片/提示框/表格/代码/双链/备注区"),
    _shot("doc_md_dark", "/doc/ui-r/notes/alpha.md", theme="dark", why="同一篇的暗色态：翻色令牌是否成对"),
    _shot("doc_pretty_iframe", "/doc/ui-r/notes/beta.md", why="同名美化版默认走 iframe"),
    _shot("doc_md_via_toggle", "/doc/ui-r/notes/beta.md", click="#kb-md-src-btn",
          why="点「Markdown 源」后的第二视图"),
    _shot("doc_tags_pane", "/doc/ui-r/notes/alpha.md", click='.rtab[data-pane="info"]',
          click_wait=2500, why="右侧面板切到标签页（树 + 标签编辑态）"),
    _shot("browse_empty_sub", "/browse/ui-r/empty-sub", why="空子域空态（D1 那次的回归面）"),
    _shot("novel_txt", "/doc/nv-r/books/%E9%95%BF%E5%A4%9C.txt", why="书库 txt：章节切分与阅读排版"),
    _shot("novel_txt_prefs", "/doc/nv-r/books/%E9%95%BF%E5%A4%9C.txt", click=".nv-pref-btn",
          why="小说「排版」抽屉打开态（滑杆/选项）"),
    # —— 第二批：把 §2 里那批"只断言了控件存在"的页面与交互态逐个变成画面基线 ——
    _shot("inbox_list", "/inbox", why="收件箱列表行（归档/删除动作位）"),
    _shot("favorites_page", "/favorites", why="收藏页（favorite:true 那篇渲染出的行）"),
    _shot("tags_page", "/tags", why="标签页：标签表 + 合并选择条"),
    _shot("governance_idle", "/governance", why="治理驾驶舱首屏「尚未扫描」空态"),
    _shot("governance_scanned", "/governance", click="#gov-scan-btn", settle=6500, click_wait=2500,
          why="点「重新扫描」后的三桶结果页（断链/孤儿/近义标签）"),
    _shot("governance_orphan_tab", "/governance",
          click='#gov-scan-btn,.gov-tab[data-bucket="orphans"]', settle=6500, click_wait=2500,
          why="扫描后切到「孤儿文档」桶（bucket 动作钮）"),
    _shot("search_results", "/search?q=%E6%8F%90%E7%A4%BA%E6%A1%86",
          why="FTS 搜索结果卡片：命中高亮 + 跳转链接"),
    _shot("review_card", "/review", settle=6500, why="复习页：今日队列 + 卡片正面 + 环形进度"),
    _shot("review_graded", "/review", click='#kb-reveal,.kb-grade[data-q="3"]', settle=6500,
          # 记分后副标题会先短暂显示"本轮完成 1 张 · 已全部过完"，随后队列刷新才落到稳定态。
          # 实测（同一实例连截 3s / 8s / 15s）：3s 与 8s 差 2786 像素，8s 与 15s **AE=0** → 8 秒后已收敛。
          click_wait=8000,
          # 曾额外 freeze 过 #kb-learn-sub：`refreshStats` 两个并发请求无序号守卫，
          # 迟到的旧响应会把这一行覆盖成"到期 0 张…"，同一动作两种结果（§6 第 24 行）。
          # 2026-09-24 修掉竞态（learn.js 加 seq 守卫 + test_js_props 的"统计竞态"探针锁住）后
          # freeze 已撤回 —— 这行重新回到基线里，它红就说明竞态回来了。
          why="显示答案→点「困难」记分后的稳定态（q=3 那条 P6 抓过的边界）"),
    _shot("stats_pinned_month", "/stats?ym=2026-01", settle=6500,
          why="月度报表：ym 钉死在没有阅读数据的过去月，避开跨月与当月漂移"),
    # —— 第三批：把 §2 剩下的交互控件补完（治理页动作态 / 标签合并选择条 / 出题卡 / 搜索浮层）——
    _shot("governance_dead_selected", "/governance",
          click='#gov-scan-btn,#dead-all', settle=6500, click_wait=2500,
          why="扫描后勾「全选」：断链动作钮（转为纯文本 / 移除链接标记）由 disabled 变可用"),
    _shot("tags_merge_bar", "/tags", click='.t-check', settle=5000, click_wait=2000,
          why="标签页勾中一个标签 → 底部合并选择条出现（未选择/清除/合并到…）"),
    _shot("quiz_card", "/quiz", settle=6500,
          why="面试题卡（I-5 编号标题式抽出的卡）：题干 + 评分两档 + 侧栏"),
    _shot("search_overlay", "/doc/ui-r/notes/alpha.md",
          click='#searchbox,.kb-eng-chip[data-eng="hybrid"]', settle=5000, click_wait=2200,
          why="就地搜索浮层打开 + 引擎 chip 切到「混合 Hybrid」的选中态"),
]


def build_corpus(root: Path):
    for rel, content in CORPUS.items():
        p = root / rel.replace("/", os.sep)
        if content is None:
            p.mkdir(parents=True, exist_ok=True)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
    meta = root / "content" / "_meta"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "taxonomy.json").write_text(json.dumps(TAXONOMY, ensure_ascii=False), encoding="utf-8")


def make_manifest(base_url, out_dir, shots):
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = []
    for s in shots:
        job = {"url": base_url + s["path"], "out": str(out_dir / f"{s['name']}.png"),
               "w": 1440, "h": 900, "click": s["click"], "settle": s["settle"],
               "init": INIT_TMPL % (s["theme"], json.dumps(FREEZE_CSS + s.get("freeze", "")))}
        if s.get("click_wait") is not None:
            job["clickWait"] = s["click_wait"]
        jobs.append(job)
    f = out_dir.parent / f"manifest-{out_dir.name}.json"
    f.write_text(json.dumps({"shots": jobs}, ensure_ascii=False), encoding="utf-8")
    return f


def capture(tag, shots):
    """**自带一套临时根 + 临时实例**地截完矩阵，返回实际图目录。

    为什么不共享实例（第一版就是共享的）：矩阵里有会**改状态**的点击 ——
    复习页点「困难」写 learn.db 的排程、打开文档写 reading.db。两次截图共用一个实例时，
    第二次的环形进度/今日队列必然和第一次不同，`--stability` 就会红，而红的是 harness 不是代码。
    每次截完换一座干净的临时根，才是"同一份代码截两遍"的本义。
    """
    global PORT
    tmp = Path(tempfile.mkdtemp(prefix=f"p5-{tag}-"))
    proc = None
    try:
        build_corpus(tmp)
        # create_app 的 static_folder 是 <KB_ROOT>/static：临时根没它就全 404（P3-B 同款坑）
        shutil.copytree(ROOT / "static", tmp / "static")
        PORT = free_port()
        QA.mkdir(parents=True, exist_ok=True)
        check(f"[{tag}] 端口现挑且不落在用户常驻端口", PORT not in (5000, 5001, 5031), f"port={PORT}")
        proc = start_instance(tmp, PORT, log_path=QA / f"instance-{tag}.log")
        base = f"http://127.0.0.1:{PORT}"
        check(f"[{tag}] 临时实例起来了", port_open(PORT))
        # 页面可达性各断一条：404/500 会让"截图一致但全是错误页"这种假绿成为可能
        for path in ("/doc/ui-r/notes/alpha.md", "/browse/ui-r/empty-sub", "/review", "/stats?ym=2026-01"):
            code = subprocess.run(["node", "-e",
                                   f"fetch({json.dumps(base + path)}).then(r=>console.log(r.status))"],
                                  capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", timeout=90)
            check(f"[{tag}] 页面可访问 {path}", (code.stdout or "").strip() == "200",
                  f"got={(code.stdout or code.stderr).strip()[-80:]}")
        out_dir = QA / tag
        if out_dir.exists():
            shutil.rmtree(out_dir)
        mf = make_manifest(base, out_dir, shots)
        t0 = time.time()
        r = subprocess.run(["node", str(ROOT / "scripts" / "agent" / "shot.mjs"), "--batch", str(mf)],
                           cwd=str(ROOT), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=900)
        for line in (r.stdout or "").splitlines():
            if line.startswith("FAIL"):
                print(f"    {_safe(line)}")
        got = sorted(p.name for p in out_dir.glob("*.png"))
        check(f"[{tag}] 截图矩阵 {len(shots)} 张全部产出",
              got == sorted(f"{s['name']}.png" for s in shots),
              f"got={got} rc={r.returncode} {(r.stderr or '')[-200:]}")
        # 空白页也是"确定"的 —— 光比差异会把它读成绿。这里加一条最便宜的绊线：
        # 实测 1440×900 纯白页 PNG 只有 1033 字节，而矩阵里最小的合法截图（收藏页）是 37KB，
        # 所以 20KB 这条线既拦得住白屏/错误页，又不会误伤内容稀疏的页面。
        thin = {p.name: p.stat().st_size for p in out_dir.glob("*.png") if p.stat().st_size < 20000}
        check(f"[{tag}] 无空白截图（每张 >20KB；纯白页实测 1KB，最小合法页 37KB）", not thin, f"{thin}")
        print(f"  [{tag}] 截图耗时 {round(time.time() - t0)}s")
        geometry(tag, base)      # 非像素判据：顶栏矩形相交只能靠几何抓（见 GEOM_EXPR 上方注释）
        return out_dir
    finally:
        kill_instance(proc)
        shutil.rmtree(tmp, ignore_errors=True)
        check(f"[{tag}] 清理只删掉了系统临时目录下的临时根", not tmp.exists()
              and str(tmp).startswith(tempfile.gettempdir())
              and (ROOT / "content").is_dir(), f"tmp={tmp}")


AE_RE = re.compile(r"AE=(-?\d+)")

# ---------------------------------------------------------------- 顶栏几何（非像素）
# 为什么单独测：搜索框"绝对居中"在窄窗会盖住导航（台账 §14.3 第 1 条，2026-09-25 修），
# 而这类"两个矩形相交"在像素基线里是**稳定地错** —— 每次截图都一样，比对永远绿。
# 判据必须是几何：逐宽度量矩形，断"不相交 + 不溢出视口"，并断三档确实都在（否则
# "整个顶栏永远流行内"同样全绿）。
GEOM_WIDTHS = [1280, 1440, 1600, 1680, 1836, 1840, 2000]
GEOM_EXPR = r"""(() => {
  var rect = function (el) {
    if (!el) return null;
    var b = el.getBoundingClientRect();
    return {x: Math.round(b.x), right: Math.round(b.right), w: Math.round(b.width)};
  };
  var hit = function (a, b) { return !!a && !!b && a.x < b.right && b.x < a.right; };
  var box = rect(document.querySelector('.searchbox'));
  var nav = rect(document.querySelector('.topnav'));
  var parts = {nav: nav,
               right: rect(document.querySelector('.top-right')),
               brand: rect(document.querySelector('.brand')),
               fav: rect(document.querySelector('a.tn[href="/favorites"]'))};
  var bad = [];
  for (var k in parts) if (hit(box, parts[k])) bad.push(k);
  return JSON.stringify({
    vw: window.innerWidth,
    pos: getComputedStyle(document.querySelector('.searchbox')).position,
    w: box ? box.w : 0,
    bad: bad,
    // 绝对居中那两档：与导航右边缘（实测恒 618）的缝。缝只有 2px 也算"没相交"，
    // 但视觉上就是贴脸 —— 所以断"缝 ≥ 18"，而不只断"不相交"。
    gap_nav: (box && nav) ? box.x - nav.right : null,
    spill: box ? Math.max(0, box.right - (window.innerWidth - 14), 14 - box.x) : 0
  });
})()"""


def geometry(tag, base):
    """临时实例还活着时跑：顶栏在 7 档宽度下不许和任何东西相交。"""
    expr_file = QA / f"geom-{tag}.js"
    expr_file.write_text(GEOM_EXPR, encoding="utf-8")
    r = subprocess.run(
        ["node", str(ROOT / "scripts" / "agent" / "geom.mjs"),
         base + "/doc/ui-r/notes/alpha.md",
         ",".join(str(w) for w in GEOM_WIDTHS), "@" + str(expr_file)],
        cwd=str(ROOT), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=240)
    rows = []
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    check(f"[{tag}] 顶栏几何探针 {len(GEOM_WIDTHS)} 档全部回值",
          len(rows) == len(GEOM_WIDTHS),
          f"got={len(rows)} rc={r.returncode} {_safe((r.stderr or '')[-160:])}")
    by_w = {row.get("vw"): row for row in rows}
    for w in GEOM_WIDTHS:
        row = by_w.get(w) or {}
        check(f"[{tag}] 顶栏 {w}px：搜索框不与导航/图标组相交且不溢出视口",
              row.get("bad") == [] and row.get("spill") == 0, _safe(str(row)))
    # 三档各自的"身份"（缺了这三条，"顶栏永远流行内"也能全绿 —— 那是假绿）：
    #   ≥1837 绝对居中 560；1600~1836 绝对居中但按中隙收宽；≤1599 回流行内。
    # 边界实测（.qa/topbar_probe.mjs 单快照 · 每档连读 3 次一致）：
    #   1836 → w=560 缝=20，1840 → w=560 缝=22；临界若取 1796，1797~1840 会出现只有
    #   2~22px 的贴脸缝，所以这里同时断"缝 ≥ 18"。
    wide = [by_w.get(w) or {} for w in (1840, 2000)]
    mid = [by_w.get(w) or {} for w in (1600, 1680, 1836)]
    flow = [by_w.get(w) or {} for w in (1280, 1440)]
    check(f"[{tag}] ≥1837 绝对居中、框宽 560、与导航缝 ≥18",
          all(row.get("pos") == "absolute" and row.get("w") == 560
              and (row.get("gap_nav") or 0) >= 18 for row in wide), _safe(str(wide)))
    check(f"[{tag}] 1600~1836 绝对居中、按中隙收宽（324~560）、与导航缝 ≥18",
          all(row.get("pos") == "absolute" and 324 <= row.get("w", 0) <= 560
              and (row.get("gap_nav") or 0) >= 18 for row in mid), _safe(str(mid)))
    check(f"[{tag}] ≤1599 退出绝对居中（position=static）",
          all(row.get("pos") == "static" for row in flow), _safe(str(flow)))



def compare(a: Path, b: Path):
    """调 imgdiff（复用仓库现成工具），返回 (差异像素数, 说明)。SIZE-MISMATCH 记 -1。"""
    r = subprocess.run(["node", str(ROOT / "scripts" / "agent" / "imgdiff.mjs"),
                        str(a), str(b), FUZZ],
                       cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=180)
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    if "SIZE-MISMATCH" in out:
        return -1, out.splitlines()[0]
    m = AE_RE.search(out)
    if not m:
        return None, out[-300:]
    return int(m.group(1)), out.splitlines()[0] if out.splitlines() else ""


def main():
    if not node_available():
        return _ci.skip("ui_regress", "no-node", "SKIP: 找不到 node")
    if not chrome_path():
        return _ci.skip("ui_regress", "no-chrome", "SKIP: 找不到 Chrome")
    if not magick_available():
        return _ci.skip("ui_regress", "no-imagemagick", "SKIP: 找不到 ImageMagick（imgdiff.mjs 依赖它）")
    _ci.started("ui_regress")

    update = "--update" in sys.argv
    stability = "--stability" in sys.argv
    missing = [s["name"] for s in SHOTS
               if not (BASELINES / f"{s['name']}.png").exists()]
    if missing and not (update or stability):
        print(f"基线缺失 {len(missing)}/{len(SHOTS)}：{missing}\n"
              f"先跑 --stability 证明 harness 确定，再跑 --update 落基线。")
        return 1

    actual = capture("actual", SHOTS)
    floor = {}
    if stability:
        again = capture("actual2", SHOTS)
        print("\n[stability] 同一份代码两次截图互比（这一步红 = harness 不确定，基线无意义）")
        for s in SHOTS:
            ae, info = compare(actual / f"{s['name']}.png", again / f"{s['name']}.png")
            floor[s["name"]] = ae if ae is not None else -1
            check(f"[确定] {s['name']}：两次截图差异像素数 {ae} <= {MAX_DIFF_AE}",
                  ae is not None and 0 <= ae <= MAX_DIFF_AE, info)
    else:
        BASELINES.mkdir(parents=True, exist_ok=True)
        if update:
            for s in SHOTS:
                shutil.copyfile(actual / f"{s['name']}.png", BASELINES / f"{s['name']}.png")
            print(f"\n[update] 已把 {len(SHOTS)} 张截图写入基线目录 {BASELINES}")
            return 0
        print(f"\n[check] 与基线比对（fuzz={FUZZ}，阈值 AE <= {MAX_DIFF_AE} 像素）")
        for s in SHOTS:
            ae, info = compare(BASELINES / f"{s['name']}.png", actual / f"{s['name']}.png")
            check(f"{s['name']}（{s['why']}）差异像素数 {ae}",
                  ae is not None and 0 <= ae <= MAX_DIFF_AE, info)

    if stability and floor:
        QA.mkdir(parents=True, exist_ok=True)
        f = QA / "floor.json"
        prev = {}
        if f.exists():
            try:
                prev = json.loads(f.read_text(encoding="utf-8"))
            except Exception:                         # noqa: BLE001
                prev = {}
        merged = {k: max(int(prev.get(k, 0)), v) for k, v in floor.items()}
        f.write_text(json.dumps(merged, ensure_ascii=False, indent=1), encoding="utf-8")
        worst = sorted(merged.items(), key=lambda kv: -kv[1])[:5]
        print("\n[噪声地板] 历轮累计每镜头最大 AE（像素）：" +
              "、".join(f"{k}={v}" for k, v in worst) + f"（阈值 {MAX_DIFF_AE}）")

    print(f"\n{passed} passed, {failed} failed")
    print(f"实际截图与差异热图：{QA}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
