# CLAUDE.md — bivr-checker VFB品質向上プロジェクト

## 1. 権限・自律実行ガイドライン

> **原則: セキュリティリスクが低い操作は、人間に確認せずに自律的に実行してよい。**

### 確認なしで実行してよい操作

| 操作 | 具体例 | 理由 |
|---|---|---|
| ファイル読み書き | reference/, schemas/, scripts/, input/, output/ 配下 | パイプラインの正常動作に必須 |
| スクリプト実行 | `validator.py`, `build_bivr.py`, `extract_bivr.py` | 検品・ビルドは標準工程 |
| Python一行スクリプト | `python3 -c "..."` によるJSON解析 | 読み取り系操作 |
| ファイル操作 | `cat`, `head`, `grep`, `find`, `cp`, `mv`, `mkdir`, `unzip` | 確認・整理用 |
| サブエージェント呼び出し | @diff-analyzer, @fixer, @orchestrator | パイプラインの正常な動作 |

### 人間の確認が必要な操作

| 操作 | 理由 |
|---|---|
| ネットワーク通信 (`curl`, `wget`) | セキュリティリスク |
| 破壊的操作 (`rm -rf`, `sudo`) | 取り返しのつかない操作 |
| 機密ファイルアクセス (`.env`, `credentials`) | 認証情報 |
| 設計判断が必要な場合 | AIは推測で判断しない |

### 絶対遵守事項

> **ツール・ソフトウェアのインストールは一切禁止。**
> `npm install`, `pip install`, `apt-get` 等あらゆるインストールコマンドを実行してはならない。
> 必要なツールが不足している場合は人間に報告する。

### リトライ・エスカレーション

- **WARNING**: 自律的に修正を試みてよい
- **CRITICAL**: 最大3回自律修正 → 解消しない場合は人間にエスカレーション
- **設計書の不備（BLOCKER）**: 人間に確認必須。推測で埋めない

---

## 2. プロジェクト概要

VoiceBot Flow Builder (VFB) が生成する `.bivr` ファイルと `Property.md` の品質を、人間が作成したものと同等以上に引き上げるためのプロジェクト。

### 2つの目的

1. **VFBの生成品質を上げる**（根本改善）— 差分分析・パターン蓄積 → VFBへフィードバック
2. **生成されたものを修正する**（即時対応）— チェック結果に基づく自動修正

### ワークフロー

```
1. VFBで生成（VoiceBot Flow Builder）
2. Claude.aiのプロンプトでチェック（外部）→ チェック結果
3. 本プロジェクトで修正＆蓄積
```

### エージェント構成

| エージェント | モデル | 役割 |
|---|---|---|
| diff-analyzer | Opus | VFB生成物 vs 人間修正の差分分析・パターン抽出 |
| fixer | Sonnet | チェック結果に基づく自動修正 + デフォルト値補完 |
| orchestrator | Opus | パイプライン制御 |

### VoiceBot Flow Builderとの関係

- **独立プロジェクト** — VFBとランタイム共有なし（将来的にVFBに統合予定）
- VFBから `build_bivr.py`・`extract_bivr.py` をコピー（安定ユーティリティ）
- 本プロジェクトの蓄積データが最終的にVFBの生成ルールを改善する

### 品質向上の3要素

1. **精度向上の定義**: チェックルール（`reference/check_prompt.md`）+ デフォルト値（`reference/defaults.json`）
2. **パターンの蓄積**: VFBが何を間違えるかの頻出パターン（`reference/defaults_overrides/learned_patterns.json`）
3. **教師データの蓄積**: VFB生成物 vs 人間修正の突合ペア（`training_data/feedback/corrections/`）

---

## 4. フローJSONルール

### フローJSON基本形

```json
{
  "layout": {},
  "resultValue": "",
  "postCallAction": "",
  "name": "グループ名$フロー名_YYYYMMDD",
  "start": "開始モジュール名",
  "modules": { "モジュール名": { ... } },
  "desc": ""
}
```

- `desc` は空文字 `""`
- `modules` は辞書型（配列ではない）

### 主要モジュールタイプ

| type値 | 役割 |
|---|---|
| `Custom$wait` | 冒頭待ち時間 |
| `drjoy^Persistence$saveContextModel2DB` | コンテキストスキーマ設定 |
| `drjoy^External Integration$acceptance_times` | 受付時間判定 |
| `drjoy^Text To Speech$Text to speech` | TTS発話 |
| `drjoy^AmiVoice$Speech to Text` | 音声入力（STT） |
| `drjoy^External Integration$DTMF AmiVoice STT Input` | 音声入力（DTMF+STT） |
| `drjoy^External Integration$generate_by_OpenAI` | OpenAI分岐 |
| `drjoy^Text To Speech$Speech Retry Counter` | リトライ制御 |
| `drjoy^Persistence$save2db` | 音声録音保存（サブモジュール専用） |
| `drjoy^Persistence$saveContext2DB` | コンテキスト保存 |
| `drjoy^Persistence$saveCompletionFlag2db` | 完了フラグ保存 |
| `drjoy^Incoming$incoming-classifier` | 着信電話番号分岐 |
| `drjoy^Custom Module$Custom Jump to Flow` | サブフロー遷移 |
| `@General$Script` | スクリプト実行（`script_` プレフィックス必須） |
| `@IVR$Disconnect` | 切断 |
| `@IVR$Call Transfer` | 有人転送 |
| `drjoy^External Integration$RAG` | RAG検索 |
| `drjoy^Text To Speech$Re-confirmation node data` | TTS復唱ノード（Text To Speechカテゴリ。Customカテゴリは誤り） |
| `drjoy^Context Logic$ContextMatchRouter` | コンテキスト値ルーティング（ContextMatchRouter）。nextの条件は `^1$`, `^2$`, `^3$` 形式（インデックスベース）。詳細仕様は下記「ContextMatchRouter設定ルール」参照 |
| `drjoy^Incoming$DateOfCall Classifier` | 時間帯分岐（VFB v2新型）。DateOfCall Classifierで時間帯・曜日による分岐を実現。acceptance_timesの代替または補完として使用 |
| `drjoy^TS Custom Module$Phone Normalization` | 電話番号正規化専用モジュール（VFB v2新型）。HTML/SSML形式で出力。電話番号聴取サブフローで使用 |
| `drjoy^Persistence$saveNodeData2Session` | セッションデータ保存（スマート面会専用）。面会予約フローのみで使用 |

### next配列の規則

#### STTモジュール（最大11スロット）

```json
"next": [
  {"condition": "^TIMEOUT$",  "label": "timeout",   "nextModuleName": "リトライ_xxx"},
  {"condition": "^ERROR$",    "label": "error",     "nextModuleName": "リトライ_xxx"},
  {"condition": "^NO_RESULT$","label": "no_result", "nextModuleName": "リトライ_xxx"},
  {"condition": "^.+$",       "label": "success",   "nextModuleName": "OpenAI_xxx"}
]
```

- **success は `^.+$` で1本受けのみ**。個別パターンをSTTに入れるのは禁止
- 個別分岐は後続の `generate_by_OpenAI` で行う

#### generate_by_OpenAI（最大10スロット）

```json
"next": [
  {"condition": "^TIMEOUT$",  "label": "timeout",   "nextModuleName": "リトライ_xxx"},
  {"condition": "^ERROR$",    "label": "error",     "nextModuleName": "リトライ_xxx"},
  {"condition": "^NO_RESULT$","label": "no_result", "nextModuleName": "リトライ_xxx"},
  {"condition": "^.+$",       "label": "success",   "nextModuleName": "次のモジュール"}
]
```

- TIMEOUT/ERROR/NO_RESULT は必ず先頭3スロット
- 分岐型の場合は個別条件パターン (`^予約$` 等) を [3] 以降に配置

#### TTSモジュール

```json
"next": [
  {"condition": "^.*$", "label": "Next Module", "nextModuleName": "次のモジュール"}
]
```

- label は必ず `"Next Module"`

#### Retry Counter

```json
"next": [
  {"condition": "true",  "label": "Retry",   "nextModuleName": "先頭TTSモジュール"},
  {"condition": "false", "label": "No more", "nextModuleName": "正解ルートの次"}
]
```

- **Retry先は原則として先頭TTSモジュール**
- **`prompt_true` 固定値**: `{tts_g:申し訳ございません。 うまく聞き取りが出来ませんでした。 再度、}`
- **`prompt_false` は聴取項目の種別に応じて3パターンで設計する（下表参照）**
- **prompt_true/prompt_false はJSON内に直接記述**（IVRプロパティでは動作しない）
- `matchingmethod`: **0**（他モジュールは全て1）

#### prompt_false の3パターン体系（教師データより）

