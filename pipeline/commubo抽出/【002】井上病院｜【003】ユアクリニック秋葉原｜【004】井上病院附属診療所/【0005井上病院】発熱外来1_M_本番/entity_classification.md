# Entity Classification Summary — 井上病院 / 発熱外来

対象 yaml: 6 本

  - `【002】井上病院｜【003】ユアクリニック秋葉原｜【004】井上病院附属診療所/【0005井上病院】発熱外来1_M_本番/main.yaml`
  - `【002】井上病院｜【003】ユアクリニック秋葉原｜【004】井上病院附属診療所/【0005井上病院】発熱外来1_M_本番/受診歴有無.yaml`
  - `【002】井上病院｜【003】ユアクリニック秋葉原｜【004】井上病院附属診療所/【0005井上病院】発熱外来1_M_本番/性別確認.yaml`
  - `【002】井上病院｜【003】ユアクリニック秋葉原｜【004】井上病院附属診療所/【0005井上病院】発熱外来1_M_本番/生年月日聞き取り.yaml`
  - `【002】井上病院｜【003】ユアクリニック秋葉原｜【004】井上病院附属診療所/【0005井上病院】発熱外来1_M_本番/診察券番号聞き取り.yaml`
  - `【002】井上病院｜【003】ユアクリニック秋葉原｜【004】井上病院附属診療所/【0005井上病院】発熱外来1_M_本番/連絡先聞取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 0 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 25 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 52 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 42 | OpenAI 正規化 |

## 詳細 (entity 単位)

### Confirm
- STT: 4 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `違います` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)

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
- STT: 10 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いーえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
- OpenAI サンプル:
  - `違う`
  - `間違えた`
  - `間違った`

### 否定単語
- STT: 9 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `違います` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうじゃないねん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうちゃうねん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `違い`
  - `違う`
  - `違って`
  - `駄目`

### 性別
- STT: 10 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `おんな` (R3_STT_KANA_VARIANT)
  - `オンナ` (R3_STT_KANA_VARIANT)
  - `ジョセイ` (R3_STT_KANA_VARIANT)
  - `じょせい` (R3_STT_KANA_VARIANT)
  - `メス` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `女性`
  - `助成`
  - `女`
  - `男性`
  - `弾性`

### 持ってない
- STT: 11 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `もってない` (R3_STT_KANA_VARIANT)
  - `ないです` (R3_STT_KANA_VARIANT)
  - `もってませーん` (R3_STT_KANA_VARIANT)
  - `持っていません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いない` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `手元にありません`
  - `持ってない`
  - `以てない`
  - `持ってませーん`
  - `持ってません`

### 肯定
- STT: 7 surfaces, OpenAI: 5 surfaces
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

### 肯定単語
- STT: 13 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `OK` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `あっています` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってる` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `はい大丈夫です`
  - `違いありません`
  - `違いない`
  - `大丈夫`
  - `配送です`
