# -*- coding: utf-8 -*-
"""checkup_course_classifier 受入テスト — acceptance_test/cases.tsv（テストが正）を全件照合。

実行: python test_oracle.py
終了コード 0 = 全 PASS。FAIL があれば一覧を出して 1。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle import classify

CASES_TSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "acceptance_test", "cases.tsv")

# facility_offered サブセット（OFF_MENU）ケース。tsv では set を表現できないためインライン。
# (utterance, facility_offered_set, expected)
FACILITY_CASES = [
    ("脳ドック", {"人間ドック", "一般・定期健診"}, "レディース・専門ドック|OFF_MENU"),
]


def load_cases():
    cases = []
    with io.open(CASES_TSV, "r", encoding="utf-8") as f:
        header = f.readline().rstrip("\r\n").split("\t")
        for lineno, line in enumerate(f, start=2):
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            cols = line.split("\t")
            row = dict(zip(header, cols))
            row["_lineno"] = lineno
            cases.append(row)
    return cases


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cases = load_cases()
    fails = []
    for c in cases:
        got = classify(c["utterance"])
        if got != c["expected"]:
            fails.append((c, got))
    for utt, fac, exp in FACILITY_CASES:
        got = classify(utt, facility_offered=fac)
        if got != exp:
            fails.append(({"id": "FAC", "utterance": utt, "expected": exp,
                           "_lineno": 0, "note": "facility_offered/OFF_MENU"}, got))
    total = len(cases) + len(FACILITY_CASES)
    print("checkup_course_classifier oracle acceptance: %d/%d PASS"
          % (total - len(fails), total))
    if fails:
        print("\nFAIL %d 件:" % len(fails))
        for c, got in fails:
            print("  %s (L%d): %r -> got=%s expected=%s [%s]"
                  % (c["id"], c["_lineno"], c["utterance"], got,
                     c["expected"], c.get("note", "")))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
