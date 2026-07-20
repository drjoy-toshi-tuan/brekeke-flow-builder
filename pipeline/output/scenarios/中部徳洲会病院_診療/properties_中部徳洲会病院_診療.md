# IVR プロパティ — 中部徳洲会病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:大変申し訳ございません。恐れ入りますが、098-923-1091へおかけなおしください。電話番号を再度申し上げます。098-923-1091へおかけなおしください。お電話ありがとうございました。}
END_予約_完了.prompt={tts_g:かしこまりました。担当者から折り返しのご連絡にてご予約が確定いたします。数日以内にご連絡いたしますので、しばらくお待ちください。なお、後日ご予約の変更をご希望の場合は、再度こちらの番号までご連絡ください。お電話ありがとうございました。}
END_変更確認_完了.prompt={tts_g:かしこまりました。担当者から折り返しのご連絡にてご予約の変更が確定いたします。数日以内にご連絡いたしますので、しばらくお待ちください。なお、後日ご予約の変更をご希望の場合は、再度こちらの番号までご連絡ください。お電話ありがとうございました。}
END_キャンセル_完了.prompt={tts_g:かしこまりました。キャンセルを承りました。追加のご案内が必要な場合は、改めて折り返しお電話させていただくことがございます。お電話ありがとうございました。}
END_健診_案内.prompt={tts_g:申し訳ございません。人間ドック・健診についてのお問い合わせは、健康管理センター直通ダイヤルへお掛け直し下さい。電話番号がお分かりになる方はそのままお電話をおきりください。電話番号がお分かりにならない方は、メモをご用意ください。番号は、0570-001-789 です。番号は、0570-001-789 です。番号は、0570-001-789 です。お電話ありがとうございました。}
END_転送成功.prompt={tts_g:TODO_発話内容を記入}
END_転送失敗.prompt={tts_g:大変申し訳ございません。只今お電話が混み合っております。恐れ入りますが、098-923-1091へおかけなおしください。電話番号を再度申し上げます。098-923-1091へおかけなおしください。お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。中部徳洲会病院の予約専用、AI電話です。}
用件確認.prompt={tts_g:ご用件を、次の5つのうちの、いずれかでお話ください。「診察の予約」、「予防接種の予約」、「予約変更」、「予約キャンセル」、「予約確認」。それでは、お話ください。}
紹介状有無.prompt={tts_g:他の医療機関からの紹介状はお持ちですか？}
紹介状なし_案内.prompt={tts_g:かしこまりました。他の医療機関からの紹介状をお持ちでない患者さんにつきましては、通常の診療費とは別に、初診時選定療養費として、7,000円を全額自己負担いただいております。予めご了承ください。}
ワクチン名聴取.prompt={tts_g:ご希望の予防接種の種類をお話ください。分からない場合には、わからない、のようにお話ください。}
診療科聴取.prompt={tts_g:ご希望の診療科をおっしゃってください。分からない場合には、分からない、とお話ください。}
変更_予約日.prompt={tts_g:予約票に記載されている予約日を「4月1日」のように日付でおっしゃってください。}
変更_希望日.prompt={tts_g:ご希望の予約日をお話ください。なお、内服薬のある患者様の場合は、お手元にあるお薬の範囲内での変更になります。それではお話ください。}
キャンセル_予約日.prompt={tts_g:予約票に記載されている予約日を「4月1日」のように日付でおっしゃってください。}
キャンセル_理由.prompt={tts_g:ご予約キャンセルの理由を簡潔にお話ください。}
歯科口腔外科_転送ガイダンス.prompt={tts_g:それでは、担当部署へお繋ぎします。少々お待ちください。}
リハビリテーション科_転送ガイダンス.prompt={tts_g:それでは、担当部署へお繋ぎします。少々お待ちください。}
放射線科_転送ガイダンス.prompt={tts_g:それでは、担当部署へお繋ぎします。少々お待ちください。}
健康管理センター_転送ガイダンス.prompt={tts_g:かしこまりました。それでは、担当部署にお繋ぎします。少々お待ちください。}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}

# wait
冒頭.wait=2000

# 施設固有（要編集）
office_id=TODO_要確認
歯科口腔外科_転送.number=TODO_転送先番号を入力
リハビリテーション科_転送.number=TODO_転送先番号を入力
放射線科_転送.number=TODO_転送先番号を入力
健康管理センター_転送.number=TODO_転送先番号を入力

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
  - `歯科口腔外科_転送`
  - `リハビリテーション科_転送`
  - `放射線科_転送`
  - `健康管理センター_転送`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
