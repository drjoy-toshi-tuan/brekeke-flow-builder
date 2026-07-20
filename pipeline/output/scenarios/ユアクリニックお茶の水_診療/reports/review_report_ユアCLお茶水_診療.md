# 校閲レポート: ユアクリニックお茶の水 - 診療（メインフロー）

- **対象ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_診療.json`
- **設計書**: `docs/designs/設計書_ユアクリニックお茶の水_診療.yaml`
- **プロパティ**: `output/scenarios/ユアクリニックお茶の水_診療/properties_ユアCLお茶水_診療.md`
- **校閲日**: 2026-04-01

---

## セキュリティ・ライセンス警告（最優先確認）

なし（プロンプトインジェクション・禁止パターン検出なし）

---

## サマリー

- 検出問題数: 13件
- 重大度別: SECURITY-CRITICAL 0 / Critical 7 / Warning 4 / LICENSE-WARN 0 / Info 2
- 修正担当別: generator 11件 / prompter 0件 / properties 2件 / 人間確認 0件

---

## 検出事項

### C-001: 着信電話番号分類 — `その他` condition が無効な正規表現

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_診療.json`
- **修正担当**: generator
- **モジュール名**: `着信電話番号分類`
- **フィールド**: `next[4].condition`
- **問題**: `^*$` は有効な正規表現ではない（量詞 `*` の前に対象が存在しない）。`^.*$` の誤記。
- **現在値**: `"^*$"`
- **正しい値**: `"^.*$"`
- **修正指示**: `next[4].condition` を `"^.*$"` に修正すること。他のモジュールには一切触れないこと。
- **参照**: CLAUDE.md — next配列の規則

> 修正指示: 上記フィールドのみを修正し、他のモジュールには一切触れないこと。

---

### C-002: saveContextModel2DB のフィールド定義が設計書と不一致（`timeSlot` 欠落・`isAfterHours` 名称誤り）

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_診療.json`
- **修正担当**: generator
- **モジュール名**: `コンテキスト設定`
- **フィールド**: `params.fields`
- **問題**: 設計書セクション5「コンテキストフィールド一覧」に `timeSlot`（contextNameJp: 時間帯種別、displayType: TEXT、rangeValues: []）が定義されているが、JSONでは `isAfterHours` というフィールドで代替されている。`isAfterHours` は設計書に存在しないフィールドである。
- **現在値**: `fields` に `isAfterHours` が定義され、`timeSlot` が欠落
- **正しい値**: 設計書セクション5の通り `timeSlot`（contextNameJp: "時間帯種別", displayType: "TEXT", rangeValues: [], itemDefault: false, editable: false, deletable: true）を追加し、`isAfterHours` を削除する
- **修正指示**: `コンテキスト設定` モジュールの `params.fields` から `isAfterHours` エントリを削除し、代わりに以下エントリを追加すること。また C-003 で指摘する `saveCtx_時間外ON` / `saveCtx_時間外OFF` / `script_終話分岐` も合わせて修正が必要。

```json
{
  "contextName": "timeSlot",
  "contextNameJp": "時間帯種別",
  "displayType": "TEXT",
  "rangeValues": [],
  "editable": false,
  "deletable": true,
  "itemDefault": false
}
```

> 修正指示: `params.fields` の `isAfterHours` エントリのみを `timeSlot` エントリに置換すること。他のエントリには一切触れないこと。

---

### C-003: `saveCtx_時間外ON` / `saveCtx_時間外OFF` のコンテキスト名が設計書と不一致

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_診療.json`
- **修正担当**: generator
- **モジュール名**: `saveCtx_時間外ON`, `saveCtx_時間外OFF`
- **フィールド**: `params.contextName`, `params.contextValue`
- **問題**: 設計書では時間帯種別を保存するコンテキスト名は `timeSlot`（値: "時間外" / "営業時間内"）と定義されているが、実装では `isAfterHours`（値: "1" / "0"）が使われている。`script_終話分岐` が `$ivr.getObject("isAfterHours")` で参照しているため、C-002・C-003・C-004 の修正は一括して整合性を保って行うこと。
- **現在値**:
  - `saveCtx_時間外ON.params.contextName` = `"isAfterHours"`, `contextValue` = `"1"`
  - `saveCtx_時間外OFF.params.contextName` = `"isAfterHours"`, `contextValue` = `"0"`
