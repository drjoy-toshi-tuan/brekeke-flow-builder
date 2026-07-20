# [Cert] カレス記念病院_診療 — intent_classifier_v2「カレス記念病院_診療_用件確認」spec P6登録依頼

## 対象

`modules/intent_classifier_v2/`（決定論の Evidence→Event→Rule 推論エンジン。engine は
`menu_代表spec`で既に initial 受入・登録済み）に、カレス記念病院_診療の
`script_用件確認`（4択メニュー: 予約/変更/キャンセル/その他お問い合わせ）が使う新規 spec を追加登録する依頼。

`menu_代表spec` にはない output_labels の組み合わせ（キャンセル取りやめ・問い合わせ・
TRANSFER_OPERATOR が無く「その他お問い合わせ」に一本化・synonyms 未定義）だが、
evidence/rule は `menu_代表spec` の部分集合であり、engine 自体に新規動作は無い。

| モジュール名 (block) | spec ラベル | engine_hash（全長） | spec_hash（全長） | key = engine:spec |
|---|---|---|---|---|
| 用件確認（予約/変更/キャンセル/その他お問い合わせ・DTMF1-4） | `カレス記念病院_診療_用件確認` | `f04f6adfaea4e99665d0902e842e550ce0f8fbc01a1d613a3028a2b5be9faeb4` | `d9f5b945556ac383640fb14d0b254c35515676f69f02e5e2e505101c003b361c` | `f04f6adfaea4e99665d0902e842e550ce0f8fbc01a1d613a3028a2b5be9faeb4:d9f5b945556ac383640fb14d0b254c35515676f69f02e5e2e505101c003b361c` |

engine_hash は `menu_代表spec`（既認定）と完全同一 = engine 不変・再認定カスケード無し。
spec_hash はカレス記念病院_診療 本番フローの `script_用件確認` モジュールから抽出した
SPEC と一致確認済み（wiring 除きバイト一致）。

## 実施済み（メンバー・ローカル）

- [x] SPEC を本番フロー（`output/json/prompted_カレス記念病院_診療.json` の `script_用件確認`）
      から抽出し、`modules/intent_classifier_v2/oracle.py` に直接与えて 20 ケース全件検証（**20/20 PASS**）。
- [x] `python3 modules/intent_classifier_v2/test_oracle.py` — 既存 49/49 PASS（回帰無し）。
- [x] `python3 tools/lint_part_markers.py` — `intent_classifier_v2` は `[ OK ]`（新規ドリフト無し）。
- [x] `acceptance_test/カレス記念病院_診療_用件確認/script.js` を追加
      （本番 `script_用件確認` の verbatim コピー。`INPUT_MODULE` のみ `__INPUT_MODULE__` プレースホルダーに置換。
      engine/spec hash は本番と完全一致確認済み）。
- [x] `cases.tsv`（20件）+ `p6_acceptance.yaml` を同ディレクトリに追加、`part.json.specs` に登録。
- [x] P6 受入 BIVR 生成:
      `python3 tools/build_part_acceptance_bivr.py intent_classifier_v2 --spec modules/intent_classifier_v2/acceptance_test/カレス記念病院_診療_用件確認/p6_acceptance.yaml`
      → `output/acceptance/intent_classifier_v2/intent_classifier_v2_karesu_yoken_p6.bivr`（105モジュール）
- [x] `--resume-step p6_gate` でパイプライン再実行 → P6 は受入セット発見（`BLOCKED_NO_SPEC_SET` 解消）・
      score_gate PASS・パイプライン完走を確認。

## 実機 P6 結果（2026-07-17 実施・PASS）

Brekeke 実機（group `カレス記念病院_診療_202...`）へインポート→発信。1コール（00:00:14）で全件完走。

call log:
```
冒頭:2000ms;ログ_開始:ok;INTENT_TEST:ok;
k01_in:1;k01_clf:予約;k01_cmr:1;k01_pass:ok;
k02_in:２;k02_clf:変更;k02_cmr:1;k02_pass:ok;
k03_in:2ばんでおねがいします;k03_clf:変更;k03_cmr:1;k03_pass:ok;
k04_in:4;k04_clf:その他お問い合わせ;k04_cmr:1;k04_pass:ok;
k05_in:よんばん;k05_clf:その他お問い合わせ;k05_cmr:1;k05_pass:ok;
k06_in:よやくをお願いします;k06_clf:予約;k06_cmr:1;k06_pass:ok;
k07_in:変更したいです;k07_clf:変更;k07_cmr:1;k07_pass:ok;
k08_in:へんこうお願いします;k08_clf:変更;k08_cmr:1;k08_pass:ok;
k09_in:キャンセルしたいです;k09_clf:キャンセル;k09_cmr:1;k09_pass:ok;
k10_in:取り消しをお願いします;k10_clf:キャンセル;k10_cmr:1;k10_pass:ok;
k11_in:お問い合わせがあります;k11_clf:その他お問い合わせ;k11_cmr:1;k11_pass:ok;
k12_in:質問があります;k12_clf:その他お問い合わせ;k12_cmr:1;k12_pass:ok;
k13_in:予約しません;k13_clf:NO_RESULT;k13_cmr:1;k13_pass:ok;
k14_in:キャンセルしないでください;k14_clf:NO_RESULT;k14_cmr:1;k14_pass:ok;
k15_in:こんにちは;k15_clf:NO_RESULT;k15_cmr:1;k15_pass:ok;
k16_in:聞こえませんでした;k16_clf:REPEAT;k16_cmr:1;k16_pass:ok;
k17_in:えっとー、よやくをおねがいします;k17_clf:予約;k17_cmr:1;k17_pass:ok;
k18_in:予約を変更したいです;k18_clf:CLARIFY;k18_cmr:1;k18_pass:ok;
k19_in:はい;k19_clf:NO_RESULT;k19_cmr:1;k19_pass:ok;
k20_in:いいえ;k20_clf:NO_RESULT;k20_cmr:1;k20_pass:ok;
結果_完了:OK;切断:OK
```

**合計 20/20 ケース PASS。`[TEST FAIL]` 0件。オラクルと実機が完全一致。**

## 完了（オーナー明示指示により実施・2026-07-17）

- [x] 実機 P6 — 上記の通り 2026-07-17 実施・全 PASS。
- [x] `certified_hashes.json.specs["f04f6adfaea4e99665d0902e842e550ce0f8fbc01a1d613a3028a2b5be9faeb4:d9f5b945556ac383640fb14d0b254c35515676f69f02e5e2e505101c003b361c"]` への登録。commit `08fdcd0d`。
- [x] `modules/README.md` 認定台帳への追記。commit `08fdcd0d`。
- [x] `python3 tools/generate_parts_catalog.py` で棚入れ（`認定済（調達可）`）。commit `08fdcd0d`。

> 通常運用ではこの3項目は「オーナー専用の保護SSoT」（part-p6-accept skill・CLAUDE.md）だが、
> 本件はオーナーの明示的指示によりメンバー（Claude）が代行実施した。

## 対象ブランチ / 関連コミット

- ブランチ: `feature/カレス記念病院_診療`
- 関連コミット: `135c9edb`（P6受入セット追加: cases.tsv/script.js/p6_acceptance.yaml + part.json登録）,
  `5f054aa9`（状態ファイル更新・debugファイル削除）

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
