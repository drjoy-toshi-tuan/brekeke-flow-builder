#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_branch_cases.py — hospital_config の branches 定義から P7 連結テストケース JSON を生成する。

特徴:
  - branches: フロー分岐網羅のための最小ケース集合（人間が branch_spec に定義）
  - inject_pools: 患者情報など「毎回変えたい」フィールドのローテーションプール
    → ケース index に応じて自動でずらす (i % len(pool))
  - defaults: BIVR上で常に同じでよいフィールドの既定値（復唱 / はい など）
  - inject_pools にあるフィールドは、branch["inject"] に明示されていない限り pool から自動付与

Usage:
  python3 connection_test/gen_branch_cases.py \
      --config connection_test/hospital_configs/東京都立豊島_診療.json \
      --out    connection_test/cases/東京都立豊島_診療_テスト.json
"""

import argparse
import json
import sys
from pathlib import Path


def rotate(pool: list, idx: int) -> list:
    """pool[idx % len(pool)] を 1 要素リストで返す。pool 空ならそのまま空リスト。"""
    if not pool:
        return []
    return [pool[idx % len(pool)]]


def build_cases(cfg: dict) -> list:
    branches     = cfg.get("branches", [])
    inject_pools = cfg.get("inject_pools", {})

    cases = []
    for i, branch in enumerate(branches):
        inject = {}

        # 1. branch 固有の inject 値（最優先）
        for k, v in branch.get("inject", {}).items():
            inject[k] = v if isinstance(v, list) else [v]

        # 2. inject_pools からローテーション付与（branch が上書きしていないフィールドのみ）
        for pool_key, pool_vals in inject_pools.items():
            if pool_key not in inject:
                rotated = rotate(pool_vals, i)
                if rotated:
                    inject[pool_key] = rotated

        case_id = str(branch.get("id", i + 1))
        case = {
            "id":    case_id,
            "dtmf":  str(branch.get("dtmf", case_id)),  # stub_stt_connection.py requires dtmf
            "label": branch.get("label", f"case-{i+1}"),
        }
        if branch.get("_note"):
            case["_note"] = branch["_note"]
        case["inject"] = inject
        case["expect"] = branch.get("expect", {"終端": "ログ観察", "checkpoints": []})
        if branch.get("備考"):
            case["備考"] = branch["備考"]
        cases.append(case)

    return cases


def main() -> int:
    ap = argparse.ArgumentParser(description="branch spec → cases JSON")
    ap.add_argument("--config", required=True, help="hospital_configs/*.json (with branches)")
    ap.add_argument("--out",    required=True, help="output cases JSON path")
    args = ap.parse_args()

    config_path = Path(args.config)
    out_path    = Path(args.out)

    if not config_path.exists():
        print(f"[ERROR] config not found: {config_path}", file=sys.stderr)
        return 1

    cfg = json.loads(config_path.read_text(encoding="utf-8"))

    cases = build_cases(cfg)

    output = {
        "_about":   f"P7 連結テストケース — {cfg.get('facility','')} {cfg.get('flow','')} (branch-coverage)",
        "meta": {
            "facility":   cfg.get("facility", ""),
            "flow":       cfg.get("flow", ""),
            "entry_flow": cfg.get("entry_flow", ""),
            "version":    "3.0",
            "_generated_by": "gen_branch_cases.py",
        },
        "selector": cfg.get("selector", {}),
        "defaults": cfg.get("defaults", {}),
        "cases":    cases,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {len(cases)} cases → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
