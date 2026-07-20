"""
佐賀大学医学部附属病院 Stage1 修正スクリプト
CRITICAL/WARNING一括修正
"""
import json
import os
import copy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_FLOW = os.path.join(BASE_DIR, "output/佐賀大学医学部附属病院/extracted/佐賀大学医学部附属病院_診療_20260421.json")
SUB_SHIMEI = os.path.join(BASE_DIR, "output/佐賀大学医学部附属病院/extracted/佐賀大学医学部附属病院_氏名聴取_20260421.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "output/佐賀大学医学部附属病院/fixed/flows")
PROP_SRC = os.path.join(BASE_DIR, "input/佐賀大学医学部附属病院/properties_佐賀大学医学部附属病院_診療.md")
PROP_DST = os.path.join(BASE_DIR, "output/佐賀大学医学部附属病院/fixed/properties_佐賀大学医学部附属病院_診療.md")

os.makedirs(OUTPUT_DIR, exist_ok=True)

fixes_applied = []

def log_fix(code, module, desc):
    fixes_applied.append(f"[{code}] {module}: {desc}")
    print(f"  FIX {code} | {module} | {desc}")

# ============================================================
# MAIN FLOW
# ============================================================
with open(MAIN_FLOW, "r", encoding="utf-8") as f:
    data = json.load(f)

modules = data["modules"]

STT_TYPES = [
    "drjoy^AmiVoice$Speech to Text",
    "drjoy^External Integration$DTMF AmiVoice STT Input",
]
RETRY_TYPE = "drjoy^Text To Speech$Speech Retry Counter"

# --- C-1: detection_flag → デフォルト ---
print("\n=== C-1: detection_flag → デフォルト ===")
for name, mod in modules.items():
    if mod["type"] in STT_TYPES:
        old = mod["params"].get("detection_flag", "")
        if old != "デフォルト":
            mod["params"]["detection_flag"] = "デフォルト"
            log_fix("C-1", name, f"detection_flag: '{old}' → 'デフォルト'")

# --- C-2: Retry matchingmethod → 0 ---
print("\n=== C-2: Retry matchingmethod → 0 ===")
for name, mod in modules.items():
    if mod["type"] == RETRY_TYPE:
        old = mod.get("matchingmethod", 1)
        if old != 0:
            mod["matchingmethod"] = 0
            log_fix("C-2", name, f"matchingmethod: {old} → 0")

# --- C-3: Retry retry_count → 1 ---
print("\n=== C-3: retry_count → 1 ===")
for name, mod in modules.items():
    if mod["type"] == RETRY_TYPE:
        old = mod["params"].get("retry_count", "2")
        if str(old) != "1":
            mod["params"]["retry_count"] = "1"
            log_fix("C-3", name, f"retry_count: {old} → 1")

# --- C-4: smsFlag for fixed phone → -1 ---
print("\n=== C-4: smsFlag (固定電話) → -1 ===")
fixed_phone_flags = {
    "完了フラグ_変更_固定": -1,
    "完了フラグ_キャンセル_固定": -1,
    "完了フラグ_確認_固定": -1,
}
for name, expected_sms in fixed_phone_flags.items():
    if name in modules:
        old = modules[name]["params"].get("smsFlag")
        if old != expected_sms:
            modules[name]["params"]["smsFlag"] = expected_sms
            log_fix("C-4", name, f"smsFlag: {old} → {expected_sms}")

# --- C-5: profile_words 補充 ---
print("\n=== C-5: profile_words 補充 ===")

# 入力_診療科2: 入力_診療科からコピー
src_pw = modules["入力_診療科"]["params"].get("profile_words", "")
for target in ["入力_診療科2"]:
    if target in modules:
        old = modules[target]["params"].get("profile_words", "")
        if not old.strip():
            modules[target]["params"]["profile_words"] = src_pw
            log_fix("C-5", target, f"profile_words: 入力_診療科からコピー ({len(src_pw.splitlines())} lines)")

# 入力_診療科2_心外脳外: 入力_診療科_心外脳外からコピー
for src, dst in [
    ("入力_診療科_心外脳外", "入力_診療科2_心外脳外"),
    ("入力_診療科_ストーマ", "入力_診療科2_ストーマ"),
]:
    if src in modules and dst in modules:
        src_pw = modules[src]["params"].get("profile_words", "")
        old = modules[dst]["params"].get("profile_words", "")
        if not old.strip() and src_pw.strip():
            modules[dst]["params"]["profile_words"] = src_pw
            log_fix("C-5", dst, f"profile_words: {src}からコピー")

# 入力_確認内容: フリーワード用の基本辞書
pw_kakunin = """確認 かくにん
予約確認 よやくかくにん
予約日 よやくび
次回 じかい
次回の予約 じかいのよやく
予約日時 よやくにちじ
教えてほしい おしえてほしい
教えて おしえて
知りたい しりたい
聞きたい ききたい
日程 にってい
日にち ひにち
時間 じかん
いつ いつ
変更したい へんこうしたい
キャンセルしたい きゃんせるしたい
お薬 おくすり
検査 けんさ
結果 けっか
検査結果 けんさけっか
担当医 たんとうい
先生 せんせい
場所 ばしょ
持ち物 もちもの
準備 じゅんび"""
if "入力_確認内容" in modules:
    old = modules["入力_確認内容"]["params"].get("profile_words", "")
    if not old.strip():
        modules["入力_確認内容"]["params"]["profile_words"] = pw_kakunin
        log_fix("C-5", "入力_確認内容", f"profile_words: 確認内容用辞書設定 ({len(pw_kakunin.splitlines())} lines)")

# 入力_キャンセル理由: キャンセル理由用辞書
pw_cancel = """体調不良 たいちょうふりょう
風邪 かぜ
発熱 はつねつ
熱が出た ねつがでた
急用 きゅうよう
仕事 しごと
仕事が入った しごとがはいった
都合が悪い つごうがわるい
都合がつかない つごうがつかない
コロナ ころな
インフルエンザ いんふるえんざ
インフル いんふる
家族 かぞく
子供 こども
急病 きゅうびょう
忘れていた わすれていた
交通機関 こうつうきかん
電車が止まった でんしゃがとまった
他の病院 ほかのびょういん
通院 つういん
転院 てんいん
引っ越し ひっこし
入院 にゅういん
手術 しゅじゅつ
怪我 けが
旅行 りょこう
出張 しゅっちょう"""
if "入力_キャンセル理由" in modules:
    old = modules["入力_キャンセル理由"]["params"].get("profile_words", "")
    if not old.strip():
        modules["入力_キャンセル理由"]["params"]["profile_words"] = pw_cancel
        log_fix("C-5", "入力_キャンセル理由", f"profile_words: キャンセル理由用辞書設定 ({len(pw_cancel.splitlines())} lines)")

# 入力_予約日 / 入力_予約希望日時: 日付辞書の強化
pw_date_add = """令和 れいわ
平成 へいせい
昭和 しょうわ
大正 たいしょう
一月 いちがつ
二月 にがつ
三月 さんがつ
四月 しがつ
五月 ごがつ
六月 ろくがつ
七月 しちがつ
八月 はちがつ
九月 くがつ
十月 じゅうがつ
十一月 じゅういちがつ
十二月 じゅうにがつ
一日 ついたち
二日 ふつか
三日 みっか
四日 よっか
五日 いつか
六日 むいか
七日 なのか
八日 ようか
九日 ここのか
十日 とおか
二十日 はつか
月曜日 げつようび
火曜日 かようび
水曜日 すいようび
木曜日 もくようび
金曜日 きんようび
土曜日 どようび
日曜日 にちようび
来週 らいしゅう
再来週 さらいしゅう
来月 らいげつ
明日 あした
明後日 あさって
わからない わからない
未定 みてい
できるだけ早く できるだけはやく"""

for target in ["入力_予約日", "入力_予約希望日時"]:
    if target in modules:
        old = modules[target]["params"].get("profile_words", "")
        if len(old.strip().splitlines()) < 5:
            modules[target]["params"]["profile_words"] = pw_date_add
            log_fix("C-5/W-5", target, f"profile_words: 日付辞書に強化 ({len(pw_date_add.splitlines())} lines)")

# --- C-6: script_用件上書き_変更 ---
print("\n=== C-6: script_用件上書き_変更 実装 ===")
if "script_用件上書き_変更" in modules:
    modules["script_用件上書き_変更"]["params"]["script"] = '$runner.setResult("変更");'
    log_fix("C-6", "script_用件上書き_変更", "用件上書きスクリプト実装")

# --- C-7: status rangeValues 修正 ---
print("\n=== C-7: saveContextModel2DB fields 修正 ===")
ctx_mod = modules["コンテキスト設定"]
fields = json.loads(ctx_mod["params"]["fields"])

for f in fields:
    # Fix status rangeValues - add 途中切断(0), 転送(3)
    if f["contextName"] == "status":
        f["rangeValues"] = [
            {"id": "0", "value": "途中切断", "order": 0},
            {"id": "1", "value": "未処理", "order": 1},
            {"id": "2", "value": "代表案内", "order": 2},
            {"id": "3", "value": "転送", "order": 3},
            {"id": "6", "value": "時間外", "order": 6},
        ]
        log_fix("C-7", "コンテキスト設定", "status rangeValues: 途中切断(0),転送(3)追加")

    # W-2: classification rangeValues から id 削除
    if f["contextName"] == "classification":
        f["rangeValues"] = [
            {"value": "変更", "order": 1},
            {"value": "キャンセル", "order": 2},
            {"value": "確認", "order": 3},
        ]
        log_fix("W-2", "コンテキスト設定", "classification rangeValues: id削除")

    # clinicalDepartment rangeValues から id 削除 (if present)
    if f["contextName"] == "clinicalDepartment" and f.get("rangeValues"):
        new_rv = []
        for rv in f["rangeValues"]:
            new_rv.append({"value": rv["value"], "order": rv["order"]})
        if any("id" in rv for rv in f["rangeValues"]):
            f["rangeValues"] = new_rv
            log_fix("W-2", "コンテキスト設定", "clinicalDepartment rangeValues: id削除")

    # W-3: 標準フィールド属性修正
    STANDARD_FIELDS = {
        "classification": {"deletable": False, "editable": True, "itemDefault": True},
        "patientName": {"deletable": False, "editable": True, "itemDefault": True},
        "medicalCardNumber": {"deletable": False, "editable": True, "itemDefault": True},
        "patientDateOfBirth": {"deletable": False, "editable": True, "itemDefault": True},
        "telephoneNumber": {"deletable": False, "editable": False, "itemDefault": True},
        "additionalPhoneNumber": {"deletable": False, "editable": True, "itemDefault": True},
        "clinicalDepartment": {"deletable": False, "editable": True, "itemDefault": True},
        "status": {"deletable": False, "editable": True, "itemDefault": True},
        "dateOfCall": {"deletable": False, "editable": False, "itemDefault": True},
    }
    if f["contextName"] in STANDARD_FIELDS:
        expected = STANDARD_FIELDS[f["contextName"]]
        changed = False
        for k, v in expected.items():
            if f.get(k) != v:
                f[k] = v
                changed = True
        if changed:
            log_fix("W-3", "コンテキスト設定", f"{f['contextName']}: 標準フィールド属性修正")

    # callId: displayType TEXT → NUMBER, deletable=True, itemDefault=False
    if f["contextName"] == "callId":
        if f["displayType"] != "NUMBER":
            f["displayType"] = "NUMBER"
            log_fix("W-3", "コンテキスト設定", "callId: displayType TEXT → NUMBER")
        f["deletable"] = True
        f["itemDefault"] = False

    # reservationDate: 標準フィールド (itemDefault=True)
    if f["contextName"] == "reservationDate":
        if f.get("itemDefault") != True:
            f["itemDefault"] = True
            f["deletable"] = False
            log_fix("W-3", "コンテキスト設定", "reservationDate: itemDefault=True, deletable=False")

    # reason: 標準フィールド (itemDefault=True)
    if f["contextName"] == "reason":
        if f.get("itemDefault") != True:
            f["itemDefault"] = True
            f["deletable"] = False
            log_fix("W-3", "コンテキスト設定", "reason: itemDefault=True, deletable=False")

# W-6: 不足フィールド追加
existing_names = {f["contextName"] for f in fields}
missing_fields = []

if "checkout" not in existing_names:
    missing_fields.append({
        "contextName": "checkout",
        "contextNameJp": "途中切断項目",
        "displayType": "TEXT",
        "rangeValues": [],
        "editable": True,
        "deletable": True,
        "itemDefault": False
    })

if "Incoming_date" not in existing_names:
    missing_fields.append({
        "contextName": "Incoming_date",
        "contextNameJp": "着信日時",
        "displayType": "TEXT",
        "rangeValues": [],
        "editable": False,
        "deletable": True,
        "itemDefault": False
    })

if "check_date" not in existing_names:
    missing_fields.append({
        "contextName": "check_date",
        "contextNameJp": "予約希望日判定",
        "displayType": "TEXT",
        "rangeValues": [],
        "editable": True,
        "deletable": True,
        "itemDefault": False
    })

if "history" not in existing_names:
    missing_fields.append({
        "contextName": "history",
        "contextNameJp": "受診歴",
        "displayType": "TEXT",
        "rangeValues": [],
        "editable": True,
        "deletable": True,
        "itemDefault": False
    })

if "institution" not in existing_names:
    missing_fields.append({
        "contextName": "institution",
        "contextNameJp": "紹介元医療機関名",
        "displayType": "TEXT",
        "rangeValues": [],
        "editable": True,
        "deletable": True,
        "itemDefault": False
    })

if "introduction" not in existing_names:
    missing_fields.append({
        "contextName": "introduction",
        "contextNameJp": "紹介状",
        "displayType": "TEXT",
        "rangeValues": [],
        "editable": True,
        "deletable": True,
        "itemDefault": False
    })

if "disease" not in existing_names:
    missing_fields.append({
        "contextName": "disease",
        "contextNameJp": "病名",
        "displayType": "TEXT",
        "rangeValues": [],
        "editable": True,
        "deletable": True,
        "itemDefault": False
    })

if "symptoms" not in existing_names:
    missing_fields.append({
        "contextName": "symptoms",
        "contextNameJp": "症状",
        "displayType": "TEXT",
        "rangeValues": [],
        "editable": True,
        "deletable": True,
        "itemDefault": False
    })

for mf in missing_fields:
    fields.append(mf)
    log_fix("W-6", "コンテキスト設定", f"fields追加: {mf['contextName']} ({mf['contextNameJp']})")

# fields を JSON文字列に戻す (indent=2)
ctx_mod["params"]["fields"] = json.dumps(fields, ensure_ascii=False, indent=2)

# --- C-8: OpenAI_診療科/診療科2 の next 修正 ---
# しんげ → 心外脳外 のルーティングは OpenAI プロンプトが "しんげ" を出力する設計。
# next に ^心外$, ^神外$ があるのは、STT入力で直接 "心外" "神外" が来た場合への対応。
# ただしこれは STT → OpenAI の流れなので、OpenAI出力が "しんげ" "心外" "神外" のいずれも出しうる設計。
# プロンプト出力仕様にこれらを追加するのが正しい。
print("\n=== C-8: OpenAI_診療科/診療科2 プロンプト修正 ===")
for oai_name in ["OpenAI_診療科", "OpenAI_診療科2"]:
    if oai_name in modules:
        prompt = modules[oai_name]["params"].get("prompt", "")
        # "しんげ" の出力仕様に "心外" "神外" も追加
        if "心外" not in prompt.split("しんげ")[-1][:100] if "しんげ" in prompt else True:
            # プロンプトの出力仕様セクションで "しんげ" の行を探して拡張
            if "- しんげ" in prompt:
                prompt = prompt.replace(
                    "- しんげ",
                    "- しんげ：入電者が「しんげ」「心外」「神外」と発話した場合。「心外」「神外」もこの値として出力すること"
                )
                log_fix("C-8", oai_name, "プロンプト出力仕様に心外/神外を明記")
            # 別の形式の場合
            elif "しんげ" in prompt and "心外" not in prompt:
                # next条件側を修正: ^心外$ → 削除して ^しんげ$ のワイルドキャッチに任せる
                pass
        modules[oai_name]["params"]["prompt"] = prompt

# --- W-4: 完了フラグ_非通知 status 確認 ---
# 設計書では checkpoint=7, status=7 だが、Brekeke標準のstatusに7はない
# saveCompletionFlag2db は status=2(代表案内) のままとし、
# OpenAIコンテキストレベルで status=7 を管理する設計と判断
# → 修正しない（設計判断が必要なためスキップ）
print("\n=== W-4: 完了フラグ_非通知 → スキップ（設計確認必要） ===")

# --- W-7: Property.md detection_flag ---
# Property.md は別途修正

# --- W-9: script_用件上書き_変更 layout ---
print("\n=== W-9: script_用件上書き_変更 layout修正 ===")
if "script_用件上書き_変更" in modules:
    # キャンセルルート内なので、変更確認の近くに配置
    # 変更確認のlayoutを基準に
    henkou_kakunin = modules.get("変更確認")
    if henkou_kakunin:
        base_x = henkou_kakunin["layout"]["x"]
        base_y = henkou_kakunin["layout"]["y"]
        modules["script_用件上書き_変更"]["layout"]["x"] = base_x + 400
        modules["script_用件上書き_変更"]["layout"]["y"] = base_y + 600
        log_fix("W-9", "script_用件上書き_変更", f"layout修正: 変更確認の近くに移動")

# ============================================================
# SAVE MAIN FLOW
# ============================================================
out_main = os.path.join(OUTPUT_DIR, "佐賀大学医学部附属病院_診療_20260421.json")
with open(out_main, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"\n[OK] メインフロー保存: {out_main}")

# ============================================================
# SUBFLOW: 氏名聴取 (C-9)
# ============================================================
print("\n=== C-9: 氏名聴取サブフロー修正 ===")
with open(SUB_SHIMEI, "r", encoding="utf-8") as f:
    sub_data = json.load(f)

sub_modules = sub_data["modules"]

# STT-003: 入力_患者_氏名 の success 遷移先が空
stt_mod = sub_modules["入力_患者_氏名"]
for n in stt_mod["next"]:
    if n["condition"] == "^.+$" and not n["nextModuleName"]:
        # success → script_結果返却_氏名 に遷移（まずスクリプトを追加）
        n["nextModuleName"] = "script_結果返却_氏名"
        log_fix("C-9/STT-003", "入力_患者_氏名", "success遷移先: script_結果返却_氏名")

# Retry false 遷移先も空 → script_結果返却_氏名
retry_mod = sub_modules["リトライ_患者_氏名"]
for n in retry_mod["next"]:
    if n["condition"] == "false" and not n["nextModuleName"]:
        n["nextModuleName"] = "script_結果返却_氏名"
        log_fix("C-9/R-002", "リトライ_患者_氏名", "false遷移先: script_結果返却_氏名")

# Retry matchingmethod → 0
if retry_mod.get("matchingmethod", 1) != 0:
    retry_mod["matchingmethod"] = 0
    log_fix("C-2", "リトライ_患者_氏名", "matchingmethod → 0")

# detection_flag
if stt_mod["params"].get("detection_flag") != "デフォルト":
    stt_mod["params"]["detection_flag"] = "デフォルト"
    log_fix("C-1", "入力_患者_氏名", "detection_flag → デフォルト")

# SCR-002: 結果返却スクリプト追加
# 氏名聴取の最後のモジュールのlayoutから算出
last_y = max(m["layout"]["y"] for m in sub_modules.values())
script_result = {
    "name": "script_結果返却_氏名",
    "description": "",
    "matchingmethod": 1,
    "type": "@General$Script",
    "params": {
        "script": '$runner.setResult($runner.getModuleResult("入力_患者_氏名"));'
    },
    "next": [
        {"condition": "", "label": "", "nextModuleName": ""},
        {"condition": "", "label": "", "nextModuleName": ""},
        {"condition": "", "label": "", "nextModuleName": ""},
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
    "subs": [],
    "layout": {"x": 0, "y": last_y + 300}
}
sub_modules["script_結果返却_氏名"] = script_result
log_fix("C-9/SCR-002", "script_結果返却_氏名", "結果返却スクリプト追加")

out_sub = os.path.join(OUTPUT_DIR, "佐賀大学医学部附属病院_氏名聴取_20260421.json")
with open(out_sub, "w", encoding="utf-8") as f:
    json.dump(sub_data, f, ensure_ascii=False, indent=2)
print(f"[OK] 氏名聴取サブフロー保存: {out_sub}")

# ============================================================
# Property.md 修正 (W-7)
# ============================================================
print("\n=== W-7: Property.md修正 ===")
with open(PROP_SRC, "r", encoding="utf-8") as f:
    prop_content = f.read()

# detection_flag: 音声開始前から検出 → 検出しない
prop_content = prop_content.replace(
    "amivoice.detection_flag=音声開始前から検出",
    "amivoice.detection_flag=検出しない"
)
log_fix("W-7", "Property.md", "detection_flag: 音声開始前から検出 → 検出しない")

os.makedirs(os.path.dirname(PROP_DST), exist_ok=True)
with open(PROP_DST, "w", encoding="utf-8") as f:
    f.write(prop_content)
print(f"[OK] Property.md保存: {PROP_DST}")

# ============================================================
# SUMMARY
# ============================================================
print(f"\n{'='*60}")
print(f"修正完了: {len(fixes_applied)} 件")
print(f"{'='*60}")
for fix in fixes_applied:
    print(f"  {fix}")
