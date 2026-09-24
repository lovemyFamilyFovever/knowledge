# -*- coding: utf-8 -*-
"""知库 **P3-B · JS 侧书库解析的性质测试**（畸形样本喂进真浏览器）。

运行：python tests/test_js_props.py     （需要本机有 Chrome 与 node）

为什么单独一套：手册 §P3-B 点名的三个历史线上 bug（txt 乱码、epub「No Section Found」、
封面图空白）全在 `static/kb-novel.js` 这条解析线上，而 Python 侧工具够不着它。
本脚本不测"真书能不能打开"，只测**对任意畸形输入不得崩、且必须给出可判定结果**：

    · decodeTxt      任意字节序列不得抛未捕获异常；BOM 必须剥掉；非法 UTF-8 必须降级到 GB18030
    · buildChapters  章节数 ≥ 1；逐行口径"一行都不能丢"；每样本的带标题章数逐条钉死
    · normalizeEpubBytes  不合法/截断/缺 container 的 zip 一律返回 null（= 不重写、按原样交给 epub.js），
                     只有"编码错位"那种才返回新 ArrayBuffer；且**不得挂起**（超时即失败）
    · savePos/loadPos  循环引用、坏 JSON、2000 字超长 rel 下不得抛（那两层 try/catch 是唯一防护）

工程约定：
  · 全部样本现造在 `tempfile` 里的**临时 KB_ROOT** 下，绝不往真实 `content/` 写一个字节；
  · 端口由 `free_port()` 现挑，并在断言里证明它不是用户常驻的 5001；临时实例收工必杀；
  · 浏览器里跑的是真页面 + 真 vendor 库（JSZip/epub.js），不是 jsdom 之类的替身。

变异验证（2026-09-24 本轮手工改坏源码逐处复跑，证明断言不是摆设）：
    normalizeEpubBytes 的 `dec(clean)` 去掉           → 1 红
    `if (!fixes) return null` 改成恒不返回 null        → 3 红
    container 判据取反                                 → 3 红
    loadPos 的 try/catch 摘掉                          → 2 红
    savePos 的 try/catch 摘掉                          → 2 红（circular 探针报 THREW）
    末章 push 的 `||` 改 `&&`                          → 1 红（trailing-title 的 titled）
    过渡 push 的 `||` 改 `&&`                          → 2 红（preamble 的 n）
    每章 paras 丢首行                                  → 2 红（逐行口径）
    GB18030 降级改掉                                   → 1 红
    BOM 分支摘掉                                       → **全绿**：等价变异——`new TextDecoder("utf-8")`
        默认 `ignoreBOM:false` 本来就会吃掉前导 BOM，所以那条 if 只是不依赖运行时默认值的显式保险。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
import io
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _tmpapp import chrome_path, free_port, kill_instance, port_open, start_instance  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# 端口在 main() 里由 free_port() 现挑（绝不写死 5031，也绝不落在用户的 5001 上），
# 所以 BASE 是函数而不是模块常量。
PORT = None


def base() -> str:
    return f"http://127.0.0.1:{PORT}"
QA = ROOT / ".qa" / "p3b"

passed = failed = 0


def _safe(s):
    """把任意文本压成当前控制台编码能打印的形式。

    本套的 extra 里会带浏览器返回的正文片段，畸形样本天然能产出 U+FFFD 这类字符：
    实测把 GB18030 降级改掉后，FAIL 打印直接抛 UnicodeEncodeError('gbk')，
    整套测试在报出失败名之前就崩了 —— 红测试崩成"看不出为什么红"比不跑还糟。
    """
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


# ---------------------------------------------------------------- 样本构造
def _opf(items, spine, toc="toc.ncx"):
    manifest = "\n".join(f'    <item id="{i}" href="{h}" media-type="{m}"/>' for i, h, m in items)
    ref = "\n".join(f'    <itemref idref="{i}"/>' for i in spine)
    return ("""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>性质测试书</dc:title><dc:language>zh</dc:language>
    <dc:identifier id="id">urn:uuid:p3b</dc:identifier>
  </metadata>
  <manifest>
    <item id="ncx" href="%s" media-type="application/x-dtbncx+xml"/>
%s
  </manifest>
  <spine toc="ncx">
%s
  </spine>
</package>""" % (toc, manifest, ref)).encode("utf-8")


def _ncx(points, labels=None):
    labels = labels or points
    nav = "\n".join(
        f'    <navPoint id="n{i}" playOrder="{i + 1}"><navLabel><text>第{i + 1}章</text></navLabel>'
        f'<content src="{p}"/></navPoint>' for i, p in enumerate(points))
    return ("""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head><meta name="dtb:uid" content="urn:uuid:p3b"/></head>
  <docTitle><text>性质测试书</text></docTitle>
  <navMap>
%s
  </navMap>
</ncx>""" % nav).encode("utf-8")


def epub_bytes(entries, opf_path="OEBPS/content.opf", container_ok=True, items=None,
               spine=None, ncx_points=None):
    """entries: {zip 内真实文件名: bytes}。opf/ncx 默认按 entries 自动列 manifest。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/epub+zip")
        if container_ok:
            z.writestr("META-INF/container.xml",
                       ('<?xml version="1.0"?>'
                        '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">'
                        '<rootfiles><rootfile full-path="%s" media-type="application/oebps-package+xml"/>'
                        '</rootfiles></container>' % opf_path).encode("utf-8"))
        for name, data in entries.items():
            z.writestr(name, data)
        items = items or [(f"c{i}", name, "application/xhtml+xml")
                          for i, name in enumerate(entries)]
        z.writestr(opf_path, _opf(items, spine or [i for i, _, _ in items]))
        z.writestr("OEBPS/toc.ncx", _ncx(ncx_points or [n for n in entries]))
    return buf.getvalue()


XHTML = ('<?xml version="1.0" encoding="UTF-8"?>'
         '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>t</title></head>'
         '<body><h1>第一章</h1><p>正文内容正文内容。</p></body></html>').encode("utf-8")

