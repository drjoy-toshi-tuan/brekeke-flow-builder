# IVR プロパティ — 海老名総合病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:TODO_発話内容を記入}
END_時間外.prompt={tts_g:TODO_発話内容を記入}
END_聴取失敗.prompt={tts_g:TODO_発話内容を記入}
END_3日以内.prompt={tts_g:TODO_発話内容を記入}
END_予約希望.prompt={tts_g:TODO_発話内容を記入}
END_予約不可.prompt={tts_g:TODO_発話内容を記入}
END_変更.prompt={tts_g:TODO_発話内容を記入}
END_キャンセル.prompt={tts_g:TODO_発話内容を記入}
END_確認.prompt={tts_g:TODO_発話内容を記入}
3日以内確認.prompt={tts_g:本日から2営業日後までのご予約に関するお問い合わせは、受付時間内に外来予約センターへおかけ直しください。3日以内の予約に関するお問い合わせですか？}
用件確認.prompt={tts_g:ご用件を、次の４つからお話ください。予約の変更は1を、キャンセルは2を、確認は3を、紹介状のある方・予約を取りたい方は4。}
内容確認.prompt={tts_g:それでは、ご確認内容についてお伺いします。次回の予約日時を教えて欲しいなど、内容を簡潔にお話ください。}
診療科_変更.prompt={tts_g:それでは、ご予約されている診療科をお話しください。}
予約日_変更.prompt={tts_g:それでは、現在の予約日を「4月1日」のように日付でお話しください。}
希望日有無_変更.prompt={tts_g:次の受診予定日はお決まりですか？はい決まっています、または、いいえ決まっていません、のようにお話ください。}
次回希望日_変更.prompt={tts_g:予約希望日を「4月1日」「4月中旬」のようにお話ください。}
診療科_キャンセル.prompt={tts_g:それでは、ご予約されている診療科をお話しください。}
予約日_キャンセル.prompt={tts_g:それでは、現在の予約日を「4月1日」のように日付でお話しください。}
希望日有無_キャンセル.prompt={tts_g:次の受診予定日はお決まりですか？はい決まっています、または、いいえ決まっていません、のようにお話ください。}
次回希望日_キャンセル.prompt={tts_g:予約希望日を「4月1日」「4月中旬」のようにお話ください。}

# サブフローTTS
患者_氏名.prompt={tts_g:TODO_発話内容を記入}
患者_生年月日.prompt={tts_g:TODO_発話内容を記入}
患者_連絡先.prompt={tts_g:TODO_発話内容を記入}
相談_問合せ.prompt={tts_g:TODO_発話内容を記入}
相談_問合せループ.prompt={tts_g:TODO_発話内容を記入}
相談_FAQ失敗.prompt={tts_g:TODO_発話内容を記入}
終話_失敗.prompt={tts_g:TODO_発話内容を記入}

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
  - `END_非通知`
  - `END_時間外`
  - `END_聴取失敗`
  - `END_3日以内`
  - `END_予約希望`
  - `END_予約不可`
  - `END_変更`
  - `END_キャンセル`
  - `END_確認`
  - `患者_氏名`
  - `患者_生年月日`
  - `患者_連絡先`
  - `相談_問合せ`
  - `相談_問合せループ`
  - `相談_FAQ失敗`
  - `終話_失敗`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
