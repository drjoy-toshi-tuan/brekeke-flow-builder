# -*- coding: utf-8 -*-
"""test_validator_sb003.py — SB-003（確認グループ save2db 共有整合）回帰テスト（#253）。

1 ブロックグループ（TTS=X / 入力_X / リトライ_X）が同一 save2db を共有することを保証する。
TTS だけに save2db が付き入力/リトライが空（または別 save）だと回答取得前保存で取りこぼす（#253）。
stdlib のみ・standalone（python schemas/test_validator_sb003.py）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import validator as v  # noqa: E402

_failures = []


def _sb003(modules: dict):
    r = v.ValidationResult(file_path="t")
    v.validate_save2db_group_consistency({"modules": modules}, r)
    return [i for i in r.issues if i.code == "SB-003"]


def _save(name):
    return [{"label": name, "moduleName": name}]


def _case(label, modules, want_modules):
    got = sorted(i.module for i in _sb003(modules))
    ok = got == sorted(want_modules)
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: flagged={got} (want {sorted(want_modules)})")
    if not ok:
        _failures.append(label)


def main():
    # 崩れ: TTS に save・入力/リトライ空 → 入力/リトライを flag
    _case("TTSのみsave・入力/リトライ空", {
        "用件": {"type": "Text to Speech", "subs": _save("save-classification")},
        "入力_用件": {"type": "Speech to Text", "subs": []},
        "リトライ_用件": {"type": "Retry", "subs": []},
    }, ["入力_用件", "リトライ_用件"])

    # 崩れ: 入力だけ空（#253 氏名パターン: TTS+リトライ有・入力空）
    _case("入力だけ空", {
        "患者氏名": {"type": "Text to Speech", "subs": _save("save-patientName")},
        "入力_患者氏名": {"type": "Speech to Text", "subs": []},
        "リトライ_患者氏名": {"type": "Retry", "subs": _save("save-patientName")},
    }, ["入力_患者氏名"])

    # 正常: 3ノード同一 save → flag なし
    _case("3ノード同一save（正常）", {
        "用件": {"type": "Text to Speech", "subs": _save("save-classification")},
        "入力_用件": {"type": "Speech to Text", "subs": _save("save-classification")},
        "リトライ_用件": {"type": "Retry", "subs": _save("save-classification")},
    }, [])

    # 正常: 入力/リトライのみ同一save（TTS無し=Soniox等）→ flag なし
    _case("入力/リトライのみ同一save（TTS無）", {
        "入力_薬局名": {"type": "Speech to Text", "subs": _save("save-pharmacy")},
        "リトライ_薬局名": {"type": "Retry", "subs": _save("save-pharmacy")},
    }, [])

    # 対象外: グループ全体に save 無し（録音不要）→ flag なし
    _case("グループ全体save無（対象外）", {
        "確認": {"type": "Text to Speech", "subs": []},
        "入力_確認": {"type": "Speech to Text", "subs": []},
        "リトライ_確認": {"type": "Retry", "subs": []},
    }, [])

    # 崩れ: 別 save が混在 → 不一致ノードを flag
    _case("別saveが混在", {
        "用件": {"type": "Text to Speech", "subs": _save("save-A")},
        "入力_用件": {"type": "Speech to Text", "subs": _save("save-B")},
        "リトライ_用件": {"type": "Retry", "subs": _save("save-A")},
    }, ["入力_用件"])

    print()
    if _failures:
        print(f"[FAILED] {len(_failures)} 件: {', '.join(_failures)}")
        return 1
    print("[OK] 全テスト PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
