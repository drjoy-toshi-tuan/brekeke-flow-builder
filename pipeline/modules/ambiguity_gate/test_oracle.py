# -*- coding: utf-8 -*-
"""ambiguity_gate 受入テスト — acceptance_test/cases.tsv（テストが正）を全件照合。

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


def load_cases():
    cases = []
    with io.open(CASES_TSV, "r", encoding="utf-8") as f:
        header = f.readline().rstrip("\r\n").split("\t")
        for lineno, line in enumerate(f, start=2):
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            row = dict(zip(header, line.split("\t")))
            row["_lineno"] = lineno
            cases.append(row)
    return cases


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cases = load_cases()
    fails = []
    for c in cases:
        got = classify(c["utterance"], c["group"])
        if got != c["expected"]:
            fails.append((c, got))
    print("ambiguity_gate oracle acceptance: %d/%d PASS"
          % (len(cases) - len(fails), len(cases)))
    if fails:
        print("\nFAIL %d 件:" % len(fails))
        for c, got in fails:
            print("  %s (L%d) [%s]: %r -> got=%s expected=%s [%s]"
                  % (c["id"], c["_lineno"], c["group"], c["utterance"], got,
                     c["expected"], c.get("note", "")))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
