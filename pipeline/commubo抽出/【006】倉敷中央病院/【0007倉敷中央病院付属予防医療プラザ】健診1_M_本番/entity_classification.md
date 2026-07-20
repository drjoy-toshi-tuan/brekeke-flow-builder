# Entity Classification Summary — 倉敷中央病院 / 健診

対象 yaml: 7 本

  - `【006】倉敷中央病院/【0007倉敷中央病院付属予防医療プラザ】健診1_M_本番/予約日聞き取り.yaml`
  - `【006】倉敷中央病院/【0007倉敷中央病院付属予防医療プラザ】健診1_M_本番/変更項目：受診日orその他.yaml`
  - `【006】倉敷中央病院/【0007倉敷中央病院付属予防医療プラザ】健診1_M_本番/希望時期.yaml`
  - `【006】倉敷中央病院/【0007倉敷中央病院付属予防医療プラザ】健診1_M_本番/生年月日聴取.yaml`
  - `【006】倉敷中央病院/【0007倉敷中央病院付属予防医療プラザ】健診1_M_本番/用件聞取り（復唱無し）.yaml`
  - `【006】倉敷中央病院/【0007倉敷中央病院付属予防医療プラザ】健診1_M_本番/追加質問.yaml`
  - `【006】倉敷中央病院/【0007倉敷中央病院付属予防医療プラザ】健診1_M_本番/連絡先聴取.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- (なし)

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 0 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 43 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 43 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 134 | OpenAI 正規化 |

## 詳細 (entity 単位)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### 予約日なし
- STT: 8 surfaces, OpenAI: 10 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT)
  - `しりません` (R3_STT_KANA_VARIANT)
  - `まだ` (R3_STT_KANA_VARIANT)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `覚えてない`
  - `決まってない`
  - `決まってません`
  - `決めてない`
  - `書いていない`

### 分からない
- STT: 4 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ません` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `分からない`
  - `解らない`
  - `解らへん`
  - `解りません`
  - `分からへん`

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
- STT: 4 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
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
  - `EHが今`

### 変更内容
- STT: 8 surfaces, OpenAI: 38 surfaces
- STT サンプル:
  - `その他` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `オプション` (R3_STT_KANA_VARIANT)
  - `コース` (R3_STT_KANA_VARIANT)
  - `ないよ` (R3_STT_KANA_VARIANT)
  - `メニュー` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `その他の変更`
  - `以外`
  - `検査`
  - `種類`
  - `受診日外の変更`

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

### 次へ
- STT: 3 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `つぎ` (R3_STT_KANA_VARIANT)
  - `ツギ` (R3_STT_KANA_VARIANT)
  - `なし` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `次へ`
  - `次`

### 用件
- STT: 25 surfaces, OpenAI: 47 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `予約のキャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `取り消す`
  - `エンジンの予約`
  - `ご審査の予約`
  - `ご診断の予約`
  - `銀行診断休薬`

### 肯定
- STT: 1 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `よろしい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`
  - `異常部`
  - `丈夫`
  - `大丈夫`

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

### 肯定（エンティティ）
- STT: 1 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `はーい` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `肯定`
  - `異常部`
  - `丈夫`
  - `大丈夫`
  - `配送です`
