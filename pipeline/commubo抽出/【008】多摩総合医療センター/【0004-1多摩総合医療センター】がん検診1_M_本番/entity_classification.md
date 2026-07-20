# Entity Classification Summary — 多摩総合医療センター / がん検診

対象 yaml: 9 本

  - `【008】多摩総合医療センター/【0004-1多摩総合医療センター】がん検診1_M_本番/7年受診歴有無確認.yaml`
  - `【008】多摩総合医療センター/【0004-1多摩総合医療センター】がん検診1_M_本番/main.yaml`
  - `【008】多摩総合医療センター/【0004-1多摩総合医療センター】がん検診1_M_本番/受診案内.yaml`
  - `【008】多摩総合医療センター/【0004-1多摩総合医療センター】がん検診1_M_本番/氏名聴取.yaml`
  - `【008】多摩総合医療センター/【0004-1多摩総合医療センター】がん検診1_M_本番/生年月日聴取.yaml`
  - `【008】多摩総合医療センター/【0004-1多摩総合医療センター】がん検診1_M_本番/診察券番号.yaml`
  - `【008】多摩総合医療センター/【0004-1多摩総合医療センター】がん検診1_M_本番/診察家番号.yaml`
  - `【008】多摩総合医療センター/【0004-1多摩総合医療センター】がん検診1_M_本番/連絡先聴取.yaml`
  - `【008】多摩総合医療センター/【0004-1多摩総合医療センター】がん検診1_M_本番/都立がん検診診察券番号.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 0 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 27 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 18 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 45 | OpenAI 正規化 |

## 詳細 (entity 単位)

### もう一度
- STT: 0 surfaces, OpenAI: 8 surfaces
- OpenAI サンプル:
  - `もう一度`
  - `もう1度`
  - `もう一回`
  - `再度`
  - `1回`

### わからない
- STT: 2 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `知りません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `知らない`
  - `分からない`
  - `分かりません`

### 分からない
- STT: 8 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `知りません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `知りません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `知らない`
  - `分かりません`
  - `分からない`
  - `分かりません`
  - `解らない`

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
- STT: 5 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いません` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `されていない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `何度`
  - `何度かあります`
  - `何度かある`
  - `否定`

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

### 肯定
- STT: 6 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はじめて` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `初めて` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `初めてです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `その通り`
  - `受けたことない`
  - `受け取っている`
  - `受け取ってます`
  - `受け取ってる`

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
