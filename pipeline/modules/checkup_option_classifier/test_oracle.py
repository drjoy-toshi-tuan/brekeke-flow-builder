#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""checkup_option_classifier 受入テスト — acceptance_test/cases.tsv（テストが正）を全件照合。

cases.tsv が存在する場合はそちらを正とする。
存在しない場合はインライン TEST_CASES を実行する。

実行: python modules/checkup_option_classifier/test_oracle.py
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle import classify  # noqa: E402

CASES_TSV = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "acceptance_test", "cases.tsv")

# facility_offered サブセット（tsv では表現不可ゆえインライン。store checkup_option と一致）
FACILITY_CASES = [
    ("マンモと骨密度検査", {"マンモグラフィ"}, "マンモグラフィ"),
]

# TSV が存在しない場合のフォールバック
INLINE_CASES = [
    # ===== 復唱途中切断 =====
    ("家族コース",           "復唱途中切断"),
    ("家族構成",             "復唱途中切断"),
    ("保険は使えますか",     "復唱途中切断"),
    ("カメラをキャンセルしたい", "復唱途中切断"),
    ("受診内容",             "復唱途中切断"),
    ("オプション",           "復唱途中切断"),
    ("オプション追加",       "復唱途中切断"),
    ("",                     "復唱途中切断"),
    ("マンモ",               "復唱途中切断"),
    # ===== 不明 =====
    ("よくわからない",       "不明"),
    ("まだ決めていない",     "不明"),
    ("当日決めたいです",     "不明"),
    ("わかりません",         "不明"),
    ("不明です",             "不明"),
    ("相談したいです",       "不明"),
    # ===== 無い =====
    ("追加は不要です",       "無い"),
    ("特にありません",       "無い"),
    ("いりません",           "無い"),
    ("追加なしです",         "無い"),
    ("結構です",             "無い"),
    ("大丈夫です",           "無い"),
    # ===== 基本コース =====
    ("人間ドック",           "１日ドック"),
    ("人間ロック",           "１日ドック"),
    ("人間ドッグ",           "１日ドック"),
    ("1日ドック",            "１日ドック"),
    ("日帰りドック",         "１日ドック"),
    ("2日ドック",            "＜お通い＞２日ドック"),
    ("二日ドック",           "＜お通い＞２日ドック"),
    ("なでしこ精査コースで", "＜お通い＞２日ドック／なでしこ精査コース"),
    ("ペットCTがんコース",   "＜お通い＞２日なでしこPET-CTがんコース"),
    ("レディースドック",     "レディースドック"),
    ("女性ドック",           "レディースドック"),
    ("レディースロック",     "レディースドック"),
    # ===== オプション単体 =====
    ("脳の検査を追加したい", "脳ドック"),
    ("MRI",                  "脳ドック"),
    ("頭の検査",             "脳ドック"),
    ("脳ドック",             "脳ドック"),
    ("脳ロック",             "脳ドック"),
    ("大腸カメラ",           "大腸ドック（全大腸内視鏡検査）"),
    ("大腸内視鏡",           "大腸ドック（全大腸内視鏡検査）"),
    ("下のカメラ",           "大腸ドック（全大腸内視鏡検査）"),
    ("肺CT",                 "肺ドック"),
    ("胸部CT",               "肺ドック"),
    ("肺ロック",             "肺ドック"),
    ("眼科検査",             "眼科ドック"),
    ("マイクロアレイ",       "マイクロアレイ血液検査"),
    ("がんの血液検査",       "マイクロアレイ血液検査"),
    ("マンモ2方向",          "マンモグラフィ（2方向）"),
    ("マンモ1方向",          "マンモグラフィ（1方向）"),
    ("乳房エコー",           "乳房超音波検査"),
    ("胸のエコー",           "乳房超音波検査"),
    ("子宮頸部細胞診",       "子宮頚がん検査"),
    ("子宮体がん",           "子宮体がん検査"),
    ("睡眠時無呼吸",         "睡眠時無呼吸検査"),
    ("いびき",               "睡眠時無呼吸検査"),
    ("動脈硬化",             "動脈硬化検査"),
    ("血管年齢",             "動脈硬化検査"),
    ("B型肝炎",              "肝炎ウイルス検査"),
    ("甲状腺",               "甲状腺検査"),
    ("腫瘍マーカー",         "腫瘍マーカーセット"),
    ("ピロリ菌",             "ヘリコバクターピロリ菌検査"),
    ("胃の血液検査",         "ヘリコバクターピロリ菌検査"),
    ("PSA",                  "前立腺がん検査（PSA）"),
    ("前立腺",               "前立腺がん検査（PSA）"),
    ("骨密度",               "骨密度検査"),
    ("骨粗鬆症",             "骨密度検査"),
    ("眼底",                 "眼底検査・眼圧検査"),
    ("眼圧",                 "眼底検査・眼圧検査"),
    ("緑内障チェック",       "眼底検査・眼圧検査"),
    ("肺機能",               "肺機能検査"),
    ("呼吸機能",             "肺機能検査"),
    ("転倒予防",             "転倒予防診断"),
    ("心臓の検査",           "心臓ドック"),
    ("冠動脈CT",             "心臓ドック"),
    # ===== 複数オプション =====
    ("脳と肺の検査",         "脳ドック、肺ドック"),
    ("大腸カメラと肺ドック", "大腸ドック（全大腸内視鏡検査）、肺ドック"),
    ("脳と眼科の検査",       "脳ドック、眼科ドック"),
    # ===== 否定語除外 =====
    ("脳ドックはいらない",   "無い"),
    ("脳ドックはやめて肺ドックで", "肺ドック"),
    # ===== SUBSUMES =====
    ("脳とがんのコース",     "脳ドック＋PET-CTコース"),
    ("がんプレミアム",       "＜お通い＞３日なでしこＰＥＴ－ＣＴがんプレミアムコース"),
]


