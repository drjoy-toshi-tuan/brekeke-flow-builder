# --- 発話指定_メインフロー ---
冒頭.prompt={tts_g:お電話ありがとうございます。東京衛生アドベンチスト病院の、予約専用、AI電話です。プーという音が鳴ってからお話しください。}
確認_紹介状有無.prompt={tts_g:出産申し込み以外の紹介状はお持ちですか？「はい、持っています。」または、「いいえ、持っていません。」でお答えください。}
確認_診察券番号.prompt={tts_g:診察券またはID番号をおっしゃってください。}
復唱_診察券番号.prompt={tts_g:番号は、#data# でよろしいでしょうか。「はい、そうです。」または、「いいえ、違います。」でお答えください。}
復唱否定_診察券番号.prompt={tts_g:大変失礼いたしました。再度、診察券またはID番号をおっしゃってください。}
転送_地域連携室.prompt={tts_g:地域連携室へお繋ぎいたします。このあと話し中の音が流れた場合は、電話が混み合っている状態です。恐れ入りますが、時間をおいておかけ直しください。それでは地域連携室へお繋ぎいたします。そのままお待ちください。}
終話_かけ直し案内.prompt={tts_g:申し訳ございませんが、ただいまの時間は受付時間外となっております。受付時間は8時30分からとなります。恐れ入りますが、受付時間内におかけ直しください。お電話ありがとうございました。 それでは失礼いたします。}
確認_当日予約判断.prompt={tts_g:受診希望日は本日ですか？「はい、そうです。」または、「いいえ、違います。」でお答えください。}
転送_成功.prompt={tts_g:}
終話_転送失敗.prompt={tts_g:}
確認_診療科.prompt={tts_g:診療科をおっしゃってください。}
確認_予約日.prompt={tts_g:現在の予約日を「なながつついたち」のように日付でおっしゃってください。}
復唱_予約日.prompt={tts_g:#data# でよろしいでしょうか。「はい、そうです。」または、「いいえ、違います。」でお答えください。}
復唱否定_予約日.prompt={tts_g:大変失礼いたしました。再度、現在の予約日を「なながつついたち」のように日付でおっしゃってください。}
終話_デンタルクリニック.prompt={tts_g:申し訳ございません。デンタルクリニックは、AI電話では承ることができません。恐れ入りますが、専用番号にお掛け直し下さい。番号は03-3392-8281 です。繰り返します。番号は03-3392-8281 です。お電話ありがとうございました。それでは失礼いたします。}
終話_健診センター.prompt={tts_g:申し訳ございません。健診センターは、AI電話では承ることができません。恐れ入りますが、専用ナビダイヤルにお掛け直し下さい。番号は、0570-02-8079 です。繰り返します。番号は、0570-02-8079 です。お電話ありがとうございました。それでは失礼いたします。}
終話_緩和ケア.prompt={tts_g:申し訳ございません。緩和ケア内科は、AI電話では承ることができません。恐れ入りますが、代表番号にお掛け直し下さい。番号は03-3392-6151 です。繰り返します。番号は03-3392-6151です。お電話ありがとうございました。それでは失礼いたします。}
終話_②アナウンス.prompt={tts_g:当日受付は終了しました。お電話ありがとうございました。それでは失礼いたします。}
終話_①アナウンス.prompt={tts_g:3診療日以内の、担当者からの折り返し電話にて確定となります。また、終話後にSMSを送信いたしますのでご確認ください。お電話ありがとうございました。 それでは失礼いたします。}
終話_③アナウンス.prompt={tts_g:予約キャンセルの申し込みを受付いたしました。確認事項があれば折り返しいたします。お電話ありがとうございました。それでは失礼いたします。}

# amivoice
amivoice.uri=ws://10.0.20.11:8000/ws
amivoice.language=ja
amivoice.engine=入力汎用
amivoice.keep_filter_token=true
amivoice.silent_detection_ms=2000
amivoice.timeout_ms=30000
amivoice.probability=0.6
amivoice.detection_flag=検出しない
amivoice.save_log=false

# Save2DB
office_id=5b8a5384d2122d061d527909

# デモ用設定テンプレ
pbx.db.name=save.db
context.settings.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/pbx/context-model
acceptance_times.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/incoming-call-by-brekeke
rag_ssml.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/rag-ssml/process-text
openAI_generate.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/openai/generate-text

#RAG
speech.rag.url=http://10.0.20.11:8000/api/v1/rag
speech.rag.connect_timeout=2
speech.rag.request_timeout=3
speech.rag.credibility=0