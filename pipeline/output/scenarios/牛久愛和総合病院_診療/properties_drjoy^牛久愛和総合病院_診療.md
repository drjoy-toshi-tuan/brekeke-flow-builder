# IVR プロパティ — drjoy^牛久愛和総合病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}
END_代表案内_ワクチン.prompt={tts_g:インフルエンザや新型コロナの予防接種はAI電話では予約を承れません。代表電話の『029-873-3111』におかけ直しください。それでは失礼いたします。}
END_代表案内_複数人.prompt={tts_g:申し訳ありませんが、このAI電話ではお一人様分のご予約のみ承っております。二人目以降のご予約につきましては、代表電話の『029-873-3111』におかけ直しください。それでは失礼いたします。}
END_代表案内_リハビリ.prompt={tts_g:リハビリはAI電話では対応出来ませんので、代表電話番号までおかけ直しください。電話番号は、『029-873-3111』です。繰り返します。電話番号は、『029-873-3111』です。繰り返します。電話番号は、『029-873-3111』です。それでは失礼いたします。}
END_代表案内_小児科.prompt={tts_g:小児科はAI電話では対応出来ませんので、代表電話番号までおかけ直しください。電話番号は、『029-873-3111』です。繰り返します。電話番号は、『029-873-3111』です。繰り返します。電話番号は、『029-873-3111』です。それでは失礼いたします。}
END_代表案内_健診.prompt={tts_g:ご希望の診療科はAI電話では対応出来ませんので、健診センターまでおかけ直しください。電話番号は、『029-873-4334』です。繰り返します。電話番号は、『029-873-4334』です。繰り返します。電話番号は、『029-873-4334』です。それでは失礼いたします。}
END_代表案内_耳鼻科.prompt={tts_g:基本的に予約制ではない診療科なので当日受診が可能です。診療時間や休診情報等にございましては代表番号にてご確認ください。お電話ありがとうございます。それでは失礼いたします。}
END_代表案内_当日翌日.prompt={tts_g:当日・翌日の予約についてはAI電話ではご対応できませんので、代表電話の『029-873-3111』におかけ直しください。それでは失礼いたします。}
END_自費検診不可.prompt={tts_g:基本的に自費検診は行っていないため、他の病院をご検討ください。お電話ありがとうございます。それでは失礼いたします。}
END_通話終了_固定.prompt={tts_g:かしこまりました。後ほど折り返しお電話いたします。なお、予約日につきましてはご希望に添えない場合がございます。３営業日以内にご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_通話終了_携帯.prompt={tts_g:後ほど折り返しお電話、もしくはショートメールでご連絡いたします。なお、予約日につきましてはご希望に添えない場合がございます。３営業日以内にご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:こちら牛久愛和総合病院の、予約専用ＡＩ電話です。今日、明日の予約につきましては代表番号へおかけなおしください。}
用件確認.prompt={tts_g:ご用件をお話ください。}
新規・再診確認.prompt={tts_g:新規予約をご希望ですか？２回目以降の診察予約ですか？}
診療科.prompt={tts_g:まずは診療科をお話ください。わからない場合はわからないとお話ください。}
診療科2.prompt={tts_g:同日に受信予定の他の診療科はありますか？}
紹介状確認.prompt={tts_g:紹介状をお持ちですか？}
選定療養費案内.prompt={tts_g:紹介状をお持ちではない場合、選定療養費として７，７００円がかかる場合がございますのでご了承ください。}
担当先生.prompt={tts_g:ご希望の先生のお名前をお話ください。わからない場合はわからないとお話ください。}
現在予約日.prompt={tts_g:現在ご予約いただいている日付は、いつでしょうか？}
予約希望日.prompt={tts_g:次に、予約希望日をお伺いいたします。予約希望日もしくはご希望の曜日をお話しください。}
変更理由.prompt={tts_g:それでは、ご予約変更の理由をお話ください。}
キャンセル理由.prompt={tts_g:それでは、ご予約キャンセルの理由をお話ください。}
検診_症状確認.prompt={tts_g:症状がある場合は専門外来の予約になりますが、症状は何もないですか？}
検診_症状あり案内.prompt={tts_g:その場合は専門外来の予約になりますが、紹介状をお持ちではない場合、選定療養費として７，７００円がかかる場合がございますのでご了承ください。}
受診券確認.prompt={tts_g:受診券もしくは利用券などはありますか？}
市町村.prompt={tts_g:市町村はどちらでしょうか？}
同時予約確認.prompt={tts_g:ご一緒に他の検診のご予約はございますか？}
その他問い合わせ.prompt={tts_g:そのほかに何かお問い合わせは有りませんか？}
その他問い合わせ回答.prompt={tts_g:ご要望を承りました。順番に対応しておりますので、しばらくお待ちください。}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}
患者_診察券番号.prompt={tts_g:診察券番号をお伝えください。}

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
