# intent_classifier_v2 — 要求仕様（Evidence→Event→Rule）

- **設計正本**: `docs/governance/intent-engine-v2-design.md`
- **作成標準**: `docs/governance/script-authoring-standard.md`（§2.5: Rule は生テキストを読まない）
- **アーキテクチャ**: Normalize(+filler) → Detect Evidence(否定=`_neg`属性)
  → Build Events(fixpoint) → Apply Rules → Resolve(Specific>General・拮抗=CLARIFY) → 1テキスト出力
- **spec 起草**: `/gen-intent-spec` skill（壁打ち）/ **compile**: `tools/gen_intent_v2.py`
  （旧 intents[] 形式は auto-lower で互換）/ **scaffold**: 設計書ブロック `engine: v2`
- **preset**: `presets/yes_no.json`（否定反転・二重否定対応の yes/no）

## 入出力

- 入力: STT テキスト or DTMF（`getModuleResult`）
- setResult: `intents[].label ∪ {CLARIFY, REPEAT, NO_RESULT}`（閉集合）
  - 否定検出時は `negated_label`（未指定時 `default_negated_label`、既定 `NO_ACTION`）
- setObject: `intent_result_<step>` = 構造化結果 JSON（intent/confidence/entities/
  variables/negation/reason[]/need_clarification）— 監査・INC調査用
- 判定不能 = NO_RESULT（推測禁止）/ 候補拮抗 = CLARIFY（聞き返し）

## 分岐（wiring 側の受け）

| setResult | 遷移先 |
|---|---|
| 各 label | 業務ルート |
| CLARIFY | 聞き返し TTS → 同 STT |
| REPEAT | 同 TTS 再生 |
| NO_RESULT | リトライ |

## エッジケース（test_cases.json 準拠・40件）

- **複合文**:「7月26日に予約してるんだけど、都合がつかないので、来月で大丈夫ですか」
  → Evidence 合成（reservation+cannot_visit+future_date → WantAnotherDate）→ **変更**
- **Specific>General**:「予約をキャンセルしたい」→ キャンセル（2証拠 rule が 1証拠 rule に勝つ）
- 否定スコープ:「キャンセルしないで」→ 取りやめ /「キャンセルはやめて変更に」→ 変更
- 二重否定（yes/no preset）:「だめじゃないです」→ 肯定 /「大丈夫じゃない」→ 否定
- 拮抗:「へんこうかキャンセルか」→ CLARIFY（推測禁止・聞き返し）
- 文脈:「はい」単独は yes_no 文脈で YES・menu 文脈で CLARIFY
- REPEAT はトークン解決より優先（「もう一度お願いします」の お願いします 誤爆防止）
- filler:「えっとー、よやくを…」→ 予約 / 全角/カタカナ/DTMF/番号発話の正規化一致

## テスト状況

| 工程 | 状態 |
|---|---|
| oracle.py（Python 独立実装） | 40/40 PASS |
| test_parity.js（JS engine 実行・node） | 40/40 PASS |
| 実発話 corpus regression | 未（roadmap: extract-yesno-synonyms 経路） |
| mutation testing | 未（roadmap） |
| **P6 実機受入** | **未 — 本番投入禁止**（oracle_gate が fail-closed で担保） |
