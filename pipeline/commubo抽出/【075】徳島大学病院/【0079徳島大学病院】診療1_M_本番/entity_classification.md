# Entity Classification Summary — 徳島大学病院 / 診療

対象 yaml: 7 本

  - `【075】徳島大学病院/【0079徳島大学病院】診療1_M_本番/main.yaml`
  - `【075】徳島大学病院/【0079徳島大学病院】診療1_M_本番/WEB利用.yaml`
  - `【075】徳島大学病院/【0079徳島大学病院】診療1_M_本番/体調確認.yaml`
  - `【075】徳島大学病院/【0079徳島大学病院】診療1_M_本番/携帯番号.yaml`
  - `【075】徳島大学病院/【0079徳島大学病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【075】徳島大学病院/【0079徳島大学病院】診療1_M_本番/用件聞き取り.yaml`
  - `【075】徳島大学病院/【0079徳島大学病院】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 0 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 35 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 37 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 69 | OpenAI 正規化 |

## 詳細 (entity 単位)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

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
- STT: 19 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `いーえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ううん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
- OpenAI サンプル:
  - `否定`
  - `間違った`
  - `EHが今`
  - `そうじゃないねん`
  - `そうちゃうねん`

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

### 持ってない
- STT: 8 surfaces, OpenAI: 5 surfaces
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
- STT: 12 surfaces, OpenAI: 35 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `予約のキャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `2`
  - `2番`
  - `取り消す`
  - `二`
  - `二番`

### 肯定
- STT: 16 surfaces, OpenAI: 9 surfaces
- STT サンプル:
  - `OK` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `いいです` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `オケー` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうそう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`
  - `大丈夫です。`
  - `配送です`
  - `翌診療日`
  - `その通りです`

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
