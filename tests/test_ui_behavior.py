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
  · **不联网**：轮次 54 起本套没有任何探针会打 AI 端点（那条链路整体下线），
    原先"跑之前把 KB_AI_API_KEY 从环境里摘掉"那一步连同两条 AI 探针一起删除；
  · 语料一律合成，不读 content/小说（禁区）。
"""
import atexit
import json
import os
import queue
import re
import threading
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

import _ci  # noqa: E402  缺依赖 SKIP 时给 CI 留 annotation（见 tests/_ci.py）
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
        _ci.failed(name)
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
    # 第二个 baike 词条：一篇带 `## 相关术语`（[[双链]]）与一个**故意断链**目标
    # （[[尚不存在的术语]]）的样本，供双链建议与断链检查探针使用。
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
    # 搜索页分面探针的形状前提：查询词「标签」必须在**多个域**里都有命中，否则
    # 「点一个域分面 → 收窄 → 跨组多选是交集」那几条全是同义反复。
    # 这一篇落在 articles 域（ui-r 之外），正文里带「标签」。
    # 原先是 vue2/vue3 三篇夹具在兼这个职（同时充当已下线的标签合并靶子），
    # 瘦身时随标签页一起删掉 → 分面只剩 ui-r 单域，两条断言当场红。
    "content/articles/标签体系.md": """---
title: 标签与分类学
source: knowledge
collected: 2026-02-05
tags: [前端]
status: stable
---

# 标签与分类学

标签是横向切面，分类学是纵向骨架：同一篇文档可以贴多个标签，
但在分类树里只能落在一个子域。
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


class CdpSession:
    """一台 Chrome 跑完整套探针（轮次 33）。

    为什么要它：一次一档的 `geom.mjs` 每次求值都要付 **Chrome 冷启动 3~4s + 建/删 profile +
    2.5s settle**，实测平均 6.5~11s/次 × 45 次 ≈ 全套 484s 的全部。求值本身是毫秒级的。

    复用浏览器会改掉一件事：**隔离**。原来每趟新 profile = localStorage 是干净的；
    共用一台浏览器如果不清存储，上一趟写进 localStorage 的偏好会串到下一趟，
    于是"默认态"其实是脏的 —— 那不是提速，是假绿。所以每个作业开始前按 `fresh`
    清一次 origin 存储 + cookies（geom.mjs 的 runJob 里做），并且这个隔离本身有断言锁着
    （见 probe_isolation）。`init` 也逐作业注册/注销，不共享。
    """

    def __init__(self):
        self.proc = None
        self.q = queue.Queue()
        self.job_id = 0
        self.reader = None
        self.stderr_path = QA / "geom-session.log"
        self.restarts = 0

    def start(self):
        QA.mkdir(parents=True, exist_ok=True)
        err = open(self.stderr_path, "ab")
        self.proc = subprocess.Popen(
            ["node", str(ROOT / "scripts" / "geom.mjs"), "--session"],
            cwd=str(ROOT), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=err, text=True, encoding="utf-8", errors="replace",
            env=dict(os.environ))
        # **必须等 ready 握手**：实测在 Node 接管 stdin 之前写进管道的作业会被丢掉
        # （延后 4s 再写就正常、立刻写就永远没有回复）。丢掉一条作业 = 白等 300s 超时，
        # 而且是"套件卡在第一个探针"这种最难查的形状。
        deadline = time.time() + 60
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError("CDP 会话启动即退出（rc=%s），看 %s"
                                   % (self.proc.returncode, self.stderr_path))
            line = self.proc.stdout.readline()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("session") == "ready":
                break
        else:
            raise RuntimeError("CDP 会话 60s 内没有 ready 握手")
        self.reader = threading.Thread(target=self._pump, daemon=True)
        self.reader.start()

    def _pump(self):
        for line in self.proc.stdout:
            if line and line.strip():
                self.q.put(line)

    def alive(self):
        return bool(self.proc) and self.proc.poll() is None

    def close(self):
        if not self.proc:
            return
        try:
            self.proc.stdin.close()
        except Exception:                                # noqa: BLE001
            pass
        try:
            self.proc.wait(timeout=20)
        except Exception:                                # noqa: BLE001
            # 会话档不会走到这里；真卡住就杀掉 node（Chrome 由 geom 的 finally 收）
            try:
                self.proc.kill()
            except Exception:                            # noqa: BLE001
                pass

    def job(self, url, js, width, click, click_wait, init, fresh, timeout=300):
        """提交一个作业，回一行结果 dict。进程死了就重启一次（不让门禁整挂）。"""
        for attempt in (0, 1):
            if not self.alive():
                if attempt:
                    raise RuntimeError("CDP 会话两次都起不来")
                self.restarts += 1
                self.start()
            self.job_id += 1
            jid = self.job_id
            payload = {"id": jid, "url": url, "expr": js, "width": width,
                       "click": click, "click_wait": click_wait, "init": init,
                       "fresh": fresh}
            self.proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
            self.proc.stdin.flush()
            deadline = time.time() + timeout
            while time.time() < deadline:
                try:
                    line = self.q.get(timeout=1.0)
                except queue.Empty:
                    if not self.alive():
                        break                            # 进程没了 → 重启重试
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if row.get("id") == jid:
                    return row
            else:
                # 超时：杀掉重来，别让整套卡死
                self.close()
                continue
            self.close()
        raise RuntimeError("CDP 会话不可用")


_SESSION = CdpSession()
USE_SESSION = os.environ.get("KB_BEHAVIOR_SESSION", "1") != "0"
atexit.register(_SESSION.close)


def run_expr(url, js, width=PROBE_WIDTH, click="", click_wait=1800, init="", fresh=True):
    """在指定视口宽度下求值一个 async 表达式（表达式须 return 一个 JSON 字符串）。

    `click` 非空时先点这些选择器（逗号分隔）再求值 —— 点击引发整页导航也没关系，
    geom.mjs 等的是 readyState，求值发生在导航之后的新文档里，所以"点了到底换没换页"
    能直接断出来（这是本套能覆盖"一级导航"那 8 行的关键）。
    `init` 非空时在页面任何脚本执行**之前**注入（验"刷新后偏好仍然生效"用）。
    """
    QA.mkdir(parents=True, exist_ok=True)
    # 表达式落盘按 PID 命名：写死同一个文件名时，**两个并发跑会互相覆盖对方的表达式**
    # （轮次 49 实测：我不小心同时起两趟，两趟都在求值别人最后写进去的那份 JS —— 症状是
    # "莫名红/莫名崩"，跟被测代码毫无关系）。一次跑内是无害的，并发跑才是致命的。
    f = QA / ("behavior-expr-%d.js" % os.getpid())
    f.write_text(js, encoding="utf-8")
    if init:
        # 两条路共用同一道闸：会话档也必须先验桩的语法（坏桩会被 CDP 静默丢弃 = 假绿）
        check_init_syntax(init)
    if USE_SESSION:
        try:
            row = _SESSION.job(url, js, width, click, click_wait, init, fresh)
        except Exception as e:                            # noqa: BLE001
            check("CDP 会话可用（否则退回一次一档）", False, _safe(repr(e))[:160])
            row = None
        if row is not None and "value" in row:
            try:
                return json.loads(row["value"])
            except (TypeError, ValueError) as e:
                # TypeError = value 根本不是字符串（页面里抛了异常，CDP 把 error 对象塞进 value）。
                # 只捕 ValueError 会让整条套件以 Traceback 收场 —— 变异跑法下那就是
                # "判据没红 / 套件崩了"两种信号长得一模一样（轮次 49 实测）。
                check("CDP 探针返回值能解析", False,
                      _safe(f"{type(e).__name__}: {e} / value={row.get('value')!r}")[:400])
                return {}
        if row is not None:
            check("CDP 探针表达式执行无异常", False, _safe(row))
            return {}
    env = dict(os.environ)
    if click:
        env["KB_GEOM_CLICK"] = click
        env["KB_GEOM_CLICK_WAIT"] = str(click_wait)
    if init:
        env["KB_GEOM_INIT"] = init
    r = subprocess.run(
        ["node", str(ROOT / "scripts" / "geom.mjs"), url, str(width), "@" + str(f)],
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


def check_init_syntax(init):
    """注入桩必须先过语法自检。

    CDP 的 addScriptToEvaluateOnNewDocument 碰到 SyntaxError 是**静默不执行**的
    （Chrome 不报错、页面照常跑），于是"打了桩之后仍然绿"的断言全是假的。
    2026-09-25 轮次 32 就栽在这上面 —— 多出来的一个右括号让掌握度空态桩整段没执行，
    页面读的是真接口，那条"空列表 → 一句人话"永远不可能成立，却差点蒙过去。
    """
    QA.mkdir(parents=True, exist_ok=True)
    f2 = QA / "behavior-init.js"
    f2.write_text(init, encoding="utf-8")
    chk = subprocess.run(["node", "--check", str(f2)], cwd=str(ROOT),
                         capture_output=True, text=True,
                         encoding="utf-8", errors="replace", timeout=60)
    check("探针注入桩（init）语法正确", chk.returncode == 0,
          _safe((chk.stderr or "")[-240:]))
    return chk.returncode == 0


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
    # 统计页在**没有阅读数据的实例里**只渲染骨架：KPI 卡与图表全部有条件（has_chart 为假时
    # 连 canvas 都不存在）。所以特征元素取那张永远在的数据载荷 `#st-daily-data` —— 它证明
    # "这页真的按 stats.html 渲染了"，而不是被别的模板顶替。
    ("/stats", "阅读统计", "统计", 'id="st-daily-data"', ["/stats"]),
    ("/favorites", "收藏", "收藏", 'class="result fav-card"', ["/favorites"]),
    # 收件箱与总览是**图标入口**（顶栏没有对应的文字导航项），所以 .on 恒空。
    # 这不是断言写松了 —— 现状就是"从图标进这两页时，一级导航没有任何一项高亮"，
    # 要不要给它算归属属产品决定，本条只把事实钉住（改了这个行为，这条会红）。
    ("/inbox", "收件箱", "收件箱", 'id="inbox-kanban"', []),
    ("/home", "总览", "brand→总览", 'id="view-home"', []),
]

NAV_JS = PRELUDE + """
  out.path = location.pathname;
  out.title = document.title;
  out.on_now = [...document.querySelectorAll('.topnav .tn.on')].map(x => x.getAttribute('href'));
  return JSON.stringify(out);
})()"""


def probe_nav(base, tmp):
    print("== 0 一级导航（点了换页 + 高亮跟着变）与收件箱徽标 ==")
    before = run_expr(base + "/", NAV_JS)
    check("导航：出发页是阅读页、高亮在「阅读」",
          before.get("path") == "/" and before.get("on_now") == ["/"], before)

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


# ---------------------------------------------------------------- 探针 1：[[ 双链补全
# （原「探针 1：问吧」随 /api/ask 在轮次 53 一起删除；探针号不重排，历史可查）
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


def probe_exact(base):
    print("== 14 搜索页精确命中区 #kb-exact ==")
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


# 用户报的那条：从搜索 / 深链 / 最近阅读打开一篇文档时，左树只有 .active 高亮、
# 父级还收着 —— 等于"亮了一个你看不见的节点"。这里从**空存储**（树默认全收起）直接
# 深链进去，断三级展开 + 那一条真的滚进了树的视野 + 展开态落了盘（刷新后保持）。
TREE_REVEAL_JS = PRELUDE + r"""
  const T = e => ((e && e.textContent) || '').replace(/\s+/g, ' ').trim();
  for (let i = 0; i < 80 && !q('#tree .doc'); i++) await sleep(150);
  await sleep(700);
  const nav = q('#tree');
  const nr = nav.getBoundingClientRect();
  const dom = q('#tree .dom[data-dom="ui-r"]');
  const subA = q('#tree .sub[data-dom="ui-r"][data-sub="notes"]');
  const docsBox = subA ? subA.nextElementSibling : null;
  const docA = q('#tree .doc[data-name="beta"]');
  const dr = docA ? docA.getBoundingClientRect() : null;
  out.ls_open = localStorage.getItem('kb-tree-open');
  out.ls_sub = localStorage.getItem('kb-sub-open');
  out.dom_open = !!(dom && dom.classList.contains('open'));
  out.sub_collapsed = !!(subA && subA.classList.contains('collapsed'));
  out.docsbox_collapsed = !!(docsBox && docsBox.classList.contains('collapsed'));
  out.sub_aria = subA ? subA.getAttribute('aria-expanded') : null;
  out.doc_found = !!docA;
  out.doc_active = !!(docA && docA.classList.contains('active'));
  out.doc_in_viewport = !!(dr && nr.height && dr.top >= nr.top - 2 && dr.bottom <= nr.bottom + 2);
  out.doc_visible = !!(dr && dr.width > 0 && dr.height > 0);
  out.head = T('#article h1') || T('#article .a-title');
  return JSON.stringify(out);
})()"""


def probe_tree_reveal(base):
    print("== 16c 深链打开文档 → 左树自动展开并聚焦到那一条 ==")
    got = run_expr(base + "/doc/ui-r/notes/beta.md", TREE_REVEAL_JS)
    check("一级域跟着展开（localStorage 里原本没有它，是打开文档这件事让它展开的）",
          got.get("dom_open") is True and "ui-r" in (got.get("ls_open") or ""), got)
    check("二级子域展开：class 与 aria 一起对上（aria 不给就等于读屏软件看不见）",
          got.get("sub_collapsed") is False and got.get("docsbox_collapsed") is False
          and got.get("sub_aria") == "true" and "ui-r/notes" in (got.get("ls_sub") or ""), got)
    check("那一篇在树里既存在又可见，而且就在树的视野内（不是亮在滚出去的地方）",
          got.get("doc_found") is True and got.get("doc_visible") is True
          and got.get("doc_in_viewport") is True and got.get("doc_active") is True, got)


