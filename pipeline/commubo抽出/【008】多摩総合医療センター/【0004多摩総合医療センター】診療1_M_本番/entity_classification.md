# Entity Classification Summary — 多摩総合医療センター / 診療

対象 yaml: 15 本

  - `【008】多摩総合医療センター/【0004多摩総合医療センター】診療1_M_本番/main.yaml`
  - `【008】多摩総合医療センター/【0004多摩総合医療センター】診療1_M_本番/予約日聴取.yaml`
  - `【008】多摩総合医療センター/【0004多摩総合医療センター】診療1_M_本番/前回の症状確認.yaml`
  - `【008】多摩総合医療センター/【0004多摩総合医療センター】診療1_M_本番/受診歴確認.yaml`
  - `【008】多摩総合医療センター/【0004多摩総合医療センター】診療1_M_本番/生年月日復唱なし.yaml`
  - `【008】多摩総合医療センター/【0004多摩総合医療センター】診療1_M_本番/生年月日聴取.yaml`
  - `【008】多摩総合医療センター/【0004多摩総合医療センター】診療1_M_本番/用件聴取.yaml`
  - `【008】多摩総合医療センター/【0004多摩総合医療センター】診療1_M_本番/紹介元医療機関聞き取り.yaml`
  - `【008】多摩総合医療センター/【0004多摩総合医療センター】診療1_M_本番/紹介元電話番号聞き取り.yaml`
  - `【008】多摩総合医療センター/【0004多摩総合医療センター】診療1_M_本番/診察券復唱なし.yaml`
  - `【008】多摩総合医療センター/【0004多摩総合医療センター】診療1_M_本番/診察券番号の聴取.yaml`
  - `【008】多摩総合医療センター/【0004多摩総合医療センター】診療1_M_本番/診療科復唱なし.yaml`
  - `【008】多摩総合医療センター/【0004多摩総合医療センター】診療1_M_本番/診療科聞き取り.yaml`
  - `【008】多摩総合医療センター/【0004多摩総合医療センター】診療1_M_本番/電話番号聴取.yaml`
  - `【008】多摩総合医療センター/【0004多摩総合医療センター】診療1_M_本番/電話番号聴取復唱なし.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 572 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 43 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 31 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 103 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 00_00_01_呼吸器
- STT: 27 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `いうか` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `こー下` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_02_消化器
- STT: 18 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `消化器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `いうか` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `メーカー` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_03_脳神経
- STT: 20 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `脳神経外科` (R1_STT_PROPER_NOUN_GROUP)
  - `いうか` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `の下` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_04_リウマチ
- STT: 27 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `リウマチ外科` (R1_STT_PROPER_NOUN_GROUP)
  - `いうか` (R1_STT_PROPER_NOUN_GROUP)
  - `げか` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `メーカー` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_05_神内
- STT: 15 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `神経脳血管内科` (R1_STT_PROPER_NOUN_GROUP)
  - `シンペイ` (R1_STT_PROPER_NOUN_GROUP)
  - `神経の` (R1_STT_PROPER_NOUN_GROUP)
  - `進展` (R1_STT_PROPER_NOUN_GROUP)
  - `動脈瘤` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_分岐あり診療科
- STT: 26 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `リウマチ` (R1_STT_PROPER_NOUN_GROUP)
  - `リューマチ` (R1_STT_PROPER_NOUN_GROUP)
  - `リュウマチ` (R1_STT_PROPER_NOUN_GROUP)
  - `りゅうまち` (R1_STT_PROPER_NOUN_GROUP)
  - `夕待ち` (R1_STT_PROPER_NOUN_GROUP)

### 01_00_分岐なし診療科
- STT: 439 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `ゲノム診療科` (R1_STT_PROPER_NOUN_GROUP)
  - `NIPT` (R1_STT_PROPER_NOUN_GROUP)
  - `え飲む` (R1_STT_PROPER_NOUN_GROUP)
  - `ゲノム` (R1_STT_PROPER_NOUN_GROUP)
  - `で飲む` (R1_STT_PROPER_NOUN_GROUP)

### お問い合わせ内訳
- STT: 2 surfaces, OpenAI: 3 surfaces
- STT サンプル:
  - `問い合わせ` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `その他` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `疑義照会`
  - `薬局`
  - `診療`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### 分からない
- STT: 6 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `ません` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `わかりません` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `持っていない` (R2_STT_TEMPLATE_REUSE → hearing_phone_number)
- OpenAI サンプル:
  - `分からない`
  - `解らない`
  - `分かりません`
  - `持ってない`
  - `動かない`

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

### 否定
- STT: 12 surfaces, OpenAI: 6 surfaces
- STT サンプル:
  - `いいえ` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `ちがう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `ちゃうちゃう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `まちがった` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `違います` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `新しく`
  - `何度`
  - `何度かあります`
  - `何度かある`
  - `最新`

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
- STT: 18 surfaces, OpenAI: 62 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `その他` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `取り消す`
  - `お見舞い`
  - `飲み方`
  - `会計`
  - `行き方`

### 肯定
- STT: 10 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `はい` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `あってます` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうそう` (R3_STT_KANA_VARIANT → hearing_yesno_common)
  - `そうです` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `はーい` (R3_STT_KANA_VARIANT → hearing_yesno_common)
- OpenAI サンプル:
  - `配送です`
  - `その通り`
  - `受けたことない`
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
