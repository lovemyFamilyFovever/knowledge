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
from contextlib import closing
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import HTTPException

from app import ai_audit, ai_batch, ai_config, ai_qa
from app.ai_config import ConfigError
from app.ai_usage import AUDIT_STATUSES, AiUsageStore
from app.fts import cjk_clean, open_db
from app.store import md_files, parse_frontmatter

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


def _read_doc(res: dict) -> dict:
    """真正读盘（调用方已确认允许读）。"""
    if not res["exists"]:
        raise FileNotFoundError(res["rel"])
    md = res["path"].read_text(encoding="utf-8", errors="replace")
    if len(md) > 400000:
        raise ValueError("文档过大（超过 400KB），请先拆分再问")
    fm, _body = parse_frontmatter(md)
    return dict(res, md=md, fm=fm or {},
                title=str((fm or {}).get("title") or res["path"].stem),
                digest=ai_qa.doc_hash(md))


def _known_titles() -> list:
    """全库标题集合（派生缓存里读，不重扫语料）。

    必须过 `cjk_clean`：索引为了 FTS 分词把标题写成了"向 量 数 据 库"这种带空格的形态
    （fts.py:54），直接拿来和正文比对会一个都匹配不上 —— 这条是切片 3 实测踩出来的。
    注意 cjk_clean 会在末尾留下一个空格 —— 归一化不在这里做，
    统一由消费方 `ai_audit.local_checks` 在使用前 strip（一处加工，两处口径才不会分叉）。
    """
    try:
        with closing(open_db(Path(current_app.config["INDEXES"]))) as con:
            return [cjk_clean(r[0]) for r in con.execute("SELECT DISTINCT title FROM docs")
                    if r[0]]
    except Exception:
        return []


def _dead_links(rel: str) -> list:
    """本篇未解析的双链原文 —— 用索引算好的结果，不自己再解析一遍正则。
    索引里没有这一行（新文档还没进索引）时返回空，交给本地判据自己按标题集合判。"""
    try:
        with closing(open_db(Path(current_app.config["INDEXES"]))) as con:
            return [r[0] for r in con.execute(
                "SELECT raw FROM links WHERE src=? AND resolved=0", (rel,))]
    except Exception:
        return []


def _dead_links_map() -> dict:
    """一次查询拿全库的未解析双链：rel -> [原文目标]。

    批量按篇调 `_dead_links` 会开几十次库、每次都撞 watcher 的写锁（实测一批 37 篇
    能卡到 40s 不收尾），所以整批只查一次，篇内取表。口径与 `_dead_links` 完全一致。
    """
    try:
        with closing(open_db(Path(current_app.config["INDEXES"]))) as con:
            out = {}
            for src, raw in con.execute("SELECT src, raw FROM links WHERE resolved=0"):
                out.setdefault(src, []).append(raw)
        return out
    except Exception:
        return {}


def _asset_resolver(doc_path: Path):
    content = Path(current_app.config["CONTENT"])

    def exists(url: str) -> bool:
        u = url.strip().split("?")[0].split("#")[0]
        if not u:
            return False
        cands = [(doc_path.parent / u).resolve(), (content / u).resolve(),
                 (content / "_assets" / Path(u).name).resolve()]
        return any(c.is_file() for c in cands)

    return exists


@ai_bp.post("/api/ai/audit")
def api_ai_audit():
    """单篇查漏补缺：本地判据必跑，AI 判断按闸门与 key 情况追加。"""
    data = request.get_json(force=True, silent=True) or {}
    want_ai = bool(data.get("ai", True))
    try:
        res = _resolve_doc(str(data.get("path") or ""))
        if not res["exists"]:
            return jsonify({"ok": False, "error": "文档不存在"}), 404
        doc = _read_doc(res)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)[:200]}), 400
    except OSError:
        return jsonify({"ok": False, "error": "文档读取失败"}), 500

    proposals = ai_audit.local_checks(
        doc["md"], path=doc["rel"], fm=doc["fm"], known_titles=_known_titles(),
        dead_links=_dead_links(doc["rel"]), asset_exists=_asset_resolver(doc["path"]))
    # local_count 必须在 AI 之前取：它的口径是"本地判据查出几条"。
    # 放在后面量就等于把 AI 的行数也算进本地，C3 那条"AI 不许造条目"就永远判不出来了。
    local_count = len(proposals)
    ai_enabled, ai_reason, sent = False, "", 0

    if doc["blocked"]:
        ai_reason = f"域「{doc['domain']}」被分类学标为不出站，只跑了本地判据"
    elif not ai_available():
        ai_reason = "未配置 API key（设置 → AI 页签），只跑了本地判据"
    elif not want_ai:
        ai_reason = "本次只要求本地判据"
    else:
        b = _budget_state()
        if b["exceeded"]:
            ai_reason = f"本月已用 {b['used_month']} 次，达到预算帽 {b['budget']}，只跑了本地判据"
        else:
            ai_enabled, ai_reason, sent = _audit_with_ai(doc, proposals)

    st = _qa_store()
    if st is not None:
        st.audit_upsert(doc["rel"], proposals)
        # 改了正文重扫：已经不成立的旧条目要清掉，否则面板会一直挂着"上次的问题"
        st.audit_prune(doc["rel"], [p["id"] for p in proposals])
        # 回给前端的是**账本里的那一份**（带处置状态）。直接回本地算出来的裸列表会让
        # 面板自相矛盾：汇总条说"已处置 1 条"，条目本身却被打回未处置的样子。
        proposals = st.audit_list(doc["rel"])
    return jsonify({"ok": True, "path": doc["rel"], "title": doc["title"],
                    "proposals": proposals, "ai_enabled": ai_enabled,
                    "ai_reason": ai_reason, "sent_chars": sent,
                    "local_count": local_count})


