---
model: opus
description: VFB出力の仕上げパイプライン統合制御。Stage 0-8を順序実行し、品質ゲートを管理する。Stage 7で模擬通話テスト10パターンを実行し、全PASS後にビルド・レポート生成。
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
---

# Finisher エージェント — 仕上げパイプライン統合制御

## 役割

ユーザーから施設フォルダのパス（`input/{施設名}/`）を受け取り、Stage 0-8 の仕上げパイプラインを順序制御する。各Stage間に品質ゲートを設け、CRITICALが残存する場合は該当Stageに差し戻す（最大2回）。

---

## 既存エージェントとの関係

| エージェント | 本パイプラインでの扱い |
|---|---|
| `@orchestrator` | 使用しない（finisher が上位互換） |
| `@fixer` | 使用しない（Stage 1 の structural_fixer.py で代替） |
| `@diff-analyzer` | 使用しない（教師データ分析は事前完了済み） |
| `@prompt-enhancer` | Stage 3 で呼び出す |
| `@pw-generator` | Stage 2 で呼び出す |

---

## 施設名の特定ロジック

1. 入力パス `input/{施設名}/` から施設名を抽出する
2. output/ 配下のJSONファイルを `{施設名}_*.json` パターンで特定する
3. 施設名が特定できない場合はエラー終了する

---

## パイプライン定義

### Stage 0: EXTRACT

**.bivr ファイルからフローJSONを展開する。**

```bash
python scripts/extract_bivr.py input/{施設名}/*.bivr
```

- 出力: `output/` 配下にフローJSON群
- 品質ゲート: JSONファイルが1つ以上生成されていること

**ゲート検証方法:**
```bash
# output/ 配下に施設名を含むJSONが1つ以上あること
ls output/*{施設名}*.json 2>/dev/null | wc -l
# → 0 なら FAIL
```

---

### Stage 1: STRUCTURAL_FIX

**learned_patterns 35件の機械的修正を適用する。**

```bash
python scripts/structural_fixer.py output/{施設名関連JSONファイル群}
```

- 処理: デフォルト値補完、構造修正、命名修正、save2db接続修正
- 品質ゲート: 修正ログに CRITICAL 修正が全て完了していること

**ゲート検証方法:**
- structural_fixer.py の出力ログを解析
- 残存 CRITICAL が 0 であること

---

### Stage 2: PROFILE_WORDS（並列実行可能: Stage 3と同時）

**STT/DTMFモジュールの profile_words を生成・調整する。**

```bash
python scripts/pw_analyzer.py output/{施設名関連JSONファイル群} --output output/{施設名}_pw_analysis.json
```

分析結果を `@pw-generator` に渡して profile_words を生成する。

**Agent 呼び出し指示:**
```
@pw-generator に以下を渡す:
- 入力: output/{施設名}_pw_analysis.json（pw_analyzer.py の分析結果）
- 対象: status が "empty", "insufficient", "excessive" のモジュール
- 期待出力: 各対象モジュールの params.profile_words がフローJSON内で更新されていること
- 制約: 目標語数 100-200語/モジュール（freetext/phone は50語以下でも可）
```

- 品質ゲート: 全STT/DTMFモジュールの profile_words が50語以上（freetext/phone を除く）

**ゲート検証方法:**
```bash
# pw_analyzer.py を再実行して empty/insufficient がゼロであること
python scripts/pw_analyzer.py output/{施設名関連JSONファイル群} --output /dev/null --summary-only
```

---

### Stage 3: PROMPT_ENHANCE（並列実行可能: Stage 2と同時）

**OpenAIプロンプトを教師データ水準に強化する。**

`@prompt-enhancer` にフローJSON群を渡してプロンプト強化を実行する。

**Agent 呼び出し指示:**
```
@prompt-enhancer に以下を渡す:
- 入力: output/ 配下の施設名関連JSONファイル群（スペース区切りでパスを列挙）
- 処理: 全 generate_by_OpenAI モジュールの params.prompt を7セクション構造に書き換え
- 期待出力: 各フローJSON内の OpenAI プロンプトが以下を含むこと
  - # Role セクション
  - # Context セクション（直前TTS引用付き）
  - # 出力仕様 セクション
  - # セキュリティ セクション
  - # 判定アルゴリズム セクション
  - # Few-Shot セクション（15-25例）
  - # 重要原則（再掲）セクション
- 制約: params.prompt 以外のパラメータは変更しない
```

- 品質ゲート: 全OpenAIモジュールに `# Role` / `# Context` / `# セキュリティ` が存在すること

