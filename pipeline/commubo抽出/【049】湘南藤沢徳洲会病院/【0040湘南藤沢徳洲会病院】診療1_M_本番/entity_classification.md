# Entity Classification Summary — 湘南藤沢徳洲会病院 / 診療

対象 yaml: 19 本

  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/main.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/WEBか電話か.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/予約希望時期.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/予約日の聞き取り.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/側弯症の確認.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/再予約希望確認.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/医師名聴取.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/味覚嗅覚外来確認.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/問い合わせ内容聞き取り.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/用件.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/睡眠時無呼吸確認.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/紹介元医療機関聞き取り.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/紹介状に医師指定があるか.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/紹介状有無聞き取り.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/診察券番号聞き取り.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/診療科.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/追加診療科聴取（変更、キャンセル）.yaml`
  - `【049】湘南藤沢徳洲会病院/【0040湘南藤沢徳洲会病院】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 482 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 71 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 122 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 229 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 00_00_02_脳神経
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `脳神経外科` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `形が` (R1_STT_PROPER_NOUN_GROUP)
  - `経過` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_分岐あり診療科
- STT: 2 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `脳神経` (R1_STT_PROPER_NOUN_GROUP)
  - `よう神経` (R1_STT_PROPER_NOUN_GROUP)

### 00_01_02_産婦人科
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `産科` (R1_STT_PROPER_NOUN_GROUP)
  - `あんた` (R1_STT_PROPER_NOUN_GROUP)
  - `なんか` (R1_STT_PROPER_NOUN_GROUP)
  - `三か` (R1_STT_PROPER_NOUN_GROUP)
  - `三個` (R1_STT_PROPER_NOUN_GROUP)

### 00_01_分岐あり診療科
- STT: 3 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `産婦人科` (R1_STT_PROPER_NOUN_GROUP)
  - `その婦人科` (R1_STT_PROPER_NOUN_GROUP)
  - `三九人か` (R1_STT_PROPER_NOUN_GROUP)

### 01_00_分岐なし診療科（初診予約可）
- STT: 294 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `ＣＰＡＰ外来` (R1_STT_PROPER_NOUN_GROUP)
  - `ＣＰＡＰ` (R1_STT_PROPER_NOUN_GROUP)
  - `CPAP` (R1_STT_PROPER_NOUN_GROUP)
  - `CPAP外来` (R1_STT_PROPER_NOUN_GROUP)
  - `シーパップ` (R1_STT_PROPER_NOUN_GROUP)

### 02_00_分岐なし診療科（初診予約NG）
- STT: 10 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `循環器科` (R1_STT_PROPER_NOUN_GROUP)
  - `ハート` (R1_STT_PROPER_NOUN_GROUP)
  - `関係ないか` (R1_STT_PROPER_NOUN_GROUP)
  - `循環` (R1_STT_PROPER_NOUN_GROUP)
  - `循環器` (R1_STT_PROPER_NOUN_GROUP)

### 03_00_予約制ではない診療科
- STT: 59 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `耳鼻咽喉科` (R1_STT_PROPER_NOUN_GROUP)
  - `BB` (R1_STT_PROPER_NOUN_GROUP)
  - `BBか` (R1_STT_PROPER_NOUN_GROUP)
  - `DB` (R1_STT_PROPER_NOUN_GROUP)
  - `DBか` (R1_STT_PROPER_NOUN_GROUP)

### 04_00_対象外診療科（予約センター対応）
- STT: 7 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `集中治療科` (R1_STT_PROPER_NOUN_GROUP)
  - `集中治療` (R1_STT_PROPER_NOUN_GROUP)
  - `病理診断科` (R1_STT_PROPER_NOUN_GROUP)
  - `病理` (R1_STT_PROPER_NOUN_GROUP)
  - `病理診断` (R1_STT_PROPER_NOUN_GROUP)

### 05_00_対象外診療科（代表電話）
- STT: 34 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `リハビリテーション科` (R1_STT_PROPER_NOUN_GROUP)
  - `ミカミ` (R1_STT_PROPER_NOUN_GROUP)
  - `ミリ` (R1_STT_PROPER_NOUN_GROUP)
  - `リハ` (R1_STT_PROPER_NOUN_GROUP)
  - `リハビリ` (R1_STT_PROPER_NOUN_GROUP)

### 06_00_対象外診療科（人間ドック）
- STT: 8 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `人間ドック検診センター` (R1_STT_PROPER_NOUN_GROUP)
  - `ドック` (R1_STT_PROPER_NOUN_GROUP)
  - `健康診断` (R1_STT_PROPER_NOUN_GROUP)
  - `健診` (R1_STT_PROPER_NOUN_GROUP)
  - `健診センター` (R1_STT_PROPER_NOUN_GROUP)

### 1
- STT: 6 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `いち` (R3_STT_KANA_VARIANT)
  - `インターネット` (R3_STT_KANA_VARIANT)
  - `ウェブ` (R3_STT_KANA_VARIANT)
  - `オンライン` (R3_STT_KANA_VARIANT)
  - `ち` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `1`
  - `1番`
  - `WEB`
  - `一`
  - `一番`

### 2
- STT: 6 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `このまま` (R3_STT_KANA_VARIANT)
  - `デンワ` (R3_STT_KANA_VARIANT)
  - `に` (R3_STT_KANA_VARIANT)
  - `ニ` (R3_STT_KANA_VARIANT)
  - `にい` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `2`
  - `２`
  - `2番`
  - `ニ、`
  - `電話`

