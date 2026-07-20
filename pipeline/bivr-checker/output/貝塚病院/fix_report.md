# 仕上げレポート: 貝塚病院

## 概要

| 項目 | 値 |
|------|-----|
| 施設名 | 貝塚病院 |
| フロー数 | 5 |
| 総モジュール数 | 310 |
| STT/DTMFモジュール数 | 50 |
| OpenAIモジュール数 | 19 |
| 品質スコア | 55.8/100 |
| 判定 | FAIL |

### フロー一覧

1. `貝塚病院$健診` (136モジュール)
2. `貝塚病院$健診_20260417` (136モジュール)
3. `貝塚病院$氏名聴取_20260417` (5モジュール)
4. `貝塚病院$生年月日聴取_20260417` (10モジュール)
5. `貝塚病院$電話番号聴取_20260417` (23モジュール)

## Stage別修正サマリー

### Stage 1: 構造修正

*修正ログなし -- 現在の状態を表示*

- Retry Counter: 50個 (prompt_false設定済み: 44個)
- TTSモジュール: 67個

### Stage 2: profile_words

| モジュール | 語数 | ステータス |
|-----------|------|----------|
| 入力_冒頭確認 | 7 | 不足 |
| 入力_個人or企業 | 0 | EMPTY |
| 入力_本人確認 | 0 | EMPTY |
| 入力_入電者氏名 | 0 | EMPTY |
| 入力_用件確認 | 8 | 不足 |
| 入力_受診歴 | 4 | 不足 |
| 入力_受診内容 | 6 | 不足 |
| 入力_受診希望時期 | 0 | EMPTY |
| 入力_受診希望時期_雇入 | 0 | EMPTY |
| 入力_連絡事項 | 0 | EMPTY |
| 入力_予約日_変更 | 0 | EMPTY |
| 入力_変更内容 | 5 | 不足 |
| 入力_希望時期_変更 | 0 | EMPTY |
| 入力_その他変更内容 | 0 | EMPTY |
| 入力_予約日_キャンセル | 0 | EMPTY |
| 入力_受診内容_キャンセル | 0 | EMPTY |
| 入力_連絡事項_キャンセル | 0 | EMPTY |
| 入力_問い合わせ内容 | 0 | EMPTY |
| 入力_企業_用件確認 | 0 | EMPTY |
| 入力_担当者名 | 0 | EMPTY |
| 入力_企業_団体名 | 0 | EMPTY |
| 入力_企業_用件 | 0 | EMPTY |
| 入力_冒頭確認 | 7 | 不足 |
| 入力_個人or企業 | 0 | EMPTY |
| 入力_本人確認 | 0 | EMPTY |
| 入力_入電者氏名 | 0 | EMPTY |
| 入力_用件確認 | 8 | 不足 |
| 入力_受診歴 | 4 | 不足 |
| 入力_受診内容 | 6 | 不足 |
| 入力_受診希望時期 | 0 | EMPTY |
| 入力_受診希望時期_雇入 | 0 | EMPTY |
| 入力_連絡事項 | 0 | EMPTY |
| 入力_予約日_変更 | 0 | EMPTY |
| 入力_変更内容 | 5 | 不足 |
| 入力_希望時期_変更 | 0 | EMPTY |
| 入力_その他変更内容 | 0 | EMPTY |
| 入力_予約日_キャンセル | 0 | EMPTY |
| 入力_受診内容_キャンセル | 0 | EMPTY |
| 入力_連絡事項_キャンセル | 0 | EMPTY |
| 入力_問い合わせ内容 | 0 | EMPTY |
| 入力_企業_用件確認 | 0 | EMPTY |
| 入力_担当者名 | 0 | EMPTY |
| 入力_企業_団体名 | 0 | EMPTY |
| 入力_企業_用件 | 0 | EMPTY |
| 入力_患者_氏名 | 609 | 過多 |
| 入力_患者_生年月日 | 0 | EMPTY |
| 入力_復唱_患者生年月日 | 3 | 不足 |
| 入力_患者_携帯電話 | 0 | EMPTY |
| 入力_患者_復唱連絡先 | 0 | EMPTY |
| 入力_患者_連絡先 | 0 | EMPTY |

### Stage 3: OpenAIプロンプト

| モジュール | 文字数 | Role | Context | セキュリティ | Few-Shot | NO_RESULT |
|-----------|--------|------|---------|------------|---------|-----------|
| OpenAI_冒頭確認 | 0 | x | x | x | x | x |
| OpenAI_個人or企業 | 0 | x | x | x | x | x |
| OpenAI_本人確認 | 0 | x | x | x | x | x |
| OpenAI_用件確認 | 0 | x | x | x | x | x |
| OpenAI_受診歴 | 0 | x | x | x | x | x |
| OpenAI_受診内容 | 0 | x | x | x | x | x |
| OpenAI_変更内容 | 0 | x | x | x | x | x |
| OpenAI_企業_用件確認 | 0 | x | x | x | x | x |
| OpenAI_冒頭確認 | 974 | o | o | o | x | o |
| OpenAI_個人or企業 | 979 | o | o | o | o | o |
| OpenAI_本人確認 | 958 | o | o | o | x | o |
| OpenAI_用件確認 | 1584 | o | o | o | o | o |
| OpenAI_受診歴 | 985 | o | o | o | x | o |
| OpenAI_受診内容 | 1005 | o | o | o | o | o |
| OpenAI_変更内容 | 996 | o | o | o | x | o |
| OpenAI_企業_用件確認 | 962 | o | o | o | x | o |
| openAI_復唱_患者生年月日 | 887 | x | x | x | o | o |
| openAI_患者_復唱連絡先 | 887 | x | x | x | o | o |
| openAI_患者_携帯電話 | 875 | x | x | x | o | o |

