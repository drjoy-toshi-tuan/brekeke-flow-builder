# bivr-checker 進捗ログ

## 最終更新: 2026-04-15 (帝京溝口 差分分析・定義ブラッシュアップ完了)

---

## 帝京大学付属溝口病院 差分分析・定義ブラッシュアップ（2026-04-15）

### 格納フォルダ
`training_data/feedback/corrections/帝京大学付属溝口病院/`
- `vfb/` → VFB生成物
- `human/` → 人間修正済み（正解）
- `bivr_checker/` → bivr-checker修正済み（fixed_v5）
- `diff/analysis_report.md` → 差分分析レポート

### 主な発見（13パターン / TEIKYO-001〜013）

| 分類 | 内容 |
|---|---|
| 最重大（bivr_checker） | サブフローを1フロー（228モジュール）に統合してしまっている。Human（正解）は6フロー構成を維持 |
| 未修正 | OpenAI_担当医のcontextName="Mydoctor"→"inquiry"、完了フラグ_診察券なしstatus="0"→"2" |
| 誤修正 | リトライ_時間指定のfalse遷移先を"検査内容_聴取"に誤変更（正解: "診察日のみ変更_アナウンス"） |
| 未修正 | RAG検索フロー未生成、生年月日辞書1語のみ、紹介状後の当院宛確認未追加 |
| 正解一致 | 入力_用件確認profile_words43語、はい/いいえDTMF化 |

### 定義更新内容

**learned_patterns.json**: VFB-023〜027を追加
- VFB-023: はい/いいえ二択のDTMF化
- VFB-024: 担当医contextName非標準名
- VFB-025: 完了フラグ_診察券なしstatus誤り
- VFB-026: サブフローstart誤り・複合フロー
- VFB-027: 氏名サブフローのOpenAI正規化不要

**CLAUDE.md Section 4（フロー設計基本原則）**: 原則18〜22を追加
- 18: はい/いいえはDTMF必須
- 19: サブフローstartはフロー最初のTTSと一致
- 20: 担当医はcontextName="inquiry"
- 21: 診察券なし完了フラグはstatus="2"
- 22: 氏名サブフローにOpenAI不要

---

## pair_10 ユアクリニックお茶の水 analysis.md 作成（2026-04-15）

### 概要
- フロー数: 3（診療-Demo / 氏名 / 電話番号）
- シナリオ: 問い合わせ内容・氏名・電話番号の3聴取のみ（シンプル設計）
- 特徴: Script主導の曜日/時間帯判定・SSML電話番号読み上げ・acceptance_times非使用

### 主な設計パターン（他pairと異なる点）
1. `acceptance_times` 未使用。Script + 外部祝日APIで完全独自実装
2. 平日/土曜/祝日/日曜で細粒度の「AI受付/代表転送/時間外」3パターン制御
3. script_ssmlで電話番号SSML生成（携帯/固定の桁数自動判定・読み上げ速度制御）
4. 肯定否定辞書（600行超）が本プロジェクト最高水準

### 出力ファイル
- analysis.md: `training_data/pair_10/analysis.md`

---

## 帝京大学附属溝口病院 v5 完了（2026-04-14）

### ベース
ユーザー手修正版 `input/帝京大学付属溝口病院/帝京溝口病院_診療_user.bivr` (228モジュール、フロー名 `帝京溝口$診療_20260413_3`)

### ユーザー手修正内容（フィードバック記録）
1. **コンテキスト保存設定**: 各OpenAIモジュールの `contextName` を `inquiry` から個別名に変更
   - SameAsLastTime, Previousvisits, Mydoctor, Scheduledtime, Testditail, Injection, Referral, Test22
   - `コンテキスト設定` fieldsにこれら全て追加
2. **分岐1モジュール追加（ContextMatchRouter）**: `OpenAI_本日予約確認` の ^.+$ 先を `分岐1` に変更
   - 分岐1: OpenAI_診察券確認の出力「初めて」かどうかで Jump_氏名聴取 / Jump_診察券番号聴取 に分岐
   - OpenAI_診察券確認 ^初めて$: Jump_氏名聴取 → 本日予約確認（ループ修正）
3. **リトライ prompt_false 追加**: リトライ_診療科_初診 に prompt_false テキスト設定
4. **完了フラグ_キャンセル smsFlag**: 1 → 2 に変更
5. **OpenAI_用件確認 ^.+$ の接続変更**: 受診歴確認 → 問合せ内容_聴取

