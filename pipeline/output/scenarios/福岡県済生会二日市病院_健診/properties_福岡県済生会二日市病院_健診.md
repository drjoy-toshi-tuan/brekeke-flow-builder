# IVR プロパティ — 福岡県済生会二日市病院 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}
END_終話.prompt={tts_g:後ほど、担当者から折り返しご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_代表案内_就職進学.prompt={tts_g:大変申し訳ございません。就職時・進学時健診は代表電話番号へおかけなおしください。電話番号は、{tts_g:0 9 2 9 2 3 1 5 5 1}、繰り返します、{tts_g:0 9 2 9 2 3 1 5 5 1}、お電話ありがとうございました。それでは失礼いたします。}
用件確認.prompt={tts_g:ご用件を、健診の予約、予約の変更、キャンセルよりお話しください}
受診歴確認.prompt={tts_g:過去、当院の健康診断を受診されたことはございますか？}
前回と同じ内容確認.prompt={tts_g:今回のご予約は、前回と同じ内容を希望されていますか？}
受診希望内容_初回.prompt={tts_g:それでは、日帰り人間ドックや、生活習慣病予防健診など、ご希望の健診メニューをお話ください。}
受診希望内容_再診.prompt={tts_g:それでは、日帰り人間ドックや、生活習慣病予防健診など、ご希望の健診メニューをお話ください。}
予約日_変更.prompt={tts_g:現在の予約日をお話しください}
変更内容.prompt={tts_g:それでは、変更を希望される内容をお話しください}
予約日_キャンセル.prompt={tts_g:現在の予約日をお話しください}
予約希望日.prompt={tts_g:受診希望日を、2か月後以降の日程でお話しください}
意図不明_移行.prompt={tts_g:大変申し訳ございません。ご回答が確認できませんでした。次の項目をお伺いいたします。}
拒否対応_移行.prompt={tts_g:担当者から折り返しご連絡します。}

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
