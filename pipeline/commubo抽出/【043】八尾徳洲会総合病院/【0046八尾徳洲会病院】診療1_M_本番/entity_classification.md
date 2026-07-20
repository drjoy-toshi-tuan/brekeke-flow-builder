# Entity Classification Summary — 八尾徳洲会総合病院 / 診療

対象 yaml: 11 本

  - `【043】八尾徳洲会総合病院/【0046八尾徳洲会病院】診療1_M_本番/main.yaml`
  - `【043】八尾徳洲会総合病院/【0046八尾徳洲会病院】診療1_M_本番/Y_N.yaml`
  - `【043】八尾徳洲会総合病院/【0046八尾徳洲会病院】診療1_M_本番/フリーの内容確認.yaml`
  - `【043】八尾徳洲会総合病院/【0046八尾徳洲会病院】診療1_M_本番/フリーの変更理由.yaml`
  - `【043】八尾徳洲会総合病院/【0046八尾徳洲会病院】診療1_M_本番/予約希望日.yaml`
  - `【043】八尾徳洲会総合病院/【0046八尾徳洲会病院】診療1_M_本番/予約日.yaml`
  - `【043】八尾徳洲会総合病院/【0046八尾徳洲会病院】診療1_M_本番/用件聞き取り.yaml`
  - `【043】八尾徳洲会総合病院/【0046八尾徳洲会病院】診療1_M_本番/終話電話番号確認.yaml`
  - `【043】八尾徳洲会総合病院/【0046八尾徳洲会病院】診療1_M_本番/診察券番号聞き取り.yaml`
  - `【043】八尾徳洲会総合病院/【0046八尾徳洲会病院】診療1_M_本番/診療科.yaml`
  - `【043】八尾徳洲会総合病院/【0046八尾徳洲会病院】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 940 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 51 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 78 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 144 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 01_00_分岐なし診療科
- STT: 463 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `SAS外来` (R1_STT_PROPER_NOUN_GROUP)
  - `SDS外来` (R1_STT_PROPER_NOUN_GROUP)
  - `SFがいない。` (R1_STT_PROPER_NOUN_GROUP)
  - `SPS外来` (R1_STT_PROPER_NOUN_GROUP)
  - `SSがや。` (R1_STT_PROPER_NOUN_GROUP)

### ありません
- STT: 11 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `あれへん` (R3_STT_KANA_VARIANT)
  - `いつでも` (R3_STT_KANA_VARIANT)
  - `けっこう` (R3_STT_KANA_VARIANT)
  - `とくに` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `結構です`

### もう一度
- STT: 0 surfaces, OpenAI: 2 surfaces
- OpenAI サンプル:
  - `もう一度`
  - `もう一回`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### わからない
- STT: 12 surfaces, OpenAI: 8 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `おぼえて` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しらね` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しらん` (R3_STT_KANA_VARIANT → hearing_unknown)
- OpenAI サンプル:
  - `覚えて`
  - `知らない`
  - `知らね`
  - `知らん`
  - `分からない`

### キャンセル
- STT: 7 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `にばん` (R3_STT_KANA_VARIANT)
  - `にばんめ` (R3_STT_KANA_VARIANT)
  - `ふたつめ` (R3_STT_KANA_VARIANT)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `２`
  - `2番`
  - `取り消す`
  - `二`
  - `二つ目`

### 予約以外
- STT: 4 surfaces, OpenAI: 18 surfaces
- STT サンプル:
  - `アクセス` (R3_STT_KANA_VARIANT)
  - `くすり` (R3_STT_KANA_VARIANT)
  - `じゃない` (R3_STT_KANA_VARIANT)
  - `ではない` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `予約以外`
  - `お見舞い`
  - `違い`
  - `違う`
  - `飲み方`

### 健診センター
- STT: 15 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `健診センター` (R1_STT_PROPER_NOUN_GROUP)
  - `PD便座` (R1_STT_PROPER_NOUN_GROUP)
  - `エンジンセンター` (R1_STT_PROPER_NOUN_GROUP)
  - `ドッグ` (R1_STT_PROPER_NOUN_GROUP)
  - `音信センター` (R1_STT_PROPER_NOUN_GROUP)

### 再診予約
- STT: 1 surfaces, OpenAI: 8 surfaces
- STT サンプル:
  - `再診` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `はい新薬`
  - `安心`
  - `再診予約`
  - `最新`
  - `最新訳`

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

### 初めて
- STT: 1 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `はじめて` (R3_STT_KANA_VARIANT)

### 初診予約
- STT: 5 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `初診` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はじめて` (R3_STT_KANA_VARIANT)
  - `初めて` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `新規` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `新規予約` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `禁忌`
  - `写真`
  - `終身`
  - `初診予約`
  - `新規の予約`

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