### v5 追加修正（分岐漏れ2箇所）
1. **Fix A: OpenAI_前回と同じ確認**
   - `^はい$ → 担当医_聴取_再診` を catch-all の前に挿入
   - 修正前: `^.+$ → 診療科_聴取_再診`（担当医聴取に進む分岐が欠落）
   - 修正後: `^はい$ → 担当医_聴取_再診`, `^.+$ → 診療科_聴取_再診`

2. **Fix B: OpenAI_紹介状確認**
   - `^はい$ → 診療科_聴取_初診`, `^いいえ$ → 診療科_聴取_初診` を明示追加
   - 修正前: `^.+$ → 診療科_聴取_初診`（catch-allのみ、意図が不明確）
   - 修正後: はい/いいえ明示 + `^.+$ → 診療科_聴取_初診`（フォールバック）

### 出力ファイル
- JSON: `output/帝京大学付属溝口病院/fixed_v5/flows/帝京溝口_v5.json`
- .bivr: `output/帝京大学付属溝口病院/帝京大学附属溝口病院_fixed_v5.bivr` (32,267 bytes)
- スクリプト: `scripts/fix_teikyo_mizoguchi_v5.py`

---

## 帝京大学附属溝口病院 v4 完了（2026-04-14）

### 修正内容
1. **DTMFモジュール profile_words 設定（11箇所）**
   - 全DTMFモジュールが空文字だったため各聴取内容に応じた辞書を設定
   - 用件確認（予約/変更/キャンセル/確認/問合せ＋数字1-5）
   - 診察券確認・本日予約確認・受診歴確認・前回と同じ確認・紹介状確認 → はい/いいえ系（頭落ちパターン含む）
   - 注射装具確認（変更・キャンセル両方）→ はい/いいえ＋注射・装具関連語
   - 検査有無 → はい/いいえ＋CT/MRI等検査語
   - 術前検査・時間指定 → はい/いいえ系

2. **予約希望日の当日/翌日/明後日 → 代表電話案内分岐**
   - `OpenAI_予約希望日` と `OpenAI_予約希望日_変更` の両方に対応
   - 当日・本日・今日・翌日・明日・明後日・あさって → 出力「要代表案内」
   - 「要代表案内」 → `完了フラグ_代表案内_本日` → `代表電話_アナウンス` → 終話

3. **変更/キャンセルルート順序変更（診療科 → 注射装具確認 の順）**
   - 旧: 用件確認 → 注射装具確認 →（いいえ）→ 診療科 → 検査有無
   - 新: 用件確認 → 診療科 → 注射装具確認 →（いいえ）→ 検査有無（変更）/ 予約日（キャンセル）
   - 変更箇所: OpenAI_用件確認/OpenAI_診療科_変更/OpenAI_注射装具_変更/OpenAI_診療科_キャンセル/OpenAI_注射装具_キャンセル の next接続

4. **レイアウト改善（用件確認からの距離圧縮）**
   - y >= 7000 の全モジュール（180件）を -4700 シフト
   - 受診歴確認（予約ルート入口）: y=7721 → y=3021（用件確認y=2470から551）
   - 診療科_聴取_変更/キャンセル（各ルート新入口）: y=8751 → y=4051
   - 注射装具確認（変更/キャンセル 新2nd step）: y=5000 に再配置
   - 検査有無確認/予約日_聴取_キャンセル（新3rd step）: y=5600 に再配置

### 出力ファイル
- JSON: `output/帝京大学付属溝口病院/fixed/flows/帝京溝口$診療_20260413.json`
- .bivr: `output/帝京大学付属溝口病院/帝京大学附属溝口病院_fixed.bivr`
- スクリプト: `scripts/fix_teikyo_mizoguchi_v4.py`

---

## 完了済み作業

### 1. フォルダ構成作成
- `bivr-checker/training_data/pair_01〜pair_20` を作成済み

### 2. 教師データ投入（10ペア）
全ペアに PDF + .bivr + Property.md の3点セットが格納済み。

| pair | 施設名 | シナリオ種別 |
|---|---|---|
| pair_01 | 帯広第一病院 | 健診 |
| pair_02 | 入間ハート病院 | 診療（12サブフロー、最複雑） |
| pair_03 | 長野県立木曽病院 | 診療（耳鼻科特別ルート） |
| pair_04 | ガーデンシティ健診プラザ | 健診 |
| pair_05 | JAとりで総合医療センター | 診療（新規/再診分岐、選定療養費） |
| pair_06 | 四谷メディカルキューブ | 診療（最小・最シンプル） |
| pair_07 | 兵庫県立こども病院 | 診療（小児科、検診後受診） |
| pair_08 | 東京衛生アドベンチスト病院 | 診療（第二世代移管、時間帯分岐） |
| pair_09 | いまきいれ総合病院 | 診療（当日確認、ContextMatchRouter多用） |
| pair_10 | ユアクリニックお茶の水 | 診療（問い合わせ受付特化、Script時間帯判定、SSML電話番号読み上げ） |

