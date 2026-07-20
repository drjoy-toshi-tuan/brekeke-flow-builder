# IVR プロパティ — カレス記念病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_代表案内.prompt={tts_g:大変申し訳ございません。直近の診療に関するご用件はAI電話では承っておりません。 恐れ入りますが、代表電話にお電話をお願いいたします。 お電話ありがとうございました。それでは失礼いたします。}
END_残薬不足案内.prompt={tts_g:大変申し訳ございません。お薬が足りない場合はAI電話では承っておりません。 恐れ入りますが、代表電話にお電話をお願いいたします。 お電話ありがとうございました。それでは失礼いたします。}
終話_予約変更問合せ.prompt={tts_g:<%classification%>の申し込みを受付いたしました。 3診療日以内に担当者から折り返し電話、もしくはショートメールにてご連絡いたします。 お電話ありがとうございました。それでは失礼いたします。}
終話_キャンセル問合せ.prompt={tts_g:<%classification%>の申し込みを受付いたしました。 確認事項がある場合のみ3診療日以内に担当者から折り返し電話、もしくはショートメールにてご連絡いたします。 お電話ありがとうございました。それでは失礼いたします。}
END_非通知.prompt={tts_g:大変申し訳ございません。現在、非通知番号からの受付をしておりません。恐れ入りますが、発信者番号を通知してお掛け直しください。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。恐れ入りますが、改めておかけ直しください。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。 カレス記念病院の診療専用AI電話です。 「プ」と音が鳴ったらお話しください。}
3診療日確認.prompt={tts_g:こちらのお電話は、〇月〇日以降の受診を希望されるお問い合わせでしょうか？ 「はい、そうです」または「いいえ、違います」でお話しください。}
用件確認.prompt={tts_g:ご用件を次の４つのうちのいずれかでお話しください。 「1番、予約」「2番、変更」「3番、キャンセル」「4番、その他お問い合わせ」 ダイヤルプッシュでも入力いただけます。}
質問.prompt={tts_g:そのほかに何かお問い合わせはありますか。ない場合は「ありません。」とお話しください。}
氏名.prompt={tts_g:患者さんのお名前を「名前は山田太郎です。」のようにフルネームでお話しください。}
生年月日.prompt={tts_g:生年月日をお話しください。西暦の場合ダイヤルプッシュでも入力いただけます。}
復唱_連絡先番号確認_ANI.prompt={tts_g:ご連絡先は今おかけいただいている「××× ‐ ××× ‐ ×××」でよろしいですか？ 「はい、そうです」、または、「いいえ、ちがいます」、でお話しください。}
復唱_連絡先番号確認_ANI言い直し.prompt={tts_g:ご連絡先の電話番号は、<speak><say-as interpret-as="telephone"><%additionalPhoneNumber%></say-as></speak>、でよろしいですか？「はい、そうです」もしくは「いいえ、違います」でお答えください。}
聴取_連絡先番号確認_連絡先.prompt={tts_g:ご連絡先のお電話番号をお伺いします。携帯番号または0から始まる市外局番でお話しください。 ダイヤルプッシュでも入力いただけます。 入力が終わりましたら、最後に「こめじるし」を押してください。}
復唱_連絡先番号確認_連絡先.prompt={tts_g:ご連絡先の電話番号は、<speak><say-as interpret-as="telephone"><%additionalPhoneNumber%></say-as></speak>、でよろしいですか？「はい、そうです」もしくは「いいえ、違います」でお答えください。}
復唱_連絡先番号確認_連絡先言い直し.prompt={tts_g:ご連絡先の電話番号は、<speak><say-as interpret-as="telephone"><%additionalPhoneNumber%></say-as></speak>、でよろしいですか？「はい、そうです」もしくは「いいえ、違います」でお答えください。}
受診歴確認.prompt={tts_g:ご希望される診療科での受診ははじめてですか？わからない場合は、「わからない。」とお話しください。}
選定療養費アナウンス_予約.prompt={tts_g:他の医療機関からの紹介状をお持ちでない患者様につきましては、 通常の診療費とは別に、初診時選定療養費として7,700円を全額自己負担いただいております。 予めご了承ください。}
診療科.prompt={tts_g:受診を希望される診療科をお話しください。わからない場合は、「わからない。」とお話しください。}
予約希望日.prompt={tts_g:ご予約ご希望日をお話しください。ない場合は「ありません。」とお話しください。}
診療科_変更キャンセル.prompt={tts_g:予約されている診療科をお話しください。わからない場合は、「わからない。」とお話しください。}
主治医の先生_変更キャンセル.prompt={tts_g:主治医の先生をお話しください。わからない場合は、「わからない。」とお話しください。}
予約日聴取.prompt={tts_g:現在のご予約日をお話しください。}
理由_変更.prompt={tts_g:変更の理由をお話しください。}
理由_キャンセル.prompt={tts_g:キャンセルの理由をお話しください。}
薬処方確認_変更キャンセル.prompt={tts_g:病院からお薬を処方されている方は、「はい、飲んでいます」と、 されていない方は「いいえ、飲んでいません」とお話しください。}
残薬確認.prompt={tts_g:残薬について確認をいたします。 残薬がある場合は「はい、あります」、無い場合は「いいえありません」とお話しください。}
FAQ回答_問い合わせ内容.prompt={tts_g:TODO_発話内容を記入}
問い合わせ内容.prompt={tts_g:お問い合わせ内容をお話しください。}
FAQ不一致アナウンス.prompt={tts_g:(要記入 — FAQ不一致時の案内文言。sheet_faq.csv 整備後に確定)}

# wait
冒頭.wait=2000

# 施設固有（要編集）
office_id=6a44c5d815f52d0007140538

# 環境設定
# amivoice
amivoice.uri=ws://10.0.20.11:8000/ws
amivoice.language=ja
amivoice.engine=会話汎用
amivoice.keep_filter_token=true
amivoice.silent_detection_ms=2000
amivoice.timeout_ms=30000
amivoice.probability=0.7
amivoice.detection_flag=検出しない
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

- [ ] 以下のモジュールにアナウンス文言を記入する:
  - `FAQ回答_問い合わせ内容`

## 要レビュー（個人情報聴取の汎用デフォルト文言を使用）

以下のモジュールは設計書に施設固有の文言（`tts_modules` / `step_details`）が無かったため、汎用デフォルトを自動適用しています。TODO ではなく発話として出力済みですが、施設の呼称・敬語レベルに合わせて調整が必要か確認してください:
  - `復唱_連絡先番号確認_ANI言い直し`
  - `復唱_連絡先番号確認_連絡先`
  - `復唱_連絡先番号確認_連絡先言い直し`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
