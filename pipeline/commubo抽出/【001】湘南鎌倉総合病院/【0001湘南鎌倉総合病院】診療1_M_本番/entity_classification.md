# Entity Classification Summary — 湘南鎌倉総合病院 / 診療

対象 yaml: 7 本

  - `【001】湘南鎌倉総合病院/【0001湘南鎌倉総合病院】診療1_M_本番/main.yaml`
  - `【001】湘南鎌倉総合病院/【0001湘南鎌倉総合病院】診療1_M_本番/予約日（0205 new）.yaml`
  - `【001】湘南鎌倉総合病院/【0001湘南鎌倉総合病院】診療1_M_本番/生年月日聞き取り.yaml`
  - `【001】湘南鎌倉総合病院/【0001湘南鎌倉総合病院】診療1_M_本番/用件聞き取り.yaml`
  - `【001】湘南鎌倉総合病院/【0001湘南鎌倉総合病院】診療1_M_本番/診察券番号（0312 renew）.yaml`
  - `【001】湘南鎌倉総合病院/【0001湘南鎌倉総合病院】診療1_M_本番/診療科：1_29修正（心療内科非対応）.yaml`
  - `【001】湘南鎌倉総合病院/【0001湘南鎌倉総合病院】診療1_M_本番/連絡先電話番号聞き取り.yaml`

## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)

- 人名
- 数字
- 日付
- 時刻

## ルール別件数

| ルール | 件数 | 行き先 |
| --- | ---: | --- |
| R1_STT_PROPER_NOUN_GROUP | 582 | STT 辞書 (additional_words) |
| R2_STT_TEMPLATE_REUSE | 58 | STT 辞書 (use_template) |
| R3_STT_KANA_VARIANT | 35 | STT 辞書 (yomi) |
| R4_OPENAI_SYNONYM | 192 | OpenAI 正規化 |

## 詳細 (entity 単位)

### 00_00_01_呼吸器
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `呼吸器外科` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `レッカー` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_02_内分泌
- STT: 16 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `糖尿病内分泌科` (R1_STT_PROPER_NOUN_GROUP)
  - `ないか` (R1_STT_PROPER_NOUN_GROUP)
  - `何か` (R1_STT_PROPER_NOUN_GROUP)
  - `内科` (R1_STT_PROPER_NOUN_GROUP)
  - `内分泌内科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_03_甲状腺
- STT: 18 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `糖尿病内分泌科` (R1_STT_PROPER_NOUN_GROUP)
  - `ないか` (R1_STT_PROPER_NOUN_GROUP)
  - `何か` (R1_STT_PROPER_NOUN_GROUP)
  - `甲状腺内分泌内科` (R1_STT_PROPER_NOUN_GROUP)
  - `内科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_04_肝胆膵
- STT: 14 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `肝胆膵外科` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `レッカー` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_05_リハビリ
- STT: 11 surfaces, OpenAI: 32 surfaces
- STT サンプル:
  - `スポ` (R3_STT_KANA_VARIANT)
  - `スポーツ` (R3_STT_KANA_VARIANT)
  - `ソノダ` (R3_STT_KANA_VARIANT)
  - `その他` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `形成外科` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
- OpenAI サンプル:
  - `リハビリテーションスポーツ`
  - `スポーツリハ`
  - `スポーツリハビリ`
  - `スポーツリハビリテーション`
  - `リハビリテーションその他`

### 00_00_06_脳神経
- STT: 17 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `脳神経外科` (R1_STT_PROPER_NOUN_GROUP)
  - `けが` (R1_STT_PROPER_NOUN_GROUP)
  - `てか` (R1_STT_PROPER_NOUN_GROUP)
  - `レッカー` (R1_STT_PROPER_NOUN_GROUP)
  - `外科` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_07_放射線科
- STT: 10 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `放射線その他` (R1_STT_PROPER_NOUN_GROUP)
  - `その他` (R1_STT_PROPER_NOUN_GROUP)
  - `そんた` (R1_STT_PROPER_NOUN_GROUP)
  - `放射線検査` (R1_STT_PROPER_NOUN_GROUP)
  - `検査` (R1_STT_PROPER_NOUN_GROUP)

### 00_00_分岐あり診療科
- STT: 22 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `リハビリテーション` (R1_STT_PROPER_NOUN_GROUP)
  - `リハ` (R1_STT_PROPER_NOUN_GROUP)
  - `リハビリ` (R1_STT_PROPER_NOUN_GROUP)
  - `リハビリテーションセンター` (R1_STT_PROPER_NOUN_GROUP)
  - `リハビリテーション科` (R1_STT_PROPER_NOUN_GROUP)

### 00_01_01_産婦人科
- STT: 19 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `産科` (R1_STT_PROPER_NOUN_GROUP)
  - `あんた` (R1_STT_PROPER_NOUN_GROUP)
  - `なんか` (R1_STT_PROPER_NOUN_GROUP)
  - `三か` (R1_STT_PROPER_NOUN_GROUP)
  - `三個` (R1_STT_PROPER_NOUN_GROUP)

### 00_01_02_整形外科
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `外傷整形外科` (R1_STT_PROPER_NOUN_GROUP)
  - `外傷` (R1_STT_PROPER_NOUN_GROUP)
  - `代表` (R1_STT_PROPER_NOUN_GROUP)
  - `大庄` (R1_STT_PROPER_NOUN_GROUP)
  - `賠償` (R1_STT_PROPER_NOUN_GROUP)

