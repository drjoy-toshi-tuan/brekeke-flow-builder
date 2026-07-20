# IVR プロパティ — 亀田総合病院_総合相談室_20260611 総合相談室

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_折返し受付.prompt={tts_g:ご用件を承りました。担当者よりお電話にて折り返しご連絡いたします。お電話ありがとうございました。}
END_予約センター案内.prompt={tts_g:ご予約や受診に関するお問い合わせは、予約センターにて承っております。恐れ入りますが、予約センターまでおかけ直しください。お電話ありがとうございました。}
END_定型案内.prompt={tts_g:お問い合わせいただきありがとうございました。}
END_転送成功.prompt={tts_g:TODO_発話内容を記入}
END_転送失敗.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。こちらは亀田総合病院 総合相談室の自動音声応答です。ご用件をお伺いいたしますので、音声ガイダンスに従ってお話しください。}
発信元確認.prompt={tts_g:はじめに、お電話をくださった方についてお伺いします。患者ご本人またはご家族の方は1を、連携先の医療機関の方は2を、行政機関の方は3を、ダイヤルでご入力ください。}
用件確認.prompt={tts_g:ご用件をお話しください。総合相談室へのご相談、当院の代表番号へのご用件、ご予約に関するご用件などについて承ります。}
相談区分確認.prompt={tts_g:ご相談についてお伺いします。入院中の患者さまに関するご相談は1を、外来の患者さまに関するご相談は2を、新規のご相談は3を、ダイヤルでご入力ください。}
担当者確認_入院.prompt={tts_g:ご担当者のお名前はおわかりでしょうか。おわかりの場合は1を、わからない場合は2を、ダイヤルでご入力ください。}
担当者確認_外来.prompt={tts_g:ご担当者のお名前はおわかりでしょうか。おわかりの場合は1を、わからない場合は2を、ダイヤルでご入力ください。}
担当者確認_連携.prompt={tts_g:ご担当者のお名前はおわかりでしょうか。おわかりの場合は1を、わからない場合は2を、ダイヤルでご入力ください。}
担当者確認_行政.prompt={tts_g:ご担当者のお名前はおわかりでしょうか。おわかりの場合は1を、わからない場合は2を、ダイヤルでご入力ください。}
F1仕分け.prompt={tts_g:ご用件についてお伺いします。ご相談のご予約に関することは1を、受診に関することは2を、ダイヤルでご入力ください。}
患者氏名確認.prompt={tts_g:患者さまのお名前を、姓と名の順に、フルネームでおっしゃってください。}
担当者名聴取.prompt={tts_g:ご担当者のお名前をおっしゃってください。}
折返し_氏名.prompt={tts_g:お名前を、姓と名の順に、フルネームでおっしゃってください。}
折返し_用件内容.prompt={tts_g:ご用件の内容をお話しください。担当者へお伝えし、折り返しご連絡いたします。お話しが終わりましたら、そのままお待ちください。}
折返し_連絡先電話番号.prompt={tts_g:折り返しのご連絡先となるお電話番号を、市外局番からダイヤルでご入力ください。入力が終わりましたら、シャープを押してください。}
定型案内.prompt={tts_g:お問い合わせいただきありがとうございます。ご案内内容につきましては、ただいま準備を進めております。}

# wait
冒頭.wait=2000

# 施設固有（要編集）
office_id=TODO_要確認
相談室転送.number=TODO_転送先番号を入力
大代表転送.number=TODO_転送先番号を入力

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
  - `END_転送成功`
  - `END_転送失敗`
- [ ] 転送先電話番号を設定する:
  - `相談室転送`
  - `大代表転送`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
