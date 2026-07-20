# Brekeke モジュールリファレンス

> **スコープ注意**: AIが生成・チェックするのは「モジュール間の接続構造（next/subs配列）」のみ。
> `params` の具体的な値（発話内容・API URL等）はIVRプロパティで管理し、人間が設定する。
> 本ファイルに記載のデフォルト値はモジュール生成時に設定する初期値であり、実際の動作値はIVRプロパティで上書きされる。

---

## カテゴリ一覧

| カテゴリ | 主なモジュール |
|---|---|
| Text To Speech | Text to speech, Speech Retry Counter, Re-confirmation node data |
| External Integration | DTMF AmiVoice STT Input, generate_by_OpenAI, RAG, acceptance_times |
| AmiVoice | Speech to Text |
| Persistence | save2db, saveContext2DB, saveCompletionFlag2db, saveContextModel2DB, saveNodeData2Session |
| Incoming | incoming-classifier |
| Context Logic | ContextMatchRouter, conditional-comparison |
| @General | Script, Jump to Flow |
| @IVR | Disconnect, Reject, Call Transfer |

---

## Text To Speech$Text to speech

**type**: `drjoy^Text To Speech$Text to speech`

**params デフォルト値**:
```json
{
  "prompt": "",
  "stop_by_dtmf": "No",
  "category_words": ""
}
```

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `prompt` | `""` | 発話内容。`{tts_g: テキスト}` 形式。IVRプロパティで上書き可 |
| `stop_by_dtmf` | `"No"` | DTMF入力で発話停止しない。停止する場合は `"Yes"`。`"false"/"true"` は使用禁止 |
| `category_words` | `""` | 語調カテゴリ。IVRプロパティで一括管理 |

**next配列**:
```json
[{"condition": "^.*$", "label": "Next Module", "nextModuleName": "次のモジュール"}]
```
- label は必ず `"Next Module"`
- 終話モジュール（Disconnect前の最終TTS）は `"next": []`

**subs**: 全TTSモジュールに `save2db` サブモジュールを必ず接続
```json
[
  {"moduleName": "save-xxx", "label": "save-xxx"},
  {"moduleName": "", "label": ""},
  {"moduleName": "", "label": ""}
]
```

---

## Text To Speech$Speech Retry Counter

**type**: `drjoy^Text To Speech$Speech Retry Counter`

**params デフォルト値**:
```json
{
  "retry_count": "2",
  "prompt_true": "{tts_g:申し訳ございません。うまく聞き取りが出来ませんでした。再度、}",
  "prompt_false": ""
}
```

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `retry_count` | `"2"` | リトライ回数。設計書指定がある場合はそちらに従う |
| `prompt_true` | `"{tts_g:申し訳ございません。うまく聞き取りが出来ませんでした。再度、}"` | **固定値・変更禁止**。末尾の「再度、」が後続TTS先頭に自然に繋がる設計。**IVRプロパティでは動作しない（JSON内に直接記述すること）** |
| `prompt_false` | `""` | No more 時の発話。**原則空文字**（No more 先が通常モジュールの場合は無音で遷移）。終話モジュールに繋ぐ場合のみ明示設定。**IVRプロパティでは動作しない（JSON内に直接記述すること）** |

**matchingmethod**: `0`（完全一致）

**next配列**:
```json
[
  {"condition": "true",  "label": "Retry",   "nextModuleName": "先頭TTSモジュール"},
  {"condition": "false", "label": "No more", "nextModuleName": "正解ルートの次のモジュール"}
]
```
- **condition は `true`/`false`、label は `Retry`/`No more`**（大文字小文字・順序に注意）
- **Retry 先は必ず先頭 TTS モジュール**（TTS→STT 連鎖の起点。STT モジュールを直接指定してはいけない）
- **No more 先は正解ルートの次のモジュール**（複数分岐があり遷移先が一意でない場合は終話モジュールに繋ぐ）

**subs**: save2db サブモジュールを接続可（TTS/STTと同じ save-xxx を使う）

