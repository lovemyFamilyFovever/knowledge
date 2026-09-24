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
  · 一切动态内容（时间、阅读统计、动效）必须在截图前被钉死或排除，否则基线每天红。
    /stats 因随月份变化**故意不在矩阵里**。
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
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

CORPUS = {
    "content/ui-r/notes/alpha.md": DOC_RICH,
    "content/ui-r/notes/beta.md": DOC_B,
    "content/ui-r/notes/beta.html": DOC_HTML_PRETTY,
    "content/ui-r/notes/alpha.md.notes.md": DOC_NOTES_SIDE,
    "content/ui-r/empty-sub/": None,             # None = 只建目录（空子域工作台）
    "content/nv-r/books/长夜.txt": NOVEL_TXT,
}

TAXONOMY = {
    "domains": {"ui-r": {"label": "视觉基线", "hue": 158}, "nv-r": {"label": "基线书库", "hue": 200}},
    "subs": {"ui-r/notes": "排版样本", "ui-r/empty-sub": "空子域", "nv-r/books": "长篇"},
    "sources": {"knowledge": "知库自建"},
    "status": {"stable": "已核对"},
}

# ---------------------------------------------------------------- 截图矩阵
# theme 通过 addScriptToEvaluateOnNewDocument 在页面脚本前写 localStorage 钉死，
# 不依赖"上次点击留下的状态"。
#
# FREEZE 里只放**运行时计数器**：TOC 下方"近 7 日阅读"柱状图读的是 reading.db，
# 而每次截图本身就会往 reading.db 追加一条 open 事件 —— 第一次截和第二次截的柱子高度必然不同。
# 实测（--stability）不冻结它时同一份代码两次截图差 0.0637%，热图整块红都在右下角。
# 代价说清楚：**这块的视觉回归由本矩阵放弃**，它的正确性另有 e2e 断言兜（/api/learn/recent_read）。
FREEZE_CSS = "#kb-toc-spark{display:none!important}"
INIT_TMPL = ("try{localStorage.setItem('kb-theme','%s');"
             "localStorage.setItem('kb-force-motion','0');}catch(e){}"
             "document.addEventListener('DOMContentLoaded',function(){"
             "var s=document.createElement('style');s.id='kb-p5-freeze';"
             "s.textContent=%s;(document.head||document.documentElement).appendChild(s);});")


def _shot(name, path, theme="light", click="", settle=3500, why=""):
    return {"name": name, "path": path, "theme": theme, "click": click, "settle": settle, "why": why}


