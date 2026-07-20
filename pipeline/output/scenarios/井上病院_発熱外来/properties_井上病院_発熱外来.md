# IVR プロパティ — 井上病院 発熱外来

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:お電話が遠いようで、回答が確認できませんでした。恐れ入りますが、代表電話へご連絡下さい。}
END_予約完了.prompt={tts_g:ご予約の申し込みを受付ました。予約についてのご連絡を、ショートメッセージ、またはお電話にてご連絡いたします。それでは、失礼いたします。}
END_予約枠終了.prompt={tts_g:申し訳ございません。本日の予約受付枠は、終了いたしました。お電話ありがとうございました。}
END_予約失敗.prompt={tts_g:予約を承ることができませんでした。恐れ入りますが再度電話を掛けなおしていただき、最初から予約手続きを行ってください。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。井上病院の発熱外来、AI電話です。}
注意事項.prompt={tts_g:このお電話は、途中で電話を切ると予約確定できませんのでご注意ください。}
高校生未満案内.prompt={tts_g:本窓口は、高校生未満の場合、ご予約を承ることができません。診察を希望される方が高校生未満の場合はお電話をお切りください。}
本人確認.prompt={tts_g:診察を受けるご本人様からのお電話ですか？}
当院受診確認.prompt={tts_g:それでは、当院のご受診は、初めてですか？}
性別.prompt={tts_g:次に、性別をお伺いいたします。男性、もしくは女性でお答えください。}

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
