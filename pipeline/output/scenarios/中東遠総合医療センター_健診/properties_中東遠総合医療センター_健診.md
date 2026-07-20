# IVR プロパティ — 中東遠総合医療センター 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:お手数をおかけしますが、発信者番号を通知して再度お電話ください。電話番号の前に 186 を追加いただくことで発信者番号を通知していただくことができます。それでは失礼いたします。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、再度おかけなおしください。お電話ありがとうございました。それでは失礼いたします。}
END_予約代表案内.prompt={tts_g:申し訳ございません。AI電話ではお受けできません。祝日を除く、月曜から金曜の、9時00分から16時30分に、次の番号へおかけ直しください。電話番号は、0537-28-8133です。繰り返します。0537-28-8133です。繰り返します。0537-28-8133です。それでは失礼いたします。}
END_当日代表案内.prompt={tts_g:当日のご予約についてはAI電話ではご対応できませんので、代表電話の『0537-28-8133』におかけ直しください。それでは失礼いたします。}
END_折返案内.prompt={tts_g:複数名でのご予約はお電話でのご案内が必要となります。後ほど、担当者より、折り返しご連絡いたします。なお、営業時間外のお問い合わせは翌営業日にご連絡いたします。それでは失礼いたします。}
END_精密_携帯.prompt={tts_g:終話後、中東遠総合医療センターよりショートメールが届きますので内容をご確認ください。後程ショートメールまたは折り返しご連絡をいたします。なお、精密検査の予約、変更は14時30分から16時30分にご連絡いたします。それでは失礼いたします。}
END_精密_固定.prompt={tts_g:担当者より折り返しご連絡いたします。なお、精密検査の予約、変更は14時30分から16時30分にご連絡いたします。それでは失礼いたします。}
END_予約変更問合せ_携帯.prompt={tts_g:終話後、中東遠総合医療センターよりショートメールが届きますので内容をご確認ください。後程ショートメールまたは折り返しご連絡をいたします。それでは失礼いたします。}
END_予約変更問合せ_固定.prompt={tts_g:担当者より折り返しご連絡いたします。なお、精密検査の予約、変更は14時30分から16時30分にご連絡いたします。それでは失礼いたします。}
END_キャンセル.prompt={tts_g:ご予約のキャンセルを承りました。何かございましたら担当よりご連絡いたします。またのご利用をお待ちしております。それでは失礼いたします。}
3日以内確認.prompt={tts_g:はじめに、3営業日以内の予約に関するお問い合わせでしょうか？}
用件1聴取.prompt={tts_g:次に、お問合せ内容を次の5つのうちの、いずれかでお話しください。「人間ドック」、「健康診断」、「その他の検診」、「精密検査」、「問い合わせ」。それではお話しください。}
人数聴取.prompt={tts_g:ご予約の人数は何名様でしょうか？}
用件2聴取.prompt={tts_g:続きまして、ご用件を、次の4つのうち、いずれかでお話しください。「予約」「変更」「キャンセル」「問い合わせ」。それではお話しください。}
コース聴取_健康診断.prompt={tts_g:受診希望コースを、「健康診断」「生活習慣病予防健診」のようにお話ください。}
コース聴取_精密検査.prompt={tts_g:受診を希望される内容をお話ください。}
コース聴取_その他.prompt={tts_g:受診希望コースを、「婦人科検診」のようにお話ください。}
希望オプション聴取.prompt={tts_g:オプション検査の追加希望がございましたら「胃カメラ」のようにお話ください。ない場合は「なし」とお答えください。}
受診希望時期聴取.prompt={tts_g:受診を希望される日程や、曜日、時期をお話ください。最短での受診をご希望の場合は「最短」とお話ください。}
現在の予約日聴取_変更.prompt={tts_g:現在の予約日を「4月1日」のように日付でお話ください。}
変更内容聴取.prompt={tts_g:オプション追加や日程変更など、変更を希望される内容をお話ください。最短での受診に変更したい場合は「最短」とお話ください。}
現在の予約日聴取_キャンセル.prompt={tts_g:現在の予約日を「4月1日」のように日付でお話ください。}
問い合わせ内容聴取.prompt={tts_g:お問合せの内容をお話ください。}
追加の質問聴取.prompt={tts_g:他にオペレーターへお伝えしたいことやご質問がございましたら、お話ください。}

# サブフローTTS
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
