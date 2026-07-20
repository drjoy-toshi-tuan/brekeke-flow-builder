# 校閲レポート: 北里大学病院 - 診療

> 校閲日: 2026-03-27
> 対象ファイル: `output/json/draft_北里大学病院_診療.json`
> 出力ファイル: `output/json/reviewed_北里大学病院_診療.json`
> プロパティ: `output/properties_北里大学病院_診療.md`
> 案件区分: **Gen1 Commubo 移管案件**（設計書なし）
> 元ソース: 「【0051北里大学病院】診療1_M_本院」

---

## セキュリティ・ライセンス警告（最優先確認）

なし（セキュリティインジェクションパターン・ライセンス違反は検出されませんでした）

---

## サマリー

- 検出問題数: 7件
- 重大度別: SECURITY-CRITICAL 0 / Critical 2 / Warning 4 / LICENSE-WARN 0 / Info 1
- 自動修正: 2件 / 人間確認必要: 4件
- validator.py 最終結果: **PASS**（Critical 0、Warning 5 — うち4件はTODO値で人間設定待ち）

---

## 検出事項

### C-001: saveContextModel2DB の rangeValues に `id` フィールドが欠落

- **ファイル**: `output/json/draft_北里大学病院_診療.json`
- **モジュール名**: `コンテキスト設定`
- **フィールド**: `params.fields` 内の全 rangeValues 要素
- **問題**: `classification`（6件）、`clinicalDepartment`（12件）、`status`（5件）の rangeValues に `id` フィールドが存在しない。CLAUDE.md CTX-008「rangeValues 各要素に `id`/`order`/`value` が揃っていること」に違反。
- **現在値**: `{"order": 1, "value": "予約確認"}` 等（id なし）
- **正しい値**: `{"id": "予約確認", "order": 1, "value": "予約確認"}` 等
- **修正指示**: 各 rangeValues 要素に `id` フィールドを追加（value と同一値で設定）
- **対応**: **自動修正済み** — `id` フィールドを `value` と同一値で全 rangeValues に追加した

---

### C-002: `status` rangeValues に `order=6`（時間外）が欠落

- **ファイル**: `output/json/draft_北里大学病院_診療.json`
- **モジュール名**: `コンテキスト設定`
- **フィールド**: `params.fields` → `contextName=status` の `rangeValues`
- **問題**: CLAUDE.md「status の rangeValues が標準5値（0:途中切断, 1:未処理, 2:代表案内, 3:転送, 6:時間外）を含んでいること」に対し、`order=6`（時間外）が欠落していた。現在値は `[0, 1, 2, 3, 4]` のみ。
- **現在値**: `order` = [0, 1, 2, 3, 4] — `order=6` なし
- **正しい値**: `order` = [0, 1, 2, 3, 4, 6] — `order=6`（時間外）を含む
- **修正指示**: status rangeValues に `{"id": "時間外", "order": 6, "value": "時間外"}` を追加
- **対応**: **自動修正済み** — `order=6` のエントリを追加した

---

### W-001: `acceptance_times` の TIMEOUT が「受付中扱い」ではなく「エラー終話」に遷移

- **ファイル**: `output/json/draft_北里大学病院_診療.json`
- **モジュール名**: `受付時間判定`
- **フィールド**: `next[0]`（`^TIMEOUT$`）
- **問題**: reviewer.md「acceptance_times の next に `^TIMEOUT$` → 受付中扱い（冒頭アナウンスへ）」に対し、現在は `完了フラグ_エラー` → `終話_エラー` → `切断_エラー` に遷移している。TIMEOUT 時は受付可能時間と判定して冒頭アナウンスに戻すべき。
- **現在値**: `"nextModuleName": "完了フラグ_エラー"`
- **正しい値**: `"nextModuleName": "冒頭_アナウンス"`（または受付中扱いのパス先頭）
- **修正指示**: Gen1 Commubo の元仕様を確認の上、TIMEOUT 時の挙動を判断すること。移管案件のため Gen1 の仕様を優先する場合は、レポート記載のみにとどめることも可。
- **対応**: **未修正** — Gen1 仕様との照合が必要なため人間確認を求める

