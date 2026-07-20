# IVR プロパティ — 関越病院 薬剤部

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:おそれいりますが、電話番号が通知されていないためお受けできません。 電話番号を通知しておかけ直しください。}
END_時間外.prompt={tts_g:お電話ありがとうございます。 ただいまの時間は受付時間外となっております。 受付時間内におかけ直しください。}
END_聴取失敗.prompt={tts_g:大変申し訳ございません。 うまく聞き取ることができませんでした。 代表電話番号におかけ直しください。}
END_折返し不要.prompt={tts_g:かしこまりました。お電話ありがとうございました。それでは失礼いたします。}
END_折返しあり_入電番号.prompt={tts_g:かしこまりました。お伺いした番号に折り返しいたします。お電話ありがとうございました。それでは失礼いたします。}
END_折返しあり_聴取番号.prompt={tts_g:かしこまりました。お掛けいただいた番号に折り返しいたします。お電話ありがとうございました。それでは失礼いたします。}
薬局名.prompt={tts_g:お電話ありがとうございます。 関越病院の疑義紹介専用、AI電話です。 まず初めに、薬局名をお話ください。}
用件確認.prompt={tts_g:ご用件を、次の3つのうち、いずれかでお話ください。1、疑義照会。2、報告。3、その他問合せ。それでは、お話しください。}
担当者名.prompt={tts_g:担当者名をお話ください。}
診療科.prompt={tts_g:診療科をお話ください。}
問い合わせ内容_疑義照会.prompt={tts_g:疑義の内容をお話ください。}
問い合わせ内容_報告.prompt={tts_g:報告の内容をお話ください。}
折返し有無.prompt={tts_g:当院からの、折り返しの連絡は必要ですか？}
問い合わせ内容_その他.prompt={tts_g:問い合わせ内容をお話ください。}

# サブフローTTS
患者_診察券番号.prompt={tts_g:診察券番号をお伺いします。 8桁以内の番号をお話下さい。 番号がわからない場合は、わからない、のようにお話下さい。}
患者_氏名.prompt={tts_g:患者名をフルネームでお話ください。}
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお話しください。}
相談_問合せ.prompt={tts_g:問い合わせ内容をお話ください。}
相談_問合せループ.prompt={tts_g:他にご質問がありましたらお話ください。}
相談_FAQ失敗.prompt={tts_g:ご質問いただいた内容はAI電話ではご対応できませんので、代表電話番号におかけ直しください。}
終話_失敗.prompt={tts_g:大変申し訳ございません。 うまく聞き取ることができませんでした。 代表電話番号におかけ直しください。}

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
amivoice.detection_flag=検出しない
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
  - `患者_診察券番号`
  - `患者_氏名`
  - `患者_連絡先`
  - `相談_問合せ`
  - `相談_問合せループ`
  - `相談_FAQ失敗`
  - `終話_失敗`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
