# QA監査レポート -- 鹿児島厚生連病院 診療

**判定**: PASS
**設計書**: docs/designs/設計書_鹿児島厚生連病院_診療.yaml
**監査日時**: 2026-04-03
**設計書形式**: YAML
**監査回次**: 第4回（再審査）

---

## サマリー

| カテゴリ | 結果 | BLOCKER | CRITICAL | WARNING |
|---|---|---|---|---|
| テンプレート適合性 | PASS | 0 | 0 | 0 |
| インテント網羅性 | PASS | 0 | 0 | 1 |
| エラーパス網羅性 | PASS | 0 | 0 | 0 |
| トーン＆マナー | PASS | 0 | 0 | 1 |
| 論理整合性 | PASS | 0 | 0 | 2 |

**総合判定**: PASS（generatorへ進行可）

---

## 層1: YAML機械的検証結果

全項目パス。

| チェック項目 | 結果 |
|---|---|
| T-1: 全12セクション存在 | OK |
| T-2: 必須フィールド非空 | OK（facility_name, group_name, flow_name, flow_type, purpose 全て設定済み）|
| T-3: flow_type 値域 | OK（subflow）|
| T-4: work_type 値域 | OK（new）|
| T-5: TODO_要確認 | OK（0件）|
| T-6: hearing_items >= 1 | OK（15件）|
| T-7: termination_patterns >= 1 | OK（7件）|
| T-8: context_fields >= 1 | OK（16件）|
| L-1: save_to ↔ context_name | OK（全15項目一致）|
| L-2: termination status ↔ range_values | OK（0,1,2,6 全て定義済み）|
| L-5: display_type 値域 | OK（全16フィールド許可値内）|
| L-6: subflow定義 | OK（5件）|
| L-8: sms_flag_routing | OK（enabled=true, routing_keys=["classification"]）|

---

## 層2: LLM審査詳細

### カテゴリ1: テンプレート適合性 -- PASS

- T-1〜T-8: 全項目パス（機械検証済み）
- flow_structure.flows に6件（main 1 + sub 5）、subflows に5件 -- 対応一致
- confirmation_items に未解決BLOCKER 1件（B-1: 電話番号/環境）+ NON-BLOCKER 2件あり。設計書冒頭コメントで明示的に警告済み

### カテゴリ2: インテント網羅性 -- PASS（WARNING 1件）

- **I-1**: hearing_items 15件全てに対応する step_details あり（個人情報4件はRule 9準拠で省略適切、メインフロー11件は全て記載）
- **I-2**: openai_processing != none の全ステップに output_values 定義済み
- **I-3**: 分岐型（classify）の output_labels ↔ output_values 一致:
  - 用件確認: [予約, 変更, キャンセル, その他問い合わせ] ↔ 同+NO_RESULT
  - 次回予約希望: [希望あり, 希望なし/不明] ↔ 同+NO_RESULT
  - FAQ確認: [なし, 質問あり] ↔ 同+NO_RESULT
  - normalize/summarize系: output_labels=[] -- 分岐なしのため適切
- **I-4**: フロー図の全分岐が step_details で網羅
- **I-5**: 用件はDTMF 4択のため複合発話リスク低
- **I-6**: DTMF入力（用件確認）のボタン番号対応が notes と mapping の両方に明記

### カテゴリ3: エラーパス網羅性 -- PASS

- **E-1**: 全15 hearing_items に retry_count 設定済み（2回が主、生年月日・電話番号は1回）
- **E-2**: 全11 step_details に retry_failure 設定済み（用件確認=end_failure、他=skip）
- **E-3**: リトライ上限到達時の遷移先が全ステップのフロー図で明記:
  - 診療科: No more → saveContext2DB_診療科_登録なし → 用件_アナウンス（skip）
  - 用件確認: No more → 終話_失敗_アナウンス → 切断（end_failure）
  - その他フリー聴取: No more → 次ステップ or 終話（skip）
  - FAQ確認: No more → 終話_その他問合せ_アナウンス
- **E-4**: フロー図に全STT/OpenAIステップの TIMEOUT/ERROR/NO_RESULT 3パターン分岐記載
- **E-5**: 異常系終話パターン完備: END_聴取失敗(status=0) / END_非通知(status=2) / END_時間外(status=6)
- **E-6**: 非通知着信アナウンス定義済み
- **E-7**: 時間外着信アナウンス定義済み（acceptance_times使用、365日 7:00-20:00）

