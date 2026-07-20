# Entity Classification Summary — 慈恵会　西田病院 / 診療

対象 yaml: 8 本

  - `【016】慈恵会　西田病院/【0017西田病院】診療1_M_本番/main.yaml`
  - `【016】慈恵会　西田病院/【0017西田病院】診療1_M_本番/予約日聴取.yaml`
  - `【016】慈恵会　西田病院/【0017西田病院】診療1_M_本番/医師名フリー聴取.yaml`
  - `【016】慈恵会　西田病院/【0017西田病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【016】慈恵会　西田病院/【0017西田病院】診療1_M_本番/用件聴取.yaml`
  - `【016】慈恵会　西田病院/【0017西田病院】診療1_M_本番/診療科数確認.yaml`
  - `【016】慈恵会　西田病院/【0017西田病院】診療1_M_本番/診療科聴取（医師名）.yaml`
  - `【016】慈恵会　西田病院/【0017西田病院】診療1_M_本番/連絡先聴取.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 149 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 34 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 78 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 127 | OpenAI 正規化 |

## 詳細 (entity 単位)

### わからない
- STT: 6 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しりません` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わすれた` (R3_STT_KANA_VARIANT → hearing_unknown)
- OpenAI サンプル:
  - `覚えてない`
  - `書いていない`
  - `知らない`
  - `忘れちゃった`
  - `分からない`

### 代表案内
- STT: 5 surfaces, OpenAI: 13 surfaces
- STT サンプル:
  - `問い合わせ` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `アクセス` (R3_STT_KANA_VARIANT)
  - `その他` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `なくした` (R3_STT_KANA_VARIANT)
  - `忘れた` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `お伺いしたい`
  - `お問合せ`
  - `その他を取り合わせ`
  - `確認したい`
  - `教えて`

### 先生名
- STT: 41 surfaces, OpenAI: 31 surfaces
- STT サンプル:
  - `おくだ` (R3_STT_KANA_VARIANT)
  - `オクダ` (R3_STT_KANA_VARIANT)
  - `あクマ` (R3_STT_KANA_VARIANT)
  - `アクマ` (R3_STT_KANA_VARIANT)
  - `アズマ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `奥田先生`
  - `奥田`
  - `加隈先生`
  - `各ま`
  - `吉田先生`

### 分岐_診療科
- STT: 13 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `消化器` (R1_STT_PROPER_NOUN_GROUP)
  - `小額内科` (R1_STT_PROPER_NOUN_GROUP)
  - `少額` (R1_STT_PROPER_NOUN_GROUP)
  - `尚書き` (R1_STT_PROPER_NOUN_GROUP)
  - `庄内` (R1_STT_PROPER_NOUN_GROUP)

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
- STT: 16 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いーえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `EHが今`
  - `否定`
  - `EHが今`

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

### 消化器分岐
- STT: 20 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `消化器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `いうか` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `メーカー` (R1_STT_PROPER_NOUN_GROUP)

### 用件
- STT: 15 surfaces, OpenAI: 51 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `再診` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `取り消す`
  - `あかかりつけの予約`
  - `かかりつけの予約`
  - `もう一度診察の予約を取る`
  - `安心`

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

### 診療科
- STT: 116 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `リウマチ膠原病内科` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `U町` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `いう町か` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `こー現状` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `りうまち` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