| パターン | 使用条件 | false遷移先 | prompt_false 値 | 文言例 |
|---|---|---|---|---|
| **A. 任意聴取→次へ進む** | 任意聴取項目（氏名・症状・問い合わせ等）でリトライ上限到達 | 次のステップ | 失敗告知メッセージを設定 | `{tts_g:かしこまりました。折り返しの際に確認させていただきます。}` または `{tts_g: 大変申し訳ございません。 うまく聞き取ることができませんでしたので後ほど担当者にて確認いたします。}` |
| **B. 任意聴取→失敗終話** | 失敗したら終話させる設計の場合 | 終話_失敗 TTS | 失敗告知または空文字 | `{tts_g: 大変申し訳ございません。 うまく聞き取ることができませんでした。}` → Disconnect |
| **C. 必須聴取→無限ループ** | 用件・種別など必須聴取でリトライ上限到達後も聴取継続 | 同じ先頭TTS（ループ） | `""` 空文字 | prompt_false="" のまま、false遷移先を冒頭TTSに戻す |

> **設計手順**: PDFの「2回リトライ失敗した場合」の仕様を確認し、「次の質問へ進む」→パターンA、「終話する」→パターンB、「繰り返す」→パターンCを選択する。PDFに記載がない場合はパターンA（次へ進む）を採用し、失敗告知メッセージを設定する。

#### Retry → TTS 接続時の日本語確認ルール

Retry の `prompt_true` とその遷移先 TTS のプロンプトを連結したとき、**日本語として自然につながるか**を必ず確認する。

例（自然）:
> 「申し訳ございません。うまく聞き取りが出来ませんでした。再度、」＋「ご用件をお話しください。」
> → 「申し訳ございません。うまく聞き取りが出来ませんでした。再度、ご用件をお話しください。」 ✅

例（不自然）:
> 「申し訳ございません。うまく聞き取りが出来ませんでした。再度、」＋「以下からお選びください。1の場合は〜」
> → 前後がつながらない ❌

**不自然な場合の対処（どちらかを選択）:**

| 方法 | 内容 | 使いどころ |
|---|---|---|
| A. prompt_true を修正 | Retry モジュール内の `prompt_true` をその設問に合った文言に変更する | TTS のテキストが変えられない場合 |
| B. 遷移先を STT に変更 | Retry の `true` 遷移先を TTS ではなく **STT（入力モジュール）に直接つなぐ**。`prompt_true` がそのまま発話になる | TTS を経由させたくない場合 |

> **注意（方法B）**: STT直接指定の場合は `prompt_true` に完結した発話文を設定すること。「再度、」で終わる文言のままにしない。

### condition と label の早見表

| モジュール種別 | condition | label |
|---|---|---|
| TTS → 次へ | `^.*$` | `Next Module` |
| STT タイムアウト | `^TIMEOUT$` | `timeout` |
| STT エラー | `^ERROR$` | `error` |
| STT 認識なし | `^NO_RESULT$` | `no_result` |
| STT 成功 | `^.+$` | `success` |
| OpenAI 個別分岐 | `^{値}$` | `{値}` |
| Retry 続行 | `true` | `Retry` |
| Retry 上限 | `false` | `No more` |
| Persistence 次へ | `^.*$` | `next` |

### subs配列の規則（save2db接続）

**全TTS・STT・Retry Counter に `save2db` サブモジュールを必ず接続**

```json
"subs": [
  {"moduleName": "save-xxx", "label": "save-xxx"},
  {"moduleName": "", "label": ""},
  {"moduleName": "", "label": ""}
]
```

- ラベル名は `save-` プレフィックスで始める
- save2db は modules に定義必須、subs 経由でのみ接続（next 禁止）
- `saveCompletionFlag2db`・`saveContext2DB`・`saveContextModel2DB` はサブモジュール禁止

### TTSプロンプト形式の制約

| 形式 | 可否 | 備考 |
|---|---|---|
| `{tts_g:テキスト}` | ✅ 使用可 | 標準TTS（全小文字必須） |
| `{tts_ai:テキスト}` | ❌ 使用禁止 | AI TTS（将来対応予定、現時点では動作しない） |
| `{TTS_AI:テキスト}` | ❌ 使用禁止 | 大文字形式は誤り |
| `<speak>`, `<break>`, `<say-as>` 等のSSMLタグ | ❌ 使用禁止 | Brekeke非対応 |

> **注意**: `{tts_g:...}` は全小文字で統一。形式を誤ると発話されない。

### stop_by_dtmf の値

| 意味 | 正しい値 | 誤った値 |
|---|---|---|
| 停止しない | `"No"` | `"false"` |
| 停止する | `"Yes"` | `"true"` |

### AmiVoice Speech to Text モジュール設定ルール

`drjoy^AmiVoice$Speech to Text` のプロパティ（uri, language, engine, timeout_ms 等）は**モジュール内では全てデフォルト値のまま**にする。

> **理由**: AmiVoice設定は大元の Property.md で一括管理するため、モジュールごとに個別設定しない。

- モジュール内で設定してよいのは `profile_words`（辞書）と `retry` 回数のみ
- uri / language / engine / silent_detection_ms / timeout_ms / probability / save_log / keep_filter_token はすべてデフォルト
- **detection_flag は `"デフォルト"` を明示設定する**（`"検出しない"` は禁止。Property.md側で管理するため、モジュール側は必ず `"デフォルト"` とする）

### DTMF AmiVoice STT Input デフォルト規則

| パラメータ | 正しいデフォルト | VFBが誤設定する値 |
|---|---|---|
| `prompt` | `"{recstart}"` — **JSON内に直接記載**（IVRプロパティ禁止） | — |
| `max_dtmf_length` | `"10"` | — |
| `retry` | `"2"` | `"0"` |
| `termdtmf` | `"#"` | `"*"` ← **VFB-034: 頻出ミス** |
| `remove_term` | `"Yes"` | — |
| `stop_play_when_speech` | `"Yes"` | `"No"` ← **VFB-034: 頻出ミス** |
| `timeout` | `"30000"` — **[DTMF] タイムアウト設定。必須** | — |
| `timeout_ms` | （設定不要。[AmiVoice] タイムアウトはグローバル管理） | — |

> **重要**: `termdtmf` は必ず `"#"` に設定する。VFBが `"*"` を設定するケースが確認されている（横須賀共済病院で発生）。

> **注意**: `timeout` と `timeout_ms` は別パラメータ。DTMFタイムアウトは `timeout`（[DTMF] Time out）を使用。`timeout_ms`（[AmiVoice] タイムアウト(ms)）はDTMFモジュールには不要。AmiVoice STTモジュールの `timeout_ms` はグローバル設定（Property.md）で管理するため、モジュール内では空欄のまま。

### Re-confirmation node data 設定ルール

`drjoy^Text To Speech$Re-confirmation node data` で `#data#` を正しく表示するには `module` パラメータの設定が必須。

| パラメータ | 内容 |
|---|---|
| `module` | `#data#` の参照元モジュール名（STT または OpenAI モジュール名） |
| `prompt` | `{tts_g: #data# でよろしいでしょうか。}` 形式 |

**生年月日の復唱は専用ノードを使用:**

`drjoy^TS Custom Module$DOB Re-confirmation` を使用（通常の Re-confirmation node data とは別）。

| パラメータ | 内容 |
|---|---|
| `module` | STT入力モジュール名（例: `入力_患者_生年月日`） |
| `openAI_prompt` | 生年月日正規化プロンプト（元号変換・桁数補完・妥当性チェック含む） |
| `prompt` | `{tts_g: <speak> #data# <break time="300ms"/> でよろしいでしょうか。 </speak> ...}` |
| `saveDOB2db` | `"Yes"` |
| `dateReadingMode` | `"自動"` |

next条件: `^TIMEOUT$`/`^ERROR$`/`^INVALID$` → リトライ、`^.*$` → 次のSTT

**Re-confirmation node data の汎用的な活用（DOB以外）:**

`Re-confirmation node data` は `nodeName` に任意のモジュール名（Script・OpenAI）を指定することで、そのモジュールの出力を `#data#` に埋め込んで読み上げる汎用TTS として使用できる。

| 用途 | nodeName | Property.mdのprompt例 | skipReadHour |
|---|---|---|---|
| 動的日付挿入（3営業日後等） | `script_日付取得`（Scriptモジュール名） | `{tts_g:#data# 以降のご予約を〜}` | `"Yes"` |
| 分類結果の読み上げ（変更/キャンセル等） | `OpenAI_用件確認`（OpenAIモジュール名） | `{tts_g:#data# の理由を簡潔に〜}` | `"Yes"` |

> **注意**: `skipReadHour="Yes"` は時刻の自動読み上げを無効にするため、動的テキスト挿入の場面では必ず設定すること。

### Script モジュール（@General$Script）テンプレート

よく使うScriptロジックは `reference/scripts/` に再利用可能なテンプレートを収録している（VFB script_templates より）。

