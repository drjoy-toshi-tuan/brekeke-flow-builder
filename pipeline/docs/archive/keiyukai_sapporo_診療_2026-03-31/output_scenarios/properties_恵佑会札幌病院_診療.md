# IVRプロパティ — 恵佑会札幌病院 診療（デモ環境）

> フロー名: `恵佑会札幌$診療`
> 対象環境: デモ
> office_id: `TODO_office_id`（BLOCKER: 施設ID未確定。確定後に置き換えること）
> 生成日: 2026-03-30

---

## 環境設定

```properties
# wait
wait_2000ms.wait=2000

# amivoice
amivoice.uri=ws://10.0.20.11:8000/ws
amivoice.language=ja
amivoice.engine=入力汎用
amivoice.keep_filter_token=true
amivoice.silent_detection_ms=2000
amivoice.timeout_ms=30000
amivoice.probability=0.6
amivoice.detection_flag=音声開始前から検出
amivoice.save_log=false

# Save2DB / PBX
office_id=TODO_office_id
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

---

## TTSプロンプト

```properties
# 冒頭アナウンス
冒頭_アナウンス.prompt={tts_g: お電話ありがとうございます。こちらは恵佑会札幌病院、歯科口腔外科の予約専用自動応答サービスです。}

# 非通知・時間外
非通知_アナウンス.prompt={tts_g: 恐れ入りますが、お電話番号の前に186をつけておかけ直しください。}
時間外_アナウンス.prompt={tts_g: ただいまの時間は受付時間外となっております。受付時間は平日8時45分から17時までです。恐れ入りますが、受付時間内におかけ直しください。}

# 申し込み方法確認
TTS_申し込み方法確認.prompt={tts_g: まずはじめに、申し込み方法をお伺いします。ネットで申し込みを希望の方は、申込用のURLをショートメールにてお送りします。次のいずれかの番号をお話しください。「ネットから申し込みを希望の方は、1」、「このままお電話での申し込み希望の方は、2」、または{recstart}}

