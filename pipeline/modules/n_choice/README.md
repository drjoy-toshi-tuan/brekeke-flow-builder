# n_choice（N択分類 決定論エンジン）

DTMF または音声キーワードで N 択メニューを決定論的に判定する汎用 Script。OpenAI 不使用。

- **正本**: `script.js`（Brekeke @General$Script / Nashorn ES5。`{{…}}` を設問ごとに充填）
- **オラクル**: `oracle.py`（`classify(input, config)` 純関数）/ `test_oracle.py`
- **受入ケース**: `acceptance_test/cases.tsv`（config = 亀田・発信元3分類）

## 使い方（設問ごとに設定を充填）
`{{DTMF_MAP}}` `{{KEYWORD_PATTERNS}}` 等に設問固有の選択肢・語彙を入れて Script モジュール本体とする。
例（亀田・発信元）: `DTMF_MAP={"1":"患者本人・家族","2":"連携医療機関","3":"行政"}` ＋
keyword（本人/家族/患者… → 患者本人・家族 等）。`oracle.py` の `KAMEDA_CALLER_TYPE` 参照。

> 実モジュール化（Brekeke 画面での @General$Script 構築・フロー組込）は人手の別工程。
> 本ディレクトリは「Script モジュール用スクリプト＋認定」まで。

## 受入結果
- **oracle 29/29 PASS**（2026-06-12。DTMF/全角/数字語尾trim/keyword3分類/AmiVoice重複/フィラー・無関連→NO_RESULT）
- 実機受入（Pattern 6）: **未**（人手。Nashorn↔Python パリティ確認込み）

## 用途（亀田 総合相談室・OpenAIゼロ化）
- 発信元確認（患者本人・家族/連携医療機関/行政）
- 患者区分確認（入院/外来/新規）
- 相談種別確認（相談予約/受診）
※ 各設問で `DTMF_MAP`・`KEYWORD_PATTERNS` を差し替えて使う。
