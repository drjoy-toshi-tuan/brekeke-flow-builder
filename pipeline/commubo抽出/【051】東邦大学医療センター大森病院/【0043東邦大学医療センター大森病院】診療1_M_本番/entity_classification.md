# Entity Classification Summary — 東邦大学医療センター大森病院 / 診療

対象 yaml: 13 本

  - `【051】東邦大学医療センター大森病院/【0043東邦大学医療センター大森病院】診療1_M_本番/main.yaml`
  - `【051】東邦大学医療センター大森病院/【0043東邦大学医療センター大森病院】診療1_M_本番/キャンセル詳細チェック.yaml`
  - `【051】東邦大学医療センター大森病院/【0043東邦大学医療センター大森病院】診療1_M_本番/予約希望日.yaml`
  - `【051】東邦大学医療センター大森病院/【0043東邦大学医療センター大森病院】診療1_M_本番/予約日.yaml`
  - `【051】東邦大学医療センター大森病院/【0043東邦大学医療センター大森病院】診療1_M_本番/性別.yaml`
  - `【051】東邦大学医療センター大森病院/【0043東邦大学医療センター大森病院】診療1_M_本番/生年月日.yaml`
  - `【051】東邦大学医療センター大森病院/【0043東邦大学医療センター大森病院】診療1_M_本番/用件.yaml`
  - `【051】東邦大学医療センター大森病院/【0043東邦大学医療センター大森病院】診療1_M_本番/紹介元医療機関名.yaml`
  - `【051】東邦大学医療センター大森病院/【0043東邦大学医療センター大森病院】診療1_M_本番/診察券番号.yaml`
  - `【051】東邦大学医療センター大森病院/【0043東邦大学医療センター大森病院】診療1_M_本番/診療科（セカンドオピニオン）.yaml`
  - `【051】東邦大学医療センター大森病院/【0043東邦大学医療センター大森病院】診療1_M_本番/診療科（初診）.yaml`
  - `【051】東邦大学医療センター大森病院/【0043東邦大学医療センター大森病院】診療1_M_本番/連絡先聴取.yaml`
  - `【051】東邦大学医療センター大森病院/【0043東邦大学医療センター大森病院】診療1_M_本番/連絡先聴取（セカンドオピニオン）.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 529 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 61 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 79 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 159 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 00_00_01_呼吸器
- STT: 15 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器センター外科` (R1_STT_PROPER_NOUN_GROUP)
  - `けか` (R1_STT_PROPER_NOUN_GROUP)
  - `データ` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_02_消化器
- STT: 15 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `消化器センター外科` (R1_STT_PROPER_NOUN_GROUP)
  - `けか` (R1_STT_PROPER_NOUN_GROUP)
  - `データ` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_03_脳神経
- STT: 15 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `脳神経センター外科` (R1_STT_PROPER_NOUN_GROUP)
  - `けか` (R1_STT_PROPER_NOUN_GROUP)
  - `データ` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_04_産婦人科
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `産科` (R1_STT_PROPER_NOUN_GROUP)
  - `あんた` (R1_STT_PROPER_NOUN_GROUP)
  - `なんか` (R1_STT_PROPER_NOUN_GROUP)
  - `三か` (R1_STT_PROPER_NOUN_GROUP)
  - `三個` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_05_循環器
- STT: 14 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `循環器センター外科` (R1_STT_PROPER_NOUN_GROUP)
  - `データ` (R1_STT_PROPER_NOUN_GROUP)
  - `でか` (R1_STT_PROPER_NOUN_GROUP)
  - `駅か` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_06_総合診療
- STT: 9 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `総合診療感染症科` (R1_STT_PROPER_NOUN_GROUP)
  - `感染` (R1_STT_PROPER_NOUN_GROUP)
  - `総感染` (R1_STT_PROPER_NOUN_GROUP)
  - `総合診療内科` (R1_STT_PROPER_NOUN_GROUP)
  - `ないか` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_07_リプロダクションセンター
- STT: 13 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `リプロダクションセンター泌尿器科` (R1_STT_PROPER_NOUN_GROUP)
  - `泌尿器` (R1_STT_PROPER_NOUN_GROUP)
  - `泌尿器科` (R1_STT_PROPER_NOUN_GROUP)
  - `リプロダクションセンター婦人科` (R1_STT_PROPER_NOUN_GROUP)
  - `あんた` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_08_小児医療センター
