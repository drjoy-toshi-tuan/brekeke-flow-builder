# -*- coding: utf-8 -*-
"""checkup_intent_classifier 受入テスト — acceptance_test/ の TSV（テストが正）を全件照合。

  cases.tsv          : 用件確認文脈（SCOPE=full・既存）
  cases_lateness.tsv : 遅刻種別確認文脈（SCOPE=lateness・出口を{遅刻,変更,キャンセル}に絞る）

実行: python test_oracle.py
終了コード 0 = 全 PASS。FAIL があれば一覧を出して 1。
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle import classify

HERE = os.path.dirname(os.path.abspath(__file__))
SUITES = [
    ("full", os.path.join(HERE, "acceptance_test", "cases.tsv")),
    ("lateness", os.path.join(HERE, "acceptance_test", "cases_lateness.tsv")),
]


def load_cases(path):
    cases = []
    with io.open(path, "r", encoding="utf-8") as f:
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
    total = 0
    all_fails = []
    for scope, path in SUITES:
        if not os.path.exists(path):
            continue
        cases = load_cases(path)
        total += len(cases)
        fails = [(scope, c, classify(c["utterance"], scope)) for c in cases
                 if classify(c["utterance"], scope) != c["expected"]]
        all_fails += fails
        print("checkup_intent_classifier oracle acceptance [%s]: %d/%d PASS"
              % (scope, len(cases) - len(fails), len(cases)))
    if all_fails:
        print("\nFAIL %d 件:" % len(all_fails))
        for scope, c, got in all_fails:
            print("  [%s] %s (L%d): %r -> got=%s expected=%s [%s]"
                  % (scope, c["id"], c["_lineno"], c["utterance"], got,
                     c["expected"], c.get("note", "")))
        return 1
    print("合計 %d/%d PASS" % (total, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
