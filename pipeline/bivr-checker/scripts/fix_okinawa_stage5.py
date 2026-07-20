#!/usr/bin/env python3
"""Fix remaining structural issues in 沖縄県立南部医療センター_診療_20260415.json

Issue 1: Retry false consistency (22 modules)
Issue 2: Fields definition in saveContextModel2DB
"""

import json
import sys
from pathlib import Path

FLOW_PATH = Path(r"C:\Users\takahashi.s\VSCode\bivr-checker\output\沖縄県立南部医療センター_診療_20260415.json")

PROMPT_FALSE_FAILURE = "{tts_g: 大変申し訳ございません。 うまく聞き取ることができませんでしたので後ほど担当者にて確認いたします。}"

# From verify_result.json
RETRY_FIXES = [
    {"retry": "リトライ_小児科確認",         "expected_false": "用件確認",              "reason": "次へ進む"},
    {"retry": "リトライ_用件確認",           "expected_false": "復唱_用件確認",          "reason": "次へ進む"},
    {"retry": "リトライ_用件確認_復唱",       "expected_false": "復唱_用件確認",          "reason": "無限ループ"},
    {"retry": "リトライ_診療科_新規",         "expected_false": "診療科_新規",            "reason": "無限ループ"},
    {"retry": "リトライ_紹介状確認",          "expected_false": "紹介状確認",             "reason": "無限ループ"},
    {"retry": "リトライ_医療機関名_新規",      "expected_false": "入力_都合が悪い日_新規",   "reason": "次へ進む"},
    {"retry": "リトライ_都合が悪い日_新規",    "expected_false": "jump_氏名聴取",          "reason": "次へ進む"},
    {"retry": "リトライ_薬服用中か_変更",      "expected_false": "薬服用中か_変更",         "reason": "無限ループ"},
    {"retry": "リトライ_薬残数確認_変更",      "expected_false": "薬残数確認_変更",         "reason": "無限ループ"},
    {"retry": "リトライ_診療科_変更",         "expected_false": "診療科_変更",            "reason": "無限ループ"},
    {"retry": "リトライ_予約日_変更",         "expected_false": "復唱_予約日_変更",        "reason": "次へ進む"},
    {"retry": "リトライ_予約日_変更_復唱",     "expected_false": "復唱_予約日_変更",        "reason": "無限ループ"},
    {"retry": "リトライ_理由_変更",           "expected_false": "入力_都合が悪い日_変更",   "reason": "次へ進む"},
    {"retry": "リトライ_都合が悪い日_変更",    "expected_false": "jump_氏名聴取",          "reason": "次へ進む"},
    {"retry": "リトライ_薬服用中か_キャンセル",  "expected_false": "薬服用中か_キャンセル",    "reason": "無限ループ"},
    {"retry": "リトライ_薬残数確認_キャンセル",  "expected_false": "薬残数確認_キャンセル",    "reason": "無限ループ"},
    {"retry": "リトライ_診療科_キャンセル",     "expected_false": "診療科_キャンセル",       "reason": "無限ループ"},
    {"retry": "リトライ_予約日_キャンセル",     "expected_false": "復唱_予約日_キャンセル",   "reason": "次へ進む"},
    {"retry": "リトライ_予約日_キャンセル_復唱", "expected_false": "復唱_予約日_キャンセル",   "reason": "無限ループ"},
    {"retry": "リトライ_理由_キャンセル",       "expected_false": "jump_氏名聴取",          "reason": "次へ進む"},
    {"retry": "リトライ_診療科_確認",          "expected_false": "診療科_確認",            "reason": "無限ループ"},
    {"retry": "リトライ_確認事項",             "expected_false": "jump_氏名聴取",          "reason": "次へ進む"},
]

# Standard fields that must have deletable=false, itemDefault=true
STANDARD_FIELDS = {
    "classification":        {"deletable": False, "itemDefault": True},
    "patientName":           {"deletable": False, "itemDefault": True},
    "medicalCardNumber":     {"deletable": False, "itemDefault": True},
    "clinicalDepartment":    {"deletable": False, "itemDefault": True},
    "patientDateOfBirth":    {"deletable": False, "itemDefault": True},
    "reason":                {"deletable": False, "itemDefault": True},
    "reservationDate":       {"deletable": False, "itemDefault": True},
    "telephoneNumber":       {"editable": False, "deletable": False, "itemDefault": True},
    "additionalPhoneNumber": {"deletable": False, "itemDefault": True},
    "status":                {"deletable": False, "itemDefault": True},
    "dateOfCall":            {"editable": False, "deletable": False, "itemDefault": True},
}


