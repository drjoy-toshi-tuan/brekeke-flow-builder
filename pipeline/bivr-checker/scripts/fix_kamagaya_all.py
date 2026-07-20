#!/usr/bin/env python3
"""鎌ケ谷総合病院: Stage 1追加 + Stage 2 PW + self_contained + サブフロー結果返却"""
import json, os, copy, sys, io

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "output/鎌ケ谷総合病院/fixed/flows"

SLOT_COUNTS = {
    "@General$Script": (12, 0), "drjoy^Context Logic$ContextMatchRouter": (10, 3),
    "drjoy^AmiVoice$Speech to Text": (11, 3), "drjoy^External Integration$DTMF AmiVoice STT Input": (11, 3),
    "drjoy^External Integration$generate_by_OpenAI": (10, 3), "drjoy^Text To Speech$Speech Retry Counter": (2, 3),
    "drjoy^Text To Speech$Text to speech": (1, 3), "drjoy^Text To Speech$Re-confirmation node data": (1, 3),
    "drjoy^Persistence$saveCompletionFlag2db": (1, 3), "drjoy^Persistence$saveContext2DB": (1, 3),
    "drjoy^Persistence$saveContextModel2DB": (1, 3), "drjoy^Persistence$save2db": (0, 0),
    "drjoy^External Integration$acceptance_times": (4, 3), "drjoy^Incoming$incoming-classifier": (5, 3),
    "drjoy^Custom Module$Custom Jump to Flow": (1, 3), "Custom$wait": (1, 3),
    "@IVR$Disconnect": (0, 0), "drjoy^External Integration$RAG": (4, 3),
    "drjoy^TS Custom Module$DOB Re-confirmation": (4, 3), "drjoy^TS Custom Module$Phone Normalization": (5, 3),
}
EMPTY_NEXT = {"condition": "", "label": "", "nextModuleName": ""}
EMPTY_SUB = {"moduleName": "", "label": ""}
KEY_ORDER = ["layout", "next", "subs", "name", "description", "matchingmethod", "type", "params"]
SCRIPT_NEXT = 12

PW_YESNO_FULL = "はい はい\nはい はあ\nはい あい\nはい い\nはーい はーい\nええ ええ\nうん うん\nそうです そうです\nそうです おうです\nそうです うです\n合ってます あってます\n大丈夫です だいじょうぶです\nお願いします おねがいします\nよろしいです よろしいです\nいいです いいです\nその通りです そのとおりです\nいいえ いいえ\nいいえ いえ\nいいえ いい\n違います ちがいます\nちがいます がいます\n違う ちがう\n間違いです まちがいです\nそうじゃない そうじゃない\nダメ だめ\n1 いち\n2 に"
PW_DATE = "1月 いちがつ\n2月 にがつ\n3月 さんがつ\n4月 しがつ\n5月 ごがつ\n6月 ろくがつ\n7月 しちがつ\n8月 はちがつ\n9月 くがつ\n10月 じゅうがつ\n11月 じゅういちがつ\n12月 じゅうにがつ\n1日 ついたち\n2日 ふつか\n3日 みっか\n4日 よっか\n5日 いつか\n6日 むいか\n7日 なのか\n8日 ようか\n9日 ここのか\n10日 とおか\n11日 じゅういちにち\n12日 じゅうににち\n13日 じゅうさんにち\n14日 じゅうよっか\n15日 じゅうごにち\n16日 じゅうろくにち\n17日 じゅうしちにち\n18日 じゅうはちにち\n19日 じゅうくにち\n20日 はつか\n21日 にじゅういちにち\n22日 にじゅうににち\n23日 にじゅうさんにち\n24日 にじゅうよっか\n25日 にじゅうごにち\n26日 にじゅうろくにち\n27日 にじゅうしちにち\n28日 にじゅうはちにち\n29日 にじゅうくにち\n30日 さんじゅうにち\n31日 さんじゅういちにち\n月曜日 げつようび\n火曜日 かようび\n水曜日 すいようび\n木曜日 もくようび\n金曜日 きんようび\n来週 らいしゅう\n再来週 さらいしゅう\n来月 らいげつ"
PW_DOB = "令和 れいわ\n平成 へいせい\n昭和 しょうわ\n大正 たいしょう\n西暦 せいれき\n1 いち\n2 に\n3 さん\n4 よん\n4 し\n5 ご\n6 ろく\n7 なな\n7 しち\n8 はち\n9 きゅう\n9 く\n0 ぜろ\n0 れい\n10 じゅう\n1月 いちがつ\n2月 にがつ\n3月 さんがつ\n4月 しがつ\n5月 ごがつ\n6月 ろくがつ\n7月 しちがつ\n8月 はちがつ\n9月 くがつ\n10月 じゅうがつ\n11月 じゅういちがつ\n12月 じゅうにがつ\n1日 ついたち\n2日 ふつか\n3日 みっか\n4日 よっか\n5日 いつか\n6日 むいか\n7日 なのか\n8日 ようか\n9日 ここのか\n10日 とおか\n20日 はつか"
PW_NUMBER = "1 いち\n2 に\n3 さん\n4 よん\n4 し\n5 ご\n6 ろく\n7 なな\n7 しち\n8 はち\n9 きゅう\n9 く\n0 ぜろ\n0 れい\nわからない わからない\n覚えていない おぼえていない\nないです ないです"
PW_PHONE = "1 いち\n2 に\n3 さん\n4 よん\n5 ご\n6 ろく\n7 なな\n8 はち\n9 きゅう\n0 ぜろ\n0 れい"
PW_FREETEXT = "えーと えーと\nあの あの\nあのー あのー\nえー えー\nそうですね そうですね\nはい はい\nん ん\nんー んー\nわからない わからない\nわかりません わかりません\n体調不良 たいちょうふりょう\n仕事 しごと\n都合が悪い つごうがわるい\n予定が入った よていがはいった\n急用 きゅうよう\n行けなくなった いけなくなった"
PW_RAG = "えーと えーと\nあの あの\nえー えー\nそうですね そうですね\n検査 けんさ\n料金 りょうきん\n持ち物 もちもの\n予約 よやく\n受付 うけつけ\n駐車場 ちゅうしゃじょう\n時間 じかん\n場所 ばしょ\n紹介状 しょうかいじょう\n入院 にゅういん\n薬 くすり\n保険証 ほけんしょう"

