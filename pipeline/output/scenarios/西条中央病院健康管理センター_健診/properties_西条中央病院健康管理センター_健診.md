# IVR プロパティ — 西条中央病院健康管理センター 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:申し訳ありません。現在は受付時間外です。受付時間は、祝日を除く月曜から金曜の8時から20時です。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、営業時間内に健康管理センターへおかけ直しください。電話番号は0897-47-3625。繰り返します。番号は、0897-47-3625。詳細はホームページをご確認ください。お電話ありがとうございました。}
END_共通_携帯.prompt={tts_g:お電話ありがとうございました。それでは失礼いたします。}
END_共通_携帯以外.prompt={tts_g:お電話ありがとうございました。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。西条中央病院の、健康管理センター専用、AI電話です。}
接続詞_初めに.prompt={tts_g:初めに、}
用件確認.prompt={tts_g:それでは、ご用件を、次の4つのうちの、いずれかでお話ください。1．健診の予約。2．予約の変更。3．予約のキャンセル。4．その他お問い合わせ。それでは、お話ください。}
種類聴取.prompt={tts_g:では、ご希望のメニューを次の4つのうちのいずれかでお話ください。1．人間ドック。2．協会けんぽ。3．定期健診。4．その他の健診。それでは、お話ください。}
新規_希望時期.prompt={tts_g:では次に、受診を希望されているお日にちや曜日、人数をお話ください。決まっていない場合には、決まっていない、のようにお話ください。}
新規_希望内容.prompt={tts_g:では、胃の検査やオプション等ご希望の内容をお話ください。}
変更_予約日.prompt={tts_g:現在の予約日を、4月1日のように日付でお話ください。わからない場合は、分からない、のようにお話ください。なお、ダイヤルプッシュで月と日にちの4桁の数字を入力することもできます。}
変更_変更内容.prompt={tts_g:変更される内容を、次の2つのうちの、いずれかでお話ください。1．受診内容。2．日程変更。それでは、お話ください。}
変更_内容聴取.prompt={tts_g:続いて、オプション追加や変更等、変更を希望されている内容をお話ください。}
変更_希望時期.prompt={tts_g:続いて、受診を希望されているお日にちや曜日をお話ください。}
キャンセル_予約日.prompt={tts_g:現在の予約日を、4月1日のように日付でお話ください。わからない場合は、分からない、のようにお話ください。なお、ダイヤルプッシュで月と日にちの4桁の数字を入力することもできます。}
問合せ_内容聴取.prompt={tts_g:続いて、お問い合わせの内容をお話ください。}
新規_受付完了.prompt={tts_g:健康診断の予約の申し込みを受付いたしました。}
変更_受付完了.prompt={tts_g:予約変更の申し込みを受付いたしました。}
キャンセル_受付完了.prompt={tts_g:予約キャンセルの申し込みを受付いたしました。}
問合せ_受付完了.prompt={tts_g:お問い合わせを受付いたしました。}
締めあいさつ.prompt={tts_g:3営業日以内に、担当者から折り返し電話、もしくは、SMSにてご連絡いたします。}

# サブフローTTS
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

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
