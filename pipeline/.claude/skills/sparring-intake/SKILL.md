---
name: sparring-intake
description: VFB 工場の「壁打ち入口」（factory-v2 Phase 2）。各メンバーが自分の Claude Code で起動し、自由ゾーンに置いた drawio / 設計書YAML / 既存BIVR を入口に、qa_validator(完全性) と surfacing(調達) と部品カタログ(在庫) を 1 枚の壁打ちアジェンダに束ねる。人間+Claude がアジェンダを埋めて「生成物でなく生成器（設計書）を直して再実行」し、ゲート PASS で orchestrator ビルドへ、テスト後の残差・調達は @工場長 へ渡す。プロジェクトローカル skill。
---

# sparring-intake — 壁打ち入口（VFB 工場 v2 / Phase 2）

あなた（メンバーの Claude）は、ここで **「壁打ち相手」** になる。設計の正本は
`project-governance/docs/loop-governance.md` §9（両端決定論サンドイッチ）。本スキルは入口側の実装。

> **キーストーン（厳守）**: パイプライン（forward path）に入ったらテスト完了まで LLM 介入ゼロ。
> あなたが動くのは**ライン前（壁打ち＝設計を人間と詰める）だけ**。成果物(.bivr/JSON)は直接いじらない。
> 修復は**生成物でなく生成器（設計書 YAML・部品）を直して再実行**する。認定は人間ゲート。

## 起動時の引数

`施設名 フロー名`（new-scenario と同じ命名規約）。例: `/sparring-intake すずな皮ふ科 疑義照会`
命名規約（必須チェック・[[feedback_customer_docs_filename]] [[feedback_group_name_url_length_limit]]）:
- 半角スペース禁止 / 括弧 `(1)` 禁止 / 施設名・フロー名に `_` を含めない（orchestrator が `_` で分割）
- `{施設名}_{flow名}` の URL エンコード後 255 文字以内（漢字 ~19 字目安・日付サフィックス前提）

作業はすべて**自由ゾーン `output/scenarios/{施設名}_{flow名}/` 内に閉じる**。保護ゾーン（scripts/schemas/tools/.claude）は触らない。

## 実行フロー（上から順に）

### Step 0. 在庫を最新化
```bash
python3 tools/generate_parts_catalog.py      # modules/parts_catalog.json を再生成（調達の在庫表）
```

### Step 1. 入力 → 設計書 YAML
自由ゾーンに置かれた入力の種別で分岐（入力正本 = drawio。[[loop-governance §8]]）:

| 入力 | 手順 |
|---|---|
| **drawio**（推奨・正本） | `python3 scripts/scenario_from_drawio.py <設計.drawio> -o output/scenarios/{施設}_{flow}/設計書_{施設}_{flow}.yaml`（emitter が必須12セクションを工場デフォルト合成） |
| **設計書 YAML** | そのまま使う（変換不要） |
| **CSV（Sheet1_input.csv）** | `python3 tools/raw_to_spec.py` で各シート（Sheet2_flow / Sheet_Termination / Sheet_Script / Sheet_Settings 等）を生成 → 人間がシートを記入 → `python3 tools/csv_to_yaml.py --input <Sheet1> --sheet2 <Sheet2> --sheet-script <Sheet_Script> --facility {施設} --flow {flow}` → 設計書 YAML（表計算で入力したいメンバー向けの入口） |
| **既存 BIVR**（§1-7 フォールバック） | BIVR は deployment artifact 扱い。**自動 decompile しない**。源 YAML があれば壁打ちで源を直して再実行。無ければ surgical patch（`bivr_patches`/dirlite）。新規組立には使わない |

### Step 2. 壁打ちアジェンダ生成
```bash
python3 tools/sparring_agenda.py output/scenarios/{施設}_{flow}/設計書_{施設}_{flow}.yaml --drawio <設計.drawio>
```
→ `output/scenarios/{施設}_{flow}/sparring_agenda_{flow}.md` を出す。これを**人間に提示する**。
`fix_category="auto"` の qa Issue は agenda 生成時に `yaml_auto_fixer.py` が**自動で機械修正**され（LLM 不使用）、
アジェンダには修正後の残差＝人間が壁打ちで直す項目だけが載る。中身:
- **§1 設計の不備（qa CRITICAL）** = 完全性ゲートが指す、設計書として埋めるべき項目（差し戻し票）
- **§2 決定論で解けていない判定点（surfacing）** = 認定部品に配線できていない／未知ラベルの調達対象
- **§3 在庫（部品カタログ）** = 今そのまま調達できる認定部品／登録待ち
- **§4 次アクション**

### Step 3. 壁打ち（人間 + あなた）でアジェンダを埋める＝収束ループ
- **§1 の CRITICAL** → 設計書 YAML を**壁打ちで直す**（自由ゾーン内・生成器を直す）。あなたは人間に不足を説明し、合意した内容を YAML に反映する。
- **§2 の判定点** → §3 の在庫で賄えるか人間と確認する。
  - 在庫の認定部品で賄える → 設計書（drawio/YAML）に正しいラベル・遷移を記載して配線する。
  - 賄える部品が無い（NO_CERTIFIED_PART） → **`@工場長` に新部品調達（Case B）を依頼**（工場長が骨格生成→oracle・認定は人間ゲート）。
- 直したら **Step 2 を再実行**して残差が減ったか確認（決定論なので再実行は安い）。CRITICAL/findings が 0 になるまで回す。

### Step 4. ゲート PASS → ビルド
§1・§2 がクリアになったら、パイプラインへ（ここから先はライン内＝あなたは介入しない）:
```bash
python3 scripts/orchestrator.py --pattern 1 --spec output/scenarios/{施設}_{flow}/設計書_{施設}_{flow}.yaml
```
- **director LLM は既定で無効**（YAML 生成は本スキルの決定論入口のみ。orchestrator は既存 YAML を再利用する）。
- パイプライン内で qa CRITICAL が残った場合も orchestrator は **halt + 差し戻し票** を出す（LLM 自律修復なし）。
  差し戻し票を読んで **本スキル（Step 2〜3）に戻り、YAML を直して再実行**する — PASS まで繰り返す。

### Step 5. テスト後 → @工場長
ビルド・テスト（Oracle Gate / P7 / P6）の後の残差解析・PR/Issue 起票・新部品調達は **`@工場長`（ライン外・Sonnet）** が担当する。あなた（壁打ち入口）はここで役割を終える。

## やらないこと
- 成果物(.bivr/JSON)の手パッチを既定にする（preferred = 生成器を直して再実行）
- パイプライン（ライン内）への介入・認定の宣言（人間ゲート）
- 保護ゾーンの編集・master 直 push

## 関連
- `.claude/agents/工場長.md`（テスト後の解析/調達） / `tools/generate_parts_catalog.py` / `tools/sparring_agenda.py`
- `docs/governance/factory-v2-phase2-foreman.md`（本 Phase 設計） / `project-governance/docs/loop-governance.md` §9
- 入口の前段（CS が drawio を組む）= common-skills `scenario-composer`
