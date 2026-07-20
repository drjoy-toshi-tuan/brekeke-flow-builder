# IVR プロパティ — テスト 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
受付完了.prompt={tts_g:TODO_発話内容を記入}
聴取失敗.prompt={tts_g:TODO_発話内容を記入}
非通知.prompt={tts_g:TODO_発話内容を記入}
時間外.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。テスト施設です。STTテストモードです。}
STT方式選択.prompt={tts_g:テストモードを選択してください。通常の場合は1を、Sonioxの場合は2を押してください。}
氏名_通常.prompt={tts_g:お名前をフルネームでお伝えください。}
生年月日_通常.prompt={tts_g:生年月日を西暦でお伝えください。}
電話番号_通常.prompt={tts_g:ご連絡先の電話番号をお伝えください。}
診療科_通常.prompt={tts_g:ご希望の診療科をお話しください。}
希望予約日_通常.prompt={tts_g:ご希望の予約日をお話しください。}
主訴_通常.prompt={tts_g:症状やご相談内容をお話しください。}

# wait
冒頭.wait=2000

# 施設固有（要編集）
office_id=TODO_施設のoffice_idを入力

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
  - `受付完了`
  - `聴取失敗`
  - `非通知`
  - `時間外`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
