#!/usr/bin/env python3
"""
fix_kensei_stage2_3.py -- 健生病院（健診シナリオ）Stage 2 & 3 修正

Stage 2: profile_words充実化（21/27モジュールが空 → 全モジュール辞書設定）
Stage 3: OpenAIプロンプト修正（# Role / # Context / セキュリティセクション欠落修正）

ルール:
- フィラー: 主要キーワードに10種（あ/あー/あの/え/えー/えっと/ん/はい/ま/そうですね）、二次に3種（あ/え/えー）
- 「まー」は使用禁止
- 語尾: 主要4種（です/で/なんですが/になります）、二次2種（です/で）
- 頭落ち: 全キーワードに1-2段
- 目標語数: 50-300語/モジュール（DTMFは例外的に少なくてOK）
- matchingmethod は必ず int
"""

import json
import sys
import io
import copy

# Windows cp932 環境での日本語出力対応
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

INPUT_PATH = "output/健生病院/健生病院_健診_20260420.json"
OUTPUT_PATH = "output/健生病院/健生病院_健診_20260420.json"

# ============================================================
# フィラー・語尾・頭落ちヘルパー
# ============================================================

FILLERS_PRIMARY = ["あ", "あー", "あの", "え", "えー", "えっと", "ん", "はい", "ま", "そうですね"]
FILLERS_SECONDARY = ["あ", "え", "えー"]
SUFFIXES_PRIMARY = ["です", "で", "なんですが", "になります"]
SUFFIXES_SECONDARY = ["です", "で"]


def add_filler_variants(base_display, base_reading, is_primary=True):
    """フィラー付きバリエーションを生成"""
    fillers = FILLERS_PRIMARY if is_primary else FILLERS_SECONDARY
    lines = []
    for f in fillers:
        lines.append(f"{base_display} {f}{base_reading}")
    return lines


def add_suffix_variants(base_display, base_reading, is_primary=True):
    """語尾バリエーションを生成"""
    suffixes = SUFFIXES_PRIMARY if is_primary else SUFFIXES_SECONDARY
    lines = []
    for s in suffixes:
        lines.append(f"{base_display}{s} {base_reading}{s}")
    return lines


def add_head_clip(base_display, base_reading, clips):
    """頭落ちパターンを生成。clips = [(落ち1段), (落ち2段)] のリスト"""
    lines = []
    for clip in clips:
        lines.append(f"{base_display} {clip}")
    return lines


def build_word_entry(display, reading):
    """基本エントリ: 表記 よみがな"""
    return f"{display} {reading}"


# ============================================================
# Stage 2: profile_words辞書定義
# ============================================================

def build_profile_words_郵便番号と住所():
    """入力_郵便番号と住所: 郵便番号+住所。数字読み+都道府県+市区町村"""
    lines = []
    # 数字読み
    digits = [
        ("零", "ぜろ"), ("一", "いち"), ("二", "に"), ("三", "さん"),
        ("四", "よん"), ("四", "し"), ("五", "ご"), ("六", "ろく"),
        ("七", "なな"), ("七", "しち"), ("八", "はち"), ("九", "きゅう"),
        ("十", "じゅう"), ("百", "ひゃく"), ("千", "せん"),
    ]
    for d, r in digits:
        lines.append(build_word_entry(d, r))

    # 郵便番号関連
    kw_postal = [
        ("郵便番号", "ゆうびんばんごう"), ("番号", "ばんごう"),
    ]
    for d, r in kw_postal:
        lines.append(build_word_entry(d, r))
        lines.extend(add_filler_variants(d, r, True))

    # 都道府県（秋田県近隣含む主要県）
    prefectures = [
        ("秋田県", "あきたけん"), ("秋田", "あきた"),
        ("青森県", "あおもりけん"), ("青森", "あおもり"),
        ("岩手県", "いわてけん"), ("岩手", "いわて"),
        ("山形県", "やまがたけん"), ("山形", "やまがた"),
        ("宮城県", "みやぎけん"), ("宮城", "みやぎ"),
        ("北海道", "ほっかいどう"),
    ]
    for d, r in prefectures:
        lines.append(build_word_entry(d, r))
        lines.extend(add_filler_variants(d, r, False))

    # 秋田県主要市町村
    akita_cities = [
        ("秋田市", "あきたし"), ("横手市", "よこてし"), ("大仙市", "だいせんし"),
        ("由利本荘市", "ゆりほんじょうし"), ("大館市", "おおだてし"),
        ("能代市", "のしろし"), ("湯沢市", "ゆざわし"), ("鹿角市", "かづのし"),
        ("潟上市", "かたがみし"), ("北秋田市", "きたあきたし"),
        ("にかほ市", "にかほし"), ("仙北市", "せんぼくし"),
        ("男鹿市", "おがし"),
    ]
    for d, r in akita_cities:
        lines.append(build_word_entry(d, r))

    # 青森県主要市町村（近隣）
    aomori_cities = [
        ("弘前市", "ひろさきし"), ("青森市", "あおもりし"),
        ("八戸市", "はちのへし"), ("五所川原市", "ごしょがわらし"),
        ("十和田市", "とわだし"), ("むつ市", "むつし"),
        ("黒石市", "くろいしし"), ("つがる市", "つがるし"),
        ("平川市", "ひらかわし"), ("藤崎町", "ふじさきまち"),
        ("板柳町", "いたやなぎまち"), ("鶴田町", "つるたまち"),
        ("大鰐町", "おおわにまち"), ("田舎館村", "いなかだてむら"),
    ]
    for d, r in aomori_cities:
        lines.append(build_word_entry(d, r))

    # 住所関連語
    addr_words = [
        ("丁目", "ちょうめ"), ("番地", "ばんち"), ("番", "ばん"),
        ("号", "ごう"), ("町", "まち"), ("町", "ちょう"),
        ("村", "むら"), ("市", "し"), ("区", "く"), ("郡", "ぐん"),
    ]
    for d, r in addr_words:
        lines.append(build_word_entry(d, r))

    # フィラー付き冒頭語
    head_words = [
        ("住所は", "じゅうしょは"), ("住所", "じゅうしょ"),
        ("郵便番号は", "ゆうびんばんごうは"),
    ]
    for d, r in head_words:
        lines.append(build_word_entry(d, r))
        lines.extend(add_filler_variants(d, r, True))

    # 頭落ち
    lines.extend(add_head_clip("住所", "ゅうしょ", ["ゅうしょ"]))
    lines.extend(add_head_clip("郵便番号", "うびんばんごう", ["うびんばんごう", "びんばんごう"]))

    return "\n".join(lines)


