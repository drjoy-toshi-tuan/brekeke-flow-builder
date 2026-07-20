# CLAUDE.md — ボイスボットフロー自動生成プロジェクト

## 権限と自律実行ガイドライン（全エージェント共通）

> **原則: セキュリティリスクが低い操作は、人間に確認せずに自律的に実行してよい。**
> `.claude/settings.json` に許可/拒否ルールが定義済み。以下はエージェントが判断に迷った場合の指針。

### 確認なしで実行してよい操作（自律実行OK）

| 操作カテゴリ | 具体例 | 理由 |
|---|---|---|
| **ファイル読み書き** | docs/, output/, schemas/, scripts/ 配下の読み書き | パイプラインの正常な動作に必須。成果物は全てoutput/に出力される |
| **パイプラインスクリプト実行** | `validator.py`, `tester.py`, `format_fields.py`, `format_prompt_strings.py`, `build_bivr.py`, `extract_bivr.py`, `qa_validator.py`, `copy_subflows.py`, `gen_properties.py`, `auto_fixer.py`, `yaml_auto_fixer.py`, `gen_p7_cases.py`, `connection_test/stub_stt_connection.py`, `modules/*/test_oracle.py` | 検品・テスト・整形・ビルド・設計書機械チェック・サブフローコピー・プロパティ生成・機械修正・連結テスト生成・オラクル受入は毎回実行する標準工程 |
| **Python一行スクリプト** | `python3 -c "..."` によるJSON内容の確認・検査 | ファイル内容の読み取り・確認のみ。複数行スクリプトのファイル生成・実行は禁止 |
| **Git読み取り操作** | `git status`, `git log`, `git diff`, `git branch` | リポジトリの状態確認のみ。変更を伴わない |
| **Gitローカル操作** | `git add`, `git commit`, `git checkout`, `git stash` | ローカルリポジトリ内の操作。外部への影響なし |
| **ファイル操作** | `cat`, `head`, `grep`, `find`, `cp`, `mv`, `mkdir`, `unzip` | 確認・整理・展開のための標準ツール |
| **サブエージェント呼び出し** | `@director`, `@generator`, `@prompter`, `@fixer`, `@tester`, `@dirlite`, `@工場長` | エージェント間の連携はパイプラインの正常な動作。properties は廃止（`gen_properties.py` スクリプトに置換）。`@工場長` は**ライン外**（テスト完了後の解析/起票/部品調達）。**`@reviewer` は退役（2026-06-24）**＝校閲は壁打ち時に out-of-line（`docs/ai/skills/SKILL_redteam_review.md`） |

### 人間の確認が必要な操作（必ず聞く）

| 操作カテゴリ | 具体例 | 理由 |
|---|---|---|
| **外部への送信（Git Push）** | `git push` | Yes/No確認で実行可。現環境はローカルのみだが、リモートへの反映は人間が判断する |
| **GitHub CLI操作** | `gh pr create` 等 | GitHub環境が未構築のため現在はブロック。導入後にask（確認付き許可）に変更予定 |
| **ネットワーク通信** | `curl`, `wget`, `ssh`, `scp` | 外部サーバーとの通信はセキュリティリスクがある |
| **破壊的操作** | `rm -rf`, `sudo`, 本番環境への操作 | 取り返しのつかない操作は必ず人間が確認する |
| **機密ファイルアクセス** | `.env`, `secrets/`, `*.key`, `*.pem`, `credentials` | 認証情報・秘密鍵への読み取りは拒否設定済み |
| **設計判断が必要な場合** | 設計書に記載のない仕様の判断、BLOCKERの解消 | AIは推測で判断せず、人間に確認する |
| **ツール・パッケージのインストール** | `npm install`, `pip install`, `apt-get`, `brew` 等あらゆるインストールコマンド | **絶対禁止（確認があっても実行不可）**。下記「絶対遵守事項」参照 |

### 絶対遵守事項（例外なし）

