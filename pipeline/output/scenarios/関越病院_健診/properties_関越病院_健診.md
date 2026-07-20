# IVR プロパティ — 関越病院 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_新規.prompt={tts_g:健康診断の予約の申し込みを受付いたしました。終話後、関越病院よりショートメールが届きますので内容を必ずご確認いただき、誤りがありましたら修正をお願いいたします。後ほど、担当者から折り返し電話、もしくは、SMSにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_変更.prompt={tts_g:予約変更の申し込みを受付いたしました。終話後、関越病院よりショートメールが届きますので内容を必ずご確認いただき、誤りがありましたら修正をお願いいたします。後ほど、担当者から折り返し電話、もしくは、SMSにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_キャンセル.prompt={tts_g:予約キャンセルを受付いたしました。お電話ありがとうございました。それでは失礼いたします。}
END_折り返し.prompt={tts_g:オペレーターより改めてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_問い合わせ.prompt={tts_g:お問い合わせを受付いたしました。終話後、関越病院よりショートメールが届きますので内容を必ずご確認いただき、誤りがありましたら修正をお願いいたします。後ほど、担当者から折り返し電話、もしくは、SMSにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_代表電話案内.prompt={tts_g:本日の健診をご希望のかたは、代表電話へおかけ直しください。受付時間は、日曜祝日を除く、月曜日から金曜日は8時半から17時半、土曜日は、8時半から12時までとなっております。電話番号は049-285-3161です。お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。関越病院の、健診センター専用、AI電話です。}
用件_聴取.prompt={tts_g:ご用件を、次の4つのうち、いずれかでお話ください。1番、健診の予約。2番、予約の変更、キャンセル。3番、その他お問い合わせ。4番、当施設から着信があった方の折り返し連絡。それでは、お話ください。}
希望_コース.prompt={tts_g:ご希望のメニューを次の4つのうちのいずれかでお話ください。番号またはダイヤルプッシュでも可能です。1番、特定健診。2番、人間ドック。3番、一般健診。4番、企業健診。それでは、お話ください。}
予約_希望_人数.prompt={tts_g:受診を希望されている時期や、人数をお話ください。決まっていない場合には、決まっていない、とお話ください。}
案内_氏名_新規.prompt={tts_g:ありがとうございます。それでは、受診される方、または代表者のお名前を、フルネームでお話ください。}
現在_予約日.prompt={tts_g:現在の予約日を「4月1日」のように日付でお話ください。AIが予約日を正しく認識しない場合は、ダイヤルプッシュでの入力も可能です。日付でお話いただくか、ダイヤルプッシュで月と日にちの4桁の数字を入力してください。}
変更内容_判別.prompt={tts_g:変更またはキャンセル内容を、次の3つのうちの、いずれかでお話ください。1番、受診内容の変更。2番、予約日の変更。3番、予約のキャンセル。それでは、お話ください。}
変更詳細_受診内容.prompt={tts_g:ご希望の受診内容をお話ください。}
変更詳細_日程.prompt={tts_g:ご希望の日程をお話ください。AIが日付を正しく認識しない場合は、ダイヤルプッシュでの入力も可能です。}
変更理由_聴取.prompt={tts_g:ご予約変更の理由をお話下さい。}
キャンセル理由_聴取.prompt={tts_g:ご予約キャンセルの理由をお話下さい。}
案内_氏名_変更.prompt={tts_g:かしこまりました。続いて、予約された方のお名前を、フルネームでお話ください。}
折り返し_案内.prompt={tts_g:お忙しい中、折り返しのご連絡をいただきまして、ありがとうございます。恐れ入りますが、予約された方のお名前を、フルネームでお話ください。}
当日予約_確認.prompt={tts_g:健診日 当日のご連絡、お問い合わせですか？はい、または、いいえ、で、お話下さい。}
問い合わせ_内容.prompt={tts_g:お問い合わせの内容をお話ください。}
担当者名_その他.prompt={tts_g:お電話いただいている方のお名前を、フルネームでお話ください。}

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
