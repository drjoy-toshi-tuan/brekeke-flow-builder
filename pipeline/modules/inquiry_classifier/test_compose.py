# -*- coding: utf-8 -*-
"""inquiry_classifier composer 生成 spec の受入テスト（factory-v2）。

part.json の specs のうち "composed_from" を持つ spec を対象に、compose_spec で
RULES を合成 → acceptance_test/<spec>/cases.tsv を分類 → 期待ラベルと突合。
また filled_script の engine_hash が認定 engine と一致することも検証する。

実行: python modules/inquiry_classifier/test_compose.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
import compose_spec as C  # noqa: E402
import orchestrator as O  # noqa: E402

PART = json.load(open(os.path.join(HERE, "part.json"), encoding="utf-8"))
REG = json.load(open(os.path.join(HERE, "..", "certified_hashes.json"), encoding="utf-8"))
ENGINE_HASH = REG["parts"]["inquiry_classifier"]["engine_hash"]


def load_cases(path):
    cases = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        p = line.split("\t")
        if len(p) == 2:
            cases.append((p[0], p[1]))
    return cases


def main():
    ok = True
    composed = {k: v for k, v in PART["specs"].items() if v.get("composed_from")}
    if not composed:
        print("composed_from を持つ spec がありません")
        return 1
    for name, spec in composed.items():
        rules = C.compose_rules(spec["composed_from"])
        cases = load_cases(os.path.join(HERE, spec["cases"]))
        passed, fails = 0, []
        for inp, exp in cases:
            got = C.oracle_classify(inp, rules)
            if got == exp:
                passed += 1
            else:
                fails.append((inp, exp, got))
        print(f"[{name}] oracle {passed}/{len(cases)} PASS")
        for inp, exp, got in fails:
            print(f"  FAIL: {inp!r} expected={exp!r} got={got!r}")
            ok = False
        # engine_hash 一致（filled_script が認定 engine を改竄していないか）
        filled = open(os.path.join(HERE, spec["filled_script"]), encoding="utf-8").read()
        eh, sh = O._engine_spec_hashes(filled, PART["wiring_vars"])
        eh_ok = eh == ENGINE_HASH
        sh_ok = sh == spec.get("spec_hash")
        print(f"  engine_hash 一致={eh_ok} / spec_hash 一致={sh_ok}")
        ok = ok and eh_ok and sh_ok
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    sys.exit(main())
