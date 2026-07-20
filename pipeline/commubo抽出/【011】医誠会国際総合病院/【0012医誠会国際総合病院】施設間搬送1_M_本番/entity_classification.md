# Entity Classification Summary — 医誠会国際総合病院 / 施設間搬送

対象 yaml: 11 本

  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】施設間搬送1_M_本番/main.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】施設間搬送1_M_本番/中村さん作成：搬送or来院.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】施設間搬送1_M_本番/住所聞き取り.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】施設間搬送1_M_本番/個人情報聴取.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】施設間搬送1_M_本番/患者名聴取.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】施設間搬送1_M_本番/搬送or来院.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】施設間搬送1_M_本番/施設名聴取.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】施設間搬送1_M_本番/状態聴取.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】施設間搬送1_M_本番/緊急手術必要か確認.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】施設間搬送1_M_本番/血圧や体温の聴取（旧バイタル）.yaml`
  - `【011】医誠会国際総合病院/【0012医誠会国際総合病院】施設間搬送1_M_本番/連絡先聴取.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 0 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 17 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 33 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 67 | OpenAI 正規化 |

## 詳細 (entity 単位)

### もう一回、間違えた
- STT: 10 surfaces, OpenAI: 9 surfaces
- STT サンプル:
  - `まちがい` (R3_STT_KANA_VARIANT)
  - `まちがえ` (R3_STT_KANA_VARIANT)
  - `もういちど` (R3_STT_KANA_VARIANT)
  - `もういっかい` (R3_STT_KANA_VARIANT)
  - `もっかい` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `間違え`
  - `もう１回`
  - `もう一回`
  - `もう一度`
  - `間違い`

### もう一度
- STT: 0 surfaces, OpenAI: 2 surfaces
- OpenAI サンプル:
  - `もう一度`
  - `もう一回`

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
- STT: 8 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `違う`
  - `間違い`

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

### 救急搬送希望
- STT: 2 surfaces, OpenAI: 12 surfaces
- STT サンプル:
  - `いち` (R3_STT_KANA_VARIANT)
  - `いち` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `1`
  - `1番`
  - `一番`
  - `救急`
  - `搬送`

### 直接来院
- STT: 2 surfaces, OpenAI: 13 surfaces
- STT サンプル:
  - `に` (R3_STT_KANA_VARIANT)
  - `に` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `2`
  - `行きます`
  - `行く`
  - `自分で`
  - `直接`

### 肯定
- STT: 4 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `いち` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `それです` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`
  - `1`
  - `1番`
  - `お願いします`
  - `一番`

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

### 間違い
- STT: 0 surfaces, OpenAI: 4 surfaces
- OpenAI サンプル:
  - `間違い`
  - `違い`
  - `違う`
  - `間違え`
