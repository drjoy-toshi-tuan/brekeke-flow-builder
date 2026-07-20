# run_history — pipeline 実行サマリ集約

orchestrator.py が pipeline 完走時に書き出す 1 run = 1 ファイル形式の JSON。

## 目的

**Curator / Optimizer Agent の signal source**。

51+ 施設の pipeline 実行データ（時間・トークン・critical code・fixer 修正量等）を git tracked な 1 箇所に集約することで:

- 個別 worktree が削除されても master に永続記録が残る
- 並列実行 (launch_parallel) でも merge 衝突しない（ファイル名がユニーク）
- Curator が施設横断で「同じ critical_code が頻発している」「同じ pattern で fixer 巻き戻し量が多い」等を検出できる

## ファイル命名

```
docs/run_history/{施設}_{flow}_{YYYYMMDD_HHMMSS}.json
```

例:
- `新宿健診プラザ_健診_20260427_171020.json`
- `島村記念病院_健診_20260427_142231.json`

タイムスタンプは pipeline `started_at` から導出。同一施設の再実行は別ファイルとして残る（過去履歴保持）。

## スキーマ

`schema_version: 1` 系（2026-04-27〜）:

```json
{
  "facility": "新宿健診プラザ",
  "flow": "健診",
  "pattern": 3,
  "started_at": "2026-04-27T17:21:00",
  "ended_at": "2026-04-27T18:12:56",
  "duration_sec": 3116.0,
  "unattended": true,
  "completed": true,
  "tokens_total": {
    "input": 25137383,
    "output": 475689,
    "cache_creation": 25136875,
    "cache_read": 0
  },
  "step_summary": {
    "director": {"status":"ok","seconds":0},
    "prompter_props": {"status":"ok","seconds":540,"tokens":{...}},
    "fixer": {"status":"ok","seconds":1900,"tokens":{...}}
  },
  "critical_codes_seen": ["E-13", "CMR-001"],
  "report_paths": {
    "fixer_report": "...",
    "validator_report": "..."
  },
  "git": {
    "feature_branch": "feature/新宿健診プラザ_健診",
    "head_sha": "..."
  },
  "schema_version": 1
}
```

## 古い施設の backfill

run_history hook 実装前 (2026-04-26 以前) の施設データは `pipeline_state_*.json` から再構築可能。Phase 2 で backfill スクリプト (使い捨て) を実行予定。

## 想定される利用例

| Agent / Skill | 利用方法 |
|---|---|
| Curator: `analyze_run_history` | 直近 N 件 / 施設 X / pattern Y の実行データを集計 |
| Curator: `propose_patch_box_entries` | recurring critical code → 該当施設用 patch_box 提案 |
| Optimizer (週次) | 同じ memory が N 回有用と判定された → Core 昇格判断 |

## 注意

- このディレクトリは **git tracked** (master 永続)。`.gitignore` に追加しないこと
- `output/` 配下は将来 git 除外予定なので、ここを `output/run_history/` には置かない
- pipeline 失敗で commit step に到達しなかった run は記録されない（orchestrator が write_run_history を commit 前に呼ぶため）
