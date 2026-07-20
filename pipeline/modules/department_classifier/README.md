# Department Classifier（診療科 決定論分類）

患者の発話/STT結果を **公式診療科マスタ30科** に決定論的に分類する Brekeke スクリプト。
`OpenAI_診療科`（generate_by_OpenAI）の置き換え。北里大学TSC 訪問看護で、正規の「皮膚科」が
約半数で「精神神経科」に誤分類される OpenAI の不安定挙動（2026-06-09 Pattern7 実機観察）を根治する。

LLM 不使用。辞書（公式30科 canonical + 中黒なし表記 + 読み + 主要漢字エイリアス）を **最長一致優先** で照合。

## ファイル

| ファイル | 役割 |
|---|---|
| `script.js` | Brekeke (Nashorn/ES5.1) で動作する本体ロジック（**正本**）|
| `oracle.py` | 同等ロジックの Python ポート（期待値の独立実装）|
| `test_oracle.py` | 89 受け入れケース（oracle 自体の単体テスト）|
| `REQUIREMENTS.md` | 入出力・分岐・判定手順・辞書典拠 |
| `acceptance_test/` | Pattern 6 単体受入テスト一式（テスト設計書 YAML + 生成 bivr + 手順）|

## モジュール仕様

- **type**: `@General$Script`（汎用 Script モジュール。本番 bivr では名称 `Script_診療科分類`）
- **入力**: `$runner.getModuleResult("入力_診療科")`（STT結果。文字列 or `{text:...}`）
- **出力**（`$runner.setResult`）の3種:

  | 出力 | 意味 | フロー側ルーティング |
  |---|---|---|
  | 公式30科の canonical 名（中黒「・」付き） | 認識成功 | `^.*$` → 主治医名（sub `save-診療科正規化` が clinicalDepartment へ保存）|
  | `登録なし` | 「わからない」等の不明意図 | `^.*$` → 主治医名（**スキップ・再質問しない**）|
  | `NO_RESULT` | 数字のみ / 空 / どの科にも不一致 | `^NO_RESULT$` → save-登録なし → リトライ_診療科（再質問）|

- **正規化**: NFKC 実効サブセット（全角数字→半角・空白/記号/かぎ括弧除去・末尾定型語「です」「をお願いします」等除去）。Nashorn 想定で `String.normalize` 不使用（診療科入力は漢字/ひらがな科名・読みのため限定正規化で NFKC と実効同値）。
- **辞書典拠**: 設計書「診療科一覧」スライド8-9（公式30科 + 類義語/読み）。**リハビリテーション科はマスタ非掲載のため不採用**（2026-06-09 ユーザー確定）。
- **前提**: STT 側 profile_words が公式30科名へ整合済み（2026-06-09 実施）。よって辞書一致で十分。

## ローカル検証

```
PYTHONIOENCODING=utf-8 python test_oracle.py
```

**89/89 PASS** で 30科恒等 / profile_words 中黒なし / 包含関係（最長一致）/ 読み / 別名 / 全角・敬称 / わからない / NO_RESULT を確認。

## Brekeke 実機検証

`acceptance_test/` 参照。Pattern 6（[[project_pattern_6_test_flow]]）の汎用 `script_test_matrix` で
オラクルと同一の 89 ケースを 1 コール内に直列実行する。

1. `acceptance_test/テスト_診療科分類_20260609.bivr` を Brekeke に import（フロー `テスト$診療科分類`、450 modules）
2. 1 コール実行（入力不要、自動走行）
3. ログを `grep "[TEST FAIL]"` → **0 件なら全 PASS**、末尾 `[TEST DONE]` で完走確認

**実機受入: 89/89 PASS（2026-06-09 16:55、call 6440）**。`[TEST FAIL]` 0 件・`[TEST DONE]` 到達。
皮膚科=皮膚科（精神神経科誤分類 0）・中黒 canonical 厳密一致・空入力→NO_RESULT・わからない→登録なし、全て実機確認。Nashorn↔Python パリティ全89一致。

## 既知の制約

- profile_words（STT辞書）が公式30科へ整合済みである前提。整合が崩れると辞書未収載語は `NO_RESULT`（再質問）に落ちる。
- 包含関係（小児科 ⊂ 小児外科 ⊂ 小児心臓血管外科、消化器内科/消化器外科 等）は **キー長降順 + 同長は定義順** で安定裁定。辞書を編集する場合はこのタイブレークを壊さないこと。
- Brekeke 1 コール 1000 モジュール上限（[[feedback_brekeke_max_module_execution_1000]]）。本体は 1 module。受入テスト 89 ケース連結時は 450 modules。
- Brekeke Module Output は string 化される（[[feedback_brekeke_module_output_stringified]]）が、本モジュールは元々 string（科名/登録なし/NO_RESULT）を返すので影響なし。
- **1 文字でも改変したら再受入**（CLAUDE.md 部品ポリシー）。`script.js` 修正時は `test_oracle.py` を更新の上、`acceptance_test/` の bivr を再生成（下記）。

## bivr 再生成（script.js 修正時）

acceptance_test は汎用 `script_test_matrix` を使うため、モジュール個別の build スクリプトは不要。
`script.js` をそのまま sidecar 読込し、入力参照名 `入力_診療科` を case ごとに差し替える。

```
python scripts/orchestrator.py --pattern 6 --spec modules/department_classifier/acceptance_test/設計書_テスト_診療科分類.yaml
# → output/scenarios/テスト_診療科分類/テスト_診療科分類_<日付>.bivr を生成。acceptance_test/ へコピーして差し替え。
```
