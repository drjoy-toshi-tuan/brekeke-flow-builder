# フロー設計・テスト共通仕様 v1.0（P1〜P7）

> **制定: 2026-07-09** — このドキュメントは P1〜P7 全パターンに適用される設計・実装・テストの共通ルール。
> 既存の `deterministic-replacement-roadmap.md`・`SKILL_FAQ_Scripts.md`・`connection_test/REQUIREMENTS.md` を補完する。

---

## 1. Scripts 優先・OpenAI フォールバック 設計原則

### 1-1. 基本方針

> **処理ブロックは Scripts（ES5）で実装する。OpenAI は「決定論で書けない部分」のみ使う。**

| ブロック種別 | 実装方針 |
|---|---|
| 用件判定（予約/変更/キャンセル/お問い合わせ等） | Scripts キーワードマッチ → NO_RESULT のみ OpenAI フォールバック |
| FAQ 問合せ判定 | Scripts 完全一致マッチ → NO_RESULT のみ OpenAI フォールバック |
| Yes/No 判定 | Scripts 類義語マッチ（SKILL_B 参照） → NO_RESULT のみ OpenAI フォールバック |
| 診療科正規化 | blinder/binder モジュール（認定済） → Scripts → OpenAI フォールバック |
| 日付・予約日解析 | 現在の予約日 script 系（認定済）→ OpenAI は残留期間中のみ |
| 氏名カナ聴取 | OpenAI 残留（STT 揺れ吸収が本質的に曖昧なため）|
| 自由発話収集（`free_text` ブロック） | **Scripts 正規化**（全角→半角・スペース/句読点除去）→ save。OpenAI 不使用 |
| FAQ 照合（`faq` ブロック） | `method:script`: STT → Scripts(マッチ+setObject) → TTS({tts_g:<% scripts-faq %>}) / `method:openai`: STT → OpenAI(カテゴリ) → Scripts(回答ルックアップ+setObject) → TTS({tts_g:<% scripts-faq %>}) |
| 希望日・希望時期聴取（`hearing` + OpenAI） | `hearing` (output_format: text) で自由発話収集 → OpenAI で正規化（`docs/ai/skills/SKILL_希望日.md` の**固定プロンプトをそのまま使用**。施設固有の修正禁止。NO_RESULT を返さない仕様） |

### 1-2. フォールバック必須条件

以下を **すべて** 満たす場合は OpenAI フォールバックを追加すること:

- 実際の電話音声で多パターンの言い回しが想定される（10 パターン以上）
- 誤認識が業務上許容できない（予約/変更/キャンセルの取り違え等）
- AmiVoice 辞書登録だけでは吸収しきれない

フォールバック不要の条件: 固定数値（電話番号・診察券番号・生年月日）、DTMF 入力専用。

### 1-3. Scripts 実装テンプレート（用件判定）

```javascript
// getModuleResult は AmiVoice STT 結果モジュール名を指定
var rawInput = $runner.getModuleResult("入力_用件");
var text = "";
if (rawInput && typeof rawInput === "object" && rawInput.text) {
    text = String(rawInput.text).trim();
} else if (typeof rawInput === "string") {
    text = rawInput.trim();
}
// 正規化: 全角スペース・半角スペース・句読点・疑問符を除去
text = text.replace(/[　 ]/g, "").replace(/[？?。、！!「」]/g, "");

// --- キーワードマッチ（追加・変更は必ず AmiVoice 辞書も更新） ---
if (/予約|よやく/.test(text)) {
    $runner.setResult("予約");
} else if (/変更|へんこう|かえる|変え/.test(text)) {
    $runner.setResult("変更");
} else if (/キャンセル|取り消し|とりけし/.test(text)) {
    $runner.setResult("キャンセル");
} else if (/問い合わせ|問合せ|質問|確認|聞き/.test(text)) {
    $runner.setResult("お問い合わせ");
} else {
    $runner.setResult("NO_RESULT");
}
```

Next 条件（必須 5 分岐）:

| 条件 | next モジュール |
|---|---|
| `^予約$` | 予約 (saveContext) |
| `^変更$` | 変更 (saveContext) |
| `^キャンセル$` | キャンセル (saveContext) |
| `^お問い合わせ$` | お問い合わせ (saveContext) |
| `^NO_RESULT$` | OpenAI_入力_用件 |
| `^.*$` | OpenAI_入力_用件 （最終 catch-all） |

### 1-4. Scripts 実装テンプレート（`free_text` 正規化）

> **2026-07-13 改定**: `free_text` ブロックは「STT → save のみ」から「STT → Scripts 正規化 → save」に変更。
> OpenAI は使わない（判定・分類なし。テキスト整形のみ）。

`free_text` ブロックが scaffold で生成する Script モジュール（`script_{step}` として挿入）:

```javascript
// free_text 正規化スクリプト — 整形のみ、分類なし
var rawInput = $runner.getModuleResult("入力_{step}");
var text = "";
if (rawInput && typeof rawInput === "object" && rawInput.text) {
    text = String(rawInput.text).trim();
} else if (typeof rawInput === "string") {
    text = rawInput.trim();
}
// 全角→半角（英数字）
text = text.replace(/[Ａ-Ｚａ-ｚ０-９]/g, function(c) {
    return String.fromCharCode(c.charCodeAt(0) - 0xFEE0);
});
// スペース・句読点・括弧を除去
text = text.replace(/[　 \t]/g, "").replace(/[。、！!？?「」【】（）()・…]/g, "");

$runner.setResult(text || "NO_RESULT");
```

scaffold での配置順（`free_text` ブロック内）:

```
TTS_{step}  →  入力_{step}(STT)  →  script_{step}(正規化)  →  save-{save_to}  →  next
                                         ↓ NO_RESULT
                                    リトライ_{step}  →（上限超過）→ next（エラー終話）
```

`conditions` での分岐は原則不要（分類しない）。健診キーワード等の分岐が必要な場合は
`free_text` ではなく `hearing (output_format: enum)` + `script (A: enum_classifier)` を使うこと。

### 1-5. `faq` ブロックの scaffold 配置テンプレート（2026-07-13 改定）

> **改定内容**: ANSWER 後に回答読み上げ TTS（`FAQ回答_{step}`）を scaffold が自動生成するよう変更。
> `{tts_g:<% scripts-faq %>}` の prompt は IVR プロパティ側で設定する。

#### method: "script"（デフォルト）

```
TTS_{step}（質問）
  → 入力_{step}（STT）
      → script_{step}（Scripts: faqMap完全一致 + setObject("scripts-faq", 回答文)）
          → ANSWER  → FAQ回答_{step}（TTS: {tts_g:<% scripts-faq %>}）→ next
          → NO_RESULT → リトライ_{step} →（上限超過）→ failure_flag（エラー終話）
```

`script_{step}` が出力する値:
- 一致: `setObject("scripts-faq", 回答文)` + `setResult("ANSWER")`
- 不一致: `setResult("NO_RESULT")`

#### method: "openai"

```
TTS_{step}（質問）
  → 入力_{step}（STT）
      → script_{step}（OpenAI: 質問カテゴリ/番号を返す）
          → NO_RESULT → リトライ_{step}
          → matched   → script_{step}_answer（Scripts: answerMap[category] → setObject("scripts-faq", 回答文)）
                            → ANSWER    → FAQ回答_{step}（TTS: {tts_g:<% scripts-faq %>}）→ next
                            → NO_RESULT → リトライ_{step}
```

