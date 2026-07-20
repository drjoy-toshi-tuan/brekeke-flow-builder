# Entity Classification Summary — 医誠会国際総合病院 / 診療

対象 yaml: 7 本

  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】診療1_M_本番/main.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】診療1_M_本番/予約日の聞き取り.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】診療1_M_本番/用件（非通知判断追加）.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】診療1_M_本番/診察券番号.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】診療1_M_本番/診療科.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 275 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 42 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 26 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 83 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 01_センター系
- STT: 64 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `ERプラス` (R1_STT_PROPER_NOUN_GROUP)
  - `いーあーる` (R1_STT_PROPER_NOUN_GROUP)
  - `アイセンター` (R1_STT_PROPER_NOUN_GROUP)
  - `アイ` (R1_STT_PROPER_NOUN_GROUP)
  - `イヤーセンター` (R1_STT_PROPER_NOUN_GROUP)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### わからない
- STT: 9 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかんない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わすれました` (R3_STT_KANA_VARIANT → hearing_unknown)
- OpenAI サンプル:
  - `解らない`
  - `持ってない`
  - `不明です`
  - `分からない`

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

### 分岐なし診療科
- STT: 211 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `リウマチ膠原病アレルギー科` (R1_STT_PROPER_NOUN_GROUP)
  - `アレルギー` (R1_STT_PROPER_NOUN_GROUP)
  - `リウマチ膠原病` (R1_STT_PROPER_NOUN_GROUP)
  - `抗原量` (R1_STT_PROPER_NOUN_GROUP)
  - `年末高伝票` (R1_STT_PROPER_NOUN_GROUP)

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
- STT: 2 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `そうじゃないねん`
  - `そうちゃうねん`
  - `ちがう`
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
- STT: 17 surfaces, OpenAI: 45 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `予約のキャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `取り消す`
  - `その他のお問合せ`
  - `その他確認`
  - `その盤`
  - `角煮`

### 肯定
- STT: 6 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうそう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ダイヤ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
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
