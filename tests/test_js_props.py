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
        PORT = free_port()
        QA.mkdir(parents=True, exist_ok=True)
        check("端口是现挑的且不是用户的 5001/5000/5031",
              PORT not in (5000, 5001, 5031), f"port={PORT}")
        proc = start_instance(tmp, PORT, log_path=QA / "instance.log")
        check("临时实例起来了", port_open(PORT))

        expr = build_expr()
        r = subprocess.run(["node", str(ROOT / "scripts" / "agent" / "evalcdp.mjs"),
                            base() + "/", "@" + str(expr)],
                           cwd=str(ROOT), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300,
                           env=dict(os.environ, KB_EVAL_WAIT_MS="6000", KB_EVAL_OUT_CHARS="20000"))
        out = r.stdout or ""
        blob = out.split("EVAL:", 1)[1].split("CONSOLE_ERRORS:", 1)[0].strip() if "EVAL:" in out else ""
        console_errs = out.split("CONSOLE_ERRORS:", 1)[1].strip() if "CONSOLE_ERRORS:" in out else "?"
        data = {}
        try:
            data = json.loads(json.loads(blob)) if blob else {}
        except Exception as e:                                # noqa: BLE001
            check("CDP 返回能解析", False, f"{e} / {blob[:200]} {r.stderr[-300:]}")
            return 1
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

        check("页面无未捕获异常/警告", console_errs in ("none", ""), f"CONSOLE_ERRORS: {console_errs[:300]}")
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
