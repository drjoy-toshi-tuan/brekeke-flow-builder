# voicebot-flow-builder（VFB）— v2

病院向けボイスボットの **IVRフロー（JSON / .bivr）を「工場」として組み上げる**システムです。
**各メンバーが自分の Claude Code から呼び出して使う**ことを前提にした、設計 → ビルド → 検証のパイプラインを提供します。

> **v2 のコンセプト = パイプラインの構成自体を決定論で自動化する。**
> 「LLM がフローを書く」のではなく、**人間 ⇄ Claude の壁打ちで設計を固め → 決定論的な製造ラインが組み立て → ライン外の工場長が解析・調達する**。
> ラインの中（forward path）からは LLM を抜き、構成（どの部品をどう繋ぐか）は drawio・設計書・認定部品から機械的に決まる。

---

## 1. v2 で何が変わったか（v1 との差分）

v1 は `director → generator → reviewer → fixer` を**すべて LLM ステップ**で繋ぎ、各所に「自律リトライ／自律修復ループ」を持っていました。v2 はこれを **両端決定論サンドイッチ**に作り替えます。

### キーストーン（最重要・不変条件）

> **パイプライン（forward path）に入ったら、テスト完了まで LLM の介入余地はゼロ。テスト完了後に動く LLM は工場長のみ。**
> LLM が立つのは **ラインの前（壁打ち＝人間と設計を詰める）** と **ライン後／外（工場長＝解析・レポート・部品調達）** だけ。

これにより「製造ライン＝人が有限に監査できる枠」になり、`{ 人は枠を持ち / AI は出力を出す }` という責任境界がそのまま成立します（設計正本: `project-governance/docs/loop-governance.md` §9）。

### 達成済みのマイルストーン（master 反映済・〜#213）

| 変更 | PR | 内容 |
|---|---|---|
| **reviewer 退役** | #213 | in-line レッドチーム校閲（LLM）を撤去。校閲は**壁打ち時に out-of-line**（`docs/ai/skills/SKILL_redteam_review.md`）。reviewer を駆動していた `ui_server.py` も削除 |
| **fixer（自律修復）退役** | #212 | 新規ビルドの自律修復 `step_fixer` を PIPELINE から除去（keystone「ライン内に自律修復 LLM を置かない」）。残存 Critical は**人間壁打ちが生成器を直して再実行**。Pattern 2 の外科的修正 `step_fixer_modify`（人間の差分指示駆動）のみ存続 |
| **Phase 2: 工場長 / 壁打ち入口 / 部品カタログ** | #211 | ライン外の `@工場長`（Sonnet）、壁打ち入口 skill `/sparring-intake`、機械可読の部品カタログ `modules/parts_catalog.json` を新設 |
| **出口4経路の決定論配線 + 認定ゲート二段化** | #206-#210 | DOB / 受診オプション / 完全一致FAQ / 診療科 / 日付 を認定部品へ配線。認定ゲートを **engine/spec 二段判定**へ |

### 進行中（v2 の到達目標）

- **director（設計書生成 LLM）の解体** → 前段の **drawio 入口 + 壁打ち**へ。「散らかった入力の解釈」は人間 in the loop の壁打ちが、「厳密 YAML への形式化」は決定論生成器が担う（§9「director の分解」）。
- **prompter（OpenAI 自由発話プロンプト記述 LLM）の縮退** → OpenAI 判定を認定部品（決定論）に 1 個ずつ置換し、ライン内 LLM をゼロに近づける（`docs/governance/deterministic-replacement-roadmap.md`）。

> **正直な現状（2026-06-24）**: orchestrator の Pattern 1/3/4 のラインには **director と prompter がまだ LLM として残存**します（キーストーンの完全達成は未到達）。reviewer・fixer の退役が第一歩で、drawio 入口と決定論置換でラインを段階的に空にしていきます。

---

## 2. 使い方 — 各メンバーの Claude から呼び出す

このリポを clone し、**自分の Claude Code セッションでプロジェクトローカル skill を起動**して使います。1 シナリオは **壁打ち → ビルド → 工場長**の 3 フェーズで進みます。

