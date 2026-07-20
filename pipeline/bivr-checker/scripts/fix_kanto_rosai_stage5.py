#!/usr/bin/env python3
"""Stage 5 修正: 関東労災病院 — verify結果に基づく修正"""
import json, os, sys, re, io

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "output/関東労災病院/fixed/flows"

# ===================================================================
# 1. リトライfalse整合性修正
# ===================================================================

RETRY_FALSE_FIXES = {
    # Main flow
    "関東労災病院_診療_20260421.json": {
        # 無限ループ（分岐あり）→ false = true遷移先, prompt_false = ""
        "リトライ_用件確認": {"false_target": "用件確認", "prompt_false": "", "reason": "無限ループ"},
        "リトライ_診療科": {"false_target": "診療科", "prompt_false": "", "reason": "無限ループ"},
        "リトライ_複数診療科聴取_変更": {"false_target": "複数診療科聴取_変更", "prompt_false": "", "reason": "無限ループ"},
        "リトライ_複数診療科聴取_キャンセル": {"false_target": "複数診療科聴取_キャンセル", "prompt_false": "", "reason": "無限ループ"},
        # 次へ進む（分岐なし）→ false = catch-all遷移先
        "リトライ_複数診療科確認_変更": {"false_target": "入力_現在の予約日_変更", "prompt_false": "{tts_g:かしこまりました。次の質問に進みます。}", "reason": "次へ進む"},
        "リトライ_現在の予約日_変更": {"false_target": "script_当日翌営業日判定", "prompt_false": "{tts_g:大変申し訳ございません。うまく聞き取ることができませんでしたので後ほど担当者にて確認いたします。}", "reason": "次へ進む"},
        "リトライ_変更理由": {"false_target": "入力_予約希望日_変更", "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}", "reason": "次へ進む"},
        "リトライ_予約希望日_変更": {"false_target": "jump_氏名聴取", "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}", "reason": "次へ進む"},
        "リトライ_複数診療科確認_キャンセル": {"false_target": "入力_現在の予約日_キャンセル", "prompt_false": "{tts_g:かしこまりました。次の質問に進みます。}", "reason": "次へ進む"},
        "リトライ_現在の予約日_キャンセル": {"false_target": "キャンセル理由", "prompt_false": "{tts_g:大変申し訳ございません。うまく聞き取ることができませんでしたので後ほど担当者にて確認いたします。}", "reason": "次へ進む"},
        "リトライ_キャンセル理由": {"false_target": "入力_別日希望確認", "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}", "reason": "次へ進む"},
        "リトライ_別日希望確認": {"false_target": "jump_氏名聴取", "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}", "reason": "次へ進む"},
        "リトライ_診療科_確認": {"false_target": "jump_診察券番号聴取", "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}", "reason": "次へ進む"},
        "リトライ_問い合わせ内容": {"false_target": "jump_氏名聴取", "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}", "reason": "次へ進む"},
    },
    # Subflows
    "関東労災病院_生年月日聴取_20260421.json": {
        "リトライ_患者_生年月日": {"false_target": "患者_生年月日", "prompt_false": "", "reason": "無限ループ"},
    },
    "関東労災病院_電話番号聴取_20260421.json": {
        "リトライ_患者_連絡先": {"false_target": "患者_連絡先", "prompt_false": "", "reason": "無限ループ"},
        "リトライ_患者_復唱連絡先": {"false_target": "復唱_患者_連絡先", "prompt_false": "", "reason": "無限ループ"},
        "リトライ_患者_携帯電話": {"false_target": "患者_携帯", "prompt_false": "", "reason": "無限ループ"},
    },
}


def fix_retry_false(filepath, fixes_dict):
    """リトライfalse遷移先とprompt_falseを修正"""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    fname = os.path.basename(filepath)
    if fname not in fixes_dict:
        return 0

    fixes = fixes_dict[fname]
    count = 0
    modules = data.get("modules", {})

    for retry_name, fix in fixes.items():
        if retry_name not in modules:
            print(f"  [WARN] {retry_name} not found in {fname}")
            continue

        mod = modules[retry_name]
        nexts = mod.get("next", [])

        for n in nexts:
            if n.get("condition") == "false":
                old_target = n.get("nextModuleName", "")
                n["nextModuleName"] = fix["false_target"]
                print(f"  [FIX] {retry_name}: false target '{old_target}' -> '{fix['false_target']}' ({fix['reason']})")
                count += 1
                break

        # prompt_false
        params = mod.get("params", {})
        old_pf = params.get("prompt_false", "")
        params["prompt_false"] = fix["prompt_false"]
        if old_pf != fix["prompt_false"]:
            pf_preview = fix["prompt_false"][:40] if fix["prompt_false"] else "(empty)"
            print(f"  [FIX] {retry_name}: prompt_false -> {pf_preview}")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return count