> **🚫 ツール・ソフトウェアのインストールは一切禁止**
>
> Claude Code は、作業中にいかなるツール・ライブラリ・パッケージもインストールしてはならない。
> 人間が許可した場合でも実行しないこと。これは環境の安全性を守るための絶対的なルールである。

**禁止対象の具体例:**
- Git関連ツール（Git CLI、Git LFS、pre-commit hooks、husky 等）
- PDF読み取りツール（poppler、pdftotext、pdf2image 等）
- パッケージマネージャー経由のインストール（`npm install`、`pip install`、`apt-get install` 等）
- その他あらゆるソフトウェア・ライブラリのインストール

**必要なツールが不足している場合の対応:**
1. 「〇〇が必要ですが、インストールは許可されていません」と人間に報告する
2. 人間がマネージャーに相談し、マネージャーが手動でセットアップする

> **🚫 作業用 Python スクリプトの生成・実行は禁止**
>
> JSON生成・パッチ作業において、`scripts/` や任意のパスに Python スクリプトを新規作成して Bash で実行してはならない。
> JSON の編集は **Edit / Write / Read ツールで直接行うこと**。
> `python3 -c "..."` は内容確認（読み取り専用）のみ許可。

### リトライ・エスカレーション時の判断

- **validator.py の WARNING**: 自律的に修正を試みてよい（確認不要）
- **validator.py の CRITICAL**: `auto_fixer.py` が `fix_category="auto"` の Issue を決定論的に機械修正 → **残存 Critical は人間（壁打ち）へ**（`fixer` ステップは 2026-06-24 退役・keystone「ライン内に自律修復 LLM を置かない」）。最終レポートを上げ、人間が生成器（設計書/部品/spec-DATA）を直して再実行する（生成物でなく生成器を直す）
- **レッドチーム校閲**: `reviewer` 退役（2026-06-24・keystone）。プロンプトの攻撃耐性・分岐・出力安全性は**壁打ち時に人間+Claude が out-of-line で点検**（`docs/ai/skills/SKILL_redteam_review.md`）
- **設計書の不備**: `qa_validator.py` が機械的に 40 項目検証 → `fix_category="auto"` の Issue は `yaml_auto_fixer.py` が正規表現置換で自動解消（T-3 / T-4 / L-5 / E-8 等）→ 残った CRITICAL は **人間（壁打ち）へ差し戻し**（2026-06-19〜 director 自律リトライは廃止）。壁打ちで設計書を直してパイプラインを再実行する（下記「壁打ちブリッジ」節）

### 壁打ちブリッジと修復の所在（2026-06-19〜 / ループ・ガバナンス v0.2 §9）

- **設計書は「人間 ⇄ Claude の壁打ち」で作る／直す**のが基本。壁打ち成果（設計書 YAML）を自由ゾーン `output/scenarios/{施設}_{flow}/` に置いてパイプラインに流す。
- **qa_validator の差し戻し先は人間（壁打ち）**。CRITICAL が残れば差し戻し票（差し戻し元ゲート / check code / 設計書パス / JSON レポート）を出して halt する。**director の自律リトライは置かない**（ライン内に自律修復 LLM を置かない方針）。
- **修復は「成果物を手で直す」のではなく「設計書（＝生成器入力）を壁打ちで直して再実行」**する。決定論パイプラインは即時なので再実行が安く、**生成物でなく生成器を直す**のがベストプラクティス。
- 全体像・構想は `project-governance/docs/loop-governance.md` §9（VFB 製造ライン v2）を参照。
- **Phase 2（工場長 / 壁打ち入口 / 部品カタログ・2026-06-24）**: テスト後の解析・起票・部品調達は **`@工場長`（ライン外・Sonnet）**。壁打ち入口は **`/sparring-intake`** skill（`tools/sparring_agenda.py` が qa＋surfacing＋部品カタログを 1 枚のアジェンダに束ねる）。調達可能な認定部品の一覧は `modules/parts_catalog.json`（`tools/generate_parts_catalog.py` 生成）。設計: `docs/governance/factory-v2-phase2-foreman.md`。

