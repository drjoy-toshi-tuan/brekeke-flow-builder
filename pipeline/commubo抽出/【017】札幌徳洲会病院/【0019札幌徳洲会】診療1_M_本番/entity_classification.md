# Entity Classification Summary — 札幌徳洲会病院 / 診療

対象 yaml: 10 本

  - `【017】札幌徳洲会病院/【0019札幌徳洲会】診療1_M_本番/main.yaml`
  - `【017】札幌徳洲会病院/【0019札幌徳洲会】診療1_M_本番/予約希望日有無.yaml`
  - `【017】札幌徳洲会病院/【0019札幌徳洲会】診療1_M_本番/予約日確認.yaml`
  - `【017】札幌徳洲会病院/【0019札幌徳洲会】診療1_M_本番/生年月日聞き取り.yaml`
  - `【017】札幌徳洲会病院/【0019札幌徳洲会】診療1_M_本番/用件.yaml`
  - `【017】札幌徳洲会病院/【0019札幌徳洲会】診療1_M_本番/紹介状分岐.yaml`
  - `【017】札幌徳洲会病院/【0019札幌徳洲会】診療1_M_本番/診察券番号聞き取り.yaml`
  - `【017】札幌徳洲会病院/【0019札幌徳洲会】診療1_M_本番/診療科.yaml`
  - `【017】札幌徳洲会病院/【0019札幌徳洲会】診療1_M_本番/診療科聴取（再診）.yaml`
  - `【017】札幌徳洲会病院/【0019札幌徳洲会】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 557 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 49 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 71 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 116 | OpenAI 正規化 |

## 詳細 (entity 単位)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### もっています
- STT: 2 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ある` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `もっています`
  - `いただいています`
  - `もってる`
  - `もらってる`

### もっていません
- STT: 3 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `もってない` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `もっていません`
  - `あれへん`
  - `いただいていません`
  - `もらってない`

### わからない
- STT: 7 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `からない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しらん` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `なんだろう` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わーらない` (R3_STT_KANA_VARIANT → hearing_unknown)
- OpenAI サンプル:
  - `知らない`
  - `分からない`

### ワクチン
- STT: 2 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `ワクチン` (R1_STT_PROPER_NOUN_GROUP)
  - `ワク` (R1_STT_PROPER_NOUN_GROUP)

### 予約案内診療科
- STT: 236 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `ＩＢＤセンター` (R1_STT_PROPER_NOUN_GROUP)
  - `ＩＢＤセンター。` (R1_STT_PROPER_NOUN_GROUP)
  - `IBD千だ` (R1_STT_PROPER_NOUN_GROUP)
  - `iBセンター` (R1_STT_PROPER_NOUN_GROUP)
  - `IDセンター` (R1_STT_PROPER_NOUN_GROUP)

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
- STT: 5 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうじゃないねん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうちゃうねん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `まちがった` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `ちがう`

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

### 地域連携案内診療科
- STT: 15 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `整形外科` (R1_STT_PROPER_NOUN_GROUP)
  - `TK` (R1_STT_PROPER_NOUN_GROUP)
  - `整形` (R1_STT_PROPER_NOUN_GROUP)
  - `日経外科` (R1_STT_PROPER_NOUN_GROUP)
  - `閉経` (R1_STT_PROPER_NOUN_GROUP)

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

### 決まっていない
- STT: 13 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `きまっていない` (R3_STT_KANA_VARIANT)
  - `きまってない` (R3_STT_KANA_VARIANT)
  - `しらない` (R3_STT_KANA_VARIANT)
  - `つかれた` (R3_STT_KANA_VARIANT)
  - `まだ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `決まっていない`
  - `未定`
  - `決まってない`

### 決まっている
- STT: 3 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ある` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `きまっています` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `決まっている`
  - `はい、きま`

### 用件
- STT: 41 surfaces, OpenAI: 68 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `ヨン` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `よん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `よんばん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
- OpenAI サンプル:
  - `4`
  - `4番`
  - `取り消す`
  - `3`
  - `3番`

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

### 診療科
- STT: 304 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `ＩＢＤセンター` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `ＩＢＤセンター。` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `IBDセンター。` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `IBD千だ` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `iBセンター` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
