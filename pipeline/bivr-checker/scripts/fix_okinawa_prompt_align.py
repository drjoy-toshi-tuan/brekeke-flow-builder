#!/usr/bin/env python3
"""
fix_okinawa_prompt_align.py — PROMPT-001 修正スクリプト

沖縄県立南部医療センター_診療_20260415.json の OpenAI モジュールにおいて、
プロンプトの出力仕様セクションのフォーマットを修正し、
validator の PROMPT-001 チェックをパスさせる。

問題: 出力仕様セクションの行が「- 肯定：説明文」形式になっており、
validator が行全体をラベルとして抽出するため、next[] の condition 値と一致しない。

修正: 「- 肯定：説明文」→ 説明文を括弧付きの補足に変更するのではなく、
出力仕様の箇条書きを「- 値」のみに変更し、説明は別行に移す。
"""

import json
import re
import sys
import os

INPUT_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output",
    "沖縄県立南部医療センター_診療_20260415.json"
)

# Target modules and their expected output values (from next[] conditions)
TARGET_MODULES = {
    "openAI_用件確認_復唱": ["肯定", "否定"],
    "OpenAI_紹介状確認": ["はい", "いいえ"],
    "OpenAI_薬服用中か_変更": ["はい", "いいえ"],
    "OpenAI_薬残数確認_変更": ["あり", "なし"],
    "openAI_予約日_変更_復唱": ["肯定", "否定"],
    "OpenAI_薬服用中か_キャンセル": ["はい", "いいえ"],
    "OpenAI_薬残数確認_キャンセル": ["あり", "なし"],
    "openAI_予約日_キャンセル_復唱": ["肯定", "否定"],
}


def extract_output_spec_lines(prompt: str):
    """出力仕様セクション内の箇条書き行を抽出してインデックスとともに返す"""
    lines = prompt.split("\n")
    in_output_section = False
    results = []  # (line_index, original_line)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^#.*出力', stripped):
            in_output_section = True
            continue
        if in_output_section and stripped.startswith("#") and "出力" not in stripped:
            in_output_section = False
            continue
        if in_output_section:
            if re.match(r'^-{2,}$', stripped):
                continue
            m = re.match(r'^[-\*]\s+(.+?)$', stripped)
            if m:
                results.append((i, line))
    return results


def fix_output_spec_line(line: str, expected_values: list) -> str:
    """
    出力仕様の1行を修正する。

    Before: - 肯定：ユーザーが復唱内容を承認した場合（はい / ええ / そうです / 合ってます / 大丈夫 / お願いします 等）
    After:  - 肯定

    説明文は削除（判定アルゴリズムとFew-Shotに記載済みのため冗長）
    """
    stripped = line.strip()
    m = re.match(r'^([-\*]\s+)(.+)$', stripped)
    if not m:
        return line

    prefix = m.group(1)  # "- "
    content = m.group(2)  # "肯定：..." or "NO_RESULT：..."

    # Extract the label (before : or ：)
    label_match = re.match(r'^([^：:]+)[：:]', content)
    if label_match:
        label = label_match.group(1).strip()
    else:
        label = content.strip()

    # Only modify lines whose label matches an expected value or is NO_RESULT
    if label in expected_values or label == "NO_RESULT":
        # Preserve leading whitespace from original line
        leading_ws = ""
        for ch in line:
            if ch in (' ', '\t'):
                leading_ws += ch
            else:
                break
        return f"{leading_ws}{prefix}{label}"

    return line


def fix_prompt(prompt: str, expected_values: list, module_name: str) -> tuple:
    """プロンプトの出力仕様セクションを修正し、(修正後prompt, 変更情報)を返す"""
    lines = prompt.split("\n")
    spec_lines = extract_output_spec_lines(prompt)

    changes = []
    for line_idx, original_line in spec_lines:
        new_line = fix_output_spec_line(original_line, expected_values)
        if new_line != original_line:
            # Extract old label for reporting
            old_m = re.match(r'^[-\*]\s+(.+?)$', original_line.strip())
            new_m = re.match(r'^[-\*]\s+(.+?)$', new_line.strip())
            old_label = old_m.group(1) if old_m else original_line.strip()
            new_label = new_m.group(1) if new_m else new_line.strip()
            changes.append({
                "line": line_idx,
                "old": old_label,
                "new": new_label,
            })
            lines[line_idx] = new_line

    return "\n".join(lines), changes


def main():
    print(f"=== PROMPT-001 修正: 沖縄県立南部医療センター_診療 ===\n")

    # Load JSON
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    modules = data.get("modules", {})
    total_changes = 0

    for mod_name, expected_values in TARGET_MODULES.items():
        if mod_name not in modules:
            print(f"[SKIP] {mod_name}: モジュールが見つかりません")
            continue

        mod = modules[mod_name]
        prompt = mod.get("params", {}).get("prompt", "")
        if not prompt:
            print(f"[SKIP] {mod_name}: promptが空")
            continue

        # Get actual next conditions for verification
        next_conditions = []
        for n in mod.get("next", []):
            c = n.get("condition", "")
            if c and c not in ["^TIMEOUT$", "^ERROR$", "^NO_RESULT$", "", "^.*$", "^.+$"]:
                next_conditions.append(c.strip("^").rstrip("$"))

        print(f"--- {mod_name} ---")
        print(f"  next[] conditions: {next_conditions}")

        new_prompt, changes = fix_prompt(prompt, expected_values, mod_name)

        if changes:
            for ch in changes:
                print(f"  [FIX] 出力仕様 line {ch['line']}:")
                print(f"    BEFORE: {ch['old'][:80]}{'...' if len(ch['old']) > 80 else ''}")
                print(f"    AFTER:  {ch['new']}")
            mod["params"]["prompt"] = new_prompt
            total_changes += len(changes)
        else:
            print(f"  [OK] 変更不要")
        print()

    # Save
    if total_changes > 0:
        with open(INPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"=== 完了: {total_changes} 箇所修正、ファイル保存済み ===")
    else:
        print("=== 変更なし ===")

    return total_changes


if __name__ == "__main__":
    changes = main()
    sys.exit(0 if changes >= 0 else 1)
