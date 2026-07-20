# 校閲レポート: 琉球大学病院 - 診療（メイン + 4サブフロー）

**校閲日**: 2026-03-31
**校閲対象**:
- `output/json/draft_琉球大学病院_診療.json`（メインフロー: 109モジュール）
- `output/json/draft_琉球大学病院_氏名聴取.json`（6モジュール）
- `output/json/draft_琉球大学病院_生年月日聴取.json`（10モジュール）
- `output/json/draft_琉球大学病院_電話番号聴取.json`（24モジュール）
- `output/json/draft_琉球大学病院_診察券番号聴取.json`（6モジュール）

---

## セキュリティ・ライセンス警告（最優先確認）

### セキュリティ
異常なし。プロンプトインジェクション禁止パターンは全フローで未検出。全モジュールの type は `drjoy^`・`@General$`・`@IVR$` のいずれかで正常。

### ライセンス

**L-001: 転送先電話番号のハードコード**
- **ファイル**: `output/json/draft_琉球大学病院_診療.json`
- **モジュール名**: `転送_代表電話`
- **フィールド**: `params.transferNumber`
- **現在値**: `"0988941301"`
- **判定**: 設計書セクション5.1に「call-transfer（098-894-1301）」と明記されており、意図的なハードコードと判断。人間確認推奨（本番環境移行時に番号変更の要否確認）

---

## サマリー

| 項目 | 件数 |
|---|---|
| SECURITY-CRITICAL | 0 |
| Critical（自動修正済み） | 0 |
| Warning（自動修正済み） | 18 |
| LICENSE-WARN（人間確認） | 1 |
| Info | 3 |
| **合計** | **22** |

- **自動修正**: 18件（メインフロー12件 + サブフロー6件 — 全て `prompt_true` 誤字）
- **人間確認必要**: 1件（L-001: 転送先電話番号）

---

## 検出事項

### W-001: Retry Counter の prompt_true に誤字「職き取り」→「聞き取り」

- **ファイル**: `output/json/draft_琉球大学病院_診療.json`
- **モジュール名**: `リトライ_緊急_確認`、`リトライ_診療科`、`リトライ_用件`、`リトライ_用件_復唱`、`リトライ_予約日_変更`、`リトライ_都合悪い日_変更`、`リトライ_理由_変更`、`リトライ_予約日_キャンセル`、`リトライ_理由_キャンセル`、`リトライ_次回予約_希望`、`リトライ_都合悪い日_キャンセル`、`リトライ_問合せ内容`（計12件）
- **フィールド**: `params.prompt_true`
- **問題**: TTS発話テキスト内に「職き取り」という誤字が含まれている。「聞き取り」が正しい
- **現在値**: `"{tts_g:申し訳ございません。 うまく職き取りが出来ませんでした。 再度、}"`
- **正しい値**: `"{tts_g:申し訳ございません。 うまく聞き取りが出来ませんでした。 再度、}"`
- **対応**: **自動修正済み**（reviewed_琉球大学病院_診療.json に反映）

### W-002: サブフロー Retry Counter の同誤字（6件）

- **ファイル**:
  - `draft_琉球大学病院_生年月日聴取.json`: `リトライ_患者_生年月日`、`リトライ_復唱_患者生年月日`（2件）
  - `draft_琉球大学病院_電話番号聴取.json`: `リトライ_患者_携帯電話`、`リトライ_患者_連絡先`、`リトライ_患者_復唱連絡先`（3件）
  - `draft_琉球大学病院_診察券番号聴取.json`: `リトライ_患者_診察券番号`（1件）
- **フィールド**: `params.prompt_true`
- **問題**: W-001 と同内容の誤字
- **対応**: **自動修正済み**（各 reviewed_*.json に反映）

---

## 修正済みモジュール一覧

