#!/usr/bin/env python3
"""
format_prompt_strings.py -- OpenAI / Retry モジュールの文字列パラメータを正規化する

主な役割:
  1. generate_by_OpenAI モジュールの params.prompt 内のリテラル \\n を実改行 (LF) に置換
  2. Speech Retry Counter モジュールの params.prompt_true / prompt_false も同様に置換
  3. その他 prompt / promptTTS / context 系フィールドも対象

prompter エージェントが LLM ゆえ、改行を "\\n" のエスケープ記法のまま書き込む事故を防ぐ
後段の機械的正規化ステップ。副作用なしで何度実行しても安全。

Usage:
    python3 scripts/format_prompt_strings.py <json_path> [output_path]
    output_path 省略時は json_path を上書き。
"""

import json
import sys
from pathlib import Path


# 正規化対象のフィールド名（モジュールの params 以下で発見したら置換）
PROMPT_FIELDS = [
    "prompt", "promptTTS", "prompt_true", "prompt_false",
    "context",
]


def _normalize_string(s: str) -> str:
    """リテラルのエスケープ記法を実文字に置換"""
    if not isinstance(s, str):
        return s
    # リテラルの \n / \r / \t を実文字に
    # ※ 既に実改行を含む場合はそのまま（.replace は対象の \\n が無ければノーオペ）
    replaced = s
    replaced = replaced.replace("\\r\\n", "\n")  # CRLF リテラル → LF
    replaced = replaced.replace("\\n", "\n")
    replaced = replaced.replace("\\r", "\n")
    replaced = replaced.replace("\\t", "\t")
    return replaced


def normalize_modules(modules: dict) -> dict[str, int]:
    """modules 全体をスキャンしてプロンプト系フィールドを正規化。
    戻り値: {フィールド名: 置換発生件数}
    """
    stats: dict[str, int] = {}
    for mod_name, mod in modules.items():
        params = mod.get("params")
        if not isinstance(params, dict):
            continue
        for fld in PROMPT_FIELDS:
            val = params.get(fld)
            if not isinstance(val, str) or not val:
                continue
            new_val = _normalize_string(val)
            if new_val != val:
                params[fld] = new_val
                stats[fld] = stats.get(fld, 0) + 1
    return stats


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: format_prompt_strings.py <json_path> [output_path]", file=sys.stderr)
        sys.exit(1)

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"Error: {json_path} が見つかりません", file=sys.stderr)
        sys.exit(1)

    output_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else json_path

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    modules = data.get("modules", {})
    stats = normalize_modules(modules)

    if stats:
        details = ", ".join(f"{k}={v}" for k, v in stats.items())
        print(f"[format_prompt_strings] 正規化完了: {details}", file=sys.stderr)
    else:
        print("[format_prompt_strings] 正規化対象なし（全プロンプトが既に正しい改行）", file=sys.stderr)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    print(str(output_path))


if __name__ == "__main__":
    main()
