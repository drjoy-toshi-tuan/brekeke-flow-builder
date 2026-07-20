#!/usr/bin/env python3
"""
pw_analyzer.py — profile_words 分析スクリプト

フローJSON内の全STT/DTMFモジュールの profile_words の状態を分析し、
入力種別を判定し、対応が必要なモジュールのリストを出力する。

Usage:
    python scripts/pw_analyzer.py output/貝塚病院_健診_20260417.json [--output analysis.json]
"""

import json
import sys
import os
import argparse
import io

# --- Constants ---

STT_TYPE = "drjoy^AmiVoice$Speech to Text"
DTMF_TYPE = "drjoy^External Integration$DTMF AmiVoice STT Input"
TTS_TYPE = "drjoy^Text To Speech$Text to speech"
RETRY_TYPE = "drjoy^Text To Speech$Speech Retry Counter"
RECONFIRM_TYPE = "drjoy^Text To Speech$Re-confirmation node data"

FILLER_TOP6 = ["あ", "え", "えー", "あの", "はい", "ま"]
SUFFIX_TOP8 = ["です", "で", "なんですが", "になります", "ね", "さ", "でして", "か"]
HEAD_CLIP_PATTERNS = [
    # (original_start, clipped) — common head-clip pairs
    ("よやく", "やく"),
    ("へんこう", "んこう"),
    ("しょうわ", "ょうわ"),
    ("れいわ", "いわ"),
    ("へいせい", "いせい"),
    ("たいしょう", "いしょう"),
    ("いちがつ", "ちがつ"),
    ("にがつ", "がつ"),
    ("ついたち", "いたち"),
]

# Status thresholds
STATUS_THRESHOLDS = [
    (0, "empty"),
    (50, "insufficient"),
    (301, "adequate"),
    (float("inf"), "excessive"),
]

STATUS_LABELS = {
    "empty": ("EMPTY", "要生成", "generate", "生成推奨"),
    "insufficient": ("INSUF", "要拡充", "expand", "拡充推奨"),
    "adequate": ("OK", "OK", "none", ""),
    "excessive": ("EXCESS", "要調整", "reduce", "調整推奨"),
}

# Input type detection rules: (keywords_in_name_or_tts, input_type)
INPUT_TYPE_RULES = [
    (["用件", "ご用件"], "yoken"),
    (["生年月日", "お生まれ"], "dob"),
    (["氏名", "お名前", "名前"], "name"),
    (["診療科"], "department"),
    (["電話", "番号"], "phone"),
    (["コース", "健診", "ドック"], "kenshin_course"),
    (["日付", "予約日", "希望日", "時期"], "date"),
]

# yes_no is detected separately (needs confirmation context)
YES_NO_KEYWORDS = ["復唱", "よろしい", "正しい", "確認"]


def get_word_count(profile_words: str) -> int:
    """Count non-empty lines in profile_words."""
    if not profile_words:
        return 0
    return len([line for line in profile_words.split("\n") if line.strip()])


def get_status(word_count: int) -> str:
    """Determine status based on word count."""
    if word_count == 0:
        return "empty"
    elif word_count < 50:
        return "insufficient"
    elif word_count <= 300:
        return "adequate"
    else:
        return "excessive"


def build_reverse_map(modules: dict) -> dict:
    """Build reverse map: target_module -> list of (source_name, source_module)."""
    reverse = {}
    for name, mod in modules.items():
        for n in mod.get("next", []):
            target = n.get("nextModuleName", "")
            if target:
                if target not in reverse:
                    reverse[target] = []
                reverse[target].append((name, mod))
    return reverse


def find_preceding_tts(module_name: str, modules: dict, reverse_map: dict, depth: int = 0) -> tuple:
    """
    Find the preceding TTS module for a given STT/DTMF module.
    Returns (tts_prompt, tts_module_name) or ("", "") if not found.
    Follows Retry -> TTS chain up to 3 levels.
    """
    if depth > 5:
        return ("", "")

    sources = reverse_map.get(module_name, [])
    for src_name, src_mod in sources:
        src_type = src_mod.get("type", "")

        if src_type == TTS_TYPE:
            prompt = src_mod.get("params", {}).get("prompt", "")
            return (prompt, src_name)

        if src_type == RECONFIRM_TYPE:
            prompt = src_mod.get("params", {}).get("prompt", "")
            return (prompt, src_name)

        if src_type == RETRY_TYPE:
            # Retry's true branch points to TTS, follow the chain
            prompt_true = src_mod.get("params", {}).get("prompt_true", "")
            # Also look for the TTS that the Retry points to (via its 'true' next)
            for n in src_mod.get("next", []):
                if n.get("label") == "Retry" or n.get("condition") == "true":
                    retry_target = n.get("nextModuleName", "")
                    if retry_target and retry_target in modules:
                        target_mod = modules[retry_target]
                        if target_mod.get("type") == TTS_TYPE:
                            prompt = target_mod.get("params", {}).get("prompt", "")
                            return (prompt, retry_target)
                        else:
                            # Follow further
                            return find_preceding_tts(retry_target, modules, reverse_map, depth + 1)
            # If Retry itself is the source, try to find what points to it
            return find_preceding_tts(src_name, modules, reverse_map, depth + 1)

    return ("", "")