FIXTURES = {
    # 正常书：normalize 不该动手
    "good.epub": epub_bytes({"OEBPS/c1.xhtml": XHTML, "OEBPS/c2.xhtml": XHTML}),
    # 多看版：zip 存原始名（含 * | :），OPF/NCX 里却是百分号编码 → 必须被就地解码
    "dk-encoding.epub": epub_bytes(
        {"OEBPS/第一*章.xhtml": XHTML, "OEBPS/第二|章.xhtml": XHTML},
        items=[("c0", "第一%2A章.xhtml", "application/xhtml+xml"),
               ("c1", "第二%7C章.xhtml", "application/xhtml+xml")],
        ncx_points=["第一%2A章.xhtml", "第二%7C章.xhtml"]),
    # 编码错位但解码也查不到（真缺文件）→ 不动手
    "missing-target.epub": epub_bytes(
        {"OEBPS/存在.xhtml": XHTML},
        items=[("c0", "%E4%B8%8D%E5%AD%98%E5%9C%A8.xhtml", "application/xhtml+xml")],
        ncx_points=["%E4%B8%8D%E5%AD%98%E5%9C%A8.xhtml"]),
    "no-container.epub": epub_bytes({"OEBPS/c1.xhtml": XHTML}, container_ok=False),
    "wrong-opf-path.epub": epub_bytes({"OEBPS/c1.xhtml": XHTML}, opf_path="NOPE.opf"),
    "empty-zip.epub": (lambda b: (zipfile.ZipFile(b, "w").close(), b.getvalue())[1])(io.BytesIO()),
    "truncated.epub": epub_bytes({"OEBPS/c1.xhtml": XHTML})[:60],
    "zero-byte.epub": b"",
    "garbage.epub": bytes(bytearray(range(256))) * 4,
    "nul-name.epub": epub_bytes({"OEBPS/a\x00b.xhtml": XHTML}),
}
TXT_FIXTURES = {
    "bom-utf8.txt": "﻿第一章\n内容\n".encode("utf-8"),
    "plain-utf8.txt": "第二章\n内容\n".encode("utf-8"),
    "gb18030.txt": "第三章\n中文内容用 GBK 存。\n".encode("gb18030"),
    "invalid-utf8.txt": b"\xff\xfe\x00\x01\xe9\x94\x99",
    "empty.txt": b"",
    "nul.txt": "第四章\n\x00中间有 NUL\n".encode("utf-8"),
    "crlf.txt": "\r\n\r\n第一章\r\nabc\r\n".encode("utf-8"),
    "huge-line.txt": ("第五章\n" + "字" * 200000 + "\n").encode("utf-8"),
}
CHAPTER_TEXTS = {
    "no-chapter": "从头到尾没有章节标记的一段正文。\n第二行。\n",
    "one-chapter": "第一章 起\n正文 A\n正文 B\n",
    "many": "".join(f"第{i}章 标题\n内容{i}\n" for i in range(1, 121)),
    "long-title": "第一章这是一串长得超过四十二个字符的章节标题" + "啊" * 40 + "\n正文\n",
    "mixed-cn-num": "第一 Chapter 1\n楔子\n正文\n尾声\n后记\n番外篇·补充\n",
    "empty": "",
    "only-blank": "\n\n   \n\t\n",
    "crlf": "第一章\r\n正文\r\n第二章\r\n正文\r\n",
    # 下面两条是给"末尾/开头那两个 push 点"准备的：只断"不丢字符"测不到它们，
    # 因为标题不足 2 个时会整篇兜底，把丢失的碎片重新捞回来（实测把末章 push 的 `||` 改成
    # `&&`，前面 8 个样本全测不出来）。必须钉住**每样本的带标题章数**才咬得住。
    # 注意末尾**不能**带换行：带了就多出一行空串，cur.lines 非空，两种写法结果相同。
    "trailing-title": "第一章 起\n正文\n第二章 完",   # 末章只有标题、后面一行正文都没有
    "preamble": "这是没有章节标记的引子。\n第一章 起\n正文 A\n第二章 又\n正文 B\n",  # 首个标题前有正文
}

# 各切分样本期望的"带标题章数"（trailing-title / preamble 见上：它们专门盯末章与过渡 push）
EXPECT_TITLED = {"one-chapter": 1, "trailing-title": 2, "preamble": 2, "crlf": 2}

# 一个真会出卡的 baike 词条：`cards.py` 只对 baike/interview 抽卡，复习页要能测就得有它。
BAIKE_DOC = """---
title: 向量数据库
source: knowledge
collected: 2026-01-09
tags: [检索]
---

# 向量数据库

## 定义

**一句话定义：** 把文本变成坐标、按距离找相似内容的存储。
"""

# TOC 跟随断言用的长文档：五个小节、每节够长，滚动能真正跨过 top≤96 那条线。
TOC_DOC = ("---\ntitle: 目录跟随样本\n---\n\n# 大标题\n"
           + "".join(f"\n## 第{i}节\n\n" + ("正文行。\n" * 18) for i in range(1, 6)))


def write_fixtures(root: Path):
    d = root / "content" / "小说" / "p3b"
    d.mkdir(parents=True, exist_ok=True)
    for name, data in FIXTURES.items():
        (d / name).write_bytes(data)
    for name, data in TXT_FIXTURES.items():
        (d / name).write_bytes(data)
    return d


# ---------------------------------------------------------- 端口与临时实例：见 tests/_tmpapp.py
# （起实例这段现在由 P3-B 与 P5 共用，安全约束只写一处：端口现挑、禁占 5001、只指临时 KB_ROOT）


