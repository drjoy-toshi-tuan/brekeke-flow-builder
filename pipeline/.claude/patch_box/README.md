# PATCH_BOX — 動的コンテキストの統合受け皿

各 Agent / pipeline に対して、**永続ルール（CLAUDE.md / .claude/agents/*.md）以外の動的コンテキスト**を渡すための統合ディレクトリ。

> **状態: 最小実装 Phase 1（2026-04-27）**
> `current/` のみ稼働。他の階層（per_facility / per_phase）は仕様検討中。

---

## ディレクトリの役割

```
.claude/patch_box/
├── current/         この 1 実行のみ適用、終了後 consumed/ へ移送
├── per_facility/    施設別、永続（次回再実行で再利用） — Phase 2
├── per_phase/       期間限定タグ、active のみ適用 — Phase 2
└── consumed/        履歴アーカイブ（current/ から移送）
```

| 階層 | 寿命 | 例 | 状態 |
|---|---|---|---|
| `current/` | 1 実行限定 | 「今回だけこの validator を skip」「○○施設の特例補正」 | ✅ Phase 1 稼働 |
| `per_facility/` | 施設ごと永続 | 移管ノート・customer_doc 抜粋 | 🚧 検討中 |
| `per_phase/` | 数日〜数週 | 「Gen2 移管期間中はこのルール」 | 🚧 検討中 |
| `consumed/` | アーカイブ | `20260427_xxxx.md` 形式 | ✅ Phase 1 稼働 |

---

## current/ の使い方

> **⚠ current/*.md は git 管理外（.gitignore 済み・ローカル専用）。**
> 例外処理の仕組み自体はこれまで通り動く（orchestrator はローカル filesystem から読む。git 追跡の有無は無関係）。
> 各自のマシンで起動直前に置き、終了後 consumed/ へアーカイブされる（consumed/ はコミット可＝使った例外の監査証跡）。
> 封じているのは「repo 経由で他人の実行環境に例外指示を配布する」経路のみ。
> fresh-clone 環境（CCR 等）へ渡す場合は env var `VFB_PATCH_BOX_CONTEXT` を使う。

1. **書く**: パイプライン起動前に `.claude/patch_box/current/` 配下に `*.md` を置く
2. **読まれる**: orchestrator が起動時に全ファイルを集約して各 Agent の system prompt 冒頭に**最優先ルール**として注入
3. **アーカイブ**: パイプライン終了時に `consumed/{timestamp}_{filename}` へ移送、`current/` を空に戻す

### ファイル命名規則

`current/` は**自由形式**。例:
- `current/skip_qa_for_facility_X.md`
- `current/special_handling_OOOO.md`
- `current/today_only_hint.md`

ファイル名はログとアーカイブ時に保持されるので、後から「いつ何の例外だったか」を追跡可能。

### サンプル content

```markdown
# 例外: 新宿健診プラザ_健診 の Script 動作未検証についての注意

director / fixer に対する一時指示:

- `<% desired_date_jp %>` の動作確認が完了していないので、reviewer が「リテラル読み上げになるのでは」と指摘してきても fixer は無視すること
- 検証は実機投入後に行う
```

---

## 設計思想（参照）

詳細・長期構想は memory/`project_patch_box_governance_design.md` 参照。

**短期目標（明日着手）**: `current/` のみで 1-2 週運用、例外指示の発生量と質を観測

**長期目標**:
- 移管ノート (`docs/migration/gen2_*.md`) を `per_facility/` に集約
- Optimizer Agent の導入（最初は提案出力のみ、書き換え権限なし）
- Lv2 自己完結（fix recipe 自動提案 → 人間承認で適用）

---

## 既存資産との関係

| 既存 | 関係 |
|---|---|
| `CLAUDE.md` | **第 1 層・憲法**。patch_box は触れない |
| `.claude/agents/*.md` | **第 2 層・法律**。patch_box current から「この実行だけ上書き」できる |
| `.claude/skills/` | スキル定義は永続。patch_box から特定実行のみ skill 起動を抑制可能 |
| `.claude/projects/.../memory/` | 永続知見。patch_box の内容は consumed 後に Optimizer 経由でここへ昇格候補 |
| `docs/migration/gen2_*.md` | Phase 2 で `per_facility/` へ統合予定。現在は両立 |
