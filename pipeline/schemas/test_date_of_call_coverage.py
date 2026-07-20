# -*- coding: utf-8 -*-
"""test_date_of_call_coverage.py — DOC-001（DateOfCall 出力値カバレッジ）回帰テスト（#326）。

DateOfCall Classifier は固定出力値（時間後/時間一致/時間前・エラー時 ERROR）を返し、
出力値にマッチする next 条件が無いと実行時に通話が強制終了する。分岐は condition マッチで
行われ label は分岐に無関係。DOC-001 は:
  - 必須出力値(時間後/時間一致/時間前)のカバー漏れ → CRITICAL
  - 出力値のどれにもマッチしない死条件(例 ^年末年始$) → CRITICAL
  - ERROR 未カバー → WARNING
  - catch-all(^.*$) は全出力値をカバー扱い（誤検出しない）
  - label は自由（検証しない）

stdlib のみ・standalone（python schemas/test_date_of_call_coverage.py）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import validator as v  # noqa: E402

_failures = []


def _check(cond, msg):
    if not cond:
        _failures.append(msg)


def _doc(modules):
    r = v.ValidationResult(file_path="t")
    v.validate_date_of_call_coverage({"modules": modules}, r)
    return [i for i in r.issues if i.code == "DOC-001"]


def _doc_type(conditions, mtype=v.DATE_OF_CALL_TYPE):
    """condition 文字列のリストから DateOfCall モジュール1個を組む（label は分岐無関係なので固定）。"""
    nxt = [{"condition": c, "label": "任意ラベル", "nextModuleName": f"t{i}"}
           for i, c in enumerate(conditions)]
    return {"入電時間判定": {"type": mtype, "params": {"comparison_time": "17:00:00"}, "next": nxt}}


def _crit(issues):
    return [i for i in issues if i.severity == "CRITICAL"]


def _warn(issues):
    return [i for i in issues if i.severity == "WARNING"]


# 1) 正常（時間後/時間一致/時間前/ERROR 全カバー）→ DOC-001 なし
issues = _doc(_doc_type(["^時間後$", "^時間一致$", "^時間前$", "^ERROR$"]))
_check(issues == [], f"正常フローで DOC-001 は出ないべき: {issues}")

# 2) 必須出力値の欠落（時間前 なし）→ CRITICAL
issues = _doc(_doc_type(["^時間後$", "^時間一致$", "^ERROR$"]))
_check(len(_crit(issues)) >= 1, f"時間前 欠落で CRITICAL が出るべき: {issues}")

# 3) 死条件（^年末年始$ ^受付可$）＝出力値でない + 必須欠落 → CRITICAL（複数）
issues = _doc(_doc_type(["^年末年始$", "^受付可$", "^other$"]))
_check(len(_crit(issues)) >= 1, f"出力値でない condition + 必須欠落で CRITICAL: {issues}")
_check(any("年末年始" in i.message for i in _crit(issues)),
       f"死条件 '年末年始' が CRITICAL メッセージに含まれるべき: {[i.message for i in issues]}")

# 4) catch-all（^.*$）は全出力値をカバー扱い → CRITICAL/WARNING なし
issues = _doc(_doc_type(["^.*$"]))
_check(issues == [], f"catch-all は全カバーで DOC-001 なしのはず: {issues}")

# 5) 必須3つはあるが ERROR 無し → CRITICAL なし・WARNING あり
issues = _doc(_doc_type(["^時間後$", "^時間一致$", "^時間前$"]))
_check(_crit(issues) == [], f"必須3つ揃えば CRITICAL は無いべき: {_crit(issues)}")
_check(len(_warn(issues)) == 1, f"ERROR 未カバーで WARNING が1件出るべき: {issues}")

# 6) DateOfCall でないモジュール（同じ変な条件でも）→ DOC-001 対象外
issues = _doc({"cmr": {"type": "drjoy^Context$ContextMatchRouter",
                       "next": [{"condition": "^年末年始$", "label": "x", "nextModuleName": "y"}]}})
_check(issues == [], f"DateOfCall 以外は DOC-001 対象外: {issues}")

# 7) ラベルが出力値と違っても condition が正しければ OK（label は自由）
issues = _doc({"入電時間判定": {"type": v.DATE_OF_CALL_TYPE, "params": {}, "next": [
    {"condition": "^時間後$",  "label": "営業時間外です",   "nextModuleName": "a"},
    {"condition": "^時間一致$", "label": "ちょうど受付終了", "nextModuleName": "b"},
    {"condition": "^時間前$",  "label": "受付中",         "nextModuleName": "c"},
    {"condition": "^ERROR$",  "label": "err",           "nextModuleName": "d"},
]}})
_check(issues == [], f"label が自由でも condition が正しければ DOC-001 なし: {issues}")


if _failures:
    print("FAIL:")
    for f in _failures:
        print("  -", f)
    sys.exit(1)
print("PASS: test_date_of_call_coverage (DOC-001 #326)")