`FAQ回答_{step}` の IVR プロパティ（prompt）は **`{tts_g:<% scripts-faq %>}`** 固定。
prompter は `script_{step}` の OpenAI prompt と `script_{step}_answer` の answerMap を記述する。

---

## 2. FAQ ブロック適用ルール

### 2-1. 適用必須の箇所（4箇所固定）

以下の **4箇所** は必ず `Scripts-FAQ_*` パターン（SKILL_FAQ_Scripts.md）を使うこと。RAG または OpenAI のみの実装は禁止。

| # | 入力スロット名 | 用途 | 対応 Scripts-FAQ モジュール名 |
|---|---|---|---|
| 1 | **内容確認** | お問い合わせ subflow の最初の質問入力 | `Scripts-FAQ_問合せ` |
| 2 | **最後の質問** | メインフロー（または subflow）の追加質問（はい → 2回目 FAQ） | `Scripts-FAQ_最後の質問` |
| 3 | **その他の問い合わせ** | お問い合わせ subflow 内の補足質問スロット | `Scripts-FAQ_その他の問い合わせ` |
| 4 | **その他の質問** | 別フロー内の追加質問スロット | `Scripts-FAQ_その他の質問` |

> **注**: 上記4箇所以外で FAQ 照合が必要になった場合は、新スロット名を追加する前に設計レビューを実施すること。

### 2-2. 必須実装パターン

```
入力_相談_問合せ（AmiVoice STT）
  → Scripts-FAQ_{用途名}
      → ^ANSWER$  → TTS_FAQ回答_{用途名}（tts_text: {tts_g:<%scripts-faq%>}）
      → ^NO_RESULT$ → openAI_{用途名}（fallback）
```

### 2-3. FAQ マップ管理ルール

- faqMap のキーは「正規化後のテキスト」（スペース・句読点除去後）で設計する
- 登録エントリ追加時は AmiVoice 辞書にも対応キーワードを追加すること
- TTS 回答文の読み上げ確認（数字・記号・英字の読み方）を投入前に必須実施

### 2-4. 追加質問（最後の質問）が存在する場合

```
入力_追加の質問（DTMF/AmiVoice）
  → はい → 入力_相談_問合せ②（AmiVoice STT）
              → Scripts-FAQ_{用途名}_最後の質問
                  → ^ANSWER$  → TTS_FAQ回答_最後の質問
                  → ^NO_RESULT$ → openAI_最後の質問
  → いいえ → save-details → 終話
```

---

## 3. Retry / TTS サブモジュール化禁止

### 3-1. ルール

> **Retry（`drjoy^Text To Speech$Speech Retry`）と TTS（`drjoy^Text To Speech$Text to speech`）は
> サブフロー（sub|）として切り出してはならない。メインフロー内にインライン配置する。**

**禁止例:**
```
入力_用件 → jump_to_sub|tts_retry → (sub|tts_retry) → return
```

**正しい例:**
```
入力_用件 → リトライ_用件（Retry TTS）→ 入力_用件  （同一フロー内にインライン）
```

### 3-2. 理由

- サブフロー化すると `connection_test/stub_stt_connection.py` がリトライパスを誤検出し、テスト stub が正しく生成されない
- フロー構造の視認性が悪化し、`tester.py` の AUD-1/AUD-2 チェックが通りにくくなる

### 3-3. P7 テストでの扱い

テストスタブ生成時（`stub_stt_connection.py`）は **Retry / TTS モジュールを stub 対象から除外**する。
Retry exhaust ケースは `inject` の試行列で制御する（例: `["NO_RESULT", "NO_RESULT"]` = 2回とも失敗 → exhaust）。

---

## 4. テストケース多様化ルール（P7 連結テスト）

### 4-1. 原則

| ルール | 内容 |
|---|---|
| **全分岐カバレッジ** | メインフローの全エッジを少なくとも 1 ケースで通過すること |
| **入力の多様性** | 同一フィールドに同じ値を使いまわさない（例: 診療科=整形外科 を複数ケースで重複させない） |
| **用件別に最低 2 パターン** | 予約/変更/キャンセル/お問い合わせ各用件: ①定型入力（単語） + ②自然発話（文章）の最低 2 ケース |
| **FAQ 両経路** | Scripts ANSWER ケース（完全一致） + NO_RESULT（fallback）ケースの両方を必ず含む |
| **個人情報バリエーション** | 氏名・生年月日・診察券番号・電話番号は全ケースで異なる値を使う |

### 4-2. 入力値設計の指針

```
用件   : 定型語（例: 予約）/ 自然文（例: 予約したいんですが）/ 複合語（例: 診察の予約を取りたい）
診療科 : 毎ケース異なる科を使用（整形外科/皮膚科/眼科/泌尿器科/循環器内科/外科...）
氏名   : 実在しない架空氏名（カタカナ）をケースごとに変える
生年月日: 年代・フォーマット多様に（19800101 / 昭和55年1月1日 / 平成12年12月12日...）
診察券番号: 7桁の数値をケースごとにユニークに
電話番号: 070/080/090/03 等で多様化
```

### 4-3. 禁止パターン

- `入力_用件: ["予約"]` を複数ケースで使う（Scripts_用件 のキーワードマッチ経路が 1 ケースしか検証されない）
- 診療科・氏名・電話番号の値を複数ケースで流用
- FAQ テストで同じ質問文を 2 回使う

---

### 4-4. マスターパターン CSV（テストケース原典）

> **テストケースの入力値はマスター CSV から引用すること。手書きで新規に作成してはならない。**

| 項目 | 内容 |
|---|---|
| **ファイルパス** | `docs/testcase_master/master_test_patterns_v3.csv` |
| **管理者** | @TS-dong-nc（保護ゾーン — 変更には PR レビュー必須） |
| **主要カラム** | `case_id` / `flow_type` / `category` / `case_name` / `入力_*` / `期待_*` / `期待_終端` / `備考` |

**`flow_type` 値と対象フロー:**

| flow_type | 対象フロー | ケース例 |
|---|---|---|
| `診療` | 診療予約メインフロー | S-xxx |
| `健診` | 健診予約フロー | K-xxx |
| `地域連携` | 地域連携（病診連携）フロー | R-xxx |
| `共通` | フロー横断の境界値 | C-xxx |
| `診療`（実ログ） | 実 IVR ログから抽出したパターン | L-xxx |

**`category` 分類:**

| prefix | 種別 |
|---|---|
| `正常_*` | ゴールデンパス（フルフロー完走） |
| `口語_*` | 自然発話・口語表現 |
| `STT誤認識` | AmiVoice 音響混同・誤読みパターン |
| `症状ベース` | 診療科が不明のまま症状で問い合わせ |
| `生年月日` | 和暦/漢数字/不正日付 等のバリエーション |
| `口語_希望日` | 相対日付・あいまい日付（お盆明け・いつでも等）|
| `エラー` | 沈黙・意味不明発話・桁数不足等の異常入力 |
| `システム` | 非通知・時間外・全聴取失敗 |
| `高齢者` | 長文フィラー・間接表現・大正生まれ等 |
| `実ログ_*` | 実 IVR ログで観測された実際の発話パターン |

### 4-5. マスター CSV から P7 テストケース JSON を生成する手順

```bash
# 施設・フロータイプを指定して P7 ケース JSON を生成
python tools/gen_p7_from_master.py \
    --master docs/testcase_master/master_test_patterns_v3.csv \
    --flow-type 診療 \
    --facility 東京都立豊島病院 \
    --flow-name 診療 \
    --out output/scenarios/東京都立豊島病院_診療/テストケース仕様_東京都立豊島病院_診療_$(date +%Y%m%d).json
```

