#!/usr/bin/env python3
"""
横須賀共済病院の全STT/DTMFモジュールに profile_words を生成・更新するスクリプト。
対象: 12モジュール（pw_analyzer.py分析結果に基づく）
"""

import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# ============================================================
# フィラーTOP6 / 語尾TOP8
# ============================================================
FILLERS = ["あ", "え", "えー", "あの", "はい", "ま"]
SUFFIXES = ["です", "で", "なんですが", "になります", "ね", "さ", "でして", "か"]


def head_cut(yomi):
    """先頭1-2モーラ欠落パターンを生成。1文字のみになる場合はスキップ。"""
    results = []
    if len(yomi) < 2:
        return results
    # 1モーラ欠落
    cut1 = yomi[1:]
    if len(cut1) >= 2:
        results.append(cut1)
    # 2モーラ欠落
    if len(yomi) >= 3:
        cut2 = yomi[2:]
        if len(cut2) >= 2:
            results.append(cut2)
    return results


def expand_keyword(hyoki, yomi, use_fillers=True, use_suffixes=True, use_headcut=True):
    """1キーワードを展開して (hyoki, yomi) ペアのリストを返す。"""
    pairs = []
    # 基本形
    pairs.append((hyoki, yomi))
    # フィラー + キーワード
    if use_fillers:
        for f in FILLERS:
            pairs.append((hyoki, f + yomi))
    # キーワード + 語尾
    if use_suffixes:
        for s in SUFFIXES:
            pairs.append((hyoki, yomi + s))
    # 頭切れ
    if use_headcut:
        for cut in head_cut(yomi):
            pairs.append((hyoki, cut))
    return pairs


def format_pw(pairs):
    """ペアリストを profile_words 文字列に変換。重複除去。"""
    seen = set()
    lines = []
    for hyoki, yomi in pairs:
        key = (hyoki, yomi)
        if key not in seen:
            seen.add(key)
            lines.append(f"{hyoki} {yomi}")
    return "\n".join(lines)


