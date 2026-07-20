# Prompterエージェント追加 — 影響ファイルと変更内容

> prompter.md の新規作成に伴い、以下のファイルに変更が必要です。

---

## 1. pl.md — パイプラインパターンへの追加

### 変更箇所: 4つの作業パターンの定義テーブル

**変更前:**
```
| P1: 新規作成 | 真っさらから構築 | @director → @generator → @reviewer → 検品 |
| P2: 既存修正 | .bivr + プロパティがある状態で修正 | @generator（修正）→ @reviewer → 検品 |
| P3: Gen2→Gen3 | 第2世代プロンプトから移管 | @director → @migrator → @reviewer → 検品 |
| P4: Gen1→Gen3 | Commubo HTMLから移管 | @director → @migrator（Gen1モード）→ @reviewer → 検品 |
```

**変更後:**
```
| P1: 新規作成 | 真っさらから構築 | @director → @generator → @prompter → @reviewer → 検品 |
| P2: 既存修正 | .bivr + プロパティがある状態で修正 | @generator（修正）→ @prompter → @reviewer → 検品 |
| P3: Gen2→Gen3 | 第2世代プロンプトから移管 | @director → @migrator → @prompter → @reviewer → 検品 |
| P4: Gen1→Gen3 | Commubo HTMLから移管 | @director → @migrator（Gen1モード）→ @prompter → @reviewer → 検品 |
```

> **P2（既存修正）の補足**: プロンプト修正のみの場合は `@prompter` 単体で呼んでもよい。構造変更を伴わない場合はgeneratorを経由しない。

### 変更箇所: PLの振り分けロジック

PLがパイプラインを実行する際、generator/migratorの完了後に自動的に `@prompter` を呼ぶステップを追加する。具体的には、以下の条件で呼び出す:

- generatorまたはmigratorがフローJSONを出力した直後
- 出力されたJSONに `generate_by_OpenAI` タイプのモジュールで `params.prompt` が空欄のものがある場合

---

## 2. CLAUDE.md — エージェント一覧とパイプラインの更新

### 変更箇所: AIの担当スコープ

以下の行を追加:
```
| **AI（prompter）** | generate_by_OpenAIモジュールのプロンプト記述（Opusモデルで実行） |
```

### 変更箇所: パイプライン全体像コメント

**変更前:**
```bash
# パイプライン全体像:
# 顧客資料 → [@director] → 設計書 + 確認レポート → [@generator] → draft JSON + properties → [@reviewer] → reviewed JSON → [validator.py] → [build_bivr.py] → .bivr
```

**変更後:**
```bash
# パイプライン全体像:
# 顧客資料 → [@director] → 設計書 + 確認レポート → [@generator] → draft JSON + properties → [@prompter] → prompt入りJSON → [@reviewer] → reviewed JSON → [validator.py] → [build_bivr.py] → .bivr
```

### 変更箇所: AIが読むファイルと順番テーブル

以下の行を追加:
```
| OpenAIプロンプト記述時（@prompter） | `docs/ai/openai_prompt_design_guide.md` → `docs/ai/openai_prompts_reference.md` → `docs/designs/設計書_*.md` |
```

### 変更箇所: 設計書生成ガイドライン 13番

**変更前:**
```
13. **OpenAIモジュールのプロンプト（`params.prompt`）はフローJSON内に直接記述する**（IVRプロパティではない）。本体フローのプロンプトは別途プロンプト作成エージェントが記述するためgeneratorは空のまま出力する。
```

**変更後:**
```
13. **OpenAIモジュールのプロンプト（`params.prompt`）はフローJSON内に直接記述する**（IVRプロパティではない）。本体フローのプロンプトは `@prompter` エージェントが記述する。generatorは構造のみ出力し、promptは空のまま。個人情報聴取サブフローのプロンプトはリファレンスbivrからそのままコピーする（prompterは触らない）
```

---

## 3. README.md — エージェント仕様テーブルの更新

### 変更箇所: エージェント仕様テーブル

以下の行を追加:
```
| prompter | `.claude/agents/prompter.md` | Opus | generate_by_OpenAIモジュールのpromptを記述 |
```

### 変更箇所: パイプライン図

```
顧客資料 → [director(Opus)] → 設計書 + 確認レポート
                                    ↓
設計書 → [generator(Sonnet)] → draft JSON + properties
                                    ↓
         [prompter(Opus)]    → prompt入りJSON
                                    ↓
         [reviewer(Sonnet)]  → reviewed JSON + 校閲レポート
                                    ↓
         [validator.py]      → 構造 + properties 整合性チェック
                                    ↓
         [build_bivr.py]     → .bivr ファイル
```

---

## 4. generator.md — 既存のprompter参照記述の明確化（任意）

generator.md の L87 と L297 に「別途プロンプト作成エージェントが記述する」という記述がある。これを `@prompter` に明示的に更新する:

**変更前:** `別途プロンプト作成エージェントが記述するため空のまま出力`
**変更後:** `@prompter エージェントが記述するため空のまま出力`

---

## 5. reviewer.md — OpenAIプロンプトの校閲観点の追加検討

現在のreviewer.mdの9つの校閲観点にはOpenAIプロンプトの内容チェックは含まれていない（構造チェックのみ）。prompterが追加された後、reviewerに以下の観点を追加するかは今後の検討事項:

- [ ] OpenAIモジュールの `params.prompt` が空欄のまま残っていないか（prompterのスキップ漏れ検出）
- [ ] プロンプトの出力ラベルと `next` 配列の `condition` の整合性

> ※ プロンプトの「内容の品質」チェック（文言の適切さ等）はreviewerの範疇外。Testerエージェント（将来）の担当。

---

## 6. settings.json — 変更不要

prompterはRead/Write/Edit/Bash/Glob/Grepを使用するが、これらは既にallowリストに含まれている。追加の権限設定は不要。

---

## 7. 引き継ぎドキュメント（第4回）への記載事項

- prompter.md の新規作成（Opus、独立ステップ）
- パイプライン: generator/migrator → prompter → reviewer の順
- 担当範囲: `generate_by_OpenAI` の `params.prompt` のみ
- 個人情報サブフローのプロンプトはprompterの対象外（リファレンスからコピー済み）
- PLの4パターン全てにprompterステップを追加
- PENDING: `docs/ai/openai_prompt_design_guide.md` 等のリファレンスが十分かの確認
