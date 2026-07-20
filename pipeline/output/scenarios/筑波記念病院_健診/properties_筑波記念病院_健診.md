# IVR プロパティ — 筑波記念病院 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:お電話ありがとうございます。つくばトータルヘルスプラザの、予約専用、AI電話です。申し訳ございません。電話番号が非通知設定の場合、AI電話では受付できません。先頭に数字の186を付けるか、通知のできる電話からおかけなおしください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、代表電話の0298643588におかけ直しください。お電話ありがとうございました。}
END_代表電話案内_3日以内.prompt={tts_g:大変申し訳ございません。日曜・祝日を除き、本日より3日目以内に関するお問い合わせはAI電話では承っておりません。恐れ入りますが、この後ご案内をする代表電話にお問い合わせください。番号をご案内しますのでメモをご準備下さい。<break time="500ms"/>番号は<speak type="telephone" breakc="100ms">0298643588</speak>です。<break time="500ms"/>番号は<speak type="telephone" breakc="100ms">0298643588</speak>です。<break time="500ms"/>番号は<speak type="telephone" breakc="100ms">0298643588</speak>です。お電話ありがとうございました。}
END_代表電話案内_当日.prompt={tts_g:当日のご予約についてはAI電話ではご対応できませんので、代表電話の<speak type="telephone" breakc="100ms">0298643588</speak>におかけ直しください。お電話ありがとうございました。}
END_問い合わせ代表案内.prompt={tts_g:大変申し訳ございません。予約以外に関するお問い合わせはAI電話では承っておりません。恐れ入りますが、この後ご案内する代表電話におかけ直しください。番号をご案内しますのでメモをご準備下さい。<break time="500ms"/>番号は<speak type="telephone" breakc="100ms">0298643588</speak>です。<break time="500ms"/>番号は<speak type="telephone" breakc="100ms">0298643588</speak>です。<break time="500ms"/>番号は<speak type="telephone" breakc="100ms">0298643588</speak>です。お電話ありがとうございました。}
END_キャンセル完了.prompt={tts_g:キャンセルを受付いたしました。必要がある場合のみ、担当者よりご連絡いたします。お電話ありがとうございました。}
END_個人_新規_mobile.prompt={tts_g:ご用件を受付いたしました。日曜、祝日を除く3日以内に、担当者から折り返し電話、もしくはショートメールにてご連絡いたします。なお、折り返しのご連絡の際に、保険証の情報を確認いたします。お手元にご用意の上、お待ちください。お電話ありがとうございました。}
END_個人_新規_landline.prompt={tts_g:ご用件を受付いたしました。日曜、祝日を除く3日以内に、担当者から折り返し電話にてご連絡いたします。なお、折り返しのご連絡の際に、保険証の情報を確認いたします。お手元にご用意の上、お待ちください。お電話ありがとうございました。}
END_個人_変更_mobile.prompt={tts_g:ご用件を受付いたしました。日曜、祝日を除く3日以内に、担当者から折り返し電話、もしくはショートメールにてご連絡いたします。なお、折り返しのご連絡の際に、保険証の情報を確認いたします。お手元にご用意の上、お待ちください。お電話ありがとうございました。}
END_個人_変更_landline.prompt={tts_g:ご用件を受付いたしました。日曜、祝日を除く3日以内に、担当者から折り返し電話にてご連絡いたします。なお、折り返しのご連絡の際に、保険証の情報を確認いたします。お手元にご用意の上、お待ちください。お電話ありがとうございました。}
END_個人_確認_mobile.prompt={tts_g:ご用件を受付いたしました。日曜、祝日を除く3日以内に、担当者から折り返し電話、もしくはショートメールにてご連絡いたします。なお、折り返しのご連絡の際に、保険証の情報を確認いたします。お手元にご用意の上、お待ちください。お電話ありがとうございました。}
END_個人_確認_landline.prompt={tts_g:ご用件を受付いたしました。日曜、祝日を除く3日以内に、担当者から折り返し電話にてご連絡いたします。なお、折り返しのご連絡の際に、保険証の情報を確認いたします。お手元にご用意の上、お待ちください。お電話ありがとうございました。}
END_企業_新規_mobile.prompt={tts_g:ご用件を受付いたしました。日曜、祝日を除く3日以内に、担当者から折り返し電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。}
END_企業_新規_landline.prompt={tts_g:ご用件を受付いたしました。日曜、祝日を除く3日以内に、担当者から折り返し電話にてご連絡いたします。お電話ありがとうございました。}
END_企業_変更_mobile.prompt={tts_g:ご用件を受付いたしました。日曜、祝日を除く3日以内に、担当者から折り返し電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。}
END_企業_変更_landline.prompt={tts_g:ご用件を受付いたしました。日曜、祝日を除く3日以内に、担当者から折り返し電話にてご連絡いたします。お電話ありがとうございました。}
END_企業_確認_mobile.prompt={tts_g:ご用件を受付いたしました。日曜、祝日を除く3日以内に、担当者から折り返し電話、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。}
END_企業_確認_landline.prompt={tts_g:ご用件を受付いたしました。日曜、祝日を除く3日以内に、担当者から折り返し電話にてご連絡いたします。お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。つくばトータルヘルスプラザ、予約専用、AI電話です。予約に関する用件以外については代表電話へおかけ直し下さい。}
予約日確認.prompt={tts_g:日曜・祝日を除き、本日より4日目以降に関するお問い合わせでよろしいですか？「はい」か「いいえ」でお話しください。}
企業個人確認.prompt={tts_g:お電話いただいている方は、企業のご担当者様ですか？「はい」か「いいえ」でお話しください。}
企業名.prompt={tts_g:お電話いただいた方の、企業名をお話ください}
用件.prompt={tts_g:ご用件を、次の4つのいずれかでお話ください。「新規予約お申込の方は1を」「予約内容の変更の方は2を」「予約キャンセルの方は3を」「予約内容及び日程の確認は4を」、それではお話ください。<dtmf digit="1"/>}
新規_希望コース.prompt={tts_g:ご希望のコースを教えてください。「健康診断をご希望の方は1を」、「人間ドックをご希望の方は2を」、「乳がん・子宮がん検診のみをご希望の方は3を」、分からない場合は、「分からない」とお話ください。<dtmf digit="1"/>}
新規_助成確認.prompt={tts_g:お住いの市町村の助成制度をご利用の場合は市町村名を、企業からの予約の場合は会社名を、どちらでもない方はその他 とお話しください。}
新規_人数時期.prompt={tts_g:受診を希望される方の人数と、予約希望時期を、お話しください。}
変更キャンセル_コース確認.prompt={tts_g:現在ご予約されているコースを教えてください。「健康診断の方は1を」、「人間ドックの方は2を」、「乳がん・子宮がん検診のみの方は3を」、分からない場合は、「分からない」とお話ください。<dtmf digit="1"/>}
変更_内容.prompt={tts_g:変更や追加希望の内容について、簡潔にお話ください。}
キャンセル_対象者聴取.prompt={tts_g:キャンセルされる方のお名前をお話しください。}
キャンセル_現在予約日聴取.prompt={tts_g:現在の予約日を、お話ください}

# サブフローTTS
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