- **正しい値**:
  - `saveCtx_時間外ON.params.contextName` = `"timeSlot"`, `contextValue` = `"時間外"`
  - `saveCtx_時間外OFF.params.contextName` = `"timeSlot"`, `contextValue` = `"営業時間内"`
- **修正指示**: `saveCtx_時間外ON` と `saveCtx_時間外OFF` の `params.contextName` と `params.contextValue` を上記に修正するとともに、`script_終話分岐` のスクリプト内の `$ivr.getObject("isAfterHours")` を `$ivr.getObject("timeSlot")` に修正し、条件判定を `"1"/"0"` から `"時間外"/"営業時間内"` に変更すること。
- **参照**: 設計書セクション5, セクション7「ステップ詳細」備考

> 修正指示: C-002 の `コンテキスト設定.params.fields` 修正と同時に実施すること。

---

### C-004: リトライ上限到達時の転送パスが欠落（設計書との業務ロジック乖離）

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_診療.json`
- **修正担当**: generator
- **モジュール名**: `リトライ_問い合わせ内容`
- **フィールド**: `next[1].nextModuleName`（No more の遷移先）
- **問題**: 設計書セクション7のフロー図では「No more → script_時間帯判定 → 営業時間内 → 転送_リトライ失敗_アナウンス(TTS) → Call Transfer → 完了フラグ_リトライ転送」というパスが必要。現状は No more が直接 `終話_上限エラー` に遷移しており、営業時間内での代表転送パスが完全に欠落している。

  設計書セクション11にも「リトライ上限到達時の挙動が時間帯により異なる: 9:00-19:00は代表電話に転送（P4/P12に記載）、それ以外は終話切断。timeSlotコンテキストを参照して分岐」と明記されている。

- **現在値**: `リトライ_問い合わせ内容.next[1].nextModuleName` = `"終話_上限エラー"`
- **正しい値**: 以下のモジュール群を新規追加し、`リトライ_問い合わせ内容.next[1].nextModuleName` = `"script_時間帯判定"` に変更する

  追加が必要なモジュール:
  1. `script_時間帯判定`（Script）: `timeSlot` を参照し、"営業時間内" → `"1"`, それ以外 → `"0"` を返す
  2. `転送_リトライ失敗_アナウンス`（TTS）: 設計書セクション9に定義済みの発話内容。next は `代表電話_リトライ転送` へ
  3. `代表電話_リトライ転送`（Call Transfer）: `transferTo` = `"03-3259-1190"`. 成功 → `完了フラグ_リトライ転送`, 失敗 → `転送失敗_アナウンス`（既存モジュールに合流可）
  4. `完了フラグ_リトライ転送`（saveCompletionFlag2db）: `status` = `"3"`, `smsFlag` = `"-1"`

  `script_時間帯判定.next`:
  - `{"condition": "^1$", "label": "営業時間内", "nextModuleName": "転送_リトライ失敗_アナウンス"}`
  - `{"condition": "^0$", "label": "時間外", "nextModuleName": "終話_上限エラー"}`

- **修正指示**: 上記モジュール群をJSONに追加し、`リトライ_問い合わせ内容.next[1].nextModuleName` を `"script_時間帯判定"` に変更すること。転送失敗パスは既存の `転送失敗_アナウンス` → `完了フラグ_転送失敗` に接続してよい。save2dbサブモジュールを忘れずに接続すること。
- **参照**: 設計書セクション7, セクション8（END_リトライ転送）, セクション11

> 修正指示: C-003 の修正（`timeSlot` コンテキスト名への変更）が完了した後に実施すること。

---

### C-005: `Jump_氏名聴取` の `params.flowname` が誤ったフロー名を参照

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_診療.json`
- **修正担当**: generator
- **モジュール名**: `Jump_氏名聴取`
- **フィールド**: `params.flowname`
- **問題**: flowname が `"drjoy^Jump_to_flow$氏名聴取"` になっており、存在しないフロー名を参照している。CLAUDE.md のサブフロー遷移規則では `drjoy^グループ名$フロー名` 形式を使用する。設計書では氏名聴取フロー名は `ユアCLお茶水$氏名聴取`。
- **現在値**: `"drjoy^Jump_to_flow$氏名聴取"`
- **正しい値**: `"ユアCLお茶水$氏名聴取"`
- **修正指示**: `Jump_氏名聴取.params.flowname` を `"ユアCLお茶水$氏名聴取"` に修正すること。
- **参照**: CLAUDE.md モジュール種別一覧 / モジュール詳細設定ガイド_1.md セクション 1.5

