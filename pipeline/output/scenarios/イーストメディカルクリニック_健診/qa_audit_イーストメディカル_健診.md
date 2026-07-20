# QA監査レポート -- イーストメディカルクリニック 健診

**判定**: PASS
**設計書**: docs/designs/設計書_イーストメディカル_健診.yaml
**監査日時**: 2026-04-06
**設計書形式**: YAML

---

## サマリー

| カテゴリ | 結果 | BLOCKER | CRITICAL | WARNING |
|---|---|---|---|---|
| テンプレート適合性 | PASS | 0 | 0 | 0 |
| インテント網羅性 | PASS | 0 | 0 | 1 |
| エラーパス網羅性 | PASS | 0 | 0 | 1 |
| トーン＆マナー | PASS | 0 | 0 | 0 |
| 論理整合性 | PASS | 0 | 0 | 3 |

**総合判定**: PASS（generatorへ進行可）

---

## 層1: YAML機械的検証結果

### テンプレート適合性（T系）

| チェック | 結果 | 詳細 |
|---|---|---|
| T-1 全12セクション存在 | OK | 12/12 セクション検出 |
| T-2 必須フィールド非空 | OK | facility_name, group_name, flow_name, flow_type, purpose 全て設定済み |
| T-3 flow_type 値域 | OK | subflow |
| T-4 work_type 値域 | OK | gen2_migration |
| T-5 TODO_要確認 ↔ confirmation_items | OK | TODO_要確認=2箇所（office_id, business_hours）。confirmation_items=10件で網羅 |
| T-6 hearing_items >= 1件 | OK | 15件 |
| T-7 termination_patterns >= 1件 | OK | 6件 |
| T-8 context_fields >= 1件 | OK | 15件 |

### 論理整合性（L系 機械チェック）

| チェック | 結果 | 詳細 |
|---|---|---|
| L-1 save_to ↔ context_name | OK | 全15 hearing_items の save_to が context_fields に存在 |
| L-2 termination status ↔ range_values | OK | status=1,2,6 全て range_values に存在 |
| L-5 display_type 値域 | OK | 15フィールド全て許可値 |
| L-6 subflows 定義 | OK | 3件（氏名聴取, 生年月日聴取, 電話番号聴取） |
| L-8 sms_flag_routing | OK | enabled=false（saveCompletionFlag2dbで直接制御） |

---

## 層2: LLM審査結果

### カテゴリ1: テンプレート適合性 -- PASS

- 全12セクション完備。YAML構造に不備なし
- 基本情報: facility_name, group_name, flow_name, flow_type, purpose 全て充足
- office_id と business_hours は TODO_要確認として正しく管理。confirmation_items に列挙済み
- フロー構成: subflow型。3サブフロー（氏名/生年月日/電話番号）が Rule 9/10/11 準拠の完全コピー指定
- ゴールデンテンプレート参照: 予約管理型（用件4分岐）+ 健診受付型（smsFlag分岐）の組み合わせで妥当
- 命名規則: フロー名「イーストMC$健診_20260406」日付サフィックス統一。サブフローも同一日付
- classification の range_values: id/order/value 3フィールド揃い済み

### カテゴリ2: インテント網羅性 -- PASS（WARNING 1件）

- I-1: メインフロー聴取項目（order 4-15、計12件）全てに対応する step_details が存在。サブフロー（order 1-3）はRule 9準拠で省略妥当
- I-2: 全12 step_details に openai_rules.output_values が定義済み
- I-3: classify型（用件確認）の output_labels ["予約","変更","キャンセル","問い合わせ","企業予約"] と output_values（NO_RESULT除外後）が完全一致
- I-4: フロー図の5分岐（予約/変更/キャンセル/問い合わせ/企業予約）全てが step_details で説明されている
- I-5: **複合発話への対応方針が明示されていない**（W-4参照）。Gen2の類義語マッピングは充実しているが、「予約をキャンセルして新しい予約も」等の対応は不明
- I-6: メインフローは全てAmiVoice STT（DTMF不使用）。サブフローのDTMFはRule 9準拠
- openai_processing: classify型1件 + normalize型5件 + summarize型6件で妥当

### カテゴリ3: エラーパス網羅性 -- PASS（WARNING 1件）

