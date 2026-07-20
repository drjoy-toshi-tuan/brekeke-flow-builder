#!/usr/bin/env python3
"""
貝塚病院2（健診）包括修正スクリプト

FB-1: 冒頭アナウンスのウェブ予約文言削除（Property.md）
FB-2: 個人or企業の予約代行業者文言削除（Property.md）
FB-3: フロー順序修正（冒頭確認→本人確認→個人or企業）
FB-4: 構造チェック（途中切断原因の特定・修正）
FB-5: profile_words拡充 + OpenAIプロンプト強化
"""

import json
import sys
import os
import re

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
INPUT_DIR = os.path.join(BASE_DIR, "input", "貝塚病院2")

MAIN_JSON = os.path.join(OUTPUT_DIR, "貝塚病院_健診_20260417.json")
PROPERTY_MD = os.path.join(INPUT_DIR, "properties_貝塚病院_健診.md")

# ============================================================
# はい/いいえ用 profile_words（Stage 2 標準）
# ============================================================
YES_NO_PROFILE_WORDS = """はい はい
はい はーい
はい はいはい
はい はいです
はい はいっ
はい はいですね
はい あはい
はい えーはい
はい あのはい
はい はいそうです
はい はいそうですお願いします
はい はいお願いします
はい そうです
はい そーです
はい そうですね
はい そうですお願いします
はい お願いします
はい ええ
はい ええそうです
いいえ いいえ
いいえ いえ
いいえ いえいえ
いいえ いいえです
いいえ あいいえ
いいえ えーいいえ
いいえ いいえちがいます
いいえ いえちがいます
いいえ いいえですね
いいえ 違います
いいえ ちがいます
いいえ ちがう
いいえ 違う
いいえ いや
いいえ いやちがいます
いいえ いや違います
いいえ そうじゃない
いいえ そうではありません
いいえ そうじゃありません"""

# 本人確認用（上記 + 本人特有の語彙）
HONIN_PROFILE_WORDS = YES_NO_PROFILE_WORDS + """
はい 本人です
はい はい本人です
はい 私です
はい はい私です
はい 自分です
はい はい自分です
いいえ 本人ではありません
いいえ 本人じゃないです
いいえ 代理です
いいえ 家族です
いいえ 家族の"""

# 個人or企業用
KOJIN_KIGYO_PROFILE_WORDS = YES_NO_PROFILE_WORDS + """
はい 企業です
はい 担当者です
はい 代行業者です
はい 法人です
はい 会社です
いいえ 個人です
いいえ 個人"""

# 企業_用件確認用
KIGYO_YOUKEN_PROFILE_WORDS = YES_NO_PROFILE_WORDS + """
はい 予約です
はい 申し込みです
はい はい予約です"""


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [SAVED] {os.path.basename(path)}")


