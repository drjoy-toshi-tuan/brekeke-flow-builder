# -*- coding: utf-8 -*-
"""checkup_course_classifier — Python 参照実装（オラクル）／engine v3 universe

期待値の SSoT は acceptance_test/cases.tsv（テストが正）。正本は script.js（Nashorn/ES5.1）。
同一辞書・同一手順・同一順序で構造的に一致させる。

#274 universe 化（engine v3）:
  - CATEGORIES を実ログ/DR universe の「コース種別」へ差し替え（施設非依存）。
  - DTMF を data-driven（DTMF_MAP・@spec）に変更（旧 v2 はハードコード）。
  - GENERIC_FALLBACK も data-driven（@spec）。
  - facility_offered（任意 set）対応: カテゴリ一致ラベルが施設非提供なら "ラベル|OFF_MENU"。
  - FOLDINGS は spec。実ログ最大の「一般健診/健康診断」(5,928)を種別化するため
    `健康診断→健診` の畳みは外す（`検診→健診`・`健康診査→健診` は維持）。
engine（normalize / 判定手順 / facility_offered filter / DTMF・GENERIC の data-driven 参照）は
施設非依存。FACILITY_OFFERED は wiring（施設別に配線）。
"""

import unicodedata

ZEN_DIGITS = "０１２３４５６７８９"
HAN_DIGITS = "0123456789"
ZEN_UPPER = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
ZEN_LOWER = "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
ASCII_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ASCII_LOWER = "abcdefghijklmnopqrstuvwxyz"

PUNCT = "、。，．,.・･:;：；!！?？…‥〜～「」『』()（）[]【】<>＜＞\"'“”‘’｢｣-　 \t\r\n"

# @spec-begin
# 実ログ最大の 一般健診/健康診断 を潰さないため 健康診断→健診 は畳まない（検診/健康診査 のみ健診へ）。
FOLDINGS = [
    ("健康診査", "健診"),
    ("検診", "健診"),
]

WAKARANAI_MARKERS = [
    "わからない", "わかりません", "わかんない", "分からない", "分かりません",
]

# カテゴリ優先（上から・部分一致・先勝ち・単一出力）。抽出2ケース（雇用時/市区町村）を最優先。
CATEGORIES = [
    ("雇用時健診", ["雇用時", "雇用の健", "雇い入れ", "雇入れ", "入社時", "入社前", "採用時", "就職時"]),
    ("市区町村健診", ["市の健", "市民健", "市健診", "区の健", "区民健", "町の健", "村の健",
                  "自治体", "住民健", "特定健", "特定健康", "後期高齢", "がん検診クーポン"]),
    ("協会けんぽ・生活習慣病予防健診", ["協会けんぽ", "けんぽ", "協会健保", "生活習慣", "成人病"]),
    ("一般・定期健診", ["一般健", "一般の健", "健康診断", "定期健", "定期の健", "基本健", "職場の健", "会社の健", "法定健"]),
    ("レディース・専門ドック", ["レディース", "女性ドック", "ウィメンズ", "婦人科", "脳ドック", "心臓ドック",
                        "肺ドック", "眼科ドック", "消化器ドック", "pet", "ペット", "がんドック", "なでしこ"]),
    ("人間ドック", ["人間ドック", "ドック", "半日", "一日ドック", "1日ドック", "一泊", "1泊", "日帰り", "胃カメラ", "バリウム"]),
]

GENERIC_FALLBACK_KEY = "健診"
GENERIC_FALLBACK_LABEL = "その他の健診"

# DTMF は施設ごとに割当が違う（下記は universe 既定・facility 側で差し替え）。data-driven。
DTMF_MAP = {"1": "人間ドック", "2": "一般・定期健診", "3": "協会けんぽ・生活習慣病予防健診", "4": "市区町村健診"}
# @spec-end

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


def classify(value, facility_offered=None):
    s = normalize(value)
    # 1. 空
    if not s:
        return RESULT_NONE
    # 2. 数字のみ（DTMF 併用・data-driven）
    if _is_digits_only(s):
        return DTMF_MAP.get(s, RESULT_NONE)
    # 3. わからない検知 → その他の健診（-6 誘導文言と整合）
    for m in WAKARANAI_MARKERS:
        if m in s:
            return GENERIC_FALLBACK_LABEL
    # 4. カテゴリ走査（優先順位順・部分一致・先勝ち）
    for label, keys in CATEGORIES:
        for k in keys:
            if k in s:
                if facility_offered is not None and label not in facility_offered:
                    return label + "|OFF_MENU"
                return label
    # 5. 総称の受け皿走査
    if GENERIC_FALLBACK_KEY in s:
        return GENERIC_FALLBACK_LABEL
    # 6. 不一致
    return RESULT_NONE
