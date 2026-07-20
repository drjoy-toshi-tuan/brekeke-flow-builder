# -*- coding: utf-8 -*-
"""scaffold_webrtc_dispatch — オラクル単体テスト。

scripts/scaffold_generator.py の build_null_check / build_get_header /
build_incoming_classifier(webrtc_next=...) が oracle.py の期待値と一致するかを検証する。

実行: python modules/scaffold_webrtc_dispatch/test_oracle.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.join(_HERE, "..", "..", "scripts")

sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.abspath(_SCRIPTS_DIR))

import oracle  # noqa: E402
import scaffold_generator as sg  # noqa: E402

FAILS = []


def check(label, got, expected):
    if got != expected:
        FAILS.append((label, expected, got))


def run_null_check_cases():
    cases = [
        ("module-name key", "null_check_用件", "OpenAI_用件", "次A", "次B"),
        ("session-var key", "null_check_診察券", "<% medicalCardNumber %>", "スキップ", "診察券番号聴取"),
        ("same true/false target", "null_check_共通", "<% patientName %>", "共通遷移", "共通遷移"),
    ]
    for label, name, key, true_next, false_next in cases:
        got = sg.build_null_check(name, key, true_next, false_next)
        expected = oracle.expected_null_check(name, key, true_next, false_next)
        check(f"build_null_check[{label}]", got, expected)


def run_get_header_cases():
    got = sg.build_get_header("WebRTCヘッダ取得", "受付時間判定")
    expected = oracle.expected_get_header("WebRTCヘッダ取得", "受付時間判定")
    check("build_get_header[basic]", got, expected)


def run_incoming_classifier_cases():
    # 1) webrtc_next 省略 → regular_next にフォールバック（既存施設への回帰なし）
    _, data_default = sg.build_incoming_classifier("非通知案内", "受付時間判定")
    expected_default = oracle.expected_incoming_classifier_next("非通知案内", "受付時間判定")
    check("build_incoming_classifier[default fallback]", data_default["next"], expected_default)

    # 2) webrtc_next 指定 → WebRTC ラベルのみ差し替わり、他ラベルは不変
    _, data_webrtc = sg.build_incoming_classifier(
        "非通知案内", "受付時間判定", webrtc_next="WebRTCヘッダ取得"
    )
    expected_webrtc = oracle.expected_incoming_classifier_next(
        "非通知案内", "受付時間判定", webrtc_next="WebRTCヘッダ取得"
    )
    check("build_incoming_classifier[webrtc override]", data_webrtc["next"], expected_webrtc)


def run_webrtc_prefill_wiring_case():
    header_expected, incoming_next_expected = oracle.webrtc_prefill_wiring("受付時間判定")

    header_got = sg.build_get_header("WebRTCヘッダ取得", "受付時間判定")
    check("webrtc_prefill_wiring[get-header]", header_got, header_expected)

    _, incoming_data_got = sg.build_incoming_classifier(
        "ANON_PLACEHOLDER", "受付時間判定", webrtc_next="WebRTCヘッダ取得"
    )
    check("webrtc_prefill_wiring[incoming next]", incoming_data_got["next"], incoming_next_expected)


def main():
    run_null_check_cases()
    run_get_header_cases()
    run_incoming_classifier_cases()
    run_webrtc_prefill_wiring_case()

    total = 3 + 1 + 2 + 2
    passed = total - len(FAILS)
    print(f"[scaffold_webrtc_dispatch oracle] {passed}/{total} PASS")
    for label, expected, got in FAILS:
        print(f"  FAIL: {label}\n    expected={expected!r}\n    got     ={got!r}")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    sys.exit(main())
