#!/usr/bin/env python3
"""鎌ケ谷総合病院: リトライfalse修正 + 残PW + 孤立削除"""
import json, os, sys, io

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "output/鎌ケ谷総合病院/fixed/flows"

RETRY_FIXES = {
    "鎌ケ谷総合病院_RAG検索_20260422.json": {
        "リトライ_相談_問合せ": {"t": "相談_問合せ", "pf": ""},
    },
    "鎌ケ谷総合病院_生年月日聴取_20260422.json": {
        "リトライ_患者_生年月日": {"t": "患者_生年月日", "pf": ""},
    },
    "鎌ケ谷総合病院_診療_20260422.json": {
        "リトライ_用件確認": {"t": "script_用件確認_群分類", "pf": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"},
        "リトライ_受診歴確認": {"t": "受診歴確認", "pf": ""},
        "リトライ_紹介状確認": {"t": "紹介状確認", "pf": ""},
        "リトライ_診療科_予約": {"t": "氏名聴取", "pf": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"},
        "リトライ_診療科_変更": {"t": "予約日_変更", "pf": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"},
        "リトライ_予約日_変更": {"t": "予約希望日_変更", "pf": "{tts_g:大変申し訳ございません。うまく聞き取ることができませんでしたので後ほど担当者にて確認いたします。}"},
        "リトライ_予約希望日_変更": {"t": "script_当日予約判定_変更", "pf": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"},
        "リトライ_診療科_キャンセル": {"t": "予約日_キャンセル", "pf": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"},
        "リトライ_予約日_キャンセル": {"t": "script_当日予約判定_キャンセル", "pf": "{tts_g:大変申し訳ございません。うまく聞き取ることができませんでしたので後ほど担当者にて確認いたします。}"},
        "リトライ_理由": {"t": "氏名聴取", "pf": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"},
        "リトライ_内容確認": {"t": "診察券番号聴取", "pf": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"},
        "リトライ_その他問合せ": {"t": "その他問合せ", "pf": ""},
    },
    "鎌ケ谷総合病院_電話番号聴取_20260422.json": {
        "リトライ_患者_連絡先": {"t": "患者_連絡先", "pf": ""},
        "リトライ_患者_復唱連絡先": {"t": "復唱_患者_連絡先", "pf": ""},
        "リトライ_患者_携帯電話": {"t": "患者_携帯", "pf": ""},
    },
}

# Empty PW fix — identify from main flow
PW_FREETEXT = "えーと えーと\nあの あの\nあのー あのー\nえー えー\nそうですね そうですね\nはい はい\nん ん\nわからない わからない\n体調不良 たいちょうふりょう\n仕事 しごと\n都合が悪い つごうがわるい\n急用 きゅうよう\n行けなくなった いけなくなった\n予定が入った よていがはいった\nキャンセル きゃんせる"
PW_YOUKEN = "予約 よやく\n新規予約 しんきよやく\n変更 へんこう\nキャンセル きゃんせる\n取消 とりけし\n確認 かくにん\n問い合わせ といあわせ\n1 いち\n2 に\n3 さん\n4 よん\n1番 いちばん\n2番 にばん\n3番 さんばん\n4番 よんばん\nあ予約 あよやく\nえ変更 えへんこう\nあのキャンセル あのきゃんせる"
PW_YESNO = "はい はい\nはい はあ\nはい あい\nええ ええ\nうん うん\nそうです そうです\nいいえ いいえ\nいいえ いえ\n違います ちがいます\nある ある\nあります あります\nない ない\nないです ないです\n1 いち\n2 に"

total = 0

# 1. Retry false
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

# 2. Fill remaining empty PW
print("\n=== Empty PW fix ===")
for fname in sorted(os.listdir(BASE)):
    if not fname.endswith(".json"): continue
    path = os.path.join(BASE, fname)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    changed = False
    for mname, mod in data["modules"].items():
        mtype = mod.get("type", "")
        if "Speech to Text" not in mtype and "DTMF" not in mtype: continue
        pw = mod.get("params", {}).get("profile_words", "")
        if pw and pw.strip(): continue
        # Determine pw by name
        if "用件" in mname:
            mod["params"]["profile_words"] = PW_YOUKEN
        elif "理由" in mname or "内容" in mname or "問合せ" in mname or "共有" in mname:
            mod["params"]["profile_words"] = PW_FREETEXT
        elif "確認" in mname and "用件" not in mname:
            mod["params"]["profile_words"] = PW_YESNO
        elif "診療科" in mname:
            mod["params"]["profile_words"] = "内科 ないか\n外科 げか\n整形外科 せいけいげか\n整形 せいけい\n眼科 がんか\n耳鼻科 じびか\n皮膚科 ひふか\n泌尿器科 ひにょうきか\n産婦人科 さんふじんか\n小児科 しょうにか\n脳外科 のうげか\n消化器内科 しょうかきないか\n循環器内科 じゅんかんきないか\nあ内科 あないか\nえ外科 えげか"
        else:
            mod["params"]["profile_words"] = PW_FREETEXT
        print(f"  {mname} ({fname})")
        changed = True
        total += 1
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

# 3. Delete orphan 聴取失敗 in main flow
print("\n=== 孤立削除 ===")
path = os.path.join(BASE, "鎌ケ谷総合病院_診療_20260422.json")
with open(path, encoding="utf-8") as f:
    data = json.load(f)
modules = data["modules"]
for orphan in ["完了フラグ_聴取失敗", "聴取失敗_アナウンス", "Disconnect_聴取失敗",
               "完了フラグ_電話番号失敗", "END_電話番号失敗", "Disconnect_電話番号失敗"]:
    if orphan not in modules: continue
    referenced = any(
        n.get("nextModuleName") == orphan
        for m in modules.values() if m is not modules.get(orphan)
        for n in m.get("next", [])
    )
    if not referenced:
        del modules[orphan]
        print(f"  DEL {orphan}")
        total += 1
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Same for 電話番号聴取
path2 = os.path.join(BASE, "鎌ケ谷総合病院_電話番号聴取_20260422.json")
with open(path2, encoding="utf-8") as f:
    data2 = json.load(f)
modules2 = data2["modules"]
for orphan in ["完了フラグ_電話番号失敗", "END_電話番号失敗", "Disconnect_電話番号失敗"]:
    if orphan not in modules2: continue
    referenced = any(
        n.get("nextModuleName") == orphan
        for m in modules2.values() if m is not modules2.get(orphan)
        for n in m.get("next", [])
    )
    if not referenced:
        del modules2[orphan]
        print(f"  DEL {orphan} (電話番号)")
        total += 1
with open(path2, "w", encoding="utf-8") as f:
    json.dump(data2, f, ensure_ascii=False, indent=2)

# Remove verify_result
vr = os.path.join(BASE, "verify_result.json")
if os.path.exists(vr): os.remove(vr)

print(f"\n[TOTAL] {total} fixes")
