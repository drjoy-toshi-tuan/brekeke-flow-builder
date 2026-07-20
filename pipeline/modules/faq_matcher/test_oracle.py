"""test_oracle.py — FAQ Matcher オラクルの単体テスト (stdlib のみ、pytest 不要)。

    python test_oracle.py

正規化/トークナイズの基礎と、faq_sample.json に対する 14 ケースの判定 (FOUND:id / NOT_FOUND)
を検証する。受入テストフロー (acceptance_test/FAQAcceptanceTest.bivr) と同一カバー。
"""
from __future__ import annotations

import sys

import oracle

# --- 正規化/トークナイズの基礎 ---
NORM_CASES = [
    ("駐車場はありますか", "駐車場はありますか"),   # 変化なし
    ("ＡＢＣ１２３", "abc123"),                      # 全角英数 → 半角 + lower
    ("ク　レ ジット", "クレジット"),                # 全角/半角スペース除去
    ("カード！？", "カード"),                        # 記号除去
    ("ＣＴ検査。", "ct検査"),                        # 全角英字 lower + 句点除去
    ("コーヒー", "コーヒー"),                        # 長音 ー は残す
]

BIGRAM_CASES = [
    ("ab", ["ab"]),
    ("abc", ["ab", "bc"]),
    ("あ", ["あ"]),     # 1 文字は unigram
    ("！", []),          # 記号のみ → 空
]

# --- faq_sample.json に対する判定 (受入テスト 14 ケースと一致) ---
SEARCH_CASES = [
    ("FAQ-01", "駐車場はありますか",            "FOUND", "parking"),
    ("FAQ-02", "駐車場の場所を教えてください",   "FOUND", "parking"),
    ("FAQ-03", "受付時間を教えて",              "FOUND", "hours"),
    ("FAQ-04", "保険証は必要ですか",            "FOUND", "insurance"),
    ("FAQ-05", "クレジットカードは使えますか",   "FOUND", "payment"),
    ("FAQ-06", "カードで支払えますか",          "FOUND", "payment"),
    ("FAQ-07", "面会時間を教えて",              "FOUND", "visiting"),
    ("FAQ-08", "子供を診てもらえますか",        "FOUND", "pediatrics"),
    ("FAQ-09", "紹介状はいりますか",            "FOUND", "referral"),
    ("FAQ-10", "車を停めるところはありますか",   "NOT_FOUND", None),
    ("FAQ-11", "診療は何時までですか",          "NOT_FOUND", None),
    ("FAQ-12", "今日の天気はどうですか",        "NOT_FOUND", None),
    ("FAQ-13", "あのー、えっと",                "NOT_FOUND", None),
    ("FAQ-14", "はい",                          "NOT_FOUND", None),
]

# --- NO_QUESTION 前段ゲート (detect_no_question を直接検証、コーパス非依存) ---
# True = 「ありません」系の否定/終了応答 → NO_QUESTION。
# False = 実際の質問 (否定語を含むものも含む) → FAQ 検索へ流す。
NOQ_CASES = [
    # 陽性: ありません系・終了応答
    ("NOQ-01", "ありません",            True),
    ("NOQ-02", "特にありません",         True),
    ("NOQ-03", "ありませんね",           True),   # 文末助詞
    ("NOQ-04", "えっとありません",        True),   # 先頭フィラー
    ("NOQ-05", "ないです",              True),
    ("NOQ-06", "なし",                  True),
    ("NOQ-07", "ない",                  True),   # 短すぎ閾値より先に分離
    ("NOQ-08", "大丈夫です",            True),
    ("NOQ-09", "大丈夫",                True),
    ("NOQ-10", "結構です",              True),
    ("NOQ-11", "以上です",              True),
    ("NOQ-12", "特にございません",        True),
    ("NOQ-13", "もう質問はありません",     True),   # 接頭付き → サフィックス一致
    ("NOQ-14", "問題ないです",           True),
    ("NOQ-15", "けっこうです",           True),   # ひらがな表記ゆれ
    ("NOQ-16", "だいじょうぶ",           True),
    ("NOQ-17", "わかりました",           True),
    # 陰性: 実際の質問 (NO_QUESTION にしてはならない)
    ("NOQ-18", "他院からの手紙がありませんが初診でかかれますか", False),  # q006 衝突源
    ("NOQ-19", "予約はありませんか",      False),   # 疑問終止「か」
    ("NOQ-20", "駐車場はありますか",      False),
    ("NOQ-21", "保険証は必要ですか",      False),
    ("NOQ-22", "クレジットカードは使えますか", False),
    ("NOQ-23", "紹介状はいりますか",      False),
    ("NOQ-24", "変更はないですか",        False),   # 否定語 + 疑問終止
    ("NOQ-25", "はい",                  False),
    ("NOQ-26", "",                      False),
]

# --- 節分割 (発話の揺れ前処理) ユニット — コーパス非依存 ---
# (raw, must_contain) : segment_candidates が must_contain を候補に含むこと
SEG_CASES = [
    ("SEG-01", "ないです嘘です。駐車場ありましたよね。", "駐車場ありましたよね"),  # 言い直し+文区切り
    ("SEG-02", "ギリギリに行きたいんですけれども10分前で大丈夫ですか", "10分前で大丈夫ですか"),  # 逆接
    ("SEG-03", "駐車場じゃなくて駐輪場ありますか", "駐輪場ありますか"),  # 言い直し
    ("SEG-04", "車で行きたいんですけど駐車場ありますか", "駐車場ありますか"),  # 逆接(けど)
]
# 反復畳み込み
COLLAPSE_CASES = [
    ("CLP-01", "クレジットで支払いできますかクレジットで支払いできますか", "クレジットで支払いできますか"),
    ("CLP-02", "駐車場はありますか", "駐車場はありますか"),  # 非反復は不変
]

