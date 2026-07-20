# Claude Code 運用プロンプト集（P1〜P7 全パターン対応）

> **用途**: このファイルのプロンプトをコピーして Claude Code に貼り付けるだけで、
> 日常オペレーション（新規構築・修正・検品・辞書管理）を実行できる。
>
> **ルール**:
> - `{施設名}` `{フロー名}` `{...}` は実際の値に置き換えること
> - 保護ゾーン（`docs/` `tools/` `scripts/` 等）の恒久変更には PR レビューが必要
> - `output/scenarios/{施設}_{flow}/` は自由ゾーン — 確認不要で書き込んでよい
> - Push は必ず人間が承認する

---

## ファイル選択ガイド

| やりたいこと | プロンプト | 主な変更ファイル |
|---|---|---|
| 新しいシナリオを最初から作る（標準・Opus） | **P1-A〜P1-E** | `output/scenarios/{施設}_{flow}/` |
| 新しいシナリオを作る（トークン節約・Sonnet） | **P1+1-A〜P1+1-D** | `output/scenarios/{施設}_{flow}/` |
| 既存シナリオを部分修正する | **P2-A〜P2-C** | `output/scenarios/{施設}_{flow}/` |
| サブフローを別シナリオへコピーする | **P3** | `output/scenarios/{施設}_{flow}/` |
| IVR プロパティ（TTS 文言）を生成する | **P4** | `output/scenarios/{施設}_{flow}/` |
| JSON 構造チェック・自動修正 | **P5-A〜P5-C** | `output/json/` |
| Scripts ES5 を再生成する | **P5-D** | `output/json/` |
| AmiVoice 辞書 CSV を再生成する | **P5-E** | `output/scenarios/{施設}_{flow}/amivoice/` |
| 部品（module/script）を受け入れ検査 | **P6-A〜P6-C** | `modules/` |
| 連結テストケースを生成する | **P7-A〜P7-B** | `output/scenarios/{施設}_{flow}/` |
| 誤認識ログを追加・再反映 | **AV-A〜AV-C** | `docs/amivoice/` |
| Scripts キーワードを追加する | **KW-A〜KW-D** | `docs/amivoice/keyword_presets.yaml` |
| 全般的なデバッグ・確認 | **DBG-A〜DBG-D** | 読み取りのみ |
| spec（仕様書）を編集・追加する | **SPEC-A〜SPEC-D** | `docs/governance/flow-spec-scripts-faq-testing.md` |
| 新モジュールの仕様策定・oracle 作成 | **MOD-A〜MOD-C** | `modules/` |
| ログ分析・誤認識レポート | **LOG-A〜LOG-D** | `output/scenarios/{施設}_{flow}/logs/` |
| 特定サブフローブロックを追加する | **SUB-A〜SUB-C** | `output/scenarios/{施設}_{flow}/` |
| TTS 発話文言を検証・修正する | **TTS-A〜TTS-C** | `output/scenarios/{施設}_{flow}/` |
| **TTS 台本ドキュメントを生成する（全分岐経路）** | **TTS-D** | `output/scenarios/{施設}_{flow}/` |
| **TTS 発話確認用 bivr を生成する（実機で通し確認）** | **TTS-D2** | `output/scenarios/{施設}_{flow}/` |
| シナリオ完成チェックリストを実行 | **CHK-A〜CHK-C** | 全ファイル確認 |
| 追加・修正依頼をタスクに変換する | **REQ-A〜REQ-C** | 依頼内容による |
| **決定論化（Phase A/B）を設定・確認する** | **DET-A〜DET-D** | `output/scenarios/{施設}_{flow}/` |
| **設計書 YAML の自動修正を実行する** | **YAML-FIX-A〜YAML-FIX-B** | `output/scenarios/{施設}_{flow}/` |
| 新規ブロック型の YAML 記法を確認する | **BLK-A〜BLK-J** | `output/scenarios/{施設}_{flow}/` |

---

## P1 — 新規シナリオ構築

### P1-A: 設計書 YAML を director で生成する

```
次のシナリオの設計書 YAML を作成してください。

施設名: {施設名}
フロー名: {フロー名}
出力パス: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

【要件】
{顧客要望を箇条書きで記載}

- 診療科: {診療科リスト（例: 内科, 外科, 整形外科）}
- 受付時間: {例: 平日 9:00-17:00, 土曜 9:00-12:00}
- FAQ: {よくある質問があれば記載}
- 特記事項: {例: 初診のみ受付, 紹介状必須 等}

director を呼び出して設計書を生成し、qa_validator.py で検証してください。
CRITICAL が残った場合は差し戻しレポートを出力してください。
```

---

### P1-B: 設計書から scaffold JSON を生成する

```
以下の設計書 YAML から scaffold JSON を生成してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
出力先: output/json/scaffold_{施設名}_{フロー名}.json

python scripts/scaffold_generator.py を実行して scaffold を生成し、
scripts/layout_calculator.py でレイアウトを計算してください。
エラーがあれば内容を報告してください。
```

---

### P1-C: Scripts ES5 を生成して scaffold に埋め込む

```
以下のファイルから Scripts ES5 を生成して scaffold JSON に埋め込んでください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
scaffold: output/json/scaffold_{施設名}_{フロー名}.json
出力先: output/json/scaffold_{施設名}_{フロー名}_scripted.json

コマンド:
python tools/gen_scripts.py \
    --yaml output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
    --scaffold output/json/scaffold_{施設名}_{フロー名}.json \
    --out output/json/scaffold_{施設名}_{フロー名}_scripted.json

WARN が出た場合は内容を教えてください（input_module 不一致, preset 未定義 等）。
```

---

### P1-D: OpenAI プロンプトを prompter で記述する

```
以下の scaffold JSON に対して prompter で OpenAI プロンプトを記述してください。

scaffold: output/json/scaffold_{施設名}_{フロー名}_scripted.json
設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
出力先: output/json/prompted_{施設名}_{フロー名}.json
プロンプトサイドカー: output/scenarios/{施設名}_{フロー名}/prompts_{施設名}_{フロー名}.md

promptter エージェントを呼び出してください。
generate_by_OpenAI モジュールのみ対象です。

注意:
- 希望日/希望時期 の hearing は scaffold が固定プロンプトを自動埋め込み済み（prompter 不要）
- polar / choices[] 宣言済みの hearing は yes_no_classifier / n_choice スクリプトに
  置換済みのため generate_by_OpenAI は存在しない（prompter スキップ対象）
```

---

### P1-E: validator で検証 → auto_fixer で自動修正 → 最終 JSON を確定する

```
以下の JSON を validator で検証し、auto_fixer で自動修正して最終 JSON を出力してください。

対象 JSON: output/json/prompted_{施設名}_{フロー名}.json
出力先: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json

手順:
1. python schemas/validator.py --json-report output/json/prompted_{施設名}_{フロー名}.json
2. CRITICAL があれば: python scripts/auto_fixer.py で fix_category="auto" を機械修正
3. validator 再実行で残存 CRITICAL を確認
4. tester エージェントで構造監査
5. CRITICAL が残れば差し戻しレポートを出力して halt する（自律修復しない）
6. すべて PASS なら output/scenarios/{施設名}_{フロー名}/ に collect する

gen_properties.py も合わせて実行してください:
python scripts/gen_properties.py \
    --yaml output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
    --out output/scenarios/{施設名}_{フロー名}/properties_{施設名}_{フロー名}.md
```

---

## P1+1 — 新規シナリオ構築（トークン節約版・Pattern 11）

> **概要**: Pattern 1（Opus director）の代わりに **flow-draft MD → 決定論スケルトン → Sonnet 補完**で設計書 YAML を生成する。
> Opus 呼び出しを不要にするため、トークン消費が大幅に少ない（Opus 20〜40k → Sonnet 3〜8k 相当）。
>
> **使う場面**: `/flow-draft` で構造ドラフトをすでに壁打ちして人間が承認済みの場合。
> 構造（block type / 分岐先）が確定しているため、Sonnet は TTS 文言・context 名・ラベル名等の「文言系」だけを埋める。
>
> **P1 との使い分け**:
> | | P1（標準） | P1+1（節約） |
> |---|---|---|
> | 設計書生成 | Opus director が全量を生成 | Sonnet が文言系のみ補完 |
> | 前提条件 | 顧客資料があれば OK | `/flow-draft` 壁打ち済みが必要 |
> | トークン消費 | 多（Opus 20〜40k） | 少（Sonnet 3〜8k） |
> | 構造品質 | director が判断 | human + flow-draft で確定済み |
> | 向いている場面 | 複雑な分岐・初回新規 | 標準的な構造・繰り返し作業 |

### P1+1-A: flow-draft 壁打いを実施してスケルトンを準備する（前提）

> `/flow-draft` を実行して構造ドラフトを確定し、MD を保存する。

```
/flow-draft {施設名} {フロー名}
```

壁打ち完了後、flow-draft の MD 出力を以下のパスに保存してください:

```bash
# flow-draft の出力（チャットに表示された MD）をファイルに書き出す
# ファイル名の YYYYMMDD は本日の日付
output/scenarios/{施設名}_{フロー名}/flow_draft_YYYYMMDD.md
```

