#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compare_golden.py — golden/*.txt トレース × cases JSON → pass/fail

golden/*.txt フォーマット:
  # --- checkpoint trace (col7) ---
  key:value;key:value;...

Usage:
  python3 connection_test/compare_golden.py \
      --golden connection_test/golden/福岡大学病院_診療 \
      --cases  connection_test/cases/福岡大学_診療_0708.json \
      [--out   report_golden.md]

ファイル名から case_id を取得: case10_変更.txt → "10"
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# reuse parse / check from compare_p7_results
def parse_trace(trace_str: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for seg in trace_str.split(";"):
        seg = seg.strip()
        if not seg:
            continue
        idx = seg.find(":")
        result[seg[:idx] if idx >= 0 else seg] = (seg[idx + 1:] if idx >= 0 else "")
    return result


@dataclass
class CheckResult:
    case_id:    str
    case_label: str
    status:     str
    terminal:   str = ""
    terminal_ok: bool = False
    missing_cps: list[str] = field(default_factory=list)


def check_case(case: dict, trace: dict[str, str]) -> CheckResult:
    case_id    = str(case.get("id", "?"))
    case_label = case.get("label", "")
    expect     = case.get("expect", {})
    terminal   = expect.get("終端", "").strip()
    checkpoints = expect.get("checkpoints", [])

    trace_keys = list(trace.keys())

    terminal_ok = True
    if terminal and terminal not in ("ログ観察", ""):
        terminal_ok = any(terminal in k for k in trace_keys)

    missing = [cp for cp in checkpoints
               if not any(k == cp or k.startswith(cp) for k in trace_keys)]

    status = "PASS" if (terminal_ok and not missing) else "FAIL"
    return CheckResult(case_id, case_label, status, terminal, terminal_ok, missing)


def load_golden_traces(golden_dir: Path) -> dict[str, dict[str, str]]:
    """case_id → trace_dict"""
    result: dict[str, dict[str, str]] = {}
    for f in sorted(golden_dir.glob("case*.txt")):
        m = re.match(r"case(\d+)", f.stem)
        if not m:
            continue
        case_id = m.group(1)
        text = f.read_text(encoding="utf-8")
        # find the line after "# --- checkpoint trace"
        in_trace = False
        for line in text.splitlines():
            if "checkpoint trace" in line:
                in_trace = True
                continue
            if in_trace and line.strip() and not line.startswith("#"):
                result[case_id] = parse_trace(line.strip())
                break
    return result


def render_report(results: list[CheckResult], facility: str, flow: str) -> str:
    total  = len(results)
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    nolog  = sum(1 for r in results if r.status == "NO_LOG")

    lines = [
        f"# Golden比較レポート — {facility} {flow}",
        "",
        f"| 項目 | 件数 |",
        f"|------|------|",
        f"| 総ケース | {total} |",
        f"| PASS | {passed} |",
        f"| FAIL | {failed} |",
        f"| ゴールデン未照合 | {nolog} |",
        "",
        "---",
        "",
    ]
    for r in results:
        icon = {"PASS": "✅", "FAIL": "❌", "NO_LOG": "❓"}.get(r.status, "?")
        lines.append(f"## {icon} [{r.case_id}] {r.case_label}  →  **{r.status}**")
        if r.status == "NO_LOG":
            lines.append("- golden ファイルが見つかりません")
        else:
            lines.append(f"- 期待終端 `{r.terminal or '(なし)'}` : {'✅' if r.terminal_ok else '❌'}")
            if r.missing_cps:
                lines.append(f"- 不足チェックポイント: `{'`, `'.join(r.missing_cps)}`")
            else:
                lines.append("- チェックポイント: すべて確認")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", required=True)
    ap.add_argument("--cases",  required=True)
    ap.add_argument("--out",    default="")
    args = ap.parse_args()

    golden_dir = Path(args.golden)
    cases_path = Path(args.cases)

    if not golden_dir.is_dir():
        print(f"[ERROR] golden dir not found: {golden_dir}", file=sys.stderr)
        return 1
    if not cases_path.exists():
        print(f"[ERROR] cases JSON not found: {cases_path}", file=sys.stderr)
        return 1

    cases_json = json.loads(cases_path.read_text(encoding="utf-8"))
    facility   = cases_json.get("meta", {}).get("facility", "")
    flow       = cases_json.get("meta", {}).get("flow", "")
    cases      = cases_json.get("cases", [])

    golden_map = load_golden_traces(golden_dir)

    results = []
    for case in cases:
        cid   = str(case.get("id", ""))
        trace = golden_map.get(cid)
        if trace is None:
            results.append(CheckResult(cid, case.get("label", ""), "NO_LOG"))
        else:
            results.append(check_case(case, trace))

    report = render_report(results, facility, flow)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"[OK] golden report → {out_path}")
    else:
        print(report)

    return 1 if any(r.status == "FAIL" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