def has_yes_no_branches(module_name: str, modules: dict) -> bool:
    """Check if the module's downstream OpenAI has affirmative/negative branches."""
    mod = modules.get(module_name, {})
    # Look at the success next module
    for n in mod.get("next", []):
        target_name = n.get("nextModuleName", "")
        if not target_name:
            continue
        target_mod = modules.get(target_name, {})
        target_type = target_mod.get("type", "")
        if "generate_by_OpenAI" in target_type:
            # Check its branches for yes/no patterns
            for on in target_mod.get("next", []):
                cond = on.get("condition", "")
                label = on.get("label", "")
                combined = cond + label
                if any(k in combined for k in ["はい", "いいえ", "肯定", "否定", "yes", "no", "確認OK", "OK", "NG"]):
                    return True
    return False


def detect_input_type(module_name: str, tts_prompt: str, tts_name: str, modules: dict) -> str:
    """Detect input type from module name, TTS prompt, and TTS name."""
    # Combine search text
    search_text = module_name + " " + tts_prompt + " " + tts_name

    # Check yes_no first (needs branch check)
    if any(k in search_text for k in YES_NO_KEYWORDS):
        if has_yes_no_branches(module_name, modules) or any(k in search_text for k in ["復唱", "よろしい"]):
            return "yes_no"

    # Check other rules in order
    for keywords, input_type in INPUT_TYPE_RULES:
        if any(k in search_text for k in keywords):
            return input_type

    return "freetext"


def analyze_fillers(profile_words: str) -> tuple:
    """Analyze filler/suffix/head-clip presence in profile_words."""
    if not profile_words:
        return (False, False, False)

    lines = [line.strip() for line in profile_words.split("\n") if line.strip()]
    if not lines:
        return (False, False, False)

    filler_count = 0
    suffix_count = 0
    head_clip_found = False

    all_yomi = []
    for line in lines:
        parts = line.split(" ", 1)
        yomi = parts[1] if len(parts) == 2 else parts[0]
        all_yomi.append(yomi)

        # Check fillers
        for f in FILLER_TOP6:
            if yomi.startswith(f) and yomi != f:
                filler_count += 1
                break

        # Check suffixes
        for s in SUFFIX_TOP8:
            if yomi.endswith(s) and yomi != s:
                suffix_count += 1
                break

    # Check head-clip patterns
    yomi_set = set(all_yomi)
    for full, clipped in HEAD_CLIP_PATTERNS:
        if clipped in yomi_set:
            head_clip_found = True
            break

    # Also check for same-hyouki with different-length yomi (generic head-clip detection)
    if not head_clip_found:
        hyouki_yomis = {}
        for line in lines:
            parts = line.split(" ", 1)
            if len(parts) == 2:
                hyouki, yomi = parts
                if hyouki not in hyouki_yomis:
                    hyouki_yomis[hyouki] = []
                hyouki_yomis[hyouki].append(yomi)
        for hyouki, yomis in hyouki_yomis.items():
            if len(yomis) > 1:
                longest = max(yomis, key=len)
                for y in yomis:
                    if y != longest and longest.endswith(y):
                        head_clip_found = True
                        break
            if head_clip_found:
                break

    has_fillers = filler_count > 0
    has_suffixes = suffix_count > 0

    return (has_fillers, has_suffixes, head_clip_found)


