# -*- coding: utf-8 -*-
"""test_cmr_reference_vocab.py — CMR-008（待受値 vs 参照元 emitter 語彙）回帰テスト（#303）。

検証内容:
  1) SSoT ドリフト防止: scaffold_generator.CMR_REFERENCE_VOCAB と validator.CMR_REFERENCE_VOCAB
     が完全一致（複製 2 コピーの同期を機械保証）。
  2) CMR-008 の検出: 語彙外待受値（dead slot）を CRITICAL 検出、語彙内は非検出、
     context 参照(<%..%>)の解決、未知参照/other トークンの非対象。

stdlib のみ・standalone（python schemas/test_cmr_reference_vocab.py）。
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)                            # validator（同ディレクトリ）
sys.path.insert(0, os.path.join(_ROOT, "scripts"))  # scaffold_generator

import validator as v  # noqa: E402
import scaffold_generator as sg  # noqa: E402

_failures = []


def _check(cond, msg):
    if not cond:
        _failures.append(msg)


def _cmr008(modules):
    r = v.ValidationResult(file_path="t")
    v.validate_cmr_reference_vocab({"modules": modules}, r)
    return [i for i in r.issues if i.code == "CMR-008"]


def _cmr(ref, *vals):
    """module1/2Name=ref、moduleXValue1..=vals の CMR モジュール dict を作る。"""
    params = {"module1Name": ref, "module2Name": ref}
    for i, val in enumerate(vals, 1):
        params[f"module1Value{i}"] = val
        params[f"module2Value{i}"] = val
    return {"type": "drjoy^Context Logic$ContextMatchRouter", "params": params, "next": []}


# 1) SSoT ドリフト防止
_check(sg.CMR_REFERENCE_VOCAB == v.CMR_REFERENCE_VOCAB,
       "SSoT ドリフト: scaffold と validator の CMR_REFERENCE_VOCAB が不一致")

# 2a) 語彙外 '1'（電話番号聴取）→ CMR-008（#303 終話分岐_予約_phonetype の実例）
issues = _cmr008({"終話分岐_予約_phonetype": _cmr("電話番号聴取", "1")})
_check(len(issues) == 2, f"'1'(電話番号聴取) は module1/2 両スロットで CMR-008 検出されるべき(2件): {issues}")

# 2b) 語彙外 'MOBILE'（着信電話番号分類）→ CMR-008（#303 SMS_電話種別判定 の実例）
issues = _cmr008({"SMS_電話種別判定": _cmr("着信電話番号分類", "MOBILE")})
_check(len(issues) == 2, f"'MOBILE'(着信電話番号分類) は module1/2 両スロットで CMR-008 検出されるべき(2件): {issues}")

# 2c) 語彙内（携帯/固定/その他）→ 非検出
issues = _cmr008({"終話分岐_予約_phonetype": _cmr("電話番号聴取", "携帯", "固定", "その他")})
_check(issues == [], f"語彙内の待受値で CMR-008 が出てはいけない: {issues}")

# 2d) context 参照 <%phonetype%> でも解決される
issues = _cmr008({"cmr": _cmr("<%phonetype%>", "1")})
_check(len(issues) == 2, f"<%phonetype%> 参照でも語彙外は検出されるべき(2件): {issues}")

# 2e) 未知参照（OpenAI モジュール等）は無視（保守的・誤検出防止）
issues = _cmr008({"cmr": _cmr("OpenAI_用件確認", "予約", "変更")})
_check(issues == [], f"未知参照は CMR-008 対象外であるべき: {issues}")

# 2f) other/default トークンは対象外（CMR-002 の管轄）
issues = _cmr008({"cmr": _cmr("電話番号聴取", "携帯", "other")})
_check(issues == [], f"other トークンは CMR-008 対象外であるべき: {issues}")


if _failures:
    print("FAIL:")
    for f in _failures:
        print("  -", f)
    sys.exit(1)
print("PASS: test_cmr_reference_vocab (CMR-008 + SSoT ドリフト防止)")
