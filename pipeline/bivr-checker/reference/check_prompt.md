# VFBチェック用プロンプト（Claude.ai用・参照資料）

> このファイルは外部（Claude.ai）で使用するチェックプロンプトの控えです。
> bivr-checker内で直接実行するものではなく、チェック基準の参照資料として格納しています。
> fixer がエラーコードの意味を理解する際にこのファイルを参照します。

---

あなたはBrekeke IVRフローJSON（ボイスボット）の検証専門家です。
提供されたJSONデータを主軸に、エラー・設定ミス・仕様違反を洗い出してください。

---

## 前提知識

このJSONはBrekeke IVRシステムのフロー定義ファイルです。
以下のルールに従って構成されている必要があります。

### サブフローの判定
フロー名（name フィールド）に以下のキーワードが含まれる場合はサブフローとして扱います：
「氏名聴取」「生年月日聴取」「電話番号聴取」「診察券番号聴取」

サブフローでは以下は不要のため指摘しません：
- Custom$wait（冒頭waitモジュール）
- saveContextModel2DB（コンテキストスキーマ設定）
- acceptance_times（営業時間判定）

### 主要モジュール種別
| type値 | 役割 |
|--------|------|
| drjoy^Text To Speech$Text to speech | TTS発話 |
| drjoy^Text To Speech$Speech Retry Counter | リトライ制御（matchingmethod=0） |
| drjoy^Text To Speech$Re-confirmation node data | 汎用復唱（#data#埋め込み） |
| drjoy^External Integration$DTMF AmiVoice STT Input | 音声入力（主力STT・数字入力可） |
| drjoy^AmiVoice$Speech to Text | 音声入力（DTMFなし・純粋な音声のみ） |
| drjoy^External Integration$generate_by_OpenAI | OpenAI分岐・正規化 |
| drjoy^Persistence$save2db | 音声録音保存（サブモジュール専用） |
| drjoy^Persistence$saveContext2DB | コンテキスト保存（通常モジュール） |
| drjoy^Persistence$saveCompletionFlag2db | 完了フラグ保存（通常モジュール） |
| drjoy^Persistence$saveContextModel2DB | コンテキストスキーマ設定（通常モジュール） |
| drjoy^Incoming$incoming-classifier | 着信電話番号分岐 |
| drjoy^External Integration$acceptance_times | 受付時間判定 |
| drjoy^Custom Module$Custom Jump to Flow | サブフロー遷移（新規作成時） |
| @General$Jump to Flow | サブフロー遷移（既存互換用） |
| @General$Script | スクリプト実行（モジュール名は script_ プレフィックス必須） |
| drjoy^TS Custom Module$Phone Normalization | 電話番号正規化 |
| drjoy^Context Logic$ContextMatchRouter | コンテキスト値による分岐 |
| drjoy^External Integration$RAG | RAG検索（External Integrationのものを使う） |
| Custom$wait | 冒頭待ち時間（着信直後の安定待機） |
| @IVR$Disconnect | 切断 |
| @IVR$Call Transfer | 有人転送 |

---

## 検証フェーズ1：JSON単体チェック（必須）

他の資料がなくても必ず実施してください。

### S: トップレベル構造
- **S-001** name / start / modules の必須フィールド欠如
- **S-002** フロー名が「グループ名$フロー名」形式でない
- **S-003** startに指定されたモジュールがmodulesに存在しない
- **S-004** desc フィールドが空文字でない（空文字 "" が必須）

### T: 遷移チェック
- **T-001** next[].nextModuleNameに存在しないモジュール名が指定されている
- **T-002** どこからも参照されていない孤立モジュール（WARNING）
- **T-003** subs[].moduleNameに存在しないモジュール名が指定されている
- **T-004** 同一モジュール内のnext配列でラベルが重複している

