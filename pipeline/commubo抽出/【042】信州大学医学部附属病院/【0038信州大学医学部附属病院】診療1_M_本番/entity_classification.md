# Entity Classification Summary — 信州大学医学部附属病院 / 診療

対象 yaml: 11 本

  - `【042】信州大学医学部附属病院/【0038信州大学医学部附属病院】診療1_M_本番/main.yaml`
  - `【042】信州大学医学部附属病院/【0038信州大学医学部附属病院】診療1_M_本番/予約日の聞き取り.yaml`
  - `【042】信州大学医学部附属病院/【0038信州大学医学部附属病院】診療1_M_本番/受診歴.yaml`
  - `【042】信州大学医学部附属病院/【0038信州大学医学部附属病院】診療1_M_本番/残薬確認.yaml`
  - `【042】信州大学医学部附属病院/【0038信州大学医学部附属病院】診療1_M_本番/理由_症状.yaml`
  - `【042】信州大学医学部附属病院/【0038信州大学医学部附属病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【042】信州大学医学部附属病院/【0038信州大学医学部附属病院】診療1_M_本番/用件.yaml`
  - `【042】信州大学医学部附属病院/【0038信州大学医学部附属病院】診療1_M_本番/用件未聴取.yaml`
  - `【042】信州大学医学部附属病院/【0038信州大学医学部附属病院】診療1_M_本番/診察券番号聞き取り.yaml`
  - `【042】信州大学医学部附属病院/【0038信州大学医学部附属病院】診療1_M_本番/診療科聞き取り.yaml`
  - `【042】信州大学医学部附属病院/【0038信州大学医学部附属病院】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 464 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 45 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 41 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 174 | OpenAI 正規化 |

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

### 00_00_04_産婦人科
- STT: 27 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `産科` (R1_STT_PROPER_NOUN_GROUP)
  - `お産` (R1_STT_PROPER_NOUN_GROUP)
  - `ささえる` (R1_STT_PROPER_NOUN_GROUP)
  - `さんか` (R1_STT_PROPER_NOUN_GROUP)
  - `じゅうろく` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_05_内分泌
- STT: 32 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `糖尿病内分泌代謝内科` (R1_STT_PROPER_NOUN_GROUP)
  - `あ0か` (R1_STT_PROPER_NOUN_GROUP)
  - `か0か` (R1_STT_PROPER_NOUN_GROUP)
  - `カレー` (R1_STT_PROPER_NOUN_GROUP)
  - `カレー総合` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_分岐あり診療科
- STT: 30 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器` (R1_STT_PROPER_NOUN_GROUP)
  - `いちない` (R1_STT_PROPER_NOUN_GROUP)
  - `こー下` (R1_STT_PROPER_NOUN_GROUP)
  - `こない` (R1_STT_PROPER_NOUN_GROUP)
  - `コピー機` (R1_STT_PROPER_NOUN_GROUP)

### 01_00_分岐なし診療科
- STT: 332 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `アレルギー内科` (R1_STT_PROPER_NOUN_GROUP)
  - `アレルギー` (R1_STT_PROPER_NOUN_GROUP)
  - `てんかん外来` (R1_STT_PROPER_NOUN_GROUP)
  - `てんかん` (R1_STT_PROPER_NOUN_GROUP)
  - `転換` (R1_STT_PROPER_NOUN_GROUP)

### CT
- STT: 0 surfaces, OpenAI: 4 surfaces
- OpenAI サンプル:
  - `CT`
  - `しーてぃ`
  - `しーてー`
  - `してぃ`

### MRI
- STT: 0 surfaces, OpenAI: 7 surfaces
- OpenAI サンプル:
  - `MRI`
  - `M`
  - `R`
  - `あーるあい`
  - `えむ`

### もう一度
- STT: 6 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `まって` (R3_STT_KANA_VARIANT)
  - `もいちど` (R3_STT_KANA_VARIANT)
  - `もういっかい` (R3_STT_KANA_VARIANT)
  - `もーいちど` (R3_STT_KANA_VARIANT)
  - `もっかい` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `もう一度`
  - `もう一_回`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### わからない
- STT: 9 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しらん` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `もっていない` (R3_STT_KANA_VARIANT → hearing_unknown)
- OpenAI サンプル:
  - `知らない`

### フィラー
- STT: 2 surfaces, OpenAI: 22 surfaces
- STT サンプル:
  - `おー` (R2_STT_TEMPLATE_REUSE → hearing_phone_number)
  - `なんか` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `フィラー`
  - `あー`
  - `あのー`
  - `いやー`
  - `うー`

### 内科
- STT: 2 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `内科` (R1_STT_PROPER_NOUN_GROUP)
  - `ないか` (R1_STT_PROPER_NOUN_GROUP)

### 処方されない
- STT: 0 surfaces, OpenAI: 7 surfaces
- OpenAI サンプル:
  - `処方`
  - `3`
  - `三`
  - `三番`
  - `処方されない`

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
- STT: 3 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
- OpenAI サンプル:
  - `いーえ`
  - `いや`
  - `じゃない`
  - `ちがう`
  - `まちがった`

### 否定エンティティ
- STT: 3 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえいえ` (R3_STT_KANA_VARIANT)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `2`
  - `足りない`
  - `足りません`
  - `二番`

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

### 外科
- STT: 5 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `0か` (R1_STT_PROPER_NOUN_GROUP)
  - `ケイコ` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `元か` (R1_STT_PROPER_NOUN_GROUP)

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
- STT: 17 surfaces, OpenAI: 81 surfaces
- STT サンプル:
  - `インフルエンザ` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `インフル` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `1番`
  - `一`
  - `一新薬`
  - `一番`
  - `感染`

### 肯定
- STT: 13 surfaces, OpenAI: 10 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってる` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうそう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `その通りです`
  - `異常部`
  - `丈夫`
  - `大丈夫`
  - `配送です`

### 肯定エンティティ
- STT: 4 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ある` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いいです` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
- OpenAI サンプル:
  - `1`
  - `一`
  - `一番`
  - `足りる`
  - `余り`

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
