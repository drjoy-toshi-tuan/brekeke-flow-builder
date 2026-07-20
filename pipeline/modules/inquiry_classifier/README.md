# inquiry_classifier（用件分類・自由発話・決定論）

総合相談室の「ご用件」自由発話を OpenAI 不使用で分類する Script。亀田 `OpenAI_用件確認` の置換。

- **正本**: `script.js`（Brekeke @General$Script / Nashorn ES5。`{{INPUT_MODULE}}`/`{{CONTEXT_NAME}}`/`{{CONTEXT_DISPLAY_TYPE}}` を充填）
- **オラクル**: `oracle.py`（`classify(input)`）/ `test_oracle.py`
- **受入ケース**: `acceptance_test/cases.tsv`

## 出力と優先順位
`相談` / `予約` / `大代表` / `定型案内` / `その他` / `NO_RESULT`
顧客大原則: **相談 ＞ 予約 ＞ 大代表 ＞ 定型案内**（先勝ち）。相談予約は相談優先（弾かない）／予約系は弾く。

## 受入結果
- **oracle 30/30 PASS**（2026-06-12。相談/予約/大代表/定型案内/その他/NO_RESULT＋相談予約優先＋予約弾き）
- 実機受入（Pattern 6）: **未**（人手・Nashorn↔Python パリティ確認込み）

## 注意
- `その他`/`NO_RESULT` の切り分けは決定論ポリシー（安全側＝その他＝伝言折返し）。REQUIREMENTS 参照・調整可。
- 「外来時間」「診察時間」等のキーワード重複は既知の限界（実データで語彙チューニング）。
- 実モジュール化（Brekeke 構築）は人手。本ディレクトリは Script ＋認定まで。