**生成ロジック（`tools/gen_p7_from_master.py`）:**

1. CSV を読み込み `flow_type` でフィルタリング
2. 各行を P7 ケース JSON スキーマ（`inject` / `expect` 形式）に変換:
   - `入力_*` カラム → `inject` ステップ列
   - `期待_*` カラム → `expect` 値
   - `期待_終端` → `expect_terminal`
   - `備考` → `note`
3. `{YOYAKU}` 等のプレースホルダーは施設設計書の `step_details` から解決
4. 多様性チェック: 同一フィールドの重複値を警告出力
5. `meta` ブロックを自動付与（`generated_from`, `facility`, `flow`, `generated_at`）

**出力 JSON スキーマ（抜粋）:**

```json
{
  "meta": {
    "facility": "東京都立豊島病院",
    "flow": "診療",
    "generated_from": "docs/testcase_master/master_test_patterns_v3.csv",
    "generated_at": "2026-07-09"
  },
  "cases": [
    {
      "case_id": "S-001",
      "category": "正常_予約",
      "case_name": "新規予約_内科_フル",
      "inject": {
        "入力_用件": "予約です",
        "入力_通院歴": "初めてです",
        "入力_診療科": "内科でお願いします"
      },
      "expect": {
        "期待_用件": "予約",
        "期待_診療科": "内科",
        "expect_terminal": "通話完了"
      },
      "note": ""
    }
  ]
}
```

---

## 5. IVR ログ受入・分析・レポート

### 5-1. IVR ログ CSV フォーマット

Brekeke が出力する IVR Log CSV のカラム構成:

| カラム | 内容 | 例 |
|---|---|---|
| col0 | コール ID | `ABC-20260709-001` |
| col1 | （内部） | — |
| col2 | 発信者番号 | `0312345678` |
| col3 | （内部） | — |
| col4 | フロー名 | `drjoy^と）東京都立豊島$T_M｜診療` |
| col5 | 日時 | `2026-07-09 14:32:00` |
| col6 | 通話時間（秒） | `142` |
| col7 | トレース文字列 | `key:value;key:value;...` |

**col7 トレース文字列のパース規則:**
- セミコロン（`;`）区切り
- 各要素は `key:value` 形式
- key にコロンを含む場合は最初の `:` で分割
- 改行・タブは無視

### 5-2. ログから確認すべき項目

| 確認項目 | トレースキー | 期待値 |
|---|---|---|
| Scripts_用件 判定結果 | `Scripts_用件_result` | 予約/変更/キャンセル/お問い合わせ/NO_RESULT |
| FAQ マッチ結果 | `Scripts-FAQ_*_result` | ANSWER / NO_RESULT |
| FAQ 回答文 | `scripts-faq` | faqMap 登録値と一致 |
| 用件分岐先 | `用件` | 予約/変更/キャンセル/お問い合わせ |
| SAVE チェックポイント | `SAVE-予約` / `SAVE-変更` / `SAVE-キャンセル` | 完了 |
| 終端 | 最後に現れる終話モジュール名 | 終話①/終話②/終話③/終話 |
| OpenAI フォールバック発動 | `OpenAI_入力_*` の有無 | Scripts マッチ成功時は不在 |

### 5-3. レポート生成ツール（`tools/ivr_log_report.py`）

```
python tools/ivr_log_report.py \
    --csv <path/to/20260709.csv> \
    --facility 東京都立豊島 \
    --out output/scenarios/東京都立豊島病院_診療/ivr_log_report_20260709.md
```

**出力レポート内容:**
1. コールサマリー（総件数・平均通話時間・フロー別件数）
2. 用件分類分布（予約/変更/キャンセル/お問い合わせ）
3. Scripts_用件 マッチ率 vs OpenAI fallback 発動率
4. FAQ ヒット率（ANSWER vs NO_RESULT 比率）
5. 終端分布（どの終話に着地したか）
6. 異常ケース一覧（TIMEOUT多発・終端未到達・エラーモジュール）

---

## 6. パターン別適用サマリー（P1〜P7）

| Pattern | 作業内容 | 適用ルール |
|---|---|---|
| **P1 新規構築** | 設計書 YAML → scaffold → **gen_scripts（§8）** → prompter | §1 Scripts優先, §2 FAQ適用, §3 Retry/TTS インライン, §8 Scripts自動生成 |
| **P2 既存修正** | 設計書修正 → fixer パッチ | §1 Scripts優先（改修箇所から適用）, §3 Retry/TTSインライン |
| **P3 サブフロー再利用** | copy_subflows.py 実行 | §3 サブフロー内の Retry/TTS もインライン確認 |
| **P4 プロパティ生成** | gen_properties.py 実行 | §2 FAQ回答TTS プロパティ確認 |
| **P5 validator/auto_fixer** | 構造チェック | §1 Scripts未接続の generate_by_OpenAI を WARNING 対象に |
| **P6 部品受入** | oracle_gate + 実機 | §1 Scripts部品の oracle 100% 必須 |
| **P7 連結テスト** | stub_stt_connection.py + 実機 | §3 Retry/TTS除外, §4 テストケース多様化, §5 ログ分析 |

---

## 7. AmiVoice 辞書管理ルール

Scripts キーワードマッチが機能するには AmiVoice が正しくテキスト変換する必要がある。
Scripts に新しいキーワードを追加・変更した場合は **必ず AmiVoice 辞書も同期する**。

### 7-1. 辞書ファイル構成

| ファイル | 役割 | 管理 |
|---|---|---|
| `docs/amivoice/base_keywords.yaml` | 全施設共通のマスターキーワード定義（`target_nodes` フィールドで配布先ノードを指定） | 保護ゾーン（PR 必須） |
| `docs/amivoice/misrecognition_log.csv` | 実 IVR ログから抽出した誤認識補正エントリ | 保護ゾーン（都度追加） |
| `output/scenarios/{施設}_{flow}/amivoice/{ノード名}.csv` | **ノード別**登録申請 CSV（生成物）— STT 入力モジュール 1 つにつき 1 ファイル | 自由ゾーン（自動生成） |

**ノード別出力の設計思想:** AmiVoice STT モジュールごとに認識対象語彙が異なる（用件入力ノードには診療科名不要、診療科入力ノードには曜日名不要など）。`base_keywords.yaml` の各エントリに `target_nodes` リストを持たせることで、ノード固有の最小語彙セットを自動生成する。

### 7-2. 辞書生成コマンド

```bash
# 基本（マスター + 設計書 script_blocks から生成）
python tools/gen_amivoice_dict.py \
    --base     docs/amivoice/base_keywords.yaml \
    --yaml     output/scenarios/東京都立豊島病院_診療/設計書_東京都立豊島病院_診療.yaml \
    --facility 東京都立豊島病院 \
    --flow     診療 \
    --out-dir  output/scenarios/東京都立豊島病院_診療/amivoice

# 実ログ追加（misrecognition_log.csv を upload 後）
python tools/gen_amivoice_dict.py \
    --base     docs/amivoice/base_keywords.yaml \
    --yaml     output/scenarios/東京都立豊島病院_診療/設計書_東京都立豊島病院_診療.yaml \
    --log      docs/amivoice/misrecognition_log.csv \
    --facility 東京都立豊島病院 \
    --flow     診療 \
    --out-dir  output/scenarios/東京都立豊島病院_診療/amivoice

# OpenAI フォネティックエイリアス生成を追加（任意）
python tools/gen_amivoice_dict.py ... --openai-alias
```

