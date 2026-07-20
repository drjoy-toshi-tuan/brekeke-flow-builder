# IVR プロパティ — 大星クリニック 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}
END_受付完了_携帯.prompt={tts_g:内容を確認後、スタッフからお電話またはＳＭＳでご連絡します。ありがとうございました。それでは失礼いたします。}
END_受付完了_固定.prompt={tts_g:内容を確認後、スタッフからお電話またはＳＭＳでご連絡します。ありがとうございました。それでは失礼いたします。}
END_FAQなし案内.prompt={tts_g:ご質問いただいた内容はAI電話ではご対応できませんので、代表電話の『03-6426-5933』におかけ直しください。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:はい、大星クリニックです。予約のお電話ありがとうございます。専用AIオペレーターが内容をおうかがいします。}
用件確認.prompt={tts_g:ご用件を、診察予約、予防接種、その他、からお選びください。変更やキャンセルも「その他」でお願いします。それではどうぞ。}
診療科.prompt={tts_g:診療科がわかれば最初にお知らせください。}
内容確認_診療.prompt={tts_g:今日はどうされましたか？}
希望ワクチン.prompt={tts_g:ご希望のワクチンを、インフルエンザワクチンまたはコロナワクチンからお選びください。その他ワクチンをご希望の場合は、ワクチン名をお話しください。}
その他内容確認.prompt={tts_g:その他のお問合せ。予約の変更。キャンセル。についてお話しください。}
予約希望日時.prompt={tts_g:希望する日にちとお時間をお話しください。}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
相談_問合せ.prompt={tts_g:ご質問内容をお話しください。}
相談_問合せループ.prompt={tts_g:他にご質問はございますか。ご質問がなければ「ありません」とお伝えください。}
相談_FAQ失敗.prompt={tts_g:申し訳ございません。お調べすることができませんでした。}
終話_失敗.prompt={tts_g:誠に申し訳ございません。何度かお聞き取りを試みましたが難しかったため、お電話を終了いたします。それでは失礼いたします。}
患者_診察券番号.prompt={tts_g:診察券番号をお伝えください。}
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
