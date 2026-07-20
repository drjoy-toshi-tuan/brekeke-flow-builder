---
name: gen-youken
description: Brekeke IVR用の用件判定スクリプト（intent classifier）をインタビュー形式で生成するスキル。ユーザーにIVRメニュー仕様をヒアリングし、ES5準拠のJavaScriptコード・テストケース・Jump Setting Regexを一気通貫で生成する。コードはtemplate.jsの構造（normalize→isRepeat→classifyByNumber→classifyByVerb→reconcile）を厳守し、生成後はNode.jsでテストを実行して100%パスを確認してから納品する。「用件判定スクリプト作って」「intent classifier生成」「IVRメニュー分岐スクリプト」「変更キャンセルその他の判定」「Brekeke用件スクリプト」などの依頼があれば必ずこのスキルを使うこと。既存スクリプトへのキーワード追加・バグ修正・option変更もこのスキルで対応する。
---

# 用件判定スクリプト生成（Brekeke IVR Intent Classifier）

インタビュー → コード生成 → テスト → Jump Setting Regex の一気通貫ワークフロー。
**コードはtemplate.jsの構造を厳守。メモリから書かない。**

> **📢 新標準（2026-07-16・2026-07-17 認定完了で scaffold 既定化）**: 用件判定の
> **`type: intent` は scaffold_generator.py の既定エンジンが v2**
> （`modules/intent_classifier_v2/`・oracle 49/49 + 実機P6 27/27 PASSで認定済み）に
> なった。設計書 YAML に `engine` を書かなくても、`options[]`（strong/weak keyword）
> があれば自動的に Evidence→Event→Rule 方式へ変換される（`/gen-intent-spec` skill で
> `intent_spec` を直接書けばより高精度）。複合文（「予約してるんだけど都合がつかない
> ので来月…」→ 変更）・否定（「キャンセルしないで」）・拮抗時の聞き返し（CLARIFY）に対応する。
> 本スキルの keyword 直結方式（v1・都度生成の未認定フリーフォームスクリプト）を使いたい
> 場合は設計書 YAML に **`engine: v1` を明示**すること（既存シナリオの段階移行用）。
> 正本: `docs/governance/intent-engine-v2-design.md`

---

## インタビューフロー（Step順・スキップ禁止）

### Step 1 — モジュール名
「STT inputモジュールの名前は何ですか？ (default: `用件`)」

### Step 2 — IVR発話テキスト
「IVRの案内文（全文）を教えてください。（number→intentのmappingを確認するため）」
例：「ご用件を、次の3つからお選びください。「１．変更」「２．キャンセル」「３．その他」」

### Step 3 — 選択肢数
`ask_user_input_v0` で選択させる：2 / 3 / 4 / 5+

### Step 4 — 各選択肢の詳細（Nループ）
各optionについて以下を一度に聞く：
- 番号（1, 2, 3...）
- Intent label（output値：変更 / キャンセル / 予約確認 / その他 等）
- STRONG or WEAK（次のStep 5で説明後に確認）
- 動詞キーワード（ユーザーが列挙 → guidelinesに基づき展開）

### Step 5 — STRONG / WEAK 判定
ユーザーに説明してから確認：
- **STRONG** = 具体的な動詞。他のoptionと重複しない（例：変更・キャンセル・確認）
- **WEAK** = catch-all。汎用キーワードで他optionの語が含まれうる（例：その他・新規予約）

デフォルトルール：`その他` または `新規予約` → WEAK。それ以外 → STRONG。

### Step 5.5 — Output仕様（**必ず両方確認**）

各スクリプトには2系統のoutputがある：

**(a) `classification`（setResult）** — Jump Setting分岐用のintent label
→「setResultで返すintentは各optionで何ですか？」（short label: 変更 / キャンセル 等）

**(b) `user_classification`（setObject）** — 次工程（TTS等）用の値
→「user_classificationは必要ですか？必要なら各intentに何をmapしますか？」

| ケース | setResult | setObject (user_classification) |
|--------|-----------|----------------------------------|
| デフォルト | short label（変更） | long label（外来予約の変更） |
| TTS特有 | 変更 | TTSで読み上げる完全文 |
| 不要 | 変更 | setResultと同じ、またはsetObject省略 |

⚠️ REPEAT / NO_RESULT は setObject を保存しない（intent確定時のみ保存）

確認用テーブルをユーザーに提示する：
| Intent (setResult) | user_classification (setObject) | 備考 |
|--------------------|----------------------------------|------|
| 変更 | 外来予約の変更 | TTS確認用 |
| キャンセル | 外来予約のキャンセル | |
| その他 | 入院、手術の変更、キャンセル | |

