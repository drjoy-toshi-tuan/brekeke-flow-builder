# アナウンス
冒頭.prompt={tts_g:お電話ありがとうございます。JAとりで総合医療センターの予約専用AI電話です。当日のご予約に関してはこのAI電話では受付することができません。本日これから受診されたい方、本日の予約変更の方、リハビリのご予約に関することは代表番号におかけ直しをお願いいたします。}
確認_用件.prompt={tts_g:ご用件を次の4つの内からお話しください。「予約。」、「変更。」、「キャンセル。」、「その他問い合わせ。」、それではどうぞ。}
確認_通院歴.prompt={tts_g:過去に当院で受診されたことはありますか？「はい、あります。」、もしくは、「いいえ、ありません。」とお話しください。}
選定療養費案内.prompt={tts_g:他の医療機関からの紹介状をお持ちでない患者様につきましては、通常の診療費とは別に、初診時選定療養費として、医科の方は7,700円、歯科の方は5,500円を全額自己負担いただいております。予めご了承ください。}
確認_診療科.prompt={tts_g:それでは、受診を希望される診療科をお話しください。}
確認_診療科_2.prompt={tts_g:それでは、#data# を希望される診療科をお話しください。}
確認_追加診療科2.prompt={tts_g:他に診療科はありますか？追加の診療科をお話しいただくか、「いいえ、ありません。」とお話しください。}
確認_現在の予約日.prompt={tts_g:現在の予約日をお話しください。}
確認_予約希望日.prompt={tts_g:本日より3診療日以降の日程で、受診を希望される時期をお話しください。}
確認_理由.prompt={tts_g:今回の#data# の理由を教えてください。どうぞ。}
確認_問い合わせ内容.prompt={tts_g:確認をしたい内容に関して、簡潔にお話しください。}
復唱_診療科.prompt={tts_g:診療科は、#data# でよろしいですか？「はい、そうです。」、もしくは、「いいえ、違います。」とお話しください。}
復唱_診療科2.prompt={tts_g:診療科は、#data# でよろしいですか？「はい、そうです。」、もしくは、「いいえ、違います。」とお話しください。}
復唱診療科否定.prompt={tts_g:大変失礼いたしました。改めて、受診を希望される診療科をお話しください。}
復唱診療科2否定.prompt={tts_g:大変失礼いたしました。改めて、変更を希望される診療科をお話しください。}
対象外案内_1.prompt={tts_g:申し訳ございません。こちらの診療科はこのお電話ではお受けできません。申し訳ございませんが代表電話へおかけなおし下さい。}
対象外案内_2.prompt={tts_g:申し訳ございません。こちらの診療科はこのお電話ではお受けできません。申し訳ございませんが代表電話へおかけなおし下さい。}
対象外案内_3.prompt={tts_g:申し訳ございません。こちらの診療科はこのお電話ではお受けできません。申し訳ございませんが代表電話へおかけなおし下さい。}
終話_代表案内.prompt={tts_g:代表電話の番号は0297-74-5551です。繰り返します。代表電話の番号は0297-74-5551です。それでは失礼いたします。}
終話_アナウンス①.prompt={tts_g:ご要望を承りました。電話終了後に送信されるショートメッセージより確認、修正をお願いいたします。3診療日以内に担当者より折り返しご連絡をいたします。それでは失礼いたします。}
終話_アナウンス②.prompt={tts_g:ご要望を承りました。3診療日以内に、担当者から折り返し電話、もしくは、ショートメッセージにてご連絡いたします。担当者からのご連絡後に確定となりますので、しばらくお待ちくださいませ。それでは失礼いたします。 }
終話_アナウンス③.prompt={tts_g:キャンセルを受付いたしました。内容により、担当者からご連絡差し上げる可能性があります。お電話ありがとうございました。 それでは失礼いたします。}
終話_アナウンス④.prompt={tts_g:内容により、担当者からご連絡差し上げる可能性があります。お電話ありがとうございました。 それでは失礼いたします。}
終話_失敗.prompt={tts_g:ご回答の確認ができませんでしたのでこちらからお電話失礼させていただきます。}

# amivoice
amivoice.uri=ws://10.0.20.11:8000/ws
amivoice.language=ja
amivoice.engine=入力汎用
amivoice.keep_filter_token=true
amivoice.silent_detection_ms=2000
amivoice.timeout_ms=30000
amivoice.probability=0.57
amivoice.detection_flag=検出しない
amivoice.save_log=false

# Save2DB
office_id=5eecd4052c9faeddaddb9c87
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