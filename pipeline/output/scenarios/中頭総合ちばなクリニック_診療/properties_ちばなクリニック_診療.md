# IVR プロパティ — ちばなクリニック 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:{tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}}
END_時間外.prompt={tts_g:{tts_g:申し訳ございませんが、ただいまの時間は受付時間外となっております。受付時間は、日曜祝日年末年始を除く、月曜日から土曜日の8時30分から11時30分となっております。恐れ入りますが、受付時間内におかけなおしください。お電話ありがとうございました。それでは失礼いたします。}}
END_聴取失敗.prompt={tts_g:{tts_g:大変申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、代表電話番号へおかけなおしください。受付時間は日曜祝日、年末年始を除く月曜日から金曜日の8時30分から17時30分、土曜日は8時30分から12時30分です。分からない場合はご案内いたしますのでメモをご準備ください。電話番号は098-939-1301です。繰り返します。電話番号は098-939-1301です。繰り返します。電話番号は098-939-1301です。}}
END_受付完了_予約.prompt={tts_g:{tts_g:かしこまりました。3診療日以内に担当者から折り返し電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}}
END_予約確認.prompt={tts_g:{tts_g:お電話終了後、ショートメールをお送りしますので、記載されたURLにアクセスいただきご確認をお願いいたします。お電話ありがとうございました。それでは失礼いたします。}}
END_紹介状なし.prompt={tts_g:{tts_g:紹介状をお持ちでない場合は、中頭総合ちばなクリニック、ナビダイヤルへお掛け直しください。番号は0570-09-1301です。繰り返します、番号は0570-09-1301です。お電話ありがとうございました。それでは失礼いたします。}}
END_受付完了_二次健診.prompt={tts_g:{tts_g:かしこまりました。3診療日以内に担当者から折り返し電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}}
冒頭_アナウンス.prompt={tts_g:{tts_g:お電話ありがとうございます。中頭総合ちばなクリニックの、予約専用、AI電話です。}}
初めに_案内.prompt={tts_g:{tts_g:本日の手術、入院予約の方は、中頭総合ちばなクリニックのナビダイヤル0570-09-1301へおかけなおしの上、ご予約のところで1番を押してください。また、二次健診予約で紹介状をお持ちで無い方も、ナビダイヤル0570-09-1301へお掛け直しの上、新規のご予約へお進みください。初めに、}}
用件確認.prompt={tts_g:{tts_g:ご用件を、次の4つのうちのいずれかでお話ください。「1.予約を変更する」、「2.予約をキャンセルする」、「3.予約を確認する」、「4.二次健診予約」、それでは、お話ください。}}
予約日聴取.prompt={tts_g:{tts_g:ありがとうございます。続いて、本日の予約に、予約票に記載されている予約日を「4月1日」のように日付でおっしゃってください。}}
当日手術確認.prompt={tts_g:{tts_g:本日の予約に、手術・入院はありますか？}}
当日検査確認.prompt={tts_g:{tts_g:現在の予約に、胃カメラ、大腸カメラ、CT、MRI、シンチ検査などの、予約検査がありますか？}}
WEB確認_アナウンス.prompt={tts_g:{tts_g:診察券をお持ちの方は、当院のHPから予約を確認いただけます。お電話での予約確認は承っておりません。お電話終了後、ショートメールをお送りしますので、記載されたURLにアクセスいただきご確認をお願いいたします。}}
紹介状有無.prompt={tts_g:{tts_g:健康診断・人間ドックからの紹介状をお持ちでしょうか？}}
紹介元医療機関名聴取.prompt={tts_g:{tts_g:当院の予約は1か月以上先の日程が目安となります。紹介状は、どちらの医療機関から受け取られましたか？医療機関名をお話下さい。わからない場合は、「わからない」とお話下さい。}}
診療科聴取.prompt={tts_g:{tts_g:それでは、紹介された診療科名をお話下さい。わからない場合は「わからない」とお答えください。}}
予約希望日1.prompt={tts_g:{tts_g:ありがとうございます。続いて、受診を希望される、第一希望の、日にちをお話ください。}}
予約希望日2.prompt={tts_g:{tts_g:続けて、受診を希望される、第二希望の日にちをお話ください。}}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
患者_診察券番号.prompt={tts_g:診察券番号をお伝えください。}

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