実行すると `output/scenarios/東京都立豊島病院_診療/amivoice/` 配下に以下のようなファイルが生成される:

```
amivoice/
  入力_用件.csv
  入力_診療科.csv
  入力_生年月日.csv
  入力_予約希望日.csv
  入力_変更希望日.csv
  入力_診察券番号.csv
  入力_相談_問合せ.csv
  入力_追加の質問.csv
  入力_内容確認.csv
  入力_その他の問い合わせ.csv
  ...
```

**入力ソースの優先順位:**
1. `misrecognition_log.csv`（実ログ由来 — 最も確度が高い）
2. `base_keywords.yaml`（マスター定義 — `target_nodes` フィールドで配布先ノードを絞る）
3. 設計書 YAML `script_blocks`（施設固有キーワード — `input_module` がそのノードに対応）
4. OpenAI alias（`--openai-alias` 指定時のみ — フォネティック推測）

### 7-3. misrecognition_log.csv フォーマット

```csv
wrong,correct,count,note,target_nodes
お薬,予約,12,AmiVoice音響混同(oyaku/yoyaku),入力_用件
規約,予約,8,AmiVoice音響混同,入力_用件
制限外科,整形外科,5,AmiVoice音響混同,入力_診療科
秘密器科,泌尿器科,3,AmiVoice音響混同,入力_診療科
今日は,昭和,4,年号誤認識(L-007パターン),入力_生年月日
```

`target_nodes` カラムは省略可。省略した場合はそのエントリはどのノードにも配布されない（`_global` バケツ扱い）。複数ノードに配布する場合は `|` 区切りで列挙する（例: `入力_相談_問合せ|入力_追加の質問`）。

実 IVR ログで `Scripts_用件_result: NO_RESULT` または STT 出力が意図しない値になっているケースを収集して追記する。

### 7-4. 辞書更新チェックリスト

- [ ] 用件キーワード（予約・変更・キャンセル・お問い合わせ等）が登録済み
- [ ] FAQ 頻出キーワード（診療時間・駐車場・診察券・紹介状等）が登録済み
- [ ] 診療科名（全科）が登録済み
- [ ] `base_keywords.yaml` の値と `script_blocks` の keywords が一致している
- [ ] 実ログ由来の誤認識補正エントリを `misrecognition_log.csv` に追記済み
- [ ] 辞書更新後に AmiVoice リロードを実施済み
- [ ] テストコールで認識精度を確認済み（NO_RESULT 率が改善されているか）

---

---

## 8. Scripts 自動生成ステップ（P1 新規構築）

> **位置づけ: scaffold 完了後・prompter 前に実行する決定論的ステップ。**
> LLM を使わず、設計書 YAML の `script_blocks` セクションから ES5 Scripts コードを機械生成する。

### 8-1. 対象 Scripts ブロック種別

| `type` 値 | 用途 | キーワード指定方法 |
|---|---|---|
| `youken` | 用件判定（予約/変更/キャンセル等） | `options[].keywords` を直接記述 |
| `enum_classifier` | 汎用 enum 分類（個人/法人・はい/いいえ・初診/再診等） | **`options[].preset`** または `keywords`（両方書けばマージ） |
| `faq` | FAQ 完全一致判定（faqMap ルックアップ） | `faq_map[].q` / `faq_map[].a` を直接記述 |
| `department` | 診療科名正規化（最長一致） | `departments` リストを直接記述 |

**`enum_classifier` とプリセット:**
頻出の分類パターン（個人/法人・はい/いいえ等）は `docs/amivoice/keyword_presets.yaml` に定義済み。
`preset:` 名を指定するだけでキーワードが自動展開される。施設固有の追加語は `keywords:` に書けばマージされる。

### 8-2. 設計書 YAML の `script_blocks` セクション仕様

設計書 YAML に `script_blocks` セクションを追加し、各 Scripts ブロックの仕様を記述する:

```yaml
script_blocks:
  - type: youken          # 用件判定
    module_name: Scripts_用件
    input_module: 入力_用件
    options:
      - label: 予約
        strong: true
        keywords: [予約, よやく, とりたい, いれたい, したい]
      - label: 変更
        strong: true
        keywords: [変更, へんこう, かえる, ずらす, ずらしたい]
      - label: キャンセル
        strong: true
        keywords: [キャンセル, 取り消し, とりけし, やめる, やめたい]
      - label: お問い合わせ
        strong: false       # WEAK: catch-all
        keywords: [問い合わせ, 質問, 確認, 聞き, 聞きたい]

  - type: faq             # FAQ 完全一致判定
    module_name: Scripts-FAQ_問合せ
    input_module: OpenAI_RAG
    faq_map:
      - q: 診療時間を教えてください
        a: 診療時間は平日9時から17時です。
      - q: 駐車場はありますか
        a: 有料駐車場が100台ございます。
      - q: 初診の方は何を持ってくればいいですか
        a: 健康保険証と診察券（お持ちの方）をお持ちください。

  - type: faq
    module_name: Scripts-FAQ_最後の質問
    input_module: OpenAI_RAG
    faq_map:
      - q: 予約の確認はできますか
        a: 予約確認は受付までお電話ください。

  - type: faq
    module_name: Scripts-FAQ_その他の問い合わせ
    input_module: OpenAI_RAG
    faq_map:
      - q: 紹介状は必要ですか
        a: 初診の方は紹介状をご持参いただくとスムーズです。

  - type: faq
    module_name: Scripts-FAQ_その他の質問
    input_module: OpenAI_RAG
    faq_map:
      - q: クレジットカードは使えますか
        a: クレジットカードはご利用いただけません。

  - type: department      # 診療科正規化
    module_name: Scripts_診療科
    input_module: 入力_診療科
    departments:
      - 内科
      - 外科
      - 整形外科
      - 皮膚科
      - 眼科
      - 耳鼻咽喉科
      - 産婦人科
      - 小児科
      - 泌尿器科
      - 循環器内科

  # ---- enum_classifier の例（個人 / 法人） ----
  - type: enum_classifier
    module_name: Scripts_個人法人
    input_module: 入力_個人法人
    # repeat_guard は省略（デフォルト true）
    options:
      - label: 個人
        preset: kojin               # keyword_presets.yaml の "kojin" を展開
      - label: 企業
        preset: kigyo_hojin         # keyword_presets.yaml の "kigyo_hojin" を展開
        keywords: [NPO法人, 社会福祉法人]  # 施設固有の追加語はここに書く（preset にマージ）

  # ---- enum_classifier の例（はい / いいえ） ----
  - type: enum_classifier
    module_name: Scripts_選定療養費確認
    input_module: 入力_選定療養費
    options:
      - label: 同意
        preset: sentei_ryoyouhi_agree
      - label: 非同意
        preset: sentei_ryoyouhi_disagree
```

### 8-2-1. キーワードプリセット（`docs/amivoice/keyword_presets.yaml`）

`enum_classifier` で使える定義済みプリセット一覧:

| プリセット名 | 用途 | 主なキーワード |
|---|---|---|
| `kojin` | 個人回答 | 個人、自分、一般、個人です... |
| `kigyo_hojin` | 企業・法人回答 | 企業、会社、法人、団体、株式会社... |
| `hai` | はい（肯定） | はい、そうです、大丈夫です、お願いします... |
| `iie` | いいえ（否定） | いいえ、違います、間違いです... |
| `shoshin` | 初診回答 | 初診、初めて、はじめて、新患... |
| `saishin` | 再診回答 | 再診、以前に来たことがある、通院中... |
| `gozen` | 午前希望 | 午前、午前中、朝、早い時間... |
| `gogo` | 午後希望 | 午後、昼以降、夕方... |
| `dansei` | 男性 | 男性、男、男です... |
| `josei` | 女性 | 女性、女、女です... |
| `shinsatsuken_ari` | 診察券あり | あります、持っています... |
| `shinsatsuken_nashi` | 診察券なし | ありません、持っていません、なくしました... |
| `shokaijo_ari` | 紹介状あり | あります、持っています、持参します... |
| `shokaijo_nashi` | 紹介状なし | ありません、持っていません... |
| `sentei_ryoyouhi_agree` | 選定療養費同意 | 同意します、大丈夫です、払います... |
| `sentei_ryoyouhi_disagree` | 選定療養費非同意 | 同意しません、払えません... |

**プリセットに新しいパターンを追加する方法:**

```yaml
# docs/amivoice/keyword_presets.yaml に追記するだけ
# → 全シナリオに即時反映（gen_scripts.py 再実行時）

my_new_preset:
  note: "〇〇という質問に対する△△回答"
  keywords:
    - キーワード1
    - キーワード2
    - キーワード3
```

追加手順:
1. `docs/amivoice/keyword_presets.yaml` に新しいプリセット名でエントリを追記
2. `note:` に対応する TTS 文言の例を書く
3. `keywords:` に実際の発話パターンを網羅的に列挙
4. 設計書 YAML の `script_blocks` で `preset: my_new_preset` と指定
5. PR を作成して `@TS-dong-nc` にレビュー依頼（保護ゾーン）

---

### 8-2-2. Claude Code への依頼プロンプト集（日常運用）

実運用で発生する追加作業を Claude Code に依頼するときの**そのまま使えるプロンプト例**。

---

#### ケース A — AmiVoice が誤認識した語を登録したい

> 実際の通話ログで「予約」が「お薬」と認識されていた。

```
docs/amivoice/misrecognition_log.csv に以下の誤認識を追記してください。
wrong: お薬
correct: 予約
count: 12
note: AmiVoice音響混同(oyaku/yoyaku)
target_nodes: 入力_用件
```

→ Claude Code は `misrecognition_log.csv` に 1 行追記するだけ。
→ 次回 `gen_amivoice_dict.py` 実行時に自動で各ノード CSV に反映される。

---

#### ケース B — Scripts のキーワードが足りない（既存プリセットに追加）

> Scripts_用件 で「申し込みたい」が NO_RESULT になっている。

```
docs/amivoice/keyword_presets.yaml の youken_yoyaku プリセット（なければ作成）に
以下のキーワードを追加してください。
追加語: 申し込みたい、申し込む、申し込みをしたい
```

または、プリセットではなく特定シナリオの設計書だけ直したい場合:

```
output/scenarios/東京都立豊島病院_診療/設計書_東京都立豊島病院_診療.yaml の
script_blocks > Scripts_用件 > options > label: 予約 の keywords に
以下を追加してください。
追加語: 申し込みたい、申し込む
```

---

#### ケース C — 新しいプリセットを作りたい

> 「健康診断コース（一般・人間ドック・オプション）」を選ばせる block を作りたい。

```
docs/amivoice/keyword_presets.yaml に以下の新しいプリセットを追加してください。

kenshin_ippan:
  note: "「一般健診か人間ドックか」に対する一般健診回答"
  keywords: [一般健診, 一般, 通常健診, 基本コース]

kenshin_dock:
  note: "人間ドック回答"
  keywords: [人間ドック, ドック, 人間ドックコース]

kenshin_option:
  note: "オプション追加回答"
  keywords: [オプション, 追加, オプションあり]
```

---

#### ケース D — AmiVoice 辞書ノードに語を追加したい

> 入力_診療科 に「腎臓内科」を追加したい（AmiVoice 辞書 + Scripts 両方）。

```
以下を両方に追加してください。

1. docs/amivoice/base_keywords.yaml の department カテゴリに:
   word: 腎臓内科
   reading: じんぞうないか
   priority: high
   target_nodes: [入力_診療科]

2. output/scenarios/東京都立豊島病院_診療/設計書_東京都立豊島病院_診療.yaml の
   script_blocks > Scripts_診療科 > departments に「腎臓内科」を追加。
```

---

#### ケース E — 誤認識ログをまとめてアップロードしたい

> 今月のログから 20 件の誤認識を追加したい。

```
docs/amivoice/misrecognition_log.csv に以下の行を追記してください（CSV 形式）。

wrong,correct,count,note,target_nodes
お薬,予約,12,音響混同,入力_用件
規約,予約,8,音響混同,入力_用件
制限外科,整形外科,5,音響混同,入力_診療科
```

---

**依頼時のポイント:**
- `misrecognition_log.csv` への追記 → ケース A / E（AmiVoice 辞書側）
- `keyword_presets.yaml` への追記 → ケース B / C（Scripts 側・全シナリオ共通）
- 設計書 YAML の `script_blocks` 直接編集 → ケース B 下段（特定シナリオだけ直す場合）
- AmiVoice + Scripts 両方直す → ケース D（2ファイル同時に指定する）

### 8-3. gen_scripts.py の実行

```bash
python tools/gen_scripts.py \
    --yaml     output/scenarios/東京都立豊島病院_診療/設計書_東京都立豊島病院_診療.yaml \
    --scaffold output/json/scaffold_東京都立豊島病院_診療.json \
    --out      output/json/scaffold_東京都立豊島病院_診療_scripted.json
# --presets docs/amivoice/keyword_presets.yaml  ← 省略可（自動検索）
```

実行時に `input_module` が scaffold に存在しない場合は **WARN** を出力する（生成は続行）。モジュール名の不一致を早期発見できる。

**処理フロー:**

```
設計書 YAML の script_blocks
  → type=youken  → 用件判定 ES5 コードを生成 → scaffold JSON の該当モジュールに params.script を埋め込み
  → type=faq     → FAQ faqMap ES5 コードを生成 → scaffold JSON の該当モジュールに params.script を埋め込み
  → type=dept    → 診療科正規化 ES5 コードを生成 → 同上
  → 出力: scaffold_*_scripted.json（prompter の入力として使用）
```

### 8-4. gen_scripts.py が生成する ES5 コード例

**用件判定（type: youken）:**

```javascript
var rawInput = $runner.getModuleResult("入力_用件");
var text = "";
if (rawInput && typeof rawInput === "object" && rawInput.text) {
    text = String(rawInput.text).trim();
} else if (typeof rawInput === "string") {
    text = rawInput.trim();
}
text = text.replace(/[　 ]/g, "").replace(/[？?。、！!「」]/g, "");

if (/予約|よやく|とりたい|いれたい|したい/.test(text)) {
    $runner.setResult("予約");
} else if (/変更|へんこう|かえる|ずらす|ずらしたい/.test(text)) {
    $runner.setResult("変更");
} else if (/キャンセル|取り消し|とりけし|やめる|やめたい/.test(text)) {
    $runner.setResult("キャンセル");
} else if (/問い合わせ|質問|確認|聞き|聞きたい/.test(text)) {
    $runner.setResult("お問い合わせ");
} else {
    $runner.setResult("NO_RESULT");
}
```

**FAQ 完全一致判定（type: faq）:**