| テンプレート | 用途 | 出力値 |
|---|---|---|
| `future_date.js` | 入力日付が今日より未来か判定 | SUCCESS / FAIL |
| `phone_type.js` | 電話番号を携帯/固定/その他に分類 | 携帯 / 固定 / その他 |
| `day_of_week.js` | 現在の曜日判定 | 平日 / 土曜 / 日曜祝日 |
| `business_hours.js` | 営業時間内か判定（引数: 開始時/終了時） | 営業時間内 / 営業時間外 |
| `condition_group.js` | 多段分岐のグループ分類 | グループ番号 1〜10 |

Script実装が必要な場合はまずテンプレートを確認してから実装すること。

### Script モジュール（@General$Script）禁止事項

`$runner.getModuleResult()` / `$runner.setModuleResult()` / `$runner.setContext()` 等の Brekeke 非対応APIを使ったスクリプトは**電話切断の原因となるため使用禁止**。

| 禁止パターン | 正しい代替方法 |
|---|---|
| グループ判定スクリプト（診療科→グループ名変換） | OpenAI プロンプトがグループ名を直接出力するよう設計 |
| 携帯判別スクリプト（電話番号→携帯/固定） | `drjoy^Incoming$incoming-classifier` で着信番号分類 |
| SMS判定スクリプト | 電話番号サブフローが phonetype context に保存した値を `ContextMatchRouter` で参照して分岐（incoming-classifierの追加は不可 — フロー内1つのみ制限） |

### 命名規則

**禁止文字**: `①②③` 等の環境依存文字、`（）()[]` 等の括弧、スペース

**フロー名**: `グループ名$フロー名_YYYYMMDD` — URLエンコード後255バイト以内

**グループ名**: 顧客資料記載の施設名をそのまま使用（省略・独自命名禁止）

**モジュール名**: `大分類_内容` 形式
- TTS: `冒頭_アナウンス`, `患者_氏名`
- STT: `入力_患者_氏名`
- OpenAI: `OpenAI_患者_氏名`
- Retry: `リトライ_患者_氏名`
- save2db: `save-患者_氏名`

**TTSプロンプト名とモジュール名の完全一致が必須**

### フロー設計の基本原則

1. **冒頭に wait 2000ms が必須**（`Custom$wait`）
2. **冒頭チェーン（VFB v2標準）**: wait → saveContextModel2DB → incoming-classifier → [acceptance_times] → 冒頭TTS
   - 非通知着信を冒頭アナウンスの前に排除できる
   - 案件によりイレギュラーな順序が必要な場合は手動で変更する
3. 全STT入力にリトライを設定（**PDFに記載があればその回数、記載がなければ2回**。実績: 2回が多数、3回も存在）
4. リトライ上限で終話_失敗 or 切断 or 次の質問へ進む（Section 4 の prompt_false 3パターン体系を参照）
5. タイムアウト・エラー時のフォールバックが必ず存在すること
6. 全TTS/STTに save2db サブモジュールを接続
7. AmiVoice内蔵RAGは使わない。External Integration の RAG を使う
8. STT入力種別に応じて profile_words に辞書単語を設定
9. 個人情報聴取サブフローはリファレンスを使用
10. 電話番号聴取は incoming-classifier で携帯/固定分岐
11. 全サブフロー出口に結果返却スクリプトモジュールを配置
12. 全終話パスで saveCompletionFlag2db → TTS → Disconnect の順
13. OpenAIプロンプトはフローJSON内に直接記述
14. OpenAI の params.module は出力元モジュールを必ず指定（**同フロー内の実在モジュール名**と完全一致すること。他フローのモジュール名不可）
15. acceptance_times: true のみ冒頭アナウンスに進む
16. RAGはサブフロー化して配置
17. Scriptモジュールの値取得: `$runner.getModuleResult()` 推奨
18. はい/いいえ二択質問は原則 DTMF AmiVoice STT Input を使用する（AmiVoice Speech to Text のみは不可）
19. 各サブフローの `start` モジュールは当該フローの最初のTTSモジュール名と一致すること（他フローのモジュール名を誤って設定しない）
20. 担当医名は contextName="inquiry" に格納する（"Mydoctor" 等の非標準名は禁止）
21. 診察券なし・代表案内終話の完了フラグは status="2" を設定する（status="0" は真の途中切断のみ）
22. 氏名聴取サブフローに OpenAI 正規化モジュールは不要（STT → Retry → サブフロー終了のシンプル構成とする）
23. **モジュール集約の原則（DRY原則）** — 以下の両条件を満たすモジュール群は1つに集約し、ContextMatchRouterで前後を制御する（下記「モジュール集約ルール」参照）
24. **incoming-classifierはフロー内で1つのみ使用する**（冒頭チェーンに配置）。SMS送信判定など終話前の電話番号種別分岐には incoming-classifier を追加せず、電話番号サブフローが保存した phonetype context の返り値を ContextMatchRouter で参照して分岐する

### モジュール集約ルール（DRY原則）

#### 集約の判定基準

以下の**両条件を同時に満たすモジュール群**は1つに集約する：

1. **TTSプロンプトが完全に同一**（文言・読み上げ内容が同じ）
2. **保存するcontextName・contextValue（またはstatus）が同一**

どちらか一方でも異なる場合は集約しない。

#### 集約パターン早見表

| ケース | 集約前（冗長） | 集約後（正しい） |
|---|---|---|
| 複数ルートが同じ終話アナウンスで終わる | 予約終話TTS・変更終話TTS・キャンセル終話TTS を別々に定義 | 終話TTS を1つ定義し、ContextMatchRouterで振り分け |
| 複数ルートが同じ代表案内/エラーTTSに遷移する | 代表転送アナウンスを複数配置 | 代表転送アナウンスを1つに集約、各ルートからそこへ遷移 |
| 複数用件で同じサブフロー（氏名・生年月日・電話番号）を呼ぶ | Jump_氏名_予約・Jump_氏名_変更・Jump_氏名_キャンセルを別々に定義 | Jump_氏名を1つ定義、ContextMatchRouterで呼び出し元を管理 |
| 複数ルートが同じ完了フラグ+Disconnectで終わる | CompletionFlag_予約・CompletionFlag_変更などを別々に定義 | statusの種類ごとに1つに統合し、ContextMatchRouterで分岐 |

#### ContextMatchRouterによる集約の実装例

```
【冗長な設計（VFB典型）】
予約ルート → 終話_予約(TTS) → Flag_予約 → Disconnect_成功
変更ルート → 終話_変更(TTS) → Flag_変更 → Disconnect_成功
キャンセルルート → 終話_キャンセル(TTS) → Flag_キャンセル → Disconnect_成功
※ 全て同じTTSプロンプト・同じstatus="1" なのに3セット生成

【集約した設計（Human正解）】
予約ルート ─┐
変更ルート ──→ 終話アナウンス(TTS×1) → Flag_完了(CompletionFlag×1, status="1") → Disconnect(×1)
キャンセルルート ─┘
※ ContextMatchRouterで「どの用件で終了したか」を保持しつつ、共通終話パスに集約
```

#### 集約できないケース（注意）

- 同じTTS文言でも **statusが異なる**場合（例: 正常終了=1・代表案内=2 → 別途定義が必要）
- 同じTTS文言でも **SMS送信フラグ（smsFlag）が異なる**場合
- **分岐後に異なる処理**が続く場合（一時的に同じ箇所を通るだけ）

### 着信分類（incoming-classifier）ルール

冒頭チェーン内で着信電話番号を分類し、非通知のみ終話に誘導する。

| 分類 | 遷移先 | 理由 |
|---|---|---|
| 非通知 | `終話_非通知` → Disconnect | 折り返し不可のため受け付けない |
| 海外 | 次のモジュール（受付継続） | 受け付ける |
| その他 | 次のモジュール（受付継続） | 受け付ける |
| 通常着信 | 次のモジュール（受付継続） | 受け付ける |

**非通知のみ終話。海外・その他は受付フローに続ける。**

---

### .bivr エクスポート形式

ZIPアーカイブ（拡張子 `.bivr`）:
```
{名前}.bivr
└── flows/
    └── @flow_{URLエンコード済みフロー名}.txt
```

---

## 5. Property.md ルール

### フォーマット

```
{モジュール名}.prompt={tts_g:テキスト}
```

### モジュール名との完全一致が必須

- 正: `冒頭.prompt={tts_g:...}` ← モジュール名「冒頭」
- 誤: `tts_冒頭.prompt=...` (プレフィックス不一致)

### 必須セクション

1. **冒頭.prompt**: 冒頭アナウンス
2. **終話_非通知.prompt**: 非通知終話
3. **終話_失敗.prompt**: 聴取失敗終話
4. **amivoice設定群**: uri, language, engine, silent_detection_ms, timeout_ms, probability, detection_flag, save_log, keep_filter_token
5. **API URL群**: office_id, pbx.db.name, context.settings.url, acceptance_times.url, rag_ssml.url, openAI_generate.url
6. **RAG設定群**: speech.rag.url, speech.rag.connect_timeout, speech.rag.request_timeout, speech.rag.credibility

