#!/usr/bin/env python3
"""関越病院_薬剤部 フローJSON & Property.md 修正スクリプト"""

import json
import os
import copy

BASE = "C:/Users/takahashi.s/VSCode/bivr-checker"
INPUT_JSON = os.path.join(BASE, "output/関越病院_薬剤部_20260416.json")
INPUT_PROP = os.path.join(BASE, "input/関越病院_薬剤部/properties_関越病院_薬剤部.md")
OUT_DIR = os.path.join(BASE, "output/関越病院_薬剤部/fixed_v1")
OUT_JSON = os.path.join(OUT_DIR, "関越病院_薬剤部_20260416.json")
OUT_PROP = os.path.join(OUT_DIR, "properties_関越病院_薬剤部.md")

os.makedirs(OUT_DIR, exist_ok=True)

# Load JSON
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

modules = data["modules"]

# ============================================================
# 1-1. Retry matchingmethod: 1 -> 0
# ============================================================
RETRY_TYPE = "drjoy^Text To Speech$Speech Retry Counter"
retry_fixed = 0
for name, mod in modules.items():
    if mod["type"] == RETRY_TYPE:
        mod["matchingmethod"] = 0
        retry_fixed += 1
print(f"1-1. Retry matchingmethod fixed: {retry_fixed} modules")

# ============================================================
# 1-2. ContextMatchRouter nextスロット: 11 -> 10
# ============================================================
CMR_TYPE = "drjoy^Context Logic$ContextMatchRouter"
cmr_names = ["用件分岐1", "用件分岐2", "終話分岐_電話種別"]
for name in cmr_names:
    if name in modules:
        mod = modules[name]
        nexts = mod["next"]
        if len(nexts) == 11:
            # Find and remove empty slot (last one that's empty)
            # Check from end for empty slots
            removed = False
            for i in range(len(nexts) - 1, -1, -1):
                slot = nexts[i]
                if slot.get("condition", "") == "" and slot.get("label", "") == "" and slot.get("nextModuleName", "") == "":
                    nexts.pop(i)
                    removed = True
                    break
            if not removed:
                # If no completely empty slot, remove the last one
                nexts.pop()
            print(f"1-2. {name}: next slots {len(nexts)+1} -> {len(nexts)}")
        else:
            print(f"1-2. {name}: next slots already {len(nexts)}")

# ============================================================
# 1-3. subs スロット数修正
# ============================================================

# save2db: subs=[] and next=[]
SAVE2DB_TYPE = "drjoy^Persistence$save2db"
save2db_fixed = 0
for name, mod in modules.items():
    if mod["type"] == SAVE2DB_TYPE:
        mod["subs"] = []
        mod["next"] = []
        save2db_fixed += 1
print(f"1-3a. save2db subs/next cleared: {save2db_fixed} modules")

# Disconnect: subs=[] and next=[]
DISCONNECT_TYPE = "@IVR$Disconnect"
disc_fixed = 0
for name, mod in modules.items():
    if mod["type"] == DISCONNECT_TYPE:
        mod["subs"] = []
        mod["next"] = []
        disc_fixed += 1
print(f"1-3b. Disconnect subs/next cleared: {disc_fixed} modules")

# 冒頭 wait: subs=0 -> subs=3 empty slots
WAIT_TYPE = "Custom$wait"
for name, mod in modules.items():
    if mod["type"] == WAIT_TYPE:
        if len(mod.get("subs", [])) == 0:
            mod["subs"] = [
                {"moduleName": "", "label": ""},
                {"moduleName": "", "label": ""},
                {"moduleName": "", "label": ""}
            ]
            print(f"1-3c. {name} (wait): subs 0 -> 3")

# ============================================================
# 1-4. ContextMatchRouter デフォルト遷移先修正
# ============================================================