確認ポイント:
- 各 step の block type が正しいか（date_of_call_classifier は廃止・使用不可 → `script: custom` を使う）
- N択 enum hearing に `choices:` が宣言されているか（なければ n_choice 化されない）
- polar hearing（はい/いいえ系）は choices: 不要（yes_no_classifier が自動適用）
- 分岐の抜け・漏れがないか（`match: other` の行き先を含む）
- 人間が「OK」を出してから次のステップへ進む

---

### P1+1-B: yaml_scaffold_template.py でスケルトン YAML を生成する

```bash
python3 tools/yaml_scaffold_template.py \
    --flow-draft output/scenarios/{施設名}_{フロー名}/flow_draft_YYYYMMDD.md \
    --facility {施設名} \
    --flow {フロー名}
```

出力: `output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}_skeleton.yaml`

スケルトン YAML の内容:
- `scenario_flow` ブロック構造は **決定論的に生成済み**（block type・次ステップ・choices[] が埋まっている）
- `{PLACEHOLDER_TTS}` / `{PLACEHOLDER_SAVE_TO}` / `{PLACEHOLDER_STATUS}` 等は未記入
- `context_fields` / `hearing_items` / `step_details` / `termination_patterns` は PLACEHOLDER のみ

---

### P1+1-C: orchestrator で Pattern 11 を起動する（スケルトン → Sonnet 補完 → 以降 P1 と同じ）

```bash
python3 scripts/orchestrator.py --pattern 11 \
    --spec docs/migration/{施設名}_{フロー名}.md \
    --assignee hamaguchi --env demo
```

> `--spec` は顧客資料（MD / PDF の markitdown 変換）を Sonnet に渡すために使用。
> `flow_draft_*.md` は `output/scenarios/{施設名}_{フロー名}/` から自動検索される。
> `--spec` 未指定でも動作するが、TTS 文言の品質が下がる可能性がある。

パイプラインの流れ（Pattern 11）:
```
branch
  → yaml_scaffold  ← tools/yaml_scaffold_template.py（決定論・高速）
  → yaml_fill      ← Sonnet が PLACEHOLDER を補完（customer_doc 参照）
  → qa             ← qa_validator + yaml_auto_fixer（機械検証）
  → scaffold       ← scaffold_generator.py（JSON 生成）
  → gen_scripts    ← スクリプト ES5 自動生成
  → prompter_props ← OpenAI プロンプト記述 + properties 生成
  → merge → validator → tester → auto_fixer
  → collect → commit → oracle → P7 → P6 → approve
```

所要時間目安: スケルトン 1 分 + Sonnet 補完 3〜5 分 + 全工程 15〜30 分

---

### P1+1-D: スケルトン YAML の PLACEHOLDER を手動で補完する（Sonnet を使わない場合）

> Sonnet 補完を使わず、人間が直接 `_skeleton.yaml` を編集して設計書を作る場合。

```bash
# 1. スケルトンを生成
python3 tools/yaml_scaffold_template.py \
    --flow-draft output/scenarios/{施設名}_{フロー名}/flow_draft_YYYYMMDD.md \
    --facility {施設名} --flow {フロー名}

# 2. スケルトンを最終 YAML にコピー
cp output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}_skeleton.yaml \
   output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

# 3. 人間が {PLACEHOLDER_*} を全て置換する（エディタで編集）

# 4. qa_validator で検証
python3 schemas/qa_validator.py \
    output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

# 5. P1-B 以降（scaffold → prompter → validator → collect）を orchestrator で実行
python3 scripts/orchestrator.py --pattern 1 \
    --spec output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
    --resume-step scaffold \
    --assignee hamaguchi --env demo
```

---

## P2 — 既存シナリオの修正

### P2-A: 既存 JSON の特定ブロックを修正する（外科的パッチ）

```
以下の JSON の特定モジュールを修正してください。

対象 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
修正指示:
  - モジュール名: {モジュール名（例: Scripts_用件）}
  - 修正内容: {例: キーワードに「お薬の相談」を追加する}

fixer エージェント（Pattern 2 外科的パッチモード）を使用してください。
修正後に validator で検証し、CRITICAL がなければ報告してください。
```

---

### P2-B: 既存 JSON の TTS 文言を一括変更する

```
以下の JSON の TTS 文言を変更してください。

対象 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
変更内容:
  - 変更前: 「{変更前の文言}」
  - 変更後: 「{変更後の文言}」
  - 対象モジュール: {モジュール名 or "すべての TTS モジュール"}

変更後に gen_properties.py で properties_*.md を再生成してください:
python scripts/gen_properties.py \
    --yaml output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
    --out output/scenarios/{施設名}_{フロー名}/properties_{施設名}_{フロー名}.md
```

---

### P2-C: OpenAI プロンプトを特定ブロックだけ書き直す（リフレッシュ）

```
以下の JSON の OpenAI プロンプトを書き直してください。

対象 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
対象モジュール: {モジュール名（例: OpenAI_用件分類）}
修正理由: {例: 「薬の相談」が NO_RESULT になるため分岐追加}
設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

promptter エージェントの Pattern 2 リフレッシュモードを使用してください。
修正後にプロンプトサイドカー（prompts_*.md）も更新してください。
```

---

## P3 — サブフロー再利用

### P3: サブフローを別シナリオへコピーする

```
以下のサブフローを新しいシナリオへコピーしてください。

コピー元シナリオ: output/scenarios/{コピー元施設}_{コピー元フロー}/
コピー先シナリオ: output/scenarios/{コピー先施設}_{コピー先フロー}/
コピーするサブフロー名: {サブフロー名（例: PatientName, DateSelection）}

コマンド:
python tools/copy_subflows.py \
    --src output/scenarios/{コピー元施設}_{コピー元フロー}/{コピー元施設}_{コピー元フロー}.json \
    --dst output/scenarios/{コピー先施設}_{コピー先フロー}/{コピー先施設}_{コピー先フロー}.json \
    --subflows {サブフロー名}

コピー後に validator で検証してください。
```

---

## P4 — IVR プロパティ生成

### P4-A: properties_*.md を生成する

```
以下の設計書から IVR プロパティ（TTS 発話文言）を生成してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
scaffold または最終 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
出力先: output/scenarios/{施設名}_{フロー名}/properties_{施設名}_{フロー名}.md

コマンド:
python scripts/gen_properties.py \
    --yaml output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
    --out output/scenarios/{施設名}_{フロー名}/properties_{施設名}_{フロー名}.md

生成後に TTS モジュール数と properties の行数を報告してください。
```

---

### P4-B: 特定モジュールの TTS 文言だけ確認する

```
以下の JSON の TTS モジュールをすべてリストアップしてください。

対象 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json

モジュール名と {tts_g:...} 形式の文言を一覧表にしてください。
変更したいものがあれば指示します。
```

---

## P5 — 検証・自動修正

### P5-A: validator で JSON を検証する

```
以下の JSON を validator で検証してください。

対象 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json

コマンド:
python schemas/validator.py output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json

CRITICAL / WARNING の数と内容を報告してください。
```

---

### P5-B: auto_fixer で自動修正可能な CRITICAL を修正する

```
以下の JSON を auto_fixer で自動修正してください。

対象 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json

手順:
1. python schemas/validator.py --json-report {対象 JSON} > /tmp/validator_report.json
2. python scripts/auto_fixer.py --report /tmp/validator_report.json --json {対象 JSON}
3. validator 再実行で残存 CRITICAL を確認
4. 残存 CRITICAL があれば内容を報告する（自律修復しない）
```

---

### P5-C: tester で構造監査を実行する

```
以下の JSON を tester で構造監査してください。

対象 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json

tester エージェントを呼び出して tester.py を実行してください。
AUD-1/AUD-2/R-1/R-2/R-3 の結果を報告してください。
```

---

### P5-D: Scripts ES5 を再生成して JSON に再埋め込みする

```
Scripts ES5 を再生成して JSON に埋め込み直してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
現在の JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
出力先: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json（上書き）

コマンド:
python tools/gen_scripts.py \
    --yaml output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
    --scaffold output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json \
    --out output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json

再生成後に validator で検証してください。
```

---

### P5-E: AmiVoice 辞書 CSV を再生成する

```
AmiVoice 辞書 CSV をノード別に再生成してください。

base_keywords: docs/amivoice/base_keywords.yaml
設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
出力先: output/scenarios/{施設名}_{フロー名}/amivoice/

コマンド:
python tools/gen_amivoice_dict.py \
    --base docs/amivoice/base_keywords.yaml \
    --yaml output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
    --facility {施設名} \
    --flow {フロー名} \
    --out-dir output/scenarios/{施設名}_{フロー名}/amivoice

生成されたノード別 CSV ファイル一覧と各エントリ数を報告してください。
```

---

## P6 — 部品受入検査

### P6-A: oracle_gate で部品の hash を確認する

```
以下の JSON に含まれる Scripts/module 部品を oracle_gate で検証してください。

対象 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json

python tools/oracle_gate.py を実行して:
- engine 一致 / spec 認定済み → PASS
- engine 不一致 → BLOCK（内容を報告）
- 新規 spec → 受入要求（内容を報告）

結果サマリーを出力してください。
```

---

### P6-B: 新しい部品（module/script）の受入テストを実行する

