# bivr-checker プロジェクトドキュメント

> 作成日: 2026-04-27

---

## 1. プロジェクト定義

### 目的

**VoiceBot Flow Builder (VFB)** が自動生成する `.bivr` ファイルと `Property.md` の品質を、人間が手作業で作成したものと同等以上に引き上げるための品質保証プロジェクト。

### 背景

- VFBが生成するフローJSONには構造的なエラー・プロンプト不足・辞書欠落などの品質問題が多い
- 人間が毎回手修正するのは工数が大きいため、修正パイプラインを自動化している
- 修正前後の差分を教師データとして蓄積し、VFB自体の生成品質向上にもフィードバックする

### ランタイム

修正済み `.bivr` ファイルは **Brekeke PBX** にアップロードし、AI電話の自動応答フローとして稼働する。

### 実績

計14施設の修正を完了（スコア82.9〜97.3点）。教師データは pair_01〜pair_11 の11施設分を収録。

---

## 2. パイプライン概要（Stage 0〜8）

```
入力: input/{施設名}/*.bivr + properties_*.md + *.pdf
  |
  Stage 0: EXTRACT        — .bivr → フローJSON展開
  Stage 1: STRUCTURAL_FIX — 構造的エラーの自動修正
  Stage 1.7: RETRY_PATTERN — Retry Counterパターン自動分類・修正
  Stage 2: PROFILE_WORDS  — AmiVoice辞書(profile_words)生成 (@pw-generator)
  Stage 3: PROMPT_APPLY   — OpenAIプロンプト テンプレート適用 (@prompt-enhancer)
  Stage 4: PROPERTY_FIX   — Property.md整合性修正
  Stage 5: VERIFY         — 品質検証（80点以上で合格）
  Stage 6: BUILD          — .bivrビルド
  Stage 7: CALL_TEST      — 模擬通話テスト（10パターン全PASS必須）
  Stage 8: REPORT         — 修正レポート生成
  |
出力: output/{施設名}/{施設名}_fixed.bivr
```

---

## 3. ディレクトリ構成

```
bivr-checker/
├── CLAUDE.md              # 全ルール集（フローJSON・Property.md・モジュール仕様）
├── PIPELINE_SPEC.md       # パイプライン仕様書（Stage 0-8の実行コマンド・品質ゲート）
├── PROJECT_DESIGN.md      # プロジェクト設計書
├── KNOWLEDGE_BASE.md      # ナレッジベース
├── PROGRESS_LOG.md        # 進捗ログ
├── scripts/               # パイプラインスクリプト群（後述）
├── reference/             # ルール・テンプレート・辞書
│   ├── defaults.json           # デフォルト値カタログ
│   ├── defaults_overrides/     # VFB頻出エラーパターン蓄積
│   ├── templates/              # モジュールテンプレート(JSON)
│   ├── subflows/               # サブフローテンプレート
│   ├── prompts/                # OpenAIプロンプトテンプレート
│   ├── dictionaries/           # AmiVoice辞書（氏名・生年月日・肯定否定）
│   ├── scripts/                # Scriptモジュール用JSテンプレート
│   ├── context/                # コンテキストフィールド定義
│   └── env/                    # 環境設定(demo/prod)
├── schemas/               # JSONスキーマ定義
├── training_data/         # 教師データ（VFB生成+人間修正ペア）
│   ├── pair_01〜pair_11/       # 各施設の突合ペア
│   ├── cross_analysis.md       # 横断分析結果
│   └── feedback/corrections/   # 修正前後ペア蓄積
├── input/                 # VFB出力（施設別）
│   └── {施設名}/*.bivr, *_Property.md, *.pdf
├── output/                # 修正済み出力（施設別）
│   └── {施設名}/extracted/, fixed/, reports/
└── .claude/agents/        # Claude Codeエージェント定義
    ├── diff-analyzer.md        # VFB vs 人間の差分分析
    ├── fixer.md                # 自動修正
    ├── orchestrator.md         # パイプライン制御
    └── finisher.md             # 仕上げ屋
```

---

## 4. コアスクリプト一覧（パイプライン構成）

### 4.1 `extract_bivr.py` — .bivr展開（Stage 0）

| 項目 | 内容 |
|---|---|
| **用途** | `.bivr` ファイル（ZIPアーカイブ）からフローJSONを展開する |
| **入力** | `.bivr` ファイルパス |
| **出力** | `output/` 配下にフロー名ごとの `.json` ファイル |
| **主な処理** | ZIPエントリ名のURLデコード → フロー名復元 → JSON pretty-print出力 |
| **オプション** | `--list`（一覧表示のみ）、`--minified`（1行出力）、`-o`（出力先指定） |

