# 設計書 — 中之島クリニック 健診（第3世代）v2

> 第2世代フロー `_健診1__中之島クリニック__1_.docx` からの移行
> generator / migrator への入力用設計書
> **サブフロー分割型**（CLAUDE.md Rule 9 準拠）
> **v2更新 (2026-03-31)**: 4/1施設変更対応（3施設→2施設、西宮除外）+ PDF打ち合わせ内容反映 + エラー修正

---

## 1. 基本情報

| 項目 | 内容 |
|---|---|
| 施設名 | 中之島クリニック |
| グループ名 | 中之島CL |
| 対応施設 | 中之島クリニック / 中之島クリニックレディースプラザ（2施設。4/1以降、西宮ガーデンズ除外） |
| 施設ID (office_id) | TODO_要確認 |
| 営業時間 | 月〜土 9:00〜15:00（祝日除く）（PDF掲示物 p.30 準拠） |
| フロー構成 | **サブフロー分割型**（3フロー構成） |

### フロー一覧

| # | フロー名（Brekeke） | 種別 | 概要 |
|---|---|---|---|
| 1 | 中之島CL$健診 | メインフロー | 冒頭チェーン〜施設選択〜用件選択〜サブフロー呼出 |
| 2 | 中之島CL$氏名聴取 | サブフロー | 氏名聴取 → 結果返却 |
| 3 | 中之島CL$電話番号聴取 | サブフロー | 着信番号分岐 → 電話番号聴取/復唱確認 → 終話チェーン → 結果返却 |

---

## 2. フロー構成（サブフロー分割型）

CLAUDE.md Rule 9 に従い、個人情報聴取（氏名・電話番号）を項目ごとに個別サブフローとして構築する。

| サブフロー | 対象 | 遷移方式 | 備考 |
|---|---|---|---|
| 中之島CL$氏名聴取 | 氏名聴取 | drjoy^Custom Module$Custom Jump to Flow | 汎用パターン |
| 中之島CL$電話番号聴取 | 電話番号聴取 | drjoy^Custom Module$Custom Jump to Flow | incoming-classifier + script_携帯判別 + Phone Normalization + Re-confirmation |

> 生年月日・診察券番号はこのフローでは聴取しないため、サブフロー不要。

---

## 3. フローの目的

2施設共通の健診予約受付AI電話。施設選択（DTMF 2択）の後、人間ドック・健診の受付またはその他問い合わせの振り分けを行う。氏名と連絡先電話番号を聴取し、担当者への折り返し依頼を受け付ける。

---

## 4. シナリオフロー図

### フロー1: 中之島CL$健診（メインフロー）

```
wait(2000ms)
  → saveContextModel2DB
  → acceptance_times
      ├─ 時間外 → 時間外_アナウンス(TTS) → 完了フラグ_時間外 → END_時間外 → 切断
      └─ 受付可 → incoming-classifier
                    ├─ 非通知 → 非通知_アナウンス(TTS) → 完了フラグ_非通知 → END_非通知 → 切断
                    └─ 通常 → 冒頭_アナウンス(TTS)
                                → 施設_選択(TTS)
                                → 入力_施設_選択(DTMF AmiVoice STT)
                                → OpenAI_施設_選択(generate_by_OpenAI)
                                    ├─ 中之島クリニック → saveContext_施設
                                    ├─ 中之島クリニックレディースプラザ → saveContext_施設
                                    └─ NO_RESULT → リトライ_施設_選択
                                → saveContext_施設(saveContext2DB)
                                → 用件_選択(TTS)
                                → 入力_用件_選択(DTMF AmiVoice STT)
                                → OpenAI_用件_選択(generate_by_OpenAI)
                                    ├─ 人間ドック → saveContext_用件 → Custom Jump → 中之島CL$氏名聴取
                                    ├─ その他 → saveContext_用件 → 問合せ_内容(TTS)
                                    │            → 入力_問合せ_内容(AmiVoice STT)
                                    │            → OpenAI_問合せ_内容
                                    │            → saveContext_問合せ → Custom Jump → 中之島CL$氏名聴取
                                    └─ NO_RESULT → リトライ_用件_選択
                                → [氏名聴取サブフローから戻り]
                                → Custom Jump → 中之島CL$電話番号聴取
                                → [電話番号聴取サブフローから戻り — 終話はサブフロー内で実行]
```