def load_tsv():
    cases = []
    with io.open(CASES_TSV, "r", encoding="utf-8") as f:
        header_line = f.readline().rstrip("\r\n")
        header = header_line.split("\t")
        for lineno, line in enumerate(f, start=2):
            line = line.rstrip("\r\n")
            if not line.strip() or line.startswith("#"):
                continue
            cols = line.split("\t")
            row = dict(zip(header, cols))
            row["_lineno"] = lineno
            cases.append(row)
    return cases


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if os.path.exists(CASES_TSV):
        rows = load_tsv()
        print(f"[checkup_option_classifier] cases.tsv から {len(rows)} ケース + facility {len(FACILITY_CASES)} 件実行")
        fails = []
        for r in rows:
            got = classify(r["utterance"])
            if got != r["expected"]:
                fails.append((r, got))
        fac_fails = []
        for utt, fac, exp in FACILITY_CASES:
            got = classify(utt, facility_offered=fac)
            if got != exp:
                fac_fails.append((utt, exp, got))
        total = len(rows) + len(FACILITY_CASES)
        nfail = len(fails) + len(fac_fails)
        print(f"結果: {total - nfail}/{total} PASS  "
              f"{'[OK]' if not nfail else '[FAIL]'}")
        if fails:
            print(f"\nFAIL {len(fails)} 件:")
            for r, got in fails:
                print(f"  {r['id']} (L{r['_lineno']}): {r['utterance']!r:40s}"
                      f"  expected={r['expected']!r}  got={got!r}"
                      f"  [{r.get('note','')}]")
        if fac_fails:
            print(f"\n[facility] FAIL {len(fac_fails)} 件:")
            for utt, exp, got in fac_fails:
                print(f"  {utt!r}  expected={exp!r}  got={got!r}")
        return 0 if not nfail else 1
    else:
        print(f"[checkup_option_classifier] インライン {len(INLINE_CASES)} ケース実行")
        fails = []
        for inp, expected in INLINE_CASES:
            got = classify(inp)
            if got != expected:
                fails.append((inp, expected, got))
        total = len(INLINE_CASES)
        print(f"結果: {total - len(fails)}/{total} PASS  "
              f"{'[OK]' if not fails else '[FAIL]'}")
        if fails:
            for inp, expected, got in fails:
                print(f"  FAIL  {inp!r:40s}  expected={expected!r}  got={got!r}")
        return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
