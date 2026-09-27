# -*- coding: utf-8 -*-
"""批量查漏补缺回归（切片 4，2026-09-27）—— 先估算、后异步跑、预算帽是硬门。

运行：python tests/test_ai_batch.py

四条判据值得单独说明：
  · **估算零出站**：`/api/ai/batch/estimate` 要报"大概花多少钱"，而它自己一次网都不出 ——
    要问几篇是本地判据算出来的，不是猜的；
  · **长任务不挂在一次 fetch 上**：start 必须**立刻**返回（作业还在 running），
    真正的扫描在 daemon 线程里；这条是靠"start 的耗时"和"C3 线程里没有 app_context 就会红"两
    处一起锁的 —— 后者是这类改造最容易踩的坑：线程里没有 request context，
    任何 current_app.* 都会炸，作业会静默地"每篇都失败"；
  · **预算帽只许本地**：预估超过剩余额度时带 AI 的批量不开（429），
    而 ai=false 的纯本地批量照跑（它零调用零出站，没有"超支"这回事）；
  · **批量名单的口径与索引一致**：`_` 前缀目录、`.notes.md` 旁挂、非 .md 都不得入列。
"""
import json
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _ci  # noqa: E402
from test_ai_config import CALLS, start_provider  # noqa: E402
from test_ai_qa import rag_hit  # noqa: E402  向量命中的形状只写一份，两处共用

from app import ai_audit, ai_batch, ai_qa  # noqa: E402
from app.app import create_app  # noqa: E402

KEY = "sk-BATCHCANARY-Q9ZL"


def dirty(i):
    """每篇都踩「应引未引」（要问 AI）+ 空小节（本地判据）。"""
    return ('---\ntitle: "批量样本' + str(i) + '"\ncollected: 2024-01-05\n---\n\n'
            "# 批量样本" + str(i) + "\n\n## 定义\n\n## 细节\n\n"
            "正文里提到了 向量数据库 这个已有的词条，却没有链过去。\n")


# 控制组样本：一个全库已有的词条都不提 —— 判据若在这种篇上也亮红，那就是永远亮红的废铁。
CLEANDOC = ('---\ntitle: "干净样本"\nsource: baike\ncollected: 2026-09-01\n'
            'tags: [检索]\nstatus: stable\n---\n\n# 干净样本\n\n## 定义\n\n'
            "这一节把要说的话说完了。\n\n## 结尾\n\n这一句是完整的。\n")

# 简历正文里提一个全库已有的词条却不链过去 = 一条 needs_ai 候选。
# 有意为之：不出站闸门要拦的就是"这种确实想问 AI 的篇"。光有一篇没候选的简历，
# 把闸门拆掉也不会有任何断言变红（实测踩过，见台账 §6）。
CAREER = ('---\ntitle: "简历乙"\nsource: career\ncollected: 2026-09-01\n'
          'tags: [职业]\nstatus: stable\n---\n\n# 简历乙\n\n## 定义\n\n'
          '项目里用过 向量数据库。\n\n## 空节\n\n## 结尾\n\n收尾一句。\n')

TAXONOMY = {"domains": {"baike": {"label": "百科", "hue": 158},
                        "career": {"label": "职业", "hue": 42, "ai": False}}}

N_DIRTY = 6

passed = failed = 0
FAILS = []


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS {name}")
    else:
        failed += 1
        FAILS.append(name)
        _ci.failed(name)
        print(f"  FAIL {name} :: {str(extra)[:220]}")


def make_root(tmp):
    root = Path(tmp)
    c = root / "content"
    (c / "baike" / "sub").mkdir(parents=True)
    (c / "baike" / "term").mkdir(parents=True)
    (c / "baike" / "_trash").mkdir(parents=True)
    (c / "career").mkdir(parents=True)
    (c / "_meta").mkdir(parents=True)
    for i in range(N_DIRTY):
        (c / "baike" / "sub" / f"d{i}.md").write_text(dirty(i), encoding="utf-8")
    (c / "baike" / "sub" / "clean.md").write_text(CLEANDOC, encoding="utf-8")
    (c / "baike" / "term" / "向量数据库.md").write_text(
        '---\ntitle: "向量数据库"\nsource: baike\ncollected: 2026-09-01\ntags: [检索]\n'
        'status: stable\n---\n\n# 向量数据库\n\n## 定义\n\n按向量检索的库。\n\n## 结尾\n\n完了。\n',
        encoding="utf-8")
    (c / "career" / "B.md").write_text(CAREER, encoding="utf-8")
    # 三类"看着像语料但其实不该被扫"的东西：旁挂备注、_ 前缀目录、非 md
    (c / "baike" / "sub" / "d0.md.notes.md").write_text("# 备注\n\n别扫我。\n", encoding="utf-8")
    (c / "baike" / "_trash" / "old.md").write_text(dirty(99), encoding="utf-8")
    (c / "baike" / "sub" / "page.html").write_text("<h1>不是 md</h1>", encoding="utf-8")
    (c / "_meta" / "taxonomy.json").write_text(
        json.dumps(TAXONOMY, ensure_ascii=False), encoding="utf-8")
    return root


def client_for(root, rag_hits=None):
    app = create_app(root)
    app.config["_AI_USAGE"] = None
    if rag_hits is None:
        app.config["KB_HOOKS"]["get_rag"] = lambda: (None, None)
        app.config["KB_HOOKS"]["query_rag"] = lambda *a, **k: []
    else:
        # 假向量索引（形状照 app/rag.COLS，与 test_ai_qa 的 rag_hit 共用一份）
        app.config["KB_HOOKS"]["get_rag"] = lambda: (object(), object())
        app.config["KB_HOOKS"]["query_rag"] = lambda *a, **k: list(rag_hits)
        app.config["KB_HOOKS"]["rag_model_ready"] = lambda: True
    return app, app.test_client()


def wait_job(c, want_done=True, secs=25):
    """轮询到作业不在跑为止（轮询本身就是被测契约的一部分，不用 sleep 猜时长）。"""
    t0 = time.time()
    job = None
    while time.time() - t0 < secs:
        job = c.get("/api/ai/batch/status").get_json()["job"]
        if not job.get("running"):
            return job, time.time() - t0
        time.sleep(0.05)
    return job, time.time() - t0