# ================================================================ 探针 16d：窄屏右栏 = 底部工具栏
# 用户实拍：手机上"目录/标签/备注/双链"那一坨卡在正文中段（旧写法把它做成流里的
# sticky 块，面板内联展开）。现在它是**贴底工具栏**，点页签才从下往上展开。
# 断言口径全部是"他抱怨的那几个像素"：工具栏在不在底部、压不压状态栏、
# 页签够不够 44px 触控区、收起时有没有残留空壳、四种关闭手势（再点/Esc/点外面/换文档）。
RAIL_SHEET_JS = PRELUDE + r"""
  const rect = e => { const b = e && e.getBoundingClientRect(); return b ? {x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height)} : null; };
  for (let i = 0; i < 80 && !q('#article h1'); i++) await sleep(150);
  await sleep(700);
  // tab0 = 第一枚**右栏面板**页签；工具栏最前面那颗「分类」是另一个抽屉，不能拿它当样本
  const rail = q('#p-rail'), tab0 = q('.rtab[data-pane]');
  if (!rail || !tab0) { out.fail = 'no rail'; return JSON.stringify(out); }
  const cs = getComputedStyle(rail);
  out.pos = cs.position;
  out.disp = cs.display;
  out.rail = rect(rail);
  out.tab0 = rect(tab0);
  out.tabN = document.querySelectorAll('.rtab[data-pane]').length;
  out.pane0 = rect(q('.rpane.active'));
  out.open0 = cls('#p-rail', 'rail-open');
  out.aria0 = tab0.getAttribute('aria-expanded');
  out.statusbar = rect(q('.statusbar'));
  out.sbDisp = getComputedStyle(q('.statusbar')).display;
  out.hScroll = document.documentElement.scrollWidth > innerWidth + 1;
  tab0.click(); await sleep(700);
  out.openPane = rect(q('.rpane.active'));
  out.openRail = rect(rail);
  out.open1 = cls('#p-rail', 'rail-open');
  out.aria1 = tab0.getAttribute('aria-expanded');
  out.paneScrollH = q('.rpane.active').scrollHeight;
  out.paneOverflow = getComputedStyle(q('.rpane.active')).overflowY;
  out.paneMaxH = Math.round(parseFloat(getComputedStyle(q('.rpane.active')).maxHeight) || 0);
  out.panePos = getComputedStyle(q('.rpane.active')).position;
  out.paneRight = Math.round(q('.rpane.active').getBoundingClientRect().right);
  out.vw = innerWidth;
  out.vh = innerHeight;
  /* 锚点换了：≤980 那一行状态栏已按用户要求（图3）整条撤掉，工具栏因此贴住视口底边，
     抽屉则撑满整屏（图6）。再拿 `.statusbar` 的矩形当"底"会永远量到 0×0。
     工具栏的真实矩形在 `.rtabs` 上（`#p-rail` 这一层已收成 0 高的容器）。 */
  const tb = q('.rtabs').getBoundingClientRect();
  out.tbBottomGap = Math.round(innerHeight - tb.bottom);
  out.tbH = Math.round(tb.height);
  out.fullWidth = Math.round(tb.left) === 0 && Math.round(tb.right) === innerWidth;
  const pb = q('.rpane.active').getBoundingClientRect();
  out.paneTop = Math.round(pb.top);
  out.paneBottom = Math.round(pb.bottom);
  out.panePadBottom = Math.round(parseFloat(getComputedStyle(q('.rpane.active')).paddingBottom) || 0);
  out.toolbarAbovePane = (() => {
    const e = document.elementFromPoint(Math.round(innerWidth * 0.5), Math.round(innerHeight - 8));
    return !!(e && e.closest && e.closest('.rtabs'));
  })();
  out.paneWithinViewport = rect(q('.rpane.active')).y >= 0;
  tab0.click(); await sleep(700);
  out.open2 = cls('#p-rail', 'rail-open');
  out.pane2 = rect(q('.rpane.active'));
  tab0.click(); await sleep(700);
  out.open3 = cls('#p-rail', 'rail-open');
  (q('#article') || document.body).dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true, cancelable: true}));
  await sleep(500);
  out.open4 = cls('#p-rail', 'rail-open');
  tab0.click(); await sleep(700);
  out.open5 = cls('#p-rail', 'rail-open');
  (q('.article') || q('main')).dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
  await sleep(400);
  out.open6 = cls('#p-rail', 'rail-open');
  tab0.click(); await sleep(700);
  document.dispatchEvent(new CustomEvent('kb:article-rendered'));
  await sleep(400);
  out.open7 = cls('#p-rail', 'rail-open');
  return JSON.stringify(out);
})()"""

RAIL_DESK_JS = PRELUDE + r"""
  for (let i = 0; i < 80 && !q('#article h1'); i++) await sleep(150);
  await sleep(700);
  const rail = q('#p-rail'), tab0 = q('.rtab[data-pane]');
  if (!rail || !tab0) { out.fail = 'no rail'; return JSON.stringify(out); }
  out.pos = getComputedStyle(rail).position;
  out.open0 = cls('#p-rail', 'rail-open');
  out.aria0 = tab0.getAttribute('aria-expanded');
  out.paneH = Math.round(q('.rpane.active').getBoundingClientRect().height);
  out.railW = Math.round(rail.getBoundingClientRect().width);
  tab0.click(); await sleep(600);
  out.open1 = cls('#p-rail', 'rail-open');
  out.aria1 = tab0.getAttribute('aria-expanded');
  out.paneH2 = Math.round(q('.rpane.active').getBoundingClientRect().height);
  rail.classList.add('rail-open');
  document.dispatchEvent(new CustomEvent('kb:article-rendered'));
  await sleep(300);
  out.open2 = cls('#p-rail', 'rail-open');
  out.navTabDisp = getComputedStyle(q('#kb-nav-tab')).display;
  out.leftDisp = getComputedStyle(q('#p-left')).display;
  out.navOn = cls('main', 'kb-nav-on');
  q('#kb-nav-tab').click(); await sleep(500);
  out.navOnAfterClick = cls('main', 'kb-nav-on');
  return JSON.stringify(out);
})()"""

# 「分类」抽屉：style.css 在 ≤860 把左树整块 display:none，窄屏原本**没有任何**翻目录的路径
# （用户报的"移动端 pwa 没有目录结构的按钮"）。工具栏第一颗页签就是那条路径。
NAV_SHEET_JS = PRELUDE + r"""
  const rect = e => { const b = e && e.getBoundingClientRect(); return b ? {x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height)} : null; };
  for (let i = 0; i < 80 && !q('#article h1'); i++) await sleep(150);
  await sleep(700);
  const navTab = q('#kb-nav-tab'), left = q('#p-left'), m = q('main'), rail = q('#p-rail');
  if (!navTab || !left || !m) { out.fail = 'no nav tab'; return JSON.stringify(out); }
  out.vw = innerWidth;
  out.tabIsFirst = document.querySelector('.rtab') === navTab;
  out.tabDisp = getComputedStyle(navTab).display;
  out.tabRect = rect(navTab);
  out.leftDisp0 = getComputedStyle(left).display;
  out.navOn0 = m.classList.contains('kb-nav-on');
  navTab.click(); await sleep(700);
  out.navOn1 = m.classList.contains('kb-nav-on');
  out.leftDisp1 = getComputedStyle(left).display;
  out.leftRect = rect(left);
  out.treeItems = document.querySelectorAll('#tree .dom').length;
  out.treeFirstH = rect(q('#tree .dom')).h;
  out.ariaNav1 = navTab.getAttribute('aria-expanded');
  out.railOpenWhenNav = rail.classList.contains('rail-open');
  /* 判据换了：图6 要求分类抽屉**撑满整屏**，所以"底边必须 ≤ 工具栏上沿"这条不成立了；
     现在要量的是两件真事 —— 抽屉自己 top=0/底到视口底，工具栏仍浮在它上面点得到。 */
  out.navFullHeight = (() => {
    const lb = left.getBoundingClientRect();
    return lb.top <= 1 && Math.abs(lb.bottom - innerHeight) <= 1;
  })();
  out.toolbarPaintedAbove = (() => {
    const e = document.elementFromPoint(Math.round(innerWidth * 0.4), Math.round(innerHeight - 8));
    return !!(e && e.closest && e.closest('.rtabs'));
  })();
  out.navPadBottom = Math.round(parseFloat(getComputedStyle(left).paddingBottom) || 0);
  out.navInViewport = rect(left).y >= 0;
  out.navScrolls = getComputedStyle(left).overflowY;
  out.navMaxH = Math.round(parseFloat(getComputedStyle(left).maxHeight) || 0);
  // 原始浮点 + 两侧 CSS 值：这类断言差 1px 就会红，不留下证据下一轮只能瞎猜
  out.raw = { lTop: left.getBoundingClientRect().top, lBottom: left.getBoundingClientRect().bottom,
              tbTop: q('.rtabs').getBoundingClientRect().top,
              tbH: q('.rtabs').getBoundingClientRect().height, vh: innerHeight,
              lBottomCss: getComputedStyle(left).bottom, sbDisp: getComputedStyle(q('.statusbar')).display };
  navTab.click(); await sleep(700);
  out.navOn2 = m.classList.contains('kb-nav-on');
  out.leftDisp2 = getComputedStyle(left).display;
  navTab.click(); await sleep(700);
  (q('#article') || document.body).dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true, cancelable: true}));
  await sleep(500);
  out.navOn3 = m.classList.contains('kb-nav-on');
  navTab.click(); await sleep(700);
  q('.rtab[data-pane]').click(); await sleep(700);
  out.mutux = { navOn: m.classList.contains('kb-nav-on'), railOpen: rail.classList.contains('rail-open') };
  navTab.click(); await sleep(700);
  (q('.article') || q('main')).dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
  await sleep(400);
  out.navOn4 = m.classList.contains('kb-nav-on');
  navTab.click(); await sleep(700);
  document.dispatchEvent(new CustomEvent('kb:article-rendered'));
  await sleep(400);
  out.navOn5 = m.classList.contains('kb-nav-on');
  return JSON.stringify(out);
})()"""


# 窄屏工具栏的三件事：可见页签数、换档钳位、展开有没有停在半开帧（用户实拍的红框）
# 抽屉形状本身（右边缘贴入、底边压在工具栏上沿）由下面 RAIL_SHEET_JS 那组断言管。
RAIL_VIS_JS = """(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 100 && !document.querySelector('.rtab'); i++) await wait(50);
  await wait(600);
  const vis = () => [...document.querySelectorAll('.rtab')]
    .filter(t => getComputedStyle(t).display !== 'none').map(t => t.dataset.pane || 'nav');
  const out = { vw: innerWidth, visible: vis(),
                domN: document.querySelectorAll('.rtab[data-pane]').length };
  tab('info', document.querySelector('.rtab[data-pane="info"]'));
  const pane = () => document.querySelector('.rpane.active');
  await wait(120);
  out.h120 = Math.round(pane().getBoundingClientRect().height);
  await wait(780);
  const b = pane().getBoundingClientRect();
  out.h900 = Math.round(b.height);
  out.vh = innerHeight;
  out.paneBottom = Math.round(b.bottom);
  out.sbDisp = getComputedStyle(document.querySelector('.statusbar')).display;
  /* 锚点从状态栏换成视口：状态栏在 ≤980 已整条撤掉（用户图3），拿它的矩形当"底"会量到 0。 */
  out.clipped = b.bottom > innerHeight + 1;
  tab('notes', document.querySelector('.rtab[data-pane="notes"]'));
  await wait(250);
  out.forcedActive = (document.querySelector('.rtab.active') || {}).dataset
    ? document.querySelector('.rtab.active').dataset.pane : null;
  railTabClamp();
  await wait(300);
  out.afterClamp = (document.querySelector('.rtab.active') || {}).dataset
    ? document.querySelector('.rtab.active').dataset.pane : null;
  out.paneAfterClamp = (document.querySelector('.rpane.active') || {}).id;
  out.railOpen = document.querySelector('#p-rail').classList.contains('rail-open');
  // 层级：抽屉要盖住顶栏。main 是 z-index:4 的堆叠上下文，抽屉的 59/60 出不去那一层，
  // 会被 header{z-index:7} 压住顶上 91px（用户实拍：抽屉第一行被切；elementFromPoint 命中 HEADER）。
  const headerAt = (x) => {
    const e = document.elementFromPoint(x, 20);
    return !!(e && e.closest && e.closest('header'));
  };
  out.headerStillOnTop = null;
  const navTab = document.querySelector('#kb-nav-tab');
  if (navTab && getComputedStyle(navTab).display !== 'none') {
    navTab.click(); await wait(450);
    out.headerStillOnTop = headerAt(20);
    const sc = getComputedStyle(document.querySelector('main'), '::after');
    out.scrim = { pos: sc.position, z: sc.zIndex, w: Math.round(parseFloat(sc.width) || 0) };
    navTab.click(); await wait(350);
  }
  return JSON.stringify(out);
})()"""


