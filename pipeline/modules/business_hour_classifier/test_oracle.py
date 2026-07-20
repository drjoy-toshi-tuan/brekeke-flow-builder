"""BusinessHour Classifier 受け入れケース.

Pattern 6 ([[project_pattern_6_test_flow]]) で実機検証する前にロジックを
ローカルで全分岐通す。Brekeke 実機との突合は別 .bivr で行う。
"""
from __future__ import annotations

import datetime as _dt

from oracle import Params, classify

# 2026-2027 年の祝日 (内閣府 syukujitsu.csv 由来) を mock。テスト中は HTTP を叩かない。
# 本番では Brekeke Note `drjoy.holidays` から fetch_jp_holidays.py で生成した行が読まれる。
HOLIDAYS_2026 = {
    # 2026
    "2026-01-01", "2026-01-12", "2026-02-11", "2026-02-23", "2026-03-20",
    "2026-04-29", "2026-05-03", "2026-05-04", "2026-05-05", "2026-05-06",
    "2026-07-20", "2026-08-11", "2026-09-21", "2026-09-22", "2026-09-23",
    "2026-10-12", "2026-11-03", "2026-11-23",
    # 2027 (翌年予約対応、内閣府 CSV から)
    "2027-01-01", "2027-01-11", "2027-02-11", "2027-02-23", "2027-03-21",
    "2027-03-22", "2027-04-29", "2027-05-03", "2027-05-04", "2027-05-05",
    "2027-07-19", "2027-08-11", "2027-09-20", "2027-09-23", "2027-10-11",
    "2027-11-03", "2027-11-23",
}

# 過去日ガード (1.5) を決定論で回すための基準「今日」。
# レガシー BH-01〜25 は reference_date 未指定 (= "now") なので、ここで注入する now が基準になる。
# 全レガシーケースの target (最古 2026-01-01) より前の日付に置くことで、過去日ガードが
# 一切発火せず従来の期待値が保たれる。過去日ケース (BH-26〜) は各自 reference_date を上書きする。
TEST_NOW = _dt.datetime(2026, 1, 1, 0, 0, 0)

