#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""新規部品スケルトン生成（factory-v2 Phase 2 / 工場長の「部品調達」を決定論化）。

工場長が NO_CERTIFIED_PART の判定点に対して新部品を「調達」するとき、
認定仕様（docs/governance/part-certification-spec.md）に沿った正しい骨格を
機械的に用意するためのツール。これにより工場長は構造を手書きせず、
中身（用途・規格データ・テストケース）の充填に集中できる。

生成物（modules/<part_id>/ 配下・既存があれば中断して何もしない）:
  - REQUIREMENTS.md            入出力/分岐/エッジケース（要記入）
  - script.js                  @part-id/@engine-version マーカー + wiring + @spec ブロックの雛形
  - oracle.py                  classify() の雛形（決定論判定の本体）
  - test_oracle.py             cases.tsv を読んで oracle.classify を検証
  - part.json                  part_id/engine_version/output_labels/wiring_vars/spec_vars/specs
  - acceptance_test/<spec>/cases.tsv   入力<TAB>期待ラベル のヘッダ

注意: 本ツールは「骨格」を出すだけ。認定（certified_hashes 登録）は実機 P6 PASS 後の
人間ゲート。工場長は oracle PASS まで持っていって PR/Issue を起票する（自律認定はしない）。

stdlib のみ・LLM 不使用。pip install 不要。
使い方: python3 tools/new_part_skeleton.py <part_id> [--spec <spec_label>] [--labels A,B,NO_RESULT]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "modules"

SCRIPT_JS_TEMPLATE = """// @part-id: {part_id}
// @engine-version: v1
//
// {part_id} — 決定論判定エンジン（工場長が調達した新部品の雛形）。
// 認定仕様: docs/governance/part-certification-spec.md
//   engine = 全用途でバイト不変のアルゴリズム（engine_hash 対象）
//   spec   = 施設/設問ごとに正当に変わる分類データ（@spec で囲う・spec_hash 対象）
//   wiring = 入力元/保存先（part.json の wiring_vars に列挙・両ハッシュから除外）

// --- wiring（part.json の wiring_vars に列挙すること）---
var SOURCE_MODULE = "{{{{SOURCE_MODULE}}}}";

// @spec-begin
// TODO: 施設/設問ごとに変わる分類データをここに置く（変更時は再受入が走る）。
// var RULES = {{{{RULES}}}};
// @spec-end

// （ここから下が engine = 不変アルゴリズム。placeholder を置かないこと）
var logger = $runner.getLogger();

// TODO: 判定本体を実装。getModuleResult(SOURCE_MODULE) で入力取得 → 正規化 → 判定 → setResult。
"""

ORACLE_PY_TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""{part_id} のオラクル（決定論判定の Python 実装・テストが正）。

script.js の engine と同一ロジックをここに実装し、test_oracle.py で全ケース PASS を担保する。
"""
from __future__ import annotations


def classify(utterance: str) -> str:
    """入力発話 → 出力ラベル（part.json の output_labels のいずれか）を返す。

    TODO: 決定論判定を実装。判定不能は "NO_RESULT" を返す（沈黙の誤受理を避ける）。
    """
    raise NotImplementedError("classify() を実装してください")
'''

TEST_ORACLE_PY_TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""{part_id} のオラクル受入テスト。acceptance_test/<spec>/cases.tsv を読んで classify を検証する。

cases.tsv 形式: 1 行 1 ケース、`入力<TAB>期待ラベル`（# 始まりはコメント・空行は無視）。
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from oracle import classify  # noqa: E402


def _iter_cases():
    for tsv in sorted(HERE.glob("acceptance_test/*/cases.tsv")):
        for lineno, line in enumerate(tsv.read_text(encoding="utf-8").splitlines(), 1):
            s = line.rstrip("\\n")
            if not s.strip() or s.lstrip().startswith("#"):
                continue
            parts = s.split("\\t")
            if len(parts) < 2:
                continue
            yield tsv, lineno, parts[0], parts[1]


def main() -> int:
    total = 0
    failed = 0
    for tsv, lineno, utt, expected in _iter_cases():
        total += 1
        got = classify(utt)
        if got != expected:
            failed += 1
            print(f"[FAIL] {{tsv.parent.name}}:{{lineno}} input={{utt!r}} expected={{expected}} got={{got}}")
    if total == 0:
        print("[WARN] ケースが 0 件です。acceptance_test/<spec>/cases.tsv を用意してください。")
        return 1
    print(f"{{total - failed}}/{{total}} PASS")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
'''

REQUIREMENTS_TEMPLATE = """# {part_id} — 要件定義（REQUIREMENTS）

