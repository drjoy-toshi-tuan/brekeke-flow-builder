# Entity Classification Summary — 松本協立病院 / 診療

対象 yaml: 20 本

  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/main.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/一般内科案内→不明点確認.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/予約日の聞き取り.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/再予約希望有無.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/医師名聴取.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/医師確認（循環器内科）.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/受診希望確認（心臓血管外科）.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/小児科リハビリ確認.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/小児科対象確認.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/希望日聞き取り.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/当日予約確認.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/後日予約希望有無聞き取り.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/検査名聞き取り.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/用件聞き取り.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/紹介状有無聞き取り.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/診察券番号聞き取り.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/診療科聞き取り.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/診療科聞き取り（当日、発熱外来あり）.yaml`
  - `【041】松本協立病院/【0037松本協立病院】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 510 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 68 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 86 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 203 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 00_整形外科（後日予約受付）
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `整形外科` (R1_STT_PROPER_NOUN_GROUP)
  - `K外科` (R1_STT_PROPER_NOUN_GROUP)
  - `TK` (R1_STT_PROPER_NOUN_GROUP)
  - `えー外科` (R1_STT_PROPER_NOUN_GROUP)
  - `せいけい` (R1_STT_PROPER_NOUN_GROUP)

### 01_00_初診紹介状必須_診療科
- STT: 127 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器内科` (R1_STT_PROPER_NOUN_GROUP)
  - `こーない` (R1_STT_PROPER_NOUN_GROUP)
  - `吸気内科` (R1_STT_PROPER_NOUN_GROUP)
  - `呼吸器` (R1_STT_PROPER_NOUN_GROUP)
  - `呼内` (R1_STT_PROPER_NOUN_GROUP)

### 01_発熱外来
- STT: 4 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `発熱外来` (R1_STT_PROPER_NOUN_GROUP)
  - `感染症` (R1_STT_PROPER_NOUN_GROUP)
  - `熱がある` (R1_STT_PROPER_NOUN_GROUP)
  - `発熱` (R1_STT_PROPER_NOUN_GROUP)

### 02_00_初診紹介状不要_診療科
- STT: 47 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `スマートウォッチ外来` (R1_STT_PROPER_NOUN_GROUP)
  - `アップルウォッチ` (R1_STT_PROPER_NOUN_GROUP)
  - `ウォッチ` (R1_STT_PROPER_NOUN_GROUP)
  - `スマートウォッチ` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)

### 02_一般内科誘導_診療科
- STT: 50 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器内科` (R1_STT_PROPER_NOUN_GROUP)
  - `こーない` (R1_STT_PROPER_NOUN_GROUP)
  - `吸気内科` (R1_STT_PROPER_NOUN_GROUP)
  - `呼吸器` (R1_STT_PROPER_NOUN_GROUP)
  - `呼内` (R1_STT_PROPER_NOUN_GROUP)

### 03_予約センター転送_診療科
- STT: 98 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `スマートウォッチ外来` (R1_STT_PROPER_NOUN_GROUP)
  - `アップルウォッチ` (R1_STT_PROPER_NOUN_GROUP)
  - `ウォッチ` (R1_STT_PROPER_NOUN_GROUP)
  - `スマートウォッチ` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)

### 04_00_別窓口案内_診療科
- STT: 33 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `歯科センター` (R1_STT_PROPER_NOUN_GROUP)
  - `Cか` (R1_STT_PROPER_NOUN_GROUP)
  - `ああいい車` (R1_STT_PROPER_NOUN_GROUP)
  - `ああ一緒` (R1_STT_PROPER_NOUN_GROUP)
  - `はーいい車` (R1_STT_PROPER_NOUN_GROUP)

### 04_別窓口案内_診療科
- STT: 39 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `歯科センター` (R1_STT_PROPER_NOUN_GROUP)
  - `Cか` (R1_STT_PROPER_NOUN_GROUP)
  - `ああいい車` (R1_STT_PROPER_NOUN_GROUP)
  - `ああ一緒` (R1_STT_PROPER_NOUN_GROUP)
  - `はーいい車` (R1_STT_PROPER_NOUN_GROUP)

### 05_00_対象外_診療科
- STT: 21 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `失神外来` (R1_STT_PROPER_NOUN_GROUP)
  - `しっしん` (R1_STT_PROPER_NOUN_GROUP)
  - `シッシン` (R1_STT_PROPER_NOUN_GROUP)
  - `失神` (R1_STT_PROPER_NOUN_GROUP)
  - `放射線科` (R1_STT_PROPER_NOUN_GROUP)

### 2階
- STT: 2 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `にかい` (R3_STT_KANA_VARIANT)
  - `小児` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
- OpenAI サンプル:
  - `2階`
  - `向かい`
  - `二回`
  - `二階`
  - `二杯`

### 4階
- STT: 1 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `よんかい` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `4階`
  - `四回`
  - `四階`
  - `四杯`
  - `大人`

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
- STT: 8 surfaces, OpenAI: 11 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `覚えていない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `知りません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `忘れた` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `覚えていません`
  - `覚えてない`
  - `覚えてません`
  - `分からない`
  - `分かりません`

### キャンセル
- STT: 4 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `取り消す`

### リハビリテーション科
- STT: 14 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `リハビリテーション科` (R1_STT_PROPER_NOUN_GROUP)
  - `ミカミ` (R1_STT_PROPER_NOUN_GROUP)
  - `ミリ` (R1_STT_PROPER_NOUN_GROUP)
  - `リハ` (R1_STT_PROPER_NOUN_GROUP)
  - `リハビリ` (R1_STT_PROPER_NOUN_GROUP)

