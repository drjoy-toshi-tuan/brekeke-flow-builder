# Brekeke IVR フローJSON 生成リファレンス — 実フロー完全解析

> **目的**: generator エージェントが正確な IVR フロー JSON を出力するための構造仕様書
> **ソース**: `export__19_.bivr` (HCクリニック厚木$健診_20260311) を完全解析

---

## 1. フローJSON トップレベル構造

```json
{
  "layout": {},
  "resultValue": "",
  "postCallAction": "",
  "name": "施設名$フロー名_YYYYMMDD",
  "start": "冒頭",
  "modules": { /* モジュール名をキーとした辞書 */ },
  "desc": ""
}
```

- `name`: `{施設略称}${フロー区分}_{日付}` 形式（例: `HCクリニック厚木$健診_20260311`）
- `start`: 最初に実行されるモジュール名（通常 `"冒頭"`）
- `modules`: **辞書型**（配列ではない）。キー = モジュール名、値 = モジュール定義

---

## 2. モジュール共通構造

```json
{
  "layout": { "x": 0, "y": 0 },
  "next": [ /* 遷移条件の配列 */ ],
  "subs": [ /* DB保存先の配列（常に3要素） */ ],
  "name": "モジュール名",
  "description": "",
  "matchingmethod": 1,
  "type": "モジュールタイプ文字列",
  "params": { /* タイプ固有のパラメータ */ }
}
```

### 2.1 next 配列（遷移条件）

```json
{
  "condition": "^正規表現$",
  "label": "表示ラベル",
  "nextModuleName": "遷移先モジュール名"
}
```

- 空の condition/nextModuleName は未使用スロット（テンプレートとして残す）
- STTモジュールには最大11スロット（timeout, error, no_result, success + jump1-7）
- OpenAIモジュールには最大10スロット（timeout, error, no_result + 分岐 + jumpN）
- 条件の評価は**上から順**。最初にマッチした遷移先が使われる
- `^.*$` は「それ以外全て」（フォールバック）として最後に配置

### 2.2 subs 配列（DB保存先）

```json
[
  { "moduleName": "save-項目名", "label": "save-項目名" },
  { "moduleName": "", "label": "" },
  { "moduleName": "", "label": "" }
]
```

- 常に3要素。使わないスロットは空文字
- 第1要素がメインのDB保存先モジュール参照

### 2.3 matchingmethod

- `1`: 通常（正規表現マッチング）
- `0`: リトライカウンター専用（true/falseの分岐）

---

## 3. モジュールタイプ一覧と詳細

### 3.1 wait（ウェイト） — 冒頭待機

```
type: "Custom$wait"
params: { "wait": "" }
```

- フロー開始時の待機。`start` モジュールとして使用
- 次は `営業時間チェック` へ

### 3.2 acceptance_times（受付時間チェック）

```
type: "drjoy^External Integration$acceptance_times"
params: {}
```

遷移:
- `^true$` → acceptable → `コンテキスト設定`
- `^false$` → rejected → `時間外フラグ`
- `^TIMEOUT$`, `^ERROR$` → `時間外フラグ`

### 3.3 saveContextModel2DB（コンテキストモデル設定）

```
type: "drjoy^Persistence$saveContextModel2DB"
params: {
  "fields": "[JSON文字列: Dr.JOY画面の項目定義]"
}
```

- `fields` は JSON 配列の**文字列**（二重エスケープ注意）
- 各フィールド: `contextName`, `contextNameJp`, `rangeValues[]`（任意）

#### フィールド定義一覧（HCクリニック厚木）

| contextName | contextNameJp | rangeValues |
|---|---|---|
| classification | 区分 | 予約,インフルエンザ,変更,キャンセル,確認,問合せ,遅刻,その他 |
| patientName | 患者名 | — |
| medicalCardNumber | 診察券番号 | — |
| clinicalDepartment | 診療科 | — |
| patientDateOfBirth | 生年月日(和暦) | — |
| reason | 理由 | — |
| cancellation_change_date | 変更有無 | — |
| reservation_change_date | 変更希望日 | — |
| reservationDate | 予約日 | — |
| telephoneNumber | 電話番号 | — |
| additionalPhoneNumber | 連絡先電話番号 | — |
| status | 状態 | 途中切断,未処理,代表案内,転送,時間外,HP案内 |
| dateOfCall | 入電日時 | — |
| DesiredreservationDate | 予約希望日 | — |
| history | 受診歴 | — |
| course | コース | — |
| AddOption | 追加オプション | — |
| question | その他お問い合わせ | — |
| group_reservation | 氏名、生年月日（複数予約時） | — |
| change_contents | 変更内容確認 | — |
| arrival_time | 到着時間 | — |

