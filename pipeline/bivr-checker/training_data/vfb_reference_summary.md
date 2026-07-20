# VoiceBot Flow Builder リファレンスサマリー

> bivr-checker プロジェクト用に VoiceBot Flow Builder の全ドキュメントから抽出した統合リファレンス。
> ソース: voicebot-flow-builder/docs/, schemas/, .claude/agents/

---

## 1. フローJSON トップレベル構造

```json
{
  "layout": {},
  "resultValue": "",
  "postCallAction": "",
  "name": "施設名$フロー名_YYYYMMDD",
  "start": "冒頭",
  "modules": { "モジュール名": { ... } },
  "desc": ""
}
```

- `name`: `{施設略称}${フロー区分}_{日付8桁}` 形式
- `start`: 最初に実行されるモジュール名（通常 `"冒頭"`）
- `modules`: **辞書型**（配列ではない）。キー = モジュール名、値 = モジュール定義
- `desc`: 空文字 `""`

---

## 2. モジュール共通構造

```json
{
  "layout": { "x": 0, "y": 0 },
  "next": [],
  "subs": [
    { "moduleName": "save-xxx", "label": "save-xxx" },
    { "moduleName": "", "label": "" },
    { "moduleName": "", "label": "" }
  ],
  "name": "モジュール名",
  "description": "",
  "matchingmethod": 1,
  "type": "drjoy^カテゴリ$モジュール種別",
  "params": {}
}
```

- `subs`: 常に3要素。使わないスロットは空文字。第1要素がメインのDB保存先
- `matchingmethod`: `1` = 通常（正規表現マッチング）, `0` = リトライカウンター専用

---

## 3. モジュールタイプ一覧と params/next/subs ルール

### 3.1 wait（冒頭待機）

| 項目 | 値 |
|---|---|
| type | `Custom$wait` |
| params | `{ "wait": "" }` （IVRプロパティで `冒頭.wait=2000` と設定） |
| next | 1スロット: `^.*$` → コンテキスト設定 |
| subs | 不要 |
| 配置 | start モジュールとして必須 |

### 3.2 saveContextModel2DB（コンテキストモデル設定）

| 項目 | 値 |
|---|---|
| type | `drjoy^Persistence$saveContextModel2DB` |
| params.fields | JSON配列の**文字列**（二重エスケープ注意）。各要素: contextName, contextNameJp, displayType, rangeValues[], editable, deletable, itemDefault |
| next | 1スロット → 次のモジュール |
| subs | サブモジュール接続**不可** |
| 配置 | wait の直後に必ず配置 |

**displayType の許可値**: TEXT, NUMBER, DATE, DATE_OF_BIRTH, PHONE_NUMBER, CLASSIFICATION, DEPARTMENT
- TEXT/NUMBER/DATE は複数フィールドで重複可
- それ以外は1つのみ使用可
- clinicalDepartment は必ず DEPARTMENT

### 3.3 acceptance_times（受付時間チェック）

| 項目 | 値 |
|---|---|
| type | `drjoy^External Integration$acceptance_times` |
| params | `{}` |
| next | `^true$` → 冒頭アナウンス, `^false$`/`^TIMEOUT$`/`^ERROR$` → 時間外フラグ |
| 配置 | 任意。営業時間制御が不要なフローでは省略可 |

### 3.4 Text to speech（TTS）

| 項目 | 値 |
|---|---|
| type | `drjoy^Text To Speech$Text to speech` |
| params | `{ "stop_by_dtmf": "No", "category_words": "", "prompt": "" }` |
| next | `{ "condition": "^.*$", "label": "Next Module", "nextModuleName": "..." }` |
| subs | save2db サブモジュール接続**必須** |

- `stop_by_dtmf`: `"Yes"` / `"No"` のみ許可（`"true"` / `"false"` は**禁止**）
- `prompt`: 空の場合はIVRプロパティで設定。直接指定時は `{tts_g:テキスト}` 形式
- next label は必ず `"Next Module"`

### 3.5 Speech to Text（STT — AmiVoice）

