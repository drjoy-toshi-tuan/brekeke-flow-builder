# IVR プロパティ — 足利中央病院 地域連携

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}
END_完了.prompt={tts_g:ご依頼を承りました。3診療日以内に担当者から折り返しご連絡いたします。それでは失礼いたします。}
END_電話案内.prompt={tts_g:当日の予約についてはAI電話ではご対応できませんので、代表電話の、0284-72-8401、におかけ直しください。}
END_転送成功.prompt={tts_g:TODO_発話内容を記入}
END_転送失敗.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。足利中央病院の、地域連携室専用、AI電話です。}
緊急確認.prompt={tts_g:こちらのお電話は本日中に対応が必要な緊急案件になりますでしょうか。緊急の場合は、はい、違う場合は、いいえ、とお話しください。}
施設名聴取.prompt={tts_g:はじめに、施設名をお話しください。}
入電者氏名聴取.prompt={tts_g:次に、お電話いただいている方の氏名をお話しください。}
用件確認.prompt={tts_g:それでは、ご用件をお伺いいたします。次の3つのうち、いずれかでお話しください。1、相談・紹介に関して。2、日程調整に関して。3、その他お問い合わせに関して。それではお話しください。}
病名聴取.prompt={tts_g:次に、受診される方の病名をお話しください。}
相談_内容聴取.prompt={tts_g:本件の内容を簡潔にお話しください。}
日程_内容聴取.prompt={tts_g:本件の内容を簡潔にお話しください。}
希望日時聴取.prompt={tts_g:予約希望日をお伺いいたします。ご都合の良い日付や曜日を、10月1日、10月上旬や、来週のようにお話しください。}
返信期限確認.prompt={tts_g:返信期日のご希望がありましたらお話しください。}
その他_内容聴取.prompt={tts_g:本件の内容を簡潔にお話しください。}
最後の問い合わせ.prompt={tts_g:そのほかに何かお問い合わせは有りませんか。}

# サブフローTTS
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}

# wait
冒頭.wait=2000

# 施設固有（要編集）
office_id=TODO_要確認
緊急転送.number=TODO_転送先番号を入力

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
- [ ] 以下のモジュールにアナウンス文言を記入する:
  - `END_転送成功`
  - `END_転送失敗`
- [ ] 転送先電話番号を設定する:
  - `緊急転送`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
