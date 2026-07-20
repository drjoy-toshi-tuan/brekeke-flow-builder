# Incoming Category Classifier / Phone2Name 参照資料

> 着信電話番号 → Dr.JOY 電話帳マッチによるカテゴリ分類・氏名読み上げを実装する際の参照資料置き場。

## ファイル

| ファイル | 内容 | 由来 |
|---|---|---|
| `sample_phonebook_相談室.csv` | Dr.JOY 電話帳の CSV ダウンロード見本 | 「相談室｜第三世代」シナリオから 1 行抽出 |
| `sample_松本協立病院相談室.bivr` | Phone2Name の実装例（2 フロー、76+62 モジュール） | 本番稼働中の参考実装 |

## sample_phonebook_相談室.csv のスキーマ

```csv
"電話番号","氏名","フリガナ","ブラックリスト","リスト1","リスト2","リスト3","リスト4","リスト5","入電通知"
"08078281487","DrJOYテスト","ドクタージョイテスト","0","1","0","0","0","0","0"
```

- `電話番号`: ハイフン無し E.164 風（実フォーマットは設定により異なる、要 Brekeke 確認）
- `氏名` / `フリガナ`: 個人名・施設名・薬局名。Phone2Name モジュールが TTS 読み上げに使うのは **フリガナ**（カタカナ）側
- **`氏名` フィールドの制約**: **括弧（全角『（）』半角『()』）等の特殊文字を含めると Dr.JOY 電話帳のインポートが失敗する**。2026-05-12 すずな皮ふ科で「ミネ薬局（ミネドラッグ）」が import 失敗で判明
  - CS 提供データに括弧があっても、CSV 生成時に **括弧と中身を除去** または別表記に整形すること（例: `ミネ薬局（ミネドラッグ）` → `ミネ薬局` または `ミネ薬局 ミネドラッグ`）
  - 推奨整形: 正規表現 `[（(].*?[）)]` で除去
  - 同様にカンマ・ダブルクォート・改行も避ける（CSV パースを壊す）
- `ブラックリスト` / `リスト1〜5`: 1 = 該当, 0 = 非該当。`incoming-category-classifier` が判定するカテゴリは **このリスト1〜5 のどれかにヒットしたか**を返す（推定、要 Brekeke 動作確認）
- `入電通知`: Dr.JOY 画面ポップアップ通知の有無フラグ

## sample_松本協立病院相談室.bivr の Phone2Name 実装例

`flows/@flow_松本協立病院_相談室1$基本フロー転送あり.txt` 内の `施設確認` モジュール:

```json
{
  "name": "施設確認",
  "type": "drjoy^External Integration$Phone2Name",
  "params": {
    "FOUND_KATAKANA_NAME_DEFAULT_TMP": "recipient_name様、お電話ありがとうございます。",
    "NOT_FOUND_KATAKANA_NAME_DEFAULT_TMP": ""
  },
  "next": [
    {"condition": "^TIMEOUT$",  "label": "timeout",      "nextModuleName": "医療機関事業所企業名"},
    {"condition": "^TRUE$",     "label": "found result", "nextModuleName": "電話番号聴取"},
    {"condition": "^NO_RESULT$","label": "no result",    "nextModuleName": "医療機関事業所企業名"},
    {"condition": "^ERROR$",    "label": "error",        "nextModuleName": "医療機関事業所企業名"}
  ]
}
```

**ポイント**:
- `FOUND_KATAKANA_NAME_DEFAULT_TMP` 内の `recipient_name` は動的差込プレースホルダ。Dr.JOY 電話帳のフリガナが実行時に差し込まれる。
- 検出失敗（NO_RESULT / TIMEOUT / ERROR）は **聴取モジュールにフォールバック**（「医療機関事業所企業名」hearing）。
- next の 4 ルートは label `found result` / `timeout` / `no result` / `error` で固定（typical pattern）。

## 想定する組み合わせパターン

```
incoming-classifier
  ├─ 非通知/海外 → 切断
  └─ 通常着信
      → incoming-category-classifier（Dr.JOY 電話帳でカテゴリ判定）
        ├─ リスト1 にヒット → Phone2Name（カテゴリ A 向け TTS、例「○○薬局さんですね」）→ 担当者名へ
        ├─ リスト2 にヒット → Phone2Name（カテゴリ B 向け TTS）→ 担当者名へ
        ├─ ブラックリスト → 切断
        └─ NO_RESULT → 薬局名/施設名 聴取 → 担当者名へ
```

> **注意**: Brekeke 上の `incoming-category-classifier` モジュールの実際の next ラベル名・category 名のフォーマットは Brekeke 仕様に依存する。実装前に **実機の挙動を確認すること**（このサンプル CSV の リスト1〜5 が動作確認時のテストデータ）。

## 関連ドキュメント

- `docs/brekeke/モジュール詳細設定ガイド_1.md §4.6 Phone2Name` — params 仕様
- `docs/brekeke/モジュール詳細設定ガイド_1.md §6.2 incoming-category-classifier` — params 仕様
- `docs/brekeke/モジュール選定ガイド_v2.md §1.4 電話帳ベースの送信元分類` — 選定基準
