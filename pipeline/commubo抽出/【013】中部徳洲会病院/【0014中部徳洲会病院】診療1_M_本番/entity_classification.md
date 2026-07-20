# Entity Classification Summary — 中部徳洲会病院 / 診療

対象 yaml: 8 本

  - `【013】中部徳洲会病院/【0014中部徳洲会病院】診療1_M_本番/main.yaml`
  - `【013】中部徳洲会病院/【0014中部徳洲会病院】診療1_M_本番/予約日.yaml`
  - `【013】中部徳洲会病院/【0014中部徳洲会病院】診療1_M_本番/新：連絡先聴取.yaml`
  - `【013】中部徳洲会病院/【0014中部徳洲会病院】診療1_M_本番/旧：生年月日聴取.yaml`
  - `【013】中部徳洲会病院/【0014中部徳洲会病院】診療1_M_本番/生年月日聴取※4_30 フリーへ.yaml`
  - `【013】中部徳洲会病院/【0014中部徳洲会病院】診療1_M_本番/用件.yaml`
  - `【013】中部徳洲会病院/【0014中部徳洲会病院】診療1_M_本番/紹介状有無.yaml`
  - `【013】中部徳洲会病院/【0014中部徳洲会病院】診療1_M_本番/診療科.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 373 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 38 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 40 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 91 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 00_00_01_呼吸器
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `レッカー` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_01_消化器
- STT: 4 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `消化器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `消化器内科` (R1_STT_PROPER_NOUN_GROUP)
  - `内科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_01_脳神経
- STT: 17 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `脳神経外科` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `レッカー` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_分岐あり診療科
- STT: 8 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器` (R1_STT_PROPER_NOUN_GROUP)
  - `コピー機` (R1_STT_PROPER_NOUN_GROUP)
  - `応急義` (R1_STT_PROPER_NOUN_GROUP)
  - `吸気` (R1_STT_PROPER_NOUN_GROUP)
  - `五九` (R1_STT_PROPER_NOUN_GROUP)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### わからない
- STT: 11 surfaces, OpenAI: 9 surfaces
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

### 予防接種
- STT: 9 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `予防接種` (R1_STT_PROPER_NOUN_GROUP)
  - `インフル` (R1_STT_PROPER_NOUN_GROUP)
  - `の棒全紙` (R1_STT_PROPER_NOUN_GROUP)
  - `ワクチン` (R1_STT_PROPER_NOUN_GROUP)
  - `女房先週` (R1_STT_PROPER_NOUN_GROUP)

### 人間ドックや健診の予約
- STT: 24 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `健診` (R1_STT_PROPER_NOUN_GROUP)
  - `KC` (R1_STT_PROPER_NOUN_GROUP)
  - `センター` (R1_STT_PROPER_NOUN_GROUP)
  - `ドック` (R1_STT_PROPER_NOUN_GROUP)
  - `のドック` (R1_STT_PROPER_NOUN_GROUP)

### 分岐なし診療科
- STT: 299 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `SH外来` (R1_STT_PROPER_NOUN_GROUP)
  - `ミスー外来` (R1_STT_PROPER_NOUN_GROUP)
  - `営業の検査` (R1_STT_PROPER_NOUN_GROUP)
  - `性病` (R1_STT_PROPER_NOUN_GROUP)
  - `二千一外来` (R1_STT_PROPER_NOUN_GROUP)

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
- STT: 14 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ちがいまーす` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `EHが今`
  - `そうじゃないねん`
  - `そうちゃうねん`
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
- STT: 16 surfaces, OpenAI: 45 surfaces
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

### 肯定
- STT: 13 surfaces, OpenAI: 11 surfaces
- STT サンプル:
  - `OK` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `してまーす` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうでーす` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そのとおり` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`
  - `その通り`
  - `異常部`
  - `合って`
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
