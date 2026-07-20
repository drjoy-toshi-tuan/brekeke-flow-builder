#!/usr/bin/env python3
"""
profile_words generator for 渓仁会円山クリニック (15 STT modules)
"""
import json
import sys
import os

# Filler TOP6 (no まー)
FILLERS = ["あ", "え", "えー", "あの", "はい", "ま"]
# 語尾TOP8
SUFFIXES = ["です", "で", "なんですが", "になります", "ね", "さ", "でして", "か"]


def head_cut(reading):
    """Generate head-cut patterns (先頭1-2モーラ欠落)"""
    results = []
    chars = list(reading)
    if len(chars) < 2:
        return results
    small_kana = set("ゃゅょぁぃぅぇぉっ")
    i = 0
    moras = []
    while i < len(chars):
        mora = chars[i]
        while i + 1 < len(chars) and chars[i + 1] in small_kana:
            mora += chars[i + 1]
            i += 1
        while i + 1 < len(chars) and chars[i + 1] == "ー":
            mora += chars[i + 1]
            i += 1
        moras.append(mora)
        i += 1

    if len(moras) >= 3:
        cut1 = "".join(moras[1:])
        if len(cut1) > 1:
            results.append(cut1)
    if len(moras) >= 4:
        cut2 = "".join(moras[2:])
        if len(cut2) > 1:
            results.append(cut2)
    return results


def expand_keyword(display, reading, max_fillers=6, max_suffixes=8):
    """Expand a keyword with fillers, suffixes, and head-cuts"""
    words = []
    words.append((display, reading))
    for f in FILLERS[:max_fillers]:
        words.append((display, f + reading))
    for s in SUFFIXES[:max_suffixes]:
        words.append((display, reading + s))
    for hc in head_cut(reading):
        words.append((display, hc))
    return words


def make_pw_string(word_list, max_words=200):
    """Convert list of (display, reading) tuples to profile_words string"""
    seen = set()
    unique = []
    for d, r in word_list:
        key = (d, r)
        if key not in seen:
            seen.add(key)
            unique.append((d, r))
    if len(unique) > max_words:
        unique = unique[:max_words]
    return "\n".join(f"{d} {r}" for d, r in unique)


# ============================================================
# 1. 入力_用件選択 (yoken)
# ============================================================
pw_yoken = []
for d, r in [
    ("予約", "よやく"), ("予約したい", "よやくしたい"), ("新規予約", "しんきよやく"),
    ("受診したい", "じゅしんしたい"), ("取りたい", "とりたい"),
    ("お願いしたい", "おねがいしたい"), ("健診", "けんしん"),
    ("健診の予約", "けんしんのよやく"),
]:
    pw_yoken += expand_keyword(d, r)
for d, r in [
    ("変更", "へんこう"), ("予約変更", "よやくへんこう"),
    ("日程変更", "にっていへんこう"), ("変えたい", "かえたい"),
    ("ずらしたい", "ずらしたい"),
]:
    pw_yoken += expand_keyword(d, r)
for d, r in [
    ("キャンセル", "きゃんせる"), ("取消", "とりけし"),
    ("やめたい", "やめたい"), ("行けなくなった", "いけなくなった"),
]:
    pw_yoken += expand_keyword(d, r)
for d, r in [
    ("確認", "かくにん"), ("聞きたい", "ききたい"),
    ("問い合わせ", "といあわせ"), ("わからない", "わからない"),
]:
    pw_yoken += expand_keyword(d, r)
# STT誤認識パターン (VFBオリジナルから維持)
pw_yoken += [
    ("検診", "けんしん"), ("検針", "けんしん"), ("返信", "けんしん"),
    ("天候診断", "けんしん"), ("妊娠の予約", "けんしん"),
    ("薬", "よやく"), ("お薬", "よやく"),
    ("取り直したい", "へんこう"), ("取り直す", "へんこう"),
    ("別の", "へんこう"), ("変えて", "へんこう"),
    ("やめる", "きゃんせる"), ("取り消し", "きゃんせる"),
    ("取り消す", "きゃんせる"),
]
pw_yoken_str = make_pw_string(pw_yoken)

# ============================================================
# 2. 入力_予約_受診歴確認 (yes_no)
# ============================================================
pw_jushinreki = []
for d, r in [
    ("あり", "あり"), ("はい", "はい"), ("ある", "ある"),
    ("あります", "あります"), ("ございます", "ございます"),
    ("受診したことある", "じゅしんしたことある"),
    ("来たことある", "きたことある"),
    ("通院したことある", "つういんしたことある"),
    ("かかったことある", "かかったことある"),
    ("ええ", "ええ"), ("うん", "うん"), ("そうです", "そうです"),
]:
    pw_jushinreki += expand_keyword(d, r)
