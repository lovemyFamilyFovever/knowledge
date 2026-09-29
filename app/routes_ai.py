# -*- coding: utf-8 -*-
"""AI 出站层：OpenAI 兼容 chat 客户端 + 选词问 AI + 配置/测试/用量端点。

配置的唯一入口是 app/ai_config.py（env > .ai-config.json > 缺省），本模块只消费不回显明文 key。
只依赖标准库 urllib —— 与 AGENTS「任意 Python 可启动」兼容。

端点（轮次 53 起只剩这些 —— 查漏 / 批量 / 问吧 三块按用户要求整体移除）：
  GET/PUT /api/ai/config   读（脱敏）/ 写（校验后落 gitignored JSON）
  DELETE /api/ai/config    清除本机配置文件
  POST /api/ai/test        1-token 级连通性 ping，失败分类见 _classify_error()
  GET /api/ai/usage        今日/本月调用数、tokens、估算花费、预算余额
  POST /api/ai/explain     选词问 AI：只发选中的那几个字，只回一句解释

key 未配置时 explain 返回 not_configured(503)，前端如实指路「设置 → AI 页签」。
"""
import json
import threading
import time
import urllib.error
import urllib.request

from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import HTTPException

from app import ai_config, ai_qa
from app.ai_config import ConfigError
from app.ai_usage import AiUsageStore

ai_bp = Blueprint("ai", __name__)

# 失败分类（前端按 code 出文案，后端按 code 记账）
E_NOT_CONFIGURED = "not_configured"
E_AUTH = "auth"
E_MODEL_404 = "model_404"
E_TIMEOUT = "timeout"
E_UNREACHABLE = "unreachable"
E_HTTP = "http_error"

_LOCK = threading.Lock()


def _root():
    return current_app.config["ROOT"]


def _cfg() -> dict:
    """生效配置（含明文 key，仅本模块内部使用，严禁进响应/日志）。"""
    return ai_config.effective(_root())["values"]


def ai_available() -> bool:
    return bool(_cfg()["api_key"])


def _store() -> AiUsageStore | None:
    """indexes/ai.db 的账本句柄（派生缓存，建不起就返回 None 让调用方降级为不记账）。"""
    st = current_app.config.get("_AI_USAGE")
    if st is not None:
        return st
    with _LOCK:
        st = current_app.config.get("_AI_USAGE")
        if st is None:
            try:
                st = AiUsageStore(current_app.config["INDEXES"])
            except Exception:
                st = False
            current_app.config["_AI_USAGE"] = st
    return st if st is not False else None


def _record(kind, **kw):
    st = _store()
    if st is None:
        return
    try:
        st.record(kind, **kw)
    except Exception:
        pass  # 记账失败绝不能反噬主流程（账本可事后重建）


def _classify_error(e, http_status: int = 0) -> str:
    """把异常/状态码归到固定分类；未知一律 http_error/unreachable，不给"看起来成功了"的余地。"""
    if isinstance(e, urllib.error.HTTPError):
        code = e.code
    elif http_status:
        code = http_status
    else:
        code = 0
    if code in (401, 403):
        return E_AUTH
    if code == 404:
        return E_MODEL_404
    if code:
        return E_HTTP
    if isinstance(e, (TimeoutError,)) or "timed out" in str(e).lower():
        return E_TIMEOUT
    return E_UNREACHABLE