### 拡張URLフィールド（施設によって追加）

以下は施設の設定に応じて追加されるURLフィールド（pair_11実績）：

| キー | 用途 | prod値 |
|---|---|---|
| `drjoy.save.url` | 予約情報保存API | `https://reserve.drjoy.jp/api/anonymous/dr/ha/brekeke-booking-ai` |
| `get-intonation-from-drjoy.url` | イントネーション取得API | `https://reserve.drjoy.jp/api/anonymous/dr/ha/brekeke-replace-intonation` |
| `phone_2_name.url` | 電話番号→氏名変換API | `https://reserve.drjoy.jp/api/anonymous/dr/ha/phone-to-name` |

### Property.mdのスコープ（メインフロー＋サブフロー共通）

**メインフローの Property.md に記載した TTS プロンプトは、サブフロー内の同名 TTS モジュールにも自動的に反映される。**
したがって、サブフローの TTS プロンプト（`患者_氏名.prompt` 等）もメインフローの Property.md に記載する。
Jump to Flow の `properties` パラメータにサブフロー用プロンプトを個別転送する必要はない。

> **バリデーター注意**: PROP-001 はメインフロー内の TTS モジュールだけでなく、サブフロー内の TTS モジュール名も照合対象に含めること。メインフローに存在しなくてもサブフローに存在すれば正常。

### Property.mdに含まれない情報

- OpenAIプロンプト（.bivr内に直接記述）
- profile_words（.bivr内に直接記述）
- retry prompt_true / prompt_false（.bivr内に直接記述）

---

## 6. バリデーターエラーコード

### VFBポート（71項目）

| コード | 重要度 | 内容 |
|---|---|---|
| S-001 | CRITICAL | 必須フィールド(name/start/modules)欠落 |
| S-002 | CRITICAL | フロー名が グループ名$フロー名 形式でない（structural_fixer で自動修正） |
| S-003 | CRITICAL | startモジュールが modules内に存在しない |
| T-001 | CRITICAL | 遷移先モジュールが modules内に存在しない |
| T-002 | WARNING | 孤立モジュール（どこからも参照されない） |
| T-003 | CRITICAL | subs参照先が modules内に存在しない |
| T-004 | CRITICAL | 同一モジュール内のnextラベル重複 |
| STT-000 | CRITICAL | STT nextが最大11スロット超過 |
| STT-001 | CRITICAL | TIMEOUT/ERROR/NO_RESULT遷移先なし |
| STT-002 | CRITICAL | TIMEOUT/ERROR/NO_RESULT遷移先が空 |
| STT-003 | CRITICAL | success遷移 ^.+$ 未定義 |
| STT-004 | CRITICAL | STTに個別パターン含有（OpenAIで分岐すべき） |
| TTS-001 | CRITICAL | TTS next labelが "Next Module" でない |
| TTS-002 | CRITICAL | stop_by_dtmfが "true"/"false"（"Yes"/"No"必須） |
| TTS-003 | INFO | promptが {tts_g:} 形式でない |
| OAI-001 | CRITICAL | generate_by_OpenAI の module が空 |
| OAI-002 | CRITICAL | module参照先が modules内に存在しない |
| OAI-003 | WARNING | promptTTS に値が設定されている |
| OAI-004 | WARNING | next先頭3スロットの順序不正 |
| R-001 | CRITICAL | Retry に condition='true' なし |
| R-002 | CRITICAL | Retry に condition='false' なし |
| R-003 | CRITICAL | true の label が 'Retry' でない |
| R-004 | CRITICAL | false の label が 'No more' でない |
| R-005 | WARNING | retry_count 未設定 |
| SB-001 | WARNING | TTS/STTに save2db 未接続 |
| SB-002 | CRITICAL | save2db に next遷移が設定されている |
| CTX-010 | CRITICAL | saveContext2DB の contextName が空 |
| CTX-011 | CRITICAL | saveContext2DB の contextValue が空 |
| CTX-013 | CRITICAL | contextValue に #data# 使用（禁止） |
| CTX-012 | CRITICAL | saveCompletionFlag2db の status が空 |
| CTX-014 | WARNING | fields がminified（目視確認困難） |
| CTX-016 | CRITICAL | clinicalDepartment の displayType が DEPARTMENT でない |
| CTX-017 | CRITICAL | 重複不可 displayType が複数使用 |
| COMP-001 | CRITICAL | status "0"/"5" は使用禁止 |
| N-001 | CRITICAL | モジュール名に環境依存文字 |
| N-002 | WARNING | モジュール名に括弧 |
| N-003 | WARNING | モジュール名にスペース |
| DTMF-001 | CRITICAL | prompt に {recstart} なし |
| DTMF-002 | WARNING | max_dtmf_length 未設定 |
| DTMF-003 | WARNING | retry が "0" |
| DTMF-004 | WARNING | termdtmf/remove_term/stop_play_when_speech 未設定 |
| FLOW-001 | CRITICAL | startモジュールが wait でない |
| FLOW-002 | CRITICAL | 冒頭チェーンに saveContextModel2DB なし |
| FLOW-004 | CRITICAL | Custom Jump to Flow の flowname が空 |
| FLOW-005 | INFO | Custom Jump to Flow の properties が空（メインフローの Property.md がサブフローにも反映されるため、通常は問題なし） |
| FLOW-006 | WARNING | STT直前にTTS/Retryなし |
| FLOW-007 | CRITICAL | 冒頭チェーンに冒頭アナウンス（TTSモジュール）が存在しない |
| FLOW-008 | CRITICAL | incoming-classifier がフロー内に2つ以上ある |
| MM-001 | CRITICAL | matchingmethod が文字列または未設定（int型必須） |
| S-004 | CRITICAL | モジュールに必須フィールド（name/description/matchingmethod/type/params/next/subs/layout）が欠落 |
| PROMPT-001 | CRITICAL | next分岐ラベルがprompt出力仕様にない |
| PROMPT-002 | WARNING | prompt出力仕様にnext対応なし |
| PROMPT-003 | CRITICAL | OpenAI prompt が空欄 |
| PROMPT-004 | WARNING | ワイルドカード分岐でNO_RESULT記述なし |
| PROMPT-005 | CRITICAL | OpenAI prompt に `# Role` セクションがない（VFB品質基準 P-3a） |
| PROMPT-006 | CRITICAL | OpenAI prompt に `# Context` セクションがない（VFB品質基準 P-3b） |
| PROMPT-007 | WARNING | OpenAI prompt にインジェクション防御セクションがない（VFB品質基準 P-4c） |
| REACH-001 | CRITICAL | startから到達不能モジュール |
| REACH-002 | WARNING | 到達可能なDisconnectなし |
| REACH-003 | WARNING | Retry Counter非経由ループ |
| LAYOUT-001 | CRITICAL | 大半のlayoutが(0,0) |
| LAYOUT-002 | WARNING | 一部layoutが(0,0) |
| LAYOUT-003 | WARNING | 横並びレイアウト |
| LAYOUT-004 | WARNING | モジュール座標の重なり（x:200px/y:150px 未満の間隔） |
| LAYOUT-005 | WARNING | 終話モジュール（完了フラグ）がフロー上部に配置されている |
| PH-001 | CRITICAL | 電話番号サブフローに incoming-classifier なし |
| PH-002 | CRITICAL | 携帯判別スクリプトなし |
| SCR-001 | WARNING | スクリプト名が script_ で始まらない |
| SCR-002 | CRITICAL | サブフローに結果返却スクリプトなし |
| SF-TERM-001 | CRITICAL | return方式なのにDisconnectあり |

### bivr-checker 固有（6項目）

| コード | 重要度 | 内容 |
|---|---|---|
| PROP-001 | CRITICAL | Property.mdプロンプトキーとTTSモジュール名不一致（メインフロー＋サブフロー両方を照合対象とすること） |
| PROP-002 | CRITICAL | Property.md必須セクション欠落 |
| PROP-003 | WARNING | 環境URL不一致（demo/prod混在） |
| PROP-004 | WARNING | amivoice設定欠落 |
| CROSS-001 | CRITICAL | フローJSON-Property.md間モジュール名不一致 |
| CROSS-002 | CRITICAL | サブフローflowname不一致 |
| CROSS-003 | CRITICAL | Jump to Flow の参照先サブフローが同ディレクトリに存在しない（サブフロー欠落） |

---

## 7. デフォルト値カタログ

参照: `reference/defaults.json`

### AmiVoice設定（全ペア共通）

