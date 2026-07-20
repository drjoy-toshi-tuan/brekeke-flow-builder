# field_presence 受入テストフロー（Pattern 6 単体）

Python オラクル `../test_oracle.py`（33/33 PASS）と同一ケース（name 以外の **32**）を、汎用 `script_test_matrix`
で 1 コール内に直列実行する Brekeke flow。KIND が config（production では 6 インスタンスが各 KIND 固定）の
ため、正本テンプレ `../../../docs/brekeke/script_templates/field_presence.js` を **kind ごとにコピーして
`var KIND` のみ解決**した `script_<kind>.js` を 5 つの matrix が読み込む（KIND 以外は 1 文字も変えない）。
各ケース `<id>_in`（入力注入）→ `<id>_clf`（`{{INPUT_MODULE}}`→`<id>_in` 置換）→ `<id>_cmr`（出力==期待値）。

※ name は production の KIND ではない（氏名は L1 省略・FAQ のみ）ため P6 対象外。
※ テンプレの `{{CONTEXT_FIELD}}` は未解決でも context 無し → getModuleResult フォールバックで動く。

## 同梱物
| ファイル | 役割 |
|---|---|
| `テスト_field_presence_20260617.bivr` | Brekeke にインポートする flow（zip・169 modules = 32×5 + matrix 5 + frame 4）|
| `設計書_テスト_field_presence.yaml` | 生成元（5 KIND の script_test_matrix を連鎖、32 ケース内包）|
| `script_{department,date,phone,birthday,card}.js` | テンプレ正本を KIND 解決したコピー（matrix が読込）|

## カバーする 32 ケース（5 KIND・= oracle CASES の name 以外）
- department 7 / date 8 / phone 5 / birthday 5 / card 7（card は「持っていない/ありません」等 no-card 表明も PRESENT）
- 各 KIND に「答え+雑音質問の混在→PRESENT（答え優先）」「質問だけ→ABSENT」を含む

## 実機検証
Brekeke ログを grep `[TEST FAIL]` して 0 件なら全 PASS。`[TEST DONE]` 到達で 32 ケース完走。

## bivr 再生成（テンプレ修正時）
```
# 5 script_<kind>.js は テンプレを cp して var KIND 行のみ解決（{{KIND}} → <kind>）
python scripts/test_scaffold_generator.py modules/field_presence/acceptance_test/設計書_テスト_field_presence.yaml output/json/test_field_presence.json
python scripts/build_bivr.py output/json/test_field_presence.json -o modules/field_presence/acceptance_test/テスト_field_presence_20260617.bivr
```