def _chat(messages: list[dict], timeout: int = 60, max_tokens: int | None = None,
          kind: str = "ask", cfg: dict | None = None) -> tuple[str, dict]:
    """一次出站 chat，返回 (content, usage)。失败抛 RuntimeError("ai:<code>:<detail>")。

    cfg 可传入「表单态」配置（/api/ai/test 要在不落盘的前提下试跑），缺省用生效配置。
    """
    c = cfg or _cfg()
    key = c["api_key"]
    if not key:
        raise RuntimeError(f"ai:{E_NOT_CONFIGURED}:未配置 API key")
    try:
        base = ai_config.validate_base_url(c["base_url"], bool(c["allow_local"]))
    except ConfigError as e:
        raise RuntimeError(f"ai:{E_UNREACHABLE}:{e}") from None

    payload = {"model": c["model"], "messages": messages, "temperature": 0.3}
    if max_tokens:
        payload["max_tokens"] = max_tokens
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base + "/chat/completions", data=body, method="POST",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:200]
        except Exception:
            pass
        code = _classify_error(e)
        _record(kind, model=c["model"], ok=False, error=f"{code}:{e.code}",
                latency_ms=int((time.perf_counter() - t0) * 1000))
        raise RuntimeError(f"ai:{code}:{detail}") from None
    except Exception as e:  # URLError / 超时 / DNS / JSON 解析失败
        code = _classify_error(e)
        _record(kind, model=c["model"], ok=False, error=f"{code}:{type(e).__name__}",
                latency_ms=int((time.perf_counter() - t0) * 1000))
        raise RuntimeError(f"ai:{code}:{e}") from None
    latency = int((time.perf_counter() - t0) * 1000)
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
    if not isinstance(content, str):
        content = str(content)
    _record(kind, model=c["model"], ok=True, usage=usage, latency_ms=latency)
    return content.strip(), usage


SYSTEM_PROMPT = (
    "你是「知库」的个人知识库助手。仅依据提供的语料片段回答问题；"
    "语料不足以回答时明确说明。回答使用简体中文，简洁、结构化，"
    "并在结尾列出引用的文档路径（[来源] 前缀）。"
)


def _budget_state() -> dict:
    c = _cfg()
    st = _store()
    used = st.summary()["month_usage"]["calls"] if st else 0
    budget = int(c["monthly_budget_calls"] or 0)
    return {"used_month": used, "budget": budget,
            "left": (budget - used) if budget > 0 else None,
            "exceeded": bool(budget > 0 and used >= budget)}


@ai_bp.get("/api/ai/config")
def api_ai_config_get():
    """脱敏配置视图 —— 永不返回明文 key。"""
    return jsonify(ai_config.public_config(_root()))


@ai_bp.put("/api/ai/config")
def api_ai_config_put():
    data = request.get_json(force=True, silent=True)
    if not isinstance(data, dict):
        return jsonify({"ok": False, "error": "请求体必须是 JSON 对象"}), 400
    try:
        pub = ai_config.save_config(_root(), data)
    except ConfigError as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    pub["message"] = "已保存到 " + ai_config.CONFIG_FILENAME + "（本机文件，不入库）"
    return jsonify(pub)


@ai_bp.delete("/api/ai/config")
def api_ai_config_delete():
    removed = ai_config.clear_config(_root())
    return jsonify({"ok": True, "removed": removed,
                    "config": ai_config.public_config(_root())})


@ai_bp.post("/api/ai/test")
def api_ai_test():
    """连通性 ping：一条极短消息 + max_tokens 上限，如实回分类结果与延迟。

    请求体可选带**未保存的表单值**（base_url / model / timeout_s / allow_local / api_key），
    这样「填完先测、测通再存」的动线成立；不落盘、不改配置。api_key 留空 = 用已存的 key。
    """
    body = request.get_json(force=True, silent=True) or {}
    eff = ai_config.effective(_root())
    c = dict(eff["values"])
    key_from = eff["sources"]["api_key"]
    for field in ("base_url", "model", "timeout_s", "allow_local"):
        if field in body and body[field] not in (None, ""):
            try:
                c[field] = ai_config.coerce(field, body[field])
            except ConfigError as e:
                return jsonify({"ok": False, "code": "bad_config", "error": str(e)}), 400
    typed_key = str(body.get("api_key") or "").strip()
    if typed_key:
        c["api_key"] = typed_key
        key_from = "form"
    if "base_url" in body and body["base_url"]:
        try:
            c["base_url"] = ai_config.validate_base_url(c["base_url"], bool(c["allow_local"]))
        except ConfigError as e:
            return jsonify({"ok": False, "code": "bad_config", "error": str(e)}), 400
    if not c["api_key"]:
        return jsonify({"ok": False, "code": E_NOT_CONFIGURED,
                        "error": "尚未配置 API key"}), 503
    try:
        content, usage = _chat([{"role": "user", "content": "ping"}],
                               timeout=int(c["timeout_s"]), max_tokens=8, kind="test", cfg=c)
    except RuntimeError as e:
        parts = str(e).split(":", 2)
        code = parts[1] if len(parts) > 1 else E_UNREACHABLE
        detail = parts[2] if len(parts) > 2 else str(e)
        return jsonify({"ok": False, "code": code, "error": _test_hint(code),
                        "detail": detail[:200], "model": c["model"]}), 502
    return jsonify({"ok": True, "code": "ok", "model": c["model"],
                    "reply": content[:120], "usage": usage,
                    "base_url": c["base_url"], "key_source": key_from})


