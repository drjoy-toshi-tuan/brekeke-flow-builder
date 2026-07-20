# IVR プロパティ — 札幌禎心会病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:申し訳ございませんが、ただいまの時間は受付時間外となっております。受付時間は、日曜祝日、年末年始を除く、月曜日から金曜日の9時から17時、土曜日の9時から12時となっております。恐れ入りますが、受付時間内におかけなおしください。}
END_聴取失敗.prompt={tts_g:申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、代表電話へおかけ直しください。電話番号は011-712-1131です。繰り返します。電話番号は011-712-1131です。}
END_受付完了_携帯.prompt={tts_g:ご予約の申し込みを受付いたしました。3診療日以内に、担当者から折り返し電話、もしくは、SMSにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_受付完了_固定.prompt={tts_g:ご予約の申し込みを受付いたしました。3診療日以内に、担当者から折り返し、電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_当日代表案内.prompt={tts_g:申し訳ございません。当日のご予約に関しては、こちらのAI電話ではお受けできません。恐れ入りますが、代表電話までおかけなおしください。電話番号は011-712-1131です。繰り返します。電話番号は011-712-1131です。}
END_診療科代表案内.prompt={tts_g:<% clinicalDepartment %>はAI電話では受付できません。恐れ入りますが、代表電話までおかけ直しください。電話番号は011-712-1131です。繰り返します。電話番号は011-712-1131です。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。札幌禎心会病院の、予約専用、AI電話です。}
用件_予約or情報提供書.prompt={tts_g:ご用件を、次の2つのうちの、いずれかでお話ください。「予約について」。「情報提供書の申し込みについて」。それでは、お話ください。}
当日受診確認.prompt={tts_g:まず初めにお伺いします。本日の予約に関する内容ですか？はい、または、いいえでお答えください。}
用件_予約系.prompt={tts_g:ご用件を、次の4つのうちの、いずれかでお話ください。「診察の予約を取る」「予約を変更する」「予約をキャンセルする」「予約を確認する」、それでは、お話ください。}
新患確認.prompt={tts_g:当院でのご受診は初めてですか？はい、または、いいえでお答えください。}
紹介状有無.prompt={tts_g:他の医療機関からの紹介状はお持ちですか？「はい持っています」、または、「いいえ持っていません」のように少し長めの言葉でお答えください。}
選定療養費案内.prompt={tts_g:他の医療機関からの紹介状をお持ちでない患者さんにつきましては、通常の診療費とは別に、初診時選定療養費として、1,100円を全額自己負担いただいております。予めご了承ください。}
診療科.prompt={tts_g:受診を希望される診療科をお話ください。予約変更や予約キャンセルの場合は、予約票に記載されている診療科をお話ください。}
予約日.prompt={tts_g:予約票に記載されている予約日を「4月1日」のように日付でおっしゃってください。なお、AIが予約日を正しく認識しない場合は、ダイヤルプッシュでの入力も可能です。月と日にちの4桁の数字を入力してください。}
確認内容.prompt={tts_g:ご確認内容についてお伺いします。「次回の予約日時を教えて欲しい」など、内容を簡潔におっしゃってください。}
情報提供書_医療機関名.prompt={tts_g:どこの医療機関へのお手紙ですか？}
情報提供書_診療科宛先.prompt={tts_g:どの診療科宛になりますか？}

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
