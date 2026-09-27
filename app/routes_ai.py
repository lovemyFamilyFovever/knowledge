# -*- coding: utf-8 -*-
"""AI 出站层：OpenAI 兼容 chat 客户端 + RAG 检索增强回答 + 配置/测试/用量端点。

配置的唯一入口是 app/ai_config.py（env > .ai-config.json > 缺省），本模块只消费不回显明文 key。
只依赖标准库 urllib —— 与 AGENTS「任意 Python 可启动」兼容。

端点：
  GET/PUT /api/ai/config   读（脱敏）/ 写（校验后落 gitignored JSON）
  POST /api/ai/test        1-token 级连通性 ping，失败分类见 _classify_error()
  GET /api/ai/usage        今日/本月调用数、tokens、估算花费、预算余额
  POST /api/ai/explain     切片 2：选词问 AI（dry=true 只回「将要发什么」，不出站、不计费）
  GET /api/ai/qa           切片 2：本篇问过的（读派生缓存，不碰语料）
  POST /api/ask            RAG 问答（沿用旧行为，新增记账与预算帽）
  GET /api/ask/status      可用性（旧前端在用，保持兼容）

key 未配置时 /api/ask 返回 not_configured(503)，前端优雅降级；
RAG 组件缺失时自动跳过检索（纯 chat 仍可用）。
"""
import json
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import HTTPException

from app import ai_config, ai_qa
from app.ai_config import ConfigError
from app.ai_usage import AiUsageStore
from app.store import parse_frontmatter

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


def _qa_store():
    return _store()


def _doc_for_explain(data: dict):
    """校验 + 读盘 + 域级闸门。返回 (payload, None) 或 (None, (json, status))。

    正文一律服务端现读：前端只交 path + selection，否则"发什么出去"由浏览器说了算，
    域级闸门（不变量 9 ①）就拦不住了。
    """
    rel = str(data.get("path") or "").strip().replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    selection = " ".join(str(data.get("selection") or "").split())
    mode = str(data.get("mode") or "term").strip()
    if mode not in ai_qa.MODES:
        mode = "term"
    if not rel or not selection:
        return None, (jsonify({"ok": False, "error": "path 与 selection 都不能为空"}), 400)
    if len(selection) < 2:
        return None, (jsonify({"ok": False, "error": "选中的内容太短（至少 2 个字符）"}), 400)
    if len(selection) > 4000:
        return None, (jsonify({"ok": False, "error": "选中的内容太长（上限 4000 字）"}), 400)
    try:
        p = current_app.config["KB_HOOKS"]["safe_rel"](rel, {".md"})
    except HTTPException as e:      # safe_rel 用 abort 拒绝：原样抛，别降级成 500
        return None, (jsonify({"ok": False, "error": e.description}), e.code)
    # 域名取**客户端传来的相对路径**的第一段，不要拿 p 去 relative_to(CONTENT)：
    # safe_rel 里 p 是 resolve() 过的，而 Windows 临时目录常以 8.3 短名传入，
    # 两者一个短一个长 → relative_to 直接 ValueError → 500（切片 2 实测踩过）。
    domain = rel.split("/", 1)[0]
    if not ai_config.domain_allows_egress(current_app.config["CONTENT"], domain):
        # 硬门在后端：绕过前端直接打接口也一样 403（不变量 9 ①）。
        # 闸门**排在存在性检查之前**：否则"这个路径存不存在"本身就成了对不出站
        # 目录的一次探测，而且 404/403 两种答案会让前端有理由去猜内容。
        return None, (jsonify({"ok": False, "code": "domain_blocked",
                               "error": f"域「{domain}」被分类学标为不出站，AI 无法读取该文档"}),
                      403)
    if not p.is_file():
        return None, (jsonify({"ok": False, "error": "文档不存在"}), 404)
    try:
        md = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, (jsonify({"ok": False, "error": "文档读取失败"}), 500)
    if len(md) > 400000:
        return None, (jsonify({"ok": False, "error": "文档过大（超过 400KB），请改用整篇档以外的问题粒度"}),
                      413)
    # 选中超过 80 字 → 语义上就是"问这段"，不是"问这个词"
    if mode == "term" and len(selection) > 80:
        mode = "passage"
    fm, _body = parse_frontmatter(md)
    title = str(fm.get("title") or p.stem)
    return {"path": rel, "domain": domain, "selection": selection, "mode": mode,
            "md": md, "title": title, "digest": ai_qa.doc_hash(md)}, None


