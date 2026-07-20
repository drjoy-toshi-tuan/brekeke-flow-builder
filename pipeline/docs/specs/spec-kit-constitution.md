# Spec Kit — 変更ガバナンス憲章（constitution）

> **目的: 本リポジトリへのあらゆる変更（コード / プロンプト / 設計書 / spec）が、
> ①出力品質を落とさないこと、②実データに基づき実運用に適合していること、を機械的に担保する。**
>
> 位置づけ: CLAUDE.md（権限・セキュリティの憲法）の下位、個別 spec（layout_spec 等）の上位。
> 変更を提案・実装する人間および AI エージェントは、着手前に本章を読むこと。

---

## 0. 二大原則（すべての変更に適用）

| 原則 | 意味 | 検証方法 |
|---|---|---|
| **P1: 出力品質を証明せよ** | 変更後の成果物（YAML / JSON / prompt / properties）が既存ゲートを全て PASS し、品質が同等以上であることを示す | 下記「品質ゲート表」の該当ゲートを変更前後で実行し、レポートを PR に添付 |
| **P2: 実データに根拠を持て** | 新しい仕様・synonym・プロンプト・分類ルールは、実在する顧客資料・実シナリオ YAML・実通話ログのいずれかを出典とする。推測・創作で仕様を増やさない | PR 説明に出典（ファイルパス / 施設名 / 資料名）を明記。出典がない項目は `augment` / TODO 扱いで人間レビューへ |

**LLM ハルシネーション対策の鉄則**: LLM が生成した値（TTS 文言・モジュール名・分岐条件・mapping）は
「出典が示せるまで未確定」として扱う。出典なしで master に入れない。

---

## 1. 変更タイプ別チェックリスト

### A. パイプラインスクリプト変更（scripts/ schemas/ tools/）

- [ ] 決定論優先: LLM で解いている処理を追加しない（`deterministic-replacement-roadmap.md` 準拠）。やむを得ず LLM を使う場合は fallback 経路として隔離し、ログに `FALLBACK` を明示
- [ ] 既存シナリオ 1 件以上で回帰実行（qa_validator → scaffold → validator → tester が全 PASS）
- [ ] 入出力仕様の変更は該当 spec ドキュメント（docs/specs/ / docs/governance/）を同 PR で更新
- [ ] 保護ゾーンのため PR + コードオーナーレビュー必須

### B. プロンプト・SKILL テンプレート変更（docs/ai/skills/）

- [ ] 変更理由となった**実際の誤判定事例**（通話ログ / テストケース）を PR に記載
- [ ] SKILL_A〜E 由来のプロンプトは `gen_prompts.py` のテンプレートと同期していること（片方だけ直さない）
- [ ] 分類系プロンプトはテストケース（期待入出力表）を最低 5 件更新・追加
- [ ] レッドチーム観点（攻撃耐性・NO_RESULT 分岐・出力安全性）を壁打ちで点検（SKILL_redteam_review.md）

### C. 設計書 YAML（output/scenarios/）

- [ ] `scenario_flow` の block_type は allowlist（`schemas/qa_validator.py` KNOWN_BLOCK_TYPES）のみ
- [ ] 聴取項目名は `docs/specs/hearing_item_catalog.yaml` の canonical 名を使用。カタログにない項目は synonym 追加を先に PR する（勝手な別名を作らない）
- [ ] TTS 文言・分岐条件はすべて顧客資料に出典があること。ない場合は `{PLACEHOLDER_*}` のまま残し、人間壁打ちで確定（yaml_fill に推測させない）
- [ ] qa_validator CRITICAL 0 件で scaffold へ

### D. カタログ・辞書データ（hearing_item_catalog.yaml / stt_dictionary 等）

- [ ] 新 synonym・新 canonical は**実在シナリオ or 実顧客資料での出現例**を出典として明記
- [ ] `normalize_hearing_items.py` のスモークテスト（実ラベルでの一致確認）を再実行
- [ ] canonical に紐づく block_type / output_format / save_to の変更は既存シナリオへの影響を grep で確認

### E. modules / script 部品

- [ ] `modules/README.md` の DoD 準拠: REQUIREMENTS.md + oracle.py + test_oracle.py 全 PASS + 実機受入（P6）
- [ ] 1 文字でも改変したら再受入（part-certification-spec.md）

---

## 2. 品質ゲート表（P1 の検証手段）

| ゲート | コマンド | 対象 | PASS 条件 |
|---|---|---|---|
| 設計書検証 | `python3 schemas/qa_validator.py <yaml>` | 設計書 | CRITICAL 0 |
| 構造検証 | `python3 scripts/validator.py <json>` | フロー JSON | CRITICAL 0 |
| 構造監査 | `python3 scripts/tester.py <json>` | フロー JSON | AUD/R 系 0 |
| プロンプト決定論生成 | `python3 scripts/gen_prompts.py <yaml>` | prompt | exit 0（FALLBACK 0 が理想。FALLBACK ありは理由を PR に記載） |
| 部品オラクル | `modules/*/test_oracle.py` | 部品 | 全ケース PASS |
| 連結テスト | `gen_p7_cases.py` → 実機 | 完成品 | 全エッジ PASS |
| 採点 | score_gate | 完成品 | 出荷可 |

**ルール: 変更がどのゲートに影響するかを PR で宣言し、そのゲートの前後比較を示す。**
「影響なし」と宣言する場合もその根拠（触っていない領域である理由）を書く。

---

## 3. 実データ主義（P2 の運用）

1. **出典の優先順位**: 実顧客資料（PDF / drawio / 議事録）＞ 既存本番シナリオ YAML ＞ 実通話・テストログ ＞（出典なし＝採用不可）
2. **カタログ駆動**: 聴取項目は必ず catalog 経由（`normalize_hearing_items.py`）で正規化してから設計書に載せる。director / 人間が独自の項目名を発明しない
3. **不明は不明のまま**: 資料に無い情報は PLACEHOLDER / augment / BLOCKER として明示し、壁打ちで人間が確定する。「それらしい値で埋める」ことを AI に許さない
4. **生成物でなく生成器を直す**: 出力の欠陥を見つけたら成果物パッチではなく、設計書・カタログ・テンプレート（＝生成器の入力）を直して再実行する

---

## 4. PR テンプレート追記事項（本章準拠の宣言）

PR 本文に以下 3 行を必ず含める:

```
- 品質ゲート: <実行したゲートと結果（例: qa_validator PASS / validator PASS / gen_prompts exit0）>
- データ出典: <仕様・文言・synonym の根拠となった実資料のパス or 「コード変更のみ・仕様追加なし」>
- LLM 関与: <この変更で LLM 生成物を含むか。含む場合は人間レビュー済みか>
```

---

## 5. 関連文書

- `CLAUDE.md` — 権限・セキュリティ・パイプライン全体像（本章の上位）
- `docs/governance/deterministic-replacement-roadmap.md` — LLM→決定論置換の優先順位
- `docs/governance/part-certification-spec.md` — 部品認定（engine/spec 二段ハッシュ）
- `docs/specs/hearing_item_catalog.yaml` — 聴取項目カタログ（正本）
- `docs/ai/skills/SKILL_redteam_review.md` — 壁打ち校閲の観点