def probe_rail_sheet(base):
    print("== 16d 窄屏右栏 → 贴底工具栏，点页签展开侧边抽屉 ==")
    url = base + "/doc/ui-r/notes/beta.md"
    got = run_expr(url, RAIL_SHEET_JS, width=390)
    check("工具栏脱离文档流贴在底部（position:fixed），四枚页签都在",
          got.get("pos") == "fixed" and got.get("disp") != "none" and got.get("tabN") == 4, got)
    check("窄屏撤掉底部状态栏（用户图3）：工具栏自己贴住视口底边、通宽、触控区够高",
          got.get("sbDisp") == "none" and got.get("tbBottomGap") == 0
          and got.get("fullWidth") is True and got.get("tbH", 0) >= 44, got)
    check("页签触控区 ≥44px（手机上点不准的按钮等于没有）",
          (got.get("tab0") or {}).get("h", 0) >= 44, got)
    check("默认收起：没有 rail-open，且收起态面板高度真的是 0（不留空壳）",
          got.get("open0") is False and (got.get("pane0") or {}).get("h") == 0
          and got.get("aria0") == "false", got)
    check("点页签展开：抽屉按内容起高、不超出视口、溢出时自己滚",
          got.get("open1") is True and (got.get("openPane") or {}).get("h", 0) > 100
          and (got.get("openRail") or {}).get("y", -1) >= 0
          and got.get("paneWithinViewport") is True
          and got.get("paneScrollH", 0) >= (got.get("openPane") or {}).get("h", 0) - 2
          and got.get("paneOverflow") == "auto" and got.get("aria1") == "true", got)
    check("页签点开的是**侧边抽屉**：撑满整个视口高度（用户图6，top=0 且底边到视口底），"
          "宽 ≤86vw 且 ≤380px、贴右边缘、自己滚；工具栏浮在它之上仍可点，内容底部留白≥工具栏高",
          got.get("panePos") == "fixed" and got.get("paneTop") == 0
          and abs(got.get("paneBottom", -1) - (got.get("vh") or -1)) <= 1
          and got.get("toolbarAbovePane") is True
          and (got.get("panePadBottom") or 0) >= (got.get("tbH") or 999)
          and (got.get("openPane") or {}).get("w", 0) <= 380
          and (got.get("openPane") or {}).get("w", 0) <= round((got.get("vw") or 0) * 0.86) + 1
          and abs(got.get("paneRight", 0) - (got.get("vw") or -1)) <= 1
          and got.get("paneOverflow") == "auto", got)
    check("抽屉不再受 60vh 上限约束（旧写法把面板压在工具栏上方一条里，长目录只能滚一小截）",
          got.get("paneMaxH") in (0, None) and (got.get("openPane") or {}).get("h", 0) > 500, got)
    check("再点当前页签收起", got.get("open2") is False and (got.get("pane2") or {}).get("h") == 0, got)
    check("Esc 收起（Esc 分层关闭链里加了这一环）",
          got.get("open3") is True and got.get("open4") is False, got)
    check("点抽屉外面收起（手机没有 Esc，这是唯一的兜底手势）",
          got.get("open5") is True and got.get("open6") is False, got)
    check("换文档（kb:article-rendered）收起：不然新正文上面还压着上一篇的目录",
          got.get("open7") is False, got)
    check("窄屏不产生横向滚动", got.get("hScroll") is False, got)
    # 窄屏贴底工具栏只留三颗（分类/目录/标签）+ 展开不许停在半开态：用户实拍的那张
    # "只露出标题行的空壳"就是 max-height 过渡的中间帧，红框指的就是它。
    rv = run_expr(url, RAIL_VIS_JS, width=390)
    check("390 档可见页签恰好是三颗：分类 / 目录 / 标签（备注与双链只留宽屏）",
          rv.get("visible") == ["nav", "toc", "info"] and rv.get("domN") == 4, rv)
    check("换档防御：active 停在被隐藏的「备注」上时，railTabClamp 把它落回「目录」，"
          "不留一块看不见页签的面板",
          rv.get("forcedActive") == "notes" and rv.get("afterClamp") == "toc"
          and rv.get("paneAfterClamp") == "pane-toc" and rv.get("railOpen") is True, rv)
    check("面板展开是**一步到位**的：120ms 与 900ms 两次量到同一个高度（没有半开中间帧）",
          rv.get("h120") == rv.get("h900") and (rv.get("h900") or 0) > 100, rv)
    check("面板底边就落在视口底边上（满高抽屉，图6）且不溢出屏幕；窄屏状态栏整条撤掉（图3）",
          rv.get("clipped") is False and abs(rv.get("paneBottom", -1) - rv.get("vh", -2)) <= 1
          and rv.get("sbDisp") == "none", rv)
    dv = run_expr(url, RAIL_VIS_JS, width=1600)
    check("390 档抽屉压在顶栏之上：顶栏那条带里命中的不是 header，且遮罩是 fixed 的一整层",
          rv.get("headerStillOnTop") is False
          and (rv.get("scrim") or {}).get("pos") == "fixed"
          and (rv.get("scrim") or {}).get("z") == "7", rv)
    check("宽屏照旧：四颗文档页签全部可见、clamp 不碰「备注」、底部状态栏仍在（隐藏只归窄屏那一档）",
          dv.get("visible") == ["toc", "info", "notes", "links"]
          and dv.get("afterClamp") == "notes" and dv.get("sbDisp") != "none", dv)
    d = run_expr(url, RAIL_DESK_JS, width=1600)
    check("桌面档零副作用：右栏仍在网格里（relative）、常驻可见，点页签不会长出抽屉态",
          d.get("pos") == "relative" and d.get("open0") is False and d.get("open1") is False
          and d.get("aria0") is None and d.get("aria1") is None
          and d.get("paneH", 0) > 100 and d.get("paneH2", 0) > 100 and d.get("railW", 0) >= 200, d)
    check("桌面档那颗「分类」页签不存在（左树常驻，多一个钮等于假入口）",
          d.get("navTabDisp") == "none" and d.get("leftDisp") != "none"
          and d.get("navOn") is False and d.get("navOnAfterClick") is False, d)
    # 861~980 这一档：style.css 只把网格收成两轨，右栏若还在流里会被甩到第二行
    band = run_expr(url, PRELUDE + r"""
  for (let i = 0; i < 80 && !q('#article h1'); i++) await sleep(150);
  await sleep(700);
  const rect = e => { const b = e.getBoundingClientRect(); return {x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height)}; };
  const rail = q('#p-rail'), left = q('#p-left'), m = q('main');
  out.vw = innerWidth;
  out.tracks = getComputedStyle(m).gridTemplateColumns;
  out.railPos = getComputedStyle(rail).position;
  out.rail = rect(rail);
  out.tb = rect(q('.rtabs'));   // 工具栏的真实矩形：#p-rail 这一层已收成 0 高的容器
  out.vh = innerHeight;
  out.navTab = getComputedStyle(q('#kb-nav-tab')).display;
  out.leftDisp = getComputedStyle(left).display;
  out.left = rect(left);
  out.art = rect(q('#p-article'));
  q('.rtab[data-pane]').click(); await sleep(700);
  out.opened = cls('#p-rail', 'rail-open');
  out.paneH = rect(q('.rpane.active')).h;
  out.paneTop = rect(q('.rpane.active')).y;
  out.paneBottom = Math.round(q('.rpane.active').getBoundingClientRect().bottom);
  out.tbH = Math.round(parseFloat(getComputedStyle(q('.rtabs')).height) || 0);
  out.panePadBottom = Math.round(parseFloat(getComputedStyle(q('.rpane.active')).paddingBottom) || 0);
  return JSON.stringify(out);
})()""", width=900)
    check("900 档：页签条是通宽贴住视口底边的一条（.rtabs 自己 fixed），不是被 grid 换行甩到第二行的 240px 窄柱",
          band.get("railPos") == "fixed" and (band.get("tb") or {}).get("x") == 0
          and (band.get("tb") or {}).get("w") == band.get("vw")
          and 40 <= (band.get("tb") or {}).get("h", 0) <= 90
          and abs((band.get("tb") or {}).get("y", -1) + (band.get("tb") or {}).get("h", 0)
                  - (band.get("vh") or -1)) <= 1
          and len(band.get("tracks", "").split()) == 2, band)
    check("900 档：左树仍是常驻列，「分类」页签不出现（那一档树没被藏）",
          band.get("leftDisp") != "none" and (band.get("left") or {}).get("w", 0) >= 200
          and band.get("navTab") == "none", band)
    check("900 档：工具栏页签照样能展开，且抽屉在这一档同样是满高（顶到上沿、底到视口底、给工具栏留出内容底部）",
          band.get("opened") is True and band.get("paneTop") == 0
          and abs(band.get("paneBottom", -1) - (band.get("vh") or -1)) <= 1
          and (band.get("panePadBottom") or 0) >= (band.get("tbH") or 999), band)
    # ---- 「分类」抽屉：窄屏原本没有翻目录的路径（style.css ≤860 把左树整块隐藏）----
    for w in (390, 800):
        n = run_expr(url, NAV_SHEET_JS, width=w)
        tag = f"{w}px 档"
        check(f"{tag}「分类」页签在工具栏最前面、可见、触控区 ≥44px",
              n.get("tabIsFirst") is True and n.get("tabDisp") not in (None, "none")
              and (n.get("tabRect") or {}).get("h", 0) >= 44, n)
        check(f"{tag}默认不占位：没有 kb-nav-on，左树仍是 display:none",
              n.get("navOn0") is False and n.get("leftDisp0") == "none", n)
        check(f"{tag}点一下左树从左侧滑出：**撑满整个视口高度**（用户图6）、自己滚、"
              f"工具栏仍浮在它上面点得到，内容底部留白≥工具栏高",
              n.get("navOn1") is True and n.get("leftDisp1") == "flex"
              and (n.get("leftRect") or {}).get("h", 0) > 100
              and n.get("navInViewport") is True and n.get("navFullHeight") is True
              and n.get("toolbarPaintedAbove") is True
              and (n.get("navPadBottom") or 0) >= (n.get("raw", {}).get("tbH") or 999)
              and n.get("navScrolls") == "auto" and n.get("ariaNav1") == "true", n)
        check(f"{tag}树真的在里面且域可见（不是空壳面板）",
              n.get("treeItems", 0) >= 1 and (n.get("treeFirstH") or 0) > 8, n)
        check(f"{tag}与右栏抽屉互斥：分类开着时右栏抽屉不会同时展开",
              n.get("railOpenWhenNav") is False, n)
        check(f"{tag}再点一次收起", n.get("navOn2") is False and n.get("leftDisp2") == "none", n)
        check(f"{tag}Esc 收起", n.get("navOn3") is False, n)
        check(f"{tag}点右栏页签 → 分类让位、右栏抽屉展开",
              n.get("mutux") == {"navOn": False, "railOpen": True}, n)
        check(f"{tag}点抽屉外面收起", n.get("navOn4") is False, n)
        check(f"{tag}换文档收起", n.get("navOn5") is False, n)
    check("桌面档也吃得下换文档事件（万一带着 rail-open 会被清掉）",
          d.get("open2") is False, d)


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
    api = json.loads(urllib_get(base + "/api/recent_read") or "{}")
    days = api.get("days") or []
    d = run_expr(base + "/doc/ui-r/notes/alpha.md", SPARK_JS)
    counts = [x.get("count") for x in days]
    check("目录火花：右栏目录下方长出了 #kb-toc-spark 容器", d.get("host_present") is True, d)
    check("目录火花：有数据时是 canvas 柱图（带无障碍标签），不是占位文字",
          d.get("canvas") is True and "近 7 日阅读篇数" in (d.get("aria") or ""), d)
    check("目录火花：柱子的 7 个日标签与逐日篇数 == /api/recent_read（不编数、不合并）",
          d.get("labels") == [str(x.get("date", ""))[8:10] for x in days]
          and d.get("data") == counts and len(counts) == 7,
          {"labels": d.get("labels"), "data": d.get("data"), "api": counts})
    peak = max(counts) if counts else 0
    avg = (sum(counts) / len(counts)) if counts else 0
    check("目录火花：meta 那行写着峰值与日均，数字来自同一份序列",
          f"峰值 {peak} 篇" in (d.get("meta") or "") and f"日均 {avg:.1f} 篇" in (d.get("meta") or ""),
          {"meta": d.get("meta"), "peak": peak, "avg": round(avg, 1)})
    # 空态：把 /api/recent_read 打桩成全 0（只动这一条 URL，其余照常）
    stub = ("(function(){const f=window.fetch;window.fetch=function(u,o){"
            "if(String(u).indexOf('/api/recent_read')>=0){"
            "return Promise.resolve(new Response(JSON.stringify({ok:true,days:"
            "Array.from({length:7},(_,i)=>({date:'2026-09-' + (10+i),count:0})),total:0}),"
            "{status:200,headers:{'Content-Type':'application/json'}}));}"
            "return f.apply(window,arguments);};})()")
    e = run_expr(base + "/doc/ui-r/notes/alpha.md", SPARK_JS, init=stub)
    check("目录火花：全 0 序列必须落到「近 7 日暂无阅读」空态（不许留一根空柱子或转圈的省略号）",
          "近 7 日暂无阅读" in (e.get("empty_txt") or "") and e.get("canvas") is False,
          {"empty": e.get("empty_txt"), "canvas": e.get("canvas"), "meta": e.get("meta")})


# ================================================================ 探针 20：左树打开见 probe_tree_open
# 注：原「设置·小说排版偏好」「小说工具栏」两个探针随书库引擎一并下线。
















KEYS_JS = PRELUDE + r"""
  const T = e => ((e && e.textContent) || '').replace(/\s+/g, ' ').trim();
  const rows = host => [...(host || document).querySelectorAll('.kb-help-row')]
    .map(r => [T(r.querySelector('kbd')), T(r.querySelector('span'))]);
  const btn = q('#kb-settings-btn'); if (btn) btn.click();
  await sleep(600);
  const tab = document.querySelector('#kb-set-tabs [data-sec="keys"]');
  out.tab_present = !!tab;
  if (tab) tab.click();
  await sleep(400);
  out.tab_shown = !!(document.querySelector('.kb-set-sec[data-sec="keys"]')
                     && !document.querySelector('.kb-set-sec[data-sec="keys"]').hidden);
  out.set_rows = rows(document.querySelector('.kb-set-sec[data-sec="keys"]'));
  out.registry = (window.KB && KB.keys && KB.keys.registry || []).map(k => [k.combo, k.desc]);
  out.scopes = [...new Set((window.KB && KB.keys && KB.keys.registry || []).map(k => k.scope))];
  // 关掉抽屉，按 `?` 唤出完整帮助 —— 两处必须是同一份数据源渲染的
  const close = q('#kb-settings-close') || q('.kb-set-x');
  if (close) close.click();
  await sleep(400);
  document.dispatchEvent(new KeyboardEvent('keydown', {key: '?', bubbles: true, cancelable: true}));
  await sleep(600);
  out.help_open = !!(q('#kb-help') && q('#kb-help').classList.contains('show'));
  out.help_rows = rows(q('#kb-help'));
  return JSON.stringify(out);
})()"""


def probe_keys(base):
    print("== 21 快捷键清单：设置抽屉与 `?` 帮助必须同源于 KEY_REGISTRY ==")
    d = run_expr(base + "/doc/ui-r/notes/alpha.md", KEYS_JS)
    reg = d.get("registry") or []
    check("快捷键：KEY_REGISTRY 在页面上可读，且四类作用域都在（global/browse/editor/review）",
          len(reg) == 11 and set(d.get("scopes") or []) == {"global", "browse", "editor"},
          {"n": len(reg), "scopes": d.get("scopes")})
    check("快捷键：设置抽屉的「快捷键」分区能切出来（section 不再 hidden）",
          d.get("tab_present") is True and d.get("tab_shown") is True, d)
    check("快捷键：抽屉里列出的每一条 kbd + 说明与 registry 逐项一致（没有第二份手抄清单）",
          d.get("set_rows") == reg, {"rows": d.get("set_rows"), "reg": reg})
    check("快捷键：按 `?` 真的能唤出完整帮助浮层", d.get("help_open") is True, d)
    check("快捷键：`?` 帮助与设置抽屉是同一份数据源（两处条目逐字相同）",
          d.get("help_rows") == reg and len(d.get("help_rows") or []) == 11,
          {"help": (d.get("help_rows") or [])[:3], "n": len(d.get("help_rows") or [])})






