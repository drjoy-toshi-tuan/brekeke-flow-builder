# IVR プロパティ — 自治医科大学附属さいたま医療センター 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_紹介状なし.prompt={tts_g:TODO_発話内容を記入}
END_対象外診療科.prompt={tts_g:TODO_発話内容を記入}
END_再診予約.prompt={tts_g:TODO_発話内容を記入}
END_初診予約.prompt={tts_g:TODO_発話内容を記入}
END_予約変更.prompt={tts_g:TODO_発話内容を記入}
END_予約キャンセル.prompt={tts_g:TODO_発話内容を記入}
END_予約確認.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。自治医科大学附属さいたま医療センターの、外来予約専用、AI電話です。}
用件_聴取.prompt={tts_g:ご用件を、次の4つのうちの、いずれかでお話ください。1.外来診察の予約を取る、2.外来予約を変更する、3.外来予約をキャンセルする、4.外来予約を確認する。それでは、お話ください。}
紹介状_聴取.prompt={tts_g:他の医療機関からの紹介状はお持ちですか？1.はい、または、2.いいえ、でお話ください。}
診療科_聴取.prompt={tts_g:受診される診療科をお話ください。初診で紹介状をお持ちの方は、紹介状の表面に記載の診療科をお話ください。}
診療科_呼吸器二択.prompt={tts_g:呼吸器内科と呼吸器外科の、どちらですか？}
診療科_消化器二択.prompt={tts_g:消化器内科と消化器外科の、どちらですか？}
診療科_脳神経二択.prompt={tts_g:脳神経内科と脳神経外科の、どちらですか？}
診療科_産婦人科二択.prompt={tts_g:産科と婦人科の、どちらですか？}
医師名_聴取_初診.prompt={tts_g:医師名の指定がある場合は、医師名をお話ください。無い場合は「ありません」のようにお話ください。}
予約日都合_聴取_予約.prompt={tts_g:ご都合の合わない日にち、曜日、時間がありましたらお知らせください。無い場合は「ありません」のようにお話ください。}
予約種別_聴取.prompt={tts_g:次に、予約の種類をお伺いします。次の２つのいずれかでお話ください。1.診察、2.診察以外。それでは、お話ください。}
予約日_聴取.prompt={tts_g:予約票に記載されている予約日を「4月1日」のように日付でお話ください。ダイヤルプッシュで月と日にちの4桁の数字の入力も可能です。}
医師名_聴取_変更キャンセル.prompt={tts_g:予約票に記載されている先生のお名前、または診療科をお話ください。}
予約時間_聴取.prompt={tts_g:予約票に記載されている予約時間を「何時何分」のようにお話ください。}
変更理由_聴取.prompt={tts_g:ご予約変更の理由をお話ください。}
キャンセル理由_聴取.prompt={tts_g:ご予約キャンセルの理由をおっしゃってください。}
予約日都合_聴取_変更.prompt={tts_g:ご都合の合わない日にち、曜日、時間がありましたらお知らせください。無い場合は「ありません」のようにお話ください。}
予約確認内容_聴取.prompt={tts_g:ご確認内容についてお伺いします。「次回の予約日時を教えて欲しい」など、内容を簡潔にお話ください。}

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
  - `END_紹介状なし`
  - `END_対象外診療科`
  - `END_再診予約`
  - `END_初診予約`
  - `END_予約変更`
  - `END_予約キャンセル`
  - `END_予約確認`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