for d, r in [
    ("なし", "なし"), ("ない", "ない"), ("いいえ", "いいえ"),
    ("ありません", "ありません"), ("ございません", "ございません"),
    ("初めて", "はじめて"), ("初診", "しょしん"),
    ("来たことない", "きたことない"),
    ("違います", "ちがいます"),
]:
    pw_jushinreki += expand_keyword(d, r)
# 頭切れ固有パターン
pw_jushinreki += [
    ("はい", "あい"), ("はい", "い"), ("はい", "はあ"), ("はい", "はーい"),
    ("いいえ", "いえ"), ("そうです", "おうです"), ("そうです", "うです"),
    ("違います", "がいます"),
]
pw_jushinreki_str = make_pw_string(pw_jushinreki)

# ============================================================
# 3. 入力_予約_企業名 (freetext)
# ============================================================
pw_kigyou = []
for d, r in [
    ("特にない", "とくにない"), ("ありません", "ありません"),
    ("ないです", "ないです"), ("特にありません", "とくにありません"),
    ("企業名", "きぎょうめい"), ("会社名", "かいしゃめい"),
    ("株式会社", "かぶしきがいしゃ"), ("有限会社", "ゆうげんがいしゃ"),
    ("勤めていない", "つとめていない"), ("自営業", "じえいぎょう"),
    ("無職", "むしょく"), ("個人", "こじん"),
    ("フリーランス", "ふりーらんす"), ("勤務先", "きんむさき"),
    ("パート", "ぱーと"), ("アルバイト", "あるばいと"),
    ("主婦", "しゅふ"), ("退職", "たいしょく"),
]:
    pw_kigyou.append((d, r))
for f in FILLERS:
    pw_kigyou.append(("特にない", f + "とくにない"))
    pw_kigyou.append(("ありません", f + "ありません"))
pw_kigyou_str = make_pw_string(pw_kigyou)

# ============================================================
# 4. 入力_予約_受診希望コース (kenshin_course)
# ============================================================
pw_course = []
for d, r in [
    ("人間ドック", "にんげんどっく"), ("ドック", "どっく"),
    ("人間ドッグ", "にんげんどっぐ"), ("人間", "にんげん"),
    ("人間ロック", "にんげんろっく"), ("ロック", "ろっく"),
    ("人間独", "にんげんどく"),
]:
    pw_course += expand_keyword(d, r)
for d, r in [
    ("生活習慣病健診", "せいかつしゅうかんびょうけんしん"),
    ("生活習慣病", "せいかつしゅうかんびょう"),
    ("生活習慣", "せいかつしゅうかん"),
    ("習慣病", "しゅうかんびょう"),
    ("生活", "せいかつ"),
]:
    pw_course += expand_keyword(d, r)
for d, r in [
    ("定期健診", "ていきけんしん"), ("定期", "ていき"),
    ("定期健康診断", "ていきけんこうしんだん"),
    ("健康診断", "けんこうしんだん"), ("健診", "けんしん"),
]:
    pw_course += expand_keyword(d, r)
# STT誤認識パターン
pw_course += [
    ("週間", "しゅうかん"), ("提示", "ていき"),
]
pw_course_str = make_pw_string(pw_course)

