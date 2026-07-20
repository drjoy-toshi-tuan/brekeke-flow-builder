# IVR プロパティ — 湘南鎌倉総合病院 医事外来

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:お電話が遠いようで、回答が確認できませんでした。恐れ入りますが、再度代表電話へおかけなおしください。代表電話では音声ガイダンスが流れますので、「患者さん、また、ご家族の方は」の1番を押した後に、「その他については」の4番を押してください。お電話ありがとうございました。}
END_受付完了.prompt={tts_g:ご用件を承りました。3診療日以内に担当者から折り返し電話連絡いたします。なお、代表電話は大変こみあっております。当院からの折り返し電話に出られなかった場合でも、必ずこちらから再度ご連絡をしますのでお待ちくださいますようお願い申し上げます。お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:医事課外来係をお呼び出ししましたが、回線が混みあっておりお繋ぎできませんでした。AI電話がご用件をお伺いし、3診療日以内に担当者から折り返し電話連絡いたします。}
診察券_案内.prompt={tts_g:はじめに、}
氏名_案内.prompt={tts_g:それでは、}
生年月日_案内.prompt={tts_g:続いて、}
連絡先_案内.prompt={tts_g:では次に、}
用件_案内.prompt={tts_g:それでは、}
問い合わせ内容聴取.prompt={tts_g:ご用件を簡潔におっしゃってください。}
追加用件確認.prompt={tts_g:その他、追加のご用件はございますか?}
追加用件_案内.prompt={tts_g:それでは、}
追加問い合わせ聴取.prompt={tts_g:ご用件を簡潔におっしゃってください。}

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
