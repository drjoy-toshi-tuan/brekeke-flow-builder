<!--
施設名: 大星クリニック健診センター
シナリオ名: 健診
環境: 本番
元資料: docs/reference/customer_docs/【健診1】：大星クリニック.md
移管日: 2026-04-22
移管者: claude (migrate-gen2 skill)
備考: director 軽量ノート運用（2026-04-20 版を作り直し、group_name は健診センター込み）
-->

### director 向け明示指示（施設命名の override）

- **施設名（facility_name）= "大星クリニック健診センター"**（"大星クリニック" だけではない）
- **group_name = "大星クリニック健診センター"**
- **flow_name = "大星クリニック健診センター$健診_YYYYMMDD"**
- 同施設の別シナリオ（_診療）は "大星クリニック" のみを group_name に使うが、本健診シナリオは Brekeke IVR 側の運用上 "健診センター" 付きで登録する
- 冒頭アナウンス・代表電話案内等の TTS 文言内の「施設名」は原文通り「大星クリニック」のまま（customer_doc §2 に "はい、大星クリニックです。健康診断、人間ドックの予約専用AIオペレーターが〜" とある原文を使用）。group_name 側だけ健診センター付き、という分離に注意

### 移管方針
- 冒頭は opening + 冒頭_アナウンス の2ブロック1セット。冒頭アナウンス直後は入力待ち無しで、先に **非通知判定（incoming_phone_number = anonymous → END_非通知案内 / checkpoint=7）** を置いてから氏名聴取へ進む。Pattern 5 ではなく通常 Pattern で充分（WebRTC分岐は不要）。
- **聴取順序は customer_doc §5 共通ヒアリング**に従い、用件分類より**先に** 氏名 → 生年月日 を取る。生年月日は**復唱あり**（「{}ですね。」）。患者名・その他は復唱禁止（customer_doc 冒頭 "聴取内容の再質問・復唱禁止"）。
- 氏名／生年月日／診察券番号 は **サブフロー経由**（Jump to Flow）。氏名サブフロー＝PatientName サブフロー 1 枠、生年月日サブフロー＝DOB サブフロー（復唱込み）。
- 用件分類 classification は 4択（申し込み / 変更 / キャンセル / その他）で **Pattern A（OpenAI直後分岐）**。用件確認_再質問（1回）も含む。
- **申し込みルートは胃カメラ有無で内部分岐が発生**：
  - 胃カメラ有：胃カメラ方法 → 予約希望日 → コース → 会社名
  - 胃カメラ無：コース → 予約希望日 → 会社名
  両ルートとも会社名で合流し「終話判定」に接続。
- 連絡先電話番号は **口頭ヒアリングしない**（customer_doc 1-4-2 明記）。incoming_phone_number のみ使用。additionalPhoneNumber への口頭格納ブロックは作らない。終話文言分岐は incoming_phone_number の先頭3桁で判定（ContextMatchRouter Pattern B）。
- 終話パターンは **携帯（090/080/070）=SMS案内文 / 固定（10桁 or 050始まり11桁 / 非通知 / 携帯未取得）=折り返し文** の2系統。その他用件・変更・キャンセル・申し込み いずれも同じ2系統で終話（申し込みのみ SMS 有、他は固定文言流用）。
- RAG/FAQ は元資料に本体ナレッジ無し → 不要。その他用件は [その他_内容確認] で confirmation に自由文格納して終話へ。
- TTS は全て `{tts_g:...}` 小文字。`<speak type="telephone">` `<dtmf digit="8" />` `<dtmf />` タグは**生年月日ブロック・電話番号復唱（もし追加発話があった場合）・代表案内**等のプロパティにそのまま保持（SSML 禁止ルールの例外として元資料どおり残す。director 判断）。

