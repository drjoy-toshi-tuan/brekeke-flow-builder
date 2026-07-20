#!/usr/bin/env python3
"""
P1+1 パイプライン — Step 1: flow-draft MD テーブル → YAML スケルトン生成

flow-draft skill が出力した構造ドラフト MD（| # | step | block type | 条件 → next | メモ |）を
読み込み、scenario_flow ブロック構造を決定論的に組み立てた YAML スケルトンを生成する。
TTS 文言・context 名・ラベル名等の「文言系」は {PLACEHOLDER_*} として残す。
後続の yaml_fill_placeholders.py（Sonnet エージェント）が customer_doc を参照して埋める。

Usage:
    python3 tools/yaml_scaffold_template.py \\
        --flow-draft <path_to_flow_draft_md> \\
        --facility <施設名> \\
        --flow <フロー名> \\
        [--output <output_yaml_path>]

Output:
    output/scenarios/{facility}_{flow}/設計書_{facility}_{flow}_skeleton.yaml
    (--output 未指定時は上記パスに自動出力)
"""

import argparse
import re
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent


# ── MD テーブルパーサー ──────────────────────────────────────────────────────

def parse_flow_draft_table(md_text: str) -> list[dict]:
    """flow-draft MD の「ステップ一覧」テーブルを行ごとに辞書リストに変換する。"""
    steps = []
    in_table = False
    header_done = False

    for line in md_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                in_table = False  # テーブル終了
            continue

        # ヘッダ行検出: "step" と "block type" を両方含む
        if "step" in stripped.lower() and "block" in stripped.lower():
            in_table = True
            header_done = False
            continue

        if in_table and not header_done:
            # セパレーター行 |---|---|...
            header_done = True
            continue

        if in_table and header_done:
            # split by | → strip each cell
            # 先頭・末尾の空セル（パイプ外側）のみ除去、内部の空セルは保持
            all_cols = [c.strip() for c in stripped.split("|")]
            if all_cols and all_cols[0] == "":
                all_cols = all_cols[1:]
            if all_cols and all_cols[-1] == "":
                all_cols = all_cols[:-1]
            cols = all_cols
            if len(cols) < 3:
                continue
            steps.append({
                "num": cols[0],
                "step": cols[1],
                "block_type_raw": cols[2],
                "conditions_raw": cols[3] if len(cols) > 3 else "",
                "memo": cols[4] if len(cols) > 4 else "",
            })

    return steps


def parse_block_type(raw: str) -> dict:
    """block type 列文字列をパースして type, slot, script_template, output_format などを返す。"""
    raw = raw.strip()
    result: dict = {}

    # slot: patient_name / date_of_birth / phone / card_number
    m = re.match(r"slot\s*:\s*(\S+)", raw, re.I)
    if m:
        result["type"] = "slot"
        result["slot"] = re.sub(r"[()⚠️ ].*$", "", m.group(1)).strip()
        return result

    # patient_name / dob / phone / card_number (ファーストクラスエイリアス)
    if re.match(r"^(patient_name|dob|phone|card_number)$", raw, re.I):
        result["type"] = raw.lower()
        return result

    # script (A: xxx) / script (template: xxx) / script: xxx
    m = re.match(r"script\s*[\(:].*?(?:template:|A:)\s*([\w_]+)", raw, re.I)
    if m:
        result["type"] = "script"
        result["script_template"] = m.group(1)
        return result
    if re.match(r"^script$", raw.strip().lower()):
        result["type"] = "script"
        result["script_template"] = "{PLACEHOLDER_SCRIPT_TEMPLATE}"
        return result

    # hearing (enum) / hearing (text) / hearing (datetime) / hearing (number)
    m = re.match(r"hearing\s*\(([^)]+)\)", raw, re.I)
    if m:
        fmt = m.group(1).strip().lower()
        result["type"] = "hearing"
        result["output_format"] = fmt if fmt in ("text", "datetime", "enum", "number") else "enum"
        return result
    if re.match(r"^hearing$", raw.strip().lower()):
        result["type"] = "hearing"
        result["output_format"] = "enum"
        return result

    # 既知の単純型
    SIMPLE_TYPES = [
        "opening", "announcement", "termination", "call_transfer",
        "context_match_router", "cmr_chain", "null_check", "free_text",
        "intent", "faq", "augment", "subflow",
        "incoming_category_classifier", "phone2name", "phone_branch",
        "clinical_department", "clinical_department_normalize",
        "clinical_department_classifier",
    ]
    raw_lower = raw.lower().split()[0].rstrip("(,:")
    for t in SIMPLE_TYPES:
        if raw_lower == t:
            result["type"] = t
            return result

    # fallback: augment
    result["type"] = raw_lower if raw_lower else "augment"
    return result


