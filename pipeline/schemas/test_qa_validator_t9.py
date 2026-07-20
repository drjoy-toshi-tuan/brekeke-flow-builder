# -*- coding: utf-8 -*-
"""test_qa_validator_t9.py — T-9（新規/移行は 1flow 必須）回帰テスト（#255）。

factory-v2 では新規作成・Gen2/Gen1 移行の個人情報聴取を subflow 分割せず inline で配置する。
qa_validator.check_t9 が、古い director 製のサブフロー分割型を入口で CRITICAL 弾きする契約を固定する。
stdlib のみ・standalone（python schemas/test_qa_validator_t9.py）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import qa_validator as q  # noqa: E402

_failures = []


def _fires(d) -> bool:
    q._issues.clear()
    q.check_t9(d)
    return any(i.code == "T-9" and i.severity == "CRITICAL" for i in q._issues)


def _case(label, d, want):
    got = _fires(d)
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {label}: T-9={got} (want {want})")
    if not ok:
        _failures.append(label)


def _spec(work_type, targets):
    bi = {} if work_type is None else {"work_type": work_type}
    return {"basic_info": bi, "flow_structure": {"subflows": [{"target": t} for t in targets]}}


def main():
    # 弾く: new / 移行 で個人情報サブフローを分割している
    _case("new + 氏名聴取 subflow", _spec("new", ["氏名聴取"]), True)
    _case("new + 4 個人情報 subflow", _spec("new", ["氏名聴取", "生年月日聴取", "電話番号聴取", "診察券番号聴取"]), True)
    _case("gen2_migration + 個人情報聴取 wrapper", _spec("gen2_migration", ["個人情報聴取（診察券・氏名）"]), True)
    _case("gen1_migration + 電話番号聴取 subflow", _spec("gen1_migration", ["電話番号聴取"]), True)
    _case("work_type 未設定（=new扱い） + 氏名聴取 subflow", _spec(None, ["氏名聴取"]), True)
    # 弾かない: modify / RAGのみ / subflow空
    _case("modify + 氏名聴取 subflow（既存修正は対象外）", _spec("modify", ["氏名聴取"]), False)
    _case("new + RAG検索のみ（FAQは許容）", _spec("new", ["RAG検索"]), False)
    _case("new + subflow 空（1flow）", _spec("new", []), False)
    _case("new + 個人情報+RAG 混在 → 個人情報があるので弾く", _spec("new", ["氏名聴取", "RAG検索"]), True)

    print()
    if _failures:
        print(f"[FAILED] {len(_failures)} 件: {', '.join(_failures)}")
        return 1
    print("[OK] 全テスト PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