### 3. 個別分析（10件全完了）
各 `pair_XX/analysis.md` に以下を記録:
- PDF内容サマリー
- .bivr構造（全フロー、全モジュール、全接続）
- Property.md内容
- PDF → .bivr/Property のマッピング
- ギャップ分析（PDFにない情報の特定）

### 4. リファレンス収集（2件完了）
- `training_data/vfb_reference_summary.md` — VoiceBot Flow Builder全リファレンス要約（28KB）
  - 全23モジュールタイプの仕様
  - validator.pyの全エラーコード
  - 命名規則、レイアウト規則、環境設定テンプレート
- `training_data/brekeke_official_docs.md` — Brekeke公式ドキュメント要約（18KB）

### 5. 横断分析（完了）
- `training_data/cross_analysis.md` に出力済み
- 7セクション構成:
  1. シナリオ種別分類（診療7件 / 健診2件）
  2. 共通フローパターン（冒頭チェーン、個人情報サブフロー、終話チェーン等）
  3. PDF → bivr 変換ルール（9カテゴリ）
  4. デフォルト値一覧（AmiVoice設定、API URL、リトライ等）
  5. Property.mdパターン分析
  6. バリエーション・エッジケース
  7. 自動化可能性評価（40%確定/35%テンプレート/15%LLM/10%人間）

### 6. プロジェクト設計書（完了）
- `PROJECT_DESIGN.md` に出力済み
- 内容:
  - ディレクトリ構成（全フォルダ・ファイル定義）
  - CLAUDE.md構成概要（10セクション）
  - エージェント定義6種（parser/generator/fixer/reviewer/validator/orchestrator）
  - パイプラインフロー（9ステップ、リトライ・エスカレーション含む）
  - デフォルト値カタログ
  - 実装ロードマップ（4フェーズ）

---

## Phase 1 実装完了（2026-04-08）

### 完了した作業

1. **プロジェクト基盤構築** ✅
   - `reference/`, `schemas/`, `scripts/`, `input/`, `output/` フォルダ作成
   - `.claude/agents/` フォルダ作成
   - `.claude/settings.json` 作成

2. **CLAUDE.md 作成** ✅
   - VFBのCLAUDE.mdから全Brekeke IVRルールをポート（10セクション構成）
   - 中間フォーマット仕様、Property.mdルール、デフォルト値カタログ追加
   - バリデーターエラーコード（VFB 71項目 + bivr-checker固有 6項目）
   - パイプライン工程（9ステップ）

3. **リファレンスデータ整備** ✅
   - `reference/defaults.json` — 全デフォルト値カタログ
   - `reference/templates/module_templates.json` — 全18モジュールタイプテンプレート
   - `reference/templates/start_chain.json` — 冒頭チェーンテンプレート
   - `reference/templates/end_chain.json` — 終話チェーンテンプレート
   - `reference/templates/conversation_step.json` — 会話ステップテンプレート
   - `reference/templates/reconfirmation.json` — 復唱確認テンプレート
   - `reference/templates/non_notification.json` — 非通知拒否テンプレート
   - `reference/context/context_fields_{common,medical,checkup}.json` — コンテキスト定義
   - `reference/prompts/openai_yes_no.txt` — 肯定否定プロンプト
   - `reference/prompts/openai_hearing_impossible.txt` — 聴取不可プロンプト
   - `reference/dictionaries/profile_words_{yes_no,dob,name}.txt` — 辞書テンプレート
   - `reference/env/env_{demo,prod}.txt` — 環境設定テンプレート（VFBからコピー）

4. **スクリプト準備** ✅
   - `scripts/build_bivr.py` — VFBからコピー
   - `scripts/extract_bivr.py` — VFBからコピー
   - `schemas/intermediate_format.json` — 中間JSONスキーマ（全フィールド定義済み）
   - `scripts/validator.py` — VFBから全チェック関数ポート + PROP-001〜004, CROSS-001〜002追加 + --json/--subflowsオプション

5. **エージェント定義作成** ✅
   - `.claude/agents/parser.md` — PDF→中間JSON（Opus）
   - `.claude/agents/generator.md` — 中間JSON→フローJSON+Property.md（Sonnet）
   - `.claude/agents/orchestrator.md` — パイプライン制御（Opus）