```
以下の新しい部品の受入テストを実行してください。

部品名: {モジュール名（例: Scripts_個人法人）}
部品ファイル: modules/{モジュール名}/
設計書（REQUIREMENTS.md）: modules/{モジュール名}/REQUIREMENTS.md

手順:
1. python modules/{モジュール名}/oracle.py でオラクルを確認
2. python modules/{モジュール名}/test_oracle.py を実行して全ケース PASS を確認
3. 結果を modules/README.md の認定レジストリに追記する（変更内容を提案として提示）

注: Brekeke 実機受入（Pattern 6 テストフロー）は人間が実行します。
test_oracle.py 全 PASS の場合のみ「機械テスト PASS」として報告してください。
```

---

### P6-C: certified_hashes.json を更新する（新規 spec 受入）

```
以下の部品の新規 spec を受け入れて certified_hashes.json を更新してください。

部品名: {モジュール名}
spec ハッシュ: {hash 値（oracle_gate の出力から取得）}

注: 実機 Pattern 6 テスト PASS を人間が確認済みであることが前提です。
確認が取れていない場合は実行しないでください。

modules/certified_hashes.json への追記内容を提案として提示してください。
```

---

## P7 — 連結テスト

### P7-A: P7 連結テストケースを自動生成する

```
以下のシナリオの P7 連結テストケースを生成してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
出力先: output/scenarios/{施設名}_{フロー名}/p7_cases_{施設名}_{フロー名}.md

コマンド:
python tools/gen_p7_cases.py \
    --yaml output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
    --out output/scenarios/{施設名}_{フロー名}/p7_cases_{施設名}_{フロー名}.md

生成されたケース数（エッジ数）と主要なパスを報告してください。
リピートパターン（RPT-001〜RPT-004）が含まれているか確認してください。
```

---

### P7-B: STT スタブ bivr を生成して連結テストを準備する

```
以下のシナリオの STT スタブ bivr を生成してください。

テストケース: output/scenarios/{施設名}_{フロー名}/p7_cases_{施設名}_{フロー名}.md
出力先: output/scenarios/{施設名}_{フロー名}/stub_stt_{施設名}_{フロー名}.bivr

コマンド:
python connection_test/stub_stt_connection.py \
    --cases output/scenarios/{施設名}_{フロー名}/p7_cases_{施設名}_{フロー名}.md \
    --out output/scenarios/{施設名}_{フロー名}/stub_stt_{施設名}_{フロー名}.bivr

注: 実機への読み込み・発信テストは人間が実行します。
生成されたケース数を確認して報告してください。
```

---

## AV — AmiVoice 辞書管理

### AV-A: 誤認識ログに 1 件追加する

```
AmiVoice の誤認識ログに以下のエントリを追加してください。

ファイル: docs/amivoice/misrecognition_log.csv

追加内容:
  - wrong（誤認識された言葉）: {例: お薬}
  - correct（本来認識してほしい言葉）: {例: 予約}
  - count（発生件数）: {例: 8}
  - note（メモ）: {例: AmiVoice 音響混同}
  - target_nodes（対象ノード、複数はパイプ区切り）: {例: 入力_用件}

追加後に CSV の末尾 3 行を確認して報告してください。
※このファイルは保護ゾーンです。変更後は PR を作成してレビューを依頼してください。
```

---

### AV-B: 誤認識ログを一括追加する

```
AmiVoice の誤認識ログに以下のエントリを一括追加してください。

ファイル: docs/amivoice/misrecognition_log.csv

追加内容（CSV 形式）:
wrong,correct,count,note,target_nodes
{誤認識1},{正解1},{件数1},{メモ1},{対象ノード1}
{誤認識2},{正解2},{件数2},{メモ2},{対象ノード2}

追加後に docs/amivoice/misrecognition_log.csv の全行数を報告してください。
※このファイルは保護ゾーンです。変更後は PR を作成してレビューを依頼してください。
```

---

### AV-C: base_keywords.yaml にキーワードを追加する

```
base_keywords.yaml に以下のキーワードを追加してください。

ファイル: docs/amivoice/base_keywords.yaml
カテゴリ: {例: youken / faq / department / date / repeat}

追加エントリ:
  word: {単語}
  reading: {読み（ひらがな）}
  priority: {high / medium / low}
  target_nodes: [{対象ノード名}]
  note: {備考（誤認識例など）}

追加後にカテゴリ内の全エントリ数を報告してください。
※このファイルは保護ゾーンです。変更後は PR を作成してレビューを依頼してください。
```

---

## KW — Scripts キーワード管理

### KW-A: keyword_presets.yaml に新しいプリセットを追加する

```
keyword_presets.yaml に新しいプリセットを追加してください。

ファイル: docs/amivoice/keyword_presets.yaml

プリセット名: {英数字・アンダースコアのみ（例: jibun_futan）}
note: {「どの TTS 文言に対する回答か」を説明}
keywords:
  - {発話パターン1}
  - {発話パターン2}
  - {発話パターン3}
  ...

追加後にプリセット総数を報告してください。
※このファイルは保護ゾーンです。変更後は PR を作成してレビューを依頼してください。
```

---

### KW-B: 既存プリセットにキーワードを追加する

```
以下のプリセットにキーワードを追加してください。

ファイル: docs/amivoice/keyword_presets.yaml
プリセット名: {例: hai}

追加するキーワード:
  - {キーワード1}
  - {キーワード2}

追加後にそのプリセットの全キーワードを確認して報告してください。
※このファイルは保護ゾーンです。変更後は PR を作成してレビューを依頼してください。
```

---

### KW-C: 設計書 YAML の enum_classifier ブロックにキーワードを追加する

```
設計書の enum_classifier ブロックに施設固有キーワードを追加してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
対象ブロック: {module_name（例: Scripts_個人法人）}
対象ラベル: {label（例: 個人）}

追加するキーワード（preset に加えて施設固有で追加したいもの）:
  - {キーワード1}
  - {キーワード2}

変更後に gen_scripts.py を再実行して ES5 が正しく生成されるか確認してください:
python tools/gen_scripts.py \
    --yaml output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
    --scaffold output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json \
    --out output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
```

---

### KW-D: AmiVoice と Scripts の両方に同時追加する

```
以下の単語を AmiVoice 辞書と Scripts キーワードの両方に追加してください。

単語: {例: 在宅診療}
読み: {例: ざいたくしんりょう}
対象ノード: {例: 入力_用件}
対象 Scripts ブロック: {例: Scripts_用件, label: 予約}
施設: {施設名}
フロー: {フロー名}

手順:
1. docs/amivoice/base_keywords.yaml の youken カテゴリに追加（保護ゾーン → PR 必要）
2. output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml の
   該当 enum_classifier または youken ブロックの keywords: に追加
3. gen_amivoice_dict.py を再実行してノード別 CSV を更新
4. gen_scripts.py を再実行して ES5 を更新
5. validator で確認

手順 1 の保護ゾーン変更は PR 用の変更内容を提案として出力し、
手順 2〜5 は自律実行してください。
```

---

## DBG — デバッグ・確認

### DBG-A: 特定モジュールの Scripts コードを確認する

```
以下の JSON から特定モジュールの Scripts コードを取り出して表示してください。

対象 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
モジュール名: {例: Scripts_用件}

params.script の内容を表示してください。
リピート検知ブロック（もう一度/もう一回）が含まれているか確認してください。
```

---

### DBG-B: AmiVoice ノード別辞書 CSV を確認する

```
以下のノードの AmiVoice 辞書 CSV を確認してください。

CSV ファイル: output/scenarios/{施設名}_{フロー名}/amivoice/{ノード名}.csv

全エントリをカテゴリ別に表示してください。
high priority のエントリ数を報告してください。
```

---

### DBG-C: 設計書 YAML の script_blocks を一覧表示する

```
以下の設計書 YAML の script_blocks をすべて表示してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

type / module_name / input_module / preset名 / repeat_guard の値を表形式で報告してください。
repeat_guard が false になっているブロックがある場合は理由を確認してください。
```

---

### DBG-D: keyword_presets.yaml の利用状況を確認する

```
現在の keyword_presets.yaml に定義されているプリセット一覧と、
output/scenarios/ 内の設計書 YAML でそれぞれ何回使われているかを調べてください。

ファイル: docs/amivoice/keyword_presets.yaml
検索対象: output/scenarios/ 配下の全 *.yaml ファイル

各プリセット名とその利用回数を表にして報告してください。
```

---

## SPEC — 仕様書（flow-spec-scripts-faq-testing.md）の編集

### SPEC-A: P1〜P7 の特定セクションを修正・追記する

```
docs/governance/flow-spec-scripts-faq-testing.md の以下のセクションを修正してください。

対象セクション: §{セクション番号}（例: §8-2 Scripts YAML 記法）
修正内容:
  {修正・追記したい内容を具体的に記述}

修正後に変更箇所の前後 10 行を確認して報告してください。
※このファイルは保護ゾーンです。変更後は PR を作成してレビューを依頼してください。
```

---

### SPEC-B: 新しいブロック型（module）の仕様を追加する