| 項目 | 値 |
|---|---|
| type | `drjoy^AmiVoice$Speech to Text` |
| params | detection_flag, keep_filter_token, probability, language, type, silent_detection_ms, uri, profile_words, profile_name, engine, save_log, timeout_ms（全て空文字がデフォルト） |
| next | 最大11スロット |
| subs | save2db サブモジュール接続**必須** |

**STT next 標準パターン**:
```
[0] ^TIMEOUT$  / timeout   → リトライ
[1] ^ERROR$    / error     → リトライ
[2] ^NO_RESULT$ / no_result → リトライ
[3] ^.+$       / success   → OpenAI
[4-10] 空 / jump1-7       → 空（未使用）
```

- **success は `^.+$` で1本受けのみ** — 個別パターン（`^予約$` 等）をSTTに入れるのは**禁止**
- 個別分岐は後続の generate_by_OpenAI で行う

### 3.6 DTMF AmiVoice STT Input

| 項目 | 値 |
|---|---|
| type | `drjoy^External Integration$DTMF AmiVoice STT Input` |
| params.prompt | `"{recstart}"` — **JSON内に直接記載必須**（IVRプロパティに書くと上書きで失われる） |
| params.max_dtmf_length | デフォルト `"10"`（用件選択=`"1"`, 電話番号=`"11"`） |
| params.retry | `"2"` |
| params.termdtmf | `"#"` |
| params.remove_term | `"Yes"` |
| params.stop_play_when_speech | `"Yes"` |
| next | STTと同じ構造（最大11スロット） |
| subs | save2db サブモジュール接続**必須** |

### 3.7 generate_by_OpenAI

| 項目 | 値 |
|---|---|
| type | `drjoy^External Integration$generate_by_OpenAI` |
| params.contextName | DB保存先コンテキスト名 |
| params.contextDisplayType | TEXT / CLASSIFICATION / DATE / DATE_OF_BIRTH / PHONE_NUMBER |
| params.promptTTS | **必ず空欄** |
| params.module | **必須**: 出力元のSTT/OpenAIモジュール名（modules内に存在必須） |
| params.functionCall | JSON文字列（任意。空文字可） |
| params.prompt | AIへの指示プロンプト |
| next | 最大10スロット。先頭3つは TIMEOUT/ERROR/NO_RESULT の順序固定 |

**OpenAI next パターン**:
```
[0] ^TIMEOUT$  / timeout   → リトライ
[1] ^ERROR$    / error     → リトライ
[2] ^NO_RESULT$ / no_result → リトライ
[3+] 分岐条件（^予約$ 等）or ^.+$ / success
```

### 3.8 Speech Retry Counter

| 項目 | 値 |
|---|---|
| type | `drjoy^Text To Speech$Speech Retry Counter` |
| matchingmethod | **0**（他は全て1） |
| params.retry_count | `"1"` 推奨 |
| params.prompt_true | リトライ時のTTS — **JSON内に直接記述**（IVRプロパティでは動作しない） |
| params.prompt_false | リトライ上限時のTTS — **JSON内に直接記述** |
| next[0] | condition=`true`, label=`Retry` → **先頭TTSモジュール**（STT直接指定は禁止） |
| next[1] | condition=`false`, label=`No more` → 正解ルートの次のモジュール |
| subs | save2db サブモジュール接続**必須** |

**prompt_true 固定値**: `{tts_g:申し訳ございません。うまく聞き取りが出来ませんでした。再度、}`
**prompt_false 原則**: 空文字 `""`

### 3.9 save2db

| 項目 | 値 |
|---|---|
| type | `drjoy^Persistence$save2db` |
| params | `{ "contextName": "", "contextDisplayType": "TEXT" }` |
| next | 空配列 `[]` — next遷移**禁止** |
| 配置 | modules に定義必須。subs 経由のみで参照 |

### 3.10 saveContext2DB

| 項目 | 値 |
|---|---|
| type | `drjoy^Persistence$saveContext2DB` |
| params.contextName | 保存先フィールド名（必須、空禁止） |
| params.contextValue | セットする値（必須、空禁止）。固定文字列 or システム変数のみ。**`#data#` は禁止** |
| params.contextDisplayType | TEXT |
| next | `^.*$` / `next` → 次のモジュール |
| subs | サブモジュール接続**不可** |