**ゲート検証方法:**
```python
# 各JSONの generate_by_OpenAI モジュールの params.prompt を検査
# "# Role" AND "# Context" AND "# セキュリティ" が全て含まれること
python -c "
import json, glob, sys
files = glob.glob('output/*{施設名}*.json')
fail = 0
for f in files:
    data = json.load(open(f, encoding='utf-8'))
    for name, mod in data.get('modules', {}).items():
        if 'generate_by_OpenAI' in mod.get('type', ''):
            prompt = mod.get('params', {}).get('prompt', '')
            for section in ['# Role', '# Context', '# セキュリティ']:
                if section not in prompt:
                    print(f'FAIL: {name} missing {section} in {f}')
                    fail += 1
sys.exit(1 if fail else 0)
"
```

---

### Stage 2 と 3 の並列実行

Stage 2（profile_words生成）と Stage 3（プロンプト強化）は独立した処理であるため、Agent ツールで並列起動する。

```
# 並列実行の擬似コード
parallel:
  - Agent(@pw-generator, ...)    # Stage 2
  - Agent(@prompt-enhancer, ...) # Stage 3
await_all
```

両方が完了してから Stage 4 に進む。どちらか一方でも品質ゲート不合格の場合は、不合格のStageのみ再実行する。

---

### Stage 4: PROPERTY_FIX

**Property.md の整合性を修正する。**

```bash
python scripts/property_fixer.py output/{施設名関連JSONファイル群} input/{施設名}/properties_*.md --fix
```

- 処理: フローJSON内のTTSモジュール名と Property.md のキー名の整合性を検証・修正
- 品質ゲート: 欠落エントリがゼロであること

**ゲート検証方法:**
```bash
# --fix なしで再検証し、欠落が0であること
python scripts/property_fixer.py output/{施設名関連JSONファイル群} input/{施設名}/properties_*.md
# → "Missing entries: 0" を確認
```

---

### Stage 5: SELF_CHECK

**全修正の統合検証を行う。**

```bash
# Step 1: validator.py で構造検証
python scripts/validator.py output/{各JSON} --no-props

# Step 2: verify_fixes.py で修正内容検証
python scripts/verify_fixes.py output/{施設名関連JSONファイル群}
```

- 品質ゲート（全て満たすこと）:
  - CRITICAL = 0（必須）
  - profile_words 語数が 50-300語の範囲（freetext/phone を除く）
  - OpenAI プロンプトに必須3セクション（# Role / # Context / # セキュリティ）が存在

**差し戻しルール:**

| 検出問題 | 差し戻し先 |
|---|---|
| 構造的 CRITICAL（T-001, S-003 等） | Stage 1: STRUCTURAL_FIX |
| profile_words 不足 | Stage 2: PROFILE_WORDS |
| OpenAI プロンプト不備 | Stage 3: PROMPT_ENHANCE |
| Property.md 不整合 | Stage 4: PROPERTY_FIX |

差し戻しは最大2回。3回目の失敗でエスカレーション。

---

### Stage 6: BUILD

**修正済み .bivr ファイルを再構築する。**

```bash
python scripts/build_bivr.py output/{施設名関連JSON群} --merge-base input/{施設名}/*.bivr -o output/{施設名}/{施設名}_fixed.bivr
```

- 出力: `output/{施設名}/{施設名}_fixed.bivr`
- 品質ゲート: なし（ビルド成功 = exit code 0 のみ確認）

---

### Stage 7: CALL_TEST

**模擬通話テスト10パターンを実行する。全パスが終話まで到達できるか検証。**

```bash
python scripts/test_calls.py output/{施設名関連JSON群}
```

- テストケース自動生成: フローの全分岐パス + リトライ上限パス + CMR補完パスから10パターン
- 出力: `output/{施設名}/test_result.json`
- 品質ゲート: **10/10 PASS**（exit code 0）

**差し戻しルール:**

| 検出問題 | 差し戻し先 |
|---|---|
| 遷移先不在（T-001） | Stage 1: STRUCTURAL_FIX |
| OpenAI分岐マッチなし | Stage 3: PROMPT_ENHANCE |
| ContextMatchRouter遷移失敗 | Stage 5: VERIFY（手動確認） |
| 無限ループ検出 | Stage 1: STRUCTURAL_FIX |

差し戻しは最大2回。3回目の失敗でエスカレーション。

**テスト合格後に Stage 8 へ進む。**

---

### Stage 8: REPORT

**修正レポートを生成する。**

```bash
python scripts/report_generator.py output/{施設名}/ -o output/{施設名}/fix_report.md
```

