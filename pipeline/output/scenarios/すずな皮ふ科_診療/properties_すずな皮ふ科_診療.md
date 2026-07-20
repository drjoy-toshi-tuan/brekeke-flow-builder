# IVR Properties — すずな皮ふ科クリニック 診療（Pattern 2 / 疑義照会ルート追加版）
# date: 2026-05-12
# env: demo
# coverage: main flow 35 TTS + subflow 5 TTS + Phone2Name 動的差込 + インフラ設定
# source:
#   - docs/reference/customer_docs/すずなproperty.txt（稼働中のベース）
#   - docs/reference/customer_docs/すずな皮ふ科_疑義照会_raw.md（疑義照会ルート TTS）
#   - 現行 main JSON モジュール一覧と全件突合済

# =====================================================
# 1. アナウンス（冒頭・非通知）
# =====================================================
冒頭アナウンス.prompt={tts_g:お電話ありがとうございます。すずな皮ふ科クリニック、AI電話です。}
終話_非通知アナウンス.prompt={tts_g:お手数をおかけしますが、発信者番号を通知して再度お電話ください。電話番号の前に「186」を追加いただくことで、発信者番号を通知していただくことができます。お電話ありがとうございました。}

# =====================================================
# 2. 用件 hearing（Pattern 2 で 4→5 拡張：CS 設計書 P.2 アナウンス一覧1 由来）
# =====================================================
# 注: CS 設計書では「5番.疑義紹介」と記載（疑義照会の typo の可能性）。verbatim に従う
用件.prompt={tts_g: ご用件を次の5つのうちのいずれかでお話しください。1番.お問い合わせ、2番.予約、3番.予約変更、4番.予約キャンセル、5番.疑義紹介。プッシュボタンでも操作できます。}

# =====================================================
# 3. 予約フロー
# =====================================================
予約_受診歴.prompt={tts_g: 当院でのご受診は、初めてですか？それとも2回目以降ですか？「初めてです」または「2回目以降です」とお話しください。}
予約_診療科.prompt={tts_g: 一般皮膚科。か、美容皮膚科。か、をお話しください。}
予約_希望日.prompt={tts_g: ご希望される日時を「4月1日の11時」や「月曜日の15時半」などのようにお話しください。複数ある場合はすべてお知らせください。脇ボトックスのご予約は、本日より一週間後以降の日時で承っております。}
確認_手術内容.prompt={tts_g: 半年以内に診察を受け、同意書をご提出済みの、できものの手術の予約、または当院で保険脇ボトックス注射の登録がお済みの方のご予約、または同意書をご提出済みの水いぼワイキャンス治療のご予約でしょうか。}

# =====================================================
# 4. 変更・キャンセルフロー
# =====================================================
変更_診療科.prompt={tts_g: 一般皮膚科。か、美容皮膚科。か、をお話しください。}
変更_予約内容.prompt={tts_g: ご予約の内容をお話しください。}
変更_予約日.prompt={tts_g: 現在の予約日を「4月1日」のように日付でお話しください。わからない場合は「わからない」とお話しください。}

# =====================================================
# 5. 患者情報聴取（main + subflow 共通モジュール）
# =====================================================
患者_氏名.prompt={tts_g: お名前を「名前は山田太郎です」のように、フルネームでお話しください。}
患者_生年月日.prompt={tts_g: 生年月日を西暦、もしくは和暦からお話しください。}
患者_連絡先.prompt={tts_g: ご連絡先のお電話番号をお伺いします。0から始まる市外局番を含む電話番号、または携帯電話番号をお話しください。プッシュボタンでも入力いただけます。}
患者_診察券番号.prompt={tts_g: 診察券番号を、5桁以内でお話しください。わからない場合は、わからない、とお話しください。}

# =====================================================
# 6. お問い合わせフロー
# =====================================================
相談_問合せ.prompt={tts_g: お問合せ内容を簡潔にお話しください。}
相談_問合せループ.prompt={tts_g: 他にご用件があればお話しください。ない場合は、「ありません」とお話しください。}
相談_FAQ失敗.prompt={tts_g:申し訳ございません。ご質問いただきました内容は、AI電話では対応できません。後日、担当者より確認のうえご連絡いたします。}

# =====================================================
# 7. 終話アナウンス（既存）
# =====================================================
終話_予約.prompt={tts_g: ご要望を承りました。このお電話ではまだ確定しておりません。近日中に、担当者からショートメール、またはお電話にてご連絡いたします。お電話ありがとうございました。}
終話_変更.prompt={tts_g: ご要望を承りました。このお電話ではまだ確定しておりません。近日中に、担当者からショートメール、またはお電話にてご連絡いたします。お電話ありがとうございました。}
終話_キャンセル.prompt={tts_g: 予約キャンセルについてのご要望を承りました。担当者より折り返しご連絡をさせていただく場合がございます。お電話ありがとうございました。}
終話_お問い合わせ.prompt={tts_g: ご用件を承りました。近日中に、担当者からショートメール、またはお電話にてご連絡いたします。お電話ありがとうございました。}
終話_FAQ失敗.prompt={tts_g:申し訳ございません。ご質問いただきました内容は、AI電話では対応できません。後日、担当者より確認のうえご連絡いたします。}
終話_初診アナウンス.prompt={tts_g: このお電話では、ご予約はお取りできません。携帯電話の方にはSMSにてLINEの当日順番予約のご案内をお送りいたします。その他の方は、ホームページを参照の上、当日順番予約をご利用ください。お電話ありがとうございました。}
終話_一般皮膚科.prompt={tts_g: 一般皮膚科の診察は、事前予約を承っておりません。ラインの当日順番予約をご利用されるか、または直接ご来院ください。お電話ありがとうございました。}
終話_最後の質問.prompt={tts_g: 他にご用件があればお話しください。ない場合は、「ありません」とお話しください。}
終話_最後の質問ループ.prompt={tts_g: 他にご用件があればお話しください。ない場合は、「ありません」とお話しください。}
終話_切断アナウンス1.prompt={tts_g: ご回答の確認ができませんでしたのでこちらからお電話失礼させていただきます。}
終話_切断アナウンス2.prompt={tts_g: ご回答の確認ができませんでしたのでこちらからお電話失礼させていただきます。}
終話_切断アナウンス3.prompt={tts_g: ご回答の確認ができませんでしたのでこちらからお電話失礼させていただきます。}
終話_失敗.prompt={tts_g:ご回答の確認ができませんでしたので、こちらからお電話失礼させていただきます。}

