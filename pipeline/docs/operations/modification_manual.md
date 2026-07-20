# 修正依頼対応マニュアル（修正依頼受領〜納品完了）

> **対象読者**: ディレクター / テクニカルリード  
> **用途**: 既存シナリオへの修正依頼（TTS 文言変更・分岐追加・プロンプト改善・設計変更など）を受け取ってから、Dr.JOY 本番環境へ納品するまでの全工程ガイド。  
> **前提**: 対象シナリオの成果物（JSON / 設計書 YAML）が `output/scenarios/{施設名}_{フロー名}/` に存在すること。

---

## 修正の種類と対応パターン

修正依頼を受けたら、まず**修正の種類**を判定する。種類によって手順が大きく異なる。

| 修正の種類 | 例 | 対応パターン | 設計書修正 |
|---|---|---|---|
| **A: TTS 文言のみ変更** | 「〇〇でよろしいですか」→「〇〇ですね」 | P2-B | 必要（設計書が正本） |
| **B: OpenAI プロンプトのみ修正** | キーワード追加、分岐改善 | P2-C | 任意（プロンプトのみでも可） |
| **C: Scripts キーワード追加** | 「薬の相談」を用件の Scripts に追加 | P2-A（外科的パッチ） | 任意 |
| **D: 分岐・ブロック構造の変更** | 新しい用件追加、診療科リスト変更 | P2-A + 設計書修正 → scaffold 再生成 | **必要** |
| **E: フロー全体の再設計** | 受付フローを全面刷新 | 新規構築（delivery_manual.md 参照） | **必要** |

> **判断基準**: 「設計書 YAML の `scenario_flow` のブロック構造が変わるか」を確認する。  
> 変わる → D/E パターン（設計書修正 + scaffold 再生成）。変わらない → A/B/C パターン（外科的パッチ）。

---

## 全体工程マップ

```
フェーズ 1: 修正依頼の受領・分析
  1-1  修正依頼の内容確認・整理
  1-2  修正種類の判定（A/B/C/D/E）
  1-3  影響範囲の確認

フェーズ 2: 修正実施
  ── パターン A: TTS 文言変更
      2A-1  設計書 YAML の tts を修正（壁打ち）
      2A-2  gen_properties 再実行
      2A-3  validator 確認

  ── パターン B: OpenAI プロンプト修正
      2B-1  修正内容を dirlite で分析
      2B-2  prompter（リフレッシュモード）で再記述
      2B-3  validator + tester 確認

  ── パターン C: Scripts キーワード修正
      2C-1  対象モジュールを特定
      2C-2  fixer（外科的パッチ）で修正
      2C-3  validator 確認

  ── パターン D: 分岐・構造変更
      2D-1  設計書 YAML を壁打ちで修正
      2D-2  qa_validator → yaml_auto_fixer
      2D-3  scaffold 再生成 → layout → gen_scripts
      2D-4  prompter（影響箇所のみ）+ gen_properties
      2D-5  validator → auto_fixer → tester

フェーズ 3: 検品（人間 QA）
  3-1  TTS 文言を修正依頼内容と照合    ← ⚠️ 人間確認
  3-2  P7 実機テスト（影響箇所）       ← ⚠️ 人間操作（発信）
  3-3  修正ループ（問題があれば 2 へ戻る）

フェーズ 4: 納品
  4-1  納品チェックリスト確認
  4-2  git Push 承認                  ← ⚠️ 人間操作
  4-3  Dr.JOY 本番更新               ← ⚠️ 人間操作
  4-4  顧客への納品連絡
```

---

## フェーズ 1: 修正依頼の受領・分析

### 1-1. 修正依頼の内容確認・整理

修正依頼を受け取ったら、以下の情報を確認・整理する。

| 確認項目 | 確認方法 |
|---|---|
| **施設名 / フロー名** | 依頼文から特定。`output/scenarios/` で存在確認 |
| **修正内容の詳細** | 変更前/変更後を具体的に確認。「〇〇みたいな感じで」は NG。変更前・変更後を明文化 |
| **影響を受ける step / ブロック** | 設計書 YAML の `scenario_flow` と照合 |
| **本番稼働中か否か** | 稼働中なら修正 → テスト → 本番更新の間に通話が入る可能性 |
| **納品期限** | 急ぎか否かで作業優先度が変わる |

既存の成果物を確認:

```bash
# 成果物の存在確認
ls output/scenarios/{施設名}_{フロー名}/

# 設計書を確認
cat output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml | head -80
```