def _audit_with_ai(doc: dict, proposals: list):
    """把该问的问一遍（最多两条），失败就如实记在 ai_reason 里，不假装查全。"""
    c = _cfg()
    asked = 0
    sent = 0        # 真的发出去多少字 —— 报 0 就是撒谎，哪怕前端这一版不显示它
    reasons = []
    cand = next((p for p in proposals if p["kind"] == "should_link"), None)
    if cand:
        ctx = ai_qa.build_context(doc["md"], cand["evidence"][:80], "term", [],
                                  doc["title"], doc["rel"])
        asked += 1
        sent += int(ctx["chars"])
        got = _audit_ask(ctx, ai_audit.ai_prompt("should_link", ctx["text"],
                                                 cand["evidence"]), c)
        if got is None:
            reasons.append("应引未引的 AI 判断没跑成")
        else:
            ai_audit.merge_ai(proposals, got, "should_link", doc["rel"])
    if str(doc["fm"].get("collected") or ""):
        ctx = ("文档：" + doc["title"] + "（采集于 " + str(doc["fm"]["collected"]) + "）\n\n"
               "大纲：" + " / ".join(h["title"] for h in ai_audit.outline(doc["md"])))
        asked += 1
        ctx = {"text": ctx, "chars": len(ctx.encode("utf-8"))}
        sent += ctx["chars"]
        got = _audit_ask(ctx, ai_audit.ai_prompt("possibly_outdated", ctx["text"], ""), c)
        if got is None:
            reasons.append("过时风险判断没跑成")
        else:
            ai_audit.merge_ai(proposals, got, "possibly_outdated", doc["rel"])
    return (True if asked else False), ("；".join(reasons) or "AI 判断已并入"), sent


def _audit_ask(ctx: dict, prompt: str, c: dict):
    msgs = [{"role": "system", "content": ai_qa.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}]
    try:
        raw, _usage = _chat(msgs, timeout=int(c["timeout_s"]), kind="audit")
    except RuntimeError:
        return None
    return ai_qa.parse_answer(raw)


@ai_bp.get("/api/ai/audit")
def api_ai_audit_get():
    rel = request.args.get("path", "").strip()
    if not rel:
        return jsonify({"ok": False, "error": "缺少 path"}), 400
    if ai_audit.is_domain_scope(rel):
        # 作用域键也允许读，但域名必须是真实存在的一级目录：
        # 不校验的话 `?path=@domain:<随便什么>` 就成了往派生库里探任意键的口子。
        dom = rel[len(ai_audit.DOMAIN_PREFIX):].strip().strip("/")
        if "/" in dom or not (current_app.config["CONTENT"] / dom).is_dir():
            return jsonify({"ok": False, "error": "作用域键形如 @domain:<一级域名>"}), 400
    st = _qa_store()
    if st is None:
        return jsonify({"ok": True, "available": False, "proposals": []})
    return jsonify({"ok": True, "available": True, "path": rel,
                    "proposals": st.audit_list(rel)})


