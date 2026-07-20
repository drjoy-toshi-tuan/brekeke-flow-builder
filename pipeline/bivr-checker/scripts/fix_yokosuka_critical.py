#!/usr/bin/env python3
"""横須賀共済病院 残存CRITICAL修正スクリプト

修正内容:
  T-001 x6: リトライ false遷移先 TODO_scaffold → 適切な遷移先に変更
    - リトライ_当日確認: パターンB → 完了フラグ_上限エラー（仕様書: リトライ失敗→終話）
    - リトライ_用件: パターンC → 用件（無限ループ、必須聴取）
    - リトライ_診療科1: パターンC → 診療科1（無限ループ、必須聴取）
    - リトライ_診療科2: パターンA → 用件別分岐（次へ進む、任意聴取）
    - リトライ_予約日: パターンA → jump_診察券聴取（次へ進む、任意聴取）
    - リトライ_内容: パターンA → jump_診察券聴取（次へ進む、任意聴取）

  CTX-017 x2: displayType重複修正
    - phonetype: CLASSIFICATION → TEXT
    - clinicalDepartment2: DEPARTMENT → TEXT

  PROMPT-001: OpenAI_当日確認 retry_failure → プロンプトに追加 or next条件を修正
"""
import json
import sys
import io
from pathlib import Path

OUTPUT_DIR = Path("output/横須賀共済病院")

def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    main_file = OUTPUT_DIR / "横須賀共済_診療予約_20260406_20260420.json"

    with open(main_file, encoding="utf-8") as f:
        data = json.load(f)

    modules = data["modules"]
    fixes = []

    # ================================================================
    # T-001 x6: リトライ false遷移先修正
    # ================================================================

    retry_fixes = {
        # パターンB: リトライ失敗 → 終話（シナリオ仕様書: リトライ上限到達→END_上限エラー）
        "リトライ_当日確認": ("完了フラグ_上限エラー", ""),  # prompt_false空 → 上限エラーTTSが発話

        # パターンC: 必須聴取 → 無限ループ
        "リトライ_用件": ("用件", '""'),  # prompt_false空、先頭TTSに戻る

        # パターンC: 診療科1は必須
        "リトライ_診療科1": ("診療科1", '""'),

        # パターンA: 診療科2は任意 → 次へ進む
        "リトライ_診療科2": ("用件別分岐", None),  # prompt_false維持

        # パターンA: 予約日は任意 → 次へ進む
        "リトライ_予約日": ("jump_診察券聴取", None),

        # パターンA: 内容は任意 → 次へ進む
        "リトライ_内容": ("jump_診察券聴取", None),
    }

    for retry_name, (target, pf_override) in retry_fixes.items():
        mod = modules[retry_name]
        for n in mod["next"]:
            if n.get("condition") == "false":
                old = n["nextModuleName"]
                n["nextModuleName"] = target
                fixes.append(f"T-001: {retry_name} false: {old} → {target}")
        if pf_override is not None:
            if pf_override == '""':
                mod["params"]["prompt_false"] = ""
                fixes.append(f"  └ prompt_false を空に変更（パターンC: 無限ループ）")
            else:
                mod["params"]["prompt_false"] = pf_override

    # ================================================================
    # CTX-017: displayType重複修正
    # ================================================================

    ctx_mod = modules["コンテキスト設定"]
    fields = json.loads(ctx_mod["params"]["fields"])
    for field in fields:
        if field["contextName"] == "phonetype" and field["displayType"] == "CLASSIFICATION":
            field["displayType"] = "TEXT"
            fixes.append("CTX-017: phonetype displayType: CLASSIFICATION → TEXT")
        if field["contextName"] == "clinicalDepartment2" and field["displayType"] == "DEPARTMENT":
            field["displayType"] = "TEXT"
            fixes.append("CTX-017: clinicalDepartment2 displayType: DEPARTMENT → TEXT")
    ctx_mod["params"]["fields"] = json.dumps(fields, ensure_ascii=False, indent=2)

    # ================================================================
    # PROMPT-001: OpenAI_当日確認 retry_failure
    # シナリオ仕様書には「retry_failure」分岐があるが、プロンプトの出力仕様にない
    # → retry_failureはリトライ上限時にRetry Counterが自動出力する特殊値
    #   → OpenAIのnextではなくRetry Counter経由で処理するのが正しい
    #   → OpenAI_当日確認から retry_failure next条件を削除
    # ================================================================

    oai = modules["OpenAI_当日確認"]
    new_next = [n for n in oai["next"] if n.get("condition") != "^retry_failure$"]
    if len(new_next) < len(oai["next"]):
        oai["next"] = new_next
        fixes.append("PROMPT-001: OpenAI_当日確認 から ^retry_failure$ 分岐を削除（Retry Counter経由で処理）")

    # ================================================================
    # 書き出し
    # ================================================================

    with open(main_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("=== 横須賀共済病院 残存CRITICAL修正 ===\n")
    for fix in fixes:
        print(f"  ✓ {fix}")
    print(f"\n出力: {main_file}")

if __name__ == "__main__":
    main()