def build_profile_words_市町村名():
    """入力_市町村名: 市町村名。秋田県の病院なので近隣市町村名リスト"""
    lines = []

    # 秋田県全市町村
    akita_all = [
        ("秋田市", "あきたし"), ("横手市", "よこてし"), ("大仙市", "だいせんし"),
        ("由利本荘市", "ゆりほんじょうし"), ("大館市", "おおだてし"),
        ("能代市", "のしろし"), ("湯沢市", "ゆざわし"), ("鹿角市", "かづのし"),
        ("潟上市", "かたがみし"), ("北秋田市", "きたあきたし"),
        ("にかほ市", "にかほし"), ("仙北市", "せんぼくし"),
        ("男鹿市", "おがし"),
        ("小坂町", "こさかまち"), ("上小阿仁村", "かみこあにむら"),
        ("藤里町", "ふじさとまち"), ("三種町", "みたねちょう"),
        ("八峰町", "はっぽうちょう"), ("五城目町", "ごじょうめまち"),
        ("八郎潟町", "はちろうがたまち"), ("井川町", "いかわまち"),
        ("大潟村", "おおがたむら"), ("美郷町", "みさとちょう"),
        ("羽後町", "うごまち"), ("東成瀬村", "ひがしなるせむら"),
    ]

    # 青森県近隣市町村（弘前近辺は健生病院の患者多い）
    aomori_near = [
        ("弘前市", "ひろさきし"), ("青森市", "あおもりし"),
        ("八戸市", "はちのへし"), ("五所川原市", "ごしょがわらし"),
        ("十和田市", "とわだし"), ("黒石市", "くろいしし"),
        ("つがる市", "つがるし"), ("平川市", "ひらかわし"),
        ("藤崎町", "ふじさきまち"), ("板柳町", "いたやなぎまち"),
        ("鶴田町", "つるたまち"), ("大鰐町", "おおわにまち"),
        ("田舎館村", "いなかだてむら"), ("西目屋村", "にしめやむら"),
    ]

    all_cities = akita_all + aomori_near
    for d, r in all_cities:
        lines.append(build_word_entry(d, r))

    # 主要キーワードにフィラー
    primary_kw = [
        ("秋田市", "あきたし"), ("弘前市", "ひろさきし"),
        ("横手市", "よこてし"), ("大仙市", "だいせんし"),
    ]
    for d, r in primary_kw:
        lines.extend(add_filler_variants(d, r, True))

    # 二次キーワードにフィラー
    for d, r in all_cities:
        if (d, r) not in primary_kw:
            lines.extend(add_filler_variants(d, r, False))

    # 語尾バリエーション（主要市町村）
    for d, r in primary_kw:
        lines.extend(add_suffix_variants(d, r, True))

    # 頭落ち
    head_clips = [
        ("秋田市", "きたし", ["きたし"]),
        ("弘前市", "ろさきし", ["ろさきし"]),
        ("横手市", "こてし", ["こてし"]),
    ]
    for d, c, clips in head_clips:
        lines.extend(add_head_clip(d, c, clips))

    # わからない
    lines.append(build_word_entry("わからない", "わからない"))
    lines.append(build_word_entry("わかりません", "わかりません"))
    lines.extend(add_filler_variants("わからない", "わからない", True))

    return "\n".join(lines)


def build_profile_words_がん健診種類():
    """入力_がん健診種類: がん種類"""
    lines = []

    cancer_types = [
        ("胃がん", "いがん"), ("胃がん検診", "いがんけんしん"),
        ("大腸がん", "だいちょうがん"), ("大腸がん検診", "だいちょうがんけんしん"),
        ("肺がん", "はいがん"), ("肺がん検診", "はいがんけんしん"),
        ("乳がん", "にゅうがん"), ("乳がん検診", "にゅうがんけんしん"),
        ("子宮がん", "しきゅうがん"), ("子宮がん検診", "しきゅうがんけんしん"),
        ("子宮頸がん", "しきゅうけいがん"), ("子宮頸がん検診", "しきゅうけいがんけんしん"),
        ("前立腺がん", "ぜんりつせんがん"), ("前立腺がん検診", "ぜんりつせんがんけんしん"),
        ("がん検診", "がんけんしん"), ("がん", "がん"),
        ("検診", "けんしん"),
    ]

    for d, r in cancer_types:
        lines.append(build_word_entry(d, r))

    # 主要がん種にフィラー10種
    primary_cancer = [
        ("胃がん", "いがん"), ("大腸がん", "だいちょうがん"),
        ("肺がん", "はいがん"), ("乳がん", "にゅうがん"),
        ("子宮がん", "しきゅうがん"),
    ]
    for d, r in primary_cancer:
        lines.extend(add_filler_variants(d, r, True))

    # 二次にフィラー3種
    secondary_cancer = [
        ("子宮頸がん", "しきゅうけいがん"), ("前立腺がん", "ぜんりつせんがん"),
        ("がん検診", "がんけんしん"),
    ]
    for d, r in secondary_cancer:
        lines.extend(add_filler_variants(d, r, False))

    # 語尾バリエーション
    for d, r in primary_cancer:
        lines.extend(add_suffix_variants(d, r, True))

    # 頭落ち
    head_clips = [
        ("胃がん", ["がん"]),
        ("大腸がん", ["いちょうがん", "ちょうがん"]),
        ("肺がん", ["いがん"]),
        ("乳がん", ["ゅうがん"]),
        ("子宮がん", ["きゅうがん"]),
    ]
    for d, clips in head_clips:
        lines.extend(add_head_clip(d, d, clips))

    # 複数回答パターン
    combos = [
        ("胃がんと大腸がん", "いがんとだいちょうがん"),
        ("肺がんと乳がん", "はいがんとにゅうがん"),
        ("全部", "ぜんぶ"), ("全て", "すべて"),
    ]
    for d, r in combos:
        lines.append(build_word_entry(d, r))

    return "\n".join(lines)


def build_profile_words_その他内容():
    """入力_その他内容: その他健診内容の自由発話"""
    lines = []

    kw = [
        ("健康診断", "けんこうしんだん"), ("健診", "けんしん"),
        ("人間ドック", "にんげんどっく"), ("ドック", "どっく"),
        ("血液検査", "けつえきけんさ"), ("尿検査", "にょうけんさ"),
        ("心電図", "しんでんず"), ("エコー", "えこー"),
        ("超音波", "ちょうおんぱ"), ("レントゲン", "れんとげん"),
        ("X線", "えっくすせん"), ("CT", "しーてぃー"),
        ("MRI", "えむあーるあい"), ("内視鏡", "ないしきょう"),
        ("胃カメラ", "いかめら"), ("大腸カメラ", "だいちょうかめら"),
        ("骨密度", "こつみつど"), ("眼底検査", "がんていけんさ"),
        ("聴力検査", "ちょうりょくけんさ"), ("視力検査", "しりょくけんさ"),
        ("腫瘍マーカー", "しゅようまーかー"), ("ピロリ菌", "ぴろりきん"),
        ("便潜血", "べんせんけつ"), ("PSA", "ぴーえすえー"),
        ("甲状腺", "こうじょうせん"), ("肝炎", "かんえん"),
        ("アレルギー検査", "あれるぎーけんさ"),
        ("その他", "そのた"),
        ("わからない", "わからない"), ("わかりません", "わかりません"),
    ]

    for d, r in kw:
        lines.append(build_word_entry(d, r))

    # 主要キーワードにフィラー10種
    primary = [
        ("健康診断", "けんこうしんだん"), ("人間ドック", "にんげんどっく"),
        ("血液検査", "けつえきけんさ"), ("レントゲン", "れんとげん"),
        ("内視鏡", "ないしきょう"),
    ]
    for d, r in primary:
        lines.extend(add_filler_variants(d, r, True))

    # 二次にフィラー3種
    secondary = [kw_item for kw_item in kw if kw_item not in primary][:10]
    for d, r in secondary:
        lines.extend(add_filler_variants(d, r, False))

    # 語尾
    for d, r in primary:
        lines.extend(add_suffix_variants(d, r, True))

    # 頭落ち
    lines.extend(add_head_clip("健康診断", "けんこうしんだん", ["んこうしんだん"]))
    lines.extend(add_head_clip("人間ドック", "にんげんどっく", ["んげんどっく"]))
    lines.extend(add_head_clip("血液検査", "けつえきけんさ", ["つえきけんさ"]))
    lines.extend(add_head_clip("内視鏡", "ないしきょう", ["いしきょう"]))

    # 要望表現
    request_words = [
        ("希望します", "きぼうします"), ("お願いします", "おねがいします"),
        ("受けたい", "うけたい"), ("やりたい", "やりたい"),
        ("追加したい", "ついかしたい"), ("ないです", "ないです"),
        ("ありません", "ありません"), ("特にないです", "とくにないです"),
    ]
    for d, r in request_words:
        lines.append(build_word_entry(d, r))
        lines.extend(add_filler_variants(d, r, False))

    return "\n".join(lines)