> 工場長が調達した新部品の雛形。中身を埋めて oracle PASS まで持っていく。
> 認定（certified_hashes 登録）は実機 P6 PASS 後の人間ゲート。

## 用途
TODO: この部品が何の判定点を決定論化するか（例: 受診区分=新規/再診の分類）。

## 入出力
- 入力: TODO（どのモジュールの結果を受けるか・自由発話か）
- 出力ラベル（output_labels）: {labels}

## 分岐・判定ルール
TODO: ラベルごとの判定条件。判定不能は NO_RESULT（沈黙の誤受理を避ける）。

## エッジケース
TODO: 揺れ・否定・複合・OFF_FRAME 等。

## 受入
- oracle: `python3 modules/{part_id}/test_oracle.py`（cases.tsv 全 PASS）
- 実機: Pattern 6 bivr で [TEST FAIL]=0（人間ゲート）
"""

CASES_TSV_TEMPLATE = """# {part_id} / spec={spec} 受入ケース。1 行 1 ケース: 入力<TAB>期待ラベル
# 例:
# はい\t肯定
# いいえ\t否定
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="新規部品スケルトンを生成する")
    ap.add_argument("part_id", help="部品 ID（snake_case 推奨。例: visit_type_classifier）")
    ap.add_argument("--spec", default="default", help="最初の規格ラベル（acceptance_test/<spec>/）")
    ap.add_argument("--labels", default="NO_RESULT", help="出力ラベルをカンマ区切りで（例: 新規,再診,NO_RESULT）")
    args = ap.parse_args()

    part_id = args.part_id.strip()
    labels = [s.strip() for s in args.labels.split(",") if s.strip()]
    part_dir = MODULES_DIR / part_id

    if part_dir.exists():
        print(f"[中断] {part_dir.relative_to(REPO_ROOT).as_posix()} は既に存在します。既存部品を上書きしません。")
        return 1

    spec_dir = part_dir / "acceptance_test" / args.spec
    spec_dir.mkdir(parents=True, exist_ok=True)

    (part_dir / "REQUIREMENTS.md").write_text(
        REQUIREMENTS_TEMPLATE.format(part_id=part_id, labels="、".join(labels) or "TODO"),
        encoding="utf-8",
    )
    (part_dir / "script.js").write_text(SCRIPT_JS_TEMPLATE.format(part_id=part_id), encoding="utf-8")
    (part_dir / "oracle.py").write_text(ORACLE_PY_TEMPLATE.format(part_id=part_id), encoding="utf-8")
    (part_dir / "test_oracle.py").write_text(TEST_ORACLE_PY_TEMPLATE.format(part_id=part_id), encoding="utf-8")
    part_json = {
        "part_id": part_id,
        "engine_version": "v1",
        "output_labels": labels,
        "wiring_vars": ["SOURCE_MODULE"],
        "spec_vars": [],
        "specs": {
            args.spec: {
                "cases": f"acceptance_test/{args.spec}/cases.tsv",
                "filled_script": "script.js",
                "note": "工場長が調達した新部品。実機 P6 PASS まで未認定。",
            }
        },
    }
    (part_dir / "part.json").write_text(
        json.dumps(part_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (spec_dir / "cases.tsv").write_text(
        CASES_TSV_TEMPLATE.format(part_id=part_id, spec=args.spec), encoding="utf-8"
    )

    rel = part_dir.relative_to(REPO_ROOT).as_posix()
    print(f"[生成] {rel}/ に新部品スケルトンを作成しました。")
    print("次の手順:")
    print(f"  1. {rel}/REQUIREMENTS.md を埋める（用途・入出力・分岐）")
    print(f"  2. {rel}/acceptance_test/{args.spec}/cases.tsv に受入ケースを書く")
    print(f"  3. {rel}/oracle.py に classify() を実装し script.js の engine と一致させる")
    print(f"  4. python3 {rel}/test_oracle.py で全 PASS を確認")
    print(f"  5. python3 tools/generate_parts_catalog.py でカタログ再生成")
    print("  6. 実機 P6 + certified_hashes 登録は人間ゲート（工場長は PR/Issue 起票まで）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
