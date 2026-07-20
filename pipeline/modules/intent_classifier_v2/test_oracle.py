#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""intent_classifier_v2 oracle 受入テスト — test_cases.json（JS parity と共有）を全件検証"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from oracle import classify  # noqa: E402


def main() -> None:
    data = json.loads((Path(__file__).parent / "test_cases.json").read_text(encoding="utf-8"))
    specs = data["specs"]
    fails = []
    for case in data["cases"]:
        got = classify(specs[case["spec"]], case["input"])
        exp = case["expect"]
        ok = True
        for k, v in exp.items():
            if k == "entities":
                for ek, ev in v.items():
                    if got["entities"].get(ek) != ev:
                        ok = False
            elif got.get(k) != v:
                ok = False
        status = "PASS" if ok else "FAIL"
        if not ok:
            fails.append((case, got))
        print(f"[{status}] {case['desc']}: 「{case['input']}」 → {got['intent']}"
              f" (conf={got['confidence']}, neg={got['negation']})")
    print()
    total = len(data["cases"])
    print(f"=== {total - len(fails)}/{total} PASS ===")
    if fails:
        for case, got in fails:
            print(f"\nFAIL: {case['desc']}")
            print(f"  期待: {json.dumps(case['expect'], ensure_ascii=False)}")
            print(f"  実際: {json.dumps(got, ensure_ascii=False)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
