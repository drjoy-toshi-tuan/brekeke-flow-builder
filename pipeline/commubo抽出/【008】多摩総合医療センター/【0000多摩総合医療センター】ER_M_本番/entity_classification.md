# Entity Classification Summary — 多摩総合医療センター / ER

対象 yaml: 1 本

  - `【008】多摩総合医療センター/【0000多摩総合医療センター】ER_M_本番/main.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 0 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 2 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 7 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 12 | OpenAI 正規化 |

## 詳細 (entity 単位)

### もう一度
- STT: 0 surfaces, OpenAI: 4 surfaces
- OpenAI サンプル:
  - `もう一度`
  - `一回`
  - `一度`
  - `再度`

### 否定（エンティティ）
- STT: 6 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT)
  - `いや` (R3_STT_KANA_VARIANT)
  - `じゃない` (R3_STT_KANA_VARIANT)
  - `ちがう` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `否定`
  - `当てはまらない`

### 肯定（エンティティ）
- STT: 3 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `いいです` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `はーい` (R3_STT_KANA_VARIANT)
  - `よろしいです` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `肯定`
  - `異常部`
  - `丈夫`
  - `大丈夫`
  - `当てはまる`
