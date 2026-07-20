# アナウンス
冒頭アナウンス.prompt={tts_g: お電話ありがとうございます。ユアクリニックお茶の水のAI電話です。全部で3つ質問をさせていただきます。}
冒頭アナウンス2.prompt={tts_g: お電話ありがとうございます。ユアクリニックお茶の水のAI電話です。只今のお時間は、スタッフへお繋ぎいたします。代表電話に転送いたしますのでそのままお待ちください。}
時間外アナウンス.prompt={tts_g:お電話ありがとうございます。ユアクリニックお茶の水のAI電話です。ただいまのお時間は診療時間外です。救急の方は東京都医療機関案内サービス、ひまわり<say-as interpret-as="telephone">03-5272-0303</say-as>におかけください。当院へお問い合わせの方は、この後にご用件をお伺いいたします。内容確認後、院内スタッフから翌営業日終了までにショートメッセージもしくはお電話にてご連絡いたします。全部で3つ質問をさせていただきます。}
代表転送アナウンス.prompt={tts_g: 申し訳ございません、うまく認識ができませんでした。代表電話に転送いたしますのでそのままお待ちください。}
かけ直しアナウンス.prompt={tts_g: 申し訳ございません。只今お電話が込み合っております。恐れ入りますが、お時間を空けて再度おかけなおしください。お電話ありがとうございました。それでは失礼いたします。}
かけ直しアナウンス2.prompt={tts_g: 申し訳ございません、うまく認識ができませんでした。恐れ入りますが、お時間を空けて再度おかけなおしください。お電話ありがとうございました。それでは失礼いたします。}
確認_問い合わせ内容.prompt={tts_g: まずは1つ目の質問です。本日のお問い合わせ内容をお話ください。それではどうぞ。}
終話アナウンス.prompt={tts_g: ありがとうございます。質問は以上です。 内容確認後、院内スタッフから土・日、祝日を除く2日以内にショートメッセージもしくはお電話にてご連絡いたします。お電話ありがとうございました。 それでは失礼いたします。}

## 氏名聴取サブフロー (ユアCLお茶水$氏名聴取)
### 患者_氏名.prompt={tts_g: かしこまりました。続いて2つ目の質問です。お名前をフルネームでお話ください。それではどうぞ。}
### 患者_連絡先.prompt={tts_g: ありがとうございます。それでは、最後の質問です。ご連絡先のお電話番号をお伺いします。折返しの電話番号は、ただいまおかけいただいている番号でよろしいでしょうか？はいの場合は1を、いいえの場合は2を、ダイヤルプッシュで入力してください。}

## Re-confirmation node data モジュールは params.prompt に直接設定済み
### 患者_携帯: 「ご連絡先の電話番号は、今おかけいただいている、{電話番号}、でよろしいですか？」
### 復唱_患者_連絡先: 「ご連絡先の電話番号は、{電話番号}、でよろしいですか？」

# amivoice
amivoice.uri=ws://10.0.20.11:8000/ws
amivoice.language=ja
amivoice.engine=入力汎用
amivoice.keep_filter_token=true
amivoice.silent_detection_ms=2000
amivoice.timeout_ms=30000
amivoice.probability=0.6
amivoice.detection_flag=検出しない
amivoice.save_log=false

# Save2DB
office_id=5b8a5376d2122d061d50df75

# デモ用設定テンプレ
pbx.db.name=save.db
context.settings.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/pbx/context-model
acceptance_times.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/incoming-call-by-brekeke
rag_ssml.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/rag-ssml/process-text
openAI_generate.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/openai/generate-text

#RAG
speech.rag.url=http://10.0.20.11:8000/api/v1/rag
speech.rag.connect_timeout=2
speech.rag.request_timeout=3
speech.rag.credibility=0