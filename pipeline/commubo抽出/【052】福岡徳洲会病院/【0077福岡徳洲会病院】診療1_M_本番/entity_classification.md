# Entity Classification Summary — 福岡徳洲会病院 / 診療

対象 yaml: 11 本

  - `【052】福岡徳洲会病院/【0077福岡徳洲会病院】診療1_M_本番/main.yaml`
  - `【052】福岡徳洲会病院/【0077福岡徳洲会病院】診療1_M_本番/リハビリ確認内容.yaml`
  - `【052】福岡徳洲会病院/【0077福岡徳洲会病院】診療1_M_本番/予約日.yaml`
  - `【052】福岡徳洲会病院/【0077福岡徳洲会病院】診療1_M_本番/変更希望日.yaml`
  - `【052】福岡徳洲会病院/【0077福岡徳洲会病院】診療1_M_本番/氏名.yaml`
  - `【052】福岡徳洲会病院/【0077福岡徳洲会病院】診療1_M_本番/理由.yaml`
  - `【052】福岡徳洲会病院/【0077福岡徳洲会病院】診療1_M_本番/生年月日.yaml`
  - `【052】福岡徳洲会病院/【0077福岡徳洲会病院】診療1_M_本番/用件.yaml`
  - `【052】福岡徳洲会病院/【0077福岡徳洲会病院】診療1_M_本番/診察券番号.yaml`
  - `【052】福岡徳洲会病院/【0077福岡徳洲会病院】診療1_M_本番/追加問い合わせ_追加診療科.yaml`
  - `【052】福岡徳洲会病院/【0077福岡徳洲会病院】診療1_M_本番/連絡先.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 0 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 39 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 28 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 75 | OpenAI 正規化 |

## 詳細 (entity 単位)

### もう一度
- STT: 2 surfaces, OpenAI: 8 surfaces
- STT サンプル:
  - `もっかい` (R3_STT_KANA_VARIANT)
  - `もっかい` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `もう一度`
  - `もう一回`
  - `一回`
  - `一階`
  - `一度`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### 分からない
- STT: 9 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `しりません` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `知りません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `しらん` (R3_STT_KANA_VARIANT → hearing_unknown)
- OpenAI サンプル:
  - `分からない`
  - `知らない`
  - `分かりません`
  - `解らない`
  - `持ってない`

### 初めて
- STT: 2 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `初めて` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はじめて` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `始めて`

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
- STT: 8 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ちがいまーす` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `EHが今`
  - `違いまーす`

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
- STT: 21 surfaces, OpenAI: 33 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `確認` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `2`
  - `取り消す`
  - `二`
  - `3`
  - `三`

### 肯定
- STT: 1 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `はーい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
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
