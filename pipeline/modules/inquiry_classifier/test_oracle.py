"""inquiry_classifier — オラクル単体テスト（acceptance_test/cases.tsv を実行）

実行: python3 modules/inquiry_classifier/test_oracle.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle  # noqa: E402

CASES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "acceptance_test", "亀田総合相談室", "cases.tsv")


def load_cases(path):
    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("#") or line == "":
                continue
            parts = line.split("\t")
            if len(parts) != 2:
                continue
            cases.append((parts[0], parts[1]))
    return cases


def main():
    cases = load_cases(CASES)
    passed = 0
    fails = []
    for inp, expected in cases:
        got = oracle.classify(inp)
        if got == expected:
            passed += 1
        else:
            fails.append((inp, expected, got))
    print(f"[inquiry_classifier oracle] {passed}/{len(cases)} PASS")
    for inp, expected, got in fails:
        print(f"  FAIL: input={inp!r} expected={expected!r} got={got!r}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