---

### W-002: `saveCompletionFlag2db` の status/smsFlag 値が CLAUDE.md 標準値と乖離

- **ファイル**: `output/json/draft_北里大学病院_診療.json`
- **対象モジュール**: `完了フラグ_非通知`、`完了フラグ_海外`、`完了フラグ_時間外`
- **問題**: CLAUDE.md「非通知・海外: status=`"2"`, smsFlag=`"-1"` / 時間外: status=`"6"`, smsFlag=`"-1"`」に対し、プロパティファイルおよびフローの設定値が異なる。これは Gen1 Commubo 移管案件のため、Gen1 の仕様が反映されていると考えられる。
- **現在値**:
  - `完了フラグ_非通知`: status=0, smsFlag=0（CLAUDE.md 標準: status=2, smsFlag=-1）
  - `完了フラグ_海外`: status=0, smsFlag=0（CLAUDE.md 標準: status=2, smsFlag=-1）
  - `完了フラグ_時間外`: status=3, smsFlag=0（CLAUDE.md 標準: status=6, smsFlag=-1）
- **修正指示**: Dr.JOY 側仕様との照合が必要。Gen1 から継続の場合は現在値維持を承認の上、人間がレビューすること。
- **対応**: **未修正** — Gen1 移管案件のため人間判断を要する

---

### W-003: `saveContextModel2DB` の fields が minified（1行）形式

- **ファイル**: `output/json/reviewed_北里大学病院_診療.json`
- **モジュール名**: `コンテキスト設定`
- **フィールド**: `params.fields`
- **問題**: validator.py が CTX-014 として検出。動作には影響しないが、Brekeke フローデザイナーでの目視確認が困難。
- **現在値**: minified（1行）JSON 文字列
- **修正方法**: `python3 scripts/format_fields.py output/json/reviewed_北里大学病院_診療.json` で自動整形可能
- **対応**: **未修正** — 人間がビルド前に実行すること（動作には影響なし）

---

### W-PROP-TODO-001: プロパティに TODO_ 値が残存

- **ファイル**: `output/properties_北里大学病院_診療.md`
- **問題**: 以下の4箇所に `TODO_` が残存している。Brekeke IVR に設定する際に人間が入力すること。

| キー | 内容 |
|---|---|
| `office_id` | `TODO_施設のoffice_idを入力` |
| `転送_折り返し予約センター.number` | `TODO_折り返し予約センター番号を入力` |
| `転送_眼科予約センター.number` | `TODO_眼科予約センター番号を入力` |
| `転送_婦人科予約センター.number` | `TODO_婦人科予約センター番号を入力` |

- **対応**: **未修正** — 人間が施設担当者に確認の上、Brekeke IVR プロパティ画面に直接設定すること

---

### I-001: `wait` モジュールの type が `Custom$wait`（非標準プレフィックス）

- **ファイル**: `output/json/draft_北里大学病院_診療.json`
- **モジュール名**: `冒頭`
- **フィールド**: `type`
- **問題**: `Custom$wait` は `drjoy^` プレフィックスを持たない。ただし Gen1 移管案件では一般的な表記であり、Brekeke IVR での動作実績がある場合は問題なし。
- **対応**: レポート記載のみ。動作確認の上、問題がなければ承認すること。

---

## 修正済みモジュール一覧

| # | モジュール名 | フィールド | 修正内容 | 重大度 |
|---|---|---|---|---|
| 1 | `コンテキスト設定` | `params.fields` → classification.rangeValues[*].id | `id` フィールドを全6要素に追加（value と同一値） | Critical |
| 2 | `コンテキスト設定` | `params.fields` → clinicalDepartment.rangeValues[*].id | `id` フィールドを全12要素に追加（value と同一値） | Critical |
| 3 | `コンテキスト設定` | `params.fields` → status.rangeValues[*].id | `id` フィールドを全5要素に追加（value と同一値） | Critical |
| 4 | `コンテキスト設定` | `params.fields` → status.rangeValues | `{"id": "時間外", "order": 6, "value": "時間外"}` を追加 | Critical |

