# Entity Classification Summary — 浦添総合病院 / 健診

対象 yaml: 7 本

  - `【010】浦添総合病院/【0010浦添総合病院健診センター】健診1_M_本番/main.yaml`
  - `【010】浦添総合病院/【0010浦添総合病院健診センター】健診1_M_本番/個人・企業判別.yaml`
  - `【010】浦添総合病院/【0010浦添総合病院健診センター】健診1_M_本番/内容フリー聴取.yaml`
  - `【010】浦添総合病院/【0010浦添総合病院健診センター】健診1_M_本番/現在の予約日_予約希望日.yaml`
  - `【010】浦添総合病院/【0010浦添総合病院健診センター】健診1_M_本番/生年月日聞き取り.yaml`
  - `【010】浦添総合病院/【0010浦添総合病院健診センター】健診1_M_本番/用件.yaml`
  - `【010】浦添総合病院/【0010浦添総合病院健診センター】健診1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 0 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 49 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 49 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 117 | OpenAI 正規化 |

## 詳細 (entity 単位)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### 企業：用件
- STT: 15 surfaces, OpenAI: 19 surfaces
- STT サンプル:
  - `新規` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `いち` (R3_STT_KANA_VARIANT)
  - `いちばん` (R3_STT_KANA_VARIANT)
  - `さいしょ` (R3_STT_KANA_VARIANT)
  - `ようやく` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `1`
  - `1番`
  - `一`
  - `一番`
  - `最初`

### 個人：用件
- STT: 36 surfaces, OpenAI: 60 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `さんばん` (R3_STT_KANA_VARIANT)
  - `みっつ` (R3_STT_KANA_VARIANT)
  - `みっつめ` (R3_STT_KANA_VARIANT)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `3番`
  - `三`
  - `三番`
  - `取り消す`
  - `予約キャンセル`

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
- STT: 12 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `ちがう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ちゃうちゃう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `まちがった` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `会社で`
  - `会社です`
  - `三重`
  - `未定`
  - `決まっていない`

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

### 肯定
- STT: 9 surfaces, OpenAI: 12 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうそう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はーい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `個人マスク`
  - `大丈夫`
  - `配送です`
  - `肯定`
  - `決まった`

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
