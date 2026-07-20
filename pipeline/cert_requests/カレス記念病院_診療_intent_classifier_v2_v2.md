# [Cert] intent_classifier_v2 — menu_代表spec P6登録依頼（master同期後・v2）

> 旧 `feature/intent_classifier_v2_p6_accept` ブランチは master に大量の更新
> （語彙拡張7件・他セッションのP6準備 `6ba7621f`）が入ったため作り直し。
> 本ファイルは `feature/intent_classifier_v2_p6_accept_v2` での再受入記録。

## 対象

`modules/intent_classifier_v2/` — 決定論の Evidence→Event→Rule 推論エンジン。初回受入
（既存 certified_hashes.json に未登録）。

master 同期後に発見・修正した不具合:
- `script.js` の `var SPEC = {{SPEC_JSON}};` が `@spec-begin`/`@spec-end` で囲まれておらず、
  他セッションの先行 P6 準備コミット（`6ba7621f`・engine_hash `c75fbfcd...`登録）も
  この不具合を継承していた（spec が変わるたびengine_hashも変わり「1エンジンで複数spec受入」
  という設計が機能しない）。再修正し、engine_hash を `f04f6adf...` に訂正。

| モジュール名 (block) | spec ラベル | engine_hash（全長） | spec_hash（全長） | key = engine:spec |
|---|---|---|---|---|
| 用件確認_menu代表spec（予約/変更/キャンセル/キャンセル取りやめ/問い合わせ/TRANSFER_OPERATOR/CLARIFY/REPEAT/NO_RESULT） | `menu_代表spec` | `f04f6adfaea4e99665d0902e842e550ce0f8fbc01a1d613a3028a2b5be9faeb4` | `80ae3714cdf48651c6a8ff47b7fffa5182542cdd87601bbce7673a1417439cea` | `f04f6adfaea4e99665d0902e842e550ce0f8fbc01a1d613a3028a2b5be9faeb4:80ae3714cdf48651c6a8ff47b7fffa5182542cdd87601bbce7673a1417439cea` |

engine_hash は template（`{{SPEC_JSON}}`未充填）と filled（`generated_menu.js`）間で一致確認済み。

## 実施済み（メンバー・ローカル）

- [x] `python3 modules/intent_classifier_v2/test_oracle.py` — **49/49 PASS**
- [x] mutation testing 再検証（negation scope/specificity優先度/CLARIFYマージン）—
      現行46ケース（他セッションの語彙拡張分含む）で3ミュータント全て検出確認済み
- [x] 実発話 corpus regression（2026-07-17・実ログ2本・計約3600ペア）:
      「いいです」「希望します」「ありません」の語彙欠落を発見・修正。
      修正後は実ラベル確定済み31発話中、既知ノイズ1件（「はい言えることはない」・
      実ラベル側の疑わしいSTT崩れ）を除き全一致
- [x] `python3 tools/lint_part_markers.py` — `intent_classifier_v2` は `[ OK ]`
- [x] 27ケース分の cases.tsv を他セッション準備分（`用件確認_menu`）から採用・
      P6 受入 BIVR 生成（`modules/build_classifier_acceptance_bivr.py intent_classifier_v2`）:
      `modules/intent_classifier_v2/acceptance_test/IntentV2AcceptanceTest.bivr`
      （27ケース/55モジュール）
      ※他セッションのYAML（`type: intent`+`engine: v2`）は `test_scaffold_generator.py` が
        intent ブロック型未対応のためビルド不能だったため、実績あるチェーン方式で作り直し。

## 実機 P6 結果（2026-07-17 実施・PASS）

Brekeke 実機（group `カレス記念病院_診療_202...$用件分類v2受入`）へインポート→発信。
call log の `Jp.テストm01`〜`Jp.テストm27` が cases.tsv の expected と全件一致
（例: `m01:予約` `m07:キャンセル取りやめ` `m10:CLARIFY` `m11:TRANSFER_OPERATOR`
`m13:NO_RESULT` `m15:REPEAT` `m16〜m19:問い合わせ` 等）、最終 `Jp.PASS_全件PASS:OK` で完走。

**合計 27/27 ケース PASS。fail 0件。オラクルと実機が完全一致。**

## 完了（オーナー明示指示により実施・2026-07-17）

- [x] `certified_hashes.json.specs["f04f6adf...:80ae3714..."]` への登録。commit `f56fe3bb`。
- [x] `modules/README.md` 認定台帳への追記。commit `f56fe3bb`。
- [x] `python3 tools/generate_parts_catalog.py` で棚入れ（`認定済（調達可）`）。commit `f56fe3bb`。

> 通常運用ではこの3項目は「オーナー専用の保護SSoT」（part-p6-accept skill・CLAUDE.md）だが、
> 本件はオーナー（本forkの管理者）の明示的指示によりメンバー（Claude）が代行実施した。

## 対象ブランチ / 関連コミット

- ブランチ: `feature/intent_classifier_v2_p6_accept_v2`（push済み）
- 関連コミット: `135ca9e3`（P6実機受入インフラ再構築）, `a2977fd6`（corpus regression第2回）,
  `f56fe3bb`（engine+spec認定登録）

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