---

## Generator再生成が必要な箇所

なし（Critical 問題は自動修正済み）

---

## 人間が確認すべき箇所

### 1. acceptance_times TIMEOUT の遷移先（W-001）

`受付時間判定` モジュールの `^TIMEOUT$` 遷移先が `完了フラグ_エラー` になっている。
Gen1 Commubo での元の挙動を確認し、受付可能時間と判断すべきか否かを判断すること。

**判断指針**:
- Gen1 で TIMEOUT を「受付中扱い」としていた場合 → `nextModuleName` を `冒頭_アナウンス` に変更
- Gen1 で TIMEOUT を「エラー終話」としていた場合 → 現状維持でよい

### 2. saveCompletionFlag2db の status/smsFlag 値（W-002）

非通知・海外・時間外の完了フラグ値が CLAUDE.md 標準と異なる。
Dr.JOY バックエンドの仕様を確認し、以下の変更が必要か判断すること：

| モジュール | 現在値 | CLAUDE.md 標準 |
|---|---|---|
| `完了フラグ_非通知` | status=0, smsFlag=0 | status=2, smsFlag=-1 |
| `完了フラグ_海外` | status=0, smsFlag=0 | status=2, smsFlag=-1 |
| `完了フラグ_時間外` | status=3, smsFlag=0 | status=6, smsFlag=-1 |

### 3. TODO_ 値の入力（W-PROP-TODO-001）

Brekeke IVR プロパティ画面で以下を設定すること：
- `office_id`: 施設の office_id（Dr.JOY 管理画面で確認）
- `転送_折り返し予約センター.number`: 折り返し予約センター番号
- `転送_眼科予約センター.number`: 眼科予約センター番号
- `転送_婦人科予約センター.number`: 婦人科予約センター番号

### 4. fields 整形（W-003）

ビルド前に以下を実行すること（任意）：
```bash
python3 scripts/format_fields.py output/json/reviewed_北里大学病院_診療.json
```

---

## 構造整合性チェック結果（全件 PASS）

| チェック項目 | 結果 |
|---|---|
| start モジュールが modules 内に存在するか | PASS |
| 全 nextModuleName が modules 内に存在するか | PASS |
| 孤立モジュール（到達不能）がないか | PASS（134モジュール全件到達可能） |
| TTS next label が `Next Module` か | PASS |
| STT success が `^.+$` 1本受けか | PASS |
| Retry counter/label が `true/false` / `Retry/No more` か | PASS |
| stop_by_dtmf が `"No"`/`"Yes"` か | PASS |
| DTMF prompt に `{recstart}` が含まれるか | PASS |
| 全 TTS/STT/Retry に save2db が接続されているか | PASS |
| save2db が next 遷移先になっていないか | PASS |
| Disconnect の next が空配列か | PASS |
| wait モジュールの subs が空配列か | PASS |
| モジュール名に環境依存文字・括弧・スペースがないか | PASS |
| プロパティと JSON のモジュール名一致 | PASS |

---

## 備考

- 本案件は設計書が存在しないため、Gen1 Commubo 移管案件として CLAUDE.md 品質基準に基づいて校閲を実施した。
- 個人情報聴取サブフロー（氏名・生年月日・電話番号・診察券番号）は本フローとは別の `北里$氏名聴取` 等のサブフローとして実装される前提であり、本フローには含まれていない（正常）。
- 案内系 TTS（`案内_外来調剤`、`案内_内視鏡` 等）は全て `完了フラグ_案内`（status=4）→ `終話_案内終了` → 切断 のパスに収束する設計になっており、統一されている。
