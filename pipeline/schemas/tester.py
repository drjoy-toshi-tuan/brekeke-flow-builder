#!/usr/bin/env python3
"""
tester.py — ボイスボットフローJSON 品質テスター

OpenAIプロンプト品質チェック + 全ルート到達性テストを統合実行し、
Markdownレポートを出力する。prompter実行前のファイルは受け付けない。

Usage:
    python schemas/tester.py output/json/prompted_xxx.json \\
        --subflows output/json/draft_xxx_氏名聴取.json output/json/draft_xxx_電話番号聴取.json \\
        --properties output/scenarios/{施設}_{flow}/properties_{施設}_{flow}.md

    # 探索上限の引き上げ（デフォルト: 10000）
    python schemas/tester.py ... --max-routes 30000

    # レポート出力先指定
    python schemas/tester.py ... -o output/reports/test_report_xxx.md

NOTE: prompter実行後のファイル（prompted_*.json / reviewed_*.json）に対して実行すること。
      OpenAIモジュールのpromptが空の場合は実行を中止する。
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "connection_test"))
from sim_connection import structural_audit, load_flows_json, is_terminal_type


# ============================================================
# Pre-flight チェック
# ============================================================

def preflight_check(flow_data: dict) -> list[str]:
    """OpenAIモジュールのpromptが空のものを検出して返す"""
    empty_modules = []
    for name, mod in flow_data.get("modules", {}).items():
        if "generate_by_OpenAI" in mod.get("type", ""):
            prompt = mod.get("params", {}).get("prompt", "")
            if not prompt.strip():
                empty_modules.append(name)
    return empty_modules


# ============================================================
# レポート生成
# ============================================================

def generate_report(
    flow_name: str,
    json_path: str,
    properties_path: str | None,
    subflow_paths: list[str],
    walk_result,
) -> str:
    """Markdownレポートを生成して返す"""

    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 総合判定
    has_critical = False
    if walk_result:
        has_critical = any(i.severity == "CRITICAL" for i in walk_result.issues)

    verdict = "FAIL" if has_critical else "PASS"

    # ヘッダー
    lines.append(f"# テストレポート — {flow_name}")
    lines.append("")
    lines.append(f"**判定**: {verdict}")
    lines.append(f"**テスト対象**: `{json_path}`")
    if properties_path:
        lines.append(f"**IVRプロパティ**: `{properties_path}`")
    if subflow_paths:
        lines.append(f"**サブフロー**: {', '.join(f'`{p}`' for p in subflow_paths)}")
    lines.append(f"**実行日時**: {now}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ========== 構造監査（フラット化）==========
    if walk_result is not None:
        lines.append("## 構造監査（フラット化）")
        lines.append("")

        route_critical = sum(1 for i in walk_result.issues if i.severity == "CRITICAL")
        route_warning = sum(1 for i in walk_result.issues if i.severity == "WARNING")

        lines.append(f"**ルート数（サンプル）**: {len(walk_result.routes)}  "
                      f"**CRITICAL**: {route_critical}  **WARNING**: {route_warning}")
        lines.append(f"**モジュールカバレッジ**: "
                      f"{len(walk_result.reached_modules)}/{walk_result.total_modules} "
                      f"({walk_result.coverage:.1f}%)")
        lines.append("")

        # ルート一覧テーブル
        lines.append("### ルート一覧（サンプル）")
        lines.append("")
        lines.append("| # | 分類 | ルート概要 | 終端 | 種別 | 判定 |")
        lines.append("|---|---|---|---|---|---|")

        for i, route in enumerate(walk_result.routes):
            # ルート概要（要約）
            path_names = [str(step) for step in route.path]
            if len(path_names) > 6:
                summary = " → ".join(path_names[:3]) + " → ... → " + " → ".join(path_names[-2:])
            else:
                summary = " → ".join(path_names)

            icon = "✓" if is_terminal_type(route.terminal_type) else "✗"
            lines.append(
                f"| {i+1} | {route.classification} | {summary} "
                f"| {route.terminal} | {route.terminal_type} | {icon} |"
            )

        lines.append("")

        # 問題検出
        if walk_result.issues:
            lines.append("### 問題検出")
            lines.append("")
            for issue in walk_result.issues:
                lines.append(f"- [{issue.severity}] {issue.code}: {issue.message}")
            lines.append("")

        # 未到達モジュール
        if walk_result.unreached_modules:
            lines.append("### 未到達モジュール")
            lines.append("")
            for m in walk_result.unreached_modules:
                lines.append(f"- {m}")
            lines.append("")

    return "\n".join(lines)


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="ボイスボットフローJSON 品質テスター",
    )
    parser.add_argument("flow_json", help="メインフローJSONファイルパス")
    parser.add_argument(
        "--subflows", nargs="*", default=[],
        help="サブフローJSONファイルパス（複数指定可）",
    )
    parser.add_argument(
        "--properties", default=None,
        help="IVRプロパティファイルパス",
    )
    parser.add_argument(
        "--max-routes", type=int, default=10000,
        help="ルート探索の上限数（デフォルト: 10000）",
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="レポート出力先パス（省略時は stdout）",
    )

    args = parser.parse_args()

    # フローJSON読み込み
    with open(args.flow_json, encoding="utf-8") as f:
        flow_data = json.load(f)

    flow_name = flow_data.get("name", Path(args.flow_json).stem)

    # --- Pre-flight: prompter実行済みか確認 ---
    empty_modules = preflight_check(flow_data)
    if empty_modules:
        print(f"[ABORT] prompter未実行: {len(empty_modules)}個のOpenAIモジュールで"
              f"params.promptが空です", file=sys.stderr)
        for m in empty_modules:
            print(f"  - {m}", file=sys.stderr)
        print(f"\nprompter実行後のファイル（prompted_*.json / reviewed_*.json）に"
              f"対して実行してください。", file=sys.stderr)
        sys.exit(2)

    # --- 構造監査（フラット化して監査）---
    flows, main_name = load_flows_json(args.flow_json, args.subflows or [])
    print(f"[構造監査] フロー読み込み: {list(flows.keys())}", file=sys.stderr)

    walk_result, _flat = structural_audit(flows, main_name, max_routes=args.max_routes)

    route_c = sum(1 for i in walk_result.issues if i.severity == "CRITICAL")
    route_w = sum(1 for i in walk_result.issues if i.severity == "WARNING")
    print(f"[構造監査] ルート {len(walk_result.routes)}本（サンプル）  "
          f"カバレッジ {walk_result.coverage:.1f}%  "
          f"CRITICAL={route_c}  WARNING={route_w}", file=sys.stderr)

    # --- レポート生成 ---
    report = generate_report(
        flow_name=flow_name,
        json_path=args.flow_json,
        properties_path=args.properties,
        subflow_paths=args.subflows,
        walk_result=walk_result,
    )

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n[完了] レポート出力: {args.output}", file=sys.stderr)
    else:
        print(report)

    # 終了コード
    has_critical = any(i.severity == "CRITICAL" for i in walk_result.issues)
    sys.exit(1 if has_critical else 0)


if __name__ == "__main__":
    main()
