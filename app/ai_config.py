# -*- coding: utf-8 -*-
"""AI 出站配置层（切片 1）—— 设计见 docs/spec-ai-assistant.md 第 3 节。

存哪、谁优先：
    环境变量 KB_AI_* > 仓库根 .ai-config.json（gitignored） > 代码缺省
环境变量仍是 start.bat / _local_env.bat 的注入通道（不改那条链），只是不再让
程序去改写 bat —— bat 是执行入口不是配置存储，且 AGENTS 已把它划为全英文 + 编码坑区。
UI 上如实显示每个字段当前的**生效来源**（env / file / default），避免"界面改了没生效"。

三条红线（对应 AGENTS 不变量 9）：
    ① 完整 key 永不离开本模块 —— 对外只给 mask_key() 的尾 4 位；
    ② base_url 过 validate_base_url()：只收 http(s)，本机/内网地址要显式 allow_local；
    ③ 本模块的读写只落在仓库根的单个 JSON 文件，不碰 content/，不碰 indexes/。
"""
import json
import os
import re
from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urlparse

CONFIG_FILENAME = ".ai-config.json"

DEFAULTS = {
    "base_url": "https://api.xiaomimimo.com/v1",
    "model": "mimo-v2.5",
    "timeout_s": 30,
    "allow_local": False,
    "monthly_budget_calls": 300,
    "price_in_per_1k": 0.0,
    "price_out_per_1k": 0.0,
}

# 字段 → 环境变量名（只有这三项有 env 通道；其余字段只认文件/缺省）
ENV_KEYS = {"base_url": "KB_AI_BASE_URL", "api_key": "KB_AI_API_KEY", "model": "KB_AI_MODEL"}

_INT_FIELDS = {"timeout_s", "monthly_budget_calls"}
_FLOAT_FIELDS = {"price_in_per_1k", "price_out_per_1k"}
_BOOL_FIELDS = {"allow_local"}
_STR_FIELDS = {"base_url", "model", "api_key"}

_URL_RE = re.compile(r"^https?://[^\s]+$", re.I)
_LOCAL_HOSTS = {"localhost", "localhost.localdomain"}


class ConfigError(ValueError):
    """配置校验失败：消息面向用户，不得包含绝对路径。"""


def config_path(root: Path | str) -> Path:
    return Path(root) / CONFIG_FILENAME


def mask_key(key: str) -> str:
    """脱敏表示：只露尾 4 位。空串 → 空串。"""
    k = (key or "").strip()
    if not k:
        return ""
    if len(k) <= 4:
        return "*" * len(k)
    return "*" * 6 + k[-4:]


def _coerce(field: str, value):
    """按类型收口字段值；收不拢就抛 ConfigError（宁可报错也不静默用错值）。"""
    if field in _BOOL_FIELDS:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.strip().lower() in ("1", "true", "yes", "on"):
                return True
            if value.strip().lower() in ("0", "false", "no", "off", ""):
                return False
        raise ConfigError(f"{field} 需要布尔值")
    if field in _INT_FIELDS:
        try:
            n = int(float(str(value).strip()))
        except (TypeError, ValueError):
            raise ConfigError(f"{field} 需要整数") from None
        return n
    if field in _FLOAT_FIELDS:
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            raise ConfigError(f"{field} 需要数字") from None
    return str(value if value is not None else "").strip()


def _coerce_range(field: str, value):
    v = _coerce(field, value)
    if field == "timeout_s":
        v = max(1, min(int(v), 600))
    if field == "monthly_budget_calls":
        v = max(0, int(v))
    if field in _FLOAT_FIELDS:
        v = max(0.0, float(v))
    return v


def read_file_config(root: Path | str) -> dict:
    """读 .ai-config.json；文件不在/读不懂一律当作未配置（只读接口不炸 500）。"""
    p = config_path(root)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def effective(root: Path | str) -> dict:
    """合并三层后的生效配置 + 每个字段的来源。

    返回 {"values": {...含 api_key...}, "sources": {field: "env"|"file"|"default"}}。
    values["api_key"] 是全仓唯一出现明文 key 的地方，调用方不得回显。
    """
    file_cfg = read_file_config(root)
    values: dict = {}
    sources: dict = {}
    for field, dv in DEFAULTS.items():
        env_name = ENV_KEYS.get(field)
        if env_name and os.environ.get(env_name, "").strip():
            values[field] = _coerce_range(field, os.environ[env_name])
            sources[field] = "env"
        elif field in file_cfg and str(file_cfg.get(field)).strip() != "":
            values[field] = _coerce_range(field, file_cfg[field])
            sources[field] = "file"
        else:
            values[field] = dv
            sources[field] = "default"
    key = ""
    if ENV_KEYS["api_key"] and os.environ.get(ENV_KEYS["api_key"], "").strip():
        key = os.environ[ENV_KEYS["api_key"]].strip()
        sources["api_key"] = "env"
    elif str(file_cfg.get("api_key") or "").strip():
        key = str(file_cfg["api_key"]).strip()
        sources["api_key"] = "file"
    else:
        sources["api_key"] = "default"
    values["api_key"] = key
    return {"values": values, "sources": sources}