> 修正指示: 上記フィールドのみを修正し、他のモジュールには一切触れないこと。

---

### C-006: `Jump_電話番号聴取` の `params.flowname` が誤ったフロー名を参照

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_診療.json`
- **修正担当**: generator
- **モジュール名**: `Jump_電話番号聴取`
- **フィールド**: `params.flowname`
- **問題**: flowname が `"drjoy^Jump_to_flow$電話番号聴取"` になっており、存在しないフロー名を参照している。設計書では電話番号聴取フロー名は `ユアCLお茶水$電話番号聴取`。
- **現在値**: `"drjoy^Jump_to_flow$電話番号聴取"`
- **正しい値**: `"ユアCLお茶水$電話番号聴取"`
- **修正指示**: `Jump_電話番号聴取.params.flowname` を `"ユアCLお茶水$電話番号聴取"` に修正すること。
- **参照**: CLAUDE.md モジュール種別一覧 / モジュール詳細設定ガイド_1.md セクション 1.5

> 修正指示: 上記フィールドのみを修正し、他のモジュールには一切触れないこと。

---

### C-007: `saveCtx_時間外ON` の next が `問い合わせ内容_聴取` へ遷移（設計書との不一致）

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_診療.json`
- **修正担当**: generator
- **モジュール名**: `saveCtx_時間外ON`
- **フィールド**: `next[0].nextModuleName`
- **問題**: 設計書のフロー図では `時間外_アナウンス(TTS) → [問い合わせ内容聴取に合流]` と記載されており、時間外アナウンス後に問い合わせ内容聴取へ進む。ただし現在のフローでは `時間外_アナウンス → saveCtx_時間外ON → 問い合わせ内容_聴取` となっており経路自体は正しい。

  **実際の問題は別にある**: `saveCtx_時間外ON.next` が `"問い合わせ内容_聴取"` に遷移しているが、`問い合わせ内容_聴取` は TTS モジュール（`drjoy^Text To Speech$Text to speech`）であり、これは正しい。一方で `saveCtx_時間外OFF.next` も同じく `"問い合わせ内容_聴取"` に遷移しているため合流点としては機能している。

  よって C-007 の指摘は取り下げ（設計書と一致）。ただし **`inquiry` フィールドの `deletable` 差異** を下記 I-001 として記録する。

  **→ この指摘は撤回。以下 I-001 に差し替え。**

---