def fix_flow_order(data):
    """FB-3: フロー順序修正"""
    changes = 0
    modules = data["modules"]

    # 1. OpenAI_冒頭確認: ^はい$ → 個人or企業 → 本人確認
    mod = modules["OpenAI_冒頭確認"]
    for nx in mod["next"]:
        if nx["condition"] == "^はい$" and nx["nextModuleName"] == "個人or企業":
            nx["nextModuleName"] = "本人確認"
            nx["label"] = "はい"
            print("  [FB-3] OpenAI_冒頭確認: ^はい$ → 本人確認（個人or企業から変更）")
            changes += 1

    # 2. OpenAI_本人確認: ^いいえ$ → 入電者氏名 → 個人or企業
    mod = modules["OpenAI_本人確認"]
    for nx in mod["next"]:
        if nx["condition"] == "^いいえ$" and nx["nextModuleName"] == "入電者氏名":
            nx["nextModuleName"] = "個人or企業"
            nx["label"] = "いいえ"
            print("  [FB-3] OpenAI_本人確認: ^いいえ$ → 個人or企業（入電者氏名から変更）")
            changes += 1

    # 3. OpenAI_個人or企業: ^個人$ → 本人確認 → 入電者氏名
    mod = modules["OpenAI_個人or企業"]
    for nx in mod["next"]:
        if nx["condition"] == "^個人$" and nx["nextModuleName"] == "本人確認":
            nx["nextModuleName"] = "入電者氏名"
            nx["label"] = "個人"
            print("  [FB-3] OpenAI_個人or企業: ^個人$ → 入電者氏名（本人確認から変更）")
            changes += 1

    # Also fix retry_pattern_fixer's リトライ_冒頭確認 false → 本人確認 (was 個人or企業)
    if "リトライ_冒頭確認" in modules:
        retry_mod = modules["リトライ_冒頭確認"]
        for nx in retry_mod["next"]:
            if nx["condition"] == "false" and nx["nextModuleName"] == "個人or企業":
                nx["nextModuleName"] = "本人確認"
                print("  [FB-3] リトライ_冒頭確認: false → 本人確認（個人or企業から変更）")
                changes += 1

    # Fix リトライ_本人確認 false → 個人or企業 (was jump_氏名聴取 - should skip to 個人or企業 when retry fails)
    # Actually, for retry failure on 本人確認, we should go to next step which is jump_氏名聴取 (pattern A)
    # But since flow order changed, let's check what makes sense:
    # 本人確認(はい) → jump_氏名聴取, 本人確認(いいえ) → 個人or企業
    # On retry failure, it should proceed as if "はい" (benefit of doubt) → jump_氏名聴取
    # This was already set correctly by retry_pattern_fixer

    # Fix リトライ_個人or企業 false: should go to next logical step
    # 個人or企業 is reached from 本人確認(いいえ)
    # 個人or企業(企業問合せ) → 企業_用件確認, 個人or企業(個人) → 入電者氏名
    # On retry failure, treat as 個人 → 入電者氏名
    if "リトライ_個人or企業" in modules:
        retry_mod = modules["リトライ_個人or企業"]
        for nx in retry_mod["next"]:
            if nx["condition"] == "false":
                if nx["nextModuleName"] != "入電者氏名":
                    old = nx["nextModuleName"]
                    nx["nextModuleName"] = "入電者氏名"
                    print(f"  [FB-3] リトライ_個人or企業: false → 入電者氏名（{old}から変更）")
                    changes += 1

    return changes


def fix_profile_words(data):
    """FB-5: profile_words拡充"""
    changes = 0
    modules = data["modules"]

    pw_map = {
        "入力_本人確認": HONIN_PROFILE_WORDS.strip(),
        "入力_個人or企業": KOJIN_KIGYO_PROFILE_WORDS.strip(),
        "入力_企業_用件確認": KIGYO_YOUKEN_PROFILE_WORDS.strip(),
    }

    for mod_name, pw in pw_map.items():
        if mod_name in modules:
            old_pw = modules[mod_name]["params"].get("profile_words", "")
            if not old_pw or old_pw.strip() == "":
                modules[mod_name]["params"]["profile_words"] = pw
                print(f"  [FB-5] {mod_name}: profile_words設定（{len(pw.splitlines())}語）")
                changes += 1

    # Also enhance 入力_冒頭確認 if it's missing some entries
    if "入力_冒頭確認" in modules:
        existing = modules["入力_冒頭確認"]["params"].get("profile_words", "")
        # Add missing entries
        enhanced = YES_NO_PROFILE_WORDS.strip()
        # Add 冒頭確認 specific words
        enhanced += """
はい 人間ドック
はい にんげんドック
はい 健康診断
はい けんこうしんだん
はい 健診
はい けんしん
はい ドック
はい どっく"""
        if existing.count("\n") < enhanced.count("\n"):
            modules["入力_冒頭確認"]["params"]["profile_words"] = enhanced.strip()
            print(f"  [FB-5] 入力_冒頭確認: profile_words強化（{len(enhanced.strip().splitlines())}語）")
            changes += 1

    return changes


