# IVR プロパティ — Medcity21 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
END_共通_携帯.prompt={tts_g:かしこまりました。お申し込みを受付いたしました。3営業日以内に、担当者からの折り返し電話にて確定となります。なおこの後、ショートメッセージが送付されますのでご確認ください。お電話ありがとうございました。それでは失礼いたします。}
END_共通_携帯以外.prompt={tts_g:かしこまりました。お申し込みを受付いたしました。3営業日以内に、担当者からの折り返し電話にて確定となります。お電話ありがとうございました。それでは失礼いたします。}
END_キャンセル.prompt={tts_g:かしこまりました。予約のキャンセルを承りました。必要がある場合のみ担当者からご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_返信不要.prompt={tts_g:かしこまりました。お電話ありがとうございました。それでは失礼いたします。}
END_代表案内.prompt={tts_g:申し訳ありません。このご用件は、AI電話ではお受けできません。06-6624-4010まで、お電話ください。受付時間は、月曜から土曜の、9時から16時半です。お電話ありがとうございました。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。人間ドック、MedCity21のAI電話です。}
用件確認.prompt={tts_g:本日のご用件を、次のうち、いずれかでお選びください。なお、質問は2分半程度で完了します。予約。日程変更。キャンセル。オプションの追加・変更。その他お問い合わせ。}
用件確認_失敗_アナウンス.prompt={tts_g:申し訳ございません、ご回答が確認できませんでした。}
予約_受診歴確認.prompt={tts_g:当施設のご利用は初めてでしょうか？}
予約_内容確認.prompt={tts_g:前回受診いただいているコースと同じ内容でよろしいでしょうか？}
予約_保険組合名.prompt={tts_g:加入されている健康保険組合名をお話しください。補助を利用されない場合は、利用しない、とお話しください。わからない場合は、わからない、とお話しください。}
予約_希望コース.prompt={tts_g:希望のコースをお話しください。わからない場合はわからない、とお話しください。}
予約_オプション追加.prompt={tts_g:今回新たに追加を希望するオプションはありますか。}
予約_希望時期.prompt={tts_g:予約を希望される時期を、2週間以上先の日程でお話しください。}
変更_条件確認.prompt={tts_g:現在の予約日は本日を含め一週間以内でしょうか？}
変更_予約日聴取.prompt={tts_g:現在予約されている日程をお話しください。}
変更_希望時期聴取.prompt={tts_g:変更後の希望日をお話しください。}
キャンセル_条件確認.prompt={tts_g:本日を含め2週間以内の予約のキャンセルでしょうか？}
キャンセル_予約日聴取.prompt={tts_g:現在予約されている日程をお話しください。}
キャンセル_振替希望.prompt={tts_g:別の日程でのご受診を希望されますか？}
オプション_予約日聴取.prompt={tts_g:現在予約されている日程をお話しください。}
オプション_内容聴取.prompt={tts_g:オプションの追加や変更の希望内容をお話しください。}
問合せ_内容聴取.prompt={tts_g:お問い合わせの内容をお話しください。}
問合せ_返信希望.prompt={tts_g:問い合わせ内容について折り返しを希望される場合は、はい、とお話しください。この後、お名前などをお聞きします。解決した方はこのままお電話をお切りください。}
ラスト質問.prompt={tts_g:そのほかに何かお問い合わせは有りませんか？}

# サブフローTTS
相談_問合せ.prompt={tts_g:ご質問内容をお話しください。}
相談_問合せループ.prompt={tts_g:他にご質問はございますか。ご質問がなければ「ありません」とお伝えください。}
相談_FAQ失敗.prompt={tts_g:申し訳ございません。お調べすることができませんでした。}
終話_失敗.prompt={tts_g:誠に申し訳ございません。何度かお聞き取りを試みましたが難しかったため、お電話を終了いたします。それでは失礼いたします。}
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