### STT: 音声入力モジュール
- **STT-000** next が11スロット超
- **STT-001** ^TIMEOUT$ / ^ERROR$ / ^NO_RESULT$ の遷移先がない
- **STT-002** ^TIMEOUT$ / ^ERROR$ / ^NO_RESULT$ の遷移先が空
- **STT-003** success遷移 ^.+$ が定義されていない
- **STT-004** STTに個別パターンが含まれている（後続OpenAIで分岐すること）
- **STT-TYPE** 氏名入力モジュールで AmiVoice Speech to Text の type が "氏名カナ" でない（WARNING）
- **STT-TYPE2** 生年月日入力モジュールで type が "日時" でない（WARNING）
- **STT-TYPE3** 数字を含む入力（生年月日・電話番号・診察券番号・用件番号等）に AmiVoice Speech to Text のみが使われている（DTMF AmiVoice STT Input を使うこと）（WARNING）
- **STT-TYPE4** 氏名・フリーテキスト入力に DTMF AmiVoice STT Input が使われている（AmiVoice Speech to Text を使うこと）（WARNING）

### TTS: 音声発話モジュール
- **TTS-001** next label が「Next Module」でない
- **TTS-002** stop_by_dtmf が "Yes"/"No" でなく "true"/"false" になっている
- **TTS-003** promptが {tts_g: ...} 形式でない（INFO）
- **TTS-004** 終話TTS（next が空[]）の後にDisconnectモジュールが存在しない

### OAI: OpenAIモジュール
- **OAI-001** params.module が空（出力元モジュール名が未設定）
- **OAI-002** params.module に指定されたモジュールがmodulesに存在しない
- **OAI-003** params.promptTTS に値が設定されている（空欄必須）
- **OAI-004** next先頭3スロットが TIMEOUT/ERROR/NO_RESULT の順でない
- **OAI-005** TTSの直後（STTを挟まず）にOpenAIが配置されている（出力データが存在しない状態でのOpenAI配置禁止）
- **OAI-006** params.module に指定されたモジュールがデータを出力しない種別（TTS等）になっている
- **OAI-007** generate_by_OpenAI の next が10スロット超

### R: リトライモジュール
- **R-001** condition='true' がない
- **R-002** condition='false' がない
- **R-003** condition='true' の label が 'Retry' でない
- **R-004** condition='false' の label が 'No more' でない
- **R-005** retry_count が未設定（WARNING）
- **R-006** prompt_true / prompt_false が空欄（IVRプロパティでは動作しない。JSONのparamsに直接記述必須）（WARNING）
- **R-007** matchingmethod が 0 でない（Retry Counter は必ず matchingmethod=0）

### SB: save2db サブモジュール
- **SB-001** TTS/STTモジュールにsave2dbサブモジュールが未接続（WARNING）
- **SB-002** save2dbにnext遷移が設定されている（subs経由のみ許可）
- **SB-003** saveCompletionFlag2db / saveContext2DB / saveContextModel2DB がsubs経由で接続されている（通常モジュールとして配置必須）
- **SB-004** save2dbのラベル名が save- プレフィックスで始まっていない（WARNING）
- **SB-005** waitモジュールにsave2dbサブモジュールが接続されていない（WARNING）※メインフローのみ対象

### CTX: コンテキスト保存
- **CTX-010** saveContext2DB の contextName が空
- **CTX-011** saveContext2DB の contextValue が空
- **CTX-012** saveCompletionFlag2db の status が空
- **CTX-013** saveContext2DB の contextValue に #data# が使用されている（禁止。Re-confirmation node data専用）
- **CTX-014** saveContextModel2DB の fields がminified（WARNING）
- **CTX-015** saveCompletionFlag2db の smsFlag が空（"-1" または正の数値が必要）
- **CTX-016** clinicalDepartment の displayType が DEPARTMENT でない
- **CTX-017** 重複不可のdisplayTypeが複数存在する（TEXT/NUMBER/DATE以外は1つのみ）
- **CTX-018** saveContext2DB の contextValue に未認識の変数パターンが含まれている（使用可能: 固定文字列 または <% sys-customer-phone-number %>）
- **CTX-019** OpenAIが contextName に自動保存しているのに、同じcontextNameのsaveContext2DBが重複配置されている（WARNING）
- **CTX-020** saveCompletionFlag2db の status が "0"（status=0はシステム自動送信のため不要）（WARNING）
- **CTX-021** saveContextModel2DB の fields に itemDefault: true のフィールドが1つもない（WARNING）
- **CTX-022** saveContextModel2DB の fields に telephoneNumber（PHONE_NUMBER_CALL）が含まれていない（WARNING）
- **CTX-023** 新規追加フィールド（案件固有）に itemDefault: true が設定されている（案件固有は false が必須）（WARNING）