def parse_conditions(raw: str) -> list[dict]:
    """「条件 → next」列をパースして conditions リストを返す。"""
    raw = raw.strip()
    if not raw:
        return []

    # 単純な → next（直接遷移・分岐なし）
    if re.match(r"^→\s*\S", raw) and "/" not in raw:
        next_step = raw.lstrip("→").strip()
        return [{"_direct": True, "next": next_step}]

    # 複数分岐: X→Y / Z→W / ...
    conditions = []
    parts = [p.strip() for p in raw.split("/")]
    for part in parts:
        if "→" in part:
            match_raw, next_raw = part.split("→", 1)
            conditions.append({
                "match": match_raw.strip(),
                "next": next_raw.strip(),
            })
    return conditions


def get_direct_next(conditions: list[dict]) -> str | None:
    """直接遷移（1条件で _direct=True）なら next を返す。"""
    if len(conditions) == 1 and conditions[0].get("_direct"):
        return conditions[0]["next"]
    return None


# ── YAML スケルトン生成 ───────────────────────────────────────────────────────

def generate_yaml_skeleton(steps: list[dict], facility: str, flow: str) -> str:
    lines: list[str] = []

    lines += [
        f"# 設計書スケルトン — {facility} {flow}",
        f"# 生成元: P1+1 tools/yaml_scaffold_template.py",
        f"# 生成日: {{PLACEHOLDER_DATE}}",
        f"# 備考: {{PLACEHOLDER_*}} は yaml_fill_placeholders エージェント (Sonnet) が埋める",
        f'version: "1.0"',
        "",
        "# --- セクション1: 基本情報 ---",
        "basic_info:",
        f'  facility_name: "{facility}"',
        '  group_name: "{PLACEHOLDER_GROUP_NAME}"',
        '  flow_name: "{PLACEHOLDER_FLOW_NAME}"',
        '  target_facility: "{PLACEHOLDER_TARGET_FACILITY}"',
        '  office_id: "TODO_要確認"',
        '  phone_number: "{PLACEHOLDER_PHONE_NUMBER}"',
        '  business_hours: "{PLACEHOLDER_BUSINESS_HOURS}"',
        '  flow_type: "1flow"',
        '  work_type: "new_build"',
        '  environment: "demo"',
        "",
        "# --- セクション3: フローの目的 ---",
        'purpose: "{PLACEHOLDER_PURPOSE}"',
        "",
        "# --- セクション4c: シナリオフロー定義（ブロック構成）---",
        "scenario_flow:",
    ]

    termination_steps: list[str] = []
    hearing_steps: list[tuple[str, str]] = []  # (step_name, output_format)
    has_transfer = False

    for s in steps:
        binfo = parse_block_type(s["block_type_raw"])
        conditions = parse_conditions(s["conditions_raw"])
        direct_next = get_direct_next(conditions)
        btype = binfo.get("type", "augment")
        step_name = s["step"]
        memo = s["memo"].strip()

        if memo:
            lines.append(f"  # {memo}")
        lines.append(f"  - step: {step_name}")
        lines.append(f"    type: {btype}")

        if btype == "opening":
            lines.append("    use_acceptance_times: true")
            lines.append(f"    next: {direct_next or '{PLACEHOLDER_NEXT}'}")

        elif btype == "announcement":
            lines.append(f"    next: {direct_next or '{PLACEHOLDER_NEXT}'}")

        elif btype == "hearing":
            output_format = binfo.get("output_format", "enum")
            lines.append(f"    output_format: {output_format}")
            if output_format == "enum":
                labels = [
                    c["match"] for c in conditions
                    if not c.get("_direct") and c.get("match") not in ("other", "NO_RESULT")
                ]
                if labels:
                    choices_str = "[" + ", ".join(f'"{l}"' for l in labels) + "]"
                    lines.append(f"    choices: {choices_str}")
                else:
                    lines.append("    choices: {PLACEHOLDER_CHOICES}")
            lines.append('    save_to: "{PLACEHOLDER_SAVE_TO}"')
            if direct_next:
                lines.append(f"    next: {direct_next}")
            else:
                lines.append("    retry_failure: {PLACEHOLDER_RETRY_FAILURE}")
            hearing_steps.append((step_name, output_format))

        elif btype == "slot":
            slot_val = binfo.get("slot", "{PLACEHOLDER_SLOT}")
            lines.append(f"    slot: {slot_val}")
            lines.append(f"    next: {direct_next or '{PLACEHOLDER_NEXT}'}")

        elif btype in ("patient_name", "dob", "phone", "card_number"):
            lines.append(f"    next: {direct_next or '{PLACEHOLDER_NEXT}'}")

        elif btype == "script":
            tmpl = binfo.get("script_template", "{PLACEHOLDER_SCRIPT_TEMPLATE}")
            lines.append(f"    script_template: {tmpl}")
            if conditions and not direct_next:
                lines.append("    conditions:")
                for c in conditions:
                    if c.get("_direct"):
                        continue
                    lines.append(f'      - match: "{c["match"]}"')
                    lines.append(f'        next: {c["next"]}')
                # ensure 'other'
                if not any(c.get("match") == "other" for c in conditions):
                    lines.append('      - match: "other"')
                    lines.append("        next: {PLACEHOLDER_OTHER_NEXT}")
            elif direct_next:
                lines.append(f"    next: {direct_next}")

        elif btype == "context_match_router":
            lines.append('    reference_module: "{PLACEHOLDER_REFERENCE_MODULE}"')
            if conditions and not direct_next:
                lines.append("    conditions:")
                for c in conditions:
                    if c.get("_direct"):
                        continue
                    lines.append(f'      - match: "{c["match"]}"')
                    lines.append(f'        next: {c["next"]}')
                if not any(c.get("match") == "other" for c in conditions):
                    lines.append('      - match: "other"')
                    lines.append("        next: {PLACEHOLDER_OTHER_NEXT}")

        elif btype == "cmr_chain":
            lines.append('    reference_module: "{PLACEHOLDER_REFERENCE_MODULE}"')
            if conditions and not direct_next:
                lines.append("    conditions:")
                for c in conditions:
                    if c.get("_direct"):
                        continue
                    lines.append(f'      - match: "{c["match"]}"')
                    lines.append(f'        next: {c["next"]}')

        elif btype == "termination":
            lines.append(f'    termination_ref: "{step_name}"')
            termination_steps.append(step_name)

        elif btype == "call_transfer":
            lines.append('    transfer_type: "Blind Transfer"')
            lines.append('    on_failure_announcement: "{PLACEHOLDER_TRANSFER_FAILURE_TTS}"')
            has_transfer = True

        elif btype == "subflow":
            lines.append('    flowname: "{PLACEHOLDER_FLOWNAME}"')
            lines.append(f"    next: {direct_next or '{PLACEHOLDER_NEXT}'}")

        elif btype in ("free_text",):
            lines.append('    save_to: "{PLACEHOLDER_SAVE_TO}"')
            lines.append(f"    next: {direct_next or '{PLACEHOLDER_NEXT}'}")

        elif btype == "null_check":
            if conditions and not direct_next:
                lines.append("    conditions:")
                for c in conditions:
                    if c.get("_direct"):
                        continue
                    lines.append(f'      - match: "{c["match"]}"')
                    lines.append(f'        next: {c["next"]}')

        else:
            # generic: 分岐 or 直接遷移
            if direct_next:
                lines.append(f"    next: {direct_next}")
            elif conditions:
                lines.append("    conditions:")
                for c in conditions:
                    if c.get("_direct"):
                        continue
                    lines.append(f'      - match: "{c["match"]}"')
                    lines.append(f'        next: {c["next"]}')

        lines.append("")

    # ── セクション5: コンテキストフィールド ──────────────────────────────────
    lines += [
        "# --- セクション5: コンテキストフィールド一覧（saveContextModel2DB 用）---",
        "# PLACEHOLDER: yaml_fill_placeholders が customer_doc を参照して全量定義する",
        "context_fields:",
        '  - context_name: "{PLACEHOLDER_CTX_NAME}"',
        '    context_name_jp: "{PLACEHOLDER_CTX_NAME_JP}"',
        '    display_type: "{PLACEHOLDER_DISPLAY_TYPE}"',
        "    range_values: []",
        "    item_default: true",
        "    editable: true",
        "    deletable: true",
        '    notes: "{PLACEHOLDER_NOTES}"',
        "",
    ]

    # ── セクション6: 聴取項目一覧 ────────────────────────────────────────────
    if hearing_steps:
        lines += [
            "# --- セクション6: 聴取項目一覧 ---",
            "hearing_items:",
        ]
        for i, (hname, hfmt) in enumerate(hearing_steps, 1):
            lines += [
                f"  - order: {i}",
                f'    name: "{hname}"',
                '    stt_type: "{PLACEHOLDER_STT_TYPE}"',
                "    retry_count: 2",
                "    echo_back: false",
                '    save_to: "{PLACEHOLDER_SAVE_TO}"',
                '    openai_processing: "{PLACEHOLDER_OAI_TYPE}"',
                f'    output_format: "{hfmt}"',
                "    output_labels: {PLACEHOLDER_LABELS}",
                '    notes: "{PLACEHOLDER_NOTES}"',
                "",
            ]

    # ── セクション7: ステップ詳細（TTS 文言）────────────────────────────────
    tts_blocks = [s for s in steps
                  if parse_block_type(s["block_type_raw"]).get("type") in
                  ("announcement", "hearing", "opening", "call_transfer")]
    if tts_blocks:
        lines += [
            "# --- セクション7: ステップ詳細（TTS文言等）---",
            "# PLACEHOLDER: yaml_fill_placeholders が customer_doc を参照して全量記述する",
            "step_details:",
        ]
        for s in tts_blocks:
            btype = parse_block_type(s["block_type_raw"]).get("type")
            lines += [
                f"  - step: {s['step']}",
                '    announcement: "{PLACEHOLDER_TTS}"',
                "",
            ]

    # ── セクション8: 終話パターン ─────────────────────────────────────────────
    if termination_steps:
        lines += [
            "# --- セクション8: 終話パターン ---",
            "termination_patterns:",
        ]
        for tname in termination_steps:
            lines += [
                f'  - name: "{tname}"',
                '    announcement: "{PLACEHOLDER_TTS}"',
                '    status: "{PLACEHOLDER_STATUS}"',
                '    sms_flag: "{PLACEHOLDER_SMS_FLAG}"',
                "",
            ]

    return "\n".join(lines)