CASES = [
    # (id, params_override, expected, comment)
    ("BH-01-平日営業中",
        {"target_datetime": "2026-06-02 10:00:00"}, "営業中",
        "火曜 10:00 — 既定スケジュール"),
    ("BH-02-平日朝の前",
        {"target_datetime": "2026-06-02 08:30:00"}, "営業時間外",
        "火曜 8:30 — 開店前"),
    ("BH-03-平日夜の後",
        {"target_datetime": "2026-06-02 19:30:00"}, "営業時間外",
        "火曜 19:30 — 閉店後"),
    ("BH-04-平日開店ジャスト",
        {"target_datetime": "2026-06-02 09:00:00"}, "営業中",
        "火曜 9:00:00 — 境界 (open は含む)"),
    ("BH-05-平日閉店ジャスト",
        {"target_datetime": "2026-06-02 18:00:00"}, "営業時間外",
        "火曜 18:00:00 — 境界 (close は含まない)"),
    ("BH-06-土曜",
        {"target_datetime": "2026-06-06 10:00:00"}, "定休日",
        "土曜 — 既定で closed"),
    ("BH-07-日曜",
        {"target_datetime": "2026-06-07 10:00:00"}, "定休日",
        "日曜 — 既定で closed"),
    ("BH-08-元日",
        {"target_datetime": "2026-01-01 10:00:00"}, "祝日",
        "元日 木曜 — 祝日扱い"),
    ("BH-09-こどもの日",
        {"target_datetime": "2026-05-05 10:00:00"}, "祝日",
        "こどもの日 火曜 — 平日祝日"),
    ("BH-10-年末12-31",
        {"target_datetime": "2026-12-31 10:00:00"}, "固定休",
        "12/31 木曜 — 既定 closed_dates ヒット"),
    ("BH-11-年始01-02",
        {"target_datetime": "2026-01-02 10:00:00"}, "固定休",
        "1/2 金曜 — 既定 closed_dates ヒット"),
    ("BH-12-祝日open設定で平日扱い",
        {"target_datetime": "2026-05-05 10:00:00",
         "national_holiday": "open"}, "営業中",
        "ER対応病院想定 — 祝日でも稼働"),
    ("BH-13-水曜午後休 1100",
        {"target_datetime": "2026-06-03 11:00:00",
         "weekday_schedule": "mon=09:00-18:00,tue=09:00-18:00,wed=09:00-12:00,thu=09:00-18:00,fri=09:00-18:00,sat=closed,sun=closed"},
        "営業中",
        "水曜 11:00 — 午前は営業"),
    ("BH-14-水曜午後休 1300",
        {"target_datetime": "2026-06-03 13:00:00",
         "weekday_schedule": "mon=09:00-18:00,tue=09:00-18:00,wed=09:00-12:00,thu=09:00-18:00,fri=09:00-18:00,sat=closed,sun=closed"},
        "営業時間外",
        "水曜 13:00 — 午後休"),
    ("BH-15-24h無休病院",
        {"target_datetime": "2026-06-06 23:30:00",
         "weekday_schedule": "mon=00:00-23:59,tue=00:00-23:59,wed=00:00-23:59,thu=00:00-23:59,fri=00:00-23:59,sat=00:00-23:59,sun=00:00-23:59",
         "closed_dates": "",
         "national_holiday": "open"},
        "営業中",
        "ER 24/7 — 土曜深夜も営業中"),
    ("BH-16-不正target",
        {"target_datetime": "2026/06/02 10:00"}, "ERROR",
        "スラッシュ区切り — fmt 不一致"),
    ("BH-17-不正schedule",
        {"target_datetime": "2026-06-02 10:00:00",
         "weekday_schedule": "mon=09:00-18:00,tue=invalid_range,wed=09:00-18:00,thu=09:00-18:00,fri=09:00-18:00,sat=closed,sun=closed"},
        "ERROR",
        "対象曜日 tue のエントリが壊れている"),
    ("BH-17b-未指定曜日は定休扱い",
        {"target_datetime": "2026-06-02 10:00:00",
         "weekday_schedule": "mon=09:00-18:00"}, "定休日",
        "tue が未指定 — implicit closed"),
    ("BH-18-振替休日",
        {"target_datetime": "2026-05-06 10:00:00"}, "祝日",
        "5/6 振替休日 水曜 — API ヒット"),
    ("BH-19-平日closed設定",
        {"target_datetime": "2026-06-03 10:00:00",
         "weekday_schedule": "mon=09:00-18:00,tue=09:00-18:00,wed=closed,thu=09:00-18:00,fri=09:00-18:00,sat=closed,sun=closed"},
        "定休日",
        "水曜全休クリニック"),
    ("BH-20-土曜午前のみ営業",
        {"target_datetime": "2026-06-06 11:00:00",
         "weekday_schedule": "mon=09:00-18:00,tue=09:00-18:00,wed=09:00-18:00,thu=09:00-18:00,fri=09:00-18:00,sat=09:00-13:00,sun=closed"},
        "営業中",
        "土曜午前のみ営業の施設"),
    # --- Date-only 入力 (saveContext2DB DATE 型 / yyyy-MM-dd リテラル) の判定 ---
    # 時刻 00:00 は「日付のみ」扱いで時刻範囲チェックをスキップし営業日扱い
    ("BH-21-予約日_平日_DATE",
        {"target_datetime": "2027-02-01 00:00:00"}, "営業中",
        "DATE 型: 月曜 (営業日) → 時刻 0:00 でも営業中扱い"),
    ("BH-22-予約日_土曜_DATE",
        {"target_datetime": "2027-02-06 00:00:00"}, "定休日",
        "DATE 型: 土曜 → 定休日 (時刻スキップでも曜日判定は有効)"),
    ("BH-23-予約日_祝日_DATE",
        {"target_datetime": "2027-01-01 00:00:00"}, "祝日",
        "DATE 型: 元日 → 祝日 (時刻スキップでも祝日判定は有効)"),
    ("BH-24-予約日_固定休_DATE",
        {"target_datetime": "2026-12-31 00:00:00"}, "固定休",
        "DATE 型: 12/31 → 固定休 (時刻スキップでも固定休判定は有効)"),
    ("BH-25-予約日_リテラル_yyyy-MM-dd",
        {"target_datetime": "2027-02-01"}, "営業中",
        "yyyy-MM-dd リテラル (時刻省略) → DATE 同様、月曜は営業中"),
    # --- 過去日ガード (予約受付特性: 過去日は一律 営業時間外) ---
    # 基準「今日」= 2026-06-04 (木) 15:00 を reference_date で注入。日付単位比較。
    ("BH-26-過去日_昨日_平日営業内",
        {"target_datetime": "2026-06-03 10:00:00", "reference_date": "2026-06-04 15:00:00"}, "営業時間外",
        "昨日 (水) 営業時間内でも過去日 → 営業時間外 (修正前は誤って営業中)"),
    ("BH-27-過去日_昨日_DATE",
        {"target_datetime": "2026-06-03", "reference_date": "2026-06-04 15:00:00"}, "営業時間外",
        "昨日 date-only (00:00) でも過去日ガードが date-only 判定より優先"),
    ("BH-28-当日_過ぎた朝枠",
        {"target_datetime": "2026-06-04 10:00:00", "reference_date": "2026-06-04 15:00:00"}, "営業中",
        "今日 (木) の既に過ぎた朝枠 — 日付単位なので過去扱いせず通常判定 → 営業中"),
    ("BH-29-当日_DATE",
        {"target_datetime": "2026-06-04", "reference_date": "2026-06-04 15:00:00"}, "営業中",
        "今日 date-only — 過去でなく当日 → 営業中"),
    ("BH-30-翌日_平日営業内",
        {"target_datetime": "2026-06-05 10:00:00", "reference_date": "2026-06-04 15:00:00"}, "営業中",
        "明日 (金) 営業時間内 — 未来は通常判定 → 営業中"),
    ("BH-31-明後日_土曜",
        {"target_datetime": "2026-06-06 10:00:00", "reference_date": "2026-06-04 15:00:00"}, "定休日",
        "明後日 (土) — 未来の定休はそのまま定休日"),
    ("BH-32-過去日は固定休より優先",
        {"target_datetime": "2026-01-02 10:00:00", "reference_date": "2026-06-04 15:00:00"}, "営業時間外",
        "過去の 1/2 (固定休該当) でもガードが先 → 営業時間外 (固定休にしない)"),
    ("BH-33-過去日は祝日より優先",
        {"target_datetime": "2026-05-05 10:00:00", "reference_date": "2026-06-04 15:00:00"}, "営業時間外",
        "過去のこどもの日 (祝日該当) でもガードが先 → 営業時間外 (祝日にしない)"),
    ("BH-34-過去年祝日_Note未登録",
        {"target_datetime": "2025-01-01 10:00:00", "reference_date": "2026-06-04 15:00:00"}, "営業時間外",
        "過去年の元日 (HOLIDAYS_2026 に無い) — 過去ガードが Note 抜けを救い 営業時間外"),
]


def main() -> int:
    pass_count = 0
    fail_count = 0
    rows = []
    for case_id, overrides, expected, comment in CASES:
        params = Params(**{**Params().__dict__, **overrides})
        try:
            got = classify(params, now=TEST_NOW, holiday_set=HOLIDAYS_2026)
        except Exception as e:
            got = f"EXCEPTION:{e}"
        status = "PASS" if got == expected else "FAIL"
        if status == "PASS":
            pass_count += 1
        else:
            fail_count += 1
        rows.append((case_id, expected, got, status, comment))

    width_id = max(len(r[0]) for r in rows)
    print(f"{'id'.ljust(width_id)}  {'expected'.ljust(10)}  {'got'.ljust(10)}  status  comment")
    print("-" * (width_id + 50))
    for case_id, expected, got, status, comment in rows:
        print(f"{case_id.ljust(width_id)}  {expected.ljust(10)}  {got.ljust(10)}  {status:6}  {comment}")
    print("-" * (width_id + 50))
    print(f"{pass_count}/{pass_count + fail_count} PASS")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
