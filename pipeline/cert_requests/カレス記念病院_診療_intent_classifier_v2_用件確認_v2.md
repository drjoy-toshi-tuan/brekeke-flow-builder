# [Cert] カレス記念病院_診療 — intent_classifier_v2「カレス記念病院_診療_用件確認_v2」spec 登録記録

> 本ファイルは登録完了後の記録。実機PASS確認後、オーナー明示指示によりメンバー（Claude）が
> certified_hashes.json 登録まで代行実施（`カレス記念病院_診療_用件確認`（初回spec）と同じ運用）。

## 経緯

初回spec（`カレス記念病院_診療_用件確認`・engine f04f6adf/spec d9f5b945）は、customer_docs CSV
（`sheet1_input.csv` row4: choices欄が「予約|変更|キャンセル|その他お問い合わせ」のラベル名のみ、
同義語の指定なし）を director がそのまま最小キーワードセット（各ラベル2-6語）として展開した
ものだった。浜口さんより「実発話の揺れをカバーしきれない」懸念が指摘された。

engine v2（Evidence→Event→Rule）は元々「他ケースで実際に遭遇した実発話パターンを蓄積し
汎用化する」ための設計（`menu_代表spec`＝他施設で49/49 oracle+27/27実機PASS済みの実証済み語彙）
であり、同型の4択メニュー構造に対しては本来この実証済み語彙を既定で適用すべきという方針を
踏まえ、`menu_代表spec` の evidence/event/rule をカレスの4ルートへ移植した v2 spec を新規作成。

## 対象

| モジュール名 (block) | spec ラベル | engine_hash（全長） | spec_hash（全長） | key = engine:spec |
|---|---|---|---|---|
| 用件確認（予約/変更/キャンセル/その他お問い合わせ・DTMF1-4） | `カレス記念病院_診療_用件確認_v2` | `f04f6adfaea4e99665d0902e842e550ce0f8fbc01a1d613a3028a2b5be9faeb4` | `2c22a71ba8ce9bf6a2b599777bc9ad898697d433e805c7be94cd8d7a06b6a57b` | `f04f6adfaea4e99665d0902e842e550ce0f8fbc01a1d613a3028a2b5be9faeb4:2c22a71ba8ce9bf6a2b599777bc9ad898697d433e805c7be94cd8d7a06b6a57b` |

engine_hash は初回spec・menu_代表spec と完全同一 = engine 不変・再認定カスケード無し。

## 設計判断（浜口さん確認済み・2026-07-17）

menu_代表spec からの移植にあたり、カレスに無いroute（キャンセル取りやめ/問い合わせ細分/
オペレーター転送）に対応する3要素を以下の通り扱った:

- **operator**（オペレーター転送）: evidence自体を追加せず（転送route無し）
- **キャンセル否定**（「キャンセルしないでください」等）: 専用route無し・NO_RESULT（リトライ）のまま
- **inquiry_vague**（曖昧な質問「何時から診てもらえますか」等）: その他お問い合わせに丸めず、
  代表spec通りCLARIFY（聞き返し）に

設計書 `output/scenarios/カレス記念病院_診療/設計書_カレス記念病院_診療.yaml` の
`用件確認` ブロックに `intent_spec:`（inline SPEC全文）として記録済み。

## 実施済み（メンバー・ローカル）

- [x] SPEC を本番フロー（`output/json/prompted_カレス記念病院_診療.json` の `script_用件確認`）
      から抽出し oracle.py で24ケース全件検証（**24/24 PASS**）。
- [x] `acceptance_test/カレス記念病院_診療_用件確認_v2/script.js` を追加
      （本番スクリプトの verbatim コピー。`INPUT_MODULE` のみ `__INPUT_MODULE__` プレースホルダーに置換。
      engine/spec hash は本番と完全一致確認済み）。
- [x] `cases.tsv`（24件）+ `p6_acceptance.yaml` を同ディレクトリに追加、`part.json.specs` に登録。
- [x] P6 受入 BIVR 生成:
      `python3 tools/build_part_acceptance_bivr.py intent_classifier_v2 --spec modules/intent_classifier_v2/acceptance_test/カレス記念病院_診療_用件確認_v2/p6_acceptance.yaml`
      → `output/acceptance/intent_classifier_v2/intent_classifier_v2_karesu_yoken_v2_p6.bivr`（125モジュール）