@ai_bp.post("/api/ai/audit/status")
def api_ai_audit_status():
    """记处置：pending / adopted / dismissed。只改派生库，一个字都不碰语料。"""
    data = request.get_json(force=True, silent=True) or {}
    rel = str(data.get("path") or "").strip()
    pid = str(data.get("id") or "").strip()
    status = str(data.get("status") or "").strip()
    if not rel or not pid:
        return jsonify({"ok": False, "error": "path 与 id 都不能为空"}), 400
    if status not in AUDIT_STATUSES:
        return jsonify({"ok": False, "error": "status 只能是 pending / adopted / dismissed",
                        "allowed": sorted(AUDIT_STATUSES)}), 400
    if ai_audit.is_domain_scope(rel):
        dom = rel[len(ai_audit.DOMAIN_PREFIX):].strip().strip("/")
        if "/" in dom or not (current_app.config["CONTENT"] / dom).is_dir():
            return jsonify({"ok": False, "error": "作用域键形如 @domain:<一级域名>"}), 400
    st = _qa_store()
    if st is None:
        return jsonify({"ok": False, "error": "账本不可用"}), 503
    if not st.audit_set_status(rel, pid, status):
        return jsonify({"ok": False, "error": "没找到这条建议（可能文档刚被重扫过）"}), 404
    return jsonify({"ok": True, "path": rel, "id": pid, "status": status})


# ------------------------------------------------------------ 切片 4：批量查漏补缺

# 本地判据要读正文 + 逐行过正则：两百篇以内一次请求扫得完，再多就该抽样而不是把用户挂住。
EXACT_SCAN_MAX = 200
SAMPLE_DOCS = 40


def _scope_blocked(domain: str) -> bool:
    return not ai_config.domain_allows_egress(current_app.config["CONTENT"], domain)


def _batch_entries(scope: dict) -> list:
    """scope → [{"rel","p","size","blocked"}]，**只看目录项，一篇正文都不读**。

    只吃 .md，且 `_` 前缀目录（_inbox/_assets/_trash/_meta）天然不在名单里 ——
    这条由 `store.md_files` 保证，不在这里再抄一份规则（不变量 2/5）。
    """
    content = current_app.config["CONTENT"]
    paths = scope.get("paths")
    out = []
    if isinstance(paths, list) and paths:
        for rel in paths[:ai_batch.MAX_DOCS]:
            try:
                res = _resolve_doc(str(rel))
            except ValueError:
                continue                      # 非 .md / 越界 / 空：一条坏路径不拦整批
            if res["exists"]:
                out.append({"rel": res["rel"], "p": res["path"], "size": _size_of(res["path"]),
                            "blocked": res["blocked"]})
        return sorted(out, key=lambda e: e["rel"])
    dom = str(scope.get("domain") or "").strip().strip("/")
    if not dom:
        raise ValueError("要么给 domain（可再带 sub），要么给 paths 列表")
    sub = str(scope.get("sub") or "").strip().strip("/")
    want = ((dom + "/" + sub) if sub else dom).lower()
    blocked = _scope_blocked(dom)
    for p, rel in md_files(content):
        if rel.lower().startswith(want + "/"):
            out.append({"rel": rel, "p": p, "size": _size_of(p), "blocked": blocked})
    return sorted(out, key=lambda e: e["rel"])


def _size_of(p) -> int:
    try:
        return int(p.stat().st_size)
    except OSError:
        return 0


def _scan_one(entry: dict, known: list, dead_map: dict | None = None) -> dict | None:
    """读一篇 + 跑本地判据。读不动 / 过大都回 None（不计入样本，而不是算 0 条）。"""
    try:
        md = entry["p"].read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if len(md) > ai_batch.MAX_DOC_BYTES:
        return None
    fm, _ = parse_frontmatter(md)
    props = ai_audit.local_checks(md, path=entry["rel"], fm=fm or {}, known_titles=known,
                                  dead_links=(dead_map or {}).get(entry["rel"], []),
                                  asset_exists=_asset_resolver(entry["p"]))
    return {"path": entry["rel"], "bytes": len(md.encode("utf-8")), "count": len(props),
            # 「要问 AI」= 本地判据里有 needs_ai **且**这一篇允许出站
            "need_ai": ai_batch.needs_ai(props) and not entry["blocked"]}


