# Entity Classification Summary — 中部徳洲会病院 / 医療福祉相談室

対象 yaml: 2 本

  - `【013】中部徳洲会病院/【中部徳洲会病院】医療福祉相談室1_M_本番/0307：看護師復唱→看護師 へ.yaml`
  - `【013】中部徳洲会病院/【中部徳洲会病院】医療福祉相談室1_M_本番/main.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 0 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 5 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 121 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 105 | OpenAI 正規化 |

## 詳細 (entity 単位)

### わからない
- STT: 7 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しりません` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかんない` (R3_STT_KANA_VARIANT → hearing_unknown)
- OpenAI サンプル:
  - `解らない`
  - `書いていない`
  - `知らない`
  - `分からない`
  - `分からん`

### 下地
- STT: 3 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `しもじ` (R3_STT_KANA_VARIANT)
  - `シモジ` (R3_STT_KANA_VARIANT)
  - `しもち` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `下地`
  - `C文字`

### 下地個人判別
- STT: 6 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `こうたろう` (R3_STT_KANA_VARIANT)
  - `コウタロウ` (R3_STT_KANA_VARIANT)
  - `シモジコウタロウ` (R3_STT_KANA_VARIANT)
  - `あおい` (R3_STT_KANA_VARIANT)
  - `アオイ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `下地光太郎`
  - `硬貨ろう`
  - `下地碧生`
  - `下地青い`
  - `青い`

### 否定
- STT: 5 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ちがう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `EHが今`
  - `違う人です`

### 大城
- STT: 3 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `オーシロ` (R3_STT_KANA_VARIANT)
  - `オオシロ` (R3_STT_KANA_VARIANT)
  - `おーヒロ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `大城`
  - `503`

### 大城個人判別
- STT: 7 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `おおしろみのる` (R3_STT_KANA_VARIANT)
  - `オオシロミノル` (R3_STT_KANA_VARIANT)
  - `みのる` (R3_STT_KANA_VARIANT)
  - `ミノル` (R3_STT_KANA_VARIANT)
  - `おおしろなおゆき` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `大城実`
  - `大城尚幸`

### 山城
- STT: 2 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `ヤシロ` (R3_STT_KANA_VARIANT)
  - `ヤマシロ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `山城`

### 山城個人判別
- STT: 3 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `アオイ` (R3_STT_KANA_VARIANT)
  - `ヨウコ` (R3_STT_KANA_VARIANT)
  - `リョウコ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `山城碧生`
  - `青い山`
  - `山城諒子`
  - `看護師の山城さん`

### 担当者判別
- STT: 87 surfaces, OpenAI: 73 surfaces
- STT サンプル:
  - `カオリ` (R3_STT_KANA_VARIANT)
  - `ファーロー` (R3_STT_KANA_VARIANT)
  - `コウタロウ` (R3_STT_KANA_VARIANT)
  - `シモジ` (R3_STT_KANA_VARIANT)
  - `しもじ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `ファーロー香織`
  - `方増産`
  - `下地光太郎`
  - `下地`
  - `下地碧生`

### 肯定
- STT: 3 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はーい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`
  - `その通りです`
  - `異常部`
  - `丈夫`
  - `大丈夫`
