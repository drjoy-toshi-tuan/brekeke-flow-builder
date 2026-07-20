# -*- coding: utf-8 -*-
"""ambiguity_gate — 紛れペア(最小対)の曖昧検出器 / Python 参照実装（オラクル）

決定論分類の多段構成 Stage2（検品）。区別 token が小さく STT が壊しやすい候補群（GROUP）に対し、
発話を NFKC 正規化 → 文字 2-gram → IDF 被覆率 で採点し、トップと次点の idf-margin で
「綺麗に分離できるか」を判定する:
  - 分離できる(margin >= MIN_IDF_MARGIN)     → 勝者ラベルを返す（Stage1 の結果を確定）
  - 団子(margin < MIN_IDF_MARGIN)            → "CONFIRM"（親→確認ステップ＝DTMF 等へ）
  - 何も当たらない / 短すぎ                   → "NO_RESULT"（通常リトライ）

FAQ Matcher（modules/faq_matcher）の normalize / bigrams / idf_coverage と同方式（パリティ）。
「優先順位で黙って既定採用」して半分誤るのを避け、区別が立たない時は "拾えないと分かる" に倒す。

期待値の SSoT は acceptance_test/cases.tsv（テストが正）。正本は script.js（Nashorn/ES5.1）。
GROUP 定義（紛れ候補群とその語彙）は組込先のデータ。本オラクルは検証用の例 GROUPS を内蔵する。

stdlib のみ（math / unicodedata）。pip 不使用。
"""
from __future__ import annotations

import math
import sys
import unicodedata

# =============================================================================
# CONFIG — script.js の CONFIG ブロック既定値と一致させること
# =============================================================================
MIN_QUERY_CHARS = 2     # 正規化後この文字数未満は判定しない（→ NO_RESULT）
MIN_IDF_MARGIN = 0.12   # 採用候補と次点候補の idf 被覆率の差の下限。未満は団子（曖昧）→ CONFIRM

# NFKC 後に除去する記号・空白（faq_matcher / 4分類器 と同集合）。長音 ー(U+30FC) は残す。
STRIP_CHARS = set(
    " \t\r\n　"
    "、。，．,.・…‥〜~「」『』（）()【】[]＜＞<>｜|‐-—―／/＼\\＿_"
    "：:；;！!？?“”‘’\"'`｢｣･"
)

CONFIRM = "CONFIRM"      # 団子＝親分類→確認ステップへ
RESULT_NONE = "NO_RESULT"

# 検証用の例 GROUP（実組込では組込先がここに紛れ候補群を定義 / Note 等から供給）。
# 形式: group 名 -> [(ラベル, [語彙バリアント...]), ...]
GROUPS = {
    "course_dock": [
        ("1日ドック", ["1日ドック", "日帰りドック", "一日ドック", "日帰り"]),
        ("2日ドック", ["2日ドック", "一泊ドック", "二日ドック", "1泊2日ドック", "泊まりのドック"]),
    ],
    "dept_shoukaki": [
        ("消化器内科", ["消化器内科", "消化器の内科", "胃腸内科"]),
        ("消化器外科", ["消化器外科", "消化器の外科"]),
    ],
}


def normalize(value):
    if isinstance(value, dict):
        value = value.get("text", "")
    s = "" if value is None else str(value)
    s = unicodedata.normalize("NFKC", s)
    s = s.lower()
    return "".join(ch for ch in s if ch not in STRIP_CHARS)


def bigrams(value):
    n = normalize(value)
    if len(n) == 0:
        return []
    if len(n) == 1:
        return [n]
    return [n[i:i + 2] for i in range(len(n) - 1)]


def _build(members):
    """member family -> (docs[(label, variant, toks)], df, n)。"""
    docs = []
    for label, variants in members:
        for v in variants:
            docs.append((label, v, bigrams(v)))
    df = {}
    for (_l, _v, toks) in docs:
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    return docs, df, len(docs)


def _idf(df, n, term):
    d = df.get(term, 0)
    return math.log(1 + (n - d + 0.5) / (d + 0.5))


def _idf_coverage(qtoks, doc_toks, df, n):
    """質問 bigram のうちマッチした分の IDF 質量比。ありふれた共通 bigram（区別に効かない）は
    寄与が小さく、珍しい区別 token（内科/外科・1/2 由来）のマッチを強く反映する。"""
    qset = set(qtoks)
    if not qset:
        return 0.0
    dset = set(doc_toks)
    num = den = 0.0
    for t in qset:
        w = _idf(df, n, t)
        den += w
        if t in dset:
            num += w
    return (num / den) if den else 0.0


def classify(value, group):
    """発話 + GROUP -> 勝者ラベル / "CONFIRM" / "NO_RESULT"。

    上から: GROUP 不在→NO_RESULT / 短すぎ→NO_RESULT / 完全一致(1ラベル)→そのラベル /
    member 最大 idf_coverage を比較 → 何も当たらない→NO_RESULT / margin 不足→CONFIRM / 勝者ラベル。
    """
    members = GROUPS.get(group)
    if members is None:
        return RESULT_NONE
    qn = normalize(value)
    if len(qn) < MIN_QUERY_CHARS:
        return RESULT_NONE
    qtoks = bigrams(value)
    docs, df, n = _build(members)

    # exact-match 短絡: 正規化が member variant と完全一致し、それが 1 ラベルに限るなら即採用
    exact_labels = set()
    for (label, v, _toks) in docs:
        if normalize(v) == qn:
            exact_labels.add(label)
    if len(exact_labels) == 1:
        return next(iter(exact_labels))

    # member 単位の最大 idf_coverage
    best_by_label = {}
    for (label, _v, toks) in docs:
        ic = _idf_coverage(qtoks, toks, df, n)
        if label not in best_by_label or ic > best_by_label[label]:
            best_by_label[label] = ic
    ranked = sorted(best_by_label.items(), key=lambda kv: kv[1], reverse=True)
    if not ranked or ranked[0][1] <= 0.0:
        return RESULT_NONE
    best_ic = ranked[0][1]
    second_ic = ranked[1][1] if len(ranked) > 1 else 0.0
    if (best_ic - second_ic) < MIN_IDF_MARGIN:
        return CONFIRM
    return ranked[0][0]


# プローブ（期待値設計用）。(group, utterance)
PROBE = [
    ("course_dock", "1日ドック"), ("course_dock", "2日ドック"), ("course_dock", "日帰りドック"),
    ("course_dock", "ドック"), ("course_dock", "天気のこと"),
    ("dept_shoukaki", "消化器内科"), ("dept_shoukaki", "消化器外科"), ("dept_shoukaki", "消化器"),
]


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) >= 2:
        print(classify(argv[1], argv[0]))
        return 0
    print(f"# gate: MIN_QUERY_CHARS={MIN_QUERY_CHARS} MIN_IDF_MARGIN={MIN_IDF_MARGIN}\n")
    for g, q in PROBE:
        print(f"  [{g:14}] {q!r:16} -> {classify(q, g)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
