# IVR プロパティ — 鎌ケ谷総合病院 診療_20260416

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:TODO_発話内容を記入}
END_通常_携帯.prompt={tts_g:TODO_発話内容を記入}
END_通常_固定.prompt={tts_g:TODO_発話内容を記入}
END_歯科口腔外科.prompt={tts_g:TODO_発話内容を記入}
END_健康管理センター.prompt={tts_g:TODO_発話内容を記入}
END_インフルエンザワクチン.prompt={tts_g:TODO_発話内容を記入}
END_コロナワクチン.prompt={tts_g:TODO_発話内容を記入}
END_対応外診療科案内.prompt={tts_g:TODO_発話内容を記入}
END_当日予約案内.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。鎌ケ谷総合病院の、予約専用、AI電話です。}
用件確認.prompt={tts_g:ご用件をお話しください。予約は1、変更は2、キャンセルは3、その他のお問い合わせは4を押してください。}
受診歴確認.prompt={tts_g:当院でのご受診は初めてですか。初めての方は1、以前受診されたことがある方は2を押してください。}
紹介状確認.prompt={tts_g:初診のご予約ですね。他の医療機関からの紹介状はお持ちですか。お持ちの方は1、お持ちでない方は2を押してください。}
選定療養費案内.prompt={tts_g:他の医療機関からの紹介状をお持ちでない患者さんにつきましては、通常の診療費とは別に、初診時選定療養費として、2200円を全額自己負担いただいております。予めご了承ください。}
診療科.prompt={tts_g:受診を希望される診療科をお話しください。}
予約日_変更.prompt={tts_g:次に、予約票に記載されている予約日を、5月1日のように日付でお話しください。}
予約希望日_変更.prompt={tts_g:次に、予約希望日をお伺いいたします。ご都合の良い日付や曜日をお話しください。}
予約希望日復唱_変更.prompt={tts_g:承りました。日曜・祝日は休診の診療科もございます。こちらのお電話では予約は確定しておりませんので、担当者からの折返し連絡をお待ちください。}
理由_変更.prompt={tts_g:差し支えなければご予約変更の理由をお話しください。}
予約日_キャンセル.prompt={tts_g:次に、予約票に記載されている予約日を、5月1日のように日付でお話しください。}
理由_キャンセル.prompt={tts_g:差し支えなければご予約キャンセルの理由をお話しください。}
内容確認.prompt={tts_g:ご確認内容についてお伺いします。次回の予約日時を教えてほしい、など、内容を簡潔にお話しください。}

# サブフローTTS
相談_問合せ.prompt={tts_g:TODO_発話内容を記入}
相談_問合せループ.prompt={tts_g:TODO_発話内容を記入}
相談_FAQ失敗.prompt={tts_g:TODO_発話内容を記入}
終話_失敗.prompt={tts_g:TODO_発話内容を記入}
患者_診察券番号.prompt={tts_g:TODO_発話内容を記入}
患者_氏名.prompt={tts_g:TODO_発話内容を記入}
患者_生年月日.prompt={tts_g:TODO_発話内容を記入}
患者_連絡先.prompt={tts_g:TODO_発話内容を記入}

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
- [ ] 以下のモジュールにアナウンス文言を記入する:
  - `END_聴取失敗`
  - `END_通常_携帯`
  - `END_通常_固定`
  - `END_歯科口腔外科`
  - `END_健康管理センター`
  - `END_インフルエンザワクチン`
  - `END_コロナワクチン`
  - `END_対応外診療科案内`
  - `END_当日予約案内`
  - `相談_問合せ`
  - `相談_問合せループ`
  - `相談_FAQ失敗`
  - `終話_失敗`
  - `患者_診察券番号`
  - `患者_氏名`
  - `患者_生年月日`
  - `患者_連絡先`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