```javascript
var rawInput = $runner.getModuleResult("OpenAI_RAG");
var text = "";
if (rawInput && typeof rawInput === "object" && rawInput.text) {
    text = String(rawInput.text).trim();
} else if (typeof rawInput === "string") {
    text = rawInput.trim();
}
text = text.replace(/[　 ]/g, "").replace(/[？?。、！!「」]/g, "");

var faqMap = {
    "診療時間を教えてください": "診療時間は平日9時から17時です。",
    "駐車場はありますか": "有料駐車場が100台ございます。",
    "初診の方は何を持ってくればいいですか": "健康保険証と診察券（お持ちの方）をお持ちください。"
};

var answer = faqMap[text];
if (answer) {
    $runner.setObject("scripts-faq", answer);
    $runner.setResult("ANSWER");
} else {
    $runner.setResult("NO_RESULT");
}
```

### 8-5. P1 パイプラインへの組み込み位置

```
scaffold_generator.py（完成品 JSON 生成）
  ↓
gen_scripts.py（Scripts ES5 コードを scaffold JSON に埋め込み）  ← §8 NEW
  ↓
prompter（残りの generate_by_OpenAI プロンプトを記述）
  ↓
gen_properties.py（TTS プロパティ生成）
  ↓
validator → auto_fixer → tester
```

### 8-6. gen_scripts.py が担当しないもの（prompter に残す）

| ブロック | 理由 |
|---|---|
| `generate_by_OpenAI`（用件・OpenAI fallback） | Scripts NO_RESULT 後のフォールバック。自由発話解釈は LLM 必須 |
| `generate_by_OpenAI`（氏名カナ聴取） | STT 揺れの吸収が本質的に曖昧 |
| `generate_by_OpenAI`（日付・希望日解析） | 相対日付・文脈依存は LLM に残留 |
| `free_text` ブロック（自由発話収集） | **Scripts 正規化のみ**（§1-4 参照）。`generate_by_OpenAI` は使わない |

---

---

## 9. ContextMatchRouter とセッション変数（`<%...%>`）の設計ルール

### 9-1. ContextMatchRouter の基本動作

ContextMatchRouter（CMR）は **モジュールの出力値（context）で分岐する**モジュール。
固定パターン分岐（予約/変更/キャンセル等）には Script より CMR を優先すること。

```
type: "drjoy^Context Logic$ContextMatchRouter"
matchingmethod: 1
```

**1 モジュール出力だけで分岐する場合:**

`module1Name` と `module2Name` に**同じモジュール名を指定**し、
`module1ValueN` と `module2ValueN` にも同じ値を設定する。

> 理由: CMR は「module1 AND module2」の組み合わせ判定で動作する。
> `module2Name` を空にすると AND 条件が成立せず、常にフォールスルーになる。

```yaml
# 1 モジュール分岐の正しい書き方
contextName1: Scripts_用件   # module1Name
contextName2: Scripts_用件   # module2Name（同じ）
next:
  - condition: "^1$"   label: 予約         nextModuleName: sub|予約
  - condition: "^2$"   label: 変更         nextModuleName: sub|変更
  - condition: "^3$"   label: キャンセル   nextModuleName: sub|キャンセル
  - condition: "^4$"   label: お問い合わせ nextModuleName: sub|お問い合わせ
  - condition: "^.*$"  label: catch-all    nextModuleName: 転送  # 必須
```

**catch-all（`^.*$` または `^0$`）は必須** — 欠落すると AUD-1 CRITICAL。

---

### 9-2. セッション変数 `<%contextName%>` の参照ルール

Brekeke セッション内で保存されたデータは `<%contextName%>` 形式で TTS や `saveContext2DB` の `contextValue` に埋め込める。

#### データ保存方法と `<%...%>` 参照可否

| 保存方法 | 保存先 | `<%...%>` で参照できるか |
|---|---|---|
| `$runner.setObject("name", value)` | セッションメモリ（Scripts / gen_scripts） | ✅ **可能** |
| `saveContext2DB` モジュール（`contextName` / `contextValue`） | セッション + DB | ✅ **可能** |
| `generate_by_OpenAI` の `contextName` 出力 | DB のみ | ❌ **不可**（後述） |
| システム変数（`sys-customer-phone-number` 等） | セッション固定 | ✅ **可能** |

#### OpenAI 結果を `<%...%>` で使う場合は `saveContext2DB` を挟む

`generate_by_OpenAI` モジュールが `contextName` に書き込んだ値は **DB 保存のみ** で、
セッションメモリには載らない。そのため **そのままでは `<%contextName%>` で参照できない**。

```
# NG: OpenAI 結果を直接 TTS で参照
generate_by_OpenAI (contextName: 用件)
  → TTS: {tts_g:ご用件は<%用件%>ですね}   ← <%用件%> が空になる

# OK: saveContext2DB を挟んでセッションに載せる
generate_by_OpenAI (contextName: 用件)
  → saveContext2DB (contextName: 用件, contextValue: <%用件%>)   ← DB → session へコピー
  → TTS: {tts_g:ご用件は<%用件%>ですね}   ← ✅ 正しく展開される
```

> **注**: Scripts の `$runner.setObject("name", value)` は setObject の時点でセッションに載るため、
> `saveContext2DB` を挟まなくても `<%name%>` で参照可能。

---

#### 【重要パターン】Scripts + OpenAI fallback の両経路が同一 context に書く場合

用件判定など「Scripts キーワードマッチ → NO_RESULT のみ OpenAI fallback」の構成では、
**両経路が同じ context key（例: `classification`）に書き込むよう統一し、CMR は `<%classification%>` を読む**。

```
入力_用件（AmiVoice STT）
  │
  ▼
Scripts_用件
  ├─ 予約/変更/キャンセル/お問い合わせ
  │    → $runner.setObject("classification", "予約")  etc.
  │      ※ setObject でセッションに即座に載る → <%classification%> で参照可
  │
  └─ NO_RESULT
       ▼
     OpenAI_入力_用件（generate_by_OpenAI, contextName: classification）
       ▼
     saveContext2DB（contextName: classification, contextValue: <%classification%>）
       ※ OpenAI の DB 値をセッションにコピー → <%classification%> で参照可
  
  ↓（両経路ともここに合流）
ContextMatchRouter
  module1Name: （saveContext2DB モジュール名 or Scripts_用件）
  → next 条件で <%classification%> の値に基づき分岐
  → ^予約$      → sub|予約
  → ^変更$      → sub|変更
  → ^キャンセル$ → sub|キャンセル
  → ^お問い合わせ$ → sub|お問い合わせ
  → ^.*$        → 転送（catch-all 必須）
```

**ポイント:**
- Scripts 経路: `$runner.setObject("classification", 値)` → セッション即時反映
- OpenAI 経路: `generate_by_OpenAI` の後に必ず `saveContext2DB` で `<%classification%>` をセッションにコピー
- CMR は `<%classification%>` という**統一されたセッション変数**を読む → 経路を問わず同じ分岐ロジックが動く
- **重複 saveContext2DB 禁止**: Scripts 経路は setObject 済みなので、同じ key を再度 saveContext2DB しない

---

#### 【必須】値の三者一致ルール（Scripts / OpenAI / contextModel2DB）

`saveContext2DB` の `contextValue` は `<%classification%>`（OpenAI が DB に書いた値をそのまま参照）を指定する。
このとき **Scripts が返す値・OpenAI が返す値・`contextModel2DB` で宣言した enum の値** が **完全に一致**していなければならない。

