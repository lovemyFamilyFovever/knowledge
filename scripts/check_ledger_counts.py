# -*- coding: utf-8 -*-
"""知库台账对账器：§0 的最新一轮数字必须等于按 §1~§5「状态」列重算的数。

为什么要有它（2026-09-24，台账 §6 第 21 行的教训）：轮次 13 那一行写着"未覆盖 81 → 76"，
但作为计数依据的 §5「状态」列 13 行**一格都没改**（全是 `未测`）—— 那个 76 是手写的，
没有任何一格在表格里背书。台账的规矩本来就是"计数由表格状态列统计"，缺的是**把规矩变成断言**。
本脚本就是那块缺失的机制：改完表格或 §0 后跑一次，对不上就红。

用法：
    python scripts/check_ledger_counts.py            # 对账，不一致 exit 1
    python scripts/check_ledger_counts.py --json     # 机器可读输出
口径（写死在这里，改口径要同步改台账 §0 的注记）：
    · 已覆盖 = 状态列取值 ∈ COVERED；`部分覆盖`/`部分` 一律**不算**已覆盖（保守口径）；
    · `不适用` 的行仍计入总格子（P0 的 199 是这么来的），只从"未覆盖"里排除；
    · 只认"下一行是 |--- 分隔行"的表头，避免把正文里含"状态"二字的数据行当表头。
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

# 控制台编码不许把脚本崩掉：Windows runner 默认 cp1252、本机钩子是 GBK，而报表里全是中文与 §。
# **编不出来的字符替换掉，绝不抛异常**（与 tests 里那套 _safe 同一口径；
# CI 侧另有 job 级 PYTHONIOENCODING=utf-8 兜底 —— 两边都要，别只靠环境）。
try:
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "测试文件" / "覆盖台账.md"

COVERED = {"E2E", "单测", "门禁", "已覆盖", "人工", "基线"}   # 基线 = P5 截图矩阵逐像素锁住交互后状态
NA = "不适用"
SECTIONS = {"1": "端点", "2": "UI 控件", "3": "文件类型", "4": "不变量", "5": "解析入口"}


def _cells(line):
    return [c.strip().strip("*") for c in line.strip().strip("|").split("|")]


def _is_sep(line):
    return bool(re.match(r"^\|[\s:|-]+\|$", line.strip()))


def parse_tables(lines):
    """返回 {节号: Counter(状态取值)}。"""
    out = {}
    sec = None
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^## (\d)\.", line)
        if m:
            sec = m.group(1)
        if (sec in SECTIONS and line.startswith("| ") and _is_sep(lines[i + 1] if i + 1 < len(lines) else "")):
            head = _cells(line)
            if "状态" in head:
                col = head.index("状态")
                cnt = Counter()
                j = i + 2
                while j < len(lines) and lines[j].startswith("|"):
                    cells = _cells(lines[j])
                    if len(cells) > col and cells[0] not in ("", "---"):
                        cnt[cells[col] or "(空)"] += 1
                    j += 1
                out.setdefault(sec, Counter()).update(cnt)
                i = j
                continue
        i += 1
    return out


def parse_latest_round(lines):
    """§0 表格最后一行的 (总格子, 已覆盖, 未覆盖, 轮次)。"""
    rows = []
    for k, l in enumerate(lines):
        if l.startswith("| 轮次 |") and _is_sep(lines[k + 1]):
            start = k + 2
            j = start
            while j < len(lines) and lines[j].startswith("|"):
                rows.append(_cells(lines[j]))
                j += 1
            break
    if not rows:
        raise SystemExit("找不到 §0 轮次表")
    last = rows[-1]
    # 列位不可靠：轮次 13 起的行把"跑的阶段"并进了"模型/会话"那一格，数字格的位置因此左移。
    # 所以不按下标取，而是找**连续三个纯数字格**的那一段（轮次号是孤格，前后是日期与文字，不会连成三个）。
    runs, cur = [], []
    for c in last:
        if re.fullmatch(r"\d{1,4}", c):
            cur.append(int(c))
        else:
            if len(cur) >= 3:
                runs.append(cur)
            cur = []
    if len(cur) >= 3:
        runs.append(cur)
    if not runs:
        raise SystemExit("§0 最后一轮行里找不到『总/已覆盖/未覆盖』三个连续数字格：" + str(last[:7]))
    trip = runs[-1]
    return last[0], trip[0], trip[1], trip[2]


def main():
    as_json = "--json" in sys.argv
    lines = LEDGER.read_text(encoding="utf-8").splitlines()
    tables = parse_tables(lines)
    per = {}
    total = covered = 0
    for sec in sorted(SECTIONS):
        cnt = tables.get(sec, Counter())
        n = sum(cnt.values())
        cov = sum(v for k, v in cnt.items() if k in COVERED)
        na = sum(v for k, v in cnt.items() if k.startswith(NA))
        per[sec] = {"名称": SECTIONS[sec], "行": n, "已覆盖": cov, "不适用": na,
                    "未覆盖": n - cov - na, "取值": dict(cnt)}
        total += n
        covered += cov
    uncov = total - covered
    rnd, r_total, r_cov, r_uncov = parse_latest_round(lines)
    ok = (total == r_total and covered == r_cov and uncov == r_uncov)

    if as_json:
        print(json.dumps({"ok": ok, "computed": {"total": total, "covered": covered,
                                                 "uncovered": uncov},
                          "ledger_round": {"round": rnd, "total": r_total, "covered": r_cov,
                                           "uncovered": r_uncov},
                          "per_section": per}, ensure_ascii=False, indent=1))
        return 0 if ok else 1

    print(f"按 §1~§5 状态列重算：总 {total} / 已覆盖 {covered} / 未覆盖 {uncov}")
    for sec in sorted(SECTIONS):
        d = per[sec]
        print(f"  §{sec} {d['名称']:8s} 行={d['行']:3d} 已覆盖={d['已覆盖']:3d} "
              f"不适用={d['不适用']:3d} 未覆盖={d['未覆盖']:3d}  取值={sorted(d['取值'].items(), key=lambda kv: -kv[1])}")
    print(f"§0 第 {rnd} 轮写的是：总 {r_total} / 已覆盖 {r_cov} / 未覆盖 {r_uncov}")
    if ok:
        print("OK 账本与表格一致")
        return 0
    print("MISMATCH 台账 §0 的数字与表格状态列对不上（要么改表、要么改 §0，别只改一处）")
    for label, a, b in (("总格子", total, r_total), ("已覆盖", covered, r_cov), ("未覆盖", uncov, r_uncov)):
        if a != b:
            print(f"  {label}: 表格算出 {a}，§0 写着 {b}，差 {a - b}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
