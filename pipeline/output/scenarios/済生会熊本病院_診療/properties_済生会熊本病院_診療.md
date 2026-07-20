# IVR プロパティ — 済生会熊本病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:申し訳ございません。電話番号が非通知設定の場合、AI電話では受付できません。先頭に数字の、1、8、6、を付けておかけなおしください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:ただいまの時間は受付時間外となります。受付時間は平日、8時30分から17時となっております。恐れ入りますが、受付時間内にお掛け直し下さい。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、平日、8時30分から17時に、予約確認センターへお掛け直し下さい。電話番号は、096-351-8051です。お電話ありがとうございました。}
END_確認.prompt={tts_g:予約確認の申し込みを受付いたしました。土日祝日を除く翌日までに、担当者から折り返し電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_変更.prompt={tts_g:予約変更の申し込みを受付いたしました。土日祝日を除く翌日までに、担当者から折り返し電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_キャンセル.prompt={tts_g:予約キャンセルの申し込みを受付いたしました。確認事項がある場合は、担当者よりお電話させていただきますので、ご了承ください。土日祝日を除く翌日までに、担当者から折り返し電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_その他.prompt={tts_g:その他お問い合わせ、の申し込みを受付いたしました。土日祝日を除く翌日までに、担当者から折り返し電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。済生会熊本病院の予約確認センターです。ここからはAI電話がご案内します。途中で電話を切った場合でも、担当者よりご連絡いたしますので、ご安心ください。初めに、}
氏名_次へ.prompt={tts_g:ありがとうございます。次に、}
診察券_次へ.prompt={tts_g:それでは、}
生年月日_次へ.prompt={tts_g:かしこまりました。次に、}
用件_前置き.prompt={tts_g:それでは、}
用件確認.prompt={tts_g:ご用件を、次の4つのうちのいずれかでお話ください。「予約を確認する」、「予約を変更する」、「予約をキャンセルする」、「その他お問い合せ」、それでは、お話ください。}
確認内容.prompt={tts_g:ご用件の内容について、簡潔にお話しください。}
現在の予約日_変更.prompt={tts_g:現在の予約日を「4月1日」のように日付でお話ください。わからない場合は「わからない」のようにお話下さい。}
希望日.prompt={tts_g:予約希望時期を「来週」、や、「今月下旬」、のようにおっしゃってください。}
現在の予約日_キャンセル.prompt={tts_g:現在の予約日を「4月1日」のように日付でお話ください。わからない場合は「わからない」のようにお話下さい。}
キャンセル理由.prompt={tts_g:キャンセル理由をおっしゃってください。}
完了_前置き.prompt={tts_g:ありがとうございます。}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_診察券番号.prompt={tts_g:診察券番号をお伝えください。}
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