---

## External Integration$DTMF AmiVoice STT Input

**type**: `drjoy^External Integration$DTMF AmiVoice STT Input`

> DTMF と AmiVoice STT を組み合わせた主力入力モジュール。

**params デフォルト値**:
```json
{
  "prompt": "{recstart}",
  "timeout": "30000",
  "timeout_ms": "",
  "profile_words": "",
  "profile_name": "",
  "detection_flag": "デフォルト",
  "keep_filter_token": "Yes",
  "engine": "デフォルト",
  "type": "テキスト",
  "language": "デフォルト",
  "save_log": "No",
  "probability": "",
  "silent_detection_ms": "",
  "uri": "",
  "stop_play_when_speech": "Yes",
  "max_dtmf_length": "10",
  "termdtmf": "#",
  "remove_term": "Yes",
  "retry": "2",
  "condition": "",
  "prompt_retry": ""
}
```

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `prompt` | `"{recstart}"` | **必須**。`{recstart}` を必ず含めること。DTMF/音声検出を開始する録音マーカー。**JSON内に直接記載し、IVRプロパティには記載しない**（プロパティ上書きで `{recstart}` が消失するのを防止） |
| `timeout` | `"30000"` | DTMF入力タイムアウト（ms）。IVRプロパティで一括管理可 |
| `timeout_ms` | `""` | AmiVoice STT タイムアウト（ms）。IVRプロパティで一括管理可 |
| `profile_words` | `""` | 認識補助単語リスト。入力種別に応じた辞書を設定（→ `docs/amivoice_dictionary.md`） |
| `profile_name` | `""` | AmiVoice プロファイル名 |
| `detection_flag` | `"デフォルト"` | 音声検出フラグ |
| `keep_filter_token` | `"Yes"` | フィルタートークン保持 |
| `engine` | `"デフォルト"` | STTエンジン |
| `type` | `"テキスト"` | 認識タイプ（テキスト/数値/日時/電話番号等） |
| `language` | `"デフォルト"` | 言語 |
| `save_log` | `"No"` | STTログ保存フラグ |
| `probability` | `""` | 認識確度閾値 |
| `silent_detection_ms` | `""` | 無音検出時間（ms） |
| `uri` | `""` | カスタムURI |
| `stop_play_when_speech` | `"Yes"` | 発話検出時にプロンプト再生を停止する |
| `max_dtmf_length` | `"10"` | **デフォルト10**。入力種別に応じて上書きする（例: 用件選択=`"1"`、診療科コード=`"4"`、FAX番号=`"10"`、電話番号=`"11"`） |
| `termdtmf` | `"#"` | DTMF終端文字（`#` = こめじるし）。変更不要 |
| `remove_term` | `"Yes"` | 終端文字を入力値から除去する |
| `retry` | `"2"` | **デフォルト2**。DTMF入力リトライ回数（Speech Retry Counter とは別の DTMF 専用リトライ） |
| `condition` | `""` | 追加条件（通常空文字） |
| `prompt_retry` | `""` | DTMFリトライ時のプロンプト（通常空文字。Speech Retry Counter で制御する） |

**profile_words 設定ルール**: 入力種別に応じて辞書を選択する（詳細は `docs/amivoice_dictionary.md`）。

| 入力種別 | 使用辞書 |
|---|---|
| 氏名 | 氏名辞書 |
| 生年月日・日付 | 和暦辞書 + month辞書 + day辞書 |
| 時間 | hour辞書 |
| 曜日 | 曜日辞書 |
| 診療科・外来 | 診療科辞書 |
| 健診・検診 | 健診辞書 |
| 薬・薬剤 | 処方薬剤辞書 |
| 復唱確認 | 肯定否定辞書 |
| 用件区分 | 施設固有（設計書参照） |
| 病棟・フロア・階 | 施設固有（設計書参照） |

フォーマット: `"表記 よみがな\n表記 よみがな\n..."` （半角スペース区切り、改行区切り）

