# Entity Classification Summary — 多根クリニック / 健診

対象 yaml: 9 本

  - `【037】多根クリニック/【000多根クリニック】健診1_M_本番/main.yaml`
  - `【037】多根クリニック/【000多根クリニック】健診1_M_本番/予約日聴取.yaml`
  - `【037】多根クリニック/【000多根クリニック】健診1_M_本番/企業or個人.yaml`
  - `【037】多根クリニック/【000多根クリニック】健診1_M_本番/受診希望日.yaml`
  - `【037】多根クリニック/【000多根クリニック】健診1_M_本番/変更orキャンセル.yaml`
  - `【037】多根クリニック/【000多根クリニック】健診1_M_本番/生年月日.yaml`
  - `【037】多根クリニック/【000多根クリニック】健診1_M_本番/用件.yaml`
  - `【037】多根クリニック/【000多根クリニック】健診1_M_本番/紹介状_受診結果.yaml`
  - `【037】多根クリニック/【000多根クリニック】健診1_M_本番/電話番号聴取.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 48 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 65 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 37 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 160 | OpenAI 正規化 |

## 詳細 (entity 単位)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### 予約キャンセル
- STT: 3 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `予約キャンセル`

### 予約以外
- STT: 4 surfaces, OpenAI: 18 surfaces
- STT サンプル:
  - `アクセス` (R3_STT_KANA_VARIANT)
  - `くすり` (R3_STT_KANA_VARIANT)
  - `じゃない` (R3_STT_KANA_VARIANT)
  - `ではない` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `予約以外`
  - `お見舞い`
  - `違い`
  - `違う`
  - `飲み方`

### 予約変更
- STT: 2 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `別の` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `変更` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `予約変更`
  - `時間`
  - `日程`
  - `日付`
  - `変え`

### 予約確認
- STT: 6 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `その他` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `なくした` (R3_STT_KANA_VARIANT)
  - `確認` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `忘れた` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `問い合わせ` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `予約確認`
  - `教えて`
  - `調べて`
  - `分からない`
  - `分からん`

### 分からない
- STT: 5 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ません` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `持っていない` (R2_STT_TEMPLATE_REUSE → hearing_phone_number)
- OpenAI サンプル:
  - `分からない`
  - `解らない`
  - `持ってない`
  - `動かない`
  - `分かりません`

### 初めて
- STT: 2 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `初めて` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はじめて` (R3_STT_KANA_VARIANT)

### 別の
- STT: 2 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `別の` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `変更` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `違う`
  - `携帯`
  - `他の`
  - `変え`

### 否定
- STT: 12 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いらない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いりません` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `ちがう`
  - `ちゃうちゃう`
  - `まちがった`
  - `否定`

### 否定単語
- STT: 4 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `違います` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ダメ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ノー` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `違い`
  - `違う`
  - `違って`
  - `駄目`

### 変更内容
- STT: 0 surfaces, OpenAI: 7 surfaces
- OpenAI サンプル:
  - `受診結果`
  - `結果`
  - `質問`
  - `紹介状`
  - `照会状`

### 定期受診
- STT: 1 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `循環器` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
- OpenAI サンプル:
  - `定期受診`
  - `受診予約`
  - `定期`

### 持ってない
- STT: 7 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `いない` (R3_STT_KANA_VARIANT)
  - `いませーん` (R3_STT_KANA_VARIANT)
  - `いません` (R3_STT_KANA_VARIANT)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `もってない` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `持ってない`
  - `以てない`
  - `持ってませーん`
  - `持ってません`
  - `盛ってない`

### 新規予約
- STT: 2 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `新規予約` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `初診` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `健診の予約`
  - `健診予約`
  - `取りたい`
  - `取得`
  - `紹介状`

### 日にちのみ
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `日にちのみ`

### 用件
- STT: 36 surfaces, OpenAI: 79 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `予約のキャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `2番`
  - `取り消す`
  - `二`
  - `二番`
  - `予約キャンセル`

### 肯定
- STT: 5 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうそう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はーい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `配送です`
  - `肯定`
  - `異常部`
  - `丈夫`
  - `大丈夫`

### 肯定単語
- STT: 11 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `OK` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `あっています` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってる` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `違いありません`
  - `違いない`
  - `大丈夫`
  - `問題ありません`
  - `問題ない`

### 診療科
- STT: 48 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `IVRセンター` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `アレルギー科` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `オンコロジー` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `セカンドオピニオン` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `フット外来` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