def build_profile_words_同時健診内容():
    """入力_同時健診内容: 同時に受けたい健診。健診種類キーワード"""
    lines = []

    kw = [
        ("人間ドック", "にんげんどっく"), ("ドック", "どっく"),
        ("特定健診", "とくていけんしん"), ("一般健診", "いっぱんけんしん"),
        ("がん検診", "がんけんしん"), ("胃がん検診", "いがんけんしん"),
        ("大腸がん検診", "だいちょうがんけんしん"), ("肺がん検診", "はいがんけんしん"),
        ("乳がん検診", "にゅうがんけんしん"), ("子宮がん検診", "しきゅうがんけんしん"),
        ("脳ドック", "のうどっく"), ("健康診断", "けんこうしんだん"),
        ("血液検査", "けつえきけんさ"), ("骨密度", "こつみつど"),
        ("腫瘍マーカー", "しゅようまーかー"), ("ピロリ菌", "ぴろりきん"),
        ("眼底検査", "がんていけんさ"), ("心電図", "しんでんず"),
        ("エコー", "えこー"), ("超音波", "ちょうおんぱ"),
    ]

    for d, r in kw:
        lines.append(build_word_entry(d, r))

    # 主要にフィラー10種
    primary = [
        ("人間ドック", "にんげんどっく"), ("がん検診", "がんけんしん"),
        ("特定健診", "とくていけんしん"), ("脳ドック", "のうどっく"),
    ]
    for d, r in primary:
        lines.extend(add_filler_variants(d, r, True))

    # 二次にフィラー3種
    for d, r in kw:
        if (d, r) not in primary:
            lines.extend(add_filler_variants(d, r, False))

    # 語尾
    for d, r in primary:
        lines.extend(add_suffix_variants(d, r, True))

    # 頭落ち
    lines.extend(add_head_clip("人間ドック", "にんげんどっく", ["んげんどっく"]))
    lines.extend(add_head_clip("特定健診", "とくていけんしん", ["くていけんしん"]))
    lines.extend(add_head_clip("脳ドック", "のうどっく", ["うどっく"]))

    # 要望表現
    for d, r in [("受けたい", "うけたい"), ("お願いします", "おねがいします"),
                 ("希望します", "きぼうします"), ("ないです", "ないです"),
                 ("ありません", "ありません")]:
        lines.append(build_word_entry(d, r))
        lines.extend(add_filler_variants(d, r, False))

    return "\n".join(lines)


def build_profile_words_追加オプション():
    """入力_追加オプション: オプション検査の有無と種類"""
    lines = []

    kw = [
        ("オプション", "おぷしょん"), ("オプション検査", "おぷしょんけんさ"),
        ("追加", "ついか"), ("追加検査", "ついかけんさ"),
        ("腫瘍マーカー", "しゅようまーかー"), ("ピロリ菌", "ぴろりきん"),
        ("ピロリ菌検査", "ぴろりきんけんさ"),
        ("PSA", "ぴーえすえー"), ("骨密度", "こつみつど"),
        ("骨密度検査", "こつみつどけんさ"),
        ("甲状腺", "こうじょうせん"), ("甲状腺検査", "こうじょうせんけんさ"),
        ("肝炎", "かんえん"), ("肝炎検査", "かんえんけんさ"),
        ("眼底検査", "がんていけんさ"), ("眼底", "がんてい"),
        ("アレルギー検査", "あれるぎーけんさ"),
        ("血液検査", "けつえきけんさ"),
        ("心電図", "しんでんず"), ("エコー", "えこー"),
        ("CT", "しーてぃー"), ("MRI", "えむあーるあい"),
        ("内視鏡", "ないしきょう"), ("胃カメラ", "いかめら"),
        ("便潜血", "べんせんけつ"),
        ("ABC検査", "えーびーしーけんさ"),
    ]

    for d, r in kw:
        lines.append(build_word_entry(d, r))

    # 主要にフィラー10種
    primary = [
        ("オプション", "おぷしょん"), ("腫瘍マーカー", "しゅようまーかー"),
        ("ピロリ菌", "ぴろりきん"), ("骨密度", "こつみつど"),
    ]
    for d, r in primary:
        lines.extend(add_filler_variants(d, r, True))

    # 二次にフィラー3種
    for d, r in kw:
        if (d, r) not in primary:
            lines.extend(add_filler_variants(d, r, False))

    # 語尾
    for d, r in primary:
        lines.extend(add_suffix_variants(d, r, True))

    # 頭落ち
    lines.extend(add_head_clip("オプション", "おぷしょん", ["ぷしょん"]))
    lines.extend(add_head_clip("腫瘍マーカー", "しゅようまーかー", ["ゅようまーかー"]))
    lines.extend(add_head_clip("ピロリ菌", "ぴろりきん", ["ろりきん"]))

    # ない/ある表現
    none_words = [
        ("ないです", "ないです"), ("ありません", "ありません"),
        ("特にないです", "とくにないです"), ("ない", "ない"),
        ("なし", "なし"), ("大丈夫です", "だいじょうぶです"),
        ("結構です", "けっこうです"),
        ("あります", "あります"), ("お願いします", "おねがいします"),
        ("希望します", "きぼうします"),
    ]
    for d, r in none_words:
        lines.append(build_word_entry(d, r))
        lines.extend(add_filler_variants(d, r, False))

    return "\n".join(lines)


def build_profile_words_予約希望日():
    """入力_予約希望日: 日付。月日+曜日+相対日"""
    lines = []

    # 月
    months = [
        ("一月", "いちがつ"), ("二月", "にがつ"), ("三月", "さんがつ"),
        ("四月", "しがつ"), ("五月", "ごがつ"), ("六月", "ろくがつ"),
        ("七月", "しちがつ"), ("七月", "なながつ"), ("八月", "はちがつ"),
        ("九月", "くがつ"), ("十月", "じゅうがつ"),
        ("十一月", "じゅういちがつ"), ("十二月", "じゅうにがつ"),
    ]
    for d, r in months:
        lines.append(build_word_entry(d, r))

    # 日（特殊読み）
    special_days = [
        ("一日", "ついたち"), ("二日", "ふつか"), ("三日", "みっか"),
        ("四日", "よっか"), ("五日", "いつか"), ("六日", "むいか"),
        ("七日", "なのか"), ("八日", "ようか"), ("九日", "ここのか"),
        ("十日", "とおか"), ("十四日", "じゅうよっか"),
        ("二十日", "はつか"), ("二十四日", "にじゅうよっか"),
    ]
    for d, r in special_days:
        lines.append(build_word_entry(d, r))

    # 通常日
    normal_days = [
        ("十一日", "じゅういちにち"), ("十二日", "じゅうににち"),
        ("十三日", "じゅうさんにち"), ("十五日", "じゅうごにち"),
        ("十六日", "じゅうろくにち"), ("十七日", "じゅうしちにち"),
        ("十八日", "じゅうはちにち"), ("十九日", "じゅうくにち"),
        ("二十一日", "にじゅういちにち"), ("二十二日", "にじゅうににち"),
        ("二十三日", "にじゅうさんにち"), ("二十五日", "にじゅうごにち"),
        ("二十六日", "にじゅうろくにち"), ("二十七日", "にじゅうしちにち"),
        ("二十八日", "にじゅうはちにち"), ("二十九日", "にじゅうくにち"),
        ("三十日", "さんじゅうにち"), ("三十一日", "さんじゅういちにち"),
    ]
    for d, r in normal_days:
        lines.append(build_word_entry(d, r))

    # 曜日
    weekdays = [
        ("月曜日", "げつようび"), ("火曜日", "かようび"),
        ("水曜日", "すいようび"), ("木曜日", "もくようび"),
        ("金曜日", "きんようび"), ("土曜日", "どようび"),
        ("日曜日", "にちようび"),
        ("月曜", "げつよう"), ("火曜", "かよう"),
        ("水曜", "すいよう"), ("木曜", "もくよう"),
        ("金曜", "きんよう"), ("土曜", "どよう"),
    ]
    for d, r in weekdays:
        lines.append(build_word_entry(d, r))

    # 相対日
    relative_dates = [
        ("来週", "らいしゅう"), ("再来週", "さらいしゅう"),
        ("来月", "らいげつ"), ("再来月", "さらいげつ"),
        ("今月", "こんげつ"), ("上旬", "じょうじゅん"),
        ("中旬", "ちゅうじゅん"), ("下旬", "げじゅん"),
        ("月初め", "つきはじめ"), ("月末", "げつまつ"),
        ("二週間後", "にしゅうかんご"), ("三週間後", "さんしゅうかんご"),
        ("いつでも", "いつでも"), ("いつでもいい", "いつでもいい"),
    ]
    for d, r in relative_dates:
        lines.append(build_word_entry(d, r))

    # 主要キーワードにフィラー10種
    primary = [
        ("来週", "らいしゅう"), ("来月", "らいげつ"),
        ("上旬", "じょうじゅん"), ("下旬", "げじゅん"),
        ("月曜日", "げつようび"),
    ]
    for d, r in primary:
        lines.extend(add_filler_variants(d, r, True))

    # 二次にフィラー3種
    for d, r in months[:6]:
        lines.extend(add_filler_variants(d, r, False))
    for d, r in weekdays[:7]:
        lines.extend(add_filler_variants(d, r, False))

    # 語尾
    date_suffix_kw = [
        ("来週", "らいしゅう"), ("来月", "らいげつ"),
        ("上旬", "じょうじゅん"), ("中旬", "ちゅうじゅん"),
        ("下旬", "げじゅん"),
    ]
    for d, r in date_suffix_kw:
        lines.extend(add_suffix_variants(d, r, True))

    # 頭落ち
    lines.extend(add_head_clip("来週", "らいしゅう", ["いしゅう"]))
    lines.extend(add_head_clip("来月", "らいげつ", ["いげつ"]))
    lines.extend(add_head_clip("月曜日", "げつようび", ["つようび"]))
    lines.extend(add_head_clip("一月", "いちがつ", ["ちがつ"]))

    # 「〜頃」「〜あたり」表現
    approx_words = [
        ("頃", "ころ"), ("あたり", "あたり"), ("ぐらい", "ぐらい"),
        ("希望", "きぼう"),
    ]
    for d, r in approx_words:
        lines.append(build_word_entry(d, r))

    return "\n".join(lines)