---

## Phase 0: プロジェクト方向転換＆基盤整理（2026-04-09）✅

### 方向転換の内容
- **旧**: PDF → ゼロから .bivr を生成する「ジェネレーター」
- **新**: VFB出力の .bivr + Property.md をチェック＆修正する「チェッカー」

### 完了した作業

1. **不要エージェント削除** ✅
   - `.claude/agents/parser.md` 削除（PDF→中間JSON生成は不要）
   - `.claude/agents/generator.md` 削除（新規生成は不要）

2. **新エージェント定義作成** ✅
   - `.claude/agents/checker.md` — VFB出力の品質チェック（Opus, 5観点）
   - `.claude/agents/fixer.md` — 自動修正 + デフォルト値補完（Sonnet）
   - `.claude/agents/reviewer.md` — 業務ロジックレビュー（Opus, 6観点）
   - `.claude/agents/orchestrator.md` — チェック＆修正パイプライン制御（Opus, 全面改訂）

3. **CLAUDE.md 改訂** ✅
   - セクション2: プロジェクト概要を「チェック＆修正」に書き換え
   - セクション10: パイプライン工程を EXTRACT→VALIDATE→CHECK→FIX→REVIEW→BUILD→FEEDBACK に変更
   - ファイル構成: 新エージェント、feedback/corrections、defaults_overrides を反映

4. **PROJECT_DESIGN.md 全面改訂** ✅
   - ディレクトリ構成、エージェント定義、パイプラインフロー、品質向上の仕組み、ロードマップを再設計

5. **新規ファイル作成** ✅
   - `schemas/check_report_schema.json` — チェックレポート形式定義
   - `schemas/fix_log_schema.json` — 修正ログ形式定義
   - `reference/defaults_overrides/learned_patterns.json` — VFB頻出エラーパターン（空初期化）
   - `training_data/feedback/corrections/` フォルダ作成

---

## プロジェクト再定義（2026-04-09 追加）

### 方向性の明確化
- **bivr-checkerの本質**: チェックは外部（Claude.aiプロンプト）で実施。本プロジェクトは「修正」と「蓄積」に特化
- **ワークフロー**: VFB生成 → Claude.aiでチェック → 本プロジェクトで修正＆蓄積

### エージェント構成（最終）
- diff-analyzer（Opus）: VFB vs 人間の差分分析
- fixer（Sonnet）: 外部チェック結果に基づく自動修正
- orchestrator（Opus）: パイプライン制御
- ~~checker~~ → 削除（外部プロンプトが担当）
- ~~reviewer~~ → 削除（外部プロンプトが担当）

### 追加ファイル
- `reference/check_prompt.md` — Claude.aiチェックプロンプト（参照資料として格納）

---

## Phase 1: 初回差分分析 完了（2026-04-09）

### 帯広第一病院の差分分析
- VFB生成版 vs 人間修正版の突合ペアを受領・展開
- diff_report.md を生成（構造的一致率 約40%）
- learned_patterns.json に10パターン登録（VFB-001〜010）

### 主要な発見
- ContextMatchRouter未生成（最大の欠落）
- 復唱ノード未生成
- save2db過剰（50→9に削減可能）
- Disconnect/CompletionFlag過剰
- 数字入力にDTMF未使用
- office_id未設定

---

## Phase 1 継続: 長野県立木曽病院 差分分析完了（2026-04-10）

### 実施内容
- `training_data/feedback/corrections/長野県立木曽病院/` にデータ格納・展開
- diff_report.md 生成（構造的一致率 約30%）
- learned_patterns.json 更新（VFB-001〜010のfrequency更新 + VFB-011〜013 新規追加）

### 主要な発見（帯広との差分）
- **VFB-011 NEW**: サブフロー4本が完全未生成（Jump参照のみ）→ 実動作不可
- **VFB-012 NEW**: Jump to Flow の flowname が正規形式でない
- **VFB-013 NEW**: サブフロープロンプトをProperty.mdに直書き（本来はJump properties経由）
- **VFB-001〜006, 009, 010**: 帯広と同様に確認 → frequency=2 に更新
- **VFB-007（Retry save2db未接続）**: 長野では接続済み → frequency=1 維持（案件依存の可能性）
- **VFB-008（office_id未設定）**: 長野では設定済み → frequency=1 維持

