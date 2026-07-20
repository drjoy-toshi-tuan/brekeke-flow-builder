# SKILL_CONTRACT: prompter サイドカーの [CONTRACT] ブロック解釈

> **全 SKILL (A〜F) 共通の前提ルール**。各 SKILL のプロンプト記述前に必ず読む。

## 概要

orchestrator が prompter を起動する際、サイドカー MD の各 `## モジュール名` 直下に
`[CONTRACT]…[/CONTRACT]` ブロックを注入する。これは 4 層責任モデル
(`memory: project_4layer_responsibility_model`) に従って、**OpenAI 出力（第 3 層）と
それを消費する後段 (CMR/script/RAG/save2db 等、第 4 層) の整合**を担保するための
構造化メタ情報。

prompter は CONTRACT を **必ず読み**、これに従ってプロンプト本文を構築する。

## CONTRACT ブロックの形式

```markdown
## OpenAI_受診希望日聴取_変更
[CONTRACT]
purpose: 受診希望日（変更後）を聞き取って YYYY-MM-DD に正規化
output_target_field: Preferred_date
output_target_format: YYYY-MM-DD
forbidden_in_context:
  - "5月10日"
  - "0510"
abstract_context: |
  直前にユーザーへ受診希望日の入力を依頼した。
  フォーマットは M月D日 / MMDD 4桁 / YYYY年M月D日 のいずれか。
stt_pre_normalized:
  from_template: hearing_datetime
downstream_references:
  - caller: script_受診希望日_ゲート判定_変更
    caller_type: "@General$Script"
    ref_kind: params.module
  - caller: script_受診希望日_ゲート判定_変更
    caller_type: "@General$Script"
    ref_kind: params.script.embedded
[/CONTRACT]
# Role
（以下 prompter が書く本文）
```

## prompter のハードルール（絶対遵守）

### 1. forbidden_in_context: Context への混入禁止

`forbidden_in_context` に列挙された値（typically TTS の発話例リテラル）は
**プロンプト本文の Context セクションに引用してはいけない**。

理由: GPT-4.1 + temp 0.01 で **リテラル例示値が強アンカー化** し、ユーザーの実発話を
引きずる現象がある（新宿健診プラザの「4月30日 → 4月1日」誤判定が実例）。
memory `feedback_few_shot_breaks_output.md` 同機序。

**❌ NG (現在多い書き方)**:
```
直前にユーザーへ次の質問がされています：
「予約日を「4月1日」のように日付でお話ください。0401のように4桁の数字でお話ください。」
```

**✅ OK (CONTRACT 準拠)**:
```
# Context（重要）
直前にユーザーへ予約日の入力を依頼した。
フォーマットは「M月D日」または「MMDD 4桁」または「YYYY年M月D日」のいずれか。
```

### 2. abstract_context: 抽象記述を優先

`abstract_context` が指定されている場合、それを **Context セクションのベース** にする。
TTS テキストをそのまま引用しない。

abstract_context の文言を機械的にコピーするのではなく、SKILL 固有の文脈
(日付正規化用語、Yes/No 判定用語等) と統合して書く。

### 3. stt_pre_normalized: STT 層責務の重複排除

`stt_pre_normalized` がある場合、第 2 層 (AmiVoice STT 辞書) で揺れ吸収済みであることを
**Context に 1 行記載するのみ**。OpenAI 側で同義語列挙して再吸収しようとしない。

**❌ NG (重複)**:
```
ユーザーは「4月30日」「30日」「サンジュウ」「３０日」のように発話する可能性があります。
これらすべてを 2026-04-30 として認識してください。
```

**✅ OK (層責任尊重)**:
```
（注: 月名・相対日付の発話揺れは STT 層 (hearing_datetime テンプレ) で正規化済み。
OpenAI は正規化済みテキストを受け取る前提でフォーマット変換のみ実施せよ）
```

### 4. downstream_references: 出力厳格化の判断材料

`downstream_references` の各 ref を見て、**output_format をどう厳格化するか** を判断する。

| caller_type に含まれるキーワード | ref_kind 例 | 出力厳格化方針 |
|---|---|---|
| `Script` (`@General$Script`) | `params.module` / `params.script.embedded` | 後段 script が `getModuleResult` で読む前提。**機械可読フォーマット厳格、空文字や前置き禁止** |
| `ContextMatchRouter` | `params.module1Name` / `module2Name` | 後段 CMR の slot 値と **完全一致** する出力を要求。表記揺れ禁止 |
| `generate_by_OpenAI` | `params.module` | OpenAI 連結処理。後段 OpenAI が読みやすい簡潔な構造化テキスト |
| `Jump to Flow` | `params.flowname` 等 | サブフローへ引数として渡される。`subflow_expected_format` (CONTRACT 内に追加情報) に従う |
| `Re-confirmation` | `params.nodeName` | 復唱で再生される。出力値を読み上げ可能な形式（不可読記号禁止）|
| 上記いずれにも該当しない、または **未知の caller_type** | — | **既定挙動**: output_target_format に厳密準拠、前置きなし、リテラルのみ |

**重要 (フォールバック)**: 未知の `caller_type` / `ref_kind` が来ても、**プロンプト記述を破綻させない**。
default は「output_target_format 厳守 + 前置き禁止 + NO_RESULT 経路の保証」で堅く書く。

### 5. CONTRACT 不在時の挙動

`[CONTRACT]…[/CONTRACT]` ブロックが存在しない場合、または一部フィールド欠落の場合:

- **不在で破綻しない**こと。既存の SKILL ベースプロンプトで書く（後方互換）
- 欠落フィールド: 該当ハードルールをスキップ、それ以外は適用

### 6. CONTRACT は OpenAI に渡らない

`[CONTRACT]…[/CONTRACT]` ブロックは prompter サイドカー MD 内のメタ情報であり、
inject_prompts.py が JSON へ注入する際に **strip される**。最終 OpenAI prompt には含まれない。
prompter は自身がこの情報を消費するだけで、本文に貼り付けない。

## CONTRACT が空 / 部分欠落のときの優先順位

```
forbidden_in_context あり    → Context に literal 引用禁止 (絶対)
abstract_context あり        → Context のベースとして利用 (推奨)
stt_pre_normalized あり      → 「STT で正規化済み」記述に置換 (推奨)
downstream_references あり   → 出力厳格化を消費側に合わせる (絶対)
output_target_format あり    → Output 形式の根拠 (絶対)
purpose / output_target_field → Role 記述の参考 (推奨)
```

## 実装上の関連物

- 設計思想: memory `project_4layer_responsibility_model.md`
- CMR の `^0$ other` 排他形式設計と PROMPT-005 検証も同 memory 参照
- orchestrator が CONTRACT 構築するヘルパー: `schemas/module_graph.py:find_module_references / find_cmr_consumers`
- prompter SKILL ファミリ: SKILL_A〜F は本ファイルのルールを **全て継承** する（個別 SKILL 内で再記載しない、本ファイル参照のみで足りる）
