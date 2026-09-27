# -*- coding: utf-8 -*-
"""AI 配置层回归（切片 1，2026-09-27）—— 填写 / 测试 / 保存 / 用量 四条路全都锁死。

运行：python tests/test_ai_config.py

为什么单开一套而不是塞进 test_e2e_smoke：那套打的是「端点会不会 500、非法入参会不会 4xx」，
本套打的是**语义**：key 的三层优先级、保存时"空串=保持 / null=清除"这种容易写反的约定、
以及 /api/ai/test 的失败分类。分类错了用户就照着假线索去查网络问题，代价比 500 大。

三条硬约束（改这个文件前必读）：
  · **绝不联网**：出站点一律打本机 127.0.0.1 上的假 provider（make_server 起在现挑端口）。
    也因此每例都要显式 allow_local=True —— 顺手证明了"本机地址不放行就存不进去"。
  · **零真实语料**：KB_ROOT 指向 tempfile，content/ 里只有合成的两篇 md；不碰 content/小说/。
  · **明文 key 永不出现在响应里**：每条断言都用 store 里那个 canary 串去反查响应文本。
"""
import json
import os
import sys
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _ci  # noqa: E402
from _tmpapp import free_port  # noqa: E402

from flask import Flask, Response, request  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from app import ai_config  # noqa: E402
from app.app import create_app  # noqa: E402

CANARY = "sk-CANARY-0123456789abcdef"
PASSKEY = "sk-PASS-abcdefghijklmnop"

passed = failed = 0
FAILS = []
CAPTURED = {}
# 每个前缀被调用了几次 —— 切片 2 用它证明「缓存命中不重复计费」与「只重试一次」
CALLS = {}


def counted(seg):
    """按路径首段计数，并记下这次**真的发出去了**什么（headers + body）。

    不靠回显到响应里：那会把 Authorization 原文带回我们自己的 HTTP 响应，
    反而污染「响应里没有 key」那条断言。
    """
    CALLS[seg] = CALLS.get(seg, 0) + 1
    CAPTURED.clear()
    CAPTURED.update({"auth": request.headers.get("Authorization", ""),
                     "body": request.get_json(silent=True) or {}, "path": seg})


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS {name}")
    else:
        failed += 1
        FAILS.append(name)
        print(f"  FAIL {name} :: {str(extra)[:220]}")