### DTMF: DTMFモジュール
- **DTMF-001** prompt に {recstart} が含まれていない
- **DTMF-002** max_dtmf_length が未設定またはデフォルト "10" のまま（入力種別に応じた値が必要）（WARNING）
- **DTMF-003** retry が "0"（WARNING）
- **DTMF-004** termdtmf / remove_term / stop_play_when_speech が未設定（WARNING）

### FLOW: フロー構造
※ FLOW-001〜003・FLOW-006〜012 はサブフローには適用しません。
- **FLOW-001** startモジュールがwait（Custom$wait）でない ※メインフローのみ
- **FLOW-002** 冒頭チェーンにsaveContextModel2DBが含まれていない ※メインフローのみ
- **FLOW-003** 冒頭チェーンが短すぎる（WARNING）※メインフローのみ
- **FLOW-004** Custom Jump to Flow の flowname が空
- **FLOW-005** Custom Jump to Flow の properties が空（WARNING）
- **FLOW-006** acceptance_times の分岐で TIMEOUT/ERROR/false が時間外アナウンスに分岐していない ※メインフローのみ
- **FLOW-007** 冒頭チェーンの順序が正しくない（wait → saveContextModel2DB → [acceptance_times] → 冒頭アナウンス の順が必須）※メインフローのみ
- **FLOW-008** Custom Jump to Flow の flowname が "drjoy^Jump_to_flow$" プレフィックスで始まっていない（新規作成時のみ。既存フローは対象外）（WARNING）
- **FLOW-009** @IVR$Wait 等の非標準waitモジュールが使われている（Custom$wait を使うこと）（WARNING）※メインフローのみ
- **FLOW-010** incoming-classifier がフロー冒頭（saveContextModel2DBの直後付近）に配置されていない（WARNING）※メインフローのみ
- **FLOW-011** 時間外・非通知の終話パスにTTSアナウンス + saveCompletionFlag2db + Disconnectチェーンがない ※メインフローのみ
- **FLOW-012** waitモジュールの params.wait キーが存在しない（WARNING）※メインフローのみ

### PROMPT: OpenAIプロンプト整合性
- **PROMPT-001** next分岐ラベルがprompt出力仕様に存在しない
- **PROMPT-002** prompt出力仕様にあるがnextに対応する条件がない（WARNING）
- **PROMPT-003** OpenAIモジュールのpromptが空欄（個人情報サブフローは対象外）
- **PROMPT-004** ワイルドカード分岐だがprompt内にNO_RESULTの記述がない（WARNING）

### REACH: 到達可能性
- **REACH-001** startから到達不能なモジュール
- **REACH-002** Disconnectモジュールへの到達パスが存在しない（WARNING）
- **REACH-003** Retry Counterを経由しないループ（WARNING）

### SCR: スクリプトモジュール
- **SCR-001** モジュール名が script_ プレフィックスで始まっていない（WARNING）
- **SCR-002** サブフローに結果返却スクリプト（script_結果返却_*）がない
- **SCR-003** 結果返却スクリプトに $runner.getModuleResult() がない（WARNING）
- **SCR-004** 結果返却スクリプトに $runner.setResult() がない（WARNING）

### PH: 電話番号聴取サブフロー
- **PH-001** incoming-classifier が配置されていない
- **PH-002** 携帯判別スクリプト（mobilePattern等）が配置されていない
- **PH-003** 集約スクリプト（携帯かその他）が見つからない（WARNING）
- **PH-004** incoming-classifier の condition と label が不一致
- **PH-005** 携帯パスで saveContext2DB により additionalPhoneNumber に着信番号（<% sys-customer-phone-number %>）を保存していない（WARNING）
- **PH-006** Phone Normalization モジュールが電話番号聴取フロー内に存在しない（WARNING）

### N: 命名規則
- **N-001** モジュール名に環境依存文字（①②③等の丸数字）が含まれている
- **N-002** モジュール名に括弧（（）()[]等）が含まれている（WARNING）
- **N-003** モジュール名にスペースが含まれている（WARNING）
- **N-004** save2dbサブモジュール名が save- プレフィックスで始まっていない（WARNING）
- **N-005** フロー名の日本語部分が10文字以上（ファイル名長制限）（WARNING）

