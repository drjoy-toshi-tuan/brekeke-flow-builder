# Entity Classification Summary — 鹿児島市立病院 / 診療

対象 yaml: 8 本

  - `【063】鹿児島市立病院/【0087鹿児島市立病院】診療1_M_本番/main.yaml`
  - `【063】鹿児島市立病院/【0087鹿児島市立病院】診療1_M_本番/初診確認.yaml`
  - `【063】鹿児島市立病院/【0087鹿児島市立病院】診療1_M_本番/生年月日.yaml`
  - `【063】鹿児島市立病院/【0087鹿児島市立病院】診療1_M_本番/用件.yaml`
  - `【063】鹿児島市立病院/【0087鹿児島市立病院】診療1_M_本番/紹介元電話番号.yaml`
  - `【063】鹿児島市立病院/【0087鹿児島市立病院】診療1_M_本番/紹介状.yaml`
  - `【063】鹿児島市立病院/【0087鹿児島市立病院】診療1_M_本番/診療科.yaml`
  - `【063】鹿児島市立病院/【0087鹿児島市立病院】診療1_M_本番/連絡先電話番号.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 324 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 51 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 56 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 133 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 00_00_01_呼吸器
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `形が` (R1_STT_PROPER_NOUN_GROUP)
  - `経過` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_02_消化器
- STT: 13 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `消化器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `しょうげ` (R1_STT_PROPER_NOUN_GROUP)
  - `しょげ` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_03_脳神経
- STT: 13 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `脳神経外科` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `のうげ` (R1_STT_PROPER_NOUN_GROUP)
  - `の下` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_04_産婦人科
- STT: 21 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `産科` (R1_STT_PROPER_NOUN_GROUP)
  - `3` (R1_STT_PROPER_NOUN_GROUP)
  - `3か` (R1_STT_PROPER_NOUN_GROUP)
  - `お産` (R1_STT_PROPER_NOUN_GROUP)
  - `さんか` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_分岐あり診療科
- STT: 9 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器` (R1_STT_PROPER_NOUN_GROUP)
  - `こー下` (R1_STT_PROPER_NOUN_GROUP)
  - `コピー機` (R1_STT_PROPER_NOUN_GROUP)
  - `吸気` (R1_STT_PROPER_NOUN_GROUP)
  - `五九` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_分岐あり診療科（産婦人科）
- STT: 2 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `産婦人科` (R1_STT_PROPER_NOUN_GROUP)
  - `三婦人` (R1_STT_PROPER_NOUN_GROUP)

### 01_00_分岐なし診療科
- STT: 254 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `メーカー` (R1_STT_PROPER_NOUN_GROUP)
  - `リバー` (R1_STT_PROPER_NOUN_GROUP)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### わからない
- STT: 15 surfaces, OpenAI: 16 surfaces
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
  - `分からない`
  - `分からん`

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
- STT: 18 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `いーえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ううん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
- OpenAI サンプル:
  - `否定`
  - `違う`
  - `間違った`
  - `載っていません`
  - `載ってません`

### 否定単語
- STT: 5 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `違います` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いいえ違います` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ダメ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ノー` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `違い`
  - `違う`
  - `違って`
  - `間違えている`
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
- STT: 21 surfaces, OpenAI: 67 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `確認` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `3`
  - `Cancel`
  - `三`
  - `取り消す`
  - `4`

### 肯定
- STT: 14 surfaces, OpenAI: 12 surfaces
- STT サンプル:
  - `OK` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `いいです` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `オケー` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はーい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`
  - `受けます`
  - `初診です`
  - `大丈夫です。`
  - `配送です`

### 肯定単語
- STT: 21 surfaces, OpenAI: 12 surfaces
- STT サンプル:
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `OK` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `あっています` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってる` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `違いありません`
  - `違いない`
  - `正しいです`
  - `大丈夫`
  - `大丈夫です`

### 記載なし
- STT: 2 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `さいな` (R3_STT_KANA_VARIANT)
  - `さいなし` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `記載なし`
  - `一切`
  - `機材`
  - `記載`
