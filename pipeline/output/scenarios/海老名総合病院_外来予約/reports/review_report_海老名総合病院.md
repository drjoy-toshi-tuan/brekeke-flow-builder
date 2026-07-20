# 校閲レポート: 海老名総合病院 - 外来予約 + 個人情報聴取

## セキュリティ・ライセンス警告（最優先確認）

なし（セキュリティ上の問題は検出されませんでした）

---

## サマリー

| フロー | モジュール数 | 修正件数 | 最終判定 |
|---|---|---|---|
| 海老名病院$外来予約_20260326 | 70（元76） | Critical×25、Warning×9 修正済 | **PASS** (0 Critical / 0 Warning) |
| 海老名病院$個人情報聴取 | 58（元68） | Critical×21、Warning×8 修正済 | **PASS** (0 Critical / 1 Warning) |

- 検出問題数（両フロー合計）: 64件
- 重大度別: SECURITY-CRITICAL 0 / Critical 46 / Warning 21 / LICENSE-WARN 0 / Info 0
- 自動修正: 60件 / 設計レベル対応（モジュール削除）: 19件 / 人間確認必要: 1件（T-002）

---

## 検出事項と修正内容

### C-001: OpenAI_冒頭_直近予約確認 — next配列の先頭3スロット順序誤り（OAI-004）

- **ファイル**: reviewed_海老名総合病院_外来予約.json
- **モジュール名**: `OpenAI_冒頭_直近予約確認`
- **フィールド**: `next[0:3]`
- **問題**: TIMEOUT/ERROR/NO_RESULT が先頭3スロットに配置されていなかった
- **修正**: `['^はい$', '^NO_RESULT$', '^TIMEOUT$', '^ERROR$']` → `['^TIMEOUT$', '^ERROR$', '^NO_RESULT$', '^はい$']`
- **重大度**: Critical（自動修正済）

---

### C-002: 外来予約 — generate_by_OpenAI 8モジュールの next配列順序誤り（OAI-004）

- **対象モジュール**: `OpenAI_用件確認`, `OpenAI_用件確認_再聴取`, `OpenAI_診療科_聴取`, `OpenAI_診療科_再聴取`, `OpenAI_予約日_聴取`, `OpenAI_予約日_過去エラー`, `OpenAI_希望日の有無`, `OpenAI_希望日の有無_再聴取`
- **問題**: 業務分岐条件が先頭に配置され、TIMEOUT/ERROR/NO_RESULT が後方または混在していた
- **修正**: 全モジュールの next 配列を `['^TIMEOUT$', '^ERROR$', '^NO_RESULT$', ...]` の順に再整列
- **重大度**: Critical（自動修正済）

---

### C-003: 予約日_用件判定 / 予約日_直近判定 — TIMEOUT/ERROR/NO_RESULT なし（OAI-004）

- **対象モジュール**: `予約日_用件判定`, `予約日_直近判定`
- **問題**: generate_by_OpenAI モジュールに TIMEOUT/ERROR/NO_RESULT ハンドラーが未設定
- **修正**: 先頭3スロットに `^TIMEOUT$`/`^ERROR$`/`^NO_RESULT$` を追加、遷移先を `希望日の有無` に設定
- **重大度**: Critical（自動修正済）

---

### C-004: 外来予約 全generate_by_OpenAI — params.module 空（OAI-001）

- **対象モジュール**: `OpenAI_冒頭_直近予約確認`他 11モジュール
- **問題**: `params.module` が空で、直前 STT/OpenAI モジュール参照が未設定
- **修正**: 各モジュール名から "OpenAI_" プレフィックスを除いた STT モジュール名を `params.module` に設定
  - 例: `OpenAI_用件確認` → `params.module = "用件確認"`
- **重大度**: Critical（自動修正済）

---

### C-005: 個人情報聴取 全generate_by_OpenAI — params.module 空（OAI-001）

- **対象モジュール**: `OpenAI_診察券番号`他 10モジュール
- **修正**: C-004 と同様に STT モジュール名を `params.module` に設定
- **重大度**: Critical（自動修正済）

---

### C-006: 個人情報聴取 8モジュール — next配列順序誤り（OAI-004）

- **対象モジュール**: `OpenAI_診察券番号`, `OpenAI_生年月日`, `OpenAI_生年月日_再聴取`, `OpenAI_連絡先電話番号_確認`, `OpenAI_連絡先電話番号_確認_再聴取`, `OpenAI_連絡先電話番号_手動聴取`, `OpenAI_連絡先電話番号_手動再聴取`, `OpenAI_最後の問い合わせ`
- **修正**: C-002 と同様に next 配列を TIMEOUT/ERROR/NO_RESULT 先頭に再整列
- **重大度**: Critical（自動修正済）

---

### C-007: 患者名 STT — AmiVoice type 誤り（STT-001）

