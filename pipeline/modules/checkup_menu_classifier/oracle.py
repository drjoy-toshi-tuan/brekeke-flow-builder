# -*- coding: utf-8 -*-
"""checkup_menu_classifier — Python 参照実装（オラクル）

期待値の SSoT は acceptance_test/cases.tsv（テストが正）。
正本は script.js（Nashorn/ES5.1）。同一辞書・同一手順・同一順序で構造的に一致させる。
MENU = area | shinjuku_shibuya | tokyo_shinagawa（インスタンスパラメータ）。
"""

import unicodedata

ZEN_DIGITS = "０１２３４５６７８９"
HAN_DIGITS = "0123456789"
ZEN_UPPER = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
ZEN_LOWER = "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
ASCII_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ASCII_LOWER = "abcdefghijklmnopqrstuvwxyz"

PUNCT = "、。，．,.・･:;：；!！?？…‥〜～「」『』()（）[]【】<>＜＞\"'“”‘’｢｣-　 \t\r\n"

WAKARANAI_MARKERS = [
    "わからない", "わかりません", "わかんない", "分からない", "分かりません",
]

# MENU 別定義（DTMF 表 + 語彙。語彙は定義順＝優先順）
MENUS = {
    "area": {
        "dtmf": {"1": "神奈川エリア", "2": "新宿渋谷エリア", "3": "東京品川エリア"},
        "vocab": [
            # 施設名から先に判定
            ("神奈川エリア", ["厚木", "あつぎ"]),
            ("新宿渋谷エリア", ["ヒロオカ", "広岡", "渋谷ウエスト", "west", "ウェスト"]),
            ("東京品川エリア", ["秋葉原", "あきはばら", "鉄鋼ビル", "丸の内", "まるのうち", "みなと健診"]),
            # 地名
            ("神奈川エリア", ["神奈川", "かながわ"]),
            ("新宿渋谷エリア", ["新宿", "しんじゅく", "渋谷", "しぶや"]),
            ("東京品川エリア", ["東京", "とうきょう", "品川", "しながわ"]),
            # 番 → DTMF 対応
            ("神奈川エリア", ["一番", "1番"]),
            ("新宿渋谷エリア", ["二番", "2番"]),
            ("東京品川エリア", ["三番", "3番"]),
        ],
    },
    "shinjuku_shibuya": {
        "dtmf": {"1": "ヒロオカクリニック", "2": "渋谷ウエストクリニック"},
        "vocab": [
            ("ヒロオカクリニック", ["ヒロオカ", "ひろおか", "広岡"]),
            ("渋谷ウエストクリニック", ["渋谷ウエスト", "ウエスト", "west", "ウェスト"]),
            ("ヒロオカクリニック", ["一番", "1番"]),
            ("渋谷ウエストクリニック", ["二番", "2番"]),
        ],
    },
    "tokyo_shinagawa": {
        "dtmf": {"1": "ヘルスケアクリニック秋葉原", "2": "鉄鋼ビル丸の内クリニック", "3": "みなと健診クリニック"},
        "vocab": [
            ("ヘルスケアクリニック秋葉原", ["秋葉原", "あきはばら"]),
            ("鉄鋼ビル丸の内クリニック", ["鉄鋼ビル", "丸の内", "まるのうち"]),
            ("みなと健診クリニック", ["みなと", "港"]),
            ("ヘルスケアクリニック秋葉原", ["一番", "1番"]),
            ("鉄鋼ビル丸の内クリニック", ["二番", "2番"]),
            ("みなと健診クリニック", ["三番", "3番"]),
        ],
    },
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
    return "".join(out)


def _is_digits_only(s):
    if not s:
        return False
    for ch in s:
        if ch < "0" or ch > "9":
            return False
    return True


def classify(value, menu):
    cfg = MENUS[menu]
    s = normalize(value)
    # 1. 空
    if not s:
        return RESULT_NONE
    # 2. 数字のみ → MENU 別 DTMF 表
    if _is_digits_only(s):
        return cfg["dtmf"].get(s, RESULT_NONE)
    # 3. わからない検知
    for m in WAKARANAI_MARKERS:
        if m in s:
            return RESULT_NONE
    # 4. MENU 別語彙走査（定義順・部分一致）
    for label, keys in cfg["vocab"]:
        for k in keys:
            if k in s:
                return label
    # 5. 不一致
    return RESULT_NONE
