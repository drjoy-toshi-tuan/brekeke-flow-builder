# Entity Classification Summary — 中頭病院 / 診療

対象 yaml: 15 本

  - `【026】中頭病院｜【027】ちばなクリニック/【0028中頭病院】診療1_M_本番/main.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0028中頭病院】診療1_M_本番/WEB確認案内.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0028中頭病院】診療1_M_本番/予約日の聞き取り.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0028中頭病院】診療1_M_本番/医療機関名聞き取り.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0028中頭病院】診療1_M_本番/医療機関名聞き取り_1.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0028中頭病院】診療1_M_本番/希望日.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0028中頭病院】診療1_M_本番/新規用診療科.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0028中頭病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0028中頭病院】診療1_M_本番/用件聞き取り.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0028中頭病院】診療1_M_本番/第1受診希望日.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0028中頭病院】診療1_M_本番/肯定否定.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0028中頭病院】診療1_M_本番/診察券番号確認.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0028中頭病院】診療1_M_本番/診療科確認.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0028中頭病院】診療1_M_本番/診療科聞き取り.yaml`
  - `【026】中頭病院｜【027】ちばなクリニック/【0028中頭病院】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 474 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 40 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 47 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 95 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 00_00_01_呼吸器
- STT: 14 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `お休憩か` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `形が` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_02_消化器
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `消化器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `形が` (R1_STT_PROPER_NOUN_GROUP)
  - `経過` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_03_脳神経
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `脳神経外科` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `形が` (R1_STT_PROPER_NOUN_GROUP)
  - `経過` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_04_婦人科
- STT: 15 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `遺伝外来` (R1_STT_PROPER_NOUN_GROUP)
  - `以前外来` (R1_STT_PROPER_NOUN_GROUP)
  - `遺伝` (R1_STT_PROPER_NOUN_GROUP)
  - `外来` (R1_STT_PROPER_NOUN_GROUP)
  - `一般婦人科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_分岐あり診療科
- STT: 19 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器` (R1_STT_PROPER_NOUN_GROUP)
  - `コピー機` (R1_STT_PROPER_NOUN_GROUP)
  - `吸気` (R1_STT_PROPER_NOUN_GROUP)
  - `五九` (R1_STT_PROPER_NOUN_GROUP)
  - `補給機` (R1_STT_PROPER_NOUN_GROUP)

### 01_00_分岐なし診療科
- STT: 396 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `形成外科` (R1_STT_PROPER_NOUN_GROUP)
  - `ケーズギガ。` (R1_STT_PROPER_NOUN_GROUP)
  - `以前から、` (R1_STT_PROPER_NOUN_GROUP)
  - `九千円か` (R1_STT_PROPER_NOUN_GROUP)
  - `形成` (R1_STT_PROPER_NOUN_GROUP)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### わからない
- STT: 19 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `さあ` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しらん` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しるか` (R3_STT_KANA_VARIANT → hearing_unknown)
- OpenAI サンプル:
  - `覚えて`
  - `分からない`
  - `分らない`
  - `覚えてない`
  - `知らない`

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

### 希望しない
- STT: 4 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `いや` (R3_STT_KANA_VARIANT)
  - `しない` (R3_STT_KANA_VARIANT)
  - `だめ` (R3_STT_KANA_VARIANT)
  - `できない` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `希望しない`
  - `結構`
  - `駄目`
  - `無理`

### 希望する
- STT: 5 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `OK` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `したい` (R3_STT_KANA_VARIANT)
  - `します` (R3_STT_KANA_VARIANT)
  - `できる` (R3_STT_KANA_VARIANT)
  - `みる` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `希望する`
  - `可能`
  - `見たい`
  - `見る`

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

### 産婦人科
- STT: 6 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `産婦人科` (R1_STT_PROPER_NOUN_GROUP)
  - `ギネ` (R1_STT_PROPER_NOUN_GROUP)
  - `ぎね` (R1_STT_PROPER_NOUN_GROUP)
  - `サンフ` (R1_STT_PROPER_NOUN_GROUP)
  - `フジコ` (R1_STT_PROPER_NOUN_GROUP)

### 用件
- STT: 18 surfaces, OpenAI: 48 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `キャンセルする` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `取り消す`
  - `その他確認`
  - `確認する`
  - `角煮`
  - `教えて`

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