def enhance_openai_prompts(data):
    """FB-5: OpenAIプロンプトのはい/いいえ判定パターン強化"""
    changes = 0
    modules = data["modules"]

    # OpenAI_本人確認: Add more patterns
    mod = modules.get("OpenAI_本人確認")
    if mod:
        prompt = mod["params"].get("prompt", "")
        # Check if extended patterns are missing
        if "ええ" not in prompt or "お願いします" not in prompt:
            # Add extended patterns to STEP2 (はい)
            old_step2 = """はい本人です
本人ですお願いします"""
            new_step2 = """はい本人です
はいお願いします
お願いします
ええ
ええそうです
本人ですお願いします
そうですお願いします"""
            prompt = prompt.replace(old_step2, new_step2)

            # Add extended patterns to STEP3 (いいえ)
            old_step3 = """いいえちがいます
いえ違います
いや違います"""
            new_step3 = """いいえちがいます
いえ違います
いや違います
ちがいますけど
そうじゃないです
そうではないです"""
            prompt = prompt.replace(old_step3, new_step3)

            mod["params"]["prompt"] = prompt
            print("  [FB-5] OpenAI_本人確認: はい/いいえ判定パターン強化")
            changes += 1

    # OpenAI_個人or企業: Add more patterns
    mod = modules.get("OpenAI_個人or企業")
    if mod:
        prompt = mod["params"].get("prompt", "")
        # Enhance 個人 section with more patterns
        if "個人ですよ" not in prompt:
            old_kojin = """個人です
違う
いえ
いや
そうではありません
そうじゃない
→ 個人"""
            new_kojin = """個人です
個人ですよ
違う
いえ
いや
そうではありません
そうじゃない
そうじゃないです
そうではないです
ちがいますけど
→ 個人"""
            prompt = prompt.replace(old_kojin, new_kojin)

            # Enhance 企業問合せ section
            old_kigyo = """代行
法人
会社
→ 企業問合せ"""
            new_kigyo = """代行
法人
会社
予約代行
→ 企業問合せ"""
            prompt = prompt.replace(old_kigyo, new_kigyo)

            mod["params"]["prompt"] = prompt
            print("  [FB-5] OpenAI_個人or企業: 判定パターン強化")
            changes += 1

    # OpenAI_企業_用件確認: Add patterns if empty profile_words
    mod = modules.get("OpenAI_企業_用件確認")
    if mod:
        prompt = mod["params"].get("prompt", "")
        if "ええ" not in prompt and "はいそうです" in prompt:
            # Add ええ patterns
            prompt = prompt.replace(
                "はいそうです",
                "はいそうです\nええ\nええそうです"
            )
            mod["params"]["prompt"] = prompt
            print("  [FB-5] OpenAI_企業_用件確認: はい判定パターン強化")
            changes += 1

    return changes


def check_fb4_disconnection(data):
    """FB-4: 途中切断の原因チェック"""
    modules = data["modules"]
    issues = []
    changes = 0

    # Check all modules for T-001 (missing next targets)
    all_module_names = set(modules.keys())
    for mod_name, mod in modules.items():
        for nx in mod.get("next", []):
            target = nx.get("nextModuleName", "")
            if target and target not in all_module_names:
                issues.append(f"  [FB-4] T-001: {mod_name} → {target}（存在しない）")

        for sub in mod.get("subs", []):
            target = sub.get("moduleName", "")
            if target and target not in all_module_names:
                issues.append(f"  [FB-4] T-003: {mod_name} subs → {target}（存在しない）")

    # Check matchingmethod (must be int)
    for mod_name, mod in modules.items():
        mm = mod.get("matchingmethod")
        if mm is not None and not isinstance(mm, int):
            mod["matchingmethod"] = int(mm) if str(mm).isdigit() else 1
            changes += 1
            print(f"  [FB-4] MM-001: {mod_name} matchingmethod → {mod['matchingmethod']}（型修正）")

    # Check detection_flag for STT modules
    for mod_name, mod in modules.items():
        if "Speech to Text" in mod.get("type", "") and "Retry" not in mod.get("type", ""):
            df = mod["params"].get("detection_flag", "")
            if df != "デフォルト":
                mod["params"]["detection_flag"] = "デフォルト"
                changes += 1
                print(f"  [FB-4] {mod_name}: detection_flag → デフォルト（'{df}'から変更）")

    # Check DTMF modules too
    for mod_name, mod in modules.items():
        if "DTMF" in mod.get("type", ""):
            df = mod["params"].get("detection_flag", "")
            if df != "デフォルト":
                mod["params"]["detection_flag"] = "デフォルト"
                changes += 1
                print(f"  [FB-4] {mod_name}: detection_flag → デフォルト（'{df}'から変更）")

    for issue in issues:
        print(issue)

    return changes