```
[フェーズ1: ライン前]  あなた（メンバーの Claude）が「壁打ち相手」    /sparring-intake または /new-scenario
        ↓  設計書 YAML を「生成器」として固める（成果物は直接いじらない）
[フェーズ2: ライン内]  orchestrator が決定論で製造（LLM 介入なし）      python3 scripts/orchestrator.py
        ↓  Oracle Gate / P7 / P6
[フェーズ3: ライン後]  @工場長 が残差を解析・PR/Issue 起票・部品調達     @工場長（Sonnet・ライン外）
```

### 入口 skill（ライン前 = あなたが壁打ち相手になる）

| skill / エージェント | 起動例 | 用途 |
|---|---|---|
| **`/sparring-intake`** | `/sparring-intake すずな皮ふ科 疑義照会` | **v2 の標準入口**。自由ゾーンに置いた drawio / 設計書YAML / 既存BIVR を入口に、**完全性（qa）+ 決定論で解けていない判定点（surfacing）+ 在庫（部品カタログ）を 1 枚の壁打ちアジェンダ**に束ね、人間と詰める。収束したら orchestrator へ |
| **`/new-scenario`** | `/new-scenario ヘルスケアクリニック厚木 健診` | Pattern 1（完全新規）。customer_docs PDF を MD 化 → Pattern 1 軽量ノート起草 → orchestrator 起動コマンド提示まで（現状 director 経由。drawio 入口へ移行中） |
| **`/migrate-gen2`** | — | Gen2 → Gen3 移管（Pattern 3）の自動化 |
| **`/yaml-to-drawio`** | — | 設計書 YAML → drawio 生成（入力正本 drawio の作図補助。逆方向の drawio→YAML は `scripts/scenario_from_drawio.py`）|
| **`/generate-manual-brief`** | — | 顧客向け運用マニュアルの素材生成 |

> 入口の前段（CS が drawio を組む）は共通基盤 `common-skills` の `scenario-composer`。**設計書の入力正本は drawio**（§8 決着・2026-06-19）。

### 工場長（ライン後／外 = テスト後の解析・調達）

| エージェント | 起動 | 用途 |
|---|---|---|
| **`@工場長`**（Sonnet・ライン外） | `@工場長 …` | テスト完了後に残差を triage（Case A 規格内DATA不足 / Case B 新規spec・新部品 / Case C 上流STT・TTS）→ **PR**(Case A・oracle 再通過) / **Issue**(Case B・枠変更) を起票 → 在庫に無い判定点は新部品を**調達**（骨格生成 → oracle PASS まで）。**自律修復しない・認定は人間ゲート**。定義: `.claude/agents/工場長.md` |

### 壁打ちの鉄則（preferred path）

- **直すのは「成果物」ではなく「生成器」。** .bivr / JSON を手でパッチするのではなく、**設計書 YAML・部品・spec-DATA を直して決定論パイプラインを再実行**する。ラインは LLM 不在で一瞬で終わるので、fix-and-rerun が安い（手パッチは一回限りの fallback）。
- **認定（`certified_hashes` 登録）は常に人間ゲート。** 壁打ち・工場長は起票・oracle PASS まで。
- **作業は自由ゾーン `output/scenarios/{施設}_{flow}/` に閉じる。** 保護ゾーン（`scripts/` `schemas/` `tools/` `.claude/`）は触らない。

---

## 3. アーキテクチャ — 両端決定論サンドイッチ

```
[壁打ち: 人間+Claude] → ║YAML生成器(規格適合)║ → ║qa_validator(完全性)║ → 決定論製造(scaffold/layout/prompter*/properties/validator/tester/build) → ║出口ゲート(oracle/cert + P7/P6)║ → 出荷
   解釈・試行錯誤(人間)      =directorの決定論部分      純粋な入口ゲート          ── ライン内：テスト完了まで LLM 介入ゼロ ──        Oracle=決定論 / P7・P6=当面 人間通話テスト
                                                                                                          ↑
                                                                                       テスト後の解析・修復起票・部品調達 = @工場長（ライン外）
```

