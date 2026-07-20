# 新規シナリオ作成ガイド（Pattern 1 / P1+1）

> **用途**: 新規病院シナリオをゼロから作るときの手順書。  
> 各ステップに「Claude Code に貼り付けるプロンプト」を同梱している。  
> `{施設名}` `{フロー名}` `{...}` は実際の値に必ず置き換えること。

---

## 全体フロー

```
[STEP 0] 前提確認・命名規約チェック
      ↓
[STEP 1] /new-scenario スキルで顧客資料を読み込みノートを起草
      ↓
[STEP 2] /flow-draft で構造ドラフト壁打ち ← ⚠️ 人間承認必須
      ↓
[STEP 3] orchestrator 起動 — P1（Opus） または P1+1（Sonnet 節約版）を選択
      │
      ├─ director → 設計書 YAML 生成
      │   └─ qa_validator → yaml_auto_fixer → 残 CRITICAL は壁打ちへ差し戻し
      │
      ├─ scaffold_generator → JSON 生成 → layout_calculator
      ├─ gen_scripts → Scripts ES5 埋め込み
      ├─ prompter（LLM）+ gen_properties.py（スクリプト）— 並列
      ├─ validator → auto_fixer → tester
      └─ commit
      ↓
[STEP 4] P7 連結テストケース生成（自動）
      ↓
[STEP 5] IVR プロパティ最終確認（TTS 文言）← ⚠️ 人間確認
      ↓
[STEP 6] 完成チェックリスト実行
      ↓
[STEP 7] Push 承認 ← ⚠️ 人間操作
```

---

## STEP 0: 前提確認

### 命名規約（必須チェック）

| ルール | NG 例 | OK 例 |
|---|---|---|
| 半角スペース禁止 | `東京 クリニック` | `東京クリニック` |
| 括弧 `(1)` 禁止 | `診療(外来)` | `診療外来` |
| `_` を施設名・フロー名に含めない | `東京_クリニック` | `東京クリニック` |
| `{施設名}_{フロー名}` の URL エンコード後 255 文字以内 | （漢字 19 字目安） | — |

### 顧客資料の配置

```
docs/reference/customer_docs/{施設名}_{フロー名}.pdf   ← PDF の場合
docs/reference/customer_docs/{施設名}_{フロー名}.md    ← MD の場合（MD 優先）
```

**既存ディレクトリの確認**:

```bash
ls output/scenarios/ | grep {施設名}
```

すでに存在する場合は別のフロー名にするか、人間と協議して上書き判断を行う。

---

## STEP 1: /new-scenario でノート起草

```
/new-scenario {施設名} {フロー名}
```

スキルが自動で:
1. `docs/reference/customer_docs/` から顧客資料を特定
2. PDF の場合 → `markitdown` で MD 化（`docs/reference/customer_docs/{施設名}_{フロー名}_raw.md`）
3. Pattern 1 軽量ノートを起草（`docs/migration/{施設名}_{フロー名}.md`）
4. `/flow-draft` 起動コマンドを提示

ノート起草後、**STEP 2 の flow-draft に必ず進む**（director を先に呼んではならない）。

---

## STEP 2: /flow-draft で構造ドラフト壁打ち

```
/flow-draft {施設名} {フロー名}
```

スキルが顧客資料からブロック構造の草案 MD 表を出力する。  
人間と壁打ちして以下を確定する:

| 確認項目 | 内容 |
|---|---|
| 各 step の block type | `date_of_call_classifier` は廃止・使用不可 |
| N 択 enum hearing | `choices:` の宣言があるか（ない → OpenAI のまま） |
| polar hearing（はい/いいえ） | `choices:` 不要。自動で `yes_no_classifier` |
| 分岐の抜け・漏れ | `match: other` の行き先を含む |
| subflow 分割の要否 | FAQ / 用件聴取など Jump to Flow が必要か |

**⚠️ 人間が「OK」を出してから STEP 3 へ進む。**

---

## STEP 3: orchestrator 起動

### P1（標準・Opus）推奨

director が顧客資料を全量読んで設計書 YAML を生成する。品質重視。

**プロンプト:**
```
以下の設定で Pattern 1（新規シナリオ構築）を実行してください。

施設名: {施設名}
フロー名: {フロー名}
ノートパス: docs/migration/{施設名}_{フロー名}.md
出力先: output/scenarios/{施設名}_{フロー名}/

orchestrator を Pattern 1 で起動してください。
```

**CLI（直接起動する場合）:**
```bash
python3 scripts/orchestrator.py --pattern 1 \
  --spec docs/migration/{施設名}_{フロー名}.md \
  --assignee hamaguchi --env demo
```

### P1+1（トークン節約版・Sonnet）