**next配列（最大11スロット: timeout/error/no_result/success + jump1〜jump7）**:
```json
[
  {"condition": "^TIMEOUT$",   "label": "timeout",   "nextModuleName": "リトライ_xxx"},
  {"condition": "^ERROR$",     "label": "error",     "nextModuleName": "リトライ_xxx"},
  {"condition": "^NO_RESULT$", "label": "no_result", "nextModuleName": "リトライ_xxx"},
  {"condition": "^.+$",        "label": "success",   "nextModuleName": "OpenAI_xxx"},
  {"condition": "",            "label": "jump1",     "nextModuleName": ""},
  {"condition": "",            "label": "jump2",     "nextModuleName": ""},
  {"condition": "",            "label": "jump3",     "nextModuleName": ""},
  {"condition": "",            "label": "jump4",     "nextModuleName": ""},
  {"condition": "",            "label": "jump5",     "nextModuleName": ""},
  {"condition": "",            "label": "jump6",     "nextModuleName": ""},
  {"condition": "",            "label": "jump7",     "nextModuleName": ""}
]
```
- **success は `^.+$` 1本受けのみ**。`^予約$` 等の個別パターンをSTT nextに入れてはいけない
- 個別分岐は後続の `generate_by_OpenAI` モジュールで行う

**subs**: 全STTモジュールに `save2db` サブモジュールを必ず接続

---

## AmiVoice$Speech to Text

**type**: `drjoy^AmiVoice$Speech to Text`

> DTMFなしのSTT専用モジュール。

**params デフォルト値**:
```json
{
  "detection_flag": "デフォルト",
  "keep_filter_token": "Yes",
  "engine": "デフォルト",
  "probability": "",
  "save_log": "No",
  "language": "デフォルト",
  "timeout_ms": "",
  "type": "テキスト",
  "silent_detection_ms": "",
  "uri": "",
  "profile_words": ""
}
```

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `type` | `"テキスト"` | 認識タイプ |
| `language` | `"デフォルト"` | 言語 |
| `engine` | `"デフォルト"` | STTエンジン |
| `profile_words` | `""` | 認識補助単語リスト。DTMF AmiVoice STT Input と同じルールで設定（→ `docs/amivoice_dictionary.md`） |
| `detection_flag` | `"デフォルト"` | 音声検出フラグ |
| `keep_filter_token` | `"Yes"` | フィルタートークン保持 |
| `timeout_ms` | `""` | タイムアウト（ms） |
| `silent_detection_ms` | `""` | 無音検出時間 |
| `probability` | `""` | 認識確度閾値 |
| `save_log` | `"No"` | ログ保存フラグ |
| `uri` | `""` | カスタムURI |

**next配列**: DTMF AmiVoice STT Input と同様（最大11スロット、success=`^.+$` 1本受け）

**subs**: save2db サブモジュールを必ず接続

---

## External Integration$generate_by_OpenAI

**type**: `drjoy^External Integration$generate_by_OpenAI`

> STT結果を受けてOpenAIで分類・分岐判定を行うモジュール。URL・プロンプトはIVRプロパティで一括管理。

**params デフォルト値**:
```json
{
  "contextName": "",
  "contextDisplayType": "TEXT",
  "promptTTS": "",
  "module": "",
  "functionCall": "",
  "prompt": ""
}
```

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `contextName` | `""` | 保存するコンテキスト名 |
| `contextDisplayType` | `"TEXT"` | コンテキスト表示形式（TEXT / CLASSIFICATION / DEPARTMENT 等） |
| `promptTTS` | `""` | OpenAI応答をTTS化する際のテンプレート |
| `module` | `""` | STT結果の参照元モジュール名。IVRプロパティで上書き可 |
| `functionCall` | `""` | Function Calling 定義（JSON）。必要に応じて設定（任意）。`contextDisplayType` が TEXT の場合は通常空文字のまま |
| `prompt` | `""` | OpenAIプロンプト。IVRプロパティで上書き可 |

