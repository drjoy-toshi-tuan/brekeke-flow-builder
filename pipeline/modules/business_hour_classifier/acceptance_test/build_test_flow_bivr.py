"""build_test_flow_bivr.py — BusinessHour Classifier 受入テストフロー .bivr 生成。

test_oracle.py (Python オラクル) と同一の 26 ケースを Pattern 6 形式 (チェイン式) で
1 コール内に直列実行する。期待 jump が発火すれば次テストへ、不一致なら FAIL 終話に分岐。
各ケースで TARGET_DATETIME / WEEKDAY_SCHEDULE / CLOSED_DATES / NATIONAL_HOLIDAY を上書き可能。

出力: ./BusinessHourAcceptanceTest.bivr (Brekeke 管理画面で flow として import)
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).parent
PROJECT_ROOT = HERE.parent  # business_hour_classifier/

FLOW_NAME = "テスト$BusinessHour受入"

# --- スケジュール定義 (重複文字列を圧縮) ---
DEFAULT_SCHED = "mon=09:00-18:00,tue=09:00-18:00,wed=09:00-18:00,thu=09:00-18:00,fri=09:00-18:00,sat=closed,sun=closed"
WED_PM_OFF    = "mon=09:00-18:00,tue=09:00-18:00,wed=09:00-12:00,thu=09:00-18:00,fri=09:00-18:00,sat=closed,sun=closed"
TWENTY_FOUR_H = "mon=00:00-23:59,tue=00:00-23:59,wed=00:00-23:59,thu=00:00-23:59,fri=00:00-23:59,sat=00:00-23:59,sun=00:00-23:59"
WED_FULL_OFF  = "mon=09:00-18:00,tue=09:00-18:00,wed=closed,thu=09:00-18:00,fri=09:00-18:00,sat=closed,sun=closed"
SAT_AM_ONLY   = "mon=09:00-18:00,tue=09:00-18:00,wed=09:00-18:00,thu=09:00-18:00,fri=09:00-18:00,sat=09:00-13:00,sun=closed"
INVALID_TUE   = "mon=09:00-18:00,tue=invalid_range,wed=09:00-18:00,thu=09:00-18:00,fri=09:00-18:00,sat=closed,sun=closed"

# 過去日ガード用の基準「今日」。受入テストは実行時刻 (timeStart) に依存させないため、
# 全ケースで REFERENCE_DATE を固定注入する。レガシー BH-01〜25 は全 target (最古 2026-01-01)
# より前のこの値を使い過去日ガードを一切発火させない。過去日ケース (BH-26〜) は個別に上書き。
# test_oracle.py の TEST_NOW (= 2026-01-01 00:00:00) と一致させること。
TEST_NOW_LITERAL = "2026-01-01 00:00:00"

# (id, label, overrides, expected) ※ Python オラクル test_oracle.py の CASES と対応
TEST_CASES = [
    ("BH-01", "平日営業中",       {"target_datetime": "2026-06-02 10:00:00"}, "営業中"),
    ("BH-02", "平日朝の前",       {"target_datetime": "2026-06-02 08:30:00"}, "営業時間外"),
    ("BH-03", "平日夜の後",       {"target_datetime": "2026-06-02 19:30:00"}, "営業時間外"),
    ("BH-04", "平日開店ジャスト", {"target_datetime": "2026-06-02 09:00:00"}, "営業中"),
    ("BH-05", "平日閉店ジャスト", {"target_datetime": "2026-06-02 18:00:00"}, "営業時間外"),
    ("BH-06", "土曜",             {"target_datetime": "2026-06-06 10:00:00"}, "定休日"),
    ("BH-07", "日曜",             {"target_datetime": "2026-06-07 10:00:00"}, "定休日"),
    ("BH-08", "元日",             {"target_datetime": "2026-01-01 10:00:00"}, "祝日"),
    ("BH-09", "こどもの日",       {"target_datetime": "2026-05-05 10:00:00"}, "祝日"),
    ("BH-10", "年末12-31",        {"target_datetime": "2026-12-31 10:00:00"}, "固定休"),
    ("BH-11", "年始01-02",        {"target_datetime": "2026-01-02 10:00:00"}, "固定休"),
    ("BH-12", "祝日open設定",     {"target_datetime": "2026-05-05 10:00:00", "national_holiday": "open"}, "営業中"),
    ("BH-13", "水曜午後休1100",   {"target_datetime": "2026-06-03 11:00:00", "weekday_schedule": WED_PM_OFF}, "営業中"),
    ("BH-14", "水曜午後休1300",   {"target_datetime": "2026-06-03 13:00:00", "weekday_schedule": WED_PM_OFF}, "営業時間外"),
    ("BH-15", "24h無休病院",       {"target_datetime": "2026-06-06 23:30:00", "weekday_schedule": TWENTY_FOUR_H, "closed_dates": "", "national_holiday": "open"}, "営業中"),
    ("BH-16", "不正target",        {"target_datetime": "2026/06/02 10:00"}, "ERROR"),
    ("BH-17", "不正schedule",      {"target_datetime": "2026-06-02 10:00:00", "weekday_schedule": INVALID_TUE}, "ERROR"),
    ("BH-17b","未指定曜日tue",     {"target_datetime": "2026-06-02 10:00:00", "weekday_schedule": "mon=09:00-18:00"}, "定休日"),
    ("BH-18", "振替休日0506",      {"target_datetime": "2026-05-06 10:00:00"}, "祝日"),
    ("BH-19", "水曜全休",          {"target_datetime": "2026-06-03 10:00:00", "weekday_schedule": WED_FULL_OFF}, "定休日"),
    ("BH-20", "土曜午前のみ",      {"target_datetime": "2026-06-06 11:00:00", "weekday_schedule": SAT_AM_ONLY}, "営業中"),
    # --- date-only 入力 (saveContext2DB DATE 型 / yyyy-MM-dd リテラル) ---
    ("BH-21", "予約日平日DATE",    {"target_datetime": "2027-02-01 00:00:00"}, "営業中"),
    ("BH-22", "予約日土曜DATE",    {"target_datetime": "2027-02-06 00:00:00"}, "定休日"),
    ("BH-23", "予約日祝日DATE",    {"target_datetime": "2027-01-01 00:00:00"}, "祝日"),
    ("BH-24", "予約日固定休DATE",  {"target_datetime": "2026-12-31 00:00:00"}, "固定休"),
    ("BH-25", "予約日リテラル",    {"target_datetime": "2027-02-01"}, "営業中"),
    # --- 過去日ガード (予約受付特性: 過去日は一律 営業時間外)。基準=2026-06-04(木)15:00 を注入 ---
    ("BH-26", "過去日昨日平日内",   {"target_datetime": "2026-06-03 10:00:00", "reference_date": "2026-06-04 15:00:00"}, "営業時間外"),
    ("BH-27", "過去日昨日DATE",    {"target_datetime": "2026-06-03", "reference_date": "2026-06-04 15:00:00"}, "営業時間外"),
    ("BH-28", "当日過ぎた朝枠",     {"target_datetime": "2026-06-04 10:00:00", "reference_date": "2026-06-04 15:00:00"}, "営業中"),
    ("BH-29", "当日DATE",         {"target_datetime": "2026-06-04", "reference_date": "2026-06-04 15:00:00"}, "営業中"),
    ("BH-30", "翌日平日内",        {"target_datetime": "2026-06-05 10:00:00", "reference_date": "2026-06-04 15:00:00"}, "営業中"),
    ("BH-31", "明後日土曜",        {"target_datetime": "2026-06-06 10:00:00", "reference_date": "2026-06-04 15:00:00"}, "定休日"),
    ("BH-32", "過去日_固定休より先", {"target_datetime": "2026-01-02 10:00:00", "reference_date": "2026-06-04 15:00:00"}, "営業時間外"),
    ("BH-33", "過去日_祝日より先",   {"target_datetime": "2026-05-05 10:00:00", "reference_date": "2026-06-04 15:00:00"}, "営業時間外"),
    ("BH-34", "過去年祝日Note無",   {"target_datetime": "2025-01-01 10:00:00", "reference_date": "2026-06-04 15:00:00"}, "営業時間外"),
]


def build_script_for_case(case_id: str, expected: str, overrides: dict, base_script: str) -> str:
    """script.js をベースに、テストケース 1 件分のスクリプトを組み立てる。

    冒頭にテストマーカーログを挿入し、CONFIG 定数を overrides に従って書き換える。
    上書き可能な key: target_datetime / reference_date / weekday_schedule / closed_dates / national_holiday
    """
    # 受入テストは実行時刻 (timeStart) に依存させないため、reference_date を必ず固定注入する。
    # 過去日ケースは個別に上書き済み。それ以外は TEST_NOW_LITERAL (全 target より前) で過去日ガード非発火。
    overrides = {"reference_date": TEST_NOW_LITERAL, **overrides}
    target_dt = overrides.get("target_datetime", "(default)")
    marker_extras = " ".join(f"{k}={v!r}" for k, v in sorted(overrides.items()) if k != "target_datetime")
    marker = (
        f'$runner.getLogger().info('
        f'"[{case_id}] expected={expected} target={target_dt} {marker_extras}");\n\n'
    )

    replacements = {
        "target_datetime":  ("TARGET_DATETIME",  overrides.get("target_datetime")),
        "reference_date":   ("REFERENCE_DATE",   overrides.get("reference_date")),
        "weekday_schedule": ("WEEKDAY_SCHEDULE", overrides.get("weekday_schedule")),
        "closed_dates":     ("CLOSED_DATES",     overrides.get("closed_dates")),
        "national_holiday": ("NATIONAL_HOLIDAY", overrides.get("national_holiday")),
    }

    s = base_script
    for _key, (const_name, value) in replacements.items():
        if value is None:
            continue
        pattern = re.compile(rf'var {const_name}\s*=\s*"[^"]*"\s*;')
        if not pattern.search(s):
            raise SystemExit(f"ERROR: {const_name} 行が見つからない (script.js が想定外フォーマット)")
        s = pattern.sub(f'var {const_name} = "{value}";', s)
    return marker + s


def empty_next_slot() -> dict:
    return {"condition": "", "label": "", "nextModuleName": ""}


def empty_subs() -> list:
    return [{"moduleName": "", "label": ""} for _ in range(3)]


def make_script_module(name: str, script: str, layout: dict,
                       expected_label: str, on_match_next: str, on_fail_next: str,
                       description: str) -> dict:
    """テストケース用 @General$Script モジュール (期待ジャンプ + catch-all FAIL)。"""
    next_slots = [
        {"condition": f"^{expected_label}$", "label": "PASS→次", "nextModuleName": on_match_next},
        {"condition": "^.*$",                "label": "FAIL",      "nextModuleName": on_fail_next},
    ]
    while len(next_slots) < 10:
        next_slots.append(empty_next_slot())
    return {
        "name": name,
        "type": "@General$Script",
        "matchingmethod": 1,
        "description": description,
        "layout": layout,
        "params": {"script": script.replace("\r\n", "\n").replace("\n", "\r\n")},
        "next": next_slots,
        "subs": empty_subs(),
    }


def make_disconnect_module(name: str, layout: dict, description: str) -> dict:
    return {
        "name": name,
        "type": "@IVR$Disconnect",
        "matchingmethod": 1,
        "description": description,
        "layout": layout,
        "params": {},
        "next": [empty_next_slot() for _ in range(10)],
        "subs": empty_subs(),
    }


def main() -> int:
    base_script = (PROJECT_ROOT / "script.js").read_text(encoding="utf-8")

    modules: dict[str, dict] = {}
    x_test, x_fail = 300, 700
    y_step = 200
    y0 = 100

    # 終話: PASS (最後のケース成功で到達)
    pass_name = "PASS_全件PASS"
    modules[pass_name] = make_disconnect_module(
        pass_name,
        layout={"x": x_test, "y": y0 + (len(TEST_CASES) + 1) * y_step},
        description=f"全 {len(TEST_CASES)} ケースの期待 jump が連続発火 → 受入テスト PASS",
    )

    next_module = pass_name
    for idx, (case_id, label, overrides, expected) in reversed(list(enumerate(TEST_CASES))):
        i = idx + 1
        fail_name = f"FAIL_{case_id}_期待:{expected}"
        modules[fail_name] = make_disconnect_module(
            fail_name,
            layout={"x": x_fail, "y": y0 + i * y_step},
            description=f"{case_id} ({label}) で期待 '{expected}' と異なる結果。回帰",
        )
        test_name = f"テスト{case_id}_{label}"
        script = build_script_for_case(case_id, expected, overrides, base_script)
        modules[test_name] = make_script_module(
            test_name,
            script=script,
            layout={"x": x_test, "y": y0 + i * y_step},
            expected_label=expected,
            on_match_next=next_module,
            on_fail_next=fail_name,
            description=f"受入テストケース {case_id}: {label} (expected={expected})",
        )
        next_module = test_name

    start_name = next_module

    flow = {
        "name": FLOW_NAME,
        "desc": f"BusinessHour Classifier 受入テスト {len(TEST_CASES)} ケース (Pattern 6 チェイン式)。"
                f"test_oracle.py と同一カバー。1 コールで全ケース直列実行、PASS_全件PASS 到達で受入確定。",
        "start": start_name,
        "modules": modules,
        "layout": {"width": 1200, "height": y0 + (len(TEST_CASES) + 2) * y_step},
        "resultValue": "",
        "postCallAction": "",
    }

    out = HERE / "BusinessHourAcceptanceTest.bivr"
    body = json.dumps(flow, ensure_ascii=False, separators=(",", ":"))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        fname = "flows/@flow_" + quote(FLOW_NAME, safe="") + ".txt"
        zf.writestr(fname, body)
    print(f"wrote {out} ({out.stat().st_size} bytes, {len(modules)} modules)")
    print(f"   flow file: {fname}")
    print(f"   start: {start_name}")
    print(f"   {len(TEST_CASES)} cases + {len(TEST_CASES)} FAIL terminations + 1 PASS termination")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
