# flow_draft — 千葉徳洲会病院 診療2
作成日: 2026-07-13 / 作成者: hamaguchi / ステータス: 壁打ち中

---

## ブロック構造一覧

| # | step 名 | ブロック型 | choices / conditions | 備考 |
|---|---|---|---|---|
| 1 | opening | `opening` | — | 受付時間判定 acceptance_times 込み |
| 2 | 当日翌日確認 | `hearing` | choices なし → yes_no_classifier | はい→予約センター案内, いいえ→次へ |
| 3 | 氏名聴取 | `patient_name` | — | scaffold インライン展開（Jump to Flow 不使用）|
| 4 | 生年月日聴取 | `dob` | — | **復唱 OFF**（施設固有ルール）|
| 5 | 電話番号聴取 | `phone` | — | 復唱あり（唯一の復唱許可項目）|
| 6 | 用件確認 | `hearing` | choices: 予約/変更/キャンセル/確認 | 4択 enum。出力値を CMR 後段で参照 |

### 予約ルート

| # | step 名 | ブロック型 | choices / conditions | 備考 |
|---|---|---|---|---|
| 7a | 受診歴確認 | `hearing` | choices: 新規/再診 | 2択 enum |
| 8a-新 | 紹介状確認 | `hearing` | choices なし → yes_no_classifier | いいえ→END_紹介状無し |
| 9a-新 | 病名聴取 | `free_text` | — | 紹介状あり新規のみ |
| 7a-再 | 診察券番号聴取_再診 | `card_number` | — | 再診ルートのみ |
| 10a | 診療科聴取_予約 | `clinical_department` | — | TTS: 「受診を希望される診療科」|
| 11a | 診療科分類_予約 | `clinical_department_classifier` | 予約不可6科→call_transfer予約センター / 健診→call_transfer健診センター / other→次 | 眼科/放射線治療科/麻酔科/緩和ケア科/小児科/皮膚科が不可。婦人科は通過 |
| 12a | 予約日聴取 | `script` | reservation_date_classifier | **認定済み部品**。YYYY-MM-DD / 不明 / NO_RESULT |
| 13a | その他問い合わせ聴取 | `faq` | — | 全終話前 RAG |

### 変更ルート

| # | step 名 | ブロック型 | choices / conditions | 備考 |
|---|---|---|---|---|
| 7b | 診察券番号聴取_変更 | `card_number` | — | 用件確認直後 |
| 8b | 診療科聴取_変更キャンセル | `clinical_department` | — | TTS: 「予約票に記載されている診療科」（予約ルートと文言別） |
| 9b | 診療科分類_変更キャンセル | `clinical_department_classifier` | 健診→call_transfer健診センター / other→次 | 予約不可科チェックは変更/キャンセルでは行わない（すでに予約済みのため） |
| 10b | 予約日聴取_変更 | `script` | reservation_date_classifier | 現在の予約日を聴取 |
| 11b | 希望時期聴取 | `free_text` | — | 変更希望時期（自由発話収集・Scripts 正規化）|
| 12b | その他問い合わせ聴取 | `faq` | — | 全終話前 RAG |

### キャンセルルート

| # | step 名 | ブロック型 | choices / conditions | 備考 |
|---|---|---|---|---|
| 7c | 診察券番号聴取_キャンセル | `card_number` | — | 用件確認直後 |
| 8c | 診療科聴取_変更キャンセル | `clinical_department` | — | 変更ルートと同一ブロックに合流可 |
| 9c | 診療科分類_変更キャンセル | `clinical_department_classifier` | 健診→call_transfer健診センター / other→次 | 変更と合流可 |
| 10c | 予約日聴取_キャンセル | `script` | reservation_date_classifier | 現在の予約日を聴取 |
| 11c | キャンセル理由聴取 | `free_text` | — | Scripts 正規化 |
| 12c | その他問い合わせ聴取 | `faq` | — | 全終話前 RAG |

### 確認ルート

| # | step 名 | ブロック型 | choices / conditions | 備考 |
|---|---|---|---|---|
| 7d | 診察券番号聴取_確認 | `card_number` | — | 用件確認直後 |
| 8d | 確認事項聴取 | `faq` | — | 健診キーワード検出→call_transfer健診センター。診療科聴取なし |
| 9d | 最後の質問聴取 | `faq` | — | 全終話前 RAG |

### 合流・後段

| # | step 名 | ブロック型 | choices / conditions | 備考 |
|---|---|---|---|---|
| — | 連絡方法聴取 | `hearing` | choices なし → yes_no_classifier | phone_branch の携帯(MOBILE)ルートのみ。固定/OTHER はスキップ |
| — | smsFlag分岐 | `context_match_router` | 新規/再診=1 / 変更/キャンセル=2 / 確認=3 | 用件 classification を参照 |
| — | END_当日翌日 | `call_transfer` | — | 予約センター 047-774-0489 |
| — | END_紹介状無し | `termination` | — | 即終話 |
| — | END_予約不可診療科 | `call_transfer` | — | 予約センター 047-774-0489 |
| — | END_健診センター | `call_transfer` | — | 健診センター 047-774-0385 |
| — | termination | `termination` | — | 折り返し受付完了 |

---

## 確認済みブロック型決定事項

| step | 旧案 | 確定型 | 理由 |
|---|---|---|---|
| 予約日聴取（変更/キャンセル） | `hearing` / `free_text` | `script` (reservation_date_classifier) | 認定済み部品。決定論的 YYYY-MM-DD 正規化 |
| 内容確認聴取 / 確認事項聴取 | `hearing` / `free_text` | `faq` | RAG 照合ブロック |
| 最後の質問聴取 | `free_text` | `faq` | 全終話前 RAG（診療1 と同方針）|
| その他問い合わせ聴取 | `free_text` | `faq` | 全終話前 RAG（予約/変更/キャンセルルート共通）|

---

## BLOCKER（director 着手前に解消が必要）

- office_id 未確認
- 受付時間（曜日・時間帯）未確認
- 診療2 のフロー名・050番号 未確定
- 診療1 との共存/置き換え関係 未確認
