# Entity Classification Summary — 西宮渡辺病院  / 診療

対象 yaml: 9 本

  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0020西宮渡辺病院】診療1_M_本番/main.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0020西宮渡辺病院】診療1_M_本番/予約日の聞き取り.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0020西宮渡辺病院】診療1_M_本番/変更キャンセル分岐.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0020西宮渡辺病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0020西宮渡辺病院】診療1_M_本番/用件聞き取り.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0020西宮渡辺病院】診療1_M_本番/紹介状の有無確認.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0020西宮渡辺病院】診療1_M_本番/診察券番号聞き取り.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0020西宮渡辺病院】診療1_M_本番/診療科聞き取り.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0020西宮渡辺病院】診療1_M_本番/連絡先携帯聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 279 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 44 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 37 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 105 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 01_00_分岐なし診療科
- STT: 279 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `フットケア看護外来` (R1_STT_PROPER_NOUN_GROUP)
  - `トクヤ` (R1_STT_PROPER_NOUN_GROUP)
  - `とケア` (R1_STT_PROPER_NOUN_GROUP)
  - `どけや` (R1_STT_PROPER_NOUN_GROUP)
  - `フードケア` (R1_STT_PROPER_NOUN_GROUP)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

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

### 健康診断
- STT: 5 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `健康診断` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `健診` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `検診` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `検針` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `人間ドック` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
- OpenAI サンプル:
  - `検査`
  - `人間ドッグ`

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
- STT: 13 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうじゃないねん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうちゃうねん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ちがう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
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
- STT: 22 surfaces, OpenAI: 62 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `予約のキャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `取り消す`
  - `その他確認`
  - `角煮`
  - `教えて`
  - `時間を忘れた`

### 緊急救急
- STT: 0 surfaces, OpenAI: 10 surfaces
- OpenAI サンプル:
  - `救急`
  - `QQ`
  - `UU`
  - `いう牛`
  - `急激`

### 肯定
- STT: 7 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `そうそう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
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
