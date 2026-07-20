#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_flow_module.py — 巨大 bivr フロー JSON 内の 1 モジュールを決定論パッチする CLI（issue #319）。

Brekeke エクスポートの flow JSON は改行なし単一行で数十万文字に達することがあり（順天堂_診療で
約35万文字）、Claude Code の Read/Edit ツール（トークン上限）では直接編集できない。本ツールは
json.loads → dict 差替 → json.dumps で機械的にパッチするため、ファイルの大きさに依存しない
（読むのは Python であってツールの Read ではない＝上限問題を最初から回避する）。

【位置づけ】flow JSON は「手編集する source」ではなくビルド/デプロイ成果物である。原則は
設計書 YAML を直して scaffold 再生成（＝生成器を直す）。source YAML が無い既存本番 bivr の
サージカル修正（Pattern 2・generate_by_OpenAI→@General$Script 決定論化 等）でのみ本ツールを使い、
手貼りでなく機械パッチ＋整合検証で行う。整合検証は scripts/rename_openai_modules.py の決定論核を共有。

操作（--module で対象を特定し、下記の順で適用）:
  --set-type TYPE            module.type を差し替え（例: @General$Script）
  --set-params-json FILE     module.params = json.load(FILE)（params 丸ごと置換＝OpenAI 残骸一掃）
  --set-script FILE          module.params.script = FILE の内容（決定論スクリプト本文の注入）
  --set-param KEY VALUE      module.params[KEY] = VALUE（文字列・反復可）
  --rename NEWNAME           モジュール名変更＋全参照追従（modules キー / name / next / subs /
                             CMR module1Name,2Name / params.module / script 本文 / start）

パッチ後は必ず整合性を検証（verify_flow_integrity）。ダングリング参照（実在しない先を指す
next/subs/CMR/params）があれば表示し exit 1（--allow-dangling で警告のみ・exit 0）。

使い方:
  # OpenAI モジュールを決定論 Script へ in-place 差替（params 総取替＋改名で参照も追従）
  python3 tools/patch_flow_module.py --flow flows/診療_基本フロー.json --module OpenAI_診療科 \
      --set-type '@General$Script' --set-params-json params_dept.json --rename script_診療科

  # script 本文だけ差替（名前維持＝既存参照そのまま）
  python3 tools/patch_flow_module.py --flow flows/xxx.json --module script_診療科 \
      --set-script modules/department_classifier/script.js

  # 変更せず確認のみ
  python3 tools/patch_flow_module.py --flow flows/xxx.json --module X --set-type Y --dry-run

.bivr（zip）は直接編集しない。extract_bivr.py で JSON 展開 → 本ツールでパッチ →
build_bivr.py で再ビルド（バイト再現性は #224 の方針に従う）。
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

# 決定論核（scripts/）を共有（rename_openai_to_script.py と同じ整合検証・参照追従）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from rename_openai_modules import (  # noqa: E402
    apply_rename_mapping,
    verify_flow_integrity,
)


