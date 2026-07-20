# IVR プロパティ — 深川市立病院 地域連携

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）— メインフロー（深川市立病院$地域連携_20260410）
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。深川市立病院の地域連携室専用AI電話です。ご用件は受診申込みですか。「はい、そうです」「いいえ、違います」のようにお話しください。}
受診申込確認.prompt={tts_g:受診のお申し込みでしょうか。}
本日受診確認.prompt={tts_g:本日の受診をご希望ですか。「本日希望」もしくは「明日以降」とお話しください。}
所属氏名_聴取.prompt={tts_g:お電話いただいている方の所属とお名前をお話しください。}
患者問合せ確認.prompt={tts_g:患者様に関するお問合せでしょうか。「はい、そうです」「いいえ、違います」のようにお話しください。}
外来入院確認.prompt={tts_g:患者様が外来の方か、入院の方かを確認いたします。外来の方は「外来です」、入院の方は「入院です」とお話しください。}
患者氏名_聴取.prompt={tts_g:患者様のお名前をフルネームでお話しください。}
患者生年月日_聴取.prompt={tts_g:患者様の生年月日を西暦もしくは和暦でお話しください。}
内容_聴取.prompt={tts_g:お問い合わせの内容をお話しください。}
END_代表案内.prompt={tts_g:当日の受診希望はAI電話では承っておりません。お手数ですが代表電話0164-22-1101へおかけ直しいただき、該当外来へ受診希望をお伝えください。お電話ありがとうございました。}
END_予約フォーム.prompt={tts_g:当院のホームページにございます、患者紹介予約申込専用の診療情報提供書に必要事項を記入し、地域連携室までファックスをお願いいたします。予約が取れ次第、連携室より予約票をファックスいたします。お電話ありがとうございました。}
END_正常終話.prompt={tts_g:お問い合わせを承りました。確認次第、担当者からご連絡いたします。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:大変申し訳ございません。うまく聞き取りができませんでした。担当者よりご連絡いたします。お電話ありがとうございました。}
時間外_アナウンス.prompt={tts_g:ただいまの時間は受付時間外となります。恐れ入りますが、時間内におかけ直しください。稼働時間は土、日、祝日を除く平日、8時30分から16時です。お電話ありがとうございました。}
非通知_アナウンス.prompt={tts_g:非通知のお電話はお受けできません。お電話ありがとうございました。}

# アナウンス（TTS prompt）— 電話番号聴取サブフロー（深川市立病院$電話番号聴取_20260410）
患者_連絡先.prompt={tts_g:お折り返し先のお電話番号を入力してください。}

# wait
冒頭_wait.wait=2000

# 施設固有（要編集）
office_id=TODO_施設のoffice_idを入力

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

- [ ] `office_id` を設定する（設計書に `TODO_要確認` と記載あり。確認後に実際の値を入力すること）
- [ ] `患者_連絡先.prompt` の発話文言を確認・調整する（サブフローデフォルト文言を仮設定済み。設計書に指定がある場合はその文言に変更すること）

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
> DTMFモジュールの `{recstart}` もIVRプロパティには記載しない。フローJSON内の `params.prompt` に直接記述すること。