# ---------------------------------------------------------------- 假 provider
# 路径前缀决定行为：/ok /auth /nf /slow /garbage /emptychoices /boom /capture /qa /badjson；
# /ok 与 /qa 要求 Bearer 里含 "REAL"，用来证明「没配好 key 时压根不发请求」。
def build_provider():
    app = Flask("fake-provider")

    def reply(body, status=200):
        return Response(json.dumps(body), status=status, mimetype="application/json")

    @app.route("/ok/chat/completions", methods=["POST"])
    def ok():
        auth = request.headers.get("Authorization", "")
        if "REAL" not in auth:
            return reply({"error": {"message": "bad key"}}, 401)
        return reply({"choices": [{"message": {"content": "pong 在线"}}],
                      "usage": {"prompt_tokens": 7, "completion_tokens": 3,
                                "total_tokens": 10}})

    @app.route("/auth/chat/completions", methods=["POST"])
    def auth_fail():
        return reply({"error": {"message": "invalid api key"}}, 401)

    @app.route("/nf/chat/completions", methods=["POST"])
    def nf():
        return reply({"error": {"message": "model not found"}}, 404)

    @app.route("/slow/chat/completions", methods=["POST"])
    def slow():
        import time
        time.sleep(3)
        return reply({"choices": [{"message": {"content": "too late"}}]})

    @app.route("/garbage/chat/completions", methods=["POST"])
    def garbage():
        return Response("<html>not json</html>", status=200, mimetype="text/html")

    @app.route("/emptychoices/chat/completions", methods=["POST"])
    def emptychoices():
        return reply({"choices": []})

    @app.route("/boom/chat/completions", methods=["POST"])
    def boom():
        return reply({"error": {"message": "server boom"}}, 500)

    @app.route("/capture/chat/completions", methods=["POST"])
    def capture():
        # 把「到底发出去了什么」记进模块级字典，供 C 组直接断言 ——
        # 不能靠回显到响应里：那等于让测试自己造一条 key 上路的假象，且会把 Authorization
        # 原文带回我们的 HTTP 响应，反而污染「响应里没有 key」这条断言。
        counted("capture")
        return reply({"choices": [{"message": {"content": "captured ok"}}],
                      "usage": {"prompt_tokens": 11, "completion_tokens": 5,
                                "total_tokens": 16}})

    # ---- 切片 2 用：按约定 JSON schema 回答 / 故意不按 schema 回答（用来试重试上限） ----
    @app.route("/qa/chat/completions", methods=["POST"])
    def qa():
        counted("qa")
        ans = {"answer": "贝尔不等式：定域隐变量理论对关联函数给出的上界，量子力学可违反。",
               "confidence": "high",
               "terms": [{"term": "定域隐变量", "brief": "测量结果只由本地隐变量决定"}],
               "sources": ["baike/sub/A.md"]}
        return reply({"choices": [{"message": {"content": json.dumps(ans, ensure_ascii=False)}}],
                      "usage": {"prompt_tokens": 120, "completion_tokens": 40,
                                "total_tokens": 160}})

    @app.route("/audit/chat/completions", methods=["POST"])
    def audit():
        """切片 3 用：把候选词原样判成 terms（便于断言"AI 的结论并回了哪条建议"）。"""
        counted("audit")
        ans = {"answer": "两个候选里只有一个是真引用。", "confidence": "medium",
               "terms": [{"term": "向量数据库", "brief": "正文里它在讲存储选型"}],
               "sources": []}
        return reply({"choices": [{"message": {"content": json.dumps(ans, ensure_ascii=False)}}],
                      "usage": {"prompt_tokens": 300, "completion_tokens": 30,
                                "total_tokens": 330}})

    @app.route("/auditgap/chat/completions", methods=["POST"])
    def audit_gap():
        """切片 5 用：复核覆盖空白的答复 —— 只认列出的候选名，绝不发明新主题。"""
        counted("audit")
        ans = {"answer": "三个候选里只有一个值得单独立篇。", "confidence": "medium",
               "terms": [{"term": "缺失术语", "brief": "多篇都在讲它，值得一篇独立词条"}],
               "sources": []}
        return reply({"choices": [{"message": {"content": json.dumps(ans, ensure_ascii=False)}}],
                      "usage": {"prompt_tokens": 200, "completion_tokens": 25,
                                "total_tokens": 225}})

    @app.route("/auditpair/chat/completions", methods=["POST"])
    def audit_pair():
        """切片 5b 用：判「与已有语料矛盾」的答复 —— 只认列出的配对编号，绝不新增配对。"""
        counted("audit")
        ans = {"answer": "两处对同一件事的说法确实对立。", "confidence": "high",
               "terms": [{"term": "与《向量数据库》", "brief": "本篇说按词建表，那篇说按向量存"}],
               "sources": []}
        return reply({"choices": [{"message": {"content": json.dumps(ans, ensure_ascii=False)}}],
                      "usage": {"prompt_tokens": 260, "completion_tokens": 30,
                                "total_tokens": 290}})

    @app.route("/auditslow/chat/completions", methods=["POST"])
    def audit_slow():
        """切片 4 用：慢一点的 audit 答复，给"作业跑中途改配置"留出确定性窗口。

        测试需要"作业还在跑、帽子已经被压低"这一格 —— 不靠 sleep 猜，
        而是让每次调用本身就慢（0.35s × 篇数远大于断言侧的一次 PUT 往返）。
        """
        import time
        time.sleep(0.35)
        return audit()

    @app.route("/badjson/chat/completions", methods=["POST"])
    def badjson():
        counted("badjson")
        return reply({"choices": [{"message": {"content": "这是一段散文，不是约定的 JSON。"}}],
                      "usage": {"total_tokens": 9}})

    return app


def start_provider():
    port = free_port()
    srv = make_server("127.0.0.1", port, build_provider(), threaded=True)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv, f"http://127.0.0.1:{port}"


# ---------------------------------------------------------------- 迷你语料
DOC = ('---\ntitle: "合成甲"\nsource: "baike"\nstatus: "imported"\n---\n\n'
       '# 合成甲\n\n正文 zzaimark。\n')

TAXONOMY = {
    "domains": {
        "baike": {"label": "百科", "hue": 158},
        "小说": {"label": "网文", "search": False, "ai": False},
    }
}