### 3.4 Text to speech（TTSアナウンス）

```
type: "drjoy^Text To Speech$Text to speech"
params: {
  "stop_by_dtmf": "No",
  "category_words": "",
  "prompt": ""
}
```

- `prompt`: 空の場合はプロパティファイルで設定。直接指定時は `{tts_g:テキスト}` 形式
- `stop_by_dtmf`: DTMF入力で読み上げを中断するか
- `category_words`: 空（通常未使用）
- 次の遷移: `"condition": "^.*$"` で常に1つの入力モジュールへ

### 3.5 Speech to Text（STT音声入力）

```
type: "drjoy^AmiVoice$Speech to Text"
params: {
  "detection_flag": "デフォルト",
  "keep_filter_token": "No" or "Yes",
  "probability": "",
  "language": "デフォルト",
  "type": "テキスト",
  "silent_detection_ms": "",
  "uri": "",
  "profile_words": "辞書登録文字列",
  "profile_name": "",
  "engine": "デフォルト",
  "save_log": "No",
  "timeout_ms": ""
}
```

- `profile_words`: 改行区切りの辞書。形式: `単語 よみがな`（例: `雇用時健診 こようじけんしん`）
- `keep_filter_token`: 通常 `"No"`、一部 `"Yes"`
- 空文字のパラメータはプロパティファイルのデフォルト値を使用

#### STT 標準遷移パターン:
```json
[
  { "condition": "^TIMEOUT$", "label": "timeout", "nextModuleName": "リトライ-{項目名}" },
  { "condition": "^ERROR$",   "label": "error",   "nextModuleName": "リトライ-{項目名}" },
  { "condition": "^NO_RESULT$", "label": "no_result", "nextModuleName": "リトライ-{項目名}" },
  { "condition": "^.+$",      "label": "success",  "nextModuleName": "OpenAI-{項目名}" },
  { "condition": "", "label": "jump1", "nextModuleName": "" },
  /* ... jump2-7 も空で追加 */
]
```

### 3.6 DTMF AmiVoice STT Input（DTMF＋音声入力）

```
type: "drjoy^External Integration$DTMF AmiVoice STT Input"
```

- 生年月日など、ダイヤルプッシュと音声の両方を受け付ける場面で使用
- パラメータはSTTと同様

### 3.7 generate_by_OpenAI（AI正規化）

```
type: "drjoy^External Integration$generate_by_OpenAI"
params: {
  "contextName": "DB保存先のコンテキスト名",
  "contextDisplayType": "TEXT" | "CLASSIFICATION" | "DATE" | "DATE_OF_BIRTH" | "PHONE_NUMBER",
  "promptTTS": "",
  "module": "参照するSTTモジュール名",
  "functionCall": "JSON文字列（function calling使用時）",
  "prompt": "AIへの指示プロンプト"
}
```

#### contextDisplayType の使い分け:
| 値 | 用途 | 例 |
|---|---|---|
| TEXT | 自由テキスト | 氏名、希望コース、追加オプション、変更内容 |
| CLASSIFICATION | 固定選択肢 | 用件区分 |
| DATE | 日付 | 予約日、変更希望日 |
| DATE_OF_BIRTH | 生年月日 | 生年月日 |
| PHONE_NUMBER | 電話番号 | 連絡先電話番号 |

#### functionCall の構造（使用時）:
```json
{
  "name": "dialogue_completed",
  "description": "聴取した内容を保存します",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": {
      "フィールド名": {
        "type": "string",
        "description": "説明",
        "display_type": "TEXT",
        "enum": ["選択肢1", "選択肢2"]  // 任意
      }
    },
    "required": ["フィールド名"],
    "additionalProperties": false
  }
}
```

- `functionCall` が空文字の場合: プロンプトの出力がそのまま condition マッチングに使われる
- `functionCall` がある場合: function calling の戻り値でルーティングされる