# ===================================================================
# 2. Property.md PROP-001 修正: Jump to Flow properties にサブフロー TTS を設定
# ===================================================================

def fix_jump_properties(main_flow_path, property_path):
    """Jump to Flow の properties にサブフローのTTSプロンプトを設定"""
    with open(main_flow_path, encoding="utf-8") as f:
        data = json.load(f)

    with open(property_path, encoding="utf-8") as f:
        prop_content = f.read()

    modules = data.get("modules", {})
    count = 0

    # サブフロー名→Property.mdのTTSプロンプトマッピング
    subflow_tts_map = {
        "jump_氏名聴取": ["患者_氏名"],
        "jump_生年月日聴取": ["患者_生年月日"],
        "jump_診察券番号聴取": ["患者_診察券番号"],
        "jump_電話番号聴取": ["患者_連絡先"],
    }

    for jump_name, tts_keys in subflow_tts_map.items():
        if jump_name not in modules:
            continue

        mod = modules[jump_name]
        props_lines = []

        for key in tts_keys:
            pattern = rf'^{re.escape(key)}\.prompt=(.+)$'
            m = re.search(pattern, prop_content, re.MULTILINE)
            if m:
                props_lines.append(f"{key}.prompt={m.group(1)}")

        if props_lines:
            mod["params"]["properties"] = "\n".join(props_lines)
            print(f"  [FIX] {jump_name}: properties set ({len(props_lines)} TTS prompts)")
            count += 1

    with open(main_flow_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return count


# ===================================================================
# 3. profile_words 語数調整（50-300語に収める）
# ===================================================================

def fix_pw_range(filepath):
    """profile_wordsを50-300語の範囲に調整"""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    modules = data.get("modules", {})

    for mname, mod in modules.items():
        mtype = mod.get("type", "")
        if mtype not in (
            "drjoy^AmiVoice$Speech to Text",
            "drjoy^External Integration$DTMF AmiVoice STT Input",
        ):
            continue

        pw = mod.get("params", {}).get("profile_words", "")
        if not pw:
            continue

        lines = [l for l in pw.split("\n") if l.strip() and not l.startswith("#")]
        word_count = len(lines)

        if word_count > 300:
            # Truncate: keep first 290 lines (to leave some room)
            truncated = lines[:290]
            mod["params"]["profile_words"] = "\n".join(truncated)
            print(f"  [FIX] {mname}: profile_words {word_count} -> 290 words (truncated)")
            count += 1
        elif word_count < 50:
            # DTMF modules with numbers often have fewer words - that's OK if < 50
            if mtype == "drjoy^External Integration$DTMF AmiVoice STT Input":
                # DTMF is exempted from 50 minimum for number/date input
                pass
            else:
                print(f"  [WARN] {mname}: profile_words {word_count} words (below 50, may need more)")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return count


# ===================================================================
# Main
# ===================================================================

if __name__ == "__main__":
    total = 0

    print("\n=== リトライfalse整合性修正 ===")
    for fname in sorted(os.listdir(BASE)):
        if fname.endswith(".json"):
            total += fix_retry_false(os.path.join(BASE, fname), RETRY_FALSE_FIXES)

    print("\n=== Jump to Flow properties修正 ===")
    main_flow = os.path.join(BASE, "関東労災病院_診療_20260421.json")
    prop_file = "input/関東労災病院/properties_関東労災病院_診療.md"
    total += fix_jump_properties(main_flow, prop_file)

    print("\n=== profile_words語数調整 ===")
    for fname in sorted(os.listdir(BASE)):
        if fname.endswith(".json"):
            total += fix_pw_range(os.path.join(BASE, fname))

    print(f"\n[TOTAL] {total} fixes applied")