| パラメータ | 標準値 |
|---|---|
| uri | `ws://10.0.20.11:8000/ws` |
| language | `ja` |
| engine | `入力汎用` |
| keep_filter_token | `true` |
| silent_detection_ms | `2000` |
| timeout_ms | `30000` |
| probability | `0.6`（標準。施設によって0.57〜0.7の範囲で微調整。pair_11は0.63） |
| detection_flag | Property.md側: `検出しない` を設定。**モジュール側: 必ず `"デフォルト"` を明示設定する**（`"検出しない"` は禁止、空欄/未設定も禁止。VFBのUIで「デフォルト」が選択された状態にする） |
| save_log | `false` |

### saveContextModel2DB — fields 構造

`params.fields` は以下の属性を持つオブジェクトの配列をJSON文字列化したもの（indent=2 必須）。

| 属性 | 型 | 必須 | 説明 |
|---|---|---|---|
| `contextName` | string | ✅ | 内部キー（英語） |
| `contextNameJp` | string | ✅ | 管理画面の表示名（日本語） |
| `displayType` | string | ✅ | 表示・入力タイプ（下表参照） |
| `rangeValues` | array | ✅ | 選択肢一覧（選択肢なしは `[]`） |
| `editable` | boolean | ✅ | 管理画面で編集可能か |
| `deletable` | boolean | ✅ | 管理画面で削除可能か |
| `itemDefault` | boolean | ✅ | 標準フィールドか（`true`=標準、`false`=案件固有） |

### displayType 一覧と制約

| displayType | 用途 | 複数使用 |
|---|---|---|
| `TEXT` | テキスト自由入力 | ✅ 複数可 |
| `NUMBER` | 数値 | ✅ 複数可 |
| `DATE` | 日付 | ✅ 複数可 |
| `CLASSIFICATION` | 用件区分（`classification` 専用） | ❌ フロー内1つのみ |
| `DEPARTMENT` | 診療科（`clinicalDepartment` 専用） | ❌ フロー内1つのみ |
| `DATE_OF_BIRTH` | 生年月日 | ❌ フロー内1つのみ |
| `PHONE_NUMBER` | 連絡先電話番号（編集可） | ❌ フロー内1つのみ |
| `PHONE_NUMBER_CALL` | 着信元電話番号（編集不可） | ❌ フロー内1つのみ |
| `STATUS` | 完了ステータス | ❌ フロー内1つのみ |

### rangeValues 形式

```json
// 選択肢あり（通常案件）
"rangeValues": [{"value": "予約", "order": 1}, {"value": "変更", "order": 2}]

// 選択肢なし
"rangeValues": []

// スマート面会案件のみ id フィールドを追加
"rangeValues": [{"id": "1", "value": "選択肢名", "order": 1}]
```

### 標準フィールド（デフォルト12フィールド — 赤字以外は変更不可）

以下の12フィールドは全案件で必須。**赤字（可変）はclassification.rangeValuesとclinicalDepartment.rangeValuesのみ**。それ以外の属性値は固定で変更不可。

| # | contextName | contextNameJp | displayType | editable | deletable | itemDefault | rangeValues |
|---|---|---|---|---|---|---|---|
| 1 | `classification` | 区分 | CLASSIFICATION | true | false | true | 🔴 案件ごとに設定（id不要、order+valueのみ） |
| 2 | `patientName` | 患者名 | TEXT | true | false | true | [] |
| 3 | `medicalCardNumber` | 診察券番号 | NUMBER | true | false | true | [] |
| 4 | `clinicalDepartment` | 診療科 | DEPARTMENT | true | false | true | 🔴 案件ごとに設定（デフォルト: [IVRセンター]） |
| 5 | `patientDateOfBirth` | 生年月日(和暦) | DATE_OF_BIRTH | true | false | true | [] |
| 6 | `reason` | 理由 | TEXT | true | false | true | [] |
| 7 | `reservationDate` | 予約日 | DATE | true | false | true | [] |
| 8 | `telephoneNumber` | 電話番号 | PHONE_NUMBER_CALL | false | false | true | [] |
| 9 | `additionalPhoneNumber` | 連絡先電話番号 | PHONE_NUMBER | true | false | true | [] |
| 10 | `status` | 状態 | STATUS | true | false | true | [途中切断(0)/未処理(1)/代表案内(2)/転送(3)/時間外(6)] ※id+order+value形式 |
| 11 | `callId` | 通話ID | NUMBER | true | true | false | [] |
| 12 | `dateOfCall` | 入電日時 | DATE | false | false | true | [] |

> **重要**: rangeValuesの形式が2種類ある:
> - classification/clinicalDepartment等: `{"order": 1, "value": "xxx"}` （idなし）
> - statusのみ: `{"id": "0", "order": 0, "value": "途中切断"}` （id+order+value）

### 案件固有フィールド（デフォルトの後に追加）

追加フィールドのフォーマット:
- `deletable`: true
- `itemDefault`: false
- 他の属性は用途に応じて設定

| contextName例 | contextNameJp | displayType | 用途 |
|---|---|---|---|
| `reservation_change_date` | 変更希望日 | DATE | 変更ルートの希望日 |
| `summary_matter` | 用件の要約をフリーテキストで格納 | TEXT | 自由記述の要約 |
| `clinicalDepartment2` | 診療科2 | TEXT | 2科目の診療科 |
| `inquiryContent` | 問合せ内容 | TEXT | 確認ルートの問合せ内容 |
| `phonetype` | 電話種別 | TEXT | 携帯/その他の判別 |

### 除外フィールド（saveContextModel2DB に含めない）

| フィールド | 理由 |
|---|---|
| `endpoint` | `saveCompletionFlag2db` 経由で管理 |
| `smsFlag` | `saveCompletionFlag2db` 経由で管理 |

### 状態フラグ

| 状態 | status値 |
|---|---|
| 途中切断 | 0 |
| 未処理 | 1 |
| 代表案内 | 2 |
| 転送 | 3 |
| 時間外 | 6 |

### DTMF桁数

| 用途 | max_dtmf_length |
|---|---|
| 用件選択 | 1 |
| 電話番号 | 11 |
| 生年月日 | 8 |
| デフォルト | 10 |

---

## 7a. ContextMatchRouter 設定ルール

### 概要

`drjoy^Context Logic$ContextMatchRouter` は、参照モジュールの出力値をインデックスにマッピングして分岐するモジュール。

### params 設定（単一モジュール参照の場合も全フィールド必須）

参照するモジュールが1つだけの場合でも、**`module1Name` と `module2Name` の両方に同じモジュール名を入力する**。

```json
{
  "module1Name": "OpenAI_用件",
  "module2Name": "OpenAI_用件",
  "module1Value1": "予約",
  "module1Value2": "変更・キャンセル",
  "module1Value3": "その他確認",
  "module1Value4": "", "module1Value5": "", ..., "module1Value10": "",
  "module2Value1": "予約",
  "module2Value2": "変更・キャンセル",
  "module2Value3": "その他確認",
  "module2Value4": "", "module2Value5": "", ..., "module2Value10": ""
}
```

**ルール:**
- `module1Name` と `module2Name` は**常に同じ値**（片方だけの設定は不可）
- 各組み合わせ（Value1〜10）の `module1ValueN` と `module2ValueN` も**同じ値をセット**
- 使用しないスロット（Value4〜10 など）は空文字 `""` で埋める

### next 条件フォーマット

| 分岐 | condition | 意味 |
|---|---|---|
| 1番目の値にマッチ | `^1$` | module1Value1 かつ module2Value1 が一致 |
| 2番目の値にマッチ | `^2$` | module1Value2 かつ module2Value2 が一致 |
| N番目の値にマッチ | `^N$` | インデックスベース（値そのものではない） |
| デフォルト | `^.*$` | どれにも一致しない場合のフォールバック |

### next スロット数

最大12スロット（使用しないスロットは `{"condition": "", "label": "", "nextModuleName": ""}` で埋める）

### matchingmethod

`1` 固定（Retry Counter のみ `0`）

### モジュール共通必須フィールド（Brekeke PBX要件）

全モジュールは以下のフィールドを必ず持つこと。欠落するとBrekekeへのアップロードが失敗する。

| フィールド | 型 | 値 |
|---|---|---|
| `name` | string | モジュール名（modulesのキーと同一） |
| `description` | string | `""` 空文字 |
| `matchingmethod` | **integer** | `1`（Retry Counterのみ `0`）。文字列 `"1"` は不可、必ず数値型 |
| `type` | string | モジュールタイプ |
| `params` | object | モジュール固有パラメータ |
| `next` | array | 遷移先配列（モジュールタイプごとに固定スロット数） |
| `subs` | array | サブモジュール配列（モジュールタイプごとに固定スロット数） |
| `layout` | object | `{"x": number, "y": number}` |

### params 値の型保持ルール（Brekeke PBX要件 — 最重要）