### セッション改善サイクル（2026-07-15〜 / 防ぐが勝ち・エラーは1回だけ）

- **各作業セッションの冒頭に `/session-kaizen` を 1 回呼ぶ**（軽量・宣言のみ）。セッション末に「収穫チェック」を行い、学びを repo に着地させる（7 カテゴリ×着地先マップは skill 参照）。
- **着地優先度: ①機械ゲート > ②データ > ③Skill > ④文書**。手で直して終わり・チャットにだけ残る改善は成果と見なさない。
- 事故・不具合は `docs/incidents/` に INC-ID 付きで記録し、**必ず機械ゲート化を検討**する（例: INC-260629-1 恵佑会 P7 乖離 → `verify_test_bivr.py` 自動ゲート）。

---

## 非エンジニア向けコミュニケーション規程（全応答に適用・必読）

> **本リポジトリのユーザーには技術バックグラウンドの無い人が含まれる。**
> Claude Code は仕事の受付・進捗報告・確認・エラー報告のすべてで、専門用語
> （スクリプト名 / パイプライン工程名 / Git・GitHub 用語）を**単独で使わず**、
> 「用語（＝やさしい説明）」の形で必ず併記する。ユーザーに判断を求めるときは
> 選択肢を「選ぶとどうなるか」で説明し、不可逆操作（上書き・削除・本番反映）は
> 何が消える/変わるかを具体的に言ってから確認する。
> 用語対訳表・場面別ルールの正本: **`docs/specs/spec-kit-communication.md`**

---

## プロジェクト概要

本リポジトリは、**病院向けボイスボットのIVRフロー（JSON）を AI で自動生成・校閲・検品する**ためのワークスペースです。

---

## AIの担当スコープ（重要）

設計書 YAML の `scenario_flow` ブロック構造を中心としたパイプライン。allowlist は `schemas/qa_validator.py` の `KNOWN_BLOCK_TYPES` が正本（2026-07-10 時点で **26 種**。2026-05〜07 に段階的追加され、本行は追随して更新すること）。基本9型（opening / announcement / hearing / subflow / context_match_router / script / date_of_call_classifier / call_transfer / termination）＋ `augment`（placeholder 型、新ブロック未実装時の暫定枠。WARNING扱いで人間レビューへ回す）に加え、個人情報スロット系（slot / patient_name / dob / phone / card_number）・電話番号系（incoming_category_classifier / phone2name / phone_branch）・診療科系（clinical_department / clinical_department_normalize / clinical_department_classifier）・用件・FAQ系（intent / faq）・その他（cmr_chain / null_check / free_text）が追加済み。全26種の使い分け・重複実装（用件判定=intent とscript_blocksのyoken等）の詳細は `.claude/skills/flow-draft/SKILL.md` の早見表を参照。LLM は「LLM でしか判断できない部分」のみ担当する。

