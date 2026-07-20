# Entity Classification Summary — 札幌禎心会病院 / 診療

対象 yaml: 10 本

  - `【031】札幌禎心会病院｜【032】北口クリニック/【0044禎心会さっぽろ北口クリニック】診療1_M_本番/main.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0044禎心会さっぽろ北口クリニック】診療1_M_本番/予約希望日.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0044禎心会さっぽろ北口クリニック】診療1_M_本番/予約日（フリー聴取）.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0044禎心会さっぽろ北口クリニック】診療1_M_本番/生年月日聞き取り.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0044禎心会さっぽろ北口クリニック】診療1_M_本番/用件聞き取り.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0044禎心会さっぽろ北口クリニック】診療1_M_本番/症状ヒアリング.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0044禎心会さっぽろ北口クリニック】診療1_M_本番/診療科.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0044禎心会さっぽろ北口クリニック】診療1_M_本番/診療科フリー聴取.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0044禎心会さっぽろ北口クリニック】診療1_M_本番/追加要望.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0044禎心会さっぽろ北口クリニック】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 309 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 41 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 28 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 104 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 01_00_分岐なし診療科
- STT: 278 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `ペインクリニック外科` (R1_STT_PROPER_NOUN_GROUP)
  - `DE` (R1_STT_PROPER_NOUN_GROUP)
  - `DEクリニック` (R1_STT_PROPER_NOUN_GROUP)
  - `Pingクリニック` (R1_STT_PROPER_NOUN_GROUP)
  - `Pクリニック` (R1_STT_PROPER_NOUN_GROUP)

### あります
- STT: 2 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ある` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `受診歴ある`

### もう一度
- STT: 0 surfaces, OpenAI: 9 surfaces
- OpenAI サンプル:
  - `もう一度`
  - `1回`
  - `1度`
  - `もう1回`
  - `もう1度`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### わからない
- STT: 10 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `おぼえてない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しらん` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しりません` (R3_STT_KANA_VARIANT → hearing_unknown)
- OpenAI サンプル:
  - `覚えてない`
  - `知らない`
  - `知らん`
  - `分からない`
  - `分からん`

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

### 代表案内診療科
- STT: 23 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `がんセカンドオピニオン外来` (R1_STT_PROPER_NOUN_GROUP)
  - `オピニオン` (R1_STT_PROPER_NOUN_GROUP)
  - `がんセカンドオピニオン` (R1_STT_PROPER_NOUN_GROUP)
  - `セカンド` (R1_STT_PROPER_NOUN_GROUP)
  - `セカンドオピニオン` (R1_STT_PROPER_NOUN_GROUP)

### 分岐あり
- STT: 8 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `心臓ドック` (R1_STT_PROPER_NOUN_GROUP)
  - `ドック` (R1_STT_PROPER_NOUN_GROUP)
  - `ロック` (R1_STT_PROPER_NOUN_GROUP)
  - `振動ロック` (R1_STT_PROPER_NOUN_GROUP)
  - `腎臓ボックス` (R1_STT_PROPER_NOUN_GROUP)

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
- STT: 2 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `そうじゃないねん`
  - `そうちゃうねん`
  - `ちがう`
  - `ではない`
  - `はじめてではない`

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

### 心臓
- STT: 2 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `シンゾウ` (R3_STT_KANA_VARIANT)
  - `シンゾ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `心`
  - `振動`

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
- STT: 17 surfaces, OpenAI: 56 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `予約のキャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `4`
  - `４`
  - `四`
  - `取り消す`
  - `3`

### 肯定
- STT: 7 surfaces, OpenAI: 5 surfaces
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