#### OpenAI 標準遷移パターン:
```json
[
  { "condition": "^TIMEOUT$",   "label": "timeout",   "nextModuleName": "リトライ-{項目名}" },
  { "condition": "^ERROR$",     "label": "error",     "nextModuleName": "リトライ-{項目名}" },
  { "condition": "^NO_RESULT$", "label": "no_result", "nextModuleName": "リトライ-{項目名}" },
  // --- ここから分岐固有 ---
  { "condition": "^特定値$",    "label": "ラベル",    "nextModuleName": "遷移先" },
  { "condition": "^.*$",        "label": "デフォルト", "nextModuleName": "フォールバック先" },
  // --- 未使用スロット ---
  { "condition": "", "label": "jumpN", "nextModuleName": "" }
]
```

### 3.8 Speech Retry Counter（リトライカウンター）

```
type: "drjoy^Text To Speech$Speech Retry Counter"
params: {
  "retry_count": "1",
  "prompt_true": "{tts_g:リトライ時のアナウンス}",
  "prompt_false": "{tts_g:リトライ上限超過時のアナウンス}"
}
```

- `matchingmethod`: **0**（他のモジュールは1）
- 遷移: `"condition": "true"` → Retry先, `"condition": "false"` → No more先

#### リトライメッセージのパターン:

| パターン | prompt_true | prompt_false |
|---|---|---|
| 標準（大半のステップ） | `恐れ入りますがご回答が確認できませんでした。今一度、` | `かしこまりました。折り返しの際にお伺いいたします。` |
| 用件確認（致命的） | 同上 | `ご回答の確認ができませんでしたのでこちらからお電話失礼させていただきます。` |
| 氏名 | `うまく聞き取れませんでした。ゆっくり過ぎるとうまく聞き取れませんので、普通のスピードで、再度、フルネームをお話しください。` | 標準 |
| 電話番号 | `恐れ入りますがご回答が確認できませんでした。はい か いいえで再度お答えいただけますでしょうか。` | `ご回答の確認ができませんでしたので、現在通知いただいている電話番号へご連絡いたします。` |
| その他お問い合わせ | `恐れ入りますがご回答が確認できませんでした。今一度おっしゃっていただけますでしょうか。` | `かしこまりました。折り返しの際にお伺いいたします。` |
| 空（無言終話） | — | （空文字 → 無言で終話） |

### 3.9 save2db（DB保存）

```
type: "drjoy^Persistence$save2db"
params: {
  "contextName": "",
  "contextDisplayType": "TEXT"
}
```

- 他モジュールの `subs` から参照される（サブモジュール）
- `next` は空配列
- 独立した遷移は持たない

### 3.10 saveContext2DB（コンテキスト直接保存）

```
type: "drjoy^Persistence$saveContext2DB"
params: {
  "contextName": "保存先フィールド名",
  "contextValue": "セットする値",
  "contextDisplayType": "TEXT"
}
```

- 例: `contextName: "course"`, `contextValue: "<%雇用時健診%> "` → コース名を固定値で設定

### 3.11 saveCompletionFlag2db（完了フラグ保存）

```
type: "drjoy^Persistence$saveCompletionFlag2db"
params: {
  "status": "1",
  "smsFlag": "1"
}
```

| status | 意味 | smsFlag |
|---|---|---|
| 1 | 未処理 | 1 (SMS1: 受付確認SMS) |
| 2 | 代表案内 | 0 |
| 6 | 時間外 | 0 |
| 7 | HP案内 | 2 (SMS2: 雇用時健診フォームリンク) |

### 3.12 incoming-classifier（着信分類）

```
type: "drjoy^Incoming$incoming-classifier"
params: {}
```

遷移ラベル: `非通知`, `固定`, `海外`, `携帯`, `その他`

### 3.13 ContextMatchRouter（コンテキスト値による分岐）

```
type: "drjoy^Context Logic$ContextMatchRouter"
```

- 用件区分の値に応じて終話ガイダンスを切り替える
- params の `module{N}Value{M}` で値とモジュールの対応を定義

### 3.14 Jump to Flow（フロー間ジャンプ）

```
type: "@General$Jump to Flow"
```

