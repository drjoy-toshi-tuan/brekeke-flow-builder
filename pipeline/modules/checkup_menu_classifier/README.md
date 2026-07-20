# checkup_menu_classifier — 健診CC メニュー選択 決定論分類器

ヘルスケアクリニック厚木 統合CC の「エリア選択」「施設選択_新宿渋谷」「施設選択_東京品川」の
generate_by_OpenAI を置き換える決定論 Script。**1 script に 3 メニュー内蔵**、設定行 `MENU` で切替。
仕様: `REQUIREMENTS.md`。

## 使い方

1. `script.js` を @General$Script モジュールとして配置（3 インスタンス）。
2. 設定行を差し替え: `SOURCE_MODULE`（入力 STT モジュール名）と `MENU`
   （`area` / `shinjuku_shibuya` / `tokyo_shinagawa`）。**この 2 行のみインスタンスパラメータ**。
3. 出力は設計書 enum ラベル（神奈川エリア／ヒロオカクリニック等）。NO_RESULT → リトライ。

## 判定方式

正規化 → 空 / DTMF（MENU 別表）/ わからない検知 → MENU 別語彙走査（施設名→地名の定義順）。
DTMF 指定の質問だが発話回答も救う（「厚木」→神奈川エリア等）。

## テスト（テストが正）

- 期待値 SSoT: `acceptance_test/cases.tsv`（41 ケース、3 メニュー混載）
- オラクル受入: `python test_oracle.py` → **41/41 PASS（2026-06-10）**
- Brekeke 実機受入（Pattern 6 単体）: 未実施
