# SKILL_JSON_rules — フローJSON設計ルール（共有スキル）

> **対象エージェント**: generator / fixer / reviewer / dirlite / properties  
> **読むタイミング**: JSONの生成・修正・検証を行う前に必ず参照すること

---

## JSON構造

### フローJSON の基本形

```json
{
  "layout": {},
  "resultValue": "",
  "postCallAction": "",
  "name": "グループ名$フロー名",
  "start": "開始モジュール名",
  "modules": {
    "モジュール名": {
      "layout": {"x": number, "y": number},
      "next": [...],
      "subs": [...],
      "name": "モジュール名",
      "description": "",
      "matchingmethod": 1,
      "type": "drjoy^カテゴリ$モジュール名",
      "params": {}
    }
  },
  "desc": ""
}
```

- `desc` は空文字 `""` にする
- `params` はモジュール種別ごとのデフォルト値をセットする（詳細: `docs/brekeke/brekeke_module_reference.md`）
- IVRプロパティが `params` の値を上書きするため、具体的な発話テキスト・URL等は空のままでよい

### 主要モジュールタイプ

| type値 | 役割 |
|---|---|
| `drjoy^Text To Speech$Text to speech` | TTS発話 |
| `drjoy^Text To Speech$Speech Retry Counter` | リトライ制御 |
| `drjoy^External Integration$DTMF AmiVoice STT Input` | 音声入力（主力STT） |
| `drjoy^AmiVoice$Speech to Text` | 音声入力（DTMFなしSTT） |
| `drjoy^External Integration$generate_by_OpenAI` | OpenAI分岐 |
| `drjoy^External Integration$RAG` | RAG検索（External Integrationのものを使う） |
| `drjoy^Persistence$save2db` | 音声録音保存（サブモジュール専用） |
| `drjoy^Persistence$saveContext2DB` | コンテキスト保存（通常モジュール） |
| `drjoy^Persistence$saveCompletionFlag2db` | 完了フラグ保存（通常モジュール） |
| `drjoy^Persistence$saveContextModel2DB` | コンテキストスキーマ設定（通常モジュール） |
| `drjoy^Incoming$incoming-classifier` | 着信電話番号分岐 |
| `drjoy^External Integration$acceptance_times` | 受付時間判定 |
| `drjoy^Custom Module$Custom Jump to Flow` | サブフロー遷移（新規作成時はこちらを使う） |
| `@General$Jump to Flow` | フロー間遷移（既存互換用。新規では使わない） |
| `@General$Script` | スクリプト実行（サブフロー結果返却等）。モジュール名は `script_` プレフィックス必須 |
| `Custom$wait` | 冒頭待ち時間（着信直後の安定待機） |
| `@IVR$Disconnect` | 切断 |
| `@IVR$Call Transfer` | 有人転送（オペレーター・代表番号への転送） |

---

## next配列の規則

**⚠️ ラベルの一意性（全モジュール共通）**: 同一モジュールの next 配列内で **ラベル（`label`）は重複してはならない**。ラベルが重複するとBrekekeフローデザイナーで正しく接続が表示されない。

### STT モジュール（DTMF AmiVoice STT Input / AmiVoice Speech to Text）

**最大11スロット**。使わないジャンプスロットは **condition・label・nextModuleName をすべて空文字列にすること**（枠ごと削除しない）（最大 jump1〜jump7）。

```json
"next": [
  {"condition": "^TIMEOUT$",  "label": "timeout",   "nextModuleName": "リトライ_xxx"},
  {"condition": "^ERROR$",    "label": "error",     "nextModuleName": "リトライ_xxx"},
  {"condition": "^NO_RESULT$","label": "no_result", "nextModuleName": "リトライ_xxx"},
  {"condition": "^.+$",       "label": "success",   "nextModuleName": "OpenAI_xxx"},
  {"condition": "",           "label": "jump1",     "nextModuleName": ""},
  ...（最大jump7まで）
]
```

- **success は `^.+$` で1本受けのみ**。`^予約$` 等の個別パターンをSTTに入れてはいけない
- 個別分岐は後続の `generate_by_OpenAI` で行う

### generate_by_OpenAI モジュール

**最大10スロット**。next配列の順序は以下の通り固定。使わないジャンプスロットは **condition・label・nextModuleName をすべて空文字列にすること**（STT と同じルール）:

```json
"next": [
  {"condition": "^TIMEOUT$",  "label": "timeout",   "nextModuleName": "リトライ_xxx"},
  {"condition": "^ERROR$",    "label": "error",     "nextModuleName": "リトライ_xxx"},
  {"condition": "^NO_RESULT$","label": "no_result", "nextModuleName": "リトライ_xxx"},
  {"condition": "^.+$",       "label": "success",   "nextModuleName": "次のモジュール"},
  {"condition": "",           "label": "jump1",     "nextModuleName": ""},
  ...（最大jump6まで）
]
```

- **TIMEOUT/ERROR/NO_RESULT は必ず先頭3スロット [0],[1],[2] に配置する**（STTと同じ順序）
- 分岐条件（`^予約変更$` 等）や success はその後に配置する
- 分岐型の場合は success の代わりに個別条件パターンを [3] 以降に並べる

### TTS モジュール

```json
"next": [
  {"condition": "^.*$", "label": "Next Module", "nextModuleName": "次のモジュール"}
]
```

- label は必ず `"Next Module"`
- 終話モジュール（Disconnect/Reject前の最終TTS）は `"next": []`

### Retry Counter モジュール

```json
"next": [
  {"condition": "true",  "label": "Retry",   "nextModuleName": "先頭TTSモジュール"},
  {"condition": "false", "label": "No more", "nextModuleName": "正解ルートの次のモジュール"}
]
```

- **condition は `true`/`false`、label は `Retry`/`No more`**（混同厳禁）
- **Retry 先は必ず先頭 TTS モジュール**（TTS→STT 連鎖の起点。STT モジュールを直接指定してはいけない）
- **No more 先は正解ルートの次のモジュール**（複数分岐があり遷移先が一意でない場合は終話モジュールに繋ぐ）
- **`prompt_true` は固定値** `{tts_g:申し訳ございません。うまく聞き取りが出来ませんでした。再度、}` — 末尾「再度、」が後続 TTS 先頭に自然に繋がる設計。**変更禁止・IVRプロパティでは動作しないため JSON 内に直接記述すること**
- **`prompt_false` は原則空文字** `""` — No more 先が通常モジュールの場合は無音で遷移。終話モジュールに繋ぐ場合のみ明示設定。**IVRプロパティでは動作しないため JSON 内に直接記述すること**

### ContextMatchRouter / conditional-comparison モジュール

**空スロット禁止**。実際に使う分岐のみ記述し、未使用スロットを残してはいけない。

```json
"next": [
  {"condition": "^予約$",  "label": "予約",  "nextModuleName": "予約ルート"},
  {"condition": "^変更$",  "label": "変更",  "nextModuleName": "変更ルート"},
  {"condition": "^.*$",    "label": "その他","nextModuleName": "デフォルトルート"}
]
```

- **条件網羅**: 全パターンを網羅し、最後は `^.*$` でデフォルトルートを必ず設けること
- **不要になったスロットは空白化すること**: 設計変更で不要になった分岐スロットは枠ごと削除せず、condition・label・nextModuleName をすべて `""` に空白化すること

### condition と label の早見表

| モジュール種別 | condition | label |
|---|---|---|
| TTS → 次へ | `^.*$` | `Next Module` |
| STT タイムアウト | `^TIMEOUT$` | `timeout` |
| STT エラー | `^ERROR$` | `error` |
| STT 認識なし | `^NO_RESULT$` | `no_result` |
| STT 成功 | `^.+$` | `success` |
| OpenAI タイムアウト | `^TIMEOUT$` | `timeout` |
| OpenAI エラー | `^ERROR$` | `error` |
| OpenAI 認識なし | `^NO_RESULT$` | `no_result`/`NO_RESULT` |
| OpenAI 成功 | `^.+$` / `^.*$` | `success` |
| OpenAI 個別分岐 | `^{値}$` | `{値}` |
| Retry 続行 | `true` | `Retry` |
| Retry 上限 | `false` | `No more` |
| Persistence 次へ | `^.*$` | `next` |

---

## subs配列の規則（save2db 接続）

**全ての TTS・STT・Retry Counter モジュールに `save2db` サブモジュールを必ず接続すること**（音声録音に必須）。

```json
"subs": [
  {"moduleName": "save-xxx", "label": "save-xxx"},
  {"moduleName": "", "label": ""},
  {"moduleName": "", "label": ""}
]
```