### カテゴリ4: トーン＆マナー -- PASS（WARNING 1件）

- **M-1**: 全TTS文言がです/ます調で統一
- **M-2**: 技術用語（DTMF, STT, コンテキスト等）がTTS文言に不使用
- **M-3**: エラー時文言に「恐れ入りますが」「申し訳ございません」等の緩衝表現あり
- **M-4**: 冒頭アナウンスに「鹿児島厚生連病院」含む
- **M-5**: 全終話アナウンスに「お電話ありがとうございました」含む
- **M-6**: リトライ促しはRetry Counter prompt_true（システム固定値）で対応

### カテゴリ5: 論理整合性 -- PASS（WARNING 2件）

- **L-1〜L-8**: 機械検証全パス
- **L-3**: smsFlag の組み合わせが網羅的かつ矛盾なし（予約/変更/その他=1、キャンセル=2、異常系=-1。キャンセル→変更更新時はclassification変更でsmsFlag=1に遷移）
- **L-4**: tts_modules（21件）がフロー図の全TTSモジュールをカバー

---

## 指摘事項

### BLOCKER（人間の確認が必要 -- パイプライン停止）

なし

> **注記**: confirmation_items B-1（電話番号/環境の未確定）は設計書冒頭で明示的に警告されており、generator実行前に人間が解消する前提。設計書自体の構造・論理に問題はないためQAとしてはBLOCKERとしない。

### CRITICAL（Directorが修正可能 -- 自動差し戻し）

なし

### WARNING（品質向上の提案 -- 修正推奨だがPASS可）

| # | セクション | 指摘内容 | 推奨アクション |
|---|---|---|---|
| W-1 | セクション9: tts_modules | 終話_その他問合せ_アナウンスが「折り返しショートメールもしくは電話にて」とSMSに言及。固定電話発信者にも読み上げられるが、special_notesに「もしくは電話にてでカバーしており携帯/固定の終話TTS分岐は設けない（設計判断済み）」と記載済み。 | 設計判断として妥当。対応不要 |
| W-2 | セクション4: flow_diagrams (RAGサブフロー) | RAGサブフロー内の「params.moduleでメインフローのSTT結果を参照」が技術的に曖昧。Custom Jump to Flowでサブフロー遷移後、メインフローモジュールのCross-flow参照が可能かはBrekeke実装依存。 | generatorが既存RAGサブフロー構造を参照して適切に構築可能。special_notesにデータ受け渡し方法の注記追加を推奨 |
| W-3 | セクション9: tts_modules | FAQ回答_アナウンスのannouncement が「（IVRプロパティで設定）」。RAG検索結果の動的読み上げの仕組みが不明確。confirmation_items N-2に記載済み。 | N-2解消後に文言確定。generator進行に支障なし |
| W-4 | セクション7: step_details (診療科) | 診療科の output_values に「（診療科リスト22科のいずれか）」「フリーテキスト」という抽象的記述あり。ただし診療科はsuccess 1本受け（分岐なし）のため、next配列には影響しない。prompterはcontext_fields.clinicalDepartment.range_values（24値）を参照可能。 | 軽微。prompterが参照先を特定できるため対応不要 |

---

## 設計書の品質評価

本設計書は全体として**高品質**であり、generatorが迷わず構築できるレベルに達している。

**特に優れている点**:
- フロー図が全ルート（予約/変更/キャンセル/その他問い合わせ + キャンセル→変更更新）の分岐を詳細に記述
- キャンセル→変更更新の複雑なロジック（classification更新 + 予約希望時期再聴取 + smsFlag変更）が正確に設計
- FAQループ構造（質問あり→RAG検索→回答→再質問）の繰り返し動作が明示的
- AmiVoice辞書が充実（診療科22科+類義語47語、用件辞書、次回予約希望辞書）
- 全15聴取項目の save_to ↔ context_fields（16件）の完全な整合性
- smsFlag分岐設計（routing_keys, patterns）が明確
- 終話パターン7件で全ルートの終了状態を網羅
- 設計判断の根拠がspecial_notesに明記（携帯/固定TTS分岐省略の理由等）
- confirmation_itemsがBLOCKER/NON-BLOCKER/解消済みの3段階で整理

**BLOCKER=0、CRITICAL=0。generatorへの進行を許可する。**
confirmation_items B-1（電話番号/環境の確定）はgenerator実行前に人間が解消すること。
