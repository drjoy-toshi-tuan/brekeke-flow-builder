# Entity Classification Summary — 新潟県けんこう財団 / 健診

対象 yaml: 12 本

  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【004健昌会】健診1_M_本番/main.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【004健昌会】健診1_M_本番/オプション追加変更有無.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【004健昌会】健診1_M_本番/予約日確定有無確認.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【004健昌会】健診1_M_本番/受診票有無確認.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【004健昌会】健診1_M_本番/問合せ先施設名.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【004健昌会】健診1_M_本番/変更希望日.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【004健昌会】健診1_M_本番/希望時間帯.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【004健昌会】健診1_M_本番/現在の予約日聞き取り.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【004健昌会】健診1_M_本番/生年月日聞き取り.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【004健昌会】健診1_M_本番/用件聞き取り.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【004健昌会】健診1_M_本番/登録番号聞き取り.yaml`
  - `【033】新潟県けんこう財団｜【034】健昌会｜【035】新潟縣健康管理協会/【004健昌会】健診1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 0 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 55 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 135 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 216 | OpenAI 正規化 |

## 詳細 (entity 単位)

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

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
- STT: 2 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `初めて` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はじめて` (R3_STT_KANA_VARIANT)

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

### 受診希望施設名
- STT: 17 surfaces, OpenAI: 30 surfaces
- STT サンプル:
  - `うめだ` (R3_STT_KANA_VARIANT)
  - `うめ` (R3_STT_KANA_VARIANT)
  - `キンイチ` (R3_STT_KANA_VARIANT)
  - `きんき` (R3_STT_KANA_VARIANT)
  - `キンキ` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `1`
  - `一`
  - `一番`
  - `近畿`
  - `2`

### 否定
- STT: 16 surfaces, OpenAI: 11 surfaces
- STT サンプル:
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ニ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `にばん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `2`
  - `２`
  - `違う`
  - `間違い`

### 否定単語
- STT: 21 surfaces, OpenAI: 13 surfaces
- STT サンプル:
  - `ありません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いえ` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `いや` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `じゃない` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `否定`
  - `違い`
  - `違う`
  - `違って`
  - `駄目`

### 届いている
- STT: 3 surfaces, OpenAI: 10 surfaces
- STT サンプル:
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ある` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `もらいました` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `届いている`
  - `持ってます`
  - `受け取りました`
  - `送ってもらいました`
  - `届いた`

### 届いてない
- STT: 4 surfaces, OpenAI: 12 surfaces
- STT サンプル:
  - `きてません` (R3_STT_KANA_VARIANT)
  - `こない` (R3_STT_KANA_VARIANT)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `持っていません` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `届いてない`
  - `持ってない`
  - `持ってませーん`
  - `持ってません`
  - `送ってこない`

### 希望時間帯
- STT: 15 surfaces, OpenAI: 25 surfaces
- STT サンプル:
  - `に` (R3_STT_KANA_VARIANT)
  - `ニ` (R3_STT_KANA_VARIANT)
  - `にーばん` (R3_STT_KANA_VARIANT)
  - `にばん` (R3_STT_KANA_VARIANT)
  - `ニバン` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `10時～11時台`
  - `10時`
  - `10時台`
  - `11時`
  - `11時台`

### 希望無し
- STT: 4 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `いつでも` (R3_STT_KANA_VARIANT)
  - `おまかせ` (R3_STT_KANA_VARIANT)
  - `どちらでも` (R3_STT_KANA_VARIANT)
  - `どっちでも` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `希望無し`
  - `希望はない`
  - `空いている時間`
  - `空いてる時間`
  - `空きがある`

### 持っている
- STT: 5 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ある` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `いまーす` (R3_STT_KANA_VARIANT)
  - `います` (R3_STT_KANA_VARIANT)
  - `いる` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `持っている`
  - `持っていまーす`
  - `持ってまーす`
  - `持ってます`
  - `盛ってまーす`

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

### 数字の３
- STT: 1 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `さん` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `3`
  - `３`
  - `3バン`
  - `３番`
  - `三`

### 決まっていない
- STT: 5 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `いない` (R3_STT_KANA_VARIANT)
  - `いませーん` (R3_STT_KANA_VARIANT)
  - `いません` (R3_STT_KANA_VARIANT)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ません` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `決まっていない`
  - `決まってない`
  - `決まってません`

### 決まっている
- STT: 1 surfaces, OpenAI: 4 surfaces
- STT サンプル:
  - `います` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `決まっている`
  - `決まっています`
  - `決まってます`
  - `決まってる`

### 用件
- STT: 27 surfaces, OpenAI: 46 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `きゃんせる` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `ニ` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `ニバン` (R3_STT_KANA_VARIANT → hearing_yoken_common)
  - `にばん` (R3_STT_KANA_VARIANT → hearing_yoken_common)
- OpenAI サンプル:
  - `2`
  - `２`
  - `取り消す`
  - `二`
  - `二番`

### 肯定
- STT: 26 surfaces, OpenAI: 12 surfaces
- STT サンプル:
  - `あります` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ある` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `うん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `うんうん` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `したい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `肯定`
  - `1`
  - `１`
  - `一`
  - `一番`

### 肯定エンティティ
- STT: 11 surfaces, OpenAI: 2 surfaces
- STT サンプル:
  - `あっています` (R3_STT_KANA_VARIANT)
  - `あってます` (R3_STT_KANA_VARIANT)
  - `うん` (R3_STT_KANA_VARIANT)
  - `うんうん` (R3_STT_KANA_VARIANT)
  - `そう` (R3_STT_KANA_VARIANT)
- OpenAI サンプル:
  - `肯定`
  - `大丈夫`

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
