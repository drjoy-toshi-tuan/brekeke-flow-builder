# Entity Classification Summary — 中頭病院 / 診療

対象 yaml: 13 本

  - `【026】中頭病院｜【027】ちばなクリニック/【0025ちばなクリニック】診療1_M_本番/main.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0025ちばなクリニック】診療1_M_本番/WEB確認案内.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0025ちばなクリニック】診療1_M_本番/予約希望日1，2まとめて聴取.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0025ちばなクリニック】診療1_M_本番/予約日の聞き取り.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0025ちばなクリニック】診療1_M_本番/当日手術Y_N.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0025ちばなクリニック】診療1_M_本番/当日検査Y_N.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0025ちばなクリニック】診療1_M_本番/生年月日聞き取り.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0025ちばなクリニック】診療1_M_本番/用件聞き取り.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0025ちばなクリニック】診療1_M_本番/紹介元医療機関名聴取.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0025ちばなクリニック】診療1_M_本番/紹介状有無.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0025ちばなクリニック】診療1_M_本番/診察券番号聞き取り.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0025ちばなクリニック】診療1_M_本番/診療科聞き取り.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0025ちばなクリニック】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 137 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 34 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 53 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 86 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 01_00_分岐なし診療科
- STT: 121 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `メーカー` (R1_STT_PROPER_NOUN_GROUP)
  - `レッカー` (R1_STT_PROPER_NOUN_GROUP)

### わからない
- STT: 15 surfaces, OpenAI: 8 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しらね` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しらん` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `ちゅんちゅん` (R3_STT_KANA_VARIANT → hearing_unknown)
- OpenAI サンプル:
  - `覚えて`
  - `分からない`
  - `分らない`
  - `覚えてない`
  - `知らない`

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
- STT: 3 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ちがう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `そうじゃないねん`
  - `そうちゃうねん`
  - `まちがった`

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

### 否定（エンティティ）
- STT: 11 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT)
  - `いや` (R3_STT_KANA_VARIANT)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
- OpenAI サンプル:
  - `否定`
  - `持ってない`
  - `持ってません。`

### 希望しない
- STT: 4 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `いや` (R3_STT_KANA_VARIANT)
  - `しない` (R3_STT_KANA_VARIANT)
  - `だめ` (R3_STT_KANA_VARIANT)
  - `できない` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `希望しない`
  - `結構`
  - `駄目`
  - `無理`

### 希望する
- STT: 5 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `OK` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `したい` (R3_STT_KANA_VARIANT)
  - `します` (R3_STT_KANA_VARIANT)
  - `できる` (R3_STT_KANA_VARIANT)
  - `みる` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `希望する`
  - `可能`
  - `見たい`
  - `見る`

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

### 用件
- STT: 22 surfaces, OpenAI: 32 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `にばん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `2`
  - `2番`
  - `ニ番`
  - `取り消す`
  - `二、`

### 肯定
- STT: 5 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうそう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はーい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`
  - `異常部`
  - `丈夫`
  - `大丈夫`
  - `配送です`

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

### 肯定（エンティティ）
- STT: 7 surfaces, OpenAI: 9 surfaces
- STT サンプル:
  - `OK` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `してまーす` (R3_STT_KANA_VARIANT)
  - `そう` (R3_STT_KANA_VARIANT)
  - `そうでーす` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `肯定`
  - `お持ちです`
  - `その通り`
  - `異常部`
  - `合って`

### 腎臓内科
- STT: 3 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `じんぞうないか` (R1_STT_PROPER_NOUN_GROUP)
  - `腎臓` (R1_STT_PROPER_NOUN_GROUP)
  - `透析` (R1_STT_PROPER_NOUN_GROUP)

### 膠原病・リウマチ科
- STT: 4 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `リウマチ科` (R1_STT_PROPER_NOUN_GROUP)
  - `リウマチ` (R1_STT_PROPER_NOUN_GROUP)
  - `膠原病` (R1_STT_PROPER_NOUN_GROUP)
  - `膠原病科` (R1_STT_PROPER_NOUN_GROUP)
