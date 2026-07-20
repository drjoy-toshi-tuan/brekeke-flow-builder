---
name: generate-manual-brief
description: voicebot-flow-builder 内部に蓄積された知識（モジュール選定ガイド / agent prompt / SKILL テンプレ / 実例シナリオ等）を読み合わせ、Brekeke Flow Designer + IVR Property の人間向けマニュアルを Claude Design (https://claude.ai/design) に投げる構造化ブリーフとして出力する。出力は単一の markdown ファイルで、コピー → Design に貼り付け → 視覚的に整ったマニュアルを生成、という連携を想定。
---

# /generate-manual-brief — Claude Design 向けブリーフ生成 skill

## 目的

人間が手作業で Brekeke Flow Designer + IVR Property を作成 / 修正するためのマニュアルを、claude.ai の **Claude Design**（リサーチプレビュー、独立 quota）に投げて視覚的に整ったクイックリファレンスとして仕上げる。本 skill はその「Design に渡す入力ブリーフ」を生成する役。

CLI Claude Code 側は重い読み込み・合成（VBFB 全体スキャン）を担当し、見た目の最適化は Claude Design に委ねる、というハイブリッド設計。

## 起動コンテキスト

- **どこで**: team-routines or voicebot-flow-builder のどちらでも可（参照は VBFB 配下）
- **誰が**: 浜口さん（社内マニュアル更新タイミング）
- **引数**: 任意。デフォルトは「VN メンバー含む読者、30-50p クイックリファレンス」
- **副作用**: 出力ファイル 1 つ書き出すのみ、自動 push しない（ブリーフは目視確認推奨）

## 想定読者層 / 仕上がり

- **読者**: TS チーム + VN メンバー
- **page 数想定**: 30-50p（クイックリファレンス）
- **テイスト**: 用語に英語並記、章末に「よくある失敗」、mermaid 図 + 表組み + 実例コード中心

## 読み込むソース（VBFB 配下）

```
[原則ソース]
1. docs/brekeke/モジュール選定ガイド_v2.md
2. docs/brekeke/モジュール詳細設定ガイド_1.md
3. docs/brekeke/brekeke_flow_reference.md (あれば)
4. docs/specs/設計書テンプレート.yaml
5. CLAUDE.md (システム構成・JSON 構造規則・next 配列規則ほか)

[エージェント挙動]
6. .claude/agents/director.md
7. .claude/agents/generator.md
8. .claude/agents/prompter.md
9. .claude/agents/reviewer.md
10. .claude/agents/fixer.md
11. .claude/agents/tester.md
12. .claude/agents/dirlite.md

[プロンプトテンプレ]
13. docs/ai/skills/SKILL_A_classification.md 〜 SKILL_E_freetext.md (5 種)
14. docs/ai/skills/SKILL_JSON_rules.md
15. docs/ai/skills/SKILL_quality_criteria.md

[ナレッジベース]
16. bivr-checker/KNOWLEDGE_BASE.md

[実例（2-3 施設選定）]
17. output/scenarios/{施設1}/properties_*.md + .bivr 抜粋
18. output/scenarios/{施設2}/properties_*.md + .bivr 抜粋
   (代表的 hearing パターン / RAG / 終話多段 等を含むものを選ぶ)
```

## 作業手順

### Step 1: Plan agent でアウトライン確定

`Plan` subagent に以下を依頼:
- 上記ソース群を踏まえ、30-50p クイックリファレンスの章立てを提案
- 各章の page 想定 + 含めるべき要素 + 関連 VBFB ソースを列挙
- VN メンバー対応のため、用語英語並記の方針を明示

出力: 章立て markdown（main session で受け取る）

参考雛形（Plan agent はこれを叩き台に最適化）:

```
1. はじめに — システム全体像 / 用語集 (3-4p)
2. フローデザイナー基本操作 — UI 操作 / モジュール追加 / 接続 (4-6p)
3. 9 ブロック型の使い方 — opening / announcement / hearing / subflow / context_match_router / script / date_of_call_classifier / call_transfer / termination (10-15p、章の大半)
4. IVR Property の書き方 — TTS 形式 / Phone2Name 動的差込 / 環境別差分 (4-6p)
5. よくあるパターン — echo_back hearing / RAG サブフロー / Pattern A/B 分岐 / 終話多段 (5-7p)
6. トラブルシューティング — 通話失敗 / STT 失敗 / OpenAI NO_RESULT 等 (3-5p)
7. 制約・禁止事項 — SSML 不可 / status=0 不可 / モジュール選定の落とし穴 等 (2-3p)
8. 付録 — モジュール type 早見表 / next/label 早見表 / 用語集 (3-4p)
```

### Step 2: 章別 sub-agent 並列実行（最大 6 本）

`general-purpose` subagent を 6 本並列起動、各章のコンテンツ・サマリと verbatim 引用を集める。各 subagent には:
- 読む対象（限定リスト）
- 担当章の page 数目安
- 期待する return 形式（後述）

を明示。

**Subagent 構成**:

| Subagent | 担当章 | 主な読み込み対象 |
|---|---|---|
| `chapter-overview` | 1. はじめに | CLAUDE.md システム構成、用語集（mermaid アーキ図仕様も生成） |
| `chapter-blocks` | 3. 9 ブロック型（最大セクション） | docs/brekeke/モジュール選定ガイド_v2.md, モジュール詳細設定ガイド_1.md, agent generator.md/prompter.md/fixer.md |
| `chapter-property` | 4. IVR Property | properties_*.md 実例 2-3 件、CLAUDE.md の TTS 形式記述、Phone2Name 仕様 |
| `chapter-patterns` | 5. パターン集 | SKILL_A〜E, scenario_flow 実例、RAG サブフロー仕様 |
| `chapter-troubleshoot` | 2/6/7 統合 | bivr-checker/KNOWLEDGE_BASE.md, agent.md 内の "禁止事項"、validator.py コード（落とし穴抽出） |
| `examples-collector` | 付録 + 全章に挿入する実例 | output/scenarios/ から代表 2-3 施設選定、`.bivr` JSON 抜粋（短く） |

各 subagent の **return 形式（固定）**:

```markdown
## 章 {N}: {タイトル}

### 概要 (1-2 段落)
{200-400 字}

### 含める要素
- 表組み: {内容}
- mermaid 図: {内容、図の素案も}
- コード例: {言語、内容}
- 注意ボックス: {落とし穴 1-2 件}

### verbatim 引用（Design が参照する原文抜粋）
- ソース: docs/brekeke/モジュール選定ガイド_v2.md §2.1
  > 「9 ブロック型のうち...」(verbatim 200-500 字)
- ソース: ...

### 各セクション
#### {N}.1 {小見出し}
- ポイント箇条書き
- 関連実例: `output/scenarios/A_診療/properties_A_診療.md` の 用件 hearing
```

### Step 3: Main session で統合

全 subagent の return を読み合わせ、以下構造の **brief markdown** を生成:

```markdown
# Brief for Claude Design — Brekeke Flow Designer + IVR Property マニュアル

## このブリーフの使い方

1. このファイル全体をコピー
2. https://claude.ai/design を開く
3. 新規チャットに貼り付け
4. 「このブリーフに従って、TS + VN メンバー向けクイックリファレンスマニュアル（30-50p）を設計してください」と指示

## 出力イメージ

- A4 換算 30-50 page クイックリファレンス
- TS + VN メンバー対応（日本語見出し、主要用語に英語並記）
- mermaid 図 + 表組み + コード例中心
- 章末に「よくある失敗」または「注意」コラム
- 検索しやすい階層見出し（目次自動生成）

## 全体デザイン指示

- 視覚: claude.ai docs ライクのクリーンレイアウト、左サイドバー TOC
- 色: 基本モノクロ、注意ボックスに薄色アクセント
- フォント: 本文 sans-serif、コード monospace
- 図: mermaid（フローチャート / sequenceDiagram）
- 印刷想定: A4 縦、page-break 適切位置

## 章立て（確定）

{Step 1 で Plan agent が出した章立てを転記}

## 各章の中身

{Step 2 の subagent return を統合}

### 章 1: はじめに
（subagent return をそのまま）

### 章 2: ...

## 用語集（VN 向け日英並記）

| 日本語 | English | 簡単な意味 |
|---|---|---|
| 用件 (yo-ken) | Intent / Purpose | 着信時に分類する 4-5 種類の話題 |
| 復唱 (echo_back) | Echo back | STT 結果を読み上げて確認するパターン |
| ... | ... | ... |

## 付録（Design 側で展開推奨）

### A. モジュール type 早見表
（subagent return 由来）

### B. next/label 早見表
（CLAUDE.md 由来、表組み）

### C. 関連 VBFB ファイル参照
- もっと詳しく見たい場合の対応ソースリスト
```

### Step 4: 出力

`voicebot-flow-builder/docs/manuals/brief_designer_manual_{YYYY-MM-DD}.md` に Write。

ファイル冒頭に以下メタ情報:

```markdown
---
routine: generate-manual-brief
date: YYYY-MM-DD
target: claude.ai Design (リサーチプレビュー)
audience: TS + VN メンバー
expected_output: 30-50p クイックリファレンス
source_revision: {VBFB git short hash}
---
```

### Step 5: チャット表示

ファイルパス + 使い方を表示:

```
📄 Brief 生成完了
  パス: voicebot-flow-builder/docs/manuals/brief_designer_manual_{YYYY-MM-DD}.md
  サイズ: {KB}

[Claude Design への投げ方]
1. cat output/manuals/brief_*.md | pbcopy (Mac) / clip (Windows)
2. https://claude.ai/design を開く
3. 新規セッションで貼り付け
4. 出力をエクスポートして Drive に保存
```

### Step 6: commit 提案（任意）

```
[git 操作]
- 新規ブリーフは git 未追跡。気に入った版を残すなら下記:
  cd C:/Users/hamaguchi.t/voicebot-flow-builder
  git add docs/manuals/brief_designer_manual_{date}.md
  git commit -m "docs: マニュアルブリーフ生成 {date}"
```

auto-commit はしない（人間レビュー前提）。

## 禁止事項

- **マニュアル本体を生成しない**。本 skill はブリーフ生成のみ。仕上げは Claude Design に委ねる
- **VBFB ソースを編集しない**。読むだけ
- **自動 push 禁止**。git commit も人間判断
- Plan / 章別 subagent が return しなかった章は空セクションとして残す（推測で埋めない）

## 関連 doc

- 想定ターゲット: https://claude.ai/design（リサーチプレビュー、独立 quota）
- 出力先: `voicebot-flow-builder/docs/manuals/`
- ハイブリッド設計の理由: CLI 側 quota で重い合成、Design 側 quota で見た目最適化、を分担

## 設計判断

- **なぜブリーフだけ生成して本体は Design に任せるか**: Design はリサーチプレビューで独立 quota、視覚最適化に特化したモデル想定。CLI 側で本体まで作ると視覚的に劣化する可能性 + CLI quota 消費が増える
- **なぜ単一ファイル出力か**: Design に貼り付ける都合、複数ファイルだと手間。1 ファイル 15-25 KB 以内に収める
- **なぜ git 自動 commit しない**: ブリーフは目視確認推奨（章立て・引用箇所が意図通りかチェック）
