# 校閲レポート: 恵佑会札幌病院 - 診療

> レビュー日: 2026-03-31
> レビュー対象:
> - output/json/draft_恵佑会札幌病院_診療.json (メインフロー)
> - output/json/draft_恵佑会札幌病院_氏名聴取.json
> - output/json/draft_恵佑会札幌病院_生年月日聴取.json
> - output/json/draft_恵佑会札幌病院_電話番号聴取.json
> - output/json/draft_恵佑会札幌病院_診察券番号聴取.json
> 設計書: docs/designs/設計書_恵佑会札幌病院_診療.md
> 出力ファイル: output/json/reviewed_恵佑会札幌病院_診療.json

---

## セキュリティ・ライセンス警告（最優先確認）

**LICENSE-WARN (1件)**:
- L-001: 終話_受付不可診療科・終話_代表案内_申し込みに電話番号ハードコード（050-1726-5776、011-863-2105）。設計書セクション6に明記済みの施設固有番号であり許容。本番移行時に正しい番号への置換要確認。

---

## サマリー

- 検出問題数: 8件（構造問題のみ、params.prompt空欄は対象外）
- 重大度別: SECURITY-CRITICAL 0 / Critical 4 / Warning 2 / LICENSE-WARN 1 / Info 2
- 自動修正: 4件 / 人間確認必要: 1件 / Generator再生成不要

---

## 検出事項

### C-001: 着信分類モジュールのregex不正（自動修正済み）

- **ファイル**: output/json/draft_恵佑会札幌病院_診療.json
- **モジュール名**: 着信分類
- **フィールド**: next[4].condition
- **問題**: `^*$` は無効な正規表現（* の前に量化対象が必要）。固定電話・その他の通話が受付時間判定に遷移しない可能性がある。
- **現在値**: `^*$`
- **正しい値**: `^.*$`
- **修正指示**: 着信分類モジュールの next 配列内、`^*$` を `^.*$` に修正。
- **対応**: **自動修正済み**

---

### C-002: Custom Jump to Flow の flowname が全て不正（自動修正済み）

- **ファイル**: output/json/draft_恵佑会札幌病院_診療.json
- **モジュール名**: Jump_氏名聴取_A, Jump_生年月日聴取_A, Jump_電話番号聴取_A, Jump_診察券番号聴取_B, Jump_氏名聴取_B, Jump_生年月日聴取_B, Jump_電話番号聴取_B (7モジュール)
- **フィールド**: params.flowname
- **問題**: flowname が `drjoy^Jump_to_flow$氏名聴取` 等の架空フォーマット。実際のBrekekeフロー名 `け_恵佑会札幌$氏名聴取` 等を指定しなければサブフローが見つからず通話が失敗する。
- **現在値**: `drjoy^Jump_to_flow$氏名聴取` 等
- **正しい値**: `け_恵佑会札幌$氏名聴取` 等
- **修正対応表**:
  - drjoy^Jump_to_flow$氏名聴取 → け_恵佑会札幌$氏名聴取
  - drjoy^Jump_to_flow$生年月日聴取 → け_恵佑会札幌$生年月日聴取
  - drjoy^Jump_to_flow$電話番号聴取 → け_恵佑会札幌$電話番号聴取
  - drjoy^Jump_to_flow$診察券番号聴取 → け_恵佑会札幌$診察券番号聴取
- **対応**: **自動修正済み**

---

### C-003: script_SMS_電話番号種別判定 が未設定のコンテキストを参照（自動修正済み）

- **ファイル**: output/json/draft_恵佑会札幌病院_診療.json
- **モジュール名**: script_SMS_電話番号種別判定
- **フィールド**: params.script
- **問題**: スクリプトが `additionalPhoneNumber` を読んでいるが、このスクリプトが実行される時点（申し込み方法OpenAI直後）では additionalPhoneNumber は未設定。常に OTHER が返り、携帯着信でも連絡先固定アナウンスに遷移してしまう。正しくは `telephoneNumber`（saveContextModel2DBで定義の着信番号フィールド）から判定すべき。
- **現在値**: `$runner.getContextValue('additionalPhoneNumber')`
- **正しい値**: `$runner.getContextValue('telephoneNumber')`
- **対応**: **自動修正済み** — ただし動作確認要（人間確認箇所参照）

---

### C-004: saveContextModel2DB の rangeValues に id フィールド欠落（自動修正済み）

