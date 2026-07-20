#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_enrich_nchoice_config.py — n_choice spec 既定シノニム注入の受入テスト（issue #279 ①③）。

実行: python test_enrich_nchoice_config.py
終了コード 0 = 全 PASS。FAIL があれば一覧を出して 1。

検証:
  ③ DTMF_MAP 数字キー → TOKEN_MAP 音声表記（N番/音読み/漢数字）を自動付与（1-9 のみ）
  ① KEYWORD/COMPOUND_PATTERNS の有無ラベル result → 所持表現を regex 追記
  + 冪等 / author 既存尊重 / JSON パース失敗ガード / 非有無ラベル非発火 / DTMF 非数字非発火
  + enrich 後 config で n_choice oracle が期待通り分類する end-to-end 一致
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_MODULES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "modules", "n_choice")
sys.path.insert(0, _MODULES)

from scaffold_generator import _enrich_nchoice_config  # noqa: E402
import oracle as nchoice_oracle  # modules/n_choice/oracle.py  # noqa: E402

_FAILS: list = []


def check(cond: bool, label: str) -> None:
    if not cond:
        _FAILS.append(label)


def _cfg(tp: dict) -> dict:
    """template_params(JSON文字列) → n_choice oracle config。"""
    def j(k, d):
        v = tp.get(k, d)
        return json.loads(v) if isinstance(v, str) else v
    return {
        "dtmf_map": j("DTMF_MAP", "{}"),
        "token_map": j("TOKEN_MAP", "[]"),
        "digit_keyword_patterns": j("DIGIT_KEYWORD_PATTERNS", "[]"),
        "compound_patterns": j("COMPOUND_PATTERNS", "[]"),
        "keyword_patterns": j("KEYWORD_PATTERNS", "[]"),
    }


def _tp(dtmf="{}", token="[]", digitkw="[]", compound="[]", keyword="[]") -> dict:
    return {"DTMF_MAP": dtmf, "TOKEN_MAP": token, "DIGIT_KEYWORD_PATTERNS": digitkw,
            "COMPOUND_PATTERNS": compound, "KEYWORD_PATTERNS": keyword}


def test_voice_forms_numeric():
    """③: 数字選択に音声表記が付き、enrich 後 classify が「2番/にばん/二番/二」→ラベルになる。"""
    tp = _tp(dtmf='{"1":"入院","2":"外来","3":"新規"}',
             keyword='[{"regex":"入院","result":"入院"},{"regex":"外来|通院","result":"外来"},{"regex":"新規|初診","result":"新規"}]')
    ch = _enrich_nchoice_config(tp)
    check(any("③" in c for c in ch), "③: 変更が記録される")
    cfg = _cfg(tp)
    for inp, exp in [("2番", "外来"), ("にばん", "外来"), ("二番", "外来"), ("二", "外来"),
                     ("2", "外来"), ("3番", "新規"), ("外来", "外来")]:
        check(nchoice_oracle.classify(inp, cfg) == exp, f"③ classify({inp})=={exp}")


def test_possession_ari_nashi():
    """①: 有無ラベルに所持表現が付き、持ってます→あり / 持ってません→なし（極性反転なし）。"""
    tp = _tp(dtmf='{"1":"あり","2":"なし"}',
             keyword='[{"regex":"ある|あります","result":"あり"},{"regex":"ない|ありません","result":"なし"}]')
    ch = _enrich_nchoice_config(tp)
    check(any("①" in c for c in ch), "①: 変更が記録される")
    cfg = _cfg(tp)
    for inp, exp in [("持ってます", "あり"), ("もってます", "あり"),
                     ("持ってません", "なし"), ("もってません", "なし"),
                     ("あります", "あり"), ("ありません", "なし"),
                     ("1", "あり"), ("2", "なし")]:
        check(nchoice_oracle.classify(inp, cfg) == exp, f"① classify({inp})=={exp}")


def test_idempotent():
    """2 回目の enrich は何も足さない（冪等）。"""
    tp = _tp(dtmf='{"1":"あり","2":"なし"}',
             keyword='[{"regex":"ある","result":"あり"}]')
    first = _enrich_nchoice_config(tp)
    second = _enrich_nchoice_config(tp)
    check(len(first) >= 1, "冪等: 1回目は変更あり")
    check(second == [], f"冪等: 2回目は空（実際 {second}）")


def test_author_existing_voice_forms_respected():
    """author が既に N番 を TOKEN に持つ選択肢は ③ をスキップ（上書きしない）。"""
    tp = _tp(dtmf='{"1":"入院","2":"外来"}',
             token='[{"regex":"1番|一番","result":"入院"},{"regex":"2番|二番","result":"外来"}]')
    ch = _enrich_nchoice_config(tp)
    check(ch == [], f"author既存N番→③skip（実際 {ch}）")


def test_parse_failure_untouched():
    """JSON パース不能な値は安全側で一切触らない。"""
    tp = _tp(dtmf='{壊れた', keyword='[]')
    orig = dict(tp)
    ch = _enrich_nchoice_config(tp)
    check(ch == [], "parse失敗→変更なし")
    check(tp["DTMF_MAP"] == orig["DTMF_MAP"], "parse失敗→DTMF_MAP不変")


def test_non_polar_label_no_possession():
    """有無でないラベル（用件等）には所持表現を足さない（①非発火・③のみ）。"""
    tp = _tp(dtmf='{"1":"変更","2":"キャンセル"}',
             keyword='[{"regex":"変更","result":"変更"},{"regex":"キャンセル","result":"キャンセル"}]')
    ch = _enrich_nchoice_config(tp)
    check(not any("①" in c for c in ch), "①: 非有無ラベルでは発火しない")
    check(any("③" in c for c in ch), "③: 数字キーがあれば発火する")
    check("持って" not in tp["KEYWORD_PATTERNS"], "①: KEYWORDに所持表現が入らない")


def test_no_numeric_dtmf_no_voice_forms():
    """DTMF_MAP に数字キーが無ければ ③ は発火しない。"""
    tp = _tp(dtmf='{}',
             keyword='[{"regex":"はい","result":"はい"}]')
    ch = _enrich_nchoice_config(tp)
    check(not any("③" in c for c in ch), "③: 数字キー無しでは発火しない")
    check(tp["TOKEN_MAP"] == "[]", "③: TOKEN_MAP不変")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    test_voice_forms_numeric()
    test_possession_ari_nashi()
    test_idempotent()
    test_author_existing_voice_forms_respected()
    test_parse_failure_untouched()
    test_non_polar_label_no_possession()
    test_no_numeric_dtmf_no_voice_forms()
    if _FAILS:
        print(f"FAIL: {len(_FAILS)} 件")
        for f in _FAILS:
            print(f"  - {f}")
        return 1
    print("PASS: enrich_nchoice_config 全ケース OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