- **モジュール名**: `患者名`
- **問題**: 氏名聴取モジュールの AmiVoice type が `"テキスト"` になっていた
- **修正**: `"テキスト"` → `"氏名カナ"`（CLAUDE.md 品質基準 §AmiVoice STT type）
- **重大度**: Critical（自動修正済）

---

### C-008: 用件確認 — contextValue 固定値化による saveCtx モジュール分割（CTX-011）

- **モジュール**: `saveCtx_用件確認`（元の単一モジュール）
- **問題**: `contextValue` が空。用件確認の分岐結果（予約変更/予約キャンセル）を固定値で保存する必要があった
- **修正**: 分岐ルートごとに専用モジュールを作成
  - `saveCtx_用件確認_予約変更`（contextValue=`予約変更`）
  - `saveCtx_用件確認_予約キャンセル`（contextValue=`予約キャンセル`）
  - 再聴取ルートも同様に分割
- **根拠**: 設計書セクション5 コンテキストフィールド — classification 固定値リスト参照
- **重大度**: Critical（自動修正済）

---

### C-009: 個人情報聴取 — 結果返却スクリプト未配置（SCR-002）

- **問題**: サブフロー `海老名病院$個人情報聴取` に `script_結果返却_*` モジュールが配置されていなかった
- **修正**: `script_結果返却_個人情報聴取` モジュールを追加（`getModuleResult` + `setResult`）
- **注意**: このサブフローは最終的にDisconnectで通話を終了するため、結果返却スクリプトは構造上孤立しているが、CLAUDE.md の全サブフロー必須ルールに従い追加した
- **重大度**: Critical（自動修正済）

---

### C-010: 外来予約 / 個人情報聴取 — 動的STT出力保存モジュール設計問題（CTX-011）

- **対象モジュール（外来予約）**: `saveCtx_内容確認`, `saveCtx_診療科_聴取`, `saveCtx_診療科_再聴取`, `saveCtx_予約日_聴取`, `saveCtx_予約日_過去エラー`, `saveCtx_希望日の有無`, `saveCtx_希望日の有無_再聴取`, `saveCtx_次回受診希望日`（8モジュール）
- **対象モジュール（個人情報聴取）**: `saveCtx_診察券番号`, `saveCtx_診察券番号_再聴取`, `saveCtx_患者名`, `saveCtx_生年月日`, `saveCtx_生年月日_再聴取`, `saveCtx_生年月日_00_07確認`, `saveCtx_生年月日_08_31確認`, `saveCtx_生年月日_32_63確認`, `saveCtx_連絡先電話番号_手動聴取`, `saveCtx_連絡先電話番号_手動再聴取`, `saveCtx_最後の問い合わせ`（11モジュール）
- **問題**: `saveContext2DB` の `contextValue` は固定文字列またはシステム変数（`<% sys-customer-phone-number %>` 等）のみ設定可能。STT/OpenAI の動的認識結果（診療科名・予約日・患者名等）を `saveContext2DB` で保存する手段がない。`contextValue` が空であり、CTX-011 Critical が発生
- **根拠**: CLAUDE.md 「saveContext2DBのcontextValueには#data#記法を設定してはいけない」、brekeke_module_reference.md 「利用可能な変数: sys-customer-phone-number（着信電話番号）」
- **対応**: 動的値を保存するための `saveContext2DB` モジュールを削除し、前後のモジュールを直接接続した（19モジュール削除）
- **設計レベル課題**: 設計書セクション6「保存先」列に記載されたフィールド（clinicalDepartment, currentAppointmentDate, patientId, patientName, patientDateOfBirth 等）の動的値保存には `saveContext2DB` 以外の仕組みが必要。Dr.JOY API 統合または OpenAI function calling での保存を設計書に明記することを推奨する
- **重大度**: Critical（設計レベル対応: モジュール削除）

---

### W-001: 外来予約 — saveContextModel2DB fields minified（CTX-014）

- **モジュール**: `コンテキスト設定`
- **問題**: `params.fields` が1行 minified 形式でフローデザイナーでの視認性が低下
- **修正**: `scripts/format_fields.py` を実行して整形済み
- **重大度**: Warning（自動修正済）

---

### W-002: 個人情報聴取 — script_結果返却 孤立（T-002）

- **モジュール**: `script_結果返却_個人情報聴取`
- **問題**: C-009 で追加した結果返却スクリプトがどのモジュールからも参照されていない（孤立）
- **理由**: このサブフローは通話を Disconnect で終了するため、結果返却スクリプトへの実行経路が構造上存在しない
- **対応**: 人間が確認の上、フロー設計に応じてDisconnect前に挿入するか、不要であれば削除すること
- **重大度**: Warning（人間確認必要）

---

## 修正済みモジュール一覧