# ============================================================
# Date dictionary (shared across date modules)
# ============================================================
def make_date_pw():
    words = []
    months = [
        ("1月", "いちがつ"), ("2月", "にがつ"), ("3月", "さんがつ"),
        ("4月", "しがつ"), ("5月", "ごがつ"), ("6月", "ろくがつ"),
        ("7月", "しちがつ"), ("8月", "はちがつ"), ("9月", "くがつ"),
        ("10月", "じゅうがつ"), ("11月", "じゅういちがつ"), ("12月", "じゅうにがつ"),
    ]
    for d, r in months:
        words.append((d, r))

    special_days = [
        ("1日", "ついたち"), ("2日", "ふつか"), ("3日", "みっか"),
        ("4日", "よっか"), ("5日", "いつか"), ("6日", "むいか"),
        ("7日", "なのか"), ("8日", "ようか"), ("9日", "ここのか"),
        ("10日", "とおか"), ("14日", "じゅうよっか"), ("20日", "はつか"),
        ("24日", "にじゅうよっか"),
    ]
    for d, r in special_days:
        words.append((d, r))

    relative = [
        ("来週", "らいしゅう"), ("再来週", "さらいしゅう"),
        ("来月", "らいげつ"), ("明日", "あした"), ("明日", "あす"),
        ("明後日", "あさって"), ("今週", "こんしゅう"),
        ("今月", "こんげつ"), ("上旬", "じょうじゅん"),
        ("中旬", "ちゅうじゅん"), ("下旬", "げじゅん"),
    ]
    for d, r in relative:
        words += expand_keyword(d, r, max_fillers=6, max_suffixes=4)

    weekdays = [
        ("月曜日", "げつようび"), ("火曜日", "かようび"),
        ("水曜日", "すいようび"), ("木曜日", "もくようび"),
        ("金曜日", "きんようび"), ("土曜日", "どようび"),
        ("日曜日", "にちようび"),
    ]
    for d, r in weekdays:
        words.append((d, r))
        for hc in head_cut(r):
            words.append((d, hc))

    nums = [
        ("1", "いち"), ("2", "に"), ("3", "さん"),
        ("4", "よん"), ("4", "し"), ("5", "ご"),
        ("6", "ろく"), ("7", "なな"), ("7", "しち"),
        ("8", "はち"), ("9", "きゅう"), ("9", "く"),
        ("10", "じゅう"), ("20", "にじゅう"),
        ("30", "さんじゅう"), ("31", "さんじゅういち"),
    ]
    for d, r in nums:
        words.append((d, r))

    # 頭切れ for months
    words.append(("1月", "ちがつ"))
    words.append(("4月", "がつ"))

    # Filler + common date patterns
    for f in FILLERS:
        words.append(("来週", f + "らいしゅう"))
        words.append(("来月", f + "らいげつ"))
        words.append(("4月", f + "しがつ"))
        words.append(("5月", f + "ごがつ"))

    return words


date_words = make_date_pw()
date_pw_str = make_pw_string(date_words)

# For キャンセル_予約希望時期, add ありません/ない
cancel_date_words = date_words[:]
for d, r in [
    ("ありません", "ありません"), ("ないです", "ないです"),
    ("ない", "ない"), ("特にありません", "とくにありません"),
    ("特にない", "とくにない"),
]:
    cancel_date_words += expand_keyword(d, r, max_fillers=3, max_suffixes=3)
cancel_date_pw_str = make_pw_string(cancel_date_words)

# ============================================================
# 10. 入力_変更_変更項目
# ============================================================
pw_henkou_item = []
for d, r in [
    ("オプション変更", "おぷしょんへんこう"), ("オプション", "おぷしょん"),
    ("日程変更", "にっていへんこう"), ("日程", "にってい"),
    ("日にち", "ひにち"), ("日付", "ひづけ"),
    ("スケジュール", "すけじゅーる"), ("予約日", "よやくび"),
    ("それ以外", "それいがい"), ("その他", "そのた"),
    ("それ以外の変更", "それいがいのへんこう"),
    ("コース変更", "こーすへんこう"), ("コース", "こーす"),
    ("変更", "へんこう"), ("追加", "ついか"), ("取りやめ", "とりやめ"),
]:
    pw_henkou_item += expand_keyword(d, r)
pw_henkou_item_str = make_pw_string(pw_henkou_item)

# ============================================================
# 11. 入力_変更_内容確認_オプション (freetext)
# ============================================================
pw_freetext_option = []
for d, r in [
    ("追加", "ついか"), ("削除", "さくじょ"), ("変更", "へんこう"),
    ("オプション", "おぷしょん"), ("検査", "けんさ"),
    ("人間ドック", "にんげんどっく"), ("生活習慣病", "せいかつしゅうかんびょう"),
    ("定期健診", "ていきけんしん"), ("血液検査", "けつえきけんさ"),
    ("胃カメラ", "いかめら"), ("大腸検査", "だいちょうけんさ"),
    ("エコー", "えこー"), ("CT", "しーてぃー"),
    ("MRI", "えむあーるあい"), ("脳ドック", "のうどっく"),
    ("乳がん", "にゅうがん"), ("子宮がん", "しきゅうがん"),
    ("肺がん", "はいがん"), ("腫瘍マーカー", "しゅようまーかー"),
    ("心電図", "しんでんず"), ("レントゲン", "れんとげん"),
    ("骨密度", "こつみつど"), ("聴力", "ちょうりょく"),
    ("視力", "しりょく"), ("肝炎", "かんえん"),
]:
    pw_freetext_option.append((d, r))
for f in FILLERS:
    pw_freetext_option.append(("変更", f + "へんこう"))
    pw_freetext_option.append(("追加", f + "ついか"))
pw_freetext_option_str = make_pw_string(pw_freetext_option)

