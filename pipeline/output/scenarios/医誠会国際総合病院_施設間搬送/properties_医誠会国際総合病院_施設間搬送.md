# IVR プロパティ — 医誠会国際総合病院 施設間搬送

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:{tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}}
END_時間外.prompt={tts_g:{tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}}
END_聴取失敗.prompt={tts_g:{tts_g:大変申し訳ございません。うまく聞き取ることができませんでした。今おかけいただいている電話番号へ折り返しご連絡しますので、お待ちください。それでは、失礼いたします。}}
END_直接来院完了.prompt={tts_g:{tts_g:受診のお申し込みを受け付けました。なお現在、国内ではしかの流行が確認されています。発疹や発熱などの症状がある方、または1ヶ月以内に海外渡航歴のある方、そのほか思い当たることがある方は、受付までお申し出ください。それでは、お気を付けてお越しください。}}
END_転送成功.prompt={tts_g:TODO_発話内容を記入}
END_転送失敗.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:{tts_g:医誠会無料救急搬送です。AI電話が対応いたします。}}
搬送or来院確認.prompt={tts_g:{tts_g:救急搬送をご希望の場合は、1、ご自身で直接お越しになる場合は、2、と、お答えください。}}
施設名聴取_アナウンス.prompt={tts_g:{tts_g:それでは、はじめに、}}
施設名聴取.prompt={tts_g:{tts_g:お迎え先の施設名を、お話ください。}}
住所聴取_アナウンス.prompt={tts_g:{tts_g:続いて、}}
住所聴取.prompt={tts_g:{tts_g:お迎え先のご住所を、お話ください。}}
状態聴取_アナウンス.prompt={tts_g:{tts_g:次に、}}
状態聴取.prompt={tts_g:{tts_g:患者様の状態を、お話ください。}}
バイタル聴取.prompt={tts_g:{tts_g:分かる範囲で、血圧や体温、治療中の病気など、お話ください。}}
氏名聴取_搬送_アナウンス.prompt={tts_g:{tts_g:かしこまりました。続いて、}}
個人情報聴取_搬送_アナウンス.prompt={tts_g:{tts_g:続いて、}}
個人情報聴取_搬送.prompt={tts_g:{tts_g:生年月日、年齢、性別を、お話ください。}}
連絡先聴取_搬送_アナウンス.prompt={tts_g:{tts_g:最後に、}}
緊急手術確認.prompt={tts_g:{tts_g:病院、クリニックからの緊急手術が必要な方ですか？必要な場合は、1、不要な場合は、2、と、お答えください。}}
転送ガイダンス.prompt={tts_g:{tts_g:それでは、電話を転送いたします。少々お待ちください。}}
直接来院_アナウンス.prompt={tts_g:{tts_g:かしこまりました。紹介状持参がない場合、選定療養費、9900円をお支払いいただきますので、ご了承ください。それでは、}}
個人情報聴取_来院_アナウンス.prompt={tts_g:{tts_g:続いて、}}
個人情報聴取_来院.prompt={tts_g:{tts_g:生年月日、年齢、性別を、お話ください。}}
症状聴取.prompt={tts_g:{tts_g:分かる範囲で、体温、治療中の病気などを、お話ください。}}
連絡先聴取_来院_アナウンス.prompt={tts_g:{tts_g:最後に、}}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}

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
  - `END_転送成功`
  - `END_転送失敗`
- [ ] 転送先電話番号を設定する:
  - `担当者へ転送`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