- 別の .bivr フロー（例: Jump遅刻）を呼び出し、戻ってきた後の遷移先を指定
- `next[0]` の `nextModuleName` が戻り先

### 3.15 RAG（FAQ応答）

```
type: "drjoy^External Integration$RAG"
```

- その他お問い合わせでFAQ回答を試みる
- 成功 → ループ、失敗/no result → 終話

### 3.16 Script（スクリプト実行）

```
type: "@General$Script"
```

- カスタムロジック実行用

### 3.17 Disconnect（切断）

```
type: "@IVR$Disconnect"
params: {}
```

- 通話を切断する。TTS後に配置

---

## 4. 会話ステップの標準モジュールチェーン

1つの会話ステップは原則として **5モジュール** で構成される:

```
TTS（アナウンス） → STT（音声入力） → OpenAI（AI正規化） → Retry（リトライ） → save（DB保存）
```

### 例: 用件確認ステップ

```
用件(TTS) → 入力-用件(STT) → OpenAI-用件(OpenAI) → リトライ-用件(Retry) → save-用件(save2db)
```

### 命名規則

| モジュール種別 | 命名パターン | 例 |
|---|---|---|
| TTS | `{ステップ名}` | `用件`, `受診歴`, `希望コース` |
| STT | `入力-{ステップ名}` or `入力_{ステップ名}` | `入力-用件`, `入力_再受診の希望` |
| OpenAI | `OpenAI-{ステップ名}` or `OpenAI_{ステップ名}` | `OpenAI-用件`, `OpenAI_FAQ` |
| Retry | `リトライ-{ステップ名}` or `リトライ_{ステップ名}` | `リトライ-用件` |
| save | `save-{項目名}` or `save_{項目名}` | `save-用件` |

> 注: `-` と `_` の使い分けに厳密なルールはなく混在している。新規作成時はどちらでもよいが、1つのステップ内では統一する。

---

## 5. フロー全体の開始チェーン

```
冒頭(wait) → 営業時間チェック(acceptance_times)
  ├── true → コンテキスト設定(saveContextModel2DB) → 冒頭アナウンス(TTS) → 仕訳-電話番号(incoming-classifier)
  │     ├── 非通知 → 電話番号※非通知番号からの入電(TTS) → 非通知切断フラグ → 切断-非通知
  │     ├── 海外 → 海外からの入電(TTS) → 代表案内フラグ-海外 → 切断-国際電話
  │     └── 固定/携帯/その他 → 用件(TTS) → [用件確認フロー]
  └── false/timeout/error → 時間外フラグ → 時間外(TTS) → 切断-時間外
```

---

## 6. フロー全体の終了チェーン

```
[最後のステップ] → フラグ設定-status1,sms1(saveCompletionFlag) → 用件による終話ガイダンス分岐(ContextMatchRouter)
  ├── 問合せ → 終話-問合せ(TTS) → 切断-終話
  ├── 予約 → 終話-予約(TTS) → 切断-終話
  ├── 変更 → 終話-変更(TTS) → 切断-終話
  ├── キャンセル → 終話-キャンセル(TTS) → 切断-終話
  ├── 遅刻 → 終話-遅刻(TTS) → 切断-終話
  ├── 確認 → 終話-確認(TTS) → 切断-終話
  └── インフルエンザ → 終話-予約(TTS) → 切断-終話
```

---

## 7. サブフロー（Jump遅刻）

別 .bivr ファイルとして定義。メインフローの `Jump to Flow` モジュールから呼ばれる。

```
遅刻アナウンス(TTS) → 到着時間(TTS) → 入力_遅刻_到着時間(STT) → openAI_遅刻_到着時間(OpenAI) → リトライ_遅刻_到着時間(Retry) → save-遅刻(save2db)
```

戻り値で呼び出し元フローの遷移先（氏名 or フラグ設定）に復帰。

---

## 8. モジュール数の目安

HCクリニック厚木（147モジュール）の内訳:

| タイプ | 数 | 説明 |
|---|---|---|
| save2db | 33 | 各ステップ + α |
| Text to speech | 33 | アナウンス + 終話ガイダンス |
| Speech Retry Counter | 19 | リトライ対応ステップ数 |
| generate_by_OpenAI | 19 | AI正規化対応ステップ数 |
| Speech to Text | 17 | 音声入力ステップ数 |
| Disconnect | 6 | 終話パターン数 |
| saveCompletionFlag2db | 6 | フラグパターン数 |
| saveContext2DB | 3 | 固定値セット |
| incoming-classifier | 2 | 着信分類 (冒頭 + 電話番号) |
| Jump to Flow | 2 | 遅刻フロー呼び出し |
| その他 | 7 | wait, acceptance, contextModel, contextRouter, RAG, Script, DTMF |
| **合計** | **147** | |

---

## 9. layout（座標）について

- フローデザイナーでの表示位置。JSON生成時は適当な値でよい
- 既存フローを参考にする場合: x は -800〜3200、y は -400〜5200 程度の範囲
- 基本的に上から下、左から右に配置。メインフローは中央付近

---

## 10. OpenAI プロンプト設計パターン

### 10.1 分類型（用件確認など）

```
役割: 〇〇の正規化専門家
出力形式: ラベル1語のみ（解説禁止）
判定ステップ（優先順位付き）:
  1. キーワード強制マッチ
  2. 音韻補正・キーワードマッチ
  3. 文脈・意図判定
  4. NO_RESULT
例示（Few-shot）
制約事項
```

### 10.2 正規化型（希望コース、追加オプションなど）

```
質問文を明示
リスト内にある単語と一致させる（類義語マッピング付き）
出力ルール（語句のみ、説明禁止）
該当なし→原文出力 or NO_RESULT
```

### 10.3 はい/いいえ判定型（受診歴、前回と同じ、再受診希望など）

```
はい → 正ラベル
いいえ → 負ラベル
どちらでもない → NO_RESULT
```

### 10.4 日付変換型（予約日、変更希望日など）

```
テキストを yyyy/mm/dd 形式に変換
明日/明後日は着信日基準
年またぎの補正ルール
不可能なら NO_RESULT
```

### 10.5 自由テキスト型（氏名、問い合わせ内容など）

```
テキストを整形して出力
カタカナ変換（氏名の場合）
要約（問い合わせの場合: 15-35文字、体言止め）
特定キーワード検出（遅刻、雇用時健診）
```

---

## 11. .bivr パッケージング仕様

### ファイル構造
```
{name}.bivr (ZIP形式)
  └── flows/
      └── @flow_{URLエンコードされた名前}.txt
```

### URLエンコード規則
- **全文字をエンコード**（半角英数字も含む）
  - `H` → `%48`, `C` → `%43`, `$` → `%24`
- 日本語は UTF-8 バイト列のパーセントエンコード
- ファイル名先頭に `@` を付与

### JSONの格納形式
- **必ず1行**（改行・インデントなし）
- 拡張子は `.txt`（.json ではない）

### 複数フローの同梱
- 1つの .bivr に複数の .txt ファイルを格納可能
- 例: メインフロー + Jump遅刻フロー

---

## 12. generator が出力すべきもの

設計書を入力として、以下を生成する:

1. **メインフローJSON** — 上記構造に従った全モジュール定義
2. **サブフローJSON**（必要な場合） — Jump先のフロー
3. **プロパティファイル** — アナウンス文、環境設定（別途 properties エージェントが担当）

### 生成時のチェックリスト

- [ ] 全 TTS モジュールの `prompt` が設定書のアナウンス文と一致
- [ ] 全 STT モジュールの `profile_words` に必要な辞書が含まれる
- [ ] 全 OpenAI モジュールの `prompt` が正規化ルールを正確に反映
- [ ] 全 OpenAI モジュールの `condition` 分岐が設計書の遷移先と一致
- [ ] 全 Retry モジュールの `retry_count` が設計書と一致（通常 1）
- [ ] 全 Retry モジュールの No more 先が設計書のフォールバック先と一致
- [ ] コンテキスト設定の `fields` が Dr.JOY 画面項目と一致
- [ ] `saveCompletionFlag2db` の status/smsFlag が正しい
- [ ] `incoming-classifier` の分岐が非通知・海外・固定・携帯を網羅
- [ ] 終話の `ContextMatchRouter` が全用件タイプに対応
- [ ] サブフロー（Jump先）が必要な場合、別ファイルとして生成
- [ ] 全モジュール名がユニーク（重複なし）
- [ ] `start` が正しいモジュール名を指す