### 現在の蓄積状況
- 分析済み施設: 2（帯広第一病院・長野県立木曽病院）
- 登録パターン: 13種（VFB-001〜013）
- frequency=2（全施設で確認）: VFB-001, 002, 003, 004, 005, 006, 009, 010

---

## Phase 1 継続: ユアクリニックお茶の水 差分分析完了（2026-04-10）

### 実施内容
- `training_data/feedback/corrections/ユアクリニックお茶の水/` にデータ格納・展開
- diff_report.md 生成（構造的一致率 約45%）
- learned_patterns.json 更新（VFB-001〜010 frequency=3へ + VFB-014, 015 新規追加）

### 主要な発見（新規パターン）
- **VFB-014 NEW**: 冒頭チェーンで incoming-classifier が冒頭TTS より前（帯広でも確認、frequency=2）
- **VFB-015 NEW**: 業務ロジックScript（時刻判定・SMS・電話番号変換）を生成しない

### 現在の蓄積状況
- 分析済み施設: 3（帯広第一病院・長野県立木曽病院・ユアクリニックお茶の水）
- 登録パターン: 15種（VFB-001〜015）
- **frequency=3（全施設で確認 = VFBの体質的問題確定）**:
  VFB-001, 002, 003, 004, 005, 006, 009, 010
- frequency=2: VFB-011, 012, 014
- frequency=1: VFB-007, 008, 013, 015

---

## 入間ハート病院 診療フロー フルリビルド完了（2026-04-10）

### 実施内容
- VFB生成 `.bivr`（106モジュール、1フラットフロー）を完全再構築
- `scripts/build_iruma_heart.py` で5フロー（83モジュール + 4サブフロー）を新規生成
- バリデーション: 0 CRITICAL、6 WARNING（全て設計上許容）

### 主な修正内容（VFB vs 固定版）

| VFB問題 | 対応 |
|---|---|
| フラット1フロー（サブフロー未生成） | 5フロー構成に再設計（診療・氏名・生年月日・電話番号・RAG） |
| 復唱確認ノード未使用 | 用件・種別・電話番号(固定)の3箇所に復唱確認を追加 |
| ContextMatchRouter多用 | Scriptモジュールによる分岐に置き換え（CLAUDE.md準拠） |
| 終話パスの抜け | 4終話パス（予約/変更確認/キャンセル/失敗）を完備 |
| incoming-classifier 位置不正 | 冒頭チェーン内で正しく配置 |
| status=0 禁止値使用（COMP-001） | status=1 に修正 |
| PROMPT-001: next条件とプロンプト不一致 | 全OpenAIプロンプト出力仕様を `- ラベル` 単独行に統一 |
| PROMPT-002: フリーワード未対応条件 | 出力仕様から削除、NO_RESULT説明に吸収 |

### 追加修正（2026-04-10 v2）

| 問題 | 原因 | 修正内容 |
|---|---|---|
| Re-confirmation node data が動作しない | type を `Custom$Re-confirmation node data` と誤記 | `drjoy^Text To Speech$Re-confirmation node data` に修正 |
| LAYOUT-003 横並び警告 | 全モジュールがx方向(左→右)に並んでいた | y軸方向（上→下）に再設計。y_range=9420px > 8300px(=83×100) |

### 追加修正（2026-04-10 v3）— フロー動作ロジック全面修正

| 問題 | 修正内容 |
|---|---|
| 時間外アナウンスが終話していた | `false` 側: `冒頭_アナウンス_時間外` TTS → `用件_アナウンス` へ続くように変更。`saveCompletionFlag2db_時間外`・`切断_時間外` を削除 |
| リトライ上限失敗が全て終話していた | 分岐必要（用件・種別）→ 無限ループ（先頭TTS）、分岐不要（診療科・症状・希望日等）→ 次ステップへ進む |
| 分岐にScriptモジュールを使っていた | 全分岐を `drjoy^Context Logic$ContextMatchRouter` に変更。条件は `^1$`, `^2$`, `^3$` のインデックスベース |
| 確認分岐がフリーワードOpenAIだった | `移動_確認RAG` (Jump to Flow → RAGサブフロー) に変更。props: `問合せ_問合せ.prompt={tts_g:確認内容を簡潔にお話しください。}` |
| 終話前にRAG検索があった | `移動_RAG検索` モジュールを削除。`script_終話種別判定` → 直接 `終話分岐` に接続 |

- バリデーション結果: 0 CRITICAL、5 WARNING（PASS）、モジュール数: 70

