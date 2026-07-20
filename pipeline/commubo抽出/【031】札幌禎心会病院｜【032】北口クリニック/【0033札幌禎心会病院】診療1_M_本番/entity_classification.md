# Entity Classification Summary — 札幌禎心会病院 / 診療

対象 yaml: 10 本

  - `【031】札幌禎心会病院｜【032】北口クリニック/【0033札幌禎心会病院】診療1_M_本番/main.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0033札幌禎心会病院】診療1_M_本番/予約日の聞き取り.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0033札幌禎心会病院】診療1_M_本番/当日受診確認.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0033札幌禎心会病院】診療1_M_本番/情報提供書.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0033札幌禎心会病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0033札幌禎心会病院】診療1_M_本番/用件聞き取り.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0033札幌禎心会病院】診療1_M_本番/診察券番号聞き取り.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0033札幌禎心会病院】診療1_M_本番/診療科フリー.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0033札幌禎心会病院】診療1_M_本番/診療科聞き取り.yaml`
  - `【031】札幌禎心会病院｜【032】北口クリニック/【0033札幌禎心会病院】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 235 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 42 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 33 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 140 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 01_00_分岐なし診療科
- STT: 212 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `てんかん外来` (R1_STT_PROPER_NOUN_GROUP)
  - `てんかん` (R1_STT_PROPER_NOUN_GROUP)
  - `てんたん` (R1_STT_PROPER_NOUN_GROUP)
  - `てんぱん` (R1_STT_PROPER_NOUN_GROUP)
  - `印鑑が要らない` (R1_STT_PROPER_NOUN_GROUP)

### つなぎことば
- STT: 0 surfaces, OpenAI: 6 surfaces
- OpenAI サンプル:
  - `うん`
  - `あー`
  - `うーん`
  - `ええ`
  - `えーっと`

### もう一度
- STT: 0 surfaces, OpenAI: 2 surfaces
- OpenAI サンプル:
  - `もう一度`
  - `もう一回`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### キャンセル
- STT: 4 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `取り消す`

### 予約
- STT: 2 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `予約` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `お薬` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `お百`
  - `お役`
  - `ご予約`
  - `予約について`

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

### 代表案内診療科
- STT: 23 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `がんセカンドオピニオン外来` (R1_STT_PROPER_NOUN_GROUP)
  - `オピニオン` (R1_STT_PROPER_NOUN_GROUP)
  - `がんセカンドオピニオン` (R1_STT_PROPER_NOUN_GROUP)
  - `セカンド` (R1_STT_PROPER_NOUN_GROUP)
  - `セカンドオピニオン` (R1_STT_PROPER_NOUN_GROUP)

### 再診予約
- STT: 1 surfaces, OpenAI: 16 surfaces
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
- STT: 5 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `はじめて` (R3_STT_KANA_VARIANT)
  - `初めて` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `かかっていない` (R3_STT_KANA_VARIANT)
  - `かかってない` (R3_STT_KANA_VARIANT)
  - `まだ` (R3_STT_KANA_VARIANT)

### 初診予約
- STT: 9 surfaces, OpenAI: 12 surfaces
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

### 否定
- STT: 7 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `かかったことがある` (R3_STT_KANA_VARIANT → hearing_yesno_common)
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

### 変更
- STT: 2 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `変更` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `別の` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `延期`
  - `時間`
  - `日程`
  - `日付`
  - `判子`

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

### 情報提供書
- STT: 0 surfaces, OpenAI: 4 surfaces
- OpenAI サンプル:
  - `情報提供書`
  - `情報`
  - `情報提供`
  - `提供書`

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

### 確認
- STT: 3 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `確認` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `なくした` (R3_STT_KANA_VARIANT)
  - `忘れた` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `お聞き`
  - `教えて`
  - `調べて`
  - `分からない`
  - `分からん`

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