---

### 1-2. 修正種類の判定

```
以下の修正依頼を分析して、修正種類（A/B/C/D/E）を判定してください。

施設名: {施設名}
フロー名: {フロー名}
設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

修正依頼:
{依頼内容を箇条書きで記載}

修正種類の判定と、影響を受けるブロック・モジュールを列挙してください。
```

---

### 1-3. 影響範囲の確認

修正が他のブロックや分岐に波及しないか確認する。

```
以下の修正が設計書に与える影響範囲を確認してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
修正箇所: {影響するブロック名 / step 名}

影響を受ける可能性のある下流ブロック・分岐先・context 変数を列挙してください。
```

---

## フェーズ 2: 修正実施

---

### パターン A: TTS 文言のみ変更

#### 2A-1. 設計書 YAML を壁打ちで修正

TTS 文言は**設計書 YAML の `step_details.tts`（または `tts` フィールド）が正本**。  
`properties_*.md` や JSON を直接編集してはならない（再生成で上書きされるため）。

```
以下の設計書の TTS 文言を修正してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

修正箇所:
  - step: {step 名（例: 用件確認）}
  - 変更前: 「{変更前の TTS 文言}」
  - 変更後: 「{変更後の TTS 文言}」

修正後に設計書 YAML の当該箇所を表示して確認してください。
```

#### 2A-2. gen_properties 再実行

```bash
python3 scripts/gen_properties.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  output/json/prompted_{施設名}_{フロー名}.json \
  --out output/scenarios/{施設名}_{フロー名}/properties_{施設名}_{フロー名}.md
```

#### 2A-3. validator 確認

```bash
python3 schemas/validator.py output/json/prompted_{施設名}_{フロー名}.json
```

CRITICAL が出た場合は auto_fixer で自動修正:

```bash
python3 scripts/auto_fixer.py output/json/prompted_{施設名}_{フロー名}.json
```

---

### パターン B: OpenAI プロンプトのみ修正

#### 2B-1. dirlite で修正指示書を生成

```
以下のシナリオのプロンプト修正指示書を作成してください。

施設名: {施設名}
フロー名: {フロー名}
既存 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

修正依頼:
  - 対象モジュール: {OpenAI モジュール名（例: OpenAI_用件確認）}
  - 修正内容: {例: 「お薬の相談」を「確認」カテゴリに追加する}
  - 修正理由: {例: 「薬の相談」が NO_RESULT になって通話が切れる}

dirlite エージェントを呼び出して、fixer が実行できる粒度の修正指示書を生成してください。
```

#### 2B-2. prompter（リフレッシュモード）で再記述

```
以下のモジュールの OpenAI プロンプトを修正してください。

対象 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
対象モジュール: {OpenAI モジュール名}
修正内容: {修正内容の詳細}
設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

prompter エージェントの Pattern 2 リフレッシュモードを使用してください。
修正後にプロンプトサイドカー（prompts_{施設名}_{フロー名}.md）も更新してください。

またフォールバック Script（script_{step}_fallback）のキーワードも同期して更新してください。
```

> **注意**: OpenAI プロンプトを修正したら、対応する `script_{step}_fallback` の  
> キーワードマッチも同じ内容で更新する（両者が乖離すると OpenAI 障害時に誤動作する）。

#### 2B-3. validator + tester 確認

```bash
python3 schemas/validator.py output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
python3 scripts/tester.py output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
```

---

### パターン C: Scripts キーワード追加・修正（外科的パッチ）

#### 2C-1. 対象モジュールを特定

```
以下の設計書から修正が必要なモジュール名を特定してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
修正内容: {例: 用件判定 Scripts の「確認」キーワードに「教えてください」を追加}

対象の Scripts モジュール名と、現在のキーワードリストを表示してください。
```

#### 2C-2. fixer（外科的パッチ）で修正

```
以下の JSON の Scripts モジュールを外科的に修正してください。

対象 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
対象モジュール: {モジュール名（例: script_用件確認）}
修正内容:
  - 修正前: {変更前のキーワードや条件}
  - 修正後: {変更後のキーワードや条件}

fixer エージェントを使用して最小限の変更のみ行ってください。
修正後に validator で検証し、CRITICAL がなければ報告してください。
```

#### 2C-3. validator 確認

```bash
python3 schemas/validator.py output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
```

---

### パターン D: 分岐・ブロック構造の変更

設計書 YAML の `scenario_flow` が変わる場合はこのパターン。  
scaffold を再生成するため、工程が多い。