> **注意**: 終話チェーン（saveCompletionFlag2db + END TTS + Disconnect）は電話番号聴取サブフロー内に配置する。smsFlag の6パターン分岐もサブフロー内で実行する。

### フロー2: 中之島CL$氏名聴取（サブフロー）

```
氏名_聴取(TTS)
  → 入力_氏名(AmiVoice STT)
  → OpenAI_氏名(generate_by_OpenAI)
      ├─ success → saveContext_氏名(saveContext2DB) → script_結果返却_氏名
      └─ TIMEOUT/ERROR/NO_RESULT → リトライ_氏名
                                      ├─ Retry → 氏名_聴取(TTS)
                                      └─ No more → script_結果返却_氏名(スキップ)
```

> リトライ上限到達時は氏名未取得のまま次へスキップ（電話番号聴取へ進む）。
> `script_結果返却_氏名`: `$runner.getModuleResult()` で氏名を取得し `$runner.setResult()` でメインフローに返却。

### フロー3: 中之島CL$電話番号聴取（サブフロー）

```
incoming-classifier(着信番号分岐)
  ├─ 携帯(090/080/070) → 携帯_確認(TTS: 着信番号を復唱)
  │     → 入力_携帯_確認(DTMF AmiVoice STT)
  │     → OpenAI_携帯_確認(肯定/否定判定)
  │         ├─ 肯定 → script_携帯判別 → 携帯電話判別(saveContext: phonetype=携帯)
  │         │     → script_携帯かその他(集約) → script_携帯ルート(結果返却)
  │         │     → [終話チェーンへ]
  │         └─ 否定 → [その他パスへ合流]
  │
  └─ その他(固定/IP等) → 電話番号_聴取(TTS)
        → 入力_電話番号(DTMF AmiVoice STT)
        → Phone Normalization(generate_by_OpenAI)
            ├─ success → saveContext_電話番号(saveContext2DB)
            │     → Re-confirmation(TTS: 番号復唱)
            │     → 入力_電話番号_確認(DTMF AmiVoice STT)
            │     → OpenAI_電話番号_確認(肯定/否定判定)
            │         ├─ 肯定 → script_携帯判別 → 携帯以外(saveContext: phonetype=その他)
            │         │     → script_携帯かその他(集約) → script_その他ルート(結果返却)
            │         │     → [終話チェーンへ]
            │         └─ 否定 → 電話番号_訂正(TTS) → 入力_電話番号(ループ)
            └─ NO_RESULT → リトライ_電話番号
                              ├─ Retry → 電話番号_聴取(TTS)
                              └─ No more → END_上限到達エラー(TTS) → 完了フラグ_上限エラー → 切断

[終話チェーン]
  → smsFlag分岐(script で clinicalDepartment × full-body_checkup を判定)
      ├─ 人間ドック × 中之島CL → 完了フラグ_人間ドック_中之島(status=1, smsFlag=1) → END_人間ドック(TTS) → 切断
      ├─ 人間ドック × レディース → 完了フラグ_人間ドック_レディース(status=1, smsFlag=2) → END_人間ドック(TTS) → 切断
      ├─ その他 × 中之島CL → 完了フラグ_その他_中之島(status=1, smsFlag=4) → END_その他(TTS) → 切断
      └─ その他 × レディース → 完了フラグ_その他_レディース(status=1, smsFlag=5) → END_その他(TTS) → 切断
```

> **smsFlag分岐の実装方針**: clinicalDepartment（2値）× full-body_checkup（2値）= 4パターン。
> `@General$Script` で clinicalDepartment と full-body_checkup を参照し、smsFlag値を決定する方式を推奨。
> 4つの saveCompletionFlag2db モジュールをそれぞれ配置する。
> END_人間ドック / END_その他 の TTS文言は共通（施設による文言差なし）のため、TTS自体は2モジュールで済む。
> **注意（西宮除外）**: smsFlag=3（人間ドック×西宮）と smsFlag=6（その他×西宮）は4/1以降不要。定義を削除する。