JS_BODY = r"""
(async function () {
  var out = {uncaught: [], epub: {}, txt: {}, chap: {}, pos: {}, ms: 0};
  var t0 = performance.now();
  await (window.KBNOVEL.ensureEpubLib ? window.KBNOVEL.ensureEpubLib() : Promise.resolve());
  async function grab(url) {
    var r = await fetch(url);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.arrayBuffer();
  }
  // epub 侧：normalizeEpubBytes 必须在 8 秒内给出结论（挂起 = 当年的 blob URL 卡死）
  var EPUPS = %EPUBS%;
  for (var i = 0; i < EPUPS.length; i++) {
    var n = EPUPS[i], rec = {};
    var t1 = performance.now();
    try {
      var buf = await grab('/raw/小说/p3b/' + encodeURIComponent(n));
      var res = await Promise.race([
        window.KBNOVEL.normalizeEpubBytes(buf),
        new Promise(function (_, rej) { setTimeout(function () { rej(new Error('TIMEOUT')); }, 8000); })
      ]);
      rec.kind = res === null ? 'null' : (res instanceof ArrayBuffer ? 'buffer' : typeof res);
      if (res instanceof ArrayBuffer) {
        var z = await window.JSZip.loadAsync(res);
        var opf = z.file('OEBPS/content.opf');
        var xml = opf ? await opf.async('string') : '';
        var m, RE = /href="([^"]+)"/g, bad = 0, total = 0;
        while ((m = RE.exec(xml))) {
          total++;
          var raw = m[1].split('#')[0].replace(/&amp;/g, '&');
          if (!z.file('OEBPS/' + raw) && !z.file(raw)) bad++;
        }
        rec.dangling = bad; rec.hrefs = total;
      }
    } catch (e) { rec.error = String(e && e.message || e).slice(0, 80); }
    rec.ms = Math.round(performance.now() - t1);
    out.epub[n] = rec;
  }
  // txt 侧：任意字节不得抛，且 BOM 必须被剥掉
  var TXTS = %TXTS%;
  for (var j = 0; j < TXTS.length; j++) {
    var tn = TXTS[j], tr = {};
    try {
      var ab = await grab('/raw/小说/p3b/' + encodeURIComponent(tn));
      var text = window.KBNOVEL.decodeTxt(ab);
      tr.type = typeof text;
      tr.head = text.slice(0, 12);
      tr.hasBom = text.charCodeAt(0) === 0xFEFF;
      tr.len = text.length;
      var cs = window.KBNOVEL.buildChapters(text, tn);
      tr.chapters = cs.length;
      tr.titled = cs.filter(function (c) { return c.title; }).length;
      var paras = cs.reduce(function (a, c) { return a + (c.paras || []).length; }, 0);
      tr.paras = paras;
      tr.nonBlankLines = text.split(/\r?\n/).filter(function (l) { return l.trim(); }).length;
    } catch (e) { tr.error = String(e && e.message || e).slice(0, 80); }
    out.txt[tn] = tr;
  }
  // 章节切分：直接在页面里跑字符串样本
  var CHAPS = %CHAPS%;
  Object.keys(CHAPS).forEach(function (k) {
    try {
      var cs = window.KBNOVEL.buildChapters(CHAPS[k], k);
      // 逐行口径。被 CHAP_RE 命中且 ≤42 字符的标题行会渲染成小节标题：正常章不进 paras，
      // 但标题不足 2 个时会走兜底整篇成 1 章、标题行又留在 paras 里 —— 一进一出，
      // 所以「字符总数相等」这个口径会被骗过（实测 one-chapter 差 4）。
      // 改成只断言一件绝不该发生的事：**非标题行必须一行不少地出现在段落里**（多算不算错，丢了才是错）。
      var RE = window.KBNOVEL.CHAP_RE;
      var want = CHAPS[k].split(/\r?\n/)
        .filter(function (l) { return l.trim() && !(RE.test(l) && l.trim().length <= 42); })
        .map(function (l) { return l.trim(); });
      var got = cs.reduce(function (a, c) {
        // 段落是"连续非空行 join 成一块"，所以必须按正则 /\n+/ 拆回行；
        // 写成 split('\n+') 是按字面量拆，永远拆不开 —— 我第一版就栽在这儿。
        return a.concat((c.paras || []).join('\n').split(/\n+/));
      }, []).map(function (l) { return l.trim(); }).filter(function (l) { return l; });
      var miss = want.filter(function (l) { return got.indexOf(l) < 0; });
      out.chap[k] = {n: cs.length, titled: cs.filter(function (c) { return c.title; }).length,
                     lost: miss.length, sample: miss.slice(0, 2)};
    } catch (e) { out.chap[k] = {error: String(e && e.message || e).slice(0, 80)}; }
  });
  // 续读位置：savePos/loadPos 各自只有一层 try/catch 防护（static/kb-novel.js:246-247）。
  // 去掉 catch 的后果是"读过的书再点就白屏"，而且只在 localStorage 里留下坏 JSON 时复现，
  // 手工几乎测不到 —— 所以这里主动造坏数据。每个探针返回 true=行为正确，
  // 抛出异常则由 t() 记成 'THREW:...'。
  var POS = {};
  function t(name, fn) {
    try { POS[name] = fn(); }
    catch (e) { POS[name] = 'THREW:' + String(e && e.message || e).slice(0, 60); }
  }
  function K(rel) { return 'kb-nv-pos:' + rel; }
  t('roundtrip', function () {
    window.KBNOVEL.savePos('p3b/第一章.md', {cfi: '/6/2!/4/1:0', pct: 0.5});
    var v = window.KBNOVEL.loadPos('p3b/第一章.md');
    return !!v && v.cfi === '/6/2!/4/1:0' && v.pct === 0.5;
  });
  t('overwrite', function () {
    window.KBNOVEL.savePos('p3b/ov.md', {n: 1});
    window.KBNOVEL.savePos('p3b/ov.md', {n: 2});
    var v = window.KBNOVEL.loadPos('p3b/ov.md');
    return !!v && v.n === 2;
  });
  t('isolated', function () {
    window.KBNOVEL.savePos('p3b/a.md', {n: 1});
    window.KBNOVEL.savePos('p3b/b.md', {n: 2});
    var a = window.KBNOVEL.loadPos('p3b/a.md'), b = window.KBNOVEL.loadPos('p3b/b.md');
    return !!a && a.n === 1 && !!b && b.n === 2;
  });
  t('weirdRel', function () {
    // 中文/冒号/2000 字超长 rel：键名拼接不得越界串台，也不得抛
    var longRel = 'x' + '长'.repeat(1000) + ':a/b:c.md';
    window.KBNOVEL.savePos(longRel, {ok: 1});
    var v = window.KBNOVEL.loadPos(longRel);
    return !!v && v.ok === 1 && localStorage.getItem(K('x' + '长'.repeat(999) + ':a/b:c.md')) === null;
  });
  t('missingKey', function () { return window.KBNOVEL.loadPos('p3b/never-written.md') === null; });
  t('circular', function () {
    var o = {n: 1};
    o.self = o;                                  // JSON.stringify 会抛 TypeError
    window.KBNOVEL.savePos('p3b/circ.md', o);    // 必须被 catch 吃掉
    window.KBNOVEL.loadPos('p3b/circ.md');       // 读回去同样不得抛
    return true;
  });
  t('undefinedDropped', function () {
    window.KBNOVEL.savePos('p3b/undef.md', {a: undefined, f: function () {}});
    var v = window.KBNOVEL.loadPos('p3b/undef.md');
    return !!v && typeof v === 'object';
  });
  t('corruptJson', function () {
    localStorage.setItem(K('p3b/bad.md'), '{不是 JSON');
    return window.KBNOVEL.loadPos('p3b/bad.md') === null;
  });
  t('scalarStored', function () {
    // 存进去的是合法 JSON 但不是对象：loadPos 只负责"不抛 + 原样给回"，判定留给调用方
    localStorage.setItem(K('p3b/s1.md'), '123');
    localStorage.setItem(K('p3b/s2.md'), '"str"');
    localStorage.setItem(K('p3b/s3.md'), 'null');
    localStorage.setItem(K('p3b/s4.md'), '[]');
    return window.KBNOVEL.loadPos('p3b/s1.md') === 123 &&
           window.KBNOVEL.loadPos('p3b/s2.md') === 'str' &&
           window.KBNOVEL.loadPos('p3b/s3.md') === null &&
           Array.isArray(window.KBNOVEL.loadPos('p3b/s4.md'));
  });
  ['p3b/第一章.md', 'p3b/ov.md', 'p3b/a.md', 'p3b/b.md', 'p3b/circ.md', 'p3b/undef.md',
   'p3b/bad.md', 'p3b/s1.md', 'p3b/s2.md', 'p3b/s3.md', 'p3b/s4.md']
    .forEach(function (k) { localStorage.removeItem(K(k)); });
  out.pos = POS;
  out.ms = Math.round(performance.now() - t0);
  return JSON.stringify(out);
})()
"""