# First, analyze current CMR next arrays
for cmr_name in cmr_names:
    if cmr_name in modules:
        mod = modules[cmr_name]
        print(f"\n--- {cmr_name} current next ---")
        for i, slot in enumerate(mod["next"]):
            print(f"  [{i}] condition={slot.get('condition','')!r} label={slot.get('label','')!r} -> {slot.get('nextModuleName','')!r}")
        print(f"  params keys with 'Value': ", {k: v for k, v in mod["params"].items() if "Value" in k and v})

# 用件分岐1: classification分岐
# 疑義照会/報告 -> 診療科方面, その他問合せ -> 問い合わせ内容_その他
# ^.+$ (Other) -> 用件確認 (設計書: デフォルト: 用件聴取)
if "用件分岐1" in modules:
    mod = modules["用件分岐1"]
    for slot in mod["next"]:
        cond = slot.get("condition", "")
        if cond in ("^.+$", "^.*$"):
            if not slot.get("nextModuleName", ""):
                slot["nextModuleName"] = "用件確認"
                print(f"1-4. 用件分岐1: ^.+$ default -> 用件確認")

# 用件分岐2: 疑義照会/報告の分岐
# 疑義照会 -> 問い合わせ内容_疑義照会, 報告 -> 問い合わせ内容_報告
# ^.+$ (Other) -> 問い合わせ内容_報告
if "用件分岐2" in modules:
    mod = modules["用件分岐2"]
    for slot in mod["next"]:
        cond = slot.get("condition", "")
        if cond in ("^.+$", "^.*$"):
            if not slot.get("nextModuleName", ""):
                slot["nextModuleName"] = "問い合わせ内容_報告"
                print(f"1-4. 用件分岐2: ^.+$ default -> 問い合わせ内容_報告")

# 終話分岐_電話種別: 携帯 -> 折返しあり_入電番号方面, その他 -> 折返しあり_聴取番号方面
# ^.+$ (Other) -> 完了フラグ_折返しあり_聴取番号
if "終話分岐_電話種別" in modules:
    mod = modules["終話分岐_電話種別"]
    for slot in mod["next"]:
        cond = slot.get("condition", "")
        if cond in ("^.+$", "^.*$"):
            if not slot.get("nextModuleName", ""):
                # Find the module that handles 聴取番号 path
                # Look for 完了フラグ_折返しあり_聴取番号 or similar
                target = None
                for mname in modules:
                    if "完了フラグ" in mname and "聴取番号" in mname:
                        target = mname
                        break
                if not target:
                    # Try other patterns
                    for mname in modules:
                        if "折返しあり_聴取番号" in mname and "完了フラグ" in mname:
                            target = mname
                            break
                if not target:
                    # Fallback: look for any 聴取番号 related module
                    for mname in modules:
                        if "聴取番号" in mname:
                            target = mname
                            print(f"  Found potential target: {mname}")
                if target:
                    slot["nextModuleName"] = target
                    print(f"1-4. 終話分岐_電話種別: ^.+$ default -> {target}")
                else:
                    print(f"1-4. WARNING: Could not find 聴取番号 target module")

# ============================================================
# 1-5. callId fields修正
# ============================================================
SCM2DB_TYPE = "drjoy^Persistence$saveContextModel2DB"
for name, mod in modules.items():
    if mod["type"] == SCM2DB_TYPE:
        fields_str = mod["params"].get("fields", "")
        fields = json.loads(fields_str)
        for field in fields:
            if field.get("contextName") == "callId":
                field["itemDefault"] = False
                field["displayType"] = "NUMBER"
                field["editable"] = True
                print(f"1-5. callId: itemDefault=false, displayType=NUMBER, editable=true")

            # 1-6. status rangeValues修正
            if field.get("contextName") == "status":
                field["rangeValues"] = [
                    {"id": "0", "order": 0, "value": "途中切断"},
                    {"id": "1", "order": 1, "value": "未処理"},
                    {"id": "2", "order": 2, "value": "代表案内"},
                    {"id": "3", "order": 3, "value": "転送"},
                    {"id": "6", "order": 4, "value": "時間外"}
                ]
                print(f"1-6. status rangeValues: fixed to 5 values")

        mod["params"]["fields"] = json.dumps(fields, ensure_ascii=False, indent=2)

