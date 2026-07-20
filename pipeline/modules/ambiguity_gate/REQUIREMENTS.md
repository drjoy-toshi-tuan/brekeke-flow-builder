# ambiguity_gate — 紛れペア（最小対）の曖昧検出器（決定論分類 多段構成 Stage2）

## 目的・背景

OpenAI 正規化時代に持てなかった「**正規化結果が正しいかを検証する 2 段目（検品）**」を決定論で実装する共通部品。
区別 token が小さく STT が壊しやすい候補（最小対）— 例: **1日ドック / 2日ドック**、**消化器内科 / 消化器外科** —
は、優先順位設定では「区別が付かない時に先に書いた方を黙って既定採用」してしまい、STT が区別 token を壊すと
**自信満々で半分誤る（誤りが表に出ない）**。本部品はスコア＋ idf-margin で「綺麗に分離できるか」を判定し、
分離できない時は **"拾えないと分かる"（CONFIRM）** に倒して親→確認ステップ（DTMF 等）へ流す。

各分類器に内蔵すると責任範囲が膨大化するため、**単一の共通モジュール**として全分類器が CMR で合流する。

## 入出力

- 入力: `$runner.getModuleResult(SOURCE_MODULE)`（上流の発話）/ 設定 `GROUP`（紛れ候補群名）
- 出力（`setResult`、CMR で分岐）:
  - **勝者ラベル**（例 `1日ドック`）= 区別が立ち分離 OK → そのまま確定
  - **`CONFIRM`** = 団子（idf-margin < しきい値）→ 親分類→確認ステップ（DTMF 等）へ
  - **`NO_RESULT`** = 候補群に当たらない / 短すぎ / 未定義 GROUP → 通常リトライ

## アルゴリズム（faq_matcher と同方式）

1. `normalize`: NFKC → lower → STRIP（4分類器・faq_matcher と同集合）
2. `bigrams`: 文字 2-gram（語順・分割崩れに強い）
3. GROUP の各 member（ラベル＋語彙バリアント）を doc 展開し df / n を構築
4. **exact-match 短絡**: 正規化が 1 ラベルの variant と完全一致 → そのラベル
5. member 別 **最大 idf_coverage**（質問 bigram のうちマッチした分の IDF 質量比。ありふれた共通 bigram は
   寄与小、珍しい区別 token を強く反映）
6. 何も当たらない（best ≤ 0）→ `NO_RESULT`
7. **idf-margin**（best − 次点） < `MIN_IDF_MARGIN` → `CONFIRM`（団子）
8. それ以外 → best ラベル

## CONFIG

| 定数 | 既定 | 意味 |
|---|---|---|
| `MIN_QUERY_CHARS` | 2 | 正規化後この文字数未満は判定しない（→ NO_RESULT）|
| `MIN_IDF_MARGIN` | 0.12 | 採用候補と次点の idf 被覆率差の下限。未満は団子 → CONFIRM。**紛れペアの厳しさ・施設方針で調整するツマミ**（施設から「確認が増えすぎ」と出たらここを緩める）|

## GROUP 定義

`GROUPS` = `group名 -> [(ラベル, [語彙バリアント...]), ...]`。組込先のデータ（将来は Note / プロパティ供給も検討）。
script.js / oracle.py 内蔵の例は検証用（`course_dock` / `dept_shoukaki`）。

## 既知の範囲・限界

- **NFKC はカナ↔ひらがな↔漢字を変換しない**: `しょうかきないか`（かな化）は漢字 bigram に当たらず `NO_RESULT`。
  これは上流 TTS 誘導 / 辞書のカナ・読み変種で対処する範囲（本部品の責務外）。
- 本部品は**分離可否の検出器**であって、確認ステップ（DTMF 等）の UI は呼び出し側フローが持つ。
  確認ステップは checkup_menu_classifier の MENU（子だけスコープ）として再利用できる（音声で紛れる固有名詞を番号で確定する前例と同じ）。

## DoD

- [x] REQUIREMENTS.md
- [x] oracle.py + test_oracle.py（cases.tsv 全件 PASS = 18/18）
- [x] script.js（Nashorn/ES5.1・oracle.py とパリティ）
- [ ] Brekeke 実機受入（Pattern 6 受入 bivr）— 全 PASS
- [ ] Nashorn↔Python パリティ実機確認
- [x] certified_hashes.parts に engine 登録済み（v2・engine_hash 2c7a2fc2…）
- [ ] Brekeke 実機受入 → certified_hashes.specs 登録 / modules/README.md 認定レジストリ spec 行追記

## パイプライン統合で要対応（本スケルトン外）

- ~~`scripts/orchestrator.py` の `_CONFIG_LINE_PREFIXES` に `"var GROUP"` を追加~~
  → **v2 ゲートで解決済み**。`GROUP` は `part.json` の `wiring_vars` で宣言し、`_engine_spec_hashes` が
  wiring 行を engine/spec 両ハッシュから除外する（`_CONFIG_LINE_PREFIXES` 自体が v2 で廃止）。
- ~~受入 bivr 生成器（`build_classifier_acceptance_bivr.py`）の group 列対応~~
  → **対応済み**。`CONFIG_COLS = {"menu": "MENU", "group": "GROUP"}` で cases.tsv の `group` 列を `var GROUP` に注入。
- フロー配線（**未**）: 親分類 → ambiguity_gate → CMR（`^CONFIRM$`→確認ステップ / `^NO_RESULT$`→リトライ / 他→ラベル確定）。
