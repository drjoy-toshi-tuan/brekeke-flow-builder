# IVR プロパティ — 渓仁会円山クリニック 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_通常.prompt={tts_g:携帯電話の方には、通話終了後、今、お話頂いた内容のショートメールが届きますので、必ずご確認をお願いいたします。担当者が3診療日以内にお電話またはショートメールにてご連絡いたします。確認後、予約内容の確定となりますので、それまで登録内容に変更はございません。お電話ありがとうございました。それでは失礼いたします。}
END_非通知.prompt={tts_g:申し訳ございません。当院では非通知でのお電話はお受けしておりません。番号通知設定をしてお掛け直しいただくか、代表電話、011-611-7766までお電話ください。お電話ありがとうございました。それでは失礼いたします。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間は月曜日から土曜日、8時半から17時となっております。時間内に改めてお掛け直しください。お電話ありがとうございました。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、代表電話、011-611-7766へおかけ直しください。なお、ガイダンスの、1番の1、を選択してください。受付時間は、月曜日から土曜日の8時半から17時となっております。電話番号は、011-611-7766です。お電話ありがとうございました。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。渓仁会円山クリニックの健診専用、電話です。初めに、受診される方のお名前、生年月日、ご連絡先をお伺いします。}
用件選択.prompt={tts_g:それではご用件を次の4つのうちのいずれかでお話ください。1.健診の予約。2.予約の変更。3.予約のキャンセル。4.予約内容の確認。それではお話ください。}
予約_受診歴確認.prompt={tts_g:当院への受診歴はありますか？}
予約_企業名.prompt={tts_g:お勤めされている方は企業名をお話ください。そうではない方は、特にない、のようにお話ください。}
予約_受診希望コース.prompt={tts_g:ご希望のメニューを次の3つのうちのいずれかでお話ください。人間ドック。生活習慣病健診。定期健診。それでは、お話ください。}
予約_予約希望時期.prompt={tts_g:ご希望の予約日や希望時期を、4月1日、や、4月上旬、のようにお話ください。なお、本日から3週間以降の予約を受け付けております。}
変更_予約日.prompt={tts_g:次に現在の予約日を、4月1日、のように日付でお話ください。}
変更_変更項目.prompt={tts_g:変更される内容を、次の3つのうちの、いずれかでお話ください。オプション変更。日程変更。それ以外の変更。それではお話ください。}
変更_内容確認_オプション.prompt={tts_g:変更されたいオプション名をお話ください。}
変更_予約希望時期.prompt={tts_g:受診を希望される日にちを、4月1日、のように日付でお話ください。}
変更_内容確認_その他.prompt={tts_g:変更されたい内容をお話しください。}
キャンセル_予約日.prompt={tts_g:次に現在の予約日を、4月1日、のように日付でお話ください。}
キャンセル_予約希望時期.prompt={tts_g:ご希望の予約日や希望時期を、4月1日、や、4月上旬、のようにお話ください。ない場合は、ありません、とお話しください。}
確認_お問い合わせ.prompt={tts_g:確認したい内容をお話ください。}
共通_最後の問い合わせ.prompt={tts_g:そのほかに何かお問い合わせは有りませんか？}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}
相談_問合せ.prompt={tts_g:ご質問内容をお話しください。}
相談_問合せループ.prompt={tts_g:他にご質問はございますか。ご質問がなければ「ありません」とお伝えください。}
相談_FAQ失敗.prompt={tts_g:申し訳ございません。お調べすることができませんでした。}
終話_失敗.prompt={tts_g:TODO_発話内容を記入}

# wait
冒頭.wait=2000

# 施設固有（要編集）
office_id=TODO_施設のoffice_idを入力

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
  - `終話_失敗`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