def build_expr():
    js = (JS_BODY.replace("%EPUBS%", json.dumps(list(FIXTURES), ensure_ascii=False))
          .replace("%TXTS%", json.dumps(list(TXT_FIXTURES), ensure_ascii=False))
          .replace("%CHAPS%", json.dumps(CHAPTER_TEXTS, ensure_ascii=False)))
    QA.mkdir(parents=True, exist_ok=True)
    f = QA / "expr.js"
    f.write_text(js, encoding="utf-8")
    return f


# ---------------------------------------------------------------- 复习页统计竞态（§6 第 24 行）
# refreshStats 有两个并发来源（进页面一次、每次记分一次），没有序号守卫时"谁后到谁写 DOM"。
# 这里不换网络：直接替掉 window.KB.api.today（learn.js 调用时才取属性，所以补丁生效），
# 灌两个假响应 —— **先发的那个慢、后发的那个快**，于是"后到的"是旧数据。
# 有守卫：副标题取新数据（7/42%）；把守卫去掉：副标题被旧数据覆盖（满屏 99）。
RACE_JS = r"""
(async function () {
  var out = {calls: 0, seq: 0, sub: '', afterDone: '', ready: false};
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  var sub = document.getElementById('kb-learn-sub');
  if (!sub || !window.KB || !window.KB.api || !window.KBLEARN) { out.err = '页面未就绪（缺 KBLEARN/KB.api）'; return JSON.stringify(out); }
  for (var i = 0; i < 60 && !/张/.test(sub.textContent || ''); i++) await sleep(200);
  out.ready = /张/.test(sub.textContent || '');
  if (!out.ready) { out.err = '队列没出卡（副标题只在有当前卡时写）'; return JSON.stringify(out); }
  var real = window.KB.api.today, n = 0;
  window.KB.api.today = function () {
    n++;
    var mine = n;
    return new Promise(function (res) {
      setTimeout(function () {
        res({ stats: mine === 1
          ? { due_n: 99, new_left: 99, streak_days: 99, mastered_pct: 99, done_today: 99 }
          : { due_n: 7, new_left: 3, streak_days: 2, mastered_pct: 42, done_today: 1 } });
      }, mine === 1 ? 600 : 50);
    });
  };
  window.KBLEARN.refreshStats();
  window.KBLEARN.refreshStats();
  await sleep(1500);
  out.calls = n;
  out.seq = window.KBLEARN.statsSeq();
  out.sub = (sub.textContent || '').replace(/\s+/g, '');
  // 阶段 2：done 态（showDone 写过"本轮完成…"）之后，统计刷新不得再把这行改回队列口径。
  // 这一行有两个写者（refreshStats 与 showDone），只加 seq 守卫时两者仍会按异步先后互相覆盖。
  if (window.KBLEARN.setDone) {
    sub.textContent = '本轮完成 1 张 · 已全部过完';
    window.KBLEARN.setDone(true);
    window.KBLEARN.refreshStats();
    await sleep(700);
    out.afterDone = (sub.textContent || '').replace(/\s+/g, '');
    window.KBLEARN.setDone(false);
  } else { out.err2 = 'KBLEARN.setDone 未导出'; }
  window.KB.api.today = real;
  return JSON.stringify(out);
})()
"""


def build_race_expr():
    QA.mkdir(parents=True, exist_ok=True)
    f = QA / "expr-race.js"
    f.write_text(RACE_JS, encoding="utf-8")
    return f


