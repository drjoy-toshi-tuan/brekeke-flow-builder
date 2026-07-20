# IVR プロパティ — 東京北医療センター 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:TODO_発話内容を記入}
END_時間外.prompt={tts_g:TODO_発話内容を記入}
END_聴取失敗.prompt={tts_g:TODO_発話内容を記入}
END_地域連携室案内.prompt={tts_g:TODO_発話内容を記入}
END_予約不可案内.prompt={tts_g:TODO_発話内容を記入}
END_通常完了.prompt={tts_g:TODO_発話内容を記入}
用件確認.prompt={tts_g:ご用件を次の4つの内からお話しください。「予約」、「予約変更」、「キャンセル」、「予約確認」。それではどうぞ。}
紹介状確認.prompt={tts_g:紹介状はお持ちでしょうか。「はい、持っています。」「いいえ、持っていません」のようにお話しください。}
診療科.prompt={tts_g:診療科をお話しください。}
症状聴取.prompt={tts_g:今回の症状を簡潔にお話しください。}
予約希望時期.prompt={tts_g:本日より3営業日以降の日程で受診を希望されるお日にちをお話しください。それではどうぞ。}
予約日.prompt={tts_g:現在の予約日をお話しください。それではどうぞ。}
残薬確認.prompt={tts_g:変更を希望されるお日にちまでの残薬はございますでしょうか。「はい、あります」や「いいえ、ありません」のようにお答えください。飲んでいない方は飲んでいないとお話しください。}
予約希望時期_変更.prompt={tts_g:本日より3営業日以降の日程で受診を希望されるお日にちをお話しください。それではどうぞ。}
変更理由.prompt={tts_g:変更を希望される理由を簡潔にお話しください。}
キャンセル理由.prompt={tts_g:キャンセルを希望される理由をお話しください。}
確認内容.prompt={tts_g:確認をしたい内容に関して、「次回の予約日を確認したい」などと簡潔にお話しください。それではどうぞ。}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
患者_診察券番号.prompt={tts_g:診察券番号をお伝えください。}
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
  - `END_聴取失敗`
  - `END_地域連携室案内`
  - `END_予約不可案内`
  - `END_通常完了`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
