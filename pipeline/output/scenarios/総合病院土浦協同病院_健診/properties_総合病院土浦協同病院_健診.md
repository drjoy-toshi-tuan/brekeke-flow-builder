# IVR プロパティ — 総合病院土浦協同病院 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_当日予約不可.prompt={tts_g:大変申し訳ございませんが、このお電話ではこちらのご用件は受け付けできません。お手数をおかけいたしますが、代表電話にお掛け直しください。それでは失礼いたします。}
END_受付不可診療科.prompt={tts_g:大変申し訳ございませんが、このお電話ではこちらのご用件は受け付けできません。お手数をおかけいたしますが、代表電話にお掛け直しください。それでは失礼いたします。}
END_当日完了.prompt={tts_g:お申し込みを受け付けました。3営業日以内に担当者より折り返しのお電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_新規完了.prompt={tts_g:お申し込みを受け付けました。3営業日以内に担当者より折り返しのお電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_変更完了.prompt={tts_g:お申し込みを受け付けました。3営業日以内に担当者より折り返しのお電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_企業完了.prompt={tts_g:お申し込みを受け付けました。3営業日以内に担当者より折り返しのお電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。土浦協同病院の予防医療センター、予約専用AI電話です。}
当日受診の確認.prompt={tts_g:こちらのお電話は本日の遅刻、またはキャンセル、に関する問い合わせですか？「はい」または「いいえ」でお話しください。}
当日_遅刻キャンセル.prompt={tts_g:それでは用件をお話しください。}
当日_確認事項.prompt={tts_g:最後に確認事項や質問はございますか？}
企業か個人かの確認.prompt={tts_g:それではお伺いします。今お電話いただいているのは個人予約の方でしょうか。個人予約の場合は、「はい」と、その他企業などの予約ご担当者様の場合は、「いいえ」とお話しください。}
個人_用件確認.prompt={tts_g:続いて、予約の有無についてお伺いします。「これから予約をされる方は、１と」、「既に予約をされている方やその他お問い合わせは、２と」お話ください。}
新規_希望内容.prompt={tts_g:予約を希望されるコースについて、お伺いします。「人間ドックをご希望の方は、1と」、「各種健康診断、または特定保健指導をご希望の方は、2と」、「精密検査をご希望の方は、3と」お話ください。プッシュボタンでも操作できます。}
新規_希望時期.prompt={tts_g:それでは、予約希望時期を、6月上旬、や、7月1週目のようにお話しください。}
個人_確認事項_新規.prompt={tts_g:最後に確認事項や質問はございますか？}
変更_内容確認.prompt={tts_g:それでは、ご用件を簡潔にお話しください。}
個人_確認事項_変更.prompt={tts_g:最後に確認事項や質問はございますか？}
企業_団体名.prompt={tts_g:続いて企業・団体名をお話しください。}
企業_用件.prompt={tts_g:人数と受診内容などのご用件を、お話しください。}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}
相談_問合せ.prompt={tts_g:ご質問内容をお話しください。}
相談_問合せループ.prompt={tts_g:他にご質問はございますか。ご質問がなければ「ありません」とお伝えください。}
相談_FAQ失敗.prompt={tts_g:申し訳ございません。お調べすることができませんでした。}
終話_失敗.prompt={tts_g:誠に申し訳ございません。何度かお聞き取りを試みましたが難しかったため、お電話を終了いたします。それでは失礼いたします。}

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