### 3.11 saveCompletionFlag2db

| 項目 | 値 |
|---|---|
| type | `drjoy^Persistence$saveCompletionFlag2db` |
| params.status | `"1"`,`"2"`,`"3"`,`"6"`,`"7"` 以降（`"0"`,`"5"` は**使用禁止**） |
| params.smsFlag | `"0"` or `"1"` or `"2"` |
| 配置 | 終話ガイダンス（TTS）の**直前**に配置。順序: saveCompletionFlag2db → TTS → Disconnect |
| subs | サブモジュール接続**不可** |

### 3.12 incoming-classifier（着信分類）

| 項目 | 値 |
|---|---|
| type | `drjoy^Incoming$incoming-classifier` |
| params | `{}` |
| next ラベル | `非通知`, `固定`, `海外`, `携帯`, `その他` |

### 3.13 ContextMatchRouter

| 項目 | 値 |
|---|---|
| type | `drjoy^Context Logic$ContextMatchRouter` |
| 用途 | コンテキスト値に基づく分岐 |

### 3.14 Custom Jump to Flow

| 項目 | 値 |
|---|---|
| type | `drjoy^Custom Module$Custom Jump to Flow` |
| params.flowname | 遷移先サブフロー名（空禁止） |
| params.properties | サブフロー用IVRプロパティ情報 |
| next | サブフロー完了後の戻り先 |

### 3.15 Jump to Flow（旧型・既存互換）

| 項目 | 値 |
|---|---|
| type | `@General$Jump to Flow` |
| next[0] | 戻り先 |

### 3.16 RAG（FAQ応答）

| 項目 | 値 |
|---|---|
| type | `drjoy^External Integration$RAG` |
| 配置 | サブフローに分離して使用 |

### 3.17 Script

| 項目 | 値 |
|---|---|
| type | `@General$Script` |
| モジュール名 | `script_` プレフィックス必須 |
| API | `$runner.getModuleResult("名前")` で取得, `$runner.setResult("値")` で返却 |

### 3.18 Disconnect

| 項目 | 値 |
|---|---|
| type | `@IVR$Disconnect` |
| params | `{}` |
| next | なし（終端） |

### 3.19 Call Transfer（有人転送）

| 項目 | 値 |
|---|---|
| type | `@IVR$Call Transfer` |
| params | number, transfer_type=`"Blind Transfer"`, timeout=`"30000"` |
| next | `true`(Succeeded) → 転送成功flag → 切断, `false`(Failed) → 失敗TTS |

### 3.20 DOB Re-confirmation（生年月日復唱）

| 項目 | 値 |
|---|---|
| type | `drjoy^TS Custom Module$DOB Re-confirmation` |
| params | openAI_prompt, saveDOB2db, prompt, module, dateReadingMode |
| next | success → 復唱STT, INVALID → リトライ, timeout/error → リトライ |

### 3.21 Phone Normalization（電話番号正規化）

| 項目 | 値 |
|---|---|
| type | `drjoy^TS Custom Module$Phone Normalization` |
| params | phoneReadingMode=`"全桁"`, module=入力元モジュール名 |
| next | success → 復唱, INVALID → リトライ |

### 3.22 Re-confirmation node data（汎用復唱）

| 項目 | 値 |
|---|---|
| type | `drjoy^Text To Speech$Re-confirmation node data` |
| params.nodeName | 参照元モジュール名 |
| params.prompt | `{tts_g:...#data#...}` 形式 |

### 3.23 DateOfCall Classifier（時間帯分岐）

| 項目 | 値 |
|---|---|
| type | `drjoy^Incoming$DateOfCall Classifier` |
| params.comparison_time | `"16:00:00"` 等 |
| next | 時間前, 時間一致, 時間後 |

---

## 4. next 配列ルール（condition / label 早見表）

