# IVR プロパティ — 沖縄県立中部病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_通院中以外受付不可.prompt={tts_g:TODO_発話内容を記入}
END_取り直し受付不可.prompt={tts_g:TODO_発話内容を記入}
END_再診予約の変更.prompt={tts_g:TODO_発話内容を記入}
END_予約日の確認.prompt={tts_g:TODO_発話内容を記入}
END_予約のキャンセル.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。沖縄県立中部病院の予約専用AI電話です。}
通院確認.prompt={tts_g:現在、当病院に通院中ですか？「はい、通院中です」。「いいえ、通院中ではありません」、のようにお答えください。どうぞ。}
本人確認.prompt={tts_g:現在お電話いただいている方についてお伺いします。受診されるご本人様の場合は『本人』とお答えください。ご本人様以外の場合は、お名前とご関係をお話しください。}
診療科.prompt={tts_g:診療科をお話しください。わからない場合はわからないとお話しください。}
用件確認.prompt={tts_g:ご用件を「再診予約の変更」、「予約日の確認」、「予約のキャンセル」、「予約の取り直し」の中からお選びください。それではどうぞ。}
現在の予約日_変更.prompt={tts_g:次に、現在の予約日をお話しください。}
理由_変更.prompt={tts_g:今回の変更の理由をお話しください。どうぞ。}
予約希望日_変更.prompt={tts_g:次に、ご変更したい予約希望日をお話しください。どうぞ。}
都合悪い日.prompt={tts_g:予約日に関して、ご来院ができないお日にちがあればお話しください。 ない場合は、「ないです」とお話しください。}
その他共有事項.prompt={tts_g:その他、「お薬が足りない」など、事前にお伝えしたいことがあればお話しください。なければ「ありません」とお話しください。どうぞ。}
確認事項.prompt={tts_g:ご確認内容についてお伺いします。「次回の予約日時を教えて欲しい」など、内容を簡潔にお話しください。}
理由_キャンセル.prompt={tts_g:今回のキャンセルの理由をお話しください。どうぞ。}
現在の予約日_キャンセル.prompt={tts_g:次に、現在の予約日をお話しください。}
キャンセル時案内.prompt={tts_g:予約をキャンセルされた場合、次回のご予約時に紹介状が必要となります。再度受診する予定がある方は、予約キャンセルではなく予約変更をおすすめいたします。予約変更をご希望の方は1を、完全キャンセルをご希望の方は2を押してください。}
前回の予約日.prompt={tts_g:前回の予約日は、本日から3か月以内の予約日でしょうか？「はい、そうです」「いいえ、違います」のようにお答えください。}

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
- [ ] 以下のモジュールにアナウンス文言を記入する:
  - `END_通院中以外受付不可`
  - `END_取り直し受付不可`
  - `END_再診予約の変更`
  - `END_予約日の確認`
  - `END_予約のキャンセル`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
