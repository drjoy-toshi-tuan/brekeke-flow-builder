<!--
施設名: 人間ドック会館クリニック
シナリオ名: 健診
環境: 本番
元資料: docs/reference/customer_docs/【健診1】：人間ドック会館クリニック.md
移管日: 2026-04-20
移管者: 浜口
備考: 更新日時 2026/01/28 (status/smsFlag 再制御・冒頭アナウンス修正済み)。yaml セクションが優先ソース。SSML タグ (`<speak>`, `<dtmf/>` 等) は Gen2 記法。Gen3 では `{tts_g:...}` 小文字のみで、SSML は使用しない。
-->

### 移管方針
- **Date of Call Classifier**: 不要。受付時間分岐・時間外案内は customer_doc に記載なし。
- **冒頭分岐 (非通知判定)**: incoming_classifier で「非通知」→ 非通知拒否 TTS → status=2/smsFlag=0 で termination、catch-all `^*$` → 通常冒頭アナウンスへ。
- **用件聴取 (classification)**: Pattern A。generate_by_OpenAI (enum: 予約/変更/キャンセル/問い合わせ) 直後に OpenAIClassifier で 4分岐。復唱 Yes/No あり (echo_back)、否定時は専用再質問フォーマットへ、聴取失敗時は classification="問い合わせ" を格納してフローは継続。
- **companyCheck (個人/企業)**: Pattern A。Yes/No 型 generate_by_OpenAI + Classifier で 2分岐。「個人」→ 氏名+生年月日、「企業」→ 企業名+担当者名 を聴取後、電話番号フローに合流。
- **電話番号判定**: 着信番号の種別 (携帯=090/080/070/050 / 固定電話 / 非通知) による分岐が必要。script ブロックで phone_type を算出し ContextMatchRouter で `携帯電話`→携帯番号確認 (Incoming_phone_number 復唱 Yes/No)、`固定電話`→手動聴取+復唱に振り分ける (Pattern B)。
- **用件別詳細フロー分岐**: classification 値で 4 ルートに分岐 (ContextMatchRouter、Pattern B)。合流はなく、各ルートが独立して終話チェーンに到達。
- **サブフロー化対象**: 氏名/生年月日/電話番号は必ず Jump to Flow で既存サブフロー呼び出し (個人フロー・企業フローとも patientName に統一格納)。メインへのインライン展開禁止。RAG/FAQ は本施設では無し。
- **終話**: 4 パターン (予約/変更/キャンセル/問い合わせ) + 非通知拒否 + フォールバック問い合わせ。各終話の status/smsFlag は termination_patterns で定義。

### 施設固有の特殊ルール
- **status/smsFlag の特殊遷移**: デフォルト status=0/smsFlag=0、非通知拒否時のみ status=2/smsFlag=0。終話時に (予約 smsFlag=1 / 変更 smsFlag=2 / キャンセル smsFlag=3 / 問合せ smsFlag=4)。終話アナウンス到達前の切断は status=0 保持 (endpoint=冒頭切断/途中切断)。
- **電話番号桁数検証**: 10桁/11桁以外は再ヒアリング。11桁は先頭3桁が 090/080/070/050 のいずれか必須。10桁はこれら先頭3桁禁止 (該当時は再ヒアリング)。先頭0が欠落した9桁/10桁は先頭に "0" を補完。→ script ブロックで正規化+検証ロジックを持つ。
- **携帯番号簡略確認**: 着信が携帯の場合のみ「今おかけいただいている {Incoming_phone_number} でよろしいですか」の Yes/No 確認を行い、Yes なら追加聴取なしで additionalPhoneNumber に格納。固定電話は必ず手動聴取。
- **当日予約拒否**: 受診希望日が本日の場合「当日予約は承っておりません。1週間後以降の日付で再度お話しください」の案内あり (個人/企業共通)。Preferred_date 聴取ブロックでの検証要。
- **用件聴取失敗時のフォールバック**: classification が確定できなかった場合「問い合わせ」として格納し、問い合わせフローに進むが、「その他」聴取はスキップして直接終話 (問い合わせ) へ。
- **option のキーワード救済**: 「特にない/ない/ありません/大丈夫」→ option="なし"、「わからない/わかりません」→ **companyName** に "不明" を格納 (原文誤記の可能性あり、director 判断で option に格納すべきか要確認)。
- **改訂履歴**: 1/28 修正で status/smsFlag 再制御と冒頭アナウンス文言が差し替わり済み。旧版プロンプトが残っている場合は無視し yaml と最新文面を正とする。

### director が見落としやすいポイント
- **企業フローでは patientName に「担当者名」を格納する**（氏名ではなく担当者名） — yaml 指定: 「ご担当者様のお名前を〜」→ 保存先 `[patientName]`、企業名は別途 `company_name`。企業名聴取で復唱禁止。
- **個人/企業で聴取項目数が異なる**: 個人は「健康保険組合」あり (予約時)、企業も「健康保険組合」あり (予約時)。ただし個人では氏名+生年月日、企業では企業名+担当者名で 生年月日を聴取しない設計。director は「企業フローに生年月日なし」を見落としやすい。
- **復唱可能 = 3項目のみ**: 用件・生年月日・電話番号。それ以外は復唱禁止 (氏名・企業名・担当者名・健康保険組合・希望コース・追加オプション・受診希望日・予約日・変更内容・問合せ内容・その他)。scaffold の echo_back 設定で 3 項目以外には付けないこと。
- **復唱後否定用の専用再質問フォーマット**: 用件・生年月日・電話番号の 3 項目のみ。通常の再質問アナウンス A とは別文面で、用件は DTMF 付き。generate_by_OpenAI の retry_prompt で再質問 A/B/C を使い分ける必要あり。
- **dtmf digit="1"**: 用件聴取の固定発話に含まれる。Gen3 では SSML 不可のため、TTS から DTMF タグを剥がし、IVR プロパティ or 並列 DTMF モジュールで代替する必要がある。director は「タグを削除しない」との元資料記載に惑わされず、Gen3 流儀で処理すること。
- **yaml の「AI補完: true/[不正時,リトライ超過時]」**: classification/companyCheck/電話番号判定/用件分岐_内部 等の内部箱で OpenAI ベースの曖昧語彙マッチを行う指定。Gen3 では ContextMatchRouter の前段に classifier を立てるか、classifier 単体で enum 判定する設計へ翻訳する。
- **inqury の誤記**: yaml 問合せ内容聴取_問合せ の保存先が `[inqury]` と誤記されている (function では `inquiry`)。director は function 側の `inquiry` を正として修正すること。
- **「その他」聴取のスキップ条件**: 用件が聴取失敗で問い合わせ扱いになった場合は「その他」を飛ばして終話へ (customer_doc 3-3-4 / 3-4-4 の注記)。

### 詳細は元資料を参照
- `docs/reference/customer_docs/【健診1】：人間ドック会館クリニック.md`
  - function: L1-144 (dialogue_completed スキーマ・endpoint/status/smsFlag enum)
  - プロンプト: L146-914 (復唱ルール・再質問ルール・終話アナウンス文面)
  - yaml (優先ソース): L915-1272 (箱一覧・分岐条件・保存先)
