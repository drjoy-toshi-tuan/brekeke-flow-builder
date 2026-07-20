#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_oracle.py — reservation_date_classifier オラクルの単体テスト

2 系統:
  [A] 日付非依存ケース  … 期待値 = 設計意図（= JS 忠実挙動と一致）。これが P6 bivr に焼く対象。
  [B] 日付依存ケース    … today=2026-06-12(金) 固定。期待値は独立計算（datetime / JS式の再実装）で算出。
                          現行 JS の挙動をパリティ確認する（= bivr の期待値源としての信頼性確保）。

実行: python3 modules/reservation_date_classifier/test_oracle.py
"""

import sys
import os
import calendar
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle import classify, js_getday  # noqa: E402

FIXED_TODAY = date(2026, 6, 12)  # 金曜
DAY_MAP = {"日": 0, "月": 1, "火": 2, "水": 3, "木": 4, "金": 5, "土": 6}


def fmt(d):
    return "%04d-%02d-%02d 00:00" % (d.year, d.month, d.day)


# ----------------------------------------------------------------------------
# [A] 日付非依存ケース（P6 bivr へ焼く対象。設計意図 == JS 挙動）
# ----------------------------------------------------------------------------
INDEPENDENT_CASES = [
    # id, input, expected
    ("abs01", "2030年7月15日", "2030-07-15 00:00"),
    ("abs02", "2030年12月31日", "2030-12-31 00:00"),
    ("abs03", "令和12年3月3日", "2030-03-03 00:00"),        # 令和12 = 2030
    ("dtmf8", "20300715", "2030-07-15 00:00"),             # 8桁 DTMF 絶対日付
    ("dtmf8p", "20200101", "NO_RESULT"),                   # 8桁 過去日(DTMF) → NO_RESULT
    ("inv01", "13月5日", "NO_RESULT"),                      # 無効月
    ("inv02", "2030年2月30日", "NO_RESULT"),                # 無効日(2/30)
    ("inv03", "2030年4月31日", "NO_RESULT"),                # 無効日(4/31)
    ("unk01", "わからない", "不明"),
    ("unk02", "わかりません", "不明"),
    ("unk03", "未定", "不明"),
    ("unk04", "忘れました", "不明"),
    ("unk05", "覚えていない", "不明"),
    ("unk06", "上旬", "不明"),                              # 上旬/中旬/下旬 は不明扱い
    ("unk07", "中旬", "不明"),
    ("unk08", "下旬", "不明"),
    ("nr01", "", "NO_RESULT"),
    ("nr02", "予約したい", "NO_RESULT"),
    ("nr03", "こんにちは", "NO_RESULT"),
    ("nr04", "あのー", "NO_RESULT"),
    # --- engine v2: has_月 回収（Rule A/B・西暦年あり=today 非依存）+ Mガード ---
    ("hasm_yr", "2030年7月20", "2030-07-20 00:00"),          # Rule B: N月M→N月M日
    ("hasm_ten_yr", "2030年6月3十", "2030-06-30 00:00"),     # Rule A: 3十→30 → Rule B
    ("hasm_punct_yr", "2030年7月20。", "2030-07-20 00:00"),   # 末尾句点でも 日 補完
    ("hasm_guard_year", "1月20年", "NO_RESULT"),             # Mガード: M月D年 化けは NO_RESULT
    ("hasm_guard_overflow", "1月100", "NO_RESULT"),          # Mガード: 3桁化けは NO_RESULT
    # --- engine v2: 事故① 曖昧な時期表現→不明（NO_RESULT ループ回避・上旬/中旬/下旬 と統一）---
    ("jiko1_shojun", "6月初旬", "不明"),                     # 初旬 を UNKNOWN_RE へ追加
    ("jiko1_gurai", "5月ぐらい", "不明"),                    # VAGUE_PERIOD 遅延フォールバック
    ("jiko1_dokoka", "5月のどこか", "不明"),
    ("jiko1_hajime", "5月初め頃", "不明"),
]

# ----------------------------------------------------------------------------
# [B] 日付依存ケース（today=2026-06-12 固定。期待値は独立計算）
# ----------------------------------------------------------------------------
def _next_week_dow(today, dow_ja):
    # FIX(2026-06-12): 暦週・月曜始まり。今週月曜 + 7 + 目標曜日(月曜起点)。例: 金曜の来週月曜=翌週15日
    gd = js_getday(today)
    monday_off = (gd + 6) % 7
    this_monday = today + timedelta(days=-monday_off)
    return this_monday + timedelta(days=7 + (DAY_MAP[dow_ja] + 6) % 7)


def _this_week_dow(today, dow_ja):
    # FIX(2026-06-12): 暦週・月曜始まり（今週の実日。過去でもその日）。例: 金曜の今週月曜=8日
    gd = js_getday(today)
    monday_off = (gd + 6) % 7
    this_monday = today + timedelta(days=-monday_off)
    return this_monday + timedelta(days=(DAY_MAP[dow_ja] + 6) % 7)


def _bare_dow(today, dow_ja):
    # 裸の曜日（今週/来週の語なし）= 直近の次の出現（今日と同曜日なら +7）
    gd = js_getday(today)
    diff = (DAY_MAP[dow_ja] - gd + 7) % 7
    return today + timedelta(days=(7 if diff == 0 else diff))


def _day_only_expected(only_d, today):
    """JS の「日のみ」分岐: 当月→過去なら翌月送り、その後 validateAndOutput。"""
    temp = date(today.year, today.month, only_d)
    if temp < today:
        if today.month == 12:
            temp = date(today.year + 1, 1, only_d)
        else:
            temp = date(today.year, today.month + 1, only_d)
    return _validate_expected(temp.year, temp.month, temp.day, today)


def _validate_expected(y, m, d, today, is_dtmf=False):
    """JS validateAndOutput の期待値を独立に再現（妥当性 + 過去日→翌年）。"""
    try:
        cd = date(y, m, d)
    except ValueError:
        return "NO_RESULT"
    if cd >= today:
        return fmt(cd)
    if is_dtmf:
        return "NO_RESULT"
    try:
        ny = date(y + 1, m, d)
        return fmt(ny)
    except ValueError:
        return "NO_RESULT"   # runCorrection は実質到達不能（下記 NOTE 参照）


def build_dependent_cases(today):
    last_this = calendar.monthrange(today.year, today.month)[1]
    nm_year = today.year + (1 if today.month == 12 else 0)
    nm_month = 1 if today.month == 12 else today.month + 1
    last_next = calendar.monthrange(nm_year, nm_month)[1]

    cases = [
        ("rel_today", "今日", fmt(today)),
        ("rel_honjitsu", "本日", fmt(today)),
        ("rel_ashita", "明日", fmt(today + timedelta(1))),
        ("rel_ashita_h", "あした", fmt(today + timedelta(1))),
        ("rel_asatte", "明後日", fmt(today + timedelta(2))),
        # FIX(2026-06-12): しあさって は +3（明々後日 を あさって より先に判定するよう修正済）
        ("rel_shiasatte", "しあさって", fmt(today + timedelta(3))),
        ("rel_3go", "3日後", fmt(today + timedelta(3))),
        ("rel_10go", "10日後", fmt(today + timedelta(10))),
        # 今月N日（未来=literal / 過去でも今年=literal）
        ("rel_imN", "今月20日", fmt(date(today.year, today.month, 20))),
        ("rel_imN_past", "今月5日", fmt(date(today.year, today.month, 5))),
        # 来月N日
        ("rel_nmN", "来月3日", fmt(date(nm_year, nm_month, 3))),
        # 月末系
        ("rel_getumatu", "今月末", _validate_expected(today.year, today.month, last_this, today)),
        ("rel_imgetumatu", "今月末", _validate_expected(today.year, today.month, last_this, today)),
        ("rel_nmgetumatu", "来月末", _validate_expected(nm_year, nm_month, last_next, today)),
        # 来週/今週=暦週・月曜始まり（FIX 2026-06-12）。裸曜日=直近の次の出現。
        ("rel_raishu_mon", "来週月曜", fmt(_next_week_dow(today, "月"))),   # 金曜→翌週月曜=6/15
        ("rel_konshu_mon", "今週月曜", fmt(_this_week_dow(today, "月"))),   # 金曜→今週月曜=6/8(過去でも今年)
        ("rel_konshu_wed", "今週水曜日", fmt(_this_week_dow(today, "水"))), # 6/10
        ("rel_bare_kin", "金曜日", fmt(_bare_dow(today, "金"))),           # 裸=直近の次=6/19
        # 裸の月日（過去なら翌年送り）
        ("md_future", "7月15日", _validate_expected(today.year, 7, 15, today)),
        ("md_past", "1月5日", _validate_expected(today.year, 1, 5, today)),
        ("md_kanji", "七月十五日", _validate_expected(today.year, 7, 15, today)),
        # 4桁 DTMF（MMDD・年送り）
        ("dtmf4_future", "0715", _validate_expected(today.year, 7, 15, today, is_dtmf=False)),  # 4桁は年送り済→未来
        ("dtmf4_roll", "0105", fmt(date(today.year + 1, 1, 5))),
        # STT 補正の誤爆確認（通知→1日 / 発火→20日）
        ("stt_tsuchi", "通知", _day_only_expected(1, today)),   # 通知→1日→「日のみ」過去は翌月送り
        ("stt_hakka", "発火", _validate_expected(today.year, today.month, 20, today)),   # 発火→20日
        # 助詞ゆれ・スラッシュ・元号
        ("joshi", "7月の15日", _validate_expected(today.year, 7, 15, today)),
        ("slash", "7/15", _validate_expected(today.year, 7, 15, today)),
        ("reiwa_rel", "令和8年1月5日", _validate_expected(2026, 1, 5, today)),  # 令和8=2026, 1/5 過去→2027
        # --- engine v2: has_月 回収（today 依存・today=2026-06-12）---
        ("hasm_md_future", "7月20", _validate_expected(today.year, 7, 20, today)),   # Rule B・未来=そのまま
        ("hasm_md_past", "1月27", _validate_expected(today.year, 1, 27, today)),     # Rule B・過去→翌年送り
        ("hasm_ten", "6月3十", _validate_expected(today.year, 6, 30, today)),        # Rule A(3十→30)・未来
        ("hasm_nod", "5月7のか", _validate_expected(today.year, 5, 7, today)),       # 末尾「のか」でも補完・過去→翌年
        ("hasm_selfcorr", "3月5ではなく4月10日", _validate_expected(today.year, 4, 10, today)),  # GUARD: 完成日4月10日を採用（破棄側3月5を予約しない）
        ("jiko1_guard", "6月3日ぐらい", _validate_expected(today.year, 6, 3, today)),  # 具体日付き修飾は md が先に解決→不明化しない
    ]
    return cases


def run():
    fails = []
    total = 0

    # [A]
    for cid, inp, exp in INDEPENDENT_CASES:
        total += 1
        got = classify(inp, FIXED_TODAY)
        if got != exp:
            fails.append((cid, repr(inp), exp, got))

    # [B]
    for cid, inp, exp in build_dependent_cases(FIXED_TODAY):
        total += 1
        got = classify(inp, FIXED_TODAY)
        if got != exp:
            fails.append((cid, repr(inp), exp, got))

    for cid, inp, exp, got in fails:
        print("FAIL %-14s in=%-16s exp=%-18s got=%s" % (cid, inp, exp, got))

    print("PASS %d/%d" % (total - len(fails), total))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(run())