### 施設固有の特殊ルール
- **復唱は生年月日のみ**：氏名・診察券番号・コース・オプション・予約希望日・会社名・用件 すべて echo_back 禁止（scaffold デフォルト False 維持、明示 False 指定）。customer_doc 冒頭【補足】に「生年月日以外は一切復唱・確認をしてはいけません」と厳命。
- **非通知は即終話**（incoming_phone_number=anonymous/空/0桁）。checkpoint=7 を設定。冒頭アナウンス直後に非通知判定ブロックを置く。status はこの場合 0（申し込み条件未達）。
- **連絡先電話番号は口頭聴取禁止**（1-4-2）。additionalPhoneNumber hearing ブロックは作らない。status / smsFlag 判定は「additionalPhoneNumber が空である前提で incoming_phone_number を使う」。
- **status ルール**（function description 準拠）：
  - 代表電話案内で終話した場合 → status=2
  - classification ∈ {申し込み, 変更, キャンセル} かつ patientName 非空 かつ patientDateOfBirth 非空 → status=1
  - それ以外（その他 / 聴取不能） → status=0
- **smsFlag ルール**：additionalPhoneNumber が 090/080/070/060 で始まり（※customer_doc 表記どおり 060 含む）、patientName / patientDateOfBirth が非空の場合に classification で分岐。**本シナリオでは additionalPhoneNumber を聴取しないため、実質 incoming_phone_number が携帯のときに格納先を additionalPhoneNumber に自動コピーするか、director 判断で incoming_phone_number をそのまま smsFlag 判定対象にするかの整理が必要**（Gen3 では additionalPhoneNumber スロットを incoming_phone_number からコピーする script ブロックを挟むのが素直 = director 判断）。
- **会社名＝companyName は「企業申込ならお勤め先、個人なら『その他』発話」**。空文字 or "その他" 格納で個人扱い。**organizationName ではなく companyName** を function に合わせて使用（受診者氏名とは別項目、hearing ブロックで単独取得。PatientName サブフローには流さない）。
- **受診歴 medical_history と 胃カメラ gastroscopy は enum=有/無**。「はい/あります」→ 有、「いいえ/ありません」→ 無 の正規化を prompt に明記。
- **「検診」→「健診」扱い**（customer_doc §5 キーワード判定）。ただし customer_doc 原文では「乳がん／子宮がん／子宮頸がん」前置時に除外…としつつ「以下の単語は『健診』と判断します：『検診』」と二重記載（矛盾）がある。本施設は健診専用のため **単純に検診→健診扱いに寄せる**（director 判断）。
- **「人間ドック」類義語**：「人間ロック」「ドック」「ロック」「人間独」→ 人間ドック。course 正規化プロンプトに反映。
- **「予約」類義語**：「薬」「お薬」→ 予約（AmiVoice 誤認救済）。
- **「変更」類義語**：「取り直したい」「別の」「変えたい」「変えて」「変える」。
- **「キャンセル」類義語**：「やめる」「取り消し」「取り消す」「取消」「やめたい」。
- **相対日付換算**（1-4）：今日／明日／明後日は着信日時から自動換算。過去日付は未来日付であることを確認し、未来のみ受付。
- **予約希望日 Preferred_date は output_format: text**（フリーワードそのまま）。明確な日付発話時のみ yyyy-MM-dd に正規化。
- **reservationDate（現在の予約日）は output_format: datetime**（yyyy-MM-dd 00:00:00）。年指定なし時は当年、10月以降に1-9月発話なら翌年。
- **生年月日は DTMF `<dtmf digit="8" />` 併用聴取**（顧客側で既に明記）。DOB サブフロー側で DTMF 受付設定を入れる。
- **数字キーワード救済**（1-7, 1-9）：C/Sea→4、Go/ご→5 他。診察券番号サブフロー・電話番号関連の prompt に反映（prompter 担当）。
- **複数名発話時の格納ルール**：最初の1名のみ patientName / patientDateOfBirth へ。2人目以降はカタカナ氏名＋yyyy-MM-dd で reason に改行区切り格納。2人目以降の氏名は **PatientName サブフローに再充当しない**（reason テキスト扱い）。
- **FAQ外質問は代表電話案内**（1-2）：「うまく聞き取りができませんでした。再度ご用件をお話しください」を1回挟んで2回目以降に代表電話 03-6426-5933 案内＋終話。status=2 / endpoint=電話案内。
- **聴取不能終話**（1-5）：無回答2回リトライ→3回目到達で「再度おかけなおしください」で終話。status=0 / endpoint=途中切断。
- **タグ保持**：`<dtmf />` `<speak>` `<forward>` は削除禁止（1-8）。