def fix_retry_false(flow, changes):
    """Fix retry false destinations and prompt_false values."""
    modules = flow["modules"]

    for fix in RETRY_FIXES:
        retry_name = fix["retry"]
        expected_false = fix["expected_false"]
        reason = fix["reason"]

        if retry_name not in modules:
            print(f"  [SKIP] {retry_name} not found in modules")
            continue

        mod = modules[retry_name]
        next_arr = mod["next"]

        # Find the false entry
        false_entry = None
        for entry in next_arr:
            if entry.get("condition") == "false":
                false_entry = entry
                break

        if false_entry is None:
            print(f"  [SKIP] {retry_name}: no false condition found")
            continue

        old_false = false_entry["nextModuleName"]

        # Verify target exists
        if expected_false not in modules:
            print(f"  [WARN] {retry_name}: target '{expected_false}' not in modules!")
            continue

        # Fix false destination
        if old_false != expected_false:
            false_entry["nextModuleName"] = expected_false
            changes.append(f"[retry_false] {retry_name}: false '{old_false}' -> '{expected_false}' ({reason})")

        # Fix prompt_false based on pattern
        if reason == "無限ループ":
            # Pattern C: prompt_false = ""
            old_pf = mod["params"].get("prompt_false", "")
            if old_pf != "":
                mod["params"]["prompt_false"] = ""
                changes.append(f"[prompt_false] {retry_name}: set to '' (無限ループ)")
        elif reason == "次へ進む":
            # Pattern A: prompt_false = failure message
            old_pf = mod["params"].get("prompt_false", "")
            if old_pf != PROMPT_FALSE_FAILURE:
                mod["params"]["prompt_false"] = PROMPT_FALSE_FAILURE
                changes.append(f"[prompt_false] {retry_name}: set failure message (次へ進む)")


def fix_fields(flow, changes):
    """Fix fields in saveContextModel2DB."""
    modules = flow["modules"]

    # Find the saveContextModel2DB module
    ctx_mod = None
    ctx_name = None
    for name, mod in modules.items():
        if mod.get("type") == "drjoy^Persistence$saveContextModel2DB":
            ctx_mod = mod
            ctx_name = name
            break

    if ctx_mod is None:
        print("  [SKIP] No saveContextModel2DB module found")
        return

    fields_str = ctx_mod["params"].get("fields", "")
    fields = json.loads(fields_str)

    field_changes = 0
    for field in fields:
        cn = field.get("contextName", "")
        if cn in STANDARD_FIELDS:
            expected = STANDARD_FIELDS[cn]
            for attr, val in expected.items():
                if field.get(attr) != val:
                    old_val = field.get(attr)
                    field[attr] = val
                    changes.append(f"[fields] {cn}.{attr}: {old_val} -> {val}")
                    field_changes += 1

    if field_changes > 0:
        # Write back as JSON string with indent=2
        ctx_mod["params"]["fields"] = json.dumps(fields, ensure_ascii=False, indent=2)
        print(f"  Fixed {field_changes} field attributes in {ctx_name}")


def main():
    print(f"Reading: {FLOW_PATH}")
    with open(FLOW_PATH, "r", encoding="utf-8") as f:
        flow = json.load(f)

    changes = []

    print("\n=== Issue 1: Retry false consistency ===")
    fix_retry_false(flow, changes)

    print("\n=== Issue 2: Fields definition ===")
    fix_fields(flow, changes)

    # Write back
    print(f"\nWriting: {FLOW_PATH}")
    with open(FLOW_PATH, "w", encoding="utf-8") as f:
        json.dump(flow, f, ensure_ascii=False, indent=2)

    # Summary
    print(f"\n=== Summary: {len(changes)} changes ===")
    for c in changes:
        print(f"  {c}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
