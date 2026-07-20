# IVR プロパティ — 岡山中央病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:ただいまの時間帯は、AI電話の対応時間外です。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:お電話が遠いようで、回答が確認できませんでした。恐れ入りますが、おかけなおしください。お電話ありがとうございました。}
END_受付完了.prompt={tts_g:申し込みを受付いたしました。担当者から電話、もしくは、ショートメッセージにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_人間ドック案内.prompt={tts_g:申し訳ございませんが、人間ドックのご予約に関するお問い合わせは、健康増進センターにて承ります。電話番号を申し上げますので、そちらへお掛けなおし下さい。健康増進センターの電話番号は、086-252-3222です。繰り返します。健康増進センターの電話番号は、086-252-3222です。繰り返します。健康増進センターの電話番号は、086-252-3222です。お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:セントラルクリニック・伊島です。AI電話にてご用件を承り、担当者よりお電話いたしますので、予めご了承ください。それでは、最初に、}
用件聴取.prompt={tts_g:ご用件を、次の3つのうちのいずれかでお話ください。「診察の予約について」、「人間ドックについて」、「その他ご相談」。それでは、お話ください。}
診療科聴取.prompt={tts_g:それでは、ご希望の診療科名をお答えください。}
希望日聴取.prompt={tts_g:ご希望の日時や、内容をお話ください。折り返し、電話で詳しく確認させていただきます。}
連絡事項_診察予約.prompt={tts_g:他にご連絡事項はございますか？なければ、特になし、とお答えください。}
相談内容聴取.prompt={tts_g:それでは、お問い合わせ内容をお話ください。}
連絡事項_相談.prompt={tts_g:他にご連絡事項はございますか？なければ、特になし、とお答えください。}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
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
