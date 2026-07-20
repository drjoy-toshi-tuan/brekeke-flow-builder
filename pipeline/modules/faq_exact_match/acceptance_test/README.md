# faq_exact_match 受入テストシナリオフロー

Python オラクル `../oracle.py` と同等のケースを Pattern 6 形式（チェイン式）で **1 コール内に直列実行**
する Brekeke flow。各ケースは本番 `script.js` の入力取得行 1 行だけをリテラル入力に差し替えるので、
**STT / AmiVoice 設定・`getModuleResult` 配線の不確実性から独立した「辞書引きロジックの決定論テスト」** になる
（`trim`・object/string 振り分け・`faqMap` 完全一致・`setObject` は本番 verbatim で実行）。

期待 jump が連続発火すれば PASS、いずれかで不一致なら対応 FAIL 終話で停止。

> **assert 強度**: ANSWER ケースの期待条件は「正解の答え本文そのもの」(`^<答え>$`)。
> 単に「ANSWER 分岐に行った」ではなく「**正しい回答本文を `setObject` 経路で返したか**」まで実機で検証する。
> 本番は `setResult` に `"ANSWER"`/`"NO_RESULT"` を出すが、受入では最終行を
> `$runner.setResult(result === "ANSWER" ? answer : result)` に差し替え、分岐と回答本文を 1 条件で同時に assert する。

## 同梱物

| ファイル | 役割 |
|---|---|
| `FaqExactMatchAcceptanceTest.bivr` | Brekeke にインポートする flow（**57 modules** = 28 ケース + 28 FAIL + 1 PASS）|
| `../build_test_flow_bivr.py` | 上記 bivr の生成器（`../script.js` をベースに `oracle.match()` で期待値を実測して条件化）|
| `README.md` | このファイル |

## カバーする 28 ケース（`oracle.match` で期待値実測）

| 区分 | 件数 | ID | 期待 |
|---|---|---|---|
| 完全一致 | 12 | EM-01〜EM-12 | ANSWER（回答本文一致まで）|
| trim（前後空白/タブ）| 2 | TR-01, TR-02 | ANSWER |
| object 入力 `{text:…}` | 2 | OB-01, OB-02 | ANSWER（`.text` 抽出 + trim）|
| 非マッチ（言い換え/部分/末尾記号欠落/無関係）| 5 | NF-01〜NF-05 | NO_RESULT |
| 空 / 空白のみ | 2 | EP-01, EP-02 | NO_RESULT |
| 継承プロパティ（堅牢化検証）| 5 | PT-01〜PT-05 | NO_RESULT |

> NF-05（`手の外科…可能ですか` 末尾 `。` なし）は EM-07（末尾 `。` あり）と対で、**完全一致が 1 文字単位**であることを示す。
> PT-01〜05（`toString`/`constructor`/`hasOwnProperty`/`__proto__`/`valueOf`）は `hasOwnProperty` 堅牢化が効いていることの確認ケース。

## フロー構造（チェイン式）

```
[テストEM-01_駐車場_完全一致]  var rawInput="駐車場はありますか";
   │ ^約33台分ございます…ご確認ください$ ──→ 次のケースへ (PASS)
   │ ^.*$                              ──→ [FAIL_EM-01_期待:ANSWER]
   ▼
[テストEM-02 …] → … → [テストPT-05_継承_valueOf] → ^NO_RESULT$ → [PASS_全件PASS]
```

## 実行手順

### 前提

- `../script.js` を改変していないこと（`faqMap` 含む）。変えたら `python ../build_test_flow_bivr.py` で bivr を作り直す。
- このモジュールは **Note も外部 API も使わない**（`faqMap` は script 埋め込み）。テナント側の事前準備は不要。

### Brekeke 投入

1. `FaqExactMatchAcceptanceTest.bivr` を Brekeke 管理画面で flow として import
2. テスト発信 or「フロー実行」で **1 コールだけ**実行
3. Brekeke ログ画面で結果を観察

### ログから結果判定

各ケースで下記が記録される（`$runner.getLogger().info`）:

```
[EM-01] kind=string input=駐車場はありますか
[EM-01] expected=ANSWER result=ANSWER answer=約33台分ございます。…
Module.exec() name=テストEM-02_面会時間_完全一致   ← 次ケースへ
```

**全件 PASS の判定**:
```
Module.exec() name=PASS_全件PASS
```
↑ この行が出れば 28 ケース全パス → 受入確定。

**いずれかで FAIL**:
```
Module.exec() name=FAIL_EM-08_期待:ANSWER
```
↑ ここで停止。直前の `[EM-08] expected=… result=… answer=…` ログで不一致内容が分かる。

### grep 推奨

```
grep -E '\[(EM|TR|OB|NF|EP|PT)-[0-9]+\]|Module\.exec\(\) name=(テスト|FAIL|PASS)' brekeke.log
```

## FAIL 時の切り分け

| 症状 | 主な疑い |
|---|---|
| ANSWER ケースが NO_RESULT で FAIL | `faqMap` のキーが script.js と不一致（全角/半角・句読点・末尾記号）。`script.js` を改変したのに bivr 未再生成 |
| ANSWER ケースで分岐は合うが条件不一致 | 回答本文 `a` が `script.js` と 1 文字でも違う（受入条件 `^答え$` に一致しない）|
| trim 系（TR/OB）が NO_RESULT で FAIL | Nashorn の `String.prototype.trim()` 挙動差（通常一致）|
| 継承プロパティ（PT）が ANSWER で FAIL | **`hasOwnProperty` 堅牢化が入っていない**（`script.js` が原版＝素の `faqMap[text]`）|
| Py と実機で判定がズレる | `script.js` を直したら `../test_oracle.py` と本 bivr を必ず両方再実行（オラクルが正本）|

## 既知の制約

- このフローは `script.js` の `faqMap`（54 件）での回帰確認用。`faqMap` を変えたら再生成すること。
- Brekeke 1 コール 1000 モジュール上限内（本 flow 57 modules）。
- 28 ケースのロジック判定は Python オラクル（`../test_oracle.py` 26/26 PASS）と整合。`OB-*` の入力形状ハンドリングは
  本受入フローでのみ検証（オラクルは text レベルを担保）。アルゴリズムの正しさはオラクル側で担保。
- `OpenAI_RAG` の **配線**（in-flow の `getModuleResult`）は P7 連結テストの責務。P6 は辞書引きの全ケース網羅が責務。