**next配列**:
```json
[
  {"condition": "^TIMEOUT$",   "label": "timeout",   "nextModuleName": "リトライ_xxx"},
  {"condition": "^ERROR$",     "label": "error",     "nextModuleName": "リトライ_xxx"},
  {"condition": "^NO_RESULT$", "label": "no_result", "nextModuleName": "リトライ_xxx"},
  {"condition": "^予約$",      "label": "予約",      "nextModuleName": "次モジュール_予約"},
  {"condition": "^変更$",      "label": "変更",      "nextModuleName": "次モジュール_変更"}
]
```
- **TIMEOUT/ERROR/NO_RESULT は必ず先頭3スロット [0],[1],[2]**（STT と同じ順序。これ以外の配置は禁止）
- 分岐条件（`^予約$` 等）は [3] 以降に配置する（STT next には入れない）
- jump1〜7 の追加分岐も可能

---

## External Integration$RAG

**type**: `drjoy^External Integration$RAG`

> **AmiVoice内蔵のRAGサブモジュールは使わない**。External IntegrationカテゴリのRAGを使用する。
> URL等はIVRプロパティで一括管理。

**params デフォルト値**:
```json
{
  "prompt": "",
  "module": ""
}
```

| jump label | 意味 |
|---|---|
| `timeout` | タイムアウト |
| `error` | エラー |
| `no result` | 結果なし |
| `success` | 成功 |

---

## Persistence$save2db

**type**: `drjoy^Persistence$save2db`

> `modules` に定義が必須。`subs` 経由でのみ接続する。`next` 連鎖（通常フロー）への配置は禁止。
> 定義がないと Brekeke フローデザイナーが表示できない。

**params デフォルト値**:
```json
{
  "contextName": "",
  "contextDisplayType": "TEXT"
}
```

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `contextName` | `""` | 保存するコンテキスト名 |
| `contextDisplayType` | `"TEXT"` | コンテキスト表示形式 |

**contextDisplayType の選択肢**:
`TEXT` / `DEPARTMENT` / `CLASSIFICATION` / `NUMBER` / `DATE_OF_BIRTH` / `DATE` / `PHONE_NUMBER` / `PHONE_NUMBER_CALL`

**モジュール定義テンプレート**:
```json
"save-xxx": {
  "layout": {"x": 数値, "y": 数値},
  "next": [],
  "subs": [
    {"moduleName": "", "label": ""},
    {"moduleName": "", "label": ""},
    {"moduleName": "", "label": ""}
  ],
  "name": "save-xxx",
  "description": "",
  "matchingmethod": 1,
  "type": "drjoy^Persistence$save2db",
  "params": {"contextName": "", "contextDisplayType": "TEXT"}
}
```

**命名規則**: ラベル名は必ず `save-` プレフィックスで始める（例: `save-用件_確認`, `save-氏名`）
**共用ルール**: TTS とその直後の STT・Retry Counter は同じ save-xxx を使う

---

## Persistence$saveContext2DB

**type**: `drjoy^Persistence$saveContext2DB`

> **通常モジュールとして配置**（subs接続不可）

**params デフォルト値**:
```json
{
  "contextName": "",
  "contextDisplayType": "TEXT",
  "contextValue": ""
}
```

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `contextName` | `""` | コンテキスト名 |
| `contextDisplayType` | `"TEXT"` | コンテキスト表示形式 |
| `contextValue` | `""` | コンテキスト値。変数は `<%変数名%>` 形式で参照可 |

**利用可能な変数**: `sys-customer-phone-number`（着信電話番号）

**next配列**:
```json
[{"condition": "^.*$", "label": "next", "nextModuleName": "次のモジュール"}]
```

---

## Persistence$saveCompletionFlag2db

**type**: `drjoy^Persistence$saveCompletionFlag2db`

> **通常モジュールとして配置**（subs接続不可）。通話完了フラグとSMSフラグをDBに保存する。