- **入口は 2 段の決定論ゲート**。前段＝**YAML 生成器**（drawio 等 → 設計書 YAML・規格適合チェック）、後段＝**qa_validator**（設計判断の完全性＝復唱／リトライ／TODO 残ゼロ等）。どちらも fail は**人間（壁打ち）へ差し戻し**。LLM は両ゲートの**外側**で人間が回す試行錯誤であって、ゲート内には入らない。
- **限界の明示**: 入口ゲートは「規格適合 + 完全性（well-formed）」の sound verifier。**設計が意味的に正しいかは判定しない** — その残差は壁打ちの人間レビューが持つ。
- **出口は Oracle Gate（決定論・byte-parity）→ P7/P6**。P7（連結）/ P6（部品単体実機）は Oracle Gate に統一しきれておらず**当面は人間の通話テスト**が必要。統一が進むほど人間テストは縮小する。
- `*prompter` は現状ライン内に残る LLM（OpenAI 自由発話プロンプト記述）。決定論部品への置換で縮退中（§1 参照）。

---

## 4. 製造ライン（orchestrator）の実際の工程

`scripts/orchestrator.py` が 4 パターンの決定論ラインを自動制御します（並列実行・Git 自動ブランチ・Human-in-the-Loop 承認つき）。

```bash
# 1施設（orchestrator 直接）
python3 scripts/orchestrator.py --pattern {1-4} --spec output/scenarios/{施設}_{flow}/設計書_{施設}_{flow}.yaml

# 途中から再開
python3 scripts/orchestrator.py --resume-state output/scenarios/{施設}_{flow}/pipeline_state_*.json

# 複数施設を並列（git worktree ベース・ローカル専用）
python3 scripts/launch_parallel.py setup --specs <spec1> <spec2> --pattern 3
```

| パターン | 用途 | ライン（要点） |
|---|---|---|
| **1** | 新規作成 | branch → director → qa → copy_subflows → scaffold → layout → generator(skip) → **prompter+properties 並列** → merge → validator → tester+build 並列 → auto_fixer → collect → commit → **oracle_gate → p7_gen → p7_acceptance(人間) → p6_gate → approve(人間)** |
| **2** | 既存フロー修正 | branch → extract_bivr → scaffold_extractor → dirlite（差分 or リフレッシュ判定）→ pattern2_apply → properties → validator → tester+build → auto_fixer → collect → commit → 出口ゲート |
| **3** | Gen2 → Gen3 移管 | Pattern 1 と同型（`--spec` に移管ノート .md） |
| **4** | Gen1 → Gen3 移管 | Pattern 1 と同型 |

- **reviewer / fixer ステップは PIPELINE_STEPS から除去済み**（#212/#213）。残存 Critical は LLM が直さず**人間壁打ちが生成器を直して再実行**。決定論の `auto_fixer`（CTX-017 / status / LAYOUT deoverlap 等の機械修正）は据置。
- `--skip-qa` / `--skip-tester` / `--dry-run` 等の補助フラグあり。Pattern 6（テストフロー生成）は OpenAI/STT 不要の最小構成で部品の動作検証に使う。

---

## 5. 部品カタログと認定ゲート（engine / spec / wiring 二段判定）

OpenAI プロンプトで解いている判定を、**受入テスト通過済みの module / script に 1 個ずつ置き換える**のが v2 の土台です。LLM に残すのは決定論で書けない「自由発話の解釈」のみ。

### 認定ゲート v2 — 部品種別と規格の二段判定

「ネジはネジ、釘は釘。各々に規格がある」。bivr 内の `@General$Script` を `modules/` 正本と二段で照合します（仕様: `docs/governance/part-certification-spec.md`）。

| 軸 | 意味 | ゲート挙動 |
|---|---|---|
| **engine** | 部品種別の刻印（全用途で不変のアルゴリズム） | **不一致はブロック**（別の部品＝認識しない） |
| **spec** | 受入必須の分類データ（DTMF_MAP / KEYWORD / RULES 等） | **新規 spec は受入要求**（実機 P6）／認定済 spec はスキップ |
| **wiring** | 入力元・保存先（`var SOURCE_MODULE` 等） | **照合から除外**（インスタンス差） |

`certified_hashes.json` の `parts`（engine の正）+ `specs`（`engine_hash:spec_hash` 台帳）で判定。**「1 文字でも改変したら再受入」を機械化**（旧「設定行除外の単一ハッシュ」は廃止）。

### 部品カタログ — 在庫表（壁打ち・工場長が引く）