# ================================================================ 探针 23：统计页（月份翻页 / 每日图 / 掌握度）
# 台账 §2 两行：统计 · 月份 prev/next｜统计 · #stDailyChart / #stChartNote / #st-daily-data。
# 口径：事件**只经 /api/track**（应用自己的写路径）造，绝不手改 indexes/reading.db（不变量 3）；
# 判据两头咬住 —— 页面渲染出的数 vs 同一份库用生产谓词重算的数，逐根柱子 vs 模板内嵌的 JSON 载荷。
STATS_DRIVER_JS = PRELUDE + r"""
  const post = (path, event, sec) => fetch('/api/track', {method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({path, event, seconds: sec})}).then(r => r.json());
  out.seeded = [];
  out.seeded.push(await post('ui-r/notes/beta.md', 'read_minute', 60));
  out.seeded.push(await post('ui-r/notes/beta.md', 'read_minute', 60));
  out.seeded.push(await post('ui-r/notes/beta.md', 'read_minute', 60));
  out.seeded.push(await post('baike/term/倒排索引.md', 'read_minute', 60));
  out.seeded.push(await post('baike/term/倒排索引.md', 'open', 0));
  out.seeded.push(await post('ui-r/notes/beta.md', 'finish', 0));
  return JSON.stringify(out);
})()"""

STATS_JS = PRELUDE + r"""
  const T = e => ((e && e.textContent) || '').replace(/\s+/g, ' ').trim();
  // 月份一律从 <title> 读：空态那一档模板不渲染 .stats-body，data-ym 跟着没了（轮次 32 实测）
  const ymOf = () => (document.title.match(/·\s*(\d{4}-\d{2})\s*·/) || [])[1] || null;
  for (let i = 0; i < 60 && !(window.Chart && q('#stDailyChart')); i++) await sleep(150);
  await sleep(1500);
  out.ym = ymOf();
  out.ym_attr = q('.stats-body') ? q('.stats-body').getAttribute('data-ym') : null;
  out.payload = T(q('#st-daily-data'));
  out.ym_title = ymOf();
  out.crumb = [...document.querySelectorAll('.crumb .iconbtn')]
    .map(a => ({href: a.getAttribute('href'), txt: T(a)}));
  out.kpis = [...document.querySelectorAll('.kpi-card')].map(c => ({
    id: c.getAttribute('data-st-card'), num: T(c.querySelector('.num')),
    delta: T(c.querySelector('.delta')), canvas: !!c.querySelector('canvas')}));
  const cv = q('#stDailyChart');
  out.canvas = !!cv;
  out.aria = cv ? (cv.getAttribute('aria-label') || '') : '';
  out.note = txt('#stChartNote');
  out.nochart = txt('.st-nochart');
  out.empty_title = txt('.empty .e-title');
  out.lb = [...document.querySelectorAll('.lb-row')].map(a => ({
    href: a.getAttribute('href'), rank: T(a.querySelector('.lb-rank')),
    t: T(a.querySelector('.lb-t')), min: T(a.querySelector('.lb-min')),
    w: ((a.querySelector('.lb-bar > i') || {}).style || {}).width}));
  const ch = window.Chart && cv ? window.Chart.getChart(cv) : null;
  out.labels = ch ? ch.data.labels : null;
  out.minutes = ch ? ch.data.datasets[0].data : null;
  out.docs = ch ? ch.data.datasets[1].data : null;
  // 四张 KPI 卡各自的小柱子（c1 活跃 / c2 分钟 / c3 打开 / c4 读完）也是同一套序列喂的
  out.sparks = [...document.querySelectorAll('[data-spark]')].map(c => {
    const k = c.querySelector('canvas');
    const g = window.Chart && k ? window.Chart.getChart(k) : null;
    return {kind: c.getAttribute('data-spark'),
            canvas: !!k,
            data: g ? g.data.datasets[0].data : null};
  });
  return JSON.stringify(out);
})()"""

STATS_NAV_JS = PRELUDE + r"""
  const T = e => ((e && e.textContent) || '').replace(/\s+/g, ' ').trim();
  await sleep(900);
  const ymOf = () => (document.title.match(/·\s*(\d{4}-\d{2})\s*·/) || [])[1] || null;
  out.path = location.pathname + location.search;
  out.ym = ymOf();
  out.ym_attr = q('.stats-body') ? q('.stats-body').getAttribute('data-ym') : null;
  out.crumb = [...document.querySelectorAll('.crumb .iconbtn')]
    .map(a => ({href: a.getAttribute('href'), txt: T(a)}));
  out.canvas = !!q('#stDailyChart');
  out.nochart = T(q('.st-nochart'));
  out.empty_title = T(q('.empty .e-title'));
  out.payload = T(q('#st-daily-data'));
  out.kpi_cards = document.querySelectorAll('.kpi-card').length;
  return JSON.stringify(out);
})()"""



def probe_stats(base, tmp):
    print("== 23 统计页：月份 prev/next · 每日图 · 复习卡覆盖 ==")
    import calendar
    from app.reading import ReadingStore
    now_ym = time.strftime("%Y-%m")
    prev_ym = (f"{int(now_ym[:4]) - 1}-12" if now_ym[5:7] == "01"
               else f"{now_ym[:4]}-{int(now_ym[5:7]) - 1:02d}")
    # 造事件走首页上的一次 fetch（首页不发 /api/track，不会污染当月计数）
    seed = run_expr(base + "/", STATS_DRIVER_JS)
    check("统计页：事件经 /api/track 全部收下（tracked 逐条为真）",
          len(seed.get("seeded") or []) == 6
          and all(x.get("tracked") is True for x in (seed.get("seeded") or [])),
          seed.get("seeded"))
    # 生产谓词重算一遍（读的是同一个临时实例的派生库，只读）
    rs = ReadingStore(tmp / "indexes")
    try:
        kpi = rs.monthly(now_ym)
    finally:
        rs.close()
    dim = calendar.monthrange(int(now_ym[:4]), int(now_ym[5:7]))[1]
    # **独立预言**：绕开 monthly()，直接对 reading.db 的原始事件表手写一条聚合。
    # 为什么非要另起一个口径：上一版这里拿 monthly() 的结果去对页面，而页面读的也是
    # monthly() —— 于是把 `"finished": int(d[3])` 改成 0 时两边一起变 0，断言照样绿
    # （定点变异 F 实测存活）。判据必须站在被测函数之外才叫锁。
    import sqlite3
    con = sqlite3.connect(tmp / "indexes" / "reading.db")
    try:
        rows = con.execute(
            """SELECT day, SUM(seconds)/60.0, COUNT(DISTINCT path),
                      COUNT(DISTINCT CASE WHEN event='finish' THEN path END)
               FROM reading_events WHERE ym=? GROUP BY day""", (now_ym,)).fetchall()
        raw_month = con.execute(
            """SELECT COUNT(DISTINCT day), COALESCE(SUM(seconds),0)/60.0,
                      COUNT(DISTINCT CASE WHEN event='open' THEN path END),
                      COUNT(DISTINCT CASE WHEN event='finish' THEN path END)
               FROM reading_events WHERE ym=?""", (now_ym,)).fetchone()
    finally:
        con.close()
    by_day = {r[0]: r for r in rows}
    oracle_min = [round(float(by_day[f"{now_ym}-{i + 1:02d}"][1]), 1)
                  if f"{now_ym}-{i + 1:02d}" in by_day else 0.0 for i in range(dim)]
    oracle_doc = [int(by_day[f"{now_ym}-{i + 1:02d}"][2])
                  if f"{now_ym}-{i + 1:02d}" in by_day else 0 for i in range(dim)]
    oracle_fin = [int(by_day[f"{now_ym}-{i + 1:02d}"][3])
                  if f"{now_ym}-{i + 1:02d}" in by_day else 0 for i in range(dim)]
    d = run_expr(base + "/stats", STATS_JS)

    # ---- 行 1：#stDailyChart / #stChartNote / #st-daily-data
    check("统计页：默认落在当月，KPI 四卡 + 图表都在（不是空态占位）",
          d.get("ym") == now_ym and d.get("ym_attr") == now_ym
          and (d.get("payload") or "[]") != "[]" and len(d.get("kpis") or []) == 4
          and d.get("canvas") is True and not d.get("nochart"),
          {"ym": d.get("ym"), "kpis": len(d.get("kpis") or []),
           "canvas": d.get("canvas"), "nochart": d.get("nochart")})
    check("每日图：横轴按**日历 1..当月天数**铺刻度（缺日也占位，不压缩成有数的几根）",
          d.get("labels") == list(range(1, dim + 1)),
          {"head": (d.get("labels") or [])[:3], "tail": (d.get("labels") or [])[-2:],
           "want": dim})
    payload = json.loads(d.get("payload") or "[]")
    want_min = [0.0] * dim
    want_doc = [0] * dim
    for x in payload:
        day = int(str(x.get("day"))[8:10])
        want_min[day - 1] += float(x.get("minutes") or 0)
        want_doc[day - 1] += int(x.get("docs") or 0)
    check("每日图：两根序列（分钟柱 / 打开篇数线）逐日 == 模板内嵌的 #st-daily-data",
          len(payload) > 0
          and [round(float(v), 1) for v in (d.get("minutes") or [])]
          == [round(v, 1) for v in want_min]
          and d.get("docs") == want_doc,
          {"chart": d.get("minutes"), "payload": want_min,
           "docs": d.get("docs"), "want_doc": want_doc})
    nz = [i for i, v in enumerate(want_min) if v > 0]
    peak_i = max(nz, key=lambda i: want_min[i]) if nz else 0
    sum_min = round(sum(want_min), 1)
    note = d.get("note") or ""
    check("每日图：#stChartNote 的峰值/有记录天数/日均全从同一份序列算（不另编一套数）",
          f"第 {peak_i + 1} 天" in note and f"{want_min[peak_i]:g} 分钟" in note
          and f"有记录 {len(nz)} 天" in note
          and f"日均 {sum_min / dim:.1f} 分钟" in note,
          {"note": note, "peak_day": peak_i + 1, "active": len(nz),
           "avg": round(sum_min / dim, 1)})
    check("每日图：canvas 带无障碍标签且写明当月（读不了图的人还有一句话）",
          now_ym in (d.get("aria") or "") and "每日阅读时长" in (d.get("aria") or ""),
          d.get("aria"))
    mins = [float(x.get("minutes") or 0) for x in kpi["docs"]]
    rows = d.get("lb") or []
    check("文档榜：按当月累计时长降序，第一名正是我灌得最多的那篇，行数与后端一致",
          len(mins) > 0 and mins == sorted(mins, reverse=True)
          and "beta" in (kpi["docs"][0]["path"] or "") and len(rows) == len(kpi["docs"]),
          {"lb": len(rows), "docs": len(kpi["docs"]), "mins": mins})
    check("文档榜：每行分钟数 == 生产谓词算出的分钟数，条形按最高值归一（第一名 100%）",
          bool(rows) and all(r.get("min", "").startswith(f"{k:g} min")
                             for r, k in zip(rows, mins))
          and rows[0].get("w") == "100%",
          {"shown": [r.get("min") for r in rows][:3], "want": mins[:3],
           "w0": rows[0].get("w") if rows else None})

    sparks = {x.get("kind"): x for x in (d.get("sparks") or [])}
    # 读完那条序列用**独立预言**（原始事件表），不用载荷 —— 载荷与图表同源于 monthly()，
    # 两边一起被改坏时"逐日 == 载荷"这种判据会自证通过（变异 F 就是这么活下来的）
    want_fin = oracle_fin
    check("KPI 迷你柱：四张卡的逐日序列 == 分钟/打开按载荷铺、读完按**原始事件表**铺（c4 不许被抹平）",
          {"presence", "minutes", "docs", "finished"} == set(sparks.keys())
          and sparks.get("minutes", {}).get("canvas") is True
          and len(sparks.get("minutes", {}).get("data") or []) == len(want_min)
          and all(abs(a - b) < 1e-9 for a, b in zip(sparks.get("minutes", {}).get("data") or [],
                                                    want_min))
          and sparks.get("docs", {}).get("data") == want_doc
          and sparks.get("finished", {}).get("data") == want_fin
          and sparks.get("presence", {}).get("data") == [1 if v > 0 else 0 for v in want_min]
          and all(sparks[k].get("canvas") is True for k in sparks),
          {"kinds": sorted(sparks.keys()),
           "fin": sparks.get("finished", {}).get("data"), "want_fin": want_fin,
           "min": sparks.get("minutes", {}).get("data"), "want_min": want_min,
           "pres": sparks.get("presence", {}).get("data")})

    # ---- 行 2：KPI 四个数与后端逐项一致（读的是同一份派生库）
    knum = {c.get("id"): c.get("num") for c in (d.get("kpis") or [])}
    check("KPI：活跃天数 / 月度时长 / 访问篇数 / 读完篇数 == ReadingStore.monthly 重算",
          knum.get("c1") == f"{kpi['active_days']}/ {dim} 天"
          and knum.get("c2") == f"{kpi['total_minutes']:g}分钟"
          and knum.get("c3") == f"{kpi['opened_docs']}篇"
          and knum.get("c4") == f"{kpi['finished_docs']}篇",
          {"shown": knum, "want": kpi})
    # 上面那条比的是"页面 vs monthly()"，两者同源 —— 一旦 monthly() 本身被改坏，它会跟着一起绿。
    # 所以再加一条**绕开被测函数**的：直接拿原始事件表的手写聚合对画面。
    check("独立预言：KPI 四个数 == reading_events 手写聚合（monthly() 自己算错也要红）",
          knum.get("c1") == f"{raw_month[0]}/ {dim} 天"
          and knum.get("c2") == f"{round(float(raw_month[1]), 1):g}分钟"
          and knum.get("c3") == f"{raw_month[2]}篇"
          and knum.get("c4") == f"{raw_month[3]}篇",
          {"shown": knum, "raw": raw_month, "dim": dim})
    check("独立预言：每日图的分钟/打开 + c4 的读完序列 == 原始事件表逐日聚合（不是只跟载荷对账）",
          len(d.get("minutes") or []) == dim
          and all(abs(a - b) < 1e-9 for a, b in zip(d.get("minutes") or [], oracle_min))
          and d.get("docs") == oracle_doc
          and sparks.get("finished", {}).get("data") == oracle_fin
          and sum(oracle_fin) >= 1,
          {"chart_fin": sparks.get("finished", {}).get("data"), "oracle_fin": oracle_fin,
           "chart_min": d.get("minutes"), "oracle_min": oracle_min,
           "chart_doc": d.get("docs"), "oracle_doc": oracle_doc})

    # ---- 行 3：月份 prev/next 是真钮、点了真的换月
    crumb = d.get("crumb") or []
    check("月份导航：当月页给 prev 钮、不给 next 钮（未来月份点不出东西）",
          any(c.get("href") == "/stats?ym=" + prev_ym for c in crumb)
          and not any(c.get("href") == "/stats?ym=" + now_ym for c in crumb)
          and any(c.get("href") == "/" for c in crumb), crumb)
    back = run_expr(base + "/stats", STATS_NAV_JS, click=".crumb a:first-of-type")
    check("月份导航：点 prev 钮真的换到上个月（URL 与 data-ym 一起变）",
          back.get("path") == "/stats?ym=" + prev_ym and back.get("ym") == prev_ym,
          {"path": back.get("path"), "ym": back.get("ym")})
    check("月份导航：没有记录的那个月落到空态那句话，KPI 与图表一个都不渲染（不画空图、不编数）",
          prev_ym in (back.get("empty_title") or "") and back.get("ym") == prev_ym
          and back.get("ym_attr") is None and back.get("canvas") is False
          and back.get("kpi_cards") == 0 and back.get("payload") == "[]",
          {"empty": back.get("empty_title"), "canvas": back.get("canvas"),
           "kpi_cards": back.get("kpi_cards"), "payload": back.get("payload")})
    fwd = run_expr(base + "/stats?ym=" + prev_ym, STATS_NAV_JS,
                   click='.crumb a[href="/stats?ym=' + now_ym + '"]')
    check("月份导航：过去那个月给 next 钮，点了回得到当月（来回都得通）",
          fwd.get("ym") == now_ym and fwd.get("path") == "/stats?ym=" + now_ym
          and fwd.get("canvas") is True,
          {"path": fwd.get("path"), "ym": fwd.get("ym"), "canvas": fwd.get("canvas")})
    fut = run_expr(base + "/stats?ym=2030-01", STATS_NAV_JS)
    check("月份导航：翻到未来月份也不给 next 钮（不给点出空洞的机会）",
          fut.get("ym") == "2030-01" and fut.get("ym_attr") is None
          and fut.get("kpi_cards") == 0 and not any(
              (c.get("href") or "").startswith("/stats?ym=2030-02")
              for c in (fut.get("crumb") or [])), fut.get("crumb"))
    bad = run_expr(base + "/stats?ym=2026-9", STATS_NAV_JS)
    check("月份导航：非法 ym（2026-9 少个 0）被路由挡回当月，不带病渲染",
          bad.get("ym") == now_ym and bad.get("path") == "/stats?ym=2026-9", {"ym": bad.get("ym"), "path": bad.get("path")})









