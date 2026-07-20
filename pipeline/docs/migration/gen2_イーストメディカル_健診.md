<!--
施設名: イーストメディカルクリニック
シナリオ名: 健診
環境: 本番
元資料: docs/reference/customer_docs/【健診1】：イーストメディカル.md
移管日: 2026-04-27
移管者: 浜口
備考: Gen2→Gen3 移管・再起草。元資料末尾の yaml セクション（flow:）が確定版フロー、それ以前の本番＿プロンプト/デモプロンプトは旧版。確定版 yaml を主、本番プロンプトを補助として読むこと。
-->

### 移管方針
- 用件分岐は **4 分岐**（予約 / 変更 / キャンセル / 問い合わせ）。「その他」「確認」は問い合わせへ寄せる catch-all。
- **Pattern A**（incoming-classifier 直後で OpenAI 用件分類 → ContextMatchRouter で 4 分岐）。echo_back は連絡先電話番号のみで複数 context 組み合わせ不要。
- サブフロー: PatientName（受診者名）/ DateOfBirth（生年月日）/ PhoneNumber（連絡先電話番号）の 3 本。診察券番号サブフローは **使わない**（function スキーマには medicalCardNumber があるが、シナリオでは聴取しない）。
- Date of Call Classifier: **不要**。営業時間外分岐の指定なし、reservationDate / Desired_consultation の前段に addCurrentDate（scaffold 自動付与）で十分。

### 施設固有の特殊ルール
- **連絡先電話番号は incoming_phone_type による 3 分岐**（MOBILE / FIXED / OTHER）。MOBILE は番号を読み上げて Yes/No 確認（echo_back あり）、FIXED は携帯番号を別途聴取、OTHER は SMS 受信可能な番号を聴取。**この分岐は ContextMatchRouter で実現**（Brekeke のシステム変数 `incoming_phone_type` を判定）。
- **電話番号 3 回聴取失敗時の二段階フォールバック**: anonymous なら `END_聴取失敗_匿名`（status=2）、非匿名なら「お電話いただいた番号で登録いたします」アナウンス → 用件確認へ合流。
- **echo_back 対象は連絡先電話番号のみ**。受診者名・生年月日・受診希望コース・問い合わせ内容・追加の質問は **復唱絶対禁止**（プロンプトで強い指示あり）。
- **救済語が多い**: 「検針/返品/返信/天候診断/返金控寸断」→ 健診、「人間ロック/ドック/ロック/人間独」→ 人間ドック、「薬/お薬」→ 予約、「取り直し/別の/変えたい」→ 変更、「やめる/取り消し」→ キャンセル。OpenAI 用件分類プロンプトに必ず救済語を列挙する。
- **受診希望コースリストは 30 件弱**（director は元資料【3】を参照して列挙、scaffold は free text で `course` に保存、復唱なし）。リスト外は「折り返しのお電話にて詳しくお伺いします」を発話して進む。
- **複数名予約 catch-all**: 元資料 1-15 に「企業/団体予約は HP からのみ」分岐あり（status=2 で終話）が、最新 yaml では未実装 → **director 判断**で取り込むか割愛するか決める。割愛推奨。
- **endpoint / Health_insurance_subsidy / DesiredreservationDate** は本番 function スキーマに存在しない（デモ版のみ）。**本番 function を採用**（17 フィールド）。`smsFlag` は 0/1/2、終話箱の更新値で付与。
- **「もしもし」のみ発話 → 同一質問再提示**は再質問ルール 6 で吸収可能（director 判断で個別ハンドリング不要）。

### director が見落としやすいポイント
- 元資料には旧版プロンプトが 4 ブロック繰り返されている（本番 / 本番＿20260206 / デモ最新＿20260203 / デモ＿20260203）。**最新確定版は末尾の `# yaml` セクション**。プロンプトは smsFlag/status 制御や救済語等の補足としてのみ参照する。
- 終話箱は 4 種類: `END_予約等`（status=1, smsFlag=1）/ `END_キャンセル`（status=1, smsFlag=2）/ `END_聴取失敗_匿名`（status=2）/ `END_聴取失敗`（status=2）。**status=2 が二系統ある**ことに注意。
- 終話文言は予約/変更/問い合わせ共通（「担当者より…048-799-2211…」）で 1 種、キャンセル専用（「ご予約のキャンセルを承りました…」）で 1 種、計 2 種。
- `<break time="10000ms"/>` は **SSML 禁止ルール違反**。Gen3 では削除し、必要なら無音区間は IVR 側で対応する旨をプロンプトに残さない。
- 生年月日リトライ上限は **2 回**（他項目は 3 回）→ 3 回失敗時に `patientDateOfBirth` をブランクで進む特殊仕様。サブフローのリトライ設定で対応。
- `additionalPhoneNumber` は **連絡先電話番号聴取まで絶対セットしない**（途中切断時もブランク維持）。本番 function 説明にも明記あり、prompter は OpenAI プロンプトで強く指示。

### 詳細は元資料を参照
docs/reference/customer_docs/【健診1】：イーストメディカル.md
