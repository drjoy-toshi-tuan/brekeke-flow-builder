# IVR プロパティ — 人間ドック会館CL 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:非通知でのお電話は受付できません。発信者番号を通知してから、再度おかけ直しください。お電話ありがとうございました。それでは失礼いたします。}
END_時間外.prompt={tts_g:受付時間外のため、ただいまお電話をおつなぎすることができません。恐れ入りますが、受付時間内に改めてお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:かしこまりました。折り返しの際に確認させていただきます。お電話ありがとうございました。それでは失礼いたします。}
END_終話_予約.prompt={tts_g:申し込みを受付いたしました。3営業日以内に折り返しお電話もしくはショートメールにてご連絡いたします。折り返し番号は、03-3937-6256です。03-3937-6256から着信がありましたら、ご対応をお願いします。お電話ありがとうございました。それでは失礼いたします。}
END_終話_変更.prompt={tts_g:申し込みを受付いたしました。3営業日以内に折り返しお電話もしくはショートメールにてご連絡いたします。折り返し番号は、03-3937-6256です。03-3937-6256から着信がありましたら、ご対応をお願いします。お電話ありがとうございました。それでは失礼いたします。}
END_終話_キャンセル.prompt={tts_g:キャンセルを受付いたしました。またのご利用をお待ちしております。お電話ありがとうございました。それでは失礼いたします。}
END_終話_問い合わせ.prompt={tts_g:申し込みを受付いたしました。3営業日以内に折り返しお電話もしくはショートメールにてご連絡いたします。折り返し番号は、03-3937-6256です。03-3937-6256から着信がありましたら、ご対応をお願いします。お電話ありがとうございました。それでは失礼いたします。}
用件_確認.prompt={tts_g:次の4つのうちのいずれかでご用件をお話しください。1.予約を取る、2.変更する、3.キャンセルする、4.その他お問い合わせ、それではお話しください。}
個人_企業_確認.prompt={tts_g:ご連絡をいただいている方は健康診断を受けるご本人様でしょうか。「はい、そうです」、または「いいえ、違います」、のようにお話ください。}
企業名_聴取.prompt={tts_g:ご連絡をいただいている方の、企業名もしくは団体名をお話しください。}
担当者名_聴取.prompt={tts_g:ご担当者様のお名前を、「私は、ドック花子です。」のようにフルネームでお話ください。}
健康保険組合_予約.prompt={tts_g:ご加入の健康保険組合をお話しください。}
希望コース_予約.prompt={tts_g:受診を希望されるコースや内容をお話しください。}
追加オプション_予約.prompt={tts_g:追加を希望されるオプション検査がございましたら、お話しください。ない場合には、「特にない」とお話しください。}
受診希望日_予約.prompt={tts_g:受診を希望されるお日にちをお話しください。}
その他_予約.prompt={tts_g:その他に何かお問い合わせはございますか？}
予約日_変更.prompt={tts_g:現在の予約日をお話しください。}
変更内容_変更.prompt={tts_g:オプション検査の追加や変更、もしくは日程変更など希望されている内容をお話ください。}
その他_変更.prompt={tts_g:その他に何かお問い合わせはございますか？}
予約日_キャンセル.prompt={tts_g:現在の予約日をお話しください。}
その他_キャンセル.prompt={tts_g:その他に何かお問い合わせはございますか？}
問合せ_内容.prompt={tts_g:お問い合わせの内容をお話ください。}
その他_問合せ.prompt={tts_g:その他に何かお問い合わせはございますか？}

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