### 4.2 `structural_fixer.py` — 構造修正（Stage 1）

| 項目 | 内容 |
|---|---|
| **用途** | VFBが繰り返す既知エラーパターンを機械的に一括修正する |
| **入力** | フローJSON（1つまたは複数） |
| **出力** | 修正済みフローJSON（上書き） |
| **修正関数（17個）** | DTMF termdtmf/stop_play修正、Retry prompt_true標準化、prompt_false設定、save2db接続、saveCompletionFlag status修正、TTS label修正、stop_by_dtmf修正、STT success統合、DTMF retry/prompt修正、matchingmethod/キー順序/detection_flag/スロット数/全角数字修正 等 |
| **検出のみ** | ContextMatchRouter欠落、Re-confirmation欠落、profile_words空、DRY原則違反、到達不能モジュール |
| **オプション** | `--dry-run`（変更せず検出のみ） |

### 4.3 `retry_pattern_fixer.py` — Retryパターン修正（Stage 1.7）

| 項目 | 内容 |
|---|---|
| **用途** | Retry Counterの `prompt_false` / 遷移先を設計書に基づき自動分類・修正する |
| **入力** | フローJSON |
| **出力** | 修正済みフローJSON |
| **パターン体系** | **A.** 任意聴取→次へ進む、**B.** 失敗→終話、**C.** 必須聴取→無限ループ |
| **判定ロジック** | 用件/区分の必須項目→パターンC、設計書で終話指定→B、その他→A |

### 4.4 `pw_analyzer.py` — profile_words分析（Stage 2 前処理）

| 項目 | 内容 |
|---|---|
| **用途** | フローJSON内の全STT/DTMFモジュールの辞書状態を分析し、入力種別を判定する |
| **入力** | フローJSON |
| **出力** | 分析結果（各モジュールの語数・状態・入力種別・対応要否） |
| **判定項目** | 語数（empty/insufficient/adequate/excessive）、フィラー有無、頭切れ有無、入力種別（用件/氏名/生年月日/診療科/復唱/日付/フリーテキスト等） |

### 4.5 `apply_prompt_templates.py` — プロンプトテンプレート適用（Stage 3）

| 項目 | 内容 |
|---|---|
| **用途** | フローJSON内の全OpenAIモジュールに標準テンプレート（7セクション構造）を自動適用する |
| **入力** | フローJSON + `reference/prompts/prompt_templates.json` |
| **出力** | プロンプト更新済みフローJSON |
| **スキル分類** | 用件分類(SKILL_A)、肯定否定(SKILL_B)、日付(SKILL_C)、正規化(SKILL_D)、フリーテキスト(SKILL_E) |

### 4.6 `property_fixer.py` — Property.md修正（Stage 4）

| 項目 | 内容 |
|---|---|
| **用途** | フローJSONとProperty.mdの整合性チェック・自動修正 |
| **入力** | フローJSON + Property.md |
| **出力** | 修正済みProperty.md（`--fix` オプション時） |
| **チェック項目** | TTSモジュール名とプロンプトキーの一致、必須セクション（amivoice設定・API URL・RAG設定）の存在、環境URL整合性（demo/prod混在チェック） |

### 4.7 `validator.py` — バリデーション（Stage 5 前半）

| 項目 | 内容 |
|---|---|
| **用途** | フローJSONがBrekeke IVR仕様に適合しているかを自動検証する |
| **入力** | フローJSON（複数可） + Property.md（オプション） + サブフロー（オプション） |
| **出力** | 検証結果（CRITICAL/WARNING/INFO） |
| **検証項目（77項目）** | 構造(S-001〜S-004)、遷移(T-001〜T-004)、STT(STT-000〜STT-004)、TTS(TTS-001〜TTS-003)、OpenAI(OAI-001〜OAI-004)、Retry(R-001〜R-005)、サブモジュール(SB-001〜SB-002)、コンテキスト(CTX-010〜CTX-017)、完了フラグ(COMP-001)、命名(N-001〜N-003)、DTMF(DTMF-001〜DTMF-004)、フロー構造(FLOW-001〜FLOW-008)、プロンプト(PROMPT-001〜PROMPT-007)、到達性(REACH-001〜REACH-003)、レイアウト(LAYOUT-001〜LAYOUT-005)、Property(PROP-001〜PROP-004)、クロス(CROSS-001〜CROSS-003) |

