<!--
施設名: 順天堂東京江東高齢者医療センター
シナリオ名: 診療
環境: 本番（デモ・本番適用中、稼働中）
元資料: docs/reference/customer_docs/【診療1】：順天堂東京江東高齢者医療センター.md
移管日: 2026-05-20
移管者: 浜口
備考: Gen2 元資料は 2026/03/19 17:18 更新版（冒頭アナウンス修正）。SSML 多用・status/smsFlag が 6 値 × 6 値の特殊配列なので注意。
-->

### 移管方針
- 冒頭は **Pattern A**（phone_type 判定で OTHER→非通知拒否終話 / MOBILE/FIXED→通常冒頭）。phone_type は Brekeke 側の判定（Gen2 yaml の「phone_type判定」箱）を踏襲、incoming-category-classifier ではなく **incoming-classifier の MOBILE/FIXED/OTHER 3 分岐 + catch-all `^*$`** を使う。
- 続柄→個人情報（氏名/生年月日/連絡先電話番号）→用件、の **順番固定** が要件。氏名・生年月日・連絡先電話番号は **PatientName / DateOfBirth / Phone のサブフロー 1 枠ずつ** で構成（インライン展開禁止）。
- 連絡先電話番号は phone_type で分岐する点が独特：**MOBILE は incoming_phone_number 確認型（Yes→incoming を代入 / No→再聴取→復唱）**、**FIXED は普通に聴取→復唱**。Phone サブフロー側で phone_type を参照する分岐が必要なので **director 判断**で（既存 Phone サブフローに条件分岐が無ければ拡張、または 2 つに分離）。
- 用件分岐は **Pattern A**（用件直後の OpenAI で 4 分類 → ContextMatchRouter）。診療予約だけは更に「診察/ワクチン確認」で再分岐するため **2 段 OpenAI + 2 段 CMR** 構成。
- 受診歴・紹介状有無・健診結果有無・選定療養費は全て Yes/No 二値 → **scaffold の Yes/No 固定プロンプト**で OK。「わからない」を許容する箱（受診歴・診察券番号・診療科・医療機関名）は 3 値で **director がプロンプト指定**。
- Date of Call Classifier は **不要**（年末年始・営業時間外の特例案内が customer_doc に無い）。
- FAQ 確認ルールあり（§10）→ **RAG サブフロー要否は director 判断**。順天堂 FAQ/RAG 設計課題（memory: project_juntendo_faq_rag）に依存。当面は FAQ サブフロー無しでテンプレ完走、人間レビューで RAG を後付け検討する想定。
- 復唱は **予約日／生年月日／連絡先電話番号** の 3 項目のみ scaffold の echo_back=true を立てる。他は全部 echo_back=false（patientName / clinicalDepartment / medicalCardNumber 等で復唱フラグを立てないこと）。

### 施設固有の特殊ルール
- **status 値割り当て**（6 値）:
  - `0`=デフォルト保持 / `1`=各終話アナウンス出力後 / `7`=非通知拒否の冒頭アナウンス / `8`=かけ直し案内（医療機関名不明） / `9`=選定療養費不承による受付不可案内
- **smsFlag 値割り当て**（6 値）:
  - `0`=デフォルト保持 / `1`=終話（診察予約／受診歴無し or 有り） / `2`=終話（ワクチン予約） / `3`=終話（予約変更） / `4`=終話（キャンセル） / `5`=終話（予約日時確認）
- **選定療養費**は健診結果有無で経路が違う:
  - 紹介状無し → 健診結果「有り」→ 選定療養費案内（案内のみ、回答待たず即診療科へ）
  - 紹介状無し → 健診結果「無し」→ 選定療養費聴取（肯定/否定）→ 否定なら status=9 で終話、selectedExpenses="不承" 同時格納
- **紹介状有り** → 医療機関名聴取 →「わからない」回答で status=8 終話（かけ直し案内）。
- **classification は二段確定**：用件で「診療予約」と確定後、診察/ワクチン確認で「診察予約」or「ワクチン予約」に上書き。CMR 構成上 classification の値遷移を director が設計書 step_details に明記する必要あり。
- **classification 別の聴取項目厳守**（customer_doc 内に「他項目聴取絶対禁止」と複数回明記）:
  - ワクチン予約=3 項目（診察券番号/ワクチン種類/都合が悪い日）
  - 予約変更=7 項目（残薬確認まで）
  - キャンセル=5 項目（**都合が悪い日は聴取禁止**、診療科→複数診療科→現在の予約日→理由）
  - 予約日時確認=2 項目（診察券番号/診療科のみ）
