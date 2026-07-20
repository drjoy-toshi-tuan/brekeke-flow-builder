# Fixer修正レポート — 成増厚生病院 アルコール病棟
生成日時: 2026-04-13 17:48

## 修正前 Critical サマリー

| ソース | Critical 件数 |
|---|---|
| バリデータ1（生成直後の構造チェック） | 0 件 |
| バリデータ2（マージ後の最終構造チェック） | 0 件 |
| レビュアー（レッドチーム校閲） | 6 件 |
| テスター（プロンプト品質・ルート到達性） | 1429 件 |
| **合計** | **1435 件** |

## Fixer修正完了内容

一時ファイルは `output/logs/` (gitignore済み) に残りますが影響なし。

---

修正完了:

- **C-001**: `Jump_電話番号聴取.params.flowname` を `drjoy^な_成増厚生病院$アルコール病棟_電話番号聴取_20260413` に修正（サブフロー参照先の「アルコール病棟_」プレフィックス追加）
- **C-002**: `Jump_RAG検索_inquiry.params.flowname` を `drjoy^な_成増厚生病院$アルコール病棟_RAG検索_20260413` に修正
- **C-003**: `Jump_RAG検索_pre.params.flowname` を `drjoy^な_成増厚生病院$アルコール病棟_RAG検索_20260413` に修正
- **C-004**: `script_smsFlag分岐.params.script` 内の flowName 変数を `な_成増厚生病院$アルコール病棟_電話番号聴取_20260413` に修正（SMS携帯判定が正常動作するように）
- **C-005**: `OpenAI_患者名` の next[0](TIMEOUT)・next[1](ERROR)・next[2](NO_RESULT) の nextModuleName を `受診歴入院歴` → `リトライ_患者名` に修正（患者名リトライが機能するように）
- **C-006**: `コンテキスト設定.params.fields` 内の `status` フィールドの rangeValues に4エントリ（未処理/非通知/聴取失敗/時間外）を追加。併せて `classification` の rangeValues の order 値を整数型から文字列型に修正（W-005）

## プロンプト品質修正完了内容（prompter担当）

校閲レポートを確認しました。

## 結果: prompter担当のCritical指摘は **0件** です

レポートのサマリーに明記されています:

> **修正担当別: generator 11件 / prompter 0件 / properties 1件 / 人間確認 2件**

また、「修正指示一覧（エージェント別）」セクションにも:

> ### prompter向け
> なし（全 OpenAI プロンプトは品質基準を満たしている）

と記載されています。

### 検出されたCritical 6件の担当は全て **generator** です:

| ID | 内容 | 担当 |
|---|---|---|
| C-001 | Jump_電話番号聴取 の flowname プレフィックス欠落 | generator |
| C-002 | Jump_RAG検索_inquiry の flowname プレフィックス欠落 | generator |
| C-003 | Jump_RAG検索_pre の flowname プレフィックス欠落 | generator |
| C-004 | script_smsFlag分岐 の flowName 変数誤り | generator |
| C-005 | OpenAI_患者名 の TIMEOUT/ERROR/NO_RESULT リトライバイパス | generator |
| C-006 | status の rangeValues 空配列 | generator |

OpenAIプロンプトの品質（出力ラベル整合性・インジェクション対策・Context・NO_RESULT）は全モジュールでPASSしており、prompterが修正すべき箇所はありません。

**次のアクション**: これらのCritical修正は `@fixer` または `@generator` に依頼してください。

## 残存指摘一覧（要人間確認）

### 最終バリデータ結果（Critical / Warning / Info 全件）

