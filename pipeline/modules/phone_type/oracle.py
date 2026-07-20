# -*- coding: utf-8 -*-
"""phone_type — Python 参照実装（オラクル）

期待値の SSoT は acceptance_test/cases.tsv（テストが正）。
正本は script.js（Nashorn/ES5.1）。両者は同一規則・同順評価で構造的に一致させる。

規則（050=その他。本番 script_携帯判別 準拠）:
  1. 入力から数字以外を除去
  2. 11 桁 かつ 先頭 060/070/080/090 → 携帯（060 も携帯 11 桁）
  3. 10 桁 かつ 先頭 0[1-9]       → 固定（050 は 11 桁なので該当せず・10 桁 06x 大阪は固定）
  4. それ以外                     → その他
"""

import re

RESULT_MOBILE = "携帯"
RESULT_FIXED = "固定"
RESULT_DEFAULT = "その他"

_MOBILE_RE = re.compile(r"^(060|070|080|090)")
_FIXED_RE = re.compile(r"^0[1-9]")
_MOBILE_LEN = 11
_FIXED_LEN = 10


def classify(value):
    """電話番号文字列 → 携帯 / 固定 / その他。"""
    if isinstance(value, dict):
        value = value.get("text", "")
    s = "" if value is None else str(value)
    num = re.sub(r"[^0-9]", "", s)
    if len(num) == _MOBILE_LEN and _MOBILE_RE.match(num):
        return RESULT_MOBILE
    if len(num) == _FIXED_LEN and _FIXED_RE.match(num):
        return RESULT_FIXED
    return RESULT_DEFAULT