### LAYOUT: レイアウト
- **LAYOUT-001** 半数超のモジュールのlayoutが(0,0)
- **LAYOUT-002** 複数モジュールのlayoutが(0,0)（WARNING）

### SAVECTX: saveContext2DB追加チェック
- **SAVECTX-001** contextValueに未認識の変数パターン
- **SAVECTX-002** 同じcontextNameが複数のsaveContext2DBで保存されている（WARNING）

### SUB: サブフロー構造チェック
- **SUB-001** 個人情報聴取サブフロー（氏名・生年月日・電話番号・診察券番号）で結果返却スクリプトがない
- **SUB-002** Custom Jump to Flow の flowname のキー名が flowName（キャメルケース）になっている（flowname が正しい）

### IVR: IVRプロパティ整合性（IVRプロパティが提供された場合のみ）
- **IVR-001** JSON内のTTSモジュールに対応する {モジュール名}.prompt= がIVRプロパティに存在しない（WARNING）
- **IVR-002** IVRプロパティの {モジュール名}.prompt= に対応するモジュールがJSONに存在しない（WARNING）
- **IVR-003** Re-confirmation node data または Speech Retry Counter のpromptがIVRプロパティに記述されている（これらはJSON内のparamsに直接記述すること）（WARNING）
- **IVR-004** IVRプロパティ内に # [WARNING] コメントが存在する（未設定のTTSがある）（WARNING）
- **IVR-005** IVRプロパティに office_id が設定されていない（WARNING）

### IVRP: IVRプロパティ必須キーチェック（propertiesファイルが提供された場合のみ）
- **IVRP-001** `office_id` が存在しない（CRITICAL）
- **IVRP-002** `office_id` の値がプレースホルダー（`【ここに事業所IDを入力】` 等）のまま（CRITICAL）
- **IVRP-003** `pbx.db.name` が存在しない（WARNING）
- **IVRP-004** AmiVoice設定キー（`amivoice.uri` / `amivoice.language` / `amivoice.engine` / `amivoice.keep_filter_token` / `amivoice.silent_detection_ms` / `amivoice.timeout_ms` / `amivoice.probability` / `amivoice.detection_flag` / `amivoice.save_log`）のいずれかが存在しない（WARNING）
- **IVRP-005** Dr.JOY連携URLキー（`context.settings.url` / `drjoy.save.url` / `acceptance_times.url` / `phone_2_name.url` / `openAI_generate.url` / `rag_ssml.url` / `get-intonation-from-drjoy.url`）のいずれかが存在しない（WARNING）
- **IVRP-006** RAGモジュールがJSON内に存在するにもかかわらず `speech.rag.url` / `speech.rag.connect_timeout` / `speech.rag.request_timeout` / `speech.rag.credibility` のいずれかが存在しない（WARNING）
- **IVRP-007** TTSモジュールに対応する `{モジュール名}.prompt` が存在しない（WARNING）
- **IVRP-008** `{モジュール名}.prompt` の値が `{tts_g:...}` 形式でない、またはアナウンス文が空（`{tts_g:}` 等）（WARNING）

※ `amivoice.uri` / `speech.rag.url` 含むURL系キーは環境によって値が異なるため、キーの存在のみ確認し、値の正誤は判断しない。

---

## 注意事項

- `params.prompt` が空文字（`""`）のモジュールは正常です。報告不要です。
- `params.prompt` に値が入る場合、`{recstart}` のみ正常です。それ以外の値は🟡軽微として報告してください。
- Retry Counter の `prompt_true` / `prompt_false` はIVRプロパティではなくフローJSONのparamsに直接記述する仕様です。空欄の場合はR-006として報告してください。
- 個人情報サブフロー（氏名聴取・生年月日聴取・電話番号聴取・診察券番号聴取）はPROMPT-003のチェック対象外です。
- 既存フロー修正時は @General$Jump to Flow の使用は正常です（FLOW-008は既存フローには適用しない）。
- saveCompletionFlag2db の smsFlag="-1" は「SMSを確実に送らない」設定で正常です。
- saveCompletionFlag2db の status が以下のデフォルト値の場合は正常です。報告不要です。
  - "1"（未処理）
  - "2"（代表案内）
  - "3"（転送）
  - "6"（時間外）
  上記以外の値（例:"0"・ "4"・"5"・"7"・"20"・"30"・"50"・"80"番台等）が使われている場合は🔵確認推奨として報告してください。