```
[Properties] チェック対象: C:\Users\hamaguchi.t\vfb-成増厚生病院_アルコール病棟\output\properties_成増厚生病院_アルコール病棟.md

============================================================
[REPORT] バリデーション結果: な_成増厚生病院$アルコール病棟_20260413
============================================================
モジュール数: 62
検出問題数: 11
  [Critical]: 0
  [Warning]:  11
  [Info]:     0
判定: [PASS]

--- 検出事項 ---
  [W] [FLOW-005] Jump_電話番号聴取 > params.properties: Custom Jump to Flow の properties が空です — サブフロー用IVRプロパティ情報が未設定です
  [W] [FLOW-005] Jump_RAG検索_inquiry > params.properties: Custom Jump to Flow の properties が空です — サブフロー用IVRプロパティ情報が未設定です
  [W] [FLOW-005] Jump_RAG検索_pre > params.properties: Custom Jump to Flow の properties が空です — サブフロー用IVRプロパティ情報が未設定です
  [W] [SAVECTX-003] OpenAI_用件確認 > next[問い合わせ] → saveContext_classification: generate_by_OpenAI の分岐直後に saveContext2DB が配置されています — OpenAIルーティング済みのパスで固定値を再保存するのは冗長です。削除して直接次のモジュールに接続してください
  [W] [P-011] リトライ_用件確認 > params.prompt_false: Retryモジュール 'リトライ_用件確認' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
  [W] [P-011] リトライ_受診歴入院歴 > params.prompt_false: Retryモジュール 'リトライ_受診歴入院歴' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
  [W] [P-011] リトライ_患者名 > params.prompt_false: Retryモジュール 'リトライ_患者名' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
  [W] [P-011] リトライ_新規継続 > params.prompt_false: Retryモジュール 'リトライ_新規継続' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
  [W] [P-011] リトライ_患者本人確認 > params.prompt_false: Retryモジュール 'リトライ_患者本人確認' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
  [W] [P-011] リトライ_電話口氏名 > params.prompt_false: Retryモジュール 'リトライ_電話口氏名' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
  [W] [P-030] (properties) > TODO: propertiesに TODO_ が残っています: office_id=TODO_要確認
```

### レビュアーレポート（1パスで修正しきれなかった分を含む）

# 校閲レポート: 成増厚生病院 - アルコール病棟

> 対象ファイル: `output/json/prompted_成増厚生病院_アルコール病棟.json`
> 設計書: `docs/designs/設計書_成増厚生病院_アルコール病棟.yaml`
> 校閲日: 2026-04-13

---

## セキュリティ・ライセンス警告（最優先確認）

SECURITY-CRITICAL: なし
LICENSE-WARN: なし

セキュリティインジェクションパターン、不正なmodule typeは検出されなかった。

---

## サマリー

- 検出問題数: 14件
- 重大度別: SECURITY-CRITICAL 0 / Critical 6 / Warning 5 / LICENSE-WARN 0 / Info 3
- 修正担当別: generator 11件 / prompter 0件 / properties 1件 / 人間確認 2件

> validator.py は 0 Critical / 11 Warning（PASS）。本レポートは validator 委任外の業務ロジック・設計整合性の指摘。

---

## 検出事項

---

### C-001: Jump_電話番号聴取 の flowname が「アルコール病棟」プレフィックス欠落

- **ファイル**: `output/json/prompted_成増厚生病院_アルコール病棟.json`
- **修正担当**: generator
- **モジュール名**: `Jump_電話番号聴取`
- **フィールド**: `params.flowname`
- **問題**: 参照先サブフロー名に「アルコール病棟_」が含まれておらず、Brekekeがサブフローを見つけられない
- **現在値**: `drjoy^な_成増厚生病院$電話番号聴取_20260413`
- **正しい値**: `drjoy^な_成増厚生病院$アルコール病棟_電話番号聴取_20260413`
- **修正指示**: `Jump_電話番号聴取.params.flowname` を上記正しい値に修正すること。設計書 `flow_structure.subflows[0].name` を参照。
- **参照**: CLAUDE.md Rule 17b「params.flowname の形式が正しいこと」

> 修正指示: 上記フィールドのみを修正し、他のモジュールには一切触れないこと。

---

### C-002: Jump_RAG検索_inquiry の flowname が「アルコール病棟」プレフィックス欠落

