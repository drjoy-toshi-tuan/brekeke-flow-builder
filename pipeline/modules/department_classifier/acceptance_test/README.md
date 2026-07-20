# Department Classifier 受入テストシナリオフロー（Pattern 6 単体）

Python オラクル `../test_oracle.py` と **完全に同一の 89 ケース** を、Pattern 6 の汎用
`script_test_matrix` で **1 コール内に直列実行** する Brekeke flow。各ケースは
`<id>_in`（入力注入）→ `<id>_clf`（**正本 `../script.js` をそのまま読込**、入力参照名
`入力_診療科` を `<id>_in` に置換）→ `<id>_cmr`（出力 == 期待値で分岐）→ `<id>_pass`/`<id>_fail`（ログ）。

OpenAI/STT は一切呼ばない（入力は inline_script で直接注入）。検証対象ロジックは 1 文字も変えていない。

## 同梱物

| ファイル | 役割 |
|---|---|
| `テスト_診療科分類_20260609.bivr` | Brekeke にインポートする flow（**450 modules** = dispatch 1 + 89×5 + frame 4）|
| `設計書_テスト_診療科分類.yaml` | 上記 bivr の生成元（`script_file: ../script.js` を sidecar 読込、89 ケースを内包）|
| `README.md` | このファイル |

## カバーする 89 ケース（= oracle CASES と 1:1）

| prefix | 件数 | 内容 |
|---|---|---|
| `can01-30` | 30 | 公式30科 canonical の恒等（中黒は正規化で除去→中黒なしキーで一致）|
| `pw01-06`  | 6  | profile_words の中黒なし表記 → 公式 canonical（中黒付き）|
| `inc01-13` | 13 | 包含関係（小児科 ⊂ 小児外科 等）を最長一致で裁定 |
| `skn01-04` | 4  | **皮膚科**（OpenAI が精神神経科へ誤分類していた問題の根治。語尾/敬称付き含む）|
| `ym01-11`  | 11 | 読み（ひらがな）からの分類 |
| `al01-08`  | 8  | 別名/口語（精神科→精神神経科, がん/ケモ→放射線治療科 等）|
| `fz01-03`  | 3  | 全角空白/かぎ括弧/敬称フィラー混じり |
| `wk01-07`  | 7  | 「わからない」不明意図 → **登録なし**（スキップ・再質問しない）|
| `nr01-07`  | 7  | **NO_RESULT**（空/数字のみ/フィラー/無関係発話 → 再質問）|

## 実行手順

### Brekeke 投入
1. `テスト_診療科分類_20260609.bivr` を Brekeke 管理画面で flow としてインポート（フロー `テスト$診療科分類`）。
   - `テスト$Soniox診療`(40) はビルド時の既知の無害な同梱（実害なし）。
2. テスト発信用の番号 or「フロー実行」で **1 コールだけ** 実行（発話・DTMF 不要。冒頭 wait 2 秒後、89 ケースが自動走行して切断）。
3. Brekeke ログ画面で結果を観察。

### ログから結果判定
- **`[TEST FAIL]` の件数が 0 なら全 89 ケース PASS。**
- 末尾に **`[TEST DONE] 診療科 決定論分類 単体受入テスト 89 ケース 完走`** が出れば完走。
- 各 PASS 行: `[TEST PASS] <id> in=<入力> exp=<期待>` / FAIL 行: `[TEST FAIL] <id> in=<入力> exp=<期待> got=<clf実出力>`
- 中間に `[SCRIPT-DEPT] raw=… norm=… out=…`（分類器本体ログ）と `ContextMatchRouter: Matched at index 1`（PASS）/ `index 0`（FAIL）も出る。

```
grep -c "\[TEST FAIL\]" call.log     # → 0 を確認
grep "\[TEST DONE\]"   call.log      # → 1 行出れば完走
```

## 実機結果

**89/89 PASS（2026-06-09 16:55、call 6440 / Thread-5351）**。`[TEST FAIL]` 0 件・`[TEST DONE]` 到達。
皮膚科=皮膚科（`raw=皮膚科 … out=皮膚科`、精神神経科誤分類 0）・中黒 canonical 厳密一致・
空入力（`raw= norm= out=NO_RESULT`）・わからない→登録なし、全て実機確認。Nashorn↔Python パリティ全89一致。

## 既知の制約

- Brekeke 1 コール 1000 モジュール上限（[[feedback_brekeke_max_module_execution_1000]]）内（450 modules）。89 ケースを超えて分割が要る場合は YAML の `cases` を分けて複数 bivr 化する。
- 本テストは `../script.js` の現行ロジック前提。`script.js` を修正したら下記で再生成すること。

## bivr 再生成（`../script.js` 修正時）

```
python scripts/orchestrator.py --pattern 6 --spec modules/department_classifier/acceptance_test/設計書_テスト_診療科分類.yaml
# → output/scenarios/テスト_診療科分類/ に bivr 生成 → この acceptance_test/ にコピーして差し替え
```

汎用 `script_test_matrix`（`scripts/test_scaffold_generator.py`）が `../script.js` をそのまま読み、
`入力_診療科` を case ごとの `<id>_in` に置換して展開する。モジュール個別の build スクリプトは不要。
