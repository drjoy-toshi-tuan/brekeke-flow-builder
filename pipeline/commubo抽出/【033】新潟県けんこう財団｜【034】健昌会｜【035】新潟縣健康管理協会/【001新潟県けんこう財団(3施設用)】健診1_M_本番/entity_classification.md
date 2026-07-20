# Entity Classification Summary — 新潟県けんこう財団 / 健診

対象 yaml: 17 本

  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/main.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/SMS送信用携帯番号聞き取りへ.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/予約日聞き取り.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/企業：連絡先電話番号聞き取り.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/受診希望日.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/受診票有無の確認.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/希望日聴取（施設分岐あり）.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/希望時間聞き取り.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/折り返し確認.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/施設名聞き取り.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/生年月日聞き取り.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/用件聞き取り（時間内）.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/用件聞き取り（時間外）.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/用件聞き取り（連休中）.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/登録番号聞き取り.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/連絡先電話番号.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【001新潟県けんこう財団(3施設用)】健診1_M_本番/（保留）折返し方法確認.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 100 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 51 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 102 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 157 | OpenAI 正規化 |

## 詳細 (entity 単位)

### WEB予約
- STT: 10 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `インターネット` (R3_STT_KANA_VARIANT)
  - `いんたーねっと` (R3_STT_KANA_VARIANT)
  - `ウェブ` (R3_STT_KANA_VARIANT)
  - `ウエブ` (R3_STT_KANA_VARIANT)
  - `サイト` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `WEB予約`
  - `L400`
  - `URL`
  - `WEB`
  - `全部予約`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

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

### 受診希望施設名
- STT: 39 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `新潟健診プラザ` (R1_STT_PROPER_NOUN_GROUP)
  - `1` (R1_STT_PROPER_NOUN_GROUP)
  - `いち` (R1_STT_PROPER_NOUN_GROUP)
  - `イチ` (R1_STT_PROPER_NOUN_GROUP)
  - `いちばん` (R1_STT_PROPER_NOUN_GROUP)

### 否定
- STT: 17 surfaces, OpenAI: 11 surfaces
- STT サンプル:
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `それじゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ニ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `2`
  - `２`
  - `違う`
  - `間違い`

### 否定単語
- STT: 20 surfaces, OpenAI: 20 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ダメ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `2`
  - `違い`
  - `違う`
  - `違って`

### 折返し電話
- STT: 5 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `おりかえし` (R3_STT_KANA_VARIANT)
  - `オリカエシ` (R3_STT_KANA_VARIANT)
  - `かけて` (R3_STT_KANA_VARIANT)
  - `でんわ` (R3_STT_KANA_VARIANT)
  - `デンワ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `折返し電話`
  - `かけ直し`
  - `折り返し`
  - `折返し`
  - `電話`

### 持っている
- STT: 5 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ある` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いまーす` (R3_STT_KANA_VARIANT)
  - `います` (R3_STT_KANA_VARIANT)
  - `いる` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `持っている`
  - `持っていまーす`
  - `持ってまーす`
  - `持ってます`
  - `盛ってまーす`

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

### 数字の１
- STT: 4 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `いち` (R3_STT_KANA_VARIANT)
  - `イチ` (R3_STT_KANA_VARIANT)
  - `いちばん` (R3_STT_KANA_VARIANT)
  - `イチバン` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `１`
  - `1`
  - `一`
  - `一番`

### 数字の２
- STT: 3 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `ニ` (R3_STT_KANA_VARIANT)
  - `にばん` (R3_STT_KANA_VARIANT)
  - `ニバン` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `２`
  - `2`
  - `二`
  - `二番`

### 時分
- STT: 2 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `時` (R2_STT_TEMPLATE_REUSE → hearing_time)
  - `分` (R2_STT_TEMPLATE_REUSE → hearing_time)

### 用件
- STT: 80 surfaces, OpenAI: 59 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `サン` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `さんばん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `3`
  - `3番`
  - `三`
  - `三番`
  - `取り消す`

### 肯定
- STT: 26 surfaces, OpenAI: 13 surfaces
- STT サンプル:
  - `あっています` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いいです` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `いち` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `イチ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`
  - `1`
  - `１`
  - `一`
  - `一番`

### 肯定エンティティ
- STT: 11 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `あっています` (R3_STT_KANA_VARIANT)
  - `あってます` (R3_STT_KANA_VARIANT)
  - `イチ` (R3_STT_KANA_VARIANT)
  - `いち` (R3_STT_KANA_VARIANT)
  - `イチバン` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `肯定`
  - `1`
  - `一`
  - `一番`
  - `大丈夫`

### 肯定単語
- STT: 15 surfaces, OpenAI: 9 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `OK` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `あっています` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってる` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `1`
  - `違いありません`
  - `違いない`
  - `一`
  - `一番`
