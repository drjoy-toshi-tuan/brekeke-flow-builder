# IVR プロパティ — と）東京都立豊島_20260712 M｜診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
予約受付完了.prompt={tts_g:かしこまりました。ご予約の申し込みを受付いたしました。内容を確認のうえ、スタッフから折り返しご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
変更受付完了.prompt={tts_g:かしこまりました。ご予約変更の申し込みを受付いたしました。内容を確認のうえ、スタッフから折り返しご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
キャンセル受付完了.prompt={tts_g:かしこまりました。ご予約キャンセルの申し込みを受付いたしました。内容を確認のうえ、スタッフから折り返しご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
問い合わせ受付完了.prompt={tts_g:かしこまりました。お問い合わせ内容を受付いたしました。内容を確認のうえ、スタッフから折り返しご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
聴取失敗.prompt={tts_g:申し訳ございません。うまくお聞き取りできませんでした。恐れ入りますが、しばらくたってからおかけ直しください。それでは失礼いたします。}
非通知.prompt={tts_g:お客様のお電話は非通知のため、折り返しのご連絡ができません。恐れ入りますが、電話番号を通知の上おかけ直しください。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。東京都立豊島病院、AI電話受付です。}
用件確認.prompt={tts_g:ご用件をお伺いします。ご予約は1番を、変更は2番を、キャンセルは3番を、その他のお問い合わせは4番と、お話しいただくか番号をプッシュしてください。}
追加の質問.prompt={tts_g:最後に、その他ご質問はございますか。ご質問がある場合はお話しください。無い場合は「ないです」とお話しいただくか、1番をプッシュしてください。}
FAQ回答.prompt={tts_g:<%scripts-faq%>}
FAQ失敗案内.prompt={tts_g:承知いたしました。お問い合わせの内容は、後ほどスタッフよりお電話の際にお伺いいたします。}

# wait
冒頭.wait=2000

# 施設固有（要編集）
office_id=TODO_要確認

# 環境設定
# amivoice
amivoice.uri=ws://10.0.20.11:8000/ws
amivoice.language=ja
amivoice.engine=会話汎用
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