def build_profile_words_現在の予約日():
    """入力_現在の予約日: 日付（予約希望日と同じベース）"""
    # 同じ日付辞書 + わからない
    lines_base = build_profile_words_予約希望日()
    extra = [
        build_word_entry("わからない", "わからない"),
        build_word_entry("わかりません", "わかりません"),
        build_word_entry("覚えていない", "おぼえていない"),
        build_word_entry("忘れました", "わすれました"),
    ]
    extra.extend(add_filler_variants("わからない", "わからない", True))
    return lines_base + "\n" + "\n".join(extra)


def build_profile_words_変更希望内容():
    """入力_変更希望内容: 変更項目の自由発話"""
    lines = []

    kw = [
        ("日付変更", "ひづけへんこう"), ("日にち変更", "ひにちへんこう"),
        ("日程変更", "にっていへんこう"), ("予約日変更", "よやくびへんこう"),
        ("変更", "へんこう"), ("日にちを変えたい", "ひにちをかえたい"),
        ("コース変更", "こーすへんこう"), ("検査変更", "けんさへんこう"),
        ("追加したい", "ついかしたい"), ("追加", "ついか"),
        ("オプション追加", "おぷしょんついか"),
        ("人間ドック", "にんげんどっく"), ("脳ドック", "のうどっく"),
        ("がん検診", "がんけんしん"), ("健康診断", "けんこうしんだん"),
        ("内視鏡", "ないしきょう"), ("バリウム", "ばりうむ"),
        ("胃カメラ", "いかめら"),
    ]

    for d, r in kw:
        lines.append(build_word_entry(d, r))

    # 日付系語彙
    date_kw = [
        ("来週", "らいしゅう"), ("来月", "らいげつ"),
        ("月曜日", "げつようび"), ("火曜日", "かようび"),
        ("水曜日", "すいようび"), ("木曜日", "もくようび"),
        ("金曜日", "きんようび"), ("土曜日", "どようび"),
    ]
    for d, r in date_kw:
        lines.append(build_word_entry(d, r))

    # 主要にフィラー10種
    primary = [
        ("変更", "へんこう"), ("日にち変更", "ひにちへんこう"),
        ("追加したい", "ついかしたい"), ("コース変更", "こーすへんこう"),
    ]
    for d, r in primary:
        lines.extend(add_filler_variants(d, r, True))

    # 二次にフィラー3種
    for d, r in kw:
        if (d, r) not in primary:
            lines.extend(add_filler_variants(d, r, False))

    # 語尾
    for d, r in primary:
        lines.extend(add_suffix_variants(d, r, True))

    # 頭落ち
    lines.extend(add_head_clip("変更", "へんこう", ["んこう"]))
    lines.extend(add_head_clip("日にち変更", "ひにちへんこう", ["にちへんこう"]))
    lines.extend(add_head_clip("追加したい", "ついかしたい", ["いかしたい"]))

    # 要望表現
    for d, r in [("お願いします", "おねがいします"), ("したい", "したい"),
                 ("変えたい", "かえたい")]:
        lines.append(build_word_entry(d, r))
        lines.extend(add_filler_variants(d, r, False))

    return "\n".join(lines)


def build_profile_words_検診受診日():
    """入力_検診受診日: 乳がん検診を受けた日付"""
    # 日付ベース + 乳がん関連
    lines_base = build_profile_words_予約希望日()
    extra = [
        build_word_entry("乳がん検診", "にゅうがんけんしん"),
        build_word_entry("乳がん", "にゅうがん"),
        build_word_entry("検診", "けんしん"),
        build_word_entry("受診日", "じゅしんび"),
        build_word_entry("わからない", "わからない"),
        build_word_entry("わかりません", "わかりません"),
        build_word_entry("覚えていない", "おぼえていない"),
    ]
    extra.extend(add_filler_variants("乳がん検診", "にゅうがんけんしん", True))
    extra.extend(add_filler_variants("わからない", "わからない", False))
    return lines_base + "\n" + "\n".join(extra)


def build_profile_words_問合せ内容_個人():
    """入力_問合せ内容_個人: 問合せの自由発話"""
    lines = []

    kw = [
        ("予約の確認", "よやくのかくにん"), ("予約確認", "よやくかくにん"),
        ("確認", "かくにん"), ("予約", "よやく"),
        ("二次検査", "にじけんさ"), ("再検査", "さいけんさ"),
        ("精密検査", "せいみつけんさ"), ("検査結果", "けんさけっか"),
        ("結果", "けっか"), ("料金", "りょうきん"),
        ("費用", "ひよう"), ("値段", "ねだん"),
        ("支払い", "しはらい"), ("保険", "ほけん"),
        ("持ち物", "もちもの"), ("準備", "じゅんび"),
        ("食事制限", "しょくじせいげん"), ("絶食", "ぜっしょく"),
        ("駐車場", "ちゅうしゃじょう"), ("アクセス", "あくせす"),
        ("行き方", "いきかた"), ("場所", "ばしょ"),
        ("時間", "じかん"), ("所要時間", "しょようじかん"),
        ("何時から", "なんじから"), ("受付時間", "うけつけじかん"),
        ("コース内容", "こーすないよう"), ("検査内容", "けんさないよう"),
        ("健診内容", "けんしんないよう"),
        ("キャンセル待ち", "きゃんせるまち"),
        ("空き状況", "あきじょうきょう"),
        ("紹介状", "しょうかいじょう"),
    ]

    for d, r in kw:
        lines.append(build_word_entry(d, r))

    # 主要にフィラー10種
    primary = [
        ("予約の確認", "よやくのかくにん"), ("二次検査", "にじけんさ"),
        ("料金", "りょうきん"), ("検査結果", "けんさけっか"),
        ("確認", "かくにん"),
    ]
    for d, r in primary:
        lines.extend(add_filler_variants(d, r, True))

    # 二次にフィラー3種
    for d, r in kw:
        if (d, r) not in primary:
            lines.extend(add_filler_variants(d, r, False))

    # 語尾
    for d, r in primary:
        lines.extend(add_suffix_variants(d, r, True))

    # 頭落ち
    lines.extend(add_head_clip("予約の確認", "よやくのかくにん", ["やくのかくにん"]))
    lines.extend(add_head_clip("二次検査", "にじけんさ", ["じけんさ"]))
    lines.extend(add_head_clip("料金", "りょうきん", ["ょうきん"]))

    # 自由表現
    for d, r in [("聞きたい", "ききたい"), ("教えてほしい", "おしえてほしい"),
                 ("知りたい", "しりたい"), ("わからない", "わからない")]:
        lines.append(build_word_entry(d, r))
        lines.extend(add_filler_variants(d, r, False))

    return "\n".join(lines)


