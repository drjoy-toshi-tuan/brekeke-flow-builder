# Entity Classification Summary — 羽生総合病院 / 診療

対象 yaml: 9 本

  - `【024】羽生総合病院/【羽生総合病院】診療1_M_本番/main.yaml`
  - `【024】羽生総合病院/【羽生総合病院】診療1_M_本番/予約日聞取り.yaml`
  - `【024】羽生総合病院/【羽生総合病院】診療1_M_本番/当日予約.yaml`
  - `【024】羽生総合病院/【羽生総合病院】診療1_M_本番/生年月日聞き取りTEST.yaml`
  - `【024】羽生総合病院/【羽生総合病院】診療1_M_本番/用件.yaml`
  - `【024】羽生総合病院/【羽生総合病院】診療1_M_本番/紹介状確認.yaml`
  - `【024】羽生総合病院/【羽生総合病院】診療1_M_本番/診察券番号.yaml`
  - `【024】羽生総合病院/【羽生総合病院】診療1_M_本番/診療科.yaml`
  - `【024】羽生総合病院/【羽生総合病院】診療1_M_本番/連絡先聴取.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 494 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 60 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 50 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 138 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 00_00_分岐あり診療科
- STT: 34 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器` (R1_STT_PROPER_NOUN_GROUP)
  - `コピー機` (R1_STT_PROPER_NOUN_GROUP)
  - `吸気` (R1_STT_PROPER_NOUN_GROUP)
  - `五九` (R1_STT_PROPER_NOUN_GROUP)
  - `入金` (R1_STT_PROPER_NOUN_GROUP)

### 01_00_分岐なし診療科
- STT: 391 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `リウマチ膠原病内科` (R1_STT_PROPER_NOUN_GROUP)
  - `B町` (R1_STT_PROPER_NOUN_GROUP)
  - `H` (R1_STT_PROPER_NOUN_GROUP)
  - `U町` (R1_STT_PROPER_NOUN_GROUP)
  - `いう混抗原量` (R1_STT_PROPER_NOUN_GROUP)

### 01_呼吸器
- STT: 14 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `お休憩か` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `形が` (R1_STT_PROPER_NOUN_GROUP)

### 03_甲状腺
- STT: 16 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `えが` (R1_STT_PROPER_NOUN_GROUP)
  - `がいか` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
- OpenAI サンプル:
  - `糖尿内分泌`
  - `ない分室`
  - `糖尿病外来`
  - `糖尿毎度んす`

### 04_小児科
- STT: 23 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `リハビリテーション科` (R1_STT_PROPER_NOUN_GROUP)
  - `ミカミ` (R1_STT_PROPER_NOUN_GROUP)
  - `ミリ` (R1_STT_PROPER_NOUN_GROUP)
  - `リハ` (R1_STT_PROPER_NOUN_GROUP)
  - `リハビリ` (R1_STT_PROPER_NOUN_GROUP)

### わからない
- STT: 7 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わすれた` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `覚えていない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `覚えてない`
  - `書いていない`
  - `知らない`
  - `分からない`
  - `分からん`

### 予約不要
- STT: 1 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `腎臓内科` (R1_STT_PROPER_NOUN_GROUP)

### 予約対応なし
- STT: 2 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `病理診断科` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
  - `麻酔科` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
- OpenAI サンプル:
  - `予約対応なし`

### 代表案内
- STT: 4 surfaces, OpenAI: 9 surfaces
- STT サンプル:
  - `リハビリテーション科` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
  - `緩和ケア` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
  - `歯科口腔外科` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
  - `小児科` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
- OpenAI サンプル:
  - `代表案内`
  - `胃婁交換`
  - `外来化学療法`
  - `救急科`
  - `心理療法室`

### 代表案内案件
- STT: 6 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `エンジン` (R3_STT_KANA_VARIANT)
  - `ドック` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `健康診断` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `健診` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `検診` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
- OpenAI サンプル:
  - `代表案内`
  - `原因`

### 健診
- STT: 11 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `健診` (R1_STT_PROPER_NOUN_GROUP)
  - `エンジン` (R1_STT_PROPER_NOUN_GROUP)
  - `ドック健診` (R1_STT_PROPER_NOUN_GROUP)
  - `会社の` (R1_STT_PROPER_NOUN_GROUP)
  - `会社の健診` (R1_STT_PROPER_NOUN_GROUP)

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
- STT: 14 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いいです` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `ちがう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ちゃうちゃう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `今日じゃない`
  - `否定`
  - `EHが今`
  - `持ってない`
  - `違う`

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
- STT: 12 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `もってない` (R3_STT_KANA_VARIANT)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `もっていない` (R3_STT_KANA_VARIANT)
  - `もってませーん` (R3_STT_KANA_VARIANT)
  - `持っていません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `手元にありません`
  - `持ってない`
  - `以てない`
  - `持ってませーん`
  - `持ってません`

### 用件
- STT: 26 surfaces, OpenAI: 57 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `さん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `さんばん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `サンバン` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `３`
  - `三番`
  - `取り消す`
  - `二百株`
  - `予約キャンセル`

### 肯定
- STT: 15 surfaces, OpenAI: 14 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうそう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はーい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `今日がいい`
  - `今日で`
  - `配送です`
  - `肯定`
  - `異常部`

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

### 腎臓内科
- STT: 6 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `腎臓内科` (R1_STT_PROPER_NOUN_GROUP)
  - `ジンナイ` (R1_STT_PROPER_NOUN_GROUP)
  - `現像内科` (R1_STT_PROPER_NOUN_GROUP)
  - `腎臓` (R1_STT_PROPER_NOUN_GROUP)
  - `腎臓前か` (R1_STT_PROPER_NOUN_GROUP)

### 面会
- STT: 0 surfaces, OpenAI: 13 surfaces
- OpenAI サンプル:
  - `面会`
  - `オンライン面会`
  - `お見舞い`
  - `リモート面会`
  - `宴会`
