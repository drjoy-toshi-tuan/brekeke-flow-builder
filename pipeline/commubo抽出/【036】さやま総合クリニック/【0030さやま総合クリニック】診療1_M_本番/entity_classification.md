# Entity Classification Summary — さやま総合クリニック / 診療

対象 yaml: 8 本

  - `【036】さやま総合クリニック/【0030さやま総合クリニック】診療1_M_本番/main.yaml`
  - `【036】さやま総合クリニック/【0030さやま総合クリニック】診療1_M_本番/予約日の聞き取り.yaml`
  - `【036】さやま総合クリニック/【0030さやま総合クリニック】診療1_M_本番/希望日の聞き取り.yaml`
  - `【036】さやま総合クリニック/【0030さやま総合クリニック】診療1_M_本番/生年月日聞き取り.yaml`
  - `【036】さやま総合クリニック/【0030さやま総合クリニック】診療1_M_本番/用件聞き取り.yaml`
  - `【036】さやま総合クリニック/【0030さやま総合クリニック】診療1_M_本番/診察券番号聞き取り.yaml`
  - `【036】さやま総合クリニック/【0030さやま総合クリニック】診療1_M_本番/診療科聞き取り.yaml`
  - `【036】さやま総合クリニック/【0030さやま総合クリニック】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 510 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 41 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 50 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 88 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 00_00_01_呼吸器
- STT: 13 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `形が` (R1_STT_PROPER_NOUN_GROUP)
  - `経過` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_02_内分泌
- STT: 17 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `代謝内分泌内科` (R1_STT_PROPER_NOUN_GROUP)
  - `たいしゃ` (R1_STT_PROPER_NOUN_GROUP)
  - `タイシャ` (R1_STT_PROPER_NOUN_GROUP)
  - `代謝` (R1_STT_PROPER_NOUN_GROUP)
  - `代謝内分泌` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_03_甲状腺
- STT: 18 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `代謝内分泌内科` (R1_STT_PROPER_NOUN_GROUP)
  - `たいしゃ` (R1_STT_PROPER_NOUN_GROUP)
  - `タイシャ` (R1_STT_PROPER_NOUN_GROUP)
  - `代謝` (R1_STT_PROPER_NOUN_GROUP)
  - `代謝内分泌` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_分岐あり診療科
- STT: 14 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器` (R1_STT_PROPER_NOUN_GROUP)
  - `コピー機` (R1_STT_PROPER_NOUN_GROUP)
  - `吸気` (R1_STT_PROPER_NOUN_GROUP)
  - `五九` (R1_STT_PROPER_NOUN_GROUP)
  - `補給機` (R1_STT_PROPER_NOUN_GROUP)

### 01_00_分岐なし診療科
- STT: 435 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `メンタルヘルス科` (R1_STT_PROPER_NOUN_GROUP)
  - `ヘルス` (R1_STT_PROPER_NOUN_GROUP)
  - `メンタル` (R1_STT_PROPER_NOUN_GROUP)
  - `メンタルヘルス` (R1_STT_PROPER_NOUN_GROUP)
  - `メンヘル` (R1_STT_PROPER_NOUN_GROUP)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### 今日
- STT: 3 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `今日` (R2_STT_TEMPLATE_REUSE → hearing_datetime)
  - `これから` (R3_STT_KANA_VARIANT)
  - `本日` (R2_STT_TEMPLATE_REUSE → hearing_datetime)
- OpenAI サンプル:
  - `今から`
  - `当日`
  - `当日予約`

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
- STT: 15 surfaces, OpenAI: 11 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `そうではない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `それではない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `違う`
  - `間違い`
  - `間違っている`
  - `間違ってます`

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
- STT: 22 surfaces, OpenAI: 42 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `さん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `サン` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `さんばん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `サンバン` (R3_STT_KANA_VARIANT → hearing_yoken_common)
- OpenAI サンプル:
  - `3`
  - `3番`
  - `三`
  - `三番`
  - `取り消す`

### 看護外来
- STT: 13 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `看護外来` (R1_STT_PROPER_NOUN_GROUP)
  - `DM` (R1_STT_PROPER_NOUN_GROUP)
  - `DM指導` (R1_STT_PROPER_NOUN_GROUP)
  - `EMC` (R1_STT_PROPER_NOUN_GROUP)
  - `EM指導` (R1_STT_PROPER_NOUN_GROUP)

### 肯定
- STT: 17 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `あっています` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あっている` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってる` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いいです` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
- OpenAI サンプル:
  - `肯定`
  - `大丈夫です`
  - `正しい`
  - `異常部`
  - `丈夫`

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