# ============================================================
# 1-7. 完了フラグ_聴取失敗 status: "3" -> "2"
# ============================================================
if "完了フラグ_聴取失敗" in modules:
    mod = modules["完了フラグ_聴取失敗"]
    if mod["params"].get("status") == "3":
        mod["params"]["status"] = "2"
        print(f"1-7. 完了フラグ_聴取失敗: status 3 -> 2")

# ============================================================
# 1-8. prompt_true スペース追加
# ============================================================
CORRECT_PROMPT_TRUE = "{tts_g:申し訳ございません。 うまく聞き取りが出来ませんでした。 再度、}"
pt_fixed = 0
for name, mod in modules.items():
    if mod["type"] == RETRY_TYPE:
        current = mod["params"].get("prompt_true", "")
        if current and current != CORRECT_PROMPT_TRUE:
            mod["params"]["prompt_true"] = CORRECT_PROMPT_TRUE
            pt_fixed += 1
print(f"1-8. prompt_true space fix: {pt_fixed} modules")

# ============================================================
# 1-9. profile_words設定
# ============================================================

PROFILE_WORDS = {
    "入力_薬局名": (
        "薬局 やっきょく\n"
        "調剤薬局 ちょうざいやっきょく\n"
        "あ薬局 あやっきょく\n"
        "あー薬局 あーやっきょく\n"
        "あの薬局 あのやっきょく\n"
        "え薬局 えやっきょく\n"
        "えー薬局 えーやっきょく\n"
        "えっと薬局 えっとやっきょく\n"
        "ん薬局 んやっきょく\n"
        "はい薬局 はいやっきょく\n"
        "ま薬局 まやっきょく\n"
        "そうですね薬局 そうですねやっきょく\n"
        "です です\n"
        "ですが ですが\n"
        "なんですが なんですが\n"
        "になります になります\n"
        "で で\n"
        "でして でして\n"
        "薬局です やっきょくです\n"
        "薬局ですが やっきょくですが\n"
        "薬局になります やっきょくになります\n"
        "調剤 ちょうざい\n"
        "ドラッグストア どらっぐすとあ"
    ),
    "入力_担当者名": (
        "です です\n"
        "ですが ですが\n"
        "で で\n"
        "になります になります\n"
        "なんですが なんですが\n"
        "でして でして\n"
        "あ あ\n"
        "あー あー\n"
        "あの あの\n"
        "え え\n"
        "えー えー\n"
        "えっと えっと\n"
        "ん ん\n"
        "はい はい\n"
        "ま ま\n"
        "そうですね そうですね\n"
        "と申します ともうします\n"
        "といいます といいます"
    ),
    "入力_用件確認": (
        "1 いち\n"
        "2 に\n"
        "3 さん\n"
        "疑義照会 ぎぎしょうかい\n"
        "報告 ほうこく\n"
        "その他 そのた\n"
        "問合せ といあわせ\n"
        "問い合わせ といあわせ"
    ),
    "入力_診療科": (
        "内科 ないか\n"
        "外科 げか\n"
        "整形外科 せいけいげか\n"
        "リハビリテーション科 りはびりてーしょんか\n"
        "リハビリ りはびり\n"
        "呼吸器内科 こきゅうきないか\n"
        "呼吸器外科 こきゅうきげか\n"
        "消化器内科 しょうかきないか\n"
        "消化器外科 しょうかきげか\n"
        "脳神経内科 のうしんけいないか\n"
        "脳神経外科 のうしんけいげか\n"
        "循環器内科 じゅんかんきないか\n"
        "心臓血管外科 しんぞうけっかんげか\n"
        "歯科口腔外科 しかこうくうげか\n"
        "産科 さんか\n"
        "婦人科 ふじんか\n"
        "小児科 しょうにか\n"
        "泌尿器科 ひにょうきか\n"
        "眼科 がんか\n"
        "耳鼻咽喉科 じびいんこうか\n"
        "整形 せいけい\n"
        "呼吸器 こきゅうき\n"
        "消化器 しょうかき\n"
        "脳神経 のうしんけい\n"
        "循環器 じゅんかんき\n"
        "心臓 しんぞう\n"
        "歯科 しか\n"
        "口腔外科 こうくうげか\n"
        "耳鼻科 じびか\n"
        "あ ないか あないか\n"
        "あー ないか あーないか\n"
        "あの ないか あのないか\n"
        "え ないか えないか\n"
        "えー ないか えーないか\n"
        "えっと ないか えっとないか\n"
        "ん ないか んないか\n"
        "はい ないか はいないか\n"
        "ま ないか まないか\n"
        "そうですね そうですね\n"
        "です です\n"
        "ですが ですが\n"
        "なんですが なんですが\n"
        "になります になります\n"
        "で で\n"
        "内科です ないかです\n"
        "外科です げかです\n"
        "整形外科です せいけいげかです"
    ),
    "入力_問い合わせ内容_疑義照会": (
        "です です\n"
        "ですが ですが\n"
        "で で\n"
        "になります になります\n"
        "なんですが なんですが\n"
        "でして でして\n"
        "あ あ\n"
        "あー あー\n"
        "あの あの\n"
        "え え\n"
        "えー えー\n"
        "えっと えっと\n"
        "ん ん\n"
        "はい はい\n"
        "ま ま\n"
        "そうですね そうですね\n"
        "疑義 ぎぎ\n"
        "照会 しょうかい\n"
        "用量 ようりょう\n"
        "用法 ようほう\n"
        "処方 しょほう\n"
        "薬 くすり\n"
        "変更 へんこう\n"
        "確認 かくにん\n"
        "お薬 おくすり\n"
        "投与量 とうよりょう\n"
        "服用 ふくよう\n"
        "相互作用 そうごさよう\n"
        "禁忌 きんき\n"
        "アレルギー あれるぎー\n"
        "副作用 ふくさよう"
    ),
    "入力_問い合わせ内容_報告": (
        "です です\n"
        "ですが ですが\n"
        "で で\n"
        "になります になります\n"
        "なんですが なんですが\n"
        "でして でして\n"
        "あ あ\n"
        "あー あー\n"
        "あの あの\n"
        "え え\n"
        "えー えー\n"
        "えっと えっと\n"
        "ん ん\n"
        "はい はい\n"
        "ま ま\n"
        "そうですね そうですね\n"
        "報告 ほうこく\n"
        "副作用 ふくさよう\n"
        "変更 へんこう\n"
        "確認 かくにん\n"
        "お薬 おくすり\n"
        "処方 しょほう\n"
        "服用 ふくよう\n"
        "中止 ちゅうし\n"
        "残薬 ざんやく"
    ),
    "入力_問い合わせ内容_その他": (
        "です です\n"
        "ですが ですが\n"
        "で で\n"
        "になります になります\n"
        "なんですが なんですが\n"
        "でして でして\n"
        "あ あ\n"
        "あー あー\n"
        "あの あの\n"
        "え え\n"
        "えー えー\n"
        "えっと えっと\n"
        "ん ん\n"
        "はい はい\n"
        "ま ま\n"
        "そうですね そうですね\n"
        "問い合わせ といあわせ\n"
        "確認 かくにん\n"
        "お薬 おくすり\n"
        "処方 しょほう\n"
        "在庫 ざいこ\n"
        "納品 のうひん"
    ),
    "入力_折返し有無": (
        "はい はい\n"
        "はい はあ\n"
        "はい あい\n"
        "はい い\n"
        "はーい はーい\n"
        "ええ ええ\n"
        "そうです そうです\n"
        "そうです おうです\n"
        "お願いします おねがいします\n"
        "必要です ひつようです\n"
        "お願い おねがい\n"
        "いいえ いいえ\n"
        "いいえ いえ\n"
        "いいえ いい\n"
        "いや いや\n"
        "不要です ふようです\n"
        "大丈夫です だいじょうぶです\n"
        "結構です けっこうです\n"
        "いらない いらない\n"
        "いりません いりません\n"
        "あ はい あはい\n"
        "あー はい あーはい\n"
        "あの はい あのはい\n"
        "え はい えはい\n"
        "えー はい えーはい\n"
        "えっと はい えっとはい\n"
        "ん はい んはい\n"
        "ま はい まはい\n"
        "そうですね そうですね"
    ),
}

