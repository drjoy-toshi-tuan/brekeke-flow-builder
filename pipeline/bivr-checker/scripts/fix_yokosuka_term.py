#!/usr/bin/env python3
"""横須賀共済病院 TERM-001/002/004 修正スクリプト

修正内容:
  TERM-001: jump_電話番号聴取 → TODO_scaffold（存在しない）
    → 着信分類_SMS判定 (incoming-classifier) を追加
    → 携帯 → 完了フラグ_受付完了, その他 → 完了フラグ_受付完了_SMS無し

  TERM-002/004: 完了フラグ_代表案内 が当日・新規予約の両方で使われるのに
    END_代表案内_新規予約 にしか行かない
    → 完了フラグ_代表案内_当日 を新設
    → OpenAI_当日確認 ^はい$ → 完了フラグ_代表案内_当日 に変更
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
    # TERM-001: jump_電話番号聴取 → 着信分類_SMS判定 → 完了フラグ分岐
    # ================================================================

    # 1a. jump_電話番号聴取 の遷移先を修正
    jump_tel = modules["jump_電話番号聴取"]
    old_next = jump_tel["next"][0]["nextModuleName"]
    jump_tel["next"][0]["nextModuleName"] = "着信分類_SMS判定"
    fixes.append(f"TERM-001: jump_電話番号聴取 next: {old_next} → 着信分類_SMS判定")

    # 1b. 着信分類_SMS判定 モジュール新設
    modules["着信分類_SMS判定"] = {
        "type": "drjoy^Incoming$incoming-classifier",
        "params": {},
        "next": [
            {"condition": "^非通知$", "label": "非通知", "nextModuleName": "完了フラグ_受付完了_SMS無し"},
            {"condition": "^固定$", "label": "固定", "nextModuleName": "完了フラグ_受付完了_SMS無し"},
            {"condition": "^海外$", "label": "海外", "nextModuleName": "完了フラグ_受付完了_SMS無し"},
            {"condition": "^携帯$", "label": "携帯", "nextModuleName": "完了フラグ_受付完了"},
            {"condition": "^.*$", "label": "その他", "nextModuleName": "完了フラグ_受付完了_SMS無し"},
        ],
        "subs": [
            {"moduleName": "", "label": ""},
            {"moduleName": "", "label": ""},
            {"moduleName": "", "label": ""},
        ],
        "layout": {"x": 560, "y": 8700},
    }
    fixes.append("TERM-001: 着信分類_SMS判定 モジュール新設 (incoming-classifier)")
    fixes.append("TERM-001: 携帯 → 完了フラグ_受付完了 (SMS), その他 → 完了フラグ_受付完了_SMS無し")

    # ================================================================
    # TERM-002/004: 完了フラグ_代表案内_当日 を新設
    # ================================================================

    # 2a. 完了フラグ_代表案内_当日 モジュール新設
    # 既存の 完了フラグ_代表案内 と同じ status=2, smsFlag=-1
    modules["完了フラグ_代表案内_当日"] = {
        "type": "drjoy^Persistence$saveCompletionFlag2db",
        "params": {
            "status": "2",
            "endpoint": "",
            "smsFlag": "-1",
        },
        "next": [
            {"condition": "^.*$", "label": "next", "nextModuleName": "END_代表案内_当日"},
        ],
        "subs": [
            {"moduleName": "", "label": ""},
            {"moduleName": "", "label": ""},
            {"moduleName": "", "label": ""},
        ],
        "layout": {"x": 0, "y": 2400},
    }
    fixes.append("TERM-002/004: 完了フラグ_代表案内_当日 モジュール新設 (status=2, smsFlag=-1)")

    # 2b. OpenAI_当日確認 の ^はい$ 遷移先を変更
    oai_toujitsu = modules["OpenAI_当日確認"]
    for n in oai_toujitsu["next"]:
        if n.get("condition") == "^はい$":
            old = n["nextModuleName"]
            n["nextModuleName"] = "完了フラグ_代表案内_当日"
            fixes.append(f"TERM-002/004: OpenAI_当日確認 ^はい$: {old} → 完了フラグ_代表案内_当日")
            break

    # ================================================================
    # 検証: 到達可能性チェック
    # ================================================================

    start = data.get("start", "")
    visited = set()
    queue = [start]
    while queue:
        current = queue.pop(0)
        if current in visited or current not in modules:
            continue
        visited.add(current)
        mod = modules[current]
        for n in mod.get("next", []):
            nm = n.get("nextModuleName", "")
            if nm and nm not in visited:
                queue.append(nm)
        for s in mod.get("subs", []):
            sm = s.get("moduleName", "")
            if sm and sm not in visited:
                queue.append(sm)

    unreachable = set(modules.keys()) - visited

    print("=== 横須賀共済病院 TERM修正 ===\n")
    for fix in fixes:
        print(f"  ✓ {fix}")
    print()

    if unreachable:
        print(f"⚠ 到達不能モジュール ({len(unreachable)}件):")
        for u in sorted(unreachable):
            print(f"  - {u}")
    else:
        print("✓ 全モジュール到達可能")

    # 書き出し
    with open(main_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n出力: {main_file}")

if __name__ == "__main__":
    main()
