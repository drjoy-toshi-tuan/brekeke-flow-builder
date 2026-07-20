# -*- coding: utf-8 -*-
"""test_resolve_hearing_backend.py — A3 surfacing 駆動 resolver の純関数テスト。

scaffold_generator.resolve_hearing_backend を、modules/ への I/O 非依存 (surfaces はインラインスタブ)
で代表ケース検証する。stdlib のみ・PyYAML 不要・standalone 実行 (python scripts/test_resolve_hearing_backend.py)。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scaffold_generator import resolve_hearing_backend  # noqa: E402

# 用件 inquiry の surface スタブ (part.json output_labels 相当)
INQUIRY_SURFACE = [{
    "part_id": "inquiry_classifier", "spec": "外来予約FULL", "scope": None,
    "labels": {"予約", "予約変更", "予約キャンセル", "予約確認", "その他問合せ", "NO_RESULT"},
}]

# yes_no の surface スタブ (肯定/否定/NO_RESULT)。真性 polar 正準化 (_canon_polar_core) の検証用。
YESNO_SURFACE = [{
    "part_id": "yes_no_classifier", "spec": None, "scope": None,
    "labels": {"肯定", "否定", "NO_RESULT"},
}]


def _case(name, got, want_backend, want_detail_contains=None):
    ok = got[0] == want_backend
    if ok and want_detail_contains is not None:
        ok = want_detail_contains in got[1]
    print(("PASS " if ok else "FAIL ") + name + (f"  → {got}" if not ok else ""))
    return ok


def run():
    results = []

    # 1) enum + 用件ラベルが surface に一致 → deterministic(part:spec)
    results.append(_case(
        "enum 用件→inquiry_classifier:外来予約FULL",
        resolve_hearing_backend(
            "enum", "inquiryType", set(),
            conditions=[{"match": "予約"}, {"match": "予約変更"}, {"match": "予約キャンセル"},
                        {"match": "予約確認"}, {"match": "other"}],
            surfaces=INQUIRY_SURFACE),
        "deterministic", "inquiry_classifier:外来予約FULL"))

    # 2) enum + 未知ラベル + surface 空 → block(none)
    results.append(_case(
        "enum 未知ラベル→block none",
        resolve_hearing_backend("enum", "somethingElse", set(),
                                conditions=[{"match": "foo"}, {"match": "bar"}], surfaces=[]),
        "block", "none"))

    # 3) enum + 診療科 save_to + 未surface → block(known:department_classifier)
    results.append(_case(
        "enum 診療科未surface→block known",
        resolve_hearing_backend("enum", "clinicalDepartment", set(),
                                conditions=[{"match": "内科"}, {"match": "外科"}], surfaces=[]),
        "block", "known:department_classifier"))

    # 4) datetime → deterministic(date)
    results.append(_case(
        "datetime→deterministic date",
        resolve_hearing_backend("datetime", "reservationDate", set()),
        "deterministic", "date"))

    # 5) text → collect_only
    results.append(_case(
        "text→collect_only",
        resolve_hearing_backend("text", "callReason", set()),
        "collect_only"))

    # 6) save_to が patch_box 例外 → openai (format に依らず最優先)
    results.append(_case(
        "exception→openai",
        resolve_hearing_backend("enum", "faqQuery", {"faqQuery"},
                                conditions=[{"match": "駐車場"}], surfaces=[]),
        "openai", "patch_box"))

    # 7) slot_type=生年月日 → deterministic(dob_normalizer:slot)
    results.append(_case(
        "slot 生年月日→dob_normalizer:slot",
        resolve_hearing_backend("text", "patientDateOfBirth", set(), slot_type="生年月日"),
        "deterministic", "dob_normalizer:slot"))

    # 8) 収集系 context (氏名) → collect_only
    results.append(_case(
        "collect-only context 氏名→collect_only",
        resolve_hearing_backend("text", "patientName", set()),
        "collect_only"))

    # 9) 真性 polar はい/いいえ → 肯定/否定 正準化 → deterministic(yes_no_classifier)
    results.append(_case(
        "polar はい/いいえ→yes_no_classifier",
        resolve_hearing_backend("enum", "medicalTicket", set(),
                                conditions=[{"match": "はい"}, {"match": "いいえ"}],
                                surfaces=YESNO_SURFACE),
        "deterministic", "yes_no_classifier"))

    # 10) 真性 polar あり/なし → deterministic(yes_no_classifier)
    results.append(_case(
        "polar あり/なし→yes_no_classifier",
        resolve_hearing_backend("enum", "referralLetter", set(),
                                conditions=[{"match": "あり"}, {"match": "なし"}],
                                surfaces=YESNO_SURFACE),
        "deterministic", "yes_no_classifier"))

    # 11) 該当/非該当 も polar → deterministic(yes_no_classifier)
    results.append(_case(
        "polar 該当/非該当→yes_no_classifier",
        resolve_hearing_backend("enum", "reservationDecision", set(),
                                conditions=[{"match": "該当"}, {"match": "非該当"}],
                                surfaces=YESNO_SURFACE),
        "deterministic", "yes_no_classifier"))

    # 12) ★非polar 二択 (企業/個人=n_choice 領分) は yes_no surface があっても誤 surface しない → block none
    results.append(_case(
        "非polar 企業/個人→block none (誤surface防止)",
        resolve_hearing_backend("enum", "companyCheck", set(),
                                conditions=[{"match": "企業"}, {"match": "個人"}],
                                surfaces=YESNO_SURFACE),
        "block", "none"))

    # 13) ★polar と非polar の混在 (はい/個人) も触らない → block none
    results.append(_case(
        "混在 はい/個人→block none (gate)",
        resolve_hearing_backend("enum", "mixedCtx", set(),
                                conditions=[{"match": "はい"}, {"match": "個人"}],
                                surfaces=YESNO_SURFACE),
        "block", "none"))

    npass = sum(1 for r in results if r)
    print("-" * 50)
    print(f"{npass}/{len(results)} PASS")
    return npass == len(results)


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