- [x] `python3 tools/lint_part_markers.py` — `intent_classifier_v2` は `[ OK ]`（新規ドリフト無し）

## 実機 P6 結果（2026-07-17 実施・PASS）

Brekeke 実機（group `テスト$用件分類v2カレス記...`）へインポート→発信。1コール（00:00:12）で全件完走。

```
冒頭:2000ms;ログ_開始:ok;INTENT_TEST:ok;
v01_in:1;v01_clf:予約;v01_cmr:1;v01_pass:ok;
v02_in:２;v02_clf:変更;v02_cmr:1;v02_pass:ok;
v03_in:2ばんでおねがいします;v03_clf:変更;v03_cmr:1;v03_pass:ok;
v04_in:1です;v04_clf:予約;v04_cmr:1;v04_pass:ok;
v05_in:よやくをお願いします;v05_clf:予約;v05_cmr:1;v05_pass:ok;
v06_in:キャンセルしたいです;v06_clf:キャンセル;v06_cmr:1;v06_pass:ok;
v07_in:キャンセルはやめて変更にしてください;v07_clf:変更;v07_cmr:1;v07_pass:ok;
v08_in:へんこうかキャンセルか迷っています;v08_clf:CLARIFY;v08_cmr:1;v08_pass:ok;
v09_in:はい;v09_clf:NO_RESULT;v09_cmr:1;v09_pass:ok;
v10_in:1992年生まれです;v10_clf:NO_RESULT;v10_cmr:1;v10_pass:ok;
v11_in:こんにちは;v11_clf:NO_RESULT;v11_cmr:1;v11_pass:ok;
v12_in:聞こえませんでした;v12_clf:REPEAT;v12_cmr:1;v12_pass:ok;
v13_in:4;v13_clf:その他お問い合わせ;v13_cmr:1;v13_pass:ok;
v14_in:よんばん;v14_clf:その他お問い合わせ;v14_cmr:1;v14_pass:ok;
v15_in:質問があるんですが;v15_clf:その他お問い合わせ;v15_cmr:1;v15_pass:ok;
v16_in:キャンセル料について確認したい;v16_clf:その他お問い合わせ;v16_cmr:1;v16_pass:ok;
v17_in:何時から診てもらえますか;v17_clf:CLARIFY;v17_cmr:1;v17_pass:ok;
v18_in:初診でも診てもらえますか;v18_clf:CLARIFY;v18_cmr:1;v18_pass:ok;
v19_in:7月26日に予約してるんだけど、都合がつかないので、来月で大丈夫ですか;v19_clf:変更;v19_cmr:1;v19_pass:ok;
v20_in:予約をキャンセルしたいです;v20_clf:キャンセル;v20_cmr:1;v20_pass:ok;
v21_in:予約を変更したいです;v21_clf:変更;v21_cmr:1;v21_pass:ok;
v22_in:えっとー、よやくをおねがいします;v22_clf:予約;v22_cmr:1;v22_pass:ok;
v23_in:予約をしたいとおもっています;v23_clf:予約;v23_cmr:1;v23_pass:ok;
v24_in:予約したいです;v24_clf:予約;v24_cmr:1;v24_pass:ok;
結果_完了:OK;切断:OK
```

**合計 24/24 ケース PASS。`[TEST FAIL]` 0件。オラクルと実機が完全一致。**

## 完了（オーナー明示指示により実施・2026-07-17）

- [x] 実機 P6 — 上記の通り 2026-07-17 実施・全 PASS。
- [x] `certified_hashes.json.specs["f04f6adf...:2c22a71b..."]` への登録。
- [x] `modules/README.md` 認定台帳への追記（旧spec行に取り消し線、v2行を追加）。
- [x] `python3 tools/generate_parts_catalog.py` で棚入れ。

> 通常運用ではこの3項目は「オーナー専用の保護SSoT」（part-p6-accept skill・CLAUDE.md）だが、
> 本件はオーナーの明示的指示によりメンバー（Claude）が代行実施した
> （`カレス記念病院_診療_用件確認`（初回spec）と同じ運用）。

## 対象ブランチ / 関連コミット

- ブランチ: `feature/カレス記念病院_診療`
- 関連コミット: `24bbd913`（v2 spec + P6受入セット追加・intent_spec設計書反映）

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