```
docs/governance/flow-spec-scripts-faq-testing.md に新しいブロック型の仕様を追加してください。

追加場所: §8（Scripts 自動生成）の block type 一覧表 + 新セクション

新ブロック型の情報:
  type 名: {例: date_classifier}
  用途: {例: 希望日・変更希望日の分類}
  input_module: {例: 入力_予約希望日}
  output（setResult の値）: {例: GOZEN / GOGO / SPECIFIC_DATE / NO_RESULT}
  repeat_guard: {true / false}
  YAML 記法例:
    {YAML サンプルを記載}
  gen_scripts.py への追加方法: {例: gen_date_classifier_script 関数を追加}

§8-1 の block type 表への行追加と §8-X の詳細セクション作成を両方行ってください。
※このファイルは保護ゾーンです。変更後は PR を作成してレビューを依頼してください。
```

---

### SPEC-C: P7 マスターテストケースファイルにテストケースを追加する

```
P7 連結テストのマスターテストケースファイルにテストケースを追加してください。

対象シナリオ: output/scenarios/{施設名}_{フロー名}/p7_cases_{施設名}_{フロー名}.md
追加するテストケース:
  - ケース ID: {例: TC-025}
  - シナリオ名: {例: 診療科を言わずに沈黙した場合}
  - 入力シーケンス: {例: 用件=予約 → 診療科=（無音3秒）→ NO_RESULT → TTS再読}
  - 期待する結果: {例: REPEAT → TTS再読 → 2回目 REPEAT_LIMIT → オペレーター転送}
  - 関連ルール: {例: §10 リピートパターン}

追加後にテストケース総数を報告してください。
リピートパターン（RPT-001〜RPT-004）のカバー状況も確認してください。
```

---

### SPEC-D: 既存 spec の誤りを修正する

```
docs/governance/flow-spec-scripts-faq-testing.md に誤りがあります。修正してください。

誤りの場所: §{セクション番号}、{行の特徴（例: "repeat_limit のデフォルト値"）}
現在の記述: {誤っている内容}
正しい記述: {正しい内容}
修正理由: {なぜ誤りか}

修正後に該当箇所を表示してください。
※このファイルは保護ゾーンです。変更後は PR を作成してレビューを依頼してください。
```

---

## MOD — 新規モジュール（部品）の仕様策定・追加

### MOD-A: 新しい module/script の REQUIREMENTS.md を作成する

```
以下の新しい部品の REQUIREMENTS.md を作成してください。

部品名: {例: Scripts_sentei_ryoyouhi}
ディレクトリ: modules/{部品名}/
用途: {例: 選定療養費の同意確認（はい/いいえ分類）}

REQUIREMENTS.md に含める内容:
  1. 入力: input_module 名と getModuleResult で取得するデータ形式
  2. 出力: setResult の値一覧（例: 同意 / 不同意 / REPEAT / REPEAT_LIMIT / NO_RESULT）
  3. 分岐ロジック: 各キーワードとその対応 setResult
  4. repeat_guard: もう一度/もう一回 の処理（§10 準拠）
  5. エッジケース: 空入力 / 短すぎる発話 / 混在発話
  6. テストケース: 全分岐を網羅する入力例と期待出力

作成後に REQUIREMENTS.md のパスを報告してください。
```

---

### MOD-B: oracle.py と test_oracle.py を生成する

```
以下の部品の Python オラクルを生成してください。

部品名: {部品名}
REQUIREMENTS.md: modules/{部品名}/REQUIREMENTS.md

生成するファイル:
  1. modules/{部品名}/oracle.py   — JS ロジックを Python で再現
  2. modules/{部品名}/test_oracle.py — REQUIREMENTS.md の全テストケースを pytest で実装

生成後に python modules/{部品名}/test_oracle.py を実行して全 PASS を確認してください。
FAIL があれば oracle.py のロジックを修正してください。
```

---

### MOD-C: gen_scripts.py に新しいブロック型のジェネレーターを追加する

```
gen_scripts.py に新しいジェネレーター関数を追加してください。

追加する関数名: gen_{type_name}_script
対応する type: {type 名（例: date_classifier）}
REQUIREMENTS.md: modules/{部品名}/REQUIREMENTS.md

要件:
  - build_input_reader() を使って input_module から text を取得
  - build_repeat_guard(repeat_limit) でリピート検知を先頭に挿入（repeat_guard デフォルト True）
  - build_branches() または独自の ES5 ロジックで分岐
  - GENERATORS 辞書に "{type_名}": gen_{type_name}_script を追加

生成後に以下のコマンドで動作確認してください:
python tools/gen_scripts.py \
    --yaml {テスト用 YAML パス} \
    --scaffold {テスト用 scaffold パス} \
    --out /tmp/test_scripted.json

※gen_scripts.py は保護ゾーンです。変更後は PR を作成してレビューを依頼してください。
```

---

## LOG — ログ読み取り・分析・レポート

### LOG-A: 実通話ログから誤認識を抽出してレポートする

```
以下の通話ログファイルから AmiVoice 誤認識パターンを抽出してレポートしてください。

ログファイル: {ログファイルのパス（例: output/scenarios/{施設}_{flow}/logs/call_log_*.csv）}
対象期間: {例: 2026-07-01 〜 2026-07-09}

抽出する情報:
  1. NO_RESULT になった発話テキストとその入力モジュール
  2. 発生回数（5件以上を high priority として分類）
  3. 想定される正しい認識テキスト
  4. 関連する Scripts モジュール

出力形式:
  - サマリー表（誤認識語 / 件数 / 正解 / 対象ノード）
  - docs/amivoice/misrecognition_log.csv への追記候補（CSV 形式）

追記候補を確認したうえで、追記してよければ「AV-B: 誤認識ログを一括追加する」を実行してください。
```

---

### LOG-B: NO_RESULT 発生状況を分析して改善提案を出す

```
以下のログから NO_RESULT が多い Scripts モジュールを特定して改善提案を出してください。

ログファイル: {ログファイルのパス}

分析内容:
  1. モジュール別 NO_RESULT 発生回数ランキング（上位 10 件）
  2. 各モジュールで NO_RESULT になった発話テキスト例（上位 5 件ずつ）
  3. 改善提案:
     a. キーワード追加で解決できるもの → KW-C または KW-D のプロンプトを提示
     b. プリセット追加が必要なもの → KW-A のプロンプトを提示
     c. OpenAI へのフォールバック見直しが必要なもの → 設計書修正を提案

改善提案を優先度（高/中/低）つきで報告してください。
```

---

### LOG-C: リピート発生状況を分析する（§10 遵守確認）

```
以下のログからリピート発生状況を分析してください（§10 聞き返しリピートパターン）。

ログファイル: {ログファイルのパス}

確認内容:
  1. REPEAT / REPEAT_LIMIT の発生回数（モジュール別）
  2. REPEAT_LIMIT に至ったコール数とオペレーター転送率
  3. リピートが多いモジュール TOP 5（TTS 文言の改善候補）
  4. repeat_guard が未設定のモジュールがあればリスト（§10 違反）

「REPEAT_LIMIT → オペレーター転送」率が 10% を超えるモジュールは
TTS 文言の見直しを推奨として報告してください。
```

---

### LOG-D: パイプライン実行ログからエラーを抽出する

```
以下のパイプラインログからエラー・WARNING を抽出して分類してください。

ログファイル: {例: output/scenarios/{施設}_{flow}/pipeline_state_{施設}_{flow}.json}
または: {例: output/reports/test_report_*.md}

分類:
  - CRITICAL（即時対応必要）: 内容と修正方法を提示
  - WARNING（要確認）: 内容と影響範囲を報告
  - INFO（正常動作）: スキップ

CRITICAL がある場合は P5-B（auto_fixer）または人間壁打ちへの差し戻しを提案してください。
```

---

## SUB — サブフロー（特定ブロック）の新規作成

### SUB-A: 既存フローに新しいサブフローブロックを追加する

```
以下のフロー JSON に新しいサブフローブロックを追加してください。

対象 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

追加するサブフロー:
  名前: {例: DateSelection_変更希望日}
  用途: {例: 予約変更希望日を聴取する}
  接続元モジュール: {例: TTS_変更内容確認 の next}
  構成:
    - TTS: {発話文言（例: 「ご変更を希望される日時をお聞かせください」）}
    - 入力: {input_module 名（例: 入力_変更希望日）}
    - Scripts/OpenAI: {分類方法（例: OpenAI で日付正規化）}
    - 分岐: {例: DATE → 確認ステップ / NO_RESULT → リトライ / REPEAT → TTS 再読}

fixer エージェント（Pattern 2 外科的パッチモード）または
設計書 YAML を更新して scaffold を再生成する方法どちらが適切か判断して実行してください。
修正後に validator で検証してください。
```

---

### SUB-B: 設計書 YAML に新しい scenario_flow ブロックを追加する

```
設計書 YAML に新しいブロックを追加してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

追加するブロック:
  type: {例: subflow / script / enum_classifier}
  module_name: {例: Scripts_選定療養費}
  input_module: {例: 入力_選定療養費}
  接続位置: {例: 「TTS_初診説明」の後、「TTS_予約確認」の前}
  内容:
    {ブロックの設定を YAML 形式で記述}
    例:
    - type: enum_classifier
      module_name: Scripts_選定療養費
      input_module: 入力_選定療養費
      options:
        - label: 同意
          preset: sentei_ryoyouhi_agree
        - label: 不同意
          preset: sentei_ryoyouhi_disagree

追加後に qa_validator.py で設計書を検証してください。
CRITICAL がなければ scaffold を再生成して validator で確認してください。
```

