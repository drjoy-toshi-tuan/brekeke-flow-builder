# Entity Classification Summary — 岐阜大学医学部付属病院 / 診療

対象 yaml: 12 本

  - `【083】岐阜大学医学部付属病院/【083岐阜大学医学部附属病院】診療1_M_本番/main.yaml`
  - `【083】岐阜大学医学部付属病院/【083岐阜大学医学部附属病院】診療1_M_本番/WEB or AI電話.yaml`
  - `【083】岐阜大学医学部付属病院/【083岐阜大学医学部附属病院】診療1_M_本番/WEB入力番号聞き取り.yaml`
  - `【083】岐阜大学医学部付属病院/【083岐阜大学医学部附属病院】診療1_M_本番/予約希望時期の聞き取り.yaml`
  - `【083】岐阜大学医学部付属病院/【083岐阜大学医学部附属病院】診療1_M_本番/予約日の聞き取り.yaml`
  - `【083】岐阜大学医学部付属病院/【083岐阜大学医学部附属病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【083】岐阜大学医学部付属病院/【083岐阜大学医学部附属病院】診療1_M_本番/用件聞き取り.yaml`
  - `【083】岐阜大学医学部付属病院/【083岐阜大学医学部附属病院】診療1_M_本番/肯定否定確認（次回予約希望）.yaml`
  - `【083】岐阜大学医学部付属病院/【083岐阜大学医学部附属病院】診療1_M_本番/肯定否定確認（残薬有無）.yaml`
  - `【083】岐阜大学医学部付属病院/【083岐阜大学医学部附属病院】診療1_M_本番/診察券番号聞き取り.yaml`
  - `【083】岐阜大学医学部付属病院/【083岐阜大学医学部附属病院】診療1_M_本番/診療科聞き取り.yaml`
  - `【083】岐阜大学医学部付属病院/【083岐阜大学医学部附属病院】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 632 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 70 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 96 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 200 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 00_00_01_呼吸器
- STT: 15 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `いうか` (R1_STT_PROPER_NOUN_GROUP)
  - `吸気外科` (R1_STT_PROPER_NOUN_GROUP)
  - `京急ですか` (R1_STT_PROPER_NOUN_GROUP)
  - `呼外` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_02_消化器
- STT: 11 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `消化器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `しょうげ` (R1_STT_PROPER_NOUN_GROUP)
  - `しょげ` (R1_STT_PROPER_NOUN_GROUP)
  - `尚書き外科` (R1_STT_PROPER_NOUN_GROUP)
  - `消外` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_03_脳神経
- STT: 14 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `脳神経外科` (R1_STT_PROPER_NOUN_GROUP)
  - `しんげ` (R1_STT_PROPER_NOUN_GROUP)
  - `の下` (R1_STT_PROPER_NOUN_GROUP)
  - `の買い` (R1_STT_PROPER_NOUN_GROUP)
  - `神経外科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_04_放射線
- STT: 20 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `放射線科` (R1_STT_PROPER_NOUN_GROUP)
  - `ほうか` (R1_STT_PROPER_NOUN_GROUP)
  - `ホウカ` (R1_STT_PROPER_NOUN_GROUP)
  - `ほうしゃせんか` (R1_STT_PROPER_NOUN_GROUP)
  - `ホウシャセンカ` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_05_腎臓
- STT: 24 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `腎移植外科` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `メーカー` (R1_STT_PROPER_NOUN_GROUP)
  - `リバー` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_分岐あり診療科
- STT: 23 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器` (R1_STT_PROPER_NOUN_GROUP)
  - `こー下` (R1_STT_PROPER_NOUN_GROUP)
  - `コピー機` (R1_STT_PROPER_NOUN_GROUP)
  - `吸気` (R1_STT_PROPER_NOUN_GROUP)
  - `五九` (R1_STT_PROPER_NOUN_GROUP)

### 01_00_分岐なし診療科
- STT: 482 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `リハビリテーション部リハビリテーション科` (R1_STT_PROPER_NOUN_GROUP)
  - `ミカミ` (R1_STT_PROPER_NOUN_GROUP)
  - `ミリ` (R1_STT_PROPER_NOUN_GROUP)
  - `リハ` (R1_STT_PROPER_NOUN_GROUP)
  - `リハビリ` (R1_STT_PROPER_NOUN_GROUP)

