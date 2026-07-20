<!--
施設名: リウマチ科みやもと
シナリオ名: 診療
環境: 本番
元資料: docs/reference/customer_docs/【診療1】：リウマチ科みやもと.md
移管日: 2026-04-27
移管者: 浜口
備考: Gen2→Gen3 移管。リウマチ科専門クリニック・完全予約制。
-->

### 移管方針
- group_name: 「リウマチ科みやもと」（10 字、URL 制限 OK）。flow_name は「リウマチ科みやもと$診療」
- 用件分岐: 3 分岐（予約／体調不良相談／問い合わせ）→ classification 列挙値も 3 種類 + 空文字
- Pattern: **A**（用件確認 generate_by_OpenAI 直後に分岐。echo_back や複数 context 組み合わせ要件は無いため B 不要）
- サブフロー: PatientName / DateOfBirth / PhoneNumber 採用。診察券番号は無し
- Date of Call Classifier: **不要**（営業時間外対応の記述なし。終話 endpoint に「時間外」enum はあるが本文に運用ルール無し → director判断）
- 連絡先電話番号: 着信番号種別（anonymous / mobile=070-090・060 / fixed）で分岐 → mobile/fixed は確認フロー、anonymous は新規聴取（PhoneNumber サブフロー側で吸収）
- 終話: 通常終話 + 電話番号 3 回失敗時の強制終話（END_番号確認不可）
- addCurrentDate: **不要**（datetime hearing 無し。希望日は free text で Preferred date 格納）

### 施設固有の特殊ルール
- リウマチ科専門クリニック・**完全予約制**。「予約なしで受診できますか」には「完全予約制となります」と返答してから希望日聴取
- 用件確認後に **9 種の details キーワード分岐** あり（予約変更／当日診察／予約忘れ／空き状況／予約なし受診／予約日欠席／紹介状あり／紹介状なし／転院希望）。1〜8 は希望日 or 症状を追加聴取し `Preferred date` または `details` に格納、9（転院希望）のみ `diagnosis clinic` に「医療機関名と病名」を格納
- キーワード補完ルール（用件確認時）:
  - 「印刷／定期／新薬／再診／最新／禁忌」→ 診察として扱う
  - 「薬／お薬」→ 予約として扱う
  - 「契約変更／契約法」→ 変更、「契約キャンセル」→ キャンセル
- 聴取内容の**復唱禁止**（電話番号のみ telephone 形式で復唱可。ただし SSML 禁止のため Gen3 では `{tts_g:...}` 内で電話番号を読み上げる形に置換）
- 数字キーワード正規化: 「4」は for/four を入れない、「5,5」を「号」と認識しない 等の聴き分けルールあり（OpenAI プロンプトに記述）
- 「すぐに連絡ください」催促 → 「内容を確認のうえ、緊急性を判断〜」と返答
- 「看護師に代わってほしい」→ 「まずはAIが対応〜」と返答
- echo_back 対象: 連絡先電話番号のみ（氏名・生年月日は復唱禁止）
- smsFlag: status=1 のとき "1"、代表番号案内時 "2"、それ以外 "0"
- endpoint enum: 冒頭切断／時間外／電話転送／電話案内／途中切断／通話完了
- status: Preferred date / diagnosis clinic 以外が埋まれば 1（director 判断）

### director が見落としやすいポイント
- 用件分岐は 3 種類だが、details の 9 キーワード分岐は **details 聴取後の二段目分岐**であり用件分類ではない。Pattern A の用件直後分岐 + details 後の ContextMatchRouter で表現
- 初診／再診の概念は表に出ず、「紹介状」「転院希望」が初診相当として diagnosis clinic 聴取に分岐する → 初診/再診サブフロー化はしない（director 判断）
- 連絡先聴取の分岐条件で元資料は「090/080/070/060」と記載（050 は別記）。Gen3 PhoneNumber サブフローのデフォルト判定と差異あり → サブフロー側のデフォルト挙動で吸収する想定（director 判断）
- 終話文言「3 診療日以内に担当者から折り返し電話、もしくはショートメールにてご連絡」は固定文言。SMS 利用施設である点に留意
- 「そのほかに何かお問い合わせは有りませんか？」は question 格納の自由テキスト hearing で、status=1 更新もここで行う
- SSML タグ（`<speak>`/`<break>`/`<say-as>`）は元資料に多数登場するが Gen3 では**全削除**し、`{tts_g:...}` の自然文に置換すること
- 元資料の function 定義に「DesiredreservationDate」という綴りが混在しているが、設計書では `Preferred date` に統一（director 判断）

### 詳細は元資料を参照
docs/reference/customer_docs/【診療1】：リウマチ科みやもと.md
