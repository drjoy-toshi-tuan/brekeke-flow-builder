# ý tưởng cải tiến — Spec-Driven Voicebot Builder

> 作成日: 2026-07-15  
> ステータス: アイデア段階（未実装）  
> 担当: dong.nguyen@drjoy.jp

---

## 背景・問題意識

現行パイプラインの課題:
- YAML 生成に Opus (LLM) を使用 → トークンコスト高・時間がかかる
- 壁打ち（/flow-draft）が人間の確認ボトルネックになっている
- AI が block type を「判断」するため出力が不安定
- AmiVoice 辞書登録・TTS 文言確認が別作業になっている
- **根本原因**: LLM に構造判断を任せすぎている

---

## ゴール

> **人間が Spec を管理する — コードが実行する — AI に全部任せない**
>
> 目標: パイプラインの 90% をコードで処理。LLM は「どうしても決定論で書けない部分」のみ。

---

## 提案アーキテクチャ

### 入力フロー（ユーザー体験）

```
1. User がフローを自由テキストで貼り付ける
   例: "冒頭 → 用件確認 → 氏名聴取 → 生年月日 → 終話"
         ↓
2. Normalize engine
   キーワード → 標準 block type にマッピング
         ↓
3. 聴取項目ごとにドラフト表を生成
   User はドロップダウンで各項目を選択
         ↓
4. システムがデフォルトロジックを自動補完
   User は確認 / 修正のみ
         ↓
5. リアルタイム validation（入力中に即エラー表示）
         ↓
6. Compile → Pipeline 実行
```

### システム全体像

```
┌─────────────────────────────────────────────────┐
│           SPEC FILE (Excel / UI)                │
│         ← 人間が書いて管理する SSoT →           │
│                                                 │
│  Flow │ TTS │ Context │ Choices │ Scripts │ ... │
└───────────────────┬─────────────────────────────┘
                    │ compile
                    ▼
         excel_to_yaml.py（純粋なコード）
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│           VISUAL REVIEW LAYER                   │
│         ← 人間が目視で確認・承認する →           │
│                                                 │
│  • フロー図（drawio 自動生成）                  │
│  • TTS テキスト一覧（canvas と照合）            │
│  • AmiVoice 辞書リスト（登録前に確認）          │
│  • スクリプトロジック プレビュー                │
└───────────────────┬─────────────────────────────┘
                    │ 人間承認 ✅
                    ▼
┌─────────────────────────────────────────────────┐
│           CODE PIPELINE（全自動）               │
│  scaffold → validator → properties → tester     │
└─────────────────────────────────────────────────┘
```

---

## Spec File — Excel が唯一の SSoT

| Sheet | 内容 | 担当 |
|---|---|---|
| **Flow** | ステップ名・block type・next・retry・settings | Staff（ドロップダウン） |
| **TTS** | モジュール名 → 発話テキスト | Staff（テキスト自由入力） |
| **Context** | 変数名・display type・保存値 | Staff（ドロップダウン + テキスト） |
| **Choices** | Enum ラベル → value → next | Staff（テキスト） |
| **Scripts** | テンプレートキー or カスタムロジック | Staff 選択 / Owner が custom 記述 |
| **AmiVoice** | ブロックごとの登録辞書 | Staff（テキスト） |
| **Termination** | 終話パターン一覧 | Staff |
| **Settings** | office_id・SMS flag・env など | Staff + Owner 確認 |

### ドロップダウンで制御（誤入力防止）

- Block type → `KNOWN_BLOCK_TYPES`（26種）
- Slot type → `patient_name / dob / phone / card_number`
- Format → `enum / text / datetime`
- Script template → 認定済みテンプレートキー
- Next → 同シート内の STT 番号参照（存在しない → コンパイルエラー）

---

## Maintain / 修正フロー

**原則: Spec File が常に SSoT。出力（JSON/YAML）は直接触らない。**

```
Spec v2（修正後）
      ↓ compile
Draft YAML
      ↓ diff
┌─────────────────────────────┐
│ DIFF REVIEW                 │
│ 🟡 用件確認: enum に1分岐追加 │
│ 🔴 氏名聴取: TTS text 変更  │
│ ✅ 生年月日: 変更なし        │
│ [Confirm → Re-run pipeline] │
└─────────────────────────────┘
```

---

## Validation — 3層

```
Layer 1（入力中・リアルタイム）:
  • Next が存在しない STT 番号 → 赤表示
  • Block type + format の組み合わせ不正 → ドロップダウンで防止
  • TTS text 空 → 黄色 warning
  • Choices enum < 2 → 警告

Layer 2（compile 時）:
  • Orphan step（誰も参照しない） → error
  • Dead end が termination でない → error
  • Context name 重複 → warning

Layer 3（既存 qa_validator）:
  • YAML 構造検証 → 変更なし
```

---

## 拡張ルール（新しいロジックが出たとき）

```
Staff:「該当するドロップダウンがない」→ Owner へ報告
Owner: 定義して以下に追加:
  ① 新スクリプトテンプレート → tools/script_templates.json
  ② 新 block type            → scaffold_generator.py + qa_validator.py
→ 次回からドロップダウンに自動反映
→ 「Spec 外パッチ」は絶対しない
```

---

## 実装スコープ（未着手）

| コンポーネント | 種別 | 説明 |
|---|---|---|
| `tools/excel_to_yaml.py` | 新規 | Excel → scenario_flow YAML コンパイラ |
| `tools/excel_review_gen.py` | 新規 | Review Package（drawio・TTS・AmiVoice）生成 |
| `tools/script_templates.json` | 新規 | テンプレートキー → ロジック定義 |
| `tools/voicebot_template.xlsx` | 新規 | Staff 配布用 Excel テンプレート |
| 既存パイプライン | 変更なし | scaffold_generator 以降はそのまま |

## 実装順序（推奨）

1. Excel template 設計（シート構成・ドロップダウン定義）
2. `excel_to_yaml.py` の基本 compile（Flow + TTS + Choices → YAML）
3. Validation layer 1〜2
4. Review Package 生成（TTS list + AmiVoice list）
5. Diff review 機能
6. drawio 自動生成連携（既存 yaml_to_drawio 流用）
7. （将来）Excel → Web UI へ移行

---

## 現状との比較

| 項目 | 現状 | 導入後 |
|---|---|---|
| YAML 生成 | AI（Opus・20〜40k token） | Excel → コンパイル |
| 出力検証 | qa_validator が事後検出 | 人間が事前に目視確認 |
| AmiVoice 辞書 | 別途手作業 | Excel から自動生成・確認 |
| スクリプトロジック | prompter AI | テンプレート選択・人間確認 |
| Token コスト | 高（Opus） | ほぼ 0 |
| 人間コントロール | 低（AI 判断） | 高（全行を人間が決定） |
