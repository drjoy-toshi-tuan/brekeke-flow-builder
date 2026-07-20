#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_rename_openai_modules.py — OpenAI_* → script_* 一括リネーム核の受入テスト（issue #236）。

実行: python test_rename_openai_modules.py
終了コード 0 = 全 PASS。FAIL があれば一覧を出して 1。

issue #236 の 4 残存パターン + 誤リネーム防止（generate_by_OpenAI 本体）+ 冪等性 +
衝突ガード を網羅する。外部依存なし（純 in-memory フロー）。
"""

import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rename_openai_modules import (  # noqa: E402
    detect_openai_script_renames,
    apply_rename_mapping,
    expand_mapping_with_aux,
    detect_openai_residue,
    detect_dangling_references,
    verify_flow_integrity,
)

_FAILS: list[str] = []


def check(cond: bool, label: str) -> None:
    if not cond:
        _FAILS.append(label)


def _fixture_flow() -> dict:
    """4 残存パターン + 負例 + 正常 Script を含むフロー。"""
    return {
        "name": "テスト$恵佑会_診療",
        "start": "冒頭",
        "modules": {
            # 正常: 冒頭（負例: Script でない・改名しない）
            "冒頭": {
                "type": "Custom$wait", "name": "冒頭",
                "next": [{"condition": "^.*$", "label": "next", "nextModuleName": "入力_用件確認"}],
                "subs": [], "params": {},
            },
            # パターン#2: 上流 next が OpenAI_用件確認 を参照
            "入力_用件確認": {
                "type": "drjoy^STT$AmiVoice_STT", "name": "入力_用件確認",
                "next": [{"condition": "^.*$", "label": "success", "nextModuleName": "OpenAI_用件確認"}],
                "subs": [], "params": {},
            },
            # パターン#1: type は @General$Script なのに名前が OpenAI_*（+ subs 参照を保険でテスト）
            "OpenAI_用件確認": {
                "type": "@General$Script", "name": "OpenAI_用件確認",
                "next": [{"condition": "^.*$", "label": "next", "nextModuleName": "終話分岐_用件"}],
                "subs": [{"moduleName": "OpenAI_用件確認", "label": "OpenAI_用件確認"}],
                "params": {"script": "var r = $runner.getModuleResult(\"入力_用件確認\");"},
            },
            # パターン#3: CMR の module1Name/module2Name が OpenAI_用件確認
            "終話分岐_用件": {
                "type": "drjoy^Context Logic$ContextMatchRouter", "name": "終話分岐_用件",
                "next": [{"condition": "^1$", "label": "変更", "nextModuleName": "script_群分類"},
                         {"condition": "^0$", "label": "other", "nextModuleName": "リトライ_用件確認"}],
                "subs": [],
                "params": {"module1Name": "OpenAI_用件確認", "module2Name": "OpenAI_用件確認",
                           "module1Value1": "変更", "module2Value1": "変更"},
            },
            # パターン#4: saveDefault-OpenAI_* 補助モジュール
            "saveDefault-OpenAI_用件確認": {
                "type": "drjoy^Persistence$saveContext2DB", "name": "saveDefault-OpenAI_用件確認",
                "next": [{"condition": "^.*$", "label": "next", "nextModuleName": "リトライ_用件確認"}],
                "subs": [], "params": {"contextName": "classification"},
            },
            # script 本文が getModuleResult("OpenAI_用件確認") を参照（本文追従テスト）
            "script_群分類": {
                "type": "@General$Script", "name": "script_群分類",
                "next": [{"condition": "^1$", "label": "1", "nextModuleName": "リトライ_用件確認"}],
                "subs": [],
                "params": {"module": "OpenAI_用件確認",
                           "script": "var v = $runner.getModuleResult('OpenAI_用件確認'); $runner.setResult(v);"},
            },
            # 負例: generate_by_OpenAI 本体（type に Script を含まない）→ 改名してはならない
            "OpenAI_診療科": {
                "type": "drjoy^External Integration$generate_by_OpenAI", "name": "OpenAI_診療科",
                "next": [{"condition": "^.*$", "label": "default", "nextModuleName": "リトライ_用件確認"}],
                "subs": [], "params": {"module": "入力_診療科"},
            },
            # 正常 Script（既に script_ 命名）→ 不変
            "script_既存": {
                "type": "@General$Script", "name": "script_既存",
                "next": [], "subs": [], "params": {"script": "$runner.setResult('x');"},
            },
            # パターン#5: Re-confirmation node data の params.nodeName が OpenAI_用件確認 を参照（#348）
            "復唱_用件確認": {
                "type": "drjoy^Text To Speech$Re-confirmation node data", "name": "復唱_用件確認",
                "next": [{"condition": "^.*$", "label": "next", "nextModuleName": "リトライ_用件確認"}],
                "subs": [], "params": {"nodeName": "OpenAI_用件確認", "prompt": "{tts_g:#data#}"},
            },
            "リトライ_用件確認": {
                "type": "Custom$Speech Retry Counter", "name": "リトライ_用件確認",
                "next": [], "subs": [], "params": {},
            },
        },
    }


def test_detect_and_apply() -> None:
    flow = _fixture_flow()
    mapping = detect_openai_script_renames(flow)

    # 検出: OpenAI_用件確認(Script) + saveDefault 補助 = 2 名。診療科(本体)は対象外。
    check(mapping.get("OpenAI_用件確認") == "script_用件確認", "detect: OpenAI_用件確認 → script_用件確認")
    check(mapping.get("saveDefault-OpenAI_用件確認") == "saveDefault-script_用件確認",
          "detect: saveDefault 補助対追従")
    check("OpenAI_診療科" not in mapping, "detect: generate_by_OpenAI 本体は対象外（誤リネーム防止）")
    check("script_群分類" not in mapping, "detect: 既存 script_ 命名は対象外")
    check(len(mapping) == 2, f"detect: 写像は 2 名（実際 {len(mapping)}）")

    apply_rename_mapping(flow, mapping)
    m = flow["modules"]

    # #1 名前/キー
    check("script_用件確認" in m and "OpenAI_用件確認" not in m, "#1: modules キー改名")
    check(m["script_用件確認"]["name"] == "script_用件確認", "#1: name フィールド改名")
    # #2 上流 next
    check(m["入力_用件確認"]["next"][0]["nextModuleName"] == "script_用件確認", "#2: 上流 next 参照追従")
    # #3 CMR module1Name/module2Name
    cmr = m["終話分岐_用件"]["params"]
    check(cmr["module1Name"] == "script_用件確認" and cmr["module2Name"] == "script_用件確認",
          "#3: CMR module1Name/module2Name 追従")
    # #4 補助
    check("saveDefault-script_用件確認" in m and "saveDefault-OpenAI_用件確認" not in m,
          "#4: saveDefault 補助改名")
    # subs 追従
    sub = m["script_用件確認"]["subs"][0]
    check(sub["moduleName"] == "script_用件確認" and sub["label"] == "script_用件確認", "subs 追従")
    # params.module 追従（script_群分類）
    check(m["script_群分類"]["params"]["module"] == "script_用件確認", "params.module 追従")
    # #5 Re-confirmation params.nodeName 追従（#348）
    check(m["復唱_用件確認"]["params"]["nodeName"] == "script_用件確認",
          "#5: Re-confirmation params.nodeName 追従")
    # script 本文の引用参照追従
    body = m["script_群分類"]["params"]["script"]
    check("'script_用件確認'" in body and "OpenAI_用件確認" not in body, "script 本文の引用参照追従")
    # 負例: generate_by_OpenAI 本体は不変
    check("OpenAI_診療科" in m and m["OpenAI_診療科"]["name"] == "OpenAI_診療科",
          "負例: generate_by_OpenAI 本体は不変")
    # 正常 Script 不変
    check("script_既存" in m, "正常 script_ は不変")
    # start 不変
    check(flow["start"] == "冒頭", "start 不変")


def test_idempotent() -> None:
    flow = _fixture_flow()
    apply_rename_mapping(flow, detect_openai_script_renames(flow))
    # 2 回目: 残骸はもう無い
    second = detect_openai_script_renames(flow)
    check(len(second) == 0, f"冪等: 2 回目の検出は空（実際 {len(second)}）")


def test_collision_guard() -> None:
    # OpenAI_x(Script) と既存 script_x が併存 → new が衝突するため OpenAI_x はスキップ
    flow = {
        "name": "t$c", "start": "a",
        "modules": {
            "OpenAI_x": {"type": "@General$Script", "name": "OpenAI_x",
                         "next": [], "subs": [], "params": {}},
            "script_x": {"type": "@General$Script", "name": "script_x",
                         "next": [], "subs": [], "params": {}},
        },
    }
    mapping = detect_openai_script_renames(flow)
    check("OpenAI_x" not in mapping, "衝突ガード: 既存 script_x と衝突する OpenAI_x はスキップ")


def test_expand_aux() -> None:
    flow = _fixture_flow()
    mp = expand_mapping_with_aux(flow, {"OpenAI_用件確認": "script_用件確認"})
    check(mp.get("saveDefault-OpenAI_用件確認") == "saveDefault-script_用件確認",
          "expand_mapping_with_aux: 補助対を補完")


# --- issue #273: 整合性検証（残骸検出 + ダングリング参照検出） ---

def test_verify_residue_and_clean_after_rename() -> None:
    """残骸 1 件を検出し、rename 後は残骸ゼロ・start も追従・dangling ゼロ。"""
    flow = {
        "name": "t$v", "start": "OpenAI_確認",
        "modules": {
            "OpenAI_確認": {"type": "@General$Script", "name": "OpenAI_確認",
                          "next": [{"condition": "^.*$", "label": "n", "nextModuleName": "終端"}],
                          "subs": [], "params": {}},
            "終端": {"type": "@IVR$Disconnect", "name": "終端", "next": [], "subs": [], "params": {}},
        },
    }
    v = verify_flow_integrity(flow)
    check(v["residue"] == ["OpenAI_確認"], f"verify: 残骸 1 件検出（実際 {v['residue']}）")
    check(v["dangling"] == [], f"verify: 参照は全実在で dangling 0（実際 {v['dangling']}）")

    apply_rename_mapping(flow, detect_openai_script_renames(flow))
    v2 = verify_flow_integrity(flow)
    check(v2["residue"] == [], "verify: rename 後 残骸ゼロ")
    check(v2["dangling"] == [], "verify: rename 後 dangling ゼロ")
    check(flow["start"] == "script_確認", "verify: start も rename 追従（残骸ゼロ）")


def test_detect_partial_rename_dangling() -> None:
    """部分リネーム: 本体は script_ にしたが 上流 next と CMR module1Name が旧名のまま残る。

    #273 の再発シナリオ（手動パッチで参照を取りこぼす）を機械的に捕捉できることを確認。
    """
    flow = {
        "name": "t$d", "start": "入口",
        "modules": {
            "入口": {"type": "drjoy^STT$AmiVoice_STT", "name": "入口",
                    "next": [{"condition": "^.*$", "label": "s", "nextModuleName": "OpenAI_用件"}],
                    "subs": [], "params": {}},
            "script_用件": {"type": "@General$Script", "name": "script_用件",
                          "next": [], "subs": [], "params": {}},
            "CMR": {"type": "drjoy^Context Logic$ContextMatchRouter", "name": "CMR",
                   "next": [], "subs": [],
                   "params": {"module1Name": "OpenAI_用件", "module2Name": "<%var%>"}},
            # #348: Re-confirmation の nodeName も旧名のまま取りこぼされた（復唱が壊れる穴）
            "復唱": {"type": "drjoy^Text To Speech$Re-confirmation node data", "name": "復唱",
                   "next": [], "subs": [], "params": {"nodeName": "OpenAI_用件"}},
        },
    }
    d = detect_dangling_references(flow)
    pairs = {(x["field"], x["target"]) for x in d}
    check(("next[0].nextModuleName", "OpenAI_用件") in pairs, "dangling: 上流 next 旧名を検出")
    check(("params.module1Name", "OpenAI_用件") in pairs, "dangling: CMR module1Name 旧名を検出")
    check(("params.nodeName", "OpenAI_用件") in pairs, "dangling: Re-confirmation nodeName 旧名を検出（#348）")
    check(all(t != "<%var%>" for _, t in pairs), "dangling: <%var%> 変数形式はスキップ")
    check(len(d) == 3, f"dangling: 検出は 3 件（実際 {len(d)}）")
    # 残骸は無い（OpenAI_用件 はモジュールとして存在せず、Script は正しく script_ 命名）
    check(detect_openai_residue(flow) == [], "dangling ケースに Script 残骸は無い")


def test_verify_clean_flow() -> None:
    """健全なフロー（残骸なし・全参照実在）は residue/dangling とも空。"""
    flow = {
        "name": "t$ok", "start": "script_x",
        "modules": {
            "script_x": {"type": "@General$Script", "name": "script_x",
                        "next": [{"condition": "^.*$", "label": "n", "nextModuleName": "終端"}],
                        "subs": [], "params": {}},
            "終端": {"type": "@IVR$Disconnect", "name": "終端", "next": [], "subs": [], "params": {}},
        },
    }
    v = verify_flow_integrity(flow)
    check(v["residue"] == [] and v["dangling"] == [], "verify: 健全フローは問題ゼロ")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    test_detect_and_apply()
    test_idempotent()
    test_collision_guard()
    test_expand_aux()
    test_verify_residue_and_clean_after_rename()
    test_detect_partial_rename_dangling()
    test_verify_clean_flow()
    if _FAILS:
        print(f"FAIL: {len(_FAILS)} 件")
        for f in _FAILS:
            print(f"  - {f}")
        return 1
    print("PASS: rename_openai_modules 全ケース OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