```
Scripts_用件が返す値       OpenAI_用件が返す値          contextModel2DB の range
───────────────────────────────────────────────────────────────────────
  予約                    予約                         予約
  変更                    変更                         変更
  キャンセル              キャンセル                   キャンセル
  お問い合わせ            お問い合わせ                 お問い合わせ
  NO_RESULT               （出力しない）               —
```

**OpenAI 経路の正しい接続:**

```yaml
# generate_by_OpenAI
module: OpenAI_入力_用件
contextName: classification       # DB に保存されるキー名

# saveContext2DB（直後に接続）
contextName:  classification      # 同じキー名
contextValue: <%classification%>  # OpenAI が DB に書いた値をセッションにコピー
              # ← ここは固定文字列「予約」等を書かない。
              #   OpenAI の出力値をそのまま参照するために <%classification%> を使う。
              #   ただし OpenAI プロンプトが返す値が contextModel2DB の enum と一致すること（下記参照）
```

**OpenAI プロンプト設計の必須要件:**

OpenAI には必ず出力値を enum で制約すること。enum の値は `contextModel2DB` の range 宣言と完全一致させる。

```
# プロンプト内の出力制約（例）
以下のいずれか1つだけを返してください:
予約 / 変更 / キャンセル / お問い合わせ
上記以外の発話は「お問い合わせ」として扱います。
```

**contextModel2DB の range 宣言（例）:**

```yaml
module: contextModel_classification
contextName: classification
displayType: TEXT
range:
  - 予約
  - 変更
  - キャンセル
  - お問い合わせ
```

**NG パターン（値が不一致）:**

```
Scripts が返す値: "予約する"   ← 末尾に「する」が余分
OpenAI が返す値:  "予約"
contextModel2DB:  "予約"
→ CMR で Scripts 経路だけマッチしない
```

```
Scripts が返す値: "お問い合わせ"
OpenAI が返す値:  "問い合わせ"   ← 「お」が抜けている
contextModel2DB:  "お問い合わせ"
→ OpenAI 経路で CMR がマッチしない
```

---

### 9-3. CMR で 2 モジュール以上の組み合わせ分岐

`module1Name` と `module2Name` に**異なるモジュールを指定**すると、2 つの出力値の組み合わせで分岐できる。

```yaml
# 例: 施設判定 × 診療科で分岐
contextName1: OpenAI_施設
contextName2: Scripts_診療科
next:
  - condition: "^1$"
    module1Value: "病院A"
    module2Value: "内科"
    nextModuleName: 病院A_内科ルート
  - condition: "^2$"
    module1Value: "病院A"
    module2Value: "外科"
    nextModuleName: 病院A_外科ルート
  - condition: "^.*$"   # catch-all 必須
    nextModuleName: 転送
```

**2 モジュール分岐で OpenAI 結果を使う場合の注意:**
- CMR が参照するのは各モジュールの「最後の出力値」
- `generate_by_OpenAI` の結果は DB のみなので、CMR が読む前に `saveContext2DB` でセッションに載せること

```
generate_by_OpenAI (contextName: 施設)
  → saveContext2DB (contextName: 施設, contextValue: <%施設%>)   ← 必須
  → ContextMatchRouter (module1: 施設, module2: Scripts_診療科)
```

---

### 9-4. `<%...%>` 使用チェックリスト（設計書・JSON 共通）

- [ ] `setObject` で保存した値を `<%name%>` で参照している → ✅ 問題なし
- [ ] OpenAI `contextName` の値を TTS / saveContext2DB で `<%name%>` 参照している → `saveContext2DB` 中継が必要
- [ ] CMR の `module1Name` / `module2Name` に OpenAI モジュールを直接指定している → `saveContext2DB` 中継が必要
- [ ] `saveContext2DB` を連鎖して使う場合、`saveContext2DB` / `saveCompletionFlag2db` / `saveContextModel2DB` はサブモジュールに接続不可（通常モジュールとして配置）
- [ ] TTS 内で `<%contextName%>` を使う場合、本番実機で「リテラル読み上げになっていないか」を確認（動作検証必須）

---

## 10. 聞き返しリピートパターン（もう一度/もう一回）

> ### ⛔ 必須ルール（P1 新規構築・P2 既存修正 — 例外なし）
>
> **AmiVoice STT または DTMF+AmiVoice が接続されているすべての入力ノードに、リピート検知を実装しなければならない。**
> 新規シナリオ作成時も、既存シナリオの修正時も同様。省略は不可。
> **DTMF 専用ノード（AmiVoice を一切使わないノード）のみ対象外。**

### 10-1. 設計原則

- caller が「もう一度」「もう一回」等と言った場合、直前の TTS を再生して同じ入力ノードに戻る。
- リピートは **最大 2 回まで**（初回 + リピート 1 + リピート 2）。3 回目以降はオペレーター転送またはフロー終端へ。
- リピートカウンターは `$runner.setObject("repeat_count", n)` でセッションに保持し、Scripts で管理する。
- `もう一度` / `もう一回` の検知は **各 Scripts ブロックの先頭**（キーワードマッチより前）で行う。

**対象ノード種別:**

| 入力種別 | リピート検知 | 備考 |
|---|---|---|
| AmiVoice STT のみ | **必須** | 用件・診療科・生年月日・予約希望日・診察券番号・相談問合せ等すべて |
| DTMF + AmiVoice（併用） | **必須** | AmiVoice 経路にはリピート検知を入れる |
| DTMF 専用（AmiVoice なし） | 対象外 | DTMF 入力では発声しない前提 |

**`gen_scripts.py` の挙動:**
- `repeat_guard` フィールドを **省略した場合もデフォルト `true`** として扱う（AmiVoice ノードで意図的に外す場合のみ `repeat_guard: false` を明示する）。
- `repeat_guard: false` を明示した場合のみリピート検知ブロックを挿入しない。

### 10-2. 検知キーワード

| キーワード | 読み | 備考 |
|---|---|---|
| もう一度 | もういちど | 最頻出 |
| もう一回 | もういっかい | 同義 |
| 繰り返し | くりかえし | 口語表現 |
| もう一度言ってください | — | フレーズ表現 |
| 聞こえません | きこえません | 音量問題と区別しない（リピートで対応） |
| もう少し大きな声で | — | 同上 |

AmiVoice 辞書への登録は `docs/amivoice/base_keywords.yaml` の `repeat` カテゴリに定義する（§7 参照）。

### 10-3. Scripts 実装テンプレート

全 STT 入力ノードの Scripts 先頭に下記ブロックを追加する（`gen_scripts.py` が `type: repeat_guard` を検出して自動挿入）。

```javascript
// ---- リピート検知（先頭で必ず判定） ----
var rawInput = $runner.getModuleResult("入力_用件");  // ← ノードごとに変更
var text = "";
if (rawInput && typeof rawInput === "object" && rawInput.text) {
    text = String(rawInput.text).trim();
} else if (typeof rawInput === "string") {
    text = rawInput.trim();
}
text = text.replace(/[　 ]/g, "").replace(/[？?。、！!「」]/g, "");

if (/もう一度|もう一回|くりかえし|繰り返し|聞こえません|もう少し/.test(text)) {
    var repeatRaw = $runner.getObject("repeat_count");
    var repeatCount = repeatRaw ? parseInt(String(repeatRaw), 10) : 0;
    if (repeatCount < 2) {
        $runner.setObject("repeat_count", repeatCount + 1);
        $runner.setResult("REPEAT");
    } else {
        // リピート上限到達 → オペレーター転送
        $runner.setResult("REPEAT_LIMIT");
    }
    // ↓ 以降の通常判定は実行しない
} else {
    // リピートカウンターをリセット（正常入力が来たら）
    $runner.setObject("repeat_count", 0);

    // ---- 通常のキーワード判定（ここに既存ロジックを続ける） ----
    // ...
}
```

