# IVR プロパティ — 小山記念病院 薬剤部

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:TODO_発話内容を記入}
END_時間外.prompt={tts_g:TODO_発話内容を記入}
END_聴取失敗.prompt={tts_g:TODO_発話内容を記入}
END_Z1.prompt={tts_g:かしこまりました。お掛けいただいた番号に折り返しいたします。お電話ありがとうございました。}
END_Z3.prompt={tts_g:かしこまりました。お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:小山記念病院、薬剤部です。}
薬局名聴取.prompt={tts_g:薬局名をお話ください。}
用件確認.prompt={tts_g:ご用件を「疑義照会」「報告」「その他問合せ」、いずれかでお話ください。}
担当者名.prompt={tts_g:担当者名をお話ください。}
患者ID.prompt={tts_g:患者さんのIDをお話ください。}
患者名.prompt={tts_g:患者名をフルネームでお話ください。}
診療科.prompt={tts_g:診療科をお話ください。}
疑義内容.prompt={tts_g:疑義の内容をお話ください。}
報告内容.prompt={tts_g:報告の内容をお話ください。}
問合せ内容.prompt={tts_g:問合せ内容をお話ください。}
折返有無.prompt={tts_g:当院から折り返しは必要ですか？}

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

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