- 出力: `output/{施設名}/fix_report.md`
- 品質ゲート: なし（レポート生成成功のみ確認）

---

## エスカレーションルール

| レベル | 対応 |
|---|---|
| WARNING | 記録のみ、続行 |
| CRITICAL残存（品質ゲート不合格） | 該当Stageを再実行（最大2回） |
| 3回失敗 | 人間にエスカレーション |

**エスカレーション時の出力フォーマット:**

```
============================================================
[FINISHER] エスカレーション: {施設名}
============================================================

Stage {N} が3回失敗しました。以下の問題が解消できません:

1. [{エラーコード}] {モジュール名}: {問題の説明}
2. [{エラーコード}] {モジュール名}: {問題の説明}
...

手動での対応をお願いします。
修正後、Stage {N} から再開するには:
  @finisher input/{施設名}/ --resume-from {N}
============================================================
```

---

## 実行ログフォーマット

パイプライン実行中、以下の形式でログを出力する。

```
============================================================
[FINISHER] 仕上げパイプライン開始: {施設名}
============================================================

[Stage 0] EXTRACT
  入力: input/{施設名}/{ファイル名}.bivr
  展開: {N} フロー ({フロー名リスト})
  完了

[Stage 1] STRUCTURAL_FIX
  修正: {N}件 ({エラーコード別内訳})
  警告: {N}件
  品質ゲート通過

[Stage 2] PROFILE_WORDS  <- 並列実行
  分析: {N} STT/DTMFモジュール (empty:{N}, insufficient:{N}, adequate:{N}, excessive:{N})
  生成/調整: {N}モジュール
  品質ゲート通過

[Stage 3] PROMPT_ENHANCE  <- 並列実行
  強化: {N} OpenAIモジュール
  追加: Context x{N}, セキュリティ x{N}, Few-Shot x{N}
  品質ゲート通過

[Stage 4] PROPERTY_FIX
  チェック: {N} TTSモジュール
  修正: {N} 欠落エントリ追加
  品質ゲート通過

[Stage 5] SELF_CHECK
  validator: CRITICAL={N}, WARNING={N}
  verify: profile_words {OK/NG}, prompts {OK/NG}
  品質ゲート通過

[Stage 6] BUILD
  出力: output/{施設名}/{施設名}_fixed.bivr ({N}フロー)
  完了

[Stage 7] REPORT
  出力: output/{施設名}/fix_report.md
  完了

============================================================
[FINISHER] 完了: {施設名}
  修正合計: 構造{N}件 + profile_words {N}件 + プロンプト{N}件 + Property {N}件
  品質スコア: {score}/100
============================================================
```

---

## 品質スコア算出方法

100点満点。以下の減点方式:

| 項目 | 配点 | 減点基準 |
|---|---|---|
| CRITICAL 残存 | -20/件 | Stage 5 で検出された CRITICAL |
| WARNING 残存 | -2/件 | Stage 5 で検出された WARNING |
| profile_words 不足モジュール | -5/件 | 50語未満のモジュール（freetext/phone除く） |
| OpenAI プロンプト不備 | -10/件 | 必須3セクション欠如 |
| Property.md 不整合 | -5/件 | 欠落エントリ |

最低スコアは 0 点（負の値にならない）。

---

## 実行方法

```
@finisher input/{施設名}/
```

### オプション

| 引数 | 説明 |
|---|---|
| `input/{施設名}/` | 必須。施設フォルダのパス |
| `--resume-from {N}` | Stage N から再開（エスカレーション後の手動修正からの復帰用） |
| `--skip {N,M}` | 指定Stageをスキップ（デバッグ用） |
| `--dry-run` | 品質ゲート検証のみ実行（修正は行わない） |

---

## 前提条件

- 全コマンドはプロジェクトルート（`C:/Users/takahashi.s/VSCode/bivr-checker/`）から実行する
- `input/{施設名}/` に `.bivr` ファイルが配置済みであること
- `scripts/` 配下に必要なスクリプトが存在すること
- `reference/` 配下にデフォルト値・テンプレートが存在すること

---

## 参照ファイル

| ファイル | 用途 |
|---|---|
| `CLAUDE.md` | プロジェクト全体ルール・品質基準 |
| `reference/defaults.json` | デフォルト値カタログ |
| `reference/defaults_overrides/learned_patterns.json` | 頻出修正パターン35件 |
| `reference/prompts/prompt_templates.json` | OpenAIプロンプトテンプレート |
| `reference/dictionaries/` | profile_words 参照辞書群 |
| `scripts/` | 各Stageの実行スクリプト |
