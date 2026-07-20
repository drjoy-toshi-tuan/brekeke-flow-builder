# -*- coding: utf-8 -*-
"""test_drawio_to_scenario.py — drawio_to_scenario パーサ + surfacing の golden オラクル。

fixtures（drawio_parser_fixtures/）に対する期待 surfacing を assert する。
新規パイプライン部品の DoD（オラクル + テスト）を満たす最小スイート。
  python test_drawio_to_scenario.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drawio_to_scenario import analyze  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "drawio_parser_fixtures")
MODULES = os.path.join(os.path.dirname(HERE), "modules")


def _codes(res, step=None):
    return [f["code"] for f in res["findings"]
            if step is None or f["step"] == step]


def _crit(res):
    return [f for f in res["findings"] if f["severity"] == "CRITICAL"]


def run():
    cases = []

    # 1) クリーン: yes_no が選定され surfacing は空（ハッピーパス）
    r = analyze(os.path.join(FIX, "yesno_clean.drawio"), MODULES)
    cases.append(("yesno_clean: CRITICAL 0", len(_crit(r)) == 0))
    cases.append(("yesno_clean: PART_SELECTED yes_no",
                  any(f["code"] == "PART_SELECTED" and "yes_no_classifier" in f["message"]
                      for f in r["findings"])))

    # 2) 壊れ: 否定 が未配線 → CRITICAL UNWIRED_LABEL ちょうど1件
    r = analyze(os.path.join(FIX, "yesno_broken.drawio"), MODULES)
    crit = _crit(r)
    cases.append(("yesno_broken: CRITICAL 1", len(crit) == 1))
    cases.append(("yesno_broken: UNWIRED_LABEL 否定",
                  len(crit) == 1 and crit[0]["code"] == "UNWIRED_LABEL"
                  and "否定" in crit[0]["message"] and crit[0]["step"] == "用件確認"))

    # 3) shinryo composer golden（現実・ロッシー）: 正確なギャップを surfacing
    r = analyze(os.path.join(FIX, "shinryo_composer_golden.drawio"), MODULES)
    # 用件確認: inquiry_classifier 外来予約FULL spec（composer 生成）が選定される（B-2）
    cases.append(("shinryo: 用件確認 PART_SELECTED inquiry_classifier:外来予約FULL",
                  any(f["code"] == "PART_SELECTED"
                      and "inquiry_classifier:外来予約FULL" in f["message"]
                      for f in r["findings"] if f["step"] == "用件確認")))
    cases.append(("shinryo: 用件確認 に NO_CERTIFIED/UNWIRED 残らない",
                  not ({"NO_CERTIFIED_PART", "UNWIRED_LABEL"} & set(_codes(r, "用件確認")))))
    cases.append(("shinryo: CMR_phonetype NO_CERTIFIED_PART",
                  "NO_CERTIFIED_PART" in _codes(r, "CMR_phonetype")))
    cases.append(("shinryo: UNLABELED_BRANCH 誤検知ゼロ（失敗エッジ分離）",
                  "UNLABELED_BRANCH" not in _codes(r)))
    cases.append(("shinryo: 氏名聴取 inline 選定",
                  "SLOT_INLINE" in _codes(r, "氏名聴取")))
    cases.append(("shinryo: LABEL_LEAK ゼロ（病院セーフティ）",
                  "LABEL_LEAK" not in _codes(r)))

    npass = sum(1 for _, ok in cases if ok)
    for name, ok in cases:
        print(("PASS " if ok else "FAIL ") + name)
    print("-" * 50)
    print(f"{npass}/{len(cases)} PASS")
    return npass == len(cases)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    sys.exit(0 if run() else 1)
