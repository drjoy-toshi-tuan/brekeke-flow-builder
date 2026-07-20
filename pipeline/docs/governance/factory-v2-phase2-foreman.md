# factory-v2 Phase 2 — 工場長 + 壁打ち入口 + 部品カタログ（設計 / 実装メモ）

状態: **実装 v0.1（2026-06-24）**。ブランチ `feature/factory-v2-phase2-foreman`（#209 = Phase 1 から stack）。
親設計: `project-governance/initiatives/vfb-factory-restructure.md` §2-4 / `docs/loop-governance.md` §9。
本書は VFB 側（L3 フィールド）の Phase 2 実装の SSoT。**#209 は Draft 据置**・本ブランチはその上に積む。

---

## 0. 目的（浜口さん 2026-06-24 の壁打ち）

VFB v2 を「チームメンバーが各自の Claude Code から呼んで壁打ち → 工場長が認定部品を調達して組む」形にして
**手っ取り早く全体公開**し、公開後に **標準化側の成績表（coverage scorecard）に当てて 1 個ずつ育てる**。
当面の納品物 = **壁打ち入口（A）＋ 部品カタログ（B）＋ 工場長エージェント（C）** の 3 点（一括）。

> **重要な前提の訂正（2026-06-24 調査）**: 「工場長エージェントは既に存在」とされていたが、リポ全ブランチ・
> docs を確認した結果、工場長は governance に**仕様化済みだが VFB 実体は未実装**だった（`.claude/agents/` は
> director/generator/prompter/reviewer/tester/fixer/dirlite のみ）。本 Phase で**新規実装**する。

---

## 1. キーストーン（A/B/C すべてが守る）

`loop-governance §9`: **パイプライン（forward path）に入ったらテスト完了まで LLM 介入ゼロ。テスト後に動く LLM は工場長のみ。**
- LLM が立つのは**ライン前（壁打ち＝設計を人間と詰める）と後/外（工場長＝解析/レポート/調達）だけ**。
- 修復は**生成物（.bivr/JSON）でなく生成器（設計書 YAML・部品・spec-DATA）を直して再実行**。
- **認定（certified_hashes 登録）は常に人間ゲート**。工場長・入口は起票・oracle PASS まで。
- **枠（scripts/schemas/tools/.claude）変更は常に HQ + PR**。本実装も feature ブランチ → PR。

---

## 2. コンポーネント

### B. 部品カタログ INDEX — `tools/generate_parts_catalog.py`
`certified_hashes.json`(parts+specs) + 各 `part.json` を読み、機械可読 `modules/parts_catalog.json`
（＋人間向け `modules/PARTS_CATALOG.md`）を生成。工場長・入口が「今どの認定部品が調達できるか」を機械列挙する土台。
- status: `certified`(engine登録+spec認定) / `engine_only`(engineのみ) / `pending_registration`(part.json+oracle有・未登録) / `oracle_only` / `draft`。
- 決定論・stdlib・`--check` で冪等検証（CI/pre-commit 可）。SSoT は書き換えない。
- **初回生成結果**: 15 件（certified 8 / engine_only 4 / pending 2 / oracle_only 1）。

### C. 工場長エージェント — `.claude/agents/工場長.md`（Sonnet・ライン外）
テスト後に残差を triage（Case A 規格内DATA / Case B 規格不足・新部品 / Case C 上流STT/TTS）→ レポート →
**PR**(Case A・oracle再通過) / **Issue**(Case B/枠・HQ) 起票。
- **部品調達**: まず `parts_catalog.json` で在庫確認 → 賄えなければ `tools/new_part_skeleton.py` で
  認定仕様(@part-id/@spec/wiring)準拠の骨格生成 → oracle PASS まで。**実機 P6 + cert 登録は人間ゲート**。
- 自律修復しない / 認定を宣言しない / ライン内工程をいじらない。
- 補助: `tools/new_part_skeleton.py`（新部品スケルトン・決定論）。

### A. 壁打ち入口スキル — `.claude/skills/sparring-intake/SKILL.md`（メンバーが各自起動）
入力(drawio/YAML/既存BIVR)を自由ゾーンに置く → 設計書YAML化 → **壁打ちアジェンダ**生成 → 収束ループ → orchestrator → @工場長。
- 補助: `tools/sparring_agenda.py` = qa_validator(完全性) + drawio_to_scenario(surfacing調達) + parts_catalog(在庫) を 1 枚に束ねる。設計書も成果物も書き換えない。
- 既存BIVR は §1-7 フォールバック（自動 decompile しない・源YAML修正再実行 or surgical patch）。

