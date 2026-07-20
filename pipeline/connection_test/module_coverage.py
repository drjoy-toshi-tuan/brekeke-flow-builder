#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
module_coverage.py — 「シナリオ内の全モジュールがテストで最低 1 回実行されたか」を機械検証する。

品質 spec（2026-07-14）:
  - 全テストケース（正常系 + 異常系）を通して、bivr 内の全モジュールが最低 1 回実行されること
  - 実機ログ確認時にも「全モジュール実行済みか」を機械チェックすること

使い方:
  # 実機ログ（Brekeke ログ CSV・col7 トレース）と bivr を突合
  python3 connection_test/module_coverage.py \\
      --bivr output/scenarios/{施設}_{flow}/xxx.bivr \\
      --log  output/scenarios/{施設}_{flow}/logs/run_*.csv [--log ...複数可] \\
      [--report output/scenarios/{施設}_{flow}/module_coverage_{flow}.md]

  終了コード: 0=全モジュール実行済み / 2=未実行モジュールあり（レポート参照）

  ※ 実機前の静的被覆（そもそも到達可能か）は sim_connection.py audit の
    unreached_modules を使う（本ツールは「実行されたか」のログ事後検証）。

判定規則:
  - 対象 = bivr 全フローの modules キー（メインチェーン）。subs（save2db 等の副層）は
    親モジュール実行時に走るため、親が実行済みなら実行済みとみなす。
  - ログのトレース keyは サブフロー呼び出しで "jump名.モジュール名" と前置されるため、
    末尾セグメント（短名）で照合する。
  - 実行されないのが正当なモジュール（他 DID 入口専用等）は --ignore REGEX で除外を宣言する
    （黙って除外しない — レポートに ignore 一覧を明記する）。
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import zipfile
from pathlib import Path


def load_bivr_modules(bivr_path: Path) -> dict[str, dict[str, dict]]:
    """{flow短名: {モジュール名: モジュール定義}} を返す。"""
    flows: dict[str, dict[str, dict]] = {}
    with zipfile.ZipFile(bivr_path) as z:
        for n in z.namelist():
            d = json.loads(z.read(n).decode("utf-8"))
            name = d.get("name", n)
            short = name.split("$", 1)[-1]
            flows[short] = d.get("modules", {}) or {}
    return flows


def executed_names_from_log(log_path: Path) -> set[str]:
    """Brekeke ログ CSV の col7 トレース（k:v;k:v;）から実行モジュール短名集合を返す。
    サブフロー prefix（jump名.モジュール名）は末尾セグメントに正規化。"""
    executed: set[str] = set()
    with log_path.open(encoding="utf-8", errors="replace", newline="") as f:
        for raw in csv.reader(f):
            if len(raw) < 7:
                continue
            trace = raw[6]
            for seg in trace.split(";"):
                seg = seg.strip()
                if not seg:
                    continue
                key = seg.partition(":")[0].strip()
                if not key:
                    continue
                executed.add(key)
                # jump prefix 正規化（a.b.c → c も登録）
                if "." in key:
                    executed.add(key.rsplit(".", 1)[-1])
    return executed


def sub_module_names(mod: dict) -> list[str]:
    """モジュール定義の subs から参照サブモジュール名を列挙する。"""
    names = []
    for s in mod.get("subs", []) or []:
        n = (s or {}).get("moduleName", "")
        if n:
            names.append(n)
    return names


def check_coverage(flows: dict[str, dict[str, dict]], executed: set[str],
                   ignore_patterns: list[str]) -> dict:
    """フローごとに 未実行モジュール を判定する。"""
    ignores = [re.compile(p) for p in ignore_patterns]
    report = {"flows": {}, "total": 0, "executed": 0, "unexecuted": 0, "ignored": 0}

    # subs 副層: 親実行済みなら実行済み扱いにするため、親→subs 対応を先に作る
    for flow_short, mods in flows.items():
        covered_by_parent: set[str] = set()
        for name, mod in mods.items():
            if name in executed:
                covered_by_parent.update(sub_module_names(mod))

        missing, ignored, done = [], [], []
        for name in sorted(mods):
            if any(p.search(name) for p in ignores):
                ignored.append(name)
                continue
            if name in executed or name in covered_by_parent:
                done.append(name)
            else:
                missing.append(name)
        report["flows"][flow_short] = {
            "total": len(mods), "executed": len(done),
            "unexecuted": missing, "ignored": ignored,
        }
        report["total"] += len(mods)
        report["executed"] += len(done)
        report["unexecuted"] += len(missing)
        report["ignored"] += len(ignored)
    return report


def render_report(report: dict, bivr: str, logs: list[str],
                  ignore_patterns: list[str]) -> str:
    lines = [
        "# モジュール実行カバレッジ（テストログ突合）",
        "",
        f"- bivr: `{bivr}`",
        f"- logs: {', '.join('`%s`' % l for l in logs)}",
        f"- ignore: {', '.join('`%s`' % p for p in ignore_patterns) or '（なし）'}",
        "",
        f"**合計: {report['executed']}/{report['total']} 実行済み"
        f"（未実行 {report['unexecuted']} / ignore {report['ignored']}）**",
        "",
    ]
    for flow_short, fr in report["flows"].items():
        status = "✅ 全実行" if not fr["unexecuted"] else f"❌ 未実行 {len(fr['unexecuted'])} 件"
        lines.append(f"## {flow_short} — {fr['executed']}/{fr['total']} {status}")
        if fr["unexecuted"]:
            lines.append("")
            lines.append("未実行モジュール（テストケース追加 or --ignore 宣言が必要）:")
            for n in fr["unexecuted"]:
                lines.append(f"- [ ] `{n}`")
        if fr["ignored"]:
            lines.append("")
            lines.append(f"ignore 宣言済み: {', '.join('`%s`' % n for n in fr['ignored'])}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="bivr 全モジュールの実行カバレッジをログと突合する")
    ap.add_argument("--bivr", required=True, help="対象 bivr")
    ap.add_argument("--log", action="append", required=True,
                    help="Brekeke ログ CSV（複数指定可・全ケース分のログを渡す）")
    ap.add_argument("--ignore", action="append", default=[],
                    help="未実行でも許容するモジュール名の正規表現（理由をレポートに残すこと）")
    ap.add_argument("--report", default=None, help="Markdown レポート出力先（省略時 stdout のみ）")
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    flows = load_bivr_modules(Path(args.bivr))
    executed: set[str] = set()
    for lp in args.log:
        p = Path(lp)
        if not p.exists():
            raise SystemExit(f"[ERROR] ログが見つかりません: {p}")
        executed |= executed_names_from_log(p)

    report = check_coverage(flows, executed, args.ignore)
    md = render_report(report, args.bivr, args.log, args.ignore)
    print(md)
    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        io.open(out, "w", encoding="utf-8").write(md + "\n")
        print(f"[OK] レポート → {out}", file=sys.stderr)

    if report["unexecuted"]:
        print(f"[FAIL] 未実行モジュール {report['unexecuted']} 件 — "
              f"ケース追加または --ignore 宣言（正当理由つき）が必要", file=sys.stderr)
        return 2
    print("[PASS] 全モジュール実行済み", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
