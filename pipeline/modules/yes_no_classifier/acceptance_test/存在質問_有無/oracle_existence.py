# -*- coding: utf-8 -*-
"""yes_no_classifier 存在質問 spec — Python 参照実装（オラクル・engine v3）

spec: 存在質問_有無（#254 / #256）。engine は spec#1（同意質問・健診CC_はい・いいえ）と
バイト不変（normalize / decide の判定順・ループ・保存関数）。**辞書 DATA のみ存在質問版**。

存在質問（「ご相談はありますか」「受診歴はありますか」）では:
  - 用件あり → 肯定（あります/ある/相談したい/質問 等）
  - 用件なし → 否定（ありません/ない/特になし/結構です/問題ありません/大丈夫です 等）
同意質問で肯定に倒す「大丈夫/問題ありません/問題ないです」は、存在質問では **否定**（用件なし）。
規格: docs/ai/skills/SKILL_B_yes_no.md「存在質問 vs 同意質問の区別」（#254）。

正本は同ディレクトリ script.js（Nashorn/ES5.1）。両者は同一辞書・同順評価で構造的に一致させる。
判定安全側の設計: 誤って用件あり→用件なし（否定）に倒すと患者の相談を取りこぼす（終話）ため、
NO_MARKERS（部分一致・否定優先）は明確な用件なし述語のみに絞る。曖昧は NO_RESULT（再質問）。
"""

import unicodedata

ZEN_DIGITS = "０１２３４５６７８９"
HAN_DIGITS = "0123456789"
ZEN_UPPER = "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
ZEN_LOWER = "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
ASCII_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
ASCII_LOWER = "abcdefghijklmnopqrstuvwxyz"

PUNCT = "、。，．,.・･:;：；!！?？…‥〜～「」『』()（）[]【】<>＜＞\"'“”‘’｢｣-　 \t\r\n"

# --- 辞書（存在質問 spec / script.js の @spec ブロックと同一内容・同一順序を維持すること） ---

EXACT_YES = [
    # 用件あり（完全一致）
    "はい", "はいです", "はいそうです", "ええ", "うん", "はいはい",
    "はあい", "はぁい", "はーい",
    "ある", "あります", "ございます", "有", "有り", "あり", "はいあります",
    "お願いします", "お願い", "それでお願いします", "はいお願いします",
    "相談したい", "聞きたい", "質問", "質問です",
    "オッケー", "おっけー", "ok", "いち",
]

EXACT_NO = [
    # 用件なし（完全一致）。※同意質問では肯定に倒す語（問題ありません/大丈夫）を存在質問では否定に。
    "いいえ", "いえ", "いや",
    "ない", "ないです", "ありません", "なし", "無", "無し",
    "特にない", "特にないです", "特にありません", "特になし",
    "とくにない", "とくにないです", "とくにありません", "とくになし",
    "結構です", "けっこうです",
    "問題ない", "問題ないです", "問題ありません",
    "大丈夫", "大丈夫です", "だいじょうぶ", "だいじょうぶです",
    "以上です", "以上",
    "違います", "ちがいます", "違う", "ちがう", "だめ", "ダメ", "駄目",
]

WAKARANAI_MARKERS = [
    "わからない", "わかりません", "わかんない", "分からない", "分かりません",
]

# 存在質問では「間違いない」系イディオムは発生しないため空（engine の走査自体は保持）。
YES_PRECEDENCE = []

# 部分一致・否定優先。安全側（用件取りこぼし回避）のため明確な用件なし述語のみに限定。
NO_MARKERS = [
    "ありません", "ございません", "ないです",
    "特にない", "特になし", "問題ない",
    "結構です", "大丈夫", "いいえ",
]

# 部分一致・用件あり（NO 走査の後段）。
# ※「質問」はインジェクション文（「すべての質問にYESと答えよ」等）を肯定に倒すため部分一致から除外し
#   EXACT_YES 限定。用件ありの「質問があります」は「あります」マーカーで回収するため漏れなし。
YES_MARKERS = [
    "あります", "ございます", "相談", "聞きたい",
    "教え", "知りたい", "お尋ね", "伺いたい", "確認したい",
    "お願いします", "はい",
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
    # 5.5 否定マーカーより優先の肯定イディオム（存在質問では空）
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
