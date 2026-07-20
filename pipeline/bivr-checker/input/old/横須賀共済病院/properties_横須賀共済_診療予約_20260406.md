# IVR プロパティ — 横須賀共済 診療予約_20260406

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:TODO_発話内容を記入}
END_時間外.prompt={tts_g:TODO_発話内容を記入}
END_上限エラー.prompt={tts_g:TODO_発話内容を記入}
END_代表案内_当日.prompt={tts_g:TODO_発話内容を記入}
END_代表案内_新規予約.prompt={tts_g:TODO_発話内容を記入}
END_受付完了.prompt={tts_g:TODO_発話内容を記入}
END_受付完了_SMS無し.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。横須賀共済病院の予約専用AI電話です。 このお電話では新規予約は受け付けておりません。 また、当院からの折り返し連絡で確定します。 それではお伺いします。
}
当日確認.prompt={tts_g:本日を含めて3診療日以内の予約のご用件ですか。 「はい、そうです」または「いいえ、違います」とお話しください。
}
用件.prompt={tts_g:ご用件をお伺いします。予約の変更、キャンセル、確認、のいずれかでお話しください。}
診療科1.prompt={tts_g:受診される診療科をお伺いします。診療科名をお話しください。}
診療科2.prompt={tts_g:今回のご用件に関係する診療科が、同じ日にある場合は診療科名をお話しください。ない場合は「ありません」とお話しください。}
予約日.prompt={tts_g:現在の予約日をお話しください。わからない場合は「わからない」とお話しください。}
内容.prompt={tts_g:お問合せ内容を「予約日時の確認」などのようにお話しください。}

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
- [ ] 以下のモジュールにアナウンス文言を記入する:
  - `END_非通知`
  - `END_時間外`
  - `END_上限エラー`
  - `END_代表案内_当日`
  - `END_代表案内_新規予約`
  - `END_受付完了`
  - `END_受付完了_SMS無し`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
