# -*- coding: utf-8 -*-
"""test_node_reference.py — NODE-001（params.nodeName broken_ref）回帰テスト（#358）。

復唱(Re-confirmation node data)/保存(saveNodeData2Session)の params.nodeName が
存在しないモジュールを指す（broken_ref）と CRITICAL 検出。空 / <%context%> はスキップ。

stdlib のみ・standalone（python schemas/test_node_reference.py）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import validator as v  # noqa: E402

_failures = []


def _check(cond, msg):
    if not cond:
        _failures.append(msg)


def _node001(modules):
    r = v.ValidationResult(file_path="t")
    v.validate_node_reference({"modules": modules}, r)
    return [i for i in r.issues if i.code == "NODE-001"]


def _reconfirm(node_name):
    return {"type": "drjoy^Text To Speech$Re-confirmation node data",
            "params": {"nodeName": node_name, "prompt": "{tts_g:#data#}"}, "next": []}


def _savenode(node_name):
    return {"type": "drjoy^Persistence$saveNodeData2Session",
            "params": {"nodeName": node_name}, "next": []}


# 存在するモジュールを参照 → 検出なし
issues = _node001({"OpenAI_用件": {"type": "generate_by_OpenAI", "params": {}, "next": []},
                   "復唱_用件": _reconfirm("OpenAI_用件")})
_check(issues == [], f"実在 nodeName で NODE-001 が出てはいけない: {issues}")

# 存在しないモジュールを参照（復唱） → CRITICAL
issues = _node001({"復唱_用件": _reconfirm("OpenAI_存在しない")})
_check(len(issues) == 1 and issues[0].severity == "CRITICAL",
       f"broken nodeName(復唱) は NODE-001 CRITICAL であるべき: {issues}")

# 存在しないモジュールを参照（saveNodeData2Session） → CRITICAL
issues = _node001({"save_X": _savenode("script_不在")})
_check(len(issues) == 1, f"broken nodeName(saveNodeData2Session) も検出されるべき: {issues}")

# 空 nodeName → スキップ（受入済みフローの正当パターン）
issues = _node001({"復唱_保留": _reconfirm("")})
_check(issues == [], f"空 nodeName は NODE-001 対象外であるべき: {issues}")

# <%context%> 形 → スキップ
issues = _node001({"復唱_ctx": _reconfirm("<%classification%>")})
_check(issues == [], f"<%context%> 形 nodeName は NODE-001 対象外であるべき: {issues}")

# nodeName キー自体が無いモジュール → 無関係（検出なし）
issues = _node001({"tts": {"type": "drjoy^Text To Speech$TTS", "params": {"prompt": "x"}, "next": []}})
_check(issues == [], f"nodeName を持たないモジュールは対象外: {issues}")


if _failures:
    print("FAIL:")
    for f in _failures:
        print("  -", f)
    sys.exit(1)
print("PASS: test_node_reference (NODE-001 #358)")
