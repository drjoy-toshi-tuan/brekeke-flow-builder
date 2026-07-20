# 予約日 抽出・正規化 受入テストシナリオフロー（Pattern 6 単体）

`../script.js`（予約日パーサ・期間制限なし版）を、Pattern 6 の汎用 `script_test_matrix` で
**1 コール内に直列実行**する Brekeke flow。各ケースは `<id>_in`（入力リテラル注入）→ `<id>_clf`
（**正本 `../script.js` をそのまま読込**、入力参照名 `__SOURCE_MODULE__` を `<id>_in` に置換）→
`<id>_cmr`（出力 == 期待値で分岐）→ `<id>_pass`/`<id>_fail`（ログ）。

OpenAI/STT は一切呼ばない（入力は inline_script で直接注入）。検証対象ロジックは 1 文字も変えていない。

## 重要 — このフローは「日付非依存ケースのみ」

予約日パーサは出力が**システム日付 `new Date()`** に依存する（今日/明日/来週/月末/裸の月日/4桁DTMF/
過去日送り）。build 時に焼いた期待値は別の日に実機実行すると相対系が**spurious FAIL** する。
そこで本 bivr には **実行日に依存しない 29 ケースだけ**を載せた（engine v2 #265 で today 非依存の has_月/事故① 9 ケースを追加）:

| prefix | 件数 | 内容 |
|---|---|---|
| `abs01-03` | 3 | 絶対日付（年月日完全指定・遠未来）→ `YYYY-MM-DD 00:00` |
| `dtmf8`/`dtmf8p` | 2 | 8桁DTMF（YYYYMMDD）。過去日は NO_RESULT |
| `inv01-03` | 3 | 無効日付（13月 / 2月30日 / 4月31日）→ NO_RESULT |
| `unk01-08` | 8 | 不明意図（わからない/未定/上旬/中旬/下旬 等）→ `不明` |
| `nr01-04` | 4 | 空 / 無関係発話 / フィラー → NO_RESULT |
| `hasm_*`（v2） | 5 | has_月 回収（西暦年あり N月M→N月M日 / 3十→30 / M月D年・桁溢れガード）|
| `jiko1_*`（v2） | 4 | 事故① 曖昧時期（初旬 / ぐらい / どこか / 初め頃）→ 不明 |

> **相対日付・過去日送り・補正系・STT補正(通知/発火)・v2 の today 依存分(hasm_md_*/hasm_ten/hasm_nod/hasm_selfcorr/jiko1_guard)** は today 依存のため
> **Python オラクル `../test_oracle.py`（today=2026-06-12 固定で 63/63 PASS）側で網羅検証**する。
> bivr には載せない（= 焼いた期待値が陳腐化しないことの担保）。

## 同梱物

| ファイル | 役割 |
|---|---|
| `テスト_予約日分類_20260702.bivr` | Brekeke にインポートする flow（**150 modules** = dispatch 1 + 29×5 + frame 4）|
| `設計書_テスト_予約日分類.yaml` | 上記 bivr の生成元（`script_file: ../script.js` を sidecar 読込、29 ケース内包）|
| `README.md` | このファイル |

## 実行手順

### Brekeke 投入
1. `テスト_予約日分類_20260702.bivr` を Brekeke 管理画面で flow としてインポート（フロー `テスト$予約日分類`）。
2. テスト発信 or「フロー実行」で **1 コールだけ**実行（発話・DTMF 不要。冒頭 opening 後、29 ケースが自動走行して切断）。
3. Brekeke ログ画面で結果を観察。

### ログから結果判定
- **`[TEST FAIL]` の件数が 0 なら全 29 ケース PASS。**
- 末尾に **`[TEST DONE] 予約日 抽出・正規化 単体受入テスト 29 ケース 完走`** が出れば完走。
- 各 PASS 行: `[TEST PASS] <id> in=<入力> exp=<期待>` / FAIL 行: `[TEST FAIL] <id> in=<入力> exp=<期待> got=<clf実出力>`

```
grep -c "\[TEST FAIL\]" call.log     # → 0 を確認
grep "\[TEST DONE\]"   call.log      # → 1 行出れば完走
```

## バグ対応状況（2026-06-12 / 詳細は `../BUG_REPORT_20260612.md`）

検出した 7 件の判断・対応:

1. **B-1 `しあさって`→+2 バグ** … ✅ 修正（→+3）。
2. **B-2 `来週/今週X曜` の週ズレ** … ✅ 修正。暦週・月曜始まり（来週月曜=15日 / 今週月曜=8日）。
   明示的な相対表現（今週/今月N日 等）は名指しの日付をそのまま採用（過去でも翌年送りしない）。
   裸の曜日（今週/来週の語なし）は「直近の次の出現」。
3. **B-3 `new Date()` の TZ** … ✅ 修正。`Asia/Tokyo` 固定（VN 製のため JST に統一）。
4. **B-4 出力 `00:00`（秒なし）** … 現状維持（秒なしでよい）。
5. **B-5 `通知→1日`/`発火→20日`** … 現状維持（予約日のみ流入・STT 補正として残す）。
6. **B-6 `runCorrection` デッドコード** … 🗒️ 据え置き（害なし）。
7. **B-7 入力名 コード/コメント不一致** … ✅ 修正（コメントをコード `入力_変更_予約日` に一致）。

> 上記は本 bivr の 20 ケース（日付非依存）には影響しない（相対系・契約系のため）。bivr は正本 JS 変更に伴い再生成済。

## 既知の制約
- Brekeke 1 コール 1000 モジュール上限内（105 modules）。
- 本テストは `../script.js` の現行ロジック前提。`script.js` を修正したら下記で再生成すること。

## bivr 再生成（`../script.js` / 設計書 修正時）
```
python3 scripts/test_scaffold_generator.py modules/reservation_date_classifier/acceptance_test/設計書_テスト_予約日分類.yaml
python3 scripts/build_bivr.py output/json/scaffold_テスト_予約日分類.json -o modules/reservation_date_classifier/acceptance_test/テスト_予約日分類_<YYYYMMDD>.bivr
# （orchestrator 経由なら: python3 scripts/orchestrator.py --pattern 6 --spec modules/reservation_date_classifier/acceptance_test/設計書_テスト_予約日分類.yaml）
```
汎用 `script_test_matrix`（`scripts/test_scaffold_generator.py`）が `../script.js` をそのまま読み、
`__SOURCE_MODULE__` を case ごとの `<id>_in` に置換して展開する。モジュール個別の build スクリプトは不要。
