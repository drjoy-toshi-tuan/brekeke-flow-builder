# IVR プロパティ — 信州大学医学部附属病院 病診連携

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}
END_時間外.prompt={tts_g:申し訳ございません。ただいまの時間は受付時間外となっております。受付時間は、土日祝日と年末年始を除く、月曜日から金曜日の8時30分から17時15分です。恐れ入りますが、受付時間内におかけなおしください。お電話ありがとうございました。}
END_聴取失敗.prompt={tts_g:大変申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、地域医療連携支援室へおかけ直しください。電話番号が分かる方は、このままお電話をお切りください。わからない方はご案内しますので、メモをご準備ください。0263-37-3370、0263-37-3370、0263-37-3370。お電話ありがとうございました。}
END_FAX到着確認.prompt={tts_g:申込みを受付けしました。到着が確認できない場合は折り返しご連絡致します。お電話ありがとうございました。}
END_情報提供依頼.prompt={tts_g:申込みを受付けしました。お電話ありがとうございました。}
END_入院転院依頼.prompt={tts_g:入院・転院依頼を受付いたしました。診療科よりお返事いたします。お電話ありがとうございました。}
END_その他問合せ.prompt={tts_g:お問い合わせを受付いたしました。担当者から折り返しご連絡いたします。お電話ありがとうございました。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。信大病院・連携室AI電話です。}
施設名聴取.prompt={tts_g:まず初めに、施設名をお話ください。}
担当者名聴取.prompt={tts_g:続いて、お電話いただいているご担当者様のお名前をお話ください。}
用件確認.prompt={tts_g:ご用件をダイヤルプッシュで選択してください。1「FAX到着確認」、2「情報提供依頼」、3「入院・転院依頼」、4「その他問合せ」、それでは、ご選択ください。}
用件詳細_FAX到着確認.prompt={tts_g:FAXにてご送信いただいた内容を、ダイヤルプッシュでお答えください。「診療報告」は1番、「問い合わせ回答」は2番、「これから受診の方の追加情報」は3番、「その他」は4番、それではご選択ください。}
FAX_内容確認.prompt={tts_g:ご連絡いただきました内容を簡単にお話ください。}
当日予約日_情報提供依頼.prompt={tts_g:本日または明日の回答をご希望ですか？はいの方は1番を、いいえの方は2番を、ダイヤルプッシュで選択してください。それではご選択ください。}
情報提供_生年月日.prompt={tts_g:患者さんの生年月日をおっしゃってください。}
情報提供_診療科.prompt={tts_g:対象の診療科をお話ください。}
用件詳細_情報提供依頼.prompt={tts_g:ご依頼内容をダイヤルプッシュで選択してください。「治療の経過」は1番、「MRIの実施可否」は2番、「その他」は3番、それではご選択ください。}
情報提供_内容確認.prompt={tts_g:ご連絡いただきました内容を簡単にお話ください。}
返答期限_情報提供依頼.prompt={tts_g:お返事の期限を教えてください。}
当日予約日_入院転院.prompt={tts_g:本日または明日の入院・転院をご希望ですか？はいの方は1番を、いいえの方は2番を、ダイヤルプッシュで選択してください。それではご選択ください。}
入院転院_生年月日.prompt={tts_g:患者さんの生年月日をおっしゃってください。}
入院転院_診療科.prompt={tts_g:対象の診療科をお話ください。}
希望時期_入院転院.prompt={tts_g:入院、または転院を希望する時期をお話ください。}
医師間共有.prompt={tts_g:貴院と当院、医師間で本件は既にお話いただいてる状況ですか？はいの方は1番を、いいえの方は2番を、ダイヤルプッシュで選択してください。それではご選択ください。}
医師名_入院転院.prompt={tts_g:事前にご相談いただいた当院医師名をお話ください。分からない場合は「分からない」とお話ください。}
その他問合せ_入院転院.prompt={tts_g:その他、職員へお伝えになりたいことがありましたらお話ください。ない場合には「特にない」などとお話ください。}
用件詳細_問合せ.prompt={tts_g:次のうちいずれかの番号をダイヤルプッシュで選択してください。「紹介状の送信依頼」は1番、「問い合わせの進捗確認」は2番、「その他の問合せ」は3番、それではご選択ください。}
問合せ_その他内容.prompt={tts_g:それでは、お問い合わせいただいた内容をお話ください。}
問合せ_生年月日.prompt={tts_g:患者さんの生年月日をおっしゃってください。}
問合せ_診療科.prompt={tts_g:対象の診療科をお話ください。}

# サブフローTTS
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}

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
