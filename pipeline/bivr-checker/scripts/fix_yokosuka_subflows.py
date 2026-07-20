#!/usr/bin/env python3
"""横須賀共済病院 サブフロー構造修正スクリプト

修正内容:
  1. 氏名サブフロー:
     - STT-003: 入力_患者_氏名 success遷移先を script_結果返却_氏名 に設定
     - SCR-002: script_結果返却_氏名 モジュール追加
     - リトライ_患者_氏名 false遷移先を script_結果返却_氏名 に設定

  2. 生年月日サブフロー:
     - OAI-002: OpenAI_患者_生年月日 削除（DOB Re-confirmationが正規化を担当するため不要）
     - REACH-001: ↑の削除で解消
     - 復唱_患者_生年月日 success遷移先を script_結果返却_生年月日 に設定
     - SCR-002: script_結果返却_生年月日 モジュール追加
     - リトライ_患者_生年月日 false遷移先を script_結果返却_生年月日 に設定

  3. 診察券サブフロー:
     - openAI_患者_診察券番号 success遷移先を script_結果返却_診察券 に設定
     - SCR-002: script_結果返却_診察券 モジュール追加
     - リトライ_患者_診察券番号 false遷移先を script_結果返却_診察券 に設定
"""
import json
import sys
import io
from pathlib import Path

OUTPUT_DIR = Path("output/横須賀共済病院")

# 結果返却スクリプトテンプレート（電話番号サブフロー準拠）
RETURN_SCRIPT_TEMPLATE = '''var res = $runner.getModuleResult("{source_module}");
$runner.setResult(res);

var flowName = $runner.getCurrentFlowName();
var rid = $ivr.getRID();
var key = flowName + "." + rid;
$ivr.setObject(key, res);'''


def make_return_script(name, source_module, layout_x, layout_y):
    """結果返却スクリプトモジュール生成"""
    return {
        "type": "@General$Script",
        "params": {
            "script": RETURN_SCRIPT_TEMPLATE.format(source_module=source_module),
        },
        "next": [],
        "subs": [
            {"moduleName": "", "label": ""},
            {"moduleName": "", "label": ""},
            {"moduleName": "", "label": ""},
        ],
        "layout": {"x": layout_x, "y": layout_y},
    }


def fix_next_target(mod, condition, new_target):
    """nextの特定conditionの遷移先を変更"""
    for n in mod.get("next", []):
        if n.get("condition") == condition:
            old = n.get("nextModuleName", "")
            n["nextModuleName"] = new_target
            return old
    return None


def fix_flow(path, fixes_list):
    """フロー修正の共通処理"""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_flow(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    fixes = []

    # ================================================================
    # 1. 氏名サブフロー
    # ================================================================
    print("[1/3] 氏名サブフロー修正")
    path = OUTPUT_DIR / "横須賀共済_氏名聴取_20260420.json"
    data = fix_flow(path, fixes)
    modules = data["modules"]

    # STT-003: 入力_患者_氏名 success → script_結果返却_氏名
    old = fix_next_target(modules["入力_患者_氏名"], "^.+$", "script_結果返却_氏名")
    fixes.append(f"STT-003: 入力_患者_氏名 ^.+$: '{old}' → script_結果返却_氏名")

    # リトライ false → script_結果返却_氏名（パターンA: 次へ進む = サブフロー終了）
    old = fix_next_target(modules["リトライ_患者_氏名"], "false", "script_結果返却_氏名")
    fixes.append(f"T-001: リトライ_患者_氏名 false: '{old}' → script_結果返却_氏名")

    # SCR-002: 結果返却スクリプト追加
    # 氏名はSTT直接取得（OpenAIなし — CLAUDE.md 原則22準拠）
    # 最後に入力されたSTTモジュールの結果を返却
    modules["script_結果返却_氏名"] = make_return_script(
        "script_結果返却_氏名", "入力_患者_氏名", 0, 900
    )
    fixes.append("SCR-002: script_結果返却_氏名 追加")

    save_flow(path, data)
    print(f"  saved: {path}")

    # ================================================================
    # 2. 生年月日サブフロー
    # ================================================================
    print("[2/3] 生年月日サブフロー修正")
    path = OUTPUT_DIR / "横須賀共済_生年月日聴取_20260420.json"
    data = fix_flow(path, fixes)
    modules = data["modules"]

    # OAI-002 + REACH-001: OpenAI_患者_生年月日 を削除
    # DOB Re-confirmationが正規化を担当するため、別途OpenAIは不要
    if "OpenAI_患者_生年月日" in modules:
        del modules["OpenAI_患者_生年月日"]
        fixes.append("OAI-002/REACH-001: OpenAI_患者_生年月日 を削除（DOB Re-confirmationが正規化担当）")

    # 復唱_患者_生年月日 の success(^.*$) → script_結果返却_生年月日
    old = fix_next_target(modules["復唱_患者_生年月日"], "^.*$", "script_結果返却_生年月日")
    fixes.append(f"復唱_患者_生年月日 ^.*$: '{old}' → script_結果返却_生年月日")

    # リトライ false → script_結果返却_生年月日
    old = fix_next_target(modules["リトライ_患者_生年月日"], "false", "script_結果返却_生年月日")
    fixes.append(f"T-001: リトライ_患者_生年月日 false: '{old}' → script_結果返却_生年月日")

    # SCR-002: 結果返却スクリプト追加
    # DOB Re-confirmationの結果を返却
    modules["script_結果返却_生年月日"] = make_return_script(
        "script_結果返却_生年月日", "復唱_患者_生年月日", 0, 900
    )
    fixes.append("SCR-002: script_結果返却_生年月日 追加")

    save_flow(path, data)
    print(f"  saved: {path}")

    # ================================================================
    # 3. 診察券番号サブフロー
    # ================================================================
    print("[3/3] 診察券番号サブフロー修正")
    path = OUTPUT_DIR / "横須賀共済_診察券番号聴取_20260420.json"
    data = fix_flow(path, fixes)
    modules = data["modules"]

    # openAI_患者_診察券番号 の success遷移先を設定
    # 現在: ^.+$ success → "" (空)
    # 正しい分岐: 番号有効 → script_結果返却_診察券, NO_RESULT等はリトライ
    oai = modules["openAI_患者_診察券番号"]
    for n in oai["next"]:
        if n.get("condition") == "^.+$" and n.get("label") == "success":
            old = n["nextModuleName"]
            n["nextModuleName"] = "script_結果返却_診察券"
            fixes.append(f"openAI_患者_診察券番号 ^.+$: '{old}' → script_結果返却_診察券")
            break

    # リトライ false → script_結果返却_診察券
    old = fix_next_target(modules["リトライ_患者_診察券番号"], "false", "script_結果返却_診察券")
    fixes.append(f"T-001: リトライ_患者_診察券番号 false: '{old}' → script_結果返却_診察券")

    # SCR-002: 結果返却スクリプト追加
    modules["script_結果返却_診察券"] = make_return_script(
        "script_結果返却_診察券", "openAI_患者_診察券番号", 0, 1200
    )
    fixes.append("SCR-002: script_結果返却_診察券 追加")

    save_flow(path, data)
    print(f"  saved: {path}")

    # ================================================================
    # 結果表示
    # ================================================================
    print(f"\n=== 横須賀共済病院 サブフロー修正 ({len(fixes)}件) ===\n")
    for fix in fixes:
        print(f"  ✓ {fix}")


if __name__ == "__main__":
    main()
