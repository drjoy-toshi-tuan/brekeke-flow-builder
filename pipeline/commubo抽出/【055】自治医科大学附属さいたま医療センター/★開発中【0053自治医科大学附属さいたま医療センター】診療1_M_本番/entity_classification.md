# Entity Classification Summary — 自治医科大学附属さいたま医療センター / ★開発中【0053自治医科大学附属さいたま医療センター】診療

対象 yaml: 12 本

  - `【055】自治医科大学附属さいたま医療センター/★開発中【0053自治医科大学附属さいたま医療センター】診療1_M_本番/main.yaml`
  - `【055】自治医科大学附属さいたま医療センター/★開発中【0053自治医科大学附属さいたま医療センター】診療1_M_本番/予約日の聞き取り.yaml`
  - `【055】自治医科大学附属さいたま医療センター/★開発中【0053自治医科大学附属さいたま医療センター】診療1_M_本番/予約日都合聞き取り.yaml`
  - `【055】自治医科大学附属さいたま医療センター/★開発中【0053自治医科大学附属さいたま医療センター】診療1_M_本番/予約時間の聞き取り.yaml`
  - `【055】自治医科大学附属さいたま医療センター/★開発中【0053自治医科大学附属さいたま医療センター】診療1_M_本番/予約種別確認.yaml`
  - `【055】自治医科大学附属さいたま医療センター/★開発中【0053自治医科大学附属さいたま医療センター】診療1_M_本番/医師名聴取.yaml`
  - `【055】自治医科大学附属さいたま医療センター/★開発中【0053自治医科大学附属さいたま医療センター】診療1_M_本番/生年月日聞き取り.yaml`
  - `【055】自治医科大学附属さいたま医療センター/★開発中【0053自治医科大学附属さいたま医療センター】診療1_M_本番/用件聞き取り.yaml`
  - `【055】自治医科大学附属さいたま医療センター/★開発中【0053自治医科大学附属さいたま医療センター】診療1_M_本番/紹介状有無聞き取り.yaml`
  - `【055】自治医科大学附属さいたま医療センター/★開発中【0053自治医科大学附属さいたま医療センター】診療1_M_本番/診察券番号聞き取り.yaml`
  - `【055】自治医科大学附属さいたま医療センター/★開発中【0053自治医科大学附属さいたま医療センター】診療1_M_本番/診療科聞き取り.yaml`
  - `【055】自治医科大学附属さいたま医療センター/★開発中【0053自治医科大学附属さいたま医療センター】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 472 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 66 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 78 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 230 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 00_00_01_呼吸器
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `形が` (R1_STT_PROPER_NOUN_GROUP)
  - `経過` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_02_消化器
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `消化器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `形が` (R1_STT_PROPER_NOUN_GROUP)
  - `経過` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_03_脳神経
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `脳神経外科` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `形が` (R1_STT_PROPER_NOUN_GROUP)
  - `経過` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_04_産婦人科
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `産科` (R1_STT_PROPER_NOUN_GROUP)
  - `あんた` (R1_STT_PROPER_NOUN_GROUP)
  - `なんか` (R1_STT_PROPER_NOUN_GROUP)
  - `三か` (R1_STT_PROPER_NOUN_GROUP)
  - `三個` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_分岐あり診療科