- E-1: 全15 hearing_items に retry_count 設定済み（サブフロー: 2-3回、メインフロー: 3回 = Gen2仕様）
- E-2: 全12 step_details に retry_failure 設定済み（end_failure: 8件、skip: 4件）
- E-3: リトライ上限到達時の遷移先:
  - 用件確認 + 必須聴取ステップ（8件）: retry_failure="end_failure" -> END_聴取失敗
  - 追加の質問（4件）: retry_failure="skip" -> 正常終話にスキップ
- E-4: **TIMEOUT/ERROR/NO_RESULTの3パターンが各ステップのフロー図で省略**（W-3参照）。用件確認のみNO_RESULT -> リトライが図示。他ステップはnotesで「各ステップにリトライモジュール接続」と記載
- E-5: 異常系終話パターン3種全て定義済み（時間外/非通知/聴取失敗）
- E-6: 非通知アナウンス定義済み
- E-7: 時間外アナウンス定義済み。acceptance_times の false/TIMEOUT/ERROR -> 時間外パス（CLAUDE.md Rule 15 準拠）

### カテゴリ4: トーン＆マナー -- PASS

- M-1: 全TTS文言がです/ます調で統一
- M-2: 技術用語なし（DTMF/STT/コンテキスト等が患者向け文言に不在。「AI電話」は施設案内として許容）
- M-3: エラー時文言が適切（「大変申し訳ございません。ご回答が確認できませんでした。」-- 丁寧な謝罪+事実伝達）
- M-4: 冒頭アナウンスに施設名「イーストメディカルクリニック」含有
- M-5: 全終話パターンに「お電話ありがとうございました。それでは失礼いたします。」の挨拶含有
- M-6: リトライ促し文言はシステム標準 prompt_true（CLAUDE.md固定値）使用のため設計書側は非該当

### カテゴリ5: 論理整合性 -- PASS（WARNING 3件）

- L-1: save_to と context_name 完全一致（機械検証済み）
- L-2: termination_patterns の status値（1, 2, 6）が全て range_values に存在（機械検証済み）
- L-3: smsFlag 組み合わせの一貫性:
  - smsFlag=1: 予約/変更/問い合わせ完了（END_予約等）
  - smsFlag=2: キャンセル完了（END_キャンセル）
  - smsFlag=-1: 企業案内/聴取失敗/時間外/非通知（4パターン）
  - 同一条件で異なる smsFlag になるケースなし
- L-4: tts_modules がフロー図のTTSモジュールをカバー（ただし重複エントリあり: W-1参照）
- L-5: display_type 全フィールド許可値内（機械検証済み）
- L-6: subflows 3件定義済み（機械検証済み）
- L-7: N/A（flow_type=subflow）
- L-8: sms_flag_routing.enabled=false。smsFlag は termination_patterns で直接指定

---

## 指摘事項

### BLOCKER（人間の確認が必要 -- パイプライン停止）

なし

### CRITICAL（Directorが修正可能 -- 自動差し戻し）

なし

### WARNING（品質向上の提案 -- 修正推奨だがPASS可）

