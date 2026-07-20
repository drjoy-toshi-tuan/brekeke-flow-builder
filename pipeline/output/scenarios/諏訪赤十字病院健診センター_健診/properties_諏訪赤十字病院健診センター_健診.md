# IVR プロパティ — 諏訪赤十字病院健診センター 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:TODO_発話内容を記入}
END_時間外.prompt={tts_g:TODO_発話内容を記入}
END_聴取失敗.prompt={tts_g:TODO_発話内容を記入}
END_通常.prompt={tts_g:TODO_発話内容を記入}
END_キャンセル.prompt={tts_g:TODO_発話内容を記入}
END_3日以内直通.prompt={tts_g:TODO_発話内容を記入}
END_生活習慣病予防満員.prompt={tts_g:TODO_発話内容を記入}
END_市民健診案内.prompt={tts_g:TODO_発話内容を記入}
END_子宮頚がん案内.prompt={tts_g:TODO_発話内容を記入}
個人_企業選択.prompt={tts_g:はじめに、お電話をいただいている方についてお伺いします。ご自身やご家族の予約に関するご連絡は、1番を、企業、団体からのお申込みは、2番を押してください。}
企業_企業名.prompt={tts_g:企業、団体名を、企業名は諏訪赤十字、のようにお話ください。}
企業_部署担当者名.prompt={tts_g:ご担当者様の部署、氏名を、部署は総務課、名前は田中太郎です、のようにお話ください。}
用件選択.prompt={tts_g:ご用件を次の5つのうちのいずれかで、お話ください。1が健診の予約、2がオプションの追加、3が予約の変更、4が予約のキャンセル、5がその他お問合せ。それではお話ください。}
予約_コース選択.prompt={tts_g:現在、4月以降の予約を承っております。それでは、次より受診を希望されるコースをお選びください。1が人間ドック、2が生活習慣病予防健診、3が市民健診、4が市町村の子宮頚がん健診、5がその他コース。それではどうぞ。}
予約_人間ドック案内.prompt={tts_g:1日人間ドック、生活習慣病予防健診をご希望の方は、2026年3月以降のご予約を承っております。}
予約_その他コース名.prompt={tts_g:希望されるコース名をお話しください。コース名が分からない方は職員から折り返しの際にご案内させていただきますので、わからない、とお話しください。それではどうぞ。}
予約_オプション.prompt={tts_g:追加を希望されるオプションをお話ください。}
予約_希望時期.prompt={tts_g:受診を希望される時期やお日にちをお話ください。}
予約_人数.prompt={tts_g:受診を希望される人数をお話しください。}
追加_3日以内判断.prompt={tts_g:本日より3日以内のご予約の方でしょうか。}
追加_オプション.prompt={tts_g:追加を希望されるオプションをお話ください。}
変更_3日以内判断.prompt={tts_g:本日より3日以内のご予約の方でしょうか。}
変更_内容確認.prompt={tts_g:変更を希望される内容や、日程変更の場合は受診希望時期をお話ください。}
キャンセル_3日以内判断.prompt={tts_g:本日より3日以内のご予約の方でしょうか。}
キャンセル_現在の予約日.prompt={tts_g:次に、現在の予約日をお伺いします。本日、翌営業日のご予約の方は、恐れ入りますが健診センター直通電話、0266-57-6042へおかけなおしください。それでは現在の予約日を、4月1日、のように日付でお話ください。}
キャンセル_人員確認.prompt={tts_g:キャンセルされる方の氏名と生年月日をお話ください。}
問い合わせ_3日以内判断.prompt={tts_g:本日より3日以内のご予約の方でしょうか。}
問い合わせ_内容.prompt={tts_g:お問い合わせの内容をお話ください。なお協会けんぽの関するお問い合わせが集中しておりますので、協会けんぽに関するお問い合わせの回答は午後1時以降に順次折り返し対応させていただきます。}
共通_折り返し時間.prompt={tts_g:職員からの折り返し連絡希望時間をお伺いいたします。13時から、16時の間で、都合の良い時間をお話下さい。どうぞ。}

# サブフローTTS
患者_氏名.prompt={tts_g:TODO_発話内容を記入}
患者_生年月日.prompt={tts_g:TODO_発話内容を記入}
患者_連絡先.prompt={tts_g:TODO_発話内容を記入}

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
  - `END_非通知`
  - `END_時間外`
  - `END_聴取失敗`
  - `END_通常`
  - `END_キャンセル`
  - `END_3日以内直通`
  - `END_生活習慣病予防満員`
  - `END_市民健診案内`
  - `END_子宮頚がん案内`
  - `患者_氏名`
  - `患者_生年月日`
  - `患者_連絡先`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
