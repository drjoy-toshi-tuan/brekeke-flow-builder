# Skill: /new-flow — テキスト貼り付け → CSV → YAML ガイド付きフロー作成

## いつ使う

顧客資料（PDF/PPTX）からテキストをコピーして新規フローを作りたいとき。
- `new-scenario` との違い: director (Opus LLM) を使わず `csv_to_yaml.py`（決定論）で YAML を生成する
- 入力: ユーザーがチャットに貼り付けたテキスト（Canvas コピー等）
- 出力: `output/scenarios/{施設}_{flow}/設計書_{施設}_{flow}.yaml`

## 起動方法

```
/new-flow {施設名} {フロー名}
```

例: `/new-flow カレス記念病院 診療`

---

## Phase 0 — セットアップ

1. 引数から `FACILITY` / `FLOW` を取得。なければユーザーに確認。
2. `output/scenarios/{FACILITY}_{FLOW}/` が存在しなければ作成。
3. `tools/spec_template/sheet1_input.csv` を `output/scenarios/{FACILITY}_{FLOW}/sheet1_input.csv` にコピー（未存在時のみ）。
4. `tools/spec_template/記入ガイド.md` の内容を頭に入れる（コンテキストとして読む）。

## Phase 1 — テキスト収集（壁打ち）

**Claude がユーザーに聞く:**
```
顧客資料のテキストを貼り付けてください。
（PDF/PPTX からコピーしたテキスト、複数回に分けて貼り付けOK）
「完了」と入力したら次のステップへ進みます。
```

ユーザーが「完了」と言うまでテキストを蓄積する。

## Phase 2 — Sheet1 自動入力

貼り付けられたテキストを解析し、`sheet1_input.csv` の各列を埋める:

| 列 | 抽出方法 |
|---|---|
| `聴取項目名` | フロー上の各ステップ名（受付、診療科聴取、氏名聴取 等） |
| `TTS文言` | 顧客資料の発話文言（「〜をおっしゃってください」等） |
| `choices` | 分岐選択肢（予約\|変更\|キャンセル 等、`\|` 区切り） |
| `retry回数` | 明記あれば抽出、なければ `3` をデフォルト |
| `reconfirm` | 復唱確認の記載があれば `あり` |

**足りないフィールドは1つずつ質問する（一気に全部聞かない）:**
```
「診療科聴取」のTTS文言が見つかりませんでした。
どのような音声案内にしますか？
例: 「診療科をおっしゃってください」
```

**全フィールド埋まったら確認:**
```
sheet1_input.csv の内容を確認してください:
[表形式で表示]
修正がなければ「OK」、修正箇所を指示してください。
```

## Phase 3 — spec sheets 生成

```bash
python3 tools/raw_to_spec.py \
  --input "output/scenarios/{FACILITY}_{FLOW}/sheet1_input.csv" \
  --facility "{FACILITY}" --flow "{FLOW}"
```

🔴 未認識アイテムが出た場合:
- ユーザーに「{item} はどのブロックタイプですか？」と確認
- `tools/normalize_dictionary.json` に追加（repo 改善）
- 再実行

## Phase 4 — YAML 生成

```bash
bash tools/run_csv_to_yaml.sh "{FACILITY}" "{FLOW}"
```

エラー発生時の診断:

**DATA 問題**（CSV 記入漏れ・値の誤り）:
- 該当 CSV の該当行を修正
- 再実行

**TOOL 問題**（`csv_to_yaml.py` のバグ・未対応ブロック）:
- 修正案をユーザーに提示
- 承認後 → `tools/csv_to_yaml.py` を修正
- インシデントメモを `docs/incidents/` に記録
- commit してから再実行

最大3回リトライ。同じエラーが繰り返す場合は人間にエスカレーション。

## Phase 5 — QA バリデーション

```bash
python3 schemas/qa_validator.py "output/scenarios/{FACILITY}_{FLOW}/設計書_{FACILITY}_{FLOW}.yaml"
```

`fix_category="auto"` の CRITICAL:
```bash
python3 schemas/yaml_auto_fixer.py ...
```

残存 CRITICAL → ユーザーに報告して壁打ちで解消（自律修復しない）。

## Phase 6 — Commit & 完了報告

```
✅ 完了!

出力: output/scenarios/{FACILITY}_{FLOW}/設計書_{FACILITY}_{FLOW}.yaml

次のステップ:
  orchestrator で BIVR ビルド:
  python3 scripts/orchestrator.py --pattern 1 \
    --spec "output/scenarios/{FACILITY}_{FLOW}/設計書_{FACILITY}_{FLOW}.yaml"

repo 改善コミット（あれば）:
  - normalize_dictionary.json への追加: X 件
  - csv_to_yaml.py の修正: Y 件
```

---

## 原則

- **生成物でなく生成器を直す**: エラーは CSV でなくツール側を直すことを優先
- **エラーは1回だけ**: ツール修正は必ず commit して再発防止
- **自律修復しない**: CRITICAL 残存・ビジネスロジック判断は人間へ
- **TTS・routing logic は人間が最終確認**: Claude は提案のみ