def make_root(tmp):
    root = Path(tmp) / "kb"
    content = root / "content"
    (content / "baike" / "sub").mkdir(parents=True)
    (content / "_meta").mkdir(parents=True)
    (content / "career").mkdir(parents=True)
    (content / "_inbox").mkdir(parents=True)
    (content / "baike" / "sub" / "A.md").write_text(DOC, encoding="utf-8")
    (content / "career" / "简历.md").write_text(DOC.replace("合成甲", "职业乙"), encoding="utf-8")
    (content / "_meta" / "taxonomy.json").write_text(
        json.dumps(TAXONOMY, ensure_ascii=False), encoding="utf-8")
    return root


def client_for(root):
    """返回 (app, test_client)。账本（indexes/ai.db）走"每次操作现开连接"的写法，
    所以没有遗留句柄会把临时根锁住 —— Windows 上第一版用长句柄，实测 tempfile
    清理直接 PermissionError（教训同时钉在 app/ai_usage.py 的模块注释里）。"""
    app = create_app(root)
    app.config["_AI_USAGE"] = None  # 每实例自己的账本，别串到上个用例的临时库
    # 把 RAG 钩子摘掉：本套只验 AI 出站层，绝不允许顺手去加载 94MB 嵌入模型
    #（真机上模型在位时 get_rag() 会把一路请求拖成几十秒，而结论与模型无关）。
    app.config["KB_HOOKS"]["get_rag"] = None
    app.config["KB_HOOKS"]["query_rag"] = None
    return app, app.test_client()


def leaked(text, root):
    return str(root) in text