#### 2D-1. 設計書 YAML を壁打ちで修正 ⚠️ 人間確認

変更内容を壁打ちで確定してから設計書を修正する。

```
以下の設計書に対して構造変更を行います。変更内容を壁打ちで確認してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

変更内容:
  {修正依頼の内容を詳細に記載}

変更後の scenario_flow の該当 step を提示して確認してください。
人間が OK を出したら設計書に反映してください。
```

**⚠️ 人間が「OK」を出してから設計書に書き込む。**

#### 2D-2. qa_validator → yaml_auto_fixer

```bash
python3 schemas/qa_validator.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

# CRITICAL がある場合
python3 scripts/yaml_auto_fixer.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

# 再確認
python3 schemas/qa_validator.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
```

残存 CRITICAL は壁打ちで解消してから次へ進む。

#### 2D-3. scaffold 再生成 → layout → gen_scripts

```bash
python3 scripts/scaffold_generator.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  output/json/scaffold_{施設名}_{フロー名}.json

python3 scripts/layout_calculator.py \
  output/json/scaffold_{施設名}_{フロー名}.json

python3 scripts/gen_scripts.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  output/json/scaffold_{施設名}_{フロー名}.json
```

#### 2D-4. prompter（影響箇所のみ）+ gen_properties

変更した箇所の OpenAI プロンプトのみを再記述する（全体リフレッシュは不要）。

```
以下の scaffold JSON に対して、変更されたブロックの OpenAI プロンプトのみを記述してください。

scaffold: output/json/scaffold_{施設名}_{フロー名}.json
設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

変更されたブロック（プロンプト記述が必要なもの）:
  - {変更されたモジュール名1}
  - {変更されたモジュール名2}

変更されていないブロックの既存プロンプトはそのまま引き継いでください。
修正後にプロンプトサイドカー（prompts_{施設名}_{フロー名}.md）も更新してください。
```

gen_properties 再実行:

```bash
python3 scripts/gen_properties.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  output/json/scaffold_{施設名}_{フロー名}.json \
  --out output/scenarios/{施設名}_{フロー名}/properties_{施設名}_{フロー名}.md
```

#### 2D-5. validator → auto_fixer → tester

```bash
python3 schemas/validator.py output/json/prompted_{施設名}_{フロー名}.json
python3 scripts/auto_fixer.py output/json/prompted_{施設名}_{フロー名}.json
python3 scripts/tester.py output/json/prompted_{施設名}_{フロー名}.json
```

残存 CRITICAL は 工場長 に解析を依頼し、壁打ちで設計書を修正して再実行する。

---

## フェーズ 3: 検品（人間 QA）

### 3-1. TTS 文言・修正内容を照合 ⚠️ 人間確認

生成された `properties_{施設名}_{フロー名}.md` と**修正依頼の内容**を目視照合する。

```
以下の修正後 properties と修正依頼を照合してください。

properties: output/scenarios/{施設名}_{フロー名}/properties_{施設名}_{フロー名}.md
修正依頼:
  {修正依頼の内容}

修正が正しく反映されているか確認し、差異があれば差分リストを出力してください。
```

---

### 3-2. P7 実機テスト（影響箇所） ⚠️ 人間操作

**変更した箇所に関連する分岐のみ**テストする（全ケースでなくてよい）。

**P7 bivr の種類（目的に応じて選択）:**

| # | ファイル名 | 用途 | TTS | AmiVoice STT |
|---|---|---|---|---|
| 1 | `{施設名}_{フロー名}_連結テスト.bivr` | 全分岐の自動通話テスト | 実音声再生 | Script で inject（cases.json） |
| 2 | `{施設名}_{フロー名}_stub.bivr` | TTS+STT 両方 Script 化（完全無音・自動化） | Script でスキップ | Script で inject（cases.json） |
| 3 | `tts_preview_{施設名}_{フロー名}.bivr` | TTS 文言の聴取確認（AmiVoice のみ giả lập） | 実音声再生 | `$ivr.play()` でスキップ |

修正の種類に応じた bivr 選択:

| 修正種別 | 推奨 bivr |
|---|---|
| TTS 文言変更（A 型） | `tts_preview_*.bivr` で TTS を耳で確認後、`_連結テスト.bivr` で分岐確認 |
| OpenAI プロンプト変更（B 型） | `_連結テスト.bivr` で影響分岐のみ発信テスト |
| Scripts キーワード変更（C 型） | `_連結テスト.bivr` または `_stub.bivr` で変更キーワードの分岐を確認 |
| 構造変更（D 型） | `_連結テスト.bivr` で全影響分岐をテスト |

