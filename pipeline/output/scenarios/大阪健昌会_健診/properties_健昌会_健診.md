# IVR プロパティ — 健昌会 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:申し訳ございませんが、ただいまの時間は受付時間外となっております。受付時間は、日曜、祝日、年末年始を除く、月曜日から金曜日は、8時から16時30分、土曜日は営業日のみ、8時30分から12時となっております。恐れ入りますが、受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:大変申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、当施設の代表電話までおかけ直しいただき、ナビダイヤルの 5 番へお進みください。お電話ありがとうございました。}
END_受診票なし.prompt={tts_g:恐れ入りますが、お手元に健康診断受診のお知らせが到着後、もう一度お電話ください。お電話ありがとうございました。}
END_予約キャンセル.prompt={tts_g:ご予約のキャンセルを承りました。お電話ありがとうございました。}
END_変更受付_携帯.prompt={tts_g:変更の申し込みを承りました。内容を確認の上、担当者よりショートメールにてご連絡いたします。お電話ありがとうございました。}
END_変更受付_携帯以外.prompt={tts_g:変更の申し込みを承りました。内容を確認の上、担当者よりご連絡いたします。お電話ありがとうございました。}
END_問合せ_携帯.prompt={tts_g:お問い合わせの内容を承りました。内容を確認の上、担当者よりショートメールにてご連絡いたします。お電話ありがとうございました。}
END_問合せ_携帯以外.prompt={tts_g:お問い合わせの内容を承りました。内容を確認の上、担当者よりご連絡いたします。お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。大阪健昌会の、予約変更専用、AI電話です。こちらの電話では、予約変更のみの受付となります。新規のご予約については、代表電話におかけ直しください。}
問合せ先施設名.prompt={tts_g:問合せをしたい施設名を、1 うめだ、2 近畿、3 淀川、4 福島、のいずれかをプッシュダイヤルでご入力ください。}
用件確認.prompt={tts_g:ご用件を、次の3つのうちの、いずれかをプッシュダイヤルでご入力ください。1 予約日時の変更、2 予約のキャンセル、3 その他、予約変更に関するお問い合わせ。}
受診票有無確認.prompt={tts_g:お手元に、当会の健康診断受診のお知らせはございますか？1 はい、2 いいえ、をプッシュダイヤルでご入力ください。}
現在の予約日.prompt={tts_g:現在の予約日を、プッシュダイヤルで月と日にちの 4 桁の数字をご入力ください。}
変更希望日.prompt={tts_g:変更希望日を、プッシュダイヤルで月と日にちの 4 桁の数字をご入力ください。なお、毎週木曜日はレディースデーです。}
希望時間帯.prompt={tts_g:ご希望の時間帯を、次のいずれかの数字でプッシュダイヤルをご入力ください。1 8時～9時台、2 10時～11時台、3 12時台以降の午後。}
オプション追加変更有無.prompt={tts_g:オプション追加、変更希望はございますか？1 はい、2 いいえ、をプッシュダイヤルでご入力ください。}
変更内容.prompt={tts_g:ご希望の検査名をお話ください。}
予約日確定有無.prompt={tts_g:ご予約の日時は、施設より連絡があり、確定していますでしょうか？1 はい、2 いいえ、をプッシュダイヤルでご入力ください。}
問合せ内容.prompt={tts_g:予約変更に関する内容を、お話ください。また、予約変更以外の内容は、恐れ入りますが、各施設の代表電話番号の 2 番へおかけ直しください。}

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