flow-draft の構造が確定している場合の高速版。TTS 文言等の文言系のみ Sonnet が補完。

**前提**: `/flow-draft` 出力を `output/scenarios/{施設名}_{フロー名}/flow_draft_YYYYMMDD.md` として保存済み。

**プロンプト:**
```
以下の設定で Pattern 1+1（トークン節約版）を実行してください。

施設名: {施設名}
フロー名: {フロー名}
ノートパス: docs/migration/{施設名}_{フロー名}.md
flow_draft: output/scenarios/{施設名}_{フロー名}/flow_draft_{YYYYMMDD}.md
出力先: output/scenarios/{施設名}_{フロー名}/

orchestrator を Pattern 11 で起動してください。
```

**CLI:**
```bash
python3 scripts/orchestrator.py --pattern 11 \
  --spec docs/migration/{施設名}_{フロー名}.md \
  --assignee hamaguchi --env demo
```

---

### orchestrator 実行中の各ゲート

orchestrator が順番に以下を自動実行する。各ゲートの結果を確認すること。

#### ゲート 1: 設計書 YAML 生成 → qa_validator

orchestrator が `qa_validator.py` を自動実行して結果を出力する。  

`fix_category="auto"` の Issue は `yaml_auto_fixer.py` が自動修正。  
**残存 CRITICAL が出た場合は壁打ちで設計書を直してから再実行する（director 自律リトライは行わない）。**

手動で再確認する場合:
```
設計書 output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml を
qa_validator.py で検証してください。
CRITICAL が残っている場合は差し戻しレポートを出力してください。
```

```bash
python3 schemas/qa_validator.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
```

#### ゲート 2: scaffold → layout → gen_scripts

scaffold_generator が scenario_flow から完成品 JSON を決定論的に生成し、  
layout_calculator がレイアウトを計算し、gen_scripts が Scripts ES5 を埋め込む。

手動実行する場合:
```bash
python3 scripts/scaffold_generator.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  --out output/json/scaffold_{施設名}_{フロー名}.json

python3 scripts/layout_calculator.py \
  output/json/scaffold_{施設名}_{フロー名}.json

python3 scripts/gen_scripts.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  output/json/scaffold_{施設名}_{フロー名}.json
```

#### ゲート 3: prompter + gen_properties（並列）

prompter が `generate_by_OpenAI` ブロックのプロンプトを記述し、  
gen_properties.py が IVR プロパティ（TTS 文言）を生成する。

手動で prompter のみ再実行:
```
以下の設計書と scaffold JSON から、generate_by_OpenAI ブロックのプロンプトを
ブロック単位で記述してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
JSON: output/json/scaffold_{施設名}_{フロー名}.json
```

gen_properties のみ手動実行:
```bash
python3 scripts/gen_properties.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  output/json/scaffold_{施設名}_{フロー名}.json \
  --out output/scenarios/{施設名}_{フロー名}/properties_{施設名}_{フロー名}.md
```

#### ゲート 4: validator → auto_fixer → tester

JSON 構造チェックと自動修正が走る。

手動確認:
```bash
python3 schemas/validator.py output/json/prompted_{施設名}_{フロー名}.json
python3 scripts/auto_fixer.py output/json/prompted_{施設名}_{フロー名}.json
python3 scripts/tester.py output/json/prompted_{施設名}_{フロー名}.json
```

---

## STEP 4: P7 bivr 生成（3種）・実機テスト準備

orchestrator 完走後に自動生成されるが、手動でも実行できる。

### テストケース生成

```bash
python3 connection_test/gen_branch_cases_from_yaml.py \
  --yaml  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  --out   connection_test/cases/{施設名}_{フロー名}_branches.json
```

### P7 bivr 3種の生成

| # | ファイル名 | 用途 | TTS | AmiVoice STT |
|---|---|---|---|---|
| 1 | `{施設名}_{フロー名}_連結テスト.bivr` | 全分岐の自動通話テスト | 実音声再生 | Script で inject（cases.json） |
| 2 | `{施設名}_{フロー名}_stub.bivr` | TTS+STT 両方 Script 化（完全無音・自動化） | Script でスキップ | Script で inject（cases.json） |
| 3 | `tts_preview_{施設名}_{フロー名}.bivr` | TTS 文言の聴取確認（AmiVoice のみ giả lập） | 実音声再生 | `$ivr.play()` でスキップ |