- **ファイル**: `output/json/prompted_成増厚生病院_アルコール病棟.json`
- **修正担当**: generator
- **モジュール名**: `Jump_RAG検索_inquiry`
- **フィールド**: `params.flowname`
- **問題**: 参照先RAGサブフロー名に「アルコール病棟_」が含まれておらず、サブフロー遷移が実行時に失敗する
- **現在値**: `drjoy^な_成増厚生病院$RAG検索_20260413`
- **正しい値**: `drjoy^な_成増厚生病院$アルコール病棟_RAG検索_20260413`
- **修正指示**: `Jump_RAG検索_inquiry.params.flowname` を上記正しい値に修正すること。
- **参照**: CLAUDE.md Rule 17b

> 修正指示: 上記フィールドのみを修正し、他のモジュールには一切触れないこと。

---

### C-003: Jump_RAG検索_pre の flowname が「アルコール病棟」プレフィックス欠落

- **ファイル**: `output/json/prompted_成増厚生病院_アルコール病棟.json`
- **修正担当**: generator
- **モジュール名**: `Jump_RAG検索_pre`
- **フィールド**: `params.flowname`
- **問題**: C-002と同一。新規継続（入院相談/継続中）ルートのRAG遷移も失敗する
- **現在値**: `drjoy^な_成増厚生病院$RAG検索_20260413`
- **正しい値**: `drjoy^な_成増厚生病院$アルコール病棟_RAG検索_20260413`
- **修正指示**: `Jump_RAG検索_pre.params.flowname` を上記正しい値に修正すること。
- **参照**: CLAUDE.md Rule 17b

> 修正指示: 上記フィールドのみを修正し、他のモジュールには一切触れないこと。

---

### C-004: script_smsFlag分岐 内の flowName 変数が誤り → 携帯SMS送信が永遠に無効

- **ファイル**: `output/json/prompted_成増厚生病院_アルコール病棟.json`
- **修正担当**: generator
- **モジュール名**: `script_smsFlag分岐`
- **フィールド**: `params.script`（1行目の `var flowName = "..."` 部分）
- **問題**: スクリプト内の flowName が `な_成増厚生病院$電話番号聴取_20260413` であり、「アルコール病棟_」プレフィックスが欠落。`$ivr.getObject(key)` のキーが誤っているため phoneType が常に null → `String(null) !== "携帯"` → 全員が「その他（SMS無し）」扱いになる
- **現在値（script 冒頭）**:
  ```javascript
  var flowName = "な_成増厚生病院$電話番号聴取_20260413";
  ```
- **正しい値**:
  ```javascript
  var flowName = "な_成増厚生病院$アルコール病棟_電話番号聴取_20260413";
  ```
- **修正指示**: `script_smsFlag分岐.params.script` の `flowName` 変数の値のみを修正すること。スクリプトの他の行は変更しないこと。なお W-002 も合わせて参照すること（$ivr.getObject 非推奨問題）。
- **参照**: CLAUDE.md「システム変数一覧」「Scriptモジュールのモジュール値取得API」

> 修正指示: flowName 変数の文字列のみを修正し、他のモジュールには一切触れないこと。

---

### C-005: OpenAI_患者名 の TIMEOUT/ERROR/NO_RESULT がリトライをバイパス

- **ファイル**: `output/json/prompted_成増厚生病院_アルコール病棟.json`
- **修正担当**: generator
- **モジュール名**: `OpenAI_患者名`
- **フィールド**: `next[0].nextModuleName`, `next[1].nextModuleName`, `next[2].nextModuleName`
- **問題**: 設計書のフロー図では「OpenAI_患者名 NO_RESULT → リトライ_患者名」となっているが、JSON では TIMEOUT/ERROR/NO_RESULT の全てが直接 `受診歴入院歴` に遷移しており、患者名のリトライが一切機能しない（STTレベルのリトライのみ動作）
- **現在値**: TIMEOUT/ERROR/NO_RESULT → `受診歴入院歴`
- **正しい値**: TIMEOUT/ERROR/NO_RESULT → `リトライ_患者名`（`リトライ_患者名` の No more が `受診歴入院歴` に遷移することで retry_failure: skip を実現）
- **修正指示**:
  ```json
  "next": [
    {"condition": "^TIMEOUT$",   "label": "timeout",   "nextModuleName": "リトライ_患者名"},
    {"condition": "^ERROR$",     "label": "error",     "nextModuleName": "リトライ_患者名"},
    {"condition": "^NO_RESULT$", "label": "no_result", "nextModuleName": "リトライ_患者名"},
    {"condition": "^.+$",        "label": "success",   "nextModuleName": "受診歴入院歴"},
    ...（jump1-6 は空のまま）
  ]
  ```