---

## 5. コンテキストフィールド一覧（saveContextModel2DB 用）

| contextName | contextNameJp | contextDisplayType | rangeValues | itemDefault | editable | deletable | 備考 |
|---|---|---|---|---|---|---|---|
| classification | 区分 | CLASSIFICATION | [{"id":"1","order":"1","value":"予約"},{"id":"2","order":"2","value":"変更"},{"id":"3","order":"3","value":"キャンセル"},{"id":"4","order":"4","value":"問合せ"}] | true | true | true | 用件区分。本フローでは常に「問合せ」をセット |
| clinicalDepartment | 施設 | DEPARTMENT | [{"id":"1","order":"1","value":"中之島クリニック"},{"id":"2","order":"2","value":"中之島クリニックレディースプラザ"},{"id":"3","order":"3","value":"登録なし"}] | true | true | true | 施設選択結果（2施設。西宮除外） |
| full-body_checkup | 用件詳細 | TEXT | — | false | true | true | 「人間ドック」または「その他」 |
| patientName | 氏名 | TEXT | — | true | true | true | |
| additionalPhoneNumber | 連絡先電話番号 | PHONE_NUMBER | — | true | true | true | 聴取する電話番号 |
| reason | 問合せ内容 | TEXT | — | false | true | true | その他ルートのみ |
| question | お問合せ | TEXT | — | false | true | true | Gen2 functionに存在。Dr.JOY画面表示用として含める |
| endpoint | 通話結果 | TEXT | [{"id":"1","order":"1","value":"途中切断"},{"id":"2","order":"2","value":"時間外"},{"id":"3","order":"3","value":"電話転送"},{"id":"4","order":"4","value":"電話再度"},{"id":"5","order":"5","value":"ビル切断"},{"id":"6","order":"6","value":"通話完了"}] | false | true | true | Gen2 functionに存在。終話時にセットする通話結果 |
| status | 状態 | STATUS | [{"id":"1","order":"1","value":"未処理"},{"id":"2","order":"2","value":"代表案内"}] | true | true | true | 1=未処理 2=代表案内 |
| smsFlag | SMS区分 | TEXT | [{"id":"0","order":"0","value":"0"},{"id":"1","order":"1","value":"1"},{"id":"2","order":"2","value":"2"},{"id":"4","order":"3","value":"4"},{"id":"5","order":"4","value":"5"}] | false | true | true | 施設×用件で1,2,4,5を制御（3,6は西宮除外により不要） |

### Gen2に存在するが本設計書から除外するフィールド

以下のフィールドはGen2 functionに定義されているが、本フローで明示的に聴取するステップがなく、saveContextModel2DB に含めない。

| contextName | 除外理由 |
|---|---|
| course | フロー内でコース名を聴取するステップがない |
| option | フロー内でオプションを聴取するステップがない |
| reservationDate | フロー内で予約日を聴取するステップがない |
| Preferred_date | フロー内で希望日を聴取するステップがない |
| company_name | フロー内で会社名を聴取するステップがない |
| detail | フロー内で詳細を聴取するステップがない（reason で代替） |
| callback | フロー内でコールバック希望を聴取するステップがない |
| patientDateOfBirth | フロー内で生年月日を聴取するステップがない |
| group_reservation | フロー内で団体予約を聴取するステップがない |

> これらのフィールドが Dr.JOY 画面での表示に必要な場合は、Dr.JOY 側の設定で対応する。フローJSON の saveContextModel2DB には聴取するフィールドのみ含める方針とする。

---

## 6. 聴取項目一覧

