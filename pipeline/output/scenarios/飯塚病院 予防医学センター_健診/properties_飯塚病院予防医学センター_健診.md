# IVR プロパティ — 飯塚病院予防医学センター 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}
END_完了_携帯.prompt={tts_g:3営業日以内に、担当者から折り返し電話、もしくは、ショートメールにてご連絡いたします。また、お電話終了後に送信されるショートメールから内容確認と修正ができます。お電話ありがとうございました。それでは失礼いたします。}
END_完了_固定.prompt={tts_g:3営業日以内に、担当者から折り返し電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_キャンセル.prompt={tts_g:予約キャンセルの申し込みを受付いたしました。担当者にて確認後、改めてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。飯塚病院 予防医学センター専用の、AI電話です。これより、お話いただいた内容は、当院の個人情報保護方針に基づき適切に管理致します。}
用件_確認.prompt={tts_g:ご用件を、次の4つのうちの、いずれかでお話ください。1．「健診の予約」、2．「予約の変更」、3．「予約のキャンセル」、4．「その他お問い合わせ」、それでは、お話ください。}
受付announcement_新規.prompt={tts_g:健康診断の予約の申し込みを受付いたしました。それでは、}
種類_確認.prompt={tts_g:ご希望のメニューを次の3つのうちのいずれかでお話ください。1．「人間ドック」、2．「協会けんぽの健診」、3．「その他の健診」、それでは、お話ください。}
問合せ内容_新規.prompt={tts_g:続いて、ご相談内容を一言でお話ください。}
胃検査希望有無.prompt={tts_g:続いて、胃検査のご希望はありますか？はい、あります、または、いいえ、ありません、のようにお話ください。}
胃検査内容.prompt={tts_g:胃検査について次の2つのうちの、いずれかでお話ください。1．「胃透視検査」、2．「胃カメラ検査」、それでは、お話ください。}
ラスト質問_新規.prompt={tts_g:最後にご質問やご要望はございますか？}
企業分岐.prompt={tts_g:ご連絡をいただいている方は、健康診断を受診されるご本人様でしょうか？はい、そうです、または、いいえ、違います、のようにお話ください。}
企業担当_announcement.prompt={tts_g:企業健診のご担当者さまですね。それでは、}
受付announcement_変更.prompt={tts_g:予約変更の申し込みを受付いたしました。それでは、}
予約日_変更.prompt={tts_g:現在の予約日を「6月1日」のように日付でお話ください。}
変更内容.prompt={tts_g:では次に、変更される内容を、次の2つのうちの、いずれかでお話ください。1．「受診内容」、2．「日程変更」、それでは、お話ください。}
問合せ内容_変更.prompt={tts_g:続いて、ご相談内容を一言でお話ください。}
ラスト質問_変更.prompt={tts_g:最後にご質問やご要望はございますか？}
受付announcement_キャンセル.prompt={tts_g:予約キャンセルの申し込みを受付いたしました。それでは、}
予約日_キャンセル.prompt={tts_g:現在の予約日を「6月1日」のように日付でお話ください。}
問合せ内容_キャンセル.prompt={tts_g:続いて、ご相談内容を一言でお話ください。}
ラスト質問_キャンセル.prompt={tts_g:最後にご質問やご要望はございますか？}
受付announcement_問い合わせ.prompt={tts_g:お問い合わせを受付いたしました。続いて、}
問合せ内容_問い合わせ.prompt={tts_g:ご相談内容を一言でお話ください。}
ラスト質問_問い合わせ.prompt={tts_g:最後にご質問やご要望はございますか？}

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
