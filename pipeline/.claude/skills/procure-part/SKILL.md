---
name: procure-part
description: VFB の scaffold が NO_CERTIFIED_PART で fail-closed 停止したとき、メンバーが自分の Claude Code で「その判定点をどう埋めるか」を判断し、部品調達依頼を発行するための入口スキル。fail-closed の worklist を読み、部品カタログ（在庫）と突合し、「①在庫の認定部品を配線 ②決定論の新部品を調達 ③自由発話ゆえ OPENAI_EXCEPTION 宣言」の 3 択を判断してガイドし、Case B の場合は supply_request 起票ドラフトまで用意する。新部品の採否（新規格の採用可否）は設計判断＝オーナー人間ゲート。プロジェクトローカル skill。
---

# procure-part — 部品調達の入口（VFB / NO_CERTIFIED_PART 対応）

あなた（メンバーの Claude）は、scaffold が **NO_CERTIFIED_PART で fail-closed 停止**した判定点について、
「在庫で賄うか・新部品を調達するか・LLM に残すか」を人間と判断し、調達依頼を発行する。
この穴（fail-closed → 調達依頼が口頭で断絶）を埋めるのが本スキルの目的。

> **なぜ fail-closed か**: 認定部品も patch_box 例外も無い判定点で LLM に黙って倒すと、決定論化の担保が崩れる。
> だから build を止めて worklist を残す（`scripts/scaffold_generator.py` の設計）。
> **人間ゲート**: 新規格・新部品の**採否は設計判断＝オーナー**。あなたは在庫確認と依頼ドラフトまで。
> **認定は別**（実機 P6 → certified_hashes 登録はオーナー・`part-p6-accept` skill 参照）。

## いつ起動するか

sparring-intake / orchestrator ビルド中に scaffold が次のように停止したとき:
```
[scaffold] FAIL-CLOSED (NO_CERTIFIED_PART): N 判定点に認定部品も patch_box 例外もありません（<step名>）。
  worklist: output/reports/scaffold_block_worklist_<stem>.json
```

---

## 実行フロー（上から順に）

### Step 1. worklist を読む（何が止めているか）

```bash
cat output/reports/scaffold_block_worklist_<stem>.json
```
- 各エントリの `step`（判定点名）と surfacing 情報を確認。⚠️ `output/reports/` は **.gitignore 対象**なので
  この worklist は GitHub に届かない（他環境の工場長に自動で渡らない＝口頭断絶の原因）。依頼は下記の
  追跡対象チャネル（supply_request / cert_requests/）で出すこと。

### Step 2. 在庫を最新化して突合（必須）

```bash
python3 tools/generate_parts_catalog.py           # modules/parts_catalog.json / PARTS_CATALOG.md 再生成
```
`modules/PARTS_CATALOG.md`（人間可読）で、止まっている判定点を賄える既存部品があるか探す。status を見る:
- `certified`（engine+spec 認定・即配線可） / `engine_only`（engine のみ・spec 実機待ち） /
  `pending_registration` / `oracle_only` / `draft`。
- 各部品の `certified_specs`（認定済み）と `declared_specs`（宣言のみ・未認定在庫）の差分も確認。

### Step 3. 3 択を判断（この判断が最大の暗黙知）

| 状況 | 選ぶ道 | 手当て |
|---|---|---|
| **在庫の認定部品で割れる**（例: 用件→n_choice、はい/いいえ→yes_no_classifier、診療科→department_classifier） | ①**配線** | 設計書 YAML の該当ブロックを `script_template: <part>`（認定部品名）に直して再ビルド。新 spec なら `part-p6-accept` へ |
| **決定論で書けるが在庫に型が無い**（新しい分類軸・新しい復唱等） | ②**調達（Case B）** | Step 4 で supply_request 起票。採否はオーナー。着手可なら `tools/new_part_skeleton.py` で骨格→oracle まで |
| **自由発話の解釈で決定論不能**（患者の自由な相談内容の要約等） | ③**OPENAI_EXCEPTION 宣言** | `.claude/patch_box/current/*.md` に本文行 `OPENAI_EXCEPTION: <context名>` を書く（この実行限定の例外・git 管理外）。恒久なら設計判断としてオーナーへ |

- 迷ったら「在庫で賄えるか」を先に潰す（②③に倒す前に必ず Step 2 の突合を提示）。
- ②③は**推測で確定しない**。決定論化ロードマップ（`docs/governance/deterministic-replacement-roadmap.md`）と
  照らし、採否はオーナー/工場長に上げる。

### Step 4. 調達依頼（Case B）を起票

`gh issue create` が使える環境:
```bash
gh issue create --template supply_request.md    # [Supply] <施設>_<flow> — <判定点> 新部品/新spec 調達依頼
```
`gh` 不可環境のフォールバック（`cert_requests/README.md`）: `cert_requests/{施設}_{flow}.md` に
`.github/ISSUE_TEMPLATE/supply_request.md` と同項目で本文を書き、feature ブランチに commit → push → PR。

ドラフトに必ず入れる（テンプレ準拠）:
- **判定点 / decision 名**・surfacing 状況（det / collect_only / openai / block）・入力例（正規化済み・**PII なし**）。
- **在庫確認の結果**（必須）: 検討した既存部品と却下理由（「n_choice の規格追加では割れない理由」等）。
- 依頼 A（既存 engine に新 spec）か B（新部品）か。B ならラベル案・入出力仕様素案・代替不能の理由。
- 自分がローカルで進めた範囲（new_part_skeleton / oracle PASS まで、engine に placeholder を置いていないこと）。

---

## 受け渡しの明示（誰が次に動くか）

- **工場長（@工場長・ライン外）**: worklist と本ドラフトを入力に、Case 分類の確定・骨格生成（`new_part_skeleton.py`）・
  oracle PASS まで・PR/Issue 起票を担う。あなた（メンバー）が起票まで済ませたら @工場長 へ引き継ぐ。
- **HQ/オーナー**: 新規格・新部品の**採否確定**、実機 P6、`certified_hashes.json` 登録（保護 SSoT）。
- 部品が認定・棚入れされたら `git pull` → `generate_parts_catalog.py` 再生成で在庫が最新になる（sparring-intake Step 0 が毎回これを回す）。

関連: `.claude/agents/工場長.md` / `.github/ISSUE_TEMPLATE/supply_request.md` / `cert_requests/README.md` /
`modules/PARTS_CATALOG.md`（在庫） / `docs/governance/deterministic-replacement-roadmap.md` /
`part-p6-accept` skill（調達後の受入）/ `sparring-intake` skill（入口）。