# =====================================================
# 8. 疑義照会ルート（Pattern 2 新規追加、CS 設計書 P.8 アナウンス一覧2 由来）
# =====================================================
# verbatim from CS 設計書 markitdown 化 md（句読点を含めて忠実に再現）
薬局名.prompt={tts_g:薬局名をお話しください。}
担当者名.prompt={tts_g:今お電話いただいているご担当者名を、「担当は佐藤です」のようにお話しください。}
患者名.prompt={tts_g:患者様のお名前を、「名前は山田太郎です」のようにフルネームでお話しください。}
患者生年月日.prompt={tts_g:患者様の生年月日を、「1990年4月1日」のようにお話しください。プッシュボタンでも操作できます。}
疑義内容.prompt={tts_g:疑義の内容をお話しください。}
END_疑義照会.prompt={tts_g:かしこまりました。お掛けいただいた番号に折り返しいたします。お電話ありがとうございました。}

# =====================================================
# 9. Phone2Name 動的差込テンプレ（CS 設計書「薬局名（電話番号登録済み）」由来）
# =====================================================
# CS 設計書: 「○○さんですね。」（○○ = 薬局名フリガナ、Brekeke では recipient_name に動的差込）
Phone2Name.FOUND_KATAKANA_NAME_DEFAULT_TMP={tts_g:<% recipient_name %>さんですね。}
Phone2Name.NOT_FOUND_KATAKANA_NAME_DEFAULT_TMP=

# =====================================================
# 10. Re-confirmation node data（電話番号復唱、#data# 差込）
# =====================================================
# 注: 旧 module 名「患者_携帯電話」は現 JSON では「患者_携帯」（Re-confirmation node data type）にリネーム済み
# 復唱_患者_連絡先 は SSML(<speak><say-as>) を含む（既存稼働中のため維持、本来 Gen3 では SSML 禁止だが Brekeke が無視する想定）
患者_携帯.prompt={tts_g:ご連絡先のお電話番号は、今おかけいただいている、<% sys-customer-phone-number %>、でよろしいですか。「はい、そうです」または「いいえ、ちがいます」とお話しください。}
復唱_患者_連絡先.prompt={tts_g:お電話番号は、<speak><say-as interpret-as="telephone">#data#</say-as></speak>でよろしいですか。「はい、そうです」または「いいえ、ちがいます」とお話しください。}

# =====================================================
# 11. インフラ設定（既存稼働中のまま、すずなproperty.txt から完全継承）
# =====================================================
# wait
冒頭.wait=2000

# 転送
転送.number=1038

# amivoice
amivoice.uri=ws://speech.internal.assistant.com:8000/ws
amivoice.language=ja
amivoice.engine=入力汎用
amivoice.keep_filter_token=true
amivoice.silent_detection_ms=1500
amivoice.timeout_ms=20000
amivoice.probability=0.7
amivoice.detection_flag=検出しない
amivoice.save_log=false

# Save2DB
office_id=5eecd40f2c9faeddaddc1dc9
pbx.db.name=save.db
context.settings.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/pbx/context-model

# 各種 API URL
rag_ssml.url= https://reserve.drjoy.jp/api/anonymous/dr/ha/rag-ssml/process-text
openAI_generate.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/openai/generate-text
acceptance_times.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/incoming-call-by-brekeke
drjoy.save.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/brekeke-booking-ai
get-intonation-from-drjoy.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/brekeke-replace-intonation
phone_2_name.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/phone-to-name

# =====================================================
# 12. incoming-category-classifier (電話帳分類) 設定 — demo 環境
# =====================================================
# env=demo: demo-reserve.famishare.jp、env=prod: reserve.drjoy.jp
# 仕様: docs/brekeke/モジュール詳細設定ガイド_1.md §6.2
incoming-category-classifier.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/phone-category-assignments
incoming-category-classifier.request_timeout=10
incoming-category-classifier.connect_timeout=10

# =====================================================
# 注意事項
# =====================================================
# - 全 35 TTS モジュール（main） + 5 TTS モジュール（subflow 個人情報すずな2）の **計 40 TTS モジュール** の prompt を網羅
# - 患者_氏名 / 患者_連絡先 は main / subflow で同名モジュール（同一 TTS）として 1 エントリで両方適用
# - リトライ_* モジュールはプロパティ対象外（既存 property.txt も含めていない）
# - 「電話帳分類」(incoming-category-classifier): URL は demo 環境向け。本番投入時は `incoming-category-classifier.url` を `https://reserve.drjoy.jp/api/anonymous/dr/ha/phone-category-assignments` に差し替え
# - 「電話帳分類」が参照する Dr.JOY 電話帳の薬局登録は **人間作業**（クオール薬局 / ミツヤ薬局 / ミネ薬局 / 日本調剤 の 4 件、リスト1 に割当推奨）
# - Phone2Name.NOT_FOUND_KATAKANA_NAME_DEFAULT_TMP は空文字（フォールバック先で改めて聴取する設計）
