# IVR プロパティ — 岐阜大学医学部附属病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_当日代表案内.prompt={tts_g:TODO_発話内容を記入}
END_WEB確認.prompt={tts_g:TODO_発話内容を記入}
END_再診予約.prompt={tts_g:TODO_発話内容を記入}
END_予約変更.prompt={tts_g:TODO_発話内容を記入}
END_予約キャンセル.prompt={tts_g:TODO_発話内容を記入}
END_予約確認.prompt={tts_g:TODO_発話内容を記入}
END_転送成功.prompt={tts_g:TODO_発話内容を記入}
END_転送失敗.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。岐阜大学医学部附属病院の、予約専用、AI電話です。受付には診察券番号が必要ですので、お手元に無い方は、ご準備のうえ、おかけ直しください。また、初診予約、並びに、今日受診希望の方は、代表電話へおかけ直しください。なお、当院からの折り返しのご連絡をもって確定とさせていただきます。}
診療科_聴取.prompt={tts_g:まず初めに、受診される診療科をお話ください。「診療科は眼科です」、のように「診療科は」をつけてお話ください。}
診療科_呼吸器二択.prompt={tts_g:呼吸器内科と呼吸器外科の、どちらですか？}
診療科_消化器二択.prompt={tts_g:消化器内科と消化器外科の、どちらですか？}
診療科_脳神経二択.prompt={tts_g:脳神経内科と脳神経外科の、どちらですか？}
診療科_放射線三択.prompt={tts_g:放射線科と、放射線診断・IVRと、放射線治療の3つのうち、どれをご希望ですか？}
診療科_腎臓二択.prompt={tts_g:腎臓内科と、腎移植外科の、どちらですか？}
WEB_or_AI_聴取.prompt={tts_g:電話と同じ内容が専用のウェブページから入力できます。ウェブページの入力を希望されますか？1.はい、2.いいえ、でお話ください。「いいえ」の場合は、AI電話でご用件をお伺いします。}
WEB案内_アナウンス.prompt={tts_g:ウェブページの入力を承ります。最後に、ご連絡先のお電話番号をお伺いします。}
AI受付_アナウンス.prompt={tts_g:それでは、このままお電話で受付いたします。次に、診察券番号をお伺いします。}
用件_聴取.prompt={tts_g:ご用件を、次の4つのうちのいずれかでお話ください。1.再診の予約を取る、2.予約を変更する、3.予約をキャンセルする、4.予約を確認する。それでは、お話ください。}
再診理由_聴取.prompt={tts_g:予約理由を、お話ください。}
予約日_聴取_変更.prompt={tts_g:現在の予約日を「4月1日」のように日付でお話ください。わからない場合は「わからない」のようにお話ください。ダイヤルプッシュで月と日にちの4桁の数字の入力も可能です。}
変更理由_聴取.prompt={tts_g:変更理由をお話ください。体調不良が理由の場合は、具体的な症状をお話ください。}
予約希望時期_聴取_変更.prompt={tts_g:予約希望時期を「来週」、や、「3月下旬」、のようにお話ください。}
残薬確認_聴取_変更.prompt={tts_g:変更希望日までのお薬は十分にありますか？1.はい、2.いいえ、でお話ください。処方されていない場合は、処方されていない、とお話ください。}
予約日_聴取_キャンセル.prompt={tts_g:現在の予約日を「4月1日」のように日付でお話ください。わからない場合は「わからない」のようにお話ください。ダイヤルプッシュで月と日にちの4桁の数字の入力も可能です。}
キャンセル理由_聴取.prompt={tts_g:キャンセル理由をお話ください。体調不良が理由の場合は、具体的な症状をお話ください。}
次回予約希望_聴取.prompt={tts_g:次回の予約は希望されますか？1.はい、または、2.いいえ、でお話ください。}
予約希望時期_聴取_キャンセル.prompt={tts_g:予約希望時期を「来週」、や、「3月下旬」、のようにお話ください。}
残薬確認_聴取_キャンセル.prompt={tts_g:次回予約までのお薬は十分にありますか？1.はい、2.いいえ、でお話ください。処方されていない場合は、処方されていない、とお話ください。}
予約確認内容_聴取.prompt={tts_g:ご確認内容についてお伺いします。「次回の予約日時を教えて欲しい」など、内容を簡潔にお話ください。}

# サブフローTTS
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}
患者_診察券番号.prompt={tts_g:診察券番号をお伝えください。}
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}

# wait
冒頭.wait=2000

# 施設固有（要編集）
office_id=TODO_要確認
担当者へ転送.number=TODO_転送先番号を入力

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
  - `END_当日代表案内`
  - `END_WEB確認`
  - `END_再診予約`
  - `END_予約変更`
  - `END_予約キャンセル`
  - `END_予約確認`
  - `END_転送成功`
  - `END_転送失敗`
- [ ] 転送先電話番号を設定する:
  - `担当者へ転送`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
