# IVR プロパティ — 徳島大学病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_体調相談.prompt={tts_g:TODO_発話内容を記入}
END_代表案内.prompt={tts_g:TODO_発話内容を記入}
END_変更_WEB.prompt={tts_g:TODO_発話内容を記入}
END_変更_AI.prompt={tts_g:TODO_発話内容を記入}
END_キャンセル_AI.prompt={tts_g:TODO_発話内容を記入}
END_確認_AI.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。徳島大学病院の、予約専用AI電話です。}
体調確認.prompt={tts_g:まず初めに、今回のお問い合わせは、体調が悪くて本日診察を受けたい、もしくは、体調が悪くて予約を変更したいですか？はい、または、いいえ、でお答えください。}
用件確認.prompt={tts_g:ご用件を、次の3つのうちのいずれかでお話ください。「1番、予約変更」、「2番、予約キャンセル」、「3番、予約確認」、それでは、お話ください。}
変更_WEB案内.prompt={tts_g:予約変更は、WEBでも受付を行っております。WEB予約ページのご案内をショートメッセージでお送りすることができますが、ご希望されますか？}
変更_WEB利用Y_N.prompt={tts_g:「はい」、または「いいえ」、でお答えください。}
診療科聞き取り.prompt={tts_g:予約されている診療科をおっしゃって下さい。わからない場合は、「わからない」とお話下さい。}
診療科_呼吸器.prompt={tts_g:呼吸器膠原病内科と呼吸器外科、どちらですか？}
診療科_消化器.prompt={tts_g:消化器内科と消化器外科の、どちらですか？}
診療科_脳神経.prompt={tts_g:脳神経内科と脳神経外科の、どちらですか？}
診療科_口腔.prompt={tts_g:口腔インプラント、口腔外科、口腔内科、どの診療科でしょうか。}
診療科_歯科.prompt={tts_g:歯科は複数ございます。この後ご案内する診療科名、もしくは番号でお話下さい。1番、歯科衛生室、2番、歯科統合臨床センター、3番、歯科放射線科、4番、歯科麻酔科。}
診療科_小児.prompt={tts_g:小児は複数ございます。この後ご案内する診療科名、もしくは番号でお話下さい。1番、小児科、2番、小児外科、3番、小児歯科、4番、小児摂食外来。}
予約日聴取.prompt={tts_g:現在の予約日を「4月1日」のように日付でおっしゃってください。}
理由_変更.prompt={tts_g:今回の変更理由と、次回予約希望日をご自由にお話ください。}
理由_キャンセル.prompt={tts_g:キャンセル理由を簡単にお話ください。}
理由_確認.prompt={tts_g:ご確認内容についてお伺いします。「次回の予約日時を教えて欲しい」など、内容を簡潔に仰って下さい。}
折り返し案内.prompt={tts_g:3診療日以内に、担当者から折り返し電話、もしくは、ショートメッセージにてご連絡いたします。休日、祝日を除いて3日以上連絡がなかった場合は、予約センターへ直接お電話ください。}

# サブフローTTS
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}
患者_診察券番号.prompt={tts_g:診察券番号をお伝えください。}
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
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
- [ ] 以下のモジュールにアナウンス文言を記入する:
  - `END_体調相談`
  - `END_代表案内`
  - `END_変更_WEB`
  - `END_変更_AI`
  - `END_キャンセル_AI`
  - `END_確認_AI`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
