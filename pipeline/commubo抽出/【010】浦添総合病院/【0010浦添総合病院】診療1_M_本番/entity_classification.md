# Entity Classification Summary — 浦添総合病院 / 診療

対象 yaml: 7 本

  - `【010】浦添総合病院/【0010浦添総合病院】診療1_M_本番/main.yaml`
  - `【010】浦添総合病院/【0010浦添総合病院】診療1_M_本番/予約日聞き取り.yaml`
  - `【010】浦添総合病院/【0010浦添総合病院】診療1_M_本番/当日予約確認：5_16.yaml`
  - `【010】浦添総合病院/【0010浦添総合病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【010】浦添総合病院/【0010浦添総合病院】診療1_M_本番/用件聴取.yaml`
  - `【010】浦添総合病院/【0010浦添総合病院】診療1_M_本番/診療科.yaml`
  - `【010】浦添総合病院/【0010浦添総合病院】診療1_M_本番/連絡先聴取.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 367 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 40 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 66 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 175 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 01_00_分岐なし診療科
- STT: 201 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `いうか` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `レッカー` (R1_STT_PROPER_NOUN_GROUP)

### 01_01復唱用
- STT: 72 surfaces, OpenAI: 45 surfaces
- STT サンプル:
  - `シーエスアイ` (R3_STT_KANA_VARIANT)
  - `エスディエム` (R3_STT_KANA_VARIANT)
  - `フットケア` (R3_STT_KANA_VARIANT)
  - `グッとペア` (R3_STT_KANA_VARIANT)
  - `フット` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `CSI`
  - `csi`
  - `秀才`
  - `IBD`
  - `ibd`

### もう一度
- STT: 0 surfaces, OpenAI: 3 surfaces
- OpenAI サンプル:
  - `もう一度`
  - `もう一回`
  - `再度`

### わからない
- STT: 4 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しりません` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `覚えていない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `覚えてない`
  - `書いていない`
  - `知らない`

### 内科
- STT: 3 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `内科` (R1_STT_PROPER_NOUN_GROUP)
  - `ないか` (R1_STT_PROPER_NOUN_GROUP)
  - `何` (R1_STT_PROPER_NOUN_GROUP)

### 分からない
- STT: 5 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかんないです` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `忘れた` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `知らない`
  - `分からない`
  - `分かんない`

### 分岐あり_呼吸器
- STT: 28 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `いうか` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `こー下` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)

### 分岐あり_心臓
- STT: 34 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `循環器内科` (R1_STT_PROPER_NOUN_GROUP)
  - `ハート` (R1_STT_PROPER_NOUN_GROUP)
  - `ペースメーカー` (R1_STT_PROPER_NOUN_GROUP)
  - `循環` (R1_STT_PROPER_NOUN_GROUP)
  - `循環器` (R1_STT_PROPER_NOUN_GROUP)

### 分岐あり_膵臓・肝臓
- STT: 14 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `外科` (R1_STT_PROPER_NOUN_GROUP)
  - `げか` (R1_STT_PROPER_NOUN_GROUP)
  - `レッカー` (R1_STT_PROPER_NOUN_GROUP)
  - `形が` (R1_STT_PROPER_NOUN_GROUP)
  - `経過` (R1_STT_PROPER_NOUN_GROUP)

### 分岐あり_術前
- STT: 16 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `きょうどう` (R3_STT_KANA_VARIANT)
  - `きょうどー` (R3_STT_KANA_VARIANT)
  - `きょーどー` (R3_STT_KANA_VARIANT)
  - `整形外科` (R1_STT_PROPER_NOUN_GROUP)
  - `TK` (R1_STT_PROPER_NOUN_GROUP)
- OpenAI サンプル:
  - `共同診`
  - `支援`

### 分岐あり診療科
- STT: 24 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `肝臓` (R1_STT_PROPER_NOUN_GROUP)
  - `かんぞー` (R1_STT_PROPER_NOUN_GROUP)
  - `乾燥` (R1_STT_PROPER_NOUN_GROUP)
  - `感情` (R1_STT_PROPER_NOUN_GROUP)
  - `感想` (R1_STT_PROPER_NOUN_GROUP)

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
- STT: 12 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いいです` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `ちがう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `まちがった` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `結構です`
  - `必要ありません`
  - `必要ない`
  - `否定`
  - `結構です`

### 否定エンティティ
- STT: 4 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `いーえ` (R3_STT_KANA_VARIANT)
  - `そうじゃない` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `ちがいます` (R2_STT_TEMPLATE_REUSE → echo_back_yesno)
  - `チガウ` (R3_STT_KANA_VARIANT)
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

### 用件
- STT: 20 surfaces, OpenAI: 77 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `に` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `にばん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `ユーザースキャンする` (R3_STT_KANA_VARIANT → hearing_yoken_common)
- OpenAI サンプル:
  - `2`
  - `２`
  - `ちゃん製`
  - `取り消す`
  - `二番`

### 肯定
- STT: 12 surfaces, OpenAI: 11 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうしたい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうそう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`
  - `異常部`
  - `丈夫`
  - `大丈夫`
  - `希望します`

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
- STT: 0 surfaces, OpenAI: 5 surfaces
- OpenAI サンプル:
  - `肯定`
  - `異常部`
  - `丈夫`
  - `大丈夫`
  - `配送です`