def main() -> int:
    _ci.started("ai_config")
    srv, base = start_provider()
    try:
        # ============================================== A. 纯函数层：脱敏 / 优先级 / 校验
        print("\n[A] ai_config 纯函数")
        check("A1 mask_key 只露尾 4 位", ai_config.mask_key(CANARY) == "******cdef",
              ai_config.mask_key(CANARY))
        check("A2 mask_key 短 key 全打点", ai_config.mask_key("abc") == "***")
        check("A3 mask_key 空串还是空串", ai_config.mask_key("") == "")

        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(tmp)
            for k in ("KB_AI_API_KEY", "KB_AI_BASE_URL", "KB_AI_MODEL"):
                os.environ.pop(k, None)
            check("A4 无文件无 env = 全缺省",
                  ai_config.effective(root)["values"]["model"] == "mimo-v2.5")
            check("A5 缺省时来源标 default",
                  ai_config.effective(root)["sources"]["model"] == "default")

            ai_config.save_config(root, {"api_key": CANARY, "base_url": base + "/ok",
                                         "allow_local": True})
            onfile = json.loads(ai_config.config_path(root).read_text(encoding="utf-8"))
            check("A6 保存落盘在仓库根单个 JSON", onfile.get("api_key") == CANARY,
                  list(onfile))
            check("A7 保存后来源标 file",
                  ai_config.effective(root)["sources"]["api_key"] == "file")

            os.environ["KB_AI_API_KEY"] = PASSKEY
            eff = ai_config.effective(root)
            check("A8 env 压过文件（优先级）", eff["values"]["api_key"] == PASSKEY)
            check("A9 来源如实标 env", eff["sources"]["api_key"] == "env")
            pub = ai_config.public_config(root)
            check("A10 公开视图不含明文 key", CANARY not in json.dumps(pub)
                  and PASSKEY not in json.dumps(pub), pub)
            del os.environ["KB_AI_API_KEY"]

            # 保存语义：空串保持、null 清除
            r1 = ai_config.save_config(root, {"model": "mimo-x", "api_key": ""})
            check("A11 api_key 传空串 = 保持原值",
                  json.loads(ai_config.config_path(root).read_text(encoding="utf-8")).get("api_key") == CANARY)
            check("A12 同一次保存里其他字段照常生效", r1["model"] == "mimo-x")
            ai_config.save_config(root, {"api_key": None})
            check("A13 api_key 传 null = 清除",
                  "api_key" not in json.loads(ai_config.config_path(root).read_text(encoding="utf-8")))
            check("A14 清除后 key_present=False",
                  ai_config.public_config(root)["key_present"] is False)

            # 展示字段不许回灌进文件
            ai_config.save_config(root, {"key_masked": "******cdef", "sources": {"a": 1},
                                         "model": "mimo-y"})
            saved = json.loads(ai_config.config_path(root).read_text(encoding="utf-8"))
            check("A15 白名单外的展示字段不写盘",
                  "key_masked" not in saved and "sources" not in saved, list(saved))

            # URL 校验矩阵
            bad = [("file://", "file:///etc/passwd"), ("空格", "http://a b.com"),
                   ("无协议", "api.xiaomimimo.com/v1"), ("内网", "http://192.168.1.9/v1"),
                   ("空串", ""), ("回环未放行", "http://127.0.0.1:9/v1")]
            for label, u in bad:
                try:
                    ai_config.validate_base_url(u, allow_local=False)
                    check(f"A16 拒绝 {label}", False, "竟然放行")
                except ai_config.ConfigError:
                    check(f"A16 拒绝 {label}", True)
            check("A17 本机地址在显式放行后通过",
                  ai_config.validate_base_url("http://127.0.0.1:9/v1", allow_local=True)
                  == "http://127.0.0.1:9/v1")
            check("A18 尾斜杠被规范化",
                  ai_config.validate_base_url("https://api.xiaomimimo.com/v1/")
                  == "https://api.xiaomimimo.com/v1")

            # 域级出站黑名单（不变量 9 ①）
            blocked = ai_config.egress_blocked_domains(root / "content")
            check("A19 JSON 里 ai:false 的域进黑名单", "小说" in blocked, blocked)
            check("A20 career/interview 是代码下界，JSON 没写也拦",
                  {"career", "interview"} <= blocked, blocked)
            check("A21 普通域放行", ai_config.domain_allows_egress(root / "content", "baike"))
            check("A22 空域名按不允许处理",
                  ai_config.domain_allows_egress(root / "content", "") is False)
            # 分层各钉一条：store 只搬 JSON，ai_config 才并下界（两层都并 = 谁也测不出来）
            from app import store as _store
            raw_hidden = _store.load_taxonomy(root / "content")["ai_hidden"]
            check("A23 store.ai_hidden 只反映 JSON（不含代码下界）",
                  raw_hidden == {"小说"}, raw_hidden)
            (root / "content" / "_meta" / "taxonomy.json").unlink()
            blocked2 = ai_config.egress_blocked_domains(root / "content")
            check("A24 taxonomy.json 没了也照样拦求职两域",
                  {"career", "interview"} <= blocked2, blocked2)
            check("A25 分类学缺失时普通域仍放行（不误伤整库）",
                  ai_config.domain_allows_egress(root / "content", "baike"))

        # ============================================== B. 端点层：配置 / 测试 / 用量
        print("\n[B] HTTP 端点")
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(tmp)
            for k in ("KB_AI_API_KEY", "KB_AI_BASE_URL", "KB_AI_MODEL"):
                os.environ.pop(k, None)
            app, c = client_for(root)

            g = c.get("/api/ai/config")
            check("B1 GET /api/ai/config 200", g.status_code == 200)
            check("B2 响应里没有 key 字段", "api_key" not in g.get_json(),
                  list(g.get_json()))
            check("B3 未配置时 key_present=False", g.get_json()["key_present"] is False)

            b = c.put("/api/ai/config", data="not json", content_type="text/plain")
            check("B4 PUT 非 JSON → 400", b.status_code == 400, b.status_code)
            b = c.put("/api/ai/config", json={"base_url": "file:///etc/passwd"})
            check("B5 PUT 非法 base_url → 400", b.status_code == 400, b.get_json())
            check("B6 400 响应不泄露绝对路径", not leaked(b.get_data(as_text=True), root))
            b = c.put("/api/ai/config", json={"base_url": base + "/ok", "allow_local": True})
            check("B7 PUT 合法配置 → 200", b.status_code == 200, b.get_json())
            check("B8 保存响应仍不含明文 key",
                  CANARY not in b.get_data(as_text=True))

            # 没 key 时 test 端点必须 503 且**不发起任何请求**
            t = c.post("/api/ai/test")
            check("B9 无 key 时 POST /api/ai/test → 503 not_configured",
                  t.status_code == 503 and t.get_json().get("code") == "not_configured",
                  t.get_json())

            r = c.put("/api/ai/config", json={"api_key": CANARY, "base_url": base + "/auth",
                                             "allow_local": True})
            check("B10 换 base_url 后仍 200", r.status_code == 200, r.get_json())
            t = c.post("/api/ai/test")
            check("B11 401 → 分类 auth", t.status_code == 502
                  and t.get_json().get("code") == "auth", t.get_json())

            c.put("/api/ai/config", json={"base_url": base + "/nf", "allow_local": True})
            t = c.post("/api/ai/test")
            check("B12 404 → 分类 model_404", t.get_json().get("code") == "model_404",
                  t.get_json())

            # DNS 解析失败 = unreachable。不要用"连一个没人听的端口"来造不可达：
            # 实测本机对 127.0.0.1:1 是**静默丢包**（2s 后 timeout 而不是 refused），
            # 拿它当不可达样本会得到一个假分类。
            c.put("/api/ai/config", json={"base_url": "http://kb-ai-no-such-host.invalid/v1",
                                         "allow_local": True, "timeout_s": 5})
            t = c.post("/api/ai/test")
            check("B13 域名解析不了 → 分类 unreachable",
                  t.get_json().get("code") == "unreachable", t.get_json())

            c.put("/api/ai/config", json={"base_url": base + "/slow", "allow_local": True,
                                          "timeout_s": 1})
            t = c.post("/api/ai/test")
            check("B14 超时 → 分类 timeout", t.get_json().get("code") == "timeout",
                  t.get_json())

            c.put("/api/ai/config", json={"base_url": base + "/garbage", "allow_local": True,
                                          "timeout_s": 10})
            t = c.post("/api/ai/test")
            check("B15 回包不是 JSON → 分类报错（不是当成功）",
                  t.status_code == 502 and t.get_json().get("code") in ("unreachable", "http_error"),
                  t.get_json())

            c.put("/api/ai/config", json={"base_url": base + "/boom", "allow_local": True})
            t = c.post("/api/ai/test")
            check("B16 服务端 500 → 分类 http_error", t.get_json().get("code") == "http_error",
                  t.get_json())

            # 成功路径：key 里带 REAL 才放行
            c.put("/api/ai/config", json={"api_key": "sk-REAL-K7QF", "base_url": base + "/ok",
                                         "allow_local": True, "timeout_s": 10})
            t = c.post("/api/ai/test")
            check("B17 配对了 test → ok:true 且带延迟证据",
                  t.status_code == 200 and t.get_json().get("ok") is True, t.get_json())
            check("B18 成功响应回显 key 来源而非 key",
                  t.get_json().get("key_source") == "file"
                  and "K7QF" not in t.get_data(as_text=True), t.get_json())

            u = c.get("/api/ai/usage")
            uj = u.get_json()
            check("B19 GET /api/ai/usage 200", u.status_code == 200)
            check("B20 账本记下了上面这串 test",
                  uj.get("available") and uj["month"]["calls"] >= 1, uj)
            check("B21 失败调用也入账（不是只记成功）", uj["month"]["failed"] >= 5,
                  uj["month"])
            check("B22 单价未配置时如实标 price_configured=false",
                  uj["cost"]["price_configured"] is False, uj.get("cost"))
            # canary 的尾标必须是**字母**：上一版用 "…-9527"，结果用量响应里的
            # latency_ms 读数（DNS 失败那次实测 9527ms）撞出一次假泄漏红灯。
            check("B23 用量响应里没有 key", "K7QF" not in u.get_data(as_text=True),
                  u.get_data(as_text=True)[:400])
            check("B24 预算态给出 used/budget",
                  uj["budget"]["used_month"] == uj["month"]["calls"]
                  and uj["budget"]["budget"] > 0, uj.get("budget"))

            # 成功调用要有 token 落账
            ok_calls_before = uj["month"]["calls"]
            c.post("/api/ai/test")
            uj2 = c.get("/api/ai/usage").get_json()
            check("B25 再 ping 一次调用数 +1", uj2["month"]["calls"] == ok_calls_before + 1,
                  uj2["month"])
            check("B26 成功那次的 total_tokens 记进账本",
                  uj2["month"]["tokens"] >= 10, uj2["month"])

            # /api/ask 预算帽：把 budget 压到已用次数以下
            used = c.get("/api/ai/usage").get_json()["month"]["calls"]
            c.put("/api/ai/config", json={"monthly_budget_calls": used})
            a = c.post("/api/ask", json={"q": "量子"})
            check("B27 超预算帽 /api/ask → 429 budget_exceeded",
                  a.status_code == 429 and a.get_json().get("code") == "budget_exceeded",
                  a.get_json())
            check("B28 预算帽不影响只读的 usage/config",
                  c.get("/api/ai/usage").status_code == 200)
            c.put("/api/ai/config", json={"monthly_budget_calls": 300})

            # DELETE：清文件而不是清 env（env 优先级仍在，UI 要如实）
            d = c.delete("/api/ai/config")
            check("B29 DELETE /api/ai/config 移除文件",
                  d.status_code == 200 and d.get_json()["removed"] is True)
            check("B30 删除后回到缺省 base_url",
                  c.get("/api/ai/config").get_json()["base_url"]
                  == ai_config.DEFAULTS["base_url"])

            # env 注入时保存文件不该"看起来生效其实没生效"
            os.environ["KB_AI_MODEL"] = "env-model-zz"
            c.put("/api/ai/config", json={"model": "file-model-zz"})
            pj = c.get("/api/ai/config").get_json()
            check("B31 env 在位时生效值仍是 env 的", pj["model"] == "env-model-zz", pj)
            check("B32 且来源如实标 env（防「存了没生效」）",
                  pj["sources"]["model"] == "env", pj["sources"])
            del os.environ["KB_AI_MODEL"]

            # 「填完先测、测通再存」的动线：test 允许带未保存的表单值，且绝不落盘
            c.put("/api/ai/config", json={"api_key": "sk-REAL-K7QF", "base_url": base + "/ok",
                                         "allow_local": True, "timeout_s": 10})
            t = c.post("/api/ai/test", json={"base_url": base + "/auth"})
            check("B33 测试可用未保存的表单值（不必先存）",
                  t.status_code == 502 and t.get_json().get("code") == "auth", t.get_json())
            check("B34 表单试跑不写文件",
                  "/auth" not in ai_config.config_path(root).read_text(encoding="utf-8"))
            t = c.post("/api/ai/test", json={"base_url": "file:///etc/passwd"})
            check("B35 表单态也过同一道 URL 校验 → 400 bad_config",
                  t.status_code == 400 and t.get_json().get("code") == "bad_config",
                  t.get_json())
            t = c.post("/api/ai/test", json={"api_key": ""})
            check("B36 表单密钥留空 = 沿用已存 key（不会误清）",
                  t.status_code == 200, t.get_json())
            t = c.post("/api/ai/test", json={"base_url": "http://127.0.0.1:8001/v1",
                                            "allow_local": False})
            check("B37 表单里指向本机但未勾选放行 → 400（试跑不放宽下界）",
                  t.status_code == 400 and t.get_json().get("code") == "bad_config",
                  t.get_json())

        # ============================================== C. 出站内容（直接看服务端收到了什么）
        print("\n[C] 出站内容")
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(tmp)
            for k in ("KB_AI_API_KEY", "KB_AI_BASE_URL", "KB_AI_MODEL"):
                os.environ.pop(k, None)
            app, c = client_for(root)
            c.put("/api/ai/config", json={"api_key": "sk-REAL-K7QF",
                                         "base_url": base + "/capture",
                                         "allow_local": True, "timeout_s": 10})
            CAPTURED.clear()
            t = c.post("/api/ai/test")
            check("C1 test 成功", t.status_code == 200, t.get_json())
            check("C2 test 请求带 max_tokens 上限（防长回包烧额度）",
                  CAPTURED["body"].get("max_tokens") == 8, CAPTURED["body"])
            check("C3 ping 消息就是两个字，不带语料",
                  CAPTURED["body"]["messages"][-1]["content"] == "ping", CAPTURED["body"])
            check("C4 key 只走 Authorization 头",
                  CAPTURED["auth"] == "Bearer sk-REAL-K7QF")
            check("C5 请求体里不含 key", "K7QF" not in json.dumps(CAPTURED["body"]))
            check("C6 model 取自配置", CAPTURED["body"].get("model") == "mimo-v2.5",
                  CAPTURED["body"].get("model"))

            CAPTURED.clear()
            a = c.post("/api/ask", json={"q": "什么是贝尔不等式"})
            check("C7 /api/ask 走通（假 provider）", a.status_code == 200 and a.get_json()["ok"],
                  a.get_json())
            sent = json.dumps(CAPTURED["body"], ensure_ascii=False)
            check("C8 ask 把问题发出去了", "什么是贝尔不等式" in sent, sent[:200])
            check("C9 ask 不带 max_tokens 截断（答案要完整）",
                  "max_tokens" not in CAPTURED["body"], CAPTURED["body"])
            check("C10 RAG 不可用时如实标注无语料，不编上下文",
                  "未检索到相关语料" in sent, sent[:300])
            check("C11 绝对路径不出现在出站请求体",
                  str(root) not in sent, sent[:300])
            check("C12 ask 的答复带 usage（前端可显示本次 tokens）",
                  isinstance(a.get_json().get("usage"), dict), a.get_json())

        print(f"\n{passed} passed, {failed} failed")
        if FAILS:
            print("FAILED CASES:")
            for f in FAILS:
                print("  -", f)
        return 1 if failed else 0
    finally:
        srv.shutdown()


if __name__ == "__main__":
    sys.exit(_ci.guarded(main, "ai_config"))