### もう一回、間違えた
- STT: 5 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `まちがい` (R3_STT_KANA_VARIANT)
  - `まちがえ` (R3_STT_KANA_VARIANT)
  - `もういちど` (R3_STT_KANA_VARIANT)
  - `もういっかい` (R3_STT_KANA_VARIANT)
  - `もっかい` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `間違え`
  - `もう１回`
  - `もう一回`
  - `もう一度`
  - `間違い`

### もう一度
- STT: 2 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `ぜろ` (R3_STT_KANA_VARIANT)
  - `ゼロ` (R2_STT_TEMPLATE_REUSE → hearing_phone_number)
- OpenAI サンプル:
  - `もう一度`
  - `もう一回`
  - `０`
  - `0`
  - `再度`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### わからない
- STT: 2 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `分からない`

### キャンセル
- STT: 8 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `さん` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `3`
  - `3番`
  - `三`
  - `三番`
  - `取り消す`

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
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `健診` (R1_STT_PROPER_NOUN_GROUP)
  - `けんしん` (R1_STT_PROPER_NOUN_GROUP)
  - `ケンシン` (R1_STT_PROPER_NOUN_GROUP)
  - `健康診断` (R1_STT_PROPER_NOUN_GROUP)
  - `健康診断受診後の再検査` (R1_STT_PROPER_NOUN_GROUP)

### 側彎症
- STT: 0 surfaces, OpenAI: 8 surfaces
- OpenAI サンプル:
  - `側彎症`
  - `そこら所`
  - `脊柱側板所`
  - `脊柱側彎症`
  - `脊柱側弯症`

### 内視鏡内科（予約時のみ肝胆膵・消化器病センターへセット）
- STT: 3 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `内視鏡内科` (R1_STT_PROPER_NOUN_GROUP)
  - `ないしきょうないか` (R1_STT_PROPER_NOUN_GROUP)
  - `ナイシキョウナイカ` (R1_STT_PROPER_NOUN_GROUP)

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
- STT: 17 surfaces, OpenAI: 17 surfaces
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
- STT: 30 surfaces, OpenAI: 21 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
- OpenAI サンプル:
  - `否定`
  - `違う`
  - `間違い`
  - `間違っている`
  - `間違ってます`

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

### 味覚嗅覚外来
- STT: 11 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `味覚嗅覚外来` (R1_STT_PROPER_NOUN_GROUP)
  - `に核外来` (R1_STT_PROPER_NOUN_GROUP)
  - `に書く計画在来` (R1_STT_PROPER_NOUN_GROUP)
  - `二拡張書く` (R1_STT_PROPER_NOUN_GROUP)
  - `二百九画` (R1_STT_PROPER_NOUN_GROUP)

### 変更
- STT: 4 surfaces, OpenAI: 10 surfaces
- STT サンプル:
  - `変更` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `別の` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `にばん` (R3_STT_KANA_VARIANT)
  - `ニバン` (R3_STT_KANA_VARIANT)
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

### 整形外科（初診予約可）
- STT: 10 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `整形外科` (R1_STT_PROPER_NOUN_GROUP)
  - `TH` (R1_STT_PROPER_NOUN_GROUP)
  - `TK` (R1_STT_PROPER_NOUN_GROUP)
  - `えー外科` (R1_STT_PROPER_NOUN_GROUP)
  - `経由か` (R1_STT_PROPER_NOUN_GROUP)

### 新規
- STT: 5 surfaces, OpenAI: 5 surfaces
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
  - `新品`

### 無し
- STT: 7 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `あれだけ` (R3_STT_KANA_VARIANT)
  - `これだけ` (R3_STT_KANA_VARIANT)
  - `それだけ` (R3_STT_KANA_VARIANT)
  - `ないです` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `無し`
  - `１つだけ`
  - `一つだけ`
  - `一個だけ`
  - `無いです`

### 確認
- STT: 8 surfaces, OpenAI: 11 surfaces
- STT サンプル:
  - `確認` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `いつ` (R3_STT_KANA_VARIANT)
  - `なくした` (R3_STT_KANA_VARIANT)
  - `よばん` (R3_STT_KANA_VARIANT)
  - `ヨバン` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `4`
  - `4番`
  - `お聞き`
  - `教えて`
  - `四`

### 股関節外来
- STT: 5 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `股関節外来` (R1_STT_PROPER_NOUN_GROUP)
  - `こー関節外来` (R1_STT_PROPER_NOUN_GROUP)
  - `関節` (R1_STT_PROPER_NOUN_GROUP)
  - `関節外来` (R1_STT_PROPER_NOUN_GROUP)
  - `股関節` (R1_STT_PROPER_NOUN_GROUP)

### 肯定
- STT: 32 surfaces, OpenAI: 13 surfaces
- STT サンプル:
  - `あっています` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あっている` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってる` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いいです` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
- OpenAI サンプル:
  - `肯定`
  - `大丈夫`
  - `1`
  - `1番`
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

### 診察予約
- STT: 8 surfaces, OpenAI: 28 surfaces
- STT サンプル:
  - `はじめて` (R3_STT_KANA_VARIANT)
  - `初めて` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `新規` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `いち` (R3_STT_KANA_VARIANT)
  - `イチ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `診察予約`
  - `印刷`
  - `撮りたい`
  - `取りたい`
  - `取得`

### 間違い
- STT: 0 surfaces, OpenAI: 4 surfaces
- OpenAI サンプル:
  - `間違い`
  - `違い`
  - `違う`
  - `間違え`
