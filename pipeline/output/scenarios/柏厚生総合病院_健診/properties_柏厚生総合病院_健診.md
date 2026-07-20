# IVR プロパティ — 柏厚生総合病院 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:TODO_発話内容を記入}
END_時間外.prompt={tts_g:TODO_発話内容を記入}
END_聴取失敗.prompt={tts_g:TODO_発話内容を記入}
END_受付完了.prompt={tts_g:ご要望を承りました。翌営業日に、担当者から折り返し電話、もしくは、ショートメールにてご連絡いたします。担当者からのご連絡後に確定となりますのでしばらくお待ちくださいませ。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。柏厚生総合病院健診センターの予約専用AI電話です。}
用件確認.prompt={tts_g:ご用件を次の4つの内からお話しください。「予約」、「予約変更」、「キャンセル」、「その他問い合わせ」。それではどうぞ。}
予約_受診内容.prompt={tts_g:受診を希望される内容をお話しください。それではどうぞ。}
予約_オプション.prompt={tts_g:オプション検査を追加される方は内容をお話しください。希望されない方は「希望しない」とお話しください。それではどうぞ。}
予約_健康保険組合名.prompt={tts_g:健康保険組合などからの補助がある場合は、組合名をお話しください。わからない場合は「わからない」とお話しください。}
予約_受診希望日.prompt={tts_g:本日より2営業日以降の日程で、受診を希望されるお日にちをお話しください。それではどうぞ。}
変更_現在の受診内容.prompt={tts_g:現在予約されている受診内容を、お話しください。それではどうぞ。}
変更_現在の予約日.prompt={tts_g:現在の予約日をお話しください。それではどうぞ。}
変更_変更希望内容.prompt={tts_g:変更を希望される内容に関して、簡潔にお話しください。それではどうぞ。}
キャンセル_現在の受診内容.prompt={tts_g:現在予約されている受診内容を、お話しください。それではどうぞ。}
キャンセル_現在の予約日.prompt={tts_g:現在の予約日をお話しください。それではどうぞ。}
その他_問い合わせ内容.prompt={tts_g:確認をしたい内容に関して、簡潔にお話しください。それではどうぞ。}

# サブフローTTS
相談_問合せ.prompt={tts_g:ご質問内容をお話しください。}
相談_問合せループ.prompt={tts_g:他にご質問はございますか。ご質問がなければ「ありません」とお伝えください。}
相談_FAQ失敗.prompt={tts_g:申し訳ございません。お調べすることができませんでした。}
終話_失敗.prompt={tts_g:TODO_発話内容を記入}
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
  - `END_聴取失敗`
  - `終話_失敗`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
