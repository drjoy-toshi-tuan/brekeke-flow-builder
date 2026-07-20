# Spec Kit — 改善プロセス規程（discussion → decision → kaizen）

> **目的: 本リポジトリの改善は「思いつきの即実装」ではなく、
> 壁打ち（議論）→ 仕様化 → 実装 → 計測 → 振り返り の反復ループで行い、
> 品質を継続的に引き上げる。**
>
> 姉妹文書: `spec-kit-constitution.md`（変更の**内容**基準）。本書は変更の**進め方**基準。

---

## 0. 改善ループ（全体像）

```
[1] 課題の記録 (Problem Record)
      ↓ 実データ・実事例を添えて起票
[2] 壁打ち (Discussion)
      ↓ 人間 + Claude で選択肢を比較・決定
[3] 仕様化 (Spec First)
      ↓ 実装前に spec / 設計を文書化（小変更は PR 説明で可）
[4] 実装 (Implementation)
      ↓ constitution のチェックリスト + 品質ゲート準拠
[5] 計測 (Measure)
      ↓ 変更前後の品質指標を比較
[6] 振り返り (Retrospective)
      → 学びを CLAUDE.md / spec / SKILL / カタログへ還元 → [1] へ
```

**鉄則: どのステップも飛ばさない。ただし変更の大きさでステップの重さを変える（§4 サイズ規程）。**

---

## 1. 課題の記録 — Problem Record

改善の起点は必ず「実際に観測された問題」または「計測された品質ギャップ」。

- 起票先: GitHub Issue（または壁打ちアジェンダ `/sparring-intake`）
- 必須記載:
  - **観測事実**: 何が・どのシナリオ/工程で・いつ起きたか（ログ / レポート / ファイルパス）
  - **影響**: 出力品質・工数・リスクへの影響
  - **再現手段**: 該当ゲートのコマンド or テストケース
- 禁止: 「〜のほうが良さそう」だけの起票（実例・計測なしの改善提案は保留箱へ）

---

## 2. 壁打ち — Discussion のルール

- **人間 + Claude の out-of-line 議論**が正式な意思決定の場（ライン内 LLM ゼロの原則と対）
- Claude の役割: 選択肢の列挙・トレードオフ分析・既存 spec との整合チェック・反証（レッドチーム視点）
- 人間の役割: 設計判断・優先順位・採否の最終決定
- **決定は必ず記録する**（§3 Decision Record）。口頭/チャットだけの決定は「未決定」とみなす
- 議論で合意できない/情報不足 → 追加データ収集タスクに変換して持ち帰る（推測で決めない）

---

## 3. 決定の記録 — Decision Record（軽量 ADR）

方針レベルの決定（工程の追加/退役、LLM↔決定論の置換、カタログ構造変更 等）は
`docs/governance/decisions/YYYY-MM-DD_<slug>.md` に 1 枚で残す:

```markdown
# <決定タイトル>
- 日付 / 決定者:
- 背景（観測事実・Problem Record リンク）:
- 検討した選択肢と却下理由:
- 決定内容:
- 成功条件（何がどう改善されたら成功か・計測方法）:
- 見直し条件（どうなったらこの決定を再検討するか）:
```

過去の例に倣う: reviewer 退役 (2026-06-24)、director 自律リトライ廃止 (2026-06-19) のような
keystone 決定は CLAUDE.md にも反映する（決定 → 憲法へ昇格）。

---

## 4. サイズ規程 — 変更の大きさで手続きを変える

| サイズ | 例 | 必要な手続き |
|---|---|---|
| **S（軽微）** | typo、synonym 1 件追加、コメント修正 | PR のみ（constitution の 3 行宣言は必須） |
| **M（標準）** | スクリプトのロジック変更、SKILL 修正、catalog 項目追加 | Problem Record + PR + 該当ゲート前後比較 |
| **L（方針）** | 工程の追加/削除、LLM 使用箇所の変更、スキーマ変更 | 壁打ち + Decision Record + PR + 全ゲート回帰 |

判断に迷ったら 1 段重いほうに倒す。

---

## 5. 計測 — 品質を数字で追う

改善が「効いたか」を判定できるよう、以下を継続指標とする（PR / 振り返りで参照）:

| 指標 | 取得元 | 望ましい方向 |
|---|---|---|
| qa_validator CRITICAL 件数 / シナリオ | `--json-report` | ↓（壁打ち差し戻しの減少） |
| yaml_auto_fixer / auto_fixer の自動修正件数 | fixer レポート | ↓（生成器の品質向上で不要になる） |
| gen_prompts FALLBACK 件数 | exit=2 stderr | ↓（決定論カバレッジ拡大） |
| tester.py 監査指摘件数 | test_report | 0 維持 |
| P6/P7 実機 FAIL 件数 | 受入レポート | ↓ |
| 未マッチ聴取項目ラベル数 | `normalize_hearing_items.py --show-unmatched` | ↓（カタログ充実） |
| 1 シナリオあたりの人間介入回数（壁打ち往復数） | pipeline_state | ↓ |

**新しい工程・ツールを足す提案は、どの指標をどれだけ動かすつもりかを必ず宣言する。**

---

## 6. 振り返り — 学びの還元先

改善が完了したら、得られた知見を「次も自動的に効く場所」へ書き戻す:

| 学びの種類 | 還元先 |
|---|---|
| 恒久ルール・原則 | `CLAUDE.md` |
| 工程の仕様・判断基準 | `docs/specs/` / `docs/governance/` |
| プロンプトの改善パターン | `docs/ai/skills/SKILL_*.md` + `gen_prompts.py`（同期必須） |
| 聴取項目・synonym | `docs/specs/hearing_item_catalog.yaml` |
| 検証で捕まえるべき新パターン | `qa_validator.py` / `validator.py` にチェック追加 |
| 部品の欠陥 | oracle テストケース追加 → 再受入 |

**「人の頭の中」「チャット履歴」だけに残る学びはゼロにする** — それが継続的改善の条件。

---

## 7. 定期レビュー（リズム）

- **シナリオ納品ごと**: §5 指標のスナップショットを確認レポートに添付
- **月次**: 指標トレンド確認・保留箱（実例待ちの改善案）の棚卸し・Decision Record の見直し条件チェック
- **keystone 決定後**: 1 か月時点で成功条件を検証し、結果を Decision Record に追記

---

## 8. 関連文書

- `docs/specs/spec-kit-constitution.md` — 変更内容の品質・実データ基準（姉妹文書）
- `project-governance/docs/loop-governance.md` §9 — VFB 製造ライン v2 の全体構想
- `docs/governance/factory-v2-phase2-foreman.md` — 工場長（解析・起票・調達）
- `docs/governance/test-feedback-loop.md` — テスト結果の還元ループ
