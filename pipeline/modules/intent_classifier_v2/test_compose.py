#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compose_intent_spec（label_vocab.json マスター語彙からの spec 合成）の回帰テスト。

対象:
  1. 用件/区分メニューの 4 パターン（予約/変更/キャンセル/確認 の部分集合・任意番号）
  2. number 未指定（CSV 文字列 options）時の並び順自動割当
  3. 番号発話（1です/1番で/にばん 等）の L0 判定
  4. 日付発話ガード（8月25日/25日です/0825 等が番号・キーワードに誤ヒットしない）

実行: python3 modules/intent_classifier_v2/test_compose.py
"""

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent.parent / "tools"))

from gen_intent_v2 import compose_intent_spec, validate_spec  # noqa: E402
from oracle import classify  # noqa: E402

SUITES = [
    ("P1 予約/変更/キャンセル/確認",
     [{"number": 1, "label": "予約"}, {"number": 2, "label": "変更"},
      {"number": 3, "label": "キャンセル"}, {"number": 4, "label": "確認"}],
     [("よやくをお願いします", "予約"), ("日にちをずらしたいんですが", "変更"),
      ("予約を取り消してください", "キャンセル"), ("予約の確認をしたいです", "確認"),
      ("予約がいつだったか教えてください", "確認"), ("4", "確認"),
      ("一番でお願いします", "予約"), ("予約したんですけど行けなくなっちゃって", "変更"),
      ("1です", "予約"), ("1番で", "予約"), ("いちばんで", "予約"),
      ("えっと、1番で", "予約"), ("はい、1番です", "予約"),
      # 末尾語つき番号（2だよ/2だね/2番です — L0 サフィックス拡張 2026-07-17）
      ("2だよ", "変更"), ("2だね", "変更"), ("2番です", "変更"),
      ("えー2番でお願いしますはい", "変更"), ("にばんをお願いします", "変更"),
      # 順序・最上級・複合語は選択に化けない（AmiVoice 連結ノイズガード）
      ("2番目の窓口に行った", "NO_RESULT"), ("2番線", "NO_RESULT"),
      ("25日の2番目", "NO_RESULT"), ("いちばん早いので", "NO_RESULT"),
      ("一番上のやつ", "NO_RESULT"),
      ("一番早い日でお願いします", "CLARIFY"),  # お願いします=_YES_ → menu文脈で聞き返し
      ("一番でお願いします", "予約"), ("いちばんです", "予約"),
      # を 継続（2番を/2を/にを/一を — 2026-07-17 追加）
      ("2番を", "変更"), ("2番をお願いします", "変更"), ("2を", "変更"),
      ("にを", "変更"), ("一を", "予約"), ("いちを", "予約"),
      # 日付+を は選択に化けない
      ("25日を", "NO_RESULT"), ("2月を", "NO_RESULT")]),
    ("P2 変更/確認（CSV 文字列 options・number 自動割当）",
     ["変更", "確認"],
     [("変更したいです", "変更"), ("リスケお願いします", "変更"),
      ("予約が入ってるか確認したい", "確認"), ("1", "変更"), ("2ばんで", "確認"),
      ("新しく予約したいです", "NO_RESULT"),
      # 日付発話ガード: 番号/キーワードに誤ヒットせず聞き直しへ
      ("8月25日", "NO_RESULT"), ("25日です", "NO_RESULT"), ("1月です", "NO_RESULT"),
      ("いちがつ", "NO_RESULT"), ("2日で", "NO_RESULT"), ("2月2日", "NO_RESULT"),
      ("0825", "NO_RESULT"), ("ついたち", "NO_RESULT"), ("20日", "NO_RESULT"),
      ("1時です", "NO_RESULT"), ("12月", "NO_RESULT"),
      # 日付+意図 は意図が勝つ / メニュー文脈の「2で」は選択肢
      ("8月25日に変更したい", "変更"), ("25日の予約があってるか確認したい", "確認"),
      ("2で", "確認")]),
    ("P3 変更/キャンセル/確認/予約（番号逆順）",
     [{"number": 1, "label": "変更"}, {"number": 2, "label": "キャンセル"},
      {"number": 3, "label": "確認"}, {"number": 4, "label": "予約"}],
     [("4", "予約"), ("よやくで", "予約"), ("キャンセルしたい", "キャンセル"),
      ("にばん", "キャンセル"), ("いつでしたっけ", "確認")]),
    ("P4 変更/キャンセル/確認",
     [{"number": 1, "label": "変更"}, {"number": 2, "label": "キャンセル"},
      {"number": 3, "label": "確認"}],
     [("都合が悪くなったのでキャンセルで", "キャンセル"),
      ("日程変更をお願いします", "変更"), ("あってるか確かめたい", "確認"),
      ("予約をお願いしたいんですが", "NO_RESULT")]),
]


def main() -> None:
    total = passed = 0
    for name, options, cases in SUITES:
        spec = compose_intent_spec(options)
        assert spec is not None, f"{name}: compose が None"
        errs = validate_spec(spec)
        assert not errs, f"{name}: spec 検証エラー {errs}"
        for utt, expected in cases:
            total += 1
            got = classify(spec, utt)["intent"]
            ok = got == expected
            passed += ok
            mark = "PASS" if ok else f"FAIL exp={expected}"
            print(f"[{mark}] {name}: 「{utt}」 → {got}")
    print(f"\n=== {passed}/{total} PASS ===")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