def _test_hint(code: str) -> str:
    return {
        E_NOT_CONFIGURED: "未配置 API key",
        E_AUTH: "鉴权失败：key 无效或已过期",
        E_MODEL_404: "模型名不被该端点接受（404）",
        E_TIMEOUT: "请求超时：端点无响应或网络太慢",
        E_UNREACHABLE: "端点不可达：地址、DNS 或网络有问题",
        E_HTTP: "服务端返回异常状态",
    }.get(code, "未知错误")


@ai_bp.get("/api/ai/usage")
def api_ai_usage():
    c = _cfg()
    st = _store()
    if st is None:
        return jsonify({"ok": True, "available": False,
                        "detail": "账本不可用（indexes/ 建不起来）",
                        "budget": _budget_state()})
    s = st.summary()
    cost = st.cost_summary(s["ym"], float(c["price_in_per_1k"]), float(c["price_out_per_1k"]))
    price_ok = float(c["price_in_per_1k"]) > 0 or float(c["price_out_per_1k"]) > 0
    return jsonify({"ok": True, "available": True, "period": {"day": s["day"], "ym": s["ym"]},
                    "today": s["today"], "month": s["month_usage"], "by_kind": s["by_kind"],
                    "cost": {**cost, "price_configured": price_ok},
                    "budget": _budget_state(), "recent": st.recent(10),
                    "model": c["model"], "key_present": bool(c["api_key"])})


def _resolve_doc(rel: str) -> dict:
    """归一 + safe_rel + 域判定，**不读文件**。

    分成"判路径/判域"和"读盘"两步是为了让调用方能自己排拒绝顺序：
    explain 必须让域闸门排在存在性检查之前（否则 404/403 两种状态码就成了
    对不出站目录的探测器 —— tests/test_ai_qa.py E5 锁着这条）。
    """
    rel = (rel or "").strip().replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    if not rel:
        raise ValueError("path 不能为空")
    if not rel.lower().endswith(".md"):
        # 上下文装配与查漏判据读的都是 Markdown（#、```、[[双链]]）。
        # 挡在后端，而不是只靠前端「非 .md 不画按钮」—— 绕开界面直接打接口也一样进不来。
        raise ValueError("AI 只读 Markdown（.md）文档")
    try:
        p = current_app.config["KB_HOOKS"]["safe_rel"](rel, {".md"})
    except HTTPException as e:      # safe_rel 用 abort 拒绝：转成人话，别降级成 500
        raise ValueError(e.description) from None
    domain = rel.split("/", 1)[0]   # 取客户端相对路径首段：p 是 resolve() 过的，
    # 而 Windows 临时目录常以 8.3 短名传入，拿 p 去 relative_to(CONTENT) 会直接抛
    # ValueError → 500（切片 2 实测踩过）。
    return {"rel": rel, "path": p, "domain": domain,
            "blocked": not ai_config.domain_allows_egress(
                current_app.config["CONTENT"], domain),
            "exists": p.is_file()}


def _qa_store():
    return _store()


# 一次「解释这个词」最多让模型写多少 token。300 个 token 足够写完 120 字的中文解释，
# 而**不设这一项就是实测 30 秒的成因之一**：不封顶时模型爱把 answer/confidence/terms
# 一整套 JSON 吐完（旧版还额外要求它只回 JSON —— 见本文件的 git 历史）。
ASK_MAX_TOKENS = 300


