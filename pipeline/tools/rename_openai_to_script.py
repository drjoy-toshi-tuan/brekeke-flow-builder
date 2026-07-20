#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rename_openai_to_script.py — 手動編集 bivr/JSON 向け OpenAI_* → script_* 一括リネーム CLI（issue #236）。

generate_by_OpenAI を `@General$Script`（決定論部品）へ手動置換した際に残る
`OpenAI_*` / `openAI_*` 命名のモジュールと、その全参照（next / CMR module1Name,2Name /
params.module / Re-confirmation params.nodeName / script 本文 / saveDefault-OpenAI_* 補助）を
一括で `script_*` に正規化する。

検出・改名・参照追従のロジックは scripts/rename_openai_modules.py（決定論核）を共有し、
パイプラインの auto_fixer op `rename_module`（validator SCR-001 起票）と同一挙動。

使い方:
    # 単一フロー JSON を上書き（バックアップは取らない。git 管理下で使う想定）
    python3 tools/rename_openai_to_script.py path/to/flow.json

    # 別ファイルに出力
    python3 tools/rename_openai_to_script.py flow.json --output fixed.json

    # ディレクトリ内の全 *.json を一括処理（サブフロー含む展開済み JSON 群）
    python3 tools/rename_openai_to_script.py output/scenarios/恵佑会_診療/json/

    # 変更を加えず検出のみ（diff 確認）
    python3 tools/rename_openai_to_script.py flow.json --dry-run

    # リネームせず整合性のみ検証（残骸 + 全参照のダングリング）。問題があれば exit 1（issue #273）
    python3 tools/rename_openai_to_script.py output/scenarios/つくば_診療/json/ --verify

.bivr（zip）を直接編集する機能は持たない。.bivr は extract_bivr.py で JSON へ展開し、
本ツールで正規化したのち build_bivr.py で再ビルドする（バイト再現性は #224 の方針に従う）。

--verify（issue #273）:
    手動サージカルパッチはパイプライン（validator SCR-001 / auto_fixer / T-001 / CMR-001）を
    通らないため、置換後の整合性を機械的に検証する手段が無かった。--verify は
      (1) OpenAI_*/openAI_* 命名のまま残った @General$Script 残骸
      (2) 実在しないモジュールを指すダングリング参照（start / next / subs /
          CMR module1Name,2Name / params.module / Re-confirmation params.nodeName）
          ＝部分リネームの取りこぼし
    を検出し、いずれかがあれば exit 1 を返す。手動パッチ後のゲート / CI に使える。
"""

import argparse
import json
import sys
from pathlib import Path

# Windows cp932 化け対策（issue #225）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# 決定論核（scripts/）を読む
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from rename_openai_modules import (  # noqa: E402
    detect_openai_script_renames,
    apply_rename_mapping,
    detect_dangling_references,
    verify_flow_integrity,
)


def _load_flow(path: Path) -> dict | None:
    """フロー JSON を読む。フロー（modules を持つ dict）でなければ None。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"[SKIP] {path}: 読み込み/パース失敗: {e}", file=sys.stderr)
        return None
    if not isinstance(data, dict) or "modules" not in data:
        # フロー JSON でない（中間レポート等）はスキップ
        return None
    return data


def _process_flow(path: Path, dry_run: bool, output: Path | None) -> int:
    """1 つの JSON フローを処理。変更件数（写像エントリ数）を返す。"""
    data = _load_flow(path)
    if data is None:
        return 0

    mapping = detect_openai_script_renames(data)
    if not mapping:
        return 0

    print(f"[{path.name}] OpenAI_* Script 残骸 {len(mapping)} 名を検出:", file=sys.stderr)
    for old, new in mapping.items():
        print(f"    {old}  →  {new}", file=sys.stderr)

    if dry_run:
        print(f"  (--dry-run: 書き込みなし)", file=sys.stderr)
        return len(mapping)

    apply_rename_mapping(data, mapping)
    out = output if output else path
    # auto_fixer.py と同じくコンパクト JSON で出力（パイプライン中間 JSON の慣習）
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                   encoding="utf-8")
    print(f"  → 保存: {out}", file=sys.stderr)
    # リネーム後の取りこぼし（rename 核が追従しきれない先＝別要因のダングリング）を警告（issue #273）
    dangling = detect_dangling_references(data)
    if dangling:
        print(f"  [WARN] リネーム後もダングリング参照が {len(dangling)} 件残存"
              f"（OpenAI 残骸起因でない可能性・--verify で詳細）:", file=sys.stderr)
        for d in dangling:
            print(f"    {d['module']}.{d['field']} → '{d['target']}' (実在しない)", file=sys.stderr)
    return len(mapping)


def _verify_flow(path: Path) -> int:
    """1 つのフロー JSON を整合性検証（リネームしない）。問題件数を返す（issue #273）。"""
    data = _load_flow(path)
    if data is None:
        return 0
    report = verify_flow_integrity(data)
    residue, dangling = report["residue"], report["dangling"]
    if not residue and not dangling:
        return 0
    print(f"[{path.name}] 整合性 NG:", file=sys.stderr)
    for name in residue:
        print(f"  [残骸] OpenAI_* のまま残る @General$Script: {name}"
              f"（→ script_ にリネーム推奨）", file=sys.stderr)
    for d in dangling:
        print(f"  [ダングリング] {d['module']}.{d['field']} → '{d['target']}' が modules 内に存在しない",
              file=sys.stderr)
    return len(residue) + len(dangling)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="OpenAI_* と命名された決定論 Script モジュールを script_* へ一括リネーム（issue #236）")
    ap.add_argument("path", help="対象のフロー JSON ファイル、または *.json を含むディレクトリ")
    ap.add_argument("--output", help="出力先 JSON（単一ファイル時のみ。省略時は上書き）")
    ap.add_argument("--dry-run", action="store_true", help="検出のみ・書き込みしない")
    ap.add_argument("--verify", action="store_true",
                    help="リネームせず整合性のみ検証（残骸 + 全参照のダングリング）。問題があれば exit 1（issue #273）")
    args = ap.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"[ERROR] パスが存在しません: {target}", file=sys.stderr)
        return 1

    if args.verify:
        if args.output:
            print("[ERROR] --verify と --output は併用できません", file=sys.stderr)
            return 1
        flows = sorted(target.rglob("*.json")) if target.is_dir() else [target]
        problems = 0
        checked = 0
        for f in flows:
            if _load_flow(f) is None:
                continue
            checked += 1
            problems += _verify_flow(f)
        if problems:
            print(f"[verify] NG: {checked} フロー中に整合性問題 {problems} 件", file=sys.stderr)
            return 1
        print(f"[verify] OK: {checked} フロー、残骸・ダングリング参照なし", file=sys.stderr)
        return 0

    if target.is_dir():
        if args.output:
            print("[ERROR] ディレクトリ処理時に --output は使えません", file=sys.stderr)
            return 1
        flows = sorted(target.rglob("*.json"))
        if not flows:
            print(f"[ERROR] {target} 配下に *.json がありません", file=sys.stderr)
            return 1
        total = 0
        touched = 0
        for f in flows:
            n = _process_flow(f, args.dry_run, None)
            total += n
            touched += 1 if n else 0
        print(f"[done] {touched}/{len(flows)} ファイルでリネーム適用、写像 {total} 名", file=sys.stderr)
        return 0

    output = Path(args.output) if args.output else None
    n = _process_flow(target, args.dry_run, output)
    if n == 0:
        print(f"[done] {target}: OpenAI_* Script 残骸なし（変更なし）", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
