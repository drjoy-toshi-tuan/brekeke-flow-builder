# Entity Classification Summary — 相澤病院 / 診療

対象 yaml: 8 本

  - `【012】相澤病院/【0011相澤病院】診療1_M_本番/4_14 削除 予約日聞取り.yaml`
  - `【012】相澤病院/【0011相澤病院】診療1_M_本番/main.yaml`
  - `【012】相澤病院/【0011相澤病院】診療1_M_本番/受診希望今日？.yaml`
  - `【012】相澤病院/【0011相澤病院】診療1_M_本番/生年月日：0129更新.yaml`
  - `【012】相澤病院/【0011相澤病院】診療1_M_本番/用件.yaml`
  - `【012】相澤病院/【0011相澤病院】診療1_M_本番/紹介状聴取.yaml`
  - `【012】相澤病院/【0011相澤病院】診療1_M_本番/診療科.yaml`
  - `【012】相澤病院/【0011相澤病院】診療1_M_本番/連絡先番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 777 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 42 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 39 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 125 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 00_01_呼吸器
- STT: 24 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `いうか` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `こー下` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)

### 00_02_トモ_陽子線
- STT: 20 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `トモセラピーセンター` (R1_STT_PROPER_NOUN_GROUP)
  - `エラーPセンター` (R1_STT_PROPER_NOUN_GROUP)
  - `トモ` (R1_STT_PROPER_NOUN_GROUP)
  - `トモセラピー` (R1_STT_PROPER_NOUN_GROUP)
  - `どもせらピーセンター` (R1_STT_PROPER_NOUN_GROUP)

### 00_03_脳神経
- STT: 19 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `脳神経外科` (R1_STT_PROPER_NOUN_GROUP)
  - `いうか` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `の下` (R1_STT_PROPER_NOUN_GROUP)

### 00_04_循環器
- STT: 7 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `腫瘍循環器科` (R1_STT_PROPER_NOUN_GROUP)
  - `腫瘍` (R1_STT_PROPER_NOUN_GROUP)
  - `腫瘍循環期間` (R1_STT_PROPER_NOUN_GROUP)
  - `受容循環器科` (R1_STT_PROPER_NOUN_GROUP)
  - `循環器内科` (R1_STT_PROPER_NOUN_GROUP)

### 00_05_腫瘍
- STT: 7 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `腫瘍循環器科` (R1_STT_PROPER_NOUN_GROUP)
  - `腫瘍循環期間` (R1_STT_PROPER_NOUN_GROUP)
  - `受容循環器科` (R1_STT_PROPER_NOUN_GROUP)
  - `終了循環期間` (R1_STT_PROPER_NOUN_GROUP)
  - `循環器科` (R1_STT_PROPER_NOUN_GROUP)

### 00_06_精神
- STT: 4 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `腫瘍精神科` (R1_STT_PROPER_NOUN_GROUP)
  - `精神科` (R1_STT_PROPER_NOUN_GROUP)
  - `精神神経科` (R1_STT_PROPER_NOUN_GROUP)
  - `神経科` (R1_STT_PROPER_NOUN_GROUP)

### 00_07_放射線
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `治療科` (R1_STT_PROPER_NOUN_GROUP)
  - `しようか` (R1_STT_PROPER_NOUN_GROUP)
  - `ちりょうか` (R1_STT_PROPER_NOUN_GROUP)
  - `ヒデオか` (R1_STT_PROPER_NOUN_GROUP)
  - `資料` (R1_STT_PROPER_NOUN_GROUP)

### 00_08_小児科
- STT: 19 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `小児科` (R1_STT_PROPER_NOUN_GROUP)
  - `商品` (R1_STT_PROPER_NOUN_GROUP)
  - `将棋` (R1_STT_PROPER_NOUN_GROUP)
  - `小児` (R1_STT_PROPER_NOUN_GROUP)
  - `小児間` (R1_STT_PROPER_NOUN_GROUP)

### 00_09_スポーツ
- STT: 56 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `スポーツリハ科` (R1_STT_PROPER_NOUN_GROUP)
  - `うお釣りは` (R1_STT_PROPER_NOUN_GROUP)
  - `おーついは下` (R1_STT_PROPER_NOUN_GROUP)
  - `おー次は` (R1_STT_PROPER_NOUN_GROUP)
  - `おー釣りは` (R1_STT_PROPER_NOUN_GROUP)

### 00_10_放射線治療科
- STT: 1 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `放射線治療科` (R1_STT_PROPER_NOUN_GROUP)

### 00_分岐あり診療科
- STT: 31 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `スポーツ` (R1_STT_PROPER_NOUN_GROUP)
  - `オオツ` (R1_STT_PROPER_NOUN_GROUP)
  - `スポーツ科` (R1_STT_PROPER_NOUN_GROUP)
  - `大塚` (R1_STT_PROPER_NOUN_GROUP)
  - `疼痛` (R1_STT_PROPER_NOUN_GROUP)

### 01_分岐なし診療科
- STT: 497 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `PETCT` (R1_STT_PROPER_NOUN_GROUP)
  - `CT` (R1_STT_PROPER_NOUN_GROUP)
  - `PET` (R1_STT_PROPER_NOUN_GROUP)
  - `シーティー` (R1_STT_PROPER_NOUN_GROUP)
  - `ペット` (R1_STT_PROPER_NOUN_GROUP)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### わからない
- STT: 5 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わからん` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `不明` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `忘れた` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `解かりません`
  - `解りません`
  - `触らない`
  - `知らない`
  - `分からない`

