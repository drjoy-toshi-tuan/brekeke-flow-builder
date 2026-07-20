# bivr-checker プロジェクト設計書

## 1. プロジェクト概要

### 目的
VoiceBot Flow Builder (VFB) が生成する `.bivr` ファイルと `Property.md` の品質を、人間が作成したものと同等以上に引き上げる。

### 2つの目的
1. **VFBの生成品質を上げる**（根本改善）— VFB生成物 vs 人間修正の差分分析・パターン蓄積 → VFBへフィードバック
2. **生成されたものを修正する**（即時対応）— 外部チェック結果に基づく自動修正

### ワークフロー
```
1. VFBで .bivr + Property.md を生成（VoiceBot Flow Builder）
2. Claude.aiのチェックプロンプトで品質チェック（外部）
3. 本プロジェクトで修正＆蓄積（bivr-checker）
```

### 品質向上の3要素
1. **精度向上の定義**: チェックルール + デフォルト値の定義
2. **パターンの蓄積**: VFBが何を間違えるかの頻出パターン
3. **教師データの蓄積**: VFB生成物 vs 人間修正の突合ペア

### VoiceBot Flow Builderとの関係
- **独立プロジェクト** — 将来的にVFBに統合予定
- 本プロジェクトの蓄積データがVFBの生成ルールを改善する

---

## 2. ディレクトリ構成

```
bivr-checker/
├── CLAUDE.md                              # 全エージェント共通ルール
├── PROJECT_DESIGN.md                      # 本ドキュメント
├── PROGRESS_LOG.md                        # 進捗ログ
│
├── .claude/
│   ├── settings.json
│   └── agents/
│       ├── diff-analyzer.md               # VFB vs 人間の差分分析（Opus）
│       ├── fixer.md                       # 自動修正（Sonnet）
│       └── orchestrator.md                # パイプライン制御（Opus）
│
├── training_data/                         # 教師データ
│   ├── cross_analysis.md                  # 9ペア横断分析
│   ├── vfb_reference_summary.md
│   ├── brekeke_official_docs.md
│   ├── pair_01/ ... pair_20/             # 人間作成の正解データ
│   └── feedback/
│       └── corrections/                   # 突合ペア＋修正ログ【品質向上の核】
│           └── {施設名}/
│               ├── draft_*.json           # VFB生成版
│               ├── final_*.json           # 人間修正版
│               ├── diff_report.md         # 差分分析レポート
│               ├── fix_log.json           # 修正ログ
│               └── notes.md
│
├── reference/
│   ├── check_prompt.md                    # Claude.aiチェックプロンプト（参照資料）
│   ├── defaults.json                      # 全施設共通デフォルト値
│   ├── defaults_overrides/
│   │   └── learned_patterns.json          # VFB頻出エラーパターン（蓄積）
│   ├── templates/
│   ├── subflows/
│   ├── prompts/
│   ├── dictionaries/
│   ├── env/
│   └── context/
│
├── schemas/
│   ├── intermediate_format.json           # 参照用
│   ├── check_report_schema.json
│   └── fix_log_schema.json
│
├── scripts/
│   ├── build_bivr.py
│   ├── extract_bivr.py
│   └── validator.py
│
├── input/                                 # 修正対象を施設名別に配置
│   └── {施設名}/
│       ├── *.bivr                         # VFB出力
│       ├── *_Property.md                  # VFB出力
│       ├── check_result.md                # 外部チェック結果
│       └── *.pdf                          # 元PDF（参照用、任意）
│
└── output/
    └── {施設名}/
        ├── extracted/flows/               # .bivrから展開
        ├── fixed/flows/                   # 修正済み
        ├── fixed/*_Property.md
        ├── reports/
        └── {施設名}_fixed.bivr            # 最終出力
```

---

## 3. エージェント定義

### 3.1 diff-analyzer（差分分析）
- **モデル**: Opus
- **入力**: VFB生成版 + 人間修正版の突合ペア
- **出力**: diff_report.md + learned_patterns.json更新
- **役割**: VFBが何を間違えるかのパターン抽出 → VFBフィードバック

### 3.2 fixer（自動修正）
- **モデル**: Sonnet
- **入力**: VFB出力 + 外部チェック結果
- **参照**: check_prompt.md（エラーコード定義）、defaults.json、learned_patterns.json、過去corrections
- **出力**: 修正済みフローJSON + Property.md + fix_log.json
- **役割**: チェック結果に基づく自動修正 + デフォルト値補完

### 3.3 orchestrator（パイプライン制御）
- **モデル**: Opus
- **役割**: 修正パイプラインと差分分析パイプラインの制御

---

## 4. パイプライン

### 修正パイプライン（メイン）
```
入力: VFB出力 + check_result.md → EXTRACT → FIX → BUILD → ACCUMULATE → REPORT
```

### 差分分析パイプライン（品質向上用）
```
入力: VFB生成版 + 人間修正版 → DIFF ANALYSIS → パターン抽出 → learned_patterns更新
```

---

## 5. 実装ロードマップ

### Phase 0: 基盤整理 ✅
- プロジェクト方向転換、エージェント・設計書改訂

### Phase 1: 差分分析ツール（★現在）
- 突合ペアデータの受け入れ体制構築
- diff-analyzer による差分分析
- ベースライン品質スコアの算出

### Phase 2: fixer + 修正パイプライン
- 外部チェック結果を入力とした自動修正
- fix_log.json の出力・蓄積

### Phase 3: パターン蓄積 + VFBフィードバック
- 複数施設の差分分析でパターン集約
- learned_patterns.json の充実
- VFBの生成ルール改善提案

### Phase 4: VFB統合準備
- 蓄積データのVFB統合用整理
