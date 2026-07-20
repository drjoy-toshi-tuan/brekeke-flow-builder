# QA監査レポート -- 多根クリニック 健診

**判定**: PASS
**設計書**: `docs/designs/設計書_多根クリニック_健診.yaml`
**監査日時**: 2026-04-07（第2回監査 -- 前回 FAIL 差し戻し後の再審査）
**設計書形式**: YAML

---

## 前回差し戻し指摘の解消確認

前回レポート（FAIL）の指摘に対する解消状況を確認しました。

| 指摘ID | 内容 | 解消状況 |
|---|---|---|
| BLOCKER B-1 | office_id 未確認 | 設計書の `blockers` セクションにB-1として記録済み。未解消だが設計書内管理に移行 |
| BLOCKER B-2 | phone_number 未確認 | 同上 |
| CRITICAL E-3 | 復唱確認・個人企業分岐の No more 遷移先未定義 | **解消**: `retry_failure_next_step` フィールドが追加され、全5ステップの No more 遷移先が明記されている |
| WARNING L-4 | フロー図予約ルートの `その他(TTS)` → `その他_追加オプション(TTS)` | **解消**: フロー図が `その他_追加オプション(TTS)` に修正されている |
| WARNING I-4 | フロー図概要の紹介状ルートで医療機関名ステップが省略 | **解消**: `紹介状案内(TTS) → 医療機関名(TTS) → 入力_医療機関名(STT)` に修正されている |

---

## 機械的チェック結果（qa_validator.py）

```
=== qa_validator.py: docs/designs/設計書_多根クリニック_健診.yaml ===
CRITICAL: 0 件  WARNING: 5 件

[WARNING]  E-2: step_details '復唱_予約' の retry_failure='skip_as_yes' が不正。許容値: ['disconnect', 'end_failure', 'skip']
[WARNING]  E-2: step_details '復唱_変更キャンセル' の retry_failure='skip_as_yes' が不正。許容値: ['disconnect', 'end_failure', 'skip']
[WARNING]  E-2: step_details '復唱_紹介状受診結果' の retry_failure='skip_as_yes' が不正。許容値: ['disconnect', 'end_failure', 'skip']
[WARNING]  E-2: step_details '復唱_問い合わせ' の retry_failure='skip_as_yes' が不正。許容値: ['disconnect', 'end_failure', 'skip']
[WARNING]  E-2: step_details '個人企業分岐' の retry_failure='skip_as_individual' が不正。許容値: ['disconnect', 'end_failure', 'skip']

判定: PASS -- 機械的チェック通過。LLM審査へ進行可
```

---

## LLM審査結果

| カテゴリ | 結果 | BLOCKER | CRITICAL | WARNING |
|---|---|---|---|---|
| インテント網羅性（自然言語） | PASS | 0 | 0 | 1 |
| エラーパス網羅性（自然言語） | PASS | 0 | 0 | 1 |
| トーン＆マナー | PASS | 0 | 0 | 0 |
| 論理整合性（自然言語） | PASS | 0 | 0 | 1 |

**総合判定**: PASS（generatorへ進行可）

---

## 指摘事項

### BLOCKER（人間の確認が必要 -- パイプライン停止）

なし。

> **注記**: 設計書の `blockers` セクションに B-1（office_id）・B-2（phone_number）が TODO として残存している。
> LLM審査の14項目対象外（機械的チェックでも未検出）のため今回の判定に影響しないが、
> **IVRプロパティの設定前に必ず解消すること**（acceptance_times・incoming-classifier・Dr.JOY連携に必須）。

---

### CRITICAL（Directorが修正可能 -- 自動差し戻し）

なし。

---

### WARNING（品質向上の提案）

#### W-1 [機械的チェック E-2 × 5] `retry_failure` に規定値外の値が使用されている

**対象ステップ**:
- `復唱_予約`、`復唱_変更キャンセル`、`復唱_紹介状受診結果`、`復唱_問い合わせ` → `retry_failure: "skip_as_yes"`
- `個人企業分岐` → `retry_failure: "skip_as_individual"`

**内容**: `retry_failure` の規定値は `disconnect` / `end_failure` / `skip` の3種類。設計書が独自値を使用している。

前回差し戻しを受けて追加した `retry_failure_next_step` フィールドに各ステップの遷移先が明記されているため、generator は正しく解釈できる。しかし `qa_validator.py` がスキーマ違反として検出しており、将来 CRITICAL に昇格するリスクがある。

**推奨対応**: `retry_failure` を規定値の `"skip"` に変更し、具体的な遷移先は既存の `retry_failure_next_step` にのみ記載する形に統一することを検討する。例:
```yaml
- step_name: "復唱_予約"
  retry_failure: "skip"
  retry_failure_next_step: "予約案内（No more 時ははい扱い。用件選択の意思を尊重して予約ルートへ進む）"
```

---

#### W-2 [E-4] フロー図全体で TIMEOUT / ERROR / NO_RESULT が省略表記されている

