# QA監査レポート -- 朝日大学病院 診療

**判定**: PASS
**設計書**: docs/designs/設計書_朝日大学病院_診療.yaml
**監査日時**: 2026-04-07 17:00
**設計書形式**: YAML
**審査回数**: 2回目（前回FAIL指摘 C-1/C-2/C-3 は全て解消済み）

---

## サマリー

| カテゴリ | 結果 | BLOCKER | CRITICAL | WARNING |
|---|---|---|---|---|
| テンプレート適合性 | PASS | 0 | 0 | 0 |
| インテント網羅性 | PASS | 0 | 0 | 2 |
| エラーパス網羅性 | PASS | 0 | 0 | 1 |
| トーン＆マナー | PASS | 0 | 0 | 1 |
| 論理整合性 | PASS | 0 | 0 | 3 |

**総合判定**: PASS（generatorへ進行可） -- WARNING 7件は品質向上の提案

---

## 前回CRITICAL指摘の解消確認

| 前回# | 内容 | 状態 |
|---|---|---|
| C-1 | 診療科_キャンセル output_labels がプレースホルダー | **解消**: 24ラベル明示的に列挙済み |
| C-2 | classification range_values に id フィールド欠落 | **解消**: id: "1"/"2"/"3" 追加済み |
| C-3 | clinicalDepartment range_values に id フィールド欠落 | **解消**: id: "1"~"24" 追加済み |

---

## 層1: YAML機械的検証結果

### テンプレート適合性（T系）

| チェック | 結果 | 詳細 |
|---|---|---|
| T-1 全12セクション存在 | OK | 12/12 |
| T-2 必須フィールド非空 | OK | facility_name, group_name, flow_name, flow_type, purpose 全て入力済 |
| T-3 flow_type値域 | OK | subflow |
| T-4 work_type値域 | OK | gen2_migration |
| T-5 TODO_要確認突合 | OK | TODO 1箇所（office_id）、confirmation_items 8件中に含む |
| T-6 hearing_items存在 | OK | 17件 |
| T-7 termination_patterns存在 | OK | 6件 |
| T-8 context_fields存在 | OK | 17件 |

### 論理整合性（L系・機械的検証）

| チェック | 結果 | 詳細 |
|---|---|---|
| L-1 save_to <-> context_name | OK | hearing_items 17件 + step_details 全て一致 |
| L-2 termination status <-> range_values | OK | 全6パターンのstatus（"1","2"）が range_values（"0","1","2"）に含まれる |
| L-5 display_type値域 | OK | 全17フィールド正常 |
| L-6 subflowチェック | OK | 4サブフロー定義済 |
| L-8 sms_flag_routing | OK | enabled=false（分岐不要） |

---

## 指摘事項

### BLOCKER（人間の確認が必要 -- パイプライン停止）

なし

> 注: office_id = TODO_要確認 は既にDirectorが確認レポートで報告済み、confirmation_items に記載済み。generatorはプレースホルダーで出力可能なため、パイプラインはブロックしない。本番デプロイ前に解決必須。

### CRITICAL（Directorが修正可能 -- 自動差し戻し）

なし

### WARNING（品質向上の提案 -- 修正推奨だがPASS可）

