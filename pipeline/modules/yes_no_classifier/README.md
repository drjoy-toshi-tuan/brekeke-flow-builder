# yes_no_classifier — Yes/No 決定論分類器

scaffold 固定プロンプト `ECHO_YESNO_PROMPT`（generate_by_OpenAI）を置き換える決定論 Script。
出力は `肯定` / `否定` / `NO_RESULT`（scaffold 分岐パターン互換）。仕様: `REQUIREMENTS.md`。

## 使い方

1. `script.js` を @General$Script モジュールとして配置。
2. 先頭の設定行 `var SOURCE_MODULE = "__SOURCE_MODULE__";` を入力 STT モジュール名に差し替える
   （**この 1 行のみインスタンスパラメータ**。他の行の改変は再受入対象）。
3. next 分岐: `^肯定$` → affirm / `^否定$` → deny / `^NO_RESULT$` → リトライ（再質問）。

## 判定方式（決定論・上から評価）

正規化（全角→半角・小文字化・記号空白除去）→ 空/数字のみ → 完全一致（肯定/否定）→
わからない検知 → **否定マーカー走査（否定優先）** → 肯定マーカー走査 → NO_RESULT。

否定優先の根拠と誤爆対策（「ない」単独不使用・「いません」完全一致のみ等）は REQUIREMENTS.md 参照。

## テスト（テストが正）

- 期待値 SSoT: `acceptance_test/cases.tsv`（161 ケース。実発話 2 ヶ月分 `yes_no_analysis_202603/202604`
  の頻度上位＋disagree 全件＋合成エッジ。OpenAI 実ラベルからの意図的裁定変更は note に `deviation` 明記）
- オラクル受入: `python test_oracle.py` → **161/161 PASS（2026-06-10）**
- Brekeke 実機受入（Pattern 6 単体）: 未実施
- Nashorn↔Python パリティ: 構造一致（同一辞書・同順評価）。実機確証は Pattern 6 で行う

## 回帰運用

月次の yes_no_analysis 出力（extract-yesno-synonyms skill）から新規発話をケース追補 → 再受入。
