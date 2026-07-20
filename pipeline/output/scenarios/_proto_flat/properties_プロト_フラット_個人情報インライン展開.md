# IVR プロパティ — プロト_フラット 個人情報インライン展開

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_完了.prompt={tts_g:TODO_発話内容を記入}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:TODO_発話内容を記入}
氏名聴取.prompt={tts_g:受診される方のお名前を、フルネームでお話しください。}
生年月日聴取.prompt={tts_g:受診される方の生年月日を、西暦でお話しいただくか、ダイヤルプッシュで入力してください。}
復唱_電話番号聴取_ANI.prompt={tts_g:ご連絡先の電話番号は、今おかけいただいている、<speak><say-as interpret-as="telephone"><%additionalPhoneNumber%></say-as></speak>、でよろしいですか？「はい、そうです」もしくは「いいえ、違います」でお答えください。}
復唱_電話番号聴取_ANI言い直し.prompt={tts_g:ご連絡先の電話番号は、<speak><say-as interpret-as="telephone"><%additionalPhoneNumber%></say-as></speak>、でよろしいですか？「はい、そうです」もしくは「いいえ、違います」でお答えください。}
聴取_電話番号聴取_連絡先.prompt={tts_g:日中、ご連絡の取れるお電話番号を、市外局番からダイヤルプッシュで入力してください。}
復唱_電話番号聴取_連絡先.prompt={tts_g:ご連絡先の電話番号は、<speak><say-as interpret-as="telephone"><%additionalPhoneNumber%></say-as></speak>、でよろしいですか？「はい、そうです」もしくは「いいえ、違います」でお答えください。}
復唱_電話番号聴取_連絡先言い直し.prompt={tts_g:ご連絡先の電話番号は、<speak><say-as interpret-as="telephone"><%additionalPhoneNumber%></say-as></speak>、でよろしいですか？「はい、そうです」もしくは「いいえ、違います」でお答えください。}

# wait
冒頭.wait=2000

# 施設固有（要編集）
office_id=TODO_施設のoffice_idを入力

# 環境設定
# amivoice
amivoice.uri=ws://10.0.20.11:8000/ws
amivoice.language=ja
amivoice.engine=会話汎用
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
  - `END_完了`
  - `冒頭_アナウンス`

## 要レビュー（個人情報聴取の汎用デフォルト文言を使用）

以下のモジュールは設計書に施設固有の文言（`tts_modules` / `step_details`）が無かったため、汎用デフォルトを自動適用しています。TODO ではなく発話として出力済みですが、施設の呼称・敬語レベルに合わせて調整が必要か確認してください:
  - `復唱_電話番号聴取_ANI`
  - `復唱_電話番号聴取_ANI言い直し`
  - `復唱_電話番号聴取_連絡先`
  - `復唱_電話番号聴取_連絡先言い直し`
  - `氏名聴取`
  - `生年月日聴取`
  - `聴取_電話番号聴取_連絡先`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
