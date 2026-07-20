#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bivr_patch.py の回帰テスト（実案件由来: 新水巻 CMR 入替 / JAとりで 参照元・型変更）。

実行: python3 tools/test_bivr_patch.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE / "bivr_patch.py"

PASS = 0
FAIL = 0


def _flow():
    """新水巻/JAとりで実案件を模した最小フロー JSON。"""
    return {
        "name": "テスト$健診",
        "start": "冒頭",
        "modules": {
            "冒頭": {"type": "Custom$wait", "params": {},
                     "next": [{"condition": "^.*$", "label": "next", "nextModuleName": "用件分岐"}]},
            "用件分岐": {"type": "drjoy^Context Logic$ContextMatchRouter",
                         "params": {"module1Name": "openAI_確認_用件", "module2Name": "openAI_確認_用件"},
                         "next": [
                             {"condition": "^1$", "label": "組み合わせ1", "nextModuleName": "予約_受診歴"},
                             {"condition": "^2$", "label": "組み合わせ2", "nextModuleName": "変更_予約日"},
                             {"condition": "^3$", "label": "組み合わせ3", "nextModuleName": "変更_予約日"},
                             {"condition": "^4$", "label": "組み合わせ4", "nextModuleName": "相談_結果確認"},
                             {"condition": "^5$", "label": "組み合わせ5", "nextModuleName": "相談_問合せ"},
                         ]},
            "確認_理由": {"type": "drjoy^TS Custom Module$Re-confirmation node data",
                          "params": {"nodeName": "openAI_確認_用件"},
                          "next": [{"condition": "^.*$", "label": "next", "nextModuleName": "予約_受診歴"}]},
            "予約_受診歴": {"type": "drjoy^Text To Speech$Text to speech", "params": {"prompt": ""}, "next": []},
            "変更_予約日": {"type": "drjoy^Text To Speech$Text to speech", "params": {"prompt": ""}, "next": []},
            "相談_問合せ": {"type": "drjoy^Text To Speech$Text to speech", "params": {"prompt": ""}, "next": []},
            "相談_結果確認": {"type": "drjoy^Text To Speech$Text to speech", "params": {"prompt": ""}, "next": []},
            "openAI_確認_用件": {"type": "drjoy^OpenAI$generate_by_OpenAI", "params": {}, "next": []},
        },
    }


def run(tmp: Path, patch_yaml: str, mode: str = "--apply"):
    jp = tmp / "flow.json"
    pp = tmp / "patch.yaml"
    jp.write_text(json.dumps(_flow(), ensure_ascii=False), encoding="utf-8")
    pp.write_text(patch_yaml, encoding="utf-8")
    r = subprocess.run([sys.executable, str(TOOL), "--json", str(jp), "--patch", str(pp), mode],
                       capture_output=True, text=True, encoding="utf-8")
    after = json.loads(jp.read_text(encoding="utf-8"))
    return r, after


def check(name: str, cond: bool, detail: str = ""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"[PASS] {name}")
    else:
        FAIL += 1
        print(f"[FAIL] {name} {detail}")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # 1) 新水巻 修正①: CMR slot4/5 の入替（expect ガードつき）
        r, after = run(tmp, """
version: 1
target_flow: "テスト$健診"
patches:
  - {op: set_next, module: 用件分岐, slot: 4, next: 相談_問合せ, expect: 相談_結果確認}
  - {op: set_next, module: 用件分岐, slot: 5, next: 相談_結果確認, expect: 相談_問合せ}
""")
        nx = after["modules"]["用件分岐"]["next"]
        check("CMR入替 exit0", r.returncode == 0, r.stderr)
        check("CMR入替 slot4", nx[3]["nextModuleName"] == "相談_問合せ")
        check("CMR入替 slot5", nx[4]["nextModuleName"] == "相談_結果確認")
        check("CMR入替 condition不変", nx[3]["condition"] == "^4$")
        check("touched 出力", '"用件分岐"' in r.stdout)

        # 2) JAとりで 修正②: 参照元変更（set_param）
        r, after = run(tmp, """
version: 1
patches:
  - {op: set_param, module: 用件分岐, param: module1Name, value: "<% classification %>", expect: "openAI_確認_用件"}
""")
        check("set_param exit0", r.returncode == 0, r.stderr)
        check("set_param 値", after["modules"]["用件分岐"]["params"]["module1Name"] == "<% classification %>")

        # 3) JAとりで 修正①: 型変更 + params 全置換（set_type）
        r, after = run(tmp, """
version: 1
patches:
  - op: set_type
    module: 確認_理由
    type: "drjoy^Text To Speech$Text to speech"
    expect: "drjoy^TS Custom Module$Re-confirmation node data"
    params: {prompt: "", stop_by_dtmf: "No", category_words: ""}
""")
        m = after["modules"]["確認_理由"]
        check("set_type exit0", r.returncode == 0, r.stderr)
        check("set_type 型", m["type"] == "drjoy^Text To Speech$Text to speech")
        check("set_type params置換", m["params"] == {"prompt": "", "stop_by_dtmf": "No", "category_words": ""})
        check("set_type next温存", m["next"][0]["nextModuleName"] == "予約_受診歴")

        # 4) fail-closed: expect 不一致 → exit2 かつ一切未適用（後続の正しい op も適用されない）
        r, after = run(tmp, """
version: 1
patches:
  - {op: set_next, module: 用件分岐, slot: 4, next: 相談_問合せ, expect: 間違った期待値}
  - {op: set_param, module: 用件分岐, param: module1Name, value: "X"}
""")
        check("expect不一致 exit2", r.returncode == 2, f"rc={r.returncode}")
        check("expect不一致 slot4未変更", after["modules"]["用件分岐"]["next"][3]["nextModuleName"] == "相談_結果確認")
        check("expect不一致 後続op未適用", after["modules"]["用件分岐"]["params"]["module1Name"] == "openAI_確認_用件")

        # 5) fail-closed: 存在しないモジュール / 遷移先
        r, _ = run(tmp, 'patches:\n  - {op: set_next, module: 存在しない, slot: 1, next: 冒頭}\n')
        check("不明モジュール exit2", r.returncode == 2)
        r, _ = run(tmp, 'patches:\n  - {op: set_next, module: 用件分岐, slot: 4, next: 存在しない先}\n')
        check("不明遷移先 exit2", r.returncode == 2)

        # 6) target_flow 不一致
        r, _ = run(tmp, 'target_flow: "別施設$別flow"\npatches:\n  - {op: set_param, module: 冒頭, param: wait, value: "1000"}\n')
        check("target_flow不一致 exit2", r.returncode == 2)

        # 7) dry-run は書き込まない
        r, after = run(tmp, 'patches:\n  - {op: set_next, module: 用件分岐, slot: 4, next: 相談_問合せ}\n',
                       mode="--dry-run")
        check("dry-run exit0", r.returncode == 0, r.stderr)
        check("dry-run 未変更", after["modules"]["用件分岐"]["next"][3]["nextModuleName"] == "相談_結果確認")

        # 8) label 指定でスロット特定
        r, after = run(tmp, 'patches:\n  - {op: set_next, module: 用件分岐, label: 組み合わせ2, next: 予約_受診歴}\n')
        check("label指定 exit0", r.returncode == 0, r.stderr)
        check("label指定 変更", after["modules"]["用件分岐"]["next"][1]["nextModuleName"] == "予約_受診歴")

    print(f"\n{PASS}/{PASS + FAIL} PASS")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
