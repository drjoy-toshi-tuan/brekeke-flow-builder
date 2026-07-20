# connection_test/ — 連結テスト (Pattern 7) 台帳

単体受入済みモジュール群を繋いだ**本番フローの正常動作を実機で保持**する連結(統合)テスト。
**何を/なぜ/機構/使い方は [`REQUIREMENTS.md`](REQUIREMENTS.md)** を参照。設計経緯は memory `project_pattern_7_connection_test.md`。

> モジュール単体受入(Pattern 6)とは別物のため、`modules/` ではなくこの専用ディレクトリに収める。

## 構成
```
connection_test/
├── REQUIREMENTS.md          仕様
├── README.md                本台帳
├── stub_stt_connection.py   一般化patcher (--bivr --cases --facility)
├── cases/{施設}_{flow}.json  施設別ケース表
└── golden/{施設}_{flow}/     完走トレース資産 (回帰のゴールデン)
```

## 実施台帳

| 施設 | flow | 実施日 | カバレッジ | 結果 | golden | 備考 |
|---|---|---|---|---|---|---|
| 福岡大学病院 | 診療 | 2026-06-08 | Main全エッジ(case 1-9) + 変更/確認 完走(10/11) | case 1/5/6/10/11 実機 PASS | `golden/福岡大学病院_診療/` | **AUD-1**(用件_分岐 catch-all 欠落→classification 空でデッドエンド)を case 6 で再現記録。Entity 声経路(case 3/4)は未実行 |

## 既知の所見（このパターンが拾ったもの）
- **AUD-1**: `用件_分岐`(ContextMatchRouter) に catch-all が無く、用件をリトライ上限まで取れない経路で classification 空のまま到達 → デッドエンド。case 6/8 が再現。修正方針は監査確認依頼(担当者)で調整中。
- DTMF セレクタは同一数字連打("11")が稀に timeout → フォールバックで case 1 実行(graceful)。再試行で解消。
