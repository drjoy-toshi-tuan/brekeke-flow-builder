# IVR プロパティ — 石巻赤十字病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}
END_終話.prompt={tts_g:かしこまりました。お申し込みを受付いたしました。3診療日以内に担当者から折り返し電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_代表案内.prompt={tts_g:申し訳ございません。AI電話ではお受けできません。祝日を除く、月曜から金曜の、13時から17時に、外来予約変更の番号へおかけ直し下さい。電話番号が分かる場合は、そのままお電話をお切りください。分からない場合はご案内いたしますので、メモをご準備ください。電話番号は、0225217226です。繰り返します。電話番号は、0225217226です。繰り返します。電話番号は、0225217226です。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。石巻赤十字病院の、予約変更、AI電話です。}
用件確認.prompt={tts_g:初めに、ご用件を次の2つのうちのいずれかでお話ください。「予約の変更またはキャンセル。」「予約についての確認。」それでは、お話ください。}
予約日確認_変更キャンセル.prompt={tts_g:受診日について、現在予約されている受診日は土日祝日を除き、3日以上先でしょうか？はい、または、いいえ、でお話しください。}
予約日確認_確認.prompt={tts_g:受診日について、現在予約されている受診日は土日祝日を除き、3日以上先でしょうか？はい、または、いいえ、でお話しください。}
診療科1聴取.prompt={tts_g:受診される診療科をお伺いします。診療科が分からない場合は、「わからない」とお話しください。診療科が複数ある場合は1つめの診療科をお話しください。}
診療科2聴取.prompt={tts_g:その他の診療科をお伺いします。ない場合は「ない」とお話しください。}
内容確認.prompt={tts_g:確認したい内容を簡潔にお話しください。}
最後の問い合わせ.prompt={tts_g:そのほかに何かお問い合わせは有りませんか？}

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
