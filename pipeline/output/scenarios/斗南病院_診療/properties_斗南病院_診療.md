# IVR プロパティ — 斗南病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:TODO_発話内容を記入}
END_時間外.prompt={tts_g:TODO_発話内容を記入}
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}
END_通常.prompt={tts_g:かしこまりました。このお電話でご予約の確定ではございません。3営業日以内に折り返しの電話またはショートメールでの確認をさせて頂き確定となりますので今しばらくお待ちください。内容によってはご希望に添えない場合がございますので、ご了承ください。お電話ありがとうございました。それでは失礼いたします。}
END_紹介状なし.prompt={tts_g:紹介状をご準備されましたら、再度ご連絡をお願いいたします。お電話ありがとうございました。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。斗南病院の予約関連専用のAI電話です。ご予約について、緊急の診療が必要な場合は代表電話にお掛け直しくださいませ。また、予約変更の受付は、前日の16時までとなっております。16時以降の場合は代表電話にお掛け直しください。}
用件確認.prompt={tts_g:ご用件を、新規のご予約、2回目以降のご予約、予約の変更、予約のキャンセル、予約の日時確認、お問い合わせ、のようにお話ください。}
新規紹介状.prompt={tts_g:斗南病院宛の紹介状、もしくは検診結果はお持ちですか？}
新規紹介状_手元有無.prompt={tts_g:紹介状、もしくは検診結果はお手元にございますか？}
紹介元医療機関名_新規.prompt={tts_g:紹介元の医療機関名をお話しください。}
紹介元医療機関電話番号_新規.prompt={tts_g:紹介元医療機関の電話番号をお話しください。}
医師指定_新規.prompt={tts_g:医師のご指定はございますか？}
診療科_新規1.prompt={tts_g:まずは診療科をお話ください。わからない場合はわからないとお話ください。}
予約希望日_新規1.prompt={tts_g:予約希望日時についてご都合が悪いお日にちはございますか？}
性別_新規1.prompt={tts_g:患者様の性別をお話ください。}
病名症状_新規1.prompt={tts_g:病名または症状をお話ください。}
FAX確認_アナウンス.prompt={tts_g:診療情報提供書のFAX取り寄せをする場合がございます。ご理解・ご承諾のほど、何卒よろしくお願い申し上げます。}
選定療養費_アナウンス.prompt={tts_g:紹介状が無い場合、選定療養費7700円がかかる場合がございますのでご了承ください。}
診療科_新規2.prompt={tts_g:まずは診療科をお話ください。わからない場合はわからないとお話ください。}
性別_新規2.prompt={tts_g:患者様の性別をお話ください。}
他院確認.prompt={tts_g:今回通院する症状で、他の病院様にも、通院されていますでしょうか？}
新規紹介状2.prompt={tts_g:今回の症状で新たに斗南病院宛の紹介状、もしくは検診結果はお持ちですか？}
新規紹介状2_手元有無.prompt={tts_g:紹介状、もしくは検診結果はお手元にございますか？}
紹介元医療機関名_再診.prompt={tts_g:紹介元の医療機関名をお話しください。}
紹介元医療機関電話番号_再診.prompt={tts_g:紹介元医療機関の電話番号をお話しください。}
医師指定_再診.prompt={tts_g:医師のご指定はございますか？}
診療科_再診1.prompt={tts_g:まずは診療科をお話ください。わからない場合はわからないとお話ください。}
予約希望日_再診1.prompt={tts_g:予約希望日時についてご都合が悪いお日にちはございますか？}
診療科_再診2.prompt={tts_g:まずは診療科をお話ください。わからない場合はわからないとお話ください。}
予約希望日_再診2.prompt={tts_g:予約希望日時についてご都合が悪いお日にちはございますか？}
変更紹介状_変更.prompt={tts_g:斗南病院宛の紹介状、もしくは検診結果はお持ちですか？}
診療科_変更.prompt={tts_g:まずは診療科をお話ください。わからない場合はわからないとお話ください。}
予約日_変更.prompt={tts_g:次に現在の予約日を、7月1日、のように日付でお話ください。}
予約希望日_変更.prompt={tts_g:予約希望日時についてご都合が悪いお日にちはございますか？}
理由_変更.prompt={tts_g:それでは、変更の理由をお話ください。}
残薬確認_変更.prompt={tts_g:次の予約日まで薬は足りますでしょうか。}
変更紹介状_キャンセル.prompt={tts_g:斗南病院宛の紹介状、もしくは検診結果はお持ちですか？}
診療科_キャンセル.prompt={tts_g:まずは診療科をお話ください。わからない場合はわからないとお話ください。}
予約日_キャンセル.prompt={tts_g:次に現在の予約日を、7月1日、のように日付でお話ください。}
理由_キャンセル.prompt={tts_g:それでは、キャンセルの理由をお話ください。}
残薬確認_キャンセル.prompt={tts_g:次の予約日まで薬は足りますでしょうか。}
変更紹介状_確認.prompt={tts_g:斗南病院宛の紹介状、もしくは検診結果はお持ちですか？}
診療科_確認.prompt={tts_g:まずは診療科をお話ください。わからない場合はわからないとお話ください。}

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
  - `終話_失敗`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
