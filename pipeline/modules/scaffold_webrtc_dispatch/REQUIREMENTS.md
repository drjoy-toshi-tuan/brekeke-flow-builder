# scaffold_generator.py 拡張 — null_check ブロック型 / get-header 自動配置（WebRTC Pattern 5）

`東京都立豊島病院_診療` の BLOCKER B-3（WebRTC 事前入力フォーム対応・2026-07-10 壁打ちで仕様確定）を
実装するために scaffold_generator.py（保護ゾーン・codeowner レビュー要）へ加える 2 つの拡張の仕様。

## 位置づけ

- 対象モジュール自体（`drjoy^Context Logic$null-check` / `drjoy^Incoming$get-header`）は
  **既に Brekeke 標準モジュールとして動作仕様確定済み**（null-check: 20 ケース実機検証、
  `modules/README.md`「動作仕様確定済みの Brekeke 標準モジュール」表）。本 REQUIREMENTS は
  それらを **scaffold_generator.py の scenario_flow ブロック型として配線する Python 側ロジック**
  の入出力契約を定義し、実装前にオラクルで固定する。
- `build_null_check` は `scripts/test_scaffold_generator.py`（Pattern 6 検証専用ビルダー、216-236行）
  に参照実装が既にあり、20 ケースの実機受入で使われた実績がある。本番 `scaffold_generator.py` への
  移植では、production の helper（`M` / `_N` / `_E`、10 スロットへの手書き padding）に合わせる。
- `build_get_header` は既に `scripts/scaffold_generator.py`（474-482行）に定義済みだが、
  どの block type からも呼ばれておらず「採用施設が無いため自動配置未実装」（
  `docs/brekeke/モジュール選定ガイド_v2.md` §1.3）の状態だった。東京都立豊島病院が最初の
  採用施設となるため、本 REQUIREMENTS で自動配置を有効化する。

## スコープ

**含む**:
1. 新しい scenario_flow ブロック型 `null_check`（汎用・施設非依存）。
2. `opening` ブロックの新フィールド `webrtc_prefill: true`（Pattern 5 採用施設のみ指定）による
   get-header 自動配置。

**含まない**:
- 東京都立豊島病院の各聴取ステップ（氏名/生年月日/電話番号/診察券番号聴取）の前に実際に
  null_check ブロックを配線する作業（施設の設計書 YAML 側の作業。本拡張が入った後に行う）。
- get-header が保存する context キー名・WebRTC ブラウザ側 JSON 仕様の施設間合意
  （モジュール選定ガイド §1.3 に記載の通り個別施設で合意）。

## 1. null_check ブロック型

### YAML 入力（scenario_flow）

```yaml
- step: <ブロック名>
  type: null_check
  key: <モジュール名 または "<% context名 %>" 形式>
  true_next: <key が空/null の場合の遷移先 step>
  false_next: <key に値がある場合の遷移先 step>
```

- `key` は「モジュール名」（例: `"OpenAI_用件"`。`getModuleResult` 経由）または
  `<% varName %>` の単独参照（`getSystemVariableValue` 経由でセッション変数を直読み）。
  判定は null-check モジュール内部の JS が行うため scaffold 側は文字列をそのまま `params.key` に渡すのみ。
- `true_next` = null-check の `setResult="true"`（＝空/null/空白/空配列/空オブジェクト）の遷移先。
- `false_next` = `setResult="false"`（＝値あり）の遷移先。
- 他ブロック型の `next` / `conditions` と異なり、本ブロックは分岐必須（2 分岐）のため
  `next` フィールドは使用しない。

### 出力（Brekeke モジュール JSON）

```json
{
  "name": "<ブロック名>",
  "type": "drjoy^Context Logic$null-check",
  "params": {"key": "<key>"},
  "next": [
    {"condition": "^true$",  "label": "true",  "nextModuleName": "<true_next 解決後>"},
    {"condition": "^false$", "label": "false", "nextModuleName": "<false_next 解決後>"},
    {"condition": "", "label": "", "nextModuleName": ""}  // × 8 (計10スロット)
  ]
}
```

- `next` 配列は必ず10スロット（Brekeke UI の固定枠。ContextMatchRouter 等と同じ padding 規約）。
- `true_next` / `false_next` は scaffold の `resolve()`（サブフロー先頭 step → 実 Jump モジュール名の
  逆引き）を通してから渡す。他ブロック型の `next` 解決と同じ扱い。

### 検証（schemas/qa_validator.py 側で必要な対応）

