# Entity Classification Summary — 土浦協同病院 / 診療

対象 yaml: 10 本

  - `【072】土浦協同病院/【0054土浦協同病院】診療1_M_本番/main.yaml`
  - `【072】土浦協同病院/【0054土浦協同病院】診療1_M_本番/予約対応.yaml`
  - `【072】土浦協同病院/【0054土浦協同病院】診療1_M_本番/予約日の聞き取り.yaml`
  - `【072】土浦協同病院/【0054土浦協同病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【072】土浦協同病院/【0054土浦協同病院】診療1_M_本番/用件聞き取り.yaml`
  - `【072】土浦協同病院/【0054土浦協同病院】診療1_M_本番/肯定否定.yaml`
  - `【072】土浦協同病院/【0054土浦協同病院】診療1_M_本番/診察券番号.yaml`
  - `【072】土浦協同病院/【0054土浦協同病院】診療1_M_本番/診療科判断.yaml`
  - `【072】土浦協同病院/【0054土浦協同病院】診療1_M_本番/診療科聞き取り.yaml`
  - `【072】土浦協同病院/【0054土浦協同病院】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 468 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 45 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 66 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 197 | OpenAI 正規化 |

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
- STT: 18 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `眼科` (R1_STT_PROPER_NOUN_GROUP)
  - `がんか` (R1_STT_PROPER_NOUN_GROUP)
  - `なんか` (R1_STT_PROPER_NOUN_GROUP)
  - `整形外科` (R1_STT_PROPER_NOUN_GROUP)
  - `TK` (R1_STT_PROPER_NOUN_GROUP)

### 00_01_分岐あり診療科
- STT: 3 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `産婦人科` (R1_STT_PROPER_NOUN_GROUP)
  - `その婦人科` (R1_STT_PROPER_NOUN_GROUP)
  - `三九人か` (R1_STT_PROPER_NOUN_GROUP)

### 01_00_分岐なし診療科
- STT: 332 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `1ケ月健診小児` (R1_STT_PROPER_NOUN_GROUP)
  - `一ヶ月検診` (R1_STT_PROPER_NOUN_GROUP)
  - `がんゲノム診療科` (R1_STT_PROPER_NOUN_GROUP)
  - `え飲む` (R1_STT_PROPER_NOUN_GROUP)
  - `ゲノム` (R1_STT_PROPER_NOUN_GROUP)

### 1か月
- STT: 2 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `いっ` (R3_STT_KANA_VARIANT)
  - `ゲツ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `1か月`
  - `一`
  - `一ヵ月`
  - `一カ月`
  - `月`

### 2週間
- STT: 0 surfaces, OpenAI: 7 surfaces
- OpenAI サンプル:
  - `2週間`
  - `収監`
  - `習慣`
  - `週`
  - `週刊`

### それ以外
- STT: 8 surfaces, OpenAI: 9 surfaces
- STT サンプル:
  - `いつもの` (R3_STT_KANA_VARIANT)
  - `さん` (R3_STT_KANA_VARIANT)
  - `サン` (R3_STT_KANA_VARIANT)
  - `さんばん` (R3_STT_KANA_VARIANT)
  - `その他` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `それ以外`
  - `3`
  - `３`
  - `3番`
  - `三`

### もう一度
- STT: 4 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `なんて` (R3_STT_KANA_VARIANT)
  - `もっかい` (R3_STT_KANA_VARIANT)
  - `わからな` (R3_STT_KANA_VARIANT)
  - `わからん` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `もう一度`
  - `もう一回`
  - `聞こえない`

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

### キャンセル
- STT: 8 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `さん` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `取り消す`
  - `３`
  - `3`
  - `3番`
  - `三`

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

### 健診結果
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `健診結果` (R1_STT_PROPER_NOUN_GROUP)
  - `２` (R1_STT_PROPER_NOUN_GROUP)
  - `2` (R1_STT_PROPER_NOUN_GROUP)
  - `にばん` (R1_STT_PROPER_NOUN_GROUP)
  - `ふたつめ` (R1_STT_PROPER_NOUN_GROUP)

### 内科
- STT: 3 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `内科` (R1_STT_PROPER_NOUN_GROUP)
  - `ないか` (R1_STT_PROPER_NOUN_GROUP)
  - `何か` (R1_STT_PROPER_NOUN_GROUP)

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

### 呼吸器
- STT: 1 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `呼吸器` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
- OpenAI サンプル:
  - `コピー機`
  - `応急義`
  - `吸気`
  - `呼吸義`
  - `五九`

