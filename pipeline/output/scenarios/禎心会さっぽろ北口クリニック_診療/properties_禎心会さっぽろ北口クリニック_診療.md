# IVR プロパティ — 禎心会さっぽろ北口クリニック 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:申し訳ございませんが、ただいまの時間は受付時間外となっております。受付時間は、日曜祝日、年末年始を除く、月曜、火曜、水曜、金曜の8時25分から17時、木曜、土曜の8時25分から12時30分となっております。恐れ入りますが、受付時間内におかけなおしください。}
END_聴取失敗.prompt={tts_g:申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、代表電話へおかけ直しください。電話番号は011-709-1131です。繰り返します。電話番号は011-709-1131です。}
END_新規予約_携帯.prompt={tts_g:3診療日以内に、担当者から折り返し電話、もしくは、SMSにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_新規予約_固定.prompt={tts_g:3診療日以内に、担当者から折り返し、電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_予約確認.prompt={tts_g:予約に関するお問合せを受付いたしました。3診療日以内に、担当者からショートメール、もしくは折り返し電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_初診再診変更.prompt={tts_g:それでは、3診療日以内に、担当者からショートメール、もしくは折り返し電話にてご連絡いたします。折り返しのご連絡をもって予約が確定いたします。お電話ありがとうございました。それでは失礼いたします。}
END_予約キャンセル.prompt={tts_g:予約キャンセルの申し込みを受付いたしました。お電話ありがとうございました。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。禎心会さっぽろ北口クリニックの、予約専用電話です。ご希望をお伺いしますので、この後の質問にお答えください。}
用件聞き取り.prompt={tts_g:ご用件を、次の４つのうちの、いずれかでお話ください。「予約を取る」「予約を変更する」「予約をキャンセルする」「予約を確認する」、それでは、お話ください。}
予約案内.prompt={tts_g:ご予約のご案内をいたします。なお、直近のご予約には対応できない場合がございます。}
診療科聴取_新規.prompt={tts_g:希望される診療科、ドック、ワクチン接種などを一つ、お話ください。}
紹介状有無.prompt={tts_g:他の医療機関からの紹介状はお持ちですか？}
症状ヒアリング.prompt={tts_g:現在の症状を、簡単にお話ください。}
追加要望_新規.prompt={tts_g:複数名、複数診療科の予約や、予約希望日など、ご希望があればお話ください。なければ、特にありませんとお話ください。}
確認内容の聞き取り.prompt={tts_g:ご確認内容についてお伺いします。「次回の予約日時を教えて欲しい」など、内容を簡潔にお話ください。}
診療科聴取_変更キャンセル.prompt={tts_g:予約されている診療科、ドック、ワクチン接種などを一つ、もしくはわからないとお話ください。}
予約日聴取.prompt={tts_g:予約されている日付を「4月1日」のようにお話いただくか、「わからない」とお話ください。}
予約希望日聴取.prompt={tts_g:受診を希望されている日付や時期を、ご自由にお話ください。}

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
