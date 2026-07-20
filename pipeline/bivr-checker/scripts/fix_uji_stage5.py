#!/usr/bin/env python3
"""Stage 5 修正: 宇治徳洲会病院 — リトライfalse + fields + profile_words"""
import json, os, sys, io

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "output/宇治徳洲会病院/fixed/flows"

# ===== 1. リトライfalse修正 =====
RETRY_FIXES = {
    "宇治徳洲会病院_RAG検索_20260410.json": {
        "リトライ_相談_問合せ": {"false_target": "相談_問合せ", "prompt_false": "", "reason": "無限ループ"},
    },
    "宇治徳洲会病院_健診_20260410.json": {
        "リトライ_企業_個人確認": {"false_target": "企業_個人確認", "prompt_false": "", "reason": "無限ループ"},
        "リトライ_企業名": {"false_target": "ジャンプ_氏名聴取_企業", "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}", "reason": "次へ進む"},
        "リトライ_用件確認_企業": {"false_target": "用件確認_企業", "prompt_false": "", "reason": "無限ループ"},
        "リトライ_問合せ内容_企業": {"false_target": "ジャンプ_RAG検索_企業", "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}", "reason": "次へ進む"},
        "リトライ_用件確認_個人": {"false_target": "用件確認_個人", "prompt_false": "", "reason": "無限ループ"},
        "リトライ_変更項目": {"false_target": "変更項目_聴取", "prompt_false": "", "reason": "無限ループ"},
        "リトライ_変更希望内容": {"false_target": "予約日_聴取_変更", "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}", "reason": "次へ進む"},
        "リトライ_予約日_変更": {"false_target": "予約希望日_聴取", "prompt_false": "{tts_g:大変申し訳ございません。うまく聞き取ることができませんでしたので後ほど担当者にて確認いたします。}", "reason": "次へ進む"},
        "リトライ_予約希望日": {"false_target": "ジャンプ_氏名聴取_個人", "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}", "reason": "次へ進む"},
        "リトライ_予約日_キャンセル": {"false_target": "ジャンプ_氏名聴取_個人", "prompt_false": "{tts_g:大変申し訳ございません。うまく聞き取ることができませんでしたので後ほど担当者にて確認いたします。}", "reason": "次へ進む"},
        "リトライ_問合せ内容_個人": {"false_target": "ジャンプ_RAG検索_個人", "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}", "reason": "次へ進む"},
    },
    "宇治徳洲会病院_電話番号聴取_20260410.json": {
        "リトライ_患者_連絡先": {"false_target": "患者_連絡先", "prompt_false": "", "reason": "無限ループ"},
        "リトライ_患者_復唱連絡先": {"false_target": "復唱_患者_連絡先", "prompt_false": "", "reason": "無限ループ"},
        "リトライ_患者_携帯電話": {"false_target": "患者_携帯", "prompt_false": "", "reason": "無限ループ"},
    },
}

