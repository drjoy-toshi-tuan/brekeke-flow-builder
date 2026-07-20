"""test_oracle.py — faq_exact_match オラクルの単体テスト (stdlib のみ、pytest 不要)。

    python test_oracle.py

完全一致 → ANSWER（回答本文の一致まで検証）/ trim / 非マッチ → NO_RESULT /
空・空白 → NO_RESULT / 継承プロパティ ("toString" 等) → NO_RESULT（堅牢化の検証）
を網羅する。受入テストフロー (acceptance_test/FaqExactMatchAcceptanceTest.bivr) と同一カバー。
"""
from __future__ import annotations

import sys

import oracle

# (case_id, 入力, 期待result, 期待answer)
#   期待answer = None        → ANSWER なら faq_map[入力.strip()] と一致すればよい / NO_RESULT は ""
#   期待answer = "...文字列"  → 回答本文がその文字列と完全一致すること (代表ケースの内容固定)
CASES = [
    # --- 完全一致 → ANSWER（回答本文の正しさまで assert）---
    ("EM-01", "駐車場はありますか",
     "ANSWER", "約33台分ございます。１時間最大500円（税込）です。詳しくは当院ホームページの交通アクセス欄をご確認ください"),
    ("EM-02", "面会時間を教えてください",            "ANSWER", None),
    ("EM-03", "診察券を紛失したのですが、どうしたらいいですか", "ANSWER", None),  # 読点入りキー
    ("EM-04", "会計時にクレジットカードは使えますか？", "ANSWER", "使用可能です"),    # 末尾 ？ 込みで完全一致
    ("EM-05", "保険会社診断書の作成料金はいくらですか", "ANSWER", "5500円です"),
    ("EM-06", "差額ﾍﾞｯﾄ代は医療費控除に含まれますか",  "ANSWER", None),  # 半角カナのキー
    ("EM-07", "手の外科が無くなっても診断書を作成可能ですか。", "ANSWER", "可能です"),  # 末尾 。 込みのキー
    ("EM-08", "領収書を紛失しました。再発行できますか",
     "ANSWER", "領収書の再発行はできませんが、支払証明書(1100円）の作成は可能です"),  # 回答に半角 ( を含む
    ("EM-09", "車いすは借りられますか？",            "ANSWER", None),
    ("EM-10", "保護者付添が不要年齢は何歳からですか", "ANSWER", "18歳からです"),
    ("EM-11", "予約なしで受診できますか？",          "ANSWER", None),
    ("EM-12", "保険会社の診断書を書いてほしい",       "ANSWER", None),  # 末尾 。 ありの折り返し系

    # --- trim 検証（前後空白でも完全一致）---
    ("TR-01", "  駐車場はありますか  ",              "ANSWER", None),  # ASCII スペース両端
    ("TR-02", "\t面会時間を教えてください\t",        "ANSWER", None),  # タブ両端

    # --- 非マッチ（完全一致である証明：1文字でも違えば NO_RESULT）---
    ("NF-01", "駐車場ありますか",                    "NO_RESULT", None),  # 「は」欠落
    ("NF-02", "クレジットカードは使えますか",        "NO_RESULT", None),  # 接頭「会計時に」/末尾「？」欠落
    ("NF-03", "面会時間",                            "NO_RESULT", None),  # 部分文字列
    ("NF-04", "今日の天気は",                        "NO_RESULT", None),  # 無関係
    ("NF-05", "手の外科が無くなっても診断書を作成可能ですか", "NO_RESULT", None),  # 末尾「。」欠落 → EM-07 と対

    # --- 空・空白 → NO_RESULT ---
    ("EP-01", "",                                    "NO_RESULT", None),
    ("EP-02", "   ",                                 "NO_RESULT", None),  # 空白のみ → trim で空

    # --- 継承プロパティ → NO_RESULT（hasOwnProperty 堅牢化の検証）---
    ("PT-01", "toString",                            "NO_RESULT", None),
    ("PT-02", "constructor",                         "NO_RESULT", None),
    ("PT-03", "hasOwnProperty",                      "NO_RESULT", None),
    ("PT-04", "__proto__",                           "NO_RESULT", None),
    ("PT-05", "valueOf",                             "NO_RESULT", None),
]


def main() -> int:
    faq_map = oracle.load_faq_map()
    fails = []
    passed = 0

    for cid, inp, exp_res, exp_ans in CASES:
        r = oracle.match(inp, faq_map)
        ok = r["result"] == exp_res
        if exp_res == "ANSWER":
            # ANSWER は必ず faqMap の該当キーの本文と一致 (キー誤記は KeyError ではなく不一致で検出)
            ok = ok and r["answer"] == faq_map.get(inp.strip(), "<KEY_NOT_FOUND>")
            if exp_ans is not None:
                ok = ok and r["answer"] == exp_ans
        else:
            ok = ok and r["answer"] == ""
        if ok:
            passed += 1
        else:
            fails.append(
                f"{cid} match({inp!r}) = {r['result']}:{r['answer'][:24]!r}, "
                f"expected {exp_res}:{(exp_ans or '<map値>')[:24]!r}"
            )

    print(f"PASS {passed}/{len(CASES)}")
    for f in fails:
        print("  FAIL:", f)
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