### 下肢静脈瘤
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `下肢静脈瘤`

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

### 健診
- STT: 6 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `健診` (R1_STT_PROPER_NOUN_GROUP)
  - `ドック` (R1_STT_PROPER_NOUN_GROUP)
  - `健康診断` (R1_STT_PROPER_NOUN_GROUP)
  - `検診` (R1_STT_PROPER_NOUN_GROUP)
  - `人間ドック` (R1_STT_PROPER_NOUN_GROUP)

### 入院
- STT: 2 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `にゅういん` (R3_STT_KANA_VARIANT)
  - `ニュウイン` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `入院`

### 内科（予約不要）
- STT: 3 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `内科` (R1_STT_PROPER_NOUN_GROUP)
  - `ないか` (R1_STT_PROPER_NOUN_GROUP)
  - `ナイカ` (R1_STT_PROPER_NOUN_GROUP)

### 内科（直接来院）
- STT: 6 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `内科` (R1_STT_PROPER_NOUN_GROUP)
  - `ナイカ` (R1_STT_PROPER_NOUN_GROUP)
  - `ないか` (R1_STT_PROPER_NOUN_GROUP)
  - `なんか` (R1_STT_PROPER_NOUN_GROUP)
  - `一般内科` (R1_STT_PROPER_NOUN_GROUP)

### 再診
- STT: 1 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `再診` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `はい新薬`
  - `最新`
  - `三新薬`
  - `定期`
  - `定期受診`

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
- STT: 16 surfaces, OpenAI: 12 surfaces
- STT サンプル:
  - `いない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `いません` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `おりません` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `分からない`
  - `覚えていません`
  - `覚えてない`
  - `知らない`
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

### 医師名
- STT: 4 surfaces, OpenAI: 18 surfaces
- STT サンプル:
  - `あべ` (R3_STT_KANA_VARIANT)
  - `わかばやし` (R3_STT_KANA_VARIANT)
  - `こやま` (R3_STT_KANA_VARIANT)
  - `こばやし` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `阿部医師`
  - `あべ先生`
  - `阿部`
  - `阿部先生`
  - `市川医師`

### 否定
- STT: 26 surfaces, OpenAI: 15 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `に` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `にばん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `まちがった` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `2`
  - `違う`
  - `二`
  - `二番`
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

### 希望時間帯
- STT: 10 surfaces, OpenAI: 14 surfaces
- STT サンプル:
  - `午後` (R2_STT_TEMPLATE_REUSE → hearing_time)
  - `ごご` (R3_STT_KANA_VARIANT)
  - `ゴゴ` (R3_STT_KANA_VARIANT)
  - `午前` (R2_STT_TEMPLATE_REUSE → hearing_time)
  - `ごぜん` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `13時`
  - `14時`
  - `１時`
  - `2時`
  - `10時`

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

### 検査
- STT: 4 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `検査` (R1_STT_PROPER_NOUN_GROUP)
  - `けんさ` (R1_STT_PROPER_NOUN_GROUP)
  - `ケンサ` (R1_STT_PROPER_NOUN_GROUP)
  - `胃カメラ` (R1_STT_PROPER_NOUN_GROUP)

### 検査キャンセル
- STT: 10 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `検査キャンセル` (R1_STT_PROPER_NOUN_GROUP)
  - `検査のキャンセル` (R1_STT_PROPER_NOUN_GROUP)
  - `検査の予約キャンセル` (R1_STT_PROPER_NOUN_GROUP)
  - `検査の予約のキャンセル` (R1_STT_PROPER_NOUN_GROUP)
  - `検査の予約をキャンセル` (R1_STT_PROPER_NOUN_GROUP)

### 検査変更
- STT: 19 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `検査変更` (R1_STT_PROPER_NOUN_GROUP)
  - `検査の内容の変更` (R1_STT_PROPER_NOUN_GROUP)
  - `検査の内容を変更` (R1_STT_PROPER_NOUN_GROUP)
  - `検査の日程の変更` (R1_STT_PROPER_NOUN_GROUP)
  - `検査の日程を変更` (R1_STT_PROPER_NOUN_GROUP)

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

### 精神科
- STT: 5 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `精神科` (R1_STT_PROPER_NOUN_GROUP)
  - `メンタル` (R1_STT_PROPER_NOUN_GROUP)
  - `メンタルヘルス` (R1_STT_PROPER_NOUN_GROUP)
  - `心療内科` (R1_STT_PROPER_NOUN_GROUP)
  - `精神` (R1_STT_PROPER_NOUN_GROUP)

### 肛門外科
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `肛門外科` (R1_STT_PROPER_NOUN_GROUP)
  - `おしり` (R1_STT_PROPER_NOUN_GROUP)
  - `コウモン` (R1_STT_PROPER_NOUN_GROUP)
  - `こうもん` (R1_STT_PROPER_NOUN_GROUP)
  - `こうもんか` (R1_STT_PROPER_NOUN_GROUP)

### 肯定
- STT: 32 surfaces, OpenAI: 12 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いち` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `イチ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうそう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `1`
  - `1番`
  - `一`
  - `一番`
  - `配送です`

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
- STT: 3 surfaces, OpenAI: 27 surfaces
- STT サンプル:
  - `はじめて` (R3_STT_KANA_VARIANT)
  - `初めて` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `新規` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `診察予約`
  - `を取る`
  - `印刷の夜行`
  - `印刷予約`
  - `金4百`

### 間違い
- STT: 0 surfaces, OpenAI: 3 surfaces
- OpenAI サンプル:
  - `間違い`
  - `違う`
  - `間違え`