### Step 6 — Spec確認
以下のテーブルでユーザーに確認を取る：

| 番号 | 発音 | Output | Strong/Weak | Keywords |
|------|------|--------|-------------|---------|
| 1 | いち / 一 / 1番 | 変更 | Strong | 変更, へんこう, 変えたい... |
| 2 | に / 二 / 2番 | キャンセル | Strong | キャンセル, 取り消し... |
| 3 | さん / 三 / 3番 | その他 | Weak | 予約, 初診, 確認... |

「このspecで正しいですか？確認後にコード生成を始めます。」

### Step 7 — コード生成
1. `create_file` で `/home/claude/` にコードを書く
2. **下記のtemplate.js構造から開始し、セクション順を変えない**
3. `<MODULE_NAME>`・intent mapping・keyword regexをspecに合わせて置換
4. Step 5.5のspec通りにsetResult + setObject両方を実装
5. REPEAT/NO_RESULTはsetObjectを保存しない

### Step 8 — テストケース生成・実行
40〜60ケースを生成して `bash_tool` でNode.js実行。以下を必ずカバー：
- 純粋な番号バリエーション（1, 1番, 一番, いちばん, いちです, 1万）
- 単音番号+語尾（いち, に, さん, よん）
- 動詞のみ入力（各keywordグループ1例）
- **Reconcileケース**（1番+キャンセル, 3番+変更 等）
- もう一度 / もう一度+intentキーワード（**CRITICAL**: 後者はintentに行く）
- エッジケース（田中さんです, 予約に変更, 一日, 四時 → 誤検知してはいけない）
- NO_RESULTケース（空文字, わかりません, 天気）

100%パスするまでコードを修正してから次のStepに進む。

### Step 9 — Jump Setting Regex生成
**固定の並び順（厳守）：**
1. `^NO_RESULT$`
2. FALLBACK（negative lookahead）
3. `^REPEAT$`
4. 各intent（`^<INTENT_N>$`）

テーブルで出力：
| 順 | Branch | Regex | 遷移先 |
|----|--------|-------|--------|
| 1 | NO_RESULT | `^NO_RESULT$` | → [用件モジュール (retry)] |
| 2 | FALLBACK | `^(?!(変更\|キャンセル\|その他\|REPEAT\|NO_RESULT)$).*` | → [用件モジュール (retry)] |
| 3 | REPEAT | `^REPEAT$` | → [用件モジュール (retry)] |
| 4 | 変更 | `^変更$` | → [変更処理] |
| 5 | キャンセル | `^キャンセル$` | → [キャンセル処理] |
| 6 | その他 | `^その他$` | → [その他処理] |

コピペ用ブロックも出力する：
```
^NO_RESULT$
^(?!(変更|キャンセル|その他|REPEAT|NO_RESULT)$).*
^REPEAT$
^変更$
^キャンセル$
^その他$
```

### Step 10 — 納品
`/mnt/user-data/outputs/<classifier_name>.js` にコピーして `present_files` で共有。
最終サマリーに含めるもの：番号→intent→regexのmapping表 / サンプル入出力 / 処理した重要エッジケース / Jump Setting regexブロック

---

## ハードルール（コード生成時・絶対厳守）

| 禁止 | 理由 |
|------|------|
| テンプレートリテラル（バックティック） | Brekeke旧JSエンジン非対応 |
| `let` / `const` | ES5のみ、`var`を使う |
| アロー関数 | ES5のみ、`function() {}`を使う |
| `String/Array.prototype.includes` | `indexOf(...) !== -1` を使う |

| 必須 | 理由 |
|------|------|
| `$ivr.exec("save2db", ...)` ブロック | 永続化のため |
| `$ivr.exec` をtry/catchで囲む | サイレントfailのため |
| 単音番号バリエーションに `^...$` アンカー | 田中さん等の誤検知防止 |
| 「もう一度+intentキーワード」→ intentに遷移 | repeatではなくintentとして処理 |

---

## template.js（コード生成の起点・構造変更禁止）

