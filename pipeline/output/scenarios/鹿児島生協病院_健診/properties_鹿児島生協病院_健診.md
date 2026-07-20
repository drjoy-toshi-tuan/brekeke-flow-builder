# IVR プロパティ — 鹿児島生協病院 健診

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:申し訳ございません。ただいまの時間は受付時間外です。受付時間は日曜祝日、年末年始を除く、月曜日から金曜日の8時30分から16時30分、土曜日は8時30分から12時です。恐れ入りますが、代表電話番号へおかけなおしください。番号が分かる場合は、電話をお切りください。分からない場合はご案内いたしますのでメモをご準備ください。電話番号は、099-267-1455です。繰り返します。電話番号は、099-267-1455です。繰り返します。電話番号は、099-267-1455です。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:大変申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、代表電話番号へおかけなおしください。受付時間は日曜祝日、年末年始を除く、月曜日から金曜日の8時30分から16時30分、土曜日は8時30分から12時です。番号が分かる場合は、電話をお切りください。分からない場合はご案内いたしますのでメモをご準備ください。電話番号は、099-267-1455です。繰り返します。電話番号は、099-267-1455です。繰り返します。電話番号は、099-267-1455です。お電話ありがとうございました。}
END_締めあいさつ_携帯.prompt={tts_g:3営業日以内に担当者から折り返し電話、もしくは、ショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_締めあいさつ_その他.prompt={tts_g:3営業日以内に担当者から折り返し電話、もしくは、ショートメールにてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_GW.prompt={tts_g:大変申し訳ございませんが、5月6日まで休診となっております。なお、受付再開は5月7日からとなっております。恐れ入りますが、受付時間内におかけなおしください。お電話ありがとうございました。}
END_年末年始.prompt={tts_g:年末年始のため、担当者不在となっております。1月4日 10時より、順次担当者から折り返し、もしくはショートメールにてご連絡いたします。お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。鹿児島生協病院の、健診専用、AI電話です。}
1名複数名確認.prompt={tts_g:今回のお申込みは、1名分ですか？1名の場合は「はい、そうです」、複数名の場合は「いいえ、違います」、で、お答えください。}
用件聴取.prompt={tts_g:ご用件を、次の4つのうちの、いずれかでお話ください。
「1，健診の予約」
「2，予約の変更」
「3，予約のキャンセル」
「4，その他お問合せ」
それでは、お話ください。}
健診種類聴取.prompt={tts_g:健診の種類についてお伺いします。
これよりご案内する番号を、ダイヤルプッシュ、または、番号でお答えください。
検査結果を会社へ提出する採用時健診、定期健診は1番、
協会けんぽの生活習慣病予防健診は2番、
人間ドック等、それ以外の健診は3番、
わからない場合は、わからないとお答えください。}
所定用紙確認.prompt={tts_g:結果を記載する、所定の用紙はお持ちですか？お持ちの場合は、はい、お持ちでない場合は、いいえ、とお答えください。}
用紙注意_アナウンス.prompt={tts_g:健診結果用紙は当院所定の用紙での対応となり、手書きでの対応はできませんのであらかじめご了承下さい。}
新規_受診希望時期聴取.prompt={tts_g:受診を希望される時期をおはなしください。}
新規_2週間案内.prompt={tts_g:かしこまりました。健診結果票は受診日から2週間程度かかります。あらかじめご了承下さい。続いて、}
予約日聴取.prompt={tts_g:現在の予約日を教えてください。わからない場合には、「わからない」、とお話ください。}
胃カメラ検査確認.prompt={tts_g:ご予約のコースの中に、胃カメラの検査はございますか？「はい、あります」や、「いいえ、ないです」のように、お答えください。}
変更_受診希望時期聴取.prompt={tts_g:受診を希望される時期をおはなしください。}
問い合わせ内容聴取.prompt={tts_g:ご用件をお話ください。}
問い合わせ追加聴取.prompt={tts_g:その他、健診の内容で追加のご連絡事項はございますか？ございましたら、このままお話ください。}
職場名聴取.prompt={tts_g:健康診断の結果を提出する、職場名をお話ください。}

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