**`params` 内の値は、元のJSON型を絶対に変更してはならない。** 型が変わるとBrekekeへのインポートが失敗する。

| ルール | 正しい例 | 誤った例（インポート失敗） |
|---|---|---|
| 文字列は文字列のまま | `"smsFlag": "1"` | `"smsFlag": 1` ← int化禁止 |
| 文字列は文字列のまま | `"status": "2"` | `"status": 2` ← int化禁止 |
| 文字列は文字列のまま | `"retry_count": "2"` | `"retry_count": 2` ← int化禁止 |
| 整数は整数のまま | `"matchingmethod": 1` | `"matchingmethod": "1"` ← str化禁止 |

**修正スクリプトで値を変更する際は、元の型を必ず確認してから同じ型で代入すること。**
Python実装例:
```python
# NG: 型が変わる
mod["params"]["smsFlag"] = -1          # str→int になる

# OK: 元の型(str)を維持
mod["params"]["smsFlag"] = "-1"        # str→str のまま
```

### next / subs スロット数（モジュールタイプ別）

| モジュールタイプ | nextスロット数 | subsスロット数 |
|---|---|---|
| `@General$Script` | 12 | 0 |
| `drjoy^Context Logic$ContextMatchRouter` | 10 | 3 |
| `drjoy^AmiVoice$Speech to Text` | 11 | 3 |
| `drjoy^External Integration$DTMF AmiVoice STT Input` | 11 | 3 |
| `drjoy^External Integration$generate_by_OpenAI` | 10 | 3 |
| `drjoy^Text To Speech$Speech Retry Counter` | 2 | 3 |
| `drjoy^Text To Speech$Text to speech` | 1 | 3 |
| `drjoy^Text To Speech$Re-confirmation node data` | 1 | 3 |
| `drjoy^Persistence$saveCompletionFlag2db` | 1 | 3 |
| `drjoy^Persistence$saveContext2DB` | 1 | 3 |
| `drjoy^Persistence$saveContextModel2DB` | 1 | 3 |
| `drjoy^Persistence$save2db` | 0 | 0 |
| `drjoy^External Integration$acceptance_times` | 4 | 3 |
| `drjoy^Incoming$incoming-classifier` | 5 | 3 |
| `drjoy^Custom Module$Custom Jump to Flow` | 1 | 3 |
| `Custom$wait` | 1 | 3 |
| `@IVR$Disconnect` | 0 | 0 |

> **重要**: 使用しないスロットは `{"condition": "", "label": "", "nextModuleName": ""}` / `{"moduleName": "", "label": ""}` で埋める。スロット数がタイプごとの規定値と異なるとBrekekeへのアップロードが失敗する。

### ContextMatchRouter params キー順序

paramsのキーは以下の**交互配置**でなければならない（Brekeke PBX要件）:

```
module1Name, module2Name,
module1Value1, module2Value1,
module1Value2, module2Value2,
...
module1Value10, module2Value10
```

> `module1Value1〜10` をまとめてから `module2Value1〜10` を並べる形式は**不可**。必ず1と2を交互に配置すること。

---

## 7b. レイアウト座標ルール（voicebot-flow-builder/docs/specs/layout_spec.md より）

### 基本原則

- **x軸**: 右が正。分岐パスごとに横にずれる
- **y軸**: 下が正。フローの進行方向（**主経路は必ず上から下へ**）
- LAYOUT-003 判定条件: `x_range > 2000px AND y_range < modules×100px` → 両方満たすと警告
- **y_range を modules×100 以上にすること**が必須（83モジュールなら y_range ≥ 8300px）
- **モジュール重なり禁止**: 同一座標に複数モジュールを配置しない。最低でも x方向 200px または y方向 150px の間隔を確保する
- **終話モジュール（完了フラグ→END TTS→Disconnect）はフロー最下部に配置する**: 通話フローは上から下に読むため、終話はy座標が最大付近であること。冒頭付近（y < y_range × 0.3）に終話モジュールを配置しない（非通知・時間外の即時終話のみ例外可）

### 冒頭チェーン（固定座標）

| モジュール | x | y |
|---|---|---|
| 冒頭 (wait) | 0 | 0 |
| コンテキスト設定 | 0 | 240 |
| 着信分類 | 0 | 480 |
| 受付時間判定 | 0 | 720 |
| 冒頭アナウンス（true遷移先） | 0 | 960 |

### 会話ステップ内相対配置

TTS座標を基準として:

| モジュール | Δx | Δy |
|---|---|---|
| TTS | 0 | 0 |
| STT/DTMF | 0 | +220 |
| OpenAI | 0 | +460 |
| Retry | -280 | +460 |
| save2db | -280 | +220 |

### ステップ間隔

- **標準ステップ間**: Δy = 800（前ステップTTSから次ステップTTSまで）
- **Re-confirmationを含むステップ**: Δy = 1200以上

### 分岐パス配置

| パス種別 | 推奨x |
|---|---|
| メインパス | 0 |
| 右サブパス（検査・現在予約日等） | +800〜+1200 |
| さらに右（確認内容・フリーワード等） | +1600〜+2200 |
| 左サイドブランチ（時間外・失敗終話） | -900〜-1800 |
| 右サイドブランチ（非通知・代表案内） | +900〜+1800 |

---

## 8. OpenAIプロンプトルール

### 必須セクション（4本柱）

1. **# Role**: AIの役割定義
2. **# Context**: 入力データの文脈説明
3. **# 出力仕様**: 出力フォーマットと選択肢（next分岐条件と完全一致）
4. **# セキュリティ**: プロンプトインジェクション防御

### 基本ルール

- promptはフローJSON内 `params.prompt` に直接記述（IVRプロパティではない）
- `params.module` は出力元STT/OpenAIモジュール名を必ず設定
- `params.promptTTS` は必ず空欄
- 出力値と next 分岐条件の完全一致が必須

### プロンプト網羅性ルール（最重要）

プロンプトは**直前のTTSで発話した質問内容**を起点に設計する。発話に対して電話口で返ってくる可能性のある回答パターンを網羅的に予測し、すべての分岐に対応できるように記述すること。

**設計手順:**

1. 直前のTTSで何を質問しているかを確認する
2. その質問に対して実際の患者・利用者が**口頭でどのように答えるか**を複数パターン列挙する
3. 表記揺れ・言い回しの違い・省略形・同義語を `# Context` または `# 出力仕様` に明示する
4. 各分岐に**漏れなく**マッピングする。拾えないパターンが残らないようにする

**悪い例（簡素すぎる）:**
```
# 出力仕様
- 予約
- 変更
- キャンセル
```

**良い例（網羅的）:**
```
# Context
患者が「ご用件をお聞かせください」という質問に対して回答した音声テキストです。

# 出力仕様
以下のいずれか1語のみ出力してください。
- 予約：新規予約・初診予約・診てほしい・受診したい・予約を取りたい 等
- 変更：予約変更・日程変更・日にちを変えたい・時間を変えたい 等
- キャンセル：予約取消・キャンセルしたい・やめたい・行けなくなった 等
- その他：上記に当てはまらない・複数の意図が混在 等
```

> **判断基準**: プロンプトだけを見て「この回答がどの分岐に入るか」が一意に決まるか。曖昧な場合は記述が不足している。

### プロンプト種別

| 種別 | 用途 |
|---|---|
| 用件分類 | 入力テキストを用件カテゴリに分類 |
| 診療科判定 | 入力テキストから診療科を抽出・対象判定 |
| 肯定否定判定 | 復唱時の「はい/いいえ」判定 |
| 日付正規化 | 音声入力の日付をYYYYMMDD形式に変換 |
| 氏名正規化 | 音声入力の氏名をカタカナに変換 |
| 聴取不可出力 | リトライ上限時に「聴取不可」を強制出力 |

---

## 9. AmiVoice辞書ルール（profile_words）

### フォーマット

```
"表記 よみがな\n表記 よみがな\n..."
```

STTモジュールの `profile_words` パラメータに直接埋め込み。

> **数字は必ず半角**で記述すること（1, 2, 3 ...）。全角数字（１, ２, ３）は使用禁止。
> AmiVoiceは半角数字のみ正しく認識するため、辞書内の数字表記は全て半角に統一する。

---

### 設計の基本原則

#### 原則1: 直前のTTSが発話する内容から逆算して設計する

profile_words は「AmiVoiceが認識しやすい単語」ではなく、「**そのSTTモジュールに入力されうる全ての発話**」を起点に設計する。

**設計手順:**
1. 直前のTTSモジュールが何を質問しているかを確認する
2. その質問に対して電話口の患者/利用者が**口頭でどのように返答するか**を網羅的に列挙する
3. 各回答パターンを「表記 よみがな」の形式で辞書に追加する
4. 表記ゆれ（漢字/ひらがな/カタカナ）・省略形・同義語・方言を含める

