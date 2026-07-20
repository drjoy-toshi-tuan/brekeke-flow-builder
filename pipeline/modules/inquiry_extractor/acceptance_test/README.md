# 用件抽出 受入テストシナリオフロー（Pattern 6 単体）

Python オラクル `../test_oracle.py` と **同一ケース**（文字列注入可能な 22 件）を、Pattern 6 の汎用
`script_test_matrix` で **1 コール内に直列実行** する Brekeke flow。各ケースは
`<id>_in`（入力注入）→ `<id>_clf`（**正本 `../script.js` をそのまま読込**、入力参照名
`用件抽出_入力` を `<id>_in` に置換）→ `<id>_cmr`（setResult == 期待 canonical で分岐）→ `<id>_pass`/`<id>_fail`（ログ）。

OpenAI/STT は一切呼ばない（入力は inline_script で直接注入）。検証対象ロジックは 1 文字も変えていない。

## 同梱物

| ファイル | 役割 |
|---|---|
| `テスト_用件抽出_20260616.bivr` | Brekeke にインポートする flow（**115 modules** = dispatch 1 + 22×5 + frame 4）|
| `設計書_テスト_用件抽出.yaml` | 上記 bivr の生成元（`script_file: ../script.js` を sidecar 読込、22 ケースを内包）|
| `README.md` | このファイル |

## カバーする 22 ケース（= oracle CASES のうち文字列注入可能なもの）

| 区分 | 件数 | 内容 |
|---|---|---|
| 基本3パス | 5 | 新規予約フル / 全スロット / 変更・取消(予約日時のみ) / 変更フル(キャンセル) / 問い合わせのみ |
| 用件種別不明→スロット推定 | 4 | 予約日時→変更・取消 / 診療科→新規予約 / 予約希望日→新規予約 / 全空→問い合わせのみ |
| 用件種別 表記ゆれ | 6 | 予約したい→新規 / 取り消し・キャンセル・予約変更→変更 / 相談→問い合わせ / 変更(診療科併記) |
| 明示優先 | 1 | 「問い合わせのみ」明示は日付発話があってもスロット推定より優先 |
| 空文字 | 1 | 空入力 → 問い合わせのみ・全未取得 |
| フィールド数ズレ | 2 | 5個→パディング / 10個→切捨て |
| trim | 3 | 前後半角空白 / 全角空白 / 引用符・かぎ括弧 |

> `none_input` / `dict_input`（null・`{text:..}` 入力）は inline_script で注入できないためオラクル専管。
> production の `setObject` 撒き出し（context 15 キー）は本単体テストでは照合しない（Pattern 7 連結で確認）。

## 実行手順

### Brekeke 投入
1. `テスト_用件抽出_20260616.bivr` を Brekeke 管理画面で flow としてインポート（フロー `テスト$用件抽出`）。
2. テスト発信 or「フロー実行」で **1 コールだけ** 実行（発話・DTMF 不要。冒頭 wait 後 22 ケースが自動走行して切断）。
3. Brekeke ログ画面で結果を観察。

### ログから結果判定
- **`[TEST FAIL]` の件数が 0 なら全 22 ケース PASS。**
- 末尾に **`[TEST DONE] 用件抽出 決定論パーサ 単体受入テスト 22 ケース 完走`** が出れば完走。
- 各 PASS 行: `[TEST PASS] <id> in=<入力> exp=<期待>` / FAIL 行: `[TEST FAIL] <id> in=<入力> exp=<期待> got=<実出力>`
- 中間に `[SCRIPT-INQUIRY] raw=… out=…`（本体ログ）と `ContextMatchRouter: Matched at index 1`（PASS）/ `index 0`（FAIL）も出る。

```
grep -c "\[TEST FAIL\]" call.log     # → 0 を確認
grep "\[TEST DONE\]"   call.log      # → 1 行出れば完走
```

## 実機結果

**26/26 PASS（2026-06-16・午後01:21:40・caller 09065765660・4秒完走）**。全ケース `<id>_cmr:1`＋`<id>_pass:ok`、
`[TEST FAIL]` 0 件・`ログ_終了:ok;終了:OK` 到達。clf 出力はオラクル期待と全26バイト一致（Nashorn↔Python パリティ確証）。
→ `../REQUIREMENTS.md` DoD ＋ `modules/README.md` 認定レジストリを「認定済み」へ昇格済み。

**再々cert 26/26 PASS（2026-06-18・午前10:27:33・caller 09065765660・6秒完走）**。氏名抽出除去版（`@未取得`固定・SUMMARY氏名様なし）で全26バイト一致。`[TEST FAIL]` 0件・`終了:OK`。

## 既知の制約
- Brekeke 1 コール 1000 モジュール上限内（115 modules）。
- 本テストは `../script.js` の現行ロジック前提。`script.js` を修正したら下記で再生成すること。

## bivr 再生成（`../script.js` 修正時）
```
python scripts/test_scaffold_generator.py modules/inquiry_extractor/acceptance_test/設計書_テスト_用件抽出.yaml output/json/scaffold_テスト_用件抽出.json
python scripts/build_bivr.py output/json/scaffold_テスト_用件抽出.json -o modules/inquiry_extractor/acceptance_test/テスト_用件抽出_20260616.bivr
```
汎用 `script_test_matrix`（`scripts/test_scaffold_generator.py`）が `../script.js` をそのまま読み、
`用件抽出_入力` を case ごとの `<id>_in` に置換して展開する。モジュール個別の build スクリプトは不要。