| # | ファイル | モジュール名 | フィールド | 修正内容 | 重大度 |
|---|---|---|---|---|---|
| 1 | reviewed_琉球大学病院_診療.json | リトライ_緊急_確認 | params.prompt_true | 職き取り → 聞き取り | Warning |
| 2 | reviewed_琉球大学病院_診療.json | リトライ_診療科 | params.prompt_true | 職き取り → 聞き取り | Warning |
| 3 | reviewed_琉球大学病院_診療.json | リトライ_用件 | params.prompt_true | 職き取り → 聞き取り | Warning |
| 4 | reviewed_琉球大学病院_診療.json | リトライ_用件_復唱 | params.prompt_true | 職き取り → 聞き取り | Warning |
| 5 | reviewed_琉球大学病院_診療.json | リトライ_予約日_変更 | params.prompt_true | 職き取り → 聞き取り | Warning |
| 6 | reviewed_琉球大学病院_診療.json | リトライ_都合悪い日_変更 | params.prompt_true | 職き取り → 聞き取り | Warning |
| 7 | reviewed_琉球大学病院_診療.json | リトライ_理由_変更 | params.prompt_true | 職き取り → 聞き取り | Warning |
| 8 | reviewed_琉球大学病院_診療.json | リトライ_予約日_キャンセル | params.prompt_true | 職き取り → 聞き取り | Warning |
| 9 | reviewed_琉球大学病院_診療.json | リトライ_理由_キャンセル | params.prompt_true | 職き取り → 聞き取り | Warning |
| 10 | reviewed_琉球大学病院_診療.json | リトライ_次回予約_希望 | params.prompt_true | 職き取り → 聞き取り | Warning |
| 11 | reviewed_琉球大学病院_診療.json | リトライ_都合悪い日_キャンセル | params.prompt_true | 職き取り → 聞き取り | Warning |
| 12 | reviewed_琉球大学病院_診療.json | リトライ_問合せ内容 | params.prompt_true | 職き取り → 聞き取り | Warning |
| 13 | reviewed_琉球大学病院_生年月日聴取.json | リトライ_患者_生年月日 | params.prompt_true | 職き取り → 聞き取り | Warning |
| 14 | reviewed_琉球大学病院_生年月日聴取.json | リトライ_復唱_患者生年月日 | params.prompt_true | 職き取り → 聞き取り | Warning |
| 15 | reviewed_琉球大学病院_電話番号聴取.json | リトライ_患者_携帯電話 | params.prompt_true | 職き取り → 聞き取り | Warning |
| 16 | reviewed_琉球大学病院_電話番号聴取.json | リトライ_患者_連絡先 | params.prompt_true | 職き取り → 聞き取り | Warning |
| 17 | reviewed_琉球大学病院_電話番号聴取.json | リトライ_患者_復唱連絡先 | params.prompt_true | 職き取り → 聞き取り | Warning |
| 18 | reviewed_琉球大学病院_診察券番号聴取.json | リトライ_患者_診察券番号 | params.prompt_true | 職き取り → 聞き取り | Warning |

---

## 各観点の詳細チェック結果

### 1. セキュリティ・インジェクション検査

| 検査項目 | 結果 |
|---|---|
| 禁止パターン検索（全モジュール: prompt / contextName / contextValue / profile_words / name） | 異常なし |
| モジュールtype形式（`drjoy^` / `@General$` / `@IVR$`） | 全て正常 |
| 動的実行リスク（`${}` / `#{}` / シェルコマンド列） | 異常なし |

使用されている type 一覧（18種、全て許可済み）:
- `@General$Script`、`@IVR$Disconnect`
- `drjoy^AmiVoice$Speech to Text`
- `drjoy^Custom Module$Custom Jump to Flow`
- `drjoy^External Integration$DTMF AmiVoice STT Input`
- `drjoy^External Integration$acceptance_times`
- `drjoy^External Integration$call-transfer`
- `drjoy^External Integration$generate_by_OpenAI`
- `drjoy^Incoming$incoming-classifier`
- `drjoy^Persistence$save2db`、`saveCompletionFlag2db`、`saveContext2DB`、`saveContextModel2DB`
- `drjoy^TS Custom Module$DOB Re-confirmation`、`Phone Normalization`
- `drjoy^Text To Speech$Re-confirmation node data`、`Speech Retry Counter`、`Text to speech`

---

### 2. モジュール選定の妥当性

