# IVR プロパティ — 大分赤十字病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:TODO_発話内容を記入}
END_時間外.prompt={tts_g:TODO_発話内容を記入}
END_聴取失敗.prompt={tts_g:TODO_発話内容を記入}
END_新規案内.prompt={tts_g:TODO_発話内容を記入}
END_当日案内.prompt={tts_g:TODO_発話内容を記入}
END_変更.prompt={tts_g:TODO_発話内容を記入}
END_キャンセル.prompt={tts_g:TODO_発話内容を記入}
END_確認.prompt={tts_g:TODO_発話内容を記入}
用件確認.prompt={tts_g:初めに、ご用件を、次の３つのうちの、いずれかでお話ください。「1、予約を変更する」。「2、予約をキャンセルする」。「3、予約を確認する」。なお、当日の予約変更、キャンセルは、代表電話へおかけ直しください。それでは、お話ください。}
内容確認.prompt={tts_g:お問い合わせの内容をお話ください。}
診療科.prompt={tts_g:まずは診療科をお話ください。わからない場合はわからないとお話ください。}
予約日.prompt={tts_g:次に現在の予約日を「7月1日」のように日付でお話ください。}
予約希望日.prompt={tts_g:次に、予約の希望日をお伺いいたします。ご都合の良い日付や時間、曜日をお話ください。}
キャンセル理由.prompt={tts_g:それでは、キャンセルの理由をお話ください。}

# サブフローTTS
相談_問合せ.prompt={tts_g:TODO_発話内容を記入}
相談_問合せループ.prompt={tts_g:TODO_発話内容を記入}
相談_FAQ失敗.prompt={tts_g:TODO_発話内容を記入}
終話_失敗.prompt={tts_g:TODO_発話内容を記入}
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
  - `END_非通知`
  - `END_時間外`
  - `END_聴取失敗`
  - `END_新規案内`
  - `END_当日案内`
  - `END_変更`
  - `END_キャンセル`
  - `END_確認`
  - `相談_問合せ`
  - `相談_問合せループ`
  - `相談_FAQ失敗`
  - `終話_失敗`
  - `患者_氏名`
  - `患者_生年月日`
  - `患者_連絡先`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
