# -*- coding: utf-8 -*-
"""AI 问答（中期功能 #1）：OpenAI 兼容 chat 客户端 + RAG 检索增强回答。

端点约定（环境变量可覆盖）：
  KB_AI_BASE_URL  默认 https://api.agnes-ai.cn/v1（AgnesAI，OpenAI 兼容）
  KB_AI_API_KEY   Bearer 令牌（key 走环境变量 / start.bat，不进 git）
  KB_AI_MODEL     默认 gpt-4o-mini（换成 AgnesAI 支持的任意 chat 模型名即可）

只依赖标准库 urllib —— 与 AGENTS「任意 Python 可启动」兼容。
key 未配置时 /api/ask 返回 not_configured(503)，前端优雅降级；
RAG 组件缺失时自动跳过检索（纯 chat 仍可用）。
"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

ai_bp = Blueprint("ai", __name__)


def _cfg() -> dict:
    return {
        "base": os.environ.get("KB_AI_BASE_URL", "https://api.agnes-ai.cn/v1").rstrip("/"),
        "key": os.environ.get("KB_AI_API_KEY", ""),
        "model": os.environ.get("KB_AI_MODEL", "gpt-4o-mini"),
    }


def ai_available() -> bool:
    return bool(_cfg()["key"])


def _chat(messages: list[dict], timeout: int = 60) -> str:
    c = _cfg()
    body = json.dumps({"model": c["model"], "messages": messages, "temperature": 0.3}).encode("utf-8")
    req = urllib.request.Request(
        c["base"] + "/chat/completions", data=body, method="POST",
        headers={"Authorization": "Bearer " + c["key"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()


SYSTEM_PROMPT = (
    "你是「知库」的个人知识库助手。仅依据提供的语料片段回答问题；"
    "语料不足以回答时明确说明。回答使用简体中文，简洁、结构化，"
    "并在结尾列出引用的文档路径（[来源] 前缀）。"
)


@ai_bp.post("/api/ask")
def api_ask():
    """RAG 问答：语义检索 Top-K 语料 → 拼 prompt → LLM 生成 → 带引用返回。"""
    data = request.get_json(force=True, silent=True) or {}
    q = str(data.get("q") or "").strip()
    if not q:
        return jsonify({"ok": False, "error": "问题不能为空"}), 400
    if not ai_available():
        return jsonify({"ok": False, "error": "not_configured",
                        "hint": "未配置 KB_AI_API_KEY 环境变量"}), 503

    # 复用 routes_rag 的 KB_HOOKS 单例（rag 可选依赖缺失 → hits 留空，纯 chat 兜底）
    hits = []
    hooks = current_app.config.get("KB_HOOKS") or {}
    get_rag = hooks.get("get_rag")
    if get_rag and hooks.get("query_rag"):
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
    try:
        answer = _chat(messages)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:200]
        return jsonify({"ok": False, "error": f"AI 服务返回 {e.code}", "detail": detail}), 502
    except Exception as e:  # 网络等
        return jsonify({"ok": False, "error": f"AI 服务不可达：{e}"}), 502

    sources = [{"path": h.get("file", ""), "url": h.get("url"),
                "score": round(h.get("score", 0) or 0, 4)} for h in hits]
    return jsonify({"ok": True, "answer": answer, "sources": sources, "model": _cfg()["model"]})


@ai_bp.get("/api/ask/status")
def api_ask_status():
    return jsonify({"ok": True, "available": ai_available(),
                    "base": _cfg()["base"], "model": _cfg()["model"]})


def register(app):
    app.register_blueprint(ai_bp)
