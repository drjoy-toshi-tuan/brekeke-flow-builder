# IVR プロパティ — 東京都立豊島病院_診療_20260710 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_終話1.prompt={tts_g:申し込みを受け付けました。こちらのお電話では受付のみとなり、まだ確定ではございません。決まり次第、折り返し電話いたします。お電話ありがとうございました。}
END_終話2.prompt={tts_g:お手続きを終了させていただきます。お電話ありがとうございました。}
END_終話3.prompt={tts_g:申し込みを受け付けました。こちらのお電話では受付のみとなり、まだ確定ではございません。決まり次第、折り返し電話、もしくはショートメッセージにてご連絡いたします。多くのお申し込みをいただいている場合、ご連絡が翌営業日以降になる場合があります。お電話ありがとうございました。}
END_救急科.prompt={tts_g:救急科はAI電話では対応しておりません。恐れ入りますが、代表電話へおかけなおしください。お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。都立豊島病院の予約専用AI電話です。緊急を要する症状は代表電話へおかけなおしください。}
受診タイミング確認.prompt={tts_g:本日の受診を希望される方は１を、翌日以降の予約を希望される方は２を押してください。}
診療科_本日.prompt={tts_g:希望の診療科を1つ教えてください。わからない場合は「わからない」とお話しください。}
受診歴確認.prompt={tts_g:受診を希望される診療科の受診歴はありますか。ある場合は１を、ない場合は２を押してください。}
紹介状確認.prompt={tts_g:紹介状はお持ちですか？持っている場合は１を、持っていない場合は２を押してください。}
選定療養費確認.prompt={tts_g:紹介状をお持ちでない場合、診察代の他に7,000円かかる場合がございます。受診を希望される場合は１を、取りやめる場合は２を押してください。}
症状確認_本日.prompt={tts_g:現在のお悩みや症状を、30秒以内でお話しください。話し終わったら、そのままお待ちいただくか、１を押してください。}
予約希望日程_本日.prompt={tts_g:ご都合の良いお日にちをお話しください。なるべく多くのお日にちをお話しください。}
追加質問_本日.prompt={tts_g:その他、ご不明な点等ございましたらお話しください。ない場合は１を押してください。}
用件確認.prompt={tts_g:ご用件を、次の4つのうちのいずれかで、ダイヤルボタンで押してください。予約に関することは１を、予約の変更に関することは２を、予約のキャンセルに関することは３を、その他お問い合わせは４を押してください。}
予約内容確認.prompt={tts_g:ご希望の予約内容についてお話しください。}
予約の種類.prompt={tts_g:診察予約の方は１を、区の健診・予防接種の方は２を、妊婦の方の初診予約は３を、それ以外の予約の方は４を押してください。}
予約_診療科.prompt={tts_g:予約を希望される診療科を「診療科は内科です」のように1つお話しください。わからない場合は「わからない」とお話しください。}
予約希望日程_予約.prompt={tts_g:ご都合の良いお日にちをお話しください。なるべく多くのお日にちをお話しください。}
追加質問_予約.prompt={tts_g:その他、ご不明な点等ございましたらお話しください。ない場合は１を押してください。}
産婦_出産予定日.prompt={tts_g:出産予定日をお話しください。}
産婦_和通分娩.prompt={tts_g:和通分娩を希望される方は「１」を、希望しない方は「２」を押してください。}
産婦_区市町村.prompt={tts_g:お住いの区市町村をお話しください。}
産婦_既往歴.prompt={tts_g:現在かかっている疾患がある場合はお話しください。ない場合は１を押してください。}
産婦_希望日程.prompt={tts_g:ご都合の良いお日にちをお話しください。なるべく多くのお日にちをお話しください。}
追加質問_産婦.prompt={tts_g:その他、ご不明な点等ございましたらお話しください。ない場合は１を押してください。}
用件の確認1_区健診.prompt={tts_g:ご希望の内容についてお話しください。}
追加質問_区健診.prompt={tts_g:その他、ご不明な点等ございましたらお話しください。ない場合は１を押してください。}
変更_診療科.prompt={tts_g:予約の変更を希望される診療科を「診療科は内科です」のように1つお話しください。}
変更_現在予約日.prompt={tts_g:現在の予約日をお話しください。}
変更_希望日程.prompt={tts_g:変更後の希望日をお話しください。なるべく多くのお日にちをお話しください。}
追加質問_変更.prompt={tts_g:その他、ご不明な点等ございましたらお話しください。ない場合は１を押してください。}
キャンセル_診療科.prompt={tts_g:予約のキャンセルを希望される診療科を「診療科は内科です」のように1つお話しください。}
キャンセル_現在予約日.prompt={tts_g:現在の予約日をお話しください。}
キャンセル理由.prompt={tts_g:キャンセル理由についてお話しください。}
追加質問_キャンセル.prompt={tts_g:その他、ご不明な点等ございましたらお話しください。ない場合は１を押してください。}
確認内容.prompt={tts_g:お問い合わせ内容をお話しください。}

# サブフローTTS
患者_診察券番号.prompt={tts_g:診察券番号をお伝えください。}
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
患者_連絡先_聴取.prompt={tts_g:ご連絡先の電話番号をお伝えください。}

# wait
冒頭.wait=2000

# 施設固有（要編集）
office_id=TODO_要確認

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

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
