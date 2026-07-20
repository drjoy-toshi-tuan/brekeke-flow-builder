# IVR プロパティ — 倉敷中央病院付属予防医療プラザ 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:申し訳ありません。現在は受付時間外です。受付時間は、日曜祝日、年末年始を除く月曜から金曜の8時から16時、土曜は8時から12時です。なお、土曜は不定休のため、ホームページの「営業日のご案内」をご確認ください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:大変申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、倉敷中央病院付属予防医療プラザ専用番号、086-422-6800まで、お電話をおかけください。お電話が繋がりましたらガイダンス2番を押してください。受付時間は、日曜祝日、年末年始を除く月曜から金曜の8時から16時、土曜は8時から12時です。なお、土曜は不定休のため、ホームページの「営業日のご案内」をご確認ください。お電話ありがとうございました。}
END_共通_携帯.prompt={tts_g:3営業日を目安に、担当者からお電話、もしくは、ショートメールにてご連絡し、ご予約を確定いたします。現在お申込みが集中しており、通常よりお時間を頂戴しておりますが、必ずご連絡致しますので、よろしくお願い申し上げます。お電話ありがとうございました。それでは失礼いたします。}
END_共通_携帯以外.prompt={tts_g:3営業日を目安に、担当者から折り返しご連絡し、ご予約を確定いたします。現在お申込みが集中しており、通常よりお時間を頂戴しておりますが、必ずご連絡致しますので、よろしくお願い申し上げます。お電話ありがとうございました。それでは失礼いたします。}
END_折返し連絡.prompt={tts_g:折り返しのご連絡、ありがとうございます。大変恐れ入りますが、オペレーターより改めてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:倉敷中央病院付属予防医療プラザの、予約関連専用、AI電話です。この通話は、通話の内容確認およびサービス向上のため、録音させていただいております。}
用件確認.prompt={tts_g:ご用件を、次の5つのうちのいずれかでお話ください。健康診断の予約。予約の変更。予約のキャンセル。当施設から着信があった方の、折り返し連絡。その他お問い合わせ。それでは、お話ください。}
新規_内容聴取.prompt={tts_g:追加を希望されるオプション検査がございましたら、お話ください。ない場合には、特にありません、のようにお話ください。}
新規_希望時期.prompt={tts_g:受診を希望されている時期をお話ください。}
新規_追加質問.prompt={tts_g:他に、オペレーターにお伝えになりたいことがあれば、お話ください。なければ、特にありません、のようにお話ください。}
変更_予約日聴取.prompt={tts_g:現在の予約日を、2025年4月1日のように日付でおっしゃってください。わからない場合や、まだ決まっていない場合は、決まってない、のようにお話ください。なお、ダイヤルプッシュで月と日にちの4桁の数字を入力することもできます。}
変更_変更項目.prompt={tts_g:次の2つのうち、どちらを変更されるかお話ください。受診日。受診日以外の変更。それでは、お話ください。}
変更_希望時期.prompt={tts_g:受診を希望されている時期をお話ください。}
変更_内容聴取.prompt={tts_g:オプション追加や変更等、変更を希望されている内容をお話ください。}
変更_追加質問.prompt={tts_g:他に、オペレーターにお伝えになりたいことがあれば、お話ください。なければ、特にありません、のようにお話ください。}
キャンセル_予約日聴取.prompt={tts_g:現在の予約日を、2025年4月1日のように日付でおっしゃってください。なお、ダイヤルプッシュで月と日にちの4桁の数字を入力することもできます。}
キャンセル_追加質問.prompt={tts_g:他に、オペレーターにお伝えになりたいことがあれば、お話ください。なければ、特にありません、のようにお話ください。}
問合せ_内容聴取.prompt={tts_g:お問い合わせの内容をお話ください。}
新規_受付完了.prompt={tts_g:健康診断の、予約のお申し込みを受付いたしました。}
変更_受付完了.prompt={tts_g:予約変更のお申し込みを受付いたしました。}
キャンセル_受付完了.prompt={tts_g:予約キャンセルのお申し込みを受付いたしました。今年度新たな健診予約が必要な方は、改めてご連絡ください。}
問合せ_受付完了.prompt={tts_g:お問い合わせを受付いたしました。}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}

# wait
冒頭.wait=2000

# 施設固有（要編集）
office_id=TODO_要確認

# 環境設定
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
```

## TODO リスト

- [ ] `office_id` を設定する

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