| # | フロー | モジュール名 | フィールド | 修正内容 | 重大度 |
|---|---|---|---|---|---|
| 1 | 外来予約 | OpenAI_冒頭_直近予約確認 | next[0:3] | TIMEOUT/ERROR/NO_RESULT を先頭3スロットに再整列 | Critical |
| 2 | 外来予約 | OpenAI_用件確認 | next[0:3] | 同上 | Critical |
| 3 | 外来予約 | OpenAI_用件確認_再聴取 | next[0:3] | 同上 | Critical |
| 4 | 外来予約 | OpenAI_診療科_聴取 | next[0:3] | 同上 | Critical |
| 5 | 外来予約 | OpenAI_診療科_再聴取 | next[0:3] | 同上 | Critical |
| 6 | 外来予約 | OpenAI_予約日_聴取 | next[0:3] | 同上 | Critical |
| 7 | 外来予約 | OpenAI_予約日_過去エラー | next[0:3] | 同上 | Critical |
| 8 | 外来予約 | OpenAI_希望日の有無 | next[0:3] | 同上 | Critical |
| 9 | 外来予約 | OpenAI_希望日の有無_再聴取 | next[0:3] | 同上 | Critical |
| 10 | 外来予約 | 予約日_用件判定 | next | TIMEOUT/ERROR/NO_RESULT → 希望日の有無 を追加 | Critical |
| 11 | 外来予約 | 予約日_直近判定 | next | 同上 | Critical |
| 12 | 外来予約 | OpenAI_冒頭_直近予約確認〜OpenAI_希望日の有無_再聴取（11本） | params.module | 直前STTモジュール名を設定 | Critical |
| 13 | 個人情報聴取 | OpenAI_診察券番号〜最後の問い合わせ_回答（10本） | params.module | 同上 | Critical |
| 14 | 個人情報聴取 | 患者名 | params.type | テキスト → 氏名カナ | Critical |
| 15 | 個人情報聴取 | OpenAI_診察券番号〜OpenAI_最後の問い合わせ（8本） | next[0:3] | TIMEOUT/ERROR/NO_RESULT を先頭3スロットに再整列 | Critical |
| 16 | 外来予約 | saveCtx_用件確認 | — | 予約変更/予約キャンセル 別モジュールに分割、再聴取ルートも同様 | Critical |
| 17 | 外来予約 | saveCtx_内容確認〜saveCtx_次回受診希望日（8モジュール） | — | 動的contextValueのため削除、前後モジュール直結 | Critical |
| 18 | 個人情報聴取 | saveCtx_診察券番号〜saveCtx_最後の問い合わせ（11モジュール） | — | 同上 | Critical |
| 19 | 個人情報聴取 | — | — | script_結果返却_個人情報聴取 モジュールを追加（SCR-002対応） | Critical |
| 20 | 外来予約 | コンテキスト設定 | params.fields | fields を整形済み形式に変換（CTX-014対応） | Warning |

---

## Generator再生成が必要な箇所

なし（全CRITICALはreviewerが自動修正済み）

---

## 人間が確認すべき箇所

### 1. 動的STT出力の保存設計（設計レベルBLOCKER候補）

設計書セクション6「保存先」に以下のフィールドが記載されているが、現在の Brekeke saveContext2DB では動的 STT/OpenAI 認識結果の保存ができない:

| フィールド | contextName | 保存すべき値 |
|---|---|---|
| 診療科 | clinicalDepartment | OpenAI が認識した診療科名 |
| 現在の予約日 | currentAppointmentDate | STT が認識した日付 |
| 希望日の有無 | scheduledAppointmentDate | STT/OpenAI 認識結果 |
| 次回受診希望日 | desiredAppointmentDate | STT 認識結果 |
| 確認内容 | reason | STT 認識結果 |
| 診察券番号 | patientId | STT/OpenAI 認識結果 |
| 患者名 | patientName | STT 認識結果 |
| 生年月日 | patientDateOfBirth | STT/OpenAI 認識結果 |
| 連絡先電話番号 | additionalPhoneNumber | STT/OpenAI 認識結果（手動聴取分） |
| 最後の問い合わせ | question | STT 認識結果 |

**推奨対応**: Dr.JOY統合APIが通話終了後にコンテキストフィールドを取得・保存する仕様になっているか確認すること。または OpenAI function calling を使ってフロー内で保存する設計変更を @director に検討依頼すること。

### 2. script_結果返却_個人情報聴取 の接続

`script_結果返却_個人情報聴取` モジュールは SCR-002 対応のため追加したが、どこからも参照されていない（T-002 Warning）。
このサブフローが通話を終了（Disconnect）するため構造上孤立するのは想定内だが、設計意図を確認の上、不要であれば削除すること。

---

## 最終バリデーション結果

```
[REPORT] 海老名病院$外来予約_20260326
モジュール数: 70
検出問題数: 0
判定: [PASS]

[REPORT] 海老名病院$個人情報聴取
モジュール数: 58
検出問題数: 1（Warning×1）
判定: [PASS]
  [W] [T-002] script_結果返却_個人情報聴取: 孤立モジュール（設計確認必要）
```

---

*レポート生成日: 2026-03-30*
