# Entity Classification Summary — 飯塚病院 予防医学センター / 健診

対象 yaml: 10 本

  - `【076】飯塚病院 予防医学センター/【【0000飯塚病院 予防医学センター】健診1_M_本番/main.yaml`
  - `【076】飯塚病院 予防医学センター/【【0000飯塚病院 予防医学センター】健診1_M_本番/予約日.yaml`
  - `【076】飯塚病院 予防医学センター/【【0000飯塚病院 予防医学センター】健診1_M_本番/企業分岐.yaml`
  - `【076】飯塚病院 予防医学センター/【【0000飯塚病院 予防医学センター】健診1_M_本番/変更内容.yaml`
  - `【076】飯塚病院 予防医学センター/【【0000飯塚病院 予防医学センター】健診1_M_本番/生年月日.yaml`
  - `【076】飯塚病院 予防医学センター/【【0000飯塚病院 予防医学センター】健診1_M_本番/用件.yaml`
  - `【076】飯塚病院 予防医学センター/【【0000飯塚病院 予防医学センター】健診1_M_本番/種類.yaml`
  - `【076】飯塚病院 予防医学センター/【【0000飯塚病院 予防医学センター】健診1_M_本番/胃検査内容.yaml`
  - `【076】飯塚病院 予防医学センター/【【0000飯塚病院 予防医学センター】健診1_M_本番/胃検査希望有無.yaml`
  - `【076】飯塚病院 予防医学センター/【【0000飯塚病院 予防医学センター】健診1_M_本番/連絡先.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 68 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 61 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 44 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 202 | OpenAI 正規化 |

## 詳細 (entity 単位)

### うん
- STT: 0 surfaces, OpenAI: 2 surfaces
- OpenAI サンプル:
  - `うん`
  - `えーと`

### もう一度
- STT: 0 surfaces, OpenAI: 5 surfaces
- OpenAI サンプル:
  - `もう一度`
  - `一回`
  - `一階`
  - `再度`
  - `聞き直したい`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### 予約キャンセル
- STT: 3 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `予約キャンセル`

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

### 予約変更
- STT: 2 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `別の` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `変更` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `予約変更`
  - `時間`
  - `日程`
  - `日付`
  - `変え`

### 予約確認
- STT: 6 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `その他` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `なくした` (R3_STT_KANA_VARIANT)
  - `確認` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `忘れた` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `問い合わせ` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `予約確認`
  - `教えて`
  - `調べて`
  - `分からない`
  - `分からん`

### 分からない
- STT: 7 surfaces, OpenAI: 9 surfaces
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
- STT: 13 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `ちがう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ちゃうちゃう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `まちがった` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `会社`
  - `企業`
  - `法人`
  - `否定`
  - `EHが今`

### 否定単語
- STT: 5 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `違います` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ダメ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ちがう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ノー` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `違い`
  - `違いました`
  - `違う`
  - `違って`
  - `駄目`

### 変更しない
- STT: 1 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `そのまま` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `変更しない`
  - `変えません`
  - `変更しません`

### 変更する
- STT: 0 surfaces, OpenAI: 3 surfaces
- OpenAI サンプル:
  - `変更する`
  - `変えます`
  - `変更します`

### 変更内容
- STT: 19 surfaces, OpenAI: 42 surfaces
- STT サンプル:
  - `オプション` (R3_STT_KANA_VARIANT)
  - `コース` (R3_STT_KANA_VARIANT)
  - `メニュー` (R3_STT_KANA_VARIANT)
  - `健診` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `胃カメラ検査` (R1_STT_PROPER_NOUN_GROUP)
- OpenAI サンプル:
  - `受診内容`
  - `1`
  - `オプション追加`
  - `一`
  - `一番`

### 定期受診
- STT: 1 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `循環器` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
- OpenAI サンプル:
  - `定期受診`
  - `受診予約`
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

### 新規予約
- STT: 2 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `新規予約` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `初診` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `健診の予約`
  - `健診予約`
  - `取りたい`
  - `取得`
  - `紹介状`

### 日にちのみ
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `日にちのみ`

### 用件
- STT: 26 surfaces, OpenAI: 57 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `新規` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `3`
  - `三`
  - `取り消す`
  - `1`
  - `TC`

### 種類
- STT: 8 surfaces, OpenAI: 9 surfaces
- STT サンプル:
  - `その他` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `問い合わせ` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `けんぽ` (R3_STT_KANA_VARIANT)
  - `人間ドック` (R1_STT_PROPER_NOUN_GROUP)
  - `1` (R1_STT_PROPER_NOUN_GROUP)
- OpenAI サンプル:
  - `3`
  - `その他の健診`
  - `三`
  - `般検診`
  - `協会けんぽ`

### 肯定
- STT: 6 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうそう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はーい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `個人`
  - `配送です`
  - `肯定`
  - `異常部`
  - `丈夫`

### 肯定単語
- STT: 11 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `OK` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `あっています` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってる` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `大丈夫`
  - `問題ありません`
  - `問題ない`

### 診療科
- STT: 48 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `IVRセンター` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `アレルギー科` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `オンコロジー` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `セカンドオピニオン` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `フット外来` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
