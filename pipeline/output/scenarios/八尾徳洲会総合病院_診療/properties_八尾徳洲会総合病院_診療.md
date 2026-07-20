# IVR プロパティ — 八尾徳洲会総合病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:{tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}}
END_時間外.prompt={tts_g:{tts_g:申し訳ございませんが、ただいまの時間は受付時間外となっております。受付時間は、日曜祝日を除く、月曜日から金曜日の8時から16時、土曜日は8時から11時となっております。本日のご予約の方は、代表電話072-993-8501へおかけください。なお、12月31日から1月4日までは年末年始のため休止しております。年始は1月5日より開始いたしますので、5日の8時以降におかけくださいますようお願いいたします。お電話ありがとうございました。}}
END_聴取失敗.prompt={tts_g:{tts_g:大変申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}}
END_予約変更_完了.prompt={tts_g:{tts_g:ご予約の変更を承りました。後ほど担当者よりご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}}
END_予約キャンセル_完了.prompt={tts_g:{tts_g:ご予約のキャンセルを承りました。必要に応じて、翌診療日までに職員より折り返しご連絡をさせていただく場合がございますのでご了承ください。また、1か月以内にご連絡いただけましたら予約変更が可能です。お電話ありがとうございました。それでは失礼いたします。}}
END_予約確認_完了.prompt={tts_g:{tts_g:ご予約の確認を承りました。後ほど担当者よりご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}}
END_予約以外.prompt={tts_g:{tts_g:申し訳ございません。こちらは予約専用ダイヤルとなっております。ご予約以外のお問い合わせにつきましては、代表電話へおかけなおしください。電話番号は、072-993-8501です。お電話ありがとうございました。}}
END_代表案内.prompt={tts_g:{tts_g:電話番号は、072-993-8501です。繰り返します。電話番号は、072-993-8501です。繰り返します。電話番号は、072-993-8501です。繰り返します。電話番号は、072-993-8501です。繰り返します。電話番号は、072-993-8501です。お電話ありがとうございました。}}
END_病児保育案内.prompt={tts_g:{tts_g:大変申し訳ございませんが、病児保育診察は、代表電話へおかけなおしください。電話番号は、072-993-8501です。繰り返します。電話番号は、072-993-8501です。お電話ありがとうございました。}}
END_歯科_時間前.prompt={tts_g:{tts_g:恐れ入りますが、ただ今の時間は歯科・口腔外科の予約変更・キャンセルはお受けしておりません。8時30分以降におかけ直しください。お電話ありがとうございました。}}
END_歯科_昼休み.prompt={tts_g:{tts_g:恐れ入りますが、ただ今の時間は歯科・口腔外科の予約変更・キャンセルはお受けしておりません。13時30分以降におかけ直しください。お電話ありがとうございました。}}
END_健診_時間前.prompt={tts_g:{tts_g:健診センターへのご用件は、本日ご予約の方は、代表番号072-993-8501へ、本日のご予約以外の方は、平日11時から16時までに健診センター直通072-993-6505までおかけ直しください。お電話ありがとうございました。}}
END_転送成功.prompt={tts_g:TODO_発話内容を記入}
END_転送失敗.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:{tts_g:お電話ありがとうございます。八尾徳洲会総合病院の、予約専用、AI電話です。}}
用件確認.prompt={tts_g:{tts_g:ご用件を、次の4つのうちの、いずれかでお話いただくか、番号を押してください。「1.予約を変更する」「2.予約をキャンセルする」「3.予約を確認する」「4.歯科・口腔外科へのお電話」、それでは、お話ください。}}
用件_共通_診療科.prompt={tts_g:{tts_g:それでは順番にお伺いしますのでひとつずつお答えください。わからない場合はわからないとお話ください。予約票に記載されている診療科もしくは検査名を、「診療科は内科です」もしくは「検査名はエコーです」のようにお話ください。}}
変更_予約日.prompt={tts_g:{tts_g:現在の予約日を、「4月1日」のように日付でお話ください。}}
変更_予約希望日.prompt={tts_g:{tts_g:ご希望の予約日を、明日以降の日付で「4月1日」のようにお話ください。希望日がない場合には、「ありません」とお答えください。}}
変更_変更詳細.prompt={tts_g:{tts_g:他に予約を変更したい診療科や検査のご予約がございましたら、内容をお話ください。ない場合は「ありません」とお答えください。}}
変更_変更理由.prompt={tts_g:{tts_g:それでは、予約変更の理由をお話ください。}}
キャンセル_予約日.prompt={tts_g:{tts_g:現在の予約日を、「4月1日」のように日付でお話ください。}}
キャンセル_理由.prompt={tts_g:{tts_g:それでは、キャンセルの理由をお話ください。}}
歯科_転送ガイダンス.prompt={tts_g:{tts_g:それでは、担当部署へ転送いたします。しばらくお待ちください。}}
健診_転送ガイダンス.prompt={tts_g:{tts_g:それでは、担当部署へ転送いたします。しばらくお待ちください。}}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
患者_診察券番号.prompt={tts_g:診察券番号をお伝えください。}
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}

# wait
冒頭.wait=2000

# 施設固有（要編集）
office_id=TODO_要確認
歯科_転送.number=TODO_転送先番号を入力
健診_転送.number=TODO_転送先番号を入力

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
  - `END_転送成功`
  - `END_転送失敗`
- [ ] 転送先電話番号を設定する:
  - `歯科_転送`
  - `健診_転送`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
