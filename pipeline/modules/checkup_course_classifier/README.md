# checkup_course_classifier — 健診CC コース 決定論分類器

ヘルスケアクリニック厚木 統合CC（6 施設共通）の「コース選択」(n6) と「その他コース確認」(-6) の
generate_by_OpenAI を置き換える決定論 Script。仕様: `REQUIREMENTS.md`。

## 使い方

1. `script.js` を @General$Script モジュールとして配置（n6 用 / -6 用の 2 インスタンス）。
2. 先頭の設定行 `var SOURCE_MODULE = "__SOURCE_MODULE__";` を入力 STT モジュール名に差し替える
   （**この 1 行のみインスタンスパラメータ**）。
3. 出力 6 値: 人間ドック / 協会けんぽ / 定期健診 / 雇用時健診 / その他の健診 / NO_RESULT。
   -6 では ^雇用時健診$ のみ専用配線、他は default で氏名へ（course 生テキストは STT 側 save2db で保存）。

## 判定方式

正規化（checkup_intent_classifier と同一＋健診畳み込み）→ 空 / DTMF(1-4) /
わからない検知（→**その他の健診**。-6 の誘導文言と整合）→ カテゴリ優先順位走査:
雇用時健診 > 協会けんぽ > 定期健診 > その他の健診明示語 > 人間ドック → 総称「健診」受け皿。
特定健診・市の健診は n6 ではその他の健診へ（受付不可案内は n4 の責務、折返しでスタッフが案内）。

## テスト（テストが正）

- 期待値 SSoT: `acceptance_test/cases.tsv`（51 ケース。旧要件定義コース正規化 18 語彙＋合成エッジ）
- オラクル受入: `python test_oracle.py` → **51/51 PASS（2026-06-10）**
- Brekeke 実機受入（Pattern 6 単体）: 未実施
- 実発話回帰: 稼働後に Brekeke ログから月次採取して追補
