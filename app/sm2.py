# -*- coding: utf-8 -*-
"""SM-2 间隔重复调度器 —— 纯函数，零 IO，可独立单测。

实现要点（与经典 SuperMemo-2 对齐，便于用户对照任何在线 SM-2 计算器验证）：
    ① q < 3 视为遗忘：reps 归零、interval 归 1、lapses +1，**EF 不变**
       （EF 只在成功回忆时调整；把惩罚写进 EF 会让偶发遗忘长期拖慢整副牌）
    ② q >= 3 视为回忆成功：
       reps 1 → 间隔 1 天，reps 2 → 6 天，之后 = round(前间隔 × EF)
    ③ EF 增量 Δ = 0.1 - (5-q) × (0.08 + (5-q) × 0.02)，并夹在 [1.30, 2.80]
    ④ due_ts 锚定「今天当地 00:00」而非「此刻」：
       下午 23:59 复习与次日上午 00:01 复习不该差出一整天
"""
import time

EF_INIT = 2.50
EF_MIN = 1.30
EF_MAX = 2.80
MASTER_INTERVAL = 21   # 间隔 ≥ 21 天
MASTER_REPS = 3        # 且连续成功 ≥ 3 次 ⇒ 判定「已掌握」
MAX_INTERVAL = 365     # 间隔上限（天），避免长年不露面导致的虚假掌握

Q_MAP = {"again": 0, "hard": 3, "good": 4, "easy": 5}

DAY_SECONDS = 86400

DEFAULT_STATE = {"ef": EF_INIT, "interval": 0, "reps": 0, "lapses": 0}


def day_start(ts: float) -> int:
    """给定时间戳所在**当地日**的 00:00 unix 秒。

    刻意不用 UTC：中国时区 UTC+8 下，UTC 的「今日」比当地早 8 小时，
    夜里复习会被算进第二天，due_in_days 与实际体感错一天。
    """
    lt = time.localtime(ts)
    midnight = time.struct_time((lt.tm_year, lt.tm_mon, lt.tm_mday,
                                 0, 0, 0, lt.tm_wday, lt.tm_yday, -1))
    return int(time.mktime(midnight))


def schedule(st: dict, q: int, now: float) -> dict:
    """按 SM-2 推进一张卡的复习状态。**不改入参**，返回全新 dict。

    Args:
        st: {"ef", "interval", "reps", "lapses"}，缺字段取 DEFAULT_STATE。
        q: 0..5 的回忆质量评分。
        now: 当前 unix 秒（到期日从今天当地 00:00 起算）。

    Returns:
        {"ef","interval","reps","lapses","due_ts","mastered","due_in_days"}
    """
    ef = float(st.get("ef", EF_INIT))
    iv = int(st.get("interval", 0) or 0)
    reps = int(st.get("reps", 0) or 0)
    lapses = int(st.get("lapses", 0) or 0)

    if not isinstance(q, int) or isinstance(q, bool) or not 0 <= q <= 5:
        raise ValueError(f"q must be int in 0..5, got {q!r}")

    if q < 3:
        # 遗忘：回到第 1 天，lapses +1，EF 保持（经典 SM-2 的做法）
        reps, iv, lapses = 0, 1, lapses + 1
    else:
        reps += 1
        iv = 1 if reps == 1 else 6 if reps == 2 else max(1, round(iv * ef))
        delta = 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)
        ef = max(EF_MIN, min(EF_MAX, ef + delta))

    iv = min(iv, MAX_INTERVAL)
    # 「已掌握」口径只有一处实现：is_mastered()。历史上这里内联过同款公式，
    # 于是 is_mastered() 变成无人调用的第二份副本（改一处不会让另一处跟着变）。
    mastered = is_mastered({"interval": iv, "reps": reps})
    return {
        "ef": round(ef, 4),
        "interval": iv,
        "reps": reps,
        "lapses": lapses,
        "due_ts": day_start(now) + iv * DAY_SECONDS,
        "mastered": mastered,
        "due_in_days": iv,
    }


def q_from_label(label: str) -> int:
    """把前端的按钮语义（again/hard/good/easy）映射成 SM-2 的 0..5。"""
    try:
        return Q_MAP[str(label).strip().lower()]
    except KeyError:
        raise ValueError(f"unknown rating label: {label!r}") from None


def is_mastered(state: dict) -> int:
    """独立的「已掌握」判定（DB 侧也靠同一公式派生 mastered 列）。"""
    return 1 if (int(state.get("interval", 0) or 0) >= MASTER_INTERVAL
                 and int(state.get("reps", 0) or 0) >= MASTER_REPS) else 0