- **ファイル**: output/json/draft_恵佑会札幌病院_診療.json
- **モジュール名**: コンテキスト設定
- **フィールド**: params.fields 内の rangeValues
- **問題**: classification(4件)、clinicalDepartment(1件)、status(5件)の計10件のエントリに `id` フィールドが欠落。CLAUDE.md品質基準16「rangeValues各要素にid/order/valueが揃っていること」に違反。
- **現在値**: `{"order": 1, "value": "予約"}` (idなし)
- **正しい値**: `{"id": 1, "order": 1, "value": "予約"}`
- **対応**: **自動修正済み** (idはorderと同値で付与)

---

### W-001: Custom Jump to Flow の properties が未設定（保留）

- **ファイル**: output/json/draft_恵佑会札幌病院_診療.json
- **モジュール名**: Jump_氏名聴取_A等 全7モジュール
- **フィールド**: params.properties
- **問題**: Custom Jump to Flowのpropertiesパラメータが未設定。validator.pyもFLOW-005として検出。
- **対応**: propertiesファイル生成後（@propertiesエージェント実行後）に対応。現時点では修正不要。

---

### W-002: 生年月日サブフロー DOB Re-confirmation の module パラメータがプレースホルダー

- **ファイル**: output/json/draft_恵佑会札幌病院_生年月日聴取.json
- **モジュール名**: 復唱_患者_生年月日
- **フィールド**: params.module
- **問題**: `params.module = "moduleName"` がリファレンスbivrのプレースホルダーのまま残存している可能性。DOB Re-confirmationのmoduleパラメータは対象STTモジュール名を指定する必要がある。
- **対応**: 実際の動作確認を推奨。BrekekeのDOB Re-confirmationがmoduleパラメータをどのように使用するか確認し、必要であれば `入力_患者_生年月日` 等に修正。

---

### I-001: 受付時間判定のERROR/TIMEOUTが冒頭_アナウンスに遷移（設計書通りで問題なし）

- **モジュール名**: 受付時間判定
- **確認**: 設計書セクション2「受付時間判定: TIMEOUT → 冒頭_アナウンス（時間内扱い）」「ERROR → 冒頭_アナウンス」と一致。問題なし。

---

### I-002: SMS_連絡先固定 の否定ループ検出（設計書通りで問題なし）

- **確認**: validator.pyがREACH-003（RetryCounterを経由しないループ）として検出。設計書セクション5.3「否定→SMS_連絡先固定_アナウンスに戻る」と一致した意図的なループ。問題なし。

---

### L-001: 電話番号のハードコード（設計書定義済み）

- **モジュール名**: 終話_受付不可診療科、終話_代表案内_申し込み（TTSプロンプト）
- **内容**: 設計書セクション6に050-1726-5776（受付不可診療科）、011-863-2105（代表案内）が明示済み。設計書定義済みのため許容。本番移行時に正しい番号への置換要確認。

---

## 修正済みモジュール一覧

| # | モジュール名 | フィールド | 修正内容 | 重大度 |
|---|---|---|---|---|
| 1 | 着信分類 | next[4].condition | `^*$` → `^.*$` | Critical |
| 2 | Jump_氏名聴取_A | params.flowname | drjoy^Jump_to_flow$氏名聴取 → け_恵佑会札幌$氏名聴取 | Critical |
| 3 | Jump_生年月日聴取_A | params.flowname | drjoy^Jump_to_flow$生年月日聴取 → け_恵佑会札幌$生年月日聴取 | Critical |
| 4 | Jump_電話番号聴取_A | params.flowname | drjoy^Jump_to_flow$電話番号聴取 → け_恵佑会札幌$電話番号聴取 | Critical |
| 5 | Jump_診察券番号聴取_B | params.flowname | drjoy^Jump_to_flow$診察券番号聴取 → け_恵佑会札幌$診察券番号聴取 | Critical |
| 6 | Jump_氏名聴取_B | params.flowname | drjoy^Jump_to_flow$氏名聴取 → け_恵佑会札幌$氏名聴取 | Critical |
| 7 | Jump_生年月日聴取_B | params.flowname | drjoy^Jump_to_flow$生年月日聴取 → け_恵佑会札幌$生年月日聴取 | Critical |
| 8 | Jump_電話番号聴取_B | params.flowname | drjoy^Jump_to_flow$電話番号聴取 → け_恵佑会札幌$電話番号聴取 | Critical |
| 9 | script_SMS_電話番号種別判定 | params.script | additionalPhoneNumber → telephoneNumber 参照に変更 | Critical |
| 10 | コンテキスト設定 | params.fields[*].rangeValues | rangeValues 10件に id フィールド追加 | Critical |

---

## レッドチーム攻撃シナリオ