```bash
python3 tools/generate_parts_catalog.py    # certified_hashes.json + 各 part.json → modules/parts_catalog.json (+ PARTS_CATALOG.md)
```

| status | 意味 |
|---|---|
| 認定済（調達可） | engine 登録 + spec 認定済。そのまま配線できる |
| engine登録のみ・実機待ち | engine はあるが spec 認定（実機 P6）待ち |
| oracle有・登録待ち | part.json + oracle あり・未登録 |

現状の在庫: 認定済 9（`yes_no_classifier` / `n_choice` / `inquiry_classifier` / `phone_type` / `checkup_*` 系 / `multi_value_gate`）ほか計 16 件。**台帳の正本は `certified_hashes.json` + `part.json`**（`PARTS_CATALOG.md` / `parts_catalog.json` は自動生成・手編集しない）。人間向け認定台帳は `modules/README.md`。

### 新規部品の Definition of Done

1. `REQUIREMENTS.md`（入出力・分岐・エッジケース）
2. **Python オラクル**（`oracle.py` + `test_oracle.py`）全 PASS
3. **Brekeke 実機受入**（Pattern 6）全 PASS
4. オラクルと実機の判定一致（デプロイ済 JS とバイト一致が理想）
5. `modules/README.md` の認定レジストリに登録

> 工場長の調達補助: `python3 tools/new_part_skeleton.py <part_id> --labels "ラベル1,ラベル2,NO_RESULT" --spec <spec名>` が認定仕様（@part-id / @spec / wiring）準拠の骨格を生成。**実機 P6 + cert 登録は人間ゲート**。

---

## 6. 入口の決定論化 — drawio → 設計書 YAML → 壁打ちアジェンダ

入力正本は **drawio**。ビジネス構造だけを drawio が運び、実現知識（input_method / retry / termination の status・sms_flag / subflow flowname 等の「ベース数値・分岐方法・ブロック配置」）は**工場デフォルトが合成**します。埋められない施設固有値は TODO で残し、入口ゲートが壁打ちアジェンダとして surface します。

```bash
# drawio → 設計書 YAML（emitter が必須12セクションを工場デフォルトで合成）
python3 scripts/scenario_from_drawio.py <設計.drawio> -o output/scenarios/{施設}_{flow}/設計書_{施設}_{flow}.yaml

# 壁打ちアジェンダ生成（qa完全性 + surfacing調達 + 部品在庫 を 1 枚に）
python3 tools/sparring_agenda.py output/scenarios/{施設}_{flow}/設計書_{施設}_{flow}.yaml --drawio <設計.drawio>
# → sparring_agenda_{flow}.md（§1 設計の不備 / §2 未配線・未知ラベル / §3 在庫 / §4 次アクション）
```

`/sparring-intake` skill がこの鎖を案内し、人間と一緒にアジェンダを埋めます。`§1`（qa CRITICAL）は設計書 YAML を壁打ちで直す、`§2`（surfacing）は在庫で賄えるか確認し、賄えなければ `@工場長` に新部品調達（Case B）を依頼。直したら再実行して残差ゼロまで回します。

---

## 7. スクリプト / ツール / エージェント

### エージェント（`.claude/agents/`）

| エージェント | モデル | 役割 | 立ち位置 |
|---|---|---|---|
| **工場長**（`工場長.md`）| Sonnet | テスト後の残差 triage・解析・PR/Issue 起票・部品調達（自律修復しない） | **ライン外（後）** |
| director（`director.md`）| Opus | 顧客資料 → 設計書 YAML（scenario_flow + step_details + termination_patterns）+ 確認レポート | ライン内（縮退対象→壁打ち入口へ） |
| prompter（`prompter.md`）| Opus | OpenAI モジュールのプロンプトをサイドカー MD に記述（§8）。`inject_prompts.py` が JSON に注入 | ライン内（縮退対象→決定論部品へ） |
| generator（`generator.md`）| Sonnet | scenario_flow 検出時はスキップ。レガシー routing_map のみ稼働 | ライン内 |
| tester（`tester.md`）| Sonnet | `tester.py` を実行して構造監査 | ライン内 |
| fixer（`fixer.md`）| Sonnet | **新規ビルドの自律修復は退役**。Pattern 2 の外科的修正 `step_fixer_modify`（人間差分指示駆動）でのみ存続 | — |
| dirlite（`dirlite.md`）| Sonnet | Pattern 2 のモード判定・差分／リフレッシュ指示書生成 | ライン内（Pattern 2）|
| reviewer | — | **退役（#213）**。校閲は壁打ち時に out-of-line（旧定義 `archive/reviewer.md`）| — |