### 受付不可診療科：
- STT: 27 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `がん診療` (R1_STT_PROPER_NOUN_GROUP)
  - `がん相談支援センター` (R1_STT_PROPER_NOUN_GROUP)
  - `セカンドオピニオン外来` (R1_STT_PROPER_NOUN_GROUP)
  - `オピニオン` (R1_STT_PROPER_NOUN_GROUP)
  - `セカンド` (R1_STT_PROPER_NOUN_GROUP)

### 否定
- STT: 14 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `しらへん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`

### 否定のエンティティ
- STT: 5 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえいえ` (R3_STT_KANA_VARIANT)
  - `ちゃうちゃう` (R3_STT_KANA_VARIANT)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `違います` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
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

### 変更
- STT: 6 surfaces, OpenAI: 10 surfaces
- STT サンプル:
  - `変更` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `イチ` (R3_STT_KANA_VARIANT)
  - `いち` (R3_STT_KANA_VARIANT)
  - `いちばん` (R3_STT_KANA_VARIANT)
  - `ひとつめ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `1`
  - `一`
  - `一つ目`
  - `一番`
  - `延期`

### 定期受診
- STT: 1 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `再診` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `定期受診`
  - `はい新薬`
  - `最新`
  - `三新薬`
  - `定期`

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

### 新規
- STT: 5 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `新規` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `はじめて` (R3_STT_KANA_VARIANT)
  - `初めて` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `初診` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `新規予約` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `禁忌`
  - `写真`
  - `終身`
  - `新規の予約`
  - `新旧`

### 検査名
- STT: 397 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `CT` (R1_STT_PROPER_NOUN_GROUP)
  - `CD` (R1_STT_PROPER_NOUN_GROUP)
  - `ＣＤ` (R1_STT_PROPER_NOUN_GROUP)
  - `ＣＴ` (R1_STT_PROPER_NOUN_GROUP)
  - `CT検査` (R1_STT_PROPER_NOUN_GROUP)

### 歯科口腔外科
- STT: 38 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `歯科口腔外科` (R1_STT_PROPER_NOUN_GROUP)
  - `４` (R1_STT_PROPER_NOUN_GROUP)
  - `４ばん` (R1_STT_PROPER_NOUN_GROUP)
  - `4番` (R1_STT_PROPER_NOUN_GROUP)
  - `Cか` (R1_STT_PROPER_NOUN_GROUP)

### 病児保育診察
- STT: 0 surfaces, OpenAI: 3 surfaces
- OpenAI サンプル:
  - `病児保育診察`
  - `秒に保育`
  - `保育`

### 確認
- STT: 8 surfaces, OpenAI: 11 surfaces
- STT サンプル:
  - `確認` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `さん` (R3_STT_KANA_VARIANT)
  - `サン` (R3_STT_KANA_VARIANT)
  - `さんばん` (R3_STT_KANA_VARIANT)
  - `さんばんめ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `3`
  - `お聞き`
  - `教えて`
  - `三つ目`
  - `三番`

### 肯定
- STT: 14 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `うん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ええで` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ええよ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `おう` (R2_STT_TEMPLATE_REUSE → hearing_phone_number)
  - `おっけー` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`

### 肯定エンティティ
- STT: 3 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いいです` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `あっている`
  - `いい`
  - `そうそう`
  - `へい`

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

### 診察予約
- STT: 3 surfaces, OpenAI: 24 surfaces
- STT サンプル:
  - `はじめて` (R3_STT_KANA_VARIANT)
  - `初めて` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `新規` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `診察予約`
  - `を取る`
  - `印刷`
  - `豪ドル`
  - `撮りたい`

### 間違い
- STT: 0 surfaces, OpenAI: 3 surfaces
- OpenAI サンプル:
  - `間違い`
  - `違う`
  - `間違え`
