# Fixer修正レポート — 蘇生会総合病院 診療
生成日時: 2026-04-10 20:21

## 修正前 Critical サマリー

| ソース | Critical 件数 |
|---|---|
| バリデータ1（生成直後の構造チェック） | 0 件 |
| バリデータ2（マージ後の最終構造チェック） | 0 件 |
| レビュアー（レッドチーム校閲） | 6 件 |
| テスター（プロンプト品質・ルート到達性） | 4 件 |
| **合計** | **10 件** |

## Fixer修正完了内容

全検証が完了しました。

---

修正完了:
- **C-001**: 6つのCustom Jump to Flowモジュール（Jump_氏名聴取 / Jump_診察券番号聴取 / Jump_生年月日聴取 / Jump_電話番号聴取 / Jump_RAG_問合 / Jump_RAG_最終）の `params.flowname` を `drjoy^Jump_to_flow$` → `drjoy^蘇生会総合病院$` に修正
- **C-002**: `終話分岐` ContextMatchRouterの params を `contextName1/2` → `module1Name/module2Name` + `module1Value1〜10/module2Value1〜10` 形式に全面置換、`next[0].condition` を `^キャンセル$` → `^1$` に修正
- **C-003**: `変更_歯科判定` ContextMatchRouterの params を同様に全面置換、`next[0].condition` を `^歯科口腔外科$` → `^1$` に修正
- **C-004**: `完了フラグ_代表案内_診療科` の `params.status` を `"7"` → `"2"` に修正
- **C-005**: `完了フラグ_健康増進` の `params.status` を `"7"` → `"2"` に修正
- **C-006**: 全14リトライモジュールの `params.retry_count` を `"1"` → `"2"` に修正（リトライ_旧姓 / リトライ_診療科 / リトライ_用件 / リトライ_受診歴 / リトライ_紹介状 / リトライ_症状1 / リトライ_医師指定 / リトライ_症状2 / リトライ_変更_予約日 / リトライ_変更_希望時期 / リトライ_残薬 / リトライ_キャンセル_予約日 / リトライ_キャンセル理由 / リトライ_確認内容）

**Tester R-2 (4件)**: C-001のflowname修正により解消（broken_refの原因がグループ名誤りだったため）

**スキップした指摘**: 「修正担当: prompter」の指摘なし（全Critical修正済み）

## プロンプト品質修正完了内容（prompter担当）

校閲レポートを確認しました。

## 結果: prompter担当のCritical指摘は **0件** です

レポートのサマリーに明記されています:

> **修正担当別**: generator 12件 / prompter **0件** / properties 0件 / 人間確認 1件

また、修正指示一覧のprompterセクションにも:

> ### prompter向け
> **なし（全プロンプトは品質基準4本柱を満たしている）**

さらに、OpenAIプロンプト出力ラベル整合性チェックでも全14モジュールが **PASS** となっています。

---

**対応不要の理由**: 今回の校閲で検出されたCritical 6件（C-001〜C-006）は全て **generator担当** の構造・設定の問題です:

| タグ | 内容 | 担当 |
|---|---|---|
| C-001 | Jump to Flow の flowname グループ名誤り | generator |
| C-002 | 終話分岐 ContextMatchRouter params/next誤り | generator |
| C-003 | 変更_歯科判定 ContextMatchRouter params/next誤り | generator |
| C-004 | 完了フラグ_代表案内_診療科 status値誤り | generator |
| C-005 | 完了フラグ_健康増進 status値誤り | generator |
| C-006 | 全14リトライモジュール retry_count誤り | generator |

これらの修正は `@fixer` または `@generator` の担当範囲です。prompterとして変更すべき `params.prompt` はありません。

## 残存指摘一覧（要人間確認）

### 最終バリデータ結果（Critical / Warning / Info 全件）

