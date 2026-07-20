# Entity Classification Summary — セントラル・クリニック 伊島 / 診療

対象 yaml: 7 本

  - `【023】セントラル・クリニック 伊島/【0018岡山中央病院】診療1_M_本番/main.yaml`
  - `【023】セントラル・クリニック 伊島/【0018岡山中央病院】診療1_M_本番/先生名ヒアリング.yaml`
  - `【023】セントラル・クリニック 伊島/【0018岡山中央病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【023】セントラル・クリニック 伊島/【0018岡山中央病院】診療1_M_本番/用件聴取.yaml`
  - `【023】セントラル・クリニック 伊島/【0018岡山中央病院】診療1_M_本番/診察券番号確認.yaml`
  - `【023】セントラル・クリニック 伊島/【0018岡山中央病院】診療1_M_本番/診療科聞き取り.yaml`
  - `【023】セントラル・クリニック 伊島/【0018岡山中央病院】診療1_M_本番/連絡先聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 85 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 45 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 62 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 106 | OpenAI 正規化 |

## 詳細 (entity 単位)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### わからない
- STT: 3 surfaces, OpenAI: 11 surfaces
- STT サンプル:
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `あらしまへん`
  - `あれへん`
  - `ええように`
  - `しらない`
  - `しらん`

### 代表案内案件
- STT: 5 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `ドック` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `健康診断` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `健診` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `検診` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `人間ドック` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
- OpenAI サンプル:
  - `代表案内`

### 先生名
- STT: 26 surfaces, OpenAI: 11 surfaces
- STT サンプル:
  - `いが` (R3_STT_KANA_VARIANT)
  - `イガ` (R3_STT_KANA_VARIANT)
  - `えが` (R3_STT_KANA_VARIANT)
  - `エガ` (R3_STT_KANA_VARIANT)
  - `いまだ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `いが先生`
  - `いまだ先生`
  - `えぐち先生`
  - `おうたに先生`
  - `かねしげ先生`

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
- STT: 7 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうじゃないねん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうちゃうねん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ちがう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `違う`
  - `間違えた`
  - `間違った`

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
- STT: 12 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `もってない` (R3_STT_KANA_VARIANT)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `もっていない` (R3_STT_KANA_VARIANT)
  - `もってませーん` (R3_STT_KANA_VARIANT)
  - `持っていません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `手元にありません`
  - `持ってない`
  - `以てない`
  - `持ってませーん`
  - `持ってません`

### 用件
- STT: 29 surfaces, OpenAI: 45 surfaces
- STT サンプル:
  - `そのた` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `そのほか` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `その他` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `確認` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `相談` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `その他ご相談`
  - `教えてほしい`
  - `知りたい`
  - `聞きたい`
  - `診察の予約について`

### 肯定
- STT: 11 surfaces, OpenAI: 10 surfaces
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

### 診療科
- STT: 77 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `眼科` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `あんか` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `あんた` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `がんか` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `だんか` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