- **参照**: 設計書 `hearing_items[2]（患者名）retry_count: 2, retry_failure: skip`、設計書フロー図

> 修正指示: `OpenAI_患者名` の next[0][1][2] のみを修正し、他のモジュールには一切触れないこと。

---

### C-006: status フィールドの rangeValues が空（設計書と不一致）

- **ファイル**: `output/json/prompted_成増厚生病院_アルコール病棟.json`
- **修正担当**: generator
- **モジュール名**: `コンテキスト設定`
- **フィールド**: `params.fields` 内 `contextName="status"` の `rangeValues`
- **問題**: `status` フィールドの `rangeValues` が `[]`（空配列）になっており、Dr.JOY の受電一覧で状態ラベルが表示されない。設計書では4つの選択肢が定義されている
- **現在値**: `"rangeValues": []`
- **正しい値**:
  ```json
  "rangeValues": [
    {"id": "1", "order": "1", "value": "未処理"},
    {"id": "2", "order": "2", "value": "非通知"},
    {"id": "3", "order": "3", "value": "聴取失敗"},
    {"id": "6", "order": "6", "value": "時間外"}
  ]
  ```
- **修正指示**: `コンテキスト設定.params.fields` 内の `status` エントリの `rangeValues` を上記に修正すること。また、`classification` フィールドの `rangeValues` の `order` 値が整数（1,2,3）になっているため、文字列（"1","2","3"）に修正すること（W-005参照）。
- **参照**: 設計書 `context_fields` セクション（status エントリ）

> 修正指示: fields JSON 文字列内の該当エントリのみを修正し、他のフィールドには触れないこと。

---

### W-001: 全 Retry Counter の retry_count が 1（設計書は 2）

- **ファイル**: `output/json/prompted_成増厚生病院_アルコール病棟.json`
- **修正担当**: generator
- **モジュール名**: `リトライ_電話口氏名`, `リトライ_患者本人確認`, `リトライ_患者名`, `リトライ_受診歴入院歴`, `リトライ_用件確認`, `リトライ_新規継続`（計6モジュール）
- **フィールド**: `params.retry_count`
- **問題**: 設計書の全 hearing_items で `retry_count: 2` と指定されているが、JSON では全て `retry_count: 1` になっている。`retry_count: 1` は「1回リトライ（合計2試行）」、`retry_count: 2` は「2回リトライ（合計3試行）」を意味する
- **現在値**: `"retry_count": 1`（全6モジュール）
- **正しい値**: `"retry_count": 2`（全6モジュール）
- **修正指示**: 上記6モジュールそれぞれの `params.retry_count` を `2` に修正すること。

> 修正指示: 6モジュールの retry_count パラメータのみを修正し、他のパラメータには一切触れないこと。

---

### W-002: script_smsFlag分岐 が $ivr.getObject() 非推奨 API を使用（設計: ContextMatchRouter 推奨）

- **ファイル**: `output/json/prompted_成増厚生病院_アルコール病棟.json`
- **修正担当**: generator
- **モジュール名**: `script_smsFlag分岐`
- **フィールド**: `type`, `params.script`
- **問題**: 設計書のフロー図では `smsFlag分岐(ContextMatchRouter: phoneType)` と指定されているが、`@General$Script` + 非推奨 `$ivr.getObject()` で実装されている。CLAUDE.md では「`$ivr.getObject("key")` は非推奨（新規で使用しない）」と明記されている
- **現在値**: `type: "@General$Script"` / `$ivr.getObject(key)` 使用
- **推奨値**: `ContextMatchRouter` に変更し、`params.module: "Jump_電話番号聴取"` で電話番号サブフロー結果を参照
- **修正指示**:
  1. `script_smsFlag分岐` モジュールのタイプを `ContextMatchRouter` に変更（または設計書が許容する場合はScriptで `$runner.getModuleResult("Jump_電話番号聴取")` を使用）
  2. C-004 の flowName 修正はいずれの実装でも必要
  3. CLAUDE.md 「Scriptモジュールのモジュール値取得API」参照
