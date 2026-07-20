# IVR プロパティ — 石心会さやま総合クリニック 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:申し訳ございませんが、ただいまの時間は受付時間外となっております。受付時間は、日曜、祝日、年末年始を除く、月曜日から金曜日は、8時から18時、土曜日は、8時から17時となっております。恐れ入りますが、受付時間内におかけなおしください。}
END_聴取失敗.prompt={tts_g:お電話が遠いようで、回答が確認できませんでした。恐れ入りますが、日曜祝日を除く、月曜日から金曜日の8時から18時、土曜日の8時から17時に、外来予約センターへおかけなおしください。電話番号が分かる場合は、そのままお電話をお切りください。分からない場合はご案内いたしますのでメモをご準備ください。お電話番号は、04-2953-9995、です。繰り返します。お電話番号は、04-2953-9995、です。繰り返します。お電話番号は、04-2953-9995、です。それでは、失礼いたします。}
END_当日予約_代表案内.prompt={tts_g:申し訳ございません。当日のご予約については、AI電話ではお受けできません。恐れ入りますが、日曜祝日を除く、月曜日から金曜日の8時から18時、土曜日の8時から17時に、外来予約センターへおかけなおしください。電話番号が分かる場合は、そのままお電話をお切りください。分からない場合はご案内いたしますのでメモをご準備ください。お電話番号は、04-2953-9995、です。繰り返します。お電話番号は、04-2953-9995、です。繰り返します。お電話番号は、04-2953-9995、です。それでは、失礼いたします。}
END_受付完了_定期予約.prompt={tts_g:定期予約の申し込みを受付いたしました。後ほど、担当者から折り返し電話、もしくはSMSにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_受付完了_予約変更.prompt={tts_g:予約変更の申し込みを受付いたしました。後ほど、担当者から折り返し電話、もしくはSMSにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_受付完了_予約キャンセル.prompt={tts_g:ご予約のキャンセルの申し込みを受付いたしました。お電話ありがとうございました。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:はい。石心会さやま総合クリニックの、外来予約専用、AI電話です。}
用件確認.prompt={tts_g:はじめに、ご用件を、次の3つのうちのいずれかでお話ください。1「定期受診の予約をとる」、2「予約を変更する」、3「予約をキャンセルする」、それでは、お話ください。ダイヤルプッシュでも操作できます。}
診療科.prompt={tts_g:受診を希望される診療科をおっしゃってください。}
予約日.prompt={tts_g:予約票に記載されている予約日を「4月1日」のように日付でおっしゃってください。ダイヤルプッシュで月と日にちの4桁の数字を入力することもできます。}
希望日.prompt={tts_g:予約をご希望される日付を「4月1日」のようにおっしゃってください。ダイヤルプッシュで月と日にちの4桁の数字を入力することもできます。}
キャンセル理由.prompt={tts_g:キャンセルの理由をおっしゃってください。}
他の要望.prompt={tts_g:同日の別診療科のキャンセルや別日の予約キャンセルの追加はございますでしょうか。あればご自由に内容をおっしゃってください。ない場合は「ない」とおっしゃってください。}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
患者_診察券番号.prompt={tts_g:診察券番号をお伝えください。}
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

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