**params デフォルト値**:
```json
{
  "status": "1",
  "smsFlag": "0"
}
```

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `status` | `"1"` | 通話ステータス（数値文字列）。**`"0"` と `"5"` は使用禁止**（Gen2予約済み）。許可値: `"1"`, `"2"`, `"3"`, `"6"`, `"7"` 以降 |
| `smsFlag` | `"0"` | SMS送信フラグ（`"0"`: 送信なし / `"1"`: 送信する） |

**配置ルール**: 終話ガイダンス（TTS）の**直前**に配置すること。正しい順序: `saveCompletionFlag2db → TTS（終話ガイダンス）→ Disconnect`

**next配列**:
```json
[{"condition": "^.*$", "label": "next", "nextModuleName": "次のモジュール"}]
```

---

## Persistence$saveContextModel2DB

**type**: `drjoy^Persistence$saveContextModel2DB`

> **通常モジュールとして配置**（subs接続不可）。startノード直後に配置推奨。
> Dr.JOY画面のコンテキスト項目定義をDBに保存する。

**params**:
```json
{
  "fields": "[...]"
}
```

| パラメータ | 型 | 説明 |
|---|---|---|
| `fields` | 文字列（JSON文字列） | フィールド定義の配列を **JSONエンコードした文字列**。オブジェクトではなく文字列として渡すこと |

### fields の構造（JSON文字列をデコードした配列）

各要素のスキーマ:

| キー | 型 | 必須 | 説明 |
|---|---|---|---|
| `contextName` | string | ✓ | コンテキスト識別子（camelCase英数字） |
| `contextNameJp` | string | ✓ | Dr.JOY画面の表示ラベル（日本語） |
| `displayType` | string | ✓ | 表示タイプ（下記一覧参照） |
| `rangeValues` | array | ✓ | 選択肢リスト。選択肢なしの場合は `[]` |
| `editable` | boolean | ✓ | Dr.JOY画面で編集可能か |
| `deletable` | boolean | ✓ | Dr.JOY画面で削除可能か |
| `itemDefault` | boolean | ✓ | デフォルト表示項目か |

### displayType 一覧

| 値 | 用途 |
|---|---|
| `CLASSIFICATION` | 用件区分（rangeValues必須） |
| `TEXT` | テキスト入力 |
| `NUMBER` | 数値 |
| `DEPARTMENT` | 診療科（rangeValues必須） |
| `DATE_OF_BIRTH` | 生年月日 |
| `DATE` | 日付・日時 |
| `PHONE_NUMBER_CALL` | 発信元電話番号（自動セット、editable:false） |
| `PHONE_NUMBER` | 電話番号入力 |
| `STATUS` | 状態（rangeValues必須） |

### rangeValues の構造（CLASSIFICATION / DEPARTMENT / STATUS で使用）

```json
{ "order": 1, "value": "表示テキスト" }
```

| キー | 型 | 必須 | 説明 |
|---|---|---|---|
| `order` | number | ✓ | 表示順 |
| `value` | string | ✓ | 表示テキスト |
| `id` | string | △ | 一意ID。**スマート面会シナリオ専用**。通常フローでは不要 |

### 記述例

