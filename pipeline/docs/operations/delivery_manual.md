# 新規シナリオ 納品マニュアル（新規作成〜納品完了）

> **対象読者**: ディレクター / テクニカルリード  
> **用途**: 顧客から要件を受け取ってから、Dr.JOY 本番環境へ納品するまでの全工程を網羅したオペレーションガイド。  
> **前提**: Claude Code が起動済みであること。`{施設名}` `{フロー名}` 等の `{}` は実際の値に置き換えて使用すること。

---

## 全体工程マップ

```
フェーズ 1: 受注・準備
  1-1  顧客資料の受領・配置
  1-2  命名規約チェック
  1-3  環境確認（施設IDなど）

フェーズ 2: 設計（壁打ち）
  2-1  /new-scenario でノート起草
  2-2  /flow-draft で構造ドラフト確定  ← ⚠️ 人間承認
  2-3  BLOCKER の解消               ← ⚠️ 人間確認

フェーズ 3: 自動生成（orchestrator）
  3-1  orchestrator 起動（P1 または P1+1）
  3-2  設計書 YAML 生成 → qa_validator  ← CRITICAL 残存時は壁打ちへ差し戻し
  3-3  scaffold JSON 生成 → layout
  3-4  prompter + gen_properties（並列）
  3-5  validator → auto_fixer → tester
  3-6  oracle_gate（部品受入）

フェーズ 4: 検品（人間 QA）
  4-1  TTS 文言を顧客資料と照合         ← ⚠️ 人間確認
  4-2  P7 bivr 生成（3種）・実機検証      ← ⚠️ 人間操作（発信）
  4-3  score_gate（4 層採点）
  4-4  修正ループ（問題があれば 2 へ戻る）

フェーズ 5: 納品
  5-1  納品チェックリスト確認
  5-2  git Push 承認                 ← ⚠️ 人間操作
  5-3  Dr.JOY 本番設定              ← ⚠️ 人間操作
  5-4  顧客への納品連絡
  5-5  事後確認（開通翌日）
```

---

## フェーズ 1: 受注・準備

### 1-1. 顧客資料の受領・配置

顧客から受け取ったファイル（PDF/PowerPoint/Excel/MD）を以下のパスに配置する。

```
docs/reference/customer_docs/【{フロー名}】：{施設名}.md    ← MD 優先
docs/reference/customer_docs/【{フロー名}】：{施設名}.pdf   ← PDF（MD がない場合）
```

**優先度**: MD > PPTX > PDF  
PDF しかない場合は Claude Code が `markitdown` で MD 化する。表組み・フローチャートが崩れやすいため、変換後に人間が目視確認する。

---

### 1-2. 命名規約チェック

| ルール | NG 例 | OK 例 |
|---|---|---|
| 半角スペース禁止 | `東京 クリニック` | `東京クリニック` |
| 括弧 `(1)` 禁止 | `診療(外来)` | `診療外来` |
| アンダースコア `_` を施設名・フロー名に含めない | `東京_クリニック` | `東京クリニック` |
| `{施設名}_{フロー名}` で全体 255 文字以内（漢字で 19 字目安） | — | — |

既存シナリオとの重複確認:

```bash
ls output/scenarios/ | grep {施設名}
```

すでに同名のシナリオが存在する場合は、新しいフロー名を付けるか、既存フローの修正（Pattern 2）にするか人間が判断する。

---

### 1-3. 環境確認・情報収集

orchestrator 起動前に以下の情報を確定する。未確認のまま進めると BLOCKER になる。

| 確認項目 | 確認方法 | 備考 |
|---|---|---|
| `office_id` | Dr.JOY 管理画面で確認 | 設計書 `basic_info.office_id` に記入 |
| 050 電話番号（IVR 入電番号） | 顧客または通信会社に確認 | `basic_info.phone_number` |
| 受付時間（曜日・時間帯） | 顧客資料 or 直接確認 | `basic_info.acceptance_times` |
| 予約不可診療科のリスト | 顧客資料で確認 | `clinical_department_classifier` の除外リスト |
| SMS 送信要否（smsFlag の値） | 顧客要望で確認 | smsFlag 分岐に影響 |
| 紹介状必須ルール | 顧客資料で確認 | 新規ルートの設計に影響 |

