# IVR プロパティ — 鹿児島生協病院 健診_20260413

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}
END_クリニック案内.prompt={tts_g:大変恐れ入りますが、今回のご予約は谷山生協クリニックにて承ります。電話番号を申しあげますのでそちらへおかけなおしください。番号は099-210-2211、繰り返します、番号は099-210-2211、繰り返します、番号は099-210-2211。お電話ありがとうございました。それでは失礼いたします。}
END_当日予約不可.prompt={tts_g:当日の予約についてはAI電話ではご対応できませんので、代表電話の099-267-1455におかけ直しください。お電話ありがとうございました。それでは失礼いたします。}
END_受付完了.prompt={tts_g:お申し込みを承りました。3診療日以内に担当者から折り返し電話、もしくはSMSにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_受付完了_キャンセル.prompt={tts_g:予約のキャンセルを承りました。3診療日以内に担当者から折り返しご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
人数確認.prompt={tts_g:今回のお申込みは、お一人分ですか、複数名でしょうか。お一人の場合は1を、複数名の場合は2を押してください。}
代表者氏名.prompt={tts_g:それでは、代表者様のお名前をフルネームでお話ください。}
職場名.prompt={tts_g:職場名をお答えください。}
用件確認.prompt={tts_g:ご用件を次の4つのうちのいずれかでお話ください。健診の予約は1番、予約の変更は2番、予約のキャンセルは3番、その他お問い合わせは4番。それではお話ください。}
予約_健診内容.prompt={tts_g:健診の種類についてお伺いします。これよりご案内する番号を、ダイヤルプッシュ、または番号でお答えください。検査結果を会社へ提出する採用時健診、定期健診は1番。協会けんぽの生活習慣病予防健診は2番。人間ドック等、それ以外の健診は3番。わからない場合は、わからないとお答えください。}
予約_所定用紙.prompt={tts_g:結果を記載する所定の用紙はお持ちですか。お持ちの場合は1を、お持ちでない場合は2を押してください。}
予約_病院指定.prompt={tts_g:職場の担当者から鹿児島生協病院で受診するよう指示はありましたか。はいの場合は1を、いいえの場合は2を押してください。}
変更_予約日.prompt={tts_g:現在の予約日を教えてください。わからない場合には、わからない、とお話ください。}
変更_胃カメラ有無.prompt={tts_g:続いて、ご予約のコースの中に胃カメラの検査はございますか。ございましたら1を、なければ2を押してください。}
キャンセル_予約日.prompt={tts_g:現在の予約日を教えてください。わからない場合には、わからない、とお話ください。}
問い合わせ_内容確認.prompt={tts_g:それでは、ご用件をお話ください。}
問い合わせ_その他問合せ.prompt={tts_g:その他、健診の内容で追加のご連絡事項はございますか。ございましたら、このままお話ください。}
共通_希望時期.prompt={tts_g:受診を希望される時期をお話ください。}
氏名.prompt={tts_g:TODO_発話内容を記入}
生年月日.prompt={tts_g:TODO_発話内容を記入}
電話番号.prompt={tts_g:TODO_発話内容を記入}

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
- [ ] 以下のモジュールにアナウンス文言を記入する:
  - `氏名`
  - `生年月日`
  - `電話番号`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
