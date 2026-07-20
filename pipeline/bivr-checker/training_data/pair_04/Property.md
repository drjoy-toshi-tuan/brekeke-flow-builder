# アナウンス
冒頭.prompt={tts_g:ここからはAI電話にて予約受付を行います。}
終話_非通知.prompt={tts_g:お手数をおかけしますが、発信者番号を通知して再度お電話ください。電話番号の前に いちはちろく を追加いただくことで発信者番号を通知していただくことができます。それでは失礼いたします。}
確認_受診票の有無.prompt={tts_g:お手元に当施設より健康診断のご案内は届いていますか 届いている場合は1番と、届いていない場合は2番と お話し頂くかダイヤルプッシュで選択してください。どうぞ。}
確認_受診歴.prompt={tts_g:ガーデンシティ健診プラザのご利用は初めてですか。初めての場合は、1番と、違う場合は2番と、お話しいただくか、ダイヤルプッシュで選択してください。どうぞ。 }
確認_受診希望内容.prompt={tts_g:受診を希望される内容は、前回と同じでよろしいですか。前回と同じ場合は、1番と、違う場合は2番と、お話しいただくか、ダイヤルプッシュで選択してください。どうぞ。}
確認_用件.prompt={tts_g:お問い合わせ内容について、予約希望日の場合は、「1番」を、オプションの変更や追加については、「2番」をお話しいただくか、ダイヤルプッシュで選択してください。}
復唱_用件.prompt={tts_g:お問い合わせ内容は、#data# でよろしいですか？「はい、そうです」や「いいえ、違います」のように、お答えください。どうぞ。}
確認_健保組合名.prompt={tts_g:受診者様がご加入されている健康保険組合の名称をお答えください。わからない場合は、「わかりません。」とお答えください。どうぞ。}
確認_企業団体名.prompt={tts_g:ご受診者様がお勤めされている企業・団体名をお話しください。退職している場合やお勤めをされていない場合は、「いいえ」と、わからない場合は、「わかりません」と、お答えください。どうぞ。}
確認_希望内容.prompt={tts_g:ご希望するコース名をお伺いします。人間ドック、生活習慣病など、ご希望するコース名をおっしゃってください。}
確認_希望オプション.prompt={tts_g:オプションの変更や追加をご希望の場合は、通話完了後に送信されるSMSからご入力ください。}
確認_オプション変更追加内容.prompt={tts_g:オプションの変更や追加をご希望の場合は、通話完了後に送信されるSMSからご入力ください。}
確認_受診希望時期.prompt={tts_g:では次に、ご希望時期を「10月下旬」のようにお話しください。また、希望日が決まっている場合は、「10月1日」のようにお話しください。 どうぞ。}
確認_希望時期.prompt={tts_g:では次に、ご希望時期を「10月下旬」のようにお話しください。また、希望日が決まっている場合は、「10月1日」のようにお話しください。 どうぞ。}
確認_受診内容.prompt={tts_g:受診内容をお伺いします。「人間ドック」「健康診断」など、ご予約された受診内容をおっしゃってください。わからない場合は、わからないとお答えください。どうぞ。}
確認_被保険者.prompt={tts_g:被保険者、被扶養者区分につきまして、被保険者の方は「１番」を、 配偶者の方は「２番」を、配偶者以外のご家族の方は「３番」と、お話しいただくか ダイヤルプッシュで選択してください。}
確認_特例退職者.prompt={tts_g:特例退職者の方は「１番」、任意継続の方は「２番」を、 いずれも該当しない方は「３番」と、お話しいただくか、ダイヤルプッシュで選択してください。}
終話_①アナウンス.prompt={tts_g: 電話終了後に送信されるSMSより内容をご確認の上、追記・修正をお願いいたします。2営業日以内に担当者から折り返し電話、もしくは、ショートメールにてご連絡いたします。状況によってはご連絡が遅れる場合もございますので、あらかじめご了承ください。お電話ありがとうございました。 }
終話_②アナウンス.prompt={tts_g: 内容確認後、2営業日以内にスタッフより折り返しご連絡をいたします。状況によってはご連絡が遅れる場合もございますので、あらかじめご了承ください。お電話ありがとうございました。 }

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
office_id=697b0ca78de92d000791576e
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