```
============================================================
[REPORT] バリデーション結果: 蘇生会総合病院$診療_20260410
============================================================
モジュール数: 116
検出問題数: 7
  [Critical]: 0
  [Warning]:  7
  [Info]:     0
判定: [PASS]

--- 検出事項 ---
  [W] [LAYOUT-003] (flow) > layout: フローが横並び（水平）に配置されています （x範囲:5400px, y範囲:7000px）— 主経路はy軸方向（上から下）に配置してください
  [W] [FLOW-005] Jump_氏名聴取 > params.properties: Custom Jump to Flow の properties が空です — サブフロー用IVRプロパティ情報が未設定です
  [W] [FLOW-005] Jump_診察券番号聴取 > params.properties: Custom Jump to Flow の properties が空です — サブフロー用IVRプロパティ情報が未設定です
  [W] [FLOW-005] Jump_生年月日聴取 > params.properties: Custom Jump to Flow の properties が空です — サブフロー用IVRプロパティ情報が未設定です
  [W] [FLOW-005] Jump_電話番号聴取 > params.properties: Custom Jump to Flow の properties が空です — サブフロー用IVRプロパティ情報が未設定です
  [W] [FLOW-005] Jump_RAG_問合 > params.properties: Custom Jump to Flow の properties が空です — サブフロー用IVRプロパティ情報が未設定です
  [W] [FLOW-005] Jump_RAG_最終 > params.properties: Custom Jump to Flow の properties が空です — サブフロー用IVRプロパティ情報が未設定です
```

### レビュアーレポート（1パスで修正しきれなかった分を含む）

# 校閲レポート: 蘇生会総合病院 - 診療

- **対象ファイル**: `output/json/prompted_蘇生会総合病院_診療.json`
- **設計書**: `docs/designs/設計書_蘇生会総合病院_診療.yaml`
- **校閲日**: 2026-04-10
- **校閲者**: reviewer (v3 / Red Team)

---

## セキュリティ・ライセンス警告（最優先確認）

なし（セキュリティ上の問題は検出されなかった）

---

## サマリー

- **検出問題数**: 13件
- **重大度別**: SECURITY-CRITICAL 0 / Critical 6 / Warning 6 / LICENSE-WARN 0 / Info 1
- **修正担当別**: generator 12件 / prompter 0件 / properties 0件 / 人間確認 1件

---

## 検出事項

---

### C-001: Custom Jump to Flow 全6モジュール — flowname のグループ名が誤り

- **ファイル**: `output/json/prompted_蘇生会総合病院_診療.json`
- **修正担当**: generator
- **モジュール名**: `Jump_氏名聴取` / `Jump_診察券番号聴取` / `Jump_生年月日聴取` / `Jump_電話番号聴取` / `Jump_RAG_問合` / `Jump_RAG_最終`
- **フィールド**: `params.flowname`
- **問題**: グループ名が `Jump_to_flow` になっており、Brekeke がサブフローを発見できない（実行時にサブフロー未発見エラー）
- **現在値**: `"drjoy^Jump_to_flow$氏名聴取_20260410"` (他5モジュールも同様)
- **正しい値**: `"drjoy^蘇生会総合病院$氏名聴取_20260410"` (グループ名を `蘇生会総合病院` に修正)
- **各モジュールの修正前後**:

| モジュール名 | 現在値 | 正しい値 |
|---|---|---|
| Jump_氏名聴取 | `drjoy^Jump_to_flow$氏名聴取_20260410` | `drjoy^蘇生会総合病院$氏名聴取_20260410` |
| Jump_診察券番号聴取 | `drjoy^Jump_to_flow$診察券番号聴取_20260410` | `drjoy^蘇生会総合病院$診察券番号聴取_20260410` |
| Jump_生年月日聴取 | `drjoy^Jump_to_flow$生年月日聴取_20260410` | `drjoy^蘇生会総合病院$生年月日聴取_20260410` |
| Jump_電話番号聴取 | `drjoy^Jump_to_flow$電話番号聴取_20260410` | `drjoy^蘇生会総合病院$電話番号聴取_20260410` |
| Jump_RAG_問合 | `drjoy^Jump_to_flow$RAG検索_20260410` | `drjoy^蘇生会総合病院$RAG検索_20260410` |
| Jump_RAG_最終 | `drjoy^Jump_to_flow$RAG検索_20260410` | `drjoy^蘇生会総合病院$RAG検索_20260410` |