# ── エントリポイント ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="flow-draft MD → YAML スケルトン生成 (P1+1 Step 1)")
    parser.add_argument("--flow-draft", required=True, help="flow-draft MD ファイルのパス")
    parser.add_argument("--facility", required=True, help="施設名（例: すずな皮ふ科）")
    parser.add_argument("--flow", required=True, help="フロー名（例: 診療）")
    parser.add_argument("--output", help="出力 YAML パス（省略時: output/scenarios/{facility}_{flow}/設計書_{facility}_{flow}_skeleton.yaml）")
    args = parser.parse_args()

    flow_draft_path = Path(args.flow_draft)
    if not flow_draft_path.exists():
        print(f"ERROR: flow-draft ファイルが見つかりません: {flow_draft_path}", file=sys.stderr)
        sys.exit(1)

    md_text = flow_draft_path.read_text(encoding="utf-8", errors="replace")
    steps = parse_flow_draft_table(md_text)

    if not steps:
        print("ERROR: flow-draft MD からステップを読み取れませんでした。", file=sys.stderr)
        print("テーブルヘッダ行に 'step' と 'block' の両語が含まれているか確認してください。", file=sys.stderr)
        sys.exit(1)

    print(f"INFO: {len(steps)} ステップを読み取りました", file=sys.stderr)

    yaml_text = generate_yaml_skeleton(steps, args.facility, args.flow)

    if args.output:
        out_path = Path(args.output)
    else:
        scenario_dir = PROJECT_DIR / "output" / "scenarios" / f"{args.facility}_{args.flow}"
        scenario_dir.mkdir(parents=True, exist_ok=True)
        out_path = scenario_dir / f"設計書_{args.facility}_{args.flow}_skeleton.yaml"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml_text, encoding="utf-8")
    print(f"OK: スケルトン YAML を出力しました → {out_path}", file=sys.stderr)
    # stdout に出力パスを返す（orchestrator が参照するため）
    print(str(out_path))


if __name__ == "__main__":
    main()