### 4.8 `verify_fixes.py` — 品質スコアリング（Stage 5 後半）

| 項目 | 内容 |
|---|---|
| **用途** | 修正済みフローJSONの品質を教師データの統計と照合し、100点満点のスコアを算出する |
| **入力** | フローJSON（複数可） |
| **出力** | 品質スコア + 各カテゴリ別の得点 |
| **評価カテゴリ** | A: profile_words品質（語数・フィラー・頭切れ）、B: OpenAIプロンプト品質、C: 構造（detection_flag・全角数字等）、D: Retry→TTS接続の自然さ |
| **合格基準** | 80点以上、BLOCKER警告なし |

### 4.9 `build_bivr.py` — .bivrビルド（Stage 6）

| 項目 | 内容 |
|---|---|
| **用途** | 修正済みフローJSONから `.bivr` パッケージ（ZIPアーカイブ）を生成する |
| **入力** | フローJSON（複数可） |
| **出力** | `.bivr` ファイル |
| **主な処理** | フロー名のBrekeke互換URLエンコード → JSON minify → ZIPアーカイブ化 |
| **オプション** | `--merge-base`（元bivrのフローを引き継ぎ差し替え）、`--facility`（施設フィルタで他施設混入防止） |

### 4.10 `test_calls.py` — 模擬通話テスト（Stage 7）

| 項目 | 内容 |
|---|---|
| **用途** | フローJSONをプログラム的にたどり、全分岐パスの到達テストを行う |
| **入力** | フローJSON（メイン+サブフロー） |
| **出力** | テスト結果（PASS/FAIL × パターン数） |
| **主な処理** | startモジュールから全OpenAI分岐の組み合わせを自動生成し、Disconnectまで到達できるか検証。サブフロー（Jump to Flow）も横断追跡 |
| **合格基準** | 自動生成10パターン全PASS |

### 4.11 `report_generator.py` — レポート生成（Stage 8）

| 項目 | 内容 |
|---|---|
| **用途** | 施設の修正結果をMarkdown形式のレポートにまとめる |
| **入力** | 出力ディレクトリ（フローJSON + 品質検証結果） |
| **出力** | `fix_report.md`（修正内容・スコア・残件のサマリー） |

---

## 5. 分析・ユーティリティスクリプト

### 5.1 `analyze_profile_words.py`

| 項目 | 内容 |
|---|---|
| **用途** | 教師データ（pair_01〜20）全体の profile_words 傾向を横断分析する |
| **処理** | 全 `.bivr` からSTT/DTMFモジュールを抽出し、辞書の語数・パターンを統計集計 |

### 5.2 `extract_baseline.py`

| 項目 | 内容 |
|---|---|
| **用途** | pair_01（帯広第一病院）のVFB生成版から profile_words と OpenAI プロンプトのベースラインを抽出する |
| **処理** | 教師データのフローを解析し、VFBがどの程度の辞書・プロンプトを生成しているかを調査 |

### 5.3 `analyze_iruma_diff.py`

| 項目 | 内容 |
|---|---|
| **用途** | 入間ハート病院の3バージョン（VFB→Fixed→Human）差分を4項目で比較分析する |
| **処理** | 各バージョン間の構造・プロンプト・辞書・Property差分を出力 |

### 5.4 `build_iruma_heart.py`

| 項目 | 内容 |
|---|---|
| **用途** | 入間ハート病院のメインフロー＋4サブフローを `.bivr` にパッケージ化する |
| **処理** | 施設固有のビルドスクリプト（汎用 `build_bivr.py` の特化版） |

### 5.5 `training_data/pair_01/generate_profile_words.py`

| 項目 | 内容 |
|---|---|
| **用途** | 帯広第一病院用の profile_words を生成するジェネレーター |
| **処理** | フィラー14種 × 語尾8種 × 頭切れパターンを自動展開して辞書エントリを生成 |

---

## 6. 施設固有修正スクリプト（`fix_*.py` / `gen_pw_*.py` / `enhance_*.py`）

各施設のパイプライン実行時に発生した個別問題を修正するアドホックスクリプト群。パイプラインの汎用スクリプトではカバーできない施設固有の修正を行う。