### 学習データ更新
- `bivr-checker/CLAUDE.md` モジュールタイプ表: Re-confirmation の正しいカテゴリを修正
- `bivr-checker/CLAUDE.md` モジュールタイプ表: `Custom$ContextMatchRouter` → `drjoy^Context Logic$ContextMatchRouter`（カテゴリ・条件形式を明記）
- `bivr-checker/CLAUDE.md` セクション7b: レイアウト座標ルール追加（voicebot-flow-builder/docs/specs/layout_spec.md より）
- memory: `feedback_iruma_heart_round2.md` — 4ルール（時間外・リトライ・CMR・確認RAG）を保存

### 修正ペア保存先
- `training_data/feedback/corrections/入間ハート病院/入間ハート病院_診療_20260409_vfb.bivr`（VFB生成版）
- `training_data/feedback/corrections/入間ハート病院/入間ハート病院_診療_20260409_fixed.bivr`（修正版 v3）

---

## Phase 1 継続: 入間ハート病院 3バージョン差分分析完了（2026-04-13）

### 実施内容
- 3バージョン（VFB生成 / bivr-checker修正済み / 人間完成版）の突合ペアを受領
- `training_data/feedback/corrections/入間ハート病院/入間ハート病院_診療_20260409_human.bivr` 格納
- `scripts/analyze_iruma_diff.py` で4項目（profile_words / saveContextModel2DB / saveContext2DB / OpenAIプロンプト）の差分を自動抽出
- `diff_report_v2.md` 生成（fixed vs human の差分）
- `learned_patterns.json` 更新（VFB-016〜020 新規追加、施設数4に更新）

### 主要な発見（fixed vs human の残差）

| 項目 | 発見内容 |
|---|---|
| **VFB-016 NEW** | STTのprofile_wordsを全モジュール空欄のまま生成（frequency=4 → VFBの体質的問題確定）|
| **VFB-017 NEW** | saveContextModel2DBのfieldsが汎用設定（施設固有のrangeValues・追加フィールド欠落）|
| **VFB-018 NEW** | OpenAIプロンプトが簡素すぎる（DTMF即決/STT頭落ち/Few-Shot/施設固有リスト欠落）|
| **VFB-019 NEW** | 生年月日サブフローにOpenAI正規化モジュールが未生成（moduleが空欄→OAI-001 CRITICAL）|
| **VFB-020 NEW** | 復唱否定応答時の専用TTS未生成（否定時のUX劣化）|
| saveContext2DB | 差分なし（bivr-checkerで完全対応済み）|

### profile_wordsの設計レベル（人間版）
- 入力_用件: 予約/変更/キャンセル各カテゴリ×フィラーパターン×頭落ちパターン = 数百語
- 入力_復唱: はい系200語超・いいえ系200語超（頭落ち: は→a, ちが, がい, い等）
- 入力_希望日: 月日特殊読み・曜日・相対表現
- 入力_診療科: 施設全14科+略称
- 入力_検査種別: 施設固有の検査名+一般名（胃カメラ→内視鏡等）

### OpenAIプロンプトの設計レベル（人間版）
- 生年月日: DTMF8桁優先/西暦/和暦誤認識対応(社長は→昭和等)/STT頭落ち補完/バリデーション/Few-Shot
- 復唱確認: DTMF即決(1→肯定/2→否定)/STT断片処理/Few-Shot
- 診療科: 全診療科リスト+症状のみ→NO_RESULT(トリアージ禁止)+略称マッピング
- 検査種別: 施設固有リスト+一般名→専門語名寄せ（胃カメラ→内視鏡等）

### 現在の蓄積状況
- 分析済み施設: 4（帯広第一病院・長野県立木曽病院・ユアクリニックお茶の水・入間ハート病院）
- 登録パターン: 20種（VFB-001〜020）
- **frequency=4（全施設で確認 = VFBの体質的問題確定）**: VFB-016（profile_words空欄）
- **frequency=3**: VFB-001, 002, 003, 004, 005, 006, 009, 010
- frequency=2: VFB-011, 012, 014
- frequency=1: VFB-007, 008, 013, 015, 017, 018, 019, 020

---

## 全ペア横断分析 + CLAUDE.md 再定義（2026-04-13）

### 実施内容
- pair_01〜10 全ペアの analysis.md とbivr実ファイルを横断分析
- 人間版との差異になり得る「未定義箇所」5項目を特定・再定義

### 未定義箇所として特定・追記した項目

