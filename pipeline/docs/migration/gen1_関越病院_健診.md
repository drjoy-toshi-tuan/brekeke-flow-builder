<!--
施設: 関越病院
シナリオ: 健診
環境: 本番
元資料: commubo抽出/【045】関越病院/【0049関越病院】健診1_M_本番/
移管日: 2026-05-01
移管者: 浜口
備考: Gen1(commubo)→Gen3 移管。13サブシナリオを伴う健診予約フロー。
-->

### 移管方針
- main.yaml の冒頭は `API_DRJOY_CONTEXT_SETTINGS → API_DRJOY → 挨拶` の API 連携。Gen3 標準の冒頭チェーン（incoming-classifier → acceptance_times → opening）に置換。`基本情報` は main.yaml ヘッダーを尊重し `group_name: "関越病院"` / `flow_name: "関越病院$健診"` とする。
- 営業時間は 月〜金 8:30〜17:30 / 土 8:30〜12:00 / 日祝休 / 12/30 12:00〜1/4 年末年始休。Gen3 では acceptance_times に標準セット、年末年始は Dr.JOY 側スケジュールで吸収（ノート内で固定 holidays 配列は持たない）。
- Gen1 にあった `3/2~3/31` ブロック（番号変更告知 050-1808-1225 への誘導）は **一時運用の終了済み告知**。現時点では除外して director 判断、念のため customer_doc に番号変更の事実だけ残す。
- エンティティ仕分けは `entity_classification.md` の R1〜R4 を踏襲。STT 辞書は `hearing_yoken_common / hearing_yesno_common / hearing_unknown / hearing_phone_number / hearing_shinryoka_basic / echo_back_yesno` の use_template 参照、施設固有は additional_words。

### 施設固有の特殊ルール

- **着信元番号で「市の健診」誘導**: `着信元番号判断` で `05017070320` / `08044220245` の 2 番号は「市の乳がん／胃がん検診は代表番号へ」アナウンスを発話してから通常フローへ合流。Gen3 では incoming-classifier 直後に script ブロックで sip ヘッダ from を判定する Pattern 5 相当の小分岐を 1 段挟む（incoming_phone_number 比較の単純 CMR で可）。
- **当日予約の代表電話誘導**: 「健診日 当日のご連絡ですか？」Yes → 代表電話 049-285-3161 をアナウンスして終話（status=2/smsFlag=0）。No → 通常用件聞き取り。Gen1 の `当日予約判別` サブシナリオ→ Gen3 では opening 直後の hearing(yesno)+CMR の 1 セットに圧縮。
- **用件 4 分岐（DTMF + 音声）**: 1=新規予約 / 2=変更キャンセル / 3=その他お問い合わせ / 4=折り返し連絡。`用件聞き取り.yaml` の OpenAI synonyms（健診の予約／日程／取り消し／折返し連絡 等）を SKILL_A の正規化プロンプトに反映。**4 番（折り返し）** は他施設にない関越特有の独立分岐。
- **新規予約フロー**: `希望コース` (1=特定／2=人間ドック／3=一般／4=企業) → `予約希望/人数` (希望日 + 人数) → 担当者名/受診者名 → 生年月日 → 連絡先電話番号。コースは DTMF 4 択 + コース正規化（`費用検針→企業健診` 等の誤認識補正含む）。
- **変更/キャンセルフロー**: `現在の予約日` → `内容or日程orキャンセル 判別`(1=受診内容/2=日程変更/3=キャンセル) → `変更内容または時期 詳細` → `理由聴取（変更/キャンセル）` → 担当者名 → 生年月日 → 連絡先 → 完了。**変更とキャンセルで理由聴取の TTS 文言が違う**（「ご予約変更の理由」「ご予約キャンセルの理由」）ため CMR で分岐。
- **担当者名/受診者名サブフロー**: 1 ステップで「予約された方のお名前（受診者名）」または「お電話いただいている方のお名前（担当者名）」を分岐 TTS で聴取。Gen3 では PatientName サブフロー 1 枠に充当（受診者名 > 担当者名の優先順、memory: feedback_patientname_subflow_allocation）。
- **企業/団体名聴取**: `END_企業団体名聴取` から呼ばれるが main 上は到達経路が見当たらない。**director 判断**（折り返しルートで企業/個人を分けるか、現状は氏名のみで完結させるか）。

### director が見落としやすいポイント

- `用件の分岐_2` は新規／変更キャンセル／折り返しのいずれでも「次へ_3 → 生年月日聴取 → 連絡先電話番号」へ合流し、その他のみ独立で連絡先へ直行する **合流型 4 分岐**。Pattern B の ContextMatchRouter 後段配置がふさわしい。
- `完了フラグ` 箱は **classification 確定 + 用件分岐_1** に渡すブリッジ。Gen3 では save2db でまとめて格納し、その後 ContextMatchRouter で「新規／変更キャンセル／折り返し／その他」分岐 → 各種「申込受付」TTS（`新規` / `変更` / `キャンセル` / `折り返し連絡` / `問い合わせ`）→ `予約変更確認` 共通 TTS → 終話 の構造にする。
- `終話` と `終話_1` の 2 系統は受付完了側 (`END_切断`) と時間外/エラー側 (`END_切断_1`) の使い分けでしかない。Gen3 では status/smsFlag を分けて 1 本化可能。
- `代表案内：049-285-3161` と `代表誘導へ` の 2 つの代表電話アナウンスがあり、TTS 文言は同一。Gen3 では 1 つの termination ブロックに統合。
- 03用件NG → 代表誘導 のチェーンは「3 回聴取失敗 → 代表電話誘導」の聞き取れず終話パターン。共通 retry_count=3 として scaffold 標準。
- TTS 動的値 `<? $course ?>`（希望コース.yaml `変更コースの確認_1`）は Brekeke 解釈不可。`<% course %>` に変換（memory: feedback_tts_dynamic_value_syntax）。
- 全モジュール名 ASCII 化必須（丸数字／日本語ノード名は scaffold で `jump_xxx` 等にリネーム）。CMR.reference_module の subflow 参照は `jump_{step名}`、CMR conditions 末尾は `match: "other"` を必ず入れる。

### 詳細は元資料を参照
commubo抽出/【045】関越病院/【0049関越病院】健診1_M_本番/
