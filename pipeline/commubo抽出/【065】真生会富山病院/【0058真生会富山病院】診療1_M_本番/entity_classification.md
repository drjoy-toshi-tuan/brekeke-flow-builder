# Entity Classification Summary — 真生会富山病院 / 診療

対象 yaml: 8 本

  - `【065】真生会富山病院/【0058真生会富山病院】診療1_M_本番/main.yaml`
  - `【065】真生会富山病院/【0058真生会富山病院】診療1_M_本番/予約日の聞き取り.yaml`
  - `【065】真生会富山病院/【0058真生会富山病院】診療1_M_本番/受診内容聞き取り.yaml`
  - `【065】真生会富山病院/【0058真生会富山病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【065】真生会富山病院/【0058真生会富山病院】診療1_M_本番/用件聞き取り.yaml`
  - `【065】真生会富山病院/【0058真生会富山病院】診療1_M_本番/紹介状有無聞き取り.yaml`
  - `【065】真生会富山病院/【0058真生会富山病院】診療1_M_本番/診察券番号聞き取り.yaml`
  - `【065】真生会富山病院/【0058真生会富山病院】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 4 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 56 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 69 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 186 | OpenAI 正規化 |

## 詳細 (entity 単位)

### CO対応
- STT: 3 surfaces, OpenAI: 19 surfaces
- STT サンプル:
  - `３歳半検診` (R1_STT_PROPER_NOUN_GROUP)
  - `レーシック術前検査` (R1_STT_PROPER_NOUN_GROUP)
  - `近視外来` (R1_STT_PROPER_NOUN_GROUP)
- OpenAI サンプル:
  - `アトロピン`
  - `オルソケラトロジー`
  - `オルソ`
  - `コンタクト紛失`
  - `コンタクト破損`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

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
- STT: 8 surfaces, OpenAI: 9 surfaces
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
- STT: 2 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `別の` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `変更` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `違う`
  - `他の`
  - `変え`

### 医事課対応
- STT: 4 surfaces, OpenAI: 10 surfaces
- STT サンプル:
  - `コンタクト` (R3_STT_KANA_VARIANT)
  - `コンタクトを` (R3_STT_KANA_VARIANT)
  - `定期健診` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `適応検査` (R1_STT_PROPER_NOUN_GROUP)
- OpenAI サンプル:
  - `コンタクト作りたい`
  - `眼鏡作りたい`
  - `眼鏡`
  - `眼鏡を`
  - `診察予約`

### 否定
- STT: 19 surfaces, OpenAI: 12 surfaces
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

### 携帯電話
- STT: 2 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `スマートフォン` (R3_STT_KANA_VARIANT)
  - `スマホ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `携帯電話`
  - `携帯`
  - `携帯番号`

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
- STT: 5 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `キャンセルじゃない` (R3_STT_KANA_VARIANT)
  - `キャンセルではない` (R3_STT_KANA_VARIANT)
  - `なし` (R3_STT_KANA_VARIANT)
  - `変更` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `無し`
  - `無い`
  - `無いです`

### 用件
- STT: 29 surfaces, OpenAI: 62 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `さんばん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `サンバン` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `3`
  - `３`
  - `三`
  - `三番`
  - `取り消す`

### 看護師対応
- STT: 2 surfaces, OpenAI: 17 surfaces
- STT サンプル:
  - `オペ` (R3_STT_KANA_VARIANT)
  - `薬` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `ＯＰＥ予約`
  - `OPE予約`
  - `オペ予約`
  - `手術`
  - `手術予約`

### 肯定
- STT: 16 surfaces, OpenAI: 10 surfaces
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
- STT: 10 surfaces, OpenAI: 5 surfaces
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