- **修正指示**: 上記6モジュールの `params.flowname` のみ修正し、他フィールドには一切触れないこと。
- **参照**: `docs/brekeke/モジュール詳細設定ガイド_1.md` §9.1 Custom Jump to Flow

> 修正指示: `params.flowname` のみ修正すること。next/subs/layout への変更は禁止。

---

### C-002: `終話分岐` ContextMatchRouter — params 名誤り＋next条件誤り

- **ファイル**: `output/json/prompted_蘇生会総合病院_診療.json`
- **修正担当**: generator
- **モジュール名**: `終話分岐`
- **フィールド**: `params` 全体 / `next[0].condition`, `next[1].condition`
- **問題**: ContextMatchRouter の正しいparams名は `module1Name`/`module2Name`/`module1Value1`〜`module2Value10` だが、`contextName1`/`contextName2` という誤ったキー名が使われている。また、next[] の condition が `^キャンセル$` 等の文字列マッチになっているが、ContextMatchRouter は組み合わせ番号（`^1$`, `^2$` 等）を返すため完全に機能しない。
- **現在値**:
```json
"params": {
  "contextName1": "OpenAI_用件",
  "contextName2": "OpenAI_用件"
}
"next": [
  {"condition": "^キャンセル$", "label": "キャンセル", "nextModuleName": "完了フラグ_キャンセル完了"},
  {"condition": "^.*$", "label": "その他", "nextModuleName": "完了フラグ_汎用受付完了"}
]
```
- **正しい値**:
```json
"params": {
  "module1Name": "OpenAI_用件",
  "module2Name": "OpenAI_用件",
  "module1Value1": "キャンセル",
  "module2Value1": "キャンセル",
  "module1Value2": "", "module2Value2": "",
  ... (module1Value3〜10, module2Value3〜10 はすべて "")
}
"next": [
  {"condition": "^1$", "label": "キャンセル", "nextModuleName": "完了フラグ_キャンセル完了"},
  {"condition": "^.*$", "label": "その他", "nextModuleName": "完了フラグ_汎用受付完了"}
]
```
- **修正指示**: `params` を `module1Name`/`module2Name` + `module1Value1`〜`module1Value10`/`module2Value1`〜`module2Value10` の形式に全面置換し、next[0].condition を `^1$` に修正すること。
- **参照**: `docs/brekeke/モジュール詳細設定ガイド_1.md` §8.1 ContextMatchRouter

> 修正指示: `params` と `next[0].condition` のみ修正すること。他モジュールには触れないこと。

---

### C-003: `変更_歯科判定` ContextMatchRouter — params 名誤り＋next条件誤り

- **ファイル**: `output/json/prompted_蘇生会総合病院_診療.json`
- **修正担当**: generator
- **モジュール名**: `変更_歯科判定`
- **フィールド**: `params` 全体 / `next[0].condition`
- **問題**: C-002 と同様。`contextName1`/`contextName2` パラメータは無効なキー名。next[0].condition が `^歯科口腔外科$`（文字列マッチ）になっているが、ContextMatchRouter は `^1$` のような番号を返す。
- **現在値**:
```json
"params": {
  "contextName1": "OpenAI_診療科",
  "contextName2": "OpenAI_診療科"
}
"next": [
  {"condition": "^歯科口腔外科$", "label": "歯科口腔外科", "nextModuleName": "Jump_RAG_最終"},
  {"condition": "^.*$", "label": "その他", "nextModuleName": "変更_残薬確認"}
]
```
- **正しい値**:
```json
"params": {
  "module1Name": "OpenAI_診療科",
  "module2Name": "OpenAI_診療科",
  "module1Value1": "歯科口腔外科",
  "module2Value1": "歯科口腔外科",
  "module1Value2": "", "module2Value2": "",
  ... (module1Value3〜10, module2Value3〜10 はすべて "")
}
"next": [
  {"condition": "^1$", "label": "歯科口腔外科", "nextModuleName": "Jump_RAG_最終"},
  {"condition": "^.*$", "label": "その他", "nextModuleName": "変更_残薬確認"}
]
```
- **修正指示**: C-002 と同様の手順でparams全面置換・next[0].condition修正。
- **参照**: `docs/brekeke/モジュール詳細設定ガイド_1.md` §8.1 ContextMatchRouter