def analyze_flow(flow_data: dict) -> dict:
    """Analyze a single flow JSON."""
    flow_name = flow_data.get("name", "unknown")
    modules = flow_data.get("modules", {})
    reverse_map = build_reverse_map(modules)

    results = []
    stt_count = 0
    dtmf_count = 0

    for mod_name, mod_data in modules.items():
        mod_type = mod_data.get("type", "")

        if mod_type == STT_TYPE:
            type_label = "STT"
            stt_count += 1
        elif mod_type == DTMF_TYPE:
            type_label = "DTMF"
            dtmf_count += 1
        else:
            continue

        params = mod_data.get("params", {})
        pw = params.get("profile_words", "")
        word_count = get_word_count(pw)
        status = get_status(word_count)

        # Find preceding TTS
        tts_prompt, tts_name = find_preceding_tts(mod_name, modules, reverse_map)

        # Detect input type
        input_type = detect_input_type(mod_name, tts_prompt, tts_name, modules)

        # Analyze fillers/suffixes/head-clip
        has_fillers, has_suffixes, has_head_clip = analyze_fillers(pw)

        # Recommended action
        action = STATUS_LABELS[status][2]

        results.append({
            "module_name": mod_name,
            "module_type": type_label,
            "word_count": word_count,
            "status": status,
            "input_type": input_type,
            "preceding_tts": tts_prompt,
            "has_fillers": has_fillers,
            "has_suffixes": has_suffixes,
            "has_head_clip": has_head_clip,
            "recommended_action": action,
        })

    # Summary
    summary = {
        "empty": sum(1 for r in results if r["status"] == "empty"),
        "insufficient": sum(1 for r in results if r["status"] == "insufficient"),
        "adequate": sum(1 for r in results if r["status"] == "adequate"),
        "excessive": sum(1 for r in results if r["status"] == "excessive"),
    }

    return {
        "flow_name": flow_name,
        "total_modules": len(results),
        "stt_count": stt_count,
        "dtmf_count": dtmf_count,
        "summary": summary,
        "modules": results,
    }


def format_console_output(analysis: dict) -> str:
    """Format analysis result for console display."""
    lines = []
    sep = "=" * 60

    lines.append(sep)
    lines.append(f"[PW_ANALYZER] profile_words 分析結果: {analysis['flow_name']}")
    lines.append(sep)
    lines.append(f"モジュール数: {analysis['total_modules']} (STT: {analysis['stt_count']}, DTMF: {analysis['dtmf_count']})")
    lines.append("")

    summary = analysis["summary"]
    lines.append("--- ステータス別 ---")
    lines.append(f"  empty (要生成):       {summary['empty']}")
    lines.append(f"  insufficient (要拡充): {summary['insufficient']}")
    lines.append(f"  adequate (OK):        {summary['adequate']}")
    lines.append(f"  excessive (要調整):    {summary['excessive']}")
    lines.append("")

    # Modules that need action
    action_modules = [m for m in analysis["modules"] if m["status"] != "adequate"]
    if action_modules:
        lines.append("--- 対応が必要なモジュール ---")
        # Sort: empty first, then insufficient, then excessive
        order = {"empty": 0, "insufficient": 1, "excessive": 2}
        action_modules.sort(key=lambda m: (order.get(m["status"], 9), m["module_name"]))

        for m in action_modules:
            label = STATUS_LABELS[m["status"]][0]
            action_text = STATUS_LABELS[m["status"]][3]
            # Pad module name for alignment
            name_padded = m["module_name"].ljust(24)
            type_padded = f"({m['input_type']})".ljust(16)
            lines.append(
                f"  [{label:6s}] {name_padded} {type_padded} -- {m['word_count']}語 -> {action_text}"
            )
    else:
        lines.append("--- 全モジュール adequate (対応不要) ---")

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="profile_words 分析スクリプト: フローJSON内のSTT/DTMFモジュールを分析"
    )
    parser.add_argument(
        "input_files",
        nargs="+",
        help="分析対象のフローJSONファイル (1つ以上)",
    )
    parser.add_argument(
        "--output", "-o",
        help="分析結果JSONの出力先ファイルパス",
        default=None,
    )
    args = parser.parse_args()

    # Force UTF-8 output on Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    all_results = []

    for input_file in args.input_files:
        if not os.path.isfile(input_file):
            print(f"[ERROR] ファイルが見つかりません: {input_file}", file=sys.stderr)
            continue

        try:
            with open(input_file, "r", encoding="utf-8") as f:
                flow_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSONパースエラー: {input_file}: {e}", file=sys.stderr)
            continue

        analysis = analyze_flow(flow_data)
        all_results.append(analysis)

        # Console output
        print(format_console_output(analysis))

    if not all_results:
        print("[ERROR] 分析対象のファイルがありませんでした。", file=sys.stderr)
        sys.exit(1)

    # JSON output
    if args.output:
        output_data = all_results[0] if len(all_results) == 1 else all_results
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 分析結果を保存しました: {args.output}")


if __name__ == "__main__":
    main()
