#!/usr/bin/env python3
"""沖縄県立中部病院: Stage 1追加 + Stage 2 + Stage 5 一括修正"""
import json, os, copy, sys, io

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "output/沖縄県立中部病院/fixed/flows"

# ===== スロット/detection_flag/キー順序 (Stage 1追加) =====
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

# ===== Profile Words =====
PW_YESNO_FULL = "はい はい\nはい はあ\nはい あい\nはい い\nはーい はーい\nええ ええ\nうん うん\nそうです そうです\nそうです おうです\nそうです うです\n合ってます あってます\nあってます ってます\n大丈夫です だいじょうぶです\nだいじょうぶです いじょうぶです\nお願いします おねがいします\nおねがいします ねがいします\nよろしいです よろしいです\nいいです いいです\n問題ないです もんだいないです\nその通りです そのとおりです\nいいえ いいえ\nいいえ いえ\nいいえ いい\n違います ちがいます\nちがいます がいます\n違う ちがう\n間違いです まちがいです\nそうじゃない そうじゃない\n違うんです ちがうんです\nダメ だめ\n1 いち\n2 に"
PW_DATE = "1月 いちがつ\n2月 にがつ\n3月 さんがつ\n4月 しがつ\n5月 ごがつ\n6月 ろくがつ\n7月 しちがつ\n8月 はちがつ\n9月 くがつ\n10月 じゅうがつ\n11月 じゅういちがつ\n12月 じゅうにがつ\n1日 ついたち\n2日 ふつか\n3日 みっか\n4日 よっか\n5日 いつか\n6日 むいか\n7日 なのか\n8日 ようか\n9日 ここのか\n10日 とおか\n11日 じゅういちにち\n12日 じゅうににち\n13日 じゅうさんにち\n14日 じゅうよっか\n15日 じゅうごにち\n16日 じゅうろくにち\n17日 じゅうしちにち\n18日 じゅうはちにち\n19日 じゅうくにち\n20日 はつか\n21日 にじゅういちにち\n22日 にじゅうににち\n23日 にじゅうさんにち\n24日 にじゅうよっか\n25日 にじゅうごにち\n26日 にじゅうろくにち\n27日 にじゅうしちにち\n28日 にじゅうはちにち\n29日 にじゅうくにち\n30日 さんじゅうにち\n31日 さんじゅういちにち\n月曜日 げつようび\n火曜日 かようび\n水曜日 すいようび\n木曜日 もくようび\n金曜日 きんようび\n来週 らいしゅう\n再来週 さらいしゅう\n来月 らいげつ\n今月 こんげつ"
PW_DOB = "令和 れいわ\n平成 へいせい\n昭和 しょうわ\n大正 たいしょう\n西暦 せいれき\n1 いち\n2 に\n3 さん\n4 よん\n4 し\n5 ご\n6 ろく\n7 なな\n7 しち\n8 はち\n9 きゅう\n9 く\n0 ぜろ\n0 れい\n10 じゅう\n1月 いちがつ\n2月 にがつ\n3月 さんがつ\n4月 しがつ\n5月 ごがつ\n6月 ろくがつ\n7月 しちがつ\n8月 はちがつ\n9月 くがつ\n10月 じゅうがつ\n11月 じゅういちがつ\n12月 じゅうにがつ\n1日 ついたち\n2日 ふつか\n3日 みっか\n4日 よっか\n5日 いつか\n6日 むいか\n7日 なのか\n8日 ようか\n9日 ここのか\n10日 とおか\n20日 はつか"
PW_NUMBER = "1 いち\n2 に\n3 さん\n4 よん\n4 し\n5 ご\n6 ろく\n7 なな\n7 しち\n8 はち\n9 きゅう\n9 く\n0 ぜろ\n0 れい\nわからない わからない\n覚えていない おぼえていない\nないです ないです"
PW_PHONE = "1 いち\n2 に\n3 さん\n4 よん\n4 し\n5 ご\n6 ろく\n7 なな\n7 しち\n8 はち\n9 きゅう\n9 く\n0 ぜろ\n0 れい"
PW_FREETEXT = "えーと えーと\nあの あの\nあのー あのー\nえー えー\nそうですね そうですね\nはい はい\nん ん\nんー んー\nわからない わからない\nわかりません わかりません\n体調不良 たいちょうふりょう\n仕事 しごと\n都合が悪い つごうがわるい\n予定が入った よていがはいった\n急用 きゅうよう\n忘れた わすれた\n行けなくなった いけなくなった"
PW_RAG = "えーと えーと\nあの あの\nあのー あのー\nえー えー\nそうですね そうですね\nはい はい\n検査 けんさ\n料金 りょうきん\n持ち物 もちもの\n準備 じゅんび\n予約 よやく\n受付 うけつけ\n駐車場 ちゅうしゃじょう\n時間 じかん\nアクセス あくせす\n場所 ばしょ\n紹介状 しょうかいじょう\n入院 にゅういん"