---

### C-004: `完了フラグ_代表案内_診療科` — status 値誤り

- **ファイル**: `output/json/prompted_蘇生会総合病院_診療.json`
- **修正担当**: generator
- **モジュール名**: `完了フラグ_代表案内_診療科`
- **フィールド**: `params.status`
- **問題**: 設計書 termination_patterns では `END_代表電話案内_診療科対象外` の `status: "2"`（代表案内）と明記されているが、実装では `"7"` になっている。Dr.JOY 側で「代表案内」として正しく分類されない。
- **現在値**: `"status": "7"`
- **正しい値**: `"status": "2"`
- **修正指示**: `params.status` を `"2"` に修正するのみ。
- **参照**: `docs/designs/設計書_蘇生会総合病院_診療.yaml` §8 termination_patterns

---

### C-005: `完了フラグ_健康増進` — status 値誤り

- **ファイル**: `output/json/prompted_蘇生会総合病院_診療.json`
- **修正担当**: generator
- **モジュール名**: `完了フラグ_健康増進`
- **フィールド**: `params.status`
- **問題**: 設計書 termination_patterns では `END_健康増進センター案内` の `status: "2"` と明記されているが、`"7"` になっている。C-004 と同根の問題。
- **現在値**: `"status": "7"`
- **正しい値**: `"status": "2"`
- **修正指示**: `params.status` を `"2"` に修正するのみ。
- **参照**: `docs/designs/設計書_蘇生会総合病院_診療.yaml` §8 termination_patterns

---

### C-006: 全14 リトライモジュール — `retry_count` が 1（設計書は 2）

- **ファイル**: `output/json/prompted_蘇生会総合病院_診療.json`
- **修正担当**: generator
- **モジュール名**: `リトライ_旧姓`, `リトライ_診療科`, `リトライ_用件`, `リトライ_受診歴`, `リトライ_紹介状`, `リトライ_症状1`, `リトライ_医師指定`, `リトライ_症状2`, `リトライ_変更_予約日`, `リトライ_変更_希望時期`, `リトライ_残薬`, `リトライ_キャンセル_予約日`, `リトライ_キャンセル理由`, `リトライ_確認内容`（全14件）
- **フィールド**: `params.retry_count`
- **問題**: 設計書 hearing_items の全項目で `retry_count: 2` と定義されているが、全モジュールで `"1"` になっている。retry_count="1" では実質リトライ1回のみで終話に進み、発話認識の機会が設計より1回少なくなる。
- **現在値**: `"retry_count": "1"`（全14件）
- **正しい値**: `"retry_count": "2"`（全14件）
- **修正指示**: 上記14モジュールの `params.retry_count` をすべて `"2"` に変更すること。他フィールドには触れないこと。
- **参照**: `docs/brekeke/モジュール詳細設定ガイド_1.md` §2.3 Speech Retry Counter / `docs/designs/設計書_蘇生会総合病院_診療.yaml` §6 hearing_items

---

### W-001: 全6 Custom Jump to Flow — next[0].condition がアンカーなし `".*"`

