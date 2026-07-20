# IVR プロパティ — 川崎幸クリニック 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}
END_キャンセル完了.prompt={tts_g:かしこまりました。予約キャンセルの申し込みを受付いたしました。必要がある場合のみ、担当者から折り返し電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_確認完了.prompt={tts_g:申し込みを受付いたしました。この後、ショートメールが届きますので申し込み内容のご確認をお願いいたします。3診療日以内に担当者からショートメール、もしくは折り返し電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_内容聴取完了.prompt={tts_g:申し込みを受付いたしました。この後、ショートメールが届きますので申し込み内容のご確認をお願いいたします。3診療日以内に担当者からショートメール、もしくは折り返し電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_当日キャンセル.prompt={tts_g:申し訳ございません。本日の診療予約のキャンセルはAI電話では受け付けておりません。電話予約センターへおかけ直しください。電話番号は、044-511-2112です。電話番号は、044-511-2112です。電話番号は、044-511-2112です。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:こちらは、川崎幸クリニック。第二川崎幸クリニック診療予約専用AI電話です。こちらでは、診療予約の確認と、明日以降のキャンセルのみ対応しております。本日の診療に関することや、その他のご用件は電話予約センターへおかけ直しください。}
用件確認.prompt={tts_g:次に、ご用件を、「キャンセルする」「確認する」のいずれかでお話しください。それでは、お話しください。}
キャンセル_診療科.prompt={tts_g:キャンセルを希望される診療科を、診療科は内科です、のようにお話ください。分からない場合は、分からないとお話ください。}
現在の予約日.prompt={tts_g:現在の予約日を「4月1日」のように日付でお話ください。わからない場合は「わからない」のようにお話ください。}
確認_診療科.prompt={tts_g:確認する診療科を、診療科は内科です、のようにお話ください。分からない場合は、分からないとお話ください。}
確認内容.prompt={tts_g:確認内容をお話ください。}
内容聴取_不明時.prompt={tts_g:申し訳ございません。AIがうまく聞き取りできませんでした。お伝えしたい内容を自由にお話しください。}

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
