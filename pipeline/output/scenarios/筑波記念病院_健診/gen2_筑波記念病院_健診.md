<!--
施設名: 筑波記念病院
シナリオ名: 健診
環境: 本番
元資料: docs/reference/customer_docs/【健診】：筑波記念病院.md
移管日: 2026-04-22
移管者: claude (migrate-gen2 skill)
備考: director 軽量ノート運用（同施設 _診療 シナリオは別途存在）
-->

### 移管方針
- 冒頭は opening + 冒頭_アナウンス の2ブロック1セット。冒頭アナウンス文言は元資料原文をそのまま使用（「つくばトータルヘルスプラザ、予約専用、AI電話です。…」）。
- 非通知着信は **incoming-classifier の withheld 分岐** → 非通知終了 TTS（status=3 固定）で即終話。Pattern 5 は使わず regular_next に合流しない。
- 非通知以外の冒頭で **予約日確認（本日より4日目以降か）Yes/No 分岐**（Pattern A: OpenAI直後分岐）。いいえ→代表電話案内 `0298643588` で終話（status=2）、はい→次へ。
- その直後に **企業・個人確認 Yes/No 分岐**（company_check に「企業」or「個人」を格納）で2ルート分岐。以降の氏名・連絡先・用件フローを企業ルート／個人ルートで呼び分ける。
- **企業ルート**は companyName → 担当者名 → 電話番号確認 → 用件 の順。**個人ルート**は 氏名 → 生年月日（復唱あり）→ 電話番号確認 → 用件 の順。
- 用件は DTMF 付き4択（新規予約1 / 変更2 / キャンセル3 / 確認4）。`<dtmf digit="1"/>` タグは用件ブロックの TTS にそのまま保持。
- キャンセルは **企業×キャンセルの場合のみ「キャンセル者名」聴取あり**（reason 格納）、個人×キャンセルは名前再聴取なし → 直接コース確認へ。分岐は **Pattern B（後段 ContextMatchRouter）**: 用件=3 かつ company_check=企業 の複合条件。
- 氏名／生年月日／電話番号は **サブフロー経由（Jump to Flow）**。DTMF聴取・桁数再ヒアリング・生年月日復唱などの定型部品はサブフロー側に閉じ込める。メインにインライン展開しない。
- 終話パターンは `END_非通知終了`（status=3）／`END_代表電話案内_3日以内`（status=2）／`END_問い合わせ代表案内`（status=2, smsFlag=0）／`END_個人終話`（status=1, smsFlag=1/2/3）／`END_企業終話`（status=1, smsFlag=1/2/3）／`END_キャンセル完了`（status=1, smsFlag=4）の6系統を termination_patterns に定義。
- **個人終話／企業終話は連絡先が携帯 or 固定で TTS 文言が分岐**（携帯はSMS案内あり、固定は折り返し電話のみ）。incoming_phone_number 型で分岐する Pattern B をサブフロー直後に配置。
- TTS は全て `{tts_g:...}`（小文字）。`<speak type="telephone">` `<dtmf digit="1"/>` `<break time="500ms"/>` タグは元資料どおり保持（電話番号読み上げ・代表案内）。
- RAG / FAQ：元資料に FAQ 参照ルールの記述はあるが FAQ 本体は未提供 → **RAG 設置なし**（director 判断）。FAQ 系の発話は「その他問い合わせ」扱いで代表案内②へ流す。

### 施設固有の特殊ルール
- **「配当です」＝「はい、そうです」救済**：Yes/No 判定系 prompt に注記必須（肯定語として扱う）。
- **「9番検査」＝「子宮がん検査」／「9体がん」＝「子宮体がん」**の語彙置換。希望コース③（乳がん・子宮がん検診）選択時の subsidyProvider 聴取前段で反映。
- **「ストーリー」＝「1人」**の誤認識救済（人数・予約希望時期ブロック）。
- **数字 4/5 の誤認識救済**：「for/C/Sea」→4、「号/Go」→5。電話番号・生年月日・用件 DTMF の prompt に必須（prompter 担当）。
- **当日予約は AI 不可**：予約希望日が着信日と同日 → 代表電話案内で終話（status=2）。通常フローで生年月日を聴取する前の段階ではなく、新規予約の人数・予約希望時期ブロック後段で検出する設計。director 判断でどのブロックに置くか決める。
- **希望コースは3択 DTMF**（健康診断1 / 人間ドック2 / 乳がん・子宮がん検診のみ3）。**③選択時のみ** subsidyProvider 聴取（市町村名 / 会社名 / その他）。
- **コース語彙揺れ**：「検診/検針/返信/天候診断/返金控寸断」→「健康診断」、「人間ロック/ドック/ロック/人間独」→「人間ドック」、「薬/お薬」→「予約」。course ブロックの prompt に列挙。
- **企業担当者名の保持ルール**：企業ルートで一度 patientName に格納した担当者名は、**キャンセル者名聴取時に上書きしない**（reason に別格納）。PatientName サブフロー側で「企業ルート時の再代入禁止」を prompt に明記（director 判断）。
- **生年月日の年度異常値救済**：2900年代→1900年代に自動変換（例：2980年→1980年）。生年月日サブフロー側で対処。
- **smsFlag マッピング**：新規予約=1 / 変更=2 / 確認=3 / キャンセル=4。endpoint=通話完了以外は全て0。
- **status 判定ルール**（強制終了時）：classification=1 で course または DesiredreservationDate 空欄→status=0、classification=2 で reason 空欄→status=0、classification=3 で reservationDate 空欄→status=0、classification=4 は用件聞き取り済みなら status=1。

### director が見落としやすいポイント
- **受診者氏名は PatientName サブフロー、企業担当者名も PatientName サブフロー**で可（受診者=患者の健診特性上、両者とも患者扱いで問題なし）。ただし **企業名（companyName）は PatientName サブフローに流さない**、`companyName` context 用の hearing ブロック単独で聴取。feedback_patientname_subflow_allocation 参照。
- 『**ご質問いただいた内容は AI 電話ではご対応できませんので、折り返しでご確認させていただきます**』→発話後に**直前フロー質問をもう一度発話**するループ動作。FAQ ブロックは ContextMatchRouter で直前ブロックに戻す設計。
- 『**回答待ち中は次の質問をしない**』『**再質問は2回まで**』→ 各聴取サブフロー／hearing ブロックの Max Retry=2 を徹底。
- 『**聴取内容の復唱は生年月日のみ**』→ 氏名・電話番号・診察券番号系の echo_back は無効化（save2db の echo_back=false）。
- **連絡先電話番号の桁数バリデーション**は3回まで（初回＋再2回）、同じエラー文言「うまく聞き取りができませんでした。再度ご連絡先の電話番号をお話ください。」で再ヒアリング。電話番号サブフロー側で対応。
- **`smsFlag=1/2/3` は classification と endpoint の組合せで決まる**ため、終話ブロック側で script/更新値を分岐させる必要あり。termination_patterns の `update_context` に classification 別パターンを用意（director 判断）。
- **予約日（reservationDate）は日付形式、予約希望日（DesiredreservationDate）はフリーワード文字起こし**。格納フォーマットが異なる点に注意。
- 改訂履歴（2026/03/20）：再質問は2回まで／FAQ未登録内容への自由回答禁止 → この2点は prompter 向けの安全性注記として generate_by_OpenAI の全 prompt に織り込む。

### 詳細は元資料を参照
docs/reference/customer_docs/【健診】：筑波記念病院.md
