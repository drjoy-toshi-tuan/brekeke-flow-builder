# Entity Classification Summary — 真生会富山病院 / 予防接種

対象 yaml: 7 本

  - `【065】真生会富山病院/【0058真生会富山病院】予防接種1_M_本番/main.yaml`
  - `【065】真生会富山病院/【0058真生会富山病院】予防接種1_M_本番/予約希望日.yaml`
  - `【065】真生会富山病院/【0058真生会富山病院】予防接種1_M_本番/予約日の聞き取り.yaml`
  - `【065】真生会富山病院/【0058真生会富山病院】予防接種1_M_本番/予約日時確認（肯定否定）.yaml`
  - `【065】真生会富山病院/【0058真生会富山病院】予防接種1_M_本番/予防接種の種類聞き取り.yaml`
  - `【065】真生会富山病院/【0058真生会富山病院】予防接種1_M_本番/用件聞き取り.yaml`
  - `【065】真生会富山病院/【0058真生会富山病院】予防接種1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 37 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 53 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 63 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 152 | OpenAI 正規化 |

## 詳細 (entity 単位)

### もう一度
- STT: 0 surfaces, OpenAI: 4 surfaces
- OpenAI サンプル:
  - `もう一度`
  - `もう1回`
  - `もう一回`
  - `再度`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### フィラー
- STT: 2 surfaces, OpenAI: 21 surfaces
- STT サンプル:
  - `うん` (R3_STT_KANA_VARIANT)
  - `おー` (R2_STT_TEMPLATE_REUSE → hearing_phone_number)
- OpenAI サンプル:
  - `フィラー`
  - `あー`
  - `あのー`
  - `いやー`
  - `うー`

### ワクチン種類
- STT: 37 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `インフルエンザワクチン` (R1_STT_PROPER_NOUN_GROUP)
  - `いう円座` (R1_STT_PROPER_NOUN_GROUP)
  - `いう円座ワクチン` (R1_STT_PROPER_NOUN_GROUP)
  - `インフル` (R1_STT_PROPER_NOUN_GROUP)
  - `インフルエンザ` (R1_STT_PROPER_NOUN_GROUP)

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
- STT: 7 surfaces, OpenAI: 8 surfaces
- STT サンプル:
  - `いつ` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ません` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `分からない`
  - `解らない`
  - `覚えてない`
  - `分かりません`
  - `聞いていない`

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

### 否定
- STT: 20 surfaces, OpenAI: 11 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `そうでない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうではない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `2`
  - `２`
  - `違う`
  - `間違い`

### 否定単語
- STT: 7 surfaces, OpenAI: 9 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ダメ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ニ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `にばん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ニバン` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `2`
  - `２`
  - `違い`
  - `違う`

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

### 接種後の体調
- STT: 0 surfaces, OpenAI: 6 surfaces
- OpenAI サンプル:
  - `接種後の体調`
  - `接種した後`
  - `接種後`
  - `接種後の`
  - `体調`

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

### 新規予約
- STT: 4 surfaces, OpenAI: 23 surfaces
- STT サンプル:
  - `新規予約` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `お薬` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `初めて` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `予約` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `もう摂取の予約`
  - `契約`
  - `撮りたい`
  - `取得`
  - `親孝行とる`

### 用件（変更／キャンセル／問合せ）
- STT: 12 surfaces, OpenAI: 18 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `変更` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `取り消す`
  - `延期`
  - `取り直したい`
  - `取り直す`
  - `判子`

### 肯定
- STT: 27 surfaces, OpenAI: 11 surfaces
- STT サンプル:
  - `あっています` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あっている` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってる` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いいです` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
- OpenAI サンプル:
  - `肯定`
  - `1`
  - `１`
  - `一`
  - `一番`

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
  - `１`
  - `違いありません`
  - `違いない`
  - `一`
