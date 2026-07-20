# -*- coding: utf-8 -*-
"""go_back_classifier オラクル受入テスト。戻る/繰り返し/NONE を検証。"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle import classify  # noqa: E402

CASES = [
    # --- 戻る ---
    ("やっぱりキャンセルしたいです", "戻る"),
    ("やっぱり変更したいです", "戻る"),
    ("別の用件でお願いします", "戻る"),
    ("最初からやり直したいです", "戻る"),
    ("一からお願いします", "戻る"),
    ("前に戻してください", "戻る"),
    ("違う用件なんですけど", "戻る"),
    ("取り消してください", "戻る"),
    ("もう一回最初からお願いします", "戻る"),       # 複合→戻る優先

    # --- 繰り返し ---
    ("もう一回言ってください", "繰り返し"),
    ("もう一度お願いします", "繰り返し"),
    ("聞こえなかったです", "繰り返し"),
    ("なんて言いましたか", "繰り返し"),
    ("もっかい言って", "繰り返し"),
    ("聞き取れませんでした", "繰り返し"),

    # --- NONE（FAQ へ）---
    ("駐車場はありますか", "NONE"),
    ("何時までやってますか", "NONE"),
    ("内科でお願いします", "NONE"),                  # 本来 L1 で拾われるが L0 単体では NONE
    ("えっと", "NONE"),
    ("", "NONE"),
    # 用件発話は NONE（"変更したい"/"キャンセルしたい"単独は用件語なので 戻る にしない）
    ("予約を変更したいんですけど、6月20日の10時の予約です。", "NONE"),
    ("予約をキャンセルしたいです。来週火曜の予約です。", "NONE"),
    ("変更したいです", "NONE"),
    ("キャンセルしたいです", "NONE"),
]


def main():
    passed = 0
    failed = 0
    for raw, expected in CASES:
        got = classify(raw)
        if got == expected:
            passed += 1
        else:
            failed += 1
            print("FAIL %r => %s (expected %s)" % (raw, got, expected))
    total = passed + failed
    print("go_back_classifier オラクル受入テスト: %d/%d PASS" % (passed, total))
    if failed == 0:
        print("ALL PASS")
        return 0
    print("%d FAIL" % failed)
    return 1


if __name__ == "__main__":
    sys.exit(main())
