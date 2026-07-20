#!/usr/bin/env python3
"""properties_from_json.py — 既存 BIVR/JSON のインラインプロンプトから properties ファイルを生成

Pattern 2 (既存修正) で、fixer_modify 後の JSON にインライン記述された
TTS プロンプトを抽出して properties .md ファイルを出力する。

Pattern 2 は scaffold を走らせないため gen_properties.py の通常経路では
tts_modules リストが得られず、properties が生成されない。本スクリプトは
JSON 側の inline prompt を転記してその穴を埋める。

Usage:
    python3 scripts/properties_from_json.py <json_path> [-o output_path]

抽出対象:
- type が Text To Speech を含む全モジュール（ただし Re-confirmation node data は除外 = P-010 対象外）
- params.prompt が空でないもの
- 追加で call_transfer の dialNumber 等、プロパティで管理すべき値があれば追記
"""

import argparse
import json
import re
import sys
from pathlib import Path


def extract_properties(json_path: Path) -> tuple[list[str], list[str]]:
    """JSON からプロパティ行と TODO モジュールリストを抽出。"""
    data = json.loads(json_path.read_text(encoding="utf-8"))
    modules = data.get("modules", {})

    lines: list[str] = []
    todo: list[str] = []

    for name, mod in modules.items():
        if not isinstance(mod, dict):
            continue
        mod_type = mod.get("type", "")
        params = mod.get("params", {}) if isinstance(mod.get("params"), dict) else {}

        # TTS モジュール（ただし Re-confirmation node data は除外）
        if "Text To Speech" in mod_type and "Re-confirmation node data" not in mod_type:
            prompt = params.get("prompt", "") or ""
            prompt = prompt.strip()
            if prompt:
                # 既に {tts_g:...} 形式ならそのまま、それ以外は包む
                if re.match(r'^\{tts_[ga]i?:', prompt):
                    lines.append(f"{name}.prompt={prompt}")
                else:
                    lines.append(f"{name}.prompt={{tts_g:{prompt}}}")
            else:
                lines.append(f"{name}.prompt={{tts_g:TODO_発話内容を記入}}")
                todo.append(name)

    return lines, todo


def main() -> None:
    parser = argparse.ArgumentParser(description="JSON インラインプロンプトから properties 生成")
    parser.add_argument("json_path", help="入力 JSON ファイルパス")
    parser.add_argument("-o", "--output", help="出力 .md パス（省略時は自動導出）")
    parser.add_argument("--env", default="prod", choices=["demo", "prod"], help="環境（ファイル名に使用）")
    args = parser.parse_args()

    json_path = Path(args.json_path)
    if not json_path.exists():
        print(f"Error: JSON が見つかりません: {json_path}", file=sys.stderr)
        sys.exit(1)

    lines, todo = extract_properties(json_path)

    if args.output:
        out_path = Path(args.output)
    else:
        stem = json_path.stem
        # prompted_XXX.json → properties_XXX.md に変換
        for prefix in ("prompted_", "reviewed_", "merged_", "draft_"):
            if stem.startswith(prefix):
                stem = stem[len(prefix):]
                break
        out_path = json_path.parent.parent / f"properties_{stem}.md"

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # properties ファイル書き出し（標準ヘッダー付き）
    body = [
        "# IVR Properties (Pattern 2: extracted from existing BIVR/JSON inline prompts)",
        f"# source: {json_path.name}",
        f"# env: {args.env}",
        "",
        *lines,
    ]
    if todo:
        body.append("")
        body.append("# TODO モジュール（インラインプロンプト空のため、発話文言を記入してください）")
        for name in todo:
            body.append(f"# - {name}")

    out_path.write_text("\n".join(body) + "\n", encoding="utf-8")

    print(f"[properties_from_json] 出力: {out_path}", file=sys.stderr)
    print(f"[properties_from_json] TTS 行: {len(lines)} / TODO: {len(todo)}", file=sys.stderr)
    print(str(out_path))  # stdout 最終行 = 出力パス（orchestrator 互換）


if __name__ == "__main__":
    main()