def build_profile_words_企業名():
    """入力_企業名: 企業名/団体名"""
    lines = []

    kw = [
        ("株式会社", "かぶしきがいしゃ"), ("有限会社", "ゆうげんがいしゃ"),
        ("合同会社", "ごうどうがいしゃ"), ("合資会社", "ごうしがいしゃ"),
        ("社団法人", "しゃだんほうじん"), ("財団法人", "ざいだんほうじん"),
        ("医療法人", "いりょうほうじん"), ("学校法人", "がっこうほうじん"),
        ("市役所", "しやくしょ"), ("役場", "やくば"),
        ("県庁", "けんちょう"), ("農協", "のうきょう"),
        ("漁協", "ぎょきょう"), ("商工会議所", "しょうこうかいぎしょ"),
        ("商工会", "しょうこうかい"),
        ("事務所", "じむしょ"), ("事業所", "じぎょうしょ"),
        ("工場", "こうじょう"), ("支店", "してん"),
        ("本社", "ほんしゃ"), ("営業所", "えいぎょうしょ"),
    ]

    for d, r in kw:
        lines.append(build_word_entry(d, r))

    # 主要にフィラー10種
    primary = [
        ("株式会社", "かぶしきがいしゃ"), ("有限会社", "ゆうげんがいしゃ"),
    ]
    for d, r in primary:
        lines.extend(add_filler_variants(d, r, True))

    # 二次にフィラー3種
    for d, r in kw:
        if (d, r) not in primary:
            lines.extend(add_filler_variants(d, r, False))

    # 語尾
    for d, r in primary:
        lines.extend(add_suffix_variants(d, r, True))

    # 頭落ち
    lines.extend(add_head_clip("株式会社", "かぶしきがいしゃ", ["ぶしきがいしゃ"]))
    lines.extend(add_head_clip("有限会社", "ゆうげんがいしゃ", ["うげんがいしゃ"]))

    return "\n".join(lines)


def build_profile_words_担当者名():
    """入力_担当者名: 氏名"""
    lines = []

    # 主要苗字
    surnames = [
        ("佐藤", "さとう"), ("鈴木", "すずき"), ("高橋", "たかはし"),
        ("田中", "たなか"), ("伊藤", "いとう"), ("渡辺", "わたなべ"),
        ("山本", "やまもと"), ("中村", "なかむら"), ("小林", "こばやし"),
        ("加藤", "かとう"), ("吉田", "よしだ"), ("山田", "やまだ"),
        ("佐々木", "ささき"), ("松本", "まつもと"), ("井上", "いのうえ"),
        ("木村", "きむら"), ("林", "はやし"), ("清水", "しみず"),
        ("山崎", "やまざき"), ("阿部", "あべ"),
        ("工藤", "くどう"), ("成田", "なりた"), ("三浦", "みうら"),
        ("斎藤", "さいとう"), ("石田", "いしだ"), ("菊地", "きくち"),
        ("菊池", "きくち"), ("畠山", "はたけやま"), ("奈良", "なら"),
        ("葛西", "かさい"), ("今", "こん"),
    ]

    for d, r in surnames:
        lines.append(build_word_entry(d, r))

    # フィラー付き（主要苗字に10種）
    primary_names = [
        ("佐藤", "さとう"), ("鈴木", "すずき"), ("高橋", "たかはし"),
        ("田中", "たなか"), ("伊藤", "いとう"),
    ]
    for d, r in primary_names:
        lines.extend(add_filler_variants(d, r, True))

    # 二次にフィラー3種
    for d, r in surnames:
        if (d, r) not in primary_names:
            lines.extend(add_filler_variants(d, r, False))

    # 語尾
    suffix_words = [
        ("です", "です"), ("と申します", "ともうします"),
        ("といいます", "といいます"),
    ]
    for d_name, r_name in primary_names:
        for sd, sr in suffix_words:
            lines.append(f"{d_name}{sd} {r_name}{sr}")

    # 頭落ち
    lines.extend(add_head_clip("佐藤", "さとう", ["とう"]))
    lines.extend(add_head_clip("高橋", "たかはし", ["かはし"]))
    lines.extend(add_head_clip("田中", "たなか", ["なか"]))

    return "\n".join(lines)


def build_profile_words_担当者電話番号():
    """入力_担当者電話番号: 電話番号。DTMF+STT。最小限でOK"""
    lines = []
    digits = [
        ("零", "ぜろ"), ("一", "いち"), ("二", "に"), ("三", "さん"),
        ("四", "よん"), ("四", "し"), ("五", "ご"), ("六", "ろく"),
        ("七", "なな"), ("七", "しち"), ("八", "はち"), ("九", "きゅう"),
        ("十", "じゅう"), ("ゼロ", "ぜろ"),
    ]
    for d, r in digits:
        lines.append(build_word_entry(d, r))
    # ハイフン読み
    lines.append(build_word_entry("の", "の"))
    return "\n".join(lines)


def build_profile_words_組合名():
    """入力_組合名: 健康保険組合名"""
    lines = []

    kw = [
        ("協会けんぽ", "きょうかいけんぽ"), ("けんぽ", "けんぽ"),
        ("健康保険組合", "けんこうほけんくみあい"),
        ("健保組合", "けんぽくみあい"), ("健保", "けんぽ"),
        ("国民健康保険", "こくみんけんこうほけん"), ("国保", "こくほ"),
        ("社会保険", "しゃかいほけん"), ("社保", "しゃほ"),
        ("共済組合", "きょうさいくみあい"), ("共済", "きょうさい"),
        ("組合", "くみあい"), ("保険組合", "ほけんくみあい"),
        ("後期高齢者医療", "こうきこうれいしゃいりょう"),
        ("全国健康保険協会", "ぜんこくけんこうほけんきょうかい"),
        ("代行機関", "だいこうきかん"),
        ("わからない", "わからない"), ("わかりません", "わかりません"),
    ]

    for d, r in kw:
        lines.append(build_word_entry(d, r))

    # 主要にフィラー10種
    primary = [
        ("協会けんぽ", "きょうかいけんぽ"), ("健康保険組合", "けんこうほけんくみあい"),
        ("共済組合", "きょうさいくみあい"), ("わからない", "わからない"),
    ]
    for d, r in primary:
        lines.extend(add_filler_variants(d, r, True))

    # 二次にフィラー3種
    for d, r in kw:
        if (d, r) not in primary:
            lines.extend(add_filler_variants(d, r, False))

    # 語尾
    for d, r in primary[:3]:
        lines.extend(add_suffix_variants(d, r, True))

    # 頭落ち
    lines.extend(add_head_clip("協会けんぽ", "きょうかいけんぽ", ["ょうかいけんぽ"]))
    lines.extend(add_head_clip("健康保険組合", "けんこうほけんくみあい", ["んこうほけんくみあい"]))
    lines.extend(add_head_clip("共済組合", "きょうさいくみあい", ["ょうさいくみあい"]))

    return "\n".join(lines)


