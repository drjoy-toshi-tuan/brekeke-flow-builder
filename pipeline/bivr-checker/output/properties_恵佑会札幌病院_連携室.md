# IVR プロパティ — 恵佑会札幌病院 連携室

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_代表案内.prompt={tts_g:TODO_発話内容を記入}
END_歯科転送.prompt={tts_g:TODO_発話内容を記入}
END_一般_携帯.prompt={tts_g:TODO_発話内容を記入}
END_一般_固定.prompt={tts_g:TODO_発話内容を記入}
END_キャンセル_携帯.prompt={tts_g:TODO_発話内容を記入}
END_キャンセル_固定.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。恵佑会札幌病院の、診察予約申し込み電話です。テレビの音や周囲の騒音がない静かなところでお話しください。}
当日翌日確認.prompt={tts_g:こちらのお電話は明日以降の予約についてのお問い合わせでしょうか？明日以降の場合は「はい」、本日の場合は「いいえ」でお話しください。}
用件確認.prompt={tts_g:次の４つのうち、いずれかの番号をお話しください。「予約を申し込む方は、１」、「予約を変更する方は、２」、「予約をキャンセルする方は、3」、「その他お問い合わせの方は、4」、または{tts_g:<dtmf digit="1"/>}}
受診歴確認.prompt={tts_g:新規予約をご希望ですか？2回目以降の診察予約ですか？}
紹介状確認.prompt={tts_g:紹介状はお持ちでしょうか？}
紹介時診療科.prompt={tts_g:紹介状の封筒に記載されている診療科名を「診療科は消化器外科です」のようにお話しください。わからない場合は「わからない」とお話しください。}
診療科_初診.prompt={tts_g:診察を希望する診療科を「診療科は消化器外科です」のようにお話しください。}
診療科_再診.prompt={tts_g:診察を希望する診療科を「診療科は消化器外科です」のようにお話しください。}
予約希望日.prompt={tts_g:次に、予約希望日をお伺いいたします。予約日は3診療日以内の折り返し連絡にて確定いたします。それではご都合の良い日付や曜日をお話しください。}
現在の予約日_変更.prompt={tts_g:現在の予約日をお話しください。}
変更_予約希望日.prompt={tts_g:次に、予約希望日をお伺いいたします。予約日は3診療日以内の折り返し連絡にて確定いたします。それではご都合の良い日付や曜日をお話しください。}
現在の予約日_キャンセル.prompt={tts_g:現在の予約日をお話しください。}
キャンセル理由.prompt={tts_g:続いて、キャンセルの理由をお話しください。}
問い合わせ内容.prompt={tts_g:お問い合わせの内容をお話しください。}
その他確認事項.prompt={tts_g:そのほかに何かお問い合わせは有りませんか？}

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
  - `END_代表案内`
  - `END_歯科転送`
  - `END_一般_携帯`
  - `END_一般_固定`
  - `END_キャンセル_携帯`
  - `END_キャンセル_固定`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