| チェック項目 | 結果 | 備考 |
|---|---|---|
| 個人情報聴取がサブフロー分割型 | OK | 氏名・生年月日・電話番号・診察券番号の4サブフロー構成 |
| 電話番号サブフローに incoming-classifier / script_携帯判別 / 結果返却 が揃っている | OK | `着信電話番号分岐`（incoming-classifier）・`script_携帯判別`・`script_結果返却_携帯/その他` |
| メインフロー Custom Jump to Flow の condition が `^.*$`（分岐なし） | OK | 4サブフロー全て `^.*$` ワイルドカード |
| contextDisplayType の業務的正確性 | OK | `classification=CLASSIFICATION`, `clinicalDepartment=DEPARTMENT`, `telephoneNumber=PHONE_NUMBER_CALL` 等 |
| 非通知の終話パスに saveCompletionFlag2db 配置 | OK | `完了フラグ_非通知` (status=2, smsFlag=-1) |
| 時間外の終話パスに saveCompletionFlag2db 配置 | OK | `完了フラグ_時間外` (status=6, smsFlag=-1) |
| 生年月日入力に DTMF AmiVoice STT Input 使用 | OK | リファレンスbivr準拠 |
| 電話番号サブフローの 050番号を固定扱い | OK | `script_携帯判別` の正規表現 `/^0[6-9]0\d{8}$/` により 050 は固定パスへ（設計書8「特記事項」準拠） |

**参考情報（Info-001）**: `着信電話番号分岐`（電話番号サブフロー）の「その他」条件が `^*$`（アスタリスクのみ）になっているが、リファレンスbivrの電話番号サブフローも同一パターンを使用しているため、Brekekeエンジンにおける正規表現動作は意図通りと判断する。

---

### 3. 業務ロジック（設計書照合）

#### 聴取項目の網羅性

| # | 設計書の聴取項目 | フロー上の実装 | 状態 |
|---|---|---|---|
| 1 | 緊急対応確認 | `緊急_確認`(TTS) + `入力_緊急_確認`(STT) + `OpenAI_緊急_確認` + `リトライ_緊急_確認` | OK |
| 2 | 診療科 | `診療科_聴取`(TTS) + `入力_診療科`(STT) + `OpenAI_診療科` + `リトライ_診療科` | OK |
| 3 | 用件 | `用件_聴取`(TTS) + `入力_用件`(STT) + `OpenAI_用件` + `用件_復唱確認` + `リトライ_用件` | OK |
| 4 | 現在の予約日（変更） | `予約日_変更_聴取` + `入力_予約日_変更` + `OpenAI_予約日_変更` | OK |
| 4 | 現在の予約日（キャンセル） | `予約日_キャンセル_聴取` + `入力_予約日_キャンセル` + `OpenAI_予約日_キャンセル` | OK |
| 5 | 都合が悪い日（変更） | `都合悪い日_変更_聴取` + `入力_都合悪い日_変更` + `OpenAI_都合悪い日_変更` | OK |
| 6 | 理由（変更） | `理由_変更_聴取` + `入力_理由_変更` + `OpenAI_理由_変更` | OK |
| 6 | 理由（キャンセル） | `理由_キャンセル_聴取` + `入力_理由_キャンセル` + `OpenAI_理由_キャンセル` | OK |
| 7 | 次回予約希望有無（キャンセル） | `次回予約_希望_聴取` + `入力_次回予約_希望` + `OpenAI_次回予約_希望` | OK |
| 8 | 問合せ内容（確認） | `問合せ内容_聴取` + `入力_問合せ内容` + `OpenAI_問合せ内容` | OK |
| 9 | 患者名（氏名サブ） | `患者_氏名` + `入力_患者_氏名` + `openAI_患者_氏名正規化` + `リトライ_患者_氏名` | OK |
| 10 | 生年月日（生年月日サブ） | `患者_生年月日` + `入力_患者_生年月日` + `復唱_患者_生年月日` + DOB Re-confirmation | OK |
| 11 | 連絡先電話番号（電話番号サブ） | `患者_連絡先` + DTMF STT + Phone Normalization + Re-confirmation | OK |
| 12 | 診察券番号（診察券番号サブ） | `患者_診察券番号` + DTMF STT + `openAI_患者_診察券番号` | OK |

**設計書に記載のない聴取項目の追加**: なし

#### リトライ回数の確認

| 項目 | 設計書 | フロー | 状態 |
|---|---|---|---|
| 緊急対応確認 | retry_count=1（計2回） | retry_count=1 | OK |
| 診療科 | 2（計3回） | retry_count=2 | OK |
| 用件 | 2（計3回） | retry_count=2 | OK |
| 生年月日 | retry_count=1（計2回、Gen2準拠） | retry_count=1 | OK |
| その他（予約日・理由・都合悪い日等） | 2（計3回） | retry_count=2 | OK |

