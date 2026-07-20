# IVR プロパティ — 近森病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_変更_携帯.prompt={tts_g:予約変更の申し込みを受付いたしました。後ほど、担当者から折り返し電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_キャンセル_携帯.prompt={tts_g:予約キャンセルの申し込みを受付いたしました。後ほど、担当者から折り返し電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_予約_携帯.prompt={tts_g:診察予約の申し込みを受付いたしました。後ほど、担当者から折り返し電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_確認_携帯.prompt={tts_g:予約確認について、お問い合わせを受付いたしました。後ほど、担当者から折り返し電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_変更_固定.prompt={tts_g:予約変更の申し込みを受付いたしました。後ほど、担当者から折り返し電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_キャンセル_固定.prompt={tts_g:予約キャンセルの申し込みを受付いたしました。後ほど、担当者から折り返し電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_予約_固定.prompt={tts_g:診察予約の申し込みを受付いたしました。後ほど、担当者から折り返し電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_確認_固定.prompt={tts_g:予約確認について、お問い合わせを受付いたしました。後ほど、担当者から折り返し電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。近森病院の予約に関するAI電話です。このお電話で承る内容は、担当者からの折り返しのご連絡により、確定となります。まず初めに、}
用件確認.prompt={tts_g:ご用件を、次の4つのうちの、いずれかでお話ください。1.変更、2.キャンセル、3.診察予約、4.予約確認、それでは、お話ください。}
用件_次へ.prompt={tts_g:かしこまりました。では次に、}
診察券_次へ.prompt={tts_g:かしこまりました。続いて、}
氏名_次へ.prompt={tts_g:ありがとうございます。次に、}
生年月日_次へ.prompt={tts_g:かしこまりました。それでは、}
診療科.prompt={tts_g:診療科をお話下さい。}
診療科_次へ.prompt={tts_g:ありがとうございます。次に、}
予約日.prompt={tts_g:予約票に記載されている予約日を、「4月1日」のように日付でおっしゃってください。}
予約日_次へ.prompt={tts_g:ありがとうございます。続いて、}
キャンセル理由.prompt={tts_g:差し支えなければ、キャンセルの理由をお話ください。特に理由がない場合は、「特にない」、のようにお話ください。}
予約希望日.prompt={tts_g:受診を希望されている時期をお話ください。希望がなければ、ありません、のようにお話ください。}
確認内容.prompt={tts_g:ご確認内容について、簡潔にお話下さい。}
連絡先_前置き.prompt={tts_g:ありがとうございます。最後に、}
接続詞_最後.prompt={tts_g:最後に、}
最後の質問.prompt={tts_g:当院にお伝えになりたいことがあればお話ください。特になければ「ありません。」とお話ください。}
完了フラグ_用件確認.prompt={tts_g:かしこまりました。}

# サブフローTTS
患者_診察券番号.prompt={tts_g:診察券番号をお伝えください。}
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
