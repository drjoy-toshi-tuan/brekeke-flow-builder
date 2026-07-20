# アナウンス
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。横浜労災病院の予約専用AI電話です。}
注意事項_アナウンス.prompt={tts_g:これより、AIの案内に沿ってお話しください。また、AIのアナウンスが完全に終了してからお話しください。お電話終了後、2診療日以内に担当者が電話またはSMSでご連絡いたします。}
診療健診.prompt={tts_g:本日のご用件は、診療、または健診、どちらに関するお問い合わせでしょうか。どうぞ。}
用件.prompt={tts_g:ご用件を次の中からお選びください。予約、予約変更、キャンセル、予約確認、お話しください。どうぞ。}
紹介状確認.prompt={tts_g:紹介状はお持ちでしょうか。「はい」または「いいえ」でお答えください。どうぞ。}
診療科_予約.prompt={tts_g:ご希望の診療科名をお話しください。わからない場合は、確認の上おかけ直しください。どうぞ。}
診療科_紹介なし.prompt={tts_g:ご希望の診療科名をお話しください。わからない場合は、確認の上おかけ直しください。どうぞ。}
選定療養費_説明.prompt={tts_g:紹介状をお持ちでない場合、選定療養費7,700円がかかります。あらかじめご了承ください。}
紹介元.prompt={tts_g:紹介元の医療機関名をお話しください。どうぞ。}
医師名.prompt={tts_g:紹介状に医師の指定がありましたらお話しください。ない場合は「ない」とお話しください。どうぞ。}
現在の予約日.prompt={tts_g:現在の予約日を「4月1日」のように日付でお話しください。どうぞ。}
当日確認.prompt={tts_g:変更希望は本日の予約でしょうか？「はい」または「いいえ」でお答えください。どうぞ。}
診療科_変更.prompt={tts_g:ご希望の診療科名をお話しください。わからない場合は、確認の上おかけ直しください。どうぞ。}
変更理由.prompt={tts_g:予約変更の理由を簡潔にお話しください。どうぞ。}
確認内容.prompt={tts_g:確認をしたい内容に関して、簡潔にお話しください。どうぞ。}
転送_健診.prompt={tts_g:健診に関するご予約に関しましては、担当窓口にお繋ぎいたしますので、そのままお待ちください。}
転送_当日変更.prompt={tts_g:当日の変更に関しましては、予約センターで受付いたします。お繋ぎいたしますので、そのままお待ちください。}
転送_リハビリ.prompt={tts_g:担当オペレーターにお繋ぎいたしますので、そのままお待ちください。}
END_終話1.prompt={tts_g:ご希望の診療科につきましては、ご紹介の病院から直接、横浜労災病院へお問い合わせいただくようお伝えください。お電話ありがとうございました。それでは失礼いたします。}
END_終話2.prompt={tts_g:恐れ入りますが、ご希望された診療科は、新規予約を受け付けておりません。他の医療機関での受診をお願いいたします。お電話ありがとうございました。それでは失礼いたします。}
END_終話3.prompt={tts_g:大変申し訳ございません。紹介状をお持ちでない場合は受付することができません。紹介状をお持ちの上、改めておかけ直しください。それでは失礼いたします。}
END_終話4_SMS.prompt={tts_g:お電話内容を確認いたしました。2診療日以内に担当者から折り返し電話、もしくはショートメールにてご連絡いたします。それでは失礼いたします。}
END_終話4_noSMS.prompt={tts_g:お電話内容を確認いたしました。2診療日以内に担当者から折り返し電話、もしくはショートメールにてご連絡いたします。それでは失礼いたします。}
END_上限エラー.prompt={tts_g:恐れ入ります。ご回答がうまく認識できませんでした。AIからの質問にご回答いただいていた場合は、お手数ですが再度お話しください。別途ご質問がある場合は、当院の代表電話へお掛け直しください。}
時間外_アナウンス.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
非通知_アナウンス.prompt={tts_g:お手数をおかけしますが、発信者番号を通知して再度お電話ください。電話番号の前に「186」を追加いただくことで発信者番号を通知していただくことができます。それでは失礼いたします。}

# amivoice
amivoice.uri=ws://10.0.20.11:8000/ws
amivoice.language=ja
amivoice.engine=入力汎用
amivoice.keep_filter_token=true
amivoice.silent_detection_ms=2000
amivoice.timeout_ms=30000
amivoice.probability=0.7
amivoice.detection_flag=音声開始前から検出
amivoice.save_log=false

# Save2DB / PBX
office_id=TODO_要確認
pbx.db.name=save.db
context.settings.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/pbx/context-model
acceptance_times.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/incoming-call-by-brekeke

# OpenAI SSML
rag_ssml.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/rag-ssml/process-text
openAI_generate.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/openai/generate-text

# RAG
speech.rag.url=http://10.0.20.11:8000/api/v1/rag
speech.rag.connect_timeout=2
speech.rag.request_timeout=3
speech.rag.credibility=0
