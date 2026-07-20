# IVR プロパティ — 中部徳洲会病院 医療福祉相談室

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}
END_転送成功.prompt={tts_g:TODO_発話内容を記入}
END_転送失敗.prompt={tts_g:お電話をお繋ぎできませんでした。只今お電話が混みあっている為、お繋ぎできませんでした。恐れ入りますが、しばらく経ってから、おかけなおし下さい。失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。こちらは、中部徳洲会病院医療福祉相談室です。}
担当者案内.prompt={tts_g:それでは、担当者へ転送いたしますので、担当の名前を仰ってください。分からない場合には、分からないとお話ください。}
担当者名聴取.prompt={tts_g:担当の名前を仰ってください。分からない場合には、分からないとお話ください。}
大城聞き取り.prompt={tts_g:大城、ですね。大城実と、大城尚幸、どちらの担当者でしょうか。}
下地聞き取り.prompt={tts_g:下地、ですね。下地光太郎と、下地碧生、どちらの担当者でしょうか。}
山城聞き取り.prompt={tts_g:山城、ですね。山城碧生と、看護師の山城諒子、どちらでしょうか。}
担当者読み取得.prompt={tts_g:担当者のお名前を、もう一度ゆっくりお話しください。}
代表転送案内.prompt={tts_g:かしこまりました。それでは、医療福祉相談室の窓口へ転送いたしますので、少々お待ちください。}

# wait
冒頭.wait=2000

# 施設固有（要編集）
office_id=TODO_要確認
担当者へ転送.number=TODO_転送先番号を入力
看護師窓口へ転送.number=TODO_転送先番号を入力
代表電話へ転送.number=TODO_転送先番号を入力

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
- [ ] 転送先電話番号を設定する:
  - `担当者へ転送`
  - `看護師窓口へ転送`
  - `代表電話へ転送`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