@ai_bp.post("/api/ai/explain")
def api_ai_explain():
    """选词问 AI。dry=true 时只回"将要发出去什么"（本地算，不出站、不计费）。"""
    data = request.get_json(force=True, silent=True) or {}
    payload, refused = _doc_for_explain(data)
    if refused:
        return refused
    dry = bool(data.get("dry"))
    question = str(data.get("question") or "").strip()[:500]
    history = data.get("history") if isinstance(data.get("history"), list) else []
    if not ai_available():
        return jsonify({"ok": False, "code": E_NOT_CONFIGURED,
                        "error": "尚未配置 API key（设置 → AI 页签）"}), 503

    hits = _rag_hits(question or payload["selection"], payload["domain"])
    ctx = ai_qa.build_context(payload["md"], payload["selection"], payload["mode"], hits,
                              payload["title"], payload["path"])
    base = {"ok": True, "mode": payload["mode"], "located": ctx["located"],
            "where": ctx["where"], "sent_chars": ctx["chars"],
            "rag_hits": len(hits), "title": payload["title"]}
    if dry:
        base["preview"] = ctx["text"][:1200]
        return jsonify(base)
    if not ctx["located"]:
        # 定位不到就不假装"我读了上下文"—— 如实说，让用户决定要不要换选区
        base.update({"ok": False, "code": "not_located",
                     "error": "在文档里没找到这段选中内容（可能文档刚被改过）"})
        return jsonify(base), 422

    st = _qa_store()
    key = ai_qa.cache_key(payload["path"], payload["digest"], payload["selection"],
                          payload["mode"], question, history)
    # 命中与否**只由 key 决定**：key 里含文档 hash、选区、档位、问题与多轮历史，
    # 所以调用点不需要再写一条「有追问就跳过缓存」的守卫 —— 那样判据就散成两处，
    # 而且实测是冗余的（把那条守卫短路掉，全套一条都不红）。判据只留 cache_key 一处。
    if st is not None:
        cached = st.qa_get(key)
        if cached and cached["ok"]:
            base.update({"answer": cached["answer"], "confidence": cached["confidence"],
                         "terms": cached["terms"], "sources": cached["sources"],
                         "usage": cached["usage"], "cached": True, "cached_at": cached["ts"]})
            return jsonify(base)

    b = _budget_state()
    if b["exceeded"]:
        return jsonify({"ok": False, "error": "budget_exceeded", "code": "budget_exceeded",
                        "hint": f"本月已用 {b['used_month']} 次，达到预算帽 {b['budget']}"}), 429

    c = _cfg()
    msgs = ai_qa.build_messages(ctx["text"], payload["selection"], payload["mode"],
                                question, history)
    parsed, usage, err = None, {}, ""
    for attempt in (1, 2):
        try:
            raw, usage = _chat(msgs, timeout=int(c["timeout_s"]), kind="select")
        except RuntimeError as e:
            parts = str(e).split(":", 2)
            err = _test_hint(parts[1] if len(parts) > 1 else E_UNREACHABLE)
            usage = {}
            break                                  # 网络类失败不重试（重试就是双倍计费）
        parsed = ai_qa.parse_answer(raw)
        if parsed:
            err = ""
            break
        err = "模型没有按约定的 JSON 结构回答"
        msgs.append({"role": "user", "content": ai_qa.SCHEMA_HINT + "（上一次输出无法解析，只输出 JSON）"})
    if st is not None:
        st.qa_put(key, path=payload["path"], selection=payload["selection"],
                  mode=payload["mode"], model=c["model"], prompt_ver=ai_qa.PROMPT_VERSION,
                  ok=bool(parsed), answer=(parsed or {}).get("answer", ""),
                  confidence=(parsed or {}).get("confidence", ""),
                  terms=(parsed or {}).get("terms"), sources=(parsed or {}).get("sources"),
                  usage=usage, sent_chars=ctx["chars"], error=err)
    if not parsed:
        code = "provider_error" if err.startswith(("鉴权", "端点", "请求超时", "服务")) else "bad_schema"
        base.update({"ok": False, "code": code, "error": err or "回答失败",
                     "sent_chars": ctx["chars"]})
        return jsonify(base), 502
    base.update({"answer": parsed["answer"], "confidence": parsed["confidence"],
                 "terms": parsed["terms"], "sources": parsed["sources"],
                 "usage": usage, "cached": False, "model": c["model"]})
    return jsonify(base)


@ai_bp.get("/api/ai/qa")
def api_ai_qa_list():
    """本篇问过的（侧栏回看）：读派生缓存，不碰语料。"""
    rel = request.args.get("path", "").strip()
    if not rel:
        return jsonify({"ok": False, "error": "缺少 path"}), 400
    st = _qa_store()
    if st is None:
        return jsonify({"ok": True, "available": False, "items": []})
    return jsonify({"ok": True, "available": True, "path": rel, "items": st.qa_list_for_doc(rel)})