# ================================================================ 探针 29：搜索结果页的分面
# 台账 §2 行「搜索页 · #kb-hits / #kb-facets / #kb-facet-clear」：只有 search_results 一张像素基线。
# 搜索浮层（顶部那个）早就有 E2E，但**结果页**的分面多选没人点过 —— 而它的过滤真相在服务端
# （B19：多选全量传参），本地只留一层降级防御。所以判据一律拿 /api/search 的同参数返回当预言。
SEARCH_JS = PRELUDE + r"""
  const SQ = e => (typeof e === 'string' ? q(e) : e);
  const T = e => { const n = SQ(e); return ((n && (n.innerText || n.textContent)) || '').replace(/\s+/g, ' ').trim(); };
  const real = window.fetch;
  const seen = [];                      // 发出去的 /api/search 请求（分面是否真传给后端，只能看这里）
  window.fetch = function (u, o) { const s = String(u); if (s.indexOf('/api/search') === 0) seen.push(s);
                                   return real.apply(this, arguments); };
  const Q = new URLSearchParams(location.search).get('q') || '';
  const call = async (p) => (await (await real('/api/search?q=' + encodeURIComponent(Q) + '&limit=50' + p))).json();
  const rows = () => [...document.querySelectorAll('#kb-hits .result')];
  const chips = () => [...document.querySelectorAll('#kb-facets .kb-facet:not(.clear)')].map(b => ({
    t: b.dataset.type, id: b.dataset.id, n: T(b.querySelector('.kb-facet-n')),
    on: b.classList.contains('on'), ap: b.getAttribute('aria-pressed')}));
  const clear = () => { const c = q('#kb-facet-clear'); return c ? {present: true, hidden: !!c.hidden} : {present: false}; };
  const settle = async (pred, ticks) => { for (let i = 0; i < (ticks || 60); i++) { if (pred()) return true; await sleep(150); } return false; };
  const mark = () => seen.length;

  const j0 = await call('');
  out.n0 = (j0.exact || []).length + (j0.hits || []).length;
  out.api_domains = (j0.facets.domains || []).map(d => ({id: d.id, n: d.n}));
  out.api_tags = (j0.facets.tags || []).map(t => ({id: t.tag, n: t.n}));
  await settle(() => rows().length > 0, 60);
  out.rows0 = rows().length;
  out.meta0 = T('.srch-meta');
  out.groups = [...document.querySelectorAll('#kb-facets .kb-facet-t')].map(T);
  out.chips0 = chips();
  out.clear0 = clear();
  out.url0 = location.search;

  // 选一个"会真的减少结果"的域（n < 总数）
  const dPick = out.api_domains.filter(d => d.n < out.n0)[0] || out.api_domains[0];
  const chipSel = (t, id) => document.querySelector('#kb-facets .kb-facet[data-type="' + t + '"][data-id="' + id + '"]');
  const jd = await call('&domain=' + encodeURIComponent(dPick.id));
  const nd = (jd.exact || []).length + (jd.hits || []).length;
  let m0 = mark();
  chipSel('domain', dPick.id).click();
  await settle(() => chips().some(c => c.t === 'domain' && c.id === dPick.id && c.on), 60);
  await sleep(400);
  out.after_domain = {rows: rows().length, api_n: nd, url: location.search, reqs: seen.slice(m0),
                      chip: chips().find(c => c.t === 'domain' && c.id === dPick.id) || null,
                      hues: [...new Set(rows().map(r => r.getAttribute('data-hue')))],
                      clear: clear(), meta: T('.srch-meta')};

  chipSel('domain', dPick.id).click();
  await settle(() => !chips().some(c => c.t === 'domain' && c.id === dPick.id && c.on), 60);
  await sleep(400);
  out.after_undo = {rows: rows().length, url: location.search, clear: clear(),
                    any_on: chips().some(c => c.on)};

  const tPick = out.api_tags.filter(t => t.n < out.n0)[0] || out.api_tags[0];
  const jboth = await call('&domain=' + encodeURIComponent(dPick.id) + '&tag=' + encodeURIComponent(tPick.id));
  const nboth = (jboth.exact || []).length + (jboth.hits || []).length;
  chipSel('domain', dPick.id).click(); await sleep(350);
  m0 = mark();
  chipSel('tag', tPick.id).click();
  await settle(() => chips().filter(c => c.on).length === 2, 60);
  await sleep(400);
  out.after_two = {rows: rows().length, api_n: nboth, url: location.search, reqs: seen.slice(m0),
                   on: chips().filter(c => c.on).map(c => c.t + ':' + c.id),
                   hues: [...new Set(rows().map(r => r.getAttribute('data-hue')))],
                   meta: T('.srch-meta')};

  m0 = mark();
  q('#kb-facet-clear').click();
  await settle(() => !chips().some(c => c.on) && rows().length === out.n0, 60);
  out.after_clear = {rows: rows().length, url: location.search, clear: clear(), reqs: seen.slice(m0),
                     any_on: chips().some(c => c.on), meta: T('.srch-meta')};

  // 浏览器后退：后退到"带域筛选"那一步，界面必须跟着 URL 回到那个态
  chipSel('domain', dPick.id).click();
  await settle(() => chips().some(c => c.t === 'domain' && c.id === dPick.id && c.on), 60);
  await sleep(400);
  // 只有**确实 pushState 过**才敢 back()：pushUrl 坏掉时 back() 会直接离开这一页，
  // 整个表达式在别的文档里求值 → 崩溃点落在测量工具上，看不出是判据红（变异体实测）。
  out.pushed = location.search.indexOf('domain=') >= 0;
  if (out.pushed) {
    try { history.back(); } catch (e) { out.back_threw = String(e); }
    await settle(() => !chips().some(c => c.on), 60);
    await sleep(500);
  }
  out.after_back = {skipped: !out.pushed, url: location.search,
                    any_on: chips().some(c => c.on), rows: rows().length,
                    has_facets: !!q('#kb-facets'), clear: clear()};
  out.pick = {domain: dPick, tag: tPick};
  return JSON.stringify(out);
})()"""



# 标题 id = 文本去空白后空格→连字符。marked 不生成 heading id，而没有 id 就没有落点 ——
# URL fragment 由 app.js::scrollToHash() 按 id 定位。
HEADING_ID_JS = """(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 80 && !document.querySelectorAll('.a-body h3').length; i++) await wait(50);
  await wait(400);
  const out = { ids: {}, n3: document.querySelectorAll('.a-body h3').length };
  for (const id of ["1.-题干示例｜中级", "2.-另一题干｜高级"]) {
    const el = document.getElementById(id);
    out.ids[id] = { present: !!el, tag: el ? el.tagName : null,
                    text: el ? (el.textContent || "").trim().slice(0, 24) : null };
  }
  out.headings = [...document.querySelectorAll('.a-body h2, .a-body h3')].length;
  out.withId = [...document.querySelectorAll('.a-body h2, .a-body h3')].filter(h => h.id).length;
  out.dups = (() => { const seen = {}, d = [];
    [...document.querySelectorAll('.a-body h2, .a-body h3')].forEach(h => {
      if (!h.id) return; if (seen[h.id]) d.push(h.id); seen[h.id] = 1; });
    return d; })();
  return JSON.stringify(out);
})()"""

# 带 fragment 进来的落点判据（heading id 唯一的消费者，别只验 id 存在）。
# 判据口径：目标在滚动内容里的偏移 off，可达落点 want = min(off, 最大可滚)，滚到 want 且目标
# 贴住容器顶才算兑现。样本正文尾部那段「留白」就是为了把 off 拉进可达范围 —— 之前合成样本只有
# 1.3k 高，1600 档容器实测 745 高，want 恒等于「夹到底」，任何一路实现（包括根本没滚对）都能绿。
# 控制组（同篇不带 fragment）必须停在页首，堵死"夹到底蒙绿"。
HASH_JS = """(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 100 && !document.querySelector('.a-body h3'); i++) await wait(50);
  await wait(1400);
  const sc = document.querySelector('.article') || document.scrollingElement;
  const id = decodeURIComponent(location.hash.slice(1));
  const el = document.getElementById(id);
  const s = sc.getBoundingClientRect(), r = el ? el.getBoundingClientRect() : null;
  const max = Math.max(0, Math.round(sc.scrollHeight - sc.clientHeight));
  const off = el ? Math.round(r.top - s.top + sc.scrollTop) : null;
  const want = el ? Math.min(off, max) : null;
  return JSON.stringify({ id: id, present: !!el, scrolled: Math.round(sc.scrollTop),
    off: off, max: max, want: want,
    canLand: !!(el && off <= max),
    onTarget: !!(el && Math.abs(sc.scrollTop - want) <= 8),
    nearTop: !!(r && Math.abs(r.top - s.top) <= 14),
    visible: !!(r && r.bottom > s.top && r.top < s.bottom),
    hash: location.hash });
})()"""


def probe_heading_ids(base):
    print("== 30 标题 id：URL fragment 的落点（scrollToHash 按 id 定位）==")
    a = run_expr(base + "/doc/ui-r/notes/alpha", HEADING_ID_JS)
    ids = a.get("ids") or {}
    s1, s2 = ids.get("1.-题干示例｜中级") or {}, ids.get("2.-另一题干｜高级") or {}
    check("两道编号题干各有一个 slug id，且分别指向自己的 h3",
          s1.get("present") is True and s2.get("present") is True
          and s1.get("tag") == "H3" and s2.get("tag") == "H3"
          and "题干示例" in (s1.get("text") or "") and "另一题干" in (s2.get("text") or ""),
          {"s1": s1, "s2": s2, "n3": a.get("n3")})
    check("正文每个 h2/h3 都拿到 id（漏一个就等于那条没有落点）",
          a.get("headings", 0) > 0 and a.get("withId") == a.get("headings"), a)
    check("重名标题不产生重复 id（getElementById 只会命中首个，重复即静默错位）",
          a.get("dups") == [], a)
    frag = "1.-题干示例%EF%BD%9C%E4%B8%AD%E7%BA%A7"
    h = run_expr(base + "/doc/ui-r/notes/alpha#" + frag, HASH_JS)
    check("带 #fragment 进来滚到那一条：先确认这一档「贴顶」几何上做得到（不是夹到底）",
          h.get("present") is True and h.get("canLand") is True, h)
    check("带 #fragment 进来真的贴住容器顶（落点 = min(目标偏移, 最大可滚)）",
          h.get("onTarget") is True and h.get("nearTop") is True
          and h.get("visible") is True, h)
    c = run_expr(base + "/doc/ui-r/notes/alpha", HASH_JS)
    check("控制组：同篇不带 fragment 就停在页首（上一条的落点不是「夹到底」蒙出来的）",
          c.get("scrolled") == 0 and c.get("present") is False, c)



