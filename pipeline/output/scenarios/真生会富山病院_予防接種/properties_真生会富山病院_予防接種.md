# IVR プロパティ — 真生会富山病院 予防接種

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:申し訳ございません。電話番号が非通知設定の場合、AI電話では受付できません。
通知設定をするか、先頭に数字の186を付けてからおかけなおしください。
それでは失礼いたします。}
END_時間外.prompt={tts_g:申し訳ございませんが、ただいまの時間は受付時間外となっております。
受付時間は、日曜、祝日を除く、月曜から金曜の、9時から15時、
土曜の、9時から11時となっております。
恐れ入りますが、受付時間内におかけなおしください。}
END_聴取失敗.prompt={tts_g:申し訳ございません。
うまく聞き取ることができませんでした。
恐れ入りますが、日曜、祝日を除く、月曜から金曜の、9時から15時、
土曜の、9時から11時に、健診センターへおかけなおしください。
電話番号は、0766-52-2473です。
繰り返します。0766-52-2473です。
繰り返します。0766-52-2473です。
それでは失礼いたします。}
END_接種後体調代表案内.prompt={tts_g:接種後の体調不良については、代表電話にお掛け直しください。
電話番号は、0766-52-2156です。
繰り返します。電話番号は、0766-52-2156です。
繰り返します。電話番号は、0766-52-2156です。
お電話ありがとうございました。}
END_キャンセル完了.prompt={tts_g:キャンセルを完了いたしました。
お電話ありがとうございました。}
END_新規予約完了.prompt={tts_g:予防接種の予約を完了いたしました。
予約内容をお伝えします。
<% vaccineType %>、<% desiredDate_jp %>、<% desiredTime %>です。

次に、ご注意事項をお伝えいたします。
当日はマスク着用の上、病院の診察券を持って正面玄関からお入りください。
接種券をお持ちの方は必ずご持参ください。
もう一度、予約内容をお伝えします。
不要な方は電話をお切りください。
<% vaccineType %>、<% desiredDate_jp %>、<% desiredTime %>です。

次に、ご注意事項をお伝えいたします。
当日はマスク着用の上、病院の診察券を持って、正面玄関からお入りください。
接種券をお持ちの方は必ずご持参ください。
お電話ありがとうございました。}
END_変更完了.prompt={tts_g:予防接種の変更を完了いたしました。
予約内容をお伝えします。
<% vaccineType %>、<% desiredDate_jp %>、<% desiredTime %>です。

次に、ご注意事項をお伝えいたします。
当日はマスク着用の上、病院の診察券を持って正面玄関からお入りください。
接種券をお持ちの方は必ずご持参ください。
もう一度、予約内容をお伝えします。
不要な方は電話をお切りください。
<% vaccineType %>、<% desiredDate_jp %>、<% desiredTime %>です。

次に、ご注意事項をお伝えいたします。
当日はマスク着用の上、病院の診察券を持って、正面玄関からお入りください。
接種券をお持ちの方は必ずご持参ください。
お電話ありがとうございました。}
END_問合せ受付完了.prompt={tts_g:予防接種の問い合わせを受付いたしました。
日曜、祝日を除く3日以内に担当者から折り返し電話、
またはショートメールにてご連絡いたします。
お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。真生会富山病院、コロナ、インフルエンザ、
予防接種専用、AI電話です。}
用件確認.prompt={tts_g:ご用件を、次の4つから、お選びください。
「予約する」、「変更する」、「キャンセルする」、「その他問い合わせ」、
それでは、お話ください。}
接種後体調確認.prompt={tts_g:問い合わせの内容は、「接種後の体調不良について」でしょうか？
はい、そうです、または、いいえ、違います、のようにお答えください。}
問合せ_繋ぎ_アナウンス.prompt={tts_g:それでは、}
問合せ内容聴取.prompt={tts_g:お問い合わせの内容を簡潔にお話ください。}
問合せ_氏名繋ぎ_アナウンス.prompt={tts_g:次に、}
問合せ_生年月日繋ぎ_アナウンス.prompt={tts_g:続いて、}
キャンセル_繋ぎ_アナウンス.prompt={tts_g:次に、}
既存予約日聴取_キャンセル.prompt={tts_g:現在の予約日をお話ください。
わからない方は「わからない」とお話ください。}
キャンセル_氏名繋ぎ_アナウンス.prompt={tts_g:次に、}
キャンセル_生年月日繋ぎ_アナウンス.prompt={tts_g:続いて、}
変更_繋ぎ_アナウンス.prompt={tts_g:次に、}
既存予約日聴取_変更.prompt={tts_g:現在の予約日をお話ください。
わからない方は「わからない」とお話ください。}
変更_再予約_アナウンス.prompt={tts_g:それでは、現在の予約をキャンセルし、再度予約をお取りします。}
新規予約_1名分制限案内.prompt={tts_g:1度の電話で、予約できるのは、1名分のみです。}
ワクチン種類聴取.prompt={tts_g:接種希望のワクチンを、次の3つのうちの、いずれかでお話ください。
「インフルエンザワクチンのみ」、「新型コロナワクチンのみ」、「二つの同時接種」、
それではお話ください。}
インフル接種費用_案内.prompt={tts_g:射水市・富山市の接種券をお持ちの方は、接種券に記載の金額で、接種できます。
一般料金は4,000円です。}
コロナ接種費用_案内.prompt={tts_g:射水市・富山市の接種券をお持ちの方は、接種券に記載の金額で、接種できます。
一般料金は15,300円です。}
同時接種費用_案内.prompt={tts_g:射水市・富山市の接種券をお持ちの方は、接種券に記載の金額で、接種できます。
一般料金はインフルエンザ4,000円、コロナ15,300円です。}
予約希望日聴取_導入_アナウンス.prompt={tts_g:それでは、予約をお取りします。}
予約希望日聴取.prompt={tts_g:接種は午後に実施しています。接種日は、TODO_接種日（例: 1月26日月曜日）です。
ご都合の良い日を、お話ください。}
空き枠なし_案内.prompt={tts_g:大変申し訳ございません。
<% desiredDate_jp %>にご予約できる時間帯はございません。
再度ご希望の予約日をお伺いいたします。}
希望時間案内_アナウンス.prompt={tts_g:空いている時間をお伝えします。
<% startTimeList %>、です。
難しい場合は「いいえ」、とお答えください。
ご都合に合う時間がございましたら、希望の時間をお話ください。}
希望時間選択.prompt={tts_g:ご希望のお時間をお話ください。}
別時間_案内.prompt={tts_g:大変申し訳ございません。ご希望の時間帯、<% desiredTime %>、は予約が
取れないため、別の時間帯をご返答ください。
再度、空き時間を確認します。}
予約日時復唱確認.prompt={tts_g:<% vaccineType %>の、<% desiredDate_jp %>、<% desiredTime %>のご予約でよろしいでしょうか？}
予約完了_繋ぎ_アナウンス.prompt={tts_g:かしこまりました。}
予約_氏名繋ぎ_アナウンス.prompt={tts_g:次に、}
予約_生年月日繋ぎ_アナウンス.prompt={tts_g:続いて、}

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
