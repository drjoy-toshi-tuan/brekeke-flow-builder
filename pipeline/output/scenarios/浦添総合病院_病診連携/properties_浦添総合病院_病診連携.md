# IVR プロパティ — 浦添総合病院 病診連携

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:申し訳ございません。ただいまの時間は受付時間外となっております。受付時間は、日曜祝日と年末年始を除く、月曜日から金曜日の9時から17時、土曜日は9時から12時です。恐れ入りますが、受付時間内におかけなおしください。}
END_聴取失敗.prompt={tts_g:恐れ入りますが、医療連携支援室『かけはし』へおかけ直しください。電話番号が分かる方は、このままお電話をお切りください。わからない方はご案内しますので、メモをご準備ください。代表電話は、0、9、8、の、8、7、9、の、0、6、3、0、です。繰り返します。番号は0、9、8、の、8、7、9、の、0、6、3、0、です。お電話ありがとうございました。}
END_代表案内.prompt={tts_g:恐れ入りますが、医療連携支援室『かけはし』へおかけ直しください。電話番号が分かる方は、このままお電話をお切りください。わからない方はご案内しますので、メモをご準備ください。代表電話は、0、9、8、の、8、7、9、の、0、6、3、0、です。繰り返します。番号は0、9、8、の、8、7、9、の、0、6、3、0、です。お電話ありがとうございました。}
END_代表案内_1.prompt={tts_g:恐れ入りますが、入院・転院のご依頼については、医療連携支援室『かけはし』へおかけ直しください。電話番号が分かる方は、このままお電話をお切りください。わからない方はご案内しますので、メモをご準備ください。代表電話は、0、9、8、の、8、7、9、の、0、6、3、0、です。繰り返します。代表電話は、0、9、8、の、8、7、9、の、0、6、3、0、です。繰り返します。代表電話は、0、9、8、の、8、7、9、の、0、6、3、0、です。お電話ありがとうございました。それでは失礼いたします。}
END_当日予約.prompt={tts_g:恐れ入りますが、当日、または早急な対応をご希望の場合は、医療連携支援室『かけはし』へおかけ直しください。電話番号が分かる方は、このままお電話をお切りください。わからない方はご案内しますので、メモをご準備ください。電話番号は、0、9、8、の、8、7、9、の、0、6、3、0、です。繰り返します。電話番号は、0、9、8、の、8、7、9、の、0、6、3、0、です。繰り返します。電話番号は、0、9、8、の、8、7、9、の、0、6、3、0、です。お電話ありがとうございました。それでは失礼いたします。}
END_受付完了_予約.prompt={tts_g:かしこまりました。<% inquiringFacility %>の、申込みを受付けしました。外来予約時は、外来予約申込書、診療情報提供書を必ずFAXにてお送りください。確認が必要な際は、折り返しご連絡をいたします。それでは失礼いたします。}
END_受付完了_情報提供.prompt={tts_g:かしこまりました。<% inquiringFacility %>の、申込みを受付けしました。確認次第、折り返しご連絡をいたします。それでは失礼いたします。}
END_受付完了_FAX.prompt={tts_g:かしこまりました。<% inquiringFacility %>の、申込みを受付けました。到着が確認できない場合は翌診療日午前中までに折り返しご連絡いたします。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。浦添総合病院の、地域医療連携、AI電話です。}
施設名聴取.prompt={tts_g:紹介元の医療機関名をお話ください。}
施設名_復唱.prompt={tts_g:<% inquiringFacility %>、ご連絡ありがとうございます。}
緊急性チェック.prompt={tts_g:本件は緊急のご連絡でしょうか？「緊急です」または「いいえ、違います」とお話ください。}
用件確認.prompt={tts_g:ご用件を、次のいずれかの番号、または内容をお話いただくか、ダイヤルプッシュでお答えください。1「予約依頼」2「ファックス到着確認」3「情報提供依頼」、それでは、お話ください。}
当日予約日確認.prompt={tts_g:当日予約のご希望、または早急な対応が必要ですか？}
問い合わせ_資料期日.prompt={tts_g:資料はいつまでに必要かお答えください。}
問い合わせ_患者種別.prompt={tts_g:入院中と通院中、どちらの患者様になりますか？}
その他問合せ.prompt={tts_g:職員へお伝えになりたいことがありましたらお話ください。ない場合には特にない、などとお話ください。}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}

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

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
