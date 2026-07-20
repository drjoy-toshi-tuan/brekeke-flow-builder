---
name: script-gen
description: 新規シナリオで「既存の決定論資産（認定部品 / script_templates / キーワードプリセット）ではカバーできない新しい分類・判定」が出てきたときに、LLM が壁打ち（ライン外）で新スクリプト・新語彙を検証つきで起草するスキル。再利用可否の判定 → 語彙起草 → テストケース生成 → eval ハーネス PASS → PR まで一気通貫。パイプライン内の自動修復には使わない（keystone＝ライン内 LLM ゼロ）。プロジェクトローカル skill。
---

# script-gen — 新規判定ロジックの壁打ち起草（ライン外 LLM）

## 目的と位置づけ

決定論スクリプト（intent / enum 分類・日付判定 等）の語彙・テンプレートは
マスターファイル群に集約されている。しかし**新規シナリオには既存データが
カバーしない新しい判定**（新しい聴取軸・新しい言い回し・新しいカレンダー規則）が
必ず出てくる。

このスキルの仕事は、その「未カバー分」を LLM の言語知識で埋めることだが、
**成果物は LLM の判断そのものではなく、機械が再現・検証できるデータ**である:

> 生成物（スクリプト本体）を直接書くのではなく、**生成器の入力（マスターファイル）を
> 拡張し、評価ハーネスの PASS で品質を証明してから** PR に載せる。

- 実行場所: **壁打ち（人間 + Claude Code）のみ**。orchestrator / パイプラインからは呼ばない
- LLM の役割: 語彙の提案・意地悪ケースの発想・再利用判断の下調べ
- 機械の役割: 分類の再現（生成スクリプト）と検証（eval ハーネス）
- 人間の役割: PR レビュー（保護ゾーン）と P6 実機受入（初回投入時）

## 起動時の入力

1. **ブロック要件**: TTS 質問文・分岐クラス（期待ラベル一覧）・保存先 context・flow_type
2. **サンプル発話**（あれば）: customer_doc の記載・実ログ抜粋・ユーザーの口頭例
3. **施設名 / シナリオ名**（成果物の配置と PR 記述用）

## ステップ 0 — 再利用チェック（新規起草より先に必ずやる）

新しく作る前に、既存資産で組めないかを**この順で**確認する:

| 順 | 資産 | 確認先 | 使えるケース |
|---|---|---|---|
| 1 | 認定部品 | `modules/parts_catalog.json` / `modules/README.md` 認定台帳 | yes_no_classifier（純ポーラ二択）/ n_choice（可変語彙の択一・施設 spec 著作）/ checkup_intent・course・menu_classifier / dob・phone normalizer / department_classifier 等 |
| 2 | script テンプレート | `docs/brekeke/script_templates/README.md` | 日付・期間系（closed_period / same_day_check / date_range_check / future_date / business_hour_classifier）・固定値保存（set_context）・多段グループ（condition_group） |
| 3 | キーワードプリセット | `docs/amivoice/keyword_presets.yaml` | 用件（yoken_*）/ 初診再診・初回リピーター / あり・なし / 希望する・しない / 変更内容 / 個人・企業 / 被保険者区分 / 性別 / 午前午後 等 — intent ブロックの `preset:` で参照 |

**二択の使い分け（重要）**: はい/いいえで答えられる問い（polar）は
**yes_no_classifier 一択**（質問文の極性に依存するため enum 語彙で組んではならない）。
「本人/家族」「検査/診察」のように中身の語彙が選択肢ごとに可変な二択は n_choice。

既存資産で組めるなら**このスキルの仕事はここで終わり**（設計書に部品/テンプレ/preset を
書く方法を提示して閉じる）。

## ステップ 1 — 新語彙の起草（LLM の主担当）

既存プリセットに無い分類軸、または既存プリセットが発話を取りこぼす場合:

1. クラスごとに**判別力のある語幹**を提案する。ガードルール:
   - **polar 回答（はい/いいえ/あります/ありません/大丈夫です）を enum プリセットに入れない**
   - 多義語（結構です・大丈夫です 等、肯定にも辞退にも使われる語）は入れる場合 note に文脈条件を明記
   - 「お願いします」等の全クラス共通の汎用語は入れない
   - 助詞ゆれを吸収する語幹形にする（例: 「通ったことがあ」ではなく「通ったこと」）
   - 表記はそのままで良い（カタカナ→ひらがな等の正規化はビルド時に自動適用される）
2. `docs/amivoice/keyword_presets.yaml` に新プリセット（または既存への追記）として書く。
   `note:` に対象 TTS 質問文の例と注意点を必ず書く。

## ステップ 2 — テストケースの生成（正例＋意地悪）

語彙と同時にテストデータを増やす（語彙だけ増やして検証しないのは禁止）:

1. **正例**: `docs/testcase_master/keyword_bank.yaml` に新しい発話を追加し、
   `python3 tools/gen_master_cases.py --write ...` で master CSV にケース化する
   （フィラー値・ID 採番・多様性 invariant はツールが保証する。手で CSV を書かない）
2. **意地悪ケース**: 言い直し（「AじゃなくてB」）・否定・2 意図混在・REPEAT 境界・
   かな/カタカナゆれを `docs/testcase_master/intent_adversarial_cases.tsv` に追加。
   語彙で解けない文脈限界は `must_pass=no` + note で明文化する（隠さない）

## ステップ 3 — 機械評価（PASS するまで語彙を往復）

```bash
python3 tools/eval_intent_script.py            # 用件 + 登録済み軸 + 敵対ケース
```

- 新しい分類軸を常設評価に載せる場合は `tools/eval_intent_script.py` の `AXES` に
  (列, flow_type, クラス→preset) を追加する
- 施設固有の options 構成を試すだけなら `--options <yaml>` で ad-hoc 評価できる
- **RESULT: PASS になるまで語彙を調整**する。誤マッチ（別クラスが勝つ）が出たら
  タイブレーク（同点は後方出現優先）を踏まえて語幹を見直す

## ステップ 4 — 出口

1. **PR を作る**（keyword_presets.yaml / keyword_bank.yaml / master CSV /
   adversarial TSV / AXES 追記 — いずれも保護ゾーンなのでレビュー必須）。
   PR には eval ハーネスの実行結果（PASS）を貼る
2. 設計書 YAML では `preset:` 参照で使う（キーワードの手書き複製をしない）
3. **キーワードでは書けない新エンジン**（新しい判定アルゴリズム）が必要な場合は
   本スキルの範囲を超える → `docs/brekeke/script_templates/` の新テンプレ起草
   （oracle テスト必須、`tests/` 参照）または `@工場長` の部品調達フロー
   （`tools/new_part_skeleton.py`）へ引き継ぐ
4. **P6 実機受入は人間ゲート**: 生成 JS のエンジン・語彙が変わる初回投入時は
   ポリシーどおり実機受入を通す（`docs/governance/part-certification-spec.md`）

## 禁止事項

- パイプライン（orchestrator）内から本スキルを自動起動しない（keystone: ライン内 LLM ゼロ）
- `modules/certified_hashes.json` への追記（認定宣言）を LLM が行わない — 認定は人間ゲート
- eval ハーネス PASS の証跡なしに語彙・ケースを PR に載せない
- polar 回答の enum 化（上記ガード）
- 決定論で書ける判定を OpenAI プロンプトへ逃がす判断を単独でしない
  （`docs/governance/deterministic-replacement-roadmap.md` の方針に従い壁打ちで決める）