| # | カテゴリ | セクション | 指摘内容 | 推奨アクション |
|---|---|---|---|---|
| W-1 | インテント | セクション7: step_details | **診療科_変更/診療科_キャンセルの output_values がプレースホルダー記法**（「(22科の診療科名)」「(診療科_変更と同じ)」）。hearing_items.output_labels（SSOT）が24値を明示列挙しているためgeneratorは動作可能だが、prompterがstep_detailsを参照する際に曖昧になりうる。 | 可能であればstep_detailsのoutput_valuesにも24科を明示列挙。ただし、hearing_items.output_labelsが完備しているため必須ではない。 |
| W-2 | インテント | セクション10: amivoice_dictionary | **予約日_変更/予約日_キャンセル/予約希望日 の AmiVoice辞書が未定義**。CLAUDE.md規定「日付入力 → 和暦辞書 + month辞書 + day辞書」に基づき、日付入力用のprofile_wordsが必要。辞書なしではSTT精度が低下する可能性がある。 | 3ステップに日付辞書（month辞書 + day辞書）のprofile_words記載を追加。予約希望日はフリーテキストのため必須ではないが、予約日_変更/予約日_キャンセルには追加推奨。 |
| W-3 | エラーパス | セクション4: flow_diagrams | **フロー図の終話パターン一覧に「END_聴取失敗（電話番号サブフロー内）」が記載されているが、セクション8のtermination_patternsに対応エントリがない**。電話番号聴取サブフローは termination: "return" で常に結果（1: 携帯 / 2: その他）を返却するため、メインフロー側に聴取失敗の終話パターンは不要と思われる。フロー図の記載が過剰な可能性。 | フロー図から「END_聴取失敗（電話番号サブフロー内）」の行を削除するか、実際にメインフロー側で聴取失敗を処理する場合はtermination_patternsにエントリを追加。 |
| W-4 | トーン | セクション8: termination_patterns | **END_変更_確認（正常終話, status=1）のTTSに「ありがとうございました」が含まれていない**。同じstatus=1のEND_キャンセルには「お電話ありがとうございました」が含まれており、トーンに不統一がある。 | END_変更_確認のアナウンス末尾を「...ご確認ください。お電話ありがとうございました。それでは失礼いたします。」に変更を検討。 |
| W-5 | 論理整合 | セクション5: context_fields | **DesiredreservationDate のキャメルケースが不統一**。他フィールド（reservationDate, patientName等）はlowerCamelCaseだが、本フィールドは先頭大文字+途中小文字。正規形は `desiredReservationDate`。 | Gen2から引き継いだ命名の可能性あり。既存データとの互換性を確認の上、命名統一を検討。互換性の制約があれば現状維持で可。 |
| W-6 | 論理整合 | セクション7: step_details | **薬処方確認_キャンセルのmappingがプレースホルダー**「(薬処方確認_変更と同じ特殊ルール)」。薬処方確認の「飲んでいない」系表現の特殊分類ルールはGen2固有の重要ルールであり、prompterがプロンプトを記述する際に正確な参照が必要。 | 薬処方確認_変更のmappingをコピーして明示的に記載。特に「飲んでいない」判定の優先ルール（否定表現が含まれていれば「飲んでいない」に分類）を明記。 |
| W-7 | 論理整合 | セクション10: amivoice_dictionary | **診療科_キャンセル/薬処方確認_キャンセル/残薬確認_キャンセルの辞書が文字列参照**（「(xxx_変更と同一の辞書を使用)」）。generatorは変更ルートの辞書をコピーして適用可能だが、明示的な辞書データの方が確実。 | 変更ルートの辞書データをコピーして明示記載するのが望ましい。ただしgeneratorが参照解決可能なため必須ではない。 |

---

## 検証詳細

### カテゴリ1: テンプレート適合性

**結果: PASS**

YAML層1の機械的検証（T-1〜T-8）は全項目PASS。前回CRITICALのC-2/C-3（range_values id欠落）は修正済み。全12セクションが適切に構成されている。

### カテゴリ2: インテント網羅性

**結果: PASS（WARNING 2件: W-1, W-2）**

- **I-1（hearing_items <-> step_details対応）**: メインフローの全聴取項目にstep_detailsが定義済み。サブフロー項目（氏名/生年月日/診察券番号/電話番号）はRule 9完全コピーのため対象外。OK
- **I-2（output_values定義）**: openai_processing != none の全ステップにoutput_values定義あり。OK
- **I-3（output_labels <-> output_values一致）**: 前回CRITICALの診療科_キャンセル output_labelsは24値に修正済み。step_details側のプレースホルダーはW-1として記録。用件確認/薬処方確認/残薬確認/携帯用の質問はhearing_items.output_labelsとstep_details.output_valuesが一致。OK
- **I-4（フロー図分岐網羅）**: 用件確認4分岐（変更/キャンセル/確認/予約）、診療科分岐（病理診断科/有効科/登録なし）、薬処方確認/残薬確認/携帯用の質問の全分岐がstep_detailsに記載。OK
- **I-5（複合発話考慮）**: 明示的記載はないが、用件確認のOpenAIプロンプトで対処可能（prompter担当）。OK
- **I-6（DTMF番号対応）**: 本フローのDTMF入力は数値入力（生年月日/診察券番号/電話番号）のみで全てサブフロー。N/A

### カテゴリ3: エラーパス網羅性

**結果: PASS（WARNING 1件: W-3）**