```javascript
// =============================================================
// 1. 入力取得
// =============================================================
var classification = "NO_RESULT";
var rawInput = $runner.getModuleResult("<MODULE_NAME>");
var text = "";
if (rawInput && typeof rawInput === "object" && rawInput.text) {
    text = String(rawInput.text);
} else if (typeof rawInput === "string") {
    text = rawInput;
}
text = text == null ? "" : String(text).trim();


// =============================================================
// 2. 正規化
// =============================================================
function normalize(s) {
    if (!s) return "";
    var n = s;
    n = n.replace(/[\r\n\t]/g, "");
    // 全角数字 → 半角
    n = n.replace(/[０-９]/g, function(c) {
        return String.fromCharCode(c.charCodeAt(0) - 0xFF10 + 0x30);
    });
    // 全角英字 → 半角
    n = n.replace(/[Ａ-Ｚａ-ｚ]/g, function(c) {
        return String.fromCharCode(c.charCodeAt(0) - 0xFEE0);
    });
    // カタカナ → ひらがな
    n = n.replace(/[\u30A1-\u30F6]/g, function(c) {
        return String.fromCharCode(c.charCodeAt(0) - 0x60);
    });
    // 記号・空白すべて除去
    n = n.replace(/[\s、。,.\-_\/・:;！!？?「」『』（）\(\)　]/g, "");
    return n;
}


// =============================================================
// 3. repeat判定
// =============================================================
function hasRepeatMarker(n) {
    return (
        /(もう(いち|一)(ど|度|かい|回))/.test(n) ||
        /(もういっかい|もういっど)/.test(n) ||
        /(も(いち|一)(ど|度|かい|回))/.test(n) ||
        /(さいど(おねがい|お願い|きかせ|いって)?)/.test(n) ||
        /(再度(おねがい|お願い|きかせ|いって)?)/.test(n) ||
        /(まえ(に)?もど(って|る|して))/.test(n) ||
        /(前(に)?戻(って|る|して))/.test(n) ||
        /(きこえ(ない|ません|なかった|づらい))/.test(n) ||
        /(聞こえ(ない|ません|なかった|づらい))/.test(n) ||
        /(ききと(れない|れません|れなかった|りにくい))/.test(n) ||
        /(聞き取(れない|れません|れなかった|りにくい))/.test(n) ||
        /(くりかえ(し|して|しください))/.test(n) ||
        /(繰り返(し|して|しください))/.test(n)
    );
}

function hasIntentKeyword(n) {
    // ★ 各IVRのintentに合わせてキーワードを更新すること
    return /(<INTENT_KEYWORDS_HERE>)/.test(n);
}

function isRepeat(n) {
    if (!hasRepeatMarker(n)) return false;
    if (hasIntentKeyword(n)) return false;  // 「もう一度予約する」→ intent
    return true;
}


// =============================================================
// 4. 番号判定 (Phase A)
// =============================================================
var SUFFIX = "(です|だ|でお?ねがい(します)?|でお願い(します)?|でいい(です)?|がいい(です)?|おねがい(します)?|お願い(します)?|になります|のほう|に|ね|よ)?";

function classifyByNumber(rawText, normText) {
    if (rawText === "1" || normText === "1") return "<INTENT_1>";
    if (rawText === "2" || normText === "2") return "<INTENT_2>";
    if (rawText === "3" || normText === "3") return "<INTENT_3>";

    if (new RegExp("^(1|いち|イチ|一|ひとつ)" + SUFFIX + "$").test(normText)) return "<INTENT_1>";
    if (new RegExp("^(2|に|にい|にー|にぃ|二|ふたつ)" + SUFFIX + "$").test(normText)) return "<INTENT_2>";
    if (new RegExp("^(3|さん|さーん|さあん|三|みっつ)" + SUFFIX + "$").test(normText)) return "<INTENT_3>";

    var num1Re = /(^|[^0-9])(1[番万判版晩]|1ばん|いちばー?ん|一[番万判版晩])/;
    var num2Re = /(^|[^0-9])(2[番万判版晩位]|2ばん|にばー?ん|二[番万判版晩位])/;
    var num3Re = /(^|[^0-9])(3[番万判版晩]|3ばん|さんばー?ん|三[番万判版晩])/;

    if (num1Re.test(normText)) return "<INTENT_1>";
    if (num2Re.test(normText)) return "<INTENT_2>";
    if (num3Re.test(normText)) return "<INTENT_3>";

    return null;
}


// =============================================================
// 5. 内容判定 (Phase B)
// =============================================================
// 重要：STRONG intentを先に、WEAK（catch-all）を最後に
function classifyByVerb(n) {
    // --- <INTENT_1> (STRONG) ---
    if (/<KEYWORD_RE_1>/.test(n)) return "<INTENT_1>";

    // --- <INTENT_2> (STRONG) ---
    if (/<KEYWORD_RE_2>/.test(n)) return "<INTENT_2>";

    // --- <INTENT_3> (WEAK: catch-all) ---
    if (/<KEYWORD_RE_3>/.test(n)) return "<INTENT_3>";

    return null;
}


// =============================================================
// 6. 統合 (reconcile)
// =============================================================
function isStrongVerbIntent(intent) {
    return intent === "<STRONG_INTENT_1>"
        || intent === "<STRONG_INTENT_2>";
}

function reconcile(numIntent, verbIntent) {
    if (numIntent && verbIntent) {
        if (isStrongVerbIntent(verbIntent)) return verbIntent;  // verb強い → verb勝ち
        return numIntent;                                        // verb弱い → 番号勝ち
    }
    if (numIntent) return numIntent;
    if (verbIntent) return verbIntent;
    return "NO_RESULT";
}


// =============================================================
// 6.5 user_classification変換
// =============================================================
function toUserClassification(c) {
    if (c === "<INTENT_1>") return "<USER_CLASS_1>";
    if (c === "<INTENT_2>") return "<USER_CLASS_2>";
    if (c === "<INTENT_3>") return "<USER_CLASS_3>";
    return c;
}


// =============================================================
// 7. 判定パイプライン
// =============================================================
var normalized = normalize(text);

if (normalized.length === 0) {
    classification = "NO_RESULT";
} else if (isRepeat(normalized)) {
    classification = "REPEAT";
} else {
    var numIntent = classifyByNumber(text, normalized);
    var verbIntent = classifyByVerb(normalized);
    classification = reconcile(numIntent, verbIntent);
}


// =============================================================
// 8. 保存・出力
// =============================================================
if (classification !== "NO_RESULT" && classification !== "REPEAT") {
    var userClassification = toUserClassification(classification);

    var contextField = {
        contextName: "classification",
        displayType: "CLASSIFICATION",
        value: classification
    };
    try {
        $ivr.exec("save2db", "save", JSON.stringify({ contextField: contextField }));
    } catch (e) { /* silent */ }
    $runner.setObject("classification", classification);
    $runner.setObject("user_classification", userClassification);
}

$runner.setResult(classification);
```

