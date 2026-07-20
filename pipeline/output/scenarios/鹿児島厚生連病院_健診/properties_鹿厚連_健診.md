# IVR プロパティ — 鹿厚連 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_汎用終話.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。鹿児島厚生連病院、健康管理センターの、AI電話です。}
用件確認.prompt={tts_g:ご用件を、次の4つのうちの、いずれかでお話ください。1、「健康診断・人間ドックの予約」、、2、「予約の変更」、、3、「予約のキャンセル」、、4、「その他お問い合わせ」。それでは、お話ください。}
予約_希望コース.prompt={tts_g:それでは、ご希望のコース、オプション、検査内容などをお話ください。}
共通_現在の予約日.prompt={tts_g:現在の予約日を、5月1日、のように日付でお話ください。}
変更_内容確認.prompt={tts_g:変更される内容を、次の2つのうちの、いずれかでお話ください。「受診内容」「日程変更」、それでは、お話ください。}
変更_受診内容.prompt={tts_g:オプション検査や検査内容の追加や変更等、希望されている内容をお話ください。}
キャンセル_再受診希望.prompt={tts_g:再受診の希望はありますか？}
問い合わせ_内容.prompt={tts_g:お問い合わせの内容をお話ください。}
問い合わせ_受付回答.prompt={tts_g:かしこまりました。お問い合わせ内容に折り返し電話は必要ですか。必要がなければこのままお電話をお切りください。必要でしたら、このまま受診される方の情報をお伺いいたします。}
共通_予約希望日.prompt={tts_g:では次に、受診希望されている時期をお話ください。「早め」や「5月上旬」「5月1日」のようにお話しください。}
共通_その他質問.prompt={tts_g:その他、病院側へお伝えしたいことはありますか？}

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
  - `END_汎用終話`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