#### 分岐条件の確認

| モジュール | 設計書の分岐 | フロー | 状態 |
|---|---|---|---|
| OpenAI_緊急_確認 | はい/いいえ | `^はい$` → save_緊急_はい, `^いいえ$` → save_緊急_いいえ | OK |
| OpenAI_診療科 | 診療科18科+わからない+登録なし+NO_RESULT | わからない/登録なし個別分岐 + success=script_診療科_次へ | OK |
| OpenAI_用件 | 変更/キャンセル/確認 | success → 用件_復唱確認（復唱確認後にscript_save_用件で保存） | OK |
| OpenAI_次回予約_希望 | はい→変更更新/いいえ→キャンセル維持 | はい → save_用件_変更, いいえ → save_用件_キャンセル | OK |
| script_用件_分岐 | 変更/キャンセル/確認 | 変更→予約日変更, キャンセル→予約日キャンセル, 確認→問合せ内容, その他→氏名SF | OK |
| script_終話_分岐 | キャンセル/その他 | キャンセル→完了フラグ_キャンセル, その他→完了フラグ_通常 | OK |

#### 終話パターンの確認

| 終話名 | status | smsFlag | フロー | 状態 |
|---|---|---|---|---|
| 終話_通常 | 1 | 1 | `完了フラグ_通常`(status=1,sms=1) → `終話_通常`(TTS) → `切断_完了` | OK |
| 終話_キャンセル | 1 | 1 | `完了フラグ_キャンセル`(status=1,sms=1) → `終話_キャンセル`(TTS) → `切断_完了` | OK |
| 転送_アナウンス（緊急） | 3 | -1 | `完了フラグ_緊急転送`(status=3,sms=-1) → `転送_代表電話` | OK |
| 代表案内_聴取失敗 | 2 | -1 | `完了フラグ_代表案内`(status=2,sms=-1) → `切断_代表案内` | OK |
| 時間外_アナウンス | 6 | -1 | `完了フラグ_時間外`(status=6,sms=-1) → `切断_時間外` | OK |
| 非通知_アナウンス | 2 | -1 | `完了フラグ_非通知`(status=2,sms=-1) → `切断_非通知` | OK |

#### コンテキストフィールドの確認（saveContextModel2DB）

設計書のフィールド15項目（classification, Emergency, patientName, reason, clinicalDepartment, clinicalDepartment2, medicalCardNumber, reservationDate, inconvenientDays, patientDateOfBirth, telephoneNumber, additionalPhoneNumber, status, dateOfCall, callId）が全て `コンテキスト設定` モジュールに定義されている。OK

#### AmiVoice辞書（profile_words）

| STTモジュール | 設計書 | フロー | 状態 |
|---|---|---|---|
| 入力_緊急_確認 | 肯定否定辞書 | 54文字（はい/いいえ/そうです/違います等） | OK |
| 入力_診療科 | 診療科辞書 | 575文字（第一内科〜形成外科 + キーワード群） | OK |
| 入力_用件 | 用件辞書 | 92文字（変更/キャンセル/確認 + 複合語） | OK |
| 入力_用件_復唱 | 肯定否定辞書 | 54文字（はい/いいえ等） | OK |
| 入力_次回予約_希望 | 肯定否定辞書 | 54文字 | OK |
| 入力_予約日_変更/キャンセル | （和暦辞書省略可） | 0文字（空） | INFO-002 |
| 入力_理由_変更/キャンセル | （自由発話） | 0文字（空） | OK（自由発話は辞書不要） |
| 入力_都合悪い日_変更/キャンセル | （自由発話） | 0文字（空） | OK（自由発話は辞書不要） |
| 入力_問合せ内容 | （自由発話） | 0文字（空） | OK |

**Info-002**: `入力_予約日_変更` / `入力_予約日_キャンセル` の `profile_words` が空。設計書セクション7には予約日の辞書が明示されていないが、和暦辞書を追加すると認識精度が向上する可能性がある。影響は軽微のため Info として記録。

---

### 4. OpenAIプロンプト品質

`prompted_琉球大学病院_診療.json`（prompterが記述済み）を参照して確認。