# SMS用連絡先電話番号
TTS_SMS_連絡先携帯.prompt={tts_g: <speak>ご連絡先のお電話番号は、今おかけいただいている<say-as interpret-as="telephone">#data#</say-as><break time="300ms"/>でよろしいでしょうか？</speak>}
TTS_SMS_連絡先固定.prompt={tts_g: URLを送付するために、ご連絡先の携帯番号をお伺いします。携帯番号をお話しください。{recstart}}
TTS_SMS_連絡先固定_復唱確認.prompt={tts_g: <speak><say-as interpret-as="telephone">#data#</say-as><break time="300ms"/>でよろしいでしょうか。</speak>}

# 用件確認
TTS_用件確認.prompt={tts_g: <speak>次の4つのうち、いずれかの番号をお話しください。<break time="300ms"/>「予約を申し込む方は、1」、<break time="300ms"/>「予約を変更する方は、2」、<break time="300ms"/>「予約をキャンセルする方は、3」、<break time="300ms"/>「その他お問い合わせの方は、4」{recstart}</speak>}

# 受診歴確認
TTS_受診歴確認.prompt={tts_g: 新規予約をご希望ですか？2回目以降の診察予約ですか？}

# 紹介状確認
TTS_紹介状確認.prompt={tts_g: 紹介状はお持ちでしょうか？}

# 医師名確認（紹介状あり）
TTS_医師名確認.prompt={tts_g: 封筒に記載の、先生の名前をお話ください。}

# 希望医師確認（紹介状なし）
TTS_希望医師確認.prompt={tts_g: 診察を希望される先生の名前をお話ください。ご希望がない場合は、なしとお話ください。}

# 予約希望日（再診ルート）
TTS_予約希望日_再診.prompt={tts_g: 次に、予約希望日をお伺いいたします。予約日は3診療日以内の折り返し連絡にて確定いたします。それではご都合の良い日付や曜日をお話しください。}

# 予約日（変更ルート）
TTS_予約日_変更.prompt={tts_g: 現在の予約日をお話ください。}

# 予約希望日（変更ルート）
TTS_予約希望日_変更.prompt={tts_g: 次に、予約希望日をお伺いいたします。予約日は3診療日以内の折り返し連絡にて確定いたします。それではご都合の良い日付や曜日をお話しください。}

# 予約日（キャンセルルート）
TTS_予約日_キャンセル.prompt={tts_g: 現在の予約日をお話ください。}

# キャンセル理由
TTS_キャンセル理由.prompt={tts_g: キャンセルの理由をお話ください。}

# 内容確認（その他問い合わせ）
TTS_内容確認.prompt={tts_g: お問い合わせの内容をお話しください。}

# 最終問い合わせ確認
TTS_最終問い合わせ確認.prompt={tts_g: そのほかに何かお問い合わせは有りませんか？}

# 終話アナウンス — 予約
TTS_END_予約_MOBILE.prompt={tts_g: <speak>診察予約のご希望を受け付けました。<break time="300ms"/>このあとすぐに、通話内容の確認・修正ができるショートメッセージをお送りしますので、必ずご確認ください。<break time="300ms"/>また、3診療日以内に担当者より折り返しお電話、もしくはショートメールにてご連絡いたします。<break time="300ms"/>担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/>お電話ありがとうございました。それでは失礼いたします。</speak>}
TTS_END_予約_FIXED.prompt={tts_g: <speak>診察予約のご希望を受け付けました。<break time="300ms"/>3診療日以内に担当者から折り返し電話にてご連絡いたします。<break time="300ms"/>担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/>お電話ありがとうございました。それでは失礼いたします。</speak>}

# 終話アナウンス — 変更
TTS_END_変更_MOBILE.prompt={tts_g: <speak>予約変更のご希望を受け付けました。<break time="300ms"/>このあとすぐに、通話内容の確認・修正ができるショートメッセージをお送りしますので、必ずご確認ください。<break time="300ms"/>また、3診療日以内に担当者より折り返しお電話、もしくはショートメールにてご連絡いたします。<break time="300ms"/>担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/>お電話ありがとうございました。それでは失礼いたします。</speak>}
TTS_END_変更_FIXED.prompt={tts_g: <speak>予約変更のご希望を受け付けました。<break time="300ms"/>3診療日以内に担当者から折り返し電話にてご連絡いたします。<break time="300ms"/>担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/>お電話ありがとうございました。それでは失礼いたします。</speak>}

# 終話アナウンス — キャンセル
TTS_END_キャンセル_MOBILE.prompt={tts_g: <speak>予約キャンセルのご希望を受け付けました。<break time="300ms"/>このあとすぐに、通話内容の確認・修正ができるショートメッセージをお送りしますので、必ずご確認ください。<break time="300ms"/>また、3診療日以内に担当者より折り返しお電話、もしくはショートメールにてご連絡いたします。<break time="300ms"/>担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/>お電話ありがとうございました。それでは失礼いたします。</speak>}
TTS_END_キャンセル_FIXED.prompt={tts_g: <speak>予約キャンセルのご希望を受け付けました。<break time="300ms"/>3診療日以内に担当者から折り返し電話にてご連絡いたします。<break time="300ms"/>担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/>お電話ありがとうございました。それでは失礼いたします。</speak>}

# 終話アナウンス — その他問い合わせ
TTS_END_その他_MOBILE.prompt={tts_g: <speak>その他問い合わせのご希望を受け付けました。<break time="300ms"/>このあとすぐに、通話内容の確認・修正ができるショートメッセージをお送りしますので、必ずご確認ください。<break time="300ms"/>また、3診療日以内に担当者より折り返しお電話、もしくはショートメールにてご連絡いたします。<break time="300ms"/>担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/>お電話ありがとうございました。それでは失礼いたします。</speak>}
TTS_END_その他_FIXED.prompt={tts_g: <speak>その他問い合わせのご希望を受け付けました。<break time="300ms"/>3診療日以内に担当者から折り返し電話にてご連絡いたします。<break time="300ms"/>担当者からのご連絡をもって、受付が確定いたします。<break time="300ms"/>お電話ありがとうございました。それでは失礼いたします。</speak>}

# 終話アナウンス — SMS送信案内
END_SMS送信案内.prompt={tts_g: 申込みのページを、ショートメールでお送りします。メッセージのリンクを開き、はじめに「電話番号」で本人確認をしてください。そのあと、患者さまの情報を入力してください。お電話ありがとうございました。それでは失礼いたします。}

# 終話アナウンス — 受付不可診療科
END_受付不可診療科.prompt={tts_g: <speak>大変申し訳ございません。歯科口腔外科以外の診療科に関するお問い合わせはこちらでは承っておりません。恐れいりますが、このあとご案内をする専用電話にお問い合わせください。番号をご案内しますのでメモをご準備下さい。番号は<say-as interpret-as="telephone">050-1726-5776</say-as>です。電話番号は<say-as interpret-as="telephone">050-1726-5776</say-as>です。それでは失礼いたします。</speak>}

# 終話アナウンス — 代表案内（申し込み方法失敗）
END_代表案内_申し込み方法.prompt={tts_g: <speak>大変申し訳ございません。うまく聞き取ることができませんでした。恐れ入りますが、代表電話番号へおかけなおしください。受付時間は平日8時45分から17時までです。お電話番号をご案内いたしますのでメモをご準備ください。<say-as interpret-as="telephone">011-863-2105</say-as>です。<say-as interpret-as="telephone">011-863-2105</say-as>です。<say-as interpret-as="telephone">011-863-2105</say-as>です。お電話ありがとうございました。それでは失礼いたします。</speak>}

# 終話アナウンス — 上限エラー（電話番号聴取上限到達）
END_上限エラー.prompt={tts_g: ご回答の確認ができませんでしたのでこちらからお電話失礼させていただきます。それでは失礼いたします。}
```

---

## Retry Counter プロンプト（JSON直接設定 — 参考）

> Retry Counter の `prompt_true`（リトライ時）・`prompt_false`（上限到達時）はフローJSON内に直接記述します。
> 以下はIVRプロパティではなく、フローJSON内の `params` に設定する値の参考です。

```
リトライ_申し込み方法確認.prompt_true:
  恐れ入りますがご回答が確認できませんでした。再度、申し込み方法をお伺いします。ネットで申し込みを希望の方は、申込用のURLをショートメールにてお送りします。次のいずれかの番号をお話しください。「ネットから申し込みを希望の方は、1」、「このままお電話での申し込み希望の方は、2」、または{recstart}

リトライ_SMS_連絡先固定.prompt_true:
  申し訳ございません、聞き取りができませんでした。なお、AIが電話番号を正しく認識しない場合は、ダイヤルプッシュでの入力も可能です。再度、ご連絡先のお電話番号を携帯番号でおっしゃっていただくか、{recstart}

リトライ_予約希望日_再診.prompt_true:
  申し訳ございません。ご希望の日付をもう一度お話しください。

リトライ_予約希望日_変更.prompt_true:
  申し訳ございません。ご希望の日付をもう一度お話しください。

リトライ_予約日_変更.prompt_true:
  申し訳ございません。現在の予約日をもう一度お話しください。

リトライ_予約日_キャンセル.prompt_true:
  申し訳ございません。現在の予約日をもう一度お話しください。
```

> `prompt_false`（上限到達）は全Retryモジュール共通でシステムデフォルト（空欄）。

---

## 注意事項

- `office_id=TODO_office_id` は **BLOCKER**。施設IDが確定次第、`TODO_office_id` を実際のIDに置き換えること。
- `非通知_アナウンス` および `時間外_アナウンス` の文言は仮設定。設計書の要確認事項を参照し、確定後に修正すること。
- サブフロー（`恵佑会札幌$氏名聴取` 等）のIVRプロパティはこのファイルに含まれない。サブフローは `docs/reference/bivr/samples/個人情報サブフロー.bivr` からコピーしたため、サブフロー側のプロパティは別途設定が必要。
- `TTS_SMS_連絡先携帯` および `TTS_SMS_連絡先固定_復唱確認` の `#data#` はRe-confirmation node dataモジュール専用の記法。実際のモジュール種別に応じて確認すること。
