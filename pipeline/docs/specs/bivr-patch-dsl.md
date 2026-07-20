# bivr-patch DSL — Pattern 2 外科的修正の決定論実行（v1）

> **目的: 既存フロー JSON への外科的修正（修正依頼 P2-A 系）を
> 「人間が承認した patch ファイルを機械が原文どおり適用する」方式に置き換え、
> ライン内 LLM の最後の例外（fixer の手 Edit）を退役させる。**
>
> 実行器: `tools/bivr_patch.py`（決定論・fail-closed）。
> 診断（何を直すか）は従来どおり人間 + Claude の壁打ち（ライン外）。
> dirlite は「文章の指示書」でなく「この patch ファイルのドラフト」を出す役に移行する。

---

## アーキテクチャ

```
修正依頼 → 壁打ち（人間+Claude・ライン外）: 原因調査 → patch YAML を起草
        → 人間が patch YAML をレビュー・承認（何が変わるか 1 行 1 変更で可視）
        → orchestrator --pattern 2 --spec <patch.yaml> --base <既存.bivr>
            → tools/bivr_patch.py が決定論適用（dry-run diff → 適用 → レポート）
            → validator（touched モジュール scope）→ tester/build → P7 → 承認
```

- 従来の Mode: Refresh / 文章指示書（dirlite → fixer）経路は**フォールバックとして存続**
  （patch DSL で表現できない稀な構造変更用）。patch で書ける修正は patch を使う。

## patch YAML 形式

```yaml
# 修正依頼: <施設> <flow> — <依頼の要約>（出典: 通話ID / 依頼メール等）
version: 1
target_flow: "福岡県新水巻病院$健診"   # 任意（bivr 内フロー名の確認用。省略可）
patches:
  # 例1: CMR の遷移先入れ替え（新水巻 修正① 相当）
  - op: set_next
    module: 用件分岐
    slot: 4                      # next[] の 1-based 位置。label:/condition: でも指定可
    next: 相談_問合せ
    expect: 相談_結果確認         # 現在値ガード（違ったら fail = 古い patch の誤適用防止）
  - op: set_next
    module: 用件分岐
    slot: 5
    next: 相談_結果確認
    expect: 相談_問合せ

  # 例2: モジュール参照元の変更（JAとりで 修正② 相当）
  - op: set_param
    module: 終話分岐
    param: module1Name
    value: "<% classification %>"
    expect: "openAI_確認_用件"

  # 例3: モジュール型の変更（JAとりで 修正① 相当）
  - op: set_type
    module: 確認_理由
    type: "drjoy^Text To Speech$Text to speech"
    params: {prompt: "", stop_by_dtmf: "No", category_words: ""}   # 型変更時の params 全置換（省略時は既存 params 温存）
```

### 対応 op（v1 — 実案件 9 修正の全てを被覆）

| op | 対象 | 必須キー | 説明 |
|---|---|---|---|
| `set_next` | next[] の遷移先 | module, slot\|label\|condition, next | 指定スロットの nextModuleName のみ書換（condition/label は不変） |
| `set_param` | params の 1 キー | module, param, value | 参照元変更・文言・設定値の書換 |
| `set_type` | モジュール型 | module, type | 型の書換。`params:` 指定時は params も全置換 |

### 安全機構（fail-closed）

1. **expect ガード**: 各 op に `expect`（現在値）を書ける。実際の値と不一致なら**全体を中止**
   （フローが既に変わっていた＝patch が古い、を機械検出）。壁打ち起草時は必ず付ける。
2. **全検証 → 一括適用**: 全 op を先に検証し、1 件でもエラー（モジュール不存在・スロット不存在・
   expect 不一致・未知 op）があれば**何も書き込まない**。部分適用は起きない。
3. **dry-run**: `--dry-run` で「変更一覧（before → after）」だけ表示。壁打ちレビューで使う。
4. **監査レポート**: 適用時に `bivr_patch_report_*.md`（適用した全変更の before/after 表）を出力。
   patch YAML 自体も成果物ディレクトリにコミット＝変更履歴が Git に残る。
5. **touched モジュール一覧**を stdout(JSON) で返す — orchestrator が validator の scope 制限に使う。

## orchestrator 統合

- `--pattern 2 --spec <ファイル>` の spec が **YAML かつ top-level に `patches:`** を持つ場合、
  dirlite agent をスキップして patch モードに入る（`step_dirlite` が判定）。
- `step_pattern2_apply` が `tools/bivr_patch.py --json <base展開JSON> --patch <spec> --apply` を実行。
  exit≠0 でパイプライン停止（人間へ差し戻し）。
- 以降（properties / validator / tester / build / P7 / 承認）は従来の Pattern 2 と同一。

## 品質ゲート

- 実行器は `tools/test_bivr_patch.py`（実案件由来の回帰: 新水巻 CMR 入替 / JAとりで参照元変更・型変更）
  全 PASS を DoD とする。
- patch YAML には**修正依頼の出典**（通話 ID / 依頼文書）をコメントで必ず記す
  （spec-kit-constitution P2: 実データ根拠）。

## 関連
- `docs/operations/modification_manual.md` — 修正種類 A〜E の判定（本 DSL は主に C/D の機械部分）
- `docs/specs/spec-kit-constitution.md` / `script-input-handling.md`
- governance §1-7 surgical patch（本 DSL はその決定論化）