---

### SUB-C: PatientName サブフローを追加する（氏名聴取）

```
以下のフローに PatientName サブフロー（氏名聴取）を追加してください。

対象 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
接続位置: {例: TTS_用件確認 の次}

PatientName サブフロー仕様（docs/brekeke/モジュール選定ガイド_v2.md §3.1.1 準拠）:
  - フロー内に PatientName サブフロー枠は 1 つだけ（重複禁止）
  - 構成: TTS_氏名確認 → 入力_氏名 → OpenAI_氏名正規化 → TTS_氏名復唱 → 確認分岐
  - 氏名は SaveContext2DB で patient_name に保存

copy_subflows.py で既存の PatientName サブフローが利用できる場合はそちらを優先してください。
```

---

## TTS — 発話文言の検証

### TTS-A: TTS 文言が設計書と一致しているか確認する

```
以下の JSON の TTS 発話文言が設計書と一致しているか確認してください。

対象 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
properties: output/scenarios/{施設名}_{フロー名}/properties_{施設名}_{フロー名}.md

確認内容:
  1. JSON 内の {tts_g:...} と設計書 step_details の tts_text が一致しているか
  2. properties_*.md の文言と JSON の {tts_g:...} が一致しているか
  3. {TTS_AI:...}（大文字）が誤用されていないか（正しくは {tts_g:...} または {tts_ai:...}）
  4. SSML タグ（<speak>, <break> 等）が混入していないか

不一致があれば一覧表（モジュール名 / JSON の文言 / 設計書の文言 / 差分）で報告してください。
```

---

### TTS-B: TTS 文言を設計書ベースで一括修正する

```
以下の JSON の TTS 文言を設計書の内容に合わせて修正してください。

対象 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

修正対象:
  - {モジュール名1}: 「{現在の文言}」→「{正しい文言}」
  - {モジュール名2}: 「{現在の文言}」→「{正しい文言}」

修正後に gen_properties.py を再実行して properties_*.md を更新してください。
validator で検証して CRITICAL がないことを確認してください。
```

---

### TTS-C: 新しい TTS モジュールの発話文言をレビューする

```
以下の TTS 発話文言を音声案内として適切か確認してください。

モジュール名: {例: TTS_選定療養費説明}
発話文言: 「{文言}」
文脈: {例: 選定療養費の説明後に同意確認を行う前の案内}

確認ポイント:
  1. 文言の長さ（長すぎないか — 目安 60 文字以内）
  2. 患者が次に何を言うべきか明確か
  3. 「はい」「いいえ」などの応答キーワードを誘導しているか
  4. 丁寧語・敬語のレベルが適切か
  5. 医療用語が平易に言い換えられているか

改善提案があれば代替文言も提示してください。
```

---

### TTS-D: 全分岐経路の台本ドキュメントを生成する

> **目的**: フロー JSON + properties ファイルから「どの経路でどの順番に何を喋るか」の台本 MD を出力し、
> 実際に電話せずに視覚的に発話内容を確認する。5 分の通話を繰り返す代わりに台本で一括確認できる。

**コマンド（ターミナルで直接実行）:**

```bash
# 全経路（リトライ・エラー分岐含む）
python3 tools/gen_scenario_script.py \
  --json  output/scenarios/{施設}_{フロー名}/json/{施設}_{フロー名}.json \
  --props output/scenarios/{施設}_{フロー名}/properties_{施設}_{フロー名}.md \
  --out   output/scenarios/{施設}_{フロー名}/scenario_script_{施設}_{フロー名}.md

# 正常経路のみ（TIMEOUT/ERROR/リトライ分岐を除外）
python3 tools/gen_scenario_script.py \
  --json  output/scenarios/{施設}_{フロー名}/json/{施設}_{フロー名}.json \
  --props output/scenarios/{施設}_{フロー名}/properties_{施設}_{フロー名}.md \
  --out   output/scenarios/{施設}_{フロー名}/scenario_script_{施設}_{フロー名}.md \
  --happy-only
```

**主なオプション:**

| オプション | デフォルト | 説明 |
|---|---|---|
| `--happy-only` | なし | 正常経路のみ出力（TIMEOUT/ERROR/NO_RESULT/false 枝を除外） |
| `--max-paths N` | 40 | 出力する経路数の上限 |
| `--max-depth N` | 60 | DFS の深さ上限（ループ防止） |
| `--hide-system` | なし | System 行（AI 判定・Script 等）を非表示にする |
| `--out PATH` | なし | 省略時は標準出力 |

**出力例:**

```markdown
### 経路 3: acceptable → AI_時間内
> **終端**: `切断_受付完了`

| # | 話者 | 発話 / アクション | モジュール名 |
|---|---|---|---|
| 1 | 🤖 Bot ← `acceptable` | お電話ありがとうございます。...のAI電話です。 | `冒頭_アナウンス` |
| 2 | ⚙️ System | [Script 判定: script_時間帯判定] | `script_時間帯判定` |
| 3 | 🧑 User | [発話 / DTMF 入力] | `入力_Q1_問い合わせ内容` |
| 4 | 🔚 終端 | [切断] | `切断_受付完了` |
```

**使い方の流れ:**
1. `--happy-only` で正常経路のみ出力 → 正常系の発話を通しで読み確認
2. オプションなしで全経路出力 → リトライ・エラー分岐の発話も確認
3. `(TTS 未設定)` と表示される行は properties ファイルに文言が設定されていないモジュール

---

### TTS-D2: TTS 発話確認用 bivr を生成して実機で通しで聞く

> **目的**: フロー .bivr + P7 cases JSON から、各分岐経路の TTS 発話を電話で通しで確認できる
> 専用 bivr を生成する。AmiVoice/DTMF-AmiVoice ノードを `@General$Script` スタブに置き換え、
> スタブ内で固定テキストを注入しつつ `$ivr.play("{tts_g:...}")` で直接発話するため、
> **properties 設定不要**・グラフ変更ゼロで「Bot 発話 → 読み返し → Bot 発話…」を電話で確認できる。
>
> **P7 連結テスト bivr とは別ファイル** (`tts_preview_*.bivr`) として出力される。

**フロー構造（生成後）:**
```
[DTMF セレクター] → 番号で経路選択 → [元のフロー開始]
  [Bot TTS] → [STT スタブ Script: 固定テキスト注入 + $ivr.play() で即時発話 + save2db]
            → [次の Bot TTS] → ...
```
> スタブ Script が `$ivr.play("{tts_g:" + val + "}")` を呼ぶため、別途 TTS ノードや
> properties 設定は不要。グラフ構造（ロジック・分岐）はそのまま。

**コマンド（ターミナルで直接実行）:**

```bash
python3 tools/gen_tts_preview_bivr.py \
  --bivr  output/scenarios/{施設}_{フロー名}/{施設}_{フロー名}.bivr \
  --cases connection_test/cases/{施設}_{フロー名}.json \
  --out   output/scenarios/{施設}_{フロー名}/tts_preview_{施設}_{フロー名}.bivr
```

**出力ファイル:**
- `tts_preview_{施設}_{フロー名}.bivr` — IVR にインポートして電話で確認（properties 追加不要）

**IVR での確認手順:**
1. `tts_preview_*.bivr` を IVR にインポートする
2. 電話をかけて DTMF で経路番号を入力（1# = ケース1、2# = ケース2…）
3. 各経路を通しで聞いて TTS 発話文言を確認する

**主なオプション:**

| オプション | デフォルト | 説明 |
|---|---|---|
| `--tag TTS_` | TTS_ | テスト用フロー名プレフィックス（本番フローと区別するため） |
| `--out PATH` | 自動 | 省略時: ソース bivr と同ディレクトリに `tts_preview_*.bivr` |
| `--entry-flow NAME` | 自動検出 | cases JSON の entry_flow が bivr と一致しない場合に明示指定 |

---

## CHK — シナリオ完成チェックリスト

### CHK-A: シナリオ完成チェックリストを実行する

