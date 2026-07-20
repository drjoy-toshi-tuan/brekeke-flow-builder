# アナウンス
冒頭.prompt={tts_g:お電話ありがとうございます。四谷メディカルキューブのAI電話です。}
終話_非通知.prompt={tts_g:恐れ入りますが電話番号が非通知設定の場合、AI電話では受付できません。通知設定をしていただくか、先頭に数字の186を付けておかけなおしください。それでは失礼いたします。}
確認_用件.prompt={tts_g:ご用件を次の5つの内、いずれかでお話しください。1、診察予約。2、予約日変更。3、予約キャンセル。4、症状相談。5、予約日確認及び、その他問い合わせ。もう一度お聞きになりたい場合は、『もう一回。』とお話しください。ダイアルプッシュでも受付可能です。}
確認_受診歴.prompt={tts_g:今回ご希望の診療科にかかったことはございますでしょうか。はい、またはいいえでお答えください。}
症状相談_緊急確認.prompt={tts_g:ご相談内容は緊急の内容でしょうか。「はい、そうです」または「いいえ、ちがいます」のようにお話しください。}
予約確認_確認内容.prompt={tts_g:確認事項や問い合わせ内容を簡潔にお話しください。内容を確認後、当院より折り返しご連絡いたします。}
確認_相談内容.prompt={tts_g:ご相談内容を簡潔にお話しください。内容を確認後、当院より折り返しご連絡いたします。}
転送案内.prompt={tts_g:当院の看護師へお電話をお繋ぎいたします。このままお待ちください。}
確認_都合の悪い時期.prompt={tts_g:来院日に関して、ご都合のつかないお日にちや時期がございましたらお話しください。}
確認_症状.prompt={tts_g:今回受診を希望される症状について簡潔にお話しください。経過受診の場合は「前回と同じ。」のようにお話しください。}
確認_現在の予約日.prompt={tts_g:現在の予約日をお話しください。}
終話_初診.prompt={tts_g:初診予約のご希望ですね。担当窓口におつなぎ致しますのでこのままお待ちください。}
終話_予約と変更.prompt={tts_g:ご要望を承りました。こちらのお電話では確定いたしません。3診療日以内に当院より折り返し電話、もしくはショートメールにてご連絡いたしますので、お待ちくださいませ。それでは失礼いたします。}
終話_キャンセル.prompt={tts_g:キャンセルのご要望を承りました。内容確認が必要な場合のみ当院よりご連絡をする場合がございます。あらかじめご了承ください。それでは失礼いたします。}
終話_相談その他.prompt={tts_g:内容を承りました。内容を確認後、当院より折り返し電話、もしくはショートメールにてご連絡いたしますので、お待ちくださいませ。それでは失礼いたします。}
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
office_id=5eecd40e2c9faeddaddc0dc4
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