def probe_read_history(base):
    print("== 31 阅读历史：顶栏钮把左栏在「分类树」与「最近打开」之间切换 ==")
    url = base + "/doc/ui-r/notes/alpha"
    for w in (1440, 390):
        got = run_expr(url, HIST_JS, width=w)
        tag = f"{w}px"
        check(f"[{tag}] 顶栏「阅读」旁边有第二颗「阅读历史」钮",
              got.get("btnText") == "阅读历史", got)
        check(f"[{tag}] 默认是关的：左栏仍是分类树，历史面板不占地方",
              got.get("closed", {}).get("histOn") is False
              and got.get("closed", {}).get("tree") not in (None, "none"), got)
        check(f"[{tag}] 首屏那一篇就进了历史（记录挂在 setDoc，不是 openDoc —— -boot 走的是内嵌 doc-data）",
              (got.get("histKey") or 0) >= 1, got)
        o = got.get("opened") or {}
        check(f"[{tag}] 点开：树让位、历史面板出现、钮的 aria-expanded=true，列表里有当前这篇",
              o.get("histOn") is True and o.get("tree") == "none" and o.get("hist") != "none"
              and o.get("aria") == "true" and any("排版约定样本" in t for t in (o.get("rows") or [])), got)
        c = got.get("closedAgain") or {}
        check(f"[{tag}] 面板右上角的 × 关掉后回到分类树（aria 一起落回 false）",
              c.get("histOn") is False and c.get("tree") != "none" and c.get("aria") == "false", got)
        n = got.get("afterNav") or {}
        check(f"[{tag}] 换一篇（走客户端路由）后顺序立刻更新：最新在前，面板开着也当场刷新",
              n.get("rows") and "排版约定样本-B" in n["rows"][0] and len(n["rows"]) >= 2, got)
        if w == 390:
            check("[390px] 窄屏从顶栏点进来时把「分类」抽屉一起顶出来（钮亮了而东西在屏外 = 假入口），"
                  "并且这只有历史列表的抽屉也**撑满整个视口高度**（用户图6），状态栏已撤",
                  o.get("navOn") is True and o.get("histTop") == 0
                  and abs(o.get("histBottom", -1) - (o.get("vh") or -1)) <= 1
                  and o.get("sbDisp") == "none", got)
    s390 = run_expr(url, MOBILE_SEARCH_JS, width=390)
    check("[390px] 窄屏顶栏那条常驻搜索框让位，右上角换成一颗搜索钮，且不与视口右边缘溢出",
          s390.get("boxDisp") == "none" and s390.get("btnDisp") != "none"
          and s390.get("btnW", 0) >= 28 and s390.get("overflow") is False, s390)
    check("[390px] 点搜索钮展开的就是那个全局浮层，输入框自动获得焦点，Esc 关得掉",
          s390.get("shown") is True and s390.get("focused") == "kb-so-q"
          and s390.get("afterEsc") is True, s390)
    check("[390px] 搜索浮层是**全屏垂直居中**的弹层（用户图8，对齐统计弹层）："
          "遮罩铺满视口、面板中线与视口中线对齐、上下各留边距、四条圆角回归 14px（不再是贴底 sheet）",
          s390.get("ovW") == s390.get("vw") and s390.get("ovH") == s390.get("vh")
          and s390.get("vCentered") is True and s390.get("hCentered") is True
          and s390.get("margins") is True and s390.get("boxRadius") == "14px", s390)
    check("[390px] 引擎条横排且**不溢出视口**（四颗 nowrap 钮会把 1fr 轨道顶到 419px，"
          "靠 rail 的 min-width:0 收住）",
          s390.get("engDir") == "row" and s390.get("engOverflow") is False, s390)
    s1440 = run_expr(url, MOBILE_SEARCH_JS, width=1440)
    check("[1440px] 宽屏零副作用：搜索框照旧在，那颗移动端搜索钮不存在于视野里",
          s1440.get("boxDisp") != "none" and s1440.get("btnDisp") == "none", s1440)



# 阅读历史面板：一次跑完「默认关 → 点开 → 关掉 → 换文档」四态
HIST_JS = """(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 100 && !document.querySelector('#kb-hist-btn'); i++) await wait(50);
  await wait(600);
  const d = sel => { const e = document.querySelector(sel); return e ? getComputedStyle(e).display : null; };
  const left = document.querySelector('#p-left'), btn = document.querySelector('#kb-hist-btn');
  const rows = () => [...document.querySelectorAll('.kb-hist-i')]
    .map(a => (a.querySelector('.kb-hist-t') || {}).textContent || '');
  let hist = 0;
  try { hist = (JSON.parse(localStorage.getItem('kb-read-history') || '[]') || []).length; } catch (e) {}
  const sb = document.querySelector('.statusbar');
  const out = { vw: innerWidth, btnText: (btn.textContent || '').trim(), histKey: hist,
    closed: { histOn: left.classList.contains('hist-on'), tree: d('#tree') } };
  btn.click(); await wait(400);
  out.opened = { histOn: left.classList.contains('hist-on'), tree: d('#tree'), hist: d('#kb-hist'),
    aria: btn.getAttribute('aria-expanded'), rows: rows(),
    navOn: document.querySelector('main').classList.contains('kb-nav-on'),
    histBottom: Math.round(document.querySelector('#p-left').getBoundingClientRect().bottom),
    histTop: Math.round(document.querySelector('#p-left').getBoundingClientRect().top),
    vh: innerHeight,
    sbDisp: sb ? getComputedStyle(sb).display : null };
  document.querySelector('.kb-hist-x').click(); await wait(300);
  out.closedAgain = { histOn: left.classList.contains('hist-on'), tree: d('#tree'),
                      aria: btn.getAttribute('aria-expanded') };
  btn.click(); await wait(250);
  const link = document.querySelector('#tree a[href$="beta"]');
  if (link) { link.click(); await wait(1800); }
  out.afterNav = { path: location.pathname, rows: rows() };
  return JSON.stringify(out);
})()"""

# 窄屏搜索入口：搜索框让位 → 右上角那颗钮 → 打开的还是同一个浮层
MOBILE_SEARCH_JS = """(async () => {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  for (let i = 0; i < 100 && !document.querySelector('#kb-so-btn'); i++) await wait(50);
  await wait(600);
  const btn = document.querySelector('#kb-so-btn'), box = document.querySelector('.searchbox');
  const b = btn.getBoundingClientRect();
  const out = { vw: innerWidth, boxDisp: getComputedStyle(box).display,
    btnDisp: getComputedStyle(btn).display, btnW: Math.round(b.width),
    overflow: b.right > innerWidth + 1 };
  btn.click(); await wait(500);
  const ov = document.querySelector('#kb-search-ov');
  out.shown = ov.classList.contains('show');
  /* 用户图8：搜索浮层要像「全库快照」那种弹层 —— 遮罩铺满整屏、面板垂直居中，
     不再是贴底升起的一坨 sheet。判据三条：遮罩等于视口、面板中线与视口中线对齐、
     上下都留出边距；再加一条圆角（贴底 sheet 的旧形状是 18px/18px/0/0）。 */
  const obr = ov.getBoundingClientRect();
  out.ovW = Math.round(obr.width);
  out.ovH = Math.round(obr.height);
  const bxb = document.querySelector('.kb-search-box').getBoundingClientRect();
  out.boxTop = Math.round(bxb.top);
  out.boxBottom = Math.round(bxb.bottom);
  out.vh = innerHeight;
  out.vCentered = Math.abs((bxb.top + bxb.height / 2) - innerHeight / 2) <= 6;
  out.hCentered = Math.abs((bxb.left + bxb.width / 2) - innerWidth / 2) <= 6;
  out.margins = Math.round(bxb.top) >= 8 && Math.round(innerHeight - bxb.bottom) >= 8;
  out.boxRadius = getComputedStyle(document.querySelector('.kb-search-box')).borderTopLeftRadius;
  // 引擎条是 overflow-x:auto 的一条：grid 的 1fr 轨道默认 min-content，
  // 四颗 nowrap 的引擎钮会把整条顶到 419px 宽（>390 视口）—— 实测踩过，靠 min-width:0 收住
  const eng = document.querySelector('.kb-search-engines');
  const eb = eng.getBoundingClientRect();
  out.engDir = getComputedStyle(eng).flexDirection;
  out.engOverflow = eb.right > innerWidth + 1;
  out.engW = Math.round(eb.width);
  out.focused = document.activeElement ? document.activeElement.id : null;
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
  await wait(400);
  out.afterEsc = !ov.classList.contains('show');
  return JSON.stringify(out);
})()"""


def probe_search_facets(base):
    print("== 29 搜索结果页：命中列表 / 分面多选 / 清空 / 浏览器后退 ==")
    q = quote("标签")
    api = json.loads(urllib_get(base + f"/api/search?q={q}&limit=50") or "{}")
    n_api = len(api.get("exact") or []) + len(api.get("hits") or [])
    s = run_expr(base + f"/search?q={q}", SEARCH_JS)
    check("搜索页：查询词在**多个域**里都有命中（分面多选需要这个形状，否则后面全是同义反复）",
          len((api.get("facets") or {}).get("domains") or []) >= 2 and n_api >= 2,
          {"domains": (api.get("facets") or {}).get("domains"), "n": n_api})
    check("搜索页：#kb-hits 渲染的行数 == 接口 exact+hits 的条数，顶部读数「共 N 条」跟着它",
          s.get("rows0") == n_api == s.get("n0")
          and f"共 {n_api} 条" in (s.get("meta0") or ""),
          {"rows": s.get("rows0"), "api": n_api, "meta": s.get("meta0")})
    want_chips = {f"domain:{d['id']}": d["n"] for d in s.get("api_domains") or []}
    want_chips.update({f"tag:{t['id']}": t["n"] for t in s.get("api_tags") or []})
    got_chips = {(c["t"] + ":" + c["id"]): int(c["n"]) for c in (s.get("chips0") or [])}
    check("搜索页：每组分面钮的标题只有非空的组、钮上的篇数逐项等于接口 facets",
          all(got_chips.get(k) == v for k, v in want_chips.items())
          and all(c.get("on") is False and c.get("ap") == "false" for c in (s.get("chips0") or []))
          and (s.get("clear0") or {}).get("present") is False,
          {"dom": got_chips, "api": want_chips, "groups": s.get("groups")})
    ad = s.get("after_domain") or {}
    pick_d = (s.get("pick") or {}).get("domain") or {}
    want_d = "domain=" + quote(pick_d.get("id") or "")
    check("搜索页：点一个域分面后真的收窄 —— 行数等于接口同参数的返回、每行 data-hue 都是那个域",
          ad.get("rows") == ad.get("api_n") and ad.get("api_n") < s.get("n0")
          and ad.get("hues") == [pick_d.get("id")], ad)
    # 这一条是变异「域筛选不传给后端」的唯一捕手：search.js 在 renderResults 里留了一层
    # **本地兜底过滤**（B19 注释：正常恒为恒等），所以只比行数时"没传参"和"传了参"长得一模一样。
    check("搜索页：过滤的真相在服务端 —— 点完分面**发出去的请求 URL 里带着 domain=**（本地兜底那条不算）",
          any(want_d in r for r in (ad.get("reqs") or [])), {"want": want_d, "reqs": ad.get("reqs")})
    check("搜索页：选中的分面钮带 .on 且 aria-pressed=true，URL 同步写 domain=（可分享/可刷新回来）",
          (ad.get("chip") or {}).get("on") is True and (ad.get("chip") or {}).get("ap") == "true"
          and f"domain={quote(pick_d.get('id') or '')}" in (ad.get("url") or "")
          and (ad.get("clear") or {}).get("present") is True, ad)
    check("搜索页：顶部读数跟着筛选改（「共 N 条」是屏幕实际条数，不是接口未过滤的那个数）",
          f"共 {ad.get('rows')} 条" in (ad.get("meta") or ""), ad)
    au = s.get("after_undo") or {}
    check("搜索页：再点同一颗是分面**取消** —— 条数回到全量、URL 里 domain 参数消失、清空钮自己收掉",
          au.get("rows") == s.get("n0") and "domain=" not in (au.get("url") or "")
          and au.get("any_on") is False and (au.get("clear") or {}).get("present") is False, au)
    at2 = s.get("after_two") or {}
    pick_t = (s.get("pick") or {}).get("tag") or {}
    check("搜索页：跨组多选（域 + 标签）是**交集**而不是并集 —— 行数等于接口带两个参数的返回",
          at2.get("rows") == at2.get("api_n") and at2.get("api_n") <= min(
              (s.get("after_domain") or {}).get("api_n", 10 ** 6), s.get("n0"))
          and sorted(at2.get("on") or []) == sorted([f"domain:{pick_d.get('id')}", f"tag:{pick_t.get('id')}"])
          and f"tag={quote(pick_t.get('id') or '')}" in (at2.get("url") or ""), at2)
    check("搜索页：两组筛选**同时进同一个请求**（一次请求带 domain 与 tag，而不是本地拼两次结果）",
          any(("domain=" in r and "tag=" in r) for r in (at2.get("reqs") or [])),
          {"reqs": at2.get("reqs")})
    ac = s.get("after_clear") or {}
    check("搜索页：点「清空筛选」一次撤掉所有组 —— 没有 .on、URL 只剩 q、条数回到全量、按钮自己消失",
          ac.get("any_on") is False and ac.get("rows") == s.get("n0")
          and (ac.get("clear") or {}).get("present") is False
          and "domain=" not in (ac.get("url") or "") and "q=" in (ac.get("url") or ""), ac)
    check("搜索页：清空之后那次请求不带任何分面参数（撤的是状态，不是只撤高亮）",
          any("domain=" not in r and "tag=" not in r for r in (ac.get("reqs") or [])),
          {"reqs": ac.get("reqs")})
    ab = s.get("after_back") or {}
    check("搜索页：浏览器后退回到上一步 URL 时，分面态跟着 URL 走（不是留着旧的高亮和旧结果）",
          ab.get("skipped") is False and "domain=" not in (ab.get("url") or "")
          and ab.get("any_on") is False and ab.get("rows") == s.get("n0"), ab)