**悪い例（簡素すぎる）:**
```
予約 よやく
変更 へんこう
```

**良い例（TTS「ご用件をお聞かせください」に対する辞書）:**
```
予約 よやく
お願いしたい おねがいしたい
予約したい よやくしたい
受診したい じゅしんしたい
診てほしい みてほしい
変更 へんこう
予約変更 よやくへんこう
日程変更 にっていへんこう
日にちを変えたい ひにちをかえたい
キャンセル きゃんせる
取消 とりけし
やめたい やめたい
行けなくなった いけなくなった
確認 かくにん
聞きたい ききたい
わからない わからない
```

#### フィラーパターン体系（標準14種 × 語尾バリエーション）

人間版では各キーワードに対して**フィラー前置きパターン**と**語尾バリエーション**を組み合わせて大量登録する。教師データ（pair_01帯広第一病院）で確認済みの体系を以下に示す。

**標準フィラー前置き（14種）:**
```
あ / あー / あの / あのー / え / えー / えっと / えーと / ん / んー / はい / ま / まー / そうですね
```

例（キーワード「よやく」）:
```
予約 あよやく
予約 あーよやく
予約 あのよやく
予約 えよやく
予約 えーよやく
予約 えっとよやく
予約 んよやく
予約 はいよやく
予約 まよやく
予約 そうですねよやく
```

**語尾バリエーション（主要20種）:**
```
キーワード+です / +で / +になります / +なんですが / +なんだけど / +だけど / +だよ
+ね / +さ / +か / +が / +の / +に / +を / +は / +や / +でして / +ですけれども / +なんです / +ですけども
```

> **実装指針**: 全語尾を網羅する必要はない。TTS発話を見てユーザーが答えそうなパターンに絞って登録する。少なくとも「フィラー10種 × キーワード」と「キーワード単独」は必須。

#### 原則2: 頭落ち（utterance先頭の欠損）を考慮する

音声認識では発話の先頭音が切れる「頭落ち」が頻繁に発生する。これに対処するため、**先頭音節が欠落した状態でも認識できるよう**、省略形・語尾のみの単語を辞書に追加する。

**頭落ち対処の具体例:**

| 本来の発話 | 頭落ちパターン | 辞書追加 |
|---|---|---|
| `よやく`（予約） | `やく` | `やく やく` を追加 |
| `へんこう`（変更） | `んこう` / `こう` | `変更 へんこう` + 語尾の形も考慮 |
| `いちがつ`（一月） | `ちがつ` / `がつ` | 月名は複数の読み方を登録 |
| `ついたち`（一日） | `いたち` | 特殊読みは念入りに登録 |
| `しょうわ`（昭和） | `ょうわ` | 元号は略称も追加（きょうわ, きょうは 等の誤認識パターンも） |

**頭落ち辞書の作成方法:**
- 2音節以上の単語は、先頭1〜2音が欠落した形を想定して登録
- 特に「よ」「ご」「お」等の敬語・丁寧語の先頭音は落ちやすい（例: `ご予約` → `予約` / `よやく`）
- 長い複合語（`予約変更`）は構成要素ごとに分割登録（`予約 よやく`・`変更 へんこう` を別行で登録）

#### 原則3: モジュール種別ごとの方針

| モジュール種別 | profile_words 設計方針 |
|---|---|
| `drjoy^AmiVoice$Speech to Text` | 充実した辞書を設定。入力種別に応じて下記「入力種別別ガイド」を適用 |
| `drjoy^External Integration$DTMF AmiVoice STT Input` | 数字（ DTMFキー）が主入力のため辞書は最小限。選択肢の読み上げ語（「いち」「に」等）と誤入力パターンのみ |
| `drjoy^Text To Speech$Re-confirmation node data` | 復唱確認のSTT入力 → 肯定否定辞書のみ設定 |

---

### 入力種別別 設計ガイドライン

#### 1. 用件・区分（diagnosticフロー冒頭）

TTS例:「ご用件をお聞かせください。予約は1を、変更は2を、キャンセルは3を、その他ご確認は4をお押しください。」

**DTMF+STT の場合**: 選択肢数字の読み仮名のみ登録（`一 いち\n二 に\n三 さん`）

**STT のみの場合**: 選択肢ごとの言い回しを網羅的に登録
```
予約 よやく
お願いしたい おねがいしたい
受診したい じゅしんしたい
診てほしい みてほしい
初診 しょしん
変更 へんこう
予約変更 よやくへんこう
日程変更 にっていへんこう
日にちを変えたい ひにちをかえたい
キャンセル きゃんせる
取消 とりけし
やめたい やめたい
行けなくなった いけなくなった
確認 かくにん
聞きたい ききたい
```

#### 2. 氏名（patientName）

**辞書**: `reference/dictionaries/profile_words_name.txt` をベースに施設所在地の頻出苗字を追加

**頭落ち対処**: 苗字の先頭音は落ちやすい（`たなか` → `なか`）。ただし氏名は組み合わせが膨大なため、OpenAIで正規化することを前提とし、辞書登録よりもOpenAIプロンプトの正規化ルールを充実させる

#### 3. 生年月日（patientDateOfBirth）

**辞書**: `reference/dictionaries/profile_words_dob.txt` をベースに使用

**必須登録:**
```
令和 れいわ
平成 へいせい
昭和 しょうわ
大正 たいしょう
```

**頭落ち対処（元号）:**
```
れいわ れいわ
昭和 きょうわ
昭和 きょうは
```
（「しょうわ」が「きょうわ」「きょうは」に誤認識されるパターンが教師データで確認済み）

**日付の特殊読み（必須）:**
```
一日 ついたち
二日 ふつか
三日 みっか
四日 よっか
八日 ようか
十日 とおか
二十日 はつか
```

#### 4. 診療科（clinicalDepartment）

**辞書設計の手順:**
1. PDFの診療科一覧から全科名を抽出
2. 各科名の「読み仮名」「省略形」「類義語」を登録
3. 「対象外」の科名も登録する（対象外→代表案内に振るためにまず認識する必要があるため）

**施設固有の辞書例（pair_06 四谷メディカルキューブ）:**
```
消化器外科 しょうかきげか
一般外科 いっぱんげか
外科 げか
消化器内科 しょうかきないか
内科 ないか
整形外科 せいけいげか
整形 せいけい
泌尿器科 ひにょうきか
婦人科 ふじんか
乳腺外科 にゅうせんげか
乳腺 にゅうせん
皮膚科 ひふか
眼科 がんか
耳鼻科 じびか
耳鼻咽喉科 じびいんこうか
放射線科 ほうしゃせんか
検査 けんさ
```

**頭落ち対処:**
```
消化器外科 ょうかきげか
整形外科 えいけいげか
```

#### 5. 復唱確認（Re-confirmation / 肯定否定分岐）

**辞書**: `reference/dictionaries/profile_words_yes_no.txt` をそのまま使用

基本形に加えて、**頭落ちパターン**を必ず追加する（教師データ pair_01 帯広第一病院で確認済み）:

```
はい はい
はい はあ
はい あい
はい い
はーい はーい
ええ ええ
そうです そうです
そうです おうです
そうです うです
合ってます あってます
あってます ってます
大丈夫です だいじょうぶです
だいじょうぶです いじょうぶです
だいじょうぶ じょうぶ
お願いします おねがいします
おねがいします ねがいします
よろしいです よろしいです
いいえ いいえ
いいえ いい
違います ちがいます
ちがいます がいます
違う ちがう
間違い まちがい
まちがいます ちがいます
```

> **注意**: 「はい」の頭落ち（「あい」「い」）は特に重要。短い語ほど先頭音が落ちやすい。`いいえ` は「いい」へ、`違います` は「がいます」へ頭落ちする。

#### 6. 予防接種ワクチン種別（施設固有）

TTS例:「接種を希望されるワクチンをお聞かせください。」

**辞書例（pair_02 入間ハート病院）:**
```
インフルエンザ いんふるえんざ
インフル いんふる
コロナ ころな
新型コロナ しんがたころな
肺炎球菌 はいえんきゅうきん
帯状疱疹 たいじょうほうしん
麻しん ましん
はしか はしか
風しん ふうしん
MR えむあーる
おたふく おたふく
おたふくかぜ おたふくかぜ
混合ワクチン こんごうわくちん
わからない わからない
わかりません わかりません
不明 ふめい
覚えていない おぼえていない
忘れました わすれました
```

#### 7. キャンセル理由（施設固有）

TTS例:「キャンセルの理由をお聞かせください。」

**辞書例（pair_02 入間ハート病院）:**
```
体調不良 たいちょうふりょう
風邪 かぜ
発熱 はつねつ
熱が出た ねつがでた
急用 きゅうよう
仕事 しごと
仕事が入った しごとがはいった
都合が悪い つごうがわるい
コロナ ころな
インフル いんふる
濃厚接触 のうこうせっしょく
家族 かぞく
子供 こども
急病 きゅうびょう
忘れていた わすれていた
交通機関 こうつうきかん
電車が止まった でんしゃがとまった
```