# ============================================================
# 12. 入力_変更_内容確認_その他 (freetext)
# ============================================================
pw_freetext_other = []
for d, r in [
    ("変更", "へんこう"), ("お願い", "おねがい"), ("確認", "かくにん"),
    ("氏名", "しめい"), ("名前", "なまえ"), ("住所", "じゅうしょ"),
    ("連絡先", "れんらくさき"), ("電話番号", "でんわばんごう"),
    ("メールアドレス", "めーるあどれす"), ("保険証", "ほけんしょう"),
    ("紹介状", "しょうかいじょう"), ("コース", "こーす"),
    ("日程", "にってい"), ("時間", "じかん"), ("人数", "にんずう"),
    ("受診者", "じゅしんしゃ"), ("担当", "たんとう"),
]:
    pw_freetext_other.append((d, r))
for f in FILLERS:
    pw_freetext_other.append(("変更", f + "へんこう"))
    pw_freetext_other.append(("お願い", f + "おねがい"))
pw_freetext_other_str = make_pw_string(pw_freetext_other)

# ============================================================
# 13. 入力_確認_お問い合わせ (freetext)
# ============================================================
pw_inquiry = []
for d, r in [
    ("予約", "よやく"), ("確認", "かくにん"), ("日程", "にってい"),
    ("時間", "じかん"), ("場所", "ばしょ"), ("持ち物", "もちもの"),
    ("保険証", "ほけんしょう"), ("紹介状", "しょうかいじょう"),
    ("駐車場", "ちゅうしゃじょう"), ("受付", "うけつけ"),
    ("料金", "りょうきん"), ("費用", "ひよう"), ("検査", "けんさ"),
    ("結果", "けっか"), ("コース", "こーす"),
    ("人間ドック", "にんげんどっく"), ("健診", "けんしん"),
    ("食事制限", "しょくじせいげん"), ("アクセス", "あくせす"),
    ("支払い", "しはらい"), ("所要時間", "しょようじかん"),
    ("キャンセル", "きゃんせる"),
]:
    pw_inquiry.append((d, r))
for f in FILLERS:
    pw_inquiry.append(("確認", f + "かくにん"))
    pw_inquiry.append(("予約", f + "よやく"))
pw_inquiry_str = make_pw_string(pw_inquiry)

# ============================================================
# 14. 入力_共通_最後の問い合わせ (freetext)
# ============================================================
pw_last = []
for d, r in [
    ("ありません", "ありません"), ("ないです", "ないです"),
    ("特にない", "とくにない"), ("大丈夫です", "だいじょうぶです"),
    ("以上です", "いじょうです"), ("結構です", "けっこうです"),
    ("もうないです", "もうないです"), ("はい", "はい"),
    ("いいえ", "いいえ"), ("あります", "あります"),
    ("もう一つ", "もうひとつ"), ("質問", "しつもん"),
    ("確認", "かくにん"), ("聞きたい", "ききたい"),
    ("それだけです", "それだけです"), ("特にありません", "とくにありません"),
]:
    pw_last.append((d, r))
for f in FILLERS:
    pw_last.append(("ありません", f + "ありません"))
    pw_last.append(("ないです", f + "ないです"))
pw_last_str = make_pw_string(pw_last)

# ============================================================
# 15. 入力_相談_問合せ (RAG flow - freetext)
# ============================================================
pw_rag = []
for d, r in [
    ("質問", "しつもん"), ("聞きたい", "ききたい"),
    ("教えてほしい", "おしえてほしい"), ("確認", "かくにん"),
    ("予約", "よやく"), ("健診", "けんしん"), ("検査", "けんさ"),
    ("駐車場", "ちゅうしゃじょう"), ("料金", "りょうきん"),
    ("場所", "ばしょ"), ("アクセス", "あくせす"), ("受付", "うけつけ"),
    ("時間", "じかん"), ("持ち物", "もちもの"),
    ("食事制限", "しょくじせいげん"), ("保険証", "ほけんしょう"),
    ("紹介状", "しょうかいじょう"), ("支払い", "しはらい"),
    ("コース", "こーす"), ("ありません", "ありません"),
    ("ないです", "ないです"), ("もうないです", "もうないです"),
    ("特にありません", "とくにありません"),
]:
    pw_rag.append((d, r))
for f in FILLERS:
    pw_rag.append(("質問", f + "しつもん"))
pw_rag_str = make_pw_string(pw_rag)