# ============================================================
# 1. 入力_当日確認 (yes_no) — 参照辞書ベース
# ============================================================
def gen_yes_no():
    """yes_no辞書を参照辞書から読み込み、フィラー展開を追加して100-200語に。"""
    ref_path = os.path.join(BASE_DIR, "reference", "dictionaries", "profile_words_yes_no.txt")
    pairs = []
    with open(ref_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2:
                pairs.append((parts[0], parts[1]))
    # 参照辞書は既に113語。必要に応じてフィラー展開を追加
    # 主要キーワードにフィラー前置きを追加（辞書にまだないもの）
    existing_yomi = {p[1] for p in pairs}
    extra_keywords = [
        ("はい", "はい"),
        ("いいえ", "いいえ"),
        ("そうです", "そうです"),
        ("違います", "ちがいます"),
        ("大丈夫です", "だいじょうぶです"),
        ("お願いします", "おねがいします"),
    ]
    for hyoki, yomi in extra_keywords:
        for f in FILLERS:
            new_yomi = f + yomi
            if new_yomi not in existing_yomi:
                pairs.append((hyoki, new_yomi))
                existing_yomi.add(new_yomi)
    # 「まー」が含まれていないか確認（含まれていたら除外）
    pairs = [(h, y) for h, y in pairs if "まー" not in y]
    return pairs


# ============================================================
# 2. 入力_用件 (yoken) — 変更/キャンセル/確認/新規予約
# ============================================================
def gen_yoken():
    """用件分類辞書を生成。classification rangeValues: 変更/キャンセル/確認 + 暗黙の新規予約。
    目標: 100-200語。主要キーワードのみフル展開、派生語は基本形+頭切れのみ。"""
    # 主要キーワード（フル展開: フィラー+語尾+頭切れ）
    main_keywords = [
        ("変更", "へんこう"),
        ("キャンセル", "きゃんせる"),
        ("確認", "かくにん"),
        ("予約", "よやく"),
    ]
    # 派生キーワード（基本形+頭切れのみ）
    sub_keywords = [
        ("予約変更", "よやくへんこう"),
        ("日程変更", "にっていへんこう"),
        ("ずらしたい", "ずらしたい"),
        ("予約キャンセル", "よやくきゃんせる"),
        ("取消", "とりけし"),
        ("やめたい", "やめたい"),
        ("行けなくなった", "いけなくなった"),
        ("予約確認", "よやくかくにん"),
        ("聞きたい", "ききたい"),
        ("わからない", "わからない"),
        ("新規予約", "しんきよやく"),
        ("予約したい", "よやくしたい"),
        ("受診したい", "じゅしんしたい"),
        ("診てほしい", "みてほしい"),
        ("お願いしたい", "おねがいしたい"),
        ("取りたい", "とりたい"),
        ("時間を変えたい", "じかんをかえたい"),
        ("日にちを変えたい", "ひにちをかえたい"),
    ]
    pairs = []
    for hyoki, yomi in main_keywords:
        pairs.extend(expand_keyword(hyoki, yomi))
    for hyoki, yomi in sub_keywords:
        pairs.append((hyoki, yomi))
        for cut in head_cut(yomi):
            pairs.append((hyoki, cut))
    return pairs


# ============================================================
# 3. 入力_診療科1 / 入力_診療科2 (department)
# ============================================================
def gen_department(include_nashi=False):
    """診療科辞書を生成。OpenAIプロンプトのマッピングから主要科名を取得。
    目標: 100-200語。正式名称はフィラー+頭切れ、略称は基本形のみ。"""
    # 正式科名（フィラー+頭切れ展開）
    main_depts = [
        ("整形外科", "せいけいげか"),
        ("眼科", "がんか"),
        ("耳鼻咽喉科", "じびいんこうか"),
        ("皮膚科", "ひふか"),
        ("循環器内科", "じゅんかんきないか"),
        ("脳神経外科", "のうしんけいげか"),
        ("形成外科", "けいせいげか"),
        ("泌尿器科", "ひにょうきか"),
        ("産婦人科", "さんふじんか"),
        ("消化器内科", "しょうかきないか"),
        ("呼吸器内科", "こきゅうきないか"),
        ("外科", "げか"),
        ("内科", "ないか"),
        ("小児科", "しょうにか"),
        ("放射線科", "ほうしゃせんか"),
        ("口腔外科", "こうくうげか"),
    ]
    # 略称・類義語（基本形のみ）
    aliases = [
        ("整形", "せいけい"),
        ("耳鼻科", "じびか"),
        ("耳鼻", "じび"),
        ("リハビリテーション科", "りはびりてーしょんか"),
        ("リハビリ", "りはびり"),
        ("皮膚", "ひふ"),
        ("循環器", "じゅんかんき"),
        ("心臓", "しんぞう"),
        ("脳外科", "のうげか"),
        ("脳外", "のうげ"),
        ("形成", "けいせい"),
        ("泌尿器", "ひにょうき"),
        ("婦人科", "ふじんか"),
        ("産科", "さんか"),
        ("精神科", "せいしんか"),
        ("精神", "せいしん"),
        ("心療内科", "しんりょうないか"),
        ("心療", "しんりょう"),
        ("消化器", "しょうかき"),
        ("呼吸器", "こきゅうき"),
        ("神経内科", "しんけいないか"),
        ("神経", "しんけい"),
        ("小児", "しょうに"),
        ("放射線", "ほうしゃせん"),
        ("麻酔科", "ますいか"),
        ("歯科", "しか"),
    ]

    pairs = []
    for hyoki, yomi in main_depts:
        # 基本形
        pairs.append((hyoki, yomi))
        # フィラー（「あ」「え」「えー」のみで絞る）
        for f in ["あ", "え", "えー"]:
            pairs.append((hyoki, f + yomi))
        # 語尾（「です」「で」のみ）
        for s in ["です", "で"]:
            pairs.append((hyoki, yomi + s))
        # 頭切れ
        for cut in head_cut(yomi):
            pairs.append((hyoki, cut))

    for hyoki, yomi in aliases:
        pairs.append((hyoki, yomi))

    if include_nashi:
        # 診療科2用: 「なし」系の語（基本形+頭切れのみ）
        nashi_keywords = [
            ("ありません", "ありません"),
            ("なし", "なし"),
            ("ないです", "ないです"),
            ("特にありません", "とくにありません"),
            ("特にない", "とくにない"),
            ("大丈夫です", "だいじょうぶです"),
            ("ございません", "ございません"),
        ]
        for hyoki, yomi in nashi_keywords:
            pairs.append((hyoki, yomi))
            for cut in head_cut(yomi):
                pairs.append((hyoki, cut))
            # フィラー前置き（主要なもののみ）
            for f in ["あ", "え"]:
                pairs.append((hyoki, f + yomi))

    return pairs


# ============================================================
# 4. 入力_予約日 (date)
# ============================================================
def gen_date():
    """予約日辞書を生成。DOB辞書(元号不要) + 相対日付 + 曜日。
    目標: 100-200語。相対日付は基本形+頭切れのみ。"""
    pairs = []

    # 月名（DOB辞書から）
    months = [
        ("一月", "いちがつ"), ("二月", "にがつ"), ("三月", "さんがつ"),
        ("四月", "しがつ"), ("五月", "ごがつ"), ("六月", "ろくがつ"),
        ("七月", "しちがつ"), ("八月", "はちがつ"), ("九月", "くがつ"),
        ("十月", "じゅうがつ"), ("十一月", "じゅういちがつ"), ("十二月", "じゅうにがつ"),
    ]
    pairs.extend(months)

    # 日付特殊読み（DOB辞書から）
    days = [
        ("一日", "ついたち"), ("二日", "ふつか"), ("三日", "みっか"),
        ("四日", "よっか"), ("五日", "いつか"), ("六日", "むいか"),
        ("七日", "なのか"), ("八日", "ようか"), ("九日", "ここのか"),
        ("十日", "とおか"), ("十一日", "じゅういちにち"), ("十二日", "じゅうににち"),
        ("十三日", "じゅうさんにち"), ("十四日", "じゅうよっか"),
        ("十五日", "じゅうごにち"), ("十六日", "じゅうろくにち"),
        ("十七日", "じゅうしちにち"), ("十八日", "じゅうはちにち"),
        ("十九日", "じゅうくにち"), ("二十日", "はつか"),
        ("二十一日", "にじゅういちにち"), ("二十二日", "にじゅうににち"),
        ("二十三日", "にじゅうさんにち"), ("二十四日", "にじゅうよっか"),
        ("二十五日", "にじゅうごにち"), ("二十六日", "にじゅうろくにち"),
        ("二十七日", "にじゅうしちにち"), ("二十八日", "にじゅうはちにち"),
        ("二十九日", "にじゅうくにち"), ("三十日", "さんじゅうにち"),
        ("三十一日", "さんじゅういちにち"),
    ]
    pairs.extend(days)

    # 相対日付（基本形+頭切れのみ、フル展開しない）
    relative_dates = [
        ("来週", "らいしゅう"),
        ("再来週", "さらいしゅう"),
        ("来月", "らいげつ"),
        ("明日", "あした"),
        ("明日", "あす"),
        ("明後日", "あさって"),
        ("今週", "こんしゅう"),
        ("今月", "こんげつ"),
    ]
    for hyoki, yomi in relative_dates:
        pairs.append((hyoki, yomi))
        for cut in head_cut(yomi):
            pairs.append((hyoki, cut))
        # フィラー前置き（「あ」「え」のみ）
        for f in ["あ", "え"]:
            pairs.append((hyoki, f + yomi))

    # 曜日
    weekdays = [
        ("月曜日", "げつようび"),
        ("火曜日", "かようび"),
        ("水曜日", "すいようび"),
        ("木曜日", "もくようび"),
        ("金曜日", "きんようび"),
        ("土曜日", "どようび"),
        ("日曜日", "にちようび"),
    ]
    for hyoki, yomi in weekdays:
        pairs.append((hyoki, yomi))
        for cut in head_cut(yomi):
            pairs.append((hyoki, cut))

    # 「わからない」系（基本形+フィラー+頭切れ）
    extra = [
        ("わからない", "わからない"),
        ("わかりません", "わかりません"),
        ("未定", "みてい"),
    ]
    for hyoki, yomi in extra:
        pairs.append((hyoki, yomi))
        for cut in head_cut(yomi):
            pairs.append((hyoki, cut))
        for f in ["あ", "え", "えー"]:
            pairs.append((hyoki, f + yomi))

    # 数字読み
    numbers = [
        ("一", "いち"), ("二", "に"), ("三", "さん"), ("四", "よん"), ("四", "し"),
        ("五", "ご"), ("六", "ろく"), ("七", "なな"), ("七", "しち"),
        ("八", "はち"), ("九", "きゅう"), ("十", "じゅう"),
        ("二十", "にじゅう"), ("三十", "さんじゅう"),
    ]
    pairs.extend(numbers)

    # 年/日
    pairs.append(("年", "ねん"))
    pairs.append(("日", "にち"))

    return pairs


# ============================================================
# 5. 入力_内容 (freetext) — 問い合わせ内容
# ============================================================
def gen_freetext_content():
    """問い合わせ内容用のfreetext辞書。最小限。"""
    keywords = [
        ("予約", "よやく"),
        ("予約変更", "よやくへんこう"),
        ("予約確認", "よやくかくにん"),
        ("予約日時の確認", "よやくにちじのかくにん"),
        ("変更", "へんこう"),
        ("確認", "かくにん"),
        ("キャンセル", "きゃんせる"),
        ("取消", "とりけし"),
        ("日程", "にってい"),
        ("日にち", "ひにち"),
        ("時間", "じかん"),
        ("担当", "たんとう"),
        ("先生", "せんせい"),
        ("診察", "しんさつ"),
        ("検査", "けんさ"),
        ("手術", "しゅじゅつ"),
        ("入院", "にゅういん"),
        ("退院", "たいいん"),
        ("紹介状", "しょうかいじょう"),
        ("薬", "くすり"),
        ("処方", "しょほう"),
        ("結果", "けっか"),
        ("問い合わせ", "といあわせ"),
    ]
    pairs = []
    for hyoki, yomi in keywords:
        pairs.append((hyoki, yomi))
    # フィラーTOP6のみ追加
    for f in FILLERS:
        pairs.append((f, f))
    return pairs


# ============================================================
# 6. 入力_患者_氏名 (name) — 609語→100-200語に削減
# ============================================================
def gen_name():
    """氏名辞書を生成。参照辞書ベース + 神奈川頻出苗字 + フレーズ系 + 頭切れ。
    目標: 100-200語。フィラーは15%制限（「あ」「え」のみ）。"""
    ref_path = os.path.join(BASE_DIR, "reference", "dictionaries", "profile_words_name.txt")
    pairs = []
    with open(ref_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2:
                pairs.append((parts[0], parts[1]))

    # 神奈川県（横須賀エリア）頻出苗字TOP50
    local_names = [
        ("鈴木", "すずき"), ("高橋", "たかはし"), ("佐藤", "さとう"),
        ("田中", "たなか"), ("渡辺", "わたなべ"), ("伊藤", "いとう"),
        ("山本", "やまもと"), ("中村", "なかむら"), ("小林", "こばやし"),
        ("加藤", "かとう"), ("吉田", "よしだ"), ("山田", "やまだ"),
        ("松本", "まつもと"), ("井上", "いのうえ"), ("木村", "きむら"),
        ("石井", "いしい"), ("清水", "しみず"), ("山口", "やまぐち"),
        ("佐々木", "ささき"), ("藤田", "ふじた"), ("小川", "おがわ"),
        ("岡田", "おかだ"), ("長谷川", "はせがわ"), ("村上", "むらかみ"),
        ("石川", "いしかわ"), ("前田", "まえだ"), ("中島", "なかじま"),
        ("阿部", "あべ"), ("斉藤", "さいとう"), ("橋本", "はしもと"),
        ("近藤", "こんどう"), ("坂本", "さかもと"), ("遠藤", "えんどう"),
        ("青木", "あおき"), ("藤井", "ふじい"), ("西村", "にしむら"),
        ("福田", "ふくだ"), ("太田", "おおた"), ("三浦", "みうら"),
        ("藤原", "ふじわら"), ("岡本", "おかもと"), ("松田", "まつだ"),
        ("中川", "なかがわ"), ("中野", "なかの"), ("原田", "はらだ"),
        ("小野", "おの"), ("竹内", "たけうち"), ("金子", "かねこ"),
        ("和田", "わだ"), ("池田", "いけだ"), ("宮崎", "みやざき"),
        ("横山", "よこやま"), ("上田", "うえだ"), ("杉山", "すぎやま"),
        ("市川", "いちかわ"), ("大野", "おおの"), ("野口", "のぐち"),
        ("原", "はら"), ("川崎", "かわさき"), ("久保", "くぼ"),
    ]
    existing = {p[1] for p in pairs}
    for hyoki, yomi in local_names:
        if yomi not in existing:
            pairs.append((hyoki, yomi))
            existing.add(yomi)

    # 頭切れ（3文字以上の主要苗字）
    headcut_names = [
        ("鈴木", "すずき"), ("高橋", "たかはし"), ("渡辺", "わたなべ"),
        ("山本", "やまもと"), ("小林", "こばやし"), ("松本", "まつもと"),
        ("長谷川", "はせがわ"), ("佐々木", "ささき"), ("中村", "なかむら"),
        ("伊藤", "いとう"), ("加藤", "かとう"), ("吉田", "よしだ"),
        ("井上", "いのうえ"), ("石川", "いしかわ"), ("中島", "なかじま"),
        ("斉藤", "さいとう"), ("橋本", "はしもと"), ("近藤", "こんどう"),
        ("坂本", "さかもと"), ("遠藤", "えんどう"),
    ]
    for hyoki, yomi in headcut_names:
        for cut in head_cut(yomi):
            if cut not in existing:
                pairs.append((hyoki, cut))
                existing.add(cut)

    # フレーズ系
    phrases = [
        ("私は", "わたしは"),
        ("名前は", "なまえは"),
        ("と申します", "ともうします"),
        ("です", "です"),
        ("と言います", "といいます"),
        ("でございます", "でございます"),
    ]
    pairs.extend(phrases)

    # フィラー（15%制限: 「あ」「え」のみ）
    pairs.append(("あ", "あ"))
    pairs.append(("え", "え"))

    # 頻出名前（下の名前）最小限
    first_names = [
        ("太郎", "たろう"), ("花子", "はなこ"), ("一郎", "いちろう"),
        ("翔太", "しょうた"), ("美咲", "みさき"), ("大輔", "だいすけ"),
        ("裕子", "ゆうこ"), ("健一", "けんいち"), ("和子", "かずこ"),
        ("明", "あきら"),
    ]
    for hyoki, yomi in first_names:
        if yomi not in existing:
            pairs.append((hyoki, yomi))
            existing.add(yomi)

    return pairs


# ============================================================
# 7. 入力_患者_生年月日 (dob/DTMF) — DOB辞書
# ============================================================
def gen_dob():
    """生年月日辞書（DTMF+STT）。参照辞書 + 元号頭切れ + フィラー展開。"""
    pairs = []
    ref_path = os.path.join(BASE_DIR, "reference", "dictionaries", "profile_words_dob.txt")
    with open(ref_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2:
                pairs.append((parts[0], parts[1]))

    # 元号の頭切れ・誤認識パターン
    era_extras = [
        ("昭和", "きょうわ"),
        ("昭和", "きょうは"),
        ("令和", "えいわ"),
        ("平成", "えいせい"),
        ("昭和", "ょうわ"),
        ("令和", "いわ"),
        ("平成", "いせい"),
        ("大正", "いしょう"),
    ]
    pairs.extend(era_extras)

    # 元号にフィラー前置き
    eras = [("令和", "れいわ"), ("平成", "へいせい"), ("昭和", "しょうわ"), ("大正", "たいしょう")]
    existing_yomi = {p[1] for p in pairs}
    for hyoki, yomi in eras:
        for f in FILLERS:
            new_yomi = f + yomi
            if new_yomi not in existing_yomi:
                pairs.append((hyoki, new_yomi))
                existing_yomi.add(new_yomi)

    # 数字読み
    numbers = [
        ("一", "いち"), ("二", "に"), ("三", "さん"), ("四", "よん"), ("四", "し"),
        ("五", "ご"), ("六", "ろく"), ("七", "なな"), ("七", "しち"),
        ("八", "はち"), ("九", "きゅう"), ("九", "く"), ("零", "ぜろ"), ("零", "れい"),
        ("十", "じゅう"), ("二十", "にじゅう"), ("三十", "さんじゅう"),
    ]
    for hyoki, yomi in numbers:
        if yomi not in existing_yomi:
            pairs.append((hyoki, yomi))
            existing_yomi.add(yomi)

    # 年/月/日
    pairs.append(("年", "ねん"))
    pairs.append(("月", "がつ"))
    pairs.append(("日", "にち"))
    pairs.append(("生まれ", "うまれ"))

    return pairs


# ============================================================
# 8. 入力_患者_診察券番号 (phone/数字 DTMF)
# ============================================================
def gen_phone_digits():
    """診察券番号用の数字辞書。DTMF主体のため最小限。"""
    pairs = [
        ("一", "いち"), ("二", "に"), ("三", "さん"), ("四", "よん"), ("四", "し"),
        ("五", "ご"), ("六", "ろく"), ("七", "なな"), ("七", "しち"),
        ("八", "はち"), ("九", "きゅう"), ("九", "く"), ("零", "ぜろ"), ("零", "れい"),
        ("十", "じゅう"),
        ("番号", "ばんごう"),
        ("診察券", "しんさつけん"),
        ("番", "ばん"),
    ]
    return pairs


# ============================================================
# 9. 入力_患者_携帯電話 / 入力_患者_復唱連絡先 (yes_no DTMF)
# ============================================================
def gen_yes_no_dtmf():
    """DTMF+STTの肯定否定。yes_no辞書の中核部分のみ。"""
    ref_path = os.path.join(BASE_DIR, "reference", "dictionaries", "profile_words_yes_no.txt")
    pairs = []
    with open(ref_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(" ", 1)
            if len(parts) == 2:
                pairs.append((parts[0], parts[1]))
    # 「まー」除外
    pairs = [(h, y) for h, y in pairs if "まー" not in y]
    return pairs


# ============================================================
# 10. 入力_患者_連絡先 (freetext DTMF) — 電話番号
# ============================================================
def gen_phone_freetext():
    """電話番号入力用のfreetext辞書。数字読みのみ。"""
    pairs = [
        ("一", "いち"), ("二", "に"), ("三", "さん"), ("四", "よん"), ("四", "し"),
        ("五", "ご"), ("六", "ろく"), ("七", "なな"), ("七", "しち"),
        ("八", "はち"), ("九", "きゅう"), ("九", "く"), ("零", "ぜろ"), ("零", "れい"),
    ]
    return pairs


# ============================================================
# メイン処理
# ============================================================
def update_module_pw(data, module_name, pairs):
    """フローJSONの指定モジュールの profile_words を更新。"""
    pw_text = format_pw(pairs)
    count = len(pw_text.split("\n"))
    data["modules"][module_name]["params"]["profile_words"] = pw_text
    return count


def main():
    # ---- メインフロー ----
    main_path = os.path.join(OUTPUT_DIR, "横須賀共済_診療予約_20260406_20260420.json")
    with open(main_path, "r", encoding="utf-8") as f:
        main_data = json.load(f)

    # 入力_当日確認 (yes_no)
    pairs = gen_yes_no()
    count = update_module_pw(main_data, "入力_当日確認", pairs)
    print(f"入力_当日確認: {count} 語")

    # 入力_用件 (yoken)
    pairs = gen_yoken()
    count = update_module_pw(main_data, "入力_用件", pairs)
    print(f"入力_用件: {count} 語")

    # 入力_診療科1 (department)
    pairs = gen_department(include_nashi=False)
    count = update_module_pw(main_data, "入力_診療科1", pairs)
    print(f"入力_診療科1: {count} 語")

    # 入力_診療科2 (department + なし)
    pairs = gen_department(include_nashi=True)
    count = update_module_pw(main_data, "入力_診療科2", pairs)
    print(f"入力_診療科2: {count} 語")

    # 入力_予約日 (date)
    pairs = gen_date()
    count = update_module_pw(main_data, "入力_予約日", pairs)
    print(f"入力_予約日: {count} 語")

    # 入力_内容 (freetext)
    pairs = gen_freetext_content()
    count = update_module_pw(main_data, "入力_内容", pairs)
    print(f"入力_内容: {count} 語")

    with open(main_path, "w", encoding="utf-8") as f:
        json.dump(main_data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {main_path}")

    # ---- 氏名聴取サブフロー ----
    name_path = os.path.join(OUTPUT_DIR, "横須賀共済_氏名聴取_20260420.json")
    with open(name_path, "r", encoding="utf-8") as f:
        name_data = json.load(f)
    pairs = gen_name()
    count = update_module_pw(name_data, "入力_患者_氏名", pairs)
    print(f"入力_患者_氏名: {count} 語")
    with open(name_path, "w", encoding="utf-8") as f:
        json.dump(name_data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {name_path}")

    # ---- 生年月日聴取サブフロー ----
    dob_path = os.path.join(OUTPUT_DIR, "横須賀共済_生年月日聴取_20260420.json")
    with open(dob_path, "r", encoding="utf-8") as f:
        dob_data = json.load(f)
    pairs = gen_dob()
    count = update_module_pw(dob_data, "入力_患者_生年月日", pairs)
    print(f"入力_患者_生年月日: {count} 語")
    with open(dob_path, "w", encoding="utf-8") as f:
        json.dump(dob_data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {dob_path}")

    # ---- 診察券番号聴取サブフロー ----
    card_path = os.path.join(OUTPUT_DIR, "横須賀共済_診察券番号聴取_20260420.json")
    with open(card_path, "r", encoding="utf-8") as f:
        card_data = json.load(f)
    pairs = gen_phone_digits()
    count = update_module_pw(card_data, "入力_患者_診察券番号", pairs)
    print(f"入力_患者_診察券番号: {count} 語")
    with open(card_path, "w", encoding="utf-8") as f:
        json.dump(card_data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {card_path}")

    # ---- 電話番号聴取サブフロー ----
    phone_path = os.path.join(OUTPUT_DIR, "横須賀共済_電話番号聴取_20260420.json")
    with open(phone_path, "r", encoding="utf-8") as f:
        phone_data = json.load(f)

    # 入力_患者_携帯電話 (yes_no DTMF)
    pairs = gen_yes_no_dtmf()
    count = update_module_pw(phone_data, "入力_患者_携帯電話", pairs)
    print(f"入力_患者_携帯電話: {count} 語")

    # 入力_患者_復唱連絡先 (yes_no DTMF)
    pairs = gen_yes_no_dtmf()
    count = update_module_pw(phone_data, "入力_患者_復唱連絡先", pairs)
    print(f"入力_患者_復唱連絡先: {count} 語")

    # 入力_患者_連絡先 (freetext/phone DTMF)
    pairs = gen_phone_freetext()
    count = update_module_pw(phone_data, "入力_患者_連絡先", pairs)
    print(f"入力_患者_連絡先: {count} 語")

    with open(phone_path, "w", encoding="utf-8") as f:
        json.dump(phone_data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {phone_path}")

    print("\n=== Summary ===")
    print("All 12 modules updated successfully.")


if __name__ == "__main__":
    main()
