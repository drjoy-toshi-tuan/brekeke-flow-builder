# faq_exact_match — 要件 (REQUIREMENTS)

STT 補正済みテキストを **FAQ 質問文と完全一致** で照合し、一致すれば回答本文を、しなければ
`NO_RESULT` を返す決定論 script（Brekeke `@General$Script`）。BM25/RAG ではなく **辞書の完全一致**。
照合用 FAQ 辞書（`faqMap`）は `script.js` 内に埋め込み（施設固有データ）。

> 言い換え・部分一致・近似は **拾わない**（自信がないものは答えない＝医療文脈の安全弁）。
> 言い換え吸収が必要な用途は別部品 `modules/faq_matcher/`（BM25 + coverage）を使う。

## 入出力仕様

| 項目 | 内容 |
|---|---|
| **Input** | 直前モジュール `OpenAI_RAG` の結果（`$runner.getModuleResult("OpenAI_RAG")`）。`{text: "..."}` オブジェクト か 文字列のいずれか |
| **入力正規化** | `String(...).trim()` のみ（前後空白を除去）。**NFKC 等の正規化はしない** |
| **照合** | `faqMap` に**自前キーとして完全一致**するキーがあれば一致（`Object.prototype.hasOwnProperty.call(faqMap, text)`）|
| **Output (context)** | 一致時のみ `$runner.setObject("scripts-faq", <回答本文>)` |
| **Branch (setResult)** | `ANSWER`（一致）/ `NO_RESULT`（不一致・空入力）|

## 分岐ルール（script.js のメインロジック）

1. 入力を取得し `trim`
2. `trim` 後が空文字 → **NO_RESULT**
3. `faqMap` に**完全一致する自前キー**あり → **ANSWER**（`setObject` に回答本文、`setResult` に `"ANSWER"`）
4. それ以外（言い換え・部分一致・無関係・継承プロパティ）→ **NO_RESULT**

## エッジケース（受入テストのカバー範囲）

| 区分 | 入力例 | 期待 | 検証意図 |
|---|---|---|---|
| 完全一致 | `駐車場はありますか` | ANSWER + 正しい回答本文 | 基本動作・**回答本文の正しさ** |
| 末尾記号込みキー | `会計時にクレジットカードは使えますか？` / `手の外科…可能ですか。` | ANSWER | キーに含まれる `？`/`。` まで完全一致が要る |
| 半角カナ・読点キー | `差額ﾍﾞｯﾄ代…` / `診察券を紛失したのですが、…` | ANSWER | 特殊文字キーの完全一致 |
| 回答に半角 `(` | `領収書を紛失しました。再発行できますか` | ANSWER | 回答本文 `支払証明書(1100円）` の照合（受入条件 regex で `\(` エスケープ）|
| 前後空白 / タブ | `␣␣駐車場はありますか␣␣` / `\t面会時間…\t` | ANSWER | `trim` が効くこと |
| object 入力 | `{text:"駐車場はありますか"}` / `{text:"␣面会…␣"}` | ANSWER | `rawInput.text` 抽出 + trim 経路 |
| 言い換え/部分 | `駐車場ありますか`（は欠落）/ `面会時間`（部分）| NO_RESULT | **完全一致である証明**（1文字でも違えば拾わない）|
| 末尾記号欠落 | `手の外科…可能ですか`（末尾 `。` なし）| NO_RESULT | キーの末尾 `。` まで厳密 |
| 無関係 | `今日の天気は` | NO_RESULT | 無関係発話を拾わない |
| 空 / 空白のみ | `""` / `"   "` | NO_RESULT | 空入力ガード |
| **継承プロパティ** | `toString` / `constructor` / `hasOwnProperty` / `__proto__` / `valueOf` | **NO_RESULT** | **下記「堅牢化」**の検証 |

## 堅牢化: 継承プロパティの除外（2026-06-19）

素の `faqMap[text]` は JavaScript のプロパティ参照なので **プロトタイプ継承プロパティも拾う**。
`faqMap["toString"]` は `Object.prototype.toString`（関数）を返し、`!== undefined` が true になって
誤って `ANSWER`（`answer` に関数が入る）になる。これを防ぐため、照合は

```js
if (Object.prototype.hasOwnProperty.call(faqMap, text)) { ... }
```

で **自前キーのみ**に限定する（`text` が `"toString"` 等でも `NO_RESULT`）。
実運用で OpenAI_RAG が英単語キーを返す確率は低いが、決定論部品としての安全弁。
Python オラクル（dict の `in` 判定 = 自前キーのみ）と一致する。

## 非対象（このモジュールの責務外）

- **言い換え/曖昧の吸収** → `modules/faq_matcher/`（BM25）
- **`OpenAI_RAG` の配線・STT 読みの精度** → P7 連結テスト / 上流 STT 層
- **`faqMap` の内容（FAQ の正しさ）** → 施設・業務側のレビュー（本部品は「辞書に忠実に引く」ことのみ担保）

## 受入の定義（Definition of Done）

1. 本書（REQUIREMENTS.md）
2. Python オラクル `oracle.py` + `test_oracle.py` 全 PASS
3. Brekeke 実機受入（Pattern 6 `acceptance_test/FaqExactMatchAcceptanceTest.bivr`）全 PASS ← **実機 PENDING**
4. オラクルと実機の判定一致（理想はデプロイ済み JS とのバイト一致）
5. `modules/README.md` 認定レジストリに登録
