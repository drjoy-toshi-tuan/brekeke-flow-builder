# IVR プロパティ — 大星クリニック健診センター 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:お手数をおかけしますが、発信者番号を通知して再度お電話ください。電話番号の前に"186"を追加いただくことで発信者番号を通知していただくことができます。それでは失礼いたします。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、再度おかけなおしください。お電話ありがとうございました。それでは失礼いたします。}
END_申込_携帯.prompt={tts_g:電話終了後に送信されるSMSより必要項目の入力を完了してください。〇日以内にスタッフより折り返しご連絡をいたします。それでは失礼いたします。}
END_申込_固定.prompt={tts_g:内容確認後、〇日以内にスタッフより折り返しご連絡をいたします。それでは失礼いたします。}
END_その他全般.prompt={tts_g:内容確認後、〇日以内にスタッフより折り返しご連絡をいたします。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:はい、大星クリニックです。健康診断、人間ドックの予約専用AIオペレーターがご用件を承ります。}
用件聴取.prompt={tts_g:ご用件を、次の4つのうち、「お申込み」「予約変更」「予約キャンセル」「その他問い合わせ」、 のいずれかをお話しください。どうぞ。}
受診歴_申込.prompt={tts_g:過去に当クリニックで受診されたことはありますか？「はい、あります。」「いいえ、ありません。」のようにお話しください。どうぞ。}
胃カメラ_申込.prompt={tts_g:胃カメラ検査を希望されますでしょうか。「はい希望します」「いいえ希望しません」のようにお話しください。どうぞ。}
胃カメラ方法_申込.prompt={tts_g:胃カメラ検査に関して、検査方法を口か鼻をお選びください。どうぞ。}
予約希望日_申込_有.prompt={tts_g:胃カメラの実施日は木曜日の午前です。受診を希望されるお日にちやお時間帯をお話しください。どうぞ。}
受診希望コース_申込_有.prompt={tts_g:ご希望の健診、または人間ドックのコース名をお話しください。どうぞ。}
受診希望コース_申込_無.prompt={tts_g:ご希望の健診、または人間ドックのコース名をお話しください。どうぞ。}
予約希望日_申込_無.prompt={tts_g:受診を希望するお日にちやお時間帯をお話しください。どうぞ。}
会社名_申込.prompt={tts_g:企業でお申込みされた場合は、お勤め先の会社名をお話しください。個人でのお申込みの場合は、「その他」とお話しください。どうぞ。}
予約日_変更.prompt={tts_g:予約した日はいつですか？どうぞ。}
変更希望日.prompt={tts_g:予約を変更される、お日にちやお時間帯をお話しください。どうぞ。}
予約日_キャンセル.prompt={tts_g:予約した日はいつですか？どうぞ。}
内容確認_その他.prompt={tts_g:お問い合わせの内容を簡潔にお話しください。どうぞ。}

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