```
以下のシナリオが完成基準を満たしているか全項目チェックしてください。

施設名: {施設名}
フロー名: {フロー名}
設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json
properties: output/scenarios/{施設名}_{フロー名}/properties_{施設名}_{フロー名}.md

## 設計書チェック（qa_validator.py 実行）
- [ ] qa_validator.py CRITICAL = 0
- [ ] scenario_flow の全ブロックに module_name が設定されている
- [ ] 全 AmiVoice 入力ノードに repeat_guard: true が設定されている（§10）
- [ ] FAQ ブロックに faq_map が定義されている
- [ ] 診療科ブロックに departments が定義されている
- [ ] N 択 hearing に choices[] が宣言されている（E-19 CRITICAL 回避）

## 決定論化チェック（Phase A/B）
- [ ] polar hearing（はい/いいえ系）で force_openai: true が不要に設定されていない
- [ ] choices[] を宣言した hearing で conditions ラベルと choices[].label が一致している
- [ ] 決定論化済み hearing（script_{step}）に generate_by_OpenAI が混在していない
- [ ] 希望日/希望時期 hearing に固定プロンプトが自動埋め込み済み（scaffold 出力確認）

## Scripts チェック（gen_scripts.py 実行結果）
- [ ] 全 script_blocks で WARN なし（preset 未定義 / input_module 不一致）
- [ ] 全 enum_classifier の options に preset または keywords が設定されている
- [ ] リピート検知（もう一度/もう一回）が全 ES5 コードに含まれている

## JSON 構造チェック（validator.py 実行）
- [ ] validator.py CRITICAL = 0
- [ ] N-002 / N-003 エラーなし（モジュール名重複・参照切れ）
- [ ] LAYOUT エラーなし（モジュール重なり）
- [ ] 全 generate_by_OpenAI に params.prompt が設定されている

## tester チェック（tester.py 実行）
- [ ] AUD-1 PASS（孤立モジュールなし）
- [ ] AUD-2 PASS（到達不能モジュールなし）
- [ ] R-1/R-2/R-3 PASS（ルーティング整合性）

## TTS 文言チェック（TTS-A 実行）
- [ ] 全 {tts_g:...} 形式（大文字 TTS_AI や SSML タグなし）
- [ ] 設計書の tts_text と JSON の文言が一致
- [ ] properties_*.md が最新の JSON と同期している

## AmiVoice 辞書チェック（gen_amivoice_dict.py 実行）
- [ ] ノード別 CSV が output/scenarios/{施設}_{flow}/amivoice/ に生成済み
- [ ] repeat キーワード（もう一度/もう一回）が全ノードの CSV に含まれている

## 部品受入チェック（oracle_gate 実行）
- [ ] oracle_gate.py BLOCK = 0
- [ ] 未認定 spec は受入済み（実機 P6 テスト PASS 確認済み）
- [ ] n_choice spec（choices[] から生成）は DET-D 手順で受入済み

## P7 連結テストチェック
- [ ] p7_cases_*.md が生成されている
- [ ] RPT-001〜RPT-004 のリピートケースが含まれている
- [ ] stub_stt_*.bivr が生成されている

各チェック項目の PASS/FAIL を表にして報告してください。
FAIL がある項目は対応するプロンプト番号（例: P5-A, TTS-B, DET-B）を提示してください。
```

---

### CHK-B: 設計書フルスペックレポートを出力する

```
以下の設計書の全仕様をレポート形式で出力してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

出力内容:
  ## 1. シナリオ概要
    - 施設名 / フロー名 / 作成日 / バージョン
    - 対応パターン（P1〜P7）
  ## 2. フロー構成
    - scenario_flow のブロック一覧（type / module_name / input_module）
    - 接続関係（どのモジュールからどこへ分岐するか）
  ## 3. Scripts ブロック一覧
    - 各 script_block の type / preset / keywords / repeat_guard
  ## 4. FAQ 一覧
    - faq_map の全 Q&A
  ## 5. 診療科一覧
    - departments の全診療科名
  ## 6. TTS 文言一覧
    - 全 tts_text（モジュール名 → 文言）
  ## 7. ContextMatchRouter 設計
    - 保存するセッション変数一覧（SaveContext2DB）
    - <%変数名%> 参照一覧
  ## 8. 終話チェーン
    - termination_patterns の全パターン
  ## 9. 決定論化状況
    - polar hearing（yes_no_classifier 使用）一覧
    - N 択 hearing（n_choice 使用）一覧
    - force_openai: true で維持している hearing と理由
    - 希望日/希望時期 固定プロンプト使用 hearing 一覧

出力先: output/scenarios/{施設名}_{フロー名}/spec_report_{施設名}_{フロー名}.md
```

---

### CHK-C: 変更差分レポートを出力する（修正前後の比較）

```
以下の JSON の修正前後を比較してレポートを出力してください。

修正前 JSON: {修正前ファイルパス（例: git stash または別名保存したもの）}
修正後 JSON: output/scenarios/{施設名}_{フロー名}/{施設名}_{フロー名}.json

比較内容:
  1. 追加されたモジュール（module_name 一覧）
  2. 削除されたモジュール
  3. 変更されたモジュール（params.script / params.prompt の差分）
  4. 変更された TTS 文言
  5. 変更されたルーティング（next / subs）
  6. 決定論化の変化（OpenAI → script_* に変わったモジュール）

出力先: output/reports/diff_report_{施設名}_{フロー名}_{日付}.md
validator の結果（修正後）も合わせて報告してください。
```

---

## REQ — 追加・修正依頼

### REQ-A: 仕様の追加依頼を整理して実行タスクに変換する

```
以下の追加依頼を実行可能なタスクに整理してください。

依頼内容:
  {依頼内容を自由記述（例: 「初診の場合に選定療養費の説明を追加したい」）}

対象シナリオ: output/scenarios/{施設名}_{フロー名}/

整理してほしいこと:
  1. 影響範囲（設計書 / JSON / Scripts / TTS / AmiVoice 辞書 / P7 テストケース）
  2. 実行順序（どのステップから始めるか）
  3. 使用するプロンプト番号（SUB-B, P1-C, TTS-B 等）
  4. 保護ゾーンへの変更が必要かどうか（PR 必要/不要）

整理結果を確認したうえで実行してよければ「はい」と返してください。
```

---

### REQ-B: 複数の修正をまとめて依頼する

```
以下の修正をまとめて実行してください。

対象シナリオ: output/scenarios/{施設名}_{フロー名}/

修正リスト:
  1. {修正内容1（例: TTS_用件確認 の文言を「〇〇」に変更）}
  2. {修正内容2（例: Scripts_診療科 に「腎臓内科」を追加）}
  3. {修正内容3（例: FAQ に「処方箋の受取について」を追加）}
  4. {修正内容4（例: 初診フローに PatientName サブフローを追加）}

各修正が完了したら validator で検証してください。
全修正完了後に CHK-A（完成チェックリスト）を実行してください。
```

---

### REQ-C: 他施設のシナリオを参考に新施設用を作る

```
以下の既存シナリオを参考にして新しい施設のシナリオを作成してください。

参考シナリオ: output/scenarios/{参考施設名}_{フロー名}/設計書_{参考施設名}_{フロー名}.yaml
新施設情報:
  施設名: {新施設名}
  フロー名: {フロー名}
  参考シナリオとの主な違い:
    - {違い1（例: 診療科が内科・外科のみ）}
    - {違い2（例: FAQ に「夜間緊急対応」を追加）}
    - {違い3（例: 選定療養費の説明は不要）}

出力先: output/scenarios/{新施設名}_{フロー名}/

P1-A〜P1-E のパイプラインを実行して新施設の設計書・JSON を生成してください。
最後に CHK-A（完成チェックリスト）で品質確認してください。
```

---

## DET — 決定論化（Phase A/B）

> **概要**: `enum` 型 hearing の OpenAI を認定スクリプト（yes_no_classifier / n_choice）に
> 自動置換する機能（PR #61/#62 で導入）。scaffold_generator.py が設計書から自動判定する。
> keystone「ライン内 LLM ゼロ」への移行作業プロンプト集。

### DET-A: polar hearing の自動判定結果を確認する（設計書変更不要）

```
以下の設計書の enum hearing が polar（はい/いいえ系）として自動判定されるか確認してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

polar と判定される条件（scaffold が自動検出）:
  - output_format: enum
  - conditions の match ラベルがすべて polar 語彙（片方だけでも可）
    肯定: はい / あり / 持っている / 該当 / 対象 / 受けた / 済み / する / はっきり 等
    否定: いいえ / なし / 持っていない / 非該当 / 対象外 / 受けていない / しない 等
  - echo_back が false（復唱確認は別途 yes_no_classifier で処理）
  - 希望日/希望時期 でない
  - force_openai: true でない

scaffold を生成して結果を確認してください:
python scripts/scaffold_generator.py \
    --yaml output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
    --out output/json/scaffold_{施設名}_{フロー名}.json

生成後に:
  1. script_{step} モジュールが生成されているか確認
  2. generate_by_OpenAI モジュール総数と script_{*} モジュール数を比較
  3. polar 判定されなかった hearing があれば理由を報告（force_openai 設定の候補か確認）
```

---

### DET-B: N 択 hearing に choices[] を宣言して n_choice 化する

> **設計書作成ルール（director 必須）**: polar 以外の enum hearing は `choices:` の宣言が**必須**。
> 書かない場合は決定論化されず OpenAI のままになる（書き忘れは `force_openai: true` と異なり意図が不明）。
> OpenAI を意図的に維持する場合のみ `force_openai: true` を明示すること。

```
以下の設計書の enum hearing に choices[] を追加して n_choice 化してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
対象 step: {step 名（例: コース選択）}

choices[] の書き方:
  choices:
    - label: {ラベル名（例: Aコース）}          # conditions の match と完全一致が必須
      dtmf: "{DTMF 番号（例: \"1\"）}"         # 省略可
      strong_keywords: [{先に評価するキーワード}] # COMPOUND（STRONG 扱い）、省略可
      keywords: [{通常キーワード}]               # KEYWORD（WEAK 扱い）
    - label: {ラベル名2}
      dtmf: "{DTMF 番号2}"
      keywords: [{キーワード}]

注意:
  - choices[].label は conditions[].match と完全一致（不一致 → E-19 CRITICAL）
  - output_format: enum を必ず設定すること
  - other 条件は conditions に残してよい（choices には不要）

追加後に qa_validator.py で E-19 チェックをパスするか確認してください:
python schemas/qa_validator.py output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

CRITICAL = 0 になったら scaffold を再生成して script_{step} モジュールの
n_choice spec（DTMF_MAP / COMPOUND_PATTERNS / KEYWORD_PATTERNS）を確認してください。
```