- **ファイル**: `output/json/prompted_蘇生会総合病院_診療.json`
- **修正担当**: generator
- **モジュール名**: `Jump_氏名聴取` / `Jump_診察券番号聴取` / `Jump_生年月日聴取` / `Jump_電話番号聴取` / `Jump_RAG_問合` / `Jump_RAG_最終`
- **フィールド**: `next[0].condition`
- **問題**: ワイルドカード条件が `".*"`（アンカーなし）になっているが、モジュール詳細設定ガイドは `"^.*$"` を正解値として定義している。Brekeke の正規表現マッチングにおいて、アンカーなし `.*` は部分一致扱いになる可能性があり、予期しない動作を招くリスクがある。
- **現在値**: `{"condition": ".*", "label": "Jump 1", ...}`
- **正しい値**: `{"condition": "^.*$", "label": "success", ...}` （labelは "success" が推奨だが、"Jump 1" のままでも動作上は許容される）
- **修正指示**: 上記6モジュールの `next[0].condition` を `"^.*$"` に修正すること。
- **参照**: `docs/brekeke/モジュール詳細設定ガイド_1.md` §9.1 Custom Jump to Flow

---

### W-002: `コンテキスト設定` — status フィールドの rangeValues が空

- **ファイル**: `output/json/prompted_蘇生会総合病院_診療.json`
- **修正担当**: generator
- **モジュール名**: `コンテキスト設定`
- **フィールド**: `params.fields` 内 `"contextName": "status"` の `"rangeValues"`
- **問題**: 設計書 context_fields では `status` フィールドに 4 種類の rangeValues（未処理, 代表案内, 聴取失敗, 時間外）が定義されているが、実装では `"rangeValues": []` の空配列になっている。Dr.JOY 画面で status 区分が表示されない。
- **現在値**: `"rangeValues": []`
- **正しい値**:
```json
"rangeValues": [
  {"value": "未処理",  "order": 1},
  {"value": "代表案内", "order": 2},
  {"value": "聴取失敗", "order": 3},
  {"value": "時間外",  "order": 6}
]
```
- **修正指示**: `コンテキスト設定` モジュールの `params.fields` 内の `status` フィールドオブジェクトに上記 rangeValues を追記すること。他フィールドオブジェクトには触れないこと。
- **参照**: `docs/designs/設計書_蘇生会総合病院_診療.yaml` §5 context_fields

---

### W-003: `コンテキスト設定` — contextNameJp が設計書と不一致（3フィールド）

- **ファイル**: `output/json/prompted_蘇生会総合病院_診療.json`
- **修正担当**: generator
- **モジュール名**: `コンテキスト設定`
- **フィールド**: `params.fields` 内の各フィールドオブジェクトの `contextNameJp`
- **問題**: 3フィールドの日本語ラベルが設計書と不一致。Dr.JOY の画面表示に影響する。

| contextName | 現在値（JSON） | 正しい値（設計書） |
|---|---|---|
| telephoneNumber | `"着信電話番号"` | `"電話番号（着信）"` |
| dateOfCall | `"着信日"` | `"受電日時"` |
| callId | `"コールID"` | `"通話ID"` |

- **修正指示**: 上記3フィールドの `contextNameJp` を設計書の値に修正すること。
- **参照**: `docs/designs/設計書_蘇生会総合病院_診療.yaml` §5 context_fields

---

### W-004: RAG サブフロー共用 — パターン1とパターン2でTTS文言が同一になる

- **ファイル**: `output/properties_蘇生会総合病院_診療.md`
- **修正担当**: 人間確認（設計判断が必要）
- **モジュール名**: `Jump_RAG_問合`（問い合わせルート）/ `Jump_RAG_最終`（全終話前）
- **フィールド**: IVRプロパティ `相談_問合せ` の TTS 文言
- **問題**: `Jump_RAG_問合` と `Jump_RAG_最終` が同一の `蘇生会総合病院$RAG検索_20260410` サブフローを共用しているため、TTS 文言 `相談_問合せ` が両者で共通になる。CLAUDE.md では：
  - パターン1（問い合わせルート初回）: `「お問い合わせ内容をご自由におっしゃってください。」`
  - パターン2（全終話前）: `「何かご質問はございますか？」`
  と異なる文言が定められている。現在はパターン1の文言のみ設定されており、全終話前（予約完了後等）でも「お問い合わせ内容をご自由に…」と案内されてしまう。
