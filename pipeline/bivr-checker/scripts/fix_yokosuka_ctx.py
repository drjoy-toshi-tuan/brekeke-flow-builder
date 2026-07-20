#!/usr/bin/env python3
"""横須賀共済病院 saveContextModel2DB fields 修正スクリプト

スプレッドシート定義に完全準拠:
  - デフォルト12フィールドを正しい属性値で再構築
  - 赤字（可変）: classification.rangeValues / clinicalDepartment.rangeValues のみ
  - それ以外は固定値（変更不可）
  - 案件固有フィールドはデフォルトの後に追加
"""
import json
import sys
import io
from pathlib import Path

OUTPUT_DIR = Path("output/横須賀共済病院")

# ============================================================
# デフォルトフィールド定義（スプレッドシート準拠・固定値）
# 赤字（可変）部分は関数引数で受け取る
# ============================================================

def build_default_fields(classification_values, department_values):
    """デフォルト12フィールドを構築。

    Args:
        classification_values: list of {"order": N, "value": "xxx"}  ← 赤字（案件ごとに変更）
        department_values: list of {"order": N, "value": "xxx"}  ← 赤字（案件ごとに変更）
    """
    return [
        {
            "contextName": "classification",
            "contextNameJp": "区分",
            "deletable": False,
            "displayType": "CLASSIFICATION",
            "editable": True,
            "itemDefault": True,
            "rangeValues": classification_values,  # 🔴 赤字: 案件ごとに変更
        },
        {
            "contextName": "patientName",
            "contextNameJp": "患者名",
            "deletable": False,
            "displayType": "TEXT",
            "editable": True,
            "itemDefault": True,
            "rangeValues": [],
        },
        {
            "contextName": "medicalCardNumber",
            "contextNameJp": "診察券番号",
            "deletable": False,
            "displayType": "NUMBER",
            "editable": True,
            "itemDefault": True,
            "rangeValues": [],
        },
        {
            "contextName": "clinicalDepartment",
            "contextNameJp": "診療科",
            "deletable": False,
            "displayType": "DEPARTMENT",
            "editable": True,
            "itemDefault": True,
            "rangeValues": department_values,  # 🔴 赤字: 案件ごとに変更
        },
        {
            "contextName": "patientDateOfBirth",
            "contextNameJp": "生年月日(和暦)",
            "deletable": False,
            "displayType": "DATE_OF_BIRTH",
            "editable": True,
            "itemDefault": True,
            "rangeValues": [],
        },
        {
            "contextName": "reason",
            "contextNameJp": "理由",
            "deletable": False,
            "displayType": "TEXT",
            "editable": True,
            "itemDefault": True,
            "rangeValues": [],
        },
        {
            "contextName": "reservationDate",
            "contextNameJp": "予約日",
            "deletable": False,
            "displayType": "DATE",
            "editable": True,
            "itemDefault": True,
            "rangeValues": [],
        },
        {
            "contextName": "telephoneNumber",
            "contextNameJp": "電話番号",
            "deletable": False,
            "displayType": "PHONE_NUMBER_CALL",
            "editable": False,
            "itemDefault": True,
            "rangeValues": [],
        },
        {
            "contextName": "additionalPhoneNumber",
            "contextNameJp": "連絡先電話番号",
            "deletable": False,
            "displayType": "PHONE_NUMBER",
            "editable": True,
            "itemDefault": True,
            "rangeValues": [],
        },
        {
            "contextName": "status",
            "contextNameJp": "状態",
            "rangeValues": [
                {"id": "0", "order": 0, "value": "途中切断"},
                {"id": "1", "order": 1, "value": "未処理"},
                {"id": "2", "order": 2, "value": "代表案内"},
                {"id": "3", "order": 3, "value": "転送"},
                {"id": "6", "order": 6, "value": "時間外"},
            ],
            "deletable": False,
            "displayType": "STATUS",
            "editable": True,
            "itemDefault": True,
        },
        {
            "contextName": "callId",
            "contextNameJp": "通話ID",
            "rangeValues": [],
            "deletable": True,
            "displayType": "NUMBER",
            "editable": True,
            "itemDefault": False,
        },
        {
            "contextName": "dateOfCall",
            "contextNameJp": "入電日時",
            "rangeValues": [],
            "deletable": False,
            "displayType": "DATE",
            "editable": False,
            "itemDefault": True,
        },
    ]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    main_file = OUTPUT_DIR / "横須賀共済_診療予約_20260406_20260420.json"

    with open(main_file, encoding="utf-8") as f:
        data = json.load(f)

    modules = data["modules"]
    ctx = modules["コンテキスト設定"]
    old_fields = json.loads(ctx["params"]["fields"])

    # 現在の案件固有フィールドを抽出（デフォルト12フィールド以外）
    default_names = {
        "classification", "patientName", "medicalCardNumber",
        "clinicalDepartment", "patientDateOfBirth", "reason",
        "reservationDate", "telephoneNumber", "additionalPhoneNumber",
        "status", "callId", "dateOfCall",
    }

    # 案件固有フィールドを保持（appointmentDateはreservationDateに統合するため除外）
    extra_fields = []
    for f in old_fields:
        cn = f["contextName"]
        if cn not in default_names and cn != "appointmentDate":
            extra_fields.append(f)

    # 横須賀共済の赤字部分（案件固有の値）
    classification_values = [
        {"order": 1, "value": "変更"},
        {"order": 2, "value": "キャンセル"},
        {"order": 3, "value": "確認"},
    ]

    department_values = [
        {"order": 1, "value": "IVRセンター"},
    ]

    # デフォルトフィールド構築 + 案件固有フィールド追加
    new_fields = build_default_fields(classification_values, department_values) + extra_fields

    # 差分表示
    print("=== saveContextModel2DB fields 修正 ===\n")

    old_map = {f["contextName"]: f for f in old_fields}
    new_map = {f["contextName"]: f for f in new_fields}

    # 変更点の表示
    for f in new_fields:
        cn = f["contextName"]
        if cn in old_map:
            old = old_map[cn]
            diffs = []
            for key in set(list(f.keys()) + list(old.keys())):
                if key == "rangeValues":
                    continue  # rangeValuesは長いのでスキップ
                if f.get(key) != old.get(key):
                    diffs.append(f"{key}: {old.get(key)} → {f.get(key)}")
            if diffs:
                print(f"  ✓ {cn}: {', '.join(diffs)}")
        else:
            print(f"  ✓ {cn}: 新規追加")

    # 削除されたフィールド
    for cn in old_map:
        if cn not in new_map:
            print(f"  ✓ {cn}: 削除（reservationDateに統合 or 不要）")

    # 書き出し
    ctx["params"]["fields"] = json.dumps(new_fields, ensure_ascii=False, indent=2)
    with open(main_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nフィールド数: {len(old_fields)} → {len(new_fields)}")
    print(f"  デフォルト: 12")
    print(f"  案件固有: {len(extra_fields)} ({', '.join(f['contextName'] for f in extra_fields)})")
    print(f"\n出力: {main_file}")


if __name__ == "__main__":
    main()