# --- 本番コーパス (faq_note.json) 統合: 発話の揺れ吸収 ---
# faq_note.json は .gitignore 対象。無い環境ではスキップ (FAIL にしない)。
DISFLUENCY_CASES = [
    # 3 例 (フル発話)
    ("DIS-01", "ギリギリに行きたいんですけれども10分前で大丈夫ですか", "FOUND", "aug_arrival_time"),
    ("DIS-02", "ないです嘘です。駐車場ありましたよね。", "FOUND", "q020"),
    ("DIS-03", "クレジットで支払いできますかクレジットで支払いできますか", "FOUND", "q017"),
    # 駐車/駐輪 振り分け (誤ルート 0)
    ("DIS-04", "駐車場ありましたよね", "FOUND", "q020"),
    ("DIS-05", "駐輪場ありましたよね", "FOUND", "q051"),
    ("DIS-06", "ないです嘘です。駐輪場ありましたよね。", "FOUND", "q051"),
    ("DIS-07", "駐車場じゃなくて駐輪場ありますか", "FOUND", "q051"),
    # NOT_FOUND 保全 (節分割が誤 FOUND を作らない)
    ("DIS-08", "今日の天気はどうですか", "NOT_FOUND", None),
    ("DIS-09", "ギリギリに着きたいんですけど近くにカフェありますか", "NOT_FOUND", None),
    ("DIS-10", "炎症は必要ですか", "NOT_FOUND", None),
]


def main() -> int:
    fails = []
    passed = 0

    for src, expected in NORM_CASES:
        got = oracle.normalize(src)
        if got == expected:
            passed += 1
        else:
            fails.append(f"normalize({src!r}) = {got!r}, expected {expected!r}")

    for src, expected in BIGRAM_CASES:
        got = oracle.bigrams(src)
        if got == expected:
            passed += 1
        else:
            fails.append(f"bigrams({src!r}) = {got!r}, expected {expected!r}")

    corpus = oracle.load_corpus()
    for case_id, q, exp_status, exp_id in SEARCH_CASES:
        r = oracle.search(q, corpus)
        ok = r["status"] == exp_status and (exp_status != "FOUND" or r["id"] == exp_id)
        if ok:
            passed += 1
        else:
            fails.append(
                f"{case_id} search({q!r}) = {r['status']}:{r['id']} "
                f"(score={r['score']} cov={r['coverage']}), expected {exp_status}:{exp_id}"
            )

    for case_id, q, exp in NOQ_CASES:
        got = oracle.detect_no_question(q)
        if got == exp:
            passed += 1
        else:
            fails.append(f"{case_id} detect_no_question({q!r}) = {got}, expected {exp}")

    # search() 統合: 前段ゲート陽性は corpus に関わらず status=NO_QUESTION
    for case_id, q in [("NOQ-S1", "ありません"), ("NOQ-S2", "特にありません"), ("NOQ-S3", "大丈夫です")]:
        r = oracle.search(q, corpus)
        if r["status"] == "NO_QUESTION":
            passed += 1
        else:
            fails.append(f"{case_id} search({q!r}).status = {r['status']}, expected NO_QUESTION")

    # 節分割 / 反復畳み込み (コーパス非依存)
    for case_id, raw, must in SEG_CASES:
        cands = oracle._segment_candidates(raw)
        if must in cands:
            passed += 1
        else:
            fails.append(f"{case_id} _segment_candidates({raw!r}) = {cands}, must contain {must!r}")
    for case_id, raw, exp in COLLAPSE_CASES:
        got = oracle._collapse_repeat(raw)
        if got == exp:
            passed += 1
        else:
            fails.append(f"{case_id} _collapse_repeat({raw!r}) = {got!r}, expected {exp!r}")

    # 本番コーパス統合 (faq_note.json があれば)。無ければスキップ。
    note_path = oracle.HERE / "faq_note.json"
    if note_path.exists():
        import json
        note_corpus = oracle.Corpus(json.loads(note_path.read_text(encoding="utf-8")))
        for case_id, q, exp_status, exp_id in DISFLUENCY_CASES:
            r = oracle.search(q, note_corpus)
            ok = r["status"] == exp_status and (exp_status != "FOUND" or r["id"] == exp_id)
            if ok:
                passed += 1
            else:
                fails.append(
                    f"{case_id} search({q!r}) = {r['status']}:{r.get('id')} "
                    f"(reason={r.get('reason','')}), expected {exp_status}:{exp_id}"
                )
        dis_n = len(DISFLUENCY_CASES)
    else:
        print("  SKIP: faq_note.json なし → DISFLUENCY_CASES をスキップ (ingest_ai_settings_csv.py で生成)")
        dis_n = 0

    total = (len(NORM_CASES) + len(BIGRAM_CASES) + len(SEARCH_CASES) + len(NOQ_CASES) + 3
             + len(SEG_CASES) + len(COLLAPSE_CASES) + dis_n)
    print(f"PASS {passed}/{total}")
    for f in fails:
        print("  FAIL:", f)
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
