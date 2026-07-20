# IVR プロパティ — 秋田県立循環器・脳脊髄センター 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_救急科案内.prompt={tts_g:TODO_発話内容を記入}
END_変更_終話1.prompt={tts_g:TODO_発話内容を記入}
END_キャンセル_終話1.prompt={tts_g:TODO_発話内容を記入}
END_確認_終話1.prompt={tts_g:TODO_発話内容を記入}
END_変更_終話2.prompt={tts_g:TODO_発話内容を記入}
END_キャンセル_終話2.prompt={tts_g:TODO_発話内容を記入}
END_確認_終話2.prompt={tts_g:TODO_発話内容を記入}
用件確認.prompt={tts_g:ご用件を、次の3つのうちの、いずれかでお話ください。1、予約変更。2、予約キャンセル。3、予約日時の確認。それでは、お話ください。}
診療科.prompt={tts_g:予約票に記載されている診療科をお話しください。どうぞ。}
脳神経特定_1.prompt={tts_g:脳神経外科ですか？脳神経内科ですか？}
診療科2.prompt={tts_g:ほかに、ご予約を変更もしくはキャンセルされる診療科があればお話ください。無い場合は、ない、とお話しください。どうぞ。}
脳神経特定_2.prompt={tts_g:脳神経外科ですか？脳神経内科ですか？}
検査.prompt={tts_g:検査を予定されている方は、検査名をお話しください。検査が無い場合や分からない場合は、ありません、や、分かりません、のようにお話しください。どうぞ。}
現在予約日.prompt={tts_g:現在の予約日を、4月1日、のように日付でお話ください。分からない場合には分からない、とお答えください。どうぞ。}
変更希望日.prompt={tts_g:ご希望の変更日を、4月1日、のように日付でお話ください。どうぞ。}
残薬確認.prompt={tts_g:当院で処方されている方は、希望の予約変更日までのお薬が足りますか？はい大丈夫です。いいえ、足りません。いずれかでお話ください。}
キャンセル理由.prompt={tts_g:次に、予約取り消しの理由を、次の4つのうちからお話ください。1、インフルエンザ、コロナ等、感染症のため。2、体調変化のため。3、他院へ入院中のため。4、都合がつかないため。それではお話ください。}

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
  - `END_救急科案内`
  - `END_変更_終話1`
  - `END_キャンセル_終話1`
  - `END_確認_終話1`
  - `END_変更_終話2`
  - `END_キャンセル_終話2`
  - `END_確認_終話2`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