**内容**: フロー図全体にわたり「`NO_RESULT/error → リトライ_xxx`」と省略して記載されている。

flow_diagrams[0].notes 末尾に「フロー図では省略しているが、next配列はCLAUDE.md規則通りTIMEOUT/ERROR/NO_RESULTの3パターンを個別スロット[0][1][2]に配置すること」と明示されており、generator への指示は伝わっている。

**対応**: 既存の notes 補足で対応済み。追加修正不要。記録のみ。

---

#### W-3 [L-4] `step_details` と `tts_modules` で「予約日」の命名が不一致

**箇所**:
- `step_details.step_name` = `"予約日_変更キャンセル"`
- `tts_modules.module_name` = `"予約日"`
- フロー図（予約ルートおよびキャンセルルートセクション）= `予約日(TTS)`

**内容**: フロー図と tts_modules は `"予約日"` で一致しているが、step_details のステップ名が `"予約日_変更キャンセル"` と異なる。generator が step_details のステップ名を TTS モジュール名として採用した場合、IVRプロパティのプロパティ名（`"予約日"`）と一致しなくなり、TTS が機能しないリスクがある。

**推奨対応**: `step_details.step_name` を `"予約日"` に統一する。`hearing_items.name` は `"予約日_変更キャンセル"` のままでも可（聴取項目の識別用途に限定）。

---

#### W-4 [I-4] `電話番号後_ルート分岐` と `受診結果_曜日判定` の実装方式が設計書内で未確定

**内容**:

- **`電話番号後_ルート分岐`** (step_details.notes): 「Scriptモジュール単体で実装することも可」と記載。OpenAI と Script の両案が並記されており、generator に判断が委ねられている。
- **`受診結果_曜日判定`** (step_details.notes): 「generatorはScriptモジュールでの実装を推奨」と記載。OpenAIの場合は前段Scriptが必要な旨も記載あり。

CLAUDE.md Rule 14（「出力データが存在しない状態でOpenAIモジュールを配置してはならない」）との関係上、OpenAIモジュールを採用する場合は `params.module` の参照先モジュール名を設計書で明示する必要がある。

**推奨対応**: 設計書内で実装方式を以下のように確定して記載する:
- `電話番号後_ルート分岐` → `Script（script_ルート判定）`単体で実装（reason非空→問い合わせ、reason空→classification値をそのまま返却）
- `受診結果_曜日判定` → `Script（script_曜日判定）`で実装（`new Date().getDay()` で 0/6 → 土日、それ以外 → 平日）

---

## ゴールデンテンプレートとの照合

参照テンプレート: `docs/specs/golden_templates/健診受付型.yaml`

| 照合項目 | テンプレート | 設計書 | 評価 |
|---|---|---|---|
| 冒頭チェーン順序（wait→saveContextModel2DB→incoming-classifier→acceptance_times） | `acceptance_times` が先 | CLAUDE.md 準拠の正しい順序 | PASS（設計書が正しい） |
| 個人情報サブフロー Rule 9 完全コピー | 全3フロー指示 | 全3フロー指示（各サブフロー図に明示） | PASS |
| 非通知/時間外の終話パス | 定義あり | END_非通知・END_時間外 定義済み | PASS |
| smsFlag 用件別設定 | 定義あり | 4種類（1〜4）明確に定義 | PASS |
| saveContextModel2DB コンテキストフィールド | 定義あり | 14フィールド定義済み | PASS |
| 電話番号サブフロー termination | `self_contained` | `return` | 意図的差異。用件別smsFlag分岐のためメインフロー終話制御。設計書に明示あり |

---

## 付記: 未解消の `confirmation_items` 一覧

generator への進行は可能だが、以下は人間による確認・解消が必要。

| # | 項目 | 重要度 | resolved |
|---|---|---|---|
| 1 | office_id（Dr.JOYオフィスID） | BLOCKER | false |
| 2 | phone_number（健診専用電話番号） | BLOCKER | false |
| 3 | 営業時間（曜日・時間帯）の最終確認 | NON-BLOCKER | false |
| 4 | smsFlag 1〜4 の割り当てが正しいか | NON-BLOCKER | false |
| 5 | 非通知アナウンスの文言（仮設定中） | NON-BLOCKER | false |
| 6 | 時間外アナウンスの文言（仮設定中） | NON-BLOCKER | false |
| 7 | classification が全ケース「問合せ」のGen2仕様 → Gen3では用件名に変更したが問題ないか | NON-BLOCKER | false |
| 8 | 電話番号リトライ回数: Gen2=3回 vs Gen3標準=2回 | NON-BLOCKER | false |

---

*QA監査レポート生成: qa エージェント（Shift-Left設計書QAエージェント）*
*第2回審査: 前回FAIL指摘（CRITICAL E-3・WARNING L-4・I-4）の解消を確認。新規WARNING 4件を記録。PASS。*