| 担当 | 内容 |
|---|---|
| **AI（director）** | 顧客要望の解析 → 設計書 YAML の生成（scenario_flow ブロック定義 + step_details + termination_patterns）→ 確認レポート |
| **プログラム（qa_validator.py）** | 設計書の機械的検証（40 項目、T / L / E / I / F / M 系）。`fix_category="auto"` を付けた Issue は `yaml_auto_fixer.py` で決定論的に解消 |
| **プログラム（yaml_auto_fixer.py）** | `qa_validator.py --json-report` の出力を読み、`fix_category="auto"` の Issue を正規表現置換で修正。コメント保持。LLM 不使用（Phase 1: T-3 / T-4 / L-5 / E-8 対応）|
| **プログラム（scaffold_generator.py）** | YAML の scenario_flow から完成品 JSON を機械生成。allowlist 26 ブロック型をビルダー関数で組み立て、復唱（echo_back）・ContextMatchRouter・終話チェーンも自動配置。**TODO_scaffold = 0**（generator パッチ不要）。個人情報4種（氏名/生年月日/電話番号/診察券番号）は新規作成では `slot`/`card_number` で決定論インライン展開が既定（Jump to Flow を使わない）。`type: subflow` で明示指定された場合もこの4種に該当すれば同じインライン展開にフォールバックする（2026-07〜） |
| **プログラム（layout_calculator.py）** | DAG ベースで縦型レイアウトを計算。分岐は横展開、合流後は共通パス。終話チェーンも自然にぶら下がる |
| **AI（generator）** | scenario_flow がある場合はスキップ（scaffold が完成品を出すため）。後方互換用にレガシー routing_map 形式のみ稼働 |
| **AI（prompter）** | generate_by_OpenAI の params.prompt を **ブロック単位** で記述。orchestrator が対象モジュールを設計書から列挙して指示。JSON 全文 Read 不要。Yes/No 判定は scaffold が固定プロンプトを埋め込み済み |
| **プログラム（gen_properties.py）** | IVRプロパティ（TTS発話文言）を生成。scaffold TTS サイドカー + 設計書 YAML から完全決定論的に生成。LLM 不使用。prompter と並列実行 |
| **AI（reviewer）** | **退役（2026-06-24・keystone: ライン内 LLM ゼロ）**。レッドチーム校閲（攻撃耐性・分岐判断・出力安全性）は壁打ち時に人間+Claude が out-of-line で実施（知見: `docs/ai/skills/SKILL_redteam_review.md`・旧定義: `.claude/agents/archive/reviewer.md`） |
| **AI（fixer）** | **新規ビルドの自律修復（step_fixer）は退役（2026-06-24・keystone）**＝残存 Critical は人間壁打ちへ。fixer エージェント自体は **Pattern 2 の外科的修正（step_fixer_modify・人間の差分指示駆動）でのみ存続**（governance §1-7 surgical patch） |
| **AI（tester）** | tester.py を実行して構造監査（フラット化して監査） |
| **プログラム（tester.py）** | 構造監査（サブフロー再帰インライン展開 + AUD-1/AUD-2/R-1/R-2/R-3） |
| **プログラム（validator.py）** | JSON 構造の機械的検証。N-002 / N-003 / LAYOUT-002 / LAYOUT-003 等の重大 Warning は Critical に昇格済み。`fix_category="auto"` を付けた Issue は `auto_fixer.py` で決定論的に解消（CTX-017 displayType 重複 / status 0-5 / LAYOUT deoverlap 等）|
| **プログラム（auto_fixer.py）** | `validator.py --json-report` の出力から `fix_category="auto"` の Issue を読み、JSON を決定論的に修正（op: set / replace / deoverlap_layout / dedup_displaytype / recalc_layout）。LLM 不使用 |
| **プログラム（block_mapper.py）** | 設計書 YAML から「モジュール名 → ブロック名」の逆引き辞書を生成。fixer がブロック単位で修正範囲を絞るために使用 |
| **プログラム（orchestrator.py）** | パイプライン全体の自動制御。並列実行・Git自動ブランチ・Human-in-the-Loop承認 |
| **プログラム（gen_p7_cases.py + connection_test/stub_stt_connection.py）** | Pattern 7 連結テストの自動生成。設計書 YAML から全エッジ網羅ケース表（下書き）→ STT スタブ bivr。実機の駆動（インポート・発信）は人間 |
| **プログラム（oracle_gate / certified_hashes.json）** | bivr 内 @General$Script を modules/ 正本と **engine/spec 二段ハッシュ**で照合（engine=部品種別の刻印・spec=規格データ・wiring=入力元/保存先は除外）し、各部品の test_oracle.py を自動実行。P6 は **engine 既知＆spec 認定済みでスキップ／engine 不一致はブロック／新規 spec は受入要求**（「1 文字でも改変したら再受入」の機械化）。仕様: `docs/governance/part-certification-spec.md` |
| **人間** | 確認レポートの BLOCKER 解消、IVRプロパティの最終確認、電話番号設定、Dr.JOY側設定、最終 Push 承認 |