# ---------------------------------------------------------------- TOC 跟随判据（§6 第 25 行）
# 断言的不是"长什么样"（那是 P5 的活），而是**规则本身**：
# 当前节 = 最后一个已经滚过顶线（top ≤ 96）的标题。这里在浏览器里独立复算一遍期望值，
# 再和页面真正高亮的那条比。app.js 若退回旧的"IO entries 里最后一个 isIntersecting 获胜"，
# 滚动中段就会高亮错条目，本探针立刻红。
TOC_JS = r"""
(async function () {
  var out = {links: 0, steps: [], moved: 0, err: ''};
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function txt(n) { return ((n && n.textContent) || '').replace(/\s+/g, ''); }
  try {
    await sleep(1800);                                    // 等 enhanceArticleDOM + buildToc
    var art = document.querySelector('.article');
    var links = Array.prototype.slice.call(document.querySelectorAll('#pane-toc a'));
    var heads = Array.prototype.slice.call(
      document.querySelectorAll('#article .a-body h1, #article .a-body h2, #article .a-body h3'));
    out.links = links.length;
    if (links.length < 3 || heads.length < 3) {
      out.err = 'TOC 条目不足 3 条（样本或渲染没生效）: links=' + links.length + ' heads=' + heads.length;
      return JSON.stringify(out);
    }
    function want() {                                     // 独立复算判据
      var cur = 0;
      for (var i = 0; i < heads.length; i++) { if (heads[i].getBoundingClientRect().top <= 96) cur = i; }
      return txt(links[Math.min(cur, links.length - 1)]);
    }
    function act() { return txt(document.querySelector('#pane-toc a.on')); }
    var seen = {};
    // 必须"滚一格 → 等 IO 落一格 → 量一格"。一口气把 scrollTop 设完再回头量，
    // 量到的每一格都是最后一档的几何（我第一版就这么错着，want 全是同一个值）。
    var ys = [0, 400, 800, 1116, 1600];
    for (var i = 0; i < ys.length; i++) {
      art.scrollTop = ys[i];
      art.dispatchEvent(new Event('scroll'));
      await sleep(600);
      var st = {y: art.scrollTop, act: act(), want: want()};
      if (st.act) seen[st.act] = 1;
      out.steps.push(st);
    }
    out.moved = Object.keys(seen).length;
  } catch (e) { out.err = String(e && e.message || e).slice(0, 90); }
  return JSON.stringify(out);
})()
"""


def build_toc_expr():
    QA.mkdir(parents=True, exist_ok=True)
    f = QA / "expr-toc.js"
    f.write_text(TOC_JS, encoding="utf-8")
    return f


# ---------------------------------------------------------------- 正文预处理（§5 最后一行 JS）
# 手册 P0 说这两个函数"模块内、未挂 window"，实测**不成立**：`static/app.js` 是顶层经典脚本，
# `function sanitizeFences` / `function enhanceArticleDOM` 直接成为 window 上的全局，
# 所以不用为了测试去改产品代码（零风险）。
#
# 两条判据各抓什么：
#   · sanitizeFences 只该改"闭栏的缩进"，所以**行数不变、非空白字符多重集不变、且幂等**；
#     任何"顺手删了点东西"的实现都会在这里露出来（它改的是要写回渲染管线的原文）。
#   · enhanceArticleDOM 是纯打补丁，**跑两遍必须和跑一遍一样**（幂等），
#     且每种标记各只产出一个结构（卡片/徽章/代码壳/表格壳/四类引用）。
ENH_JS = r"""
(async function () {
  var out = {globals: {}, f: {n: 0, threw: [], bad: [], golden: []}, e: {}, err: ''};
  function prng(seed) { var x = seed >>> 0; return function () { x = (x * 1664525 + 1013904223) >>> 0; return x / 4294967296; }; }
  try {
    out.globals.sanitizeFences = typeof window.sanitizeFences;
    out.globals.enhanceArticleDOM = typeof window.enhanceArticleDOM;
    if (out.globals.sanitizeFences !== 'function' || out.globals.enhanceArticleDOM !== 'function') {
      out.err = '两个预处理函数不在 window 上：' + JSON.stringify(out.globals);
      return JSON.stringify(out);
    }
    // —— 1) sanitizeFences ——
    var samples = [
      '', '   ', '```js\ncode\n```', '正文\n  ```\n  x\n  ```\n',
      '- a\n  ```py\n  print(1)\n  ```\n',                 // 列表内缩进开栏 + 缩进闭栏
      '- a\n  ```py\n  print(1)\n```',                     // 闭栏顶格（幽灵块的成因）
      '```\n  ```\n```\n',                                 // 三层嵌套
      '~ ~\n```\ntext', '```', '``````', '\t```\n x\n\t```',
      '中文 ``` 混排\n  ```\n', '`'.repeat(3000),
      'a\n'.repeat(4000) + '  ```\n',
      '未闭合\n```open\n没有闭栏'
    ];
    var rnd = prng(20260924);
    var pool = ['`', '~', ' ', '\t', '\n', 'a', '中', '\\', '*', '#', '>'];
    for (var r = 0; r < 120; r++) {
      var s = '', L = 1 + Math.floor(rnd() * 60);
      for (var k = 0; k < L; k++) s += pool[Math.floor(rnd() * pool.length)];
      samples.push(s);
    }
    function chars(t) { return (t || '').replace(/\s+/g, '').split('').sort().join(''); }
    samples.forEach(function (src) {
      out.f.n++;
      var got;
      try { got = window.sanitizeFences(src); }
      catch (e) { out.f.threw.push(String(e && e.message || e).slice(0, 60)); return; }
      if (typeof got !== 'string') { out.f.bad.push('返回不是字符串'); return; }
      if (got.split('\n').length !== src.split('\n').length) { out.f.bad.push('行数变了'); return; }
      if (chars(got) !== chars(src)) { out.f.bad.push('非空白字符被增删'); return; }
      var again;
      try { again = window.sanitizeFences(got); } catch (e2) { out.f.threw.push('二次调用抛错'); return; }
      if (again !== got) out.f.bad.push('不幂等');
    });
    // 金样例：判据不能是"输出里有没有缩进围栏"（那串输入本来就有缩进的**开栏**，
    // 我把对齐那行删掉时这条照样通过 —— 实测漏过一次），必须逐字比期望输出。
    out.f.golden = [
      // 顶格闭栏 → 必须对齐到开栏的两格缩进
      {in: '- a\n  ```py\n  print(1)\n```', want: '- a\n  ```py\n  print(1)\n  ```'},
      // 已经对齐的闭栏 → 一个字符都不该动
      {in: '正文\n  ```\n  x\n  ```\n', want: '正文\n  ```\n  x\n  ```\n'},
      // 顶格开栏的普通围栏 → 不该被"修"成缩进
      {in: '```js\ncode\n```', want: '```js\ncode\n```'},
      // 波浪号围栏：闭栏与开栏不同字符时不该被当成闭栏
      {in: '~~~\na\n```\nb\n~~~', want: '~~~\na\n```\nb\n~~~'},
    ].map(function (c) {
      var got = window.sanitizeFences(c.in);
      return {in: c.in, got: got, ok: got === c.want};
    });
    // —— 2) enhanceArticleDOM ——
    function build() {
      var host = document.createElement('div');
      host.innerHTML =
        '<div class="a-body">' +
        '<h1>大标题</h1><p>游离段</p>' +
        '<h2>小节一</h2><p>A</p><h3>1. 题干示例｜中级</h3><p>B</p>' +
        '<h2>小节二</h2><blockquote>\uD83D\uDCA1 提示</blockquote>' +
        '<blockquote>⚠️ 警告</blockquote><blockquote>\uD83C\uDFAF 关键要点</blockquote>' +
        '<blockquote>\uD83D\uDD0D 追问</blockquote>' +
        '<pre><code class="language-python">x = 1</code></pre>' +
        '<table><tr><td>a</td></tr></table>' +
        '<ul><li><input type="checkbox"> 待办</li></ul>' +
        '</div>';
      return host;
    }
    function tally(host) {
      function n(sel) { return host.querySelectorAll(sel).length; }
      return {
        cards: n('.a-body .sec-card'), badgeM: n('.a-body h3 .badge.m'),
        tip: n('blockquote.tip'), warn: n('blockquote.warn'),
        kp: n('blockquote.kp'), fu: n('blockquote.fu'),
        code: n('.a-body .codeblock'), tbl: n('.a-body .tbl-wrap'),
        task: n('li.task-list-item'),
        h1out: n('.a-body > h1'), grouped: n('.a-body[data-sec-grouped]'),
        gh: (function () { var h = host.querySelector('.a-body h2'); return h ? h.style.getPropertyValue('--gh') : ''; })(),
        id: (function () { var h = host.querySelector('.a-body h2'); return h ? (h.id || '') : ''; })()
      };
    }
    var h1 = build();
    window.enhanceArticleDOM(h1);
    out.e.once = tally(h1);
    window.enhanceArticleDOM(h1);
    out.e.twice = tally(h1);
    // 空壳与畸形输入不得抛
    var weird = [document.createElement('div'),
                 (function () { var d = document.createElement('div'); d.innerHTML = '<div class="a-body"></div>'; return d; })(),
                 (function () { var d = document.createElement('div'); d.innerHTML = '<div class="a-body"><pre><code></code></pre><h3>｜高级</h3></div>'; return d; })()];
    out.e.weirdThrew = [];
    weird.forEach(function (d) {
      try { window.enhanceArticleDOM(d); } catch (e) { out.e.weirdThrew.push(String(e && e.message || e).slice(0, 60)); }
    });
  } catch (e) { out.err = String(e && e.message || e).slice(0, 120); }
  return JSON.stringify(out);
})()
"""