### 02_00_対象外診療科
- STT: 32 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `眼科` (R1_STT_PROPER_NOUN_GROUP)
  - `LAN` (R1_STT_PROPER_NOUN_GROUP)
  - `あんた` (R1_STT_PROPER_NOUN_GROUP)
  - `だんだ` (R1_STT_PROPER_NOUN_GROUP)
  - `だんだん` (R1_STT_PROPER_NOUN_GROUP)

### もう一度
- STT: 2 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `もういちど` (R3_STT_KANA_VARIANT)
  - `もういっかい` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `もう一度`
  - `もう1回`
  - `もう一回`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### わからない
- STT: 6 surfaces, OpenAI: 14 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わからん` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `覚えていない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `知りません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `覚えていません`
  - `覚えてない`
  - `覚えてません`
  - `知らない`
  - `分からん`

### フィラー
- STT: 3 surfaces, OpenAI: 20 surfaces
- STT サンプル:
  - `うん` (R3_STT_KANA_VARIANT)
  - `おー` (R2_STT_TEMPLATE_REUSE → hearing_phone_number)
  - `なんか` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `フィラー`
  - `あー`
  - `あのー`
  - `いやー`
  - `うー`

### 今日
- STT: 5 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `今日` (R2_STT_TEMPLATE_REUSE → hearing_datetime)
  - `キョウ` (R3_STT_KANA_VARIANT)
  - `きょう` (R3_STT_KANA_VARIANT)
  - `これから` (R3_STT_KANA_VARIANT)
  - `本日` (R2_STT_TEMPLATE_REUSE → hearing_datetime)
- OpenAI サンプル:
  - `今から`
  - `当日`

### 代表案内案件
- STT: 5 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `ドック` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `健康診断` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `健診` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `検診` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `人間ドック` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
- OpenAI サンプル:
  - `代表案内`

### 内科
- STT: 4 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `内科` (R1_STT_PROPER_NOUN_GROUP)
  - `ないか` (R1_STT_PROPER_NOUN_GROUP)
  - `ナイカ` (R1_STT_PROPER_NOUN_GROUP)
  - `ないカ` (R1_STT_PROPER_NOUN_GROUP)

### 処方無し
- STT: 3 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `もらっていない` (R3_STT_KANA_VARIANT)
  - `もらっていません` (R3_STT_KANA_VARIANT)
  - `もらってません` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `処方無し`
  - `処方されていない`
  - `処方されていません`
  - `処方されてない`
  - `処方されてません`

### 分からない
- STT: 5 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `ません` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `覚えていない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `持っていない` (R2_STT_TEMPLATE_REUSE → hearing_phone_number)
- OpenAI サンプル:
  - `分からない`
  - `解らない`
  - `動かない`
  - `分かりません`
  - `聞いていない`

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
- STT: 24 surfaces, OpenAI: 22 surfaces
- STT サンプル:
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `違う`
  - `無い`
  - `2`
  - `２`

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

### 持っていない
- STT: 5 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `持っていない` (R2_STT_TEMPLATE_REUSE → hearing_phone_number)
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ないです` (R3_STT_KANA_VARIANT)
  - `持っていません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `初めて` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `持ってない`
  - `持ってません`
  - `新患`
  - `無いです`

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

### 放射線（分岐あり）
- STT: 2 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `放射線` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
  - `ほうしゃ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `こー斜線`
  - `放射`

### 数字の１
- STT: 4 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `いち` (R3_STT_KANA_VARIANT)
  - `イチ` (R3_STT_KANA_VARIANT)
  - `イチバン` (R3_STT_KANA_VARIANT)
  - `いちばん` (R3_STT_KANA_VARIANT)
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

### 用件
- STT: 28 surfaces, OpenAI: 61 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `サン` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `さんばん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `サンバン` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `3`
  - `３`
  - `三`
  - `三番`
  - `取り消す`

### 肯定
- STT: 30 surfaces, OpenAI: 11 surfaces
- STT サンプル:
  - `OK` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ある` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いいです` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `いえす` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`
  - `そう思う`
  - `大丈夫です`
  - `1`
  - `１`

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

### 診察or検査
- STT: 7 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `検査` (R1_STT_PROPER_NOUN_GROUP)
  - `けんさ` (R1_STT_PROPER_NOUN_GROUP)
  - `ケンサ` (R1_STT_PROPER_NOUN_GROUP)
  - `診察` (R1_STT_PROPER_NOUN_GROUP)
  - `しんさつ` (R1_STT_PROPER_NOUN_GROUP)