# ===== 2. Profile words =====
PW_YESNO = "はい はい\nはい はあ\nはい あい\nはい い\nはーい はーい\nええ ええ\nうん うん\nそうです そうです\nそうです おうです\n大丈夫です だいじょうぶです\nお願いします おねがいします\nいいです いいです\nいいえ いいえ\nいいえ いえ\n違います ちがいます\n違う ちがう\nそうじゃない そうじゃない\n1 いち\n2 に"
PW_YESNO_FULL = "はい はい\nはい はあ\nはい あい\nはい い\nはーい はーい\nええ ええ\nうん うん\nそうです そうです\nそうです おうです\nそうです うです\n合ってます あってます\nあってます ってます\n大丈夫です だいじょうぶです\nだいじょうぶです いじょうぶです\nお願いします おねがいします\nおねがいします ねがいします\nよろしいです よろしいです\nいいです いいです\n問題ないです もんだいないです\nその通りです そのとおりです\nいいえ いいえ\nいいえ いえ\nいいえ いい\n違います ちがいます\nちがいます がいます\n違う ちがう\n間違いです まちがいです\nそうじゃない そうじゃない\n違うんです ちがうんです\nダメ だめ\n1 いち\n2 に"
PW_DATE = "1月 いちがつ\n2月 にがつ\n3月 さんがつ\n4月 しがつ\n5月 ごがつ\n6月 ろくがつ\n7月 しちがつ\n8月 はちがつ\n9月 くがつ\n10月 じゅうがつ\n11月 じゅういちがつ\n12月 じゅうにがつ\n1日 ついたち\n2日 ふつか\n3日 みっか\n4日 よっか\n5日 いつか\n6日 むいか\n7日 なのか\n8日 ようか\n9日 ここのか\n10日 とおか\n11日 じゅういちにち\n12日 じゅうににち\n13日 じゅうさんにち\n14日 じゅうよっか\n15日 じゅうごにち\n16日 じゅうろくにち\n17日 じゅうしちにち\n18日 じゅうはちにち\n19日 じゅうくにち\n20日 はつか\n21日 にじゅういちにち\n22日 にじゅうににち\n23日 にじゅうさんにち\n24日 にじゅうよっか\n25日 にじゅうごにち\n26日 にじゅうろくにち\n27日 にじゅうしちにち\n28日 にじゅうはちにち\n29日 にじゅうくにち\n30日 さんじゅうにち\n31日 さんじゅういちにち\n月曜日 げつようび\n火曜日 かようび\n水曜日 すいようび\n木曜日 もくようび\n金曜日 きんようび\n来週 らいしゅう\n再来週 さらいしゅう\n来月 らいげつ"
PW_DOB = "令和 れいわ\n平成 へいせい\n昭和 しょうわ\n大正 たいしょう\n西暦 せいれき\n1 いち\n2 に\n3 さん\n4 よん\n4 し\n5 ご\n6 ろく\n7 なな\n7 しち\n8 はち\n9 きゅう\n9 く\n0 ぜろ\n0 れい\n10 じゅう\n1月 いちがつ\n2月 にがつ\n3月 さんがつ\n4月 しがつ\n5月 ごがつ\n6月 ろくがつ\n7月 しちがつ\n8月 はちがつ\n9月 くがつ\n10月 じゅうがつ\n11月 じゅういちがつ\n12月 じゅうにがつ\n1日 ついたち\n2日 ふつか\n3日 みっか\n4日 よっか\n5日 いつか\n6日 むいか\n7日 なのか\n8日 ようか\n9日 ここのか\n10日 とおか\n20日 はつか"
PW_NUMBER = "1 いち\n2 に\n3 さん\n4 よん\n4 し\n5 ご\n6 ろく\n7 なな\n7 しち\n8 はち\n9 きゅう\n9 く\n0 ぜろ\n0 れい\nわからない わからない\n覚えていない おぼえていない\n忘れました わすれました\nありません ありません\nないです ないです"
PW_PHONE = "1 いち\n2 に\n3 さん\n4 よん\n4 し\n5 ご\n6 ろく\n7 なな\n7 しち\n8 はち\n9 きゅう\n9 く\n0 ぜろ\n0 れい"

# 企業_個人確認: DTMF — 企業/個人の2択
PW_KIGYO_KOJIN = "企業 きぎょう\n法人 ほうじん\n会社 かいしゃ\n団体 だんたい\n個人 こじん\n個人的に こじんてきに\n自分で じぶんで\n1 いち\n2 に\n1番 いちばん\n2番 にばん\nあ企業 あきぎょう\nえ企業 えきぎょう\nあ個人 あこじん\nえ個人 えこじん\nあの企業 あのきぎょう\nえーと個人 えーとこじん\nそうですね企業 そうですねきぎょう"

# 企業名: STT — フリーテキスト
PW_KIGYO_NAME = "株式会社 かぶしきがいしゃ\n有限会社 ゆうげんがいしゃ\n合同会社 ごうどうがいしゃ\n社団法人 しゃだんほうじん\n財団法人 ざいだんほうじん\nNPO法人 えぬぴーおーほうじん\n医療法人 いりょうほうじん\n学校法人 がっこうほうじん\nあ株式会社 あかぶしきがいしゃ\nえ株式会社 えかぶしきがいしゃ\nあの有限会社 あのゆうげんがいしゃ\nえーと合同会社 えーとごうどうがいしゃ\nそうですね株式会社 そうですねかぶしきがいしゃ\nん株式会社 んかぶしきがいしゃ\nはい株式会社 はいかぶしきがいしゃ"

# 用件確認_企業: DTMF — 新規予約/変更/キャンセル/その他
PW_YOUKEN_KIGYO = "新規予約 しんきよやく\n予約 よやく\n新規 しんき\n変更 へんこう\n予約変更 よやくへんこう\nキャンセル きゃんせる\n取消 とりけし\nその他 そのた\n確認 かくにん\n問い合わせ といあわせ\n1 いち\n2 に\n3 さん\n4 よん\n1番 いちばん\n2番 にばん\n3番 さんばん\n4番 よんばん\nあ新規予約 あしんきよやく\nえ変更 えへんこう\nあのキャンセル あのきゃんせる\nえーとその他 えーとそのた"