### W-001: `冒頭_wait` の next label が `"Next Module"` （ガイドでは `"next"`）

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_診療.json`
- **修正担当**: generator
- **モジュール名**: `冒頭_wait`
- **フィールド**: `next[0].label`
- **問題**: モジュール詳細設定ガイド_1.md セクション 1.1 によると、wait モジュールの next label は `"next"` が正しい。実装では `"Next Module"` になっている。
- **現在値**: `"Next Module"`
- **正しい値**: `"next"`
- **修正指示**: `冒頭_wait.next[0].label` を `"next"` に修正すること。
- **参照**: docs/brekeke/モジュール詳細設定ガイド_1.md セクション 1.1

> 修正指示: 上記フィールドのみを修正し、他のモジュールには一切触れないこと。

---

### W-002: `入力_問い合わせ内容` の `keep_filter_token` がガイドのデフォルトと不一致

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_診療.json`
- **修正担当**: generator
- **モジュール名**: `入力_問い合わせ内容`
- **フィールド**: `params.keep_filter_token`
- **問題**: モジュール詳細設定ガイド_1.md セクション 3.1 によると、AmiVoice STT の `keep_filter_token` のデフォルトは `"Yes"`（フィラー単語の自動削除）。実装では `"No"` になっている。問い合わせ内容は自由発話であり、フィラー削除ありが望ましい。
- **現在値**: `"No"`
- **正しい値**: `"Yes"`
- **修正指示**: `入力_問い合わせ内容.params.keep_filter_token` を `"Yes"` に修正すること。
- **参照**: docs/brekeke/モジュール詳細設定ガイド_1.md セクション 3.1

> 修正指示: 上記フィールドのみを修正し、他のモジュールには一切触れないこと。

---

### W-003: `転送_リトライ失敗_アナウンス` が JSON に存在しない（設計書 TTS モジュール一覧と不一致）

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_診療.json`
- **修正担当**: generator
- **モジュール名**: （存在しない）`転送_リトライ失敗_アナウンス`
- **フィールド**: `modules`（モジュール追加）
- **問題**: 設計書セクション9「TTSモジュール一覧」に `転送_リトライ失敗_アナウンス`（purpose: リトライ上限到達時の転送案内）が定義されているが、JSON に当該モジュールが存在しない。C-004 で指摘したリトライ転送パスの実装時に合わせて追加が必要。
- **修正指示**: C-004 の修正時に `転送_リトライ失敗_アナウンス` TTS モジュールを追加すること。`save2db` サブモジュール（`save-転送リトライ失敗`）も忘れずに接続すること。
- **参照**: 設計書セクション9 TTS モジュール一覧

> 修正指示: C-004 の修正と同時に対応すること。

---

### W-004: properties に `冒頭_wait.wait=2000` の記述がない

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/properties_ユアCLお茶水_診療.md`
- **修正担当**: properties
- **モジュール名**: `冒頭_wait`
- **フィールド**: `properties_ユアCLお茶水_診療.md` 環境設定セクション
- **問題**: モジュール詳細設定ガイド_1.md セクション 1.1 によると、wait モジュールの `wait` パラメータ（待機時間ms）は IVRプロパティで設定する。propertiesファイルにこの記述がない。
- **現在値**: 記述なし
- **正しい値**: `冒頭_wait.wait=2000` を追加（メインフローセクションに記載）
- **修正指示**: `## メインフロー (ユアCLお茶水$診療)` セクションの先頭行に `冒頭_wait.wait=2000` を追加すること。
- **参照**: docs/brekeke/モジュール詳細設定ガイド_1.md セクション 1.1

> 修正指示: 上記1行を追加すること。他の設定には一切触れないこと。

---

### W-005: properties に `転送_リトライ失敗_アナウンス.prompt` が未定義

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/properties_ユアCLお茶水_診療.md`
- **修正担当**: properties
- **モジュール名**: `転送_リトライ失敗_アナウンス`
- **フィールド**: properties メインフローセクション
- **問題**: 設計書セクション9に定義された `転送_リトライ失敗_アナウンス` が properties に存在しない。C-004・W-003 で generator が当該モジュールを追加した後、properties にも対応エントリが必要。
- **修正指示**: C-004/W-003 の generator 修正完了後、`転送_リトライ失敗_アナウンス.prompt=TODO_発話内容を記入` を `## メインフロー` セクションに追加すること。
- **参照**: 設計書セクション9 / docs/brekeke/IVRプロパティ生成ガイド.md