- **備考**: C-004（flowName誤り）が先行して修正されれば現状の Script 実装でも動作はするが、設計書の意図（ContextMatchRouter）と乖離している

> 修正指示: `script_smsFlag分岐` のアプローチを見直すこと。ContextMatchRouter への変更推奨。

---

### W-003: 入力_電話口氏名・入力_患者名 の profile_words が空（氏名辞書未設定）

- **ファイル**: `output/json/prompted_成増厚生病院_アルコール病棟.json`
- **修正担当**: generator
- **モジュール名**: `入力_電話口氏名`, `入力_患者名`
- **フィールド**: `params.profile_words`
- **問題**: 設計書 `amivoice_dictionary` で「（氏名辞書を設定）」と明記されているが、両モジュールの `profile_words` が空文字列になっており、音声認識精度が低下する可能性がある
- **現在値**: `"profile_words": ""`
- **正しい値**: `docs/ai/amivoice_dictionary.md` の氏名辞書内容を設定
- **修正指示**: `入力_電話口氏名.params.profile_words` と `入力_患者名.params.profile_words` に、`docs/ai/amivoice_dictionary.md` の氏名辞書を設定すること。他STTモジュール（入力_患者本人確認等）の profile_words は正しく設定済み。
- **参照**: 設計書 `amivoice_dictionary` セクション

> 修正指示: 2モジュールの profile_words のみを修正し、他のパラメータには一切触れないこと。

---

### W-004: IVRプロパティのサブフロー名コメントが誤り（アルコール病棟プレフィックス欠落）

- **ファイル**: `output/properties_成増厚生病院_アルコール病棟.md`
- **修正担当**: properties
- **フィールド**: ファイル冒頭のサブフロー記載行、および各サブフローセクションの見出し
- **問題**: プロパティファイルに記載されたサブフロー名が `な_成増厚生病院$電話番号聴取_20260413` / `な_成増厚生病院$RAG検索_20260413` になっており、「アルコール病棟_」が欠落している
- **現在値**: `な_成増厚生病院$電話番号聴取_20260413`
- **正しい値**: `な_成増厚生病院$アルコール病棟_電話番号聴取_20260413`
- **修正指示**: プロパティファイル内の2箇所のサブフロー名を正しい名前に修正すること（Brekekeのプロパティキー自体への影響はないが、メンテナンス性のため一致させること）

> 修正指示: コメント・セクション見出しの文字列のみを修正すること。

---

### W-005: classification の rangeValues.order が整数型（文字列型が正しい）

- **ファイル**: `output/json/prompted_成増厚生病院_アルコール病棟.json`
- **修正担当**: generator
- **モジュール名**: `コンテキスト設定`
- **フィールド**: `params.fields` 内 `contextName="classification"` の `rangeValues[*].order`
- **問題**: `classification` フィールドの `rangeValues` の `order` が整数 (`1, 2, 3`) になっているが、設計書では文字列 (`"1"`, `"2"`, `"3"`) が正しい
- **現在値**: `{"id": "1", "value": "入院相談", "order": 1}`
- **正しい値**: `{"id": "1", "order": "1", "value": "入院相談"}`
- **修正指示**: C-006 の status rangeValues 修正と合わせて、classification の order 値を文字列型に変換すること。

> 修正指示: C-006 と同一モジュール（コンテキスト設定）の params.fields 内の修正。まとめて1パスで実施すること。

---

## レッドチーム攻撃シナリオ