### スクリプト（LLM 不使用・決定論）

| スクリプト | 役割 |
|---|---|
| `scripts/orchestrator.py` | パイプライン全体の自動制御（4 パターン・並列・HITL 承認）|
| `scripts/scenario_from_drawio.py` / `drawio_to_scenario.py` | drawio → 設計書 YAML（入口の決定論生成器）|
| `scripts/scaffold_generator.py` | scenario_flow → 完成品 JSON 機械生成（9 ブロック型・復唱・CMR・終話チェーン・多段分岐 Script+CMR で 100 条件）|
| `scripts/layout_calculator.py` / `block_layout.py` / `block_layout_spec.py` | DAG ベース縦型レイアウト計算（ブロック座標 → モジュール配置 → スロット定義）|
| `scripts/gen_properties.py` / `properties_from_json.py` | IVRプロパティ（TTS 発話文言）生成・逆生成（LLM 不使用・prompter と並列）|
| `scripts/inject_prompts.py` | サイドカー MD のプロンプトを JSON に注入 |
| `scripts/copy_subflows.py` | サブフロー静的 JSON をサンプルからコピー |
| `scripts/auto_fixer.py` / `yaml_auto_fixer.py` | validator / qa_validator の `fix_category=auto` を JSON / YAML に決定論修正 |
| `scripts/scaffold_extractor.py` | 既存 JSON から scenario_flow YAML を逆抽出（Pattern 2）|
| `scripts/build_bivr.py` / `extract_bivr.py` | .bivr 生成・展開 |
| `scripts/gen_spec_html.py` | CS 向け HTML 仕様書生成（縦型樹形図 + ブロック構成 + 全発話一覧）|
| `scripts/gen_p7_cases.py` | Pattern 7 連結テストケース表（下書き）生成 |
| `scripts/gen_phonebook_csv.py` | Dr.JOY 電話帳 CSV 生成 |
| `scripts/build_dictionaries.py` / `extract_entity_definitions.py` | AmiVoice STT 辞書のビルド・抽出 |
| `scripts/format_fields.py` / `format_prompt_strings.py` | saveContextModel2DB fields / OpenAI プロンプト文字列の整形 |
| `scripts/launch_parallel.py` | 複数施設の並列パイプライン起動（git worktree）|
| `scripts/reference_validator.py` | spec 内の参照パス実在チェック（早期失敗）|
| `scripts/curator.py` | `docs/run_history/*.json` 集計（summary / critical-codes / step-times / outliers）|
| `scripts/block_mapper.py` | モジュール名 → ブロック名 逆引き（旧 fixer 用・dead code 掃除予定）|

### ツール（`tools/`・枠の補助）

| ツール | 役割 |
|---|---|
| `tools/generate_parts_catalog.py` | 部品カタログ（在庫表）生成。`--check` で冪等検証（CI/pre-commit）|
| `tools/new_part_skeleton.py` | 新部品の骨格生成（工場長の調達基盤）|
| `tools/sparring_agenda.py` | 壁打ちアジェンダ生成（qa + surfacing + 在庫を 1 枚に）|
| `tools/lint_part_markers.py` | `@part-id` / `@spec` マーカーの lint |
| `tools/bivr_patches/` | 軽量 .bivr パッチ（Pattern 2 外科的修正の補助）|

### スキーマ・検査（`schemas/`）

| ファイル | 役割 |
|---|---|
| `schemas/qa_validator.py` | 設計書機械チェック（40 項目、T/L/E/I/F/M 系。`--json-report` で yaml_auto_fixer 連携）= **後段入口ゲート** |
| `schemas/validator.py` | JSON 構造チェック（`--json-report` で auto_fixer 連携）|
| `schemas/tester.py` | 構造監査（サブフロー再帰インライン展開 + AUD-1/AUD-2/R-1/R-2/R-3）|
| `schemas/module_graph.py` | モジュール依存グラフ |

