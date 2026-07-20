# IVR プロパティ — 福岡県済生会二日市病院 連携室

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}
END_至急代表案内.prompt={tts_g:申し訳ございません、至急のご用件の場合には、済生会二日市病院代表電話までおかけなおしください。受付時間は土日祝日を除く月曜日から金曜日の8時30分から17時です。お電話番号が分かる場合は、お電話をお切りください。分からない場合はご案内いたしますのでメモをご準備ください。092-923-1551、繰り返します、092-923-1551、繰り返します、092-923-1551、お電話ありがとうございました。それでは失礼いたします。}
END_終話.prompt={tts_g:かしこまりました。内容を確認後、担当者より折り返し電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。福岡県済生会二日市病院の患者支援センター専用、AI電話です。}
至急確認.prompt={tts_g:はじめにお伺いします。至急のご用件でしょうか？}
用件聴取.prompt={tts_g:ご用件をお話しください。}
病棟担当者確認.prompt={tts_g:入院病棟、または担当MSWをお話しください。}
患者名聴取.prompt={tts_g:患者さんのお名前をフルネームでお話ください。}
施設名聴取.prompt={tts_g:施設名・所属・お名前をお話しください。}
確認項目聴取.prompt={tts_g:その他に、何かお問い合わせはございませんか？}

# サブフローTTS
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
