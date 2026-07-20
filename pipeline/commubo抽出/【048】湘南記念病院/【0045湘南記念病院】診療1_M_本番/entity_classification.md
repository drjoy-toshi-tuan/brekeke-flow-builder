# Entity Classification Summary — 湘南記念病院 / 診療

対象 yaml: 9 本

  - `【048】湘南記念病院/【0045湘南記念病院】診療1_M_本番/main.yaml`
  - `【048】湘南記念病院/【0045湘南記念病院】診療1_M_本番/予約希望日.yaml`
  - `【048】湘南記念病院/【0045湘南記念病院】診療1_M_本番/予約日の聞き取り.yaml`
  - `【048】湘南記念病院/【0045湘南記念病院】診療1_M_本番/当日予約排除（5_22 更新）.yaml`
  - `【048】湘南記念病院/【0045湘南記念病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【048】湘南記念病院/【0045湘南記念病院】診療1_M_本番/用件（5_22 更新）.yaml`
  - `【048】湘南記念病院/【0045湘南記念病院】診療1_M_本番/診察券番号聞き取り.yaml`
  - `【048】湘南記念病院/【0045湘南記念病院】診療1_M_本番/診療科.yaml`
  - `【048】湘南記念病院/【0045湘南記念病院】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 215 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 38 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 55 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 102 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 01_00_分岐なし診療科
- STT: 215 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `アートメイク` (R1_STT_PROPER_NOUN_GROUP)
  - `あートニック` (R1_STT_PROPER_NOUN_GROUP)
  - `アイライン` (R1_STT_PROPER_NOUN_GROUP)
  - `あうんとメイク` (R1_STT_PROPER_NOUN_GROUP)
  - `あとメイク` (R1_STT_PROPER_NOUN_GROUP)

### もう一度
- STT: 6 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `まって` (R3_STT_KANA_VARIANT)
  - `もいちど` (R3_STT_KANA_VARIANT)
  - `もういっかい` (R3_STT_KANA_VARIANT)
  - `もーいちど` (R3_STT_KANA_VARIANT)
  - `もっかい` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `もう一度`
  - `もう一_回`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### わからない
- STT: 6 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しりませーん` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わすれた` (R3_STT_KANA_VARIANT → hearing_unknown)
- OpenAI サンプル:
  - `覚えてない`
  - `書いていない`
  - `知らない`
  - `分からない`
  - `分からん`

### 分からない
- STT: 6 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ません` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかんない` (R3_STT_KANA_VARIANT → hearing_unknown)
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
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `ちがう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `いーえ`
  - `まちがった`
  - `そうじゃないねん`
  - `そうちゃうねん`
  - `否定`

### 否定エンティティ
- STT: 8 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT)
  - `いや` (R3_STT_KANA_VARIANT)
  - `じゃない` (R3_STT_KANA_VARIANT)
  - `ちがいまーす` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `否定`
  - `EHが今`

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
  - `すみません` (R3_STT_KANA_VARIANT)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `持ってない`
  - `以てない`
  - `持ってませーん`
  - `持ってません`
  - `盛ってない`

### 用件
- STT: 12 surfaces, OpenAI: 45 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `キャンプ` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `のキャンセル` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `3`
  - `3番`
  - `よく県する`
  - `行けない`
  - `三`

### 肯定
- STT: 15 surfaces, OpenAI: 11 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってる` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうそう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `その通りです`
  - `異常部`
  - `丈夫`
  - `大丈夫`
  - `配送です`

### 肯定エンティティ
- STT: 2 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `してまーす` (R3_STT_KANA_VARIANT)
  - `はーい` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `肯定`
  - `異常部`
  - `合って`
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