def build_enh_expr():
    QA.mkdir(parents=True, exist_ok=True)
    f = QA / "expr-enh.js"
    f.write_text(ENH_JS, encoding="utf-8")
    return f


def run_expr(url, expr_file):
    return subprocess.run(["node", str(ROOT / "scripts" / "agent" / "evalcdp.mjs"),
                           url, "@" + str(expr_file)],
                          cwd=str(ROOT), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300,
                          env=dict(os.environ, KB_EVAL_WAIT_MS="6000", KB_EVAL_OUT_CHARS="20000"))


def parse_eval(r):
    """把 evalcdp 的 `EVAL: ... CONSOLE_ERRORS: ...` 输出拆成 (json, console 报错文本)。"""
    out = r.stdout or ""
    blob = out.split("EVAL:", 1)[1].split("CONSOLE_ERRORS:", 1)[0].strip() if "EVAL:" in out else ""
    errs = out.split("CONSOLE_ERRORS:", 1)[1].strip() if "CONSOLE_ERRORS:" in out else "?"
    try:
        return (json.loads(json.loads(blob)) if blob else {}), errs
    except Exception as e:                            # noqa: BLE001
        check("CDP 返回能解析", False, f"{e} / {blob[:200]} {(r.stderr or '')[-200:]}")
        return {}, errs


def split_console_errs(errs):
    """把 console 报错分成"本套该管的"和"来自 archify 交付件的"。

    首页 iframe 里嵌的是 `static/archify/*.html`，那是另一条线（架构图）的产物，
    它自己报错不该把书库测试判红 —— 2026-09-24 实测就被另一会话未提交的 WIP 顶红过一次
    （`zhiku-pipeline.html:13607` 的 null.querySelector）。
    判据是**栈帧是否全部落在 archify 里**：只要有一帧来自 app.js / kb-*.js / 页面本身，
    就照常算失败，不做无脑放行。
    """
    lines = [l.strip() for l in (errs or "").splitlines() if l.strip()]
    if not lines or lines == ["none"]:
        return "", ""
    frames = [l for l in lines if l.startswith("at ")]
    if frames and all("static/archify/" in f for f in frames):
        return "", "\n".join(lines)
    return "\n".join(lines), ""