```json
{
  "fields": "[\n  {\n    \"contextName\": \"classification\",\n    \"contextNameJp\": \"区分\",\n    \"rangeValues\": [\n      { \"id\": \"1\", \"order\": 1, \"value\": \"FAX到着確認\" },\n      { \"id\": \"2\", \"order\": 2, \"value\": \"情報提供依頼\" }\n    ],\n    \"displayType\": \"CLASSIFICATION\",\n    \"editable\": true,\n    \"deletable\": false,\n    \"itemDefault\": true\n  },\n  {\n    \"contextName\": \"patientName\",\n    \"contextNameJp\": \"患者名\",\n    \"rangeValues\": [],\n    \"displayType\": \"TEXT\",\n    \"editable\": true,\n    \"deletable\": false,\n    \"itemDefault\": true\n  },\n  {\n    \"contextName\": \"telephoneNumber\",\n    \"contextNameJp\": \"着信電話番号\",\n    \"rangeValues\": [],\n    \"displayType\": \"PHONE_NUMBER_CALL\",\n    \"editable\": false,\n    \"deletable\": false,\n    \"itemDefault\": true\n  },\n  {\n    \"contextName\": \"status\",\n    \"contextNameJp\": \"状態\",\n    \"rangeValues\": [\n      { \"id\": \"0\", \"order\": 0, \"value\": \"途中切断\" },\n      { \"id\": \"1\", \"order\": 1, \"value\": \"未処理\" },\n      { \"id\": \"3\", \"order\": 3, \"value\": \"転送\" }\n    ],\n    \"displayType\": \"STATUS\",\n    \"editable\": true,\n    \"deletable\": false,\n    \"itemDefault\": true\n  },\n  {\n    \"contextName\": \"dateOfCall\",\n    \"contextNameJp\": \"入電日時\",\n    \"rangeValues\": [],\n    \"displayType\": \"DATE\",\n    \"editable\": false,\n    \"deletable\": false,\n    \"itemDefault\": true\n  }\n]"
}
```

**重要**: `fields` の値は必ずJSON文字列（`"[...]"` 形式）にすること。オブジェクト（`[...]` そのまま）として渡すとBrekekeが正しく読み込めない。

**next配列**:
```json
[{"condition": "^.*$", "label": "next", "nextModuleName": "次のモジュール"}]
```

---

## Persistence$saveNodeData2Session

**type**: `drjoy^Persistence$saveNodeData2Session`

> セッションにノードデータを保存する。スマート面会等で使用。

**params デフォルト値**:
```json
{
  "key": "",
  "nodeName": ""
}
```

**next配列**:
```json
[{"condition": "^.*$", "label": "next", "nextModuleName": "次のモジュール"}]
```

---

## External Integration$acceptance_times

**type**: `drjoy^External Integration$acceptance_times`

> 受付時間判定。URL はIVRプロパティで管理。

**params デフォルト値**（2026-04 更新: TTS プラットフォーム選択追加）:
```json
{
  "ttsPlatform": "GOOGLE",
  "aiTalkApiKey": "",
  "tuningAssetsId": ""
}
```

| param | 値 | 用途 |
|---|---|---|
| `ttsPlatform` | `GOOGLE` (デフォルト) / `AI_TALK` | 時間外TTS の生成エンジン選択。設計書で AI_TALK が明示された場合のみ上書き |
| `aiTalkApiKey` | 顧客ごとの API キー | **AI_TALK 選択時は必須**（空だと動作しない）。顧客環境で人手設定、Claude は空のまま出力 |
| `tuningAssetsId` | ユーザー辞書 ID | AI_TALK のオプション（読み方チューニング用） |

> **⚠️ 人間対応項目**: `ttsPlatform=AI_TALK` のシナリオでは、`aiTalkApiKey` を顧客環境ごとに手動で設定する必要がある。scaffold_generator は AI_TALK 選択時に空キーなら stderr に TODO 警告を出す。

**next配列**（不変、4 分岐）:
```json
[
  {"condition": "^TIMEOUT$", "label": "timeout",    "nextModuleName": "終話_エラー"},
  {"condition": "^ERROR$",   "label": "error",      "nextModuleName": "終話_エラー"},
  {"condition": "^false$",   "label": "rejected",   "nextModuleName": "終話_時間外"},
  {"condition": "^true$",    "label": "acceptable", "nextModuleName": "次のモジュール"}
]
```

---

## Incoming$incoming-classifier

**type**: `drjoy^Incoming$incoming-classifier`

> 着信電話番号の種別で分岐する。office_id はIVRプロパティで管理。

**params デフォルト値**:
```json
{}
```