- STT: 8 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `小児科` (R1_STT_PROPER_NOUN_GROUP)
  - `小児` (R1_STT_PROPER_NOUN_GROUP)
  - `小児外科` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `小児循環器科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_分岐あり診療科
- STT: 31 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `リプロダクションセンター` (R1_STT_PROPER_NOUN_GROUP)
  - `リプロ` (R1_STT_PROPER_NOUN_GROUP)
  - `呼吸器センター` (R1_STT_PROPER_NOUN_GROUP)
  - `コピー機` (R1_STT_PROPER_NOUN_GROUP)
  - `吸気` (R1_STT_PROPER_NOUN_GROUP)

### 00_01_分岐あり診療科
- STT: 4 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `産婦人科` (R1_STT_PROPER_NOUN_GROUP)
  - `その婦人科` (R1_STT_PROPER_NOUN_GROUP)
  - `三九人か` (R1_STT_PROPER_NOUN_GROUP)
  - `三分の印鑑` (R1_STT_PROPER_NOUN_GROUP)

### 01_00_分岐なし診療科
- STT: 345 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `がんセンター` (R1_STT_PROPER_NOUN_GROUP)
  - `がん` (R1_STT_PROPER_NOUN_GROUP)
  - `ペインクリニック` (R1_STT_PROPER_NOUN_GROUP)
  - `ペイン` (R1_STT_PROPER_NOUN_GROUP)
  - `麻酔` (R1_STT_PROPER_NOUN_GROUP)

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

### キャンセル状況確認
- STT: 12 surfaces, OpenAI: 13 surfaces
- STT サンプル:
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ある` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `する` (R3_STT_KANA_VARIANT)
  - `ニバン` (R3_STT_KANA_VARIANT)
  - `にばん` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `希望あり`
  - `2`
  - `希望します`
  - `希望する`
  - `診療する`

### 予約キャンセル
- STT: 3 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `予約キャンセル`

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

### 予約変更
- STT: 2 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `別の` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `変更` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `予約変更`
  - `時間`
  - `日程`
  - `日付`
  - `変え`

### 予約確認
- STT: 6 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `その他` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `なくした` (R3_STT_KANA_VARIANT)
  - `確認` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `忘れた` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `問い合わせ` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `予約確認`
  - `教えて`
  - `調べて`
  - `分からない`
  - `分からん`

### 分からない
- STT: 7 surfaces, OpenAI: 6 surfaces
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
- STT: 2 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `初めて` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はじめて` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `始めて`

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
- STT: 15 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `何度`
  - `持ってない`
  - `持ってません`
  - `EHが今`

### 否定エンティティ
- STT: 5 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `いえ` (R3_STT_KANA_VARIANT)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `よろしくない` (R3_STT_KANA_VARIANT)
  - `違います` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ちゃうちゃう` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `否定`

### 否定単語
- STT: 6 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `違います` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ダメ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ちがう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ノー` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `違い`
  - `違いました`
  - `違う`
  - `違って`
  - `駄目`

### 女性
- STT: 4 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `おんな` (R3_STT_KANA_VARIANT)
  - `じょ` (R3_STT_KANA_VARIANT)
  - `そんな` (R3_STT_KANA_VARIANT)
  - `ほんま` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `女性`
  - `女`

### 定期受診
- STT: 1 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `循環器` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
- OpenAI サンプル:
  - `定期受診`
  - `受診予約`
  - `定期`

### 希望日状況確認
- STT: 10 surfaces, OpenAI: 12 surfaces
- STT サンプル:
  - `いません` (R3_STT_KANA_VARIANT)
  - `しない` (R3_STT_KANA_VARIANT)
  - `しません` (R3_STT_KANA_VARIANT)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `なし` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `決まっていない`
  - `2`
  - `決まっていません`
  - `決まってません`
  - `二番`

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

### 新規予約
- STT: 2 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `新規予約` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `初診` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `健診の予約`
  - `健診予約`
  - `取りたい`
  - `取得`
  - `紹介状`

### 日にちのみ
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `日にちのみ`

### 用件
- STT: 16 surfaces, OpenAI: 38 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `セカンドオピニオン` (R3_STT_KANA_VARIANT → hearing_yoken_common)
- OpenAI サンプル:
  - `3`
  - `三`
  - `取り消す`
  - `4`
  - `四`

### 男性
- STT: 3 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `おと` (R3_STT_KANA_VARIANT)
  - `だん` (R3_STT_KANA_VARIANT)
  - `どこ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `男性`
  - `男`

### 肯定
- STT: 6 surfaces, OpenAI: 8 surfaces
- STT サンプル:
  - `ある` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はーい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `よろしい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `持っています` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `OK` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
- OpenAI サンプル:
  - `肯定`
  - `異常部`
  - `持ってます`
  - `持ってる`
  - `丈夫`

### 肯定エンティティ
- STT: 7 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `あっています` (R3_STT_KANA_VARIANT)
  - `あってます` (R3_STT_KANA_VARIANT)
  - `いいです` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`

### 肯定単語
- STT: 12 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `OK` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `あっています` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あってる` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `大丈夫`
  - `問題ありません`
  - `問題ない`

### 診療科
- STT: 48 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `IVRセンター` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `アレルギー科` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `オンコロジー` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `セカンドオピニオン` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)
  - `フット外来` (R1_STT_PROPER_NOUN_GROUP → hearing_shinryoka_basic)

### 間違い
- STT: 0 surfaces, OpenAI: 4 surfaces
- OpenAI サンプル:
  - `間違い`
  - `違い`
  - `違う`
  - `間違え`