pw_fixed = 0
for mod_name, pw_value in PROFILE_WORDS.items():
    if mod_name in modules:
        modules[mod_name]["params"]["profile_words"] = pw_value
        pw_fixed += 1
        print(f"1-9. profile_words set: {mod_name}")
    else:
        print(f"1-9. WARNING: module {mod_name} not found")

print(f"1-9. profile_words total: {pw_fixed} modules")

# ============================================================
# Write fixed JSON
# ============================================================
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"\nJSON written to: {OUT_JSON}")

# ============================================================
# 2. Property.md修正
# ============================================================
with open(INPUT_PROP, "r", encoding="utf-8") as f:
    prop_content = f.read()

# 2-1. 薬局名.prompt修正 (冒頭挨拶を含める)
prop_content = prop_content.replace(
    "薬局名.prompt={tts_g:まず初めに、薬局名をお話ください。}",
    "薬局名.prompt={tts_g:お電話ありがとうございます。 関越病院の疑義紹介専用、AI電話です。 まず初めに、薬局名をお話ください。}"
)
print("2-1. 薬局名.prompt: 冒頭挨拶追加")

# 2-2. TODO解消
prop_content = prop_content.replace(
    "END_非通知.prompt={tts_g:TODO_発話内容を記入}",
    "END_非通知.prompt={tts_g:おそれいりますが、電話番号が通知されていないためお受けできません。 電話番号を通知しておかけ直しください。}"
)
prop_content = prop_content.replace(
    "END_時間外.prompt={tts_g:TODO_発話内容を記入}",
    "END_時間外.prompt={tts_g:お電話ありがとうございます。 ただいまの時間は受付時間外となっております。 受付時間内におかけ直しください。}"
)
prop_content = prop_content.replace(
    "END_聴取失敗.prompt={tts_g:TODO_発話内容を記入}",
    "END_聴取失敗.prompt={tts_g:大変申し訳ございません。 うまく聞き取ることができませんでした。 代表電話番号におかけ直しください。}"
)