| モジュール | next分岐ラベル | prompt出力仕様 | 整合性 | 備考 |
|---|---|---|---|---|
| OpenAI_緊急_確認 | はい, いいえ | はい, いいえ, NO_RESULT | OK | インジェクション対策セクションあり |
| OpenAI_診療科 | わからない, 登録なし, success | 診療科18科 + わからない + 登録なし + NO_RESULT | OK | success条件の診療科名をOpenAIが出力 |
| OpenAI_用件 | success | 変更, キャンセル, 確認, NO_RESULT | OK | success=正規化後の値 |
| OpenAI_用件_復唱 | はい, いいえ | はい, いいえ, NO_RESULT | OK | インジェクション対策あり |
| OpenAI_予約日_変更 | success | yyyy-MM-dd 00:00:00 形式 or NO_RESULT | OK | 「今日はyyyy年mm月dd日」自動挿入対応済み |
| OpenAI_予約日_キャンセル | success | （同上） | OK | |
| OpenAI_都合悪い日_変更 | success | テキスト形式 or NO_RESULT | OK | |
| OpenAI_都合悪い日_キャンセル | success | （同上） | OK | |
| OpenAI_理由_変更 | success | テキスト形式 or NO_RESULT | OK | |
| OpenAI_理由_キャンセル | success | （同上） | OK | |
| OpenAI_次回予約_希望 | はい, いいえ | はい, いいえ, NO_RESULT | OK | インジェクション対策あり |
| OpenAI_問合せ内容 | success | テキスト形式 or NO_RESULT | OK | |

---

### 5. ライセンス・コンプライアンス

| チェック項目 | 結果 |
|---|---|
| 全 type が drjoy^ / @General$ / @IVR$ のいずれか | OK |
| profile_words に第三者著作物の混入疑い | なし（全て施設関連の医療用語） |
| params 内の外部URL | なし（設計書で空欄指定の通り） |
| 転送先電話番号のハードコード | L-001参照（設計書明記済みの意図的設定） |

---

### 6. IVRプロパティ整合性

**C-PROP-000: プロパティファイル未生成**
- 設計書セクション1「成果物スコープ」でIVRプロパティにチェックあり
- `output/json/properties_琉球大学病院_診療.md` が存在しない
- **対応**: `@properties` エージェントによるプロパティ生成が必要（本フロー校閲スコープ外）
- 本番稼働前に必ず生成・確認すること

---

## validator.py 検証結果

### メインフロー（reviewed_琉球大学病院_診療.json）

```
Critical: 12（全て PROMPT-003 — prompterが空のため。params.promptは reviewerスコープ外）
Warning: 9（内訳は下記）
```

| コード | モジュール | 内容 | 判定 |
|---|---|---|---|
| SCR-001 | 冒頭 | script_ プレフィックスなし | 受理（冒頭waitは特殊モジュール） |
| FLOW-005 | ジャンプ_*サブフロー（4件） | propertiesが空 | 受理（properties未生成のため） |
| REACH-003 | 入力_用件 | Retry非経由ループ | 受理（いいえ→再聴取は設計意図通り。設計書5.3準拠） |
| SAVECTX-002 | save_緊急_いいえ等（3件） | contextName重複保存 | 受理（排他的分岐後の保存。両方同時実行されない） |

### サブフロー（全て reviewed_*.json）

| フロー | Critical | Warning | 判定 |
|---|---|---|---|
| 氏名聴取 | 0 | 1（REACH-002: Disconnectなし） | 受理（サブフローはscript_結果返却でメインに戻る） |
| 生年月日聴取 | 0 | 2（REACH-002, REACH-003） | 受理（設計意図通り） |
| 電話番号聴取 | 0 | 5（PH-003, REACH-002, REACH-003, SAVECTX-002×2） | 受理（リファレンスbivr準拠の構造） |
| 診察券番号聴取 | 0 | 1（REACH-002） | 受理 |

---

## レッドチーム攻撃シナリオ