### 00_01_分岐あり診療科
- STT: 10 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `産婦人科` (R1_STT_PROPER_NOUN_GROUP)
  - `さんふじんか` (R1_STT_PROPER_NOUN_GROUP)
  - `その婦人科` (R1_STT_PROPER_NOUN_GROUP)
  - `三九人か` (R1_STT_PROPER_NOUN_GROUP)
  - `整形外科` (R1_STT_PROPER_NOUN_GROUP)

### 01_00_分岐なし診療科
- STT: 350 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `アレルギー科` (R1_STT_PROPER_NOUN_GROUP)
  - `アレルギー` (R1_STT_PROPER_NOUN_GROUP)
  - `アレルギー内科` (R1_STT_PROPER_NOUN_GROUP)
  - `免疫` (R1_STT_PROPER_NOUN_GROUP)
  - `免疫アレルギーセンター` (R1_STT_PROPER_NOUN_GROUP)

### 01_01_分岐なし診療科（別復唱）
- STT: 11 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `人工透析` (R1_STT_PROPER_NOUN_GROUP)
  - `PD` (R1_STT_PROPER_NOUN_GROUP)
  - `PD外来` (R1_STT_PROPER_NOUN_GROUP)
  - `腹膜` (R1_STT_PROPER_NOUN_GROUP)
  - `腹膜透析` (R1_STT_PROPER_NOUN_GROUP)

### 01_02_分岐なし診療科（診療科確認）
- STT: 11 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `CT` (R1_STT_PROPER_NOUN_GROUP)
  - `IVRセンター` (R1_STT_PROPER_NOUN_GROUP)
  - `IVR` (R1_STT_PROPER_NOUN_GROUP)
  - `MRI` (R1_STT_PROPER_NOUN_GROUP)
  - `レントゲン` (R1_STT_PROPER_NOUN_GROUP)

### 01_03_分岐なし診療科
- STT: 12 surfaces, OpenAI: 0 surfaces
- STT サンプル:
  - `スポーツ総合診療センター` (R1_STT_PROPER_NOUN_GROUP)
  - `スポ` (R1_STT_PROPER_NOUN_GROUP)
  - `スポーツ` (R1_STT_PROPER_NOUN_GROUP)
  - `スポーツ外来` (R1_STT_PROPER_NOUN_GROUP)
  - `スポーツ整形` (R1_STT_PROPER_NOUN_GROUP)

### もう一度
- STT: 0 surfaces, OpenAI: 2 surfaces
- OpenAI サンプル:
  - `もう一度`
  - `もう一回`

### もしもし
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `もしもし`

### わからない
- STT: 9 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `わからない` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
  - `しらない` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しらん` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `しりません` (R3_STT_KANA_VARIANT → hearing_unknown)
  - `ない` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `解らない`
  - `覚えてない`
  - `動かない`
  - `分からない`
  - `分かりません`

### キャンセル
- STT: 4 surfaces, OpenAI: 1 surfaces
- STT サンプル:
  - `キャンセル` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `やめる` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取り消し` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `取消` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `取り消す`

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

### 変更
- STT: 2 surfaces, OpenAI: 10 surfaces
- STT サンプル:
  - `変更` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `別の` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `延期`
  - `時間`
  - `取り直したい`
  - `取り直す`
  - `日程`

### 定期受診
- STT: 2 surfaces, OpenAI: 26 surfaces
- STT サンプル:
  - `循環器` (R2_STT_TEMPLATE_REUSE → hearing_shinryoka_basic)
  - `再診` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `定期受診`
  - `受診予約`
  - `定期`
  - `H受信`
  - `H住信`

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
- STT: 5 surfaces, OpenAI: 9 surfaces
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

### 新規予約
- STT: 2 surfaces, OpenAI: 5 surfaces
- STT サンプル:
  - `新規予約` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `初診` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
- OpenAI サンプル:
  - `取りたい`
  - `取得`
  - `紹介状`
  - `診察の予約`
  - `診療予約`

### 日にちのみ
- STT: 0 surfaces, OpenAI: 1 surfaces
- OpenAI サンプル:
  - `日にちのみ`

### 確認
- STT: 3 surfaces, OpenAI: 7 surfaces
- STT サンプル:
  - `確認` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
  - `なくした` (R3_STT_KANA_VARIANT)
  - `忘れた` (R2_STT_TEMPLATE_REUSE → hearing_unknown)
- OpenAI サンプル:
  - `お聞き`
  - `教えて`
  - `調べて`
  - `分からない`
  - `分からん`

### 肯定
- STT: 0 surfaces, OpenAI: 4 surfaces
- OpenAI サンプル:
  - `肯定`
  - `異常部`
  - `丈夫`
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

### 診察予約
- STT: 5 surfaces, OpenAI: 29 surfaces
- STT サンプル:
  - `はじめて` (R3_STT_KANA_VARIANT)
  - `再診` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `初めて` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `初診` (R2_STT_TEMPLATE_REUSE → hearing_yesno_common)
  - `新規` (R2_STT_TEMPLATE_REUSE → hearing_yoken_common)
- OpenAI サンプル:
  - `診察予約`
  - `はい新薬`
  - `印刷`
  - `禁忌`
  - `最新`

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