- director / prompter は Opus モデル
- generator / tester / fixer は Sonnet モデル（**reviewer は退役 2026-06-24・keystone**＝校閲は壁打ち時に out-of-line）
- **工場長 は Sonnet モデル（ライン外）** — テスト完了後に残差を triage・解析しレポート／PR・Issue 起票／部品調達（`tools/new_part_skeleton.py`）。**自律修復しない・認定は人間ゲート**。定義: `.claude/agents/工場長.md`
- properties は LLM 不使用（gen_properties.py スクリプト）
- TTS 発話テキスト・API URL 等はモジュール内に埋め込まず、IVRプロパティ側で定義する前提
- TTS プロンプトは **`{tts_g:...}` 形式（全小文字）をデフォルト**とする。新規に `{tts_ai:...}` 形式（全小文字、AI TTS）も選択可能だが本番稼働待ち。**`{TTS_AI:...}`（大文字）は誤り**、使わない。SSML タグ（`<speak>`, `<break>`, `<say-as>` 等）は使用禁止
- **プロパティの設定がモジュール内設定より常に優先される**

---

## モジュール / script 開発ポリシー — 決定論優先・受入テスト必須（2026-06-04 確定）

> **方針: OpenAI プロンプトで解いている判定は、決定論的に書けるものから module / script に置き換えていく。**
> LLM に残すのは「自由発話の解釈」など決定論で書けない部分のみ。
> 置き換えの優先順位・進め方: `docs/governance/deterministic-replacement-roadmap.md`

### 新規 module / script の必須要件（Definition of Done）

1. `REQUIREMENTS.md` — 入出力仕様・分岐・エッジケースを文書化
2. **Python オラクル**（`oracle.py` + `test_oracle.py`）— 全ケース PASS
3. **Brekeke 実機受入テスト**（Pattern 6 テストフロー）— 全ケース PASS
4. オラクルと実機の判定一致を確認（デプロイ済み JS とのバイト一致確認が理想）
5. `modules/README.md` の認定レジストリに登録（テスト実績・日付つき）

- **受入テストを通過していない module / script を本番シナリオに組み込んではならない**
- 認定済み部品の「そのまま利用」は再テスト不要。**1 文字でも改変したら再受入**
- シナリオ内の script ブロック（ゲート判定等）も同様 — 新規ロジックはオラクル + 受入通過が要件
- 標準構成・テスト設計の制約（1 コール 1000 モジュール上限等）は `modules/README.md` 参照

---

## 成果物の置き場所（master 保護方針）

> **施設別の成果物は必ず `output/scenarios/{施設}_{flow}/` 配下に集約すること。**

GitHub が個人アカウントのため master 保護のためにブランチ運用しており、本来 master に成果物は置かない方針。やむを得ず master に成果物が混入する場合も、**`output/scenarios/{施設}_{flow}/` で施設単位に分離**することで master が散らからないようにする。

### 配置ルール

| 種類 | 置き場所 |
|---|---|
| 設計書 YAML / .bivr / 確認レポート / fixer_report | `output/scenarios/{施設}_{flow}/` |
| **properties_*.md** | `output/scenarios/{施設}_{flow}/`（gen_properties.py が直接出力）|
| **prompts_*.md（prompter サイドカー）** | `output/scenarios/{施設}_{flow}/` |
| **pipeline_state_*.json** | `output/scenarios/{施設}_{flow}/`（orchestrator が直接出力）|
| **qa_audit_*.md** | `output/scenarios/{施設}_{flow}/` |
| 中間 JSON（`scaffold_*` `draft_*` `prompted_*` `reviewed_*` `merged_*`）| `output/json/`（共通ビルドディレクトリ、最終的に scenarios へ collect）|
| 中間レポート（`review_report_*` `test_report_*` `dirlite_report_*` `garbage_*` `refresh_instructions_*`）| `output/reports/`（パイプライン中の中間成果物）|

### 禁止