---

### DET-C: force_openai: true で OpenAI を明示的に維持する（移行期の逃げ道）

```
以下の hearing は決定論化せず OpenAI を維持してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml
対象 step: {step 名}
理由: {例: 自由発話が多く keywords では網羅できない / 社内レビュー待ち 等}

設計書の該当ブロックに force_openai: true を追加してください:
  - step: {step 名}
    type: hearing
    output_format: enum
    force_openai: true   ← これを追加
    ...

force_openai: true が設定された hearing は scaffold が OpenAI を維持します。
設定後に scaffold を再生成して generate_by_OpenAI_{step} モジュールが
存在するか確認してください。

注: force_openai は移行期の逃げ道です。
keywords で網羅できるようになったら choices[] + force_openai 削除に移行してください。
```

---

### DET-D: n_choice spec を確認して oracle 受入を行う

```
scaffold が生成した n_choice spec を確認して oracle 受入を行ってください。

対象 JSON: output/json/scaffold_{施設名}_{フロー名}.json
対象モジュール: script_{step}（n_choice を使うもの）

手順:
1. JSON から script_{step} の params.script を確認する
   - DTMF_MAP, TOKEN_MAP, COMPOUND_PATTERNS, KEYWORD_PATTERNS が定義されているか
   - choices[] の label / keywords / strong_keywords が正しく反映されているか

2. oracle_gate.py で新規 spec として検出されることを確認する:
   python tools/oracle_gate.py --json output/json/scaffold_{施設名}_{フロー名}.json

3. 「受入要求」と出たモジュールは:
   a. python modules/n_choice/test_oracle.py を実行（全 PASS 確認）
   b. Brekeke 実機 Pattern 6 テスト（人間が実施）
   c. 実機 PASS 後に P6-C プロンプトで modules/certified_hashes.json を更新

注:
  - yes_no_classifier は spec 内蔵・認定済みのため追加受入不要
  - choices[] の内容が 1 文字でも変わると「新規 spec」として再受入が必要
    （part-certification-spec.md「1 文字でも改変したら再受入」ルール）
```

---

## YAML-FIX — 設計書自動修正（yaml_auto_fixer.py）

> **概要**: `qa_validator.py` の出力から `fix_category="auto"` の Issue を
> 正規表現置換で自動修正する。LLM 不使用。
> Phase 1 対応: T-3（conditions ラベル補完）/ T-4（output_format 補完）/ L-5（next 補完）/ E-8（termination status 型修正）

### YAML-FIX-A: yaml_auto_fixer で auto 修正可能な Issue を修正する

```
以下の設計書を yaml_auto_fixer で自動修正してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

手順:
1. qa_validator.py を JSON レポートモードで実行:
   python schemas/qa_validator.py --json-report \
       output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml \
       > /tmp/qa_report.json

2. yaml_auto_fixer.py を実行:
   python schemas/yaml_auto_fixer.py \
       --report /tmp/qa_report.json \
       --yaml output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

3. qa_validator.py を再実行して残存 CRITICAL を確認する:
   python schemas/qa_validator.py \
       output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

自動修正の対象（fix_category="auto"）:
  - T-3: conditions の match ラベル不足（other 補完等）
  - T-4: output_format 未設定（enum 補完等）
  - L-5: next 参照先の補完
  - E-8: termination status の型修正（文字列 → 数値）

自動修正できない CRITICAL が残った場合は YAML-FIX-B で差し戻し票を作成してください。
```

---

### YAML-FIX-B: 残存 CRITICAL を分析して壁打ちへの差し戻し票を出す

```
qa_validator.py の残存 CRITICAL を分析して壁打ちへの差し戻し票を作成してください。

設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

手順:
1. yaml_auto_fixer 適用後の qa_validator.py を実行:
   python schemas/qa_validator.py output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

2. 残存 CRITICAL を一覧化する

3. 各 CRITICAL について分析:
   - check code（例: E-17(a), F-8, E-19, F-9）
   - 問題のある step 名
   - 修正に必要な情報（例: type を clinical_department_classifier に変更 / choices[] の追加）
   - 設計書の変更内容（どのフィールドをどう変えるか）

差し戻し票フォーマット:
  ## 差し戻し票: {施設名}_{フロー名}
  - 差し戻し元: qa_validator.py（yaml_auto_fixer 適用後）
  - 設計書: {パス}
  - 残存 CRITICAL: {件数} 件

  | # | check code | step | 問題 | 修正内容 |
  |---|---|---|---|---|
  | 1 | {code} | {step} | {問題} | {修正内容} |

  ## 主なチェックコードの修正方法
  - E-17(a): 診療科聴取 → `type: clinical_department_classifier` に変更
  - E-17(b): 用件判定 → `type: intent` に変更
  - E-19: choices[] ラベルと conditions ラベルを一致させる（BLK-I 参照）
  - F-8: faq_items → scenario_flow に `type: faq` ブロックを追加
  - F-9: phone/name/DOB hearing → `type: slot` または専用スロット型に変更

出力先: output/scenarios/{施設名}_{フロー名}/qa_diff_report_{施設名}_{フロー名}.md

※ director の自律リトライは廃止（2026-06-19〜）。
  残存 CRITICAL は人間（壁打ち）で設計書を直してパイプラインを再実行してください。
```

---

## BLK — 新規ブロック型リファレンス（2026-07-13 更新）

> scaffold_generator が対応する全ブロック型と YAML 記法。
> 設計書を書く際のコピー元として使う。

### ブロック型一覧

| type | 概要 | 生成されるエントリモジュール |
|---|---|---|
| `opening` | 冒頭 + 着信分類 + 受付時間判定 | 冒頭 |
| `announcement` | 一方向アナウンス（STT なし） | `{step}` |
| `hearing` | 音声聴取 + OpenAI 分類（または決定論スクリプト） | `{step}` |
| `subflow` | Jump to Flow | `{step}` |
| `context_match_router` | CMR 分岐 | `{step}` |
| `script` | Script 単体 | `{step}` |
| ~~`date_of_call_classifier`~~ | ~~発信日付分類~~（**廃止** 2026-07-13: Brekeke モジュール削除済み。使用不可・qa_validator F-3 CRITICAL） | — |
| `call_transfer` | 転送 | `{step}` |
| `termination` | 終話チェーン | `完了フラグ_{short}` |
| `slot` | 個人情報スロット（汎用） | slot 種別による |
| `dob` | 生年月日（slot: date_of_birth エイリアス） | `{step}` |
| `phone` | 電話番号（slot: phone エイリアス） | `着信分類_{step}` |
| `patient_name` | 氏名（slot: patient_name エイリアス） | `{step}` |
| `intent` | 用件判定 ES5 スクリプト | `{step}` |
| `phone_branch` | 電話種別分岐（MRB） | `{step}` |
| `clinical_department` | 診療科スクリプト正規化 | `{step}` |
| `clinical_department_normalize` | 診療科正規化のみ（STT なし） | `script_{step}` |
| `free_text` | 自由発話収集 | `{step}` |
| `faq` | FAQ 照合 | `{step}` |
| `card_number` | 診察券番号 ES5 正規化 | `{step}` |

---

### BLK-A: `intent` — 用件判定スクリプト

```yaml
- type: intent
  step: 用件
  save_to: classification
  options:
    - number: 1
      label: 予約
      strong: true
      keywords: ["予約", "よやく", "とりたい", "入れたい", "とって"]
    - number: 2
      label: 変更
      strong: false
      keywords: ["変更", "へんこう", "変えたい", "ずらし", "ずらしたい"]
    - number: 3
      label: キャンセル
      strong: false
      keywords: ["キャンセル", "とりけし", "やめ", "やめたい"]
  next: {次のステップ}
  retry_count: 2
```

**setResult の値**: `options[].label` の値 または `"NO_RESULT"`

---

### BLK-B: `phone_branch` — 電話種別分岐

Module Result Binder (Mode B) でコンテキスト変数を直接読んで分岐。Scripts 不要。

```yaml
- type: phone_branch
  step: 電話種別分岐
  source_context: additionalPhoneNumber
  conditions:
    - match: "^(090|080|070)"
      label: 携帯
      next: {携帯の次のステップ}
    - match: "^050"
      label: IP電話
      next: {IP電話の次のステップ}
  default_next: {固定電話の次のステップ}
```

---

### BLK-C: `clinical_department` — 診療科スクリプト正規化

kamei_normalize.js（ES5）を自動生成。departments リストから正規化辞書を構築。

```yaml
- type: clinical_department
  step: 診療科
  save_to: clinicalDepartment
  departments:
    - canonical: 内科
      aliases: ["ないか", "内科", "一般内科", "総合内科"]
    - canonical: 外科
      aliases: ["げか", "外科", "一般外科"]
    - canonical: 整形外科
      aliases: ["せいけい", "整形", "整形外科", "骨"]
    - canonical: 小児科
      aliases: ["しょうに", "小児科", "こども", "子供"]
  next: {次のステップ}
  retry_count: 2
```

**setResult の値**: `departments[].canonical` の値 または `"NO_RESULT"`

---

### BLK-D: `clinical_department_normalize` — 診療科正規化のみ（STT なし）