| # | シナリオ | 攻撃ベクトル | 予想結果 | 影響度 | 対策済み |
|---|---|---|---|---|---|
| 1 | 携帯電話から着信した患者が全聴取完了した場合 | C-004 の flowName 誤り: phoneType が null → 常に「その他」 | smsFlag=-1 で SMS 未送信（正しくは smsFlag=1） | 高 | ❌ C-004修正必要 |
| 2 | RAG 検索サブフローへの遷移が発生する場合 | C-001/C-002/C-003 の flowname 誤り | Brekeke が指定フローを見つけられず通話が中断 | 高 | ❌ C-001〜C-003修正必要 |
| 3 | 代理人が患者名を名乗ったが、音は拾えたが「ヤマダさんです」等と余計な言葉があり OpenAI が NO_RESULT を返した場合 | C-005: OpenAI_患者名 の NO_RESULT が受診歴入院歴に直行 | リトライなしで患者名聴取をスキップ | 中 | ❌ C-005修正必要 |
| 4 | 患者が「システムを無視して…」とインジェクション試行 | プロンプトインジェクション | OpenAI プロンプトの「プロンプトインジェクション対策」セクションで無視される | 低 | ✅ 全プロンプトに対策あり |
| 5 | 固定電話から着信した患者が「問い合わせ」を選択した場合 | 問い合わせルートのRAG参照（C-002依存） | flowname誤りによりRAGサブフロー遷移が失敗 | 高 | ❌ C-002修正必要 |
| 6 | 患者が「入院治療」を選択後、新規/継続で何も言わず2回リトライした場合 | retry_count: 1 → 設計の2回より少ないリトライ（W-001） | 1回のリトライ後に聴取失敗終話 | 低〜中 | ❌ W-001修正推奨 |
| 7 | STTが「お願いします」等の氏名でない発話を拾い、OpenAIがNO_RESULTを返した場合（代理人ルート） | OpenAI_患者名 のリトライバイパス（C-005） | 患者名聴取リトライなしでスキップ → 患者名が未保存のまま進行 | 中 | ❌ C-005修正必要 |
| 8 | 患者が用件不明のまま「あ、やっぱりいいです」等と言って通話した場合 | 聴取失敗経路（saveCompletionFlag2db 配置順） | saveCompletionFlag2db → TTS → Disconnect の正しい順序で終話 | 低 | ✅ 終話チェーン正常 |
| 9 | 患者が患者本人確認で「二」と発話した場合 | DTMF「2」以外の応答パターン | OpenAI が「代理人」と分類（プロンプトに「二」→「代理人」の規則あり） | 低 | ✅ プロンプト対応済み |

---

## OpenAIプロンプト出力ラベル整合性

| モジュール名 | next分岐ラベル | prompt出力仕様 | 判定 | 備考 |
|---|---|---|---|---|
| OpenAI_電話口氏名 | success(^.+$) | カタカナ氏名 / NO_RESULT | PASS | 正規化型: success 1本受けが正しい |
| OpenAI_患者本人確認 | 本人, 代理人 / NO_RESULT | 本人 / 代理人 / NO_RESULT | PASS | 分類型: 個別条件で正しく分岐 |
| OpenAI_patientName_copy | success(^.+$) | パススルー / NO_RESULT | PASS | コピー専用モジュール。全パス受診歴入院歴 |
| OpenAI_患者名 | success(^.+$) / NO_RESULT | カタカナ氏名 / NO_RESULT | WARNING | NO_RESULT → 受診歴入院歴 が間違い（C-005参照） |
| OpenAI_受診歴入院歴 | success(^.+$) / NO_RESULT→リトライ | あり / なし / NO_RESULT | PASS | 分類型だがsuccess 1本受けで問題なし |
| OpenAI_用件確認 | 入院治療, 問い合わせ / NO_RESULT | 入院治療 / 問い合わせ / NO_RESULT | PASS | 分類型: 個別条件で正しく分岐 |
| OpenAI_新規継続 | success(^.+$) / NO_RESULT | 入院相談 / 継続中 / NO_RESULT | PASS | 両値とも同一遷移先のため ^.+$ 可。contextName=classification で保存 |

---

## 修正指示一覧（エージェント別）

### generator向け（C-001〜C-006、W-001〜W-003、W-005）