---

## フェーズ 2: 設計（壁打ち）

### 2-1. /new-scenario でノート起草

```
/new-scenario {施設名} {フロー名}
```

スキルが以下を自動実行する:
- `docs/reference/customer_docs/` から顧客資料を特定
- Pattern 1 軽量ノートを起草（`docs/migration/{施設名}_{フロー名}.md`）

ノートには以下が含まれる（人間が確認・補足する）:
- シナリオ概要
- 設計方針（multiflow 構成・入電者種別・用件分岐方式など）
- 施設固有の特殊ルール
- BLOCKER リスト（未確認の情報）

---

### 2-2. /flow-draft で構造ドラフト壁打ち

```
/flow-draft {施設名} {フロー名}
```

スキルが顧客資料からブロック構造の草案 MD 表を出力する。  
以下の確認項目を人間と壁打ちして**全項目を確定**してから次に進む。

| 確認項目 | 詳細 |
|---|---|
| 各 step の block type | `date_of_call_classifier` は廃止。26 種 allowlist から選ぶ |
| 希望日・希望時期聴取 | `hearing`(output_format:text) + OpenAI（SKILL_希望日.md 固定プロンプト） |
| free_text | Scripts 正規化（OpenAI 不使用）。save_to の context 名を確認 |
| faq | method: script / openai を確定。回答 TTS は scaffold が自動配置 |
| N 択 enum hearing | `choices:` を明示宣言（未宣言だと OpenAI のまま） |
| polar hearing（はい/いいえ） | `choices:` 不要。自動で `yes_no_classifier` |
| 分岐の抜け・漏れ | `match: other` の行き先を含めて全パスを網羅 |
| 診察券番号の聴取タイミング | ルートごとに出現タイミングが異なる場合は整理 |
| 診療科チェーンのセット数 | 予約用・変更/キャンセル用で TTS 文言が異なれば別ブロック |
| smsFlag 分岐値 | 各用件（新規/再診/変更/キャンセル/確認）の値を確定 |

承認後、flow_draft を保存する:

```bash
# チャット内の表を以下のパスに保存（Claude Code に依頼）
output/scenarios/{施設名}_{フロー名}/flow_draft_{YYYYMMDD}.md
```

**⚠️ 人間が「OK」を明示してから STEP 3 へ進む。**

---

### 2-3. BLOCKER の解消

ノートの BLOCKER リスト（`docs/migration/{施設名}_{フロー名}.md` 末尾）に記載された未確認事項を、**この時点でゼロ**にしてから orchestrator を起動する。

BLOCKER が残ったまま orchestrator を起動すると、設計書 YAML に `TODO` が残り qa_validator の CRITICAL が発生する。

---

## フェーズ 3: 自動生成（orchestrator）

### 3-1. orchestrator 起動

**P1（標準・Opus）推奨** — 顧客資料を全量読んで設計書を生成する。品質重視。

```
以下の設定で Pattern 1（新規シナリオ構築）を実行してください。

施設名: {施設名}
フロー名: {フロー名}
ノートパス: docs/migration/{施設名}_{フロー名}.md
出力先: output/scenarios/{施設名}_{フロー名}/

orchestrator を Pattern 1 で起動してください。
```

**P1+1（トークン節約版・Sonnet）** — flow_draft が確定している場合の高速版。

```
以下の設定で Pattern 1+1（トークン節約版）を実行してください。

施設名: {施設名}
フロー名: {フロー名}
ノートパス: docs/migration/{施設名}_{フロー名}.md
flow_draft: output/scenarios/{施設名}_{フロー名}/flow_draft_{YYYYMMDD}.md
出力先: output/scenarios/{施設名}_{フロー名}/

orchestrator を Pattern 11 で起動してください。
```

---

### 3-2. 設計書 YAML 生成 → qa_validator

