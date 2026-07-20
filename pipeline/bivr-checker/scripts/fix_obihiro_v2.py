#!/usr/bin/env python3
"""
fix_obihiro_v2.py — 帯広第一病院_診療_20260415_1.json の修正スクリプト

Fix 1: matchingmethod = "0" を params に追加（Retry Counter 10モジュール）
Fix 2: ContextMatchRouter の ^.+$ nextModuleName を設定（6モジュール）
Fix 3: Jump モジュールの properties を設定（4モジュール）
"""

import json
import copy

SRC = "output/帯広第一病院_診療_20260415_1.json"
DST = "output/帯広第一病院/fixed_v2/flows/帯広第一病院_診療_v2.json"

with open(SRC, encoding="utf-8") as f:
    data = json.load(f)

modules = data["modules"]

# -----------------------------------------------------------------------
# Fix 1: matchingmethod = "0" for ALL Retry Counter modules
# -----------------------------------------------------------------------
RETRY_MODULES = [
    "リトライ_予約希望日",
    "リトライ_内容確認",
    "リトライ_最終確認",
    "リトライ_現在の予約日",
    "リトライ_理由聴取",
    "リトライ_用件確認",
    "リトライ_症状聴取",
    "リトライ_診療科",
    "リトライ_追加診療科",
    "リトライ_通院歴確認",
]

fixed_retry = []
for name in RETRY_MODULES:
    if name in modules:
        modules[name]["params"]["matchingmethod"] = "0"
        fixed_retry.append(name)
    else:
        print(f"[WARN] Retry module not found: {name}")

print(f"[Fix 1] Set matchingmethod='0' for {len(fixed_retry)} Retry Counter modules")
for n in fixed_retry:
    print(f"        - {n}")

# -----------------------------------------------------------------------
# Fix 2: ContextMatchRouter ^.+$ Other routes - set nextModuleName
# -----------------------------------------------------------------------
CMR_FIX = {
    "ルート分岐": "完了フラグ_聴取失敗",
    "ルート分岐_予約希望日後": "完了フラグ_聴取失敗",
    "ルート分岐_現在予約日後": "完了フラグ_聴取失敗",
    "終話分岐_用件": "完了フラグ_聴取失敗",
    "終話分岐_受付完了": "完了フラグ_受付完了_固定",
    "終話分岐_キャンセル": "完了フラグ_キャンセル_固定",
}

fixed_cmr = []
for mod_name, next_mod in CMR_FIX.items():
    if mod_name in modules:
        m = modules[mod_name]
        found = False
        for n in m["next"]:
            if n["condition"] == "^.+$":
                n["nextModuleName"] = next_mod
                found = True
                break
        if found:
            fixed_cmr.append(f"{mod_name} -> {next_mod}")
        else:
            print(f"[WARN] ^.+$ condition not found in {mod_name}")
    else:
        print(f"[WARN] CMR module not found: {mod_name}")

print(f"\n[Fix 2] Set nextModuleName for ^.+$ routes in {len(fixed_cmr)} ContextMatchRouter modules")
for n in fixed_cmr:
    print(f"        - {n}")

# -----------------------------------------------------------------------
# Fix 3: Set properties for Jump modules
# -----------------------------------------------------------------------
JUMP_PROPERTIES = {
    "Jump_診察券番号聴取": "患者_診察券番号.prompt={tts_g:診察券をお持ちの場合は診察券番号をプッシュボタンでご入力いただくか、お声でお知らせください。お持ちでない場合は「なし」とお話しください。}",
    "Jump_氏名聴取": "患者_氏名.prompt={tts_g:お名前をお聞かせください。}\n復唱_患者_氏名.prompt={tts_g: #data# 様でよろしいでしょうか。}",
    "Jump_生年月日聴取": "患者_生年月日.prompt={tts_g:生年月日をお聞かせください。例えば、昭和56年3月15日の場合は、0と3と1と5と入力するか、昭和56年3月15日とお話しください。}",
    "Jump_電話番号聴取": "患者_電話番号.prompt={tts_g:ご連絡先のお電話番号をお聞かせください。}\n復唱_患者_電話番号.prompt={tts_g: #data# でよろしいでしょうか。}",
}

fixed_jump = []
for mod_name, props in JUMP_PROPERTIES.items():
    if mod_name in modules:
        modules[mod_name]["params"]["properties"] = props
        fixed_jump.append(mod_name)
    else:
        print(f"[WARN] Jump module not found: {mod_name}")

print(f"\n[Fix 3] Set properties for {len(fixed_jump)} Jump modules")
for n in fixed_jump:
    print(f"        - {n}")

# -----------------------------------------------------------------------
# Save the fixed JSON
# -----------------------------------------------------------------------
import os
os.makedirs(os.path.dirname(DST), exist_ok=True)

with open(DST, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n[OK] Saved fixed JSON to: {DST}")
print(f"     Total modules: {len(modules)}")

# -----------------------------------------------------------------------
# Verify the fixes
# -----------------------------------------------------------------------
print("\n[Verification]")

# Check Retry Counter matchingmethod
print("Retry Counter matchingmethod:")
for name in RETRY_MODULES:
    if name in modules:
        mm = modules[name]["params"].get("matchingmethod")
        status = "OK" if mm == "0" else f"FAIL (got {mm})"
        print(f"  {name}: {status}")

# Check CMR ^.+$
print("ContextMatchRouter ^.+$ nextModuleName:")
for mod_name, expected in CMR_FIX.items():
    if mod_name in modules:
        for n in modules[mod_name]["next"]:
            if n["condition"] == "^.+$":
                actual = n["nextModuleName"]
                status = "OK" if actual == expected else f"FAIL (got {repr(actual)}, expected {repr(expected)})"
                print(f"  {mod_name}: {status}")

# Check Jump properties
print("Jump module properties:")
for mod_name, expected in JUMP_PROPERTIES.items():
    if mod_name in modules:
        actual = modules[mod_name]["params"].get("properties")
        status = "OK" if actual == expected else f"FAIL"
        print(f"  {mod_name}: {status}")
