# -*- coding: utf-8 -*-
"""dob_normalizer — オラクル単体テスト（acceptance_test/cases.tsv を実行）。

実行: python modules/dob_normalizer/test_oracle.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle  # noqa: E402

CASES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "acceptance_test", "cases.tsv")


def load_cases(path):
    cases = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        cases.append((parts[0], parts[1]))
    return cases


def main():
    cases = load_cases(CASES)
    passed, fails = 0, []
    for inp, expected in cases:
        got = oracle.classify(inp)
        if got == expected:
            passed += 1
        else:
            fails.append((inp, expected, got))
    print(f"[dob_normalizer oracle] {passed}/{len(cases)} PASS")
    for inp, expected, got in fails:
        print(f"  FAIL: input={inp!r} expected={expected!r} got={got!r}")
    return 0 if not fails else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    sys.exit(main())
