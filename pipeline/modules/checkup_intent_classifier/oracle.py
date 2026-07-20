# -*- coding: utf-8 -*-
"""checkup_intent_classifier — Python 参照実装（オラクル）

期待値の SSoT は acceptance_test/cases.tsv（テストが正）。
正本は script.js（Nashorn/ES5.1）。同一辞書・同一手順・同一順序で構造的に一致させる。
用件確認(n4) と 遅刻種別確認(-4) の両方で使う（SOURCE_MODULE のみ差し替え）。
"""

import unicodedata

ZEN_DIGITS = "０１２３４５６７８９"
HAN_DIGITS = "0123456789"
ZEN_UPPER = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
ZEN_LOWER = "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
ASCII_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ASCII_LOWER = "abcdefghijklmnopqrstuvwxyz"

PUNCT = "、。，．,.・･:;：；!！?？…‥〜～「」『』()（）[]【】<>＜＞\"'“”‘’｢｣-　 \t\r\n"

# 表記揺れ畳み込み（正規化の最終段。順序固定: 長い語から）
FOLDINGS = [
    ("健康診断", "健診"),
    ("健康診査", "健診"),
    ("検診", "健診"),
    ("一番", "1"),
    ("二番", "2"),
    ("三番", "3"),
    ("四番", "4"),
    ("1番", "1"),
    ("2番", "2"),
    ("3番", "3"),
    ("4番", "4"),
]

WAKARANAI_MARKERS = [
    "わからない", "わかりません", "わかんない", "分からない", "分かりません",
]

# カテゴリ語彙（マスタ）。走査順・活性集合は SCOPES が文脈ごとに規定する。
CATEGORY_KEYS = {
    "その他": ["その他", "そのほか", "問い合わせ", "問合せ", "問いあわせ", "質問", "聞きたい", "伺いたい", "相談", "確認"],
    "変更": ["変更", "変えたい", "変えて", "ずらしたい", "ずらして", "日にちを変え", "日程を変え", "時間を変え"],
    "キャンセル": ["キャンセル", "取り消し", "取消", "取りやめ", "中止", "やめたい", "やめます", "やめて"],
    "雇用時健診": ["雇用時健診", "雇用時の健診", "雇い入れ", "雇入れ", "入社時健診", "入社前健診", "入社前の健診", "入社時の健診"],
    "遅刻": ["遅刻", "時刻", "遅れ", "間に合いません", "間に合わない", "間に合わなそう"],
    "予約": ["予約", "受けたい", "受診したい", "申し込み", "申込"],
}

# SCOPE = 第一層TTSが提示した出口に一致する活性カテゴリ（評価順）。文脈ごとに切替（インスタンス設定行）。
#   full     = 用件確認（フル・その他=FAQ含む。現行と同一順序＝full既定で既存挙動を不変に保つ）
#   lateness = 遅刻種別確認（遅刻 or 変更・キャンセル の二択。その他/予約/健診系は出口でない＝持たない）
SCOPES = {
    "full":     ["その他", "変更", "キャンセル", "雇用時健診", "遅刻", "予約"],
    "lateness": ["遅刻", "変更", "キャンセル"],
}

# DTMF も SCOPE 別。lateness はTTSがDTMFを提示しない（speech-only）→数字は NO_RESULT。
DTMF_BY_SCOPE = {
    "full":     {"1": "予約", "2": "変更", "3": "キャンセル", "4": "その他"},
    "lateness": {},
}

RESULT_NONE = "NO_RESULT"


def normalize(value):
    if isinstance(value, dict):
        value = value.get("text", "")
    s = "" if value is None else str(value)
    s = unicodedata.normalize("NFKC", s)  # 半角カナ/全半/互換を正規化（FAQ Matcher と同方式）
    out = []
    for ch in s:
        i = ZEN_DIGITS.find(ch)
        if i >= 0:
            out.append(HAN_DIGITS[i])
            continue
        i = ZEN_UPPER.find(ch)
        if i >= 0:
            out.append(ASCII_LOWER[i])
            continue
        i = ZEN_LOWER.find(ch)
        if i >= 0:
            out.append(ASCII_LOWER[i])
            continue
        i = ASCII_UPPER.find(ch)
        if i >= 0:
            out.append(ASCII_LOWER[i])
            continue
        if PUNCT.find(ch) >= 0:
            continue
        out.append(ch)
    s = "".join(out)
    for src, dst in FOLDINGS:
        s = s.replace(src, dst)
    return s


def _is_digits_only(s):
    if not s:
        return False
    for ch in s:
        if ch < "0" or ch > "9":
            return False
    return True


def classify(value, scope="full"):
    cats = SCOPES.get(scope)
    if cats is None:
        cats = SCOPES["full"]  # 未知スコープは full にフォールバック（設定行未注入の保険）
    s = normalize(value)
    # 1. 空
    if not s:
        return RESULT_NONE
    # 2. 数字のみ（DTMF 併用・SCOPE 別表。lateness は空＝NO_RESULT）
    if _is_digits_only(s):
        return DTMF_BY_SCOPE.get(scope, DTMF_BY_SCOPE["full"]).get(s, RESULT_NONE)
    # 3. わからない検知
    for m in WAKARANAI_MARKERS:
        if m in s:
            return RESULT_NONE
    # 4. カテゴリ走査（SCOPE の活性カテゴリのみ・評価順・部分一致）
    for label in cats:
        for k in CATEGORY_KEYS[label]:
            if k in s:
                return label
    # 5. 不一致
    return RESULT_NONE