PW_MAP = {
    # Main
    "入力_通院確認": "はい はい\nはい はあ\nはい あい\nええ ええ\nうん うん\nいいえ いいえ\nいいえ いえ\n初めて はじめて\n初診 しょしん\n再診 さいしん\n通っています かよっています\n通院中 つういんちゅう\nあ通院中 あつういんちゅう\nえ初めて えはじめて\nあの初めて あのはじめて\n1 いち\n2 に",
    "入力_本人確認": "はい はい\nはい はあ\nはい あい\nええ ええ\n本人 ほんにん\n代理 だいり\n家族 かぞく\n本人です ほんにんです\n代理です だいりです\nいいえ いいえ\n家族です かぞくです\nあ本人 あほんにん\nえ代理 えだいり\n1 いち\n2 に",
    "入力_診療科": "内科 ないか\n外科 げか\n整形外科 せいけいげか\n整形 せいけい\n小児科 しょうにか\n産婦人科 さんふじんか\n婦人科 ふじんか\n眼科 がんか\n耳鼻科 じびか\n耳鼻咽喉科 じびいんこうか\n皮膚科 ひふか\n泌尿器科 ひにょうきか\n脳神経外科 のうしんけいげか\n脳外科 のうげか\n消化器内科 しょうかきないか\n循環器内科 じゅんかんきないか\n呼吸器内科 こきゅうきないか\n心臓血管外科 しんぞうけっかんげか\n精神科 せいしんか\nリハビリ りはびり\nリハビリテーション科 りはびりてーしょんか\n放射線科 ほうしゃせんか\n麻酔科 ますいか\nあ内科 あないか\nえ外科 えげか\nあの整形外科 あのせいけいげか\nえーと眼科 えーとがんか\nそうですね耳鼻科 そうですねじびか\n消化器内科 ょうかきないか\n整形外科 いけいげか",
    "入力_用件確認": "予約変更 よやくへんこう\n変更 へんこう\nキャンセル きゃんせる\n取消 とりけし\n確認 かくにん\n問い合わせ といあわせ\n新規予約 しんきよやく\n予約 よやく\n1 いち\n2 に\n3 さん\n4 よん\n1番 いちばん\n2番 にばん\n3番 さんばん\n4番 よんばん\nあ変更 あへんこう\nえキャンセル えきゃんせる\nあの確認 あのかくにん",
    "入力_現在の予約日_変更": PW_DATE,
    "入力_理由_変更": PW_FREETEXT,
    "入力_確認事項": PW_FREETEXT,
    "入力_理由_キャンセル": PW_FREETEXT,
    "入力_現在の予約日_キャンセル": PW_DATE,
    "入力_キャンセル時案内": PW_YESNO_FULL,
    "入力_前回の予約日": PW_DATE,
    "入力_予約希望日": PW_DATE,
    "入力_都合悪い日": PW_DATE + "\nないです ないです\nない ない\n特にありません とくにありません\nなし なし",
    "入力_その他共有事項": PW_FREETEXT + "\nないです ないです\n特にありません とくにありません\nなし なし",
    # Subflows
    "入力_患者_生年月日": PW_DOB,
    "入力_復唱_患者生年月日": PW_YESNO_FULL,
    "入力_患者_診察券番号": PW_NUMBER,
    "入力_患者_携帯電話": PW_YESNO_FULL,
    "入力_患者_連絡先": PW_PHONE,
    "入力_患者_復唱連絡先": PW_YESNO_FULL,
    "入力_相談_問合せ": PW_RAG,
}

# ===== リトライfalse =====
# verify で判明したものを設定（まず verify してからここを埋める）

def process_all():
    total = 0
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
                    old = params.get("detection_flag", "(unset)")
                    params["detection_flag"] = "デフォルト"
                    fixes.append(f"  detection_flag: {mname}")
            # slots
            if mtype in SLOT_COUNTS:
                exp_next, exp_subs = SLOT_COUNTS[mtype]
                cur_next, cur_subs = mod.get("next", []), mod.get("subs", [])
                if len(cur_next) != exp_next:
                    mod["next"] = (cur_next[:exp_next] if len(cur_next) > exp_next
                                   else cur_next + [copy.deepcopy(EMPTY_NEXT) for _ in range(exp_next - len(cur_next))])
                    fixes.append(f"  slots: {mname} next {len(cur_next)}->{exp_next}")
                if len(cur_subs) != exp_subs:
                    mod["subs"] = (cur_subs[:exp_subs] if len(cur_subs) > exp_subs
                                   else cur_subs + [copy.deepcopy(EMPTY_SUB) for _ in range(exp_subs - len(cur_subs))])
                    fixes.append(f"  slots: {mname} subs {len(cur_subs)}->{exp_subs}")
            # profile_words
            if mname in PW_MAP:
                mod["params"]["profile_words"] = PW_MAP[mname]
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

        # self_contained マーカー for RAG検索 and 電話番号聴取
        flow_name = data.get("name", "")
        if "RAG" in flow_name or "電話番号" in flow_name:
            data["desc"] = "termination:self_contained"
            fixes.append(f"  SET termination:self_contained")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"\n=== {fname}: {len(fixes)} fixes ===")
        total += len(fixes)

    print(f"\n[TOTAL] {total} fixes")

process_all()