# Read main flow to identify STT/DTMF module names
def get_stt_modules():
    path = os.path.join(BASE, "鎌ケ谷総合病院_診療_20260422.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    stt_mods = {}
    for mname, mod in data["modules"].items():
        mtype = mod.get("type", "")
        if "Speech to Text" in mtype or "DTMF" in mtype:
            pw = mod.get("params", {}).get("profile_words", "")
            count = len([l for l in pw.split("\n") if l.strip()]) if pw else 0
            stt_mods[mname] = {"type": mtype, "pw_count": count}
    return stt_mods

def make_pw_map():
    """動的にPWマッピングを構築"""
    stt = get_stt_modules()
    pw_map = {}
    for mname, info in stt.items():
        if info["pw_count"] > 0:
            continue  # 既に設定済み
        name_lower = mname.lower()
        if "日付" in mname or "予約日" in mname or "希望日" in mname:
            pw_map[mname] = PW_DATE
        elif "理由" in mname or "内容" in mname or "事項" in mname or "症状" in mname:
            pw_map[mname] = PW_FREETEXT
        elif "確認" in mname and "用件" not in mname:
            pw_map[mname] = PW_YESNO_FULL
    # Static mappings for subflows
    pw_map.update({
        "入力_患者_生年月日": PW_DOB,
        "入力_復唱_患者生年月日": PW_YESNO_FULL,
        "入力_患者_診察券番号": PW_NUMBER,
        "入力_患者_携帯電話": PW_YESNO_FULL,
        "入力_患者_連絡先": PW_PHONE,
        "入力_患者_復唱連絡先": PW_YESNO_FULL,
        "入力_相談_問合せ": PW_RAG,
    })
    return pw_map

def make_script(name, y):
    return {
        "layout": {"x": 0, "y": y},
        "next": [copy.deepcopy(EMPTY_NEXT) for _ in range(SCRIPT_NEXT)],
        "subs": [], "name": name, "description": "", "matchingmethod": 1,
        "type": "@General$Script", "params": {"script": "// 結果返却"}
    }

def process_all():
    total = 0
    pw_map = make_pw_map()

    for fname in sorted(os.listdir(BASE)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(BASE, fname)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        fixes = []
        modules = data.get("modules", {})
        new_modules = {}

        for mname, mod in modules.items():
            mtype = mod.get("type", "")
            # detection_flag
            if mtype in ("drjoy^AmiVoice$Speech to Text", "drjoy^External Integration$DTMF AmiVoice STT Input"):
                params = mod.get("params", {})
                if params.get("detection_flag") != "デフォルト":
                    params["detection_flag"] = "デフォルト"
                    fixes.append(f"  detection_flag: {mname}")
            # slots
            if mtype in SLOT_COUNTS:
                en, es = SLOT_COUNTS[mtype]
                cn, cs = mod.get("next", []), mod.get("subs", [])
                if len(cn) != en:
                    mod["next"] = (cn[:en] if len(cn) > en else cn + [copy.deepcopy(EMPTY_NEXT) for _ in range(en - len(cn))])
                    fixes.append(f"  slots: {mname} next {len(cn)}->{en}")
                if len(cs) != es:
                    mod["subs"] = (cs[:es] if len(cs) > es else cs + [copy.deepcopy(EMPTY_SUB) for _ in range(es - len(cs))])
                    fixes.append(f"  slots: {mname} subs {len(cs)}->{es}")
            # pw
            if mname in pw_map:
                cur_pw = mod.get("params", {}).get("profile_words", "")
                cur_count = len([l for l in cur_pw.split("\n") if l.strip()]) if cur_pw else 0
                if cur_count == 0:
                    mod["params"]["profile_words"] = pw_map[mname]
                    fixes.append(f"  pw: {mname}")
            # key order
            ordered = {}
            for key in KEY_ORDER:
                if key in mod:
                    ordered[key] = mod[key]
            for key in mod:
                if key not in ordered:
                    ordered[key] = mod[key]
            new_modules[mname] = ordered

        data["modules"] = new_modules

        # self_contained for RAG/電話番号
        flow_name = data.get("name", "")
        if "RAG" in flow_name or "電話番号" in flow_name:
            data["desc"] = "termination:self_contained"
            fixes.append("  SET termination:self_contained")

        # サブフロー結果返却スクリプト追加
        if any(kw in flow_name for kw in ["氏名", "生年月日", "診察券番号"]):
            script_name = f"script_結果返却_{flow_name.split('$')[-1].split('_')[0] if '$' in flow_name else 'sub'}"
            if script_name not in new_modules:
                max_y = max(m.get("layout", {}).get("y", 0) for m in new_modules.values())
                new_modules[script_name] = make_script(script_name, max_y + 300)
                fixes.append(f"  ADD {script_name}")
            # Fix empty success/false targets
            for mname2, mod2 in new_modules.items():
                mtype2 = mod2.get("type", "")
                if "generate_by_OpenAI" in mtype2:
                    for n in mod2.get("next", []):
                        c = n.get("condition", "")
                        if c in ("^.+$", "^.*$") and not n.get("nextModuleName"):
                            n["nextModuleName"] = script_name
                            fixes.append(f"  FIX {mname2} {c} -> {script_name}")
                if "Speech to Text" in mtype2 or "DTMF" in mtype2:
                    for n in mod2.get("next", []):
                        c = n.get("condition", "")
                        if c == "^.+$" and not n.get("nextModuleName"):
                            n["nextModuleName"] = script_name
                            fixes.append(f"  FIX {mname2} {c} -> {script_name}")
                if "Retry" in mtype2:
                    for n in mod2.get("next", []):
                        if n.get("condition") == "false" and not n.get("nextModuleName"):
                            n["nextModuleName"] = script_name
                            fixes.append(f"  FIX {mname2} false -> {script_name}")

        data["modules"] = new_modules
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"{fname}: {len(fixes)} fixes")
        total += len(fixes)

    # RAG検索: 孤立パス修正
    rag_path = os.path.join(BASE, "鎌ケ谷総合病院_RAG検索_20260422.json")
    if os.path.exists(rag_path):
        with open(rag_path, encoding="utf-8") as f:
            data = json.load(f)
        modules = data["modules"]
        for mod_name in ["相談_FAQ失敗", "終話_失敗"]:
            if mod_name in modules:
                for n in modules[mod_name].get("next", []):
                    if n.get("condition") in ("^.*$", "") and not n.get("nextModuleName"):
                        targets = {"相談_FAQ失敗": "終話_失敗", "終話_失敗": "終話_失敗終了"}
                        if mod_name in targets and targets[mod_name] in modules:
                            n["nextModuleName"] = targets[mod_name]
                            print(f"  RAG FIX: {mod_name} -> {targets[mod_name]}")
                            total += 1
        for n in modules.get("openAI_相談_問合せ", {}).get("next", []):
            if n.get("condition") in ("^NO_RESULT$", "^無し$") and not n.get("nextModuleName"):
                if "相談_FAQ失敗" in modules:
                    n["nextModuleName"] = "相談_FAQ失敗"
                    print(f"  RAG FIX: openAI {n['condition']} -> 相談_FAQ失敗")
                    total += 1
        with open(rag_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n[TOTAL] {total} fixes")

process_all()