**影響する分岐の特定:**

```
以下の修正内容から、テストすべき分岐（ケース）を列挙してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
修正箇所: {変更したブロック・step 名}

テストケース（入力→期待する遷移先）を一覧化してください。
```

**bivr 再生成（構造変更 D 型・または cases.json を更新した場合）:**

```bash
# 連結テスト bivr
python3 connection_test/stub_stt_connection.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  connection_test/cases/{施設名}_{フロー名}_branches.json \
  --out output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}_連結テスト.bivr

# Stub bivr（TTS+STT 両方 Script 化）
python3 connection_test/stub_stt_connection.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  connection_test/cases/{施設名}_{フロー名}_branches.json \
  --stub-tts \
  --out output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}_stub.bivr

# Preview bivr（AmiVoice のみ giả lập・TTS 聴取確認用）
python3 tools/gen_tts_preview_bivr.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  --out output/scenarios/{施設名}_{フロー名}/tts_preview_{施設名}_{フロー名}.bivr
```

**テスト実施（人間が発信）:**

| テスト観点 | 確認内容 |
|---|---|
| 修正箇所の動作 | 変更した TTS / 分岐 / キーワードが意図通りか |
| 修正前と同じ動作（リグレッション） | 変更していない部分が壊れていないか |
| エラー経路 | TIMEOUT / ERROR 時にフォールバックが動作するか |
| リトライ動作 | 誤入力・無応答でリトライ後に正しく終話するか |

**テスト記録**（修正の記録として残す）:

```
テスト結果を以下のファイルに追記してください。

ファイル: output/scenarios/{施設名}_{フロー名}/test_report_{YYYYMMDD}.md

修正番号: #{連番}
修正日: {YYYY-MM-DD}
修正内容: {修正依頼の概要}
テスト結果: {合格 / 不合格}
確認者: {名前}
```

---

### 3-3. 修正ループ

テストで問題が発見された場合:

| 問題の種類 | 修正先 | 戻る先 |
|---|---|---|
| TTS 文言が意図と異なる | 設計書 YAML の `step_details.tts` | 2A-1 へ |
| OpenAI プロンプトの分岐が正しくない | prompter リフレッシュ | 2B-2 へ |
| Scripts のキーワードが足りない | fixer 外科的パッチ | 2C-2 へ |
| 分岐先の遷移が間違っている | 設計書 YAML の `scenario_flow.conditions` | 2D-1 へ |
| フォールバック Script が誤動作 | prompter でキーワード同期 | 2B-2 へ |

> **ルール**: 成果物（JSON/MD）を直接編集しない。設計書（生成器）を直して再生成する。

---

## フェーズ 4: 納品

### 4-1. 納品チェックリスト（修正版）

```
output/scenarios/{施設名}_{フロー名}/ の修正後成果物を確認し、
納品チェックリストを実行してください。
```

- [ ] 設計書 YAML: qa_validator CRITICAL = 0
- [ ] JSON 構造: validator CRITICAL = 0
- [ ] 構造監査: tester CRITICAL = 0
- [ ] TTS 文言: 修正依頼内容と一致確認済み
- [ ] 実機テスト: 影響箇所の全ケース合格
- [ ] リグレッション: 変更箇所以外が壊れていないことを確認済み
- [ ] git commit: 全成果物がコミット済み
- [ ] prompts_*.md: 修正されたプロンプトが反映済み（B パターンの場合）
- [ ] properties_*.md: 最新版が存在（A/D パターンの場合）

---

### 4-2. git Push 承認 ⚠️ 人間操作

Claude Code に Push 準備を依頼:

```
output/scenarios/{施設名}_{フロー名}/ の修正後成果物を
ブランチ {branch-name} にコミットして Push の準備をしてください。
コミットメッセージには修正内容の概要を含めてください。
準備ができたら Push コマンドを提示してください（自動では Push しない）。
```

確認後に実行:

```bash
git push -u origin {branch-name}
```

---

### 4-3. Dr.JOY 本番更新 ⚠️ 人間操作

#### 修正内容別の Dr.JOY 更新手順

**A: TTS 文言のみ変更の場合**

1. Dr.JOY 管理画面で対象フローの IVR プロパティを開く
2. 変更した TTS モジュールのプロパティ値を更新する
3. フローを保存・再起動する