他モジュールの STT 結果を受け取って正規化するだけ。TTS / 復唱なし。

```yaml
- type: clinical_department_normalize
  step: 診療科正規化
  source_module: 入力_診療科
  departments:
    - canonical: 内科
      aliases: ["ないか", "内科"]
    - canonical: 外科
      aliases: ["げか", "外科"]
  next: {次のステップ}
```

---

### BLK-E: `free_text` — 自由発話収集

分類不要。発話内容をそのまま context に保存。

```yaml
- type: free_text
  step: 症状メモ
  save_to: symptomMemo
  next: {次のステップ}
  retry_count: 2
```

---

### BLK-F: `faq` — FAQ 照合

**method: script**（デフォルト）: prompter が照合ロジックを Script に記述。
**method: openai**: OpenAI が FAQ リストと照合。

```yaml
- type: faq
  step: FAQ照合
  method: script
  conditions:
    - match: ANSWER
      next: {回答アナウンスのステップ}
    - match: NO_RESULT
      next: {リトライのステップ}
  retry_count: 2
```

---

### BLK-G: `card_number` — 診察券番号 ES5 正規化

全角→半角・漢数字・ひらがな読みを正規化。8桁は `XXXX-XXXX` 形式で `yomiage_cardnumber` を生成。

```yaml
- type: card_number
  step: 診察券番号
  save_to: medicalCardNumber
  echo_back: false        # true → 復唱確認チェーンを生成
  next_found: {番号取得時の次のステップ}
  next_unknown: {不明・初診時の次のステップ}
  retry_count: 2
```

**setResult の値**:
- 正規化済み数字列（番号が取得できた）
- `"不明か未所持"`（わからない / 持っていない / 初診）
- `"NO_RESULT"`（認識失敗 / バリデーション不通過）

**復唱 TTS**（`echo_back: true` 時）:
```
{tts_g:診察券番号は、<%yomiage_cardnumber%>、でよろしいでしょうか}
```

---

### BLK-H: `slot: phone` — SMS 送信用電話番号の設定パターン

SMS を送信するには `additionalPhoneNumber`（連絡先番号）と `phonetype`（携帯/その他）の 2 コンテキストが必要。

#### Case 1: SMS が必要だが電話番号を聴取しない分岐

着信番号（ANI）をそのまま `additionalPhoneNumber` に保存する。
`announcement` ブロックの `save_to + save_value` を使う。

```yaml
- type: announcement
  step: ANI番号設定
  save_to: additionalPhoneNumber
  save_value: "<% sys-customer-phone-number %>"
  next: {次のステップ}
```

> `phonetype` は別途 `context_match_router` などで `携帯` に固定すること。

#### Case 2: `slot: phone` で「なし / ありません」回答に対応する

電話番号聴取ブロックに `next_no_phone` を指定すると、
Phone Normalization の失敗分岐に **Module Result Binder（Mode A）** が自動挿入される。

- AmiVoice 生テキストを読み、`_NASHI_PATTERN`（ない/なし/無し/ありません/持っていない/もっていない/わかりません/ございません/持ち合わせ）に一致 → `next_no_phone` へ遷移
- catch-all（上記に非該当）→ 連絡先聴取 TTS へ戻る（通常リトライ継続）

```yaml
- type: slot
  slot: phone
  step: 電話番号
  save_to: additionalPhoneNumber
  next_no_phone: {電話番号なし時の次のステップ}   # ← これを追加
  next: {取得完了後の次のステップ}
```

生成されるモジュール名: `script_{step}_連絡先なし判定`

---

### BLK-I: `hearing` with `choices[]` — N 択決定論化（n_choice）

`choices[]` を宣言すると scaffold が n_choice スクリプトを自動生成（OpenAI 不要）。

```yaml
- step: コース選択
  type: hearing
  output_format: enum
  save_to: courseType
  choices:
    - label: Aコース                              # conditions の match と完全一致必須
      dtmf: "1"                                  # DTMF 番号（省略可）
      strong_keywords: [一般健診のコース, Aコースで予約]  # COMPOUND（先に評価 = STRONG）
      keywords: [Aコース, エーコース, 一般健診]          # KEYWORD（後で評価 = WEAK）
    - label: Bコース
      dtmf: "2"
      keywords: [Bコース, ビーコース, 特定健診]
  conditions:
    - match: Aコース
      next: {次のステップ}
    - match: Bコース
      next: {次のステップ}
    - match: other
      next: {その他の次のステップ}
  retry_count: 2
```

**注意事項**:
- `choices[].label` は `conditions[].match` と完全一致（不一致 → E-19 CRITICAL）
- `strong_keywords` → COMPOUND_PATTERNS（先に評価 = STRONG）
- `keywords` → KEYWORD_PATTERNS（後で評価 = WEAK）
- `dtmf` は省略可（音声のみの場合）
- scaffold が n_choice spec（DTMF_MAP / TOKEN_MAP / COMPOUND_PATTERNS / KEYWORD_PATTERNS）を自動生成
- **n_choice spec は新規 spec 扱い** → oracle_gate / P6 実機受入が必要（DET-D 参照）

---

### BLK-J: `hearing` with polar labels — 2 択決定論化（yes_no_classifier）

`choices[]` 宣言不要。conditions ラベルが polar 語彙なら scaffold が自動で yes_no_classifier を使用。

```yaml
- step: 紹介状確認
  type: hearing
  output_format: enum
  save_to: hasReferral
  conditions:
    - match: はい
      next: {次のステップ}
    - match: いいえ
      next: {次のステップ}
  retry_count: 2
```

**polar 語彙一覧**（片方だけでも含まれていれば自動 polar 判定）:

| 肯定（affirm） | 否定（deny） |
|---|---|
| はい / あり / 持っている / もっている | いいえ / なし / 持っていない / もっていない |
| 該当 / 対象 / 受けた / 済み | 非該当 / 対象外 / 受けていない / 未 |
| する / します / ある / あります | しない / しません / ない / ありません |
| はっきり / 確かに / そうです | 違う / ちがう / 違います |

**注意事項**:
- `choices[]` 不要（polar は自動判定）
- `force_openai: true` で無効化可能（DET-C 参照）
- yes_no_classifier は認定済みのため追加受入不要
- echo_back: true の復唱確認も自動で yes_no_classifier を使用（設定不要）

---

## 時間外終話チェーン仕様（2026-07-09 変更）

> 時間外のアナウンス TTS は `acceptance_times` モジュール内で再生されるため、
> 終話チェーンに TTS を生成しない。

### 生成されるチェーン

```
完了フラグ_時間外（saveCompletionFlag, status=6）
  → 切断_時間外（disconnect）
```

### 設計書の書き方

```yaml
termination_patterns:
  - name: END_時間外
    condition: 時間外
    completion_flag_name: 完了フラグ_時間外
    status: "6"
    # tts_announcement は設定不要（acceptance_times が再生）
```

`qa_validator.py` の E-7 チェック（時間外 TTS 未定義 → CRITICAL）は **廃止（2026-07-09）** 済み。

---

## 補足: よくある追加指示パターン

### PR 作成を依頼する場合

```
変更内容を feature ブランチにコミットして PR を作成してください。

ブランチ名: feature/{変更内容の説明}
PR タイトル: {日本語で変更概要}
レビュアー: @TS-dong-nc

コミットメッセージ: {例: "feat: keyword_presets に jibun_futan プリセットを追加"}
```

---

### 複数施設への一括反映を依頼する場合

```
以下の変更を複数施設の設計書に一括反映してください。

変更内容: {例: Scripts_個人法人 の keywords に「弊社」を追加}
対象施設:
  - output/scenarios/{施設1}_{フロー1}/設計書_{施設1}_{フロー1}.yaml
  - output/scenarios/{施設2}_{フロー2}/設計書_{施設2}_{フロー2}.yaml

各施設で gen_scripts.py を再実行して ES5 を更新してください。
```

---

### 施設全体のパイプラインを最初から再実行する場合

```
以下のシナリオのパイプラインを最初から再実行してください。

施設名: {施設名}
フロー名: {フロー名}
設計書: output/scenarios/{施設名}_{フロー名}/設計書_{施設名}_{フロー名}.yaml

実行順序:
1. qa_validator.py で設計書を検証 → CRITICAL があれば yaml_auto_fixer で auto 修正
   残存 CRITICAL は差し戻し票（YAML-FIX-B）を出して halt
2. copy_subflows.py でサブフローをコピー
3. scaffold_generator.py で scaffold JSON を生成
   （polar/choices hearing は自動で yes_no_classifier/n_choice に置換）
4. prompter + gen_properties.py を並列実行
   （希望日 hearing は scaffold が固定プロンプト済みのため prompter スキップ）
5. validator.py → auto_fixer.py → validator.py 再実行
6. tester.py で構造監査
7. oracle_gate.py で部品ハッシュ検証
   （n_choice 新規 spec は DET-D の受入手順へ）
8. gen_p7_cases.py でテストケース生成
9. stub_stt_connection.py で STT スタブ bivr を生成

各ステップの結果を報告しながら進めてください。
CRITICAL が残った場合は自律修復せずに差し戻しレポートを出力して halt してください。
```

---

*最終更新: 2026-07-13 | 管理: @TS-dong-nc | レビュー: @TS-hamaguchi-t*
