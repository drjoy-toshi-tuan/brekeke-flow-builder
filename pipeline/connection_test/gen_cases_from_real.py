#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_cases_from_real.py — real_cases.csv → cases/*.json

Usage:
  python3 connection_test/gen_cases_from_real.py \
      --csv connection_test/real_cases/福岡大学_診療_template.csv \
      --base connection_test/cases/福岡大学_診療_0708.json \
      --out  connection_test/cases/福岡大学_診療_real.json

CSV column conventions:
  case_id        — unique id (R01, R02, …)
  case_name      — human-readable label
  入力_XXX       — inject value; use "|" to specify multiple (retry list)
  期待_終端      — expected terminal module name (substring match in checkpoint trace)
  期待_checkpoints — semicolon-separated checkpoint names (all must appear in trace)
"""

import argparse
import csv
import json
import sys
import zipfile
from pathlib import Path


def bivr_input_nodes(bivr_path: Path) -> set[str]:
    """bivr 内の STT / DTMF / incoming-classifier ノード名（= inject 可能なノード）を返す。"""
    nodes: set[str] = set()
    with zipfile.ZipFile(bivr_path) as z:
        for name in z.namelist():
            d = json.loads(z.read(name).decode("utf-8"))
            for mn, m in d.get("modules", {}).items():
                t = m.get("type", "")
                if "AmiVoice" in t or "incoming-classifier" in t:
                    nodes.add(mn)
    return nodes


def parse_inject_value(raw: str) -> list[str]:
    """'A|B|C' → ['A','B','C']; single value → [value]; empty → skip."""
    raw = raw.strip()
    if not raw:
        return []
    return [v.strip() for v in raw.split("|") if v.strip()]


def parse_checkpoints(raw: str | None) -> list[str]:
    """'cp1;cp2;cp3' → ['cp1','cp2','cp3']"""
    if not raw:
        return []
    raw = raw.strip()
    if not raw:
        return []
    return [c.strip() for c in raw.split(";") if c.strip()]


def csv_row_to_case(row: dict, base_meta: dict) -> dict:
    case_id   = row.get("case_id", "").strip()
    case_name = row.get("case_name", "").strip()
    terminal  = row.get("期待_終端", "").strip()
    cps       = parse_checkpoints(row.get("期待_checkpoints", ""))

    inject: dict[str, list[str]] = {}
    for key, val in row.items():
        if key.startswith("入力_") and val.strip():
            inject[key] = parse_inject_value(val)

    return {
        "id":    case_id,
        "label": case_name,
        "_source": "real_cases_csv",
        "inject": inject,
        "expect": {
            "終端":       terminal or "ログ観察",
            "checkpoints": cps,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="real_cases.csv → cases JSON")
    ap.add_argument("--csv",  required=True, help="real_cases CSV file")
    ap.add_argument("--base", required=False, help="existing cases JSON (for meta/selector/defaults)")
    ap.add_argument("--out",  required=True, help="output cases JSON path")
    ap.add_argument("--facility", default="", help="facility name (if no --base)")
    ap.add_argument("--flow",     default="", help="flow name (if no --base)")
    ap.add_argument("--bivr",     default="",
                    help="対象 bivr。指定すると CSV の 入力_ 列名が bivr のノード名に実在するか検証し、"
                         "未一致があれば fail-fast（黙って defaults 化する事故の予防）")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    out_path = Path(args.out)

    if not csv_path.exists():
        print(f"[ERROR] CSV not found: {csv_path}", file=sys.stderr)
        return 1

    # Load base JSON for meta / selector / defaults
    base_meta: dict = {}
    base_selector: dict = {}
    base_defaults: dict = {}
    if args.base and Path(args.base).exists():
        base = json.loads(Path(args.base).read_text(encoding="utf-8"))
        base_meta     = base.get("meta", {})
        base_selector = base.get("selector", {})
        base_defaults = base.get("defaults", {})
    else:
        base_meta = {
            "facility":    args.facility,
            "flow":        args.flow,
            "entry_flow":  "",
        }

    # Parse CSV
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    cases = []
    for row in rows:
        if not row.get("case_id", "").strip():
            continue  # skip blank rows
        cases.append(csv_row_to_case(row, base_meta))

    # --bivr: inject キー（= CSV の 入力_ 列名）が bivr のノード名に実在するか検証
    if args.bivr:
        bivr_path = Path(args.bivr)
        if not bivr_path.exists():
            print(f"[ERROR] bivr not found: {bivr_path}", file=sys.stderr)
            return 1
        nodes = bivr_input_nodes(bivr_path)
        unmatched = sorted({k for c in cases for k in c["inject"] if k not in nodes})
        if unmatched:
            print(f"[ERROR] {len(unmatched)} 個の 入力_ 列名が bivr のノード名に一致しません"
                  f"（このまま生成すると該当値は黙って捨てられ defaults 動作になります）:",
                  file=sys.stderr)
            for k in unmatched:
                print(f"   {k}", file=sys.stderr)
            print(f"   bivr 側の候補ノード: {sorted(nodes)}", file=sys.stderr)
            return 1
        print(f"[OK] inject キー検証: 全列名が bivr ノードに一致 ({bivr_path.name})")

    output = {
        "_about": f"real-cases generated from {csv_path.name}",
        "meta":     base_meta,
        "selector": base_selector,
        "defaults": base_defaults,
        "cases":    cases,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {len(cases)} cases → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
