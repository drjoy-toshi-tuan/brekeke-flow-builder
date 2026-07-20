# IVR プロパティ — ユアクリニックお茶の水 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:{tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}}
END_時間外.prompt={tts_g:{tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}}
END_聴取失敗.prompt={tts_g:{tts_g:申し訳ございません。うまく聞き取りができなかったため、後ほど担当者にて確認をいたします。お電話ありがとうございました。}}
END_受付完了.prompt={tts_g:{tts_g:ありがとうございます。質問は以上です。内容確認後、院内スタッフから土・日、祝日を除く二日以内にショートメッセージもしくはお電話にてご連絡いたします。お電話ありがとうございました。}}
END_転送成功.prompt={tts_g:TODO_発話内容を記入}
END_転送失敗.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:{tts_g:お電話ありがとうございます。ユアクリニックお茶の水のAI電話です。}}
時間外_アナウンス.prompt={tts_g:{tts_g:ただいまのお時間は診療時間外です。救急の方は東京都医療機関案内サービス、ひまわり03-5272-0303におかけください。当院へお問い合わせの方は、この後にご用件をお伺いいたします。内容確認後、院内スタッフから翌営業日終了までにショートメッセージもしくはお電話にてご連絡いたします。}}
Q1_問い合わせ内容.prompt={tts_g:{tts_g:全部で3つ質問をさせていただきます。まずは1つ目の質問です。本日のお問合せ内容をお話ください。それではどうぞ。}}
Q2_アナウンス.prompt={tts_g:{tts_g:かしこまりました。続いて、二つ目の質問です。}}
Q3_アナウンス.prompt={tts_g:{tts_g:それでは、最後の質問です。ご連絡先のお電話番号をお伺いします。}}
代表転送_ガイダンス.prompt={tts_g:{tts_g:只今のお時間は、スタッフへお繋ぎいたします。代表電話に転送いたしますのでそのままお待ちください。}}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}

# wait
冒頭.wait=2000

# 施設固有（要編集）
office_id=TODO_要確認
代表転送.number=TODO_転送先番号を入力

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
  - `代表転送`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