SHOTS = [
    _shot("doc_md_light", "/doc/ui-r/notes/alpha.md", why="卡片/提示框/表格/代码/双链/备注区"),
    _shot("doc_md_dark", "/doc/ui-r/notes/alpha.md", theme="dark", why="同一篇的暗色态：翻色令牌是否成对"),
    _shot("doc_pretty_iframe", "/doc/ui-r/notes/beta.md", why="同名美化版默认走 iframe"),
    _shot("doc_md_via_toggle", "/doc/ui-r/notes/beta.md", click="#kb-md-src-btn",
          why="点「Markdown 源」后的第二视图"),
    _shot("doc_tags_pane", "/doc/ui-r/notes/alpha.md", click='.rtab[data-pane="info"]',
          why="右侧面板切到标签页（树 + 标签编辑态）"),
    _shot("browse_empty_sub", "/browse/ui-r/empty-sub", why="空子域空态（D1 那次的回归面）"),
    _shot("novel_txt", "/doc/nv-r/books/%E9%95%BF%E5%A4%9C.txt", why="书库 txt：章节切分与阅读排版"),
    _shot("novel_txt_prefs", "/doc/nv-r/books/%E9%95%BF%E5%A4%9C.txt", click=".nv-pref-btn",
          why="小说「排版」抽屉打开态（滑杆/选项）"),
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
        jobs.append({"url": base_url + s["path"], "out": str(out_dir / f"{s['name']}.png"),
                     "w": 1440, "h": 900, "click": s["click"], "settle": s["settle"],
                     "init": INIT_TMPL % (s["theme"], json.dumps(FREEZE_CSS))})
    f = out_dir.parent / f"manifest-{out_dir.name}.json"
    f.write_text(json.dumps({"shots": jobs}, ensure_ascii=False), encoding="utf-8")
    return f


def capture(base_url, tag, shots):
    """跑 shot.mjs 批量模式，返回实际图目录。"""
    out_dir = QA / tag
    if out_dir.exists():
        shutil.rmtree(out_dir)
    mf = make_manifest(base_url, out_dir, shots)
    r = subprocess.run(["node", str(ROOT / "scripts" / "agent" / "shot.mjs"), "--batch", str(mf)],
                       cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    for line in (r.stdout or "").splitlines():
        if line.startswith("FAIL"):
            print(f"    {_safe(line)}")
    got = sorted(p.name for p in out_dir.glob("*.png"))
    check(f"[{tag}] 截图矩阵 {len(shots)} 张全部产出",
          got == sorted(f"{s['name']}.png" for s in shots),
          f"got={got} rc={r.returncode} {(r.stderr or '')[-200:]}")
    # 空白页也是"确定"的 —— 光比差异会把它读成绿。这里加一条最便宜的绊线：
    # 1440×900 的纯白页 PNG 只有十几 KB，渲染过的页面在 70~170KB（实测基线区间）。
    thin = {p.name: p.stat().st_size for p in out_dir.glob("*.png") if p.stat().st_size < 40000}
    check(f"[{tag}] 无空白截图（每张 >40KB，实测基线 71~170KB）", not thin, f"{thin}")
    return out_dir


AE_RE = re.compile(r"AE=(-?\d+)")


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
    global PORT
    if not node_available():
        print("SKIP: 找不到 node"); return 0
    if not chrome_path():
        print("SKIP: 找不到 Chrome"); return 0
    if not magick_available():
        print("SKIP: 找不到 ImageMagick（imgdiff.mjs 依赖它）"); return 0

    update = "--update" in sys.argv
    stability = "--stability" in sys.argv
    missing = [s["name"] for s in SHOTS
               if not (BASELINES / f"{s['name']}.png").exists()]
    if missing and not (update or stability):
        print(f"基线缺失 {len(missing)}/{len(SHOTS)}：{missing}\n"
              f"先跑 --stability 证明 harness 确定，再跑 --update 落基线。")
        return 1

    tmp = Path(tempfile.mkdtemp(prefix="p5-root-"))
    proc = None
    try:
        build_corpus(tmp)
        # create_app 的 static_folder 是 <KB_ROOT>/static：临时根没它就全 404（P3-B 同款坑）
        shutil.copytree(ROOT / "static", tmp / "static")
        PORT = free_port()
        QA.mkdir(parents=True, exist_ok=True)
        check("端口现挑且不落在用户常驻端口", PORT not in (5000, 5001, 5031), f"port={PORT}")
        proc = start_instance(tmp, PORT, log_path=QA / "instance.log")
        base = f"http://127.0.0.1:{PORT}"
        check("临时实例起来了", port_open(PORT))
        # 页面可达性先各断一条：404 会让"截图一致但全白屏"这种假绿成为可能
        for path in ("/doc/ui-r/notes/alpha.md", "/browse/ui-r/empty-sub"):
            code = subprocess.run(["node", "-e",
                                   f"fetch({json.dumps(base + path)}).then(r=>console.log(r.status))"],
                                  capture_output=True, text=True, timeout=60)
            check(f"页面可访问 {path}", (code.stdout or "").strip() == "200",
                  f"got={(code.stdout or code.stderr).strip()[-80:]}")

        actual = capture(base, "actual", SHOTS)
        if stability:
            again = capture(base, "actual2", SHOTS)
            print("\n[stability] 同一份代码两次截图互比（这一步红 = harness 不确定，基线无意义）")
            for s in SHOTS:
                ae, info = compare(actual / f"{s['name']}.png", again / f"{s['name']}.png")
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
    finally:
        kill_instance(proc)
        shutil.rmtree(tmp, ignore_errors=True)
        check("清理只删掉了系统临时目录下的临时根", not tmp.exists()
              and str(tmp).startswith(tempfile.gettempdir())
              and (ROOT / "content").is_dir(), f"tmp={tmp}")

    print(f"\n{passed} passed, {failed} failed")
    print(f"实际截图与差异热图：{QA}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
