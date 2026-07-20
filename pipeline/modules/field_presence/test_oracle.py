# -*- coding: utf-8 -*-
"""field_presence オラクル受入テスト。各 kind の PRESENT/ABSENT を検証。

雑音（質問）が混ざっていても答えがあれば PRESENT、質問だけなら ABSENT を確認する。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle import classify  # noqa: E402

# (kind, 入力STT, 期待)
CASES = [
    # --- department ---
    ("department", "内科でお願いします", "PRESENT"),
    ("department", "整形外科を受診したいです", "PRESENT"),
    ("department", "循環器でお願いします", "PRESENT"),
    ("department", "心療内科です", "PRESENT"),
    ("department", "駐車場はありますか", "ABSENT"),            # 質問だけ
    ("department", "ちょっとわからないです", "ABSENT"),
    ("department", "内科でお願いします、あと駐車場ありますか", "PRESENT"),  # 答え+雑音質問→答え優先

    # --- date ---
    ("date", "来週の月曜日でお願いします", "PRESENT"),
    ("date", "6月20日がいいです", "PRESENT"),
    ("date", "明日でお願いします", "PRESENT"),
    ("date", "3日にお願いします", "PRESENT"),
    ("date", "2026年7月1日", "PRESENT"),
    ("date", "何時までやってますか", "ABSENT"),               # 質問だけ
    ("date", "まだ決めてないです", "ABSENT"),
    ("date", "来週でお願いします、ところで駐車場は", "PRESENT"),  # 答え+雑音

    # --- phone ---
    ("phone", "090-1234-5678です", "PRESENT"),
    ("phone", "08012345678", "PRESENT"),
    ("phone", "ゼロ九〇は読めない普通の文", "ABSENT"),         # 数字なし
    ("phone", "電話番号は分かりません", "ABSENT"),
    ("phone", "09012345678です、折り返しはいつ頃ですか", "PRESENT"),  # 答え+雑音

    # --- birthday ---
    ("birthday", "昭和60年4月1日です", "PRESENT"),
    ("birthday", "1985年4月1日生まれです", "PRESENT"),
    ("birthday", "平成2年12月3日", "PRESENT"),
    ("birthday", "生年月日は秘密です", "ABSENT"),
    ("birthday", "ちょっと待ってください", "ABSENT"),

    # --- card ---
    ("card", "診察券番号は12345です", "PRESENT"),
    ("card", "67890", "PRESENT"),
    ("card", "持っていません", "PRESENT"),                    # no-card 表明も先へ
    ("card", "ありません", "PRESENT"),
    ("card", "わかりません", "PRESENT"),
    ("card", "それはどこに書いてありますか", "ABSENT"),        # 質問だけ
    ("card", "12345です、ところで予約は変更できますか", "PRESENT"),  # 答え+雑音

    # --- 未知 kind は ABSENT ---
    ("name", "山田太郎と申します", "ABSENT"),                 # name は L1 対象外＝常に ABSENT
]


def main():
    passed = 0
    failed = 0
    for kind, raw, expected in CASES:
        got = classify(kind, raw)
        ok = got == expected
        if ok:
            passed += 1
        else:
            failed += 1
            print("FAIL [%s] %r => %s (expected %s)" % (kind, raw, got, expected))
    total = passed + failed
    print("field_presence オラクル受入テスト: %d/%d PASS" % (passed, total))
    if failed == 0:
        print("ALL PASS")
        return 0
    print("%d FAIL" % failed)
    return 1


if __name__ == "__main__":
    sys.exit(main())