**B/C: プロンプト・Scripts 変更の場合**

1. 最新の `.bivr` ファイルを Dr.JOY にインポートする（上書き）
2. フローを再起動する

**D: 構造変更の場合**

1. `.bivr` を再生成する（まだ生成していない場合）:

```
最新の JSON から .bivr ファイルを生成してください。

JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
出力先: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}_{YYYYMMDD}.bivr
```

2. Dr.JOY で旧バージョンを退避（バックアップ）する
3. 新バージョンの `.bivr` をインポートする
4. 電話番号の紐付けを確認する
5. フローを再起動する

---

### 4-4. 顧客への納品連絡

```
【修正完了のご連絡】

{施設名} 様

修正依頼の対応が完了しました。

■ 修正内容: {修正の概要（例: 用件確認の TTS 文言を変更）}
■ 反映日時: {YYYY-MM-DD HH:MM}

動作確認として以下をお願いいたします:
1. {修正箇所の動作確認手順}
2. 問題がある場合はご連絡ください。

よろしくお願いいたします。
```

---

## よくある修正依頼パターンと手順早見表

### 「TTS の文言を変えたい」

→ パターン A（設計書 YAML → gen_properties → validator）

```
設計書 output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml の
step「{step 名}」の TTS 文言を以下に変更してください。

変更前: 「{変更前}」
変更後: 「{変更後}」

変更後に gen_properties.py を実行して properties_*.md を再生成し、
validator で確認してください。
```

---

### 「〇〇という言葉を言ったときの分岐を追加したい」

→ パターン C（Scripts キーワード追加）または B（OpenAI プロンプトに追加）

```
output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json の
Scripts モジュール「{モジュール名}」に、キーワード「{追加キーワード}」を
「{分岐カテゴリ}」として追加してください。

fixer エージェントで外科的パッチを当ててください。
修正後に validator で確認してください。
```

---

### 「新しい診療科を追加したい」

→ パターン D（設計書の `clinical_departments` に追加 → scaffold 再生成）

```
以下の設計書の診療科リストに「{診療科名}」を追加してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

追加する診療科: {診療科名}（予約可 / 予約不可）

修正後に scaffold_generator.py を再実行して JSON を再生成してください。
```

---

### 「受付時間を変えたい」

→ 設計書の `basic_info.acceptance_times` を変更 + Dr.JOY 設定変更

```
以下の設計書の受付時間を変更してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

変更内容:
  - 変更前: {例: 平日 9:00-17:00}
  - 変更後: {例: 平日 9:00-18:00, 土曜 9:00-13:00}

修正後に scaffold_generator.py を再実行して JSON を再生成してください。
```

Dr.JOY 管理画面でも受付時間を同期更新すること。

---

### 「OpenAI がうまく判定できないキーワードがある」

→ パターン B（プロンプト修正）+ Scripts fallback のキーワード追加

```
以下のモジュールで「{誤認識されるキーワード}」が正しく分類されていません。

対象モジュール: {OpenAI モジュール名}
期待する分類: {期待する出力カテゴリ}

prompter リフレッシュモードでプロンプトを修正し、
script_{step}_fallback のキーワードマッチも同期して更新してください。
```

---

## 所要時間目安

| 修正パターン | 目安時間 |
|---|---|
| A: TTS 文言変更 | 15〜30 分 |
| B: OpenAI プロンプト修正 | 30〜60 分 |
| C: Scripts キーワード追加 | 15〜30 分 |
| D: 分岐・構造変更（小規模） | 1〜3 時間 |
| D: 分岐・構造変更（大規模） | 3〜6 時間 |

※ 実機テストで問題が発見された場合は修正ループが発生する（上記の 1.5〜2 倍を見込む）。

---

## 関連ドキュメント

| ドキュメント | 内容 |
|---|---|
| `docs/operations/delivery_manual.md` | 新規作成〜納品の全工程マニュアル |
| `docs/operations/claude_code_prompts.md` | 全パターン対応プロンプト集（P2-A/B/C など） |
| `docs/governance/loop-governance.md` | パイプライン全体設計（keystone: ライン内自律修復なし） |
| `docs/brekeke/モジュール選定ガイド_v2.md` | ブロック型の使い分け（26 種） |
| `docs/ai/skills/SKILL_FAQ_Scripts.md` | FAQ Scripts プロンプト生成 |
| `docs/ai/skills/SKILL_希望日.md` | 希望日聴取 OpenAI 固定プロンプト |
