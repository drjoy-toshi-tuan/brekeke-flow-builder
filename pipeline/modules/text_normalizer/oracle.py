#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""text_normalizer のオラクル（決定論変換の Python 実装・テストが正）。

script.js の engine と同一ロジックをここに実装し、test_oracle.py で全ケース PASS を担保する。

この部品は分類器ではなく「変換器」: 自由テキスト聴取値（STT 生文字列）を
意味を書き換えずにクリーン化して返す。
  1. 全角英数字・全角記号 → 半角（カタカナ・かな・漢字は不変）
  2. 全角スペース → 半角、連続空白を 1 つに圧縮、前後 trim
  3. フィラー・言い淀み（えーと/あのー/えっと 等）を除去（直後の読点ごと）
  4. 読点/句点の正規化（，→、 ．→。）、末尾の句点・読点を除去
  5. 結果が空になったら元の trim 済み文字列を返す（冪等・情報を捨てない）

要約・言い換え・敬語変換は行わない（意味の書き換え禁止）。
ES5.1(Nashorn) へ同一手順で移植できる素朴な文字列処理のみを使う。
"""
from __future__ import annotations

import re

# フィラー語彙（トークン境界に接するときのみ除去。語中は触らない）
# 長い順に並べる（最長一致）
_FILLERS = [
    "なんていうか", "あのですね", "うーんと", "ええと",
    "えーっと", "えーと", "えっと", "あのー", "あのう",
    "そのー", "そのう", "うーん", "なんか",
    "まぁ", "まあ", "えー", "あー", "うー",
]

# 文末の丁寧体コピュラ（意味を変えずに落とせる語のみ）。
# 「ます」系（〜します/〜たいです以外の動詞語尾/〜ません 等）は対象外:
#   ・「〜ます」を削ると動詞語幹が壊れる（例:「確認します」→「確認し」）
#   ・「〜ません」は否定の意味そのものを担うため削ると意味が反転する
#     （例:「眠れません」→「眠れ」は真逆の意味になる）
# そのため対象は「です」とその活用（でした/ですね/ですよ/ですわ）のみに限定する。
_TRAILING_COPULA = ["ですわ", "ですね", "ですよ", "でした", "です"]

_FW_ASCII_START = 0xFF01  # ！
_FW_ASCII_END = 0xFF5E    # ～
_HW_OFFSET = 0xFEE0


def _to_halfwidth(text: str) -> str:
    """全角英数字・記号を半角へ。全角スペースは半角スペースへ。"""
    out = []
    for ch in text:
        code = ord(ch)
        if ch == "　":
            out.append(" ")
        elif _FW_ASCII_START <= code <= _FW_ASCII_END:
            out.append(chr(code - _HW_OFFSET))
        else:
            out.append(ch)
    return "".join(out)


def _strip_fillers(text: str) -> str:
    """フィラーを除去する。フィラー直後の読点・空白も一緒に落とす。

    トークン境界の定義: 文字列先頭 / 読点・句点・空白の直後。
    語中（例: 「なんかんだ」等の一部）を壊さないよう、境界に接する
    フィラーのみ最長一致で繰り返し除去する。
    """
    changed = True
    while changed:
        changed = False
        for f in _FILLERS:
            if text.startswith(f):
                rest = text[len(f):]
                rest = re.sub(r"^[、,。\s]+", "", rest)
                text = rest
                changed = True
                break
            m = re.search(r"([、,。\s])" + re.escape(f) + r"[、,\s]*", text)
            if m:
                text = text[: m.start(1) + 1] + text[m.end():]
                changed = True
                break
    return text


def _strip_trailing_copula(text: str) -> str:
    """文末の丁寧体コピュラ（です/でした/ですね/ですよ/ですわ）を除去する。

    直前の空白ごと落とす（例:「太郎 です」→「太郎」）。繰り返し適用（冪等になるまで）。
    """
    changed = True
    while changed:
        changed = False
        for c in _TRAILING_COPULA:
            m = re.search(r"\s*" + re.escape(c) + r"$", text)
            if m:
                text = text[: m.start()]
                changed = True
                break
    return text


def classify(utterance: str) -> str:
    """入力（生 STT 自由テキスト）→ クリーン化済みテキストを返す。

    分類器ではないためラベルではなく変換後文字列が戻り値。
    空入力・変換で空になる入力は元の trim 済み文字列を返す（冪等）。
    """
    raw = utterance if isinstance(utterance, str) else ""
    original = raw.strip()

    # 句読点の正規化は半角化より先に行う（，．が ASCII , . に化ける前に、。へ寄せる）
    text = raw.replace("，", "、").replace("．", "。")
    text = _to_halfwidth(text)
    text = _strip_fillers(text)
    # 連続空白の圧縮・trim
    text = re.sub(r"\s+", " ", text).strip()
    # 連続読点の圧縮と、先頭・末尾の句読点除去
    text = re.sub(r"、{2,}", "、", text)
    text = re.sub(r"^[、。]+", "", text)
    text = re.sub(r"[、。]+$", "", text)
    # 文末の丁寧体コピュラ除去（です系のみ。ます系は意味を壊すため対象外）
    text = _strip_trailing_copula(text).strip()

    return text if text else original