orchestrator が自動で qa_validator を実行する。

- `fix_category="auto"` の Issue → `yaml_auto_fixer.py` が自動修正
- **残存 CRITICAL → 壁打ちで設計書を直してから再実行**（director の自律リトライは行わない）

手動で確認する場合:

```bash
python3 schemas/qa_validator.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
```

---

### 3-3. scaffold JSON 生成 → layout

orchestrator が自動実行。手動で再実行する場合:

```bash
python3 scripts/scaffold_generator.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  output/json/scaffold_{施設名}_{フロー名}.json

python3 scripts/layout_calculator.py \
  output/json/scaffold_{施設名}_{フロー名}.json
```

---

### 3-4. prompter + gen_properties（並列）

orchestrator が自動実行。

- **prompter（LLM）**: `generate_by_OpenAI` ブロックのプロンプトを記述。  
  OpenAI の TIMEOUT/ERROR フォールバック Script にも対応するキーワードマッチを記述する。
- **gen_properties.py（スクリプト）**: IVR プロパティ（TTS 文言）を生成。

手動で gen_properties のみ再実行:

```bash
python3 scripts/gen_properties.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  output/json/scaffold_{施設名}_{フロー名}.json \
  --out output/scenarios/{施設名}_{フロー名}/properties_{施設名}_{フロー名}.md
```

---

### 3-5. validator → auto_fixer → tester

orchestrator が自動実行。手動確認:

```bash
python3 schemas/validator.py output/json/prompted_{施設名}_{フロー名}.json
python3 scripts/auto_fixer.py output/json/prompted_{施設名}_{フロー名}.json
python3 scripts/tester.py output/json/prompted_{施設名}_{フロー名}.json
```

残存 CRITICAL は 工場長 に解析を依頼し、差し戻し票をもとに設計書を修正して再実行する。

---

### 3-6. oracle_gate（部品受入）

orchestrator が自動実行。  
認定済み部品は自動スキップ。新規 spec（1 文字でも改変あり）は受入要求が発生する。

受入要求が出た場合は、`modules/` 配下の対象部品の `test_oracle.py` を人間が確認・承認する。

---

## フェーズ 4: 検品（人間 QA）

### 4-1. TTS 文言を顧客資料と照合 ⚠️ 人間確認

生成された IVR プロパティ（`properties_{施設名}_{フロー名}.md`）と顧客資料を**目視照合**する。

確認コマンド（Claude Code に照合を依頼する場合）:

```
output/scenarios/{施設名}_{フロー名}/properties_{施設名}_{フロー名}.md の
TTS 文言を顧客資料 docs/reference/customer_docs/{...}.md と照合し、
差異があれば差分リストを出力してください。
```

修正が必要な場合:
1. **設計書 YAML を壁打ちで修正する**（`step_details.tts` 等）
2. orchestrator を再実行（gen_properties + scaffold のみでも可）
3. 修正後に再照合する

> **ルール**: TTS 文言は設計書（生成器）を直して再生成する。properties_*.md を直接編集しない。

---

### 4-2. P7 bivr 生成（3種）・実機検証 ⚠️ 人間操作

P7 では目的別に **3種類の bivr** を生成する。

| # | ファイル名 | 用途 | TTS | AmiVoice STT |
|---|---|---|---|---|
| 1 | `{施設名}_{フロー名}_連結テスト.bivr` | 全分岐の自動通話テスト | 実音声再生 | Script で inject（cases.json） |
| 2 | `{施設名}_{フロー名}_stub.bivr` | TTS+STT 両方 Script 化（完全無音・自動化） | Script でスキップ | Script で inject（cases.json） |
| 3 | `tts_preview_{施設名}_{フロー名}.bivr` | TTS 文言の聴取確認（AmiVoice のみ giả lập） | 実音声再生 | `$ivr.play()` でスキップ |

---

**Step 1: テストケース生成（自動）**

```bash
python3 connection_test/gen_branch_cases_from_yaml.py \
  --yaml  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  --out   connection_test/cases/{施設名}_{フロー名}_branches.json
```