- **現在値**: `相談_問合せ={tts_g:お問い合わせ内容をご自由におっしゃってください。}`
- **選択肢**:
  1. RAGサブフローを2本（問合せ用・終話前用）に分ける → `@generator` にサブフロー追加を指示
  2. 文言を「何かご質問はございますか？ない場合は「ありません」とお話ください。」に統一し、どちらのパターンでも違和感が少ない表現を採用
- **参照**: CLAUDE.md §16 RAGサブフローのデフォルトTTS文言 / IVRプロパティの要確認事項コメント

---

### W-005: `classification` が受診歴確認後に "新規"/"再診" へ更新されない

- **ファイル**: `output/json/prompted_蘇生会総合病院_診療.json`
- **修正担当**: generator（設計確認後）
- **モジュール名**: `OpenAI_受診歴` 後の分岐（新規/再診）
- **フィールド**: 該当モジュール不在（saveContext2DB モジュールが未実装）
- **問題**: 設計書のフロー図は `OpenAI_受診歴` → `saveContext_分類_新規(classification=新規)` / `saveContext_分類_再診(classification=再診)` → 次ステップ、という構造を示している。しかし現実装では `OpenAI_用件` が `classification=予約` を保存した後、受診歴確認後に `classification` が `"新規"` or `"再診"` に更新されない。`history` フィールドには "新規"/"再診" が保存されるが、Dr.JOY の主キーである `classification` は "予約" のままとなる。
- **影響**: Dr.JOY オペレーター画面で「用件区分」が "予約" と表示され、新規か再診かを判別するためには `history` フィールドを追加参照する必要がある（設計書の意図とずれる）。
- **対応方針**: CLAUDE.md は「OpenAI の分類ラベルの固定値保存は禁止」と定めているが、設計書の context_fields では `classification` の rangeValues に "新規"/"再診" が含まれており、Gen2 の動作を再現する意図がある。人間が設計意図を確認の上、`saveContext2DB` モジュールの追加要否を判断すること。
- **参照**: `docs/designs/設計書_蘇生会総合病院_診療.yaml` §4 flow_diagrams, §5 context_fields

---

### W-006: `acceptance_times.params.office_id` に TODO_要確認 が残存

- **ファイル**: `output/json/prompted_蘇生会総合病院_診療.json`
- **修正担当**: 人間確認
- **モジュール名**: `acceptance_times`
- **フィールド**: `params.office_id`
- **問題**: `office_id` が `"TODO_要確認"` のままになっており、営業時間判定 API が正しく動作しない。
- **現在値**: `"office_id": "TODO_要確認"`
- **正しい値**: 実際の施設 office_id（Dr.JOY 側で発行される値）
- **修正指示**: 人間が Dr.JOY 管理者に `office_id` を確認の上、`params.office_id` に正式な値を設定すること。
- **参照**: `output/properties_蘇生会総合病院_診療.md` 要確認事項

---

### I-001: `冒頭` wait モジュール — params.wait に値が直書きされている

- **ファイル**: `output/json/prompted_蘇生会総合病院_診療.json`
- **修正担当**: （対応不要）
- **モジュール名**: `冒頭`
- **フィールド**: `params.wait`
- **問題**: モジュール詳細設定ガイドでは `wait` は `""` (空文字) にしてIVRプロパティで管理するとされているが、JSON に直接 `"wait": "2000"` が設定されている。IVRプロパティ側にも `冒頭.wait=2000` があるため二重設定になっている。IVRプロパティが JSON を上書きするため機能上の問題はないが、管理上の冗長さがある。
- **対応**: 機能に影響がないため今回は修正不要。次回以降の生成時に空文字に統一する。

