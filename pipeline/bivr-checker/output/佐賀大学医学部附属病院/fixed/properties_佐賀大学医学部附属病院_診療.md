# IVR プロパティ — 佐賀大学医学部附属病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}
END_FAQ外.prompt={tts_g:お話いただきました内容は、AI電話では対応ができません。外来受付時間内に代表電話0952ー31ー6511へお問い合わせください。}
END_変更_携帯.prompt={tts_g:予約変更の申し込みを受付いたしました。この後送信するショートメールから、お申し込み内容のご確認をお願いします。3診療日以内に担当者からショートメールまたは、折り返し電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_変更_固定.prompt={tts_g:予約変更の申し込みを受付いたしました。3診療日以内に担当者から折り返し電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_キャンセル_携帯.prompt={tts_g:予約キャンセルの、申し込みを受付いたしました。確認事項がある場合のみ、担当者よりご連絡させていただきます。お電話ありがとうございました。それでは失礼いたします。}
END_キャンセル_固定.prompt={tts_g:予約キャンセルの、申し込みを受付いたしました。確認事項がある場合のみ、担当者よりご連絡させていただきます。お電話ありがとうございました。それでは失礼いたします。}
END_確認_携帯.prompt={tts_g:予約確認の申し込みを受付いたしました。この後送信するショートメールから、お申し込み内容のご確認をお願いします。3診療日以内に担当者からショートメールまたは、折り返し電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_確認_固定.prompt={tts_g:予約確認の申し込みを受付いたしました。3診療日以内に担当者から折り返し電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
用件確認.prompt={tts_g:ご用件を、次の3つのうちのいずれかでお話ください。予約変更、予約キャンセル、予約確認、それでは、お話ください。}
変更_アナウンス.prompt={tts_g:既にお持ちの予約を、本日の受診に変更することは、AI電話では受け付けておりませんので、ご了承ください。}
診療科.prompt={tts_g:次に、予約されていた診療科を、「診療科は○○です。」のようにお話ください。わからない場合は、わからない、とお話ください。}
診療科_心外脳外.prompt={tts_g:心臓血管外科ですか？脳神経外科ですか？}
診療科_ストーマ.prompt={tts_g:消化器外科ですか？泌尿器科ですか？}
確認内容.prompt={tts_g:ご確認内容について、お伺いします。次回の予約日時を教えて欲しい、など、内容を簡潔にお話ください。後ほどスタッフより確認内容について回答させていただきます。}
診療科2.prompt={tts_g:同じ日に予約されていた診療科があれば、「診療科は○○です。」のようにお話ください。ない場合は、ない、とお話ください。}
診療科2_心外脳外.prompt={tts_g:心臓血管外科ですか？脳神経外科ですか？}
診療科2_ストーマ.prompt={tts_g:消化器外科ですか？泌尿器科ですか？}
予約日.prompt={tts_g:次に、現在の予約日をお話ください。}
予約希望日時.prompt={tts_g:次に、予約希望日をお伺いいたします。ご都合の良い日時をお話しください。}
変更確認.prompt={tts_g:別の日にちに変更して、予約をしますか？はい、または、いいえ、でお答えください。}
キャンセル理由.prompt={tts_g:次に、キャンセル理由を、「他の病院に通院することになった」など簡潔にお話ください。}

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
amivoice.detection_flag=検出しない
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