**next配列**（2026-04 更新: WebRTC 分岐追加）:
```json
[
  {"condition": "^非通知$", "label": "非通知", "nextModuleName": "終話_非通知"},
  {"condition": "^固定$",   "label": "固定",   "nextModuleName": "次のモジュール"},
  {"condition": "^海外$",   "label": "海外",   "nextModuleName": "終話_海外"},
  {"condition": "^携帯$",   "label": "携帯",   "nextModuleName": "次のモジュール"},
  {"condition": "^WebRTC$", "label": "WebRTC", "nextModuleName": "次のモジュール"},
  {"condition": "^*$",      "label": "その他", "nextModuleName": "次のモジュール"}
]
```

> WebRTC 分岐は現状「固定・携帯」と同じく通常フローに合流。将来 Pattern 5（WebRTC 専用シナリオ、個人情報サブフロー省略）で別扱い予定。catch-all「その他」は Brekeke 仕様で `^*$`（ドットなし）。

---

## @IVR$Disconnect / @IVR$Reject

**type**: `@IVR$Disconnect` または `@IVR$Reject`

> 通話を切断するモジュール。

**params デフォルト値**:
```json
{}
```

**next配列**: `[]`（空）
**subs配列**: `[]`（空）

---

## @General$Jump to Flow

**type**: `@General$Jump to Flow`

> 別フローへ遷移する。

**params デフォルト値**:
```json
{
  "flowname": "",
  "properties": ""
}
```

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `flowname` | `""` | 遷移先フロー名（`グループ名$フロー名` 形式） |
| `properties` | `""` | フロー間パラメータ引き渡し |

---

## Context Logic$ContextMatchRouter

**type**: `drjoy^Context Logic$ContextMatchRouter`

> モジュールの出力値で分岐する。**ルート判定にはスクリプトモジュールよりも ContextMatchRouter を優先して使用すること。**

**params デフォルト値**:
```json
{
  "contextName1": "",
  "contextName2": ""
}
```

| パラメータ | デフォルト | 説明 |
|---|---|---|
| `contextName1` | `""` | 参照するモジュール名（1つ目） |
| `contextName2` | `""` | 参照するモジュール名（2つ目）。**1つのモジュール出力だけで分岐する場合は contextName1 と同じモジュール名を指定する** |

**next配列**: 出力値の固定パターンで分岐（condition に `^値$` 形式で指定）

```json
"next": [
  {"condition": "^予約$",        "label": "予約",      "nextModuleName": "予約ルート"},
  {"condition": "^変更$",        "label": "変更",      "nextModuleName": "変更ルート"},
  {"condition": "^キャンセル$",   "label": "キャンセル", "nextModuleName": "キャンセルルート"},
  {"condition": "^.*$",          "label": "その他",     "nextModuleName": "デフォルトルート"}
]
```

**使い分けの基準**:
- **ContextMatchRouter を使う**: モジュール出力値が固定パターン（予約/変更/キャンセル等）での分岐。個人情報聴取後のルート判定、電話番号種別（携帯/固定）での分岐など
- **Script を使う**: 複数のモジュール結果の組み合わせ判定、日付計算、フリー発話の空文字判定など ContextMatchRouter では対応できない場合のみ

---

## Context Logic$conditional-comparison

**type**: `drjoy^Context Logic$conditional-comparison`

| next condition | label | 意味 |
|---|---|---|
| `true` | `true` | 条件一致 |
| `false` | `false` | 条件不一致 |

---

## モジュール生成チェックリスト

全モジュール共通で以下のフィールドを必ず含めること:

```json
{
  "layout": {"x": 数値, "y": 数値},
  "next": [...],
  "subs": [...],
  "name": "モジュール名（keyと一致）",
  "description": "",
  "matchingmethod": 1,
  "type": "drjoy^カテゴリ$モジュール名",
  "params": {...デフォルト値をセット...}
}
```

- `matchingmethod`: 通常 `1`（正規表現）。Retry Counter のみ `0`（完全一致）
- `name` フィールドは必ずモジュールキーと同じ値にする
- `description` は空文字でよい
- `subs` は使わない場合も `[]` ではなく 3スロット分の空要素を入れる（ただし Disconnect 等は `[]`）