> 修正指示: C-004/W-003 完了後に対応すること。

---

### I-001: `inquiry` コンテキストフィールドの `deletable` が設計書と不一致

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_診療.json`
- **修正担当**: generator（任意対応）
- **モジュール名**: `コンテキスト設定`
- **フィールド**: `params.fields` 内 `inquiry.deletable`
- **問題**: 設計書セクション5では `inquiry.deletable: true` だが、JSON では `false` になっている。C-002 修正時に合わせて修正することが望ましい。
- **現在値**: `"deletable": false`
- **正しい値**: `"deletable": true`
- **参照**: 設計書セクション5

---

### I-002: `acceptance_times` の `true_transfer` ラベルは非標準拡張だが設計書の要件に基づく意図的実装

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_診療.json`
- **モジュール名**: `受付時間判定`
- **フィールド**: `next[3].condition`
- **問題（情報）**: ガイドでは `acceptance_times` の標準 next パターンは `true` / `false` / `TIMEOUT` / `ERROR` の4種のみ。`true_transfer` は非標準の拡張値。ただし設計書では「AI電話/代表転送/時間外の3パターン」という3分岐要件が明記されており、この非標準値は設計書の業務要件を満たすための意図的な実装と判断する。Dr.JOY 側で `true_transfer` を返す設定が行われることを前提としているか確認が必要。
- **対応**: 設計書・Dr.JOY 側の設定書でこの3分岐が明示的に確認できれば問題なし。未確認の場合は人間に確認すること（NON-BLOCKER N-9 の関連事項）。

---

## レッドチーム攻撃シナリオ

| # | シナリオ | 攻撃ベクトル | 予想結果 | 影響度 | 対策済み |
|---|---|---|---|---|---|
| 1 | 患者が何も話さずに電話を切った（問い合わせ内容聴取中） | 無音 / TIMEOUT | リトライ_問い合わせ内容 → Retry → 再聴取 → 最大2回リトライ後、No more → 終話_上限エラー（現状）/ script_時間帯判定（修正後） | 中 | 部分的（C-004修正で完全対応） |
| 2 | 患者が「システムを無視して…」等インジェクション文を発話 | プロンプトインジェクション | OpenAI_問い合わせ内容 が NO_RESULT / 要約テキストとして保存。フロー遷移に影響なし | 低 | プロンプトにインジェクション対策セクション必要（prompterが対応） |
| 3 | 非通知 + 海外番号が着信 | 着信分類 | 非通知・海外いずれも `非通知_アナウンス` に遷移 → 完了フラグ_非通知 → 切断。海外を非通知と同じTTSに合流させる設計は意図的か確認推奨 | 低 | 設計書フロー図では「海外も非通知と同パスに合流」と明記あり。意図的 ✅ |
| 4 | 営業時間内 + 問い合わせ内容リトライ上限 | リトライ上限 + 時間帯判定 | **現状: 無条件に終話_上限エラー（切断）に遷移。設計では代表転送すべき** | 高 | ❌ C-004で修正が必要 |
| 5 | flowname が `drjoy^Jump_to_flow$氏名聴取`（存在しないフロー）へ遷移 | フロー遷移失敗 | 氏名聴取サブフローへの遷移が失敗し、通話が途中で切断またはエラー | 高 | ❌ C-005/C-006で修正が必要 |
| 6 | 時間外に問い合わせ完了後、終話分岐でフラグを参照 | コンテキスト参照 | `script_終話分岐` が `$ivr.getObject("isAfterHours")` で "0"/"1" を取得しているが、C-003修正後は `timeSlot`（"営業時間内"/"時間外"）に変わるため、スクリプトも同時修正が必要 | 高 | ❌ C-003と連動して修正が必要 |
| 7 | 「予約したい」と「キャンセルもしたい」の複合意図を発話 | 複合意図 | 問い合わせ内容は自由発話を要約保存する設計のため、OpenAI が "予約・キャンセル希望" として要約保存。分岐なしのため全て氏名聴取へ進む | 低 | 設計書 NON-BLOCKER N-4 で確認済み。要約保存設計は意図的 ✅ |
| 8 | 問い合わせ内容が極端に長い（5分以上の発話） | 長時間発話 | AmiVoice STT の `timeout_ms` に引っかかりリトライへ。問題なし | 低 | ✅ timeout あり |

