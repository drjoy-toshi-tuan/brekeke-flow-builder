# Entity Classification Summary — 西宮渡辺病院  / 診療

対象 yaml: 9 本

  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0026西宮渡辺心臓脳・血管センター病院】診療1_M_本番/main.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0026西宮渡辺心臓脳・血管センター病院】診療1_M_本番/予約日の聞き取り.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0026西宮渡辺心臓脳・血管センター病院】診療1_M_本番/変更キャンセル分岐.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0026西宮渡辺心臓脳・血管センター病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0026西宮渡辺心臓脳・血管センター病院】診療1_M_本番/用件聞き取り.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0026西宮渡辺心臓脳・血管センター病院】診療1_M_本番/紹介状の有無確認.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0026西宮渡辺心臓脳・血管センター病院】診療1_M_本番/診察券番号聞き取り.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0026西宮渡辺心臓脳・血管センター病院】診療1_M_本番/診療科聞き取り.yaml`
  - `【020】西宮渡辺病院 ｜【021】 心臓脳血管センター/【0026西宮渡辺心臓脳・血管センター病院】診療1_M_本番/連絡先携帯聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 304 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 41 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 31 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 95 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 01_00_分岐なし診療科
- STT: 75 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `ペースメーカー外来` (R1_STT_PROPER_NOUN_GROUP)
  - `ＩＣＤ` (R1_STT_PROPER_NOUN_GROUP)
  - `ペースメーカー` (R1_STT_PROPER_NOUN_GROUP)
  - `児童精神科` (R1_STT_PROPER_NOUN_GROUP)
  - `シラサキ先生` (R1_STT_PROPER_NOUN_GROUP)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### わからない
- STT: 2 surfaces, OpenAI: 12 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `あかん`
  - `あれへん`
  - `しらへん`
  - `しらん`
  - `しるか`

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

### 分岐あり診療科
- STT: 84 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `血管外科` (R1_STT_PROPER_NOUN_GROUP)
  - `K管理側` (R1_STT_PROPER_NOUN_GROUP)
  - `はたけだ` (R1_STT_PROPER_NOUN_GROUP)
  - `ハタケダ` (R1_STT_PROPER_NOUN_GROUP)
  - `はただ` (R1_STT_PROPER_NOUN_GROUP)

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
- STT: 13 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうじゃないねん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうちゃうねん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ちがう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
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

### 呼吸器外科
- STT: 6 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `吸気外科` (R1_STT_PROPER_NOUN_GROUP)
  - `京急ですか` (R1_STT_PROPER_NOUN_GROUP)
  - `呼外` (R1_STT_PROPER_NOUN_GROUP)
  - `合計` (R1_STT_PROPER_NOUN_GROUP)

### 外科
- STT: 31 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `ウエムラ` (R1_STT_PROPER_NOUN_GROUP)
  - `うえむら` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)

### 心臓血管外科
- STT: 19 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `心臓血管外科` (R1_STT_PROPER_NOUN_GROUP)
  - `解離` (R1_STT_PROPER_NOUN_GROUP)
  - `楽天ログアウト` (R1_STT_PROPER_NOUN_GROUP)
  - `関係か` (R1_STT_PROPER_NOUN_GROUP)
  - `現像結果` (R1_STT_PROPER_NOUN_GROUP)

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
- STT: 9 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `整形外科` (R1_STT_PROPER_NOUN_GROUP)
  - `TK` (R1_STT_PROPER_NOUN_GROUP)
  - `えー外科` (R1_STT_PROPER_NOUN_GROUP)
  - `やました` (R1_STT_PROPER_NOUN_GROUP)
  - `ヤマシタ` (R1_STT_PROPER_NOUN_GROUP)

### 未対応診療科
- STT: 46 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `セカンドオピニオン外来` (R1_STT_PROPER_NOUN_GROUP)
  - `セカンド` (R1_STT_PROPER_NOUN_GROUP)
  - `セカンドオピニオン` (R1_STT_PROPER_NOUN_GROUP)
  - `セカンド便四` (R1_STT_PROPER_NOUN_GROUP)
  - `今度VISA` (R1_STT_PROPER_NOUN_GROUP)

### 用件
- STT: 16 surfaces, OpenAI: 42 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `予約のキャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `取り消す`
  - `その他確認`
  - `角煮`
  - `教えて`
  - `時間を忘れた`

### 緊急救急
- STT: 0 surfaces, OpenAI: 10 surfaces
- OpenAI サンプル:
  - `救急`
  - `QQ`
  - `UU`
  - `いう牛`
  - `急激`

### 肯定
- STT: 7 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `そうそう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はーい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
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

### 脳神経外科
- STT: 11 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `脳神経外科` (R1_STT_PROPER_NOUN_GROUP)
  - `いう神経時間` (R1_STT_PROPER_NOUN_GROUP)
  - `の下` (R1_STT_PROPER_NOUN_GROUP)
  - `の外科` (R1_STT_PROPER_NOUN_GROUP)
  - `の買い` (R1_STT_PROPER_NOUN_GROUP)

### 血管外科
- STT: 23 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `血管外科` (R1_STT_PROPER_NOUN_GROUP)
  - `K管理側` (R1_STT_PROPER_NOUN_GROUP)
  - `はたけだ` (R1_STT_PROPER_NOUN_GROUP)
  - `ハタケダ` (R1_STT_PROPER_NOUN_GROUP)
  - `はただ` (R1_STT_PROPER_NOUN_GROUP)