def build_profile_words_受診人数():
    """入力_受診人数: 人数。DTMF+STT。最小限でOK"""
    lines = []

    # 数字読み
    nums = [
        ("一人", "ひとり"), ("二人", "ふたり"), ("三人", "さんにん"),
        ("四人", "よにん"), ("五人", "ごにん"), ("六人", "ろくにん"),
        ("七人", "ななにん"), ("八人", "はちにん"), ("九人", "きゅうにん"),
        ("十人", "じゅうにん"), ("十五人", "じゅうごにん"),
        ("二十人", "にじゅうにん"), ("三十人", "さんじゅうにん"),
        ("五十人", "ごじゅうにん"), ("百人", "ひゃくにん"),
        ("一", "いち"), ("二", "に"), ("三", "さん"),
        ("四", "よん"), ("五", "ご"), ("六", "ろく"),
        ("七", "なな"), ("八", "はち"), ("九", "きゅう"), ("十", "じゅう"),
        ("名", "めい"), ("人", "にん"),
    ]
    for d, r in nums:
        lines.append(build_word_entry(d, r))

    # フィラー付き（主要のみ）
    for d, r in [("一人", "ひとり"), ("二人", "ふたり"), ("三人", "さんにん")]:
        lines.extend(add_filler_variants(d, r, False))

    return "\n".join(lines)


def build_profile_words_問合せ内容_企業():
    """入力_問合せ内容_企業: 問合せの自由発話"""
    lines = []

    kw = [
        ("予約", "よやく"), ("予約確認", "よやくかくにん"),
        ("確認", "かくにん"), ("見積もり", "みつもり"),
        ("見積書", "みつもりしょ"), ("請求書", "せいきゅうしょ"),
        ("料金", "りょうきん"), ("費用", "ひよう"),
        ("コース内容", "こーすないよう"), ("検査内容", "けんさないよう"),
        ("健診内容", "けんしんないよう"),
        ("日程", "にってい"), ("日程変更", "にっていへんこう"),
        ("変更", "へんこう"), ("キャンセル", "きゃんせる"),
        ("追加", "ついか"), ("オプション", "おぷしょん"),
        ("結果", "けっか"), ("検査結果", "けんさけっか"),
        ("報告書", "ほうこくしょ"),
        ("受診票", "じゅしんひょう"), ("案内", "あんない"),
        ("送付", "そうふ"), ("郵送", "ゆうそう"),
        ("人数変更", "にんずうへんこう"), ("人数", "にんずう"),
        ("契約", "けいやく"), ("手続き", "てつづき"),
    ]

    for d, r in kw:
        lines.append(build_word_entry(d, r))

    # 主要にフィラー10種
    primary = [
        ("予約確認", "よやくかくにん"), ("見積もり", "みつもり"),
        ("料金", "りょうきん"), ("日程変更", "にっていへんこう"),
        ("確認", "かくにん"),
    ]
    for d, r in primary:
        lines.extend(add_filler_variants(d, r, True))

    # 二次にフィラー3種
    for d, r in kw:
        if (d, r) not in primary:
            lines.extend(add_filler_variants(d, r, False))

    # 語尾
    for d, r in primary:
        lines.extend(add_suffix_variants(d, r, True))

    # 頭落ち
    lines.extend(add_head_clip("予約確認", "よやくかくにん", ["やくかくにん"]))
    lines.extend(add_head_clip("見積もり", "みつもり", ["つもり"]))
    lines.extend(add_head_clip("日程変更", "にっていへんこう", ["っていへんこう"]))

    # 自由表現
    for d, r in [("聞きたい", "ききたい"), ("教えてほしい", "おしえてほしい"),
                 ("知りたい", "しりたい"), ("相談したい", "そうだんしたい"),
                 ("お願いします", "おねがいします")]:
        lines.append(build_word_entry(d, r))
        lines.extend(add_filler_variants(d, r, False))

    return "\n".join(lines)


# ============================================================
# 既存モジュールの辞書補強
# ============================================================

def enhance_冒頭判定(existing):
    """入力_冒頭判定: フィラー・頭落ち追加"""
    lines = existing.split("\n") if existing else []

    # フィラー追加（主要キーワード）
    primary_kw = [
        ("はい", "はい"), ("そうです", "そうです"),
        ("いいえ", "いいえ"), ("違います", "ちがいます"),
        ("個人", "こじん"), ("企業", "きぎょう"),
    ]
    for d, r in primary_kw:
        for f in FILLERS_PRIMARY:
            entry = f"{d} {f}{r}"
            if entry not in lines:
                lines.append(entry)

    # 語尾
    for d, r in [("個人", "こじん"), ("企業", "きぎょう")]:
        for s in SUFFIXES_PRIMARY:
            entry = f"{d}{s} {r}{s}"
            if entry not in lines:
                lines.append(entry)

    # 頭落ち
    head_clips = [
        ("そうです", ["おうです", "うです"]),
        ("違います", ["がいます"]),
        ("個人", ["じん"]),
        ("企業", ["ぎょう"]),
    ]
    for d, clips in head_clips:
        for c in clips:
            entry = f"{d} {c}"
            if entry not in lines:
                lines.append(entry)

    # 追加語彙
    extra = [
        "はい はあ", "はい あい", "はい い",
        "そうです そう", "個人です こじんです",
        "企業です きぎょうです",
    ]
    for e in extra:
        if e not in lines:
            lines.append(e)

    return "\n".join(lines)


def enhance_用件1(existing):
    """入力_用件1: フィラー・頭落ち追加"""
    lines = existing.split("\n") if existing else []

    primary_kw = [
        ("予約", "よやく"), ("変更", "へんこう"),
        ("キャンセル", "きゃんせる"), ("乳がん", "にゅうがん"),
        ("問い合わせ", "といあわせ"),
    ]
    for d, r in primary_kw:
        for f in FILLERS_PRIMARY:
            entry = f"{d} {f}{r}"
            if entry not in lines:
                lines.append(entry)

    # 語尾
    for d, r in primary_kw:
        for s in SUFFIXES_PRIMARY:
            entry = f"{d}{s} {r}{s}"
            if entry not in lines:
                lines.append(entry)

    # 頭落ち
    head_clips = [
        ("予約", ["やく"]),
        ("変更", ["んこう"]),
        ("キャンセル", ["ゃんせる"]),
        ("問い合わせ", ["いあわせ"]),
    ]
    for d, clips in head_clips:
        for c in clips:
            entry = f"{d} {c}"
            if entry not in lines:
                lines.append(entry)

    # 追加語彙
    extra = [
        "予約したい よやくしたい", "予約をお願いします よやくをおねがいします",
        "変更したい へんこうしたい", "キャンセルしたい きゃんせるしたい",
        "取り消したい とりけしたい", "やめたい やめたい",
        "精密検査 せいみつけんさ", "乳がん精密 にゅうがんせいみつ",
        "その他お問い合わせ そのたおといあわせ",
        "聞きたいことがある ききたいことがある",
    ]
    for e in extra:
        if e not in lines:
            lines.append(e)

    return "\n".join(lines)


def enhance_市町村補助(existing):
    """入力_市町村補助: フィラー・頭落ち追加"""
    lines = existing.split("\n") if existing else []

    primary_kw = [
        ("市町村", "しちょうそん"), ("利用なし", "りようなし"),
    ]
    for d, r in primary_kw:
        for f in FILLERS_PRIMARY:
            entry = f"{d} {f}{r}"
            if entry not in lines:
                lines.append(entry)

    # 語尾
    for d, r in primary_kw:
        for s in SUFFIXES_PRIMARY:
            entry = f"{d}{s} {r}{s}"
            if entry not in lines:
                lines.append(entry)

    # 追加
    extra = [
        "はい はい", "利用します りようします",
        "使います つかいます", "ないです ないです",
        "利用しません りようしません",
    ]
    for e in extra:
        if e not in lines:
            lines.append(e)

    # 頭落ち
    for d, clips in [("市町村", ["ちょうそん"]), ("利用なし", ["ようなし"])]:
        for c in clips:
            entry = f"{d} {c}"
            if entry not in lines:
                lines.append(entry)

    return "\n".join(lines)