```bash
# 1. 連結テスト bivr（メインテスト用）
python3 connection_test/stub_stt_connection.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  connection_test/cases/{施設名}_{フロー名}_branches.json \
  --out output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}_連結テスト.bivr

# 2. Stub bivr（TTS+STT 両方 Script 化・自動化向け）
python3 connection_test/stub_stt_connection.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  connection_test/cases/{施設名}_{フロー名}_branches.json \
  --stub-tts \
  --out output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}_stub.bivr

# 3. Preview bivr（AmiVoice のみ giả lập・TTS 聴取確認用）
python3 tools/gen_tts_preview_bivr.py \
  output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
  --out output/scenarios/{施設名}_{フロー名}/tts_preview_{施設名}_{フロー名}.bivr
```

またはプロンプトで:

```
以下の設計書・cases JSON から P7 bivr 3種を生成してください。

yaml: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
cases: connection_test/cases/{施設名}_{フロー名}_branches.json
出力先: output/scenarios/{施設名}_{フロー名}/

stub_stt_connection.py（連結テスト・stub）と gen_tts_preview_bivr.py（preview）を実行してください。
```

---

## STEP 5: IVR プロパティ（TTS 文言）確認

⚠️ **人間が元の顧客資料と照合して確認する。**

```
output/scenarios/{施設名}_{フロー名}/properties_{施設名}_{フロー名}.md の
TTS 文言を確認レポートと元資料と照合してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
顧客資料: docs/reference/customer_docs/{施設名}_{フロー名}.md（または PDF）
```

修正が必要な場合は **設計書 YAML を壁打ちで直してから orchestrator を再実行**する（成果物でなく設計書を直す）。

---

## STEP 6: 完成チェックリスト

```
以下のシナリオの完成チェックリストを実行してください。

施設名: {施設名}
フロー名: {フロー名}
JSON パス: output/json/prompted_{施設名}_{フロー名}.json
設計書パス: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

qa_validator / validator / tester / oracle_gate の全結果を確認し、
CRITICAL / WARNING の残存状況をレポートしてください。
```

チェックリスト項目:

- [ ] 設計書 YAML: qa_validator CRITICAL = 0
- [ ] JSON 構造: validator CRITICAL = 0
- [ ] 構造監査: tester CRITICAL = 0
- [ ] oracle_gate: 全部品 PASS or 受入済み
- [ ] IVR プロパティ: TTS 文言を顧客資料と照合済み
- [ ] P7 テストケース: branches.json 生成済み
- [ ] P7 STT スタブ: bivr 生成済み（実機テストは別途）
- [ ] git commit 済み（orchestrator が自動実行）

---

## STEP 7: Push 承認

⚠️ **Push は必ず人間が承認する。**

```
output/scenarios/{施設名}_{フロー名}/ の成果物を
ブランチ {branch-name} にコミットして Push の準備をしてください。
準備ができたら Push コマンドを提示してください（自動では Push しない）。
```

確認後:
```bash
git push -u origin {branch-name}
```

---

## トラブルシューティング

### qa_validator の CRITICAL が残った場合

```
以下の qa_validator レポートを確認して差し戻し票を出力してください。

レポート: output/scenarios/{施設名}_{フロー名}/qa_audit_{施設名}_{フロー名}.md
設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

修正が必要な箇所をリストアップし、
自動修正（yaml_auto_fixer）で解消できる項目とできない項目を分けてください。
自動修正不可のものは壁打ち差し戻し票を出力してください。
```

### orchestrator が途中で止まった場合（resume）

```bash
python3 scripts/orchestrator.py --pattern 1 \
  --spec docs/migration/{施設名}_{フロー名}.md \
  --resume output/scenarios/{施設名}_{フロー名}/pipeline_state_{施設名}_{フロー名}.json \
  --assignee hamaguchi --env demo
```

### validator の CRITICAL が残った場合

```
output/json/prompted_{施設名}_{フロー名}.json の validator レポートを確認して、
auto_fixer で自動修正できない CRITICAL を特定してください。
残存 CRITICAL があれば設計書の該当箇所を示して壁打ちへの差し戻しレポートを出してください。
```

---

## 所要時間目安

| パターン | director | 全工程合計 |
|---|---|---|
| P1（Opus） | 10〜20 分 | 30〜60 分 |
| P1+1（Sonnet 節約版） | なし | 15〜30 分 |

---

## 関連ドキュメント

- `docs/operations/claude_code_prompts.md` — 全パターン対応プロンプト集（P1〜P7・AV・KW・DBG 等）
- `.claude/skills/new-scenario/SKILL.md` — `/new-scenario` スキル詳細仕様
- `.claude/skills/flow-draft/SKILL.md` — `/flow-draft` スキル詳細仕様
- `docs/governance/loop-governance.md` — パイプライン全体設計（VFB 製造ライン v2）
- `docs/brekeke/モジュール選定ガイド_v2.md` — ブロック型の使い分け
- `schemas/qa_validator.py` — 設計書検証ルール（KNOWN_BLOCK_TYPES 等）
