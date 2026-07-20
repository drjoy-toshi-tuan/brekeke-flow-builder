#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge_cases.py — 複数の cases JSON を1つにマージして P7 stub_stt_connection.py に渡す。

用途:
  P7 連結テストでは「正解分岐（branch）+ 実発話（real）+ マスターパターン（master）」を
  1つの bivr で流したい。本ツールはそれらを結合して DTMF 番号を再採番する。

使い方:
  python3 connection_test/merge_cases.py \
      --inputs connection_test/cases/東京都立豊島_診療_branches.json \
               connection_test/cases/東京都立豊島_診療_real.json \
               connection_test/cases/東京都立豊島_診療_master.json \
      --out    connection_test/cases/東京都立豊島_診療_merged.json \
      [--label "東京都立豊島 診療 マージ"]

重複排除:
  同じ case_id が複数のソースに含まれる場合、先に登場した方を残す（後のソースを skip）。
  DTMF 番号は出力順に 1, 2, 3 … と再採番する（セレクタが 9# に収まるよう上限チェックあり）。

オプション:
  --dedup-by  id (default) | label | inject
              id    : case_id が一致したらスキップ
              label : label が一致したらスキップ
              inject: inject dict の内容が完全一致したらスキップ
  --max 200   マージ後の上限ケース数（超えたら警告して打ち切り）
  --dry-run   出力せず結果サマリのみ表示
"""

import argparse
import json
import sys
from pathlib import Path


MAX_DTMF = 99   # stub_stt_connection.py の DTMF セレクタ上限（実機: 2桁まで）


def load_cases_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if "cases" not in data:
        print(f"[WARN] {path.name}: 'cases' キーが見つかりません。スキップします。", file=sys.stderr)
        return {}
    return data


def dedup_key(case: dict, mode: str) -> str:
    if mode == "id":
        return str(case.get("id", ""))
    if mode == "label":
        return str(case.get("label", ""))
    if mode == "inject":
        # "_comment" 等のアンダースコアキーは実注入に関与しないため署名から除外
        inj = {k: v for k, v in case.get("inject", {}).items() if not k.startswith("_")}
        return json.dumps(inj, ensure_ascii=False, sort_keys=True)
    return str(case.get("id", ""))


def merge(inputs: list[Path], dedup_mode: str, max_cases: int) -> tuple[list[dict], dict, dict, dict]:
    """全ソースの cases をマージして (cases_list, meta, defaults, selector) を返す。"""
    seen: set[str] = set()
    merged: list[dict] = []
    source_stats: list[str] = []
    base_meta: dict = {}
    base_defaults: dict = {}
    base_selector: dict = {}

    for src_path in inputs:
        data = load_cases_file(src_path)
        if not data:
            continue

        # 最初のファイルの meta を基底として使う
        if not base_meta:
            base_meta = data.get("meta", {})
        # defaults / selector も先勝ちで継承（空 {} のまま出力すると
        # stub_stt_connection.py が defaults["_order"] で KeyError になる）
        src_defaults = data.get("defaults", {})
        if src_defaults:
            if not base_defaults:
                base_defaults = dict(src_defaults)
            else:
                # 後続ソースは不足キーのみ補完。_order は既存順を保ち未知キーワードを末尾に追加
                for k, v in src_defaults.items():
                    if k == "_order":
                        base_defaults["_order"] = list(base_defaults.get("_order", [])) + [
                            kw for kw in v if kw not in base_defaults.get("_order", [])]
                    elif k not in base_defaults:
                        base_defaults[k] = v
        if not base_selector and data.get("selector"):
            base_selector = data["selector"]

        src_cases = data.get("cases", [])
        added = 0
        skipped = 0
        for case in src_cases:
            key = dedup_key(case, dedup_mode)
            if key and key in seen:
                skipped += 1
                continue
            if key:
                seen.add(key)

            # _source タグを付けて追記
            c = dict(case)
            c["_source"] = src_path.stem
            merged.append(c)
            added += 1

            if len(merged) >= max_cases:
                print(f"[WARN] --max {max_cases} に達したため打ち切り。残りのソースはスキップ。",
                      file=sys.stderr)
                source_stats.append(f"  {src_path.name}: +{added} / skip {skipped} (打ち切り)")
                return merged, base_meta, base_defaults, base_selector

        source_stats.append(f"  {src_path.name}: +{added} / skip {skipped}")

    for s in source_stats:
        print(s, file=sys.stderr)

    return merged, base_meta, base_defaults, base_selector


def renumber_dtmf(cases: list[dict]) -> list[dict]:
    """DTMF を 1 始まりで再採番する。99 超えは警告。"""
    result = []
    for i, case in enumerate(cases):
        c = dict(case)
        dtmf_num = i + 1
        if dtmf_num > MAX_DTMF:
            print(f"[WARN] ケース数が {MAX_DTMF} を超えました（{dtmf_num}）。"
                  f"DTMF 2桁での動作を確認してください。", file=sys.stderr)
        c["dtmf"] = str(dtmf_num)
        result.append(c)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="複数 cases JSON を1つにマージ")
    ap.add_argument("--inputs", nargs="+", required=True, metavar="FILE",
                    help="マージするケースJSONファイル（先に書いた方が優先）")
    ap.add_argument("--out",    required=True, help="出力先 JSON パス")
    ap.add_argument("--label",  default="", help="出力 _about ラベル（省略時: 自動生成）")
    ap.add_argument("--dedup-by", choices=["id", "label", "inject"], default="id",
                    help="重複排除キー (default: id)")
    ap.add_argument("--max",    type=int, default=200, help="上限ケース数 (default: 200)")
    ap.add_argument("--dry-run", action="store_true", help="出力せずサマリのみ表示")
    args = ap.parse_args()

    input_paths = [Path(p) for p in args.inputs]
    for p in input_paths:
        if not p.exists():
            print(f"[ERROR] ファイルが見つかりません: {p}", file=sys.stderr)
            return 1

    print(f"[INFO] マージ開始 ({len(input_paths)} ソース, dedup-by={args.dedup_by})",
          file=sys.stderr)

    cases, base_meta, base_defaults, base_selector = merge(input_paths, args.dedup_by, args.max)
    cases = renumber_dtmf(cases)

    if not base_defaults.get("_order"):
        print("[WARN] defaults._order がどのソースにもありません。"
              "stub_stt_connection.py はこのままでは実行時エラーになります（手動追記が必要）。",
              file=sys.stderr)

    source_names = [p.stem for p in input_paths]
    about = args.label or (
        f"P7 マージケース — {base_meta.get('facility','')} {base_meta.get('flow','')} "
        f"[{' + '.join(source_names)}]"
    )

    output = {
        "_about":  about,
        "_sources": [str(p) for p in input_paths],
        "meta": {
            **base_meta,
            "_generated_by": "merge_cases.py",
            "_source_count":  len(input_paths),
        },
        "selector": base_selector,   # 先勝ちで継承（stub_stt_connection.py が参照）
        "defaults": base_defaults,   # 先勝ちで継承・後続ソースは不足キーのみ補完
        "cases":    cases,
    }

    print(f"[INFO] 合計 {len(cases)} ケース", file=sys.stderr)

    if args.dry_run:
        print("[DRY-RUN] 出力をスキップしました。", file=sys.stderr)
        for c in cases:
            print(f"  {c['dtmf']:>3}# {c.get('label', c.get('case_name',''))!r:40s} [{c.get('_source','')}]")
        return 0

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] → {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
