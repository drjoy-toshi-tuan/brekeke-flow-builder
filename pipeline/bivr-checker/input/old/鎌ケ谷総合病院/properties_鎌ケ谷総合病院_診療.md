# IVR プロパティ — 鎌ケ谷総合病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、代表電話へおかけ直しください。受付時間は、月曜日から金曜日は9時から17時、土、日、祝日は9時から12時となっております。電話番号は047-498-8111です。お電話ありがとうございました。}
END_歯科口腔外科.prompt={tts_g:歯科口腔外科のご予約につきましては歯科口腔外科直通番号へおかけ直しください。受付時間は、日曜、祝日を除く月曜日から金曜日は9時から17時、土曜日は9時から12時となっております。電話番号は047-498-8721です。お電話ありがとうございました。}
END_健康管理センター.prompt={tts_g:健康管理センターのご予約につきましては健診センター直通番号へおかけ直しください。受付時間は、日曜、祝日を除く月曜日から土曜日の13時から16時となっております。電話番号は047-498-8125です。お電話ありがとうございました。}
END_インフルエンザワクチン.prompt={tts_g:インフルエンザワクチンのご予約につきましては健診センター直通番号へおかけ直しください。受付時間は、日曜、祝日を除く月曜日から土曜日の13時から16時となっております。電話番号は047-498-8125です。お電話ありがとうございました。}
END_コロナワクチン.prompt={tts_g:コロナワクチンの予約受付は終了いたしました。お電話ありがとうございました。}
END_対応外診療科案内.prompt={tts_g:AI電話では対応していない診療科のため代表電話へおかけ直しください。受付時間は、月曜日から金曜日は9時から17時、土、日、祝日は9時から12時となっております。電話番号は047-498-8111です。お電話ありがとうございました。}
END_当日予約案内.prompt={tts_g:申し訳ございません。本日の予約に関するご相談は、代表電話へおかけ直しください。受付時間は、月曜日から金曜日は9時から17時、土、日、祝日は9時から12時となっております。電話番号は047-498-8111です。お電話ありがとうございました。}
END_通常_携帯.prompt={tts_g:お申し込みを受付いたしました。予約はまだ確定しておりません。担当者より3日以内に、お電話またはSMSで必ずご連絡いたします。お電話ありがとうございました。}
END_通常_固定.prompt={tts_g:お申し込みを受付いたしました。予約はまだ確定しておりません。担当者より3日以内に、お電話で必ずご連絡いたします。お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。鎌ケ谷総合病院の、予約専用、AI電話です。}
用件確認.prompt={tts_g:ご用件をお話しください。}
受診歴確認.prompt={tts_g:当院でのご受診は初めてですか？}
紹介状確認.prompt={tts_g:初診のご予約ですね？他の医療機関からの紹介状はお持ちですか？}
選定療養費案内.prompt={tts_g:他の医療機関からの紹介状をお持ちでない患者さんにつきましては、通常の診療費とは別に、初診時選定療養費として、2,200円を全額自己負担いただいております。予めご了承ください。}
診療科_予約.prompt={tts_g:受診を希望される診療科をお話しください。}
診療科_変更.prompt={tts_g:受診を希望される診療科をお話しください。}
予約日_変更.prompt={tts_g:次に、予約票に記載されている予約日を、5月1日のように日付でお話しください。}
予約希望日_変更.prompt={tts_g:次に、予約希望日をお伺いいたします。ご都合の良い日付や曜日をお話しください。}
予約希望日復唱_変更.prompt={tts_g:ご希望日を承りました。日曜、祝日は休診の診療科もございます。こちらのお電話では予約は確定しておりませんので、担当者からの折り返し連絡をお待ちください。}
診療科_キャンセル.prompt={tts_g:受診を希望される診療科をお話しください。}
予約日_キャンセル.prompt={tts_g:次に、予約票に記載されている予約日を、5月1日のように日付でお話しください。}
理由.prompt={tts_g:差し支えなければ、理由をお話しください。}
内容確認.prompt={tts_g:ご確認内容についてお伺いします。次回の予約日時を教えてほしい、など、内容を簡潔にお話しください。}
その他問合せ.prompt={tts_g:そのほかに何かお問い合わせはありませんか？}

# サブフローTTS
相談_問合せ.prompt={tts_g:ご質問内容をお話しください。}
相談_問合せループ.prompt={tts_g:他にご質問はございますか。ご質問がなければ「ありません」とお伝えください。}
相談_FAQ失敗.prompt={tts_g:申し訳ございません。お調べすることができませんでした。}
終話_失敗.prompt={tts_g:誠に申し訳ございません。何度かお聞き取りを試みましたが難しかったため、お電話を終了いたします。それでは失礼いたします。}
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