- STT: 11 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器` (R1_STT_PROPER_NOUN_GROUP)
  - `コピー機` (R1_STT_PROPER_NOUN_GROUP)
  - `吸気` (R1_STT_PROPER_NOUN_GROUP)
  - `五九` (R1_STT_PROPER_NOUN_GROUP)
  - `補給機` (R1_STT_PROPER_NOUN_GROUP)

### 01_00_分岐なし診療科
- STT: 388 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `ストーマ外来` (R1_STT_PROPER_NOUN_GROUP)
  - `FOMA` (R1_STT_PROPER_NOUN_GROUP)
  - `WOCケア` (R1_STT_PROPER_NOUN_GROUP)
  - `ウォーク` (R1_STT_PROPER_NOUN_GROUP)
  - `ウォークケア` (R1_STT_PROPER_NOUN_GROUP)

### ありません
- STT: 2 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `しません` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `指定無し`
  - `誰でも`
  - `無いです`

### それ以外
- STT: 4 surfaces, OpenAI: 9 surfaces
- STT サンプル:
  - `その他` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `ニ` (R3_STT_KANA_VARIANT)
  - `にばん` (R3_STT_KANA_VARIANT)
  - `ニバン` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `それ以外`
  - `2`
  - `２`
  - `診察じゃない`
  - `診察ではない`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### わからない
- STT: 8 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しらん` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しりません` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わからへん` (R3_STT_KANA_VARIANT → hearing_unknown)
- OpenAI サンプル:
  - `覚えてない`
  - `書いていない`
  - `知らない`
  - `分からん`
  - `忘れちゃった`

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
- STT: 6 surfaces, OpenAI: 14 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `覚えていない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `知りません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `ません` (R3_STT_KANA_VARIANT → hearing_unknown)
- OpenAI サンプル:
  - `分からない`
  - `覚えていません`
  - `覚えてない`
  - `覚えてません`
  - `知らない`

### 初診予約
- STT: 5 surfaces, OpenAI: 7 surfaces
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
  - `商品`

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
- STT: 15 surfaces, OpenAI: 10 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `そうではない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `それじゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `違う`
  - `間違い`
  - `間違って`
  - `違って`

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

### 対象外診療科
- STT: 8 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `救急科` (R1_STT_PROPER_NOUN_GROUP)
  - `急遽` (R1_STT_PROPER_NOUN_GROUP)
  - `救急` (R1_STT_PROPER_NOUN_GROUP)
  - `九九` (R1_STT_PROPER_NOUN_GROUP)
  - `十九` (R1_STT_PROPER_NOUN_GROUP)

### 小児
- STT: 4 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `小児外科` (R1_STT_PROPER_NOUN_GROUP)
  - `小児眼科` (R1_STT_PROPER_NOUN_GROUP)
  - `小児耳鼻科` (R1_STT_PROPER_NOUN_GROUP)
  - `小児泌尿器科` (R1_STT_PROPER_NOUN_GROUP)

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

### 無し
- STT: 2 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ないです` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `無し`
  - `無いです`

### 産婦人科：分岐あり
- STT: 6 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `産婦人科` (R1_STT_PROPER_NOUN_GROUP)
  - `さんふじんか` (R1_STT_PROPER_NOUN_GROUP)
  - `サンフジンカ` (R1_STT_PROPER_NOUN_GROUP)
  - `その婦人科` (R1_STT_PROPER_NOUN_GROUP)
  - `三九人か` (R1_STT_PROPER_NOUN_GROUP)

### 用件
- STT: 20 surfaces, OpenAI: 61 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `サン` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `さんばん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `3`
  - `３`
  - `三`
  - `三番`
  - `取り消す`

### 肯定
- STT: 13 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `あっています` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あっている` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってる` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いいです` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
- OpenAI サンプル:
  - `肯定`
  - `大丈夫`
  - `大丈夫です`
  - `異常部`
  - `丈夫`

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

### 診察
- STT: 6 surfaces, OpenAI: 8 surfaces
- STT サンプル:
  - `いち` (R3_STT_KANA_VARIANT)
  - `イチ` (R3_STT_KANA_VARIANT)
  - `いちばん` (R3_STT_KANA_VARIANT)
  - `イチバン` (R3_STT_KANA_VARIANT)
  - `いんすアップ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `診察`
  - `1`
  - `１`
  - `一`
  - `一番`

### 診察以外
- STT: 18 surfaces, OpenAI: 49 surfaces
- STT サンプル:
  - `アレルギー` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
  - `オンコロジー` (R3_STT_KANA_VARIANT)
  - `こうがんざい` (R3_STT_KANA_VARIANT)
  - `眼科検査` (R1_STT_PROPER_NOUN_GROUP)
  - `眼科検査2` (R1_STT_PROPER_NOUN_GROUP)
- OpenAI サンプル:
  - `CT`
  - `CT検査`
  - `MRI`
  - `MR`
  - `MRI検査`