def _doc_for_explain(data: dict):
    """explain 的入参校验：只认 path + selection，**正文一个字都不读**。

    path 仍然要过域闸门（不变量 9 ①）：它决定"这篇的选区能不能问"，而不是"发不发正文"。
    闸门必须排在存在性检查之前 —— 否则 404/403 两种状态码就成了对不出站目录的探测器
    （tests/test_ai_qa.py E5 锁着这条）。
    """
    selection = " ".join(str(data.get("selection") or "").split())
    if not str(data.get("path") or "").strip() or not selection:
        return None, (jsonify({"ok": False, "error": "path 与 selection 都不能为空"}), 400)
    if len(selection) < 2:
        return None, (jsonify({"ok": False, "error": "选中的内容太短（至少 2 个字符）"}), 400)
    if len(selection) > 4000:
        return None, (jsonify({"ok": False, "error": "选中的内容太长（上限 4000 字）"}), 400)
    try:
        res = _resolve_doc(str(data.get("path") or ""))
    except ValueError as e:
        return None, (jsonify({"ok": False, "error": str(e)[:200]}), 400)
    if res["blocked"]:
        return None, (jsonify({"ok": False, "code": "domain_blocked",
                               "error": f"域「{res['domain']}」被分类学标为不出站，"
                                        "AI 无法读取该文档"}), 403)
    if not res["exists"]:
        return None, (jsonify({"ok": False, "error": "文档不存在"}), 404)
    return {"path": res["rel"], "domain": res["domain"], "selection": selection}, None


@ai_bp.post("/api/ai/explain")
def api_ai_explain():
    """选词问 AI：**只把选中的那几个字发出去，只回一句解释**。

    这里刻意不读文档、不拼大纲、不查检索、不接受追问与档位 ——
    用户 2026-09-29 明确要求（"也不用你结合整段集合整篇文章！就只需要回答我选中的文字的含义"）。
    保留的只有四件：域闸门、注入加固、答案缓存（同一个词第二次问不再计费）、预算帽。
    """
    data = request.get_json(force=True, silent=True) or {}
    payload, refused = _doc_for_explain(data)
    if refused:
        return refused
    if not ai_available():
        return jsonify({"ok": False, "code": E_NOT_CONFIGURED,
                        "error": "尚未配置 API key（设置 → AI 页签）"}), 503
    selection = payload["selection"]
    c = _cfg()
    st = _qa_store()
    key = ai_qa.cache_key(selection, c["model"])
    if st is not None:
        cached = st.qa_get(key)
        if cached and cached["ok"] and cached["answer"]:
            return jsonify({"ok": True, "answer": cached["answer"], "selection": selection,
                            "model": cached["model"] or c["model"], "usage": cached["usage"],
                            "cached": True, "cached_at": cached["ts"]})
    b = _budget_state()
    if b["exceeded"]:
        return jsonify({"ok": False, "error": "budget_exceeded", "code": "budget_exceeded",
                        "hint": f"本月已用 {b['used_month']} 次，达到预算帽 {b['budget']}"}), 429
    try:
        raw, usage = _chat(ai_qa.build_messages(selection), timeout=int(c["timeout_s"]),
                           max_tokens=ASK_MAX_TOKENS, kind="select")
    except RuntimeError as e:
        parts = str(e).split(":", 2)
        code = parts[1] if len(parts) > 1 else E_UNREACHABLE
        err = _test_hint(code)
        if st is not None:
            st.qa_put(key, selection=selection, model=c["model"],
                      prompt_ver=ai_qa.PROMPT_VERSION, ok=False, answer="", error=err)
        return jsonify({"ok": False, "code": code, "error": err,
                        "detail": (parts[2] if len(parts) > 2 else str(e))[:200]}), 502
    answer = ai_qa.plain_answer(raw)
    if st is not None:
        st.qa_put(key, selection=selection, model=c["model"],
                  prompt_ver=ai_qa.PROMPT_VERSION, ok=bool(answer), answer=answer,
                  usage=usage, sent_chars=len(selection),
                  error="" if answer else "模型回了一段空白")
    if not answer:
        return jsonify({"ok": False, "code": "provider_error", "error": "模型没给出内容",
                        "usage": usage}), 502
    return jsonify({"ok": True, "answer": answer, "selection": selection,
                    "model": c["model"], "usage": usage, "cached": False})



def register(app):
    app.register_blueprint(ai_bp)