- `output/` 直下に施設依存ファイル（`properties_*.md` `pipeline_state_*.json` 等）を直接書き出さない
- `output/` 直下に作業用 Python スクリプト（`gen_*.py` `check_*.py` `fix_*.py` 等）を作成しない（CLAUDE.md「作業用 Python スクリプトの生成・実行は禁止」と重複ルール）
- `output/` 直下に `tmp_*.txt` 等の一時ファイルを残さない

---

## コラボレーション運用 — allowlist 方式（重要）

本リポジトリは複数メンバーがカスタマイズする。**「触ってよい場所」を allowlist で定義し、それ以外はすべて保護ゾーン**とする。人間向けの詳細ルールは `CONTRIBUTING.md`。

### 自由ゾーン（シナリオ作業はここだけ）

- `output/scenarios/{施設}_{flow}/` — シナリオ成果物・顧客資料（`reference/`）

### 保護ゾーン（上記以外すべて）

`CLAUDE.md`・`.claude/`（agents / skills / settings.json / patch_box）・`.github/`・パイプライン本体（`scripts/` `schemas/` `tools/`）・`docs/ai/skills/`・`docs/brekeke/`・`.gitignore`・`requirements.txt` 等。
変更にはコードオーナー（@TS-dong-nc）の PR レビューが必須。CODEOWNERS + guard-master.yml + ブランチ保護で機械的に守られている。

### 全エージェント共通ルール

- master へ直 push してよいのはオーナー（浜口）のみ。それ以外の環境では feature ブランチ → PR
- 保護ゾーンのファイルは Edit/Write しない。変更が必要だと判断したら、変更内容を提案としてユーザーに提示する
- 依存追加（`requirements.txt`）はオーナー承認制。インストール禁止ルール（上記「絶対遵守事項」）と併せて遵守

---

## PATCH_BOX — 動的コンテキスト（最優先ルール）

> **全 Agent / pipeline 起動時に必ず最初に確認すること。**

