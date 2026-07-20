#!/usr/bin/env python3
"""
IVR ログ分析レポートツール
使い方:
  python tools/ivr_log_report.py --csv <path/to/log.csv> --facility 東京都立豊島 \
      --out output/scenarios/東京都立豊島病院_診療/ivr_log_report_YYYYMMDD.md
"""
import argparse
import csv
import os
import re
import sys
from collections import defaultdict, Counter
from datetime import datetime


# ---- CSV パース ----

def parse_trace(trace_str):
    """col7 トレース文字列を {key: value} dict に変換"""
    result = {}
    if not trace_str:
        return result
    for item in trace_str.split(";"):
        item = item.strip()
        if not item:
            continue
        idx = item.find(":")
        if idx < 0:
            result[item] = ""
        else:
            result[item[:idx].strip()] = item[idx+1:].strip()
    return result


def load_csv(path, facility_filter=None):
    """CSV を読み込みコールリストを返す"""
    calls = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 8:
                continue
            call_id   = row[0].strip()
            caller    = row[2].strip() if len(row) > 2 else ""
            flow_name = row[4].strip() if len(row) > 4 else ""
            dt_str    = row[5].strip() if len(row) > 5 else ""
            duration  = row[6].strip() if len(row) > 6 else "0"
            trace_raw = row[7].strip() if len(row) > 7 else ""

            if facility_filter and facility_filter not in flow_name:
                continue

            try:
                dur_sec = int(float(duration))
            except ValueError:
                dur_sec = 0

            trace = parse_trace(trace_raw)
            calls.append({
                "id": call_id,
                "caller": caller,
                "flow": flow_name,
                "datetime": dt_str,
                "duration": dur_sec,
                "trace": trace,
                "trace_raw": trace_raw,
            })
    return calls


# ---- 分析 ----

def analyze(calls):
    stats = {
        "total": len(calls),
        "durations": [],
        "flows": Counter(),
        "youken": Counter(),
        "scripts_youken": Counter(),
        "faq_result": Counter(),
        "faq_answer_texts": [],
        "terminals": Counter(),
        "openai_fallback": 0,
        "anomalies": [],
    }

    for c in calls:
        trace = c["trace"]
        dur = c["duration"]
        stats["durations"].append(dur)
        stats["flows"][c["flow"]] += 1

        # 用件
        youken = trace.get("用件", "")
        if youken:
            stats["youken"][youken] += 1

        # Scripts_用件 判定結果
        sc_result = trace.get("Scripts_用件_result", "")
        if sc_result:
            stats["scripts_youken"][sc_result] += 1

        # FAQ マッチ
        for key, val in trace.items():
            if key.startswith("Scripts-FAQ") and key.endswith("_result"):
                stats["faq_result"][val] += 1
            if key == "scripts-faq" and val:
                stats["faq_answer_texts"].append(val[:80])

        # OpenAI フォールバック発動確認
        if any(k.startswith("OpenAI_入力_用件") for k in trace):
            stats["openai_fallback"] += 1

        # 終端（最後の終話モジュール）
        terminal_keys = [k for k in trace if re.search(r'終話|切断|reject|Reject', k)]
        if terminal_keys:
            stats["terminals"][terminal_keys[-1]] += 1
        else:
            stats["terminals"]["(不明)"] += 1

        # 異常検出: 通話時間 10 秒未満 / TIMEOUT 多発 / 終端未到達
        timeout_count = sum(1 for k in trace if "TIMEOUT" in trace[k])
        if dur < 10:
            stats["anomalies"].append({"id": c["id"], "reason": f"通話時間 {dur}秒 (短すぎ)", "flow": c["flow"]})
        elif timeout_count >= 3:
            stats["anomalies"].append({"id": c["id"], "reason": f"TIMEOUT {timeout_count}回", "flow": c["flow"]})
        elif not terminal_keys:
            stats["anomalies"].append({"id": c["id"], "reason": "終端モジュール未検出", "flow": c["flow"]})

    return stats


# ---- レポート生成 ----

