# Entity Classification Summary — 新宿健診プラザ / 健診

対象 yaml: 12 本

  - `【064】新宿健診プラザ/【0060新宿健診プラザ】健診1_M_本番/4営業日後の日付セット.yaml`
  - `【064】新宿健診プラザ/【0060新宿健診プラザ】健診1_M_本番/main.yaml`
  - `【064】新宿健診プラザ/【0060新宿健診プラザ】健診1_M_本番/SMS送信用携帯番号聞き取りへ.yaml`
  - `【064】新宿健診プラザ/【0060新宿健診プラザ】健診1_M_本番/予約日聞き取り.yaml`
  - `【064】新宿健診プラザ/【0060新宿健診プラザ】健診1_M_本番/予約時間聞き取り.yaml`
  - `【064】新宿健診プラザ/【0060新宿健診プラザ】健診1_M_本番/受診希望日聞き取り.yaml`
  - `【064】新宿健診プラザ/【0060新宿健診プラザ】健診1_M_本番/受診票有無の確認.yaml`
  - `【064】新宿健診プラザ/【0060新宿健診プラザ】健診1_M_本番/希望時間聞き取り.yaml`
  - `【064】新宿健診プラザ/【0060新宿健診プラザ】健診1_M_本番/生年月日聞き取り.yaml`
  - `【064】新宿健診プラザ/【0060新宿健診プラザ】健診1_M_本番/用件聞き取り.yaml`
  - `【064】新宿健診プラザ/【0060新宿健診プラザ】健診1_M_本番/登録番号聞き取り.yaml`
  - `【064】新宿健診プラザ/【0060新宿健診プラザ】健診1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 33 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 46 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 53 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 74 | OpenAI 正規化 |

## 詳細 (entity 単位)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### エンティティ保存
- STT: 38 surfaces, OpenAI: 14 surfaces
- STT サンプル:
  - `健診予約` (R1_STT_PROPER_NOUN_GROUP)
  - `けんしん` (R1_STT_PROPER_NOUN_GROUP)
  - `ようやく` (R1_STT_PROPER_NOUN_GROUP)
  - `眼瞼すんの` (R1_STT_PROPER_NOUN_GROUP)
  - `健診` (R1_STT_PROPER_NOUN_GROUP)
- OpenAI サンプル:
  - `お伺いしたい`
  - `お問合せ`
  - `その他を取り合わせ`
  - `確認したい`
  - `教えて`

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
- STT: 12 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いえいえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `それじゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `違う`
  - `間違い`
  - `間違って`
  - `間違えた`

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

### 持っている
- STT: 5 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ある` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いまーす` (R3_STT_KANA_VARIANT)
  - `います` (R3_STT_KANA_VARIANT)
  - `いる` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `持っている`
  - `持っていまーす`
  - `持ってまーす`
  - `持ってます`
  - `盛ってまーす`

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

### 時分
- STT: 2 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `時` (R2_STT_TEMPLATE_REUSE → hearing_time)
  - `分` (R2_STT_TEMPLATE_REUSE → hearing_time)

### 用件
- STT: 10 surfaces, OpenAI: 14 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `予約のキャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `取り消す`
  - `予約キャンセル`
  - `時間`
  - `取り直したい`
  - `取り直す`

### 肯定
- STT: 20 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `あっています` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `うん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `うんうん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`
  - `大丈夫です`
  - `異常部`
  - `丈夫`
  - `大丈夫`

### 肯定エンティティ
- STT: 11 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `あっています` (R3_STT_KANA_VARIANT)
  - `あってます` (R3_STT_KANA_VARIANT)
  - `うん` (R3_STT_KANA_VARIANT)
  - `うんうん` (R3_STT_KANA_VARIANT)
  - `そう` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `肯定`
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