| # | 未定義箇所 | 対応箇所 |
|---|-----------|---------|
| 1 | **Retry prompt_false の3パターン体系** | CLAUDE.md Section 4 更新 + VFB-021 追加 |
| 2 | **profile_words フィラーパターン体系（標準14種）** | CLAUDE.md Section 9 追記 + VFB-022 追加 |
| 3 | **復唱STTの頭落ちパターン（はあ/あい/おうです等）** | CLAUDE.md Section 9 復唱確認辞書を拡充 |
| 4 | **健診コースのprofile_words入力種別ガイドライン** | CLAUDE.md Section 9 に項目9追加 |
| 5 | **リトライ回数の施設依存ルール（2回 or 3回）** | CLAUDE.md フロー設計原則3を更新 |

### 主な発見（ペア別）

| ペア | 施設 | 主な発見 |
|---|---|---|
| pair_01 | 帯広第一病院（健診） | profile_wordsにフィラー14種×語尾20種の体系。prompt_falseに2パターンの文言設定 |
| pair_04 | ガーデンシティ健診プラザ | 「失敗時は次へ進む」が設計書に明記。SMS告知型のprompt_false |
| pair_05 | JAとりで総合医療センター | openAI_聴取不可モジュールを各STT入力ごとに配置（11個） |
| pair_06 | 四谷メディカルキューブ | 診療科14科の類義語が詳細。個人情報を用件前に聴取する設計 |
| pair_07 | 兵庫県立こども病院 | 5用件・3フロー構成。検診後受診という特殊ルート |
| pair_08 | 東京衛生アドベンチスト | リトライ3回。「かしこまりました。折り返しの際に〜」のprompt_false |
| pair_09 | いまきいれ総合病院 | リトライ3回。ContextMatchRouterを最大活用（5箇所）。6フロー構成 |

### 更新ファイル
- `bivr-checker/CLAUDE.md` — Section 4（Retry prompt_false体系）、Section 9（フィラー体系・復唱頭落ち・健診コース・VFBが生成しない辞書表）、フロー設計原則3
- `reference/defaults_overrides/learned_patterns.json` — VFB-021（prompt_false空欄）、VFB-022（フィラー・頭落ちパターン欠如）追加、total 22パターンに

### 現在の蓄積状況
- 分析済みペア: 10（pair_01〜10）
- 登録パターン: 22種（VFB-001〜022）
- frequency=4（全施設確認）: VFB-016（profile_words空欄）、VFB-021（prompt_false空欄）、VFB-022（フィラー欠如）
- frequency=3: VFB-001, 002, 003, 004, 005, 006, 009, 010

---

## フェーズ方針（2026-04-10 確定）

### 進め方
1. **現フェーズ（bivr-checker）**: VFB生成物をbivr-checker内で修正し、修正ペアを蓄積
2. **繰り返し**: 修正精度が完璧に近づくまで教師データ・フィードバックデータを蓄積し続ける
3. **将来フェーズ（VFB側）**: 修正が安定した段階でVFBのCLAUDE.mdや生成ルールに反映

**VFBへのフィードバックは現時点では実施しない。**

### 次回やること
- VFB生成物の修正作業を開始する
- 暗黙ルール定義（implicit_rules_todo.md）を修正ルールとして活用する
- 修正前後のペアを `training_data/feedback/corrections/` に蓄積する

---

---

## CLAUDE.md 追記（2026-04-10）

### Section 9 AmiVoice辞書ルール 全面拡充

PCクラッシュ前に依頼されていた2点を適用:

1. **プロンプト網羅性ルール** — Section 8に「プロンプト網羅性ルール（最重要）」として既に記録済み（直前TTS発話から逆算・网羅的予測・設計手順・悪い例/良い例）

2. **profile_words 設計ルール** — Section 9を全面拡充
   - 原則1: 直前TTSから逆算して設計する（TTS連動・発話予測）
   - 原則2: 頭落ち（utterance先頭欠損）への対処（省略形・欠落パターン登録）
   - 原則3: モジュール種別ごとの方針（AmiVoice STT / DTMF / Re-confirmation）
   - 入力種別別ガイドライン（用件・氏名・生年月日・診療科・復唱・ワクチン・キャンセル理由・日程）
   - 教師データ（pair_01〜09）から実例辞書を抽出して掲載
   - 「VFBが生成しないため必ず手動で設定する辞書」一覧を追加

---

## 重要ファイルパス一覧