def public_config(root: Path | str) -> dict:
    """给前端的脱敏视图 —— 永不包含明文 key。"""
    eff = effective(root)
    v, s = eff["values"], eff["sources"]
    blocked = sorted(egress_blocked_domains(Path(root) / "content"))
    return {
        "ok": True,
        "base_url": v["base_url"],
        "model": v["model"],
        "timeout_s": v["timeout_s"],
        "allow_local": v["allow_local"],
        "monthly_budget_calls": v["monthly_budget_calls"],
        "price_in_per_1k": v["price_in_per_1k"],
        "price_out_per_1k": v["price_out_per_1k"],
        "key_masked": mask_key(v["api_key"]),
        "key_present": bool(v["api_key"]),
        "sources": s,
        "file_exists": config_path(root).is_file(),
        "config_file": CONFIG_FILENAME,
        # 出站黑名单（域 id）：前端据此藏入口，后端每个出站端点再各自硬拦一次
        "egress_blocked_domains": blocked,
    }


def coerce(field: str, value):
    """对外暴露的按类型收口（/api/ai/test 要在不落盘的前提下试跑表单值）。"""
    return _coerce_range(field, value)


def validate_base_url(url: str, allow_local: bool = False) -> str:
    """SSRF 底线：只收 http(s)，主机要有解析面，本机/内网须显式放行。返回规范化 URL。"""
    u = (url or "").strip().rstrip("/")
    if not u:
        raise ConfigError("base_url 不能为空")
    if not _URL_RE.match(u):
        raise ConfigError("base_url 必须是 http(s) 地址，且不含空格")
    parsed = urlparse(u)
    host = (parsed.hostname or "").strip().lower()
    if not host:
        raise ConfigError("base_url 缺少主机名")
    if host in _LOCAL_HOSTS or _is_local_ip(host):
        if not allow_local:
            raise ConfigError("本机/内网地址需要先在设置里勾选「允许本机服务」")
    return u


def _is_local_ip(host: str) -> bool:
    try:
        ip = ip_address(host)
    except ValueError:
        return False
    return (ip.is_loopback or ip.is_private or ip.is_link_local
            or ip.is_multicast or ip.is_reserved or ip.is_unspecified)


def save_config(root: Path | str, patch: dict) -> dict:
    """把用户提交的补丁写进 .ai-config.json。

    语义（前端按此设计表单）：
      · api_key 缺省或空串 = 保持文件里已有值；显式 null = 清除。
      · 只写白名单字段，别的一律丢弃 —— 防前端把 key_masked 之类的展示字段回灌进文件。
    返回写入后的公开视图（脱敏）。
    """
    if not isinstance(patch, dict):
        raise ConfigError("请求体必须是 JSON 对象")
    p = config_path(root)
    old = read_file_config(root)
    merged = {k: v for k, v in old.items() if k in _STR_FIELDS | _INT_FIELDS | _FLOAT_FIELDS | _BOOL_FIELDS}

    if "api_key" in patch:
        raw_key = patch["api_key"]
        if raw_key is None:
            merged.pop("api_key", None)
        else:
            k = str(raw_key).strip()
            if k:
                merged["api_key"] = k

    for field in ("base_url", "model"):
        if field in patch and str(patch.get(field) or "").strip():
            merged[field] = _coerce_range(field, patch[field])
    for field in _INT_FIELDS | _FLOAT_FIELDS | _BOOL_FIELDS:
        if field in patch and patch[field] is not None:
            merged[field] = _coerce_range(field, patch[field])

    merged["base_url"] = validate_base_url(merged.get("base_url")
                                           or effective(root)["values"]["base_url"],
                                           bool(merged.get("allow_local", False)))
    p.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass  # 非 POSIX 语义下尽力而为，不影响保存成功
    return public_config(root)


def clear_config(root: Path | str) -> bool:
    """删除配置文件（只删这一个文件，不碰别的）。"""
    p = config_path(root)
    try:
        p.unlink()
        return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def egress_blocked_domains(content: Path | str) -> set:
    """域级出站黑名单（不变量 9 ①）—— 权威是 taxonomy.json 的 "ai": false，
    代码里的 store.AI_NEVER_EGRESS 是不可配置的安全下界，两者取并集。

    读不到分类学时也必须返回**非空**（下界集合），绝不能因为 JSON 损坏就放行。
    """
    from app.store import AI_NEVER_EGRESS, load_taxonomy  # 延迟导入：避免 store 侧循环
    try:
        tax = load_taxonomy(Path(content))
    except Exception:
        return set(AI_NEVER_EGRESS)
    return set(tax.get("ai_hidden") or set()) | set(AI_NEVER_EGRESS)


def domain_allows_egress(content: Path | str, domain: str) -> bool:
    """该域的一篇正文能否发往外部 AI。空域名按"不允许"处理（宁可拒）。"""
    d = (domain or "").strip()
    if not d:
        return False
    return d not in egress_blocked_domains(content)
