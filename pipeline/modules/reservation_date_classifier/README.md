# reservation_date_classifier

予約日（変更/キャンセル時の現在予約日）パーサ。自由発話・DTMF を決定論的に `YYYY-MM-DD 00:00` /
`不明` / `NO_RESULT` へ正規化する @General$Script（OpenAI 不使用・Nashorn 動作・**期間制限なし版**）。

> 既存の認定テンプレ `docs/brekeke/script_templates/current_appointment_date.js`（相対日付解決, 439/439）とは
> **別実装**（出力契約・正規化・補正エンジンが異なる）。本モジュールは独立の受入対象。

## ファイル

| ファイル | 役割 |
|---|---|
| `script.js` | Brekeke IVR Script 本体（**正本**）|
| `oracle.py` | Python オラクル（`script.js` の忠実移植・`today` パラメタ化）|
| `test_oracle.py` | オラクルの単体テスト（**48/48 PASS** @ today=2026-06-12）|
| `REQUIREMENTS.md` | 入出力仕様・分岐・エッジケース・未解決論点 |
| `acceptance_test/` | Pattern 6 実機受入（日付非依存 20 ケース）の bivr / 設計書 / 手順 |

## 使い方

```bash
# オラクル回帰
python3 modules/reservation_date_classifier/test_oracle.py        # → PASS 48/48
# 任意入力の確認
python3 modules/reservation_date_classifier/oracle.py "来週月曜" "2030年7月15日" "わからない"
```

実機受入の手順は `acceptance_test/README.md` を参照。

## 受入ステータス（2026-06-12）

| 項目 | 状態 |
|---|---|
| Python オラクル | ✅ 48/48 PASS（日付非依存 20 + 日付依存 28、today 固定）|
| Pattern 6 実機受入（日付非依存 20）| ✅ **20/20 PASS**（2026-06-12、Thread-5504、`[TEST FAIL]` 0・`[TEST DONE]` 到達）|
| 認定レジストリ登録 | ✅ 認定済み（2026-06-12、`modules/README.md`）|

✅ **検出バグ 7 件は判断・対応済**（B-1 しあさって/B-2 来週週ズレ/B-3 JST固定/B-7 入力名 を修正、
B-4 秒なし・B-5 通知発火 は現状維持、B-6 runCorrection デッドは据え置き）。詳細 `BUG_REPORT_20260612.md`。
`oracle.py` は修正後 `script.js` の忠実移植を維持し `test_oracle.py` 48/48 PASS。実機 20/20 PASS・レジストリ登録済（2026-06-12）。