- `KNOWN_BLOCK_TYPES` に `null_check` を追加（allowlist）。
- `BLOCK_REQUIRED_FIELDS["null_check"] = ["key", "true_next", "false_next"]`。
- F-1（到達可能性）/ F-2（遷移先実在性）は `next` / `conditions` しか見ていないため、
  `true_next` / `false_next` を辿るケースを追加する（cmr_chain の `reference_modules[].next` /
  `default_next` と同じ扱い方）。

## 2. opening ブロックの webrtc_prefill 自動配置

### YAML 入力（scenario_flow の opening ブロック）

```yaml
- step: 冒頭
  type: opening
  use_acceptance_times: true
  webrtc_prefill: true   # Pattern 5 採用施設のみ（省略時 false = 従来通り）
  next: 冒頭_アナウンス
```

### 配置ルール（モジュール選定ガイド_v2.md §1.3 / モジュール詳細設定ガイド_1.md §6.4 準拠）

```
着信電話番号分類(incoming-classifier)
  ├─ 非通知 → ...
  ├─ WebRTC → WebRTCヘッダ取得(get-header) → 受付時間判定   ← webrtc_prefill: true のときだけ生成
  └─ 固定/携帯/その他/海外 → 受付時間判定
```

- `webrtc_prefill` が真のときのみ `build_get_header("WebRTCヘッダ取得", after_incoming)` を
  自動生成し、`build_incoming_classifier(..., webrtc_next="WebRTCヘッダ取得")` として WebRTC ラベルの
  遷移先に差し込む。
- get-header 自体の次段（`next_module`）は `after_incoming`（＝固定/携帯/その他と同じ「受付時間判定」）。
  個人情報聴取のスキップは get-header の遷移先を変えることでは行わず、**各聴取ステップ側に置く
  null_check ブロックが担う**（BLOCKER B-3 確定仕様（2）。get-header は「フォーム値を context に
  保存してから通常フローに合流させる」役割のみを持つ。
- `webrtc_prefill` が偽/未指定の場合は **現行と完全に同一の出力**（get-header 不生成・
  `build_incoming_classifier(anon_flag, after_incoming)` を webrtc_next 省略で呼ぶ）。
  既存の全施設に対して非破壊であることが必須（回帰ゼロ）。

## DoD 状況

- [x] REQUIREMENTS.md（本ファイル）
- [x] Python オラクル（`oracle.py`）— 独立実装で期待 JSON 構造を固定
- [x] `test_oracle.py` 全 PASS（8/8、`scaffold_generator.py` 実装後に実行して確認済み）
- [x] `scaffold_generator.py` 実装（`build_null_check` 追加・`null_check` ブロック型 dispatch・
      `opening` ブロックの `webrtc_prefill` フラグによる get-header 自動配置。**保護ゾーン・
      未マージ・PR 要 @TS-dong-nc**）
- [x] `schemas/qa_validator.py` allowlist 更新（`KNOWN_BLOCK_TYPES` / `BLOCK_REQUIRED_FIELDS` に
      `null_check` 追加、F-1/F-2 に `true_next`/`false_next` 到達性・参照整合性チェックを追加。
      **保護ゾーン・未マージ・PR 要 @TS-dong-nc**）
- [x] 統合サニティ確認（`generate_scaffold_v2` に `webrtc_prefill: true` の opening + `null_check`
      ブロックを含む最小 YAML を通し、`WebRTCヘッダ取得` 自動生成・WebRTC ラベル配線・`resolve()`
      経由の `true_next`/`false_next` 解決を確認。qa_validator の F-1/F-2/F-3/F-6 も合成ケースで
      正常系・異常系（存在しない遷移先 / 必須フィールド欠落）双方を確認済み）
- [ ] Brekeke 実機受入（東京都立豊島病院 Pattern 7 連結 or Pattern 6 単体で確認。null-check /
      get-header 自体は既に動作仕様確定済みのため、ここで確認するのは **scaffold の配線が
      仕様通りの JSON を生成すること** のみ）— PR マージ後、実際の施設設計書に組み込んでから実施
- [x] `modules/README.md` への追記（本フォルダへのリンク）

## 注意

- null-check / get-header 自体の「1文字でも改変したら再受入」ポリシーはモジュール本体
  （Brekeke ネイティブ実装）に対するものであり、本拡張はそれらを呼び出す scaffold 側の
  組み立てロジックが対象。ここでの受入は「scaffold が仕様通りの JSON を出力するか」であって、
  null-check / get-header の動作仕様の再受入ではない。