| モジュール種別 | condition | label | 備考 |
|---|---|---|---|
| TTS → 次へ | `^.*$` | `Next Module` | |
| STT タイムアウト | `^TIMEOUT$` | `timeout` | |
| STT エラー | `^ERROR$` | `error` | |
| STT 認識なし | `^NO_RESULT$` | `no_result` | |
| STT 成功 | `^.+$` | `success` | 個別パターン禁止 |
| OpenAI TIMEOUT | `^TIMEOUT$` | `timeout` | 先頭[0] |
| OpenAI ERROR | `^ERROR$` | `error` | [1] |
| OpenAI NO_RESULT | `^NO_RESULT$` | `no_result` | [2] |
| OpenAI 個別分岐 | `^{値}$` | `{値}` | [3]以降 |
| OpenAI 成功 | `^.+$` / `^.*$` | `success` | |
| Retry 続行 | `true` | `Retry` | 先頭TTSへ |
| Retry 上限 | `false` | `No more` | 正解ルートの次へ |
| Persistence 次へ | `^.*$` | `next` | |

**重要ルール**:
- 同一モジュールの next 配列内で**ラベルは重複禁止**
- 条件評価は**上から順**。最初にマッチした遷移先が使われる
- `^.*$` は「それ以外全て」（フォールバック）として最後に配置

---

## 5. subs 配列ルール（save2db 接続）

- **全ての TTS/STT/Retry Counter に save2db サブモジュールを必ず接続**
- ラベル名は `save-` プレフィックスで開始
- TTS と直後の STT/Retry は**同じ save2db ラベル名**を共有
- save2db は modules に定義必須だが next からの遷移は**禁止**（subs経由のみ）
- `saveCompletionFlag2db`, `saveContext2DB`, `saveContextModel2DB` はサブモジュール接続**不可**

---

## 6. 命名規則

### 6.1 禁止文字

- 丸数字（`①②③` 等の環境依存文字）
- 括弧（`（）()[]`）
- スペース（半角・全角）
- アンダーバー以外の区切り文字

### 6.2 フロー名

- `グループ名$フロー名_YYYYMMDD` 形式
- URLエンコード後255バイト以内
- サブフローも同一の日付サフィックス

### 6.3 グループ名

- 顧客資料記載の施設名をそのまま使用（省略・独自命名禁止）
- 英字のスペース → アンダーバーに変換

### 6.4 モジュール名パターン

| カテゴリ | パターン | 例 |
|---|---|---|
| TTS | `大分類_内容` | `冒頭_アナウンス`, `患者_氏名` |
| STT | `入力_大分類_内容` | `入力_患者_氏名` |
| OpenAI | `OpenAI_大分類_内容` | `OpenAI_用件_区分` |
| Retry | `リトライ_大分類_内容` | `リトライ_患者_氏名` |
| save2db | `save-大分類_内容` | `save-患者_氏名` |
| Script | `script_内容` | `script_携帯判別` |

### 6.5 IVRプロパティ名とモジュール名

**完全一致が必須**（不一致だとTTS動作しない）。
- 正: `冒頭_アナウンス.prompt={tts_g:...}`
- 誤: `tts_冒頭_アナウンス={tts_g:...}`

---

## 7. Validator エラーコードと意味

### 構造系 (S)

| コード | 重要度 | 意味 |
|---|---|---|
| S-001 | CRITICAL | 必須フィールド (name/start/modules) が存在しない |
| S-002 | WARNING | フロー名が `グループ名$フロー名` 形式ではない |
| S-003 | CRITICAL | start モジュールが modules 内に存在しない |

### 遷移系 (T)

| コード | 重要度 | 意味 |
|---|---|---|
| T-001 | CRITICAL | next の遷移先モジュールが modules 内に存在しない |
| T-002 | WARNING | どこからも参照されていない孤立モジュール |
| T-003 | CRITICAL | subs 参照先モジュールが modules 内に存在しない |
| T-004 | CRITICAL | 同一モジュール内で next ラベルが重複 |

### STT系

