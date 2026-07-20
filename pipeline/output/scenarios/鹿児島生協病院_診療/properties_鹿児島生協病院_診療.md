# IVR プロパティ — 鹿児島生協病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}
END_初診受付不可.prompt={tts_g:恐れ入りますが、初めて受診される方のご予約はお受けできません。大変申し訳ございませんが予約なしでのご来院の上、受診をお願いします。鹿児島生協病院の眼科外来は午前中は月曜日から土曜日までの8時30分から11時30分、午後は月曜日と木曜日の13時45分から16時までの受付となっております。お電話ありがとうございました。それでは失礼いたします。}
END_受付完了_再診.prompt={tts_g:再診予約の申し込みを受付いたしました。3診療日以内に担当者から折り返し電話、もしくは、SMSにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_受付完了_変更.prompt={tts_g:予約変更の申し込みを受付いたしました。3診療日以内に担当者から折り返し電話、もしくは、SMSにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_受付完了_確認.prompt={tts_g:予約確認の申し込みを受付いたしました。3診療日以内に担当者から折り返し電話、もしくは、SMSにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_キャンセル受付完了.prompt={tts_g:予約キャンセルの申し込みを受付いたしました。3診療日以内に担当者から折り返し電話、もしくは、SMSにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。鹿児島生協病院の眼科専用、AI電話です。再診予約、予約変更、キャンセル、予約確認を承ります。なお当日の予約に関するお問い合わせは、<speak type="telephone" breakc="300ms">099-267-1455</speak>へおかけ直しください。
}
受診歴確認.prompt={tts_g:まず初めに、鹿児島生協病院の眼科を受診したことはありますか？はい、または、いいえ、でお答えください。}
用件聴取.prompt={tts_g:ご用件を、次の4つのうちの、いずれかでお話ください。「再診予約をする」、「予約日を変更する」、「予約をキャンセルする」、「予約の確認」。それでは、お話ください。}
予約変更_希望日聴取.prompt={tts_g:ご希望される予約日時を、「10月10日の午前9時」のように日付と時間をおっしゃってください。また、複数ある場合は続けて自由にお話ください。}
確認_問い合わせ内容.prompt={tts_g:確認したい内容がございましたら、内容を簡潔におっしゃってください。}
キャンセル_次回予約有無.prompt={tts_g:次回の予約希望はございますか？ございましたらご希望時期をお話ください。ない場合は「ありません」とおっしゃってください。}
キャンセル_予約希望日.prompt={tts_g:ご希望される予約日時を、「10月10日の午前9時」のように日付と時間をおっしゃってください。また、複数ある場合は続けて自由にお話ください。}
最終確認_追加問合せ.prompt={tts_g:確認したい内容がございましたら、内容を簡潔におっしゃってください。}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}

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