| カテゴリ | スクリプト例 | 内容 |
|---|---|---|
| **横浜労災病院** | `fix_yokohama_rousai.py` 〜 `_v5.py` | v1〜v5の段階的修正（レイアウト・プロンプト・フロー順序・DOB復唱等） |
| **帝京大学附属溝口病院** | `fix_teikyo_mizoguchi_v1.py` 〜 `_v5.py` | プロンプト一致・レイアウト・save2db接続・辞書・分岐漏れ修正 |
| **横須賀共済病院** | `fix_yokosuka_*.py`（7ファイル） | CRITICAL修正・フィードバック対応・profile_words・プロンプト強化・サブフロー・コンテキスト・終話パス |
| **帯広第一病院** | `fix_obihiro*.py`（3ファイル） | メインフロー修正・matchingmethod・ContextMatchRouter |
| **健生病院** | `fix_kensei_*.py`（2ファイル） + `fix_layout_kensei.py` | 丸数字除去・profile_words・プロンプト・レイアウト |
| **海風診療所** | `fix_kaifu_all.py` | サブフロー結果返却・OAI module参照修正 |
| **関東労災病院** | `fix_kanto_rosai_*.py`（3ファイル） | Stage1追加・profile_words・verify結果修正 |
| **宇治徳洲会病院** | `fix_uji_*.py`（3ファイル） | スロット数・detection_flag・リトライ・fields |
| **沖縄県立中部病院** | `fix_okinawa_all.py`, `_retry.py` | Stage1+2+5一括・リトライ修正 |
| **沖縄県立南部医療センター** | `fix_okinawa_stage1.py` 〜 `_stage5.py`, `_chiiki.py`, `_prompt_align.py` | 診療フロー(Stage1-5) + 地域連携フロー |
| **鎌ケ谷総合病院** | `fix_kamagaya_*.py`（2ファイル） | Stage1+PW+self_contained・リトライ修正 |
| **恵佑会札幌病院** | `fix_恵佑会*.py`（6ファイル） | 診療1(Stage1a-c) + 診療2/連携室(Stage1+PW+プロンプト) |
| **佐賀大学** | `fix_saga_stage1.py` | CRITICAL/WARNING一括修正 |
| **関越病院** | `fix_kanekoshi.py` + `enhance_prompts_kanetssu.py` | フロー+Property修正・プロンプト強化 |
| **貝塚病院** | `fix_kaizuka2_all.py` | フィードバック対応（文言修正） |
| **PW生成** | `gen_pw_ushiku.py`, `gen_pw_chiiki.py`, `pw_generate_maruyama.py`, `pw_apply_okinawa.py` | 牛久愛和・沖縄地域連携・渓仁会円山・沖縄診療の辞書生成 |
| **PW更新** | `update_pw_yokosuka.py`, `fix_yokosuka_pw.py` | 横須賀共済の辞書生成・品質改善 |
| **プロンプト強化** | `enhance_yokosuka_prompts.py`, `fix_恵佑会_renkei_prompts.py` | 7セクション構造への書き換え |

> **注**: Stage 2以降、`@pw-generator` / `@prompt-enhancer` エージェント使用が必須となったため、新規施設ではアドホック `fix_*.py` での辞書ハードコードは禁止。

---

## 7. エージェント構成

| エージェント | モデル | 役割 |
|---|---|---|
| `diff-analyzer` | Opus | VFB生成物 vs 人間修正の差分分析・パターン抽出 |
| `fixer` | Sonnet | チェック結果に基づく自動修正 + デフォルト値補完 |
| `orchestrator` | Opus | パイプライン制御 |
| `finisher` | — | 仕上げ屋（Stage 0-8の統合実行） |
| `@pw-generator` | — | AmiVoice辞書(profile_words)の教師データ水準生成 |
| `@prompt-enhancer` | — | OpenAIプロンプトの7セクション標準化・施設固有情報保持確認 |

---

## 8. 主要ルール・仕様ファイル

| ファイル | 内容 |
|---|---|
| `CLAUDE.md` | 全ルール集（フローJSON仕様・Property.md・モジュール別設定・品質基準） |
| `PIPELINE_SPEC.md` | パイプライン仕様書（Stage別の実行コマンド・品質ゲート・チェック定義） |
| `reference/defaults.json` | AmiVoice・DTMF・コンテキスト等のデフォルト値カタログ |
| `reference/defaults_overrides/learned_patterns.json` | VFBの頻出エラーパターン蓄積 |
| `reference/prompts/prompt_templates.json` | OpenAIプロンプトテンプレート（5スキル分類） |
| `reference/dictionaries/profile_words_*.txt` | AmiVoice辞書テンプレート（氏名・生年月日・肯定否定） |
| `reference/subflows/` | サブフローテンプレート（氏名聴取・生年月日聴取・電話番号聴取等） |
| `training_data/cross_analysis.md` | 教師データ横断分析結果 |