`.claude/patch_box/current/*.md` に置かれた `*.md` ファイルがあれば、**.claude/agents/*.md（director 等の恒久 prompt）より優先**して従う。これは「この実行限定の例外指示」を人間が直前に渡すための仕組み（例外処理の箱）。**CLAUDE.md の恒久ルール（セキュリティ・インストール禁止・コラボレーション運用等）を上書きする用途には使わない**（階層: CLAUDE.md=憲法 / agents=法律 / patch_box=実行限定の例外。README 参照）。

- **読み方**: 各 Agent は起動時に環境変数 `VFB_PATCH_BOX_CONTEXT` または `.claude/patch_box/current/` 配下の `.md` を読む
- **適用範囲**: そのパイプライン実行のみ。pipeline 完了後は orchestrator が自動で `consumed/{timestamp}_{filename}` へアーカイブ
- **書き方の例**:
  - 「今回だけ qa_validator E-X を skip」「○○施設は scaffold で特殊なフィールド処理が必要」
  - 「今日の review では reviewer が指摘してきた○○は無視（明日の本番投入に間に合わせるため）」
- **書かないもの**: 永続化すべきルールは `CLAUDE.md` か `.claude/agents/*.md`。施設固有・恒久的な指示は将来 `patch_box/per_facility/` へ（Phase 2）
- **git 管理外（ローカル専用）**: `current/*.md` は `.gitignore` 済みだが、**例外処理の仕組み自体はこれまで通り動く**（orchestrator はローカル filesystem から読む）。封じているのは「repo 経由で他環境の実行に例外指示を配布する」経路のみ。例外指示は各自のマシンで起動直前に置く（fresh-clone 環境へは env var `VFB_PATCH_BOX_CONTEXT` で渡す）。コミット対象に `current/*.md` が混入していたら違反としてユーザーに報告する
- **詳細仕様**: `.claude/patch_box/README.md` 参照
- **構想**: `.claude/projects/.../memory/project_patch_box_governance_design.md`

> 注: 現在は **Phase 1 (current/ のみ)**。 per_facility/ per_phase/ は仕様検討中。

---

## Git ブランチ運用 — push 後は必ず master 追随（2026-07-17〜）

> **feature ブランチへ push した直後は、必ず master の最新コミットを取り込むこと。**

- push 完了ごとに `git fetch origin master && git merge origin/master`（またはコンフリクトが無ければ rebase）でブランチを master に追随させる
- 目的: 複数エージェント/複数人が同時並行で master にマージしていく運用のため、ブランチが古いまま作業を続けると重複実装・コンフリクト・PR 却下（すでにマージ済み内容の再提出）が起きる
- **PR がマージ済みと判明した場合**: そのブランチに新規コミットを積み増ししない。`git fetch origin master && git checkout -B <branch> origin/master` でブランチを最新化し、未マージの新規作業だけを cherry-pick or rebase して積み直してから新しい PR を作る（本 CLAUDE.md 冒頭のシステムプロンプト規約と同じ扱い）

---

## パイプライン自動化の大原則 — 壁打ち不要・エラーは fix pipeline に戻す（2026-07-17〜）

> **本プロジェクトの一番の目的: CSV/設計書入力 → 完成品 JSON（.bivr）まで、パイプラインが人間の壁打ちなしに一気通貫で自動的に動くこと。最終目標は「パイプラインの完全自動化」。**

- パイプライン実行中にエラー・バグが出た場合、その場しのぎで生成物（YAML/JSON/スクリプト）を手で直して終わらせない
- **原則: 生成物ではなく生成器（パイプラインのコード側）を直す。** 具体的には:
  1. エラーの根本原因を pipeline のどのステップ（`csv_to_yaml.py` / `scaffold_generator.py` / `qa_validator.py` / `validator.py` / `auto_fixer.py` 等）が引き起こしているか特定する
  2. そのステップのコードを修正する（決定論的に・LLM 最小限で）
  3. **パイプラインを最初から（または該当ステップから）再実行**して、修正が正しく機能し、後続ステップまで通ることを確認する
- 壁打ち（人間 ⇄ Claude の対話で都度パッチ）は例外対応であり、目指す姿ではない。壁打ちで気づいた不具合は、その場で終わらせず「なぜパイプラインが自動で防げなかったか」を必ず問い、コード側（validator の新チェック・generator のロジック改善等）へ着地させる
- この原則は上記「セッション改善サイクル」（着地優先度: ①機械ゲート > ②データ > ③Skill > ④文書）と同じ思想の徹底版：**①機械ゲート／パイプラインコードでの恒久解決を常に最優先**とする

---

## システム構成

| コンポーネント | 説明 |
|---|---|
| Brekeke IVR | 通話制御エンジン。JSONフローを読み込んで電話応対を実行 |
| AmiVoice STT | 音声認識（Speech to Text）エンジン |
| TTS (Text to Speech) | 音声合成。**デフォルト: `{tts_g:...}` 形式**（全小文字）。本番稼働後に `{tts_ai:...}`（全小文字、AI TTS）に切り替え予定。`{TTS_AI:...}`（大文字）は誤り。SSML 不可 |
| OpenAI Assistant API | 用件分類・正規化・分岐判定（generate_by_OpenAI モジュール） |
| Dr.JOY 連携 | 予約・患者情報の API 連携 |

## パイプライン全体像

```
director → qa_validator
  ↳ CRITICAL 検出 → yaml_auto_fixer (fix_category=auto を機械修正)
    → qa_validator 再実行
    → 残存 CRITICAL は 人間（壁打ち）へ差し戻し（director 自律リトライ廃止 / 2026-06-19）
  → copy_subflows（個人情報4種以外のサブフロー: FAQ family / 用件聴取 等）
  → scaffold (完成品 JSON 生成。個人情報4種は決定論インライン展開・Jump to Flow 不使用)
  → gen_scripts (設計書 YAML の script_blocks から ES5 Scripts 自動生成。script_blocks 未指定なら no-op)
  → layout (縦型レイアウト計算)
  → generator (scenario_flow 検出 → スキップ)
  → prompter + gen_properties.py (並列: prompter=LLM, properties=スクリプト)
  → (reviewer 退役 2026-06-24: 校閲は壁打ち時に out-of-line＝keystone)
  → merge → validator (構造チェック)
  → add_date → tester + build (並列)
  → auto_fixer (fresh validator + 機械修正: CTX-017 / status / LAYOUT 等)
  → (fixer 退役 2026-06-24: 残存 Critical は LLM 修正せず人間壁打ちへ＝keystone)
  → collect_scenario → phonebook_csv (設計書 phonebook セクションから Dr.JOY 電話帳 CSV 生成。無ければ skip) → commit
  → oracle_gate (部品オラクル受入・自動)
  → p7_gen (連結テスト生成) → p7_acceptance (Human: 実機・結合)
  → p6_gate (engine/spec 二段判定 → 未認定 spec のみ単体実機) → commit_evidence
  → score_gate (4層採点ゲート: 成績表出力＋出荷可否判定) → approve (完成品ゲート: oracle+P7+P6 全 PASS のときだけ push 可)
```

---

## 共有スキルファイル（各エージェントが必要に応じて参照）

| ファイル | 内容 | 対象エージェント |
|---|---|---|
| `docs/ai/skills/SKILL_JSON_rules.md` | JSON構造規則・モジュールタイプ・next/subs規則・命名規則・フロー設計原則・システム変数 | fixer / reviewer / dirlite |
| `docs/ai/skills/SKILL_quality_criteria.md` | プロンプト品質基準（tester.py 4本柱） | reviewer / fixer / tester |
| `docs/ai/skills/SKILL_A〜E_*.md` | OpenAIプロンプトテンプレート（分類/Yes_No/日付/正規化/自由テキスト） | prompter |
| `docs/brekeke/モジュール選定ガイド_v2.md` | ブロック型の使い分け（基本9型中心。allowlist全26種の最新一覧は `schemas/qa_validator.py` の `KNOWN_BLOCK_TYPES` および `.claude/skills/flow-draft/SKILL.md` 参照）・output_format判定（datetime/text/enum）・診療科 no_result パターン・氏名聴取の PatientName サブフロー 1 枠ルール（§3.1.1）| director / scaffold_generator / reviewer |
| `docs/ai/skills/SKILL_診療科.md` | 診療科名正規化スクリプト（kamei_normalize.js）生成。DEPARTMENTS辞書・WAKARANAI・最長一致ロジック・ES5.1/Nashorn制約。Script ブロックで診療科分類が必要な場合に使用 | director / prompter |
| `docs/ai/skills/SKILL_用件.md` | 用件判定スクリプト（intent classifier）生成。インタビュー→STRONG/WEAK分類→setResult/setObject実装→テストケース出力。Script ブロックで用件分類が必要な場合に使用 | director / prompter |
| `docs/ai/skills/SKILL_FAQ_Prompt.md` | FAQ照合 OpenAI プロンプト生成。FAQリスト→質問文完全一致出力または NO_RESULT。generate_by_OpenAI ブロックで FAQ 照合が必要な場合に使用 | director / prompter |
| `docs/ai/skills/SKILL_FAQ_Scripts.md` | FAQ判定 Scripts（ES5）または OpenAI プロンプト生成。AmiVoice→RAG→完全一致判定→ANSWER/NO_RESULT分岐。FAQ ブロックのスクリプト・プロンプト両用 | director / prompter |
| `docs/ai/skills/SKILL_希望日.md` | 予約希望日・予約希望時期・変更希望日・変更希望時期の OpenAI プロンプト固定テンプレート。9 ステップ判定ロジック。NO_RESULT を返さず、不明入力はそのまま出力、希望なしは `希望日無し` を返す | director / prompter |

> **詳細仕様・Git運用ルール・ディレクトリ構成**: `README.md` を参照。
