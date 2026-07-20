# IVR プロパティ — 沖縄県立南部医療センター・こども医療センター 地域連携

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間は、日曜祝日・年末年始を除く、月曜日から土曜日の8時30分から12時です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:大変申し訳ございません。ご回答を聞き取ることができませんでした。恐れ入りますが、代表電話番号へおかけなおしください。受付時間は、日曜祝日、年末年始を除く、月曜日から土曜日の8時30分から12時です。お電話番号をご案内いたしますので、メモをご準備ください。098-888-0123。もう一度お伝えします。098-888-0123。最後にもう一度お伝えします。098-888-0123。お電話ありがとうございました。それでは失礼いたします。}
END_緊急対応不可.prompt={tts_g:当日の緊急対応はAI電話では対応できません。恐れ入りますが、代表電話番号へおかけなおしください。受付時間は、日曜祝日、年末年始を除く、月曜日から土曜日の8時30分から12時です。お電話番号をご案内いたしますので、メモをご準備ください。098-888-0123。もう一度お伝えします。098-888-0123。最後にもう一度お伝えします。098-888-0123。お電話ありがとうございました。それでは失礼いたします。}
END_整形外科案内.prompt={tts_g:申し訳ございません。整形外科は、AI電話では承ることができません。恐れ入りますが、代表電話番号へおかけなおしください。受付時間は、日曜祝日、年末年始を除く、月曜日から土曜日の8時30分から12時です。お電話番号をご案内いたしますので、メモをご準備ください。098-888-0123。もう一度お伝えします。098-888-0123。最後にもう一度お伝えします。098-888-0123。お電話ありがとうございました。それでは失礼いたします。}
END_終話1.prompt={tts_g:かしこまりました。確認事項がある場合のみ、担当者より折り返しご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_終話2.prompt={tts_g:かしこまりました。内容を確認のうえ、5診療日以内にスタッフからご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。沖縄県立南部医療センター・こども医療センター、地域連携室専用AI電話です。本件は、緊急対応が必要でしょうか。はい、いいえでお答えください。どうぞ。}
緊急対応確認.prompt={tts_g:本件は、緊急対応が必要でしょうか。はい、いいえでお答えください。どうぞ。}
医療機関名聴取.prompt={tts_g:お電話をいただいている方の、医療機関名をお話しください。どうぞ。}
入電者氏名聴取.prompt={tts_g:次に、ご担当者様の氏名を「名前は、南部 太郎です」のようにお話しください。どうぞ。}
用件.prompt={tts_g:ご用件を次の4つのうちのいずれかでお話ください。1番、外来入院申込みについて。2番、情報提供依頼。3番、入退院支援室へのお問い合わせ。4番、その他お問合せ。それではお話ください。どうぞ。}
FAX送信時期.prompt={tts_g:FAXを送信した日付と時間帯をお話しください。どうぞ。}
診療科.prompt={tts_g:まず、該当の診療科をお話しください。どうぞ。}
返信期限.prompt={tts_g:本件について、ご回答期限の日時を教えてください。どうぞ。}
担当者名聴取.prompt={tts_g:当院の担当者がお分かりの場合は担当者名をお話しください。わからない場合は「わからない」とお話しください。}
問い合わせ内容.prompt={tts_g:本件のお問い合わせ内容を、簡潔にお話しください。話し終わりましたら、「以上です。」とおっしゃってください。どうぞ。}

# サブフローTTS
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
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