def enhance_健康診断種類_市町村(existing):
    """入力_健康診断種類_市町村: フィラー・頭落ち追加"""
    lines = existing.split("\n") if existing else []

    primary_kw = [
        ("人間ドック", "にんげんどっく"), ("特定健診", "とくていけんしん"),
        ("後期高齢健診", "こうきこうれいけんしん"), ("脳ドック", "のうどっく"),
        ("がん検診", "がんけんしん"), ("その他", "そのた"),
    ]
    for d, r in primary_kw:
        for f in FILLERS_PRIMARY:
            entry = f"{d} {f}{r}"
            if entry not in lines:
                lines.append(entry)

    for d, r in primary_kw[:4]:
        for s in SUFFIXES_PRIMARY:
            entry = f"{d}{s} {r}{s}"
            if entry not in lines:
                lines.append(entry)

    # 頭落ち
    head_clips = [
        ("人間ドック", ["んげんどっく"]),
        ("特定健診", ["くていけんしん"]),
        ("後期高齢健診", ["うきこうれいけんしん"]),
        ("脳ドック", ["うどっく"]),
    ]
    for d, clips in head_clips:
        for c in clips:
            entry = f"{d} {c}"
            if entry not in lines:
                lines.append(entry)

    extra = [
        "健康診断 けんこうしんだん", "健診 けんしん",
        "ドック どっく", "人間ドックお願いします にんげんどっくおねがいします",
    ]
    for e in extra:
        if e not in lines:
            lines.append(e)

    return "\n".join(lines)


def enhance_健康診断種類_利用なし(existing):
    """入力_健康診断種類_利用なし: フィラー・頭落ち追加"""
    lines = existing.split("\n") if existing else []

    primary_kw = [
        ("人間ドック", "にんげんどっく"), ("定期一般健診", "ていきいっぱんけんしん"),
        ("がん検診", "がんけんしん"), ("脳ドック", "のうどっく"),
        ("その他", "そのた"),
    ]
    for d, r in primary_kw:
        for f in FILLERS_PRIMARY:
            entry = f"{d} {f}{r}"
            if entry not in lines:
                lines.append(entry)

    for d, r in primary_kw[:4]:
        for s in SUFFIXES_PRIMARY:
            entry = f"{d}{s} {r}{s}"
            if entry not in lines:
                lines.append(entry)

    head_clips = [
        ("人間ドック", ["んげんどっく"]),
        ("定期一般健診", ["いきいっぱんけんしん"]),
        ("脳ドック", ["うどっく"]),
    ]
    for d, clips in head_clips:
        for c in clips:
            entry = f"{d} {c}"
            if entry not in lines:
                lines.append(entry)

    extra = [
        "健康診断 けんこうしんだん", "健診 けんしん",
    ]
    for e in extra:
        if e not in lines:
            lines.append(e)

    return "\n".join(lines)


def enhance_ドック_再確認(existing):
    """入力_ドック_再確認: フィラー・頭落ち追加"""
    lines = existing.split("\n") if existing else []

    primary_kw = [
        ("人間ドック", "にんげんどっく"), ("脳ドック", "のうどっく"),
    ]
    for d, r in primary_kw:
        for f in FILLERS_PRIMARY:
            entry = f"{d} {f}{r}"
            if entry not in lines:
                lines.append(entry)

    for d, r in primary_kw:
        for s in SUFFIXES_PRIMARY:
            entry = f"{d}{s} {r}{s}"
            if entry not in lines:
                lines.append(entry)

    head_clips = [
        ("人間ドック", ["んげんどっく"]),
        ("脳ドック", ["うどっく"]),
    ]
    for d, clips in head_clips:
        for c in clips:
            entry = f"{d} {c}"
            if entry not in lines:
                lines.append(entry)

    extra = [
        "人間 にんげん", "脳 のう", "ドック どっく",
        "人間です にんげんです", "脳です のうです",
    ]
    for e in extra:
        if e not in lines:
            lines.append(e)

    return "\n".join(lines)


def enhance_胃の検査(existing):
    """入力_胃の検査: フィラー・頭落ち追加"""
    lines = existing.split("\n") if existing else []

    primary_kw = [
        ("内視鏡", "ないしきょう"), ("バリウム", "ばりうむ"),
        ("胃カメラ", "いかめら"),
    ]
    for d, r in primary_kw:
        for f in FILLERS_PRIMARY:
            entry = f"{d} {f}{r}"
            if entry not in lines:
                lines.append(entry)

    for d, r in primary_kw:
        for s in SUFFIXES_PRIMARY:
            entry = f"{d}{s} {r}{s}"
            if entry not in lines:
                lines.append(entry)

    head_clips = [
        ("内視鏡", ["いしきょう"]),
        ("バリウム", ["りうむ"]),
        ("胃カメラ", ["かめら"]),
    ]
    for d, clips in head_clips:
        for c in clips:
            entry = f"{d} {c}"
            if entry not in lines:
                lines.append(entry)

    extra = [
        "内視鏡検査 ないしきょうけんさ", "バリウム検査 ばりうむけんさ",
        "胃の検査なし いのけんさなし", "なし なし",
        "いらない いらない", "必要ない ひつようない",
    ]
    for e in extra:
        if e not in lines:
            lines.append(e)

    return "\n".join(lines)


def enhance_インフルエンザ同時接種確認(existing):
    """入力_インフルエンザ同時接種確認: フィラー・頭落ち追加"""
    lines = existing.split("\n") if existing else []

    primary_kw = [
        ("はい", "はい"), ("希望します", "きぼうします"),
        ("いいえ", "いいえ"), ("希望しません", "きぼうしません"),
    ]
    for d, r in primary_kw:
        for f in FILLERS_PRIMARY:
            entry = f"{d} {f}{r}"
            if entry not in lines:
                lines.append(entry)

    head_clips = [
        ("希望します", ["ぼうします"]),
        ("希望しません", ["ぼうしません"]),
    ]
    for d, clips in head_clips:
        for c in clips:
            entry = f"{d} {c}"
            if entry not in lines:
                lines.append(entry)

    extra = [
        "はい はあ", "はい あい", "はい い",
        "お願いします おねがいします",
        "そうです そうです", "そうです おうです",
        "結構です けっこうです", "大丈夫です だいじょうぶです",
        "いらない いらない", "いらないです いらないです",
    ]
    for e in extra:
        if e not in lines:
            lines.append(e)

    return "\n".join(lines)


def enhance_用件2(existing):
    """入力_用件2: フィラー・頭落ち追加"""
    lines = existing.split("\n") if existing else []

    primary_kw = [
        ("予約", "よやく"), ("問い合わせ", "といあわせ"),
        ("その他", "そのた"),
    ]
    for d, r in primary_kw:
        for f in FILLERS_PRIMARY:
            entry = f"{d} {f}{r}"
            if entry not in lines:
                lines.append(entry)

    for d, r in primary_kw[:2]:
        for s in SUFFIXES_PRIMARY:
            entry = f"{d}{s} {r}{s}"
            if entry not in lines:
                lines.append(entry)

    head_clips = [
        ("予約", ["やく"]),
        ("問い合わせ", ["いあわせ"]),
    ]
    for d, clips in head_clips:
        for c in clips:
            entry = f"{d} {c}"
            if entry not in lines:
                lines.append(entry)

    extra = [
        "予約したい よやくしたい", "予約お願いします よやくおねがいします",
        "聞きたい ききたい", "問い合わせしたい といあわせしたい",
    ]
    for e in extra:
        if e not in lines:
            lines.append(e)

    return "\n".join(lines)