| コード | 重要度 | 意味 |
|---|---|---|
| STT-000 | CRITICAL | STT next が最大11スロットを超過 |
| STT-001 | CRITICAL | TIMEOUT/ERROR/NO_RESULT の遷移先がない |
| STT-002 | CRITICAL | TIMEOUT/ERROR/NO_RESULT の遷移先が空 |
| STT-003 | CRITICAL | success遷移 `^.+$` が未定義 |
| STT-004 | CRITICAL | STT に個別パターンが含まれている（OpenAI で分岐すべき） |

### TTS系

| コード | 重要度 | 意味 |
|---|---|---|
| TTS-001 | CRITICAL | TTS next label が `Next Module` ではない |
| TTS-002 | CRITICAL | stop_by_dtmf が `Yes`/`No` ではなく `true`/`false` になっている |
| TTS-003 | INFO | prompt が `{tts_g:...}` 形式ではない（IVRプロパティ管理時は無視可） |

### OpenAI系 (OAI)

| コード | 重要度 | 意味 |
|---|---|---|
| OAI-001 | CRITICAL | params.module が空 |
| OAI-002 | CRITICAL | params.module の参照先がmodules内に存在しない |
| OAI-003 | WARNING | params.promptTTS に値が設定されている（空欄にすべき） |
| OAI-004 | WARNING | next 先頭3スロットが TIMEOUT/ERROR/NO_RESULT の順序になっていない |

### Retry系 (R)

| コード | 重要度 | 意味 |
|---|---|---|
| R-001 | CRITICAL | condition=`true` がない |
| R-002 | CRITICAL | condition=`false` がない |
| R-003 | CRITICAL | true の label が `Retry` ではない |
| R-004 | CRITICAL | false の label が `No more` ではない |
| R-005 | WARNING | retry_count が未設定 |

### save2db / Persistence系 (SB/CTX/COMP)

| コード | 重要度 | 意味 |
|---|---|---|
| SB-001 | WARNING | TTS/STT に save2db サブモジュールが接続されていない |
| SB-002 | CRITICAL | save2db に next 遷移が設定されている |
| CTX-010 | CRITICAL | saveContext2DB の contextName が空 |
| CTX-011 | CRITICAL | saveContext2DB の contextValue が空 |
| CTX-012 | CRITICAL | saveCompletionFlag2db の status が空 |
| CTX-013 | CRITICAL | saveContext2DB の contextValue に `#data#` が使用されている |
| CTX-014 | WARNING | saveContextModel2DB の fields がminified |
| CTX-016 | CRITICAL | clinicalDepartment の displayType が DEPARTMENT ではない |
| CTX-017 | CRITICAL | 重複不可の displayType が複数件ある |
| COMP-001 | CRITICAL | status が `"0"` or `"5"`（第2世代予約値で使用禁止） |

### 命名系 (N)

| コード | 重要度 | 意味 |
|---|---|---|
| N-001 | CRITICAL | 環境依存文字（丸数字等） |
| N-002 | WARNING | 括弧を含む |
| N-003 | WARNING | スペースを含む |

### Layout系

| コード | 重要度 | 意味 |
|---|---|---|
| LAYOUT-001 | CRITICAL | 50%以上のモジュールが (0,0) |
| LAYOUT-002 | WARNING | 3以上のモジュールが (0,0) |
| LAYOUT-003 | WARNING | 横並び（水平）配置 |

### DTMF系

| コード | 重要度 | 意味 |
|---|---|---|
| DTMF-001 | CRITICAL | prompt に `{recstart}` がない |
| DTMF-002 | WARNING | max_dtmf_length が未設定 |
| DTMF-003 | WARNING | retry が `"0"` |
| DTMF-004 | WARNING | termdtmf/remove_term/stop_play_when_speech が未設定 |

### フロー構造系 (FLOW)

| コード | 重要度 | 意味 |
|---|---|---|
| FLOW-001 | CRITICAL | start モジュールが wait ではない |
| FLOW-002 | CRITICAL | 冒頭チェーンに saveContextModel2DB がない |
| FLOW-003 | WARNING | 冒頭チェーンが短すぎる |
| FLOW-004 | CRITICAL | Custom Jump to Flow の flowname が空 |
| FLOW-005 | WARNING | Custom Jump to Flow の properties が空 |
| FLOW-006 | WARNING | STTの直前にTTS/Retryがない |

