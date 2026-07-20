# -*- coding: utf-8 -*-
"""field_normalizer 受入オラクル。`python3 modules/field_normalizer/test_oracle.py`"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from oracle import normalize  # noqa: E402

CASES = [
    # (kind, raw, expected)
    # --- name ---
    ("name", "山田太郎と申します", "山田太郎"),
    ("name", "山田太郎です", "山田太郎"),
    ("name", "私は山田太郎です", "山田太郎"),
    ("name", "名前は佐藤花子と申します", "佐藤花子"),
    ("name", "山田太郎", "山田太郎"),          # 既にクリーン（冪等）
    ("name", "山田太郎さん", "山田太郎"),        # 敬称除去
    ("name", "鈴木一郎と言います", "鈴木一郎"),
    # --- phone ---
    ("phone", "09012345678", "09012345678"),
    ("phone", "電話番号は090-1234-5678です", "09012345678"),
    ("phone", "０９０１２３４５６７８", "09012345678"),   # 全角
    ("phone", "0312345678", "0312345678"),           # 固定10桁
    ("phone", "わかりません", ""),                     # マッチ無し→空（caller が raw 維持）
    # --- card ---
    ("card", "診察券番号は12345です", "12345"),
    ("card", "12345", "12345"),
    ("card", "番号は 1234567 番です", "1234567"),
    ("card", "１２３４５", "12345"),                   # 全角
    ("card", "持っていません", ""),
    # --- birthday（和暦/西暦 → YYYY-MM-DD 00:00:00）---
    ("birthday", "昭和60年4月1日です", "1985-04-01 00:00:00"),
    ("birthday", "昭和60年4月1日", "1985-04-01 00:00:00"),
    ("birthday", "1985年4月1日生まれです", "1985-04-01 00:00:00"),
    ("birthday", "令和2年1月1日", "2020-01-01 00:00:00"),
    ("birthday", "平成31年4月30日", "2019-04-30 00:00:00"),
    ("birthday", "大正10年12月5日", "1921-12-05 00:00:00"),
    ("birthday", "わかりません", ""),
    # --- department ---
    ("department", "内科", "内科"),
    ("department", "内科でお願いします", "内科"),
    ("department", "消化器内科を受診したいです", "消化器内科"),
    ("department", "耳鼻でお願いします", "耳鼻咽喉科"),
    ("department", "循環器", "循環器内科"),
    # --- date（自然文維持・末尾丁寧除去のみ）---
    ("date", "来週の月曜日の午前", "来週の月曜日の午前"),
    ("date", "6月20日10時の予約です", "6月20日10時"),
    ("date", "来週火曜", "来週火曜"),
    ("date", "明日でお願いします", "明日"),
    # --- raw（無変換）---
    ("raw", "新規", "新規"),
    ("raw", "新規のご予約、内科、でお間違いないですか？", "新規のご予約、内科、でお間違いないですか？"),
]


def main():
    passed = 0
    failed = 0
    for kind, raw, exp in CASES:
        got = normalize(kind, raw)
        ok = got == exp
        if ok:
            passed += 1
        else:
            failed += 1
            print(f"[FAIL] kind={kind} raw={raw!r} expected={exp!r} got={got!r}")
    print(f"\n{passed}/{passed + failed} PASS" + ("" if failed == 0 else f"  ({failed} FAILED)"))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
