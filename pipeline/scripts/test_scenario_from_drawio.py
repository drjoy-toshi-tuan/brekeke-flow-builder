# -*- coding: utf-8 -*-
"""test_scenario_from_drawio.py — drawio→設計書YAML emitter のスモークテスト。

shinryo composer golden を入力に build_spec を回し、工場デフォルト合成と
構造復元（型判定・subflow 重複排除・termination 既定）を assert する。
  python test_scenario_from_drawio.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drawio_to_scenario import parse_drawio  # noqa: E402
from scenario_from_drawio import build_spec, extract_title  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "drawio_parser_fixtures", "shinryo_composer_golden.drawio")


def run():
    nodes, edges = parse_drawio(FIX)
    spec = build_spec(nodes, edges, extract_title(FIX))
    by_step = {b["step"]: b for b in spec["scenario_flow"]}
    subflow_names = [s["name"] for s in spec["flow_structure"]["subflows"]]

    cases = [
        ("basic_info.flow_type 設定", spec["basic_info"].get("flow_type") == "subflow"),
        ("CMR_phonetype = context_match_router (slot より ref 優先)",
         by_step["CMR_phonetype"]["type"] == "context_match_router"),
        ("CMR_phonetype conditions 復元 (携帯/other)",
         len(by_step["CMR_phonetype"].get("conditions", [])) == 2),
        ("冒頭 = opening", by_step["冒頭"]["type"] == "opening"),
        ("氏名聴取 = subflow", by_step["氏名聴取"]["type"] == "subflow"),
        ("subflow 重複排除 (= ユニーク)", len(subflow_names) == len(set(subflow_names))),
        ("用件確認 output_labels に受け皿 other を含めない",
         "other" not in by_step["用件確認"].get("output_labels", [])),
        ("全 termination に completion_flag_name",
         all("completion_flag_name" in t for t in spec["termination_patterns"])),
        ("sms_flag に禁止値 -1 なし",
         all(t["sms_flag"] != "-1" for t in spec["termination_patterns"])),
    ]

    npass = sum(1 for _, ok in cases if ok)
    for name, ok in cases:
        print(("PASS " if ok else "FAIL ") + name)
    print("-" * 50)
    print(f"{npass}/{len(cases)} PASS")
    return npass == len(cases)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    sys.exit(0 if run() else 1)