| # | 聴取項目 | 所属フロー | STTタイプ | DTMF最大桁数 | リトライ回数 | 復唱 | 保存先(contextName) | 備考 |
|---|---|---|---|---|---|---|---|---|
| 1 | 施設選択 | 中之島CL$健診 | DTMF AmiVoice STT Input | 1 | 2 | なし | clinicalDepartment | DTMF 1/2（2施設） |
| 2 | 用件選択 | 中之島CL$健診 | DTMF AmiVoice STT Input | 1 | 2 | なし | full-body_checkup | DTMF 1/2 |
| 3 | 問合せ内容 | 中之島CL$健診 | AmiVoice Speech to Text | — | 2 | なし | reason | その他ルートのみ |
| 4 | 氏名 | 中之島CL$氏名聴取 | AmiVoice Speech to Text | — | 2 | なし | patientName | サブフロー |
| 5 | 電話番号 | 中之島CL$電話番号聴取 | DTMF AmiVoice STT Input | 11 | 3 | あり（Phone Normalization + Re-confirmation） | additionalPhoneNumber | サブフロー。リトライ3回（Gen2仕様維持） |
| 6 | 電話番号確認 | 中之島CL$電話番号聴取 | DTMF AmiVoice STT Input | 1 | 2 | — | — | 肯定/否定の復唱確認 |
| 7 | 携帯確認 | 中之島CL$電話番号聴取 | DTMF AmiVoice STT Input | 1 | 2 | — | — | 着信番号が携帯の場合の復唱確認 |

---

## 7. ステップ詳細

### 7.0 冒頭チェーン（メインフロー共通）

**wait**: 2000ms（着信直後の安定待機）

**saveContextModel2DB**: セクション5のフィールド定義をJSON文字列で設定

**acceptance_times**: 受付時間判定
- 受付可 → incoming-classifier へ
- 時間外 → 時間外_アナウンスへ

**incoming-classifier**: 着信電話番号分岐
- 非通知 → 非通知_アナウンスへ
- 通常 → 冒頭_アナウンスへ

### 7.1 施設選択（メインフロー）

**TTSアナウンス（冒頭_アナウンス + 施設_選択）**:
> お電話ありがとうございます。お問い合わせの施設をお選びください。中之島クリニックの方は1を、中之島クリニックレディースプラザの方は2を押してください。

**入力方式**: DTMF（1/2）+ 音声

**DTMF設定**: max_dtmf_length = 1, prompt に `{recstart}` を含めること

**OpenAI正規化ルール**:
- 出力: `中之島クリニック` / `中之島クリニックレディースプラザ` / `NO_RESULT`
- DTMF `1` or 「中之島クリニック」を含む → `中之島クリニック`
- DTMF `2` or 「レディースプラザ」を含む → `中之島クリニックレディースプラザ`
- それ以外 → `NO_RESULT`

**保存先**: clinicalDepartment（saveContext2DB）
**次**: 用件選択
**リトライ失敗時（No more）**: 終話（切断）

### 7.2 用件選択（メインフロー）

**TTSアナウンス（用件_選択）**:
> この電話は1分程度で終わります。内容を正確に把握するために3点の質問にご協力ください。まず、ご用件をお選びください。人間ドックや健診のご予約は1を、それ以外のお問い合わせは2を押してください。

**入力方式**: DTMF（1/2）+ 音声

**DTMF設定**: max_dtmf_length = 1, prompt に `{recstart}` を含めること

**OpenAI正規化ルール**:
- 出力: `人間ドック` / `その他` / `NO_RESULT`
- DTMF `1` or 「ドック」「健診」「検診」「人間ドック」を含む → `人間ドック`
- DTMF `2` or 「それ以外」「その他」を含む → `その他`
- それ以外 → `NO_RESULT`

**保存先**: full-body_checkup（saveContext2DB）
**固定値セット**: classification = `問合せ`（全ケース共通）

**分岐**:
- `人間ドック` → saveContext_用件 → Custom Jump to Flow → 中之島CL$氏名聴取
- `その他` → saveContext_用件 → 問合せ内容聴取へ

**リトライ失敗時（No more）**: 問合せ内容聴取へ（デフォルトで「その他」ルート）

### 7.3 問合せ内容（メインフロー・その他ルートのみ）

**TTSアナウンス（問合せ_内容）**:
> 改めて内容を確認のうえ、のちほど折り返しご連絡いたしますが、本日はどのようなご用件でしょうか。

**入力方式**: 音声のみ（AmiVoice STT）

**OpenAI正規化**: フリーテキスト保存（正規化不要）

**保存先**: reason（saveContext2DB）
**次**: Custom Jump to Flow → 中之島CL$氏名聴取
**リトライ失敗時（No more）**: 次へスキップ（氏名聴取サブフローへ）

