#!/usr/bin/env python3
"""横須賀共済病院 フィードバック対応修正スクリプト

修正内容:
  1. detection_flag: メインフロー全STTモジュールから "検出しない" を削除
     → Property.md側で一括管理するため、モジュール側はデフォルトのまま

  2. 着信分類_SMS判定 (incoming-classifier) を削除
     → VFB上でモジュール名空白のバグ発生。ContextMatchRouterに変更
     → 電話番号サブフローが phonetype context に "携帯"/"その他" を保存済み
     → jump_電話番号聴取 の返り値で分岐
"""
import json
import sys
import io
from pathlib import Path

OUTPUT_DIR = Path("output/横須賀共済病院")


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    main_file = OUTPUT_DIR / "横須賀共済_診療予約_20260406_20260420.json"

    with open(main_file, encoding="utf-8") as f:
        data = json.load(f)

    modules = data["modules"]
    fixes = []

    # ================================================================
    # 1. detection_flag 削除（モジュール側はデフォルトのまま）
    # ================================================================
    stt_types = [
        "drjoy^AmiVoice$Speech to Text",
        "drjoy^External Integration$DTMF AmiVoice STT Input",
    ]
    for name, mod in modules.items():
        if mod.get("type", "") in stt_types:
            if "detection_flag" in mod.get("params", {}):
                old_val = mod["params"]["detection_flag"]
                del mod["params"]["detection_flag"]
                fixes.append(f"detection_flag削除: {name} (was \"{old_val}\")")

    # ================================================================
    # 2. 着信分類_SMS判定 (incoming-classifier) → ContextMatchRouter に変更
    # ================================================================

    # 2a. incoming-classifier 削除
    if "着信分類_SMS判定" in modules:
        del modules["着信分類_SMS判定"]
        fixes.append("削除: 着信分類_SMS判定 (incoming-classifier) — VFBバグの原因")

    # 2b. ContextMatchRouter 追加
    # 電話番号サブフローは phonetype context を "携帯"/"その他" で保存し、
    # 結果返却スクリプトで $runner.setResult() で返却する
    # → jump_電話番号聴取 の出力値で分岐
    modules["SMS判定"] = {
        "type": "drjoy^Context Logic$ContextMatchRouter",
        "params": {
            "module1Name": "jump_電話番号聴取",
            "module2Name": "jump_電話番号聴取",
            "module1Value1": "携帯",
            "module1Value2": "その他",
            "module1Value3": "", "module1Value4": "", "module1Value5": "",
            "module1Value6": "", "module1Value7": "", "module1Value8": "",
            "module1Value9": "", "module1Value10": "",
            "module2Value1": "携帯",
            "module2Value2": "その他",
            "module2Value3": "", "module2Value4": "", "module2Value5": "",
            "module2Value6": "", "module2Value7": "", "module2Value8": "",
            "module2Value9": "", "module2Value10": "",
        },
        "next": [
            {"condition": "^1$", "label": "携帯", "nextModuleName": "完了フラグ_受付完了"},
            {"condition": "^2$", "label": "その他", "nextModuleName": "完了フラグ_受付完了_SMS無し"},
            {"condition": "^.*$", "label": "default", "nextModuleName": "完了フラグ_受付完了_SMS無し"},
            {"condition": "", "label": "", "nextModuleName": ""},
            {"condition": "", "label": "", "nextModuleName": ""},
            {"condition": "", "label": "", "nextModuleName": ""},
            {"condition": "", "label": "", "nextModuleName": ""},
            {"condition": "", "label": "", "nextModuleName": ""},
            {"condition": "", "label": "", "nextModuleName": ""},
            {"condition": "", "label": "", "nextModuleName": ""},
            {"condition": "", "label": "", "nextModuleName": ""},
            {"condition": "", "label": "", "nextModuleName": ""},
        ],
        "subs": [
            {"moduleName": "", "label": ""},
            {"moduleName": "", "label": ""},
            {"moduleName": "", "label": ""},
        ],
        "matchingmethod": "1",
        "layout": {"x": 560, "y": 8700},
    }
    fixes.append("追加: SMS判定 (ContextMatchRouter) — jump_電話番号聴取の返り値で携帯/その他を分岐")

    # 2c. jump_電話番号聴取 の遷移先を変更
    jump_tel = modules["jump_電話番号聴取"]
    for n in jump_tel["next"]:
        if n.get("nextModuleName") == "着信分類_SMS判定":
            n["nextModuleName"] = "SMS判定"
            fixes.append("遷移先変更: jump_電話番号聴取 → SMS判定")

    # ================================================================
    # 書き出し
    # ================================================================
    with open(main_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("=== 横須賀共済病院 フィードバック対応修正 ===\n")
    for fix in fixes:
        print(f"  ✓ {fix}")
    print(f"\n出力: {main_file}")


if __name__ == "__main__":
    main()
