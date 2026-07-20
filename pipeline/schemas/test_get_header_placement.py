# -*- coding: utf-8 -*-
"""test_get_header_placement.py — get-header 標準配置の回帰テスト（#338）。

basic_info.use_get_header=true のとき、opening チェーンが
  冒頭(Custom Wait) → 受信情報取込(get-header) → コンテキスト設定(saveContextModel2DB)
になること（全シナリオ固定・#338）。false/未指定では従来通り 冒頭 → コンテキスト設定。

stdlib のみ・standalone（python schemas/test_get_header_placement.py）。
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))  # scaffold_generator

import scaffold_generator as sg  # noqa: E402

_failures = []


def _check(cond, msg):
    if not cond:
        _failures.append(msg)


def _spec(use_gh):
    """opening + termination だけの最小 scenario_flow spec。"""
    bi = {"facility_name": "検証", "flow_name": "検証"}
    if use_gh is not None:
        bi["use_get_header"] = use_gh
    return {
        "version": "2.0",
        "basic_info": bi,
        "flow_structure": {"type": "standalone",
                           "flows": [{"name": "検証", "role": "main"}], "subflows": []},
        "context_fields": [],
        "termination_patterns": [
            {"name": "非通知", "completion_flag_name": "完了_非通知"},
            {"name": "時間外", "completion_flag_name": "完了_時間外"},
            {"name": "聴取失敗", "completion_flag_name": "完了_失敗"},
        ],
        "scenario_flow": [
            {"step": "冒頭", "type": "opening", "next": "終話"},
            {"step": "終話", "type": "termination"},
        ],
    }


def _nexts(mod):
    return [n.get("nextModuleName") for n in mod.get("next", []) if n.get("nextModuleName")]


# --- use_get_header=true: wait → 受信情報取込(get-header) → コンテキスト設定 ---
m = sg.generate_scaffold_v2(_spec(True), stem="t")["modules"]
_check(_nexts(m["冒頭"]) == ["受信情報取込"],
       f"use_get_header=true: 冒頭.next は 受信情報取込 であるべき: {_nexts(m.get('冒頭', {}))}")
_check("受信情報取込" in m, "use_get_header=true: 受信情報取込(get-header) が生成されるべき")
if "受信情報取込" in m:
    _check(m["受信情報取込"]["type"] == "drjoy^Incoming$get-header",
           f"受信情報取込 の type が get-header であるべき: {m['受信情報取込']['type']}")
    _check(_nexts(m["受信情報取込"]) == ["コンテキスト設定"],
           f"受信情報取込.next は コンテキスト設定 であるべき: {_nexts(m['受信情報取込'])}")

# --- use_get_header=false: 従来通り wait → コンテキスト設定（get-header なし） ---
m = sg.generate_scaffold_v2(_spec(False), stem="t")["modules"]
_check(_nexts(m["冒頭"]) == ["コンテキスト設定"],
       f"use_get_header=false: 冒頭.next は コンテキスト設定 であるべき: {_nexts(m.get('冒頭', {}))}")
_check("受信情報取込" not in m, "use_get_header=false: 受信情報取込 は生成されないべき")

# --- 未指定（デフォルト）: false と同じ（後方互換） ---
m = sg.generate_scaffold_v2(_spec(None), stem="t")["modules"]
_check(_nexts(m["冒頭"]) == ["コンテキスト設定"],
       f"未指定: 冒頭.next は コンテキスト設定 であるべき（後方互換）: {_nexts(m.get('冒頭', {}))}")
_check("受信情報取込" not in m, "未指定: 受信情報取込 は生成されないべき（後方互換）")


if _failures:
    print("FAIL:")
    for f in _failures:
        print("  -", f)
    sys.exit(1)
print("PASS: test_get_header_placement (#338 get-header 標準配置)")
