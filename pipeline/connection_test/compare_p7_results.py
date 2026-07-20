#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compare_p7_results.py — Brekeke log CSV × cases JSON → pass/fail report

Usage:
  python3 connection_test/compare_p7_results.py \
      --log  path/to/brekeke_log.csv \
      --cases connection_test/cases/福岡大学_診療_0708.json \
      [--col-trace 6]          # 0-based column index of checkpoint trace (default: auto-detect)
      [--col-case  0]          # column index of case selector value (default: auto-detect)
      [--out report.md]        # output report path (default: stdout)

Checkpoint trace format (Brekeke "col7"):
  key:value;key:value;...
  e.g. __テストセレクタ:10;用件_分岐:1;jump-変更.変更_予約日:OK;通話完了:OK;

Pass criteria:
  1. 期待_終端  — terminal checkpoint name appears in trace (substring)
  2. 期待_checkpoints — all listed names appear somewhere in the trace keys
"""

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ── Trace parsing ─────────────────────────────────────────────────────────────

def parse_trace(trace_str: str) -> dict[str, str]:
    """Parse 'k1:v1;k2:v2;' → {'k1':'v1', 'k2':'v2', ...}"""
    result: dict[str, str] = {}
    for segment in trace_str.split(";"):
        segment = segment.strip()
        if not segment:
            continue
        idx = segment.find(":")
        if idx < 0:
            result[segment] = ""
        else:
            result[segment[:idx]] = segment[idx + 1:]
    return result


def extract_case_id_from_trace(trace: dict[str, str]) -> str | None:
    """__テストセレクタ or __保存tc → case id string"""
    for key in ("__テストセレクタ", "__保存tc"):
        if key in trace:
            return trace[key].strip()
    return None


# ── Check logic ───────────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    case_id:    str
    case_label: str
    status:     str          # PASS / FAIL / SKIP / NO_LOG
    terminal:   str = ""
    terminal_ok: bool = False
    missing_cps: list[str] = field(default_factory=list)
    trace_keys:  list[str] = field(default_factory=list)
    raw_trace:   str = ""

    @property
    def ok(self) -> bool:
        return self.status == "PASS"


def check_case(case: dict, trace: dict[str, str]) -> CheckResult:
    case_id    = str(case.get("id", "?"))
    case_label = case.get("label", "")
    expect     = case.get("expect", {})
    terminal   = expect.get("終端", "").strip()
    checkpoints = expect.get("checkpoints", [])

    trace_keys_flat = list(trace.keys())

    # terminal check: any key starts with or contains the terminal string
    terminal_ok = False
    if terminal and terminal not in ("ログ観察", ""):
        terminal_ok = any(terminal in k for k in trace_keys_flat)
    else:
        # "ログ観察" = no automated terminal check; treat as soft pass
        terminal_ok = True

    # checkpoint check: all checkpoints must appear in trace keys
    missing: list[str] = []
    for cp in checkpoints:
        # exact match or prefix match (e.g. "終話_変更" matches "終話_変更:OK")
        found = any(k == cp or k.startswith(cp) for k in trace_keys_flat)
        if not found:
            missing.append(cp)

    if not terminal_ok:
        status = "FAIL"
    elif missing:
        status = "FAIL"
    else:
        status = "PASS"

    return CheckResult(
        case_id=case_id,
        case_label=case_label,
        status=status,
        terminal=terminal,
        terminal_ok=terminal_ok,
        missing_cps=missing,
        trace_keys=trace_keys_flat,
    )


# ── Log CSV loading ────────────────────────────────────────────────────────────

def auto_detect_trace_col(header: list[str]) -> int:
    """Detect which column is the checkpoint trace (contains ';' separated key:value pairs)."""
    # common Brekeke log column names
    candidates = ["checkpoint", "trace", "col7", "メモ", "備考", "ログ"]
    for i, h in enumerate(header):
        if any(c in h.lower() for c in candidates):
            return i
    return -1  # caller falls back to scanning rows


def auto_detect_case_col(header: list[str]) -> int:
    """Detect column used to match __テストセレクタ value."""
    for i, h in enumerate(header):
        if "セレクタ" in h or "selector" in h.lower() or "case" in h.lower():
            return i
    return -1


def load_log_rows(log_path: Path, col_trace: int, col_case: int) -> list[dict]:
    """Load Brekeke log CSV and extract (case_id, trace_dict) per row."""
    rows = []
    with log_path.open(encoding="utf-8-sig", newline="", errors="replace") as f:
        reader = csv.reader(f)
        header = None
        for raw_row in reader:
            if header is None:
                header = raw_row
                # auto-detect if not given
                if col_trace < 0:
                    col_trace = auto_detect_trace_col(header)
                if col_case < 0:
                    col_case = auto_detect_case_col(header)
                continue

            if len(raw_row) <= max(col_trace, 0):
                continue

            trace_str = raw_row[col_trace] if col_trace >= 0 else ""
            # also try all columns if trace col unknown
            if col_trace < 0:
                trace_str = next(
                    (c for c in raw_row if "__テストセレクタ" in c or "冒頭" in c),
                    ""
                )

            trace = parse_trace(trace_str)
            case_id_from_log = extract_case_id_from_trace(trace)

            # fallback: use explicit case column
            if not case_id_from_log and col_case >= 0 and len(raw_row) > col_case:
                case_id_from_log = raw_row[col_case].strip()

            rows.append({
                "case_id": case_id_from_log,
                "trace":   trace,
                "raw":     trace_str,
            })
    return rows


# ── Report rendering ──────────────────────────────────────────────────────────

def render_report(results: list[CheckResult], facility: str, flow: str) -> str:
    total  = len(results)
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    nolog  = sum(1 for r in results if r.status == "NO_LOG")

    lines = [
        f"# P7 連結テスト 結果レポート — {facility} {flow}",
        "",
        f"| 項目 | 件数 |",
        f"|------|------|",
        f"| 総ケース | {total} |",
        f"| PASS | {passed} |",
        f"| FAIL | {failed} |",
        f"| ログ未照合 | {nolog} |",
        "",
        "---",
        "",
    ]

    for r in results:
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "NO_LOG": "❓"}.get(r.status, "?")
        lines.append(f"## {icon} [{r.case_id}] {r.case_label}  →  **{r.status}**")
        if r.status == "NO_LOG":
            lines.append("- ログに対応するトレースが見つかりませんでした")
        else:
            terminal_mark = "✅" if r.terminal_ok else "❌"
            lines.append(f"- 期待終端 `{r.terminal or '(なし)'}` : {terminal_mark}")
            if r.missing_cps:
                lines.append(f"- 不足チェックポイント: `{'`, `'.join(r.missing_cps)}`")
            else:
                lines.append("- チェックポイント: すべて確認")
        lines.append("")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="Brekeke log CSV × cases JSON → pass/fail report")
    ap.add_argument("--log",       required=True,  help="Brekeke log CSV file")
    ap.add_argument("--cases",     required=True,  help="cases JSON file")
    ap.add_argument("--col-trace", type=int, default=-1,
                    help="0-based column index for checkpoint trace (default: auto-detect)")
    ap.add_argument("--col-case",  type=int, default=-1,
                    help="0-based column index for case id (default: auto-detect)")
    ap.add_argument("--out",       default="",     help="output .md report path (default: stdout)")
    args = ap.parse_args()

    log_path   = Path(args.log)
    cases_path = Path(args.cases)

    if not log_path.exists():
        print(f"[ERROR] log CSV not found: {log_path}", file=sys.stderr)
        return 1
    if not cases_path.exists():
        print(f"[ERROR] cases JSON not found: {cases_path}", file=sys.stderr)
        return 1

    cases_json  = json.loads(cases_path.read_text(encoding="utf-8"))
    facility    = cases_json.get("meta", {}).get("facility", "")
    flow        = cases_json.get("meta", {}).get("flow", "")
    cases       = cases_json.get("cases", [])

    log_rows = load_log_rows(log_path, args.col_trace, args.col_case)
    # build map: case_id → trace
    log_map: dict[str, dict] = {}
    for row in log_rows:
        cid = row["case_id"]
        if cid:
            log_map[cid] = row["trace"]

    results: list[CheckResult] = []
    for case in cases:
        case_id = str(case.get("id", ""))
        trace   = log_map.get(case_id)
        if trace is None:
            results.append(CheckResult(
                case_id=case_id,
                case_label=case.get("label", ""),
                status="NO_LOG",
            ))
        else:
            results.append(check_case(case, trace))

    report = render_report(results, facility, flow)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"[OK] report → {out_path}")
    else:
        print(report)

    failed = sum(1 for r in results if r.status == "FAIL")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
