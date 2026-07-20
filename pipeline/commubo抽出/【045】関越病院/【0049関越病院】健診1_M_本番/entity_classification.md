# Entity Classification Summary — 関越病院 / 健診

対象 yaml: 10 本

  - `【045】関越病院/【0049関越病院】健診1_M_本番/main.yaml`
  - `【045】関越病院/【0049関越病院】健診1_M_本番/予約希望_人数.yaml`
  - `【045】関越病院/【0049関越病院】健診1_M_本番/内容or日程orキャンセル 判別.yaml`
  - `【045】関越病院/【0049関越病院】健診1_M_本番/変更内容または時期 詳細.yaml`
  - `【045】関越病院/【0049関越病院】健診1_M_本番/希望コース.yaml`
  - `【045】関越病院/【0049関越病院】健診1_M_本番/当日予約判別.yaml`
  - `【045】関越病院/【0049関越病院】健診1_M_本番/現在の予約日.yaml`
  - `【045】関越病院/【0049関越病院】健診1_M_本番/生年月日聴取.yaml`
  - `【045】関越病院/【0049関越病院】健診1_M_本番/用件聞き取り.yaml`
  - `【045】関越病院/【0049関越病院】健診1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 83 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 63 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 72 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 205 | OpenAI 正規化 |

## 詳細 (entity 単位)

### もう一度
- STT: 8 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `まって` (R3_STT_KANA_VARIANT)
  - `もいちど` (R3_STT_KANA_VARIANT)
  - `もういっかい` (R3_STT_KANA_VARIANT)
  - `もーいちど` (R3_STT_KANA_VARIANT)
  - `もっかい` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `もう一度`
  - `もう一_回`
  - `もう一回`
  - `再度`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### コース
- STT: 28 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `一般健診` (R1_STT_PROPER_NOUN_GROUP)
  - `3` (R1_STT_PROPER_NOUN_GROUP)
  - `3番` (R1_STT_PROPER_NOUN_GROUP)
  - `一般` (R1_STT_PROPER_NOUN_GROUP)
  - `健保` (R1_STT_PROPER_NOUN_GROUP)

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
- STT: 13 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ちがいまーす` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `違いまーす`
  - `間違えた`
  - `いーえ`
  - `まちがった`

### 否定単語
- STT: 7 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `違います` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `違い`
  - `違う`
  - `違って`
  - `駄目`

### 変更内容
- STT: 12 surfaces, OpenAI: 57 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `予約のキャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `3`
  - `3番`
  - `三`
  - `三番`
  - `取り消す`

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

### 決まっている
- STT: 4 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `いまーす` (R3_STT_KANA_VARIANT)
  - `います` (R3_STT_KANA_VARIANT)
  - `いる` (R3_STT_KANA_VARIANT)
  - `もう` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `決まっている`
  - `決まっていまーす`
  - `決まってまーす`
  - `決まってます`

### 決まってない
- STT: 5 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `いない` (R3_STT_KANA_VARIANT)
  - `いませーん` (R3_STT_KANA_VARIANT)
  - `いません` (R3_STT_KANA_VARIANT)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `まだ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `決まってない`
  - `決まっていません`
  - `決まってませーん`
  - `決まってません`

### 用件
- STT: 29 surfaces, OpenAI: 51 surfaces
- STT サンプル:
  - `その他` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `さん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `さんばん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `サンバン` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `そのほか` (R3_STT_KANA_VARIANT → hearing_yoken_common)
- OpenAI サンプル:
  - `3`
  - `お問い`
  - `教えて`
  - `三`
  - `三番`

### 肯定
- STT: 14 surfaces, OpenAI: 14 surfaces
- STT サンプル:
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうでーす` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってる` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`
  - `その通りです`
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

### 胃がん、乳がん健診
- STT: 7 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `胃がん健診` (R1_STT_PROPER_NOUN_GROUP)
  - `イオン現振` (R1_STT_PROPER_NOUN_GROUP)
  - `胃がん` (R1_STT_PROPER_NOUN_GROUP)
  - `胃癌` (R1_STT_PROPER_NOUN_GROUP)
  - `乳がん検診` (R1_STT_PROPER_NOUN_GROUP)

### 診療科
- STT: 48 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `IVRセンター` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `アレルギー科` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `オンコロジー` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `セカンドオピニオン` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `フット外来` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