# サブフロー用
prop_content = prop_content.replace(
    "患者_診察券番号.prompt={tts_g:TODO_発話内容を記入}",
    "患者_診察券番号.prompt={tts_g:診察券番号をお伺いします。 8桁以内の番号をお話下さい。 番号がわからない場合は、わからない、のようにお話下さい。}"
)
prop_content = prop_content.replace(
    "患者_氏名.prompt={tts_g:TODO_発話内容を記入}",
    "患者_氏名.prompt={tts_g:患者名をフルネームでお話ください。}"
)
prop_content = prop_content.replace(
    "患者_連絡先.prompt={tts_g:TODO_発話内容を記入}",
    "患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお話しください。}"
)
prop_content = prop_content.replace(
    "相談_問合せ.prompt={tts_g:TODO_発話内容を記入}",
    "相談_問合せ.prompt={tts_g:問い合わせ内容をお話ください。}"
)
prop_content = prop_content.replace(
    "相談_問合せループ.prompt={tts_g:TODO_発話内容を記入}",
    "相談_問合せループ.prompt={tts_g:他にご質問がありましたらお話ください。}"
)
prop_content = prop_content.replace(
    "相談_FAQ失敗.prompt={tts_g:TODO_発話内容を記入}",
    "相談_FAQ失敗.prompt={tts_g:ご質問いただいた内容はAI電話ではご対応できませんので、代表電話番号におかけ直しください。}"
)
prop_content = prop_content.replace(
    "終話_失敗.prompt={tts_g:TODO_発話内容を記入}",
    "終話_失敗.prompt={tts_g:大変申し訳ございません。 うまく聞き取ることができませんでした。 代表電話番号におかけ直しください。}"
)
print("2-2. TODO解消完了")

