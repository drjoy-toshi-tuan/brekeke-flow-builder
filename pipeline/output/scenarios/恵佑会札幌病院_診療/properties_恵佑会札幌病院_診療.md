# IVR プロパティ — 恵佑会札幌病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_代表案内_申し込み方法.prompt={tts_g:{tts_g:大変申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、代表電話番号へおかけなおしください。受付時間は平日8じ45分から17時までです。お電話番号をご案内いたしますのでメモをご準備ください。<speak type="telephone" breakc="300ms">011-863-2105</speak>　です。　<speak type="telephone" breakc="300ms">011-863-2105</speak>　です。　<speak type="telephone" breakc="300ms">011-863-2105</speak>　です。お電話ありがとうございました。それでは失礼いたします。}}
END_SMS送信案内.prompt={tts_g:{tts_g:申込みのページを、ショートメールでお送りします。メッセージのリンクを開き、はじめに「電話番号」で本人確認をしてください。そのあと、患者さまの情報を入力してください。お電話ありがとうございました。それでは失礼いたします。}}
END_受付不可診療科.prompt={tts_g:{tts_g:大変申し訳ございません。歯科口腔外科以外の診療科に関するお問い合わせはこちらでは承っておりません。恐れいりますが、このあとご案内をする専用電話にお問い合わせください。番号をご案内しますのでメモをご準備下さい。番号は<speak type="telephone" breakc="300ms">050-1726-5776</speak>です。電話番号は<speak type="telephone" breakc="300ms">050-1726-5776</speak>です。それでは失礼いたします。}}
END_予約_FIXED.prompt={tts_g:{tts_g:診察予約のご希望を受け付けました。<break time="300ms"/> 3診療日以内に担当者から折り返し電話にてご連絡いたします。<break time="300ms"/> 担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/> お電話ありがとうございました。それでは失礼いたします。}}
END_予約_MOBILE.prompt={tts_g:{tts_g:診察予約のご希望を受け付けました。<break time="300ms"/> このあとすぐに、通話内容の確認・修正ができるショートメッセージをお送りしますので、必ずご確認ください。<break time="300ms"/> また、３診療日以内に担当者より折り返しお電話、もしくはショートメールにてご連絡いたします。<break time="300ms"/> 担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/> お電話ありがとうございました。それでは失礼いたします。}}
END_変更_FIXED.prompt={tts_g:{tts_g:予約変更のご希望を受け付けました。<break time="300ms"/> 3診療日以内に担当者から折り返し電話にてご連絡いたします。<break time="300ms"/> 担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/> お電話ありがとうございました。それでは失礼いたします。}}
END_変更_MOBILE.prompt={tts_g:{tts_g:予約変更のご希望を受け付けました。<break time="300ms"/> このあとすぐに、通話内容の確認・修正ができるショートメッセージをお送りしますので、必ずご確認ください。<break time="300ms"/> また、３診療日以内に担当者より折り返しお電話、もしくはショートメールにてご連絡いたします。<break time="300ms"/> 担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/> お電話ありがとうございました。それでは失礼いたします。}}
END_キャンセル_FIXED.prompt={tts_g:{tts_g:予約キャンセルのご希望を受け付けました。<break time="300ms"/> 3診療日以内に担当者から折り返し電話にてご連絡いたします。<break time="300ms"/> 担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/> お電話ありがとうございました。それでは失礼いたします。}}
END_キャンセル_MOBILE.prompt={tts_g:{tts_g:予約キャンセルのご希望を受け付けました。<break time="300ms"/> このあとすぐに、通話内容の確認・修正ができるショートメッセージをお送りしますので、必ずご確認ください。<break time="300ms"/> また、３診療日以内に担当者より折り返しお電話、もしくはショートメールにてご連絡いたします。<break time="300ms"/> 担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/> お電話ありがとうございました。それでは失礼いたします。}}
END_その他_FIXED.prompt={tts_g:{tts_g:その他問い合わせのご希望を受け付けました。<break time="300ms"/> 3診療日以内に担当者から折り返し電話にてご連絡いたします。<break time="300ms"/> 担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/> お電話ありがとうございました。それでは失礼いたします。}}
END_その他_MOBILE.prompt={tts_g:{tts_g:その他問い合わせのご希望を受け付けました。<break time="300ms"/> このあとすぐに、通話内容の確認・修正ができるショートメッセージをお送りしますので、必ずご確認ください。<break time="300ms"/> また、３診療日以内に担当者より折り返しお電話、もしくはショートメールにてご連絡いたします。<break time="300ms"/> 担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/> お電話ありがとうございました。それでは失礼いたします。}}
冒頭_アナウンス.prompt={tts_g:{tts_g:お電話ありがとうございます。恵佑会札幌病院の、歯科口腔外科予約申し込み電話です。テレビの音や周囲の騒音がない静かなところでお話しください。}}
申し込み方法確認.prompt={tts_g:{tts_g:まずはじめに、申し込み方法をお伺いします。ネットで申し込みを希望の方は、申込用のURLをショートメールにてお送りします。次のいずれかの番号をお話しください。「ネットから申し込みを希望の方は、１」、「このままお電話での申し込み希望の方は、２」、または　<dtmf digit="1"/>}}
SMS_連絡先確認_携帯.prompt={tts_g:{tts_g:ご連絡先のお電話番号は、今おかけいただいている<speak type="telephone" breakc="300ms">{incoming_phone_number}</speak>でよろしいでしょうか？}}
SMS_連絡先聴取_固定.prompt={tts_g:{tts_g:URLを送付するために、ご連絡先の携帯番号をお伺いします。携帯番号をお話しください。}}
用件確認.prompt={tts_g:{tts_g:次の４つのうち、いずれかの番号をお話しください。<break time="300ms"/>「予約を申し込む方は、１」、<break time="300ms"/>「予約を変更する方は、２」、<break time="300ms"/>「予約をキャンセルする方は、3」、<break time="300ms"/>「その他お問い合わせの方は、4」<dtmf digit="1"/>}}
受診歴確認.prompt={tts_g:{tts_g:新規予約をご希望ですか？2回目以降の診察予約ですか？}}
紹介状確認.prompt={tts_g:{tts_g:紹介状はお持ちでしょうか？}}
医師名.prompt={tts_g:{tts_g:封筒に記載の、先生の名前をお話ください。}}
希望医師.prompt={tts_g:{tts_g:診察を希望される先生の名前をお話ください。ご希望がない場合は、なしとお話ください。}}
予約希望日_再診.prompt={tts_g:{tts_g:次に、予約希望日をお伺いいたします。予約日は3診療日以内の折り返し連絡にて確定いたします。それではご都合の良い日付や曜日をお話しください。}}
予約日_変更.prompt={tts_g:{tts_g:現在の予約日をお話ください。}}
予約希望日_変更.prompt={tts_g:{tts_g:次に、予約希望日をお伺いいたします。予約日は3診療日以内の折り返し連絡にて確定いたします。それではご都合の良い日付や曜日をお話しください。}}
予約日_キャンセル.prompt={tts_g:{tts_g:現在の予約日をお話ください。}}
キャンセル理由.prompt={tts_g:{tts_g:キャンセルの理由をお話ください。}}
内容確認_その他.prompt={tts_g:{tts_g:お問い合わせの内容をお話しください。}}

# サブフローTTS
患者_診察券番号.prompt={tts_g:診察券番号をお伝えください。}
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