### 7.4 氏名聴取（中之島CL$氏名聴取 サブフロー）

**TTSアナウンス（氏名_聴取）**:
> 予約内容を正確に把握するため、お名前をお話しください。

**入力方式**: 音声のみ（AmiVoice STT）

**OpenAI正規化**: 文字起こし結果をそのまま保存（フリーテキスト）

**保存先**: patientName（saveContext2DB）
**次**: script_結果返却_氏名 → メインフローに返却 → Custom Jump to Flow → 中之島CL$電話番号聴取
**リトライ失敗時（No more）**: 次へスキップ（script_結果返却_氏名 → 電話番号聴取へ）

### 7.5 電話番号聴取（中之島CL$電話番号聴取 サブフロー）

#### 7.5a 着信番号分岐（incoming-classifier）

サブフロー冒頭で着信番号を分類する。

- **携帯パス（090/080/070）**: 着信番号をそのまま復唱確認
- **その他パス（固定/IP等）**: 連絡先電話番号を新規聴取

#### 7.5b 携帯パス — 着信番号復唱確認

**TTSアナウンス（携帯_確認）**:
> ご連絡先の電話番号は{telephoneNumber}でよろしいでしょうか。1、はい。2、いいえ。

**入力方式**: DTMF（1/2）+ 音声

**OpenAI正規化ルール**:
- `肯定` / `否定` / `NO_RESULT`
- DTMF `1` or 「はい」→ `肯定`
- DTMF `2` or 「いいえ」→ `否定`

**分岐**:
- `肯定` → script_携帯判別（着信番号を additionalPhoneNumber にセット）→ 携帯電話判別 → 集約 → 終話チェーンへ
- `否定` → その他パスへ合流（電話番号_聴取へ）

#### 7.5c その他パス — 電話番号聴取

**TTSアナウンス（電話番号_聴取）**:
> 折り返しご連絡のため、電話番号をお話ください。

**入力方式**: DTMF + 音声

**DTMF設定**: max_dtmf_length = 11

**OpenAI正規化ルール（Phone Normalization）**:
- 電話番号フォーマット（10〜11桁、先頭0）に正規化
- 正規化成功 → 電話番号確認（Re-confirmation）へ
- 正規化失敗 → リトライ

**保存先**: additionalPhoneNumber（saveContext2DB）
**リトライ回数**: 3回（第2世代の仕様を維持）

#### 7.5d 電話番号確認（Re-confirmation）

**TTSアナウンス（電話番号_確認）**:
> 連絡先の電話番号は{additionalPhoneNumber}でよろしいでしょうか。1、はい。2、いいえでお答えください。

**入力方式**: DTMF（1/2）+ 音声

**OpenAI正規化ルール**:
- `肯定` / `否定` / `NO_RESULT`
- DTMF `1` or 「はい」→ `肯定`
- DTMF `2` or 「いいえ」→ `否定`
- 10〜11桁の数値が入力された場合 → 新しい番号として additionalPhoneNumber を更新し、再度確認

**分岐**:
- `肯定` → script_携帯判別 → 携帯以外（phonetype=その他）→ 集約 → 終話チェーンへ
- `否定` → 電話番号訂正へ

#### 7.5e 電話番号訂正

**TTSアナウンス（電話番号_訂正）**:
> 正しい電話番号を再度お話しください。

**入力方式**: DTMF + 音声
**保存先**: additionalPhoneNumber
**次**: 電話番号確認（Re-confirmation ループ）

#### 7.5f 携帯判別・集約スクリプト

| モジュール名 | type | 役割 |
|---|---|---|
| script_携帯判別 | @General$Script | 聴取番号の正規表現判定（090/080/070 → 携帯、それ以外 → その他） |
| 携帯電話判別 | drjoy^Persistence$saveContext2DB | phonetype = 「携帯」を保存 |
| 携帯以外 | drjoy^Persistence$saveContext2DB | phonetype = 「その他」を保存 |
| script_携帯かその他 | @General$Script | 携帯パス/その他パスを集約するスクリプト |
| script_携帯ルート | @General$Script | 携帯パスの結果返却（$runner.setResult()） |
| script_その他ルート | @General$Script | その他パスの結果返却（$runner.setResult()） |