### 予約確認
- STT: 1 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `確認` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `予約確認`
  - `確認したい`
  - `確認の希望`
  - `確認を希望`
  - `確認希望`

### 代表案内案件
- STT: 9 surfaces, OpenAI: 11 surfaces
- STT サンプル:
  - `ドック` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `ロック` (R3_STT_KANA_VARIANT)
  - `健康診断` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `健診` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
  - `検診` (R2_STT_TEMPLATE_REUSE → hearing_kenshin_course_basic)
- OpenAI サンプル:
  - `代表案内`
  - `健康センター`
  - `健診の結果`
  - `検診の結果`
  - `検針の`

### 内科
- STT: 2 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `内科` (R1_STT_PROPER_NOUN_GROUP)
  - `ないか` (R1_STT_PROPER_NOUN_GROUP)

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
- STT: 3 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ちがう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `そうじゃないねん`
  - `そうちゃうねん`
  - `まちがった`

### 否定エンティティ
- STT: 8 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いーえー` (R3_STT_KANA_VARIANT)
  - `いえ` (R3_STT_KANA_VARIANT)
  - `いや` (R3_STT_KANA_VARIANT)
  - `じゃない` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `否定`
  - `EHが今`

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

### 否定（エンティティ）
- STT: 4 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT)
  - `いや` (R3_STT_KANA_VARIANT)
  - `じゃない` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `否定`

### 外科
- STT: 18 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `っていうか` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `で下` (R1_STT_PROPER_NOUN_GROUP)

### 対応しない診療科
- STT: 58 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `PETCT` (R1_STT_PROPER_NOUN_GROUP)
  - `CP` (R1_STT_PROPER_NOUN_GROUP)
  - `CT` (R1_STT_PROPER_NOUN_GROUP)
  - `PET` (R1_STT_PROPER_NOUN_GROUP)
  - `Z` (R1_STT_PROPER_NOUN_GROUP)

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

### 整形外科
- STT: 2 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `整形外科` (R1_STT_PROPER_NOUN_GROUP)
  - `整形` (R1_STT_PROPER_NOUN_GROUP)

### 用件
- STT: 18 surfaces, OpenAI: 61 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `キャンプ` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `3番`
  - `３番`
  - `よく県する`
  - `三番`
  - `三本`

### 紹介状
- STT: 2 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `もってる` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `紹介状`
  - `紹介状あり`
  - `紹介状あります`

### 肯定
- STT: 6 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうそう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はーい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`
  - `異常部`
  - `丈夫`
  - `大丈夫`
  - `配送です`

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

### 肯定（エンティティ）
- STT: 1 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `はーい` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `肯定`
  - `異常部`
  - `今日がいい`
  - `今日です`
  - `丈夫`
