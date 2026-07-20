# IVR プロパティ — 羽生総合病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_当日代表案内.prompt={tts_g:TODO_発話内容を記入}
END_代表案内.prompt={tts_g:TODO_発話内容を記入}
END_健診案内.prompt={tts_g:TODO_発話内容を記入}
END_受付完了_携帯.prompt={tts_g:TODO_発話内容を記入}
END_受付完了_固定.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。羽生総合病院、予約専用、AI電話です。}
当日希望_確認.prompt={tts_g:まず初めに、お伺いします。今日の診療に関する内容ですか？はい、または、いいえ、で、お答えください。}
用件_確認.prompt={tts_g:ご用件を、次の4つのうちのいずれかでお話ください。「予約を取る」、「予約を変更する」、「予約をキャンセルする」、「予約を確認する」、それでは、お話ください。}
初診_再診_確認.prompt={tts_g:当院の受診は、初めてですか？はい、または、いいえ、で、お答えください。}
紹介状_確認.prompt={tts_g:他の医療機関からの紹介状はお持ちですか？はい、または、いいえ、で、お答えください。}
確認内容_聴取.prompt={tts_g:内容についてお聞きします。「次回の予約日時を教えて欲しい」、のようにお話下さい。}
診療科_聴取.prompt={tts_g:診療科をお話下さい。わからない場合は、「わからない」、とお話下さい。}
診療科_呼吸器二択.prompt={tts_g:呼吸器内科と呼吸器外科の、どちらですか？}
診療科_甲状腺二択.prompt={tts_g:糖尿・内分泌と、外科、どちらですか？}
診療科_小児科二択.prompt={tts_g:診察とリハビリ、どちらですか？}
予約日_聴取.prompt={tts_g:現在予約されている日にちを、「4月1日」のようにお話いただくか、ダイヤルキーから数字4桁で「0401」のように入力してください。}
用件_新規_携帯_アナウンス.prompt={tts_g:初診予約の申し込みを受付ました。後ほど担当者から折り返し電話、またはSMSにてご連絡いたします。}
用件_再診_携帯_アナウンス.prompt={tts_g:再診予約の申し込みを受付ました。後ほど担当者から折り返し電話、またはSMSにてご連絡いたします。}
用件_変更_携帯_アナウンス.prompt={tts_g:予約変更の申し込みを受付ました。後ほど担当者から折り返し電話、またはSMSにてご連絡いたします。}
用件_キャンセル_携帯_アナウンス.prompt={tts_g:予約キャンセルの申し込みを受付ました。後ほど担当者から折り返し電話、またはSMSにてご連絡いたします。}
用件_確認_携帯_アナウンス.prompt={tts_g:予約に関するお問い合わせを受付ました。後ほど担当者から折り返し電話、またはSMSにてご連絡いたします。}
用件_新規_固定_アナウンス.prompt={tts_g:初診予約の申し込みを受付ました。後ほど担当者から折り返し電話にてご連絡いたします。}
用件_再診_固定_アナウンス.prompt={tts_g:再診予約の申し込みを受付ました。後ほど担当者から折り返し電話にてご連絡いたします。}
用件_変更_固定_アナウンス.prompt={tts_g:予約変更の申し込みを受付ました。後ほど担当者から折り返し電話にてご連絡いたします。}
用件_キャンセル_固定_アナウンス.prompt={tts_g:予約キャンセルの申し込みを受付ました。後ほど担当者から折り返し電話にてご連絡いたします。}
用件_確認_固定_アナウンス.prompt={tts_g:予約に関するお問い合わせを受付ました。後ほど担当者から折り返し電話にてご連絡いたします。}
年末前_携帯_アナウンス.prompt={tts_g:なお、年末の予約専用ダイヤルの対応は、12月30日 16時30分までとなります。再開は1月5日 8時30分からとなりますので、あらかじめご了承ください。}
年末前_固定_アナウンス.prompt={tts_g:なお、年末の予約専用ダイヤルの対応は、12月30日 16時30分までとなります。再開は1月5日 8時30分からとなりますので、あらかじめご了承ください。}

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
  - `END_当日代表案内`
  - `END_代表案内`
  - `END_健診案内`
  - `END_受付完了_携帯`
  - `END_受付完了_固定`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
