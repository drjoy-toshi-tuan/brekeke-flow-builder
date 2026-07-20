# 診療科 決定論分類器（department_classifier）— 仕様

`OpenAI_診療科`（generate_by_OpenAI）を置き換える決定論分類スクリプト。北里大学TSC 訪問看護で、
正規の「皮膚科」が約半数で「精神神経科」に誤分類される OpenAI の不安定挙動（2026-06-09 Pattern7 case1/2 実機観察）を根治する。

## 位置づけ
- プロジェクト方針「OpenAI→決定論置換」（CLAUDE.md / deterministic-replacement-roadmap）に準拠。
- 入力は profile_words で公式30科名へ正規化済み（STT辞書を公式マスタへ整合済み 2026-06-09）。よって辞書完全一致で十分。

## 入出力
- 入力: `$runner.getModuleResult("入力_診療科")`（STT結果。文字列 or `{text:...}`）。
- 出力（`$runner.setResult`）の3種:
  | 出力 | 意味 | フロー側ルーティング |
  |---|---|---|
  | 公式30科の canonical 名（中黒「・」付き） | 認識成功 | `^.*$` → 主治医名（sub `save-診療科正規化` が clinicalDepartment へ保存）|
  | `登録なし` | 「わからない」等の不明意図 | `^.*$` → 主治医名（**スキップ・再質問しない**）|
  | `NO_RESULT` | DTMF数字のみ / 空 / どの科にも不一致 | `^NO_RESULT$` → save-登録なし → リトライ_診療科（再質問）|

## 判定手順（決定論・上から評価）
1. 正規化: NFKCサブセット（全角数字→半角）＋空白/記号/かぎ括弧除去＋末尾定型語除去（「です」「をお願いします」等）。
2. 「わからない」キーワード部分一致 → `登録なし`。
3. 半角数字のみ → `NO_RESULT`（診療科に番号対応なし）。
4. 辞書（公式30科 canonical＋中黒なし表記＋読み＋主要漢字エイリアス）を**最長一致優先**で照合 → canonical。
   - 包含関係（小児科 ⊂ 小児外科 ⊂ 小児心臓血管外科 等）はキー長降順＋同長は定義順で安定裁定。
5. 不一致 → `NO_RESULT`。

## 辞書の典拠
設計書「診療科一覧」スライド8-9（公式30科＋類義語/読み）。**リハビリテーション科はマスタ非掲載のため不採用**（2026-06-09 ユーザー確定）。

## 成果物（modules/department_classifier/ 標準構成）
- `script.js` … Brekeke @General$Script 版（**正本**。oracle と同一辞書・同順タイブレーク）
- `oracle.py` … Python 参照実装（期待値の独立実装）
- `test_oracle.py` … 受入テスト（**89/89 PASS, 2026-06-09**）
- `README.md` … 概要・モジュール仕様・実機検証手順・既知の制約
- `acceptance_test/` … Pattern 6 単体受入テスト一式（`設計書_テスト_診療科分類.yaml`〔`script_file: ../script.js`〕 + `テスト_診療科分類_20260609.bivr` 450 modules + 手順 README）
- フロー組込（北里大学TSC 訪問看護本番 bivr）: `Script_診療科分類`（@General$Script）として組込済み。sub=`save-診療科正規化`(save2db, clinicalDepartment)。

## DoD 状況
- [x] REQUIREMENTS.md
- [x] Python オラクル全 PASS（89/89）
- [x] **Brekeke 実機受入（Pattern 7 連結）PASS（2026-06-09）** … 連結テスト bivr 全12ケースで `Script_診療科分類:皮膚科`（皮膚科入力時、**精神神経科の誤分類0件**）。case8で `入力_診療科:わからない → Script_診療科分類:登録なし →（スキップ）主治医名`。Nashorn↔Python パリティ実機確認。
- [x] **Pattern 6 単体受入テスト 実機 PASS（2026-06-09 16:55）** … オラクルと同一 89 ケースを単体実行し **89/89 全 PASS**（`[TEST FAIL]` 0 件・`[TEST DONE]` 到達、call 6440/Thread-5351）。皮膚科=皮膚科（精神神経科誤分類 0）・中黒canonical厳密一致・空入力→NO_RESULT・わからない→登録なし、全て実機確認。**Nashorn↔Python パリティ全89ケース一致**。bivr=`テスト_診療科分類/テスト_診療科分類_20260609.bivr`（450 modules）/ 手順=`Pattern6実行ガイド_診療科分類_20260609.md`。
- [x] `modules/README.md` 認定レジストリ登録（2026-06-09、`modules/department_classifier/` へ収容・台帳1行追加）

## パリティ（Python ↔ Brekeke JS）
同一の DEPARTMENTS / WAKARANAI / TRAILERS と、最長一致＋定義順タイブレークで構造的に一致。
JS は Nashorn(ES5.1) 想定で `String.normalize` 不使用（全角数字・空白・記号・末尾語の限定正規化）。
診療科入力は漢字/ひらがな科名・読みのため、限定正規化で NFKC と実効同値。実機パリティは Pattern 7 連結（皮膚科/わからない）＋ Pattern 6 単体（全89ケース）で確証済み（2026-06-09）。

## 注意
- `登録なし` は「わからない」スキップ用の正常出力（save2db は非空なので保存可）。`NO_RESULT` のみ再質問へ。
- 1文字でも改変したら再受入（CLAUDE.md 部品ポリシー）。