# 2-3. detection_flag修正
prop_content = prop_content.replace(
    "amivoice.detection_flag=音声開始前から検出",
    "amivoice.detection_flag=検出しない"
)
print("2-3. detection_flag: 検出しない")

# Write fixed Property.md
with open(OUT_PROP, "w", encoding="utf-8") as f:
    f.write(prop_content)
print(f"\nProperty.md written to: {OUT_PROP}")

# ============================================================
# Verification summary
# ============================================================
print("\n" + "=" * 60)
print("VERIFICATION SUMMARY")
print("=" * 60)

# Reload and verify
with open(OUT_JSON, "r", encoding="utf-8") as f:
    vdata = json.load(f)

vmods = vdata["modules"]

# Check retry matchingmethod
for name, mod in vmods.items():
    if mod["type"] == RETRY_TYPE:
        assert mod["matchingmethod"] == 0, f"{name} matchingmethod != 0"
print("[OK] All Retry matchingmethod = 0")

# Check CMR next slots
for name in cmr_names:
    if name in vmods:
        assert len(vmods[name]["next"]) == 10, f"{name} next slots != 10: {len(vmods[name]['next'])}"
print("[OK] All ContextMatchRouter next = 10 slots")

# Check save2db
for name, mod in vmods.items():
    if mod["type"] == SAVE2DB_TYPE:
        assert len(mod["subs"]) == 0, f"{name} subs != 0"
        assert len(mod["next"]) == 0, f"{name} next != 0"
print("[OK] All save2db subs=0, next=0")

# Check Disconnect
for name, mod in vmods.items():
    if mod["type"] == DISCONNECT_TYPE:
        assert len(mod["subs"]) == 0, f"{name} subs != 0"
        assert len(mod["next"]) == 0, f"{name} next != 0"
print("[OK] All Disconnect subs=0, next=0")

# Check wait subs
for name, mod in vmods.items():
    if mod["type"] == WAIT_TYPE:
        assert len(mod["subs"]) == 3, f"{name} subs != 3"
print("[OK] wait subs = 3")

# Check CMR defaults
for name in cmr_names:
    if name in vmods:
        has_default = False
        for slot in vmods[name]["next"]:
            if slot.get("condition") in ("^.+$", "^.*$"):
                assert slot.get("nextModuleName", "") != "", f"{name} default nextModuleName is empty"
                has_default = True
        if has_default:
            print(f"[OK] {name} default destination set")

# Check callId
for name, mod in vmods.items():
    if mod["type"] == SCM2DB_TYPE:
        fields = json.loads(mod["params"]["fields"])
        for f in fields:
            if f["contextName"] == "callId":
                assert f["itemDefault"] == False
                assert f["displayType"] == "NUMBER"
                assert f["editable"] == True
print("[OK] callId: itemDefault=false, displayType=NUMBER, editable=true")

# Check status rangeValues
for name, mod in vmods.items():
    if mod["type"] == SCM2DB_TYPE:
        fields = json.loads(mod["params"]["fields"])
        for f in fields:
            if f["contextName"] == "status":
                assert len(f["rangeValues"]) == 5
print("[OK] status rangeValues = 5")

# Check 完了フラグ_聴取失敗
if "完了フラグ_聴取失敗" in vmods:
    assert vmods["完了フラグ_聴取失敗"]["params"]["status"] == "2"
print("[OK] 完了フラグ_聴取失敗 status = 2")

# Check prompt_true
for name, mod in vmods.items():
    if mod["type"] == RETRY_TYPE:
        assert mod["params"]["prompt_true"] == CORRECT_PROMPT_TRUE, f"{name} prompt_true incorrect"
print("[OK] All Retry prompt_true correct")

# Check profile_words
for mod_name in PROFILE_WORDS:
    if mod_name in vmods:
        assert vmods[mod_name]["params"]["profile_words"] != ""
print("[OK] All profile_words set")

print("\n[DONE] All fixes applied and verified successfully.")