---

**Step 2-A: 連結テスト bivr 生成（自動）**

AmiVoice STT を cases.json の inject_value で置き換えた bivr。実際に発信して全分岐を自動で通る。

```bash
python3 connection_test/stub_stt_connection.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  connection_test/cases/{施設名}_{フロー名}_branches.json \
  --out output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}_連結テスト.bivr
```

またはプロンプトで:

```
以下の cases JSON から P7 連結テスト bivr を生成してください。

yaml: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
cases: connection_test/cases/{施設名}_{フロー名}_branches.json
出力先: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}_連結テスト.bivr
```

---

**Step 2-B: Stub bivr 生成（自動）— TTS + STT 両方 Script 化**

TTS 発話も STT もすべて Script で処理し、実際の音声なしで自動実行できる bivr。ヘッドレス環境でのテスト自動化向け。

```bash
python3 connection_test/stub_stt_connection.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  connection_test/cases/{施設名}_{フロー名}_branches.json \
  --stub-tts \
  --out output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}_stub.bivr
```

またはプロンプトで:

```
以下の cases JSON から P7 TTS+STT スタブ bivr（--stub-tts モード）を生成してください。

yaml: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
cases: connection_test/cases/{施設名}_{フロー名}_branches.json
出力先: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}_stub.bivr
```

---

**Step 2-C: Preview bivr 生成（自動）— AmiVoice のみ giả lập**

AmiVoice STT を `$ivr.play()` で置き換えた bivr。発信すると TTS 文言が順番に実音声で再生される。人間が耳で TTS 文言を確認するための専用ツール。

```bash
python3 tools/gen_tts_preview_bivr.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  --out output/scenarios/{施設名}_{フロー名}/tts_preview_{施設名}_{フロー名}.bivr
```

またはプロンプトで:

```
以下の設計書から TTS Preview bivr を生成してください。

yaml: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
出力先: output/scenarios/{施設名}_{フロー名}/tts_preview_{施設名}_{フロー名}.bivr
```

---

**Step 3: Dr.JOY に bivr をインポート（人間操作）**

テスト目的に応じてインポートする bivr を選択する:

| 目的 | インポートする bivr |
|---|---|
| 全分岐の通話テスト（メイン） | `{施設名}_{フロー名}_連結テスト.bivr` |
| TTS 文言の聴取確認 | `tts_preview_{施設名}_{フロー名}.bivr` |
| 自動化テスト（音声不要） | `{施設名}_{フロー名}_stub.bivr` |

手順:
1. Dr.JOY 管理画面にログイン
2. 目的の bivr をインポート
3. テスト用電話番号（050 番号）を設定

---

**Step 4: 全ケース発信テスト（人間操作）**

`{施設名}_{フロー名}_連結テスト.bivr` を使って `branches.json` の各ケースを順番に発信し、以下を確認する:

| 確認項目 | 合格基準 |
|---|---|
| 各分岐の到達先 | 設計書の routing_map と一致 |
| TTS 文言の読み上げ | 顧客資料の文言と一致・聞き取れる |
| 受付時間外の動作 | acceptance_times 判定が正しい |
| リトライ動作 | 無応答・誤入力で所定回数リトライ後に適切に終話 |
| call_transfer | 予約センター・健診センター等への転送が正しい |
| termination | 折り返し受付完了のアナウンスが正しい |
| SMS/smsFlag | smsFlag 分岐値が正しい（実際の SMS 送信は別途確認） |

**テスト結果の記録**:

テスト記録は `output/scenarios/{施設名}_{フロー名}/test_report_{YYYYMMDD}.md` に記述する。

---

### 4-3. score_gate（4 層採点ゲート）

orchestrator が自動実行する。手動確認:

```
output/scenarios/{施設名}_{フロー名}/ の全成果物の品質スコアを確認してください。
oracle_gate / P7 / P6 の全 PASS を確認し、出荷可否を判定してください。
```

**合格条件（全部 PASS でないと納品不可）:**