### 10-4. フロー接続パターン

```
TTS_案内文 ─────────────┐
                         ↓
                 入力_用件（AmiVoice STT）
                         ↓
                 Scripts_用件
                   ├─ REPEAT      → TTS_案内文（ループ）
                   ├─ REPEAT_LIMIT → オペレーター転送 / 終話
                   ├─ 予約         → 予約フロー
                   ├─ 変更         → 変更フロー
                   ├─ キャンセル   → キャンセルフロー
                   ├─ お問い合わせ → FAQ フロー
                   └─ NO_RESULT   → generate_by_OpenAI（フォールバック）
```

**REPEAT ブランチ接続ルール:**
- REPEAT → 直前の TTS モジュール（`TTS_案内文` 等）に戻る。STT 入力モジュールには戻らない（TTS を飛ばしてはならない）。
- REPEAT_LIMIT → `call_transfer` または `termination` ブロックへ直結。再度 TTS に戻さない。
- `saveContext2DB` が必要な箇所がある場合でも、REPEAT/REPEAT_LIMIT 分岐の前にカウンター更新を完了させてから分岐すること。

### 10-5. OpenAI フォールバック経路でのリピート

`generate_by_OpenAI` ノードの結果を参照する Scripts または CMR のフロー上でも、**同じ repeat_count セッション変数を引き継ぐ**。

```
入力_用件 → Scripts_用件 → NO_RESULT
                              ↓
                   generate_by_OpenAI（用件分類）
                              ↓
                   saveContext2DB（contextName: classification）
                              ↓
                   ContextMatchRouter（<%classification%>）
                     ├─ 予約 / 変更 / キャンセル → 各フロー
                     └─ NO_RESULT → TTS_再確認案内
                                         ↓
                              入力_用件（再入力）← repeat_count は維持
```

OpenAI 側でも `REPEAT` を出力させてはならない。リピート検知は Scripts 層のみで行う。

### 10-6. 設計書 YAML の `script_blocks` 記法

```yaml
script_blocks:
  # AmiVoice ノード → repeat_guard は省略可（デフォルト true）
  - type: youken
    module_name: Scripts_用件
    input_module: 入力_用件
    # repeat_guard: true  ← 省略してよい（デフォルト true）
    # repeat_limit: 2     ← 省略してよい（デフォルト 2）
    options:
      - label: 予約
        keywords: [予約, よやく, 予約したい, 予約を取りたい]
      - label: 変更
        keywords: [変更, へんこう, 日にちを変えたい, 予約をずらしたい]
      - label: キャンセル
        keywords: [キャンセル, 取り消し, 予約をやめたい]
      - label: お問い合わせ
        keywords: [問い合わせ, 問合せ, 質問, 確認]

  # DTMF 専用ノード → repeat_guard: false を明示する
  - type: youken
    module_name: Scripts_DTMF確認
    input_module: 入力_DTMF確認
    repeat_guard: false   # ← DTMF 専用のため明示的に無効化
    options:
      - label: はい
        keywords: ["1"]
      - label: いいえ
        keywords: ["2"]
```

**`repeat_guard` フィールドのデフォルト値:**

| フィールド指定 | 動作 |
|---|---|
| 省略（AmiVoice ノード） | `true` として扱う — リピート検知を挿入する |
| `repeat_guard: true` | 同上（明示版） |
| `repeat_guard: false` | リピート検知を挿入しない（DTMF 専用ノード用） |

### 10-7. AmiVoice 辞書への追加

`docs/amivoice/base_keywords.yaml` に `repeat` カテゴリを追加し、全 STT 入力ノードに配布する:

```yaml
repeat:
  - word: もう一度
    reading: もういちど
    priority: high
    target_nodes: [入力_用件, 入力_診療科, 入力_生年月日, 入力_予約希望日,
                   入力_変更希望日, 入力_診察券番号, 入力_通院歴,
                   入力_相談_問合せ, 入力_追加の質問, 入力_内容確認,
                   入力_その他の問い合わせ]

  - word: もう一回
    reading: もういっかい
    priority: high
    target_nodes: [入力_用件, 入力_診療科, 入力_生年月日, 入力_予約希望日,
                   入力_変更希望日, 入力_診察券番号, 入力_通院歴,
                   入力_相談_問合せ, 入力_追加の質問, 入力_内容確認,
                   入力_その他の問い合わせ]

  - word: 聞こえません
    reading: きこえません
    priority: medium
    target_nodes: [入力_用件, 入力_診療科, 入力_生年月日, 入力_予約希望日,
                   入力_変更希望日, 入力_診察券番号]
```

### 10-8. テストケース（P7 マスター CSV への追加項目）

`docs/testcase_master/master_test_patterns_v3.csv` に以下カテゴリのケースを追加する:

| case_id | category | case_name | 入力_用件 | 期待_用件 | 備考 |
|---|---|---|---|---|---|
| RPT-001 | repeat | リピート1回目→予約 | もう一度 | 予約 | repeat後に正常入力 |
| RPT-002 | repeat | リピート2回目→変更 | もう一回 | 変更 | 2回リピート後に正常入力 |
| RPT-003 | repeat | リピート上限到達→転送 | もう一度×3 | REPEAT_LIMIT | 3回目でオペレーター |
| RPT-004 | repeat | OpenAI経路でもリピート保持 | もう一度→(OpenAI)予約 | 予約 | フォールバック経路 |

### 10-9. 実装チェックリスト（P1 新規・P2 既存修正 — 両方必須）

**P1 新規構築時:**
- [ ] シナリオ内の全 AmiVoice / DTMF+AmiVoice 入力ノードをリストアップした
- [ ] 全対象ノードの `script_blocks` エントリで `repeat_guard` を省略（デフォルト true）または `true` を明示した
- [ ] 全対象ノードのフロー JSON に REPEAT / REPEAT_LIMIT ブランチが存在する
- [ ] REPEAT ブランチが直前の TTS モジュールに戻っている（STT に直接戻っていない）
- [ ] REPEAT_LIMIT ブランチがオペレーター転送または終話に接続されている
- [ ] `repeat_count` は正常入力時にリセットされている
- [ ] DTMF 専用ノードには `repeat_guard: false` を明示した
- [ ] AmiVoice 辞書の `repeat` カテゴリが全 AmiVoice ノードの `target_nodes` に含まれている
- [ ] P7 テストケースに RPT-001〜RPT-004 相当のケースが含まれている

**P2 既存シナリオ修正時（追加確認項目）:**
- [ ] 修正対象ノードおよびその前後の AmiVoice ノードにリピート検知が既に存在することを確認した
- [ ] リピート検知が存在しない AmiVoice ノードが残っている場合、今回の修正スコープに含めて追加した
- [ ] 新たに AmiVoice ノードを追加した場合、そのノードにもリピート検知を実装した
- [ ] 既存の REPEAT/REPEAT_LIMIT ブランチ接続先が正しい TTS モジュールを指しているか確認した

---

*このドキュメントは `docs/governance/` 保護ゾーン管理。変更には @TS-dong-nc の PR レビューが必要。*
