# IVR プロパティ — 愛仁会健診センター 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:恐れ入りますが、時間内におかけ直しください。本窓口の受付時間は、土日祝日、年末年始を除く月曜から金曜は9時から15時、土曜は9時から12時です。電話番号が分かる場合は、そのままお電話をお切りください。分からない場合はご案内いたしますのでメモをご準備ください。代表電話番号は、072-692-9291です。繰り返します。代表電話番号は、072-692-9291です。繰り返します。代表電話番号は、072-692-9291です。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:お電話が遠いようで、回答が確認できませんでした。恐れ入りますが、祝日を除く、月曜日から金曜日の8時45分から17時、土曜日の8時45分から12時に、健康管理センター直通番号へおかけ直しください。電話番号が分かる場合は、そのままお電話をお切りください。分からない場合はご案内いたしますのでメモをご準備ください。代表電話番号は、072-692-9291です。繰り返します。代表電話番号は、072-692-9291です。繰り返します。代表電話番号は、072-692-9291です。お電話ありがとうございました。}
END_新規受付_携帯.prompt={tts_g:かしこまりました。3営業日以内に担当者から折り返し電話、もしくは、ショートメールにてご連絡いたします。お電話ありがとうございました。}
END_新規受付_その他.prompt={tts_g:かしこまりました。3営業日以内に担当者から折り返し電話にてご連絡いたします。お電話ありがとうございました。}
END_変更受付_携帯.prompt={tts_g:かしこまりました。3営業日以内に担当者から折り返し電話、もしくは、ショートメールにてご連絡いたします。お電話ありがとうございました。}
END_変更受付_その他.prompt={tts_g:かしこまりました。3営業日以内に担当者から折り返し電話にてご連絡いたします。お電話ありがとうございました。}
END_WEB案内.prompt={tts_g:かしこまりました。お電話終了後にショートメールでURLをお送りいたします。URLをタップし、予約申し込みを完了させてください。お電話ありがとうございました。}
END_予約以外_代表案内.prompt={tts_g:ご予約以外のお問い合わせにつきましては、恐れ入りますが、祝日を除く、月曜日から金曜日の8時45分から17時、土曜日の8時45分から12時に、健康管理センター直通番号へおかけ直しください。電話番号が分かる場合は、そのままお電話をお切りください。分からない場合はご案内いたしますのでメモをご準備ください。代表電話番号は、072-692-9291です。繰り返します。代表電話番号は、072-692-9291です。繰り返します。代表電話番号は、072-692-9291です。お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。愛仁会総合健康センターの、予約専用AI電話です。}
用件確認.prompt={tts_g:ご用件を、次の2つのうちの、いずれかでダイヤルプッシュしてください。
「予約を取る」は1を、
「予約の変更・キャンセル」は2を、
それでは、押してください。}
受診希望日.prompt={tts_g:受診を希望される日を、「10月10日」のように日程や、「10月中旬」のように時期など、自由におっしゃってください。}
用件詳細確認.prompt={tts_g:ご用件を、もう少し詳しくお聞かせください。
ご予約の変更、キャンセル、予約内容のご確認、または、アクセス・書類・お会計・症状などその他のお問い合わせ、いずれでしょうか？
ご用件をお話しください。}
WEB予約フォーム案内.prompt={tts_g:かしこまりました。お電話終了後にショートメールでURLをお送りいたします。URLをタップし、予約申し込みを完了させてください。}
現在の予約日.prompt={tts_g:現在の健診ご予約日を、「10月10日」のように日付でお話しください。わからない場合は、分からない、とおっしゃってください。}

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