---

## 8. 終話パターン

### 正常終話（4パターン — 2施設×2用件）

| # | 終話名 | 条件 | TTSアナウンス | status | smsFlag | saveCompletionFlag2dbモジュール名 |
|---|---|---|---|---|---|---|
| 1 | END_人間ドック（中之島CL） | full-body_checkup=人間ドック & clinicalDepartment=中之島クリニック | 人間ドックのご連絡を承りました。担当者からの連絡にて確定となります。なお、この後届くショートメッセージのURLから項目の入力をお願いいたします。お電話ありがとうございました。 | 1 | 1 | 完了フラグ_人間ドック_中之島 |
| 2 | END_人間ドック（レディース） | full-body_checkup=人間ドック & clinicalDepartment=中之島クリニックレディースプラザ | （同上） | 1 | 2 | 完了フラグ_人間ドック_レディース |
| 4 | END_その他（中之島CL） | full-body_checkup=その他 & clinicalDepartment=中之島クリニック | ご用件をお預かりいたしました。担当者から折り返し電話、もしくはショートメッセージにてご連絡いたします。お電話ありがとうございました。 | 1 | 4 | 完了フラグ_その他_中之島 |
| 5 | END_その他（レディース） | full-body_checkup=その他 & clinicalDepartment=中之島クリニックレディースプラザ | （同上） | 1 | 5 | 完了フラグ_その他_レディース |

### 異常終話

| # | 終話名 | 条件 | TTSアナウンス | status | smsFlag | saveCompletionFlag2dbモジュール名 |
|---|---|---|---|---|---|---|
| 7 | END_上限到達エラー | 電話番号リトライ上限超過 | 申し訳ございません。折り返し先のお電話番号を聞き取ることができませんでした。恐れ入りますが、コールセンターへおかけ直しください。お電話ありがとうございました。 | 2 | 0 | 完了フラグ_上限エラー |
| 8 | 時間外 | acceptance_times 判定 | 申し訳ございませんが、ただいまの時間は受付時間外となっております。受付時間は、祝日を除く月曜から土曜の9時から15時です。恐れ入りますが、受付時間内におかけ直しください。お電話ありがとうございました。 | 6 | 0 | 完了フラグ_時間外 |
| 9 | 非通知 | incoming-classifier 判定 | TODO_要確認（第2世代に記載なし） | 2 | 0 | 完了フラグ_非通知 |

### smsFlag ルール

| clinicalDepartment | 人間ドック (smsFlag) | その他 (smsFlag) |
|---|---|---|
| 中之島クリニック | 1 | 4 |
| 中之島クリニックレディースプラザ | 2 | 5 |
| （上限エラー/時間外/非通知） | 0 | 0 |

---

## 9. サブフロー遷移仕様

### メインフロー → 氏名聴取

| 項目 | 値 |
|---|---|
| 遷移元フロー | 中之島CL$健診 |
| 遷移先フロー | 中之島CL$氏名聴取 |
| 遷移モジュール type | drjoy^Custom Module$Custom Jump to Flow |
| 遷移元モジュール名 | ジャンプ_氏名聴取 |
| 返却値の condition | `^.*$`（ワイルドカード — 分岐不要） |
| 返却後の遷移先 | ジャンプ_電話番号聴取 |
| 結果返却スクリプト（サブフロー出口） | script_結果返却_氏名 |

### メインフロー → 電話番号聴取

| 項目 | 値 |
|---|---|
| 遷移元フロー | 中之島CL$健診 |
| 遷移先フロー | 中之島CL$電話番号聴取 |
| 遷移モジュール type | drjoy^Custom Module$Custom Jump to Flow |
| 遷移元モジュール名 | ジャンプ_電話番号聴取 |
| 返却値の condition | `^.*$`（ワイルドカード — 終話はサブフロー内で完結） |
| 返却後の遷移先 | なし（サブフロー内で終話・切断まで完結する） |
| 結果返却スクリプト（サブフロー出口） | script_携帯ルート / script_その他ルート |