# ---------------------------------------------------------------- 探针 32：左树一/二级「点击再点一次要收得回去」
# 用户实拍（任务 2）：圈的是**域行与子域行**（AI / 资产 / 文章 / 百科 / 职业 / 面试那一档）。
# 这一档此前有两个写手：pages/workbench.js 挂在 #tree 上的冒泡委托（把 kb-tree-open 写成
# 它 init 那一刻抓到的**闭包集合**）+ app.js 读 LS 渲染。闭包那份不含 revealCurInTree 之后
# 追加的当前域，于是"收起 A 域"会把 B 域的展开态从 LS 里抹掉（实测 ["ui-r"] 变成 ["baike"]）。
# 判据全是"真点 + 真量矩形 + 真读 classList/aria/LS"，不判实现细节。
TREE_COLLAPSE_JS = PRELUDE + r"""
  const rect = e => { const b = e && e.getBoundingClientRect(); return b ? {h: Math.round(b.height), disp: getComputedStyle(e).display} : null; };
  const caret = e => (e ? getComputedStyle(e, '::after').transform : null);
  for (let i = 0; i < 90 && !q('#tree .dom'); i++) await sleep(150);
  await sleep(700);
  const domEl = id => q('#tree .dom[data-dom="' + id + '"]');
  const snap = id => {
    const d = domEl(id), h = d && d.querySelector('.dom-head');
    return {
      open: !!(d && d.classList.contains('open')),
      aria: h ? h.getAttribute('aria-expanded') : null,
      subs: rect(d && d.querySelector('.subs')),
      caret: caret(h && h.querySelector('.dom-glyph')),
    };
  };
  const ls = k => localStorage.getItem(k);
  out.startPath = location.pathname;
  out.start = { cur: snap('ui-r'), other: snap('baike'),
                lsOpen: ls('kb-tree-open'), lsSubdir: ls('kb-subdir-collapsed'),
                lsSub: ls('kb-sub-open') };
  // ① 当前域（被"打开文档自动展开"顶开的）：第一下必须收回去
  const cur = q('#tree .dom[data-dom="ui-r"] .dom-head');
  cur.click(); await sleep(400); out.afterCur1 = snap('ui-r');
  out.afterCur1.path = location.pathname;
  out.afterCur1.lsOpen = ls('kb-tree-open');
  cur.click(); await sleep(400); out.afterCur2 = snap('ui-r');
  out.afterCur2.lsOpen = ls('kb-tree-open');
  // ② 另一个域（默认是收着的）：展开它**不许**把当前域的 LS 记录抹掉（旧写法就是抹掉）
  const other = q('#tree .dom[data-dom="baike"] .dom-head');
  other.click(); await sleep(400); out.afterOther1 = snap('baike');
  out.afterOther1.lsOpen = ls('kb-tree-open');
  out.afterOther1.curStillOpen = snap('ui-r').open;
  other.click(); await sleep(400); out.afterOther2 = snap('baike');
  out.afterOther2.lsOpen = ls('kb-tree-open');
  // ③ ←/→ 对齐第三层：点完域行就是这一层的操作锚点（左收右展）
  other.click(); await sleep(300);
  document.dispatchEvent(new KeyboardEvent('keydown', {key: 'ArrowLeft', bubbles: true, cancelable: true}));
  await sleep(300); out.arrowLeft = snap('baike');
  document.dispatchEvent(new KeyboardEvent('keydown', {key: 'ArrowRight', bubbles: true, cancelable: true}));
  await sleep(300); out.arrowRight = snap('baike');
  other.click(); await sleep(350);                      // 收着 baike 离场，给下一趟重载当物证
  out.beforeReload = snap('baike'); out.beforeReload.lsOpen = ls('kb-tree-open');
  // ④ 二级子域行：点一下收、再点一下开，class 与 aria 同步
  const subA = q('#tree .sub[data-dom="ui-r"][data-sub="notes"]');
  const subSnap = () => {
    const box = subA && subA.nextElementSibling;
    return { collapsed: !!(subA && subA.classList.contains('collapsed')),
             aria: subA ? subA.getAttribute('aria-expanded') : null,
             box: rect(box), lsSub: ls('kb-sub-open'),
             caret: caret(subA && subA.querySelector('.sub-ic')),
             docVisible: !!(q('#tree .doc[data-name="alpha"]') || {}).getBoundingClientRect
                         && q('#tree .doc[data-name="alpha"]').getBoundingClientRect().height > 0 };
  };
  out.sub0 = subSnap();
  subA.click(); await sleep(400); out.sub1 = subSnap();
  subA.click(); await sleep(400); out.sub2 = subSnap();
  out.end = { lsOpen: ls('kb-tree-open'), lsSubdir: ls('kb-subdir-collapsed'),
              lsSub: ls('kb-sub-open') };
  return JSON.stringify(out);
})()"""

# 收起态**落盘**：上一趟把 baike 收了（fresh=False 不清存储），这一趟重新加载页面，
# 必须还是收着的（旧写手那一份闭包会把 LS 写花，所以这里也顺带验"两份真相"没了）。
TREE_RELOAD_JS = PRELUDE + r"""
  for (let i = 0; i < 90 && !q('#tree .dom'); i++) await sleep(150);
  await sleep(700);
  const snap = id => {
    const d = q('#tree .dom[data-dom="' + id + '"]');
    const h = d && d.querySelector('.dom-head');
    return { open: !!(d && d.classList.contains('open')),
             aria: h ? h.getAttribute('aria-expanded') : null,
             subsH: d ? Math.round(d.querySelector('.subs').getBoundingClientRect().height) : -1 };
  };
  out.uiR = snap('ui-r'); out.baike = snap('baike');
  out.lsOpen = localStorage.getItem('kb-tree-open');
  return JSON.stringify(out);
})()"""


def probe_tree_collapse(base):
    print("== 32 左树一/二级：点已展开的域行必须收回去（真点 + 真量矩形 + class/aria/落盘） ==")
    seed = "try{localStorage.setItem('kb-tree-open',JSON.stringify(['ui-r']));}catch(e){}"
    url = base + "/doc/ui-r/notes/alpha.md"
    d = run_expr(url, TREE_COLLAPSE_JS, init=seed)
    st = d.get("start") or {}
    cur1, cur2 = d.get("afterCur1") or {}, d.get("afterCur2") or {}
    check("域行：打开文档时当前域是展开的（.subs 有真实高度，aria=true）",
          (st.get("cur") or {}).get("open") is True
          and ((st.get("cur") or {}).get("subs") or {}).get("h", 0) > 20
          and (st.get("cur") or {}).get("aria") == "true", st)
    check("域行：点已展开的域行**第二次点击真的收起**（class 掉、.subs 高度归 0、aria=false 同步）",
          cur1.get("open") is False and (cur1.get("subs") or {}).get("h") == 0
          and cur1.get("aria") == "false", cur1)
    check("域行：收起只是切层级，绝不把这一篇导航走（URL 一个字节都没动）",
          cur1.get("path") == d.get("startPath"), {"path": cur1.get("path"),
                                                   "start": d.get("startPath")})
    check("域行：再点一次展开回去（class/aria/.subs 高度三者一起回来）",
          cur2.get("open") is True and cur2.get("aria") == "true"
          and (cur2.get("subs") or {}).get("h", 0) > 20, cur2)
    check("域行也有折叠指示：展开态行首三角转了 90°、收起态回到 0°（读 computed transform，不看截图）",
          ((st.get("cur") or {}).get("caret") or "").startswith("matrix(0, 1")
          and (cur1.get("caret") or "").startswith("matrix(1, 0"),
          {"open": (st.get("cur") or {}).get("caret"), "closed": cur1.get("caret")})
    o1, o2 = d.get("afterOther1") or {}, d.get("afterOther2") or {}
    check("域行：展开另一个域时，当前域的展开记录不被抹掉（旧写手那份闭包集合会把 LS 写花）",
          o1.get("open") is True and o1.get("curStillOpen") is True
          and "ui-r" in (o1.get("lsOpen") or "") and "baike" in (o1.get("lsOpen") or ""), o1)
    check("域行：收起 baike 只动 baike 自己（ui-r 的记录还在 LS 里）",
          o2.get("open") is False and "ui-r" in (o2.get("lsOpen") or "")
          and "baike" not in (o2.get("lsOpen") or ""), o2)
    al, ar = d.get("arrowLeft") or {}, d.get("arrowRight") or {}
    check("域行：点完域行就有 ←/→ 的操作锚点（与第三层同一套手势，左收右展且 class/aria 同步）",
          al.get("open") is False and al.get("aria") == "false"
          and ar.get("open") is True and ar.get("aria") == "true", {"left": al, "right": ar})
    s0, s1, s2 = d.get("sub0") or {}, d.get("sub1") or {}, d.get("sub2") or {}
    check("子域行：默认展开态下文档真的可见（.sub-docs 有高度、aria=true）",
          s0.get("collapsed") is False and s0.get("aria") == "true"
          and (s0.get("box") or {}).get("h", 0) > 20 and s0.get("docVisible") is True, s0)
    check("子域行：点一下收起（class 与 aria 一起落回、文档矩形归 0）",
          s1.get("collapsed") is True and s1.get("aria") == "false"
          and (s1.get("box") or {}).get("h") == 0 and s1.get("docVisible") is False, s1)
    check("子域行：再点一下展开（回到原样）",
          s2.get("collapsed") is False and s2.get("aria") == "true"
          and (s2.get("box") or {}).get("h", 0) > 20 and s2.get("docVisible") is True, s2)
    check("折叠指示看得见：展开态行首三角转了 90°，收起态回到 0°（transform 矩阵判，不判截图）",
          (s0.get("caret") or "").startswith("matrix(0, 1")
          and (s1.get("caret") or "").startswith("matrix(1, 0")
          and (s2.get("caret") or "").startswith("matrix(0, 1"),
          {"open": s0.get("caret"), "closed": s1.get("caret")})
    check("层级钥匙各管各的：点满一/二级之后第三层那份 kb-subdir-collapsed 一个字都没被写",
          (d.get("end") or {}).get("lsSubdir") is None
          and "ui-r/notes" in ((d.get("end") or {}).get("lsSub") or ""), d.get("end"))
    # 收起态落盘：baike 现在是收着的，重新加载（不清存储）必须还收着
    r = run_expr(url, TREE_RELOAD_JS, fresh=False)
    check("收起态刷新后仍然生效（落盘的是 LS，不是这一帧的 DOM）",
          (r.get("baike") or {}).get("open") is False
          and (r.get("baike") or {}).get("subsH") == 0
          and (r.get("baike") or {}).get("aria") == "false"
          and (r.get("uiR") or {}).get("open") is True, r)
    # 移动端：「分类」抽屉里就是这同一棵树
    m = run_expr(base + "/doc/ui-r/notes/alpha.md", MOBILE_TREE_JS, width=390, init=seed)
    check("[390px] 移动端「分类」抽屉复用同一棵树：域行点第一下收起（class/aria/矩形三者同步）",
          m.get("navOn") is True and m.get("c1open") is False
          and m.get("c1aria") == "false" and m.get("c1subsH") == 0, m)
    check("[390px] 移动端再点一次展开，且抽屉不会因为切层级被关掉",
          m.get("c2open") is True and m.get("c2subsH", 0) > 20
          and m.get("c2navOn") is True, m)
    check("[390px] 移动端子域行同样能收起/展开",
          m.get("s1collapsed") is True and m.get("s2collapsed") is False, m)


MOBILE_TREE_JS = PRELUDE + r"""
  for (let i = 0; i < 90 && !q('#tree .dom'); i++) await sleep(150);
  await sleep(700);
  q('#kb-nav-tab').click(); await sleep(500);          // 唤出「分类」抽屉
  const dom = q('#tree .dom[data-dom="ui-r"]');
  const head = dom.querySelector('.dom-head');
  const subs = dom.querySelector('.subs');
  const H = () => Math.round(subs.getBoundingClientRect().height);
  out.navOn = q('main').classList.contains('kb-nav-on');
  out.open0 = dom.classList.contains('open'); out.h0 = H();
  head.click(); await sleep(400);
  out.c1open = dom.classList.contains('open'); out.c1aria = head.getAttribute('aria-expanded');
  out.c1subsH = H(); out.c1navOn = q('main').classList.contains('kb-nav-on');
  head.click(); await sleep(400);
  out.c2open = dom.classList.contains('open'); out.c2aria = head.getAttribute('aria-expanded');
  out.c2subsH = H(); out.c2navOn = q('main').classList.contains('kb-nav-on');
  const subA = q('#tree .sub[data-dom="ui-r"][data-sub="notes"]');
  const subH = () => Math.round(subA.nextElementSibling.getBoundingClientRect().height);
  out.s0h = subH();
  subA.click(); await sleep(400); out.s1collapsed = subA.classList.contains('collapsed');
  subA.click(); await sleep(400); out.s2collapsed = subA.classList.contains('collapsed');
  out.s2h = subH();
  return JSON.stringify(out);
})()"""


# ---------------------------------------------------------------- 探针 33：顶栏「阅读历史」开关态永远同步
# 用户报的毛病（任务 5）：面板收了钮还亮着 / 再点一次不是切换。
# 口径：**任何一条路径**之后，钮的 .on、aria-expanded、#p-left.hist-on、面板 computed display
# 四样必须互相一致 —— 开关态只有 #p-left.hist-on 一个判据，其余全是它的投影。
HIST_TOGGLE_JS = PRELUDE + r"""
  for (let i = 0; i < 100 && !q('#kb-hist-btn'); i++) await sleep(50);
  await sleep(600);
  const btn = q('#kb-hist-btn'), left = q('#p-left');
  // 面板是懒建的：一次都没点开过就没有这个节点，那就等于"看不见"，别把 null 当成有 display
  const d = sel => { const e = q(sel); return e ? getComputedStyle(e).display : 'none'; };
  const md = (el) => el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true}));
  const esc = () => document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true, cancelable: true}));
  /* 四样读回来一起判，而且**每一个状态都判**：开关态只有 #p-left.hist-on 一个判据，
     钮的 .on、aria-expanded、面板可见性必须全是它的投影（任何一条路径之后都不许失衡）。 */
  const st = () => {
    const s = {
      histOn: left.classList.contains('hist-on'),
      on: btn.classList.contains('on'),
      aria: btn.getAttribute('aria-expanded'),
      disp: d('#kb-hist'),
      tree: d('#tree'),
      navOn: q('main').classList.contains('kb-nav-on'),
    };
    s.ok = s.on === s.histOn && (s.aria === 'true') === s.histOn && (s.disp !== 'none') === s.histOn;
    return s;
  };
  const consistent = s => s.ok;
  out.s0 = st(); out.k0 = consistent(out.s0);
  btn.click(); await sleep(350); out.s1 = st(); out.k1 = consistent(out.s1);
  btn.click(); await sleep(350); out.s2 = st(); out.k2 = consistent(out.s2);      // 再点一次 = 切回
  btn.click(); await sleep(350); out.s3 = st(); out.k3 = consistent(out.s3);
  // 面板右上角的 ×
  q('.kb-hist-x').click(); await sleep(350); out.s4 = st(); out.k4 = consistent(out.s4);
  btn.click(); await sleep(350); out.s5 = st();
  // 点在面板**内部**不算外面（不许一按列表区就把面板收了）
  md(q('#kb-hist')); await sleep(300); out.s6 = st(); out.k6 = consistent(out.s6);
  // 点在按钮上也不算外面（mousedown 先收、onclick 再翻 = 二次错位，必须整个跳过）
  md(btn); await sleep(300); out.s7 = st(); out.k7 = consistent(out.s7);
  // 点在正文 = 外面：宽屏靠 document 级 mousedown，窄屏靠抽屉自己的"点抽屉外"手势
  const outEl = q('#article') || q('main');
  md(outEl); outEl.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
  await sleep(350); out.s8 = st(); out.k8 = consistent(out.s8);
  btn.click(); await sleep(350); out.s9 = st();
  esc(); await sleep(350); out.s10 = st(); out.k10 = consistent(out.s10);          // Esc
  btn.click(); await sleep(350); out.s11 = st();
  q('.rtab[data-pane="info"]').click(); await sleep(550); out.s12 = st(); out.k12 = consistent(out.s12);
  if (!st().histOn) { btn.click(); await sleep(350); }        // 换文档之前先确保是开着的
  out.s12b = st();
  const link = q('#tree a[href$="gamma"]') || q('a[href$="/gamma"]');
  if (link) { link.click(); await sleep(2200); }
  out.s13 = st(); out.k13 = consistent(out.s13);
  out.path13 = location.pathname;
  out.allKeys = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13].map(i => !!(out['s' + i] || {}).ok);
  return JSON.stringify(out);
})()"""