def render_report(stats, csv_path, facility):
    total = stats["total"]
    durs = stats["durations"]
    avg_dur = int(sum(durs) / len(durs)) if durs else 0
    max_dur = max(durs) if durs else 0
    min_dur = min(durs) if durs else 0

    lines = []
    lines.append(f"# IVR ログ分析レポート — {facility}")
    lines.append(f"\n- **対象ファイル**: `{os.path.basename(csv_path)}`")
    lines.append(f"- **生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- **総コール数**: {total} 件")
    lines.append("")

    # --- コールサマリー ---
    lines.append("## 1. コールサマリー")
    lines.append("")
    lines.append(f"| 項目 | 値 |")
    lines.append(f"|---|---|")
    lines.append(f"| 総コール数 | {total} 件 |")
    lines.append(f"| 平均通話時間 | {avg_dur} 秒 |")
    lines.append(f"| 最長通話時間 | {max_dur} 秒 |")
    lines.append(f"| 最短通話時間 | {min_dur} 秒 |")
    lines.append(f"| 異常ケース数 | {len(stats['anomalies'])} 件 |")
    lines.append("")

    # --- フロー別件数 ---
    lines.append("## 2. フロー別件数")
    lines.append("")
    lines.append("| フロー名 | 件数 |")
    lines.append("|---|---|")
    for flow, cnt in stats["flows"].most_common():
        lines.append(f"| `{flow}` | {cnt} |")
    lines.append("")

    # --- 用件分類 ---
    lines.append("## 3. 用件分類分布")
    lines.append("")
    lines.append("| 用件 | 件数 | 割合 |")
    lines.append("|---|---|---|")
    for youken, cnt in stats["youken"].most_common():
        pct = f"{cnt/total*100:.1f}%" if total else "-"
        lines.append(f"| {youken} | {cnt} | {pct} |")
    lines.append("")

    # --- Scripts_用件 ---
    lines.append("## 4. Scripts_用件 マッチ率")
    lines.append("")
    sc_total = sum(stats["scripts_youken"].values())
    sc_no_result = stats["scripts_youken"].get("NO_RESULT", 0)
    sc_match = sc_total - sc_no_result
    match_pct = f"{sc_match/sc_total*100:.1f}%" if sc_total else "N/A"
    fb_pct = f"{stats['openai_fallback']/total*100:.1f}%" if total else "N/A"

    lines.append(f"| 項目 | 件数 | 割合 |")
    lines.append(f"|---|---|---|")
    lines.append(f"| Scripts キーワードマッチ成功 | {sc_match} | {match_pct} |")
    lines.append(f"| NO_RESULT（OpenAI fallback） | {sc_no_result} | - |")
    lines.append(f"| OpenAI fallback 発動（実測） | {stats['openai_fallback']} | {fb_pct} |")
    lines.append("")

    lines.append("### Scripts_用件 結果内訳")
    lines.append("")
    lines.append("| 結果 | 件数 |")
    lines.append("|---|---|")
    for k, v in stats["scripts_youken"].most_common():
        lines.append(f"| {k} | {v} |")
    lines.append("")

    # --- FAQ ---
    lines.append("## 5. FAQ ヒット率")
    lines.append("")
    faq_answer = stats["faq_result"].get("ANSWER", 0)
    faq_no = stats["faq_result"].get("NO_RESULT", 0)
    faq_total = faq_answer + faq_no
    hit_pct = f"{faq_answer/faq_total*100:.1f}%" if faq_total else "N/A"
    lines.append(f"| 項目 | 件数 | 割合 |")
    lines.append(f"|---|---|---|")
    lines.append(f"| FAQ ANSWER（Scripts 完全一致ヒット）| {faq_answer} | {hit_pct} |")
    lines.append(f"| FAQ NO_RESULT（OpenAI fallback へ） | {faq_no} | - |")
    lines.append(f"| FAQ 問合せ合計 | {faq_total} | 100% |")
    lines.append("")

    if stats["faq_answer_texts"]:
        lines.append("### FAQ 回答文サンプル（上位 10 件）")
        lines.append("")
        for txt in stats["faq_answer_texts"][:10]:
            lines.append(f"- {txt}")
        lines.append("")

    # --- 終端分布 ---
    lines.append("## 6. 終端分布")
    lines.append("")
    lines.append("| 終端モジュール | 件数 | 割合 |")
    lines.append("|---|---|---|")
    for term, cnt in stats["terminals"].most_common():
        pct = f"{cnt/total*100:.1f}%" if total else "-"
        lines.append(f"| `{term}` | {cnt} | {pct} |")
    lines.append("")

    # --- 異常ケース ---
    lines.append("## 7. 異常ケース一覧")
    lines.append("")
    if stats["anomalies"]:
        lines.append("| コール ID | 異常理由 | フロー |")
        lines.append("|---|---|---|")
        for a in stats["anomalies"][:50]:
            lines.append(f"| `{a['id']}` | {a['reason']} | {a['flow']} |")
        if len(stats["anomalies"]) > 50:
            lines.append(f"\n> ... 他 {len(stats['anomalies'])-50} 件省略")
    else:
        lines.append("異常ケースなし ✅")
    lines.append("")

    lines.append("---")
    lines.append("*generated by `tools/ivr_log_report.py`*")

    return "\n".join(lines)


# ---- メイン ----

def main():
    parser = argparse.ArgumentParser(description="IVR ログ分析レポート生成")
    parser.add_argument("--csv", required=True, help="IVR ログ CSV ファイルパス")
    parser.add_argument("--facility", default="", help="施設名フィルター（col4 に含まれる文字列）")
    parser.add_argument("--out", default="", help="出力 Markdown ファイルパス（省略時は stdout）")
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f"ERROR: CSV ファイルが見つかりません: {args.csv}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading: {args.csv}", file=sys.stderr)
    calls = load_csv(args.csv, facility_filter=args.facility if args.facility else None)
    print(f"  {len(calls)} コールを読み込みました", file=sys.stderr)

    if not calls:
        print("WARNING: 対象コールが 0 件です。--facility フィルターを確認してください。", file=sys.stderr)
        sys.exit(0)

    stats = analyze(calls)
    report = render_report(stats, args.csv, args.facility or "（全施設）")

    if args.out:
        os.makedirs(os.path.dirname(args.out) if os.path.dirname(args.out) else ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"レポート出力: {args.out}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