### プロンプト整合性系 (PROMPT)

| コード | 重要度 | 意味 |
|---|---|---|
| PROMPT-001 | CRITICAL | next 分岐ラベルが prompt 出力仕様に存在しない |
| PROMPT-002 | WARNING | prompt 出力仕様のラベルに対応する next 条件がない |
| PROMPT-003 | CRITICAL | prompt が空欄（prompter 未実行） |
| PROMPT-004 | WARNING | ワイルドカード分岐で NO_RESULT 記述がない |

### 到達可能性系 (REACH)

| コード | 重要度 | 意味 |
|---|---|---|
| REACH-001 | WARNING | start から到達不能なモジュール |

### 電話番号サブフロー系 (PH)

| コード | 重要度 | 意味 |
|---|---|---|
| PH-001 | CRITICAL | incoming-classifier が配置されていない |
| PH-002 | CRITICAL | 携帯判別スクリプトが配置されていない |
| PH-003 | WARNING | 集約スクリプトが見つからない |

### スクリプト系 (SCR)

| コード | 重要度 | 意味 |
|---|---|---|
| SCR-001 | WARNING | script_ プレフィックスで始まっていない |
| SCR-002 | CRITICAL | サブフローに結果返却スクリプトがない |
| SCR-003 | WARNING | getModuleResult() の呼び出しがない |
| SCR-004 | WARNING | setResult() の呼び出しがない |
| SCR-005 | WARNING | setObject() の呼び出しがない |
| SCR-006 | WARNING | getCurrentFlowName()/getRID() の呼び出しがない |

### サブフロー終話方式系 (SF-TERM)

| コード | 重要度 | 意味 |
|---|---|---|
| SF-TERM-001 | CRITICAL | return なのに Disconnect がある |
| SF-TERM-002 | WARNING | self_contained なのに Disconnect がない |
| SF-TERM-003 | WARNING | termination 未設定で Disconnect がある |

---

## 8. OpenAI プロンプト設計ルール

### 8.1 基本ルール（全プロンプト共通）

- 出力結果の前後に一切の余計な情報を出力しない
- `\n`（改行コード）の出力禁止
- 謝辞・謝罪・説明・語尾の出力禁止
- 認識できない場合は `NO_RESULT` を出力
- IVRプロパティにプロンプトを入れる場合は**1行のみ**
- プロンプト先頭に「今日はyyyy年mm月dd日」が**システムにより自動付与**される

### 8.2 tester.py 4本柱チェック

| コード | 柱 | 重要度 | 要件 |
|---|---|---|---|
| P-3a | 文脈定義 | CRITICAL | `# Role` セクションが存在する |
| P-3b | 文脈定義 | CRITICAL | `# Context` セクションが存在する |
| P-4a | 例外処理 | CRITICAL | `NO_RESULT` の記述がある |
| P-4d | 例外処理 | CRITICAL | next配列に `^NO_RESULT$` 条件がある |
| P-5 | 整合性 | CRITICAL | prompt 出力値と next 分岐条件が一致 |
| P-4b | 例外処理 | WARNING | 出力値の限定記述がある |
| P-4c | 例外処理 | WARNING | インジェクション防御セクションがある |

### 8.3 プロンプト種別と出力形式

| 種別 | 出力形式 | 例 |
|---|---|---|
| 氏名 | カタカナフルネーム or NO_RESULT | `ヤマダタロウ` |
| 電話番号 | 数字10-11桁（ハイフンなし）or NO_RESULT | `09012345678` |
| 用件分類 | 定義済み選択肢 or NO_RESULT | `予約`, `変更`, `キャンセル` |
| 受診歴 | `初診` / `再診` / NO_RESULT | |
| 生年月日 | `YYYYMMDD` or NO_RESULT | `19800315` |

### 8.4 実行環境

