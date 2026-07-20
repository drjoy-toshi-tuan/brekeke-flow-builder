# IVR プロパティ — 西部総合病院 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。祝日を除く月〜金の8時45分から17時まで、土曜は8時45分から12時までに、おかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:大変申し訳ございません、回答が確認できませんでした。 恐れ入りますが、祝日を除く月曜～金曜の8：45～17：00、土曜は8：45～12：00に、健診センター直通番号へおかけなおしください。 西部総合病院代表電話の電話番号とは異なる番号ですので、お掛け間違いのないようお願い申し上げます。西部さくらクリニック直通電話番号が分かる場合は、そのままお電話をお切りください。 分からない場合はご案内いたしますのでメモをご準備ください。 電話番号は048-854-1114です。お電話ありがとうございました。それでは失礼いたします。}
END_携帯_予約.prompt={tts_g:かしこまりました。健診予約の希望を承りました。終話後、西部さくらクリニックよりショートメールが届きますので内容を必ずご確認いただき、誤りがありましたら修正をお願いいたします。また、ご住所と漢字氏名の登録もお願いいたします。3営業日以内に、担当者から改めてショートメールをお送りします。お電話ありがとうございました。それでは失礼いたします。}
END_携帯_変更問合せ.prompt={tts_g:かしこまりました。予約変更の希望を承りました。終話後、西部さくらクリニックよりショートメールが届きますので内容を必ずご確認いただき、誤りがありましたら修正をお願いいたします。また、ご住所と漢字氏名の登録もお願いいたします。3営業日以内に、担当者から改めてショートメールをお送りします。お電話ありがとうございました。それでは失礼いたします。}
END_携帯_キャンセル.prompt={tts_g:かしこまりました。予約変更キャンセルの希望を承りました。終話後、西部さくらクリニックよりショートメールが届きますので内容をご確認ください。また、ご住所と漢字氏名の登録もお願いいたします。お電話ありがとうございました。それでは失礼いたします。}
END_固定_予約.prompt={tts_g:かしこまりました。健診予約の希望を承りました。終話後、3営業日以内に、担当者からご連絡いたします。それでは失礼いたします。}
END_固定_変更問合せ.prompt={tts_g:かしこまりました。予約変更の希望を承りました。終話後、3営業日以内に、担当者からご連絡いたします。それでは失礼いたします。}
END_固定_キャンセル.prompt={tts_g:かしこまりました。予約キャンセルの希望を承りました。終話後、3営業日以内に、担当者からご連絡いたします。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。西部さくらクリニックの予約関連専用、AI電話です。当施設より折り返しご連絡をさせていただくため、はじめに、お電話をいただいている方についてお伺いします。}
用件確認.prompt={tts_g:ごご用件を「予約を取る」「予約の変更」「予約のキャンセル」「その他お問い合わせ」よりお話ください。}
受診歴確認.prompt={tts_g:かしこまりました。当院の受診は初めてですか？}
前回と同じ内容確認.prompt={tts_g:ご希望の検査内容は、前回と同じですか？}
受診コース.prompt={tts_g:受診を希望される内容をお話しください。}
予約希望日.prompt={tts_g:受診を希望される時期を、お話ください。}
本日予約確認.prompt={tts_g:本日のご予約ですか？}
変更内容.prompt={tts_g:日程の変更や、オプション追加など、変更を希望される内容をお話ください。}
予約日.prompt={tts_g:かしこまりました、それでは現在の予約日を「4月1日」のように日付でお話ください。}
お問い合わせ内容.prompt={tts_g:お問い合わせの内容をお話ください。}
追加質問.prompt={tts_g:他にご質問はございますでしょうか。}

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