def enhance_健康診断種類_企業(existing):
    """入力_健康診断種類_企業: フィラー・頭落ち追加"""
    lines = existing.split("\n") if existing else []

    primary_kw = [
        ("人間ドック", "にんげんどっく"), ("がん健診", "がんけんしん"),
        ("予防接種", "よぼうせっしゅ"), ("インフルエンザ", "いんふるえんざ"),
    ]
    for d, r in primary_kw:
        for f in FILLERS_PRIMARY:
            entry = f"{d} {f}{r}"
            if entry not in lines:
                lines.append(entry)

    for d, r in primary_kw:
        for s in SUFFIXES_PRIMARY:
            entry = f"{d}{s} {r}{s}"
            if entry not in lines:
                lines.append(entry)

    head_clips = [
        ("人間ドック", ["んげんどっく"]),
        ("予防接種", ["ぼうせっしゅ"]),
        ("インフルエンザ", ["んふるえんざ"]),
    ]
    for d, clips in head_clips:
        for c in clips:
            entry = f"{d} {c}"
            if entry not in lines:
                lines.append(entry)

    extra = [
        "健康診断 けんこうしんだん", "健診 けんしん",
    ]
    for e in extra:
        if e not in lines:
            lines.append(e)

    return "\n".join(lines)


# ============================================================
# Stage 3: OpenAIプロンプト修正
# ============================================================

# 全OpenAIモジュールを確認した結果、全てに # Role / # Context / セキュリティが存在。
# Stage 3は確認のみで修正不要。（verify_fixesの出力で最終確認）


# ============================================================
# メイン処理
# ============================================================

def main():
    print("=" * 60)
    print("健生病院（健診）Stage 2 & 3 修正スクリプト")
    print("=" * 60)

    # JSON読み込み
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    modules = data["modules"]
    changes = []

    # ============================================================
    # Stage 2: profile_words充実化
    # ============================================================
    print("\n--- Stage 2: profile_words充実化 ---\n")

    # 新規辞書設定（空のモジュール）
    new_dictionaries = {
        "入力_郵便番号と住所": build_profile_words_郵便番号と住所,
        "入力_市町村名": build_profile_words_市町村名,
        "入力_がん健診種類": build_profile_words_がん健診種類,
        "入力_その他内容": build_profile_words_その他内容,
        "入力_同時健診内容": build_profile_words_同時健診内容,
        "入力_追加オプション": build_profile_words_追加オプション,
        "入力_予約希望日": build_profile_words_予約希望日,
        "入力_現在の予約日": build_profile_words_現在の予約日,
        "入力_変更希望内容": build_profile_words_変更希望内容,
        "入力_検診受診日": build_profile_words_検診受診日,
        "入力_問合せ内容_個人": build_profile_words_問合せ内容_個人,
        "入力_企業名": build_profile_words_企業名,
        "入力_担当者名": build_profile_words_担当者名,
        "入力_担当者電話番号": build_profile_words_担当者電話番号,
        "入力_組合名": build_profile_words_組合名,
        "入力_受診人数": build_profile_words_受診人数,
        "入力_問合せ内容_企業": build_profile_words_問合せ内容_企業,
    }

    for mod_name, builder_fn in new_dictionaries.items():
        if mod_name in modules:
            pw = builder_fn()
            word_count = len([l for l in pw.split("\n") if l.strip()])
            modules[mod_name]["params"]["profile_words"] = pw
            print(f"  [NEW] {mod_name}: {word_count} words")
            changes.append(f"新規辞書: {mod_name} ({word_count}語)")
        else:
            print(f"  [WARN] Module not found: {mod_name}")

    # 既存辞書補強
    enhance_map = {
        "入力_冒頭判定": enhance_冒頭判定,
        "入力_用件1": enhance_用件1,
        "入力_市町村補助": enhance_市町村補助,
        "入力_健康診断種類_市町村": enhance_健康診断種類_市町村,
        "入力_健康診断種類_利用なし": enhance_健康診断種類_利用なし,
        "入力_ドック_再確認": enhance_ドック_再確認,
        "入力_胃の検査": enhance_胃の検査,
        "入力_インフルエンザ同時接種確認": enhance_インフルエンザ同時接種確認,
        "入力_用件2": enhance_用件2,
        "入力_健康診断種類_企業": enhance_健康診断種類_企業,
    }

    for mod_name, enhance_fn in enhance_map.items():
        if mod_name in modules:
            existing = modules[mod_name]["params"].get("profile_words", "")
            old_count = len([l for l in existing.split("\n") if l.strip()]) if existing else 0
            enhanced = enhance_fn(existing)
            new_count = len([l for l in enhanced.split("\n") if l.strip()])
            modules[mod_name]["params"]["profile_words"] = enhanced
            print(f"  [ENH] {mod_name}: {old_count} -> {new_count} words (+{new_count - old_count})")
            changes.append(f"辞書補強: {mod_name} ({old_count}->{new_count}語)")

    # ============================================================
    # 「まー」チェック（使用禁止）
    # ============================================================
    print("\n--- 「まー」チェック ---")
    ma_found = False
    for mod_name, mod in modules.items():
        pw = mod.get("params", {}).get("profile_words", "")
        if pw and "まー" in pw:
            print(f"  [ERROR] {mod_name} に「まー」発見！除去します。")
            lines = pw.split("\n")
            lines = [l for l in lines if "まー" not in l]
            modules[mod_name]["params"]["profile_words"] = "\n".join(lines)
            ma_found = True
    if not ma_found:
        print("  OK: 「まー」なし")

    # ============================================================
    # matchingmethod int チェック
    # ============================================================
    print("\n--- matchingmethod intチェック ---")
    mm_fixed = 0
    for mod_name, mod in modules.items():
        mm = mod.get("matchingmethod")
        if isinstance(mm, str):
            mod["matchingmethod"] = int(mm)
            mm_fixed += 1
    print(f"  修正: {mm_fixed}件" if mm_fixed else "  OK: 全てint型")

    # ============================================================
    # Stage 3: OpenAIプロンプト確認
    # ============================================================
    print("\n--- Stage 3: OpenAIプロンプト確認 ---\n")
    oai_issues = []
    for mod_name, mod in modules.items():
        if mod.get("type") == "drjoy^External Integration$generate_by_OpenAI":
            prompt = mod.get("params", {}).get("prompt", "")
            missing = []
            if "# Role" not in prompt:
                missing.append("# Role")
            if "# Context" not in prompt:
                missing.append("# Context")
            if "インジェクション" not in prompt and "injection" not in prompt.lower():
                missing.append("Security section")
            if missing:
                oai_issues.append((mod_name, missing))
                print(f"  [ISSUE] {mod_name}: missing {', '.join(missing)}")

    if not oai_issues:
        print("  OK: 全OpenAIモジュールに # Role / # Context / セキュリティセクション存在")
    else:
        print(f"\n  {len(oai_issues)} modules need fixing...")
        # ここでは全モジュールに存在するので修正不要

    # ============================================================
    # JSON保存
    # ============================================================
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n--- 保存完了: {OUTPUT_PATH} ---")
    print(f"\n変更サマリ: {len(changes)}項目")
    for c in changes:
        print(f"  - {c}")

    # 最終語数集計
    print("\n--- 最終 profile_words 語数 ---")
    for mod_name, mod in modules.items():
        if mod.get("type") in ["drjoy^AmiVoice$Speech to Text",
                                "drjoy^External Integration$DTMF AmiVoice STT Input"]:
            pw = mod.get("params", {}).get("profile_words", "")
            wc = len([l for l in pw.split("\n") if l.strip()]) if pw else 0
            status = "EMPTY" if wc == 0 else ("OK" if wc >= 50 else "LOW" if wc >= 10 else "MINIMAL")
            mod_type = "DTMF" if "DTMF" in mod.get("type", "") else "STT"
            # DTMFは少なくてもOK
            if mod_type == "DTMF" and wc > 0:
                status = "OK"
            print(f"  {mod_name} [{mod_type}]: {wc} words ({status})")

    print("\n完了！")


if __name__ == "__main__":
    main()