- モデル: GPT-4系（4.2相当）、temperature=0.1（固定）
- 出力: `generatedText` フィールドにプレーンテキスト1行
- functionCall 形式: `dialogue_completed` の `result` フィールド

---

## 9. AmiVoice 辞書ルール（profile_words）

### 9.1 フォーマット

```
表記 よみがな
表記 よみがな
```

- 1行1エントリ、**半角スペース**で区切り
- 同一単語を複数よみがなで登録可
- JSON内では `\n` でエスケープ

### 9.2 入力種別と使用辞書

| 入力種別キーワード | 使用辞書 |
|---|---|
| 氏名 | 氏名辞書 |
| 生年月日, 日付 | 和暦 + month + day辞書 |
| 時間 | hour辞書 |
| 曜日 | 曜日辞書 |
| 診療科, 外来 | 診療科辞書 |
| 健診, 検診 | 健診辞書 |
| 薬, 薬剤 | 処方薬剤辞書 |
| 復唱 | 肯定否定辞書 |
| 用件, 病棟, フロア | 施設固有（設計書参照） |

### 9.3 辞書登録の注意

- 過度な登録は逆効果（`なのか`→`7日`, `2月`→`にがつ`で12月が「いちにがつ」になる等）
- profile_words が空白でよいケース: 汎用STT、設計書に語彙リストなし

---

## 10. SSML ガイド

TTS 発話テキスト内で使用可能なSSMLタグ:

| タグ | 用途 | 例 |
|---|---|---|
| `<break time="500ms"/>` | ポーズ挿入 | 間を空ける |
| `<prosody rate="slow">` | 発話速度調整 | ゆっくり読み上げ |
| `<prosody pitch="+2st">` | 音程調整 | |
| `<emphasis level="strong">` | 強調 | |
| `<sub alias="ないか">内科</sub>` | 読み方置換 | 誤読防止 |
| `<say-as interpret-as="digits">` | 1桁ずつ読み | 電話番号 |
| `<say-as interpret-as="telephone">` | 電話番号読み | |
| `<say-as interpret-as="date" format="ymd">` | 日付読み | |

**電話番号復唱の定型**:
```
{tts_g:<speak><say-as interpret-as="digits">#data#</say-as></speak>、ですね。}
```

---

## 11. Layout 座標ルール

### 11.1 座標系

- x軸: 右が正（分岐パスごとに横オフセット）
- y軸: 下が正（フロー進行方向）
- 座標は表示のみに影響し、IVR動作には影響しない

### 11.2 開始チェーン（固定座標）

| モジュール | x | y |
|---|---|---|
| 冒頭 (wait) | -210 | -440 |
| コンテキスト設定 | -210 | -320 |
| 営業時間チェック | -210 | -200 |
| 冒頭アナウンス | -150 | -90 |

### 11.3 会話ステップ内の相対配置

TTS座標を基準(0,0)として:

| モジュール | Dx | Dy |
|---|---|---|
| TTS | 0 | 0 |
| STT | 0 | +110 |
| OpenAI | 0 | +230 |
| Retry | -280 | +230 |
| Save | -280 | +110 |

### 11.4 ステップ間隔

- 標準 Dy = 400
- メインパス最初のステップ: (x=20, y=180)

---

## 12. 環境設定テンプレート

### 12.1 デモ環境 (env_demo.txt)

```
amivoice.uri=ws://10.0.20.11:8000/ws
amivoice.language=ja
amivoice.engine=入力汎用
amivoice.keep_filter_token=true
amivoice.silent_detection_ms=2000
amivoice.timeout_ms=30000
amivoice.probability=0.7
amivoice.detection_flag=音声開始前から検出
amivoice.save_log=false
pbx.db.name=save.db
context.settings.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/pbx/context-model
acceptance_times.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/incoming-call-by-brekeke
rag_ssml.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/rag-ssml/process-text
openAI_generate.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/openai/generate-text
speech.rag.url=http://10.0.20.11:8000/api/v1/rag
speech.rag.connect_timeout=2
speech.rag.request_timeout=3
speech.rag.credibility=0
```

### 12.2 本番環境 (env_prod.txt)