# 用件確認_個人: STT — 変更/キャンセル/問い合わせ
PW_YOUKEN_KOJIN = "予約変更 よやくへんこう\n変更 へんこう\n日程変更 にっていへんこう\nキャンセル きゃんせる\n取消 とりけし\nやめたい やめたい\n問い合わせ といあわせ\n確認 かくにん\n聞きたい ききたい\n1 いち\n2 に\n3 さん\n1番 いちばん\n2番 にばん\n3番 さんばん\nあ変更 あへんこう\nえキャンセル えきゃんせる\nあの問い合わせ あのといあわせ\nえーと変更 えーとへんこう"

# 変更項目: DTMF — はい/いいえ (日程/コース)
PW_HENKOU_KOUMOKU = PW_YESNO

# 変更希望内容/問合せ内容: STT — フリーテキスト
PW_FREETEXT = "えーと えーと\nあの あの\nあのー あのー\nえー えー\nそうですね そうですね\nはい はい\nん ん\nんー んー\nわからない わからない\nわかりません わかりません\n体調不良 たいちょうふりょう\n仕事 しごと\n都合が悪い つごうがわるい\n予定が入った よていがはいった\nコース変更 こーすへんこう\n日程変更 にっていへんこう\n検査 けんさ\n料金 りょうきん\n持ち物 もちもの\n駐車場 ちゅうしゃじょう\nアクセス あくせす"

# RAG問合せ: STT
PW_RAG = "えーと えーと\nあの あの\nあのー あのー\nえー えー\nそうですね そうですね\nはい はい\n検査 けんさ\n料金 りょうきん\n持ち物 もちもの\n準備 じゅんび\n食事 しょくじ\n前日 ぜんじつ\n当日 とうじつ\n駐車場 ちゅうしゃじょう\nアクセス あくせす\n時間 じかん\n予約 よやく\nキャンセル きゃんせる\nオプション おぷしょん\n追加検査 ついかけんさ\n結果 けっか"

PW_MAP = {
    # Main flow
    "入力_企業_個人確認": PW_KIGYO_KOJIN,
    "入力_企業名": PW_KIGYO_NAME,
    "入力_用件確認_企業": PW_YOUKEN_KIGYO,
    "入力_問合せ内容_企業": PW_FREETEXT,
    "入力_用件確認_個人": PW_YOUKEN_KOJIN,
    "入力_変更項目": PW_HENKOU_KOUMOKU,
    "入力_変更希望内容": PW_FREETEXT,
    "入力_予約日_変更": PW_DATE,
    "入力_予約希望日": PW_DATE,
    "入力_予約日_キャンセル": PW_DATE,
    "入力_問合せ内容_個人": PW_FREETEXT,
    # RAG subflow
    "入力_相談_問合せ": PW_RAG,
    # 生年月日
    "入力_患者_生年月日": PW_DOB,
    # 診察券番号
    "入力_患者_診察券番号": PW_NUMBER,
    # 電話番号
    "入力_患者_携帯電話": PW_YESNO_FULL,
    "入力_患者_連絡先": PW_PHONE,
    "入力_患者_復唱連絡先": PW_YESNO_FULL,
}

def apply_fixes():
    total = 0

    # Retry false
    print("=== リトライfalse修正 ===")
    for fname in sorted(os.listdir(BASE)):
        if not fname.endswith(".json") or fname not in RETRY_FIXES:
            continue
        path = os.path.join(BASE, fname)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        fixes = RETRY_FIXES[fname]
        for retry_name, fix in fixes.items():
            mod = data["modules"].get(retry_name)
            if not mod:
                continue
            for n in mod.get("next", []):
                if n.get("condition") == "false":
                    n["nextModuleName"] = fix["false_target"]
                    total += 1
                    break
            mod["params"]["prompt_false"] = fix["prompt_false"]
            pf = fix["prompt_false"][:30] if fix["prompt_false"] else "(empty)"
            print(f"  {retry_name}: -> {fix['false_target']} ({fix['reason']}) pf={pf}")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # Profile words
    print("\n=== Profile words ===")
    for fname in sorted(os.listdir(BASE)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(BASE, fname)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        changed = False
        for mname, mod in data.get("modules", {}).items():
            if mname in PW_MAP:
                mod["params"]["profile_words"] = PW_MAP[mname]
                count = len([l for l in PW_MAP[mname].split("\n") if l.strip()])
                print(f"  {mname}: {count} words")
                changed = True
                total += 1
        if changed:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n[TOTAL] {total} fixes")

apply_fixes()