def load_flow(path: Path) -> dict:
    """フロー JSON を読む（modules を持つ dict であること）。不正なら SystemExit。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise SystemExit(f"[ERROR] {path}: 読み込み/パース失敗: {e}")
    if not isinstance(data, dict) or not isinstance(data.get("modules"), dict):
        raise SystemExit(f"[ERROR] {path}: modules を持つフロー JSON ではありません")
    return data


def main() -> int:
    ap = argparse.ArgumentParser(
        description="巨大 bivr フロー JSON 内の 1 モジュールを決定論パッチ（issue #319）")
    ap.add_argument("--flow", required=True, help="対象のフロー JSON ファイル")
    ap.add_argument("--module", required=True, help="パッチ対象のモジュール名")
    ap.add_argument("--set-type", help="module.type を差し替え")
    ap.add_argument("--set-params-json", help="module.params を FILE の JSON で丸ごと置換")
    ap.add_argument("--set-script", help="module.params.script = FILE の内容")
    ap.add_argument("--set-param", nargs=2, action="append", metavar=("KEY", "VALUE"),
                    help="module.params[KEY] = VALUE（反復可）")
    ap.add_argument("--rename", help="モジュール名を変更し全参照を追従")
    ap.add_argument("--output", help="出力先 JSON（省略時は上書き）")
    ap.add_argument("--dry-run", action="store_true", help="変更内容を表示するだけで書き込まない")
    ap.add_argument("--allow-dangling", action="store_true",
                    help="パッチ後にダングリング参照が残っても exit 0（既定は exit 1）")
    args = ap.parse_args()

    flow_path = Path(args.flow)
    if not flow_path.exists():
        raise SystemExit(f"[ERROR] パスが存在しません: {flow_path}")

    has_op = any([args.set_type, args.set_params_json, args.set_script,
                  args.set_param, args.rename])
    if not has_op:
        raise SystemExit("[ERROR] 操作が 1 つも指定されていません（--set-type/--set-params-json/"
                         "--set-script/--set-param/--rename のいずれか）")

    data = load_flow(flow_path)
    modules = data["modules"]
    name = args.module
    if name not in modules:
        raise SystemExit(f"[ERROR] モジュール '{name}' がフロー内に存在しません "
                         f"（modules 数={len(modules)}）")
    mod = modules[name]
    if not isinstance(mod, dict):
        raise SystemExit(f"[ERROR] モジュール '{name}' が dict ではありません")

    changes = []

    # 1. type 差し替え
    if args.set_type:
        old = mod.get("type", "")
        mod["type"] = args.set_type
        changes.append(f"type: {old!r} → {args.set_type!r}")

    # 2. params 丸ごと置換（OpenAI 残骸パラメータ一掃）→ 以降の set-script/set-param が上書き
    if args.set_params_json:
        pf = Path(args.set_params_json)
        try:
            new_params = json.loads(pf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise SystemExit(f"[ERROR] --set-params-json 読込失敗 {pf}: {e}")
        if not isinstance(new_params, dict):
            raise SystemExit("[ERROR] --set-params-json の中身は JSON オブジェクトである必要があります")
        mod["params"] = new_params
        changes.append(f"params: 丸ごと置換（{len(new_params)} キー）")

    if not isinstance(mod.get("params"), dict):
        mod["params"] = {}

    # 3. script 本文注入
    if args.set_script:
        sf = Path(args.set_script)
        try:
            body = sf.read_text(encoding="utf-8")
        except OSError as e:
            raise SystemExit(f"[ERROR] --set-script 読込失敗 {sf}: {e}")
        mod["params"]["script"] = body
        changes.append(f"params.script: {sf}（{len(body)} 文字）を注入")

    # 4. 個別 param
    for key, value in (args.set_param or []):
        mod["params"][key] = value
        changes.append(f"params[{key!r}] = {value!r}")

    # 5. 改名＋参照追従（最後＝これまでの差替を新名に載せる）
    if args.rename:
        new_name = args.rename
        if new_name != name and new_name in modules:
            raise SystemExit(f"[ERROR] 改名先 '{new_name}' は既に存在します（衝突）")
        applied = apply_rename_mapping(data, {name: new_name})
        changes.append(f"rename: {name!r} → {new_name!r}（参照追従 {len(applied)} 種）")
        name = new_name

    print(f"[patch_flow_module] {flow_path.name} / module={args.module}", file=sys.stderr)
    for c in changes:
        print(f"    {c}", file=sys.stderr)

    if args.dry_run:
        print("  (--dry-run: 書き込みなし)", file=sys.stderr)
    else:
        out = Path(args.output) if args.output else flow_path
        # パイプライン中間 JSON の慣習に合わせコンパクト出力（Brekeke/build_bivr と整合）
        out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                       encoding="utf-8")
        print(f"  → 保存: {out}", file=sys.stderr)

    # 整合性検証（手動パッチはパイプラインの validator/auto_fixer を通らないため機械検証必須）
    report = verify_flow_integrity(data)
    residue, dangling = report["residue"], report["dangling"]
    if residue:
        print(f"  [WARN] OpenAI_*/openAI_* 命名のまま残る @General$Script {len(residue)} 件"
              f"（→ --rename で script_ 化推奨）: {', '.join(residue)}", file=sys.stderr)
    if dangling:
        print(f"  [NG] ダングリング参照 {len(dangling)} 件（実在しない先を指す）:", file=sys.stderr)
        for d in dangling:
            print(f"    {d['module']}.{d['field']} → '{d['target']}'", file=sys.stderr)
        if not args.allow_dangling:
            print("  整合性 NG のため exit 1（--allow-dangling で警告のみに）", file=sys.stderr)
            return 1
    else:
        print("  [verify] ダングリング参照なし", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
