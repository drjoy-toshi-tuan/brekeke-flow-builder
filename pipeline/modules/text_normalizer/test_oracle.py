#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""text_normalizer のオラクル受入テスト。acceptance_test/<spec>/cases.tsv を読んで classify を検証する。

cases.tsv 形式: 1 行 1 ケース、`入力<TAB>期待ラベル`（# 始まりはコメント・空行は無視）。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from oracle import classify  # noqa: E402


def _iter_cases():
    for tsv in sorted(HERE.glob("acceptance_test/*/cases.tsv")):
        for lineno, line in enumerate(tsv.read_text(encoding="utf-8").splitlines(), 1):
            s = line.rstrip("\n")
            if not s.strip() or s.lstrip().startswith("#"):
                continue
            parts = s.split("\t")
            if len(parts) < 2:
                continue
            yield tsv, lineno, parts[0], parts[1]


def main() -> int:
    total = 0
    failed = 0
    for tsv, lineno, utt, expected in _iter_cases():
        total += 1
        got = classify(utt)
        if got != expected:
            failed += 1
            print(f"[FAIL] {tsv.parent.name}:{lineno} input={utt!r} expected={expected} got={got}")
    if total == 0:
        print("[WARN] ケースが 0 件です。acceptance_test/<spec>/cases.tsv を用意してください。")
        return 1
    print(f"{total - failed}/{total} PASS")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