> **注意**: 電話番号聴取サブフローは終話チェーンを含むため、メインフローに戻る必要はない。ただし Rule 11 に従い、結果返却スクリプトは必ず配置する（終話直前に結果を返却してから saveCompletionFlag2db → TTS → Disconnect の順で進む）。

---

## 10. AmiVoice辞書（profile_words）

### 施設選択（入力_施設_選択）
```
中之島クリニック なかのしまくりにっく
中之島 なかのしま
レディースプラザ れでぃーすぷらざ
レディース れでぃーす
```

### 用件選択（入力_用件_選択）
```
人間ドック にんげんどっく
健診 けんしん
検診 けんしん
ドック どっく
その他 そのた
それ以外 それいがい
```

### 問合せ内容（入力_問合せ_内容）
```
（フリーテキスト — profile_words 空）
```

### 氏名（入力_氏名）
```
（フリーテキスト — profile_words 空）
```

### 電話番号（入力_電話番号）
```
（DTMFメイン — profile_words 空）
```

### 電話番号確認（入力_電話番号_確認 / 入力_携帯_確認）
```
はい はい
いいえ いいえ
```

---

## 11. 特記事項・制約

- **2施設共通の1フロー構成**: 施設選択が冒頭にある特殊構成。施設によって終話時の smsFlag が変わる（4/1以降、西宮ガーデンズ除外）
- **smsFlag が 4パターン**: clinicalDepartment（2値）× full-body_checkup（2値）= 4パターン（smsFlag=1,2,4,5）
- **電話番号リトライ3回**: 第2世代の仕様を維持（第3世代標準の2回より1回多い）
- **電話番号確認中の番号再入力対応**: 第2世代の「確認中に10-11桁の新しい番号をそのまま入力できる」仕様を維持する
- **classification は常に「問合せ」**: 人間ドックでも「問合せ」がセットされる（Gen2仕様準拠）
- **終話チェーンはサブフロー内**: 電話番号聴取サブフローが終話まで完結する設計（smsFlag分岐を含む）
- **受付時間**: 月〜土 9:00〜15:00（祝日除く）（PDF p.30準拠）
- **冒頭チェーンの順序**: wait → saveContextModel2DB → acceptance_times → incoming-classifier の順。時間外チェックを先に行い、非通知チェックはその後

## 11.1 Generator向け重要指示（v2エラー修正）

以下はv1生成時に発見されたエラーの修正指示。再生成時に必ず遵守すること。

| # | 修正項目 | 内容 |
|---|---|---|
| E-1 | incoming-classifier ラベル順序 | 「携帯」「海外」のラベルが入れ替わっていた。Brekeke標準のラベル順序を厳守すること |
| E-2 | DTMF {recstart} 必須 | 全 DTMF AmiVoice STT Input モジュールの prompt に `{recstart}` を含めること（CLAUDE.md DTMF-001） |
| E-3 | サブフロー接続不備 | 氏名聴取・電話番号聴取サブフローがメインフローから Custom Jump to Flow で確実に呼び出されていること。v1ではサブフローが作成されたが未接続だった |
| E-4 | リトライ_施設のデフォルトアナウンス | リトライモジュールの prompt_true に適切なデフォルトアナウンス文を設定すること（空欄にしない） |

---

## 12. 要確認事項

- [x] ~~営業時間~~ — 月〜土 9:00〜15:00（祝日除く）（PDF p.30準拠で確定）
- [x] ~~時間外アナウンスの文言~~ — 設計書セクション8に設定済み
- [ ] **非通知アナウンスの文言** — 第2世代に記載なし。TODO_要確認
- [ ] **office_id** — saveContextModel2DB に設定する施設ID
- [ ] **smsFlag 1,2,4,5 の割り当てが正しいか** — 2施設対応版。本番環境と照合が必要
- [ ] **電話番号リトライ3回の維持** — 第3世代標準は2回。3回を維持するか確認
- [ ] **classification が全ケース「問合せ」で正しいか** — 人間ドックの場合も「問合せ」でよいか確認
- [ ] **除外したGen2フィールドがDr.JOY画面で不要か** — 不要であれば除外のまま

> 確認レポートの詳細は `output/reports/確認レポート_中之島CL_健診_20260326.md` を参照。