- ラベル名は必ず `save-` プレフィックスで始める
- TTS とその直後の STT・Retry Counter は同じ save2db ラベル名を使う
- `saveCompletionFlag2db`・`saveContext2DB`・`saveContextModel2DB` はサブモジュール禁止・通常モジュールとして配置
- **saveContext2DB の `contextValue` には `#data#` 記法を設定してはいけない**（`#data#` は Re-confirmation node data のTTS発話専用）。contextValue に設定できるのは固定文字列（例: `携帯`, `その他`）またはシステム変数（例: `<% sys-customer-phone-number %>`）のみ
- **saveContext2DB を使うべき場面・使わない場面**:
  - ✅ **使う**: 患者の発話からは取得できないルーティング固定値を保存する場合のみ
  - ✅ **使う**: システム変数を格納する（例: 着信番号を telephoneNumber に `<% sys-customer-phone-number %>` で保存）
  - ❌ **使わない**: 患者の発話から聴取した値全般（OpenAI が出力する値）
  - ❌ **使わない**: OpenAI の分類ラベルの固定値保存。分類結果は OpenAI の next 分岐で直接 routing する
  - **後段で同じ値による再分岐が必要な場合**: **ContextMatchRouter** を使う

### save2db モジュールの配置ルール（重要）

**save2db モジュールは `modules` に定義が必須。定義がないと Brekeke フローデザイナーが表示できない。**

```json
"save-xxx": {
  "layout": {"x": 数値, "y": 数値},
  "next": [],
  "subs": [{"moduleName": "", "label": ""}, {"moduleName": "", "label": ""}, {"moduleName": "", "label": ""}],
  "name": "save-xxx",
  "description": "",
  "matchingmethod": 1,
  "type": "drjoy^Persistence$save2db",
  "params": {"contextName": "", "contextDisplayType": "TEXT"}
}
```

- `modules` に定義する ✓（必須）
- `subs` 経由でのみ接続する ✓
- 他モジュールの `next` の遷移先にしない ✗（禁止）

---

## stop_by_dtmf の値

| 意味 | 正しい値 | 誤った値（使用禁止） |
|---|---|---|
| DTMFで停止しない | `"No"` | `"false"` |
| DTMFで停止する | `"Yes"` | `"true"` |

---

## DTMF AmiVoice STT Input — デフォルト規則

| パラメータ | デフォルト | 上書き例 |
|---|---|---|
| `prompt` | `"{recstart}"` | **JSON内に直接記載**（IVRプロパティには記載しない） |
| `max_dtmf_length` | `"10"` | 用件選択=`"1"`, 診療科コード=`"4"`, 電話番号=`"11"` |
| `retry` | `"2"` | 変更不要（Speech Retry Counter とは別の DTMF 専用） |
| `termdtmf` | `"#"` | 変更不要 |
| `remove_term` | `"Yes"` | 変更不要 |
| `stop_play_when_speech` | `"Yes"` | 変更不要 |

**ルール:**
- **`{recstart}` はフローJSON内のモジュール `params.prompt` に直接記載すること**（DTMFモジュールの録音開始マーカー）
- **`{recstart}` をIVRプロパティに記載してはならない**
- DTMFモジュールの前にTTS発話が必要な場合は、**前段の TTS モジュール**で発話し、DTMFモジュール自体の prompt は `"{recstart}"` のみとする
- `max_dtmf_length` はステップ固有の桁数が指定されていない限り `"10"` を使用

---

## 命名規則

### 禁止文字
- `①②③` 等の環境依存文字（丸数字など）
- `（）()[]` 等の括弧
- スペース
- アンダーバー以外の区切り文字

### フロー名
- `グループ名$フロー名_YYYYMMDD` 形式（末尾に作成日8桁を付与）
- グループ名＋フロー名を **URLエンコードした状態で255バイト以内**
- 例（日本語）: `す_諏訪$診療1_M_藤田_20251128` / 例（英字）: `East_Medical$健診_20260406`

### グループ名
- **顧客資料（Canva設計書・Gen2プロンプト）に記載の施設名・法人名をそのまま使用すること**（省略・独自命名禁止）
- 英字の場合: スペース → アンダーバーに変換（例: `East Medical` → `East_Medical`）
- **サブフローも同一の日付サフィックスを付けること**
- **`Jump to Flow` の `flowname` 参照先も日付付きのフロー名に合わせること**（不一致だとサブフロー遷移が壊れる）