---

## 8. プロンプトサイドカー方式（prompter が残る間の運用）

prompter は OpenAI プロンプトを JSON に直接書かず、**サイドカー MD**（`output/scenarios/{施設}_{flow}/prompts_*.md`）に `## モジュール名` 形式で記述し、`inject_prompts.py` が JSON エンコードして注入します。

```
## OpenAI_診療科
# Role
あなたは医療機関の電話受付...（プロンプト本文）
```

- JSON エンコードの事故（改行混入・エスケープ誤り）を回避。
- 校閲・修正もサイドカー MD を更新 → `inject_prompts.py` で反映（JSON 全文 Read 不要）。

---

## 9. 品質保証の構造（どこで何を担保するか）

| 層 | 担当 | チェック内容 | 失敗時 |
|---|---|---|---|
| 前段入口ゲート | YAML 生成器（drawio→YAML）| 規格適合（命名 / group_name 長 / CMR other / 復唱チェーン / status 値）| **人間（壁打ち）へ差し戻し** |
| 後段入口ゲート | qa_validator.py | 設計判断の完全性（40 項目）。`fix_category=auto` は yaml_auto_fixer で機械修正 | 残存 CRITICAL は**人間（壁打ち）へ差し戻し**（director 自律リトライは廃止）|
| 構造検証 | validator.py | JSON 構造・パラメータ・接続整合性。`fix_category=auto` は auto_fixer で機械修正 | レポート保存 → 続行 |
| 構造監査 | tester.py | フラット化 + AUD-1/AUD-2/R-1/R-2/R-3 | レポート保存 → 続行 |
| 出口（部品）| oracle_gate / certified_hashes.json | engine/spec 二段判定 + 各部品 test_oracle.py | engine 不一致＝ブロック / 新規 spec＝実機要求 |
| 出口（結合）| P7（連結）/ P6（部品単体）| 実機通話テスト（当面 人間が担保）| クリアまで出荷不可 |
| 残差対応 | @工場長（ライン外）| Case A/B/C の triage・起票・調達 | **自律修復しない**・認定は人間ゲート |

- レッドチーム校閲（攻撃耐性 / 分岐 / 出力安全性）は **壁打ち時に out-of-line**（`docs/ai/skills/SKILL_redteam_review.md`）。
- 育成ループ: 公開後、各部品を**標準化側の coverage scorecard に 1 個ずつ乗せて育てる**（yes/no 完成・date 手前・他は oracle のみ）。工場長の残差 triage / reject ログが scorecard backlog の種（`docs/governance/factory-v2-phase2-foreman.md` §4）。

---

## 10. コラボレーション運用 — allowlist 方式

複数メンバーがカスタマイズして master 反映できる体制。**「触ってよい場所」を allowlist で定義し、それ以外はすべて保護ゾーン**とします。人間向け詳細は [`CONTRIBUTING.md`](CONTRIBUTING.md)。

| ゾーン | パス | ルール |
|---|---|---|
| **自由ゾーン** | `output/scenarios/{施設}_{flow}/`（シナリオ成果物・顧客資料 `reference/`）| feature ブランチ → PR、コードオーナーレビュー不要 |
| **保護ゾーン** | 上記以外すべて（`CLAUDE.md` / `.claude/` / `.github/` / `scripts/` / `schemas/` / `tools/` / `modules/` / `docs/` SSoT / `.gitignore` / `requirements.txt`）| `.github/CODEOWNERS` によりオーナー（@TS-dong-nc）レビュー必須 + **マージもオーナー** |

- master へ直 push してよいのはオーナーのみ。それ以外は feature ブランチ → PR。
- ブランチ名: `feature/{施設名}_{フロー名}`（作業者名は入れず、PR/Issue の**アサイニー**で管理）。
- 機械的防御 3 層: `CODEOWNERS` + `.github/workflows/guard-master.yml`（非オーナーの保護パス push を自動復元）+ ブランチ保護（手順: `docs/governance/branch-protection-setup.md`）。
- エージェントは保護ゾーンを直接 Edit せず、**変更案を提示**する。

> **ガバナンスのスコープ注記**: §1 の auto-merge 境界・ゲート構成が効くのは**オーナーのプロジェクト群の中でのみ**。VFB をチームで使う際は個人ごとに権限・cert 到達度・owner が変わるため、そのままは適用できない（`loop-governance.md` §9 / §6 で再調整）。