def fix_property_md():
    """FB-1, FB-2: Property.md修正"""
    with open(PROPERTY_MD, "r", encoding="utf-8") as f:
        content = f.read()

    changes = 0

    # FB-1: 冒頭_アナウンス — remove ウェブ予約文言
    old_annc = "ご予約の方は、当院ホームページからウェブ予約も可能です。"
    if old_annc in content:
        content = content.replace(old_annc, "")
        print(f"  [FB-1] 冒頭_アナウンス: ウェブ予約文言を削除")
        changes += 1

    # FB-2: 個人or企業 — remove 予約代行業者文言
    old_agent = "もしくは、予約代行業者様でしょうか？"
    if old_agent in content:
        # Replace with just the closing question
        content = content.replace(
            "企業のご担当者様、もしくは、予約代行業者様でしょうか？",
            "企業のご担当者様でしょうか？"
        )
        print(f"  [FB-2] 個人or企業: 予約代行業者文言を削除")
        changes += 1

    # Also update the OpenAI prompts in JSON that reference the old prompt text
    # (this is handled in the JSON fix functions below)

    with open(PROPERTY_MD, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [SAVED] {os.path.basename(PROPERTY_MD)}")

    # Also copy to output directory
    output_prop = os.path.join(OUTPUT_DIR, "properties_貝塚病院_健診.md")
    with open(output_prop, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [SAVED] {os.path.basename(output_prop)}（output/にコピー）")

    return changes


def fix_openai_context_prompts(data):
    """FB-1, FB-2: OpenAIプロンプト内のContext文言も修正"""
    changes = 0
    modules = data["modules"]

    # Fix OpenAI_個人or企業 context to remove 予約代行業者
    mod = modules.get("OpenAI_個人or企業")
    if mod:
        prompt = mod["params"].get("prompt", "")
        old_text = "企業のご担当者様、もしくは、予約代行業者様でしょうか？"
        new_text = "企業のご担当者様でしょうか？"
        if old_text in prompt:
            prompt = prompt.replace(old_text, new_text)
            mod["params"]["prompt"] = prompt
            print("  [FB-2] OpenAI_個人or企業: Context内の予約代行業者文言修正")
            changes += 1

    return changes


def main():
    print("=" * 60)
    print("貝塚病院2（健診）包括修正")
    print("=" * 60)

    # Load main flow
    data = load_json(MAIN_JSON)
    total_changes = 0

    # FB-1, FB-2: Property.md修正
    print("\n--- FB-1, FB-2: Property.md修正 ---")
    total_changes += fix_property_md()

    # FB-3: フロー順序修正
    print("\n--- FB-3: フロー順序修正 ---")
    total_changes += fix_flow_order(data)

    # FB-1,2 in OpenAI prompts
    print("\n--- FB-1, FB-2: OpenAIプロンプトContext修正 ---")
    total_changes += fix_openai_context_prompts(data)

    # FB-4: 構造チェック
    print("\n--- FB-4: 構造チェック ---")
    total_changes += check_fb4_disconnection(data)

    # FB-5: profile_words + プロンプト強化
    print("\n--- FB-5: profile_words拡充 ---")
    total_changes += fix_profile_words(data)

    print("\n--- FB-5: OpenAIプロンプト強化 ---")
    total_changes += enhance_openai_prompts(data)

    # Save
    print("\n--- 保存 ---")
    save_json(MAIN_JSON, data)

    print(f"\n総修正件数: {total_changes}")
    print("=" * 60)


if __name__ == "__main__":
    main()