- [ ] qa_validator: CRITICAL = 0
- [ ] validator: CRITICAL = 0  
- [ ] tester: CRITICAL = 0
- [ ] oracle_gate: 全部品 PASS / 受入済み
- [ ] P7 実機テスト: 全ケース合格
- [ ] TTS 照合: 顧客資料との差分ゼロ

---

### 4-4. 修正ループ

テストで問題が発見された場合:

| 問題の種類 | 修正先 | 手順 |
|---|---|---|
| TTS 文言の誤り | 設計書 YAML の `step_details.tts` | 壁打ちで修正 → gen_properties 再実行 |
| 分岐ロジックの誤り | 設計書 YAML の `scenario_flow` | 壁打ちで修正 → orchestrator 再実行 |
| OpenAI プロンプトの誤り | prompter サイドカー MD | prompter 再実行（または直接修正） |
| 診療科リストの漏れ | 設計書 YAML の `clinical_departments` | 追記 → scaffold 再実行 |
| Scripts の誤り | modules/ またはインライン script | 認定部品なら再受入、インラインなら設計書修正 |

> **修正の原則**: 成果物（JSON/MD）を直接編集しない。設計書（生成器）を直して再実行する。

---

## フェーズ 5: 納品

### 5-1. 納品チェックリスト（最終確認）

以下を全て確認してから納品作業に進む:

```
output/scenarios/{施設名}_{フロー名}/ の成果物に対して納品前チェックリストを実行してください。
```

**チェックリスト:**

- [ ] 設計書 YAML: qa_validator CRITICAL = 0
- [ ] JSON 構造: validator CRITICAL = 0
- [ ] 構造監査: tester CRITICAL = 0
- [ ] oracle_gate: 全部品 PASS / 受入済み
- [ ] TTS 文言: 顧客資料と照合済み・差分ゼロ
- [ ] P7 連結テスト: 全ケース実機合格
- [ ] git commit: 全成果物がコミット済み
- [ ] `.bivr` ファイル: 最終版が `output/scenarios/{施設名}_{フロー名}/` に存在
- [ ] `properties_{施設名}_{フロー名}.md`: 最終版が存在
- [ ] `確認レポート_{施設名}_{フロー名}_{YYYYMMDD}.md`: 最終版が存在
- [ ] BLOCKER: 全て解消済み

---

### 5-2. git Push 承認 ⚠️ 人間操作

Claude Code に Push 準備を依頼する:

```
output/scenarios/{施設名}_{フロー名}/ の成果物を
ブランチ {branch-name} にコミットして Push の準備をしてください。
準備ができたら Push コマンドを提示してください（自動では Push しない）。
```

Claude Code が `git push` コマンドを提示したら、人間が確認して実行する:

```bash
git push -u origin {branch-name}
```

---

### 5-3. Dr.JOY 本番設定 ⚠️ 人間操作

以下の設定を Dr.JOY 管理画面で実施する。

**IVR フロー設定:**

1. 最終版 `.bivr` を本番環境（prod）にインポート
2. 050 本番電話番号をフローに紐付け
3. 受付時間を設定（`acceptance_times` の値を入力）

**電話帳設定:**

- 設計書 `phonebook` セクションに記載された電話番号を Dr.JOY に登録
- `phonebook_csv` が生成されている場合は CSV インポートを利用

**Dr.JOY 連携設定（API 連携がある場合）:**

- `office_id` が正しく設定されているか確認
- API 接続テスト（`incoming_category_classifier` の URL 等）

**SMS 設定（smsFlag を使う場合）:**

- smsFlag の各値に対応するテンプレートが設定されているか確認

---

### 5-4. 顧客への納品連絡

以下の内容を顧客に連絡する（メール・チャット等）:

```
【納品完了のご連絡】

{施設名} 様

{フロー名} IVR フローの納品が完了しました。

■ 開通電話番号: {050-xxxx-xxxx}
■ 受付時間: {平日 9:00〜17:00 等}
■ 開通日時: {YYYY-MM-DD HH:MM}

動作確認として以下のテストをお願いいたします。
1. 上記電話番号に架電し、フロー全体の動作を確認してください。
2. 各用件（予約/変更/キャンセル等）で折り返し受付が正常に完了するか確認してください。
3. 問題がある場合はご連絡ください。

よろしくお願いいたします。
```