### PATCH_BOX — 実行限定の動的コンテキスト（Phase 1）

`.claude/patch_box/current/*.md` に置いた指示は **agents/*.md より優先**される「この実行限定の例外指示」。優先順位は **CLAUDE.md（憲法）> agents（法律）> patch_box（実行限定の例外）** で、CLAUDE.md の恒久ルールは上書きしない。pipeline 完了後に orchestrator が `consumed/{timestamp}_{filename}` へ自動アーカイブ。`current/*.md` は **gitignore 済（ローカル専用）**で、fresh-clone 環境へは env var `VFB_PATCH_BOX_CONTEXT` で渡す。詳細: `.claude/patch_box/README.md`。

---

## 11. 命名規則（重要）

SSoT: `docs/brekeke/naming_convention.md`

- **日付サフィックス `_YYYYMMDD`（作業日）はグループ名にのみ付ける。フロー名・サブフロー名には付けない。**
  - グループ名: `中頭病院_診療_20260604` / JSON name・jump 参照: `中頭病院_診療_20260604$診療`（グループ名を verbatim 参照）
- コピー作成・修正のたびに新しい作業日でグループを版管理し、**サブフローは全件まとめて新グループ配下へ再エクスポート**（Pattern 2 修正時も必須）。一部だけ旧グループに残すと jump が解決せず通話切断になる。
- 施設名・フロー名に半角スペース / 括弧 `(1)` / `_` を含めない（orchestrator が `_` で分割）。`{施設名}_{flow名}` は URL エンコード後 255 文字以内（漢字 ~19 字目安）。
- 機械検出: `qa_validator.py` の **E-16**（group_name 末尾 `_YYYYMMDD` 必須）/ **T-2d**（flow_name の `$` 前 == group_name）/ **E-14**（jump 参照 URL 255 文字制限）。

---

## 12. ディレクトリ構成

```
voicebot-flow-builder/
├── CLAUDE.md                    # AI 共通指示書（権限 / キーストーン / 壁打ちブリッジ / モジュール開発ポリシー）
├── CONTRIBUTING.md              # 人間向け共同運用ルール（allowlist ゾーン / PR / 依存・secret）
├── README.md                    # 本ファイル
│
├── .github/                     # CODEOWNERS / guard-master（保護パス push 自動復元）/ backup-master
├── .claude/
│   ├── agents/                  # 工場長 / director / prompter / generator / tester / fixer / dirlite（archive/ に reviewer 等 退役）
│   ├── skills/                  # sparring-intake / new-scenario / migrate-gen2 / yaml-to-drawio / generate-manual-brief / extract-yesno-synonyms
│   ├── patch_box/               # 実行限定の例外指示（current/ は gitignore・ローカル専用）
│   └── settings.json            # 権限 allowlist / deny
│
├── modules/                     # 決定論部品 + 認定台帳
│   ├── README.md                #   人間向け認定レジストリ
│   ├── certified_hashes.json    #   ★ 認定 SSoT（parts=engine の正 / specs=engine:spec 台帳）
│   ├── parts_catalog.json       #   機械可読カタログ（自動生成）
│   ├── PARTS_CATALOG.md          #   人間向けカタログ（自動生成）
│   └── {part}/                  #   yes_no_classifier / n_choice / inquiry_classifier / phone_type / checkup_* / dob_normalizer / reservation_date_classifier / department_classifier / faq_* / ...
│       ├── REQUIREMENTS.md / oracle.py / test_oracle.py / script.js / part.json / acceptance_test/
│
├── scripts/                     # 決定論パイプライン本体（§7 参照）
├── schemas/                     # qa_validator / validator / tester / module_graph（入口・検査ゲート）
├── tools/                       # 枠の補助（部品カタログ生成 / 新部品骨格 / 壁打ちアジェンダ / lint / bivr_patches）
├── connection_test/             # Pattern 7 連結テスト（STT スタブ・sim / golden / recorded / cases）
│
├── docs/
│   ├── governance/              #   part-certification-spec / factory-v2-phase2-foreman / factory-v2-flip-criteria / deterministic-replacement-roadmap / branch-protection-setup / test-feedback-loop
│   ├── ai/skills/               #   prompter 用 SKILL_A〜F_*.md / SKILL_JSON_rules / SKILL_quality_criteria / SKILL_redteam_review / SKILL_CONTRACT
│   ├── brekeke/                 #   Brekeke 仕様リファレンス・モジュール選定ガイド v2・naming_convention
│   ├── specs/                   #   設計書フォーマットテンプレート（yaml / md）
│   ├── migration/               #   Gen2/Gen1 軽量移管ノート（director の付箋）
│   ├── reference/               #   bivr/samples・bivr/clients（--base 用）・customer_docs（顧客資料）
│   ├── run_history/             #   1 run = 1 JSON（curator の signal source）
│   └── archive/                 #   退避済み成果物
│
├── metrics/                     # GitHub メトリクス収集（fetch_metrics.py / metrics.json / dashboard.html）
├── examples/ · tests/           # 参考シナリオ / 単体・統合テスト
├── commubo抽出/                  # 現本番フローの抽出資材（.yaml/.bivr ペア）
│
└── output/
    ├── scenarios/{施設}_{flow}/  # ★ 自由ゾーン = 正式な成果物置き場
    │   ├── 設計書_*.yaml         #   設計書 YAML（生成器入力・正本）
    │   ├── sparring_agenda_*.md  #   壁打ちアジェンダ
    │   ├── prompts_*.md          #   prompter サイドカー
    │   ├── properties_*.md       #   IVRプロパティ
    │   ├── *.bivr / json/        #   ビルド済 BIVR / 中間 JSON
    │   ├── シナリオ仕様書_*.html  #   CS 向け HTML 仕様書
    │   └── pipeline_state_*.json #   パイプライン進捗（gitignore）
    └── reports/                  # qa / validator の JSON レポート（auto_fixer 入力）
```

---

## 13. クイックスタート

### 前提

- [Claude Code](https://docs.claude.com) インストール済み / Python 3.8+（PyYAML 等は pre-install 前提・**インストール禁止**）/ Git

### セットアップ

```bash
git clone https://github.com/TS-dong-nc/gen_flow.git
cd gen_flow
```

### 1 シナリオを通す（壁打ち → ビルド → 工場長）

```text
# フェーズ1: あなたの Claude Code で入口 skill を起動（壁打ち）
/sparring-intake すずな皮ふ科 疑義照会      # drawio/YAML を入口に、壁打ちアジェンダを埋めて設計書 YAML を固める
（完全新規で customer doc から起こす場合は） /new-scenario すずな皮ふ科 疑義照会

# フェーズ2: ゲート PASS したらビルド（ここから先はライン内・LLM 介入なし）
python3 scripts/orchestrator.py --pattern 1 \
  --spec output/scenarios/すずな皮ふ科_疑義照会/設計書_すずな皮ふ科_疑義照会.yaml --env demo

# フェーズ3: テスト後の残差・調達
@工場長 残差を triage して PR/Issue を起票してください
```

---

## 14. メトリクス・ライセンス

```bash
export GITHUB_TOKEN="ghp_xxx"   # 環境変数が必要
python metrics/fetch_metrics.py # → metrics/metrics.json 更新
open metrics/dashboard.html
```

| フィールド | 説明 |
|---|---|
| `duration_hours` | PR 作成 → マージの所要時間 |
| `actual_duration_hours` | orchestrator 着手（pipeline_state の started_at）→ マージの実所要時間 |

**ライセンス**: 社内利用限定。

---

## 関連ドキュメント

- 設計正本（v2 製造ライン・両端決定論サンドイッチ）: `project-governance/docs/loop-governance.md` §9
- Phase 2 設計（工場長 / 壁打ち入口 / 部品カタログ）: `docs/governance/factory-v2-phase2-foreman.md`
- 認定仕様（engine/spec/wiring 二段判定）: `docs/governance/part-certification-spec.md`
- 決定論置換ロードマップ: `docs/governance/deterministic-replacement-roadmap.md`
- flip 基準（v1→v2 切替）: `docs/governance/factory-v2-flip-criteria.md`
- AI 共通ルール: `CLAUDE.md` / 人間向け共同運用: `CONTRIBUTING.md`
