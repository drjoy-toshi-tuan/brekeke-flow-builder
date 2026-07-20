# IVR プロパティ — 成田赤十字病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_代表案内_本日翌日.prompt={tts_g:TODO_発話内容を記入}
END_代表案内_救急.prompt={tts_g:TODO_発話内容を記入}
END_予約受付完了.prompt={tts_g:TODO_発話内容を記入}
END_キャンセル受付完了.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。成田赤十字病院のAI電話です。本日、翌日のお問い合わせ、また診療の初診をご希望の方は恐れ入りますが、平日の9時から16時、のあいだで、当院の代表電話におかけ直しください。人間ドックのご予約については、ホームページからも承っております。}
当日翌日確認.prompt={tts_g:それでは質問を始めます。今回のお問い合わせは、本日または翌日の予約に関する内容ですか？はいそうです、または、いいえ違います、のようにお答えください。どうぞ。}
用件1.prompt={tts_g:今回のお問い合わせに関して、診療と健康診断どちらの内容をご希望でしょうか。「１、診療」、「2、健康診断」、のいずれかでお話しください。}
用件2_診療.prompt={tts_g:次の4つのうちのいずれかでご用件をお話しください。「１、予約を取る」「2、予約を変更する」「３、予約をキャンセルする」「４、その他問い合わせ」。}
診療_予約_診療科.prompt={tts_g:受診を希望される診療科をお話ください。どうぞ。}
診療_予約_希望日.prompt={tts_g:受診を希望されるお日にちを、複数お話ください。どうぞ。}
診療_変更_診療科.prompt={tts_g:予約票に記載されている診療科をお話ください。どうぞ。}
診療_変更_予約日.prompt={tts_g:予約票に記載されている予約日を「4月1日」のように日付でお話ください。どうぞ。}
診療_変更_希望日.prompt={tts_g:受診を希望されるお日にちを、複数お話ください。どうぞ。}
診療_キャンセル_診療科.prompt={tts_g:予約票に記載されている診療科をお話ください。どうぞ。}
診療_キャンセル_予約日.prompt={tts_g:予約票に記載されている予約日を「4月1日」のように日付でお話ください。どうぞ。}
診療_キャンセル_理由.prompt={tts_g:キャンセル理由を簡潔にお話しください。どうぞ。}
診療_確認_内容.prompt={tts_g:ご確認内容についてお伺いします。「次回の予約日時を教えて欲しい」など、簡潔にお話しください。どうぞ。}
用件2_健診.prompt={tts_g:次の4つのうちのいずれかでご用件をお話しください。「１、予約を取る」「2、予約を変更する」「３、予約をキャンセルする」「４、その他問い合わせ」。}
健診_予約_コース.prompt={tts_g:受診を希望される内容を次の中からお選びください。「１．人間ドック」「２．協会けんぽ」「３．事業所健診・法定健診」「４．特定健診」。}
健診_予約_オプション.prompt={tts_g:ご希望のオプション検査があればお話しください。ない場合は、「ないです」とお答えください。どうぞ。}
健診_予約_健保名.prompt={tts_g:加入されている健康保険や国民健康保険を、お話ください。わからない場合は「わからない」とお話ください。どうぞ。}
健診_予約_希望日.prompt={tts_g:受診を希望されるお日にちを、複数お話ください。どうぞ。}
健診_変更_予約日.prompt={tts_g:予約票に記載されている予約日を「4月1日」のように日付でお話ください。どうぞ。}
健診_変更_内容確認1.prompt={tts_g:予約日の変更でしょうか？「はいそうです。」「いいえ違います」のようにお話しください。}
健診_変更_希望日.prompt={tts_g:受診を希望されるお日にちを、複数お話ください。どうぞ。}
健診_変更_内容確認2.prompt={tts_g:変更したい内容を簡潔にお話しください。どうぞ。}
健診_キャンセル_予約日.prompt={tts_g:予約票に記載されている予約日を「4月1日」のように日付でお話ください。どうぞ。}
健診_キャンセル_理由.prompt={tts_g:キャンセル理由を簡潔にお話しください。どうぞ。}
健診_確認_内容.prompt={tts_g:ご確認内容についてお伺いします。「次回の予約日時を教えて欲しい」など、簡潔にお話しください。どうぞ。}

# サブフローTTS
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
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
- [ ] 以下のモジュールにアナウンス文言を記入する:
  - `END_代表案内_本日翌日`
  - `END_代表案内_救急`
  - `END_予約受付完了`
  - `END_キャンセル受付完了`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
