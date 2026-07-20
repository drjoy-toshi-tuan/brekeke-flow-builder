# IVR プロパティ — 銚子市立病院 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt） — メインフロー
非通知_アナウンス.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
時間外_アナウンス.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。銚子市立病院の健診専用AI電話です。音声ガイダンスに従い、お答えください。}
用件_選択.prompt={tts_g:ご用件を、次の4つからお選びください。予約は1、変更は2、キャンセルは3、その他お問い合わせは4。}
予約_種類.prompt={tts_g:ご予約を希望される種類を次の3つからお選びください。健康診断は1、がん検診は2、予防接種は3。}
健康診断_種類.prompt={tts_g:健康診断の種類を次の3つからお選びください。人間ドックは1、特定健診は2、その他は3。}
脳ドック_確認.prompt={tts_g:脳ドックの追加を希望されますか。希望される方は「はい」、希望されない方は「いいえ」とお話しください。}
国保_社保.prompt={tts_g:保険の種類を次の3つからお選びください。国民健康保険は1、社会保険は2、わからない場合は3。}
内容_健康診断.prompt={tts_g:その他に希望される健診内容をすべてお話しください。}
がん_種類.prompt={tts_g:がん検診の種類を次の4つからお選びください。乳がんは1、胃がんは2、肝炎は3、その他は4。}
超音波_マンモ.prompt={tts_g:乳がん検査について、乳腺エコーは1、マンモは2。}
エコー_確認.prompt={tts_g:マンモグラフィに加えて、乳腺エコーを自費で受けることもできます。エコーを追加されますか。「はい、希望します」または「いいえ、希望しません」とお話しください。}
がん_内容.prompt={tts_g:ご希望のがん健診をお話しください。}
ワクチン_種類.prompt={tts_g:ご希望のワクチン名をお話しください。}
予約_希望日.prompt={tts_g:予約を希望される曜日をお話しください。}
変更_予約日.prompt={tts_g:現在の予約日と予約内容をお話しください。}
変更_希望内容.prompt={tts_g:変更を希望される検査項目や日付をお話しください。}
キャンセル_予約日.prompt={tts_g:現在の予約日と予約内容をお話しください。}
問合せ_内容.prompt={tts_g:お問合せ内容をお話しください。}
終話_予約.prompt={tts_g:予約についてのご要望を承りました。3営業日以内に、担当者から折り返し電話、もしくは、ショートメールにてご連絡をいたします。担当者からのご連絡後に確定となります。お電話ありがとうございました。}
終話_予約_ドック.prompt={tts_g:人間ドックについてのご要望を承りました。予約は1か月半後以降となります。土日祝日を除く、3営業日以内に、担当者から折り返し電話、もしくは、ショートメールにて候補日のご連絡をいたします。担当者からのご連絡後に確定となりますのでしばらくお待ちくださいませ。お電話ありがとうございました。}
終話_予約_MR_おたふく.prompt={tts_g:MRワクチンとおたふくかぜワクチンは現在品薄のため、予約日程の受付を行っておりません。入荷があり次第、当院よりご連絡いたしますのでお待ちください。お電話ありがとうございました。}
終話_変更.prompt={tts_g:予約変更についてのご要望を承りました。3営業日以内に、担当者から折り返し電話、もしくは、ショートメールにてご連絡をいたします。担当者からのご連絡後に確定となります。お電話ありがとうございました。}
終話_キャンセル.prompt={tts_g:予約キャンセルについてのご要望を承りました。担当者より折り返しご連絡をさせていただく場合がございます。お電話ありがとうございました。}
終話_問い合わせ.prompt={tts_g:お問い合わせを承りました。3営業日以内に、担当者から折り返し電話、もしくは、ショートメールにてご連絡いたします。お電話ありがとうございました。}
終話_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}

# アナウンス（TTS prompt） — 氏名聴取サブフロー
患者_氏名.prompt={tts_g:お名前をフルネームでお話しください。}

# アナウンス（TTS prompt） — 生年月日聴取サブフロー
患者_生年月日.prompt={tts_g:生年月日を、「1970年4月1日」のようにお話しください。}

# アナウンス（TTS prompt） — 電話番号聴取サブフロー
患者_連絡先.prompt={tts_g:ご連絡先の電話番号を入力してください。}

# アナウンス（TTS prompt） — RAG検索サブフロー
相談_問合せ.prompt={tts_g:何かご質問はございますか？}
相談_問合せループ.prompt={tts_g:その他に何かご質問はございますか？ない場合は「ありません」のようにお話しください。}
# [WARNING] 相談_FAQ失敗: 設計書に該当するTTSガイダンス文が見つかりませんでした。確認してください。
相談_FAQ失敗.prompt={tts_g:TODO_発話内容を記入}
# [WARNING] 終話_失敗（RAG検索サブフロー内）: 設計書に該当するTTSガイダンス文が見つかりませんでした。確認してください。
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

- [ ] `office_id` を設定する（設計書では `TODO_要確認` となっているため Dr.JOY 側で確認が必要）
- [ ] 以下のモジュールにアナウンス文言を記入する:
  - `相談_FAQ失敗`（RAG検索サブフロー内 — 設計書に文言なし）
  - `終話_失敗`（RAG検索サブフロー内 — 設計書に文言なし）
- [ ] サブフローのTTSテキストを施設に合わせて確認・調整する:
  - `患者_氏名`（氏名聴取サブフロー — 静的JSONのデフォルト文言を仮設定）
  - `患者_生年月日`（生年月日聴取サブフロー — 静的JSONのデフォルト文言を仮設定）
  - `患者_連絡先`（電話番号聴取サブフロー — 静的JSONのデフォルト文言を仮設定）

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
> Re-confirmation node data（`患者_携帯`、`復唱_患者_連絡先`、`復唱_患者_生年月日`）の prompt はJSON内 params に直接記述するため、IVRプロパティには含まない。