### director が見落としやすいポイント
- **改訂履歴（2025/12/25）**：「用件分岐追加。function変更用件項目追加。」→ classification 4択化、medical_history / gastroscopy / method / companyName / change_item / smsFlag の function 追加が最新仕様。過去版の 3択（予約/変更/その他）構造を引きずらないこと。
- **胃カメラ有無で質問順が切り替わる**：customer_doc §5【胃カメラ＝有】と【胃カメラ＝無】で順序が異なる。「途中で別の項目に飛んではいけない」と厳命あり。scenario_flow のブロック配置で順序を厳守（cmr で内部分岐後、各ルート直列に4/3ブロック並べる）。
- **会社名 companyName は受診者氏名扱いしない**：PatientName サブフローに流さず、hearing ブロック単独で取得する。**会社/事業所からの問い合わせ**はあるが、患者氏名（受診者氏名）とは別項目。memory: feedback_patientname_subflow_allocation に従い、会社名は organizationName 相当の hearing ブロックへ。
- **受診者氏名 = 患者氏名 = PatientName サブフロー 1 枠**：入電者が担当者／企業窓口でも、customer_doc のヒアリング項目は「受診者名」のみなので **PatientName サブフローは 1 枠**。担当者名は別途聴取しない（customer_doc に担当者名取得の明記なし）。
- **受診希望コース course / 追加オプション option は enum なしの自由文**：customer_doc §3,§4 にリスト本体が空で記載。director は列挙全件転記せず「コース名／オプション名は元資料に準ずる」で扱う。一致時のみ正式名称格納、不一致時は発話文言そのまま course へ（§1-3）。**option は function 定義上必須だが、customer_doc ヒアリング順序に option 専用質問がない**（胃カメラ有無と method でオプション相当を吸収）→ option は空文字格納で問題なし（director 判断）。
- **endpoint enum 6値**（冒頭切断／時間外／電話転送／電話案内／途中切断／通話完了）：本シナリオ上「時間外」「電話転送」に到達する分岐は無い（24時間AI応答・転送なし）。termination_patterns では到達可能な 4 値（冒頭切断／電話案内／途中切断／通話完了）のみ使用（director 判断で enum から除外しても良い）。
- **change_item は function にあるがヒアリング指示なし**：customer_doc §5 変更ルートは「予約日 → 変更希望日」のみで change_item 聴取ブロックがない。**change_item は空文字格納でよい**（director 判断、もし必要なら変更希望日の直前に「何を変更されますか？」ブロックを追加するか検討）。
- **用件確認_再質問の分岐**：customer_doc yaml では「申込み」含有のみ救済、その他は END_代表電話案内 に直行。変更・キャンセル・その他の再聴取救済が無い点に注意（director 判断で再救済を対称に広げるか、原文忠実にするか選択）。**原文忠実推奨**。
- **チェックポイント 7（非通知）のみ明示**：他の終話パターンで checkpoint を明示する記載は customer_doc に無い。status で管理。
- **「自動的に追加される繋ぎ言葉」許容**（§5）：「5月の20日」→「5月20日」。予約希望日・変更希望日の日付抽出プロンプトに明記。
- **AI内部思考の発話禁止**：「スキップします」「確認は不要です」等の発話禁止（業界共通ルール、prompter 制約に入れる）。

### 詳細は元資料を参照
docs/reference/customer_docs/【健診1】：大星クリニック.md