### モジュール名
- `大分類_内容` または `大分類_内容_詳細` 形式
- TTS: `大分類_内容`（例: `冒頭_アナウンス`, `患者_氏名`）
- STT: `入力_大分類_内容`（例: `入力_患者_氏名`）
- OpenAI: `OpenAI_大分類_内容`
- Retry: `リトライ_大分類_内容`
- save2dbサブ: `save-大分類_内容`（`save-` プレフィックス必須）

### TTSプロンプト名とモジュール名の一致
**IVRプロパティ内のプロンプト名とモジュール名は完全一致が必須**（不一致だとTTS動作しない）

---

## フロー設計の基本原則

1. **冒頭に wait 2000ms が必須**（着信直後の安定待機）— モジュール型は `Custom$wait` を使用する
2. **冒頭チェーン**は `wait（Custom$wait） → saveContextModel2DB → incoming-classifier → [acceptance_times] → 冒頭アナウンス` の順で固定
2b. **incoming-classifier の着信分類ルール（全フロー共通デフォルト）**:
   - `^非通知$` → 冒頭で落とす（saveCompletionFlag2db → TTS → Disconnect）
   - `^携帯$` → acceptance_times（SMS送信可能な専用終話フローに接続）
   - `^固定$` / `^海外$` / `^.*$`（その他） → acceptance_times（固定と同一の共通フロー）
   - **`^.*$` ワイルドカードは必ず末尾に配置し、条件は `^.*$` を使うこと（`^*$` は無効な正規表現）**
3. 全STT入力に **リトライ（2回）** を設定
4. リトライ上限で **終話_失敗** または **切断モジュール** に遷移
5. タイムアウト・エラー時のフォールバックが必ず存在すること
6. 全TTS/STTモジュールに **save2db サブモジュール** を接続すること
7. AmiVoice 内蔵の RAG サブモジュールは**使わない**。External Integration の RAG を使う
8. STTモジュールの入力種別に応じて **`profile_words` に辞書単語を設定する**こと（詳細: `docs/ai/amivoice_dictionary.md`）
9. **新規フロー作成時・移管時の個人情報聴取サブフローは `docs/reference/bivr/samples/json/` の事前展開済み静的JSONを使用する**。設計書の聴取項目と復唱有無に基づいて該当JSONをcpでコピーし、フロー名プレフィックスのみ置換する。**BIVR展開（extract_bivr.py）は不要**。モジュール構造・接続・スクリプトは一切変更しない。サブフロー遷移には `drjoy^Custom Module$Custom Jump to Flow` を使用する。静的JSON一覧: 氏名聴取 / 生年月日聴取_復唱あり / 生年月日聴取_復唱なし / 電話番号聴取_復唱あり / 電話番号聴取_復唱なし / 診察券番号聴取
10. **電話番号聴取サブフローは `incoming-classifier` で着信番号を分岐し、携帯パスは着信番号を復唱確認、それ以外のパスでは連絡先番号を聴取する。最終的な携帯/その他の判定は `script_携帯判別` スクリプトで正規表現判定し、出口の結果返却スクリプトでメインフローに返却する**
11. **全サブフローの出口に結果返却スクリプトモジュール（`script_結果返却_*`）を必ず配置する**。スクリプト内で `$runner.getModuleResult()` により対象モジュールの結果を取得し、`$runner.setResult()` でメインフローに返却する
11b. **サブフローの終話方式は設計書の `termination` フラグに従う**: `return`（デフォルト）= サブフロー内にDisconnect配置禁止。`self_contained` = サブフロー内で終話チェーンまで完結
12. **全ての終話パスで `saveCompletionFlag2db` は終話ガイダンス（TTS）の直前に配置すること**。正しい順序: `saveCompletionFlag2db → TTS（終話ガイダンス）→ Disconnect`
12b. **`saveCompletionFlag2db` の `status` 値は `"0"` と `"5"` を使用禁止**。第3世代で許可される値: `"1"`, `"2"`, `"3"`, `"6"`, `"7"` 以降。設計書に status 定義がない場合はデフォルト `"1"`
13. **OpenAIモジュールのプロンプト（`params.prompt`）はフローJSON内に直接記述する**（IVRプロパティではない）
14. **OpenAIモジュール（`generate_by_OpenAI`）は `params.module` で指定されたモジュールの出力データを元にテキストを生成する**。出力データが存在しない状態でOpenAIモジュールを配置してはならない
15. **acceptance_times（営業時間判定）の分岐ルール**: `true`（営業時間内）のみ冒頭アナウンスに進む。TIMEOUT・ERROR・`false`（時間外）はすべて時間外アナウンスに分岐させる
16. **RAG（FAQ検索）モジュールの配置ルール**: RAGモジュールはサブフロー化して配置する。
    - **Gen2→Gen3移管**: パターン3（複合）= 問い合わせフロー内にRAGサブフロー＋全終話前にRAGサブフロー
    - **Gen1→Gen3移管**: パターン2 = 全終話前にRAGサブフローのみ
    - **新規作成・修正**: パターン1 = 問い合わせフロー内にRAGサブフローのみ
    - RAGサブフローのリファレンス: `docs/reference/bivr/samples/json/RAG検索.json`（静的JSON）
    - **RAGサブフローのデフォルトTTS文言**:
      - パターン1初回: `{tts_g:お問い合わせ内容をご自由におっしゃってください。}`
      - パターン2初回: `{tts_g:何かご質問はございますか？}`
      - ループ時: `{tts_g:その他に何かご質問はございますか？ない場合は「ありません」のようにお話しください。}`
    - **メインフローにRAG案内TTSを重複配置しない**（RAGサブフロー自体が冒頭TTSを持つ）