### 変更
- STT: 4 surfaces, OpenAI: 12 surfaces
- STT サンプル:
  - `変更` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `別の` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `にばん` (R3_STT_KANA_VARIANT)
  - `ふたつめ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `延期`
  - `時間`
  - `日程`
  - `日付`
  - `判子`

### 外科
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `いうか` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `メーカー` (R1_STT_PROPER_NOUN_GROUP)

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

### 心臓
- STT: 3 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `キンゾウ` (R3_STT_KANA_VARIANT)
  - `ギンゾウ` (R3_STT_KANA_VARIANT)
  - `シンゾウ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `心臓`

### 心臓外科
- STT: 6 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `心臓外科` (R1_STT_PROPER_NOUN_GROUP)
  - `キンゾウゲカ` (R1_STT_PROPER_NOUN_GROUP)
  - `ギンゾウゲカ` (R1_STT_PROPER_NOUN_GROUP)
  - `キンゾウ外科` (R1_STT_PROPER_NOUN_GROUP)
  - `新下` (R1_STT_PROPER_NOUN_GROUP)

### 心臓血管外科：心臓
- STT: 9 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `心臓血管外科` (R1_STT_PROPER_NOUN_GROUP)
  - `かんげ` (R1_STT_PROPER_NOUN_GROUP)
  - `関係か` (R1_STT_PROPER_NOUN_GROUP)
  - `警官` (R1_STT_PROPER_NOUN_GROUP)
  - `血管` (R1_STT_PROPER_NOUN_GROUP)

### 心臓血管外科：血管
- STT: 9 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `心臓血管外科` (R1_STT_PROPER_NOUN_GROUP)
  - `シンゾウ` (R1_STT_PROPER_NOUN_GROUP)
  - `関係か` (R1_STT_PROPER_NOUN_GROUP)
  - `現像結果` (R1_STT_PROPER_NOUN_GROUP)
  - `信号` (R1_STT_PROPER_NOUN_GROUP)

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

### 消化器
- STT: 1 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `消化器` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
- OpenAI サンプル:
  - `とー鍵が`
  - `今日鍵か`
  - `少額`
  - `消化管`
  - `消火器`

### 産後検診
- STT: 11 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `産後検診` (R1_STT_PROPER_NOUN_GROUP)
  - `あんご` (R1_STT_PROPER_NOUN_GROUP)
  - `さんご` (R1_STT_PROPER_NOUN_GROUP)
  - `サンゴ` (R1_STT_PROPER_NOUN_GROUP)
  - `たんご` (R1_STT_PROPER_NOUN_GROUP)

### 確認
- STT: 7 surfaces, OpenAI: 12 surfaces
- STT サンプル:
  - `確認` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `なくした` (R3_STT_KANA_VARIANT)
  - `忘れた` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `よっつめ` (R3_STT_KANA_VARIANT)
  - `よん` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `お聞き`
  - `教えて`
  - `調べて`
  - `分からない`
  - `分からん`

### 紹介状
- STT: 4 surfaces, OpenAI: 13 surfaces
- STT サンプル:
  - `イチ` (R3_STT_KANA_VARIANT)
  - `いち` (R3_STT_KANA_VARIANT)
  - `いちばん` (R3_STT_KANA_VARIANT)
  - `ひとつめ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `紹介状`
  - `1`
  - `１`
  - `案内状`
  - `一`

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

### 血管
- STT: 0 surfaces, OpenAI: 6 surfaces
- OpenAI サンプル:
  - `血管`
  - `かん外科`
  - `がん外科`
  - `欠陥`
  - `鉄管`

### 血管外科
- STT: 5 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `血管外科` (R1_STT_PROPER_NOUN_GROUP)
  - `一巻時間` (R1_STT_PROPER_NOUN_GROUP)
  - `間外科` (R1_STT_PROPER_NOUN_GROUP)
  - `時間外科` (R1_STT_PROPER_NOUN_GROUP)
  - `鉄板外科` (R1_STT_PROPER_NOUN_GROUP)

### 診察予約
- STT: 7 surfaces, OpenAI: 29 surfaces
- STT サンプル:
  - `はじめて` (R3_STT_KANA_VARIANT)
  - `初めて` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `新規` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `いち` (R3_STT_KANA_VARIANT)
  - `イチ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `診察予約`
  - `を取る`
  - `印刷`
  - `豪ドル`
  - `撮りたい`

### 違う
- STT: 4 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `じゃない` (R3_STT_KANA_VARIANT)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `ちゃう` (R3_STT_KANA_VARIANT)
  - `違います` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `違う`
  - `違い`
  - `間違い`
  - `間違え`

### 間違い
- STT: 0 surfaces, OpenAI: 3 surfaces
- OpenAI サンプル:
  - `間違い`
  - `違う`
  - `間違え`
