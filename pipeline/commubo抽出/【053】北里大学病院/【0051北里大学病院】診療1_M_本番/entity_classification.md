# Entity Classification Summary — 北里大学病院 / 診療

対象 yaml: 12 本

  - `【053】北里大学病院/【0051北里大学病院】診療1_M_本番/5_28 診療科（再診変更用）.yaml`
  - `【053】北里大学病院/【0051北里大学病院】診療1_M_本番/main.yaml`
  - `【053】北里大学病院/【0051北里大学病院】診療1_M_本番/リハ種別.yaml`
  - `【053】北里大学病院/【0051北里大学病院】診療1_M_本番/予約日（当日チェック）.yaml`
  - `【053】北里大学病院/【0051北里大学病院】診療1_M_本番/婦人科 予約希望日確認.yaml`
  - `【053】北里大学病院/【0051北里大学病院】診療1_M_本番/新規診療科.yaml`
  - `【053】北里大学病院/【0051北里大学病院】診療1_M_本番/用件聞き取り.yaml`
  - `【053】北里大学病院/【0051北里大学病院】診療1_M_本番/診察券番号聞き取り.yaml`
  - `【053】北里大学病院/【0051北里大学病院】診療1_M_本番/連絡先電話番号聞き取り.yaml`
  - `【053】北里大学病院/【0051北里大学病院】診療1_M_本番/連絡先電話番号聞き取り_1.yaml`
  - `【053】北里大学病院/【0051北里大学病院】診療1_M_本番/連絡先電話番号聞き取り_2.yaml`
  - `【053】北里大学病院/【0051北里大学病院】診療1_M_本番/連絡先電話番号聴取.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 490 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 47 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 62 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 174 | OpenAI 正規化 |

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

### 00_01_分岐あり診療科
- STT: 3 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `産婦人科` (R1_STT_PROPER_NOUN_GROUP)
  - `その婦人科` (R1_STT_PROPER_NOUN_GROUP)
  - `三九人か` (R1_STT_PROPER_NOUN_GROUP)

### 01_00_分岐なし診療科
- STT: 378 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `JPS` (R1_STT_PROPER_NOUN_GROUP)
  - `がん遺伝子パネル検査相談外来` (R1_STT_PROPER_NOUN_GROUP)
  - `スキンケア外来` (R1_STT_PROPER_NOUN_GROUP)
  - `スキンケア` (R1_STT_PROPER_NOUN_GROUP)
  - `めまいセンター` (R1_STT_PROPER_NOUN_GROUP)

### はじめて
- STT: 1 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `はじめて` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `行ったことない`
  - `最初の受診`
  - `初診です`

### わからない
- STT: 17 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しらん` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しりまへん` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `なにかな` (R3_STT_KANA_VARIANT → hearing_unknown)
- OpenAI サンプル:
  - `何か`
  - `知らない`

### フィラー
- STT: 3 surfaces, OpenAI: 21 surfaces
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

### 予約以外
- STT: 1 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
- OpenAI サンプル:
  - `予約以外`
  - `入院`
  - `面会`
  - `予約じゃない`
  - `予約ではない`

### 内科
- STT: 4 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `内科` (R1_STT_PROPER_NOUN_GROUP)
  - `なんか` (R1_STT_PROPER_NOUN_GROUP)
  - `何か` (R1_STT_PROPER_NOUN_GROUP)
  - `ないか` (R1_STT_PROPER_NOUN_GROUP)

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
- STT: 10 surfaces, OpenAI: 10 surfaces
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
  - `必要ありません`
  - `必要ない`

### 否定単語
- STT: 7 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `違います` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `そうではない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ダメ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `違う`
  - `違って`
  - `間違い`
  - `駄目`
  - `違い`

### 外科
- STT: 16 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `いうか` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `メーカー` (R1_STT_PROPER_NOUN_GROUP)
  - `リバー` (R1_STT_PROPER_NOUN_GROUP)

### 大丈夫
- STT: 0 surfaces, OpenAI: 2 surfaces
- OpenAI サンプル:
  - `大丈夫`
  - `丈夫です`

### 委託予防接種
- STT: 3 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `委託予防接種` (R1_STT_PROPER_NOUN_GROUP)
  - `市役所の` (R1_STT_PROPER_NOUN_GROUP)
  - `予防接種` (R1_STT_PROPER_NOUN_GROUP)

### 心臓
- STT: 1 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `しんぞー` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `心臓`

### 折り返し
- STT: 2 surfaces, OpenAI: 9 surfaces
- STT サンプル:
  - `かけなおし` (R3_STT_KANA_VARIANT)
  - `よっつ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `折り返し`
  - `最後の`
  - `四`
  - `出られなかった`
  - `着信があった`

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

### 携帯
- STT: 6 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `アイフォン` (R3_STT_KANA_VARIANT)
  - `アンドロイド` (R3_STT_KANA_VARIANT)
  - `シンプルフォン` (R3_STT_KANA_VARIANT)
  - `スマートフォン` (R3_STT_KANA_VARIANT)
  - `スマホ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `携帯`
  - `携帯電話`
  - `私の電話`

### 用件
- STT: 19 surfaces, OpenAI: 46 surfaces
- STT サンプル:
  - `確認` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `みっつ` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `忘れた` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `しょしん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `はじめて` (R3_STT_KANA_VARIANT → hearing_yoken_common)
- OpenAI サンプル:
  - `その他確認`
  - `角煮`
  - `教えて`
  - `三`
  - `時間を忘れた`

### 甲状腺
- STT: 0 surfaces, OpenAI: 6 surfaces
- OpenAI サンプル:
  - `甲状腺`
  - `向上`
  - `工場`
  - `攻城戦`
  - `向上専科`

### 肯定
- STT: 17 surfaces, OpenAI: 9 surfaces
- STT サンプル:
  - `OK` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ある` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえす` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `うん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`
  - `そう思う`
  - `その通り`
  - `必要だ`
  - `必要です`

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

### 臨床検査
- STT: 1 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `臨床検査` (R1_STT_PROPER_NOUN_GROUP)

### 途中抜け内容
- STT: 26 surfaces, OpenAI: 33 surfaces
- STT サンプル:
  - `外来会計` (R1_STT_PROPER_NOUN_GROUP)
  - `お会計` (R1_STT_PROPER_NOUN_GROUP)
  - `お金` (R1_STT_PROPER_NOUN_GROUP)
  - `会計` (R1_STT_PROPER_NOUN_GROUP)
  - `外来調剤` (R1_STT_PROPER_NOUN_GROUP)
- OpenAI サンプル:
  - `遺伝診療部`
  - `遺伝`
  - `診療部`
  - `栄養相談`
  - `栄養`