def main() -> int:
    _ci.started("ai_batch")
    for k in ("KB_AI_API_KEY", "KB_AI_BASE_URL", "KB_AI_MODEL"):
        os.environ.pop(k, None)
    srv, base = start_provider()
    try:
        # ============================================== A. 估算与作业状态机（纯函数）
        print("\n[A] 估算与作业状态机")
        items = [{"path": f"baike/sub/d{i}.md", "bytes": 200, "count": 2, "need_ai": True}
                 for i in range(4)] + [{"path": "baike/sub/clean.md", "bytes": 200,
                                        "count": 0, "need_ai": False}]
        est = ai_batch.estimate(items, budget_left=10)
        check("A1 估算的篇数 / 要问的篇数 / 调用数分开计（批量每篇最多问一次）",
              (est["docs"], est["docs_needing_ai"], est["calls_expected"], est["findings"])
              == (5, 4, 4, 8), est)
        priced = ai_batch.estimate(items, budget_left=10, price_in_per_1k=2.0,
                                   price_out_per_1k=8.0)
        check("A2 花费按 (输入 token/1k × 单价 + 输出/1k × 单价) 算",
              abs(priced["cost_est"] - (priced["tokens_in_est"] / 1000 * 2.0
                                        + priced["tokens_out_est"] / 1000 * 8.0)) < 1e-6,
              priced)
        check("A3 没设预算帽（left=None）不算超支",
              ai_batch.estimate(items, budget_left=None)["over_budget"] is False)
        check("A4 额度为 0 而仍要问 → over_budget 为真",
              ai_batch.estimate(items, budget_left=0)["over_budget"] is True
              and ai_batch.estimate(items, budget_left=4)["over_budget"] is False)
        big = [{"path": f"p{i}.md", "bytes": 10, "count": 1, "need_ai": True}
               for i in range(ai_batch.MAX_DOCS + 5)]
        trunc = ai_batch.estimate(big, budget_left=9999)
        check("A5 超过 MAX_DOCS 时如实标 truncated，并报清这次真会跑几篇",
              trunc["truncated"] is True and trunc["will_scan"] == ai_batch.MAX_DOCS
              and trunc["docs"] == ai_batch.MAX_DOCS + 5, trunc)
        check("A6 token 估算取高不取低（中文 1 字 < 1 token 是常态，估低了会吓到账单）",
              est["tokens_in_est"] >= 4 * 200 and est["tokens_in_est"] > 0, est)
        check("A7 needs_ai 只认判据自己标的 needs_ai",
              ai_batch.needs_ai([{"kind": "empty_section"}]) is False
              and ai_batch.needs_ai([{"kind": "should_link", "needs_ai": True}]) is True)

        # BatchRunner 的三件事：一次一个、一篇坏了不炸整批、能停
        gate = threading.Event()
        job = ai_batch.BatchJob({"domain": "x"}, 2)

        def ok_per_doc(j, it):
            gate.wait(8)          # 卡在第一篇上，好让 A8/A9 判到"真的在跑"的状态
            if it.get("rel") == "b.md":
                raise AssertionError("停止之后不该再往下跑第二篇")
            return 1, False, ""

        r1 = ai_batch.BatchRunner()
        started = r1.start([{"rel": "a.md"}, {"rel": "b.md"}], ok_per_doc, {"domain": "x"})
        check("A8 running 语义：queued/running 都算在跑，done 才算空闲",
              started.snapshot()["running"] is True and job.snapshot()["running"] is True,
              started.snapshot())
        try:
            r1.start([{"path": "c.md"}], ok_per_doc, {"domain": "y"})
            busy = False
        except ai_batch.BatchBusy:
            busy = True
        check("A9 同一个 Runner 不允许并发两个作业（派生库只有一份）", busy)
        started.request_stop()
        gate.set()
        t0 = time.time()
        while started.snapshot()["running"] and time.time() - t0 < 8:
            time.sleep(0.02)
        check("A10 请求停止后作业以 stopped 收尾（跑完当前这篇才走）",
              started.snapshot()["state"] == "stopped", started.snapshot())

        r2 = ai_batch.BatchRunner()

        def bad_per_doc(j, it):
            if it["path"] == "bad.md":
                raise RuntimeError("线程里没有 app_context 这类错就是这么冒出来的")
            return 2, False, ""

        j2 = r2.start([{"path": "ok.md"}, {"path": "bad.md"}, {"path": "ok2.md"}],
                      bad_per_doc, {"paths": []})
        t0 = time.time()
        while j2.snapshot()["running"] and time.time() - t0 < 5:
            time.sleep(0.02)
        snap = j2.snapshot()
        check("A11 一篇抛异常不拖垮整批：其余照跑，坏的那篇报名字",
              snap["state"] == "done" and snap["done"] == 3 and snap["error_count"] == 1
              and "bad.md" in snap["errors"][0], snap)
        check("A12 条数按成功篇累计（坏的那篇算 0，不猜）",
              snap["findings"] == 4, snap)

        # ============================================== A2. 覆盖空白的纯函数判据
        print("\n[A2] 覆盖空白（纯函数）")
        known = ["向量数据库", "空白样本0"]
        refs = {"缺失术语": ["gap/sub/g0.md", "gap/sub/g1.md", "gap/sub/g2.md"],
                "向量数据库": ["gap/sub/g0.md"],
                "另一个缺口": ["gap/sub/g9.md"]}
        gaps = ai_audit.coverage_gaps(refs, known, "@domain:gap")
        check("GA1 只报\"全库没有那一篇\"的目标（有同名词条的一律不进待办）",
              [g["title"] for g in gaps].count("有引用没词条：向量数据库") == 0
              and len(gaps) == 2, [g["title"] for g in gaps])
        check("GA2 被引用越多的先排（三条以上算结构问题，一条算可选）",
              [g["title"] for g in gaps][0].endswith("缺失术语")
              and [g["severity"] for g in gaps] == ["medium", "low"],
              [(g["title"], g["severity"]) for g in gaps])
        check("GA3 证据写清\"几篇里写了这条链\"并列出出处（光有结论的不算待办）",
              gaps and gaps[0]["evidence"].startswith("3 篇里写了 [[缺失术语]]")
              and "gap/sub/g1.md" in gaps[0]["evidence"], gaps and gaps[0]["evidence"])
        check("GA4 id 只由目标决定：同一篇文档重扫不会换号，处置状态才留得住",
              ai_audit.coverage_gaps(refs, known, "@domain:gap")[0]["id"]
              == ai_audit.coverage_gaps(dict(refs), known, "@domain:gap")[0]["id"]
              and ai_audit.coverage_gaps(refs, known, "@domain:gap")[0]["id"]
              != ai_audit.coverage_gaps(refs, known, "@domain:other")[0]["id"],
              [g["id"] for g in gaps])
        check("GA5 同名判据大小写不敏感（Obsidian 的链接本来就不区分大小写）",
              ai_audit.coverage_gaps({"VectorDB": ["a.md"]}, ["vectordb"], "@domain:x") == [],
              ai_audit.coverage_gaps({"VectorDB": ["a.md"]}, ["vectordb"], "@domain:x"))
        check("GA6 wikilinks 只取目标、别名与标题号切掉（同一份口径不给两处各写一遍）",
              ai_audit.wikilinks("[[甲]] 与 [[乙|显示名]] 与 [[丙#节]]") == ["甲", "乙", "丙"],
              ai_audit.wikilinks("[[甲]] 与 [[乙|显示名]] 与 [[丙#节]]"))
        check("GA7 作用域键必须以 @domain: 开头，且真实相对路径永远不会撞上它",
              ai_audit.domain_scope("gap/").lower() == "@domain:gap"
              and not ai_audit.is_domain_scope("gap/sub/g0.md")
              and ai_audit.is_domain_scope("@domain:gap"), ai_audit.domain_scope("gap/"))

        # ---- 域全景复核的三件纯函数：上下文装配、提示词口径、只收窄不造行
        gc = ai_audit.gap_context("gap", ["复核样本0", "向量数据库"], gaps)
        check("GA8 复核上下文把本域标题清单包进语料数据块（它和正文一样是不可信内容）",
              ai_qa.BLOCK_BEGIN in gc["text"] and ai_qa.BLOCK_END in gc["text"]
              and "复核样本0" in gc["text"] and gc["chars"] > 0
              and "缺失术语" in gc["text"], gc["chars"])
        check("GA9 targets 只取本地候选名、最多 20 条（发出去的就是这一份，不给 AI 留发挥空间）",
              gc["targets"] == ["缺失术语", "另一个缺口"]
              and len(ai_audit.gap_context("gap", [], [
                  dict(gaps[0], target="术语%d" % i, title="t%d" % i) for i in range(30)
              ])["targets"]) == 20, gc["targets"])
        pr = ai_audit.ai_prompt("coverage_gap", "CTX", "缺失术语、另一个缺口")
        check("GA10 提示词就地把口径写死：原样照抄候选名、不许发明新主题",
              "原样照抄" in pr and "不要发明新主题" in pr
              and "缺失术语、另一个缺口" in pr and "CTX" in pr, pr[:120])
        wide = ai_audit.coverage_gaps(refs, known, "@domain:gap")
        ai_audit.narrow_gaps(wide, {"confidence": "high", "terms": [
            {"term": "缺失术语", "brief": "多篇都在讲它"}, {"term": "AI 发明的主题", "brief": "不存在"}]})
        check("GA11 narrow_gaps 只收窄不造行：答复里发明新主题时行数一条不多",
              len(wide) == 2 and not any("发明" in g["title"] for g in wide),
              [g["title"] for g in wide])
        check("GA12 挑中的行带原文理由，没挑中的行标的是"
              "「没把它列进」（缺席是从答复推的，不是 AI 明说）",
              wide[0]["ai_terms"] == ["缺失术语"] and wide[0]["ai_note"] == "多篇都在讲它"
              and wide[1]["ai_terms"] == [] and "没把它列进" in wide[1]["ai_note"]
              and {g["ai_confidence"] for g in wide} == {"high"},
              [(g["title"], g["ai_terms"], g["ai_note"]) for g in wide])
        check("GA13 答复为空（AI 没跑成）时 narrow_gaps 一个字都不改，本地清单原样留着",
              ai_audit.narrow_gaps(ai_audit.coverage_gaps(refs, known, "@domain:gap"), None)
              == gaps, None)

        # ============================================== B. 估算端点：一次网都不出
        print("\n[B] 估算端点")
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            app, c = client_for(root)
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/audit",
                                          "allow_local": True, "timeout_s": 10})
            CALLS.clear()
            r = c.post("/api/ai/batch/estimate", json={"scope": {"domain": "baike"}})
            j = r.get_json()
            e = j.get("estimate") or {}
            check("B1 domain 估算回 200 且篇数就是可见 md 的篇数（6 脏 + 1 干净 + 1 术语本体）",
                  r.status_code == 200 and e.get("docs") == N_DIRTY + 2, (r.status_code, e))
            check("B2 估算全程零出站（它要报花费，自己却一次网都不出）",
                  CALLS == {}, CALLS)
            check("B3 旁挂 .notes.md / _ 前缀目录 / 非 md 都不在名单里",
                  e.get("docs") == N_DIRTY + 2 and all("notes" not in (t.get("path") or "")
                                                       and "_trash" not in (t.get("path") or "")
                                                       for t in (j.get("top") or [])),
                  e)
            check("B4 top 列表按本地判据条数倒序",
                  [t["count"] for t in j.get("top") or []]
                  == sorted([t["count"] for t in j.get("top") or []], reverse=True), j.get("top"))
            r = c.post("/api/ai/batch/estimate", json={"scope": {"domain": "career"}})
            ec = r.get_json().get("estimate") or {}
            check("B5 不出站域：有篇数、有本地条数，但要问 AI 的次数恒 0",
                  ec.get("docs") == 1 and ec.get("calls_expected") == 0
                  and ec.get("docs_needing_ai") == 0, ec)
            check("B6 上面这趟照样零出站", CALLS.get("audit", 0) == 0, CALLS)
            r = c.post("/api/ai/batch/estimate", json={"scope": {}})
            check("B7 既不给 domain 也不给 paths → 400 且说清要什么",
                  r.status_code == 400 and ("domain" in (r.get_json() or {}).get("error", "")),
                  r.get_json())
            r = c.post("/api/ai/batch/estimate", json={"scope": {"domain": "baike",
                                                                "sub": "没有这个子域"}})
            check("B8 空范围 → 400（不是回一份全 0 的估算让人以为扫过了）",
                  r.status_code == 400, (r.status_code, r.get_json()))
            r = c.post("/api/ai/batch/estimate", json={"scope": {"paths": [
                "../../app/app.py", "baike/sub/d0.md", "baike/sub/page.html"]}})
            ep = r.get_json().get("estimate") or {}
            check("B9 paths 模式：坏路径被跳过而不拦整批，非 md 同样不进名单",
                  r.status_code == 200 and ep.get("docs") == 1, (r.status_code, r.get_json()))
            check("B10 花费估算随单价配置走（单价 0 时不许编出钱数）",
                  "cost_est" in ep and ep["cost_est"] >= 0, ep)

        # ============================================== C. 异步作业：立刻回、轮询到、真入库
        print("\n[C] 异步作业")
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            app, c = client_for(root)
            st0 = c.get("/api/ai/batch/status").get_json()
            check("C1 没有作业时 status 也回 200（前端不必先探一次「有没有在跑」）",
                  st0.get("ok") is True and st0["job"].get("state") in ("idle", "done"), st0)
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/audit",
                                          "allow_local": True, "timeout_s": 10})
            CALLS.clear()
            t0 = time.perf_counter()
            r = c.post("/api/ai/batch/start", json={"scope": {"domain": "baike"}})
            start_ms = int((time.perf_counter() - t0) * 1000)
            j = r.get_json()
            check("C2 start 立刻返回（作业还在跑，扫描绝不挂在这次 fetch 上）",
                  r.status_code == 200 and j.get("job", {}).get("running") is True
                  and start_ms < 4000, (start_ms, j.get("job")))
            check("C3 回值里带同一份估算（用户点确认时看到的数与开跑用的是一个口径）",
                  (j.get("estimate") or {}).get("docs") == N_DIRTY + 2, j.get("estimate"))
            job_end, waited = wait_job(c)
            check("C4 轮询到作业收尾（state 不再是 running）",
                  job_end and job_end.get("running") is False, job_end)
            check("C5 每一篇都有归属：done == total",
                  job_end.get("done") == job_end.get("total") == N_DIRTY + 2, job_end)
            check("C6 线程里没有 request context 的话，每篇都会失败 —— 这条就是那道口",
                  job_end.get("error_count") == 0, job_end.get("errors"))
            check("C7 批量按篇问：调用数 == 有「应引未引」候选的篇数（不是每篇两次，也不是每条一次）",
                  job_end.get("ai_calls") == N_DIRTY and CALLS.get("audit") == N_DIRTY,
                  (job_end.get("ai_calls"), CALLS))
            got = c.get("/api/ai/audit?path=baike/sub/d1.md").get_json()
            check("C8 批量跑完的建议真的进了派生库（打开那一篇就看得到）",
                  got.get("available") is True and len(got.get("proposals") or []) > 0, got)
            kinds1 = {p["kind"] for p in (got.get("proposals") or [])}
            check("C9 AI 的结论并进了那一篇的「应引未引」",
                  "should_link" in kinds1
                  and any(p.get("ai_terms") for p in (got.get("proposals") or [])
                          if p["kind"] == "should_link"), sorted(kinds1))
            clean_got = c.get("/api/ai/audit?path=baike/sub/clean.md").get_json()
            check("C10 干净文档批量扫完仍然是 0 条（控制组，判据不是永远亮红）",
                  clean_got.get("proposals") == [], clean_got)
            r = c.post("/api/ai/batch/start", json={"scope": {"domain": "baike"}})
            check("C11 上一个作业已收尾，可以再开一个（不是永久锁死）",
                  r.status_code == 200, r.get_json())
            r = c.post("/api/ai/batch/start", json={"scope": {"domain": "baike"}})
            check("C12 作业正跑着时再 start → 409 且说清已经在跑",
                  r.status_code == 409 and "批量" in (r.get_json() or {}).get("error", ""),
                  (r.status_code, r.get_json()))
            s = c.post("/api/ai/batch/stop").get_json()
            check("C13 stop 请求被接住", s.get("stopped") is True, s)
            ended, _ = wait_job(c)
            check("C14 停止后以 stopped 收尾，且已入库的结果不回滚",
                  ended.get("state") == "stopped" and ended.get("done") >= 1, ended)
            r2 = c.post("/api/ai/batch/start", json={"scope": {"domain": "baike"}})
            check("C15 停下来的作业不占坑，能重新开跑", r2.status_code == 200, r2.get_json())
            ended2, _ = wait_job(c)
            check("C16 重新跑完一遍后建议条数不翻倍（upsert + prune 是幂等的）",
                  ended2.get("state") == "done"
                  and len(c.get("/api/ai/audit?path=baike/sub/d1.md").get_json()
                          .get("proposals") or []) == len(got.get("proposals") or []),
                  ended2)
            c.put("/api/ai/config", json={"monthly_budget_calls": 300})

        # ============================================== D. 预算帽：超了就不许带 AI 开跑
        print("\n[D] 预算帽")
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            app, c = client_for(root)
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/audit",
                                          "allow_local": True, "timeout_s": 10,
                                          "monthly_budget_calls": 2})
            CALLS.clear()
            r = c.post("/api/ai/batch/start", json={"scope": {"domain": "baike"}})
            j = r.get_json()
            check("D1 预估要问 6 次而额度只剩 2 → 429 带 AI 的批量不开",
                  r.status_code == 429 and j.get("code") == "over_budget"
                  and "6" in (j.get("error") or ""), (r.status_code, j))
            check("D2 拒绝的响应里带回那份估算（要改预算帽就照着这个数改）",
                  (j.get("estimate") or {}).get("calls_expected") == N_DIRTY, j.get("estimate"))
            check("D3 被拒的这次真的没出站", CALLS.get("audit", 0) == 0, CALLS)
            r = c.post("/api/ai/batch/start", json={"scope": {"domain": "baike"},
                                                    "ai": False})
            check("D4 同一顶帽子下纯本地批量照跑（零调用零出站，没有超支这回事）",
                  r.status_code == 200, (r.status_code, r.get_json()))
            ended, _ = wait_job(c)
            check("D5 纯本地批量：一篇都没问 AI，本地建议照常入库",
                  ended.get("ai_calls") == 0 and CALLS.get("audit", 0) == 0
                  and ended.get("done") == N_DIRTY + 2, (ended, CALLS))
            check("D6 跑完的账本里确实是 0 次调用",
                  c.get("/api/ai/usage").get_json()["month"]["calls"] == 0,
                  c.get("/api/ai/usage").get_json()["month"])

        # ============================================== D2. 跑到一半撞帽：只降级不失败
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            app, c = client_for(root)
            # 帽子先不设（monthly_budget_calls=0 → left=None）：带 AI 的批量照常开跑。
            # provider 用 /auditslow（每次 0.35s），给"作业还在跑时改配置"留出确定窗口。
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/auditslow",
                                          "allow_local": True, "timeout_s": 20,
                                          "monthly_budget_calls": 0})
            CALLS.clear()
            r = c.post("/api/ai/batch/start", json={"scope": {"paths": [
                "baike/sub/d%d.md" % i for i in range(N_DIRTY)]}, "ai": True})
            check("D7 没设预算帽时带 AI 的批量照常开跑（left=None 不等于 0）",
                  r.status_code == 200, r.get_json())
            # 作业还在跑（6 篇 × 0.35s），此刻把帽子压到 2 ——
            # 等价于"另一个标签页把本月额度用光了"这种真实并发场景。
            c.put("/api/ai/config", json={"monthly_budget_calls": 2})
            ended, _ = wait_job(c)
            check("D8 中途撞帽：作业不失败，剩下的篇照常跑本地判据",
                  ended.get("state") == "done" and ended.get("done") == N_DIRTY, ended)
            check("D9 撞帽之后不再问 AI，并把原因留在快照里（用户看得见为什么少了几篇）",
                  ended.get("ai_calls", 99) <= 2
                  and "预算帽" in (ended.get("ai_stopped_reason") or ""), ended)
            check("D10 账本里的调用数确实封在帽子内", CALLS.get("audit", 0) <= 2, CALLS)
            check("D11 降级不改变本地结论：撞帽的篇照样有条目入库",
                  c.get("/api/ai/audit?path=baike/sub/d5.md").get_json()["proposals"],
                  c.get("/api/ai/audit?path=baike/sub/d5.md").get_json())

        # ============================================== E. 无 key 与不出站域
        print("\n[E] 无 key / 不出站域")
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            app, c = client_for(root)
            r = c.post("/api/ai/batch/start", json={"scope": {"domain": "baike"}})
            check("E1 没配 key 却要求带 AI → 400 not_configured（并提示可以只跑本地）",
                  r.status_code == 400 and r.get_json().get("code") == "not_configured",
                  (r.status_code, r.get_json()))
            r = c.post("/api/ai/batch/start", json={"scope": {"domain": "baike"}, "ai": False})
            check("E2 没配 key 的纯本地批量照跑", r.status_code == 200, r.get_json())
            ended, _ = wait_job(c)
            check("E3 跑完之后派生库里确实有建议（无 key 也有一条查得出来的路）",
                  ended.get("findings", 0) > 0
                  and c.get("/api/ai/audit?path=baike/sub/d0.md").get_json()["proposals"],
                  ended)
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            app, c = client_for(root)
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/audit",
                                          "allow_local": True, "timeout_s": 10,
                                          "monthly_budget_calls": 300})
            CALLS.clear()
            r = c.post("/api/ai/batch/start", json={"scope": {"paths": [
                "baike/sub/d0.md", "career/B.md"]}, "ai": True})
            ended, _ = wait_job(c)
            check("E4 混合 paths：不出站域那一篇照样被扫，但整批只问了可出站的那一篇",
                  ended.get("done") == 2 and ended.get("ai_calls") == 1, ended)
            check("E5 而可出站那一篇的建议里带着 AI 的结论",
                  any(p.get("ai_terms") for p in c.get(
                      "/api/ai/audit?path=baike/sub/d0.md").get_json()["proposals"]),
                  c.get("/api/ai/audit?path=baike/sub/d0.md").get_json()["proposals"])
            check("E6 career 那一篇的「空小节」由本地判据查出（不需要 AI）",
                  any(p["kind"] == "empty_section" for p in c.get(
                      "/api/ai/audit?path=career/B.md").get_json()["proposals"]),
                  c.get("/api/ai/audit?path=career/B.md").get_json())

        # ============================================== F. 大范围：抽样估算 + 上限拦钱包
        print("\n[F] 抽样估算")
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            big = root / "content" / "big" / "sub"
            big.mkdir(parents=True)
            # 210 篇：每第 10 篇是脏的（21 篇要问 AI）。抽样步长 6 命中 7 篇 ——
            # 放大出来的 42 比真实的 21 还乐观，所以**拦钱包绝不能看放大值，要看上限**。
            for i in range(210):
                (big / f"b{i:03d}.md").write_text(dirty(i) if i % 10 == 0 else CLEANDOC,
                                                  encoding="utf-8")
            app, c = client_for(root)
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/audit",
                                          "allow_local": True, "timeout_s": 10,
                                          "monthly_budget_calls": 300})
            CALLS.clear()
            t0 = time.perf_counter()
            r = c.post("/api/ai/batch/estimate", json={"scope": {"domain": "big"}})
            ms = int((time.perf_counter() - t0) * 1000)
            f1 = (r.get_json() or {}).get("estimate") or {}
            check("F1 大范围估算仍然很快回（本地判据本身可能是长任务，估算不许把用户挂住）",
                  r.status_code == 200 and f1.get("sampled") is True and ms < 8000,
                  (ms, f1.get("sample")))
            check("F2 篇数报的是整个范围，实扫篇数与步长如实标出",
                  f1.get("docs") == 210 and f1.get("sample", {}).get("measured") == 35,
                  f1.get("sample"))
            check("F3 放大值确实是「抽到的比例 × 总篇数」（报的是估算，不是精扫结果）",
                  f1.get("calls_expected") == 42 and f1.get("calls_upper_bound") == 210, f1)
            c.put("/api/ai/config", json={"monthly_budget_calls":
                                          c.get("/api/ai/usage").get_json()["month"]["calls"]
                                          + 50})
            r = c.post("/api/ai/batch/estimate", json={"scope": {"domain": "big"}})
            f4 = (r.get_json() or {}).get("estimate") or {}
            check("F4 剩 50 次额度：放大值 42 看着够用，但上限 210 超帽 —— 判定看上限",
                  f4.get("budget_left") == 50 and f4.get("calls_expected") == 42
                  and f4.get("over_budget") is True, f4)
            r = c.post("/api/ai/batch/start", json={"scope": {"domain": "big"}, "ai": True})
            check("F5 于是带 AI 的大批量被拒（错误里报的是上限，不是那个乐观的 42）",
                  r.status_code == 429 and "210" in (r.get_json() or {}).get("error", ""),
                  (r.status_code, r.get_json()))
            check("F6 拒绝对全程零出站", CALLS == {}, CALLS)
            r2 = c.post("/api/ai/batch/estimate", json={"scope": {"domain": "big"}})
            check("F7 抽样步长固定 → 同一个范围连估两次是同一份数（不是每刷新一次换个数）",
                  (r2.get_json() or {}).get("estimate") == f4,
                  (r2.get_json() or {}).get("estimate"))
            c.put("/api/ai/config", json={"monthly_budget_calls": 0})
            r = c.post("/api/ai/batch/start", json={"scope": {"domain": "big"}, "ai": False})
            ended, _ = wait_job(c, secs=60)
            check("F8 纯本地批量不受帽限制，210 篇全跑完（每篇的建议都进得了库）",
                  r.status_code == 200 and ended.get("done") == 210
                  and ended.get("findings", 0) > 0, ended)
            check("F9 抽查最后一片：批量确实扫到了范围末尾，不是只跑了开头",
                  c.get("/api/ai/audit?path=big/sub/b200.md").get_json()["proposals"],
                  c.get("/api/ai/audit?path=big/sub/b200.md").get_json())

        # ============================================== G. 批量收尾算出的域待办（端点面）
        print("\n[G] 域级覆盖空白（端点面）")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            croot = root / "content"
            (croot / "gap" / "sub").mkdir(parents=True)
            (croot / "gap" / "term").mkdir(parents=True)
            (croot / "_meta").mkdir(parents=True)
            (croot / "gap" / "term" / "向量数据库.md").write_text(
                '---\ntitle: "向量数据库"\n---\n\n# 向量数据库\n\n## 定义\n\n按向量检索。\n',
                encoding="utf-8")
            for i in range(4):
                (croot / "gap" / "sub" / ("g%d.md" % i)).write_text(
                    '---\ntitle: "空白样本%d"\ncollected: 2024-01-05\n---\n\n'
                    "# 空白样本%d\n\n## 定义\n\n这里写了 [[缺失术语]]，"
                    "正文里还提到 向量数据库 却没给它建链。\n"
                    % (i, i), encoding="utf-8")
            (croot / "gap" / "sub" / "h0.md").write_text(
                '---\ntitle: "只有好链"\ncollected: 2024-01-05\n---\n\n# 只有好链\n\n'
                "## 定义\n\n只写了 [[向量数据库]]。\n", encoding="utf-8")
            (croot / "_meta" / "taxonomy.json").write_text(
                json.dumps({"domains": {"gap": {"label": "空白测试域", "hue": 158}}},
                           ensure_ascii=False), encoding="utf-8")
            app, c = client_for(root)
            CALLS.clear()
            r = c.post("/api/ai/batch/start", json={"scope": {"domain": "gap"}, "ai": False})
            ended, _ = wait_job(c)
            key = "@domain:gap"
            got = c.get("/api/ai/audit?path=" + key).get_json()
            ps = got.get("proposals") or []
            check("G1 批量跑完顺手算出域级待办，且它挂在作用域键而不是某一篇上",
                  r.status_code == 200 and ended.get("state") == "done"
                  and len(ps) == 1 and ps[0]["kind"] == "coverage_gap"
                  and "缺失术语" in ps[0]["title"], str(got)[:220])
            check("G2 出处与篇数如实写进证据",
                  ps and ps[0]["evidence"].startswith("4 篇里写了") and "gap/sub/g2.md"
                  in ps[0]["evidence"], ps and ps[0]["evidence"])
            check("G3 同一条空白不会重复出现在每一篇文档自己的建议列表里",
                  all(p["kind"] != "coverage_gap" for p in c.get(
                      "/api/ai/audit?path=gap/sub/g0.md").get_json()["proposals"]),
                  c.get("/api/ai/audit?path=gap/sub/g0.md").get_json())
            check("G4 算空白全程零出站（它是引用集合减标题集合，本地就算得出来）",
                  CALLS == {}, CALLS)
            many = sorted((x["kind"], x["id"]) for x in c.get(
                "/api/ai/audit?path=gap/sub/g0.md").get_json()["proposals"])
            one = sorted((x["kind"], x["id"]) for x in c.post(
                "/api/ai/audit", json={"path": "gap/sub/g0.md"}).get_json()["proposals"])
            check("G4b 同一篇由「批量查」与「单篇查」给出的建议一模一样（判据只有一份实现）",
                  bool(one) and one == many, {"many": many, "one": one})
            check("G4c 批量扫过的篇里确实带着「应引未引」这条（不给标题集合就会悄悄少一类）",
                  "should_link" in [k for k, _ in many], [k for k, _ in many])
            check("G4d 批量也带着「失效双链」这条（同一份索引死链清单，不是只跑了半套判据）",
                  "dead_wikilink" in [k for k, _ in many], [k for k, _ in many])
            pid = ps[0]["id"] if ps else ""
            rr = c.post("/api/ai/audit/status", json={"path": key, "id": pid,
                                                      "status": "dismissed"})
            check("G5 域待办走同一套处置状态机（忽略被记住）",
                  rr.status_code == 200 and rr.get_json().get("status") == "dismissed",
                  rr.get_json())
            c.post("/api/ai/batch/start", json={"scope": {"domain": "gap"}, "ai": False})
            wait_job(c)
            again = c.get("/api/ai/audit?path=" + key).get_json()["proposals"]
            check("G6 重算不冲掉点过的忽略（id 只由目标决定）",
                  [p for p in again if p["id"] == pid and p.get("status") == "dismissed"],
                  str(again)[:200])
            for i in range(4):
                (croot / "gap" / "sub" / ("g%d.md" % i)).unlink()
            c.post("/api/ai/batch/start", json={"scope": {"domain": "gap"}, "ai": False})
            wait_job(c)
            check("G7 引用删光之后域待办自动消失（prune 也管作用域键）",
                  c.get("/api/ai/audit?path=" + key).get_json()["proposals"] == [],
                  c.get("/api/ai/audit?path=" + key).get_json())
            check("G8 非法作用域键读与写一律 400（不许拿它探任意键）",
                  c.get("/api/ai/audit?path=@domain:nope").status_code == 400
                  and c.get("/api/ai/audit?path=@domain:a/b").status_code == 400
                  and c.post("/api/ai/audit/status",
                             json={"path": "@domain:../x", "id": "f" * 12,
                                   "status": "dismissed"}).status_code == 400, None)
            left = sorted(p.relative_to(croot).as_posix() for p in croot.rglob("*.md"))
            check("G9 整趟只往派生库里写：语料仍是那两篇（删掉的 4 篇是本测试自己删的）",
                  left == ["gap/sub/h0.md", "gap/term/向量数据库.md"], left)


        # ============================================== H. 覆盖空白的 AI 复核（切片 5）
        print("\n[H] 覆盖空白的 AI 复核")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            croot = root / "content"
            (croot / "gap" / "sub").mkdir(parents=True)
            (croot / "gap" / "term").mkdir(parents=True)
            (croot / "_meta").mkdir(parents=True)
            (croot / "gap" / "term" / "向量数据库.md").write_text(
                '---\ntitle: "向量数据库"\n---\n\n# 向量数据库\n\n## 定义\n\n按向量检索。\n',
                encoding="utf-8")
            # 两个空白：缺失术语（3 篇提到，假 provider 认为值得补）、另一个缺口（1 篇，不补）
            for i in range(3):
                (croot / "gap" / "sub" / ("h%d.md" % i)).write_text(
                    '---\ntitle: "复核样本%d"\ncollected: 2024-01-05\n---\n\n'
                    "# 复核样本%d\n\n## 定义\n\n这里写了 [[缺失术语]]。\n" % (i, i),
                    encoding="utf-8")
            (croot / "gap" / "sub" / "solo.md").write_text(
                '---\ntitle: "单独一提"\ncollected: 2024-01-05\n---\n\n# 单独一提\n\n'
                "## 定义\n\n顺带写了 [[另一个缺口]]。\n", encoding="utf-8")
            # 这一篇链接的是**已有词条**：它必须被 `known` 挡在空白清单外。
            # 没有这一篇，"复核时到底有没有把全库标题集合传进来"在端点层是判不出来的
            # （其余引用目标本来就没有词条，known 传不传都一样 —— 第一轮变异就这么活了下来）。
            (croot / "gap" / "sub" / "linked.md").write_text(
                '---\ntitle: "链到已有词条"\ncollected: 2024-01-05\n---\n\n'
                "# 链到已有词条\n\n## 定义\n\n这里写了 [[向量数据库]]，"
                "而它全库已经有那一篇了。\n", encoding="utf-8")
            (croot / "_meta" / "taxonomy.json").write_text(
                json.dumps({"domains": {"gap": {"label": "复核域", "hue": 158},
                                        "career": {"label": "职业", "hue": 42, "ai": False}}},
                           ensure_ascii=False), encoding="utf-8")

            def key_at(c, seg):
                c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/" + seg,
                                              "allow_local": True, "timeout_s": 10,
                                              "monthly_budget_calls": 300})

            app, c = client_for(root)
            key_at(c, "auditgap")
            CALLS.clear()
            r = c.post("/api/ai/batch/start", json={"scope": {"domain": "gap"}, "ai": False})
            ended, _ = wait_job(c)
            gr = ended.get("gap_review") or {}
            rows = c.get("/api/ai/audit?path=@domain:gap").get_json()["proposals"]
            check("H1 ai=false 时复核不跑，但原因写在快照里（不是静默少跑一步）",
                  r.status_code == 200 and gr.get("ran") is False
                  and "没让 AI 复核" in (gr.get("reason") or ""), gr)
            check("H2 本地清单照旧两条都在，且都没带 AI 结论",
                  len(rows) == 2 and all(not p.get("ai_terms") for p in rows),
                  [(p["title"], p.get("ai_terms")) for p in rows])
            check("H3 复核这一路真的零出站", CALLS == {}, CALLS)

            CALLS.clear()
            r = c.post("/api/ai/batch/start", json={"scope": {"domain": "gap"}, "ai": True})
            ended, _ = wait_job(c)
            gr = ended.get("gap_review") or {}
            rows = c.get("/api/ai/audit?path=@domain:gap").get_json()["proposals"]
            by = {p["title"]: p for p in rows}
            picked = [p for p in rows if p.get("ai_terms")]
            check("H4 复核跑过一次（域全景一次调用，不逐条各问）",
                  r.status_code == 200 and gr.get("ran") is True
                  and gr.get("picked") == 1 and CALLS.get("audit") == 1,
                  {"gr": gr, "CALLS": CALLS})
            check("H5 复核只在本地候选里挑：挑中的那条带上理由",
                  len(picked) == 1 and "缺失术语" in picked[0]["title"]
                  and picked[0].get("ai_note"), [(p["title"], p.get("ai_terms")) for p in rows])
            check("H6 没被挑中的那条如实标成缺席判断（措辞点明是从答复里推的，不是 AI 明说）",
                  len(by) == 2 and not by["有引用没词条：另一个缺口"]["ai_terms"]
                  and "没把它列进" in (by["有引用没词条：另一个缺口"].get("ai_note") or ""),
                  by.get("有引用没词条：另一个缺口"))
            check("H7 复核不造条目：跑完还是那两条，条数一条没多",
                  len(rows) == 2, [p["title"] for p in rows])
            check("H8 复核过一遍之后正文仍然一字节未变",
                  sorted(p.relative_to(croot).as_posix() for p in croot.rglob("*.md"))
                  == ["gap/sub/h0.md", "gap/sub/h1.md", "gap/sub/h2.md", "gap/sub/linked.md",
                      "gap/sub/solo.md", "gap/term/向量数据库.md"],
                  sorted(p.relative_to(croot).as_posix() for p in croot.rglob("*.md")))
            # 帽满：复核那一步也要让位给帽，而且要说清为什么少跑
            c.put("/api/ai/config", json={"monthly_budget_calls":
                                          c.get("/api/ai/usage").get_json()["month"]["calls"]})
            r = c.post("/api/ai/batch/start", json={"scope": {"domain": "gap"}, "ai": True})
            ended, _ = wait_job(c)
            gr = ended.get("gap_review") or {}
            check("H9 帽满时复核不跑并写明原因（清单仍在，只是没标哪些值得补）",
                  r.status_code == 200 and gr.get("ran") is False
                  and "预算帽" in (gr.get("reason") or "")
                  and len(c.get("/api/ai/audit?path=@domain:gap").get_json()["proposals"]) == 2,
                  gr)

        with tempfile.TemporaryDirectory() as td:
            # 不出站域：清单照出，复核不跑
            root = Path(td)
            croot = root / "content"
            (croot / "career").mkdir(parents=True)
            (croot / "_meta").mkdir(parents=True)
            (croot / "career" / "c0.md").write_text(
                '---\ntitle: "简历丙"\ncollected: 2024-01-05\n---\n\n# 简历丙\n\n'
                "## 定义\n\n写了 [[职业空白项]]。\n", encoding="utf-8")
            (croot / "_meta" / "taxonomy.json").write_text(
                json.dumps({"domains": {"career": {"label": "职业", "hue": 42}}},
                           ensure_ascii=False), encoding="utf-8")
            app, c = client_for(root)
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/auditgap",
                                          "allow_local": True, "timeout_s": 10,
                                          "monthly_budget_calls": 300})
            CALLS.clear()
            r = c.post("/api/ai/batch/start", json={"scope": {"domain": "career"}, "ai": True})
            ended, _ = wait_job(c)
            gr = ended.get("gap_review") or {}
            rows = c.get("/api/ai/audit?path=@domain:career").get_json()["proposals"]
            check("H10 不出站域的空白清单照出（本地算得出来，不该因为不能问 AI 就没结果）",
                  r.status_code == 200 and len(rows) == 1 and "职业空白项" in rows[0]["title"],
                  rows)
            check("H11 但全景复核不跑，原因点名是闸门不是故障",
                  gr.get("ran") is False and "不出站" in (gr.get("reason") or ""), gr)
            check("H12 整趟零出站：不出站域连候选名都没发出去", CALLS == {}, CALLS)

        # ============================================== I. 批量·与已有语料矛盾（切片 5b）
        print("\n[I] 批量·与已有语料矛盾")
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            app, c = client_for(root)
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/auditpair",
                                          "allow_local": True, "timeout_s": 20,
                                          "monthly_budget_calls": 0})
            CALLS.clear()
            e_off = c.post("/api/ai/batch/estimate",
                           json={"scope": {"domain": "baike"}}).get_json()["estimate"]
            e_on = c.post("/api/ai/batch/estimate", json={"scope": {"domain": "baike"},
                                                          "conflict": True}).get_json()["estimate"]
            check("I1 勾上矛盾核对就把每篇上限提到两次：上限与 token 一起翻倍（拦钱包看的是上限）",
                  e_off["per_doc_calls"] == 1 and e_on["per_doc_calls"] == 2
                  and e_on["calls_upper_bound"] == 2 * e_off["calls_upper_bound"]
                  and e_on["tokens_out_est"] == 2 * e_off["tokens_out_est"]
                  and e_on["docs"] == e_off["docs"],
                  {"off": e_off["calls_upper_bound"], "on": e_on["calls_upper_bound"]})
            check("I2 这一步估算照常零出站（多算一次上限也只是本地数字）",
                  CALLS == {}, CALLS)
            # 帽子卡在"1×上限"与"2×上限"之间：不勾能开、勾了必须被拦 ——
            # 这锁的是 start 那一路真的把开关换算进了帽门，而不只是估算条上写着好看。
            used = c.get("/api/ai/usage").get_json()["month"]["calls"]
            cap = e_off["calls_upper_bound"] + 1
            c.put("/api/ai/config", json={"monthly_budget_calls": used + cap})
            # 先问被拦的那一路：429 不会起作业，所以紧接着还能起第二个
            r_yes = c.post("/api/ai/batch/start", json={"scope": {"domain": "baike"},
                                                        "ai": True, "conflict": True})
            r_no = c.post("/api/ai/batch/start", json={"scope": {"domain": "baike"}, "ai": True})
            wait_job(c)
            check("I2b 帽门按 2× 上限拦：同一顶帽子下不勾能开、勾了就被 429 拦住",
                  r_no.status_code == 200 and r_yes.status_code == 429
                  and "2" in (r_yes.get_json().get("error") or ""),
                  {"no": r_no.status_code, "yes": r_yes.status_code,
                   "cap": cap, "err": (r_yes.get_json() or {}).get("error")})
            c.put("/api/ai/config", json={"monthly_budget_calls": 0})
            CALLS.clear()      # 上一趟（I2b 的整域批量）的出站数不能混进这一条对账
            r = c.post("/api/ai/batch/start", json={"scope": {"paths": ["baike/sub/d0.md"]},
                                                    "ai": True, "conflict": True})
            ended, _ = wait_job(c)
            rows = c.get("/api/ai/audit?path=baike/sub/d0.md").get_json()["proposals"]
            conf = [p for p in rows if p["kind"] == "conflict"]
            check("I3 批量按篇配出对照行并落派生库：最多三对，判为矛盾的那对带编号回到行上",
                  r.status_code == 200 and 1 <= len(conf) <= 3
                  and any(p.get("ai_terms") == ["与《向量数据库》"] for p in conf),
                  [(p["title"], p.get("ai_terms")) for p in conf])
            check("I3b 就叫这个名字的那篇排在最前（它是「在讲同一件事」的最强信号）",
                  conf and "向量数据库" in conf[0]["title"], conf[:1])
            check("I4 一篇问两次就记两次：进度条的「问 AI N 次」与真出站数同口径（按篇记会少数一半）",
                  ended.get("ai_calls") == CALLS.get("audit") and ended.get("ai_calls") >= 2,
                  {"job": ended.get("ai_calls"), "srv": CALLS})
            check("I5 配对结论里带着两边各说了什么，不是只有一句「有矛盾」",
                  conf and "本篇" in conf[0]["evidence"] and conf[0].get("ai_note"), conf[:1])
            before = (root / "content" / "baike" / "sub" / "d0.md").read_text(encoding="utf-8")
            check("I6 跑完正文一字节未变（不变量 9 ②）", before == dirty(0), len(before))

        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            app, c = client_for(root)
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/auditpair",
                                          "allow_local": True, "timeout_s": 20,
                                          "monthly_budget_calls": 0})
            CALLS.clear()
            c.post("/api/ai/batch/start", json={"scope": {"paths": ["baike/sub/d0.md"]},
                                                "ai": True})
            ended, _ = wait_job(c)
            rows = c.get("/api/ai/audit?path=baike/sub/d0.md").get_json()["proposals"]
            check("I7 不勾矛盾核对：一篇只问一次，也不建配对行（这条路口不由默认值替用户开）",
                  ended.get("ai_calls") == 1 and not any(p["kind"] == "conflict" for p in rows),
                  {"ai_calls": ended.get("ai_calls"), "kinds": [p["kind"] for p in rows]})

        with tempfile.TemporaryDirectory() as td:
            # 帽满有两种形状：开跑前就被拦（D 组已锁），和**跑到一半另一个标签页把额度用光**。
            # 后者才轮到矛盾这一步表现：它必须让位，而行照旧入库（否则用户看到的是凭空少了几条）。
            root = make_root(td)
            app, c = client_for(root)
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/auditslow",
                                          "allow_local": True, "timeout_s": 20,
                                          "monthly_budget_calls": 0})
            CALLS.clear()
            r = c.post("/api/ai/batch/start", json={"scope": {"paths": [
                "baike/sub/d%d.md" % i for i in range(3)]}, "ai": True, "conflict": True})
            c.put("/api/ai/config", json={"monthly_budget_calls": 2})
            ended, _ = wait_job(c)
            rows = c.get("/api/ai/audit?path=baike/sub/d2.md").get_json()["proposals"]
            conf = [p for p in rows if p["kind"] == "conflict"]
            check("I8 中途撞帽：之后的篇不再问 AI，但配对行照旧入库（只是没结论）",
                  r.status_code == 200 and ended.get("state") == "done"
                  and CALLS.get("audit", 99) <= 2 and conf
                  and all(not p.get("ai_terms") for p in conf),
                  {"CALLS": CALLS, "conf": len(conf), "state": ended.get("state")})
            check("I9 帽满降级要说清（否则用户看到没结论的配对行会以为是坏了）",
                  "预算帽" in (ended.get("ai_stopped_reason") or ""),
                  ended.get("ai_stopped_reason"))

        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            app, c = client_for(root)
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/auditpair",
                                          "allow_local": True, "timeout_s": 20})
            CALLS.clear()
            r = c.post("/api/ai/batch/start", json={"scope": {"domain": "career"},
                                                    "ai": True, "conflict": True})
            ended, _ = wait_job(c)
            rows = c.get("/api/ai/audit?path=career/B.md").get_json()["proposals"]
            check("I10 不出站域勾了矛盾核对也只出本地配对行：整趟零出站（配对方在放行域也一样不发）",
                  r.status_code == 200 and CALLS == {}
                  and any(p["kind"] == "conflict" for p in rows),
                  {"CALLS": CALLS, "kinds": [p["kind"] for p in rows]})

        with tempfile.TemporaryDirectory() as td:
            # 批量按篇检索必须复用同一条索引连接：每篇 open_db 一次会撞上
            # watcher 的写锁（切片 4 实测 37 篇卡 40s，台账 §6 第 71 行）。
            # 判据不能靠"跑得慢不慢"（时机不可靠），要就地打桩看它拿到的连接是不是同一个。
            from app import routes_ai
            root = make_root(td)
            app, c = client_for(root)
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/auditpair",
                                          "allow_local": True, "timeout_s": 20,
                                          "monthly_budget_calls": 0})
            real = routes_ai.fts_search
            seen_cons = []

            def spy(indexes, q, limit=50, con=None):
                seen_cons.append((con is not None, id(con)))
                return real(indexes, q, limit=limit, con=con)

            routes_ai.fts_search = spy
            try:
                c.post("/api/ai/batch/start", json={"scope": {"domain": "baike"},
                                                    "ai": False, "conflict": True})
                ended, _ = wait_job(c)
                uniq = {x[1] for x in seen_cons}
                check("I11 打桩真的在链上（否则下面两条都是空气）", bool(seen_cons), seen_cons[:2])
                check("I12 批量按篇检索复用的是同一条连接，且没有一篇是自己开库",
                      all(x[0] for x in seen_cons) and len(uniq) == 1
                      and ended.get("state") == "done", seen_cons[:4])
                check("I13 每一篇都查到了（不是只查第一篇就断）",
                      len(seen_cons) >= ended.get("done", 0)
                      and ended.get("done") == N_DIRTY + 2, {"calls": len(seen_cons),
                                                             "done": ended.get("done")})
            finally:
                routes_ai.fts_search = real
            check("I14 桩收干净了（还原后真实检索仍能用）",
                  routes_ai.fts_search is real
                  and bool(real(Path(root / "indexes"), "向量数据库", limit=3)), None)

        # ============================================ I2. 第二路候选在批量线程里也走得通
        print("\n[I2] 批量·第二路（向量索引）")
        with tempfile.TemporaryDirectory() as td:
            root = make_root(td)
            # 这篇不提任何已有词条 → FTS 那一路空手，只有第二路配得出对
            (root / "content" / "baike" / "sub" / "onlyrag.md").write_text(
                '---\ntitle: 只有语义相近\nsource: baike\ncollected: 2024-01-05\n'
                'tags: [检索]\nstatus: stable\n---\n\n# 只有语义相近\n\n## 原理\n\n'
                "把语句压成坐标存进索引，查询时按距离取回最像的几条，这就是它的全部说法。\n",
                encoding="utf-8")
            hits = [rag_hit("把语句压成坐标存进索引，查询时按距离取回最像的几条。",
                            "baike/sub/onlyrag.md", 0.95, title="只有语义相近"),
                    rag_hit("把文本变成坐标、按距离找相似内容的存储。",
                            "baike/term/向量数据库.md", 0.72, title="向量数据库")]
            app, c = client_for(root, rag_hits=hits)
            c.put("/api/ai/config", json={"api_key": KEY, "base_url": base + "/auditpair",
                                          "allow_local": True, "timeout_s": 20,
                                          "monthly_budget_calls": 0})
            CALLS.clear()
            r = c.post("/api/ai/batch/start",
                       json={"scope": {"paths": ["baike/sub/onlyrag.md"]},
                             "ai": True, "conflict": True})
            ended, _ = wait_job(c)
            rows = c.get("/api/ai/audit?path=baike/sub/onlyrag.md").get_json()["proposals"]
            conf = [p for p in rows if p["kind"] == "conflict"]
            check("I15 worker 线程里第二路照跑：配出对、零报错、结论落库",
                  r.status_code == 200 and ended.get("error_count") == 0
                  and len(conf) == 1 and bool(conf[0].get("ai_terms")),
                  {"err": ended.get("errors"), "conf": [(p["title"], p.get("ai_terms"))
                                                        for p in conf]})
            check("I16 第二路不多问 AI：一篇还是最多两次（它只换找候选的办法，不加判断种类）",
                  ended.get("ai_calls") == CALLS.get("audit") and ended.get("ai_calls") <= 2,
                  {"job": ended.get("ai_calls"), "srv": CALLS})
            check("I17 线索来源写进行上（批量与单篇同一份证据口径，不各写一套）",
                  conf and "配对线索" in conf[0]["evidence"]
                  and "语义相近" in conf[0]["evidence"], conf[:1])

        print(f"\n{passed} passed, {failed} failed")
        if FAILS:
            print("FAILED CASES:")
            for f in FAILS:
                print("  -", f)
        return 1 if failed else 0
    finally:
        srv.shutdown()


if __name__ == "__main__":
    sys.exit(_ci.guarded(main, "ai_batch"))
