#!/usr/bin/env python3
"""
yaml_auto_fixer.py -- qa_validator.py の指摘を機械的に修正する（設計書 YAML 版）

validator.py → auto_fixer.py の YAML 対応版。
qa_validator.py が --json-report で出力した Issue 一覧を読み、
fix_category="auto" の Issue に付いた fix_action に従って YAML を書き換える。

コメント保持のため text-level の正規表現置換のみ（PyYAML 経由の parse→dump は行わない）。
LLM 不使用・決定論的。

対応 op（SUPPORTED_OPS 参照。qa_validator.py の fix_action.op と同期させること）:
  - replace_all : raw yaml テキスト全体に正規表現置換を適用
                  action = {"pattern": <regex>, "replacement": <str>}
  未対応の op が来た場合は黙って無視せず、その場で stderr に WARNING を出し、
  Issue 1件ごとに failed カウントする。stats["failed"] > 0 のとき exit code 1。

Usage:
    python3 scripts/yaml_auto_fixer.py --spec output/scenarios/xxx_yyy/設計書_xxx.yaml \
        --report output/reports/qa_report_xxx.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

# qa_validator.py の fix_action.op と1対1で同期させること。
# qa_validator 側に新しい op を追加してもここに実装を追加し忘れると、
# その Issue は「未対応 op」として毎回 人間（壁打ち）へ差し戻しになる
# （black-box では気付きにくい fragile-by-convention なので明示の allowlist にしてある）。
SUPPORTED_OPS = {"replace_all"}


def _apply_replace_all(raw: str, pattern: str, replacement: str) -> tuple[str, int, str]:
    """正規表現全置換を適用。(新テキスト, 置換件数, メッセージ) を返す"""
    try:
        compiled = re.compile(pattern, flags=re.MULTILINE)
    except re.error as e:
        return raw, 0, f"regex コンパイル失敗: {e}"
    new, n = compiled.subn(replacement, raw)
    if n == 0:
        return raw, 0, "パターンマッチなし"
    return new, n, f"{n} 箇所置換"


def apply_fixes(raw: str, issues: list) -> tuple[str, dict]:
    """Issue リストの fix_action を順次適用。重複する fix_action は dedup する。

    stats:
        applied: 適用した Issue 数
        skipped: fix_action があったが何も置換されなかった Issue 数
        failed:  fix_action が失敗した Issue 数
        details: 各 Issue の処理結果
    """
    stats: dict = {"applied": 0, "skipped": 0, "failed": 0, "details": []}
    seen_keys: set[tuple] = set()

    for issue in issues:
        if issue.get("fix_category") != "auto":
            continue
        action = issue.get("fix_action") or {}
        op = action.get("op", "")
        code = issue.get("code", "?")

        if op == "replace_all":
            pattern = action.get("pattern", "")
            replacement = action.get("replacement", "")
            # 同一 (pattern, replacement) の重複適用を避ける
            key = ("replace_all", pattern, replacement)
            if key in seen_keys:
                stats["details"].append(f"[{code}] 重複 fix_action をスキップ")
                continue
            seen_keys.add(key)

            new_raw, n, msg = _apply_replace_all(raw, pattern, replacement)
            if n > 0:
                raw = new_raw
                stats["applied"] += 1
                stats["details"].append(f"[{code}] {msg}: {pattern!r} → {replacement!r}")
            elif msg == "パターンマッチなし":
                stats["skipped"] += 1
                stats["details"].append(f"[{code}] {msg}: {pattern!r}")
            else:
                stats["failed"] += 1
                stats["details"].append(f"[{code}] FAIL: {msg}")
        else:
            stats["failed"] += 1
            msg = (f"[{code}] 未対応 op: '{op}' — SUPPORTED_OPS={sorted(SUPPORTED_OPS)} に無いため "
                   f"この Issue は自動修正されません（qa_validator.py と yaml_auto_fixer.py の実装が "
                   f"同期していない可能性があります）")
            stats["details"].append(msg)
            # stats に埋もれて見落とされないよう、その場でも警告を出す
            print(f"[yaml_auto_fixer] WARNING: {msg}", file=sys.stderr)

    return raw, stats


def main() -> int:
    ap = argparse.ArgumentParser(description="yaml_auto_fixer: qa_validator の auto fix を適用")
    ap.add_argument("--spec", required=True, help="対象の設計書 YAML パス")
    ap.add_argument("--report", required=True, help="qa_validator --json-report で出力した JSON パス")
    ap.add_argument("--output", help="出力先 YAML（省略時は --spec を上書き）")
    args = ap.parse_args()

    spec_path = Path(args.spec)
    report_path = Path(args.report)

    if not spec_path.exists():
        print(f"[ERROR] 設計書が見つかりません: {spec_path}", file=sys.stderr)
        return 1
    if not report_path.exists():
        print(f"[ERROR] レポート JSON が見つかりません: {report_path}", file=sys.stderr)
        return 1

    with open(spec_path, encoding="utf-8") as f:
        raw = f.read()
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)

    issues = report.get("issues", [])
    auto_issues = [i for i in issues if i.get("fix_category") == "auto"]

    print(f"[yaml_auto_fixer] 対象: {spec_path}", file=sys.stderr)
    print(f"[yaml_auto_fixer] 検出 Issue 総数: {len(issues)}", file=sys.stderr)
    print(f"[yaml_auto_fixer] auto 修正対象: {len(auto_issues)} 件", file=sys.stderr)

    if not auto_issues:
        print("[yaml_auto_fixer] 修正対象なし（auto カテゴリの Issue なし）", file=sys.stderr)
        return 0

    new_raw, stats = apply_fixes(raw, auto_issues)

    print(f"[yaml_auto_fixer] 適用: {stats['applied']} 件 / "
          f"スキップ: {stats['skipped']} / 失敗: {stats['failed']}", file=sys.stderr)
    for d in stats["details"]:
        print(f"  {d}", file=sys.stderr)

    output_path = Path(args.output) if args.output else spec_path
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_raw)
    print(f"[yaml_auto_fixer] 保存: {output_path}", file=sys.stderr)

    print(str(output_path))
    # 一部の Issue が未対応 op 等で修正できなかった場合、CLI の exit code でも判別できるようにする
    # （orchestrator.py は stderr の「適用: N 件」を見て再チェックするため既に安全網があるが、
    #  手動実行時にも exit code だけで partial failure を検知できるようにする）
    return 1 if stats["failed"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
