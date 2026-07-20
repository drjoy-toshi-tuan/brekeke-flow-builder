# field_presence — L1 答え取得判定モジュール 要件

## 目的
商談デモ「フリー発話受付」の各聴取 STT 直後に置く **L1（答え取得判定）**。
入力 STT テキストに「当該フィールドの答え」が含まれるかを kind 別に判定し、
`PRESENT` / `ABSENT` を返す。背後の雑音（質問など）が混ざっていても、
当該フィールドの答えがあれば `PRESENT`（＝答え優先で先へ進める）。

下流カスケード（各聴取の入力ゲート）:
```
入力_X(STT) → L1_X(field_presence) → 分岐_L1_X(CMR):
    PRESENT(^0$ other) → 当該聴取の通常処理（次ステップ）
    ABSENT             → L0_X(go_back_classifier) → FAQ_X(faq_matcher)
```

## 入出力
- 入力: `getModuleResult({{INPUT_MODULE}})`（本番）または保存 context `{{CONTEXT_FIELD}}`（優先）。
- パラメータ: `{{KIND}}` ∈ `department | date | phone | birthday | card`。
- 出力（`$runner.setResult`）: `PRESENT` または `ABSENT`。

## 判定ロジック（kind 別）
| kind | PRESENT 条件 |
|---|---|
| department | 診療科辞書（inquiry_extractor / field_normalizer と同一・longest-match）が当たる |
| date | 相対日キーワード（来週/明日/…）or 「N月」「N日」「N年」パターン |
| phone | `0\d{9,10}` を含む（全角→半角・区切り除去後） |
| birthday | 和暦/西暦の「YYYY年M月D日」型 |
| card | `\d{3,10}` を含む、または no-card 表明（持っていない/ありません/わかりません/不明/なし 等）|

- `card` の no-card 表明も `PRESENT`＝「カード無し」で先へ進める（聴取プロンプトが「お持ちでない場合はその旨」を許容するため）。
- `name` 等の未対応 kind は常に `ABSENT`（氏名は L1 対象外＝FAQ のみの素ルーターを使う）。

## 対象外（設計判断）
- **氏名**: 「名前か質問か」を確実に判定する手段が無いため L1 を置かない（FAQ のみ）。
- **用件確認**: yes_no_classifier（既存）が L1 相当。
- **用件フリー聴取**: inquiry_extractor（既存 用件抽出）が L1 相当。

## 正本・parity
- Python オラクル: `modules/field_presence/oracle.py`
- JS テンプレート（正本）: `docs/brekeke/script_templates/field_presence.js`（Nashorn ES5.1・同一辞書/同一手順）
- 検出辞書は inquiry_extractor（診療科・相対日）/ field_normalizer（電話/生年月日/診察券）の正本と整合。

## DoD 進捗
1. REQUIREMENTS.md — 本書 ✅
2. Python オラクル + test_oracle.py — **33/33 PASS** ✅
3. Brekeke 実機受入（Pattern 6） — ✅ **32/32 PASS**（2026-06-17・call 09065765660・5 KIND・`[TEST FAIL]` 0・`終了:OK`）
4. オラクル↔Nashorn パリティ確認 — ✅ 全32一致（実機 clf 出力 == oracle 期待）
5. `modules/README.md` 認定登録 — ✅ 登録済（2026-06-17）