- **E-1（retry_count設定）**: 全17 hearing_itemsに設定済み。用件確認=3回（Gen2準拠）、他=2回。OK
- **E-2（retry_failure設定）**: 全step_detailsに設定済み。用件確認=end_failure、他=skip。OK
- **E-3（リトライ上限到達時の行き先）**: 用件確認→END_代表案内（フロー図にNo more明記）、診療科→空のまま続行（skip, フロー図に明記）。OK
- **E-4（TIMEOUT/ERROR/NO_RESULT分岐）**: フロー図にNO_RESULT→リトライの分岐を各ステップで明記。TIMEOUT/ERRORはSTT標準動作としてリトライに統合。OK
- **E-5（異常系終話パターン）**: END_非通知/END_初診不可/END_代表案内/END_代表案内2の4パターンで全異常ケースをカバー。OK
- **E-6（非通知着信アナウンス）**: incoming-classifier使用。非通知_アナウンスにTTS文言定義済み（186案内付き）。OK
- **E-7（時間外着信アナウンス）**: acceptance_times不使用（Gen2設計準拠、confirmation_itemsで追加要否確認中）。N/A

### カテゴリ4: トーン＆マナー

**結果: PASS（WARNING 1件: W-4）**

- **M-1（です/ます調統一）**: 全TTS文言（20件超）がです/ます調で統一。OK
- **M-2（技術用語不使用）**: DTMF/STT/コンテキスト等の患者に見えてはいけない技術用語なし。OK
- **M-3（エラー時文言）**: リトライはRetry Counter標準prompt_true使用（「申し訳ございません。うまく聞き取りが出来ませんでした。再度、」）。代表案内系の文言も「恐れ入りますが」等の緩衝表現あり。OK
- **M-4（冒頭施設名）**: 「お電話ありがとうございます。朝日大学病院の予約専用AI電話です。」施設名含む。OK
- **M-5（終話挨拶）**: 6パターン全てに「それでは失礼いたします」含む。正常終話系の一部に「お電話ありがとうございました」あり。W-4で不統一を指摘。OK
- **M-6（リトライ緩衝表現）**: Retry Counter標準文言使用。OK

### カテゴリ5: 論理整合性

**結果: PASS（WARNING 3件: W-5, W-6, W-7）**

- **L-1（save_to <-> context_name）**: 全17 hearing_items + 全step_detailsの save_to が context_fields に存在（機械検証済み）。OK
- **L-2（termination status <-> range_values）**: status "1"（未処理/正常終話）と "2"（代表案内/異常終話）が全てrange_values（"0","1","2"）に含まれる。OK
- **L-3（smsFlag網羅性）**: 正常終話（END_キャンセル/END_変更_確認）= smsFlag "1"、異常終話（END_非通知/END_初診不可/END_代表案内/END_代表案内2）= smsFlag "-1"。同一条件で異なるsmsFlagになるケースなし。OK
- **L-4（tts_modules網羅性）**: フロー図に登場する全TTSモジュール（20件）がtts_modulesに定義済み。サブフロー用TTS（氏名_聴取/生年月日_聴取/診察券番号_聴取）も記載あり。OK
- **L-5（display_type値域）**: 全17フィールド正常（機械検証済み）。OK
- **L-6（subflow定義）**: flow_type=subflow に対してsubflows 4件定義済み。全サブフローにname/target/transition_module/termination/notes完備。OK
- **L-7（flow_type整合性）**: flow_type=subflow + work_type=gen2_migration。N/A（L-7は1flow型のチェック）
- **L-8（sms_flag_routing）**: enabled=false。smsFlag分岐不要の設計（正常=1, 異常=-1 で統一）。OK

---

## ゴールデンテンプレート比較

**参照パターン**: 予約管理型（予約・変更・キャンセル）

本設計書は予約管理型ゴールデンテンプレートの変形であり、以下の点で標準と異なる:

| 項目 | ゴールデンテンプレート | 本設計書 | 評価 |
|---|---|---|---|
| 聴取順序 | 用件確認 → 個人情報 | 個人情報 → 用件確認 | Gen2準拠。意図的な設計差異 |
| 用件入力方式 | DTMF 4択 | 音声のみ（AmiVoice STT） | Gen2準拠。音声認識による自然な対話 |
| acceptance_times | なし（テンプレートもなし） | なし | 一致 |
| 薬処方/残薬確認 | なし | あり | 施設固有の追加聴取。適切 |
| サブフロー構成 | 個人情報一括サブフロー | 氏名/生年月日/診察券番号/電話番号 4分割 | Rule 9準拠。分割サブフロー |
| 予約不可診療科 | あり（リスト定義） | あり（病理診断科のみ） | 施設固有 |

**欠落要素なし**: ゴールデンテンプレートに含まれる必須要素（冒頭チェーン、非通知分岐、リトライ設計、終話パターン、コンテキストフィールド）は全て設計書に含まれている。
