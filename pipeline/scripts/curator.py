#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
curator.py -- run_history 集計ツール (Phase 1)

docs/run_history/*.json を読み、施設横断の集計を返す決定論的スクリプト。
LLM 不使用。Curator Agent (Phase 2) や Optimizer (将来) の signal source。

Usage:
    python3 scripts/curator.py summary        [--last N] [--facility X] [--pattern Y] [--json]
    python3 scripts/curator.py critical-codes [--last N] [--json]
    python3 scripts/curator.py step-times     [--last N] [--json]
    python3 scripts/curator.py outliers       [--last N] [--json]

Notes:
- 既定出力は markdown 表形式（人間が見やすい）
- `--json` で JSON 出力（後段 agent から消費しやすく）
- 副作用なし、read-only
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median, mean

PROJECT_DIR = Path(__file__).resolve().parent.parent
RUN_HISTORY_DIR = PROJECT_DIR / "docs" / "run_history"


def _load_runs(last: int = 0, facility: str = "", pattern: int = 0) -> list[dict]:
    """run_history JSON を新しい順に読み込む。filter は started_at で降順。"""
    if not RUN_HISTORY_DIR.is_dir():
        return []
    runs = []
    for f in RUN_HISTORY_DIR.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        if facility and facility not in (d.get("facility") or ""):
            continue
        if pattern and d.get("pattern") != pattern:
            continue
        d["__path"] = str(f.relative_to(PROJECT_DIR))
        runs.append(d)
    runs.sort(key=lambda r: r.get("started_at", ""), reverse=True)
    if last > 0:
        runs = runs[:last]
    return runs


def _fmt_sec(sec: float) -> str:
    if sec is None:
        return "-"
    sec = float(sec)
    m, s = divmod(int(sec), 60)
    return f"{m}:{s:02d}"


def _fmt_tokens(n: int) -> str:
    if n is None:
        return "-"
    n = int(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}k"
    return str(n)


# ---------------------------------------------------------------------------
# summary: 1 run = 1 行のオーバービュー
# ---------------------------------------------------------------------------

def cmd_summary(args) -> int:
    runs = _load_runs(args.last, args.facility, args.pattern)
    if args.json:
        out = []
        for r in runs:
            out.append({
                "facility": r.get("facility"),
                "flow": r.get("flow"),
                "pattern": r.get("pattern"),
                "started_at": r.get("started_at"),
                "duration_sec": r.get("duration_sec"),
                "completed": r.get("completed"),
                "unattended": r.get("unattended"),
                "critical_count": len(r.get("critical_codes_seen") or []),
                "tokens_total": r.get("tokens_total"),
                "path": r.get("__path"),
            })
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if not runs:
        print("(no runs found)")
        return 0
    print(f"# Run summary  ({len(runs)} run{'s' if len(runs)!=1 else ''})")
    print()
    print("| started_at | 施設 / flow | pat | duration | completed | crit | tokens(in/out/cache) |")
    print("|---|---|---|---|---|---|---|")
    for r in runs:
        tt = r.get("tokens_total") or {}
        crit = len(r.get("critical_codes_seen") or [])
        ts = (r.get("started_at") or "")[:16].replace("T", " ")
        print(
            f"| {ts} "
            f"| {r.get('facility','')} / {r.get('flow','')} "
            f"| {r.get('pattern','')} "
            f"| {_fmt_sec(r.get('duration_sec'))} "
            f"| {'✓' if r.get('completed') else '✗'} "
            f"| {crit} "
            f"| {_fmt_tokens(tt.get('input',0))}/{_fmt_tokens(tt.get('output',0))}"
            f"/{_fmt_tokens(tt.get('cache_read',0))} |"
        )
    return 0


# ---------------------------------------------------------------------------
# critical-codes: critical_codes_seen の頻度集計
# ---------------------------------------------------------------------------

def cmd_critical_codes(args) -> int:
    runs = _load_runs(args.last)
    code_counter: Counter = Counter()
    code_by_facility: dict[str, set] = defaultdict(set)
    facility_total: Counter = Counter()
    for r in runs:
        fac = f"{r.get('facility','')}/{r.get('flow','')}"
        facility_total[fac] += 1
        for code in r.get("critical_codes_seen") or []:
            code_counter[code] += 1
            code_by_facility[code].add(fac)

    if args.json:
        out = {
            "total_runs": len(runs),
            "codes": [
                {"code": c, "occurrences": n, "facility_count": len(code_by_facility[c]),
                 "facilities": sorted(code_by_facility[c])}
                for c, n in code_counter.most_common()
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    print(f"# Critical codes frequency  ({len(runs)} runs)")
    print()
    if not code_counter:
        print("(no critical codes recorded)")
        return 0
    print("| code | 出現数 | 施設数 | 例 |")
    print("|---|---|---|---|")
    for c, n in code_counter.most_common():
        facs = sorted(code_by_facility[c])
        sample = facs[0] + ("..." if len(facs) > 1 else "")
        print(f"| {c} | {n} | {len(facs)} | {sample} |")
    return 0


# ---------------------------------------------------------------------------
# step-times: step ごとの平均/p50/p95 と外れ値
# ---------------------------------------------------------------------------

def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] * (c - k) + s[c] * (k - f)


def cmd_step_times(args) -> int:
    runs = _load_runs(args.last)
    step_secs: dict[str, list[float]] = defaultdict(list)
    step_status: dict[str, Counter] = defaultdict(Counter)
    for r in runs:
        for step, summary in (r.get("step_summary") or {}).items():
            if not isinstance(summary, dict):
                continue
            sec = summary.get("seconds")
            if sec is not None:
                step_secs[step].append(float(sec))
            st = summary.get("status") or "unknown"
            step_status[step][st] += 1

    rows = []
    for step, secs in step_secs.items():
        if not secs:
            continue
        rows.append({
            "step": step,
            "n": len(secs),
            "mean_sec": round(mean(secs), 1),
            "median_sec": round(median(secs), 1),
            "p95_sec": round(_percentile(secs, 0.95), 1),
            "max_sec": round(max(secs), 1),
            "fail_count": step_status[step].get("fail", 0),
            "ok_count": step_status[step].get("ok", 0),
        })
    rows.sort(key=lambda x: -x["mean_sec"])

    if args.json:
        print(json.dumps({"total_runs": len(runs), "steps": rows}, ensure_ascii=False, indent=2))
        return 0

    print(f"# Step time stats  ({len(runs)} runs)")
    print()
    if not rows:
        print("(no step data)")
        return 0
    print("| step | n | mean | p50 | p95 | max | fail/ok |")
    print("|---|---|---|---|---|---|---|")
    for x in rows:
        print(
            f"| {x['step']} | {x['n']} | {_fmt_sec(x['mean_sec'])} "
            f"| {_fmt_sec(x['median_sec'])} | {_fmt_sec(x['p95_sec'])} "
            f"| {_fmt_sec(x['max_sec'])} | {x['fail_count']}/{x['ok_count']} |"
        )
    return 0


# ---------------------------------------------------------------------------
# outliers: 異常検出
# ---------------------------------------------------------------------------

# しきい値（経験則、必要に応じて調整）
PROMPTER_TOO_FAST_SEC = 30   # OpenAI モジュール ≥1 件で 30 秒未満は要調査
FIXER_TOO_LONG_SEC = 1500    # fixer 25 分超
TESTER_FAIL_FLAG = "fail"

# 上流系 Critical コード — director / scaffold / layout の出力品質劣化シグナル
# fixer に頼らず上流（director プロンプト・agent 定義・scaffold ロジック）で
# 解決すべき種類。fixer 後でも残っていれば「director 改修案件」として浮上させる。
UPSTREAM_CODES = {
    "N-001",       # モジュール命名違反（環境依存文字、丸数字 ① 等）
    "CMR-001",     # ContextMatchRouter.reference_module 不正値
    "CMR-007",     # ContextMatchRouter ^0$ other 分岐の next 未指定
    "T-001",       # 遷移先未定義
    "REACH-001",   # 到達不能モジュール
    "PROMPT-005",  # CMR 周辺 prompt 不整合
    "LAYOUT-003",  # 座標重複系
    "LAYOUT-004",  # 座標重複系
}


def cmd_outliers(args) -> int:
    runs = _load_runs(args.last)
    findings = []
    for r in runs:
        ss = r.get("step_summary") or {}
        fac = f"{r.get('facility','')}/{r.get('flow','')}"
        ts = (r.get("started_at") or "")[:16].replace("T", " ")

        # 1. completed=False
        if not r.get("completed"):
            findings.append({"facility": fac, "started_at": ts,
                             "kind": "incomplete", "detail": "completed=False で push に到達せず"})

        # 2. prompter_props 異常短（OpenAI モジュールの input トークン > 0 を期待）
        pp = ss.get("prompter_props") or {}
        sec = pp.get("seconds")
        tok = (pp.get("tokens") or {}).get("cache_read", 0) + (pp.get("tokens") or {}).get("input", 0)
        if sec is not None and sec < PROMPTER_TOO_FAST_SEC and tok < 100:
            findings.append({"facility": fac, "started_at": ts,
                             "kind": "prompter_too_fast",
                             "detail": f"prompter_props={sec}s tokens={tok} (LLM 呼び出し失敗 or OpenAI 0 件)"})

        # 3. fixer 異常長
        fx = ss.get("fixer") or {}
        if (fx.get("seconds") or 0) > FIXER_TOO_LONG_SEC:
            findings.append({"facility": fac, "started_at": ts,
                             "kind": "fixer_too_long",
                             "detail": f"fixer={fx.get('seconds')}s (>{FIXER_TOO_LONG_SEC}s 超)"})

        # 4. tester fail
        ts_step = ss.get("tester") or {}
        if ts_step.get("status") == TESTER_FAIL_FLAG:
            findings.append({"facility": fac, "started_at": ts,
                             "kind": "tester_fail", "detail": "tester step failed"})

        # 5. critical_codes 多発
        crit = r.get("critical_codes_seen") or []
        if len(crit) >= 10:
            findings.append({"facility": fac, "started_at": ts,
                             "kind": "many_criticals",
                             "detail": f"critical_codes={len(crit)} 件"})

        # 6. 上流系 Critical 残存 — fixer 後にも残ったら director / scaffold / layout 改修案件
        upstream_residual = sorted(set(c for c in crit if c in UPSTREAM_CODES))
        if upstream_residual:
            findings.append({"facility": fac, "started_at": ts,
                             "kind": "upstream_residual",
                             "detail": f"上流系 Critical 残存: {','.join(upstream_residual)} "
                                       f"(fixer 後でも残存 = director/scaffold/layout の改修候補)"})

    if args.json:
        print(json.dumps({"total_runs": len(runs), "findings": findings},
                         ensure_ascii=False, indent=2))
        return 0

    print(f"# Outliers  ({len(runs)} runs scanned)")
    print()
    if not findings:
        print("(no outliers detected)")
        return 0
    print("| started_at | facility | kind | detail |")
    print("|---|---|---|---|")
    for f in findings:
        print(f"| {f['started_at']} | {f['facility']} | {f['kind']} | {f['detail']} |")
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="run_history 集計ツール (Curator Phase 1)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("summary", help="run summary 一覧")
    s1.add_argument("--last", type=int, default=0, help="直近 N 件のみ")
    s1.add_argument("--facility", type=str, default="", help="施設名フィルタ (部分一致)")
    s1.add_argument("--pattern", type=int, default=0, help="pattern フィルタ (1-4)")
    s1.add_argument("--json", action="store_true")
    s1.set_defaults(func=cmd_summary)

    s2 = sub.add_parser("critical-codes", help="critical_codes_seen 頻度集計")
    s2.add_argument("--last", type=int, default=0)
    s2.add_argument("--json", action="store_true")
    s2.set_defaults(func=cmd_critical_codes)

    s3 = sub.add_parser("step-times", help="step ごとの所要時間統計")
    s3.add_argument("--last", type=int, default=0)
    s3.add_argument("--json", action="store_true")
    s3.set_defaults(func=cmd_step_times)

    s4 = sub.add_parser("outliers", help="異常検出 (prompter短・fixer長・tester失敗 等)")
    s4.add_argument("--last", type=int, default=0)
    s4.add_argument("--json", action="store_true")
    s4.set_defaults(func=cmd_outliers)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