def main():
    global PORT
    if not shutil.which("node"):
        print("SKIP: 找不到 node")
        return 0
    if not chrome_path():
        print("SKIP: 找不到 Chrome")
        return 0

    tmp = Path(tempfile.mkdtemp(prefix="p3b-root-"))
    proc = None
    try:
        write_fixtures(tmp)
        # create_app 的 static_folder 是 <KB_ROOT>/static —— 临时根没有它就全 404，
        # kb-novel.js / vendor 都进不了页面，测的就是空气了。
        shutil.copytree(ROOT / "static", tmp / "static")
        (tmp / "content" / "_meta").mkdir(parents=True, exist_ok=True)
        (tmp / "content" / "_meta" / "taxonomy.json").write_text(
            '{"domains": {}}', encoding="utf-8")
        # 复习页竞态探针要有一张真卡：cards.py 只对 baike/interview 抽卡
        (tmp / "content" / "baike" / "term").mkdir(parents=True, exist_ok=True)
        (tmp / "content" / "baike" / "term" / "向量数据库.md").write_text(
            BAIKE_DOC, encoding="utf-8")
        # TOC 跟随探针用的长文档（§6 第 25 行的判据断言）
        (tmp / "content" / "ui-x" / "notes").mkdir(parents=True, exist_ok=True)
        (tmp / "content" / "ui-x" / "notes" / "目录跟随样本.md").write_text(
            TOC_DOC, encoding="utf-8")
        PORT = free_port()
        QA.mkdir(parents=True, exist_ok=True)
        check("端口是现挑的且不是用户的 5001/5000/5031",
              PORT not in (5000, 5001, 5031), f"port={PORT}")
        proc = start_instance(tmp, PORT, log_path=QA / "instance.log")
        check("临时实例起来了", port_open(PORT))

        expr = build_expr()
        data, console_errs = parse_eval(run_expr(base() + "/", expr))
        epub, txt, chap = data.get("epub", {}), data.get("txt", {}), data.get("chap", {})
        pos = data.get("pos", {})

        # —— epub：每个样本都要有结论，且不得挂起
        check("epub 样本全部有结论（无一项缺失）", set(epub) == set(FIXTURES), f"{sorted(epub)}")
        hang = [k for k, v in epub.items() if v.get("ms", 0) >= 8000]
        check("normalizeEpubBytes 无一挂起（8 秒超时未触发）", not hang, f"{hang}")
        check("正常书 normalize 返回 null（绝不多改一遍）", epub.get("good.epub", {}).get("kind") == "null",
              f"got {epub.get('good.epub')}")
        dk = epub.get("dk-encoding.epub", {})
        check("多看版错位书返回新 ArrayBuffer 且重写后零悬空 href",
              dk.get("kind") == "buffer" and dk.get("dangling") == 0 and dk.get("hrefs", 0) >= 2,
              f"got {dk}")
        for name in ("missing-target.epub", "no-container.epub", "wrong-opf-path.epub", "empty-zip.epub"):
            check(f"{name} → null（不认识的包一律不动手）", epub.get(name, {}).get("kind") == "null",
                  f"got {epub.get(name)}")
        for name in ("truncated.epub", "zero-byte.epub", "garbage.epub", "nul-name.epub"):
            v = epub.get(name, {})
            check(f"{name} 有明确结论（null 或 error），不是静默挂死",
                  v.get("kind") in ("null", "buffer") or "error" in v, f"got {v}")

        # —— txt：任意字节不得抛
        bad = {k: v for k, v in txt.items() if "error" in v}
        check("decodeTxt 对 8 种字节样本均不抛异常", not bad, f"{bad}")
        check("BOM 被剥掉（首字符不是 U+FEFF，正文从「第一章」开始）",
              txt.get("bom-utf8.txt", {}).get("hasBom") is False and
              txt.get("bom-utf8.txt", {}).get("head", "").startswith("第一章"),
              f"got {txt.get('bom-utf8.txt')}")
        g = txt.get("gb18030.txt", {})
        check("非法 UTF-8 自动降级到 GB18030（第三章能读出来）",
              g.get("head", "").startswith("第三章") or "第三章" in str(g), f"got {g}")
        z = txt.get("empty.txt", {})
        check("空文件不崩（len=0 且有章节结论）", "error" not in z and z.get("len") == 0, f"got {z}")
        h = txt.get("huge-line.txt", {})
        check("20 万字单行不崩且不挂起", "error" not in h and h.get("len", 0) > 200000, f"got {h}")
        check("txt 样本的章节数都 ≥1（永不出空书）",
              all(v.get("chapters", 0) >= 1 for v in txt.values()), f"{txt}")

        # —— buildChapters：不丢内容
        check("章节样本全部有结论", set(chap) == set(CHAPTER_TEXTS), f"{sorted(chap)}")
        lost = {k: v for k, v in chap.items() if "error" in v or v.get("lost", 0) != 0}
        check("buildChapters 不丢任何非空白字符（含无章节/超长标题/纯空白/120 章）", not lost, f"{lost}")
        many = chap.get("many", {})
        check("120 章样本切出 120 章", many.get("n", 0) >= 120 and many.get("titled", 0) >= 120,
              f"got {many}")
        lt = chap.get("long-title", {})
        check("超长标题不被当成章节标记（退回全文兜底，1 章）", lt.get("titled", 0) <= 1, f"got {lt}")
        ob = chap.get("only-blank", {})
        check("纯空白文本仍返回 1 章（不出 No Section Found 式空壳）", ob.get("n", 0) == 1, f"got {ob}")
        # 章数口径：只有"不丢字符"会漏掉末章/过渡章被整篇兜底重新捞回的情况
        wrong_n = {k: (chap.get(k, {}).get("titled"), v) for k, v in EXPECT_TITLED.items()
                   if chap.get(k, {}).get("titled") != v}
        check("带标题章数逐样本对得上（含末章只有标题、首标题前有正文两种边角）",
              not wrong_n, f"expect/actual {wrong_n}")
        pre = chap.get("preamble", {})
        check("preamble 样本切出 3 章（引子独立成章 + 2 个带标题章）且引子行不丢",
              pre.get("n") == 3 and pre.get("titled") == 2 and pre.get("lost") == 0, f"got {pre}")

        # —— 续读位置：savePos/loadPos 只有一层 try/catch，摘掉就是"读过的书再点白屏"
        probes = ["roundtrip", "overwrite", "isolated", "weirdRel", "missingKey",
                  "circular", "undefinedDropped", "corruptJson", "scalarStored"]
        check("pos 探针全部有结论", set(pos) == set(probes), f"{sorted(pos)}")
        threw = {k: pos[k] for k in probes
                 if isinstance(pos.get(k), str) and str(pos.get(k)).startswith("THREW")}
        check("savePos/loadPos 对 9 种输入均不抛（含循环引用/坏 JSON/超长 rel）", not threw, f"{threw}")
        wrong = {k: pos[k] for k in probes if pos.get(k) is not True}
        check("9 条 pos 探针结果全为 true（值对，不只是不抛）", not wrong, f"{wrong}")

        # —— 复习页统计竞态：换第二个页面（/review）再跑一次 CDP
        race, race_errs = parse_eval(run_expr(base() + "/review", build_race_expr()))
        check("review 页探针跑起来了（KBLEARN 已导出、队列出了卡）",
              race.get("ready") is True, f"{race} / CONSOLE_ERRORS: {race_errs[:160]}")
        check("探针确实发出了两次 today 请求", race.get("calls") == 2, f"{race}")
        sub_txt = str(race.get("sub", ""))
        check("后发的新响应赢：副标题取 7/42%（不是慢到的旧响应 99）",
              "99" not in sub_txt and "到期7张" in sub_txt and "42%" in sub_txt, f"sub={sub_txt!r}")
        check("done 态后统计刷新不再覆盖副标题（showDone 与 refreshStats 两个写者不打架）",
              race.get("afterDone", "") == "本轮完成1张·已全部过完", f"afterDone={race.get('afterDone')!r}")

        # —— TOC 跟随判据：换第三个页面（长文档）再跑一次
        toc, toc_errs = parse_eval(run_expr(base() + "/doc/ui-x/notes/%E7%9B%AE%E5%BD%95%E8%B7%9F%E9%9A%8F%E6%A0%B7%E6%9C%AC.md",
                                            build_toc_expr()))
        check("TOC 探针跑起来了（目录 ≥3 条且渲染生效）", not toc.get("err"),
              f"{toc.get('err')} / links={toc.get('links')} / CONSOLE_ERRORS: {toc_errs[:140]}")
        bad_steps = [st for st in toc.get("steps", []) if st.get("act") != st.get("want")]
        check("每个滚动位置高亮的都是判据算出的那一节（top≤96 的最后一个标题）",
              bool(toc.get("steps")) and not bad_steps, f"错位={bad_steps} 全部={toc.get('steps')}")
        check("滚动确实换了条目（不是永远高亮同一条）", int(toc.get("moved", 0)) >= 2,
              f"不同条目数={toc.get('moved')} steps={toc.get('steps')}")

        # —— 正文预处理（sanitizeFences / enhanceArticleDOM）：换第四个页面跑
        enh, enh_errs = parse_eval(run_expr(base() + "/doc/ui-x/notes/%E7%9B%AE%E5%BD%95%E8%B7%9F%E9%9A%8F%E6%A0%B7%E6%9C%AC.md",
                                            build_enh_expr()))
        check("两个预处理函数确实在 window 上（手册说没挂，实测挂了）",
              enh.get("globals", {}) == {"sanitizeFences": "function", "enhanceArticleDOM": "function"}
              and not enh.get("err"), f"{enh.get('globals')} err={enh.get('err')}")
        f = enh.get("f", {})
        check(f"sanitizeFences 对 {f.get('n')} 个样本（含 120 个随机串）均不抛",
              not f.get("threw"), f"{f.get('threw')}")
        check("sanitizeFences 不改行数、不增删非空白字符、且幂等",
              not f.get("bad"), f"{(f.get('bad') or [])[:4]} 共 {len(f.get('bad') or [])} 例")
        gold_bad = [g for g in f.get("golden", []) if not g.get("ok")]
        check("sanitizeFences 四条金样例逐字正确（顶格闭栏对齐 / 已对齐不动 / 顶格开栏不动 / 异字符不当闭栏）",
              len(f.get("golden", [])) == 4 and not gold_bad,
              f"不符={[(g['in'][:26], g['got'][:26]) for g in gold_bad]}")
        once, twice = enh.get("e", {}).get("once", {}), enh.get("e", {}).get("twice", {})
        want_e = {"cards": 2, "badgeM": 1, "tip": 1, "warn": 1, "kp": 1, "fu": 1,
                  "code": 1, "tbl": 1, "task": 1, "h1out": 1, "grouped": 1}
        wrong_e = {k: (once.get(k), v) for k, v in want_e.items() if once.get(k) != v}
        check("enhanceArticleDOM 每种标记各产出一个结构（2 卡 / 1 徽章 / 4 类引用 / 代码壳 / 表格壳 / 任务项）",
              not wrong_e, f"实际/期望 {wrong_e} 全量={once}")
        check("enhanceArticleDOM 幂等：跑两遍与跑一遍完全相同",
              once and once == twice, f"once={once} twice={twice}")
        check("h2 拿到稳定色相 --gh 与可定位 id（闪卡跳转原文的锚点）",
              bool(once.get("gh")) and bool(once.get("id")), f"gh={once.get('gh')} id={once.get('id')}")
        check("空壳 / 无 .a-body / 空 code 等畸形容器不抛",
              not enh.get("e", {}).get("weirdThrew"), f"{enh.get('e', {}).get('weirdThrew')}")

        mine = [split_console_errs(x)[0] for x in (console_errs, race_errs, toc_errs, enh_errs)]
        theirs = [split_console_errs(x)[1] for x in (console_errs, race_errs, toc_errs, enh_errs)]
        mine_txt = "\n".join(x for x in mine if x)
        check("三个页面均无本套该管的未捕获异常/警告", mine_txt == "", f"CONSOLE_ERRORS: {mine_txt[:300]}")
        for t in [x for x in theirs if x]:
            print(f"  NOTE 排除来自 static/archify/* 的报错（另一条线在改，不算本套）："
                  f"{_safe(t.splitlines()[0][:110])}")
        print(f"\n浏览器侧总耗时 {data.get('ms')} ms；样本 "
              f"{len(FIXTURES)} epub + {len(TXT_FIXTURES)} txt + {len(CHAPTER_TEXTS)} 切分文本 "
              f"+ {len(probes)} 个续读位置探针")
    finally:
        kill_instance(proc)
        shutil.rmtree(tmp, ignore_errors=True)
        # 这条不是装饰：本套是仓库里少数会"物理删整棵树"的测试，一旦被改成删 ROOT
        # 就是灾难（I4 白名单要求逐点判定）。断言删除目标确实在系统临时目录下。
        check("清理只删掉了系统临时目录下的临时根", not tmp.exists()
              and str(tmp).startswith(tempfile.gettempdir())
              and (ROOT / "content").is_dir(), f"tmp={tmp}")

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