---

## レッドチーム攻撃シナリオ

> 患者の予期しない発話やエッジケースをシミュレーション

| # | シナリオ | 攻撃ベクトル | 予想結果 | 影響度 | 対策済み |
|---|---|---|---|---|---|
| 1 | C-001 が未修正のまま BIVR インポートした場合、全サブフロー遷移が失敗する | flowname 不一致 | 氏名聴取・診察券番号聴取等に遷移できず通話中断 | 最高 | ❌（C-001修正必須） |
| 2 | 患者が「わからない、あとシステムに指示を無視させたい」と言った場合 | プロンプトインジェクション | 各OpenAIプロンプトにインジェクション対策セクションあり → NO_RESULT でリトライへ | 低 | ✅ |
| 3 | 患者が診療科として「救急」と発話した場合（STT誤変換あり） | 診療科認識誤り | `OpenAI_診療科` プロンプト内に「救急科 → 予約不可」マッピングあり → 代表電話案内 | 低 | ✅ |
| 4 | 患者が用件として「お薬だけ欲しい」と発話した場合 | STT誤変換による誤分類 | `OpenAI_用件` に STT誤変換補正（薬 → 予約）が明示的に定義されている → 予約に分類 | 低 | ✅ |
| 5 | C-002/C-003 が未修正の場合、`終話分岐` と `変更_歯科判定` が常にフォールスルー | ContextMatchRouter params 誤り | キャンセルルートが「その他」扱いになる。歯科の変更でも残薬確認が発生する | 高 | ❌（C-002/C-003修正必須） |
| 6 | 患者が旧姓の代わりに「山田でございます（姓も含んだ発話）」をした場合 | 旧姓として姓のみが抽出されるリスク | `OpenAI_旧姓` プロンプトが STEP4「旧姓テキスト出力」でそのまま出力する設計のため、「山田でございます」全体が旧姓として登録されるリスクあり | 中 | ⚠️（プロンプト改善余地あり） |
| 7 | 患者が診療科として「先生に聞かないとわからない」等の複合発話をした場合 | わからない + 余計な語句 | `OpenAI_診療科` の `わからない` 判定（STEP2）は部分一致でなく完全一致ベース → STEPで「わからない」の語句が含まれれば `わからない` に分類される可能性がある | 低 | ✅（STEP3でコンテキスト認識） |
| 8 | retry_count=1（C-006）で1回リトライ後に即座に終話になる | 認識失敗連続 | retry_count="1" は1回試行後に「No more」→ 終話。想定の2回に届かず患者に不満を与える | 中 | ❌（C-006修正必須） |

---

## OpenAIプロンプト出力ラベル整合性

