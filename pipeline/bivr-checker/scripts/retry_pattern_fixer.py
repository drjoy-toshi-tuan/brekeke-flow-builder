#!/usr/bin/env python3
"""
Stage 1.7: Retry Pattern Fixer
各Retry Counterモジュールのprompt_false/遷移先を自動分類・修正する。

Usage:
  python scripts/retry_pattern_fixer.py <flow_json> [--dry-run]
"""
import json, sys, argparse

sys.stdout.reconfigure(encoding='utf-8')

PATTERN_A_PROMPT_FALSE = "{tts_g: 大変申し訳ございません。 うまく聞き取ることができませんでしたので後ほど担当者にて確認いたします。}"


def is_retry(mod_type: str) -> bool:
    return "Retry Counter" in mod_type


def is_tts(mod_type: str) -> bool:
    return "Text to speech" in mod_type and "Retry" not in mod_type and "Re-confirmation" not in mod_type


def is_stt(mod_type: str) -> bool:
    return "Speech to Text" in mod_type or "DTMF" in mod_type


def is_openai(mod_type: str) -> bool:
    return "generate_by_OpenAI" in mod_type


def build_reverse_map(modules: dict) -> dict:
    """module_name -> list of (source_module_name, condition) that point to it"""
    rev = {}
    for src_name, src_mod in modules.items():
        for nx in src_mod.get("next", []):
            tgt = nx.get("nextModuleName", "")
            if tgt:
                rev.setdefault(tgt, []).append((src_name, nx.get("condition", "")))
    return rev


def find_next_step_after_retry(retry_name: str, modules: dict) -> str:
    """
    Retryモジュールから正常フローの「次のステップ」を見つける。

    Retry(true) → TTS → STT → OpenAI → [次のモジュール]
    or
    Retry(true) → TTS → STT(DTMF) → OpenAI → [次のモジュール]

    OpenAIのsuccess/wildcard遷移先が「次のステップ」
    """
    retry_mod = modules[retry_name]

    # Step 1: true遷移先 = TTS
    true_target = ""
    for nx in retry_mod.get("next", []):
        if nx.get("condition") == "true":
            true_target = nx.get("nextModuleName", "")
            break

    if not true_target or true_target not in modules:
        return ""

    # Step 2: TTS → STT (follow TTS next)
    tts_mod = modules[true_target]
    stt_name = ""
    for nx in tts_mod.get("next", []):
        nm = nx.get("nextModuleName", "")
        if nm and nm in modules and is_stt(modules[nm].get("type", "")):
            stt_name = nm
            break
    # If TTS doesn't directly link to STT, check all next
    if not stt_name:
        for nx in tts_mod.get("next", []):
            nm = nx.get("nextModuleName", "")
            if nm and nm in modules:
                stt_name = nm
                break

    if not stt_name or stt_name not in modules:
        return ""

    # Step 3: STT → OpenAI (success condition ^.+$)
    stt_mod = modules[stt_name]
    openai_name = ""
    for nx in stt_mod.get("next", []):
        cond = nx.get("condition", "")
        nm = nx.get("nextModuleName", "")
        if cond in ("^.+$",) and nm and nm in modules:
            openai_name = nm
            break

    if not openai_name or openai_name not in modules:
        # STT直結の場合（OpenAIなし）、success先を返す
        for nx in stt_mod.get("next", []):
            cond = nx.get("condition", "")
            nm = nx.get("nextModuleName", "")
            if cond == "^.+$" and nm:
                return nm
        return ""

    # Step 4: OpenAI → 次のモジュール
    # success/wildcard (^.+$ or ^.*$) で、TIMEOUT/ERROR/NO_RESULTでない遷移先
    openai_mod = modules[openai_name]
    next_candidates = []
    for nx in openai_mod.get("next", []):
        cond = nx.get("condition", "")
        nm = nx.get("nextModuleName", "")
        if not nm or not cond:
            continue
        if cond in ("^TIMEOUT$", "^ERROR$", "^NO_RESULT$"):
            continue
        next_candidates.append((cond, nm))

    # ワイルドカードを優先
    for cond, nm in next_candidates:
        if cond in ("^.+$", "^.*$"):
            return nm

    # 個別条件がある場合は最初の非エラー遷移先
    if next_candidates:
        return next_candidates[0][1]

    return ""


