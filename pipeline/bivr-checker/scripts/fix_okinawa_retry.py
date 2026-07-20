#!/usr/bin/env python3
"""沖縄県立中部病院: リトライfalse修正 + サブフロー結果返却 + 孤立削除"""
import json, os, sys, io, copy

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "output/沖縄県立中部病院/fixed/flows"

RETRY_FIXES = {
    "沖縄県立中部病院_RAG検索_20260409.json": {
        "リトライ_相談_問合せ": {"t": "相談_問合せ", "pf": ""},
    },
    "沖縄県立中部病院_生年月日聴取_20260409.json": {
        "リトライ_患者_生年月日": {"t": "患者_生年月日", "pf": ""},
    },
    "沖縄県立中部病院_診療_20260409.json": {
        "リトライ_通院確認": {"t": "通院確認", "pf": ""},
        "リトライ_本人確認": {"t": "Jump_診察券番号聴取", "pf": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"},
        "リトライ_診療科": {"t": "用件確認", "pf": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"},
        "リトライ_用件確認": {"t": "用件確認", "pf": ""},
        "リトライ_現在の予約日_変更": {"t": "理由_変更", "pf": "{tts_g:大変申し訳ございません。うまく聞き取ることができませんでしたので後ほど担当者にて確認いたします。}"},
        "リトライ_理由_変更": {"t": "予約希望日", "pf": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"},
        "リトライ_確認事項": {"t": "Jump_RAG_確認", "pf": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"},
        "リトライ_理由_キャンセル": {"t": "現在の予約日_キャンセル", "pf": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"},
        "リトライ_現在の予約日_キャンセル": {"t": "キャンセル時案内", "pf": "{tts_g:大変申し訳ございません。うまく聞き取ることができませんでしたので後ほど担当者にて確認いたします。}"},
        "リトライ_キャンセル時案内": {"t": "キャンセル時案内", "pf": ""},
        "リトライ_前回の予約日": {"t": "前回の予約日", "pf": ""},
        "リトライ_予約希望日": {"t": "都合悪い日", "pf": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"},
        "リトライ_都合悪い日": {"t": "その他共有事項", "pf": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"},
        "リトライ_その他共有事項": {"t": "Jump_RAG_共有", "pf": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"},
    },
    "沖縄県立中部病院_電話番号聴取_20260409.json": {
        "リトライ_患者_連絡先": {"t": "患者_連絡先", "pf": ""},
        "リトライ_患者_復唱連絡先": {"t": "復唱_患者_連絡先", "pf": ""},
        "リトライ_患者_携帯電話": {"t": "患者_携帯", "pf": ""},
    },
}

SCRIPT_NEXT_COUNT = 12
EMPTY_NEXT = {"condition": "", "label": "", "nextModuleName": ""}

def make_script(name, y):
    return {
        "layout": {"x": 0, "y": y}, "next": [copy.deepcopy(EMPTY_NEXT) for _ in range(SCRIPT_NEXT_COUNT)],
        "subs": [], "name": name, "description": "", "matchingmethod": 1,
        "type": "@General$Script", "params": {"script": "// 結果返却"}
    }

total = 0

# 1. リトライfalse修正
print("=== リトライfalse ===")
for fname, fixes in RETRY_FIXES.items():
    path = os.path.join(BASE, fname)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for rname, fix in fixes.items():
        mod = data["modules"].get(rname)
        if not mod: continue
        for n in mod.get("next", []):
            if n.get("condition") == "false":
                n["nextModuleName"] = fix["t"]
                break
        mod["params"]["prompt_false"] = fix["pf"]
        print(f"  {rname} -> {fix['t']}")
        total += 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 2. サブフロー結果返却スクリプト追加（氏名/生年月日/診察券番号）
print("\n=== サブフロー結果返却 ===")
for fname, success_mod, script_name in [
    ("沖縄県立中部病院_氏名聴取_20260409.json", "openAI_患者_氏名正規化", "script_結果返却_氏名"),
    ("沖縄県立中部病院_生年月日聴取_20260409.json", "入力_患者_生年月日", "script_結果返却_生年月日"),
    ("沖縄県立中部病院_診察券番号聴取_20260409.json", "openAI_患者_診察券番号", "script_結果返却_診察券番号"),
]:
    path = os.path.join(BASE, fname)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    modules = data["modules"]
    if script_name not in modules:
        max_y = max(m.get("layout", {}).get("y", 0) for m in modules.values())
        modules[script_name] = make_script(script_name, max_y + 300)
        print(f"  ADD {script_name}")
        total += 1
    # success/wildcard empty -> script
    if success_mod in modules:
        for n in modules[success_mod].get("next", []):
            c = n.get("condition", "")
            if c in ("^.+$", "^.*$") and not n.get("nextModuleName"):
                n["nextModuleName"] = script_name
                print(f"  FIX {success_mod} {c} -> {script_name}")
                total += 1
    # retry false empty -> script
    for mname, mod in modules.items():
        if "Retry" in mod.get("type", ""):
            for n in mod.get("next", []):
                if n.get("condition") == "false" and not n.get("nextModuleName"):
                    n["nextModuleName"] = script_name
                    print(f"  FIX {mname} false -> {script_name}")
                    total += 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 3. RAG検索: 孤立パス修正
print("\n=== RAG検索 孤立パス ===")
path = os.path.join(BASE, "沖縄県立中部病院_RAG検索_20260409.json")
with open(path, encoding="utf-8") as f:
    data = json.load(f)
modules = data["modules"]
for target_mod, target_dest in [("相談_FAQ失敗", "終話_失敗"), ("終話_失敗", "終話_失敗終了")]:
    if target_mod in modules:
        for n in modules[target_mod].get("next", []):
            if n.get("condition") in ("^.*$", "") and not n.get("nextModuleName"):
                n["nextModuleName"] = target_dest
                print(f"  FIX {target_mod} -> {target_dest}")
                total += 1
for n in modules.get("openAI_相談_問合せ", {}).get("next", []):
    if n.get("condition") in ("^NO_RESULT$", "^無し$") and not n.get("nextModuleName"):
        n["nextModuleName"] = "相談_FAQ失敗"
        print(f"  FIX openAI_相談_問合せ {n['condition']} -> 相談_FAQ失敗")
        total += 1
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 4. メインフロー: 孤立聴取失敗パス削除
print("\n=== 孤立モジュール削除 ===")
path = os.path.join(BASE, "沖縄県立中部病院_診療_20260409.json")
with open(path, encoding="utf-8") as f:
    data = json.load(f)
modules = data["modules"]
for orphan in ["完了フラグ_聴取失敗", "聴取失敗_アナウンス", "Disconnect_聴取失敗"]:
    if orphan in modules:
        referenced = any(
            n.get("nextModuleName") == orphan
            for mname, mod in modules.items() if mname != orphan
            for n in mod.get("next", [])
        )
        if not referenced:
            del modules[orphan]
            print(f"  DEL {orphan}")
            total += 1
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 5. 電話番号聴取: 孤立削除
print("\n=== 電話番号聴取 孤立削除 ===")
path = os.path.join(BASE, "沖縄県立中部病院_電話番号聴取_20260409.json")
with open(path, encoding="utf-8") as f:
    data = json.load(f)
modules = data["modules"]
for orphan in ["完了フラグ_電話番号失敗", "END_電話番号失敗", "Disconnect_電話番号失敗"]:
    if orphan in modules:
        referenced = any(
            n.get("nextModuleName") == orphan
            for mname, mod in modules.items() if mname != orphan
            for n in mod.get("next", [])
        )
        if not referenced:
            del modules[orphan]
            print(f"  DEL {orphan}")
            total += 1
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Remove verify_result from flows
vr = os.path.join(BASE, "verify_result.json")
if os.path.exists(vr):
    os.rename(vr, os.path.join(os.path.dirname(BASE), "_verify_result.json"))

print(f"\n[TOTAL] {total} fixes")