| ファイル | パス |
|---|---|
| プロジェクト設計書 | `bivr-checker/PROJECT_DESIGN.md` |
| 横断分析 | `bivr-checker/training_data/cross_analysis.md` |
| VFBリファレンス | `bivr-checker/training_data/vfb_reference_summary.md` |
| Brekeke公式 | `bivr-checker/training_data/brekeke_official_docs.md` |
| VFB CLAUDE.md | `voicebot-flow-builder/CLAUDE.md` |
| VFB validator.py | `voicebot-flow-builder/schemas/validator.py` |
| VFB build_bivr.py | `voicebot-flow-builder/scripts/build_bivr.py` |
| VFB extract_bivr.py | `voicebot-flow-builder/scripts/extract_bivr.py` |
| VFB orchestrator.py | `voicebot-flow-builder/scripts/orchestrator.py` |
| 個別分析 | `bivr-checker/training_data/pair_XX/analysis.md` (01〜09) |

---

## 再開時の指示例

次回Claude Codeを起動した際、以下のように指示してください:

```
bivr-checker プロジェクトの PROGRESS_LOG.md を読んで、Phase 1 の実装を開始してください。
```

---

## 帝京大学附属溝口病院 診療フロー 修正完了（2026-04-13）

### 実施内容

**v1（PROMPT-001 修正）**
- `scripts/fix_teikyo_mizoguchi_v1.py` 実行
- OpenAI_診療科_再診/初診/変更/キャンセル: グループラベル（精神科|心療内科 等）追加
- OpenAI_検査内容: (MRI|CT|内視鏡) 追加
- OpenAI_担当医_リハ/初診: prose bullet → clean label 修正
- 空 next スロット 244件削除

**v2（レイアウト・Property.md・Retry）**
- `scripts/fix_teikyo_mizoguchi_v2_layout.py` 実行
- LAYOUT-003 解消: y座標2.57倍スケール（8200→21105px）
- Property.md 作成: 42 TTS モジュール全プロンプト + API設定
- P-020 解消: wait/smsプレフィックス行を削除
- Retry prompt_false 26件設定（パターンA/B）

**v3（save2db・falseルーティング・レイアウト）**
- `scripts/fix_teikyo_mizoguchi_v3.py` 実行
- CRITICAL修正: Retry save2db 未接続 26件 → save-リトライ_xxx 新規作成＆接続
- リトライ_用件確認 false → 問合せ内容_聴取（その他問い合わせルートへ）
- 分岐ありリトライ6件（診察券確認/本日予約確認/診療科x4）→ 無限ループ設定
- ユーザー手修正版（帝京溝口病院_診療.bivr）のレイアウトを201モジュール全て適用

### 出力ファイル
- `output/帝京大学付属溝口病院/fixed/flows/帝京溝口$診療_20260413.json` (227モジュール)
- `output/帝京大学付属溝口病院/fixed/properties_帝京大学附属溝口病院_診療_demo.md`
- `output/帝京大学付属溝口病院/帝京大学附属溝口病院_fixed.bivr` (22,340 bytes)
- ユーザー手修正参照: `input/帝京大学付属溝口病院/帝京溝口病院_診療_user.bivr`

---

## 横浜労災病院 診療フロー v5 修正完了（2026-04-13）

### 実施内容（`scripts/fix_yokohama_rousai_v5.py`）

1. **DOB Re-confirmation**: `復唱_患者_生年月日` → `drjoy^TS Custom Module$DOB Re-confirmation`
   - openAI_prompt（元号変換・桁数補完・妥当性チェック）、saveDOB2db=Yes、dateReadingMode=自動
   - pair_08（東京衛生アドベンチスト）を正解例として参照
2. **Re-confirmation module param**: `復唱_患者_連絡先` に `module: "OpenAI_患者_連絡先"` 追加
3. **Script モジュール5件削除**:
   - script_グループ判定_予約/紹介なし → OpenAI_診療科がグループ名を直接出力（復唱_診療科 10モジュール削除）
   - script_携帯判別/smsFlag設定 → 削除、直接ルーティング
   - script_SMS判定 → `着信分類_SMS判定`（incoming-classifier）に置換（7箇所更新）
4. **AmiVoice STT timeout_ms 空欄化**: 13件
5. **DTMF timeout修正**: timeout_ms → timeout: "30000" に変更（9件）

### CLAUDE.md 更新内容
- DTMF: `timeout_ms`（AmiVoice）ではなく`timeout`（DTMF）が正しいパラメータ
- Re-confirmation node data に `module` パラメータ必須
- DOB Re-confirmation 専用ノードの仕様追記
- Script モジュール禁止・代替方法を追記

### 出力ファイル
- `output/横浜労災病院/fixed/flows/横浜労災$診療_20260403.json` (180モジュール)
- `output/横浜労災病院/横浜労災病院_fixed.bivr` (20,099 bytes)