def classify_retry(retry_name: str, modules: dict) -> tuple:
    """
    Returns: (pattern, reason, next_step)
    pattern: "A", "B", "C"
    """
    # 用件/区分 → パターンC
    if "用件" in retry_name or "区分" in retry_name:
        retry_mod = modules[retry_name]
        true_target = ""
        for nx in retry_mod.get("next", []):
            if nx.get("condition") == "true":
                true_target = nx.get("nextModuleName", "")
        return ("C", "用件/区分は必須聴取（無限ループ）", true_target)

    # それ以外はパターンA（次へ進む）をデフォルトとする
    next_step = find_next_step_after_retry(retry_name, modules)
    if next_step:
        return ("A", f"任意聴取→次へ進む（{next_step}へ）", next_step)
    else:
        return ("A", "任意聴取→次へ進む（遷移先特定不能、手動確認推奨）", "")


def apply_pattern(retry_name: str, modules: dict, pattern: str, next_step: str, dry_run: bool) -> bool:
    """パターンを適用。変更があればTrueを返す。"""
    mod = modules[retry_name]
    params = mod.get("params", {})
    changed = False

    true_target = ""
    false_idx = -1
    for i, nx in enumerate(mod.get("next", [])):
        if nx.get("condition") == "true":
            true_target = nx.get("nextModuleName", "")
        elif nx.get("condition") == "false":
            false_idx = i

    if pattern == "C":
        # パターンC: prompt_false="" , false→true_target
        if params.get("prompt_false", "") != "":
            if not dry_run:
                params["prompt_false"] = ""
            changed = True
        if false_idx >= 0 and mod["next"][false_idx].get("nextModuleName") != true_target:
            if not dry_run:
                mod["next"][false_idx]["nextModuleName"] = true_target
            changed = True

    elif pattern == "A":
        # パターンA: prompt_false=メッセージ, false→next_step
        if next_step and false_idx >= 0:
            if mod["next"][false_idx].get("nextModuleName") != next_step:
                if not dry_run:
                    mod["next"][false_idx]["nextModuleName"] = next_step
                changed = True
            if params.get("prompt_false", "") != PATTERN_A_PROMPT_FALSE:
                if not dry_run:
                    params["prompt_false"] = PATTERN_A_PROMPT_FALSE
                changed = True

    # パターンBは現状維持

    return changed


def main():
    parser = argparse.ArgumentParser(description="Stage 1.7: Retry Pattern Fixer")
    parser.add_argument("flow_json", help="フローJSONファイルパス")
    parser.add_argument("--dry-run", action="store_true", help="変更を適用せず表示のみ")
    args = parser.parse_args()

    with open(args.flow_json, encoding="utf-8") as f:
        data = json.load(f)

    modules = data.get("modules", {})

    print(f"=== Stage 1.7: Retry Pattern Fixer ===")
    print(f"対象: {data.get('name', '?')}")
    print(f"モード: {'DRY-RUN' if args.dry_run else '適用'}")
    print()

    total_changes = 0
    for mod_name in sorted(modules.keys()):
        mod = modules[mod_name]
        if not is_retry(mod.get("type", "")):
            continue

        pattern, reason, next_step = classify_retry(mod_name, modules)

        # 現在のパターンを判定
        params = mod.get("params", {})
        cur_false_target = ""
        cur_true_target = ""
        for nx in mod.get("next", []):
            if nx.get("condition") == "true":
                cur_true_target = nx.get("nextModuleName", "")
            elif nx.get("condition") == "false":
                cur_false_target = nx.get("nextModuleName", "")
        cur_prompt_false = params.get("prompt_false", "")

        # 現在のパターンを特定
        if cur_prompt_false == "" and cur_false_target == cur_true_target:
            cur_pattern = "C"
        elif "失敗" in cur_false_target:
            cur_pattern = "B"
        else:
            cur_pattern = "A"

        changed = apply_pattern(mod_name, modules, pattern, next_step, args.dry_run)

        status = "[変更]" if changed else "[OK]"
        if changed:
            total_changes += 1

        print(f"  {status} {mod_name}: パターン{cur_pattern}→{pattern} ({reason})")
        if changed and pattern == "A":
            print(f"         false→{next_step}  prompt_false=パターンA定型文")
        elif changed and pattern == "C":
            print(f"         false→{cur_true_target}(ループ)  prompt_false=\"\"")

    if not args.dry_run and total_changes > 0:
        with open(args.flow_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n完了: {total_changes} 件変更" + (" (dry-run)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
