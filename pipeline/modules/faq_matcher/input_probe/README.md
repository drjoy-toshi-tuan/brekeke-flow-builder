# Input Read API Probe (FAQ Matcher)

OpenAI を使わない RAG 検索フローで、`@General$Script` から **直前の STT モジュールの
文字起こし(生テキスト)** を読む API を **実機で確定** するための probe。

FAQ Matcher 本体の検索ロジック（NFKC 正規化 + 文字 2-gram + BM25）を書く前に、
「患者の発話をどう取るか」だけを先に潰す。ここが未確定のまま本体を書くと、
最悪 `"success"`（STT success 分岐の label）を検索クエリにしてしまう事故になる。

## なぜ probe が要るか

`$runner.getModuleResult(<name>)` は **「マッチした next 条件の label」を返すことがある**
（2026-04-22 大分赤十字病院_診療、入力=OpenAI モジュールで判明。`docs/brekeke/
script_templates/future_date.js` のコメント参照）。

- 本フローは **OpenAI を一切使わない**ので、その「OpenAI 経路の罠」自体は発生しない。
- ただし入力源の STT は success 分岐が `{"condition":"^.+$", "label":"success"}`。
  もし label を返す挙動が STT にも一般化すると、`getModuleResult` が
  **文字起こしではなく `"success"`** を返す可能性が残る。
- 本番テンプレ間でも証言が割れている（`condition_group.js` / `phone_type.js` は実値前提、
  `future_date.js` は label が返ると警告）→ **STT については実機で白黒つけるまで未確定**。

## 前提

- 実在する **問い合わせ系 STT**（例: `入力_相談_問合せ`）が動作していること。
- テスト発信時に、その STT で **既知のはっきりしたフレーズ**を発話できること。

## 使い方

1. 対象 STT の **直後** に `@General$Script` モジュールを 1 個追加する
   （FAQ Matcher 本体が将来座る位置とほぼ同じ）。
2. `script` 欄に `probe_script.js` の全文をペースト。
3. `probe_script.js` の CONFIG `STT_MODULE_NAME` を、その直前 STT のモジュール名に差し替える。
4. このモジュールの jumps に `^in-probe-done$`（または `^.+$`）を 1 本登録し、
   その先を「テスト完了です」TTS → Disconnect に接続（通話が綺麗に終わるように）。
5. テスト発信し、STT で **既知フレーズ**を発話（推奨例: 「ちゅうしゃじょうはありますか」）。
   **何と言ったかを必ずメモ**しておく（ログ照合用）。
6. Brekeke ログを `"[in-probe"` で grep して全行回収 → 共有。
7. 手順 5 で発話したフレーズを OK で返した probe が「正解 API」。

> 非破壊（ログ出力と `setResult` のみ）。確定後は probe を撤去し、本体に差し替えること。

## 評価（ログの読み方）

| ログ出力 | 解釈 |
|---|---|
| `[in-probe A1-getModuleResult(name)] OK value=[駐車場はありますか] type=string` | ★本命的中。`getModuleResult(STT名)` が文字起こしを返す → `script.js` は CONFIG に STT 名を書くだけで入力取得が完成。**saveContext2DB 不要** |
| `[in-probe A1-...] OK value=[success] type=string` | `getModuleResult` は success 分岐の **label** を返している＝文字起こしは取れない。代替: その **1 本の STT だけ** に `saveContext2DB` を足し、B 系の system-variable で読む（全 STT への配線は不要） |
| `[in-probe A2-getModuleResult()] OK value=[駐車場はありますか]` | 引数なしで「直前モジュールの結果」を返す実装。これでも可（ただし配置依存になるので A1 を優先） |
| `[in-probe B1-sysvar(name)] OK value=[駐車場はありますか]` | STT 結果が同名 system variable として露出 → `$ivr.exec("system-variable",...)` で読める（A が label なら次善手） |
| `[in-probe C2-ex-ivr-keys] OK value=[ex.ivr keys: ...]` | STT 結果がどのキーに居るかの手掛かり。別経路設計の材料 |
| `... OK value=[null] type=object` | API は在るが STT 名では見えない（スコープ／命名違い） |
| 全件 EXCEPTION / null | 直読み経路が全滅 → `saveContext2DB`（対象 STT 1 本のみ）+ `system-variable` 読みに確定して進む |

## 期待される結果

- **第一候補**: `A1-getModuleResult(name)` が発話フレーズをそのまま返す。
  本フローは OpenAI を挟まないため、label 化される条件が薄く、文字起こしが返る可能性が高い。
- **保険**: 仮に `"success"` が返っても、対策は「FAQ 用 STT 1 本に saveContext2DB を足し、
  B 系 system-variable で読む」だけ。当初懸念の「全 STT への配線」は **どちらに転んでも不要**。

## 次のステップ

1. probe 結果から入力取得 API を確定。
2. `modules/faq_matcher/script.js` の CONFIG に
   `QUESTION_SOURCE_MODULE = "<STT名>"`（+ 必要なら読み取り方式フラグ）として反映。
3. 本体（`oracle.py` + `script.js`）の検索ロジック実装と受入テストへ。
