#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_part_acceptance_bivr.py — 認定部品の P6 受入 BIVR を1コマンドでスクラッチ生成する。

部品再認定（engine 変更後の実機 P6）のたびに「過去の bivr を探してくる」運用を無くすための
統一導線。各部品は P6 受入仕様を **部品配下** に置く（version 管理で部品と一体・output 掃除で
消えない）。本ツールはそれを Pattern 6 パイプライン（test_scaffold → layout → build_bivr）で
毎回スクラッチ生成する。spec 内の matrix ブロック型（script_test_matrix / dob_reconfirmation_test_matrix
等）で部品種別を吸収するため、ツール自体は種別非依存。

規約:
  - P6 受入 spec:  modules/<part_id>/acceptance_test/p6_acceptance.yaml
  - 出力 bivr:     output/acceptance/<part_id>/<part_id>_p6_acceptance.bivr （--out で変更可）
  - 未来日など時刻依存ケースは spec 内で相対トークン（__TOMORROW__/__FUTURE__/__FUTURE_WAREKI__）
    を使うこと。test_scaffold_generator が生成日基準で解決するのでドリフトしない。

使い方:
  python3 tools/build_part_acceptance_bivr.py dob_normalizer
  python3 tools/build_part_acceptance_bivr.py <part_id> [--out <path.bivr>] [--spec <spec.yaml>]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"

# Windows コンソール（cp932）でも子プロセスの UTF-8 出力を表示できるようにする。
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")


def _run(cmd: list[str]) -> None:
    r = subprocess.run([sys.executable, *cmd], cwd=str(REPO),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.stdout:
        print(r.stdout.rstrip())
    if r.returncode != 0:
        print(r.stderr.rstrip(), file=sys.stderr)
        raise SystemExit(f"失敗 (exit {r.returncode}): {' '.join(cmd)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="認定部品の P6 受入 BIVR をスクラッチ生成")
    ap.add_argument("part_id", help="部品 ID（modules/<part_id>/ 配下）")
    ap.add_argument("--spec", help="P6 受入 spec を明示（既定 modules/<part>/acceptance_test/p6_acceptance.yaml）")
    ap.add_argument("--out", help="出力 bivr パス（既定 output/acceptance/<part>/<part>_p6_acceptance.bivr）")
    args = ap.parse_args()

    part = args.part_id
    part_dir = REPO / "modules" / part
    if not part_dir.is_dir():
        raise SystemExit(f"部品が見つかりません: {part_dir}")

    spec = Path(args.spec) if args.spec else part_dir / "acceptance_test" / "p6_acceptance.yaml"
    if not spec.exists():
        raise SystemExit(
            f"P6 受入 spec がありません: {spec}\n"
            f"規約: modules/{part}/acceptance_test/p6_acceptance.yaml に Pattern 6 spec を置いてください "
            f"（scenario_flow に *_test_matrix ブロックを記述）。")

    out_dir = REPO / "output" / "acceptance" / part
    out_dir.mkdir(parents=True, exist_ok=True)
    scaffold_json = out_dir / f"scaffold_{part}.json"
    out_bivr = Path(args.out) if args.out else out_dir / f"{part}_p6_acceptance.bivr"

    print(f"[build_part_acceptance] part={part}  spec={spec}")
    # 1) test_scaffold: spec → 単一フロー scaffold JSON（matrix ブロックを展開・相対日付トークン解決）
    _run([str(SCRIPTS / "test_scaffold_generator.py"), str(spec), str(scaffold_json)])
    # 2) layout: block-based レイアウト（spec の scenario_flow を使う・in-place）
    _run([str(SCRIPTS / "layout_calculator.py"), str(scaffold_json), str(spec), str(scaffold_json)])
    # 3) build_bivr: 単一フロー JSON → .bivr（明示パスゆえ stale フロー混入なし）
    _run([str(SCRIPTS / "build_bivr.py"), str(scaffold_json), "-o", str(out_bivr)])

    if not out_bivr.exists():
        raise SystemExit(f"bivr が生成されませんでした: {out_bivr}")
    print(f"\n[OK] P6 受入 BIVR: {out_bivr}")
    print("  → Brekeke に import して架電。結果_全PASS 到達で受入成立。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
