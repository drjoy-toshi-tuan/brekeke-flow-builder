# IVR プロパティ — 新潟縣健康管理協会 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:申し訳ございませんが、ただいまの時間は受付時間外となっております。予約専用ダイヤルの受付時間は、祝日を除く、月曜日から土曜日の8時から16時となっております。恐れ入りますが、受付時間内におかけなおしください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:大変申し訳ございません。上手く聞き取ることができませんでした。誠に恐れ入りますが、改めておかけ直しください。お電話ありがとうございました。}
END_予約完了_営業内.prompt={tts_g:かしこまりました。内容を確認の上、担当者よりご連絡いたします。お電話ありがとうございました。}
END_予約完了_営業外.prompt={tts_g:かしこまりました。当施設の営業日に担当者より、ご連絡いたします。お電話ありがとうございました。}
END_変更完了_営業内.prompt={tts_g:かしこまりました。内容を確認の上、担当者よりご連絡いたします。お電話ありがとうございました。}
END_変更完了_営業外.prompt={tts_g:かしこまりました。当施設の営業日に担当者より、ご連絡いたします。お電話ありがとうございました。}
END_キャンセル完了.prompt={tts_g:ご予約のキャンセルを承りました。お電話ありがとうございました。}
END_企業問合せ完了_営業内.prompt={tts_g:お問い合わせを承りました。内容を確認の上、担当者よりご連絡いたします。お電話ありがとうございました。}
END_企業問合せ完了_営業外.prompt={tts_g:お問い合わせを承りました。当施設の営業日に担当者より、ご連絡いたします。お電話ありがとうございました。}
END_問合せ完了_営業内.prompt={tts_g:お問い合わせを承りました。内容を確認の上、担当者よりご連絡いたします。お電話ありがとうございました。}
END_問合せ完了_営業外.prompt={tts_g:お問い合わせを承りました。当施設の営業日に担当者より、ご連絡いたします。お電話ありがとうございました。}
END_WEB案内.prompt={tts_g:恐れ入りますが、健康診断のお知らせが届いていない方は、ホームページのWEB予約からお申込みください。お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。新潟縣健康管理協会の、予約専用、AI電話です。}
用件確認.prompt={tts_g:ご用件を、次の5つのうちの、いずれかでお話ください。1「健診の予約」、2「予約日時の変更」、3「予約のキャンセル」、4「企業ご担当者様からの問い合わせ」、5「その他お問い合わせ」、それでは、お話ください。}
受診票確認.prompt={tts_g:「健康診断受診のお知らせ」は、お手元にございますか？お持ちの方は1、お持ちでない方は2を押してください。}
登録番号.prompt={tts_g:登録番号をお伺いします。「健康診断受診のお知らせ」に記載されている登録番号を、ダイヤルプッシュで入力してください。入力が終わりましたらシャープを押してください。}
予約日.prompt={tts_g:現在のご予約日を「4月1日」のように日付でお話しください。または、ダイヤルプッシュで月と日にちの4桁の数字を入力してください。}
受診希望日.prompt={tts_g:受診希望日を「4月1日」のように日付でお話しください。または、ダイヤルプッシュで月と日にちの4桁の数字を入力してください。}
希望時間.prompt={tts_g:ご希望の時間を「9時30分」のように30分単位でお話しください。または、ダイヤルプッシュで時刻の4桁の数字を入力してください。}
企業内容.prompt={tts_g:お問い合わせの内容をお話しください。}
企業名担当者.prompt={tts_g:企業または法人名と、ご担当者のお名前をお話しください。}
企業連絡先.prompt={tts_g:ご連絡先のお電話番号を、固定電話の場合は市外局番からお話しください。または、ダイヤルプッシュで入力してください。入力が終わりましたらシャープを押してください。}
内容_その他.prompt={tts_g:お問い合わせの内容をお話しください。}

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