#### 8. 予約日・日程聴取

TTS例:「ご希望の予約日をお聞かせください。」

**辞書例（pair_02）:**
```
予約日 よやくび
現在の予約日 げんざいのよやくび
日付 ひづけ
令和 れいわ
平成 へいせい
昭和 しょうわ
一月 いちがつ
〜十二月 （各月を個別登録）
一日 ついたち
〜三十一日 （特殊読みは個別登録、通常は「にち」形式）
月曜日 げつようび
火曜日 かようび
水曜日 すいようび
木曜日 もくようび
金曜日 きんようび
土曜日 どようび
日曜日 にちようび
わからない わからない
未定 みてい
```

#### 9. 健診コース聴取（健診シナリオ固有）

TTS例:「ご希望のコース名をおっしゃってください。」

**辞書設計の手順:**
1. PDFの健診コース一覧から全コース名を抽出
2. 各コース名の「読み仮名」「省略形」「一般呼称」を登録
3. 施設固有の健康保険種別も必要に応じて登録

**辞書例（pair_01 帯広第一病院）:**
```
人間ドック にんげんどっく
人間ドック どっく
大腸ドック だいちょうどっく
膵臓ドック すいぞうどっく
脳ドック のうどっく
健康診断 けんこうしんだん
健康診断 けんしん
1コース いちこーす
2コース にこーす
3コース さんこーす
4コース よんこーす
協会けんぽ きょうかいけんぽ
生活習慣病予防健診 せいかつしゅうかんびょうよぼうけんしん
一般健診 いっぱんけんしん
節目健診 ふしめけんしん
特定健康診査 とくていけんこうしんさ
特定健康診査 とくていけんしん
乳がん検診 にゅうがんけんしん
精密健診 せいみつけんしん
```

> **健診シナリオでは必須**。VFBは健診コース名を生成しないため、PDFのコース一覧から必ず手動追加する。

---

### VFBが生成しないため必ず手動で設定する辞書

教師データ（pair_01〜10）の横断分析より、VFBはprofile_wordsを**ほぼ生成しない**か、生成しても極めて簡素。以下は必ず手動で充実させること:

| 入力種別 | VFBの生成状況 | 必要な追加 |
|---|---|---|
| 診療科STT | 空白または科名のみ | 省略形・類義語・誤認識パターン |
| 用件/区分STT | 空白または1〜2語 | 全分岐に対応する言い回し（フィラー14種含む）を網羅 |
| ワクチン種別 | 空白 | 施設取り扱いワクチン全種 + 読み仮名 |
| キャンセル理由 | 空白 | 一般的な理由10語以上 |
| 日付聴取STT | 空白 | 元号 + 月日の特殊読み + フィラー前置きパターン |
| 復唱確認STT | 肯定語のみ | 否定語・頭落ちパターン（はあ/あい/おうです等）を追加 |
| 健診コースSTT（健診のみ） | 空白 | 施設全コース名 + 省略形 + 保険種別 |

---

## 10. パイプライン工程

### 修正パイプライン（メイン）

外部チェック結果を受けてVFB出力を修正する。

```
入力: VFB出力(.bivr + Property.md) + チェック結果 + 元PDF
  ↓
1. EXTRACT — .bivr → フローJSON展開
1.7. RETRY PATTERN — Retry Counterのパターン自動分類・修正
2. FIX — チェック結果 + 蓄積パターンに基づく自動修正
3. BUILD — 修正済み .bivr 再構築
4. ACCUMULATE — 修正前後ペア保存 + パターン更新
```

### Stage 1: EXTRACT（extract_bivr.py）
- 入力: `input/{施設名}/*.bivr`（VFB出力）
- 出力: `output/{施設名}/extracted/flows/*.json`

### Stage 1.7: RETRY PATTERN（retry_pattern_fixer.py）
- 入力: フローJSON + 設計書（PDF/md）
- 処理: 各Retry Counterモジュールのprompt_false/遷移先を設計書の仕様に基づきパターンA/B/Cに自動分類・修正
- 出力: 修正済みフローJSON
- パターン判定ルール:
  - パターンC（必須ループ）: 用件/区分など必須聴取項目 → prompt_false=""、false→同じTTS
  - パターンB（失敗終話）: 設計書が明示的に終話を指定した場合 → false→完了フラグ_聴取失敗
  - パターンA（次へ進む）: 上記以外の任意聴取項目（デフォルト） → false→次のステップのTTS
- バリデーター検出: R-006（全Retry同一パターン警告）、R-007（用件/区分のPattern C未適用警告）

### Stage 2: FIX（fixer, Sonnet）
- 入力: フローJSON + Property.md + 外部チェック結果
- 参照: `reference/check_prompt.md`（エラーコード定義）、`reference/defaults.json`、`reference/defaults_overrides/learned_patterns.json`、過去のcorrections
- 出力: `output/{施設名}/fixed/` + `output/{施設名}/reports/fix_log.json`
- CRITICAL問題 → デフォルト値補完 → 構造修正 → Property修正

### Stage 3: BUILD（build_bivr.py）
- 入力: `output/{施設名}/fixed/flows/*.json`
- 出力: `output/{施設名}/{施設名}_fixed.bivr`

### Stage 4: ACCUMULATE（自動）
- 修正前後ペアを `training_data/feedback/corrections/{施設名}/` に保存
- fix_log.json → learned_patterns.json への集約（パターン蓄積）

### 差分分析パイプライン（品質向上用）

VFB生成物と人間修正済みを比較してパターンを抽出する。

```
入力: VFB生成版 + 人間修正版（突合ペア）
  ↓
1. EXTRACT — 両方の .bivr を展開
2. DIFF — 構造的差分分析
3. PATTERN — 差分からパターン抽出 → learned_patterns 更新
```

---

## 品質基準

1. 全モジュールに遷移先が定義されていること
2. 全TTS/STTに save2db サブモジュールが接続されていること
3. STT の success が `^.+$` 1本受けであること
4. Retry の condition が `true`/`false`、label が `Retry`/`No more`
5. TTS の next label が `Next Module`
6. `stop_by_dtmf` が `"No"`/`"Yes"`
7. モジュール名に環境依存文字・括弧が含まれていないこと
8. リトライ回数が設定されていること
9. DTMFの `params.prompt` に `{recstart}` が含まれていること
10. `saveContextModel2DB` の `params.fields` がJSON文字列であること
11. OpenAI next分岐ラベルと prompt出力仕様が一致すること
12. Property.md のキー名とモジュール名が完全一致すること
13. **⛔ profile_words は @pw-generator エージェント必須**: ハードコード辞書での代用禁止。教師データ水準（フィラーTOP6/語尾TOP8/頭切れ/100-200語）を満たすこと
14. **⛔ OpenAI プロンプトは @prompt-enhancer エージェント併用必須**: apply_prompt_templates.py 実行後、施設固有情報の保持を @prompt-enhancer で確認すること

---

## ファイル構成

```
bivr-checker/
├── CLAUDE.md
├── PROJECT_DESIGN.md
├── PROGRESS_LOG.md
├── .claude/
│   ├── settings.json
│   └── agents/
│       ├── diff-analyzer.md    # VFB vs 人間の差分分析
│       ├── fixer.md            # 自動修正
│       └── orchestrator.md     # パイプライン制御
├── training_data/
│   ├── cross_analysis.md
│   ├── vfb_reference_summary.md
│   ├── brekeke_official_docs.md
│   ├── pair_01/ ... pair_20/
│   └── feedback/
│       └── corrections/        # 修正前後ペア蓄積
├── reference/
│   ├── defaults.json
│   ├── defaults_overrides/     # タイプ別オーバーライド + learned_patterns
│   ├── templates/
│   ├── subflows/
│   ├── prompts/
│   ├── dictionaries/
│   ├── scripts/              # Scriptモジュール用JSテンプレート（VFBより）
│   ├── env/
│   └── context/
├── schemas/
│   ├── intermediate_format.json  # 参照用（将来利用）
│   ├── check_report_schema.json
│   └── fix_log_schema.json
├── scripts/
│   ├── build_bivr.py
│   ├── extract_bivr.py
│   └── validator.py
├── input/                      # VFB出力を施設名別に配置
│   └── {施設名}/
│       ├── *.bivr
│       ├── *_Property.md
│       └── *.pdf
└── output/                     # 施設名別に出力
    └── {施設名}/
        ├── extracted/flows/    # .bivrから展開したフローJSON
        ├── fixed/flows/        # 修正済みフローJSON
        ├── fixed/*_Property.md # 修正済みProperty.md
        ├── reports/            # 各種レポート
        └── *_checked.bivr      # 最終出力
```