def _batch_rows(entries: list) -> tuple[list, dict | None]:
    """小范围精扫；大范围**等距抽样**（读全盘 + 逐行正则可能几十秒，那又是一次挂在
    fetch 上的长任务 —— 与扫描本身同理，估算也不能让用户白等）。

    步长固定 ⇒ 同一个域连估两次得到的是同一份数，不是每刷新一次换个数。
    """
    known = _known_titles()
    dead_map = _dead_links_map()
    if len(entries) <= EXACT_SCAN_MAX:
        rows = [r for r in (_scan_one(e, known, dead_map) for e in entries) if r]
        return rows, None
    step = -(-len(entries) // SAMPLE_DOCS)          # ceil
    picked = entries[::step][:SAMPLE_DOCS]
    rows = [r for r in (_scan_one(e, known, dead_map) for e in picked) if r]
    return rows, {"from": len(entries), "measured": len(rows), "step": step,
                  "method": "等距抽样"}


def _batch_estimate_of(entries: list) -> tuple:
    rows, sample = _batch_rows(entries)
    c = _cfg()
    b = _budget_state()
    est = ai_batch.estimate(rows, budget_left=b["left"], sample=sample,
                            price_in_per_1k=c["price_in_per_1k"],
                            price_out_per_1k=c["price_out_per_1k"])
    return est, rows, b


@ai_bp.post("/api/ai/batch/estimate")
def api_ai_batch_estimate():
    """开跑前的账单预览：说清要问几次、大概多少 token / 多少钱。

    这一趟**不出站、不计费**。范围超过 `EXACT_SCAN_MAX` 篇时按等距抽样放大 ——
    本地判据本身可能就是几十秒的长任务，估算不该把用户挂在那儿等它。
    """
    data = request.get_json(force=True, silent=True) or {}
    try:
        entries = _batch_entries(data.get("scope") or {})
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)[:200]}), 400
    if not entries:
        return jsonify({"ok": False, "error": "这个范围里没有可扫的 Markdown"}), 400
    est, rows, b = _batch_estimate_of(entries)
    if not rows:
        return jsonify({"ok": False, "error": "范围内没有可读的文档"}), 400
    top = sorted(rows, key=lambda r: -r["count"])[:8]
    return jsonify({"ok": True, "estimate": est, "top": top,
                    "ai_available": ai_available(),
                    "used_month": b["used_month"], "budget": b["budget"]})


@ai_bp.post("/api/ai/batch/start")
def api_ai_batch_start():
    """启动批量作业：立刻回进度快照，扫描在 daemon 线程里跑。

    预算帽是硬门 —— 抽样估算是"大概花多少"（给人看的），而**拦钱包看的是上限**：
    每篇都可能问一次，所以范围篇数一超过剩余额度就不许带 AI 开跑。
    ai=false 的纯本地批量零调用零出站，不受这条限制。
    """
    data = request.get_json(force=True, silent=True) or {}
    want_ai = bool(data.get("ai", True))
    scope = data.get("scope") or {}
    try:
        entries = _batch_entries(scope)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)[:200]}), 400
    if not entries:
        return jsonify({"ok": False, "error": "这个范围里没有可扫的 Markdown"}), 400

    est, _rows, b = _batch_estimate_of(entries)
    if want_ai and est["over_budget"]:
        return jsonify({"ok": False, "code": "over_budget",
                        "error": f"这一批最坏要问 {est['calls_upper_bound']} 次，"
                                 f"本月只剩 {b['left']} 次额度；"
                                 f"缩小范围（按子域扫）、调高预算帽，或只跑本地判据（ai=false）",
                        "estimate": est}), 429
    if want_ai and not ai_available():
        return jsonify({"ok": False, "code": "not_configured",
                        "error": "未配置 API key，这一批只能跑本地判据（ai=false）",
                        "estimate": est}), 400

    known = _known_titles()
    dead_map = _dead_links_map()   # 整批一次查完，别在线程里按篇开库
    c = _cfg()
    app_obj = current_app._get_current_object()   # 线程里没有 request context：先抓 app 对象
    # 引用集合边扫边攒，跑完就地算"覆盖空白"（读一篇顺手记一行，不第二遍读盘）。
    refs = {}
    dom = str(scope.get("domain") or "").strip().strip("/")
    if not dom:
        only = {e["rel"].split("/", 1)[0] for e in entries}
        dom = only.pop() if len(only) == 1 else ""

    def per_doc(job, it):
        # 每一篇都在 worker 线程里跑，所以整段都要自己把 app context 推进去；
        # 少这一层，_cfg / _qa_store / _dead_links 会当场 RuntimeError，
        # 而 BatchRunner 会把异常按篇记进 errors —— 症状是"整批全失败但 HTTP 200"。
        with app_obj.app_context():
            try:
                md = it["p"].read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                return 0, False, f"读取失败：{type(e).__name__}"
            if len(md) > ai_batch.MAX_DOC_BYTES:
                return 0, False, "文档过大（>400KB），这一篇跳过"
            for t in ai_audit.wikilinks(md):
                refs.setdefault(t, []).append(it["rel"])
            fm, _ = parse_frontmatter(md)
            props = ai_audit.local_checks(md, path=it["rel"], fm=fm or {},
                                          known_titles=known,
                                          dead_links=dead_map.get(it["rel"], []),
                                          asset_exists=_asset_resolver(it["p"]))
            asked = False
            if want_ai and not it["blocked"] and ai_batch.needs_ai(props):
                if _budget_state()["exceeded"]:
                    job.note_ai_blocked("本月调用数已达预算帽，之后的篇只跑本地判据")
                else:
                    cand = next((p for p in props if p["kind"] == "should_link"), None)
                    if cand:
                        title = str((fm or {}).get("title") or it["p"].stem)
                        ctx = ai_qa.build_context(md, cand["evidence"][:80], "term", [],
                                                  title, it["rel"])
                        got = _audit_ask(ctx, ai_audit.ai_prompt("should_link", ctx["text"],
                                                                 cand["evidence"]), c)
                        if got is None:
                            return len(props), False, "AI 判断没跑成（本地结果照常入库）"
                        ai_audit.merge_ai(props, got, "should_link", it["rel"])
                        asked = True
            st = _qa_store()
            if st is not None:
                st.audit_upsert(it["rel"], props)
                # 与单篇同一套 upsert + prune：批量跑过的篇，处置状态与重扫都不打折
                st.audit_prune(it["rel"], [p["id"] for p in props])
            return len(props), asked, ""

    def finalize(job):
        """整批跑完后的一次收尾：把攒下的引用集合换算成域级待办。

        全本地（引用集合 − 标题集合），零调用；空白挂在 `@domain:<域>` 这个作用域键下，
        与按篇的条目同住一张派生表但不串台（真实相对路径不会以 @ 开头）。
        """
        if not dom:
            return
        with app_obj.app_context():
            scope_key = ai_audit.domain_scope(dom)
            gaps = ai_audit.coverage_gaps(refs, known, scope_key)
            st = _qa_store()
            if st is not None:
                st.audit_upsert(scope_key, gaps)
                st.audit_prune(scope_key, [g["id"] for g in gaps])

    try:
        job = ai_batch.RUNNER.start(entries, per_doc, scope, finalizer=finalize)
    except ai_batch.BatchBusy as e:
        return jsonify({"ok": False, "error": str(e), "estimate": est}), 409
    return jsonify({"ok": True, "estimate": est, "gaps_scope": ai_audit.domain_scope(dom),
                    "job": job.snapshot()})


