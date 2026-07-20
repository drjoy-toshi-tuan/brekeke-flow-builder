# -*- coding: utf-8 -*-
"""yes_no_classifier — Python 参照実装（オラクル・engine v3）

期待値の SSoT は acceptance_test/cases.tsv（テストが正）。
正本は script.js（Nashorn/ES5.1）。両者は同一辞書・同順評価で構造的に一致させる。
String.normalize 不使用の限定正規化（department_classifier と同方式）。

engine v3（2026-07-01・被覆スコアカード昇格 #256）:
  [ENGINE] step 5.5 = YES_PRECEDENCE 走査を新設（NO_MARKERS 走査より前）。
           「間違いない」系（=誤りが無い=肯定）が `違い`/`間違い` 否定マーカーに
           食われる誤被覆 M を評価順で根治。engine_version v2 -> v3。
  [SPEC]  EXACT_YES / NO_MARKERS / YES_MARKERS にマーカー追記（G 取りこぼし回収）。
           bare `違い` を NO_MARKERS に足せるのは step 5.5 で 間違いない系が
           先に肯定確定するため。
"""

import unicodedata

ZEN_DIGITS = "０１２３４５６７８９"
HAN_DIGITS = "0123456789"
ZEN_UPPER = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
ZEN_LOWER = "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
ASCII_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ASCII_LOWER = "abcdefghijklmnopqrstuvwxyz"

PUNCT = "、。，．,.・･:;：；!！?？…‥〜～「」『』()（）[]【】<>＜＞\"'“”‘’｢｣-　 \t\r\n"

# --- 辞書（script.js と同一内容・同一順序を維持すること） ---

EXACT_YES = [
    "はい", "はいです", "はいそうです", "そうです", "そうですね", "そうですよ",
    "ええ", "うん", "はいはい",
    "大丈夫", "大丈夫です", "合ってます", "合っています", "あってます", "あっています",
    "正しいです", "それで", "それでお願いします", "お願いします",
    "オッケー", "おっけー", "ok", "いち",
    "いいです", "いいですよ", "いいよ",
    # #279: 承諾の「よろしい」系（生年月日復唱等の確認応答・完全一致＝部分一致誤爆なし）
    "よろしい", "よろしいです", "よろしいですね", "よろしいですよ", "宜しい", "宜しいです",
    "ございます", "問題ないです", "問題ありません", "構いません", "構わないです", "かまいません",
    "います", "いる",
    "はあい", "はぁい", "はーい",
    # A3 Phase2: 有無/該当 polar 設問の肯定側ドメイン語（完全一致のみ＝部分一致誤爆なし）
    "有", "有り", "あり", "ある", "該当", "該当する", "該当します",
    # scorecard v1.1 G 回収（完全一致＝部分一致誤爆/インジェクション混入を避ける）
    # ラベル語(肯定/yes/イエス)・「お願い」はマーカー化すると R014/R019/R020 を壊すため EXACT 限定。
    "そう", "その通り", "その通りです", "お願い",
    "肯定", "肯定です", "yes", "イエス", "イエスです",
]

EXACT_NO = [
    "いいえ", "いえ", "いや",
    "違います", "ちがいます", "違う", "ちがう", "違いました",
    "間違い", "間違いです", "間違っています",
    "ダメ", "だめ", "駄目", "やめて", "やり直し", "もう一度",
    "に", "いません", "いない", "ありません", "ないです", "当てはまりません",
    # A3 Phase2: 有無/該当 polar 設問の否定側ドメイン語（完全一致のみ＝部分一致誤爆なし）
    "無", "無し", "なし", "ない", "非該当", "該当しない", "該当しません",
    # #290: 否定側ラベル語（EXACT_YES「肯定/肯定です」と対称・完全一致＝部分一致誤爆なし）
    "否定", "否定です",
]

WAKARANAI_MARKERS = [
    "わからない", "わかりません", "わかんない", "分からない", "分かりません",
]

# step 5.5: NO_MARKERS より優先の肯定イディオム（「間違いない」=誤りが無い=肯定）。
# bare `違い`/`間違い` 否定マーカーに食われるのを評価順で根治する（engine v3 新設）。
YES_PRECEDENCE = [
    "間違いない", "間違いなし", "間違いありません", "間違いなく",
]

# 部分一致・否定優先。「ない」単独は誤爆するため述語形のみ（REQUIREMENTS 参照）
NO_MARKERS = [
    "当てはまりません", "ありません", "ないそうです", "ないです",
    "違います", "ちがいます", "違いました", "違う", "ちがう",
    "いいえ", "間違い", "駄目", "だめ", "ダメ", "やめて", "やり直し",
    # scorecard v1.1 G 回収（bare `違い` は step5.5 で 間違いない系が先に肯定確定ゆえ安全）
    "違い", "間違え", "間違っ", "嫌",
]

YES_MARKERS = [
    "当てはまります", "そうです", "あります", "お願いします", "希望します", "はい",
    # scorecard v1.1 G 回収（語幹マーカー＝変種吸収・NO 走査の後段ゆえ極性反転語に食われない）
    # ※ ラベル語(肯定/yes/イエス)・「お願い」は EXACT_YES 側（インジェクション/再質問の過剰被覆回避）。
    "お願いいたします", "同じ", "了解", "正しい", "さよう",
    "合っ", "正解", "かしこまり", "もちろん", "わかった", "拝承", "当たって",
    # #279: 「よろしい」語幹（よろしいかと/よろしいでしょう 等の変種吸収・NO 走査の後段ゆえ極性反転語に食われない）
    "よろしい",
]

RESULT_YES = "肯定"
RESULT_NO = "否定"
RESULT_NONE = "NO_RESULT"


def normalize(value):
    if isinstance(value, dict):
        value = value.get("text", "")
    s = "" if value is None else str(value)
    s = unicodedata.normalize("NFKC", s)
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


def classify(value):
    """発話 → 肯定 / 否定 / NO_RESULT（上から評価・一致したら即終了）。"""
    s = normalize(value)
    # 1. 空
    if not s:
        return RESULT_NONE
    # 2. 数字のみ（DTMF 流入）
    if _is_digits_only(s):
        if s == "1":
            return RESULT_YES
        if s == "2":
            return RESULT_NO
        return RESULT_NONE
    # 3. 完全一致（肯定）
    if s in EXACT_YES:
        return RESULT_YES
    # 4. 完全一致（否定）
    if s in EXACT_NO:
        return RESULT_NO
    # 5. わからない検知（「ないです」誤爆防止のためマーカー走査より先）
    for m in WAKARANAI_MARKERS:
        if m in s:
            return RESULT_NONE
    # 5.5 否定マーカーより優先の肯定イディオム（間違いない系・engine v3 新設）
    for m in YES_PRECEDENCE:
        if m in s:
            return RESULT_YES
    # 6. 否定マーカー走査（否定優先）
    for m in NO_MARKERS:
        if m in s:
            return RESULT_NO
    # 7. 肯定マーカー走査
    for m in YES_MARKERS:
        if m in s:
            return RESULT_YES
    # 8. 不一致
    return RESULT_NONE