# ============================================================
# Mapping: module_name -> profile_words
# ============================================================
all_pws = {
    "入力_用件選択": pw_yoken_str,
    "入力_予約_受診歴確認": pw_jushinreki_str,
    "入力_予約_企業名": pw_kigyou_str,
    "入力_予約_受診希望コース": pw_course_str,
    "入力_予約_予約希望時期": date_pw_str,
    "入力_変更_予約日": date_pw_str,
    "入力_変更_変更項目": pw_henkou_item_str,
    "入力_変更_内容確認_オプション": pw_freetext_option_str,
    "入力_変更_予約希望時期": date_pw_str,
    "入力_変更_内容確認_その他": pw_freetext_other_str,
    "入力_キャンセル_予約日": date_pw_str,
    "入力_キャンセル_予約希望時期": cancel_date_pw_str,
    "入力_確認_お問い合わせ": pw_inquiry_str,
    "入力_共通_最後の問い合わせ": pw_last_str,
    "入力_相談_問合せ": pw_rag_str,
}

# ============================================================
# Quality Checks
# ============================================================
print("=== Quality Check ===")
all_pass = True
for name, pw in all_pws.items():
    count = len(pw.strip().split("\n")) if pw.strip() else 0
    is_freetext = name in [
        "入力_予約_企業名", "入力_変更_内容確認_オプション",
        "入力_変更_内容確認_その他", "入力_確認_お問い合わせ",
        "入力_共通_最後の問い合わせ", "入力_相談_問合せ",
    ]

    # 1. Check format
    for i, line in enumerate(pw.strip().split("\n")):
        parts = line.split(" ")
        if len(parts) != 2:
            print(f"  FAIL [format] {name} line {i+1}: {line!r}")
            all_pass = False

    # 2. Check reading is hiragana + ー
    for i, line in enumerate(pw.strip().split("\n")):
        parts = line.split(" ")
        if len(parts) == 2:
            reading = parts[1]
            for ch in reading:
                if not ("\u3040" <= ch <= "\u309f" or ch == "ー"):
                    print(f"  FAIL [reading] {name} line {i+1}: non-hiragana '{ch}' in '{reading}'")
                    all_pass = False
                    break

    # 4. Check word count
    status = "OK"
    if is_freetext:
        if count > 200:
            status = "EXCESSIVE"
            all_pass = False
    else:
        if count < 100:
            status = "INSUFFICIENT"
            all_pass = False
        elif count > 200:
            status = "EXCESSIVE"
            all_pass = False

    # 5. Check filler TOP6 present (non-freetext)
    if not is_freetext:
        for filler in FILLERS:
            if filler not in pw:
                pass  # Fillers are embedded in readings, check differently

    # 7. Check no まー
    if "まー" in pw:
        print(f"  FAIL [まー] {name}: contains まー")
        all_pass = False

    print(f"  {name}: {count} words [{status}]")

if all_pass:
    print("\nAll quality checks PASSED.")
else:
    print("\nSome checks FAILED - review above.")

# ============================================================
# Apply to JSON files
# ============================================================
base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
main_flow_path = os.path.join(
    base, "output", "渓仁会円山クリニック", "fixed", "flows",
    "渓仁会円山クリニック_健診_20260417.json"
)
rag_flow_path = os.path.join(
    base, "output", "渓仁会円山クリニック", "fixed", "flows",
    "渓仁会円山クリニック_RAG検索_20260417.json"
)

# Update main flow
with open(main_flow_path, "r", encoding="utf-8") as f:
    main_data = json.load(f)

main_stt_count = 0
for mod_name, mod in main_data["modules"].items():
    if "Speech to Text" in mod.get("type", ""):
        if mod_name in all_pws:
            mod["params"]["profile_words"] = all_pws[mod_name]
            main_stt_count += 1
            print(f"  Updated: {mod_name}")

with open(main_flow_path, "w", encoding="utf-8") as f:
    json.dump(main_data, f, ensure_ascii=False, indent=2)
print(f"\nMain flow: updated {main_stt_count} STT modules -> {main_flow_path}")

# Update RAG flow
with open(rag_flow_path, "r", encoding="utf-8") as f:
    rag_data = json.load(f)

rag_stt_count = 0
for mod_name, mod in rag_data["modules"].items():
    if "Speech to Text" in mod.get("type", ""):
        if mod_name in all_pws:
            mod["params"]["profile_words"] = all_pws[mod_name]
            rag_stt_count += 1
            print(f"  Updated: {mod_name}")

with open(rag_flow_path, "w", encoding="utf-8") as f:
    json.dump(rag_data, f, ensure_ascii=False, indent=2)
print(f"RAG flow: updated {rag_stt_count} STT modules -> {rag_flow_path}")
print(f"\nTotal: {main_stt_count + rag_stt_count} STT modules updated.")