---

## 3. E2E 再現（golden fixture）

```bash
# emitter → 壁打ちアジェンダ の全鎖（任意の作業フォルダで）
python3 tools/generate_parts_catalog.py
python3 scripts/scenario_from_drawio.py scripts/drawio_parser_fixtures/shinryo_composer_golden.drawio \
    -o output/scenarios/<tmp>/設計書_smoke.yaml
python3 tools/sparring_agenda.py output/scenarios/<tmp>/設計書_smoke.yaml \
    --drawio scripts/drawio_parser_fixtures/shinryo_composer_golden.drawio
```
期待: qa CRITICAL=0（emitter が 12 セクション合成）/ surfacing findings=2（phone_type CMR の
未配線ラベル＋未知ラベル NO_RESULT）。アジェンダ §1-4 が正しく出る。

---

## 4. 成績表（育成ループ）の接続点

公開後、各部品を coverage scorecard に **1 個ずつ**乗せる（部品ごとに RUBRIC / judge_prompt / probe_corpus / score が要る・
yes/no 完成・date 手前・他は oracle のみ）。
- **接続点**: 工場長の残差 triage / reject ログ（Case A の backlog）→ scorecard backlog の種。
- scorecard → certified_hashes の自動還流は**未接続**（手運用・将来）。
- 優先順位は「OpenAI が痛い slot 先行」（2026-06-23 浜口）。

---

## 5. 要・浜口さん/HQ 確定（フォローアップ — 本 PR では触っていない）

1. **CLAUDE.md への登録（済・2026-06-24）**: VFB `CLAUDE.md` に `@工場長`（Sonnet・ライン外）を登録（allowlist＋モデル行＋壁打ちブリッジ節 Phase 2 追記）。**全体/ホームの CLAUDE.md には入れない**（浜口さん判断 2026-06-24）。
2. **fixer 退役（済・別PR 2026-06-24）**: `step_fixer`（新規ビルドの自律修復・Pattern 1/2/3/4）を PIPELINE_STEPS から除去＋退役 no-op 化（keystone「ライン内に自律修復 LLM を置かない」）。残存 Critical は人間壁打ちへ（生成器を直して再実行）。`auto_fixer`（決定論）は据置。
   **reviewer も退役（済・別PR 2026-06-24）**: Alex は浜口さんのポートフォリオ専用でチーム公開 VFB には不在ゆえ「reviewer→Alex 移管」前提が成立せず、かつ reviewer は in-line LLM で keystone 抵触のため退役。校閲（攻撃耐性/分岐/出力安全性）は**壁打ち時に out-of-line**（知見保全=`docs/ai/skills/SKILL_redteam_review.md`・旧定義=`.claude/agents/archive/reviewer.md`）。**`ui_server.py`（reviewer を in-line 駆動していた Web UI）は不要のため削除**（`start_ui.py` / `.claude/launch.json` も）。
   **Pattern 2 の外科的修正 `step_fixer_modify`（人間の差分指示駆動・governance §1-7 surgical patch）は存続**＝fixer エージェント（`.claude/agents/fixer.md`）は archive せず保持。
   残: `step_fixer` 旧本体・`_run_block_fixer`・`_write_fixer_report`・block_mapper（fixer 用）等の dead code 掃除（別PR）。
3. **カタログが暴いたギャップ**（要対応）:
   - `department_classifier` / `business_hour_classifier` / `faq_matcher` は engine 登録のみで `certified_hashes.specs` に spec が無い（README 台帳＝人間 と機械 SSoT の不一致）。
   - `output_labels`（branch surface）が入っているのは yes_no / date の 2 部品だけ（§2-1 Q1「全認定部品に output_labels SSoT 化」が未完＝surfacing/調達の土台が薄い）。
4. **CLAUDE.md の gh 記述が陳腐化**: 「GitHub 環境が未構築のため gh はブロック」とあるが実際は authed（PR/Issue 起票可）。工場長の起票運用に合わせて更新要。
5. **PR 方針**: 本ブランチは #209 に stack。#209 マージ後に本 Phase をマージ（または #209 へ向けた stacked PR）。

---

## 関連
- `project-governance/initiatives/vfb-factory-restructure.md` §2-4 / `docs/loop-governance.md` §9
- `docs/governance/part-certification-spec.md` / `docs/governance/factory-v2-flip-criteria.md`
- `.claude/agents/工場長.md` / `.claude/skills/sparring-intake/SKILL.md`
- `tools/generate_parts_catalog.py` / `tools/new_part_skeleton.py` / `tools/sparring_agenda.py`