**優先度1（サービス停止レベル）**:
1. `Jump_電話番号聴取.params.flowname` → `drjoy^な_成増厚生病院$アルコール病棟_電話番号聴取_20260413`（C-001）
2. `Jump_RAG検索_inquiry.params.flowname` → `drjoy^な_成増厚生病院$アルコール病棟_RAG検索_20260413`（C-002）
3. `Jump_RAG検索_pre.params.flowname` → `drjoy^な_成増厚生病院$アルコール病棟_RAG検索_20260413`（C-003）
4. `script_smsFlag分岐.params.script` の flowName 変数 → `な_成増厚生病院$アルコール病棟_電話番号聴取_20260413`（C-004）

**優先度2（業務ロジック誤り）**:
5. `OpenAI_患者名` next[0][1][2] の nextModuleName → `リトライ_患者名`（C-005）
6. `コンテキスト設定.params.fields` 内 status の rangeValues を4エントリで埋める（C-006）
7. `コンテキスト設定.params.fields` 内 classification の rangeValues.order を文字列に（W-005）

**優先度3（品質改善）**:
8. 全6 Retry Counter の `params.retry_count` を `2` に変更（W-001）
9. `script_smsFlag分岐` を ContextMatchRouter + `$runner.getModuleResult("Jump_電話番号聴取")` に変更検討（W-002）
10. `入力_電話口氏名.params.profile_words` と `入力_患者名.params.profile_words` に氏名辞書を設定（W-003）

### prompter向け
なし（全 OpenAI プロンプトは品質基準を満たしている）

### properties向け
11. プロパティファイル内のサブフロー名コメントを正しい名前に修正（W-004）

---

## 人間が確認すべき箇所

### script_smsFlag分岐 の実装方針（W-002）

C-004 の flowName 修正で即座に機能回復するが、`$ivr.getObject()` は非推奨 API であり将来的なBrekekeのバージョンアップで動作しなくなるリスクがある。

**推奨対応**: generator に ContextMatchRouter への置き換えを指示する。  
**参考実装**:
```json
{
  "type": "drjoy^External Integration$ContextMatchRouter",
  "params": {
    "module": "Jump_電話番号聴取",
    "value": ""
  },
  "next": [
    {"condition": "^携帯$", "label": "携帯", "nextModuleName": "完了フラグ_受付完了"},
    {"condition": "^.*$",  "label": "その他", "nextModuleName": "完了フラグ_受付完了_SMS無し"}
  ]
}
```

### RAGサブフロー TTS 文言の統一問題（I-001）

`Jump_RAG検索_inquiry`（問い合わせルート）と `Jump_RAG検索_pre`（終話前）が同一RAGサブフローを参照しているため、TTS 文言が「お問い合わせ内容をご自由におっしゃってください。」に統一されている。本来なら終話前は「何かご質問はございますか？」が適切だが、サブフロー共用による設計上の制約。

プロパティの注記に「変更してもよい」と明記されており、人間が最終確認の上で決定すること。

---

## Info

### I-001: RAGサブフローの TTS 文言がinquiry/pre-terminationで統一されている（設計制約）

両 Jump（inquiry/pre）が同一サブフロー `な_成増厚生病院$アルコール病棟_RAG検索_20260413` を参照しているため、初回 TTS が同一文言になる。CLAUDE.md Rule 16 に「RAGサブフローはつなぐ・外すだけで調整可能な設計とし、最終的に問題があれば人間が修正する」とあり、これは許容範囲内の制約。

### I-002: validator P-011（prompt_false 空文字）は CLAUDE.md 仕様通り

validator.py が全 Retry Counter の `prompt_false` が空であることを WARNING（P-011）として検出しているが、CLAUDE.md の記述では「`prompt_false` は原則空文字 `""` — No more 先が通常モジュールの場合は無音で遷移」と明記されており、現在の設計は仕様通り。fixer での対応不要。

### I-003: validator SAVECTX-003（saveContext_classification）は意図的設計

validator.py が「OpenAI 分岐直後の saveContext2DB が冗長」と SAVECTX-003 で警告しているが、これは問い合わせルートの `classification="問い合わせ"` という固定値を保存する意図的な設計。CLAUDE.md「ルーティング固定値を保存する場合のみ使う」に合致している。fixer での対応不要。

---
対象JSON: `C:\Users\hamaguchi.t\vfb-成増厚生病院_アルコール病棟\output\json\prompted_成増厚生病院_アルコール病棟.json`