---

## OpenAIプロンプト出力ラベル整合性

| モジュール名 | next分岐ラベル | prompt出力仕様 | 判定 | 備考 |
|---|---|---|---|---|
| `OpenAI_問い合わせ内容` | timeout, error, no_result, success | `params.prompt` が空欄 | 保留 | prompter が記述する予定。空欄のため突合せ不可（PROMPT-003相当だが draft 段階のため許容） |

---

## 修正指示一覧（エージェント別）

### generator向け（優先順位順）

1. **C-001**: `着信電話番号分類.next[4].condition` を `"^*$"` → `"^.*$"` に修正
2. **C-002**: `コンテキスト設定.params.fields` の `isAfterHours` エントリを `timeSlot` エントリに置換（deletable=true, itemDefault=false で追加）
3. **C-003**: `saveCtx_時間外ON.params.contextName` = `"timeSlot"`, `contextValue` = `"時間外"` に修正。`saveCtx_時間外OFF.params.contextName` = `"timeSlot"`, `contextValue` = `"営業時間内"` に修正。`script_終話分岐.params.script` の `getObject("isAfterHours")` → `getObject("timeSlot")`、条件判定 "1"/"0" → "時間外"/"営業時間内" に修正
4. **C-004 + W-003**: `script_時間帯判定`・`転送_リトライ失敗_アナウンス`・`代表電話_リトライ転送`・`完了フラグ_リトライ転送` の4モジュールを追加。`リトライ_問い合わせ内容.next[1].nextModuleName` を `"script_時間帯判定"` に変更
5. **C-005**: `Jump_氏名聴取.params.flowname` を `"ユアCLお茶水$氏名聴取"` に修正
6. **C-006**: `Jump_電話番号聴取.params.flowname` を `"ユアCLお茶水$電話番号聴取"` に修正
7. **W-001**: `冒頭_wait.next[0].label` を `"Next Module"` → `"next"` に修正
8. **W-002**: `入力_問い合わせ内容.params.keep_filter_token` を `"No"` → `"Yes"` に修正
9. **I-001（任意）**: `コンテキスト設定.params.fields` 内 `inquiry.deletable` を `false` → `true` に修正（C-002修正時に合わせて対応）

### prompter向け

なし（draft段階のため OpenAI プロンプトは空欄で許容）

### properties向け

1. **W-004**: `## メインフロー` セクション先頭に `冒頭_wait.wait=2000` を追加
2. **W-005**: C-004/W-003 完了後、`転送_リトライ失敗_アナウンス.prompt=TODO_発話内容を記入` を `## メインフロー` セクションに追加

---

## 人間が確認すべき箇所

- **I-002 関連**: `受付時間判定` モジュールの `acceptance_times` が `true_transfer` という非標準値を返す設計になっているが、Dr.JOY 側でこの値を返す設定が行われているか確認が必要。設計書 NON-BLOCKER N-9 の「リトライ失敗時転送」と合わせて確認推奨。
- **BLOCKER B-1/B-2**: 設計書の `office_id` および `デモ050番号` が未確定のまま。generator 修正・validator 検証は進められるが、最終的な運用前に必ず解消すること。