---

### 5-5. 事後確認（開通翌日）

開通翌日に以下を確認する:

| 確認項目 | 確認方法 |
|---|---|
| 通話ログの存在 | Dr.JOY 管理画面で着信ログを確認 |
| エラー通話の有無 | 通話が途中で切断されていないか確認 |
| SMS 送信状況 | SMS ログを確認（smsFlag 設定がある場合） |
| 顧客からのフィードバック | 不具合報告がないか確認 |

問題があった場合は原因を特定し、修正フローに戻る。

---

## トラブルシューティング

### qa_validator の CRITICAL が残った場合

```
以下の qa_validator レポートを確認して差し戻し票を出力してください。

レポート: output/scenarios/{施設名}_{フロー名}/qa_audit_{施設名}_{フロー名}.md
設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

CRITICAL の内容を確認し、yaml_auto_fixer で解消できる項目とできない項目を分けてください。
自動修正不可のものは壁打ち差し戻し票を出力してください。
```

### orchestrator が途中で止まった場合（resume）

```bash
python3 scripts/orchestrator.py --pattern 1 \
  --spec docs/migration/{施設名}_{フロー名}.md \
  --resume output/scenarios/{施設名}_{フロー名}/pipeline_state_{施設名}_{フロー名}.json \
  --assignee hamaguchi --env demo
```

### P7 実機テストで分岐が期待通りにならない場合

1. `branches.json` の該当ケースの `inject_value` を確認する
2. 設計書の該当 step の block type・conditions を確認する
3. 問題箇所を特定して設計書を修正 → orchestrator 再実行 → 再テスト

### TTS 文言が顧客資料と一致しない場合

```
以下の TTS 文言を確認してください。

properties: output/scenarios/{施設名}_{フロー名}/properties_{施設名}_{フロー名}.md
顧客資料: docs/reference/customer_docs/{...}.md

差異がある行を列挙し、設計書 YAML の修正箇所を示してください。
```

---

## 所要時間目安

| フェーズ | 担当 | 目安時間 |
|---|---|---|
| フェーズ 1: 受注・準備 | 人間 | 30 分〜1 時間 |
| フェーズ 2: 設計（壁打ち） | 人間 + Claude | 1〜3 時間 |
| フェーズ 3: 自動生成（P1） | Claude（自動） | 30〜60 分 |
| フェーズ 3: 自動生成（P1+1） | Claude（自動） | 15〜30 分 |
| フェーズ 4: 検品（TTS 照合） | 人間 | 1〜2 時間 |
| フェーズ 4: 検品（P7 実機） | 人間 | 1〜3 時間 |
| フェーズ 5: 納品 | 人間 | 1〜2 時間 |
| **合計（P1）** | | **5〜12 時間** |
| **合計（P1+1）** | | **4〜10 時間** |

※ 修正ループが発生する場合は上記の 1.5〜2 倍を見込む。

---

## 関連ドキュメント

| ドキュメント | 内容 |
|---|---|
| `docs/operations/new_scenario_guide.md` | orchestrator 各ゲートの詳細手順 |
| `docs/operations/claude_code_prompts.md` | 全パターン対応プロンプト集（コピペ用） |
| `docs/governance/loop-governance.md` | パイプライン全体設計（VFB 製造ライン v2） |
| `docs/brekeke/モジュール選定ガイド_v2.md` | ブロック型の使い分け（26 種） |
| `.claude/skills/flow-draft/SKILL.md` | /flow-draft スキル仕様・block type 早見表 |
| `.claude/skills/new-scenario/SKILL.md` | /new-scenario スキル仕様 |
| `schemas/qa_validator.py` | 設計書検証ルール（KNOWN_BLOCK_TYPES 等） |
| `modules/README.md` | 認定部品一覧・受入テスト仕様 |