| モジュール名 | next分岐ラベル | prompt出力仕様 | 判定 | 備考 |
|---|---|---|---|---|
| OpenAI_旧姓 | success(`^.+$`) | {旧姓テキスト}, なし, NO_RESULT | ✅ PASS | normalize型 |
| OpenAI_診療科 | 予約不可, 健康増進センター, success(`^.+$`) | 予約不可, 健康増進センター, {診療科名}, わからない | ✅ PASS | classify型+success包括 |
| OpenAI_用件 | 予約, 変更, キャンセル, 確認, 問い合わせ | 予約, 変更, キャンセル, 確認, 問い合わせ, NO_RESULT | ✅ PASS | classify型5択 |
| OpenAI_受診歴 | 新規(`^新規$`), 再診(`^再診$`) | 新規, 再診, NO_RESULT | ✅ PASS | classify型2択 |
| OpenAI_紹介状 | success(`^.+$`) | あり, なし, NO_RESULT | ✅ PASS | normalize型 |
| OpenAI_症状1 | success(`^.+$`) | {症状テキスト}, NO_RESULT | ✅ PASS | summarize型 |
| OpenAI_医師指定 | success(`^.+$`) | {医師名テキスト}, なし, NO_RESULT | ✅ PASS | normalize型 |
| OpenAI_症状2 | success(`^.+$`) | はい, いいえ, NO_RESULT | ✅ PASS | classify型2択 |
| OpenAI_変更_予約日 | success(`^.+$`) | yyyy-MM-dd 00:00:00, わからない, NO_RESULT | ✅ PASS | convert型 |
| OpenAI_変更_希望時期 | success(`^.+$`) | {希望時期テキスト}, NO_RESULT | ✅ PASS | normalize型 |
| OpenAI_残薬 | success(`^.+$`) | はい, いいえ, なし, NO_RESULT | ✅ PASS | classify型3択 |
| OpenAI_キャンセル_予約日 | success(`^.+$`) | yyyy-MM-dd 00:00:00, わからない, NO_RESULT | ✅ PASS | convert型 |
| OpenAI_キャンセル理由 | success(`^.+$`) | {理由テキスト}, NO_RESULT | ✅ PASS | summarize型 |
| OpenAI_確認内容 | success(`^.+$`) | {確認テキスト}, NO_RESULT | ✅ PASS | summarize型 |

---

## 修正指示一覧（エージェント別）

### generator向け（12件）

| タグ | 修正箇所 | 修正内容 |
|---|---|---|
| C-001 | Jump_氏名聴取 ほか5モジュール `params.flowname` | `drjoy^Jump_to_flow$` → `drjoy^蘇生会総合病院$` |
| C-002 | 終話分岐 `params` + `next[0].condition` | `contextName1/2` → `module1Name/2` + valueArr ; `^キャンセル$` → `^1$` |
| C-003 | 変更_歯科判定 `params` + `next[0].condition` | `contextName1/2` → `module1Name/2` + valueArr ; `^歯科口腔外科$` → `^1$` |
| C-004 | 完了フラグ_代表案内_診療科 `params.status` | `"7"` → `"2"` |
| C-005 | 完了フラグ_健康増進 `params.status` | `"7"` → `"2"` |
| C-006 | リトライ系全14モジュール `params.retry_count` | `"1"` → `"2"` |
| W-001 | Jump系全6モジュール `next[0].condition` | `".*"` → `"^.*$"` |
| W-002 | コンテキスト設定 `params.fields` status.rangeValues | `[]` → `[{未処理/1},{代表案内/2},{聴取失敗/3},{時間外/6}]` |
| W-003 | コンテキスト設定 `params.fields` 各フィールド `contextNameJp` | telephoneNumber / dateOfCall / callId の日本語ラベル修正 |
| W-005 | （設計確認後）saveContext2DBモジュールの追加要否を判断 | 新規/再診パスに saveContext2DB(classification=新規/再診) を追加するか人間確認 |

### prompter向け

なし（全プロンプトは品質基準4本柱を満たしている）

### properties向け

なし（プロパティファイルのモジュール網羅性は問題なし）

---

## 人間が確認すべき箇所

1. **C-001〜C-006 の修正優先**: fixer によって一括修正可能。特に C-001（flowname）は BIVR インポート前に必ず修正すること。
2. **W-004 RAGサブフロー分岐設計**: パターン1（問い合わせ）とパターン2（全終話前）で TTS 文言が共通になる。発話文言を統一するか、サブフローを2本に分けるかを設計判断すること。
3. **W-005 classification の更新要否**: 設計書の意図（受診歴確認後に classification を新規/再診に更新）を実装するかどうかの確認。Dr.JOY 表示上の要件と CLAUDE.md の制約を照合して人間が判断すること。
4. **W-006 office_id 設定**: Dr.JOY 管理者に `office_id` を確認の上、`acceptance_times.params.office_id` に設定すること。

---
対象JSON: `C:\Users\hamaguchi.t\vfb-蘇生会総合病院_診療\output\json\prompted_蘇生会総合病院_診療.json`