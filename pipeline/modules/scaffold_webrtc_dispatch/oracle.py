# -*- coding: utf-8 -*-
"""scaffold_webrtc_dispatch — 独立オラクル。

scripts/scaffold_generator.py の実装から独立に、null_check ブロック型 / get-header
自動配置 / incoming-classifier の webrtc_next 配線が生成すべき Brekeke モジュール JSON を
再実装する（REQUIREMENTS.md 参照）。test_oracle.py がこの期待値と実装出力を突き合わせる。
"""

NULL_CHECK_TYPE = "drjoy^Context Logic$null-check"
GET_HEADER_TYPE = "drjoy^Incoming$get-header"


def _next_slot(condition, label, next_module):
    return {"condition": condition, "label": label, "nextModuleName": next_module}


def _empty_slot():
    return {"condition": "", "label": "", "nextModuleName": ""}


def expected_null_check(name, key, true_next, false_next):
    """null_check ブロック型が生成すべきモジュール JSON (name, data) タプル。"""
    next_ = [
        _next_slot("^true$", "true", true_next),
        _next_slot("^false$", "false", false_next),
    ]
    while len(next_) < 10:
        next_.append(_empty_slot())
    data = {
        "layout": {"x": 0, "y": 0},
        "next": next_,
        "subs": [{"moduleName": "", "label": ""}] * 3,
        "name": name,
        "description": "",
        "matchingmethod": 1,
        "type": NULL_CHECK_TYPE,
        "params": {"key": key},
    }
    return (name, data)


def expected_get_header(name, next_module):
    """get-header モジュール JSON (name, data) タプル。1 スロットのみ（padding なし）。"""
    data = {
        "layout": {"x": 0, "y": 0},
        "next": [_next_slot("^*$", "next", next_module)],
        "subs": [{"moduleName": "", "label": ""}] * 3,
        "name": name,
        "description": "",
        "matchingmethod": 1,
        "type": GET_HEADER_TYPE,
        "params": {},
    }
    return (name, data)


def expected_incoming_classifier_next(anon_next, regular_next, webrtc_next=None):
    """build_incoming_classifier の next 配列（WebRTC ラベルの遷移先を検証する用）。

    webrtc_next 省略時は regular_next にフォールバック（webrtc_prefill 未使用の既存施設と同一）。
    """
    if webrtc_next is None:
        webrtc_next = regular_next
    return [
        _next_slot("^非通知$", "非通知", anon_next),
        _next_slot("^固定$", "固定", regular_next),
        _next_slot("^海外$", "海外", regular_next),
        _next_slot("^携帯$", "携帯", regular_next),
        _next_slot("^WebRTC$", "WebRTC", webrtc_next),
        _next_slot("^*$", "その他", regular_next),
    ]


def webrtc_prefill_wiring(after_incoming, header_name="WebRTCヘッダ取得"):
    """opening ブロックが webrtc_prefill: true のとき生成すべき2点セット。

    Returns: (get_header_tuple, incoming_classifier_next_list)
    get-header 自体の next は after_incoming と同一（固定/携帯/その他と合流する）。
    """
    header = expected_get_header(header_name, after_incoming)
    incoming_next = expected_incoming_classifier_next(
        anon_next="ANON_PLACEHOLDER",
        regular_next=after_incoming,
        webrtc_next=header_name,
    )
    return header, incoming_next
