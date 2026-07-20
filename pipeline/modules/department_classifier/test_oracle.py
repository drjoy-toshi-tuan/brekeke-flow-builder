# -*- coding: utf-8 -*-
"""department_classifier universe v0 自前検証（代表ケース）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle import classify

# (入力, 期待) — 代表的な実発話パターン
CASES = [
    # 基本科
    ("内科", "内科"),
    ("外科", "外科"),
    ("小児科でお願いします", "小児科"),
    ("皮膚科", "皮膚科"),
    ("じびか", "耳鼻咽喉科"),
    ("耳鼻いんこう科", "耳鼻咽喉科"),
    # 臓器×内科/外科
    ("消化器内科", "消化器内科"),
    ("呼吸器内科を受診", "呼吸器内科"),
    ("循環器内科", "循環器内科"),
    ("脳神経外科", "脳神経外科"),
    ("整形外科にいきたい", "整形外科"),
    ("しんけいないか", "脳神経内科"),       # 神経内科→脳神経内科 正規化
    ("神経内科", "脳神経内科"),
    # 経過措置の単独禁止科（実ログ残存・受理）
    ("胃腸科", "胃腸科"),
    ("肛門科", "こう門科"),
    # 読み・エイリアス
    ("せいけい", "整形外科"),
    ("のうげか", "脳神経外科"),
    ("ますい", "麻酔科"),
    ("ペインクリニック", "麻酔科"),          # ※外来でない単独ペインは麻酔科扱い（要レビュー）
    # 曖昧（基本科なしの臓器語 → 内/外不明）
    ("消化器", "AMBIGUOUS"),
    ("脳神経", "AMBIGUOUS"),
    ("循環器", "循環器内科"),                  # ※循環器は循環器内科キーに含むため当たる（境界・要レビュー）
    # スコープ外（専門外来・法令根拠なし単独）
    ("頭痛外来", "OUT_OF_SCOPE"),
    ("禁煙外来", "OUT_OF_SCOPE"),
    ("もの忘れ外来", "OUT_OF_SCOPE"),
    ("審美歯科", "OUT_OF_SCOPE"),
    # 生成コンポーザ v0.1（修飾語 + base科 suffix）
    ("脳神経ないか", "脳神経内科"),       # 神経科なし臓器+ないか → 内科へ合成（AMBIGUOUS でなく特定科）
    ("消化器ないか", "消化器内科"),       # bare 消化器 key なし → コンポーザで内科系
    ("循環器ないか", "循環器内科"),       # 循環器 key でも当たるが結果一致
    ("脳神経げか", "脳神経外科"),         # base hiragana 外科
    ("ないか", "内科"),                   # bare base hiragana = 内科（`ないか`キー除去分の回収）
    ("げか", "外科"),                     # bare base hiragana = 外科
    ("じゃないか", "NO_RESULT"),          # 非修飾語prefix=内科に化けない（完全一致でないため）
    # 短キー除去の回帰（吸い込み磁石が消えたこと）
    ("癌化", "NO_RESULT"),               # `癌` 除去 → 腫瘍内科へ誤吸込みしない
    ("乳がん検診", "NO_RESULT"),          # `がん` 除去
    ("しかし", "NO_RESULT"),             # `しか` 除去（助詞）
    ("ますい", "麻酔科"),                 # `ますい` は保持（有効な読み）
    # 略語 exact enrich（2026-07-01・triage part-fixable由来・完全一致のみ）
    ("整形", "整形外科"),
    ("整形です。", "整形外科"),
    ("内分泌科", "糖尿病・内分泌代謝内科"),
    ("内分泌か。", "糖尿病・内分泌代謝内科"),
    ("糖尿病", "糖尿病・内分泌代謝内科"),
    ("形成", "形成外科"),
    # 略語 enrich の精度ガード（曖昧 bare は拾わない＝磁石を作らない）
    ("放射線", "NO_RESULT"),               # 科/治療科/診断科で曖昧 → exact略語に入れない
    ("循環", "NO_RESULT"),                 # 内科/外科で曖昧
    ("精神的につらい", "NO_RESULT"),        # `精神`部分一致で誤爆させない（exactのみ）
    ("整形外来", "OUT_OF_SCOPE"),          # 略語でなく外来 → OOS維持
    # わからない / DTMF / 空 / 無関係
    ("わからない", "登録なし"),
    ("決まってないです", "登録なし"),
    ("1", "NO_RESULT"),
    ("", "NO_RESULT"),
    ("こんにちは", "NO_RESULT"),
]


def main():
    if getattr(sys.stdout, "reconfigure", None):
        sys.stdout.reconfigure(encoding="utf-8")
    fails = []
    for utt, exp in CASES:
        got = classify(utt)
        mark = "ok " if got == exp else "NG "
        if got != exp:
            fails.append((utt, exp, got))
        print("  %s %r -> %s (期待 %s)" % (mark, utt, got, exp))
    print("=== %d件中 PASS=%d FAIL=%d ===" % (len(CASES), len(CASES) - len(fails), len(fails)))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