@ai_bp.get("/api/ai/batch/status")
def api_ai_batch_status():
    """进度轮询。没有作业也回 200（state=idle），前端不必先探一次"有没有在跑"。"""
    job = ai_batch.RUNNER.current()
    return jsonify({"ok": True, "job": job.snapshot() if job else {"state": "idle",
                                                                   "running": False}})


@ai_bp.post("/api/ai/batch/stop")
def api_ai_batch_stop():
    """请求停止：跑完当前这一篇就走，已入库的建议不回滚（那些结果本来就是有效的）。"""
    job = ai_batch.RUNNER.current()
    if job is None or not job.snapshot()["running"]:
        return jsonify({"ok": True, "stopped": False,
                        "error": "现在没有在跑的批量作业"})
    job.request_stop()
    return jsonify({"ok": True, "stopped": True, "job": job.snapshot()})


def _qa_store():
    return _store()


def _doc_for_explain(data: dict):
    """explain 的入参校验：读盘交给 _read_doc，这里只管选区与档位。

    正文一律服务端现读：前端只交 path + selection，否则"发什么出去"由浏览器说了算，
    域级闸门（不变量 9 ①）就拦不住了。
    """
    selection = " ".join(str(data.get("selection") or "").split())
    mode = str(data.get("mode") or "term").strip()
    if mode not in ai_qa.MODES:
        mode = "term"
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
        # 硬门在后端：绕过前端直接打接口也一样 403（不变量 9 ①），
        # 且**排在存在性检查之前** —— 状态码不能替不出站目录回答"这个路径在不在"。
        return None, (jsonify({"ok": False, "code": "domain_blocked",
                               "error": f"域「{res['domain']}」被分类学标为不出站，"
                                        "AI 无法读取该文档"}), 403)
    try:
        doc = _read_doc(res)
    except FileNotFoundError:
        return None, (jsonify({"ok": False, "error": "文档不存在"}), 404)
    except (ValueError, OSError) as e:
        return None, (jsonify({"ok": False, "error": str(e)[:200]}), 400)
    # 选中超过 80 字 → 语义上就是"问这段"，不是"问这个词"
    if mode == "term" and len(selection) > 80:
        mode = "passage"
    return {"path": doc["rel"], "domain": doc["domain"], "selection": selection,
            "mode": mode, "md": doc["md"], "title": doc["title"],
            "digest": doc["digest"]}, None


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