### Stage 4: Property.md

*修正ログなし*

## 品質検証詳細

### A. profile_words (6.0/40)

| チェック項目 | 結果 | スコア |
|------------|------|--------|
| 空モジュール | FAIL 21件 | 0/10 |
| 語数範囲(50-300) | WARN 0/7 | 0.0/10 |
| フィラーTOP6含有 | WARN 2/24 (8.3%) | 1.0/10 |
| 頭切れ含有 | WARN 0/24 (0.0%) | 0.0/5 |
| 「まー」不在 | OK 0件 | 5/5 |

### B. OpenAIプロンプト (30.9/40)

| チェック項目 | 結果 | スコア |
|------------|------|--------|
| # Role | FAIL 8/11 (72.7%) | 5.8/8 |
| # Context | FAIL 8/11 (72.7%) | 5.8/8 |
| セキュリティ | FAIL 8/11 (72.7%) | 5.8/8 |
| 文字数500+ | OK 11/11 (100.0%) | 4/4 |
| Few-Shot | WARN 6/11 (54.5%) | 5.5/8 |
| NO_RESULT | OK 11/11 (100.0%) | 4/4 |

### C. 構造 (18.9/20)

| チェック項目 | 結果 | スコア |
|------------|------|--------|
| CRITICAL | OK 0件 | 10/10 |
| prompt_false非空 | WARN 22/28 | 3.9/5 |
| TTS label | OK 35/35 | 5.0/5 |

## 残存警告

| 重要度 | 内容 |
|--------|------|
| WARNING | profile_words 不足 (7語): 入力_冒頭確認 |
| WARNING | profile_words 空: 入力_個人or企業 |
| WARNING | profile_words 空: 入力_本人確認 |
| WARNING | profile_words 空: 入力_入電者氏名 |
| WARNING | profile_words 不足 (8語): 入力_用件確認 |
| WARNING | profile_words 不足 (4語): 入力_受診歴 |
| WARNING | profile_words 不足 (6語): 入力_受診内容 |
| WARNING | profile_words 空: 入力_受診希望時期 |
| WARNING | profile_words 空: 入力_受診希望時期_雇入 |
| WARNING | profile_words 空: 入力_連絡事項 |
| WARNING | profile_words 空: 入力_予約日_変更 |
| WARNING | profile_words 不足 (5語): 入力_変更内容 |
| WARNING | profile_words 空: 入力_希望時期_変更 |
| WARNING | profile_words 空: 入力_その他変更内容 |
| WARNING | profile_words 空: 入力_予約日_キャンセル |
| WARNING | profile_words 空: 入力_受診内容_キャンセル |
| WARNING | profile_words 空: 入力_連絡事項_キャンセル |
| WARNING | profile_words 空: 入力_問い合わせ内容 |
| WARNING | profile_words 空: 入力_企業_用件確認 |
| WARNING | profile_words 空: 入力_担当者名 |
| WARNING | profile_words 空: 入力_企業_団体名 |
| WARNING | profile_words 空: 入力_企業_用件 |
| WARNING | profile_words 不足 (7語): 入力_冒頭確認 |
| WARNING | profile_words 空: 入力_個人or企業 |
| WARNING | profile_words 空: 入力_本人確認 |
| WARNING | profile_words 空: 入力_入電者氏名 |
| WARNING | profile_words 不足 (8語): 入力_用件確認 |
| WARNING | profile_words 不足 (4語): 入力_受診歴 |
| WARNING | profile_words 不足 (6語): 入力_受診内容 |
| WARNING | profile_words 空: 入力_受診希望時期 |
| WARNING | profile_words 空: 入力_受診希望時期_雇入 |
| WARNING | profile_words 空: 入力_連絡事項 |
| WARNING | profile_words 空: 入力_予約日_変更 |
| WARNING | profile_words 不足 (5語): 入力_変更内容 |
| WARNING | profile_words 空: 入力_希望時期_変更 |
| WARNING | profile_words 空: 入力_その他変更内容 |
| WARNING | profile_words 空: 入力_予約日_キャンセル |
| WARNING | profile_words 空: 入力_受診内容_キャンセル |
| WARNING | profile_words 空: 入力_連絡事項_キャンセル |
| WARNING | profile_words 空: 入力_問い合わせ内容 |
| WARNING | profile_words 空: 入力_企業_用件確認 |
| WARNING | profile_words 空: 入力_担当者名 |
| WARNING | profile_words 空: 入力_企業_団体名 |
| WARNING | profile_words 空: 入力_企業_用件 |
| WARNING | profile_words 過多 (609語): 入力_患者_氏名 |
| WARNING | profile_words 空: 入力_患者_生年月日 |
| WARNING | profile_words 不足 (3語): 入力_復唱_患者生年月日 |
| WARNING | profile_words 空: 入力_患者_携帯電話 |
| WARNING | profile_words 空: 入力_患者_復唱連絡先 |
| WARNING | profile_words 空: 入力_患者_連絡先 |
| CRITICAL | OpenAIプロンプト空: OpenAI_冒頭確認 |
| CRITICAL | OpenAIプロンプト空: OpenAI_個人or企業 |
| CRITICAL | OpenAIプロンプト空: OpenAI_本人確認 |
| CRITICAL | OpenAIプロンプト空: OpenAI_用件確認 |
| CRITICAL | OpenAIプロンプト空: OpenAI_受診歴 |
| CRITICAL | OpenAIプロンプト空: OpenAI_受診内容 |
| CRITICAL | OpenAIプロンプト空: OpenAI_変更内容 |
| CRITICAL | OpenAIプロンプト空: OpenAI_企業_用件確認 |

## 出力ファイル

- `貝塚病院_健診_20260417_fixed.bivr`