| # | セクション | 指摘内容 | 推奨アクション |
|---|---|---|---|
| W-1 | セクション9: tts_modules | **tts_modules に重複エントリの可能性**。`非通知_アナウンス` と `END_非通知` が同一文言（「恐れ入りますが、電話番号を通知しておかけ直しください。」）。`時間外_アナウンス` と `END_時間外` も同一文言。フロー図では非通知パスが `非通知_アナウンス(TTS) -> 完了フラグ_非通知 -> 切断` であり、END_非通知 TTSモジュールの位置が不明。generator が両方を別モジュールとして生成すると余剰TTSが発生する。 | (a) 非通知_アナウンス/時間外_アナウンスのみを残し END_非通知/END_時間外 を tts_modules から削除する、または (b) フロー図を `完了フラグ_非通知 -> END_非通知(TTS) -> 切断` に修正して非通知_アナウンスを削除する。いずれか一方に統一。 |
| W-2 | セクション4: flow_diagrams | **incoming-classifier の「海外」着信分岐が未記載**。incoming-classifier は非通知/海外/固定/携帯/その他を分類するが、海外着信のパスが設計されていない。 | 海外着信の処理方針を1行追記（例: 「海外 -> 非通知_アナウンスと同一パスに合流」または「海外 -> 通常パスに合流」）。generator は incoming-classifier のデフォルト動作で対応可能なため緊急性は低い。 |
| W-3 | セクション4: flow_diagrams | **用件別ルートの各聴取ステップにおけるリトライ分岐パスがフロー図で省略**。用件確認ステップのみ Retry/No more が図示されているが、後続11ステップでは省略。notes に「各用件ルートの各ステップにリトライモジュール（3回）を接続」と記載があり、step_details.retry_failure も全設定済みのため generator への情報は十分。 | 修正不要。品質向上のためには各ルートの先頭ステップにリトライ分岐の凡例を1つ追記するとより明確。 |
| W-4 | セクション7: step_details | **複合発話（例: 「予約をキャンセルして新しい予約もしたい」）への対応方針が未記載**。Gen2の会話型AIでは文脈理解で処理されていたが、Gen3のOpenAI分類では1ラベルのみ出力される。 | special_notes に「複合発話は最初に検出された用件を優先する」等の方針を追記すると、prompter がプロンプト設計時に考慮しやすい。OpenAIプロンプトで対応可能な範囲のため緊急性は低い。 |
| W-5 | セクション5: context_fields | **context_name "Desired_consultation" が他フィールドの camelCase 命名規則と不統一**。patientName, reservationDate 等は camelCase だが、Desired_consultation は先頭大文字+アンダースコア。Gen2からの移行名と推察。 | Dr.JOY側に既存参照がなければ "desiredConsultation" への統一を推奨。Brekeke動作には影響しないため修正優先度は低い。 |

---

## 設計品質の良い点

1. **Gen2仕様の忠実な移植**: 聴取順序（個人情報先行 -> 用件確認）、類義語マッピング、リトライ回数（3回）等のGen2互換性が丁寧に維持されている
2. **サブフロー設計**: Rule 9/10/11 準拠が各所に明記されており、generator が迷わない構造
3. **用件分岐の網羅性**: 5分岐（予約/変更/キャンセル/問い合わせ/企業予約）+ 4ルートの聴取項目が明確に定義されている
4. **終話パターンの完全性**: 正常系2パターン（END_予約等, END_キャンセル）+ 特殊系1パターン（END_企業案内）+ 異常系3パターン（END_聴取失敗, END_時間外, END_非通知）で全経路をカバー
5. **smsFlag設計のシンプルさ**: 用件別2値（1=予約等, 2=キャンセル）+ 異常系（-1）で管理。sms_flag_routingをdisabledにしてsaveCompletionFlag2dbの直接指定にしている点が明快
6. **AmiVoice辞書の充実**: 受診コース30種以上、用件確認の類義語（検針/返品/人間ロック等）が網羅
7. **TTS文言のSMS配慮**: SMS非言及の統一メッセージ採用により、固定電話への不適切な案内を回避。notes に設計理由を明記
8. **NON-BLOCKER管理**: confirmation_items 10件が明確に列挙され、仮設定値が設計書内に記載されており generator 実行に支障なし

---

## confirmation_items 状態（参考）

| # | 項目 | 状態 |
|---|---|---|
| 1 | office_id（施設ID） | 未解決 |
| 2 | 時間外アナウンス文言（標準文言で仮設定済み） | 未解決 |
| 3 | 非通知アナウンス文言（標準文言で仮設定済み） | 未解決 |
| 4 | 営業時間チェックの有無（acceptance_times配置あり・仮設定） | 未解決 |
| 5 | リトライ回数 Gen2仕様3回の維持可否 | 未解決 |
| 6 | 用件確認へのDTMF追加の可否 | 未解決 |
| 7 | 複数名予約（企業予約）の検出方式 | 未解決 |
| 8 | smsFlag値マッピング（Gen2: 0/1/2 -> Gen3: -1/1/2） | 未解決 |
| 9 | 追加の質問リトライ失敗時の挙動（正常終話スキップ vs END_聴取失敗） | 未解決 |
| 10 | medicalCardNumber/clinicalDepartment等の除外確認 | 未解決 |

> confirmation_items は全て未解決だが、設計書内に仮設定値が記載されており generator の実行には支障なし。最終確定前に人間が確認すること。