---

## iterationモード（既存コードの修正依頼）

「キーワード追加」「バグ修正」「optionの変更」の場合：
- インタビューを最初からやり直さない
- ユーザーが共有した最新コードを起点に修正する
- 修正後はStep 8のテストを再実行して100%パスを確認してから納品

---

## 出力前チェック（必須）

- [ ] template.jsのセクション構造（1〜8）を保持しているか
- [ ] ES5ハードルール違反（let/const/アロー関数/includes/バックティック）がないか
- [ ] STRONG intentがclassifyByVerbでWEAKより先に定義されているか
- [ ] 「もう一度+intentキーワード」のケースが正しくintentに遷移するか
- [ ] REPEAT/NO_RESULTでsetObjectを保存していないか
- [ ] Jump Setting Regexの並び順がNO_RESULT→FALLBACK→REPEAT→intent群になっているか
- [ ] テストケースが100%パスしているか（コード納品前に必ず確認）

---

## キーワードリファレンス（classifyByVerb生成時に必ず参照）

### 変更（STRONG）

#### 標準表現
```
変更|変える|変えたい|変えます|変えてください|変えてほしい
|修正|訂正|見直し|調整|直したい
```

#### 動き・移動系
```
ずらしたい|ずらす|動かしたい|動かす|スライド
|組み替え|繰り上げ|繰り下げ
```

#### 時間調整系
```
延期|前倒し|早めたい|延ばしたい|伸ばしたい
```

#### 再予約系
```
再予約|取り直したい|入れ直したい
```

#### フレーズ系（STT出力の長い発話）
```
予約をずらしたい|日にちを変えたい|時間をずらしたい
```

#### STT誤認識パターン（変更の空耳）
```
偏向|返校|編工|変口|辺境|返却|銀行
```

#### よみがな
```
よやくへんこう|にっていへんこう
```

#### 生成するregexイメージ
```javascript
if (/(変更|へんこう|変え(たい|ます|て|てください|てほしい)|修正|訂正|見直し|調整|直したい
    |ずら(したい|す)|動か(したい|す)|スライド|組み替え|繰り上げ|繰り下げ
    |延期|前倒し|早めたい|(延|伸)ばしたい
    |再予約|取り直したい|入れ直したい
    |予約をずらしたい|日にちを変えたい|時間をずらしたい
    |偏向|返校|編工|変口|辺境|返却|銀行
    |よやくへんこう|にっていへんこう)/.test(n)) return "変更";
```

---

### 予約（WEAK / 新規予約のcatch-all）

#### STT誤認識パターン（予約の空耳）
```
新居|新規|お役|お薬|要約|契約
```

#### 注意
- 予約系キーワードはWEAKとして定義する（catch-all）
- STRONG intent（変更・キャンセル等）が先にマッチした場合は予約に来ない
- 「新居」「新規」等は予約の空耳であり、変更の空耳（銀行・返却等）と混同しないこと

#### 生成するregexイメージ
```javascript
// WEAK: classifyByVerbの最後に配置
if (/(予約|よやく|新居|新規|お役|お薬|要約|契約)/.test(n)) return "新規予約";
```