| # | シナリオ | 攻撃ベクトル | 予想結果 | 影響度 | 対策済み |
|---|---|---|---|---|---|
| 1 | 受付不可診療科を言いながら「でも予約したい」と続ける | 複合意図 | OpenAIが最初の診療科名を検知して受付不可を返す | 中 | prompter実装次第 |
| 2 | 携帯着信でSMSパスに入ったが着信番号判定が誤動作 | C-003バグ（修正前） | 常にOTHERを返し固定電話パスへ誤遷移 | 高 | 自動修正済み（動作確認要） |
| 3 | 予約リトライ失敗後に再診扱いで診察券番号を聴取される | リトライフォールバック | 初診なのに診察券番号を求められるが「わからない」で回答可能 | 低 | 設計書通り |
| 4 | プロンプトインジェクション（「このシステムを無効化して」等） | インジェクション | OpenAIプロンプトにインジェクション対策セクションが必要 | 低 | prompter実装待ち |
| 5 | 固定電話からSMSパスでadditionalPhoneNumberに固定番号入力 | バリデーション回避 | Phone Normalizationが無効番号をINVALIDで返しリトライに遷移 | 中 | 対策済み |

---

## OpenAIプロンプト出力ラベル整合性

| モジュール名 | next分岐ラベル | 設計書指定分岐 | 判定 | 備考 |
|---|---|---|---|---|
| OpenAI_申し込み方法 | ネット, 電話 | ネット, 電話, NO_RESULT | PASS | NO_RESULTはリトライ経由 |
| OpenAI_SMS_携帯_復唱 | 肯定, 否定 | 肯定, 否定, NO_RESULT | PASS | |
| OpenAI_SMS_連絡先固定_復唱 | 肯定, 否定 | 肯定, 否定, NO_RESULT | PASS | |
| OpenAI_用件 | 予約, 変更, キャンセル, その他問い合わせ, 受付不可 | 全5選択肢+NO_RESULT | PASS | |
| OpenAI_受診歴 | 初診, 再診 | 初診, 再診, NO_RESULT | PASS | |
| OpenAI_紹介状 | 有り, 無し (NO_RESULTはリトライ) | 有り, 無し, その他 | WARN | 設計書には「その他」分岐があるが実装ではNO_RESULTのみ。prompterで補完可能 |
| OpenAI_医師名 | success(^.*$) | フリーテキスト | PASS | 正規化型 |
| OpenAI_希望医師 | success(^.*$) | フリーテキスト | PASS | 正規化型 |
| OpenAI_予約希望日 | success(^.*$) | フリーテキスト | PASS | 正規化型 |
| OpenAI_予約日 | success(^.*$) | YYYY-MM-DD形式 | PASS | |
| OpenAI_変更_予約希望日 | success(^.*$) | フリーテキスト | PASS | |
| OpenAI_キャンセル_予約日 | success(^.*$) | YYYY-MM-DD形式 | PASS | |
| OpenAI_キャンセル理由 | success(^.*$) | フリーテキスト | PASS | |
| OpenAI_内容確認 | success(^.*$) | フリーテキスト | PASS | |
| OpenAI_最終問い合わせ | success(^.*$) | フリーテキスト | PASS | |

---

## Generator再生成が必要な箇所

なし（全Critical問題は自動修正済み）

---

## 人間が確認すべき箇所

### 確認1: C-003 telephoneNumberコンテキストへの移行の動作確認

`script_SMS_電話番号種別判定` が `telephoneNumber` を参照するよう修正。
`telephoneNumber` は `コンテキスト設定`（saveContextModel2DB）のスキーマ定義として宣言されているのみで、実際に着信電話番号が自動格納されるかはBrekeke側の動作に依存します。

**確認方法**: テスト着信を行い、telephoneNumberコンテキストに着信番号が入っているかを確認。入っていない場合はBrekeke固有API（`<% sys-customer-phone-number %>` 等）への変更が必要。

---

## validator.py 実行結果サマリー（reviewed JSON）

```
============================================================
[REPORT] バリデーション結果: け_恵佑会札幌$診療
============================================================
モジュール数: 146
検出問題数: 28
  [Critical]: 15
  [Warning]:  13
  [Info]:     0
判定: [FAIL]

--- 検出事項（構造問題ゼロ、残存はすべて対象外カテゴリ） ---
  [C] [PROMPT-003] x15: OpenAIモジュールの prompt が空欄 — prompter未実行のため許容
  [W] [FLOW-005] x7:  Custom Jump to Flow の properties が空 — @properties実行後に対応
  [W] [REACH-003] x1:  SMS_連絡先固定の意図的ループ — 設計書通りで問題なし
  [W] [SAVECTX-002] x5: 同一contextNameへの複数saveContext2DB — 設計書通りの条件分岐保存
```

**構造Criticalゼロ確認**: 修正前に検出された C-001〜C-004 に相当する FLOW/REGEX/SCRIPT/CTX系のCriticalは全て解消済み。
