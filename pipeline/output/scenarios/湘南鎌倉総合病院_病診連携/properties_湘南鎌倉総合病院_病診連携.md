# IVR プロパティ — 湘南鎌倉総合病院 病診連携

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}
END_受付完了.prompt={tts_g:ご用件を承りました。お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:お呼び出ししましたが、お繋ぎできませんでした。AI電話がご用件をお伺いし、担当者から折り返し電話連絡いたします。}
はじめに_アナウンス.prompt={tts_g:はじめに、}
施設情報_聴取.prompt={tts_g:医療機関名、所属部署、お名前をおっしゃってください。}
では次に_アナウンス.prompt={tts_g:では次に、}
携帯番号_聴取.prompt={tts_g:緊急時の連絡方法として、携帯電話の番号をお伺いしています。携帯電話をお持ちの場合は、番号をおっしゃってください。お持ちでない場合は「持っていない」とおっしゃってください。}
それでは_アナウンス.prompt={tts_g:それでは、}
用件_聴取.prompt={tts_g:ご用件を簡潔におっしゃってください。}

# サブフローTTS
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