def probe_hist_toggle(base):
    print("== 33 顶栏「阅读历史」：开关态在每条路径上都必须同步（真点 + 真读 classList/aria/display） ==")
    url = base + "/doc/ui-r/notes/alpha"
    narrow = None
    for w, tag in ((1440, "[1440px]"), (390, "[390px]")):
        d = run_expr(url, HIST_TOGGLE_JS, width=w)
        if w == 390:
            narrow = d
        g = lambda k: d.get(k) or {}
        check(f"{tag} 默认关：钮不亮、aria=false、面板不占地方",
              g("s0").get("histOn") is False and g("s0").get("on") is False
              and g("s0").get("aria") == "false" and g("s0").get("disp") in (None, "none"), g("s0"))
        check(f"{tag} 点一下开：hist-on / .on / aria=true / 面板可见 四样一起到位（树让位）",
              g("s1").get("histOn") is True and g("s1").get("on") is True
              and g("s1").get("aria") == "true" and g("s1").get("disp") != "none"
              and g("s1").get("tree") == "none", g("s1"))
        check(f"{tag} 不传 force 时读当前态取反：再点一次是**收起**不是再展开",
              g("s2").get("histOn") is False and g("s2").get("on") is False
              and g("s2").get("aria") == "false" and g("s2").get("tree") != "none", g("s2"))
        check(f"{tag} 第三次点击又展开（开关是交替不是单向）",
              g("s3").get("histOn") is True and g("s3").get("on") is True, g("s3"))
        check(f"{tag} 面板右上角 × 关掉时，钮的 .on 与 aria 一起落回（不许只剩 aria 骗读屏）",
              g("s4").get("histOn") is False and g("s4").get("on") is False
              and g("s4").get("aria") == "false", g("s4"))
        check(f"{tag} 点在面板内部不算「外面」：mousedown 之后面板照旧开着",
              g("s6").get("histOn") is True and g("s6").get("on") is True, g("s6"))
        check(f"{tag} 点在按钮上的 mousedown 被跳过：不能收了又被 onclick 翻回来（二次错位）",
              g("s7").get("histOn") is True and g("s7").get("on") is True, g("s7"))
        check(f"{tag} 点在正文（抽屉外/遮罩那一片）算「外面」：面板收起且钮跟着回落",
              g("s8").get("histOn") is False and g("s8").get("on") is False
              and g("s8").get("aria") == "false", g("s8"))
        check(f"{tag} Esc 关掉面板同时把钮落回",
              g("s10").get("histOn") is False and g("s10").get("on") is False
              and g("s10").get("aria") == "false", g("s10"))
        if w == 390:
            check(f"{tag} 窄屏从顶栏点进来时「分类」抽屉一起顶出来（钮亮了而东西在屏外 = 假入口）",
                  g("s1").get("navOn") is True, g("s1"))
            check(f"{tag} 点右栏页签会让「分类」抽屉让位 —— 历史面板与那颗钮必须一起回落",
                  g("s12").get("histOn") is False and g("s12").get("on") is False
                  and g("s12").get("navOn") is False, g("s12"))
        else:
            check(f"{tag} 宽屏点右栏页签与历史面板无关：面板照旧开着且四样仍一致",
                  g("s12").get("histOn") is True and g("s12").get("on") is True, g("s12"))
        check(f"{tag} 换文档（客户端路由真跳到另一篇）后钮与面板一起回落",
              (d.get("path13") or "").endswith("/gamma")
              and g("s13").get("histOn") is False and g("s13").get("on") is False
              and g("s13").get("aria") == "false", {"path": d.get("path13"), "s13": g("s13")})
        check(f"{tag} 每一步都满足不变式：.on 与 aria-expanded 恒等于 hist-on，面板可见性同判据",
              len(d.get("allKeys") or []) == 14 and all(d.get("allKeys") or []),
              {"keys": d.get("allKeys"), "states": [g("s5"), g("s9"), g("s11"), g("s12b")]})
    check("[390px] 抽屉那些关闭手势都落在同一个同步点（窄屏整趟 14 个状态无一失衡）",
          bool((narrow or {}).get("allKeys")) and all((narrow or {}).get("allKeys") or []),
          {"keys": (narrow or {}).get("allKeys")})


# ---------------------------------------------------------------- 探针 34：打开任意文章默认落在「目录」页签
# 成因（任务 7）：页签的默认 active 按 doc.has_html 分岔，带 active 的面板恒为 #pane-toc
# —— 两边判据不一致，于是"美化版那一篇"一打开页签亮着「标签」、画面却是目录。
# 现在两边都由同一个判据（toc）派生，窄屏那三颗页签的落回口径也不能再造出二次错位。
DEFAULT_TAB_JS = PRELUDE + r"""
  for (let i = 0; i < 80 && !q('.rtab'); i++) await sleep(150);
  await sleep(700);
  const R = e => { const b = e && e.getBoundingClientRect(); return b ? {h: Math.round(b.height), w: Math.round(b.width), disp: getComputedStyle(e).display} : null; };
  const read = () => {
    const tabs = [...document.querySelectorAll('.rtab[data-pane]')];
    const actTabs = tabs.filter(t => t.classList.contains('active'));
    const sel = tabs.filter(t => t.getAttribute('aria-selected') === 'true');
    const panes = [...document.querySelectorAll('.rpane')].filter(p => p.classList.contains('active'));
    return {
      tabPanes: actTabs.map(t => t.dataset.pane),
      selPanes: sel.map(t => t.dataset.pane),
      paneIds: panes.map(p => p.id),
      paneRect: panes.length ? R(panes[0]) : null,
      tocVisible: R(q('#pane-toc')),
    };
  };
  out.firstPaint = read();
  out.consistent = out.firstPaint.tabPanes.length === 1
    && out.firstPaint.paneIds.length === 1
    && out.firstPaint.tabPanes[0] === 'toc'
    && out.firstPaint.paneIds[0] === 'pane-toc'
    && out.firstPaint.selPanes.join(',') === 'toc';
  // 点「标签」页签：页签与面板必须一起搬过去（不许只亮一个）
  q('.rtab[data-pane="info"]').click(); await sleep(500);
  out.afterInfo = read();
  // 再换一篇文档：窄屏 clamp 只在 notes/links 上落回目录，桌面/信息页签保持用户选择
  const link = q('a[href$="/gamma"]') || q('#tree a[href$="gamma"]');
  if (link) { link.click(); await sleep(2200); }
  out.afterNav = read();
  out.path = location.pathname;
  return JSON.stringify(out);
})()"""


def probe_default_tab(base):
    print("== 34 打开任意文章：默认页签与默认面板必须同一个判据（都落「目录」） ==")
    for rel, why in (("/doc/ui-r/notes/alpha.md", "纯 Markdown 那一篇"),
                     ("/doc/ui-r/notes/beta.md", "旁挂美化版的那一篇（旧写法在这儿分岔）"),
                     ("/doc/ui-r/notes/beta.html", "美化版本体")):
        for w in (1440, 390):
            d = run_expr(base + rel, DEFAULT_TAB_JS, width=w)
            fp = d.get("firstPaint") or {}
            tag = f"[{w}px {why}]"
            check(f"{tag} 首屏默认落在「目录」：唯一的 active 页签是 toc",
                  fp.get("tabPanes") == ["toc"] and fp.get("selPanes") == ["toc"], fp)
            check(f"{tag} 唯一 active 的面板就是 #pane-toc（页签与面板不是两套判据）",
                  fp.get("paneIds") == ["pane-toc"], fp)
            check(f"{tag} 页签态与面板态自洽（四组读数合起来成立，不是各亮各的）",
                  d.get("consistent") is True, d)
            ai = d.get("afterInfo") or {}
            check(f"{tag} 点「标签」后页签与面板一起搬到 info（不出现页签亮着目录、画面是标签）",
                  ai.get("tabPanes") == ["info"] and ai.get("paneIds") == ["pane-info"], ai)
            check(f"{tag} 换文档后仍然只有一个 active 页签与一个 active 面板（clamp 没造出二次错位）",
                  len((d.get("afterNav") or {}).get("tabPanes") or []) == 1
                  and len((d.get("afterNav") or {}).get("paneIds") or []) == 1
                  and (d.get("path") or "").endswith("/gamma"), d.get("afterNav"))


# ---------------------------------------------------------------- 探针 25：会话隔离护栏
# 这条不测产品，测的是**提速改动本身**：本套大量判据默认"localStorage 是干净的"
# （默认排版、默认小说偏好、空看板）。一次一档时那是白来的（每趟新 profile），
# 复用一台浏览器就必须有人盯着 —— 少一次清存储，"默认态"就是脏的，而且是绿着变脏。
ISO_WRITE = PRELUDE + r"""
  localStorage.setItem('kb-isolation-canary', 'leaked');
  out.canary = localStorage.getItem('kb-isolation-canary');
  return JSON.stringify(out);
})()"""

ISO_READ = PRELUDE + r"""
  out.canary = localStorage.getItem('kb-isolation-canary');
  out.keys = Object.keys(localStorage).length;
  return JSON.stringify(out);
})()"""


def probe_isolation(base):
    print("== 25 会话隔离护栏（复用浏览器以后，\"每趟干净\"必须自证） ==")
    page = base + "/doc/ui-r/notes/alpha.md"
    w1 = run_expr(page, ISO_WRITE)
    check("隔离护栏：这一趟写得进 localStorage（写不进去则后面三条都是空判）",
          w1.get("canary") == "leaked", w1)
    r1 = run_expr(page, ISO_READ)
    check("隔离护栏：下一趟读不到上一趟写的 canary（默认 fresh=True 真的在清存储）",
          r1.get("canary") is None, r1)
    run_expr(page, ISO_WRITE, fresh=False)
    r2 = run_expr(page, ISO_READ, fresh=False)
    check("隔离护栏：`fresh=False` 那一档确实**不**清存储（旋钮是真旋钮，不摆设）",
          r2.get("canary") == "leaked", r2)
    r3 = run_expr(page, ISO_READ)
    check("隔离护栏：脏读不会顺着往下传（再回到默认档，canary 又没了）",
          r3.get("canary") is None, r3)


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
        return _ci.skip("ui_behavior", "no-node", "SKIP: 找不到 node")
    if not chrome_path():
        return _ci.skip("ui_behavior", "no-chrome", "SKIP: 找不到 Chrome")
    _ci.started("ui_behavior")

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

        # 顺序有讲究：**破坏性探针一律排最后**，且排在"要用到那些文档"的探针之后
        # （删了 alpha/gamma 之后，任何还需要它们在场的只读探针都会假红 —— 轮次 24 实测）。
        run_probe("nav", probe_nav, base, tmp)          # 一级导航 + 徽标（只读，且要在删除类探针之前拿基线数）
        run_probe("wikilink", probe_wikilink, base)     # 只改编辑器缓冲，不落盘
        run_probe("tag", probe_tag_suggest, base)       # 只读（要右栏渲染出来 → 见 PROBE_WIDTH 注释）
        run_probe("mermaid", probe_mermaid, base, tmp)  # 只读 /raw
        run_probe("asset", probe_asset_rewrite, base)   # 只读 /raw（顺带把 §5 那格补上）
        run_probe("pref", probe_prefs, base)            # 只写 localStorage（不动语料；每趟自带新 profile）
        run_probe("exact", probe_exact, base)           # 只读：/search 精确命中区
        run_probe("anchor", probe_heading_ids, base)    # 只读：标题 slug id 在位，且 #fragment 真滚到落点
        run_probe("history", probe_read_history, base)   # 只读：阅读历史钮 + 窄屏搜索入口
        run_probe("search", probe_search_facets, base)  # 只读：结果页命中/分面多选/清空/后退
        run_probe("chips", probe_head_chips, base)      # 只读：chips / 右栏跳转 / 元信息 / 编辑提示
        run_probe("tree", probe_tree_open, base)        # 只读：点树里的文档真的换页
        run_probe("reveal", probe_tree_reveal, base)    # 只读：深链打开 → 树自动展开并聚焦
        run_probe("collapse", probe_tree_collapse, base)  # 只读：一/二级域行再点一次收得回去 + 落盘 + 移动端
        run_probe("histtoggle", probe_hist_toggle, base)   # 只读：阅读历史开关态在每条路径上都同步
        run_probe("defaulttab", probe_default_tab, base)   # 只读：默认页签与默认面板同一个判据
        run_probe("railsheet", probe_rail_sheet, base)  # 只读：窄屏右栏=贴底工具栏，点页签上滑展开
        run_probe("pretty", probe_pretty, base)         # 只读：美化版出口与只读态
        run_probe("finish", probe_finish_bar, base, tmp)  # 写 reading.db 的 doc_marks（不动语料）
        run_probe("spark", probe_toc_spark, base)       # 写 reading.db 的事件（派生库，不动语料）
        run_probe("keys", probe_keys, base)             # 只读：快捷键两处同源
        run_probe("stats", probe_stats, base, tmp)      # 写：/api/track 造当月事件后看统计页
        run_probe("isolation", probe_isolation, base)   # 只读：复用浏览器的隔离性自证
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
    sys.exit(_ci.guarded(main, "ui_behavior"))
