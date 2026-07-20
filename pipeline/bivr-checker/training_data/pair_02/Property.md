# アナウンス
冒頭.prompt={tts_g:お電話ありがとうございます。入間ハート病院の、予約専用AI電話です。当日に関するお問い合わせは、恐れ入りますが、代表電話番号、04-2934-5050におかけ直しください。}
終話_非通知.prompt={tts_g:申し訳ございません。非通知設定のお電話はおつなぎできません。お手数ですが、通知設定に切り替えるか、電話番号の先頭に「186」を付けておかけ直しください。}
確認_種別.prompt={tts_g:はじめに、次の4つのうちのいずれかでお話ください。「診察の方は、1を。」、「検査の方は、2を。」、「予防接種の方は、3を。」、「送迎の方は、4を。」、それでは、お話ください。プッシュボタンでも操作できます。}
確認_種別_否定後再聴取.prompt={tts_g:大変失礼いたしました。再度、次の4つのうちのいずれかでお話ください。「診察の方は、1を。」、「検査の方は、2を。」、「予防接種の方は、3を。」、「送迎の方は、4を。」、それでは、お話ください。プッシュボタンでも操作できます。}
復唱_種別.prompt={tts_g:#data# でよろしいですか？「はい、そうです」または「いいえ、ちがいます」でお話しください。}
確認_用件①.prompt={tts_g:次に、ご用件を次の4つのうちのいずれかでお話ください。「予約の方は、1を。」、「変更の方は、2を。」、「キャンセルの方は、3を。」、「その他確認の方は、4を。」、それでは、お話ください。プッシュボタンでも操作できます。}
確認_用件①_否定後再聴取.prompt={tts_g:大変失礼いたしました。再度、ご用件を次の4つのうちのいずれかでお話ください。「予約の方は、1を。」、「変更の方は、2を。」、「キャンセルの方は、3を。」、「その他確認の方は、4を。」、それでは、お話ください。プッシュボタンでも操作できます。}
復唱_用件①.prompt={tts_g:#data# でよろしいですか？「はい、そうです」または「いいえ、ちがいます」でお話しください。}
終話_失敗.prompt={tts_g:内容については後ほど担当者より確認をさせていただきます。お電話ありがとうございました。それでは失礼いたします。}
終話_代表案内.prompt={tts_g:この電話番号では検査に関するご予約を受け付けておりません。恐れ入りますが、代表電話番号、04-2934-5050におかけ直しください。}
終話_予約.prompt={tts_g:ご要望を承りました。3診療日以内に担当者より折り返し電話、もしくはショートメッセージにてご連絡をいたします。担当者からのご連絡後に確定となりますので、しばらくお待ちくださいませ。携帯電話でおかけの方はこのあとショートメッセージを送りしますので、内容と修正をお願いいたします。それでは失礼いたします。}
終話_変更＆確認.prompt={tts_g:ご要望を承りました。3診療日以内に、担当者から折り返し電話、もしくは、ショートメッセージにてご連絡いたします。担当者からのご連絡後に確定となりますので、しばらくお待ちくださいませ。携帯電話でおかけの方はこの後ショートメッセージを送りしますので、内容と修正をお願いいたします。それでは失礼いたします。 }
終話_キャンセル.prompt={tts_g:キャンセルを受付いたしました。内容により、担当者からご連絡差し上げる可能性があります。お電話ありがとうございました。 それでは失礼いたします。}

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
office_id=5eecd4062c9faeddaddbcb00

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