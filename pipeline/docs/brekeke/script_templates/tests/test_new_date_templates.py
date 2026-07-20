#!/usr/bin/env python3
"""
closed_period / same_day_check / date_range_check テンプレートの Python オラクル。

各テンプレートの判定ロジックを Python で忠実に写像し、ケース表と照合する。
（modules/ 認定部品の oracle.py と同じ思想。JS 本体の実機挙動は P6 受入で人間が確認する。
 本オラクルは「ロジック仕様の正」を機械検証可能な形で固定するためのもの。）

実行:
  python3 docs/brekeke/script_templates/tests/test_new_date_templates.py
終了コード 0 = 全ケース PASS
"""

import re
import sys
from datetime import date


# ─── closed_period のオラクル ──────────────────────────────────

def closed_period(periods: str, today: date) -> str:
    today_md = today.month * 100 + today.day
    parsed = 0
    for r in periods.split(","):
        r = re.sub(r"\s", "", r)
        if not r:
            continue
        m = re.fullmatch(r"(\d{1,2})-(\d{1,2})\.\.(\d{1,2})-(\d{1,2})", r)
        if not m:
            return "ERROR"
        parsed += 1
        s = int(m.group(1)) * 100 + int(m.group(2))
        e = int(m.group(3)) * 100 + int(m.group(4))
        hit = (s <= today_md <= e) if s <= e else (today_md >= s or today_md <= e)
        if hit:
            return "期間内"
    return "期間外" if parsed else "ERROR"


CLOSED_PERIOD_CASES = [
    # (periods, today, expected)
    ("04-29..05-06", date(2026, 5, 3),  "期間内"),   # GW 中日
    ("04-29..05-06", date(2026, 4, 29), "期間内"),   # 開始境界
    ("04-29..05-06", date(2026, 5, 6),  "期間内"),   # 終了境界
    ("04-29..05-06", date(2026, 4, 28), "期間外"),   # 前日
    ("04-29..05-06", date(2026, 5, 7),  "期間外"),   # 翌日
    ("12-29..01-03", date(2026, 12, 31), "期間内"),  # 年跨ぎ・年末側
    ("12-29..01-03", date(2026, 1, 2),   "期間内"),  # 年跨ぎ・年始側
    ("12-29..01-03", date(2026, 1, 4),   "期間外"),  # 年始明け
    ("12-29..01-03", date(2026, 12, 28), "期間外"),  # 年末前
    ("12-29..01-03,08-13..08-15", date(2026, 8, 14), "期間内"),  # 複数期間の2つ目
    ("12-29..01-03, 08-13..08-15", date(2026, 8, 16), "期間外"), # 空白入り書式
    ("bogus", date(2026, 1, 1), "ERROR"),            # 書式不正
    ("", date(2026, 1, 1), "ERROR"),                 # 空
]


# ─── same_day_check のオラクル ─────────────────────────────────

def parse_ymd(s: str):
    m = re.search(r"(\d{4})\D{0,3}(\d{1,2})\D{0,3}(\d{1,2})", str(s))
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= mo <= 12 and 1 <= d <= 31):
        return None
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def same_day_check(ctx_value: str, days_ahead: int, today: date) -> str:
    appt = parse_ymd(ctx_value)
    if appt is None:
        return "判定不能"
    diff = (appt - today).days
    return "期限内" if diff <= days_ahead else "期限外"


SAME_DAY_CASES = [
    # (context_value, days_ahead, today, expected)
    ("2026-07-12", 0, date(2026, 7, 12), "期限内"),        # 当日
    ("2026-07-13", 0, date(2026, 7, 12), "期限外"),        # 翌日は days_ahead=0 で対象外
    ("2026-07-13", 1, date(2026, 7, 12), "期限内"),        # 当日+翌日モード
    ("2026-07-14", 1, date(2026, 7, 12), "期限外"),        # 明後日
    ("2026-07-10", 0, date(2026, 7, 12), "期限内"),        # 過去日=異常データ→安全側
    ("2026/07/12 00:00", 0, date(2026, 7, 12), "期限内"),  # 保存形式ゆれ（スラッシュ+時刻）
    ("20260712", 0, date(2026, 7, 12), "期限内"),          # 8桁
    ("", 0, date(2026, 7, 12), "判定不能"),                # 未保存
    ("わからない", 0, date(2026, 7, 12), "判定不能"),      # 非日付
    ("2026-13-40", 0, date(2026, 7, 12), "判定不能"),      # 不正日付
]


# ─── date_range_check のオラクル ───────────────────────────────

def date_range_check(ctx_value: str, start_raw: str, end_raw: str) -> str:
    start, end = parse_ymd(start_raw), parse_ymd(end_raw)
    if start is None or end is None or start > end:
        return "ERROR"
    d = parse_ymd(ctx_value)
    if d is None:
        return "判定不能"
    return "範囲内" if start <= d <= end else "範囲外"


DATE_RANGE_CASES = [
    # (context_value, start, end, expected)
    ("2026-09-15", "2026-09-01", "2026-12-26", "範囲内"),
    ("2026-09-01", "2026-09-01", "2026-12-26", "範囲内"),  # 開始境界（含む）
    ("2026-12-26", "2026-09-01", "2026-12-26", "範囲内"),  # 終了境界（含む）
    ("2026-08-31", "2026-09-01", "2026-12-26", "範囲外"),
    ("2026-12-27", "2026-09-01", "2026-12-26", "範囲外"),
    ("20261001",   "2026-09-01", "2026-12-26", "範囲内"),  # 8桁形式
    ("",           "2026-09-01", "2026-12-26", "判定不能"),
    ("希望なし",   "2026-09-01", "2026-12-26", "判定不能"),
    ("2026-10-01", "2026-12-26", "2026-09-01", "ERROR"),   # start > end
    ("2026-10-01", "bogus",      "2026-12-26", "ERROR"),   # 書式不正
]


# ─── 実行 ────────────────────────────────────────────────────────

def run() -> int:
    failed = 0

    for periods, today, exp in CLOSED_PERIOD_CASES:
        got = closed_period(periods, today)
        if got != exp:
            print(f"FAIL closed_period({periods!r}, {today}) = {got!r} != {exp!r}")
            failed += 1

    for ctx, ahead, today, exp in SAME_DAY_CASES:
        got = same_day_check(ctx, ahead, today)
        if got != exp:
            print(f"FAIL same_day_check({ctx!r}, {ahead}, {today}) = {got!r} != {exp!r}")
            failed += 1

    for ctx, s, e, exp in DATE_RANGE_CASES:
        got = date_range_check(ctx, s, e)
        if got != exp:
            print(f"FAIL date_range_check({ctx!r}, {s!r}, {e!r}) = {got!r} != {exp!r}")
            failed += 1

    total = len(CLOSED_PERIOD_CASES) + len(SAME_DAY_CASES) + len(DATE_RANGE_CASES)
    print(f"{total - failed}/{total} PASS" + (f" / {failed} FAIL" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run())
