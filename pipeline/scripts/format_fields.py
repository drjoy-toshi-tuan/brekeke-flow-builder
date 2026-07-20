#!/usr/bin/env python3
"""
format_fields.py — saveContextModel2DB の fields を自動整形するスクリプト

LLMがminified（1行）で出力した fields を、インデント付きJSON文字列に変換する。
Brekeke側ではminifiedでも動作するが、フローデザイナーでの目視確認が困難になるため
このスクリプトで後処理として整形する。

使い方:
    python3 scripts/format_fields.py output/draft_〇〇病院_診療.json
    python3 scripts/format_fields.py output/*.json
"""

import json
import sys
import os


def format_fields_in_flow(file_path: str) -> bool:
    """フローJSON内のsaveContextModel2DBのfieldsをインデント付きに整形する。

    Returns:
        True if any fields were reformatted, False otherwise.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "modules" not in data:
        return False

    changed = False
    for mod_name, mod in data["modules"].items():
        mod_type = mod.get("type", "")
        if "saveContextModel2DB" not in mod_type:
            continue

        params = mod.get("params", {})
        if not isinstance(params, dict):
            continue

        fields_str = params.get("fields", "")
        if not fields_str or not isinstance(fields_str, str):
            continue

        # 既にインデント付きならスキップ
        if "\n" in fields_str:
            continue

        # minifiedなfieldsをパースしてインデント付きに変換
        try:
            fields_obj = json.loads(fields_str)
            formatted = json.dumps(fields_obj, ensure_ascii=False, indent=2)
            params["fields"] = formatted
            changed = True
            print(f"  [FORMATTED] {mod_name}.params.fields ({len(fields_str)} chars -> {len(formatted)} chars)")
        except json.JSONDecodeError as e:
            print(f"  [ERROR] {mod_name}.params.fields のパースに失敗: {e}")

    if changed:
        # フローJSON全体をminified形式で書き戻す（fields内のインデントは文字列として保持される）
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        print(f"  -> {file_path} を更新しました")

    return changed


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/format_fields.py <flow.json> [flow2.json ...]")
        print("       python3 scripts/format_fields.py output/*.json")
        sys.exit(1)

    files = [f for f in sys.argv[1:] if not f.startswith("--")]
    total_formatted = 0

    for file_path in files:
        if not os.path.exists(file_path):
            print(f"[WARN] ファイルが見つかりません: {file_path}")
            continue

        print(f"[CHECK] {file_path}")
        if format_fields_in_flow(file_path):
            total_formatted += 1
        else:
            print(f"  -> 整形不要（既にインデント付き or 対象モジュールなし）")

    print(f"\n完了: {total_formatted}/{len(files)} ファイルを整形しました")


if __name__ == "__main__":
    main()