def _rag_ready() -> bool:
    """向量模型是否已在位。**不构造 embedder**：get_rag() 会去加载/下载权重，
    把一次"选词问 AI"的预览卡成几十秒（§6 第 5 行 /api/rag/status 同款事故，
    这条路径是切片 2 的探针在真实实例上第一次跑出来才发现的）。"""
    ready = (current_app.config.get("KB_HOOKS") or {}).get("rag_model_ready")
    return bool(ready()) if ready else False


def _rag_hits(q: str, domain: str) -> list:
    """本地语义检索 Top-3，并且**按域过滤掉不出站的文档**：
    RAG 命中里混进 career/小说 的话，把它们当上下文发出去 = 绕过闸门。"""
    hooks = current_app.config.get("KB_HOOKS") or {}
    get_rag = hooks.get("get_rag")
    if not (get_rag and hooks.get("query_rag")) or not _rag_ready():
        return []
    content = Path(current_app.config["CONTENT"])
    try:
        emb, rstore = get_rag()
        if emb is None or rstore is None:
            return []
        hits = hooks["query_rag"](rstore, emb, q, k=6) or []
    except Exception:
        return []
    blocked = ai_config.egress_blocked_domains(content)
    out = []
    for h in hits:
        f = str(h.get("file") or "")
        dom = f.split("/", 1)[0] if "/" in f else f
        if dom in blocked:
            continue
        out.append(h)
    return out[:3]


@ai_bp.post("/api/ask")
def api_ask():
    """RAG 问答：语义检索 Top-K 语料 → 拼 prompt → LLM 生成 → 带引用返回。"""
    data = request.get_json(force=True, silent=True) or {}
    q = str(data.get("q") or "").strip()
    if not q:
        return jsonify({"ok": False, "error": "问题不能为空"}), 400
    if not ai_available():
        return jsonify({"ok": False, "error": E_NOT_CONFIGURED, "code": E_NOT_CONFIGURED,
                        "hint": "未配置 KB_AI_API_KEY 环境变量或 .ai-config.json"}), 503
    b = _budget_state()
    if b["exceeded"]:
        return jsonify({"ok": False, "error": "budget_exceeded", "code": "budget_exceeded",
                        "hint": f"本月已用 {b['used_month']} 次，达到预算帽 "
                                f"{b['budget']}；可在设置里调整预算"}), 429

    # 复用 routes_rag 的 KB_HOOKS 单例（rag 可选依赖缺失 → hits 留空，纯 chat 兜底）。
    # 与 _rag_hits 同一个守卫：模型不在位就别碰 get_rag()，否则这个请求会去加载/下载权重。
    hits = []
    hooks = current_app.config.get("KB_HOOKS") or {}
    get_rag = hooks.get("get_rag")
    if get_rag and hooks.get("query_rag") and _rag_ready():
        try:
            emb, rstore = get_rag()
            if emb is not None and rstore is not None:
                hits = hooks["query_rag"](rstore, emb, q, k=6) or []
        except Exception:
            hits = []

    ctx = "\n\n".join(
        f"[片段 {i + 1}] 路径: {h.get('file', '')}\n{str(h.get('text', ''))[:1200]}"
        for i, h in enumerate(hits)) if hits else "（未检索到相关语料）"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"语料片段：\n{ctx}\n\n问题：{q}"},
    ]
    c = _cfg()
    try:
        answer, usage = _chat(messages, timeout=int(c["timeout_s"]), kind="ask")
    except RuntimeError as e:
        parts = str(e).split(":", 2)
        code = parts[1] if len(parts) > 1 else E_UNREACHABLE
        detail = parts[2] if len(parts) > 2 else str(e)
        status = 503 if code == E_NOT_CONFIGURED else 502
        return jsonify({"ok": False, "error": _test_hint(code), "code": code,
                        "detail": detail[:200]}), status

    sources = [{"path": h.get("file", ""), "url": h.get("url"),
                "score": round(h.get("score", 0) or 0, 4)} for h in hits]
    return jsonify({"ok": True, "answer": answer, "sources": sources,
                    "model": c["model"], "usage": usage})


@ai_bp.get("/api/ask/status")
def api_ask_status():
    c = _cfg()
    return jsonify({"ok": True, "available": bool(c["api_key"]),
                    "base": c["base_url"], "model": c["model"]})


def register(app):
    app.register_blueprint(ai_bp)
