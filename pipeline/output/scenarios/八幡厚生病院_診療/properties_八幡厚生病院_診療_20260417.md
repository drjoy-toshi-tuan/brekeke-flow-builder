# IVR プロパティ — 八幡厚生病院 診療_20260417

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。祝日を除く、月曜日から金曜日の9時から17時の間におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ありません。回答が確認できませんでした。恐れ入りますが、祝日を除く、月曜日から金曜日の9時から17時へおかけなおしください。電話番号が分かる場合は、そのままお電話をお切りください。分からない場合はご案内いたしますのでメモをご準備ください。電話番号は、0936913344です。それでは失礼します。}
END_受付完了_携帯.prompt={tts_g:かしこまりました。ご要望内容を確認し、3日以内にSMSか電話にて返答いたします。お電話ありがとうございました。それでは失礼します。}
END_受付完了_固定.prompt={tts_g:かしこまりました。ご要望内容を確認し、3日以内にお電話にて返答いたします。お電話ありがとうございました。それでは失礼します。}
END_ネット誘導.prompt={tts_g:申込みのページを、ショートメールでお送りします。メッセージのリンクを開き、はじめに「電話番号」で本人確認をしてください。そのあと、患者さまの情報を入力してください。お電話ありがとうございました。それでは失礼します。}
冒頭アナウンス_携帯.prompt={tts_g:八幡厚生病院の、予約専用、AI電話です。まずはじめに、申し込み方法をお伺いします。}
予約手段確認.prompt={tts_g:ネットから申し込みを希望の方は1を、このままお電話での申し込み希望の方は2を押してください。}
冒頭アナウンス_固定.prompt={tts_g:お電話ありがとうございます。八幡厚生病院の、予約専用、AI電話です。}
本人確認.prompt={tts_g:お電話頂いてる方は、受診を希望されるご本人様でしょうか？「はい」、「いいえ」でお答えください。}
電話口氏名.prompt={tts_g:お電話されている方のお名前を伺います。「私はたなかたろうです」のようにフルネームでお話しください。}
本人との関係.prompt={tts_g:ご本人様との関係を教えてください。}
用件.prompt={tts_g:ご用件を、次の3つのうちの、いずれかでお話ください。1.「新規予約」、2.「予約変更」、3.「予約キャンセル」。それでは、お話ください。}
受診歴.prompt={tts_g:当院への受診は初めてでしょうか？「はい」、または、「いいえ」でお答えください。}
予約日.prompt={tts_g:現在予約されている日にちを「4月1日」のようにお話ください。}
予約希望日.prompt={tts_g:予約希望時期を4月1日15時のように日付とお時間をお話ください。}
症状.prompt={tts_g:現在の症状を教えてください。}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}
患者_診察券番号.prompt={tts_g:診察券番号をお伝えください。}

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