17b. **サブフロー参照の整合性（Custom Jump to Flow）**:
    - `params.flowname` は `drjoy^グループ名$フロー名_YYYYMMDD` 形式。サブフロー JSON の `"name"` フィールドと **完全一致** すること
    - **BIVR ビルド時に全サブフローを含めること**
18. **Scriptモジュールのモジュール値取得API**:
    - **`$runner.getModuleResult("モジュール名")`（推奨）**: モジュール名を指定して出力値を直接取得
    - **`$ivr.getProperty("モジュール名", "value")`（代替）**: プロパティ経由で取得
    - **`$ivr.getObject("key")` は非推奨**（新規で使用しない）
    - 出力には `$runner.setResult("値")` を使用する
    - **ルート判定（固定パターン分岐）には ContextMatchRouter を優先する**

---

## システム変数一覧

`<% 変数名 %>` 形式で参照する。saveContext2DB の `contextValue` やTTS発話内で使用可能。

### 汎用変数

| 変数 | 利用目的 | 備考 |
|------|---------|------|
| `sys-customer-phone-number` | 着信したユーザーの電話番号 | 電話番号サブフローの復唱確認・saveContext2DBで使用 |
| `sys-customer-name` | 着信電話番号から電話帳に登録されているユーザー名を取得 | Dr.JOY電話帳連携。未登録の場合は空 |

### スマート面会連携変数

| 変数 | 利用目的 | 備考 |
|------|---------|------|
| `visitor-id` | 面会者ID | スマート面会連携 |
| `visitor-name` | 面会者名 | スマート面会連携 |
| `patient-id` | 患者ID | スマート面会連携 |
| `patient-name` | 患者名 | スマート面会連携 |
| `frame-id` | 予約枠ID | スマート面会連携 |
| `frame-title` | 予約枠名 | スマート面会連携 |
| `booking-start-time` | 訪問開始時間 | スマート面会連携 |
| `booking-end-time` | 訪問終了時間 | スマート面会連携 |
| `relationship` | 続柄 | スマート面会連携 |
| `number-of-visitors` | 面会人数 | スマート面会連携 |
| `memo` | 備考 | スマート面会連携 |
| `contact-required` | 問い合わせ確認必須フラグ | スマート面会連携 |
| `visitor-count-options` | 設定した面会者数一覧 | スマート面会連携 |
| `department-name` | 診療科名 | External Integration の check-frame-time モジュールで使用 |

---

## .bivr エクスポート形式

ZIPアーカイブ（拡張子を `.bivr` に変えたもの）。

```
{名前}.bivr
└── flows/
    └── @flow_{URLエンコード済みフロー名}.txt   ← 拡張子 .txt、JSON1行
```

### ファイル名エンコード規則

- `$` → `%24`（URLエンコード）
- 日本語等はすべて `%XX` 形式にエンコード
- ファイル名の先頭 `@` は必須