```
amivoice.uri=ws://speech.internal.assistant.com:8000/ws
amivoice.probability=0.50
amivoice.silent_detection_ms=2000
amivoice.timeout_ms=30000
pbx.db.name=save.db
context.settings.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/pbx/context-model
acceptance_times.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/incoming-call-by-brekeke
rag_ssml.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/rag-ssml/process-text
openAI_generate.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/openai/generate-text
speech.rag.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/rag-ssml/process-text
```

### 12.3 プロパティの優先順位

- **IVRプロパティ > モジュール内設定**（プロパティの値が常に優先）
- API URL/AmiVoice設定/TTS発話内容はIVRプロパティで一括管理
- STT の URI は `amivoice.uri=` でグローバル管理（個別の `入力_xxx.uri=` は禁止）
- Retry Counter の prompt_true/prompt_false は**IVRプロパティでは動作しない**（JSON内直接記述）

---

## 13. フロー設計の基本原則

### 13.1 開始チェーン（固定）

```
冒頭(wait) → saveContextModel2DB → incoming-classifier → [acceptance_times] → 冒頭アナウンス
```

- 非通知・海外は incoming-classifier で弾く
- 営業時間チェックは任意

### 13.2 会話ステップ（5モジュール1セット）

```
TTS(質問) → STT(入力) → OpenAI(正規化/分岐) → Retry → save2db
```

### 13.3 終了チェーン

```
saveCompletionFlag2db → 終話分岐_電話番号(phonetype) → 携帯/固定用TTS → Disconnect
```

- 携帯ルート: SMS言及あり
- 固定ルート: SMS言及なし

### 13.4 サブフロー分割ルール

新規作成・移管時は以下を必ずサブフロー化:
- 患者氏名, 生年月日, 電話番号, 診察券番号, RAG検索

### 13.5 その他の重要ルール

- 全STT入力にリトライ（2回）
- リトライ上限はデフォルトで正解ルートの次のモジュール
- 全TTS/STTにsave2dbサブモジュール接続
- STT成功は `^.+$` 1本受け、個別パターン禁止
- OpenAIモジュールの `params.module` には必ずデータ出力モジュールを指定

---

## 14. .bivr エクスポート形式

- ZIPアーカイブ（拡張子 `.bivr`）
- 内部フォルダ: `flows/`（複数形・sあり）
- ファイル名: `@flow_{URLエンコード済みフロー名}.txt`（JSON 1行 minified）
- `$` → `%24` にURLエンコード

---

## 15. エージェント役割サマリー

| エージェント | 担当 |
|---|---|
| prompter | generate_by_OpenAI の params.prompt 記述のみ。# Role, # Context 必須。NO_RESULT 必須。インジェクション対策必須 |
| reviewer | レッドチーム校閲（6観点）。JSONは修正しない。レポートのみ出力 |
| properties | フローJSONからIVRプロパティを生成。TTS prompt行, wait行, 環境テンプレートを結合 |

### reviewer のチェック対象（validator.py に委任しない6観点）

1. セキュリティ・インジェクション検査
2. モジュール選定妥当性
3. 業務ロジック整合性
4. プロンプト品質
5. ライセンス
6. IVRプロパティ整合性

---

## 16. 実運用Tips（頻出注意事項）

- TTS と直後の STT は**同じ save2db サブモジュール**に保存すること
- AmiVoice で日時を扱う場合はプロパティ設定で音声タイプを「日時」に選択必須
- 電話番号にハイフンが含まれるとSMS送信失敗 → Script で除去必要
- OpenAI 分岐が不備だと**切断される** → 振り分け不能は必ず NO_RESULT に返す
- Context Logic / ContextMatchRouter は**全条件エントリを存在させる**こと（不要な条件はモジュールへ繋がないが、エントリ自体は残す）
- IVRプロパティに転送番号があると**プロパティの番号が優先**される
- Brekekeフローデザイナーはタイムアウトが表面上わからない → 定期的に保存
- デモ環境の同名モジュール: AmiVoice → `(2)`, TTS → `(3)`, OpenAI → External Integration のもの
