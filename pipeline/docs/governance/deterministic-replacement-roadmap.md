# OpenAI プロンプト層 → 決定論 module/script 置き換えロードマップ

**方針（2026-06-04 確定）**: OpenAI プロンプトで解いている判定を、受入テスト通過済みの
module / script へ置き換えていく。LLM に残すのは決定論で書けない「自由発話の解釈」のみ。
DoD は CLAUDE.md「モジュール / script 開発ポリシー」、認定台帳は `modules/README.md`。

## なぜ今やるか

- **受入テスト体制が確立した**: Pattern 6（OpenAI/STT 不要のテストフロー）+ Python オラクル + 実機受入の 3 点セット
- **実績 3 件**: DOB 復唱 / BusinessHour Classifier / 現在の予約日 script — いずれも「LLM 判定 → テスト済み決定論」の置き換えに成功
- LLM 判定は temp 0.01 でも出力が揺れ、Few-Shot 追加で壊れる実績もある。決定論部品は受入テストで品質を**固定**できる

## SKILL カテゴリ別の置換可否

| SKILL | 用途 | 置換可否 | 置換先候補 | 優先度 |
|---|---|---|---|---|
| B Yes/No | はい/いいえ判定（scaffold 固定プロンプト埋込） | ◎ | 類義語辞書マッチ + CMR/script。発話データは extract-yesno-synonyms で蓄積中（2026-04 分で 73+76 ユニーク発話） | **1** |
| C date | 日付聴取・正規化（addCurrentDate 前提の相対日付解決） | ◎ | 現在の予約日 script 系譜（439/439 実績）+ BusinessHour Classifier | **2** |
| F phone / D の番号系 | 電話番号・診察券番号の正規化 | ○ | 桁数・形式チェック script | 3 |
| D の氏名カナ | 氏名の聞き取り正規化 | △ | 当面 LLM 残留（STT 揺れの吸収が本質的に曖昧） | — |
| A 分類 | 自由発話の用件分類 | △ | 当面 LLM 残留。固定語彙に近い分類はエンティティ類義語辞書で吸収を検討 | — |
| E freetext | 自由テキスト収集 | — | 判定なし・収集のみで置換対象外 | — |

> 置換可否は現時点の見立て。**初手は頻度実測**（下記）で優先度を裏取りする。

## 進め方（1 部品あたり）

1. **頻度実測**（初回のみ全体マップ）: 既存シナリオの generate_by_OpenAI を SKILL カテゴリ別に集計し、置換インパクトを数字で確認
2. `REQUIREMENTS.md` 起草 → Python オラクル（`oracle.py` + `test_oracle.py`）
3. Pattern 6 受入 bivr で実機 PASS（220 ケース/bivr 目安、超過時は part 分割）
4. `modules/README.md` 認定レジストリへ登録
5. scaffold builder 切替（`build_openai` → script ブロック / 新 builder）— **新規シナリオから適用**
6. 既存施設は世代変更・改修のタイミングで段階移行（一斉置換はしない）

## 完了済み

| 部品 | 置き換えた判定 | テスト | 残タスク |
|---|---|---|---|
| DOB Re-confirmation | 生年月日復唱（openAI_prompt 削除） | oracle 44/47 + デプロイ JS バイト一致 | 正本のリポジトリ収容 |
| BusinessHour Classifier | 営業時間 + 祝日 + 固定休（6 分岐） | oracle 26/26 + 実機 26/26 | — |
| 現在の予約日 script | 相対日付解決 | 439/439 + Part 3 | 正本のリポジトリ収容 + **本番 現在の予約日.txt への反映** |

## ガバナンスとの関係

- `modules/` `scripts/` は保護ゾーン（CONTRIBUTING.md）。新部品 PR のレビュー観点 = **受入テスト証跡の確認**（オラクル結果 + 実機結果が PR に含まれているか）
- 認定済み部品の改変は 1 文字でも再受入。テンプレのままの利用は再テスト不要