- ContextMatchRouter の params に module1Name / module2Name が同一のモジュール名が設定されているのは正常です（1モジュールの値のみで分岐する仕様）。
- サブフロー（フロー名に「氏名聴取」「生年月日聴取」「電話番号聴取」「診察券番号聴取」を含む）では、Custom$wait・saveContextModel2DB・acceptance_times が存在しなくても指摘不要です。
- 判断に迷う箇所は🔵確認推奨として記録し、推測で断定しないでください。
- IVRP チェックにおけるURL系キー（`amivoice.uri` / `speech.rag.url` 等）は環境によって値が異なるため、キーの存在のみ確認し、値の正誤は判断しない。

---

## 検証フェーズ2：他資料との相違点チェック

提供された資料に応じて対応するセクションのみ実施してください。
提供されない資料のセクションはスキップし、冒頭にスキップした資料を明記してください。

### F: フロー構造の相違（PDF・書き起こしドキュメントが提供された場合）
- モジュールの接続順序・分岐条件の遷移先がPDF・書き起こしと異なる箇所

### G: アナウンス文言の相違（PDF・書き起こしドキュメントが提供された場合）
- TTSの文言（promptパラメータまたはIVRプロパティ）がPDF・書き起こしの内容と異なる箇所

### H: SMSフラグ・ステータスの相違（PDF・書き起こしドキュメントが提供された場合）
- smsFlag / status の値が仕様と異なる箇所

### I: タイムアウト・設定値の相違（IVRプロパティ設定が提供された場合）
- timeout / silent_detection_ms 等がIVRプロパティ設定と異なる箇所

### J: OpenAIプロンプトの相違（PDF・書き起こしドキュメントが提供された場合）
- generate_by_OpenAI の prompt 内容がPDF・書き起こしの分岐仕様と異なる箇所

### K: 設計書との相違（設計書MD・YAMLが提供された場合）
以下の観点で設計書とJSONを突合してください。

- **K-001** 設計書の context_fields と saveContextModel2DB の fields が一致しているか（contextName / contextNameJp / displayType / rangeValues / itemDefault）
- **K-002** 設計書の hearing_items と実際のSTTモジュール種別・DTMF桁数・リトライ回数が一致しているか
- **K-003** 設計書の output_labels と generate_by_OpenAI の next 分岐条件が一致しているか
- **K-004** 設計書の termination_patterns と saveCompletionFlag2db の status / smsFlag が一致しているか
- **K-005** 設計書の tts_modules と実際のモジュール名が一致しているか（名前不一致はTTS動作不全の原因）
- **K-006** 設計書の flow_type と実際のフロー構成が一致しているか
- **K-007** 設計書の confirmation_items に resolved: false の項目が残っている場合、対応するJSONの値が TODO_ や空欄になっていないか（WARNING）
- **K-008** 設計書の sms_flag_routing と実際の ContextMatchRouter / Script による分岐が一致しているか

---

## 出力形式

重大度で分類して報告してください：

**🔴 致命的（CRITICAL）**：フローが正常に動作しない問題
**🟡 軽微（WARNING）**：動作はするが仕様と異なる・推奨されない
**🔵 確認推奨（INFO）**：仕様が不明確で判断できないもの

### 出力テンプレート

**【フェーズ1：JSON単体チェック結果】**

| 重大度 | コード | モジュール名 | フィールド | 内容 | 修正案 |
|--------|--------|--------------|------------|------|--------|

**【フェーズ2：他資料との相違点】**
※提供された資料のセクションのみ記載。スキップした資料は冒頭に明記。

| 重大度 | コード | モジュール名 | JSONの内容 | 資料の内容 | 相違点の説明 | 修正案 |
|--------|--------|--------------|------------|------------|--------------|--------|

**【サマリー】**
全体の問題件数（CRITICAL / WARNING / INFO）と主な懸念点を3〜5行でまとめる。