- **個人情報聴取中の用件先取り防御**: 続柄・氏名・生年月日・連絡先電話番号の聴取中に「予約取りたい」等が入力されても classification にデータ格納禁止 → 再聴取扱い。**OpenAI 側のプロンプトに「用件キーワードでも再聴取」明記が必要**（director→prompter 受け渡し）。
- **「都合が悪い日」は診察予約・ワクチン予約・予約変更でのみ聴取**、キャンセル・予約日時確認では絶対聴取しない。
- **「わからない」格納値の正規化**: medicalCardNumber="わからない" / clinicalDepartment="登録なし"（聴取失敗時も「登録なし」）/ institution="わからない" / doctorOrclinic="希望無し"。**director は no_result/聴取失敗時の格納値を step_details に明示**。
- **STT 救済キーワード**（customer_doc §3 判断ルール抜粋、追加辞書要件）:
  - 「変更保険」→「健康保険」、「いろんな種」→「利用なし」、「PHがいます」→「いいえ違います」、「PD」→「いいえ」、「ルパン人」→「本人」（続柄聴取時のみ）、「DM/ディーエム」→「いいえ」、「社長は/修正/先生」→「昭和/平成/平成」（生年月日聴取時のみ）等。STT 辞書テンプレ（hearing_datetime / echo_back_yesno 等）の **additional_words** に投入要。

### director が見落としやすいポイント
- **冒頭アナウンス改訂**: 「1983行目（3/19）依頼対応：冒頭アナウンス修正」と明記あり。**通常の冒頭アナウンスの文言は customer_doc §3-1（840 行付近）と §4 共通固定発話を厳密一致**で取得すること。「お電話ありがとうございます。順天堂東京江東高齢者医療センターの外来予約専用AI電話です。当日緊急受診をご希望の場合は代表電話へおかけ直しください。これから流れる質問に沿ってご回答ください。」
- **SSML 多用注意**: 元資料は `<speak type="telephone" breakc="200ms">`・`<dtmf digit="1"/>` を「変更不可コード」と強調して大量使用。**Gen3 では SSML 全面禁止。TTS は `{tts_g:...}` 小文字、動的値は `<% var %>` のみ**。`<speak>` 内の電話番号読み上げは「`<% incoming_phone_number %>`」のような Brekeke 変数参照に置換。`<dtmf digit="1"/>` の DTMF 効果は IVR モジュール側で実現（プロパティで定義）。
- **連絡先電話番号 MOBILE 経路の Yes/No 分岐**: 「今おかけいただいている `<% incoming_phone_number %>` でよろしいですか？」→ Yes で additionalPhoneNumber に incoming を代入、No で別番号聴取 → 復唱。**Yes/No の判定箱 + 否定後の再聴取 + 復唱 の 3 段構成**。Phone2Name とは別物（番号確認用）。
- **「診察予約／受診歴無し」と「診察予約／受診歴有り」で終話アナウンスが別文言**: 再診側だけ「半年以上空いたら初診扱い／選定療養費が発生する可能性」の長文を読み上げる。**termination_patterns で 2 パターン定義**して Medical_history で分岐（Gen2 yaml にも「診察予約_終話判定」箱として明示あり）。
- **「複数診療科」は用件ごとに別コンテキストではなく同一 `clinicalDepartment2`** に格納（診療予約・予約変更・キャンセルで共通）。文言は用件ごとに違うので saveContextModel2DB / hearing は別ブロックでも contextName は共通。
- **FAQ 確認 §10** は customer_doc に挙動定義があるだけで FAQ 内容が無い → **RAG サブフロー組み込みは BLOCKER ではなく TODO**。director が「RAG 用ナレッジ未提供のため当面 FAQ サブフロー無しで作成」と確認レポートに明記推奨。
- **identityConfirm はフリーワード格納**（「姉です」をそのまま格納。「姉」だけに省略禁止）→ hearing の output_format は **text**、復唱・再確認は禁止。
- **「不要な発話」の禁止リスト**（customer_doc §1-1）: 「かしこまりました／承知いたしました／承りました／受け取りました」「ありがとうございます／お気軽に」は冒頭・終話・代表案内以外で使用禁止。**prompter にハードルールとして注入**（gen_properties のテンプレ TTS を生成時に検査）。

### 詳細は元資料を参照
- 元資料: `docs/reference/customer_docs/【診療1】：順天堂東京江東高齢者医療センター.md`
- 重点参照行: §3-1 通話フロー全体像 (834〜918行) / §3-2〜3-6 用件別聴取項目順 (921〜1007行) / §4 固定発話 (1011〜1209行) / function スキーマ (1213〜1472行) / yaml フロー定義 (1474〜1948行)
