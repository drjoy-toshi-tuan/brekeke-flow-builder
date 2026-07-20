# bivr-checker 知識ベース定義書

> **作成日**: 2026-04-14
> **目的**: 蓄積教師データ・フィードバック・ルールの全容整理と、現状の生成品質評価

---

## 目次

1. [蓄積データ全体像](#1-蓄積データ全体像)
2. [VFB頻出バグパターン22個と修正方針](#2-vfb頻出バグパターン22個と修正方針)
3. [コンポーネント別設計ルール](#3-コンポーネント別設計ルール)
4. [現状の生成品質評価](#4-現状の生成品質評価)
5. [不足している知識・ギャップ](#5-不足している知識ギャップ)
6. [改善ロードマップ](#6-改善ロードマップ)

---

## 1. 蓄積データ全体像

### 1-1. 教師データ（11ペア）

| Pair | 施設名 | 種別 | モジュール数 | 主な難易度要因 |
|---|---|---|---|---|
| 01 | 帯広第一病院 | 健診 | 152（3フロー） | 個人/企業分岐、健保名、代行機関、オプション選択 |
| 02 | 入間ハート病院 | 診療（複合） | 83 | 診察/検査/予防接種/送迎 × 予約/変更/キャンセル |
| 03 | 長野県立木曽病院 | 診療 | 290（5フロー） | 耳鼻科特別ルート、診療科×2サブフロー |
| 04 | ガーデンシティ健診プラザ | 健診 | 79 | 受診票有無、被保険者/特例退職者分岐 |
| 05 | JAとりで総合医療センター | 診療 | 91 | 新規/再診分岐、選定療養費案内 |
| 06 | 四谷メディカルキューブ | 診療 | 60 | 症状相談、緊急転送、遅刻対応 |
| 07 | 兵庫県立こども病院 | 診療（小児） | 133 | 検診後受診（乳児/学校）、残薬確認 |
| 08 | 東京衛生アドベンチスト病院 | 診療 | 78 | 時間帯判定（早朝/通常）、地域連携室転送 |
| 09 | いまきいれ総合病院 | 診療 | 93 | 当日確認→代表案内、再診症状確認、紹介状有無 |
| 10 | （配置待ち） | — | — | — |
| 11 | 帝京大学医学部附属みぞのくち病院 | 診療 | ~244（6フロー） | 全ペア最大186モジュール、31診療科・多段CMR、3営業日計算Script、動的日付挿入、DOB二段階OpenAI |

**修正確定施設（corrections/ に保存済み）**: 帯広第一病院、長野県立木曽病院、ユアクリニックお茶の水、入間ハート病院

### 1-2. 現行修正実績（本プロジェクトで対応した施設）

| 施設 | 最終版 | 主な修正内容 |
|---|---|---|
| 横浜労災病院 | v5完了 | DTMFタイムアウトパラメータ修正・Script禁止・DOB Re-confirmation追加 |
| 帝京大学附属溝口病院 | v5完了 | contextName個別化・分岐漏れ2箇所・smsFlag修正・ルート順序変更 |
| 入間ハート病院 | fixed完了 | CMR追加、無限ループ修正、profile_words充実 |
| 四谷メディカルキューブ | extracted済み | （修正対応中） |

### 1-3. リファレンス整備状況

| リソース | ファイル | 状態 |
|---|---|---|
| グローバルデフォルト値 | `reference/defaults.json` | ✅ 完全 |
| 学習済みパターン | `reference/defaults_overrides/learned_patterns.json` | ✅ 22パターン登録 |
| モジュールテンプレート | `reference/templates/module_templates.json` | ✅ 11種 |
| はい/いいえ辞書 | `reference/dictionaries/profile_words_yes_no.txt` | ⚠️ 22語のみ（不十分） |
| 生年月日辞書 | `reference/dictionaries/profile_words_dob.txt` | ✅ 47語（完全） |
| 氏名辞書 | `reference/dictionaries/profile_words_name.txt` | ⚠️ 施設別未テンプレート化 |
| はい/いいえプロンプト | `reference/prompts/openai_yes_no.txt` | ⚠️ 基本形のみ |
| 聴取不可プロンプト | `reference/prompts/openai_hearing_impossible.txt` | ✅ 基本形 |
| コンテキスト共通フィールド | `reference/context/context_fields_common.json` | ✅ 8フィールド |
| コンテキスト医療フィールド | `reference/context/context_fields_medical.json` | ✅ 診療科特化 |
| コンテキスト健診フィールド | `reference/context/context_fields_checkup.json` | ✅ 健診特化 |
| 個人情報サブフローテンプレート | `reference/subflows/` | ❌ 未作成 |
| RAG検索サブフローテンプレート | `reference/subflows/` | ❌ 未作成 |

---

## 2. VFB頻出バグパターン22個と修正方針

> **出典**: `reference/defaults_overrides/learned_patterns.json`（最終更新: 2026-04-16）

### 最重要（CRITICAL・頻度3以上）

| ID | 重要度 | 頻度 | パターン | 修正方針 |
|---|---|---|---|---|
| **VFB-016** | CRITICAL | 4 | **profile_wordsを一切生成しない** | 入力種別ごとに数十〜数百語登録。辞書テンプレート適用 |
| **VFB-021** | WARNING | 4 | Retry prompt_falseが空文字のまま | パターンA/B/C（後述）で設計 |
| **VFB-022** | WARNING | 4 | profile_wordsにフィラー・頭落ちパターン未記載 | 14種フィラー前置き＋頭落ちパターンを追加 |
| **VFB-001** | CRITICAL | 3 | ContextMatchRouterを生成しない | 用件分岐・条件分岐・終話分岐にCMR使用 |
| **VFB-002** | CRITICAL | 3 | Re-confirmation node data未生成 | 重要項目にRe-confirmation→STT→OpenAI→Retryを追加 |
| **VFB-003** | WARNING | 3 | save2db過剰（個別生成） | save-history共有参照に集約 |
| **VFB-005** | WARNING | 3 | DTMF AmiVoice STT未使用 | 数字入力全てにDTMF対応 |
| **VFB-006** | WARNING | 3 | Retry prompt_falseが空欄 | パターンA/B/C使い分け |
| **VFB-009** | WARNING | 3 | TTS命名規則が不統一 | 聴取系: 確認_{内容}、終話系: 終話_{種別} |
| **VFB-010** | INFO | 3 | Retry prompt_trueの文言が異なる | 標準値固定 |

### 重要（CRITICAL・頻度2以下）

| ID | 重要度 | 頻度 | パターン | 修正方針 |
|---|---|---|---|---|
| VFB-011 | CRITICAL | 2 | サブフロー本体未生成 | Jump参照時は必ず本体もbivrに含める |
| VFB-012 | CRITICAL | 2 | Jump to FlowのflownameがURLエンコード未対応 | `drjoy^{グループ名}${フロー名}`形式必須 |
| VFB-014 | CRITICAL | 2 | incoming-classifierが冒頭TTSより前に配置 | 正しい順序: wait→saveContextModel2DB→冒頭TTS→incoming |
| VFB-017 | CRITICAL | 1 | saveContextModel2DB fieldsが汎用のみ | 施設固有フィールド＋rangeValues追加 |
| VFB-019 | CRITICAL | 1 | DOB Re-confirmationにOpenAIプロンプト欠落 | 生年月日正規化ロジックを追加 |
| VFB-008 | WARNING | 1 | office_idがProperty.mdに未記載 | office_id={施設ID}を必須設定 |
| VFB-013 | WARNING | 1 | サブフローTTSをProperty.mdに直書き | Jump propertiesに記述 |
| VFB-015 | WARNING | 1 | 業務ロジックScript未生成 | 時刻判定・SMS送信等はJavaScriptで実装 |
| VFB-018 | WARNING | 1 | OpenAIプロンプトが施設固有化されない | DTMF優先判定、頭落ち対応、施設リスト列挙を追加 |
| VFB-020 | WARNING | 1 | 復唱確認の否定応答時に専用TTS未生成 | Re-confirmation否定→専用TTS→再聴取へ遷移 |
| VFB-007 | WARNING | 1 | RetryにSave2db未接続 | Retry subsにsave2db接続 |
| VFB-004 | WARNING | 3 | Disconnect/saveCompletionFlag過剰 | CMRで分岐し集約 |
| VFB-023 | WARNING | 1 | はい/いいえ二択にDTMF STT未使用 | DTMF AmiVoice STT Inputを使用 |
| VFB-024 | CRITICAL | 1 | 担当医contextNameが非標準（Mydoctor等） | contextName="inquiry"を使用 |
| VFB-025 | CRITICAL | 1 | 診察券なし完了フラグstatus=0（誤り） | status="2"（代表案内）を設定 |
| VFB-026 | CRITICAL | 1 | サブフローstartモジュールが誤り | 当該フロー最初のTTSモジュール名と一致させる |
| VFB-027 | WARNING | 1 | 氏名聴取にOpenAI正規化モジュール（不要） | STT→Retryのシンプル構成にする |
| VFB-028 | WARNING | 4 | 同一TTS/contextモジュールを複数定義（DRY違反） | CMRで集約 |
| VFB-029 | WARNING | 1 | Re-confirmation node dataを動的日付・分類結果読み上げに使わない | nodeName=Script/OpenAI名を設定、skipReadHour=Yes |
| VFB-030 | WARNING | 1 | 業務日計算Script（3営業日計算・当日/翌日判定）を生成しない | Java型+祝日APIのScript実装 |
| VFB-031 | WARNING | 1 | 複数CMRによる同一OpenAI出力の多段分岐を生成しない | フェーズ別CMRを個別作成 |
| VFB-032 | INFO | 1 | retry_count=2を全項目一律設定（任意聴取は1でよい場合） | 必須=2・任意=1の使い分け |
| VFB-033 | INFO | 1 | DOB Re-confirmation不使用の二段階OpenAI方式（設計バリアント） | 標準はDOB Re-confirmation推奨 |

---

## 3. コンポーネント別設計ルール

### 3-1. profile_words（辞書）設計ルール

**最重要: VFBが全く生成しないため、必ず手動設定が必要**

#### 入力種別別 対応テンプレート

| 入力種別 | 参照ファイル | 必要語数の目安 | 補足 |
|---|---|---|---|
| はい/いいえ（復唱確認） | `profile_words_yes_no.txt` | **200語以上** | 頭落ち必須（はあ/あい/い/おうです等） |
| 生年月日 | `profile_words_dob.txt` | 47語（完全） | 元号＋月日特殊読み＋頭落ち |
| 氏名 | `profile_words_name.txt` ＋施設別追加 | 300語以上 | 頭落ちはOpenAI正規化で対処 |
| 用件/区分（STTのみ） | 施設固有作成 | 100語以上 | 各選択肢の言い回し＋フィラー14種 |
| 用件/区分（DTMF+STT） | 最小限でよい | 10語以内 | 数字の読み仮名のみ |
| 診療科 | 施設固有作成 | 30〜50語 | 略称・類義語・頭落ち必須 |
| ワクチン種別 | 施設固有作成 | 20〜30語 | 施設取り扱い品目全種 |
| キャンセル理由 | 施設固有作成 | 15語以上 | 一般的な理由を網羅 |
| 日付/予約日 | `profile_words_dob.txt`ベース | 50語以上 | 曜日・月日・元号 |
| 健診コース（健診のみ） | 施設固有作成（必須） | コース数×5語 | VFBは未生成。全コース名＋略称 |

#### フィラー14種（全入力種別に適用）

```
あ / あー / あの / あのー / え / えー / えっと / えーと / ん / んー / はい / ま / まー / そうですね
```

例（「よやく」に対して）:
```
予約 あよやく
予約 あーよやく
予約 あのよやく
...（14種展開）
```

#### 頭落ちパターンルール

- 先頭1〜2音節が欠落したバリエーションを登録する
- 特に注意: `よ`, `ご`, `お`（敬語前置き）は落ちやすい
- 短い語（2〜3音節）ほど先頭音が落ちやすい

| 代表語 | 頭落ちパターン |
|---|---|
| はい（はい） | あい、い |
| そうです（そうです） | おうです、うです |
| しょうわ（昭和） | きょうわ、きょうは |
| ついたち（一日） | いたち |

---

### 3-2. OpenAIプロンプト設計ルール

#### 4本柱（必須セクション）

```
# Role   — AIの役割定義
# Context — 入力データの文脈説明（「○○という質問に対して患者が回答したテキスト」と明示）
# 出力仕様 — 出力フォーマットと選択肢（next分岐条件と完全一致）
# セキュリティ — プロンプトインジェクション防御
```

#### プロンプト種別と対応テンプレート

| 種別 | 参照ファイル | 状態 |
|---|---|---|
| はい/いいえ判定 | `reference/prompts/openai_yes_no.txt` | ⚠️ 基本形（拡張必要） |
| 聴取不可出力 | `reference/prompts/openai_hearing_impossible.txt` | ✅ |
| 生年月日正規化 | （テンプレート未作成） | ❌ |
| 診療科分岐 | （テンプレート未作成） | ❌ |
| 用件分類 | （テンプレート未作成） | ❌ |
| 氏名正規化 | （テンプレート未作成） | ❌ |

#### プロンプト網羅性の確認手順（設計時の必須チェック）

1. 直前のTTSで何を質問しているかを確認する
2. その質問に電話口で患者が返しうる回答パターンを全列挙する
3. 表記ゆれ・言い回し・省略形・同義語を `# Context` に明示する
4. 各next分岐条件と完全一致することを確認する

---

### 3-3. Retry prompt_false パターン体系

| パターン | 使用条件 | false遷移先 | prompt_false | 文言例 |
|---|---|---|---|---|
| **A. 任意→次へ進む** | 任意項目でリトライ上限 | 次のステップ | 失敗告知メッセージ | `{tts_g:かしこまりました。折り返しの際に確認させていただきます。}` |
| **B. 任意→失敗終話** | 失敗で終話する設計 | 終話_失敗 TTS | 失敗告知 | `{tts_g: 大変申し訳ございません。 うまく聞き取ることができませんでした。}` |
| **C. 必須→無限ループ** | 用件・種別など必須項目 | 同じ先頭TTS（ループ） | `""` 空文字 | そのまま最初の質問に戻す |

**判断基準**: PDFの「2回リトライ失敗した場合」の仕様を確認する。
- 「次の質問へ進む」→ A
- 「終話する」→ B
- 「繰り返す」→ C
- PDF未記載 → A（次へ進む）を採用

---

### 3-4. ContextMatchRouter（CMR）設計ルール

#### VFBが生成しない → 全案件で手動追加が必要

**使用場面:**
- 用件分類（予約/変更/キャンセル等）
- 初診/再診分岐
- はい/いいえの複雑な分岐
- 複数出力値から遷移先を決定する場面全般

#### params必須設定

```json
{
  "module1Name": "参照モジュール名",
  "module2Name": "参照モジュール名（同じ値を必ず設定）",
  "module1Value1": "値1",
  "module2Value1": "値1（module1Value1と同値）",
  "module1Value2": "値2",
  "module2Value2": "値2（同値）",
  ...（使用しないスロットは空文字で埋める）
}
```

**重要**: `module1Name` と `module2Name` は常に同じ値。片方だけでは動作しない。

#### next条件フォーマット

```json
{"condition": "^1$", "label": "値1にマッチ", "nextModuleName": "遷移先A"},
{"condition": "^2$", "label": "値2にマッチ", "nextModuleName": "遷移先B"},
{"condition": "^.*$", "label": "フォールバック", "nextModuleName": "デフォルト遷移先"}
```

---

### 3-5. サブフロー設計ルール

#### 「Jump参照があれば本体も必ず.bivrに含める」（VFB-011の根本対策）

VFBの最大の欠陥: Jump to Flowの参照は生成するが、参照先サブフローの本体を生成しない。

**標準サブフロー種別と構成モジュール数:**

| サブフロー種別 | 標準モジュール数 | 主な構成 |
|---|---|---|
| 個人情報（氏名/生年月日/電話番号） | 39〜50 | STT×3＋ReConf×3＋OpenAI×3＋Retry×3 |
| RAG検索 | 11〜15 | TTS→STT→RAG→OpenAI→TTS分岐 |
| 診療科聴取 | 70〜73 | TTS→STT→OpenAI（科名判定）→CMR（対象/非対象） |
| 電話番号確認 | 19 | incoming-classifier→TTS→STT→ReConf→OpenAI |

---

### 3-6. レイアウト座標ルール

#### 基本原則
- y軸: 下が正（フローは上から下へ）
- **LAYOUT-003 回避**: `y_range ≥ modules × 100px` を必ず確保
- 83モジュールなら `y_range ≥ 8,300px`

#### 標準ステップ間隔

| 関係 | Δy |
|---|---|
| TTSからSTT/DTMF | +220 |
| TTSからOpenAI | +460 |
| TTSからRetry | Δx=-280, Δy=+460 |
| TTSからsave2db | Δx=-280, Δy=+220 |
| ステップ間（TTS→次TTS） | +800 |
| Re-confirmationを含むステップ | +1200以上 |

---

## 4. 現状の生成品質評価

### 3-7. pair_11 固有パターン — 帝京大学医学部附属みぞのくち病院

#### 3-7-1. Re-confirmation node dataの汎用的な活用

`Re-confirmation node data` は `nodeName` に任意のモジュール名を指定することで、そのモジュールの出力結果を `#data#` に埋め込んで読み上げることができる。DOB復唱以外の用途：

| 用途 | nodeName に設定するモジュール | Property.md prompt 例 |
|---|---|---|
| 動的日付挿入（3営業日後） | `script_日付取得`（Script） | `{tts_g:#data# 以降の〜}` |
| 用件名の読み上げ（変更/キャンセル等） | `OpenAI_用件確認`（OpenAI） | `{tts_g:#data# の理由を〜}` |

必須設定: `skipReadHour="Yes"` で時刻読み上げを無効化すること。

#### 3-7-2. 3営業日計算Scriptパターン

「3診療日以内に折り返し」を冒頭アナウンスに動的挿入するためのJavaScriptパターン：

```javascript
// script_日付取得: holidays-jp.github.io から祝日取得 → 3営業日後を計算
var apiUrl = "https://holidays-jp.github.io/api/v1/" + year + "/date.json";
// ... Calendar計算 ...
$runner.setResult(resultMonth + "月" + resultDay + "日");  // "5月15日" 形式で返す
```

```javascript
// script_3days分岐: 現在の予約日が当日/翌日/翌々日なら代表案内に誘導
var reservationRaw = $runner.getModuleResult("openAI_現在の予約日");
// ... 日付比較 ...
$runner.setResult("代表案内");  // または "success"
```

Script名は `script_` プレフィックス必須（SCR-001）。

#### 3-7-3. OpenAIプロンプトのアルゴリズム形式

31診療科以上の大病院では、OpenAIプロンプトに明示的なアルゴリズム（STEP_A〜STEP_G）と Few-shot 例（表形式）を組み込む「アルゴリズム形式」が有効：

```
STEP_A: 不明明示判定（「わからない」「何科」→ 登録なし）
STEP_B: 入力正規化（全角半角・長音記号・中黒）
STEP_C: DTMF入力→NO_RESULT
STEP_D: 完全一致判定
STEP_E: 部分一致判定（長い語優先: 消化器外科 > 外科）
STEP_F: 症状のみ→NO_RESULT（症状からの推測禁止）
STEP_G: 該当なし→NO_RESULT
```

`# ⚠ 絶対ルール` セクションで「症状から推測しない」「文脈補完しない」を明示することで誤分類を防ぐ。

#### 3-7-4. 新status値・smsFlag値

| status | smsFlag | 意味 | 用途 |
|---|---|---|---|
| 7 | -1 | 診察券なし/番号不明終話 | 診察券番号が不明で受け付けできない場合 |
| 22 | -1 | 直接来院案内 | 特定診療科は電話受付不可・直接来院に誘導 |
| -1（smsFlag） | — | SMS明示的無効化 | 代表案内・非通知・時間外等でSMSを送らない場合 |

> 標準のsmsFlag=0とsmsFlag=-1の違いは施設設計次第。pair_11では代表案内系に一律-1を使用。

---

### 4-1. 評価サマリー

```
現状の生成品質: ★★★☆☆（3/5）
「VFBの出力をそのまま使える」レベル: ×
「人間が作ったものと同等」レベル: △（ルーチン部分は可、施設固有設計は要確認）
```

### 4-2. 領域別の評価

#### ✅ 自動修正が確実にできる領域

| 修正内容 | 根拠 | 対応パターン |
|---|---|---|
| Retry prompt_false設定 | パターンA/B/Cが確立 | VFB-006/021 |
| TTS next label修正 | 「Next Module」固定 | TTS-001 |
| STT success条件 `^.+$` | ルール確定 | STT-003/004 |
| Retry condition/label | true/false, Retry/No more固定 | R-001〜004 |
| DTMF timeout/promptパラメータ | 詳細ルール確定 | DTMF-001〜004 |
| save2db接続確認 | subs接続ルール確定 | SB-001/002 |
| stop_by_dtmf Yes/No修正 | TTS-002 |
| contextName個別化 | 2026-04-14のルール追加 | CTX-010 |
| DTMFのtimeoutパラメータ名 | timeout（timeout_msでない） | 横浜労災修正より |
| Script禁止・代替方法 | Brekeke非対応API確認 | SCR-001/002 |

**評価**: ルールが明確で、スクリプトによる自動修正が可能。

#### ⚠️ 確認が必要だが方針は確立している領域

| 修正内容 | 確認が必要な理由 | 必要な入力 |
|---|---|---|
| profile_words充実化 | 施設固有の診療科・用件が必要 | PDFの選択肢一覧 |
| OpenAIプロンプト施設固有化 | 診療科リスト・分岐仕様 | PDF仕様 |
| ContextMatchRouter追加 | どこに分岐を設けるかはPDF依存 | フロー設計書 |
| Re-confirmation追加 | どの項目に復唱を設けるかはPDF依存 | PDF仕様 |
| サブフロー構成 | 何をサブフロー化するかは施設規模次第 | PDF仕様＋モジュール数 |
| Retry prompt_false パターン選択 | PDFの「2回失敗した場合」の仕様確認 | PDF仕様 |
| CMR用 contextName設定 | 何を聴取するか施設固有 | PDF仕様 |

**評価**: PDFを読めば判断できる。人間によるレビュー1回で確定可能。

#### ❌ 現状では自動化困難な領域

| 修正内容 | 理由 | 対応方針 |
|---|---|---|
| 施設固有の業務ロジック設計 | PDFにも記載がない暗黙ルールが存在 | 顧客確認必須 |
| 完全に新規のフロー設計（VFBなしの0→1） | 参照ペアなしでは設計不可 | VFB出力をベースにする前提 |
| profile_words 診療科辞書の網羅性 | 読み仮名・略称・誤認識パターンが施設固有 | 半自動（AI+人間確認） |
| OpenAI プロンプトの診療科リスト | 全診療科名をPDFから正確に抽出 | PDF解析＋人間確認 |

**評価**: 現状では人間の判断が不可欠。完全自動化には施設データの構造化が必要。

### 4-3. 具体的な一致率シミュレーション

帯広第一病院の差分分析（VFB vs 人間版）をベースにした推定:

| 観点 | VFBそのままの一致率 | bivr-checker修正後の推定一致率 |
|---|---|---|
| 構造的正確性（CRITICALエラー0） | 約30% | **約85%** |
| Retryパラメータ（prompt_true/false） | 約40% | **約95%** |
| profile_words充実度 | 約5% | **約60%** ※施設固有語は手動 |
| OpenAIプロンプト品質 | 約40% | **約75%** |
| レイアウト品質 | 約50% | **約80%** |
| **総合一致率** | **約30%** | **約80%** |

> ※「人間が作ったものと同等」= 一致率90%以上と定義した場合

### 4-4. 結論

> **「ルーチン修正（CRITICAL/WARNING対応）」は現状でも十分な品質で自動化できる。**
> **ただし、施設固有の設計判断（profile_words・OpenAIプロンプト・サブフロー構成）は、PDFを読んでAIが提案し、人間が確認するサイクルが最低1回必要。**

**現在のビジネス価値:**
- VFB出力の「そのまま使えないもの」を「レビュー1回で使えるもの」に変換できる
- 人間の作業時間: VFBからの修正 → 約2〜4時間 → bivr-checker経由 → **約30分〜1時間**（推定）

---

## 5. 不足している知識・ギャップ

### 高優先度（早期整備が必要）

#### GAP-1: profile_words yes_no辞書の不足（最重要）

- **現状**: 22語のみ
- **必要**: 200語以上（フィラー14種×全選択肢＋頭落ちパターン）
- **対処**: `profile_words_yes_no.txt` を教師データpair_01の実装を参考に拡張
- **影響**: 全施設の復唱確認STTの認識精度に直結

#### GAP-2: OpenAIプロンプトテンプレートの不足

不足しているテンプレート:
- 生年月日正規化（DOB Re-confirmation用）
- 診療科分岐（施設別科名リスト展開）
- 用件分類（網羅的な言い回しパターン）
- 氏名正規化（カタカナ変換、頭落ち対応）

#### GAP-3: サブフロー標準テンプレートが未作成

- `reference/subflows/personal_info_standard.json` — 未作成
- `reference/subflows/rag_search_standard.json` — 未作成
- `reference/subflows/clinical_department_standard.json` — 未作成

サブフローが実装されていないと、長野県立木曽病院のような案件では修正がほぼ不可能（152→290モジュールの差分が発生）。

#### GAP-4: 施設固有contextName設定の自動化

- 現状: `contextName` の個別化ルールはあるが、フィールド名の命名規則が不完全
- 帝京溝口病院v3で発覚（2026-04-14ルール追加済み）
- **対処**: `reference/context/context_name_mapping.json` に拡張フィールド定義を追加

### 中優先度

#### GAP-5: Property.md施設種別別テンプレート未整備

- 診療/健診/小児科ごとに必要なセクションが異なるが統一フォーマットがない
- 横浜労災病院・帝京溝口病院のProperty出力を参照してテンプレート化

#### GAP-6: チェック結果→修正の自動マッピング

- check_prompt.md（71エラーコード）と learned_patterns.json（22パターン）の対応表が未作成
- エラーコード → 修正スクリプト の自動紐付けができていない

### 低優先度

#### GAP-7: フィラー・頭落ち辞書の自動生成ツール

- 現状は手動で辞書を作成している
- Pythonスクリプトで「基本語→フィラー前置き14種×語尾20種」を自動展開できる

#### GAP-8: corrections/フォルダの整理

- 修正前後ペアが4施設分蓄積されているが、diff_report.mdからのパターン抽出が不完全
- learned_patterns.jsonへのフィードバックが一部未反映の可能性

---

## 6. 改善ロードマップ

### Phase 2（即時対応可能）

| 作業 | 優先度 | 効果 |
|---|---|---|
| profile_words_yes_no.txt を200語以上に拡張 | 最高 | 全施設の復唱確認品質向上 |
| 生年月日正規化プロンプトテンプレート作成 | 高 | DOB Re-confirmationの完全対応 |
| 診療科分岐プロンプトテンプレート作成 | 高 | 診療シナリオの自動化精度向上 |
| GAP-4: contextName mapping拡張 | 高 | コンテキスト設定漏れの防止 |

### Phase 3（中期整備）

| 作業 | 優先度 | 効果 |
|---|---|---|
| サブフロー標準テンプレート3種作成 | 高 | 長野県立木曽病院クラスの案件を自動化 |
| エラーコード→修正スクリプト対応表作成 | 中 | fixer agentの精度向上 |
| Property.md施設種別別テンプレート作成 | 中 | Property品質の安定化 |

### Phase 4（長期整備）

| 作業 | 優先度 | 効果 |
|---|---|---|
| profile_words自動生成スクリプト | 低 | 辞書作成工数を1/5に削減 |
| fixer agentの全パターン実装 | 高 | 修正工数を大幅削減 |
| VFBへのフィードバック | 低 | 根本的な生成品質向上 |

---

## 付録: デフォルト値クイックリファレンス

### AmiVoice設定（全施設共通）

```
uri: ws://10.0.20.11:8000/ws
language: ja
engine: 入力汎用
silent_detection_ms: 2000
timeout_ms: 30000
probability: 0.6
detection_flag: 検出しない
save_log: false
keep_filter_token: true
```

### リトライ設定

```
retry_count: 2（標準。PDF指定があればそれに従う）
prompt_true: {tts_g:申し訳ございません。 うまく聞き取りが出来ませんでした。 再度、}
matchingmethod: 0（Retryのみ。他は全て1）
```

### DTMF設定

```
prompt: {recstart}（JSON内に直接記述）
max_dtmf_length: 10（デフォルト）、用件選択=1、電話番号=11、生年月日=8
retry: 2
termdtmf: #
remove_term: Yes
stop_play_when_speech: Yes
timeout: 30000（DTMFタイムアウト。timeout_msとは別）
```

### コンテキスト名マッピング

| 日本語 | contextName | displayType |
|---|---|---|
| 氏名 | patientName | TEXT |
| 生年月日 | patientDateOfBirth | DATE_OF_BIRTH |
| 診療科 | clinicalDepartment | DEPARTMENT |
| 電話番号(着信) | telephoneNumber | PHONE_NUMBER_CALL |
| 連絡先電話番号 | additionalPhoneNumber | PHONE_NUMBER |
| 区分/用件 | classification | CLASSIFICATION |
| 診察券番号 | medicalCardNumber | NUMBER |

### 状態フラグ（saveCompletionFlag2db）

```
未処理: 1
代表案内: 2
転送: 3
時間外: 6
途中切断: 0（禁止: 明示的に設定しない）
完了フラグ_5: 5（禁止: 使用不可）
```

---

*このドキュメントは `bivr-checker` プロジェクトの作業定義書です。CLAUDE.md と合わせて参照してください。*
