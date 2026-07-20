# go_back_classifier 受入テストフロー（Pattern 6 単体）

Python オラクル `../test_oracle.py`（**24/24 PASS**）と**同一の 24 ケース**を、汎用 `script_test_matrix` で
1 コール内に直列実行する Brekeke flow。各ケース `<id>_in`（入力注入）→ `<id>_clf`（**正本テンプレ
`../../../docs/brekeke/script_templates/go_back_classifier.js` をそのまま読込**、`{{INPUT_MODULE}}` を
`<id>_in` に置換）→ `<id>_cmr`（出力 == 期待値で分岐）→ `<id>_pass`/`<id>_fail`（ログ）。

OpenAI/STT は呼ばない（入力は inline_script で直接注入）。検証ロジックは 1 文字も変えていない。
※テンプレの `{{CONTEXT_FIELD}}` は未解決のままだが、テストでは context が無く getModuleResult(`<id>_in`) に
フォールバックする（=入力注入値を読む）。

## 同梱物
| ファイル | 役割 |
|---|---|
| `テスト_go_back_20260617.bivr` | Brekeke にインポートする flow（zip・125 modules = matrix dispatch 1 + 24×5 + frame 4）|
| `設計書_テスト_go_back.yaml` | 上記 bivr の生成元（`script_file` でテンプレ正本を sidecar 読込、24 ケース内包）|

## カバーする 24 ケース（= oracle CASES と 1:1）
- 戻る 9（やっぱり変更/キャンセル/別の用件/最初から/やり直し/前に戻/違う用件/取り消し/複合）
- 繰り返し 6（もう一回言って/もう一度/聞こえなかった/なんて言った/もっかい/聞き取れ）
- NONE 9（駐車場？/何時？/内科/えっと/空 + **用件語負例 nn06-09**: 変更したい/キャンセルしたい文を NONE に）

## 実機検証
**24/24 PASS（2026-06-18・午前10:32:30・caller 09065765660・2秒完走）**。全ケース `<id>_cmr:1`/`<id>_pass:ok`、`[TEST FAIL]` 0件・`終了:OK`。

Brekeke ログを grep `[TEST FAIL]` して 0 件なら全 PASS。`[TEST DONE]` 到達で 24 ケース完走。

## bivr 再生成（テンプレ修正時）
```
python scripts/test_scaffold_generator.py modules/go_back_classifier/acceptance_test/設計書_テスト_go_back.yaml output/json/test_go_back.json
python scripts/build_bivr.py output/json/test_go_back.json -o modules/go_back_classifier/acceptance_test/テスト_go_back_20260617.bivr
```