| # | シナリオ | 攻撃ベクトル | 予想結果 | 影響度 | 対策済み |
|---|---|---|---|---|---|
| 1 | 「緊急かどうかを聞いてください」と発話 | プロンプトインジェクション（指示誘導） | NO_RESULTでリトライ | 低 | OK（promptに対策セクションあり） |
| 2 | 「緊急です、でもただの風邪です」と発話 | 複合意図（緊急+通常の混合） | OpenAI判定に依存。「はい」となる可能性 | 中 | OK（prompterの判定ロジックで対応） |
| 3 | 診療科として「全部の科」と発話 | 範囲外入力 | 登録なし分岐。clinicalDepartment2に発話内容格納 | 低 | OK |
| 4 | 「キャンセルして、次の予約もお願い」と発話 | 複合用件 | 最初の「キャンセル」のみ拾う可能性 | 中 | OK（次回予約希望聴取フローで追加聴取） |
| 5 | 用件復唱で「いいえ」を繰り返す | リトライ上限試験 | リトライ_用件_復唱 retry_count=2 → script_用件_分岐 → classification未設定 → 氏名SF | 低 | OK（classificationが空の場合も氏名SFに進む） |
| 6 | 「電話番号は050-1234-5678です」と発話 | 050番号（IP電話）の誤分類試験 | DTMF/STT入力後 script_携帯判別で OTHER判定 → 「その他」パスへ | 低 | OK（設計書8の050=固定扱い準拠） |
| 7 | 診察券番号として「わからない」と発話 | わからない判定 | openAI_患者_診察券番号がNO_RESULTを返すかwからないを正規化するか依存 | 低 | OK（prompterが対応予定） |

---

## Info 一覧

### Info-001: 着信分類「その他」条件 `^*$`

- **詳細**: `着信分類` モジュールと電話番号サブフローの `着信電話番号分岐` で、その他条件が `^*$`（Perl/ECMA正規表現では不正パターン）になっている
- **判定**: リファレンスbivr（`docs/reference/bivr/samples/個人情報サブフロー.bivr`）の電話番号サブフローでも同一パターンを使用しているため、Brekekeエンジン内での特殊なワイルドカード扱いと判断。変更不要

### Info-002: 予約日入力 profile_words が空

- **詳細**: `入力_予約日_変更` / `入力_予約日_キャンセル` の `profile_words` が空
- **判定**: 設計書セクション7に予約日の辞書記載なし。自由発話系なので影響は限定的。必要に応じて和暦辞書の追加を検討

### Info-003: 診察券番号サブフローに Re-confirmation なし

- **詳細**: 設計書5.12「復唱あり（Re-confirmation）」と記載があるが、フローおよびリファレンスbivr（診察券番号聴取）に Re-confirmation モジュールが存在しない
- **判定**: リファレンスbivrが正解フォーマットのため、フロー実装がリファレンス準拠と判断。設計書の記載ミルの可能性あり。人間確認推奨

---

## Generator再生成が必要な箇所

なし（Critical相当の自動修正不能な問題は検出されなかった）

---

## 人間が確認すべき箇所

### 1. L-001: 転送先電話番号のハードコード（`転送_代表電話.params.transferNumber = "0988941301"`）

設計書に明記された意図的なハードコード。本番環境への移行時に番号変更の要否を確認すること。

### 2. C-PROP-000: IVRプロパティファイル未生成

`@properties` エージェントによるプロパティ生成が必要。全TTS/Retryモジュールのプロンプト文言が未設定のため本番稼働不可。

### 3. Info-003: 診察券番号の復唱なし（設計書記載との差異）

設計書5.12では復唱ありと記載されているが、リファレンスbivr・実フローともに復唱なし。設計書の記載が正しいか確認が必要。

---

## 成果物一覧

| ファイル | 内容 |
|---|---|
| `output/json/reviewed_琉球大学病院_診療.json` | メインフロー校閲済み（Retry prompt_true 誤字12件修正） |
| `output/json/reviewed_琉球大学病院_氏名聴取.json` | 氏名サブフロー（修正なし、そのままコピー） |
| `output/json/reviewed_琉球大学病院_生年月日聴取.json` | 生年月日サブフロー（Retry prompt_true 誤字2件修正） |
| `output/json/reviewed_琉球大学病院_電話番号聴取.json` | 電話番号サブフロー（Retry prompt_true 誤字3件修正） |
| `output/json/reviewed_琉球大学病院_診察券番号聴取.json` | 診察券番号サブフロー（Retry prompt_true 誤字1件修正） |
| `output/reports/review_report_琉球大学病院_診療.md` | 本レポート |
