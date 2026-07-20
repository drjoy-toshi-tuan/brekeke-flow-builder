# IVRプロパティ — 中之島CL 健診（デモ環境）
# 対象フロー: 中之島CL$健診 / 中之島CL$氏名聴取 / 中之島CL$電話番号聴取

---

## TTSプロンプト

```properties
# ===== 中之島CL$健診（メインフロー）=====

# 時間外
時間外_アナウンス.prompt={tts_g: ただいまの時間は受付時間外となっております。受付時間内に改めてお電話ください。お電話ありがとうございました。}
END_時間外.prompt={tts_g: お電話ありがとうございました。}

# 非通知
非通知_アナウンス.prompt={tts_g: 恐れ入りますが、電話番号を通知のうえ、改めておかけ直しください。お電話ありがとうございました。}
END_非通知.prompt={tts_g: お電話ありがとうございました。}

# 冒頭
冒頭_アナウンス.prompt={tts_g: お電話ありがとうございます。お問い合わせの施設をお選びください。}

# 施設選択
施設_選択.prompt={tts_g: 中之島クリニックの方は1、中之島クリニックレディースプラザの方は2、西宮ガーデンズ健診クリニックの方は3を押してください。}

# 用件選択
用件_選択.prompt={tts_g: ご用件をお選びください。人間ドックや健診のご予約・お問い合わせの方は1、それ以外のお問い合わせの方は2を押してください。}

# 問合せ内容
問合せ_内容.prompt={tts_g: 改めて内容を確認のうえ折り返しご連絡いたしますが、本日はどのようなご用件でしょうか。}

# ===== 中之島CL$氏名聴取（サブフロー）=====

# 氏名聴取
氏名_聴取.prompt={tts_g: お名前をお話しください。}

# ===== 中之島CL$電話番号聴取（サブフロー）=====

# 携帯パス — 着信番号復唱確認
携帯_確認.prompt={tts_g: <speak>ご連絡先の電話番号は<break time="200ms"/><speak type="telephone" breakc="300ms">{telephoneNumber}</speak>でよろしいでしょうか。よろしければ1、違う場合は2を押してください。</speak>}

# その他パス — 電話番号聴取
電話番号_聴取.prompt={tts_g: ご連絡先の電話番号をお話しいただくか、プッシュボタンで入力してください。}

# 電話番号確認 (Re-confirmation)
電話番号_確認.prompt={tts_g: <speak>連絡先の電話番号は<break time="200ms"/><speak type="telephone" breakc="300ms">{additionalPhoneNumber}</speak>でよろしいでしょうか。よろしければ1、違う場合は2を押してください。</speak>}

# 電話番号訂正
電話番号_訂正.prompt={tts_g: 正しい電話番号を再度お話しいただくか、プッシュボタンで入力してください。}

# 終話 — 人間ドック
END_人間ドック.prompt={tts_g: 人間ドックのご連絡を承りました。担当者からの連絡にて確定となります。なお、この後届くショートメッセージのURLから項目の入力をお願いいたします。お電話ありがとうございました。}

# 終話 — その他
END_その他.prompt={tts_g: ご用件をお預かりいたしました。担当者から折り返し電話、もしくはショートメッセージにてご連絡いたします。お電話ありがとうございました。}

# 終話 — 上限エラー
END_上限到達エラー.prompt={tts_g: 申し訳ございません。折り返し先のお電話番号を聞き取ることができませんでした。恐れ入りますが、コールセンターへおかけ直しください。お電話ありがとうございました。}
```

---

## リトライカウンター

```properties
# ===== 中之島CL$健診 =====
リトライ_施設_選択.prompt_true={tts_g: 恐れ入りますがご回答が確認できませんでした。今一度、}
リトライ_施設_選択.prompt_false={tts_g: かしこまりました。折り返しの際にお伺いいたします。}
リトライ_用件_選択.prompt_true={tts_g: 恐れ入りますがご回答が確認できませんでした。今一度、}
リトライ_用件_選択.prompt_false={tts_g: かしこまりました。折り返しの際にお伺いいたします。}
リトライ_問合せ_内容.prompt_true={tts_g: 恐れ入りますがご回答が確認できませんでした。今一度、}
リトライ_問合せ_内容.prompt_false={tts_g: かしこまりました。折り返しの際にお伺いいたします。}

# ===== 中之島CL$氏名聴取 =====
リトライ_氏名.prompt_true={tts_g: 恐れ入りますがご回答が確認できませんでした。今一度、}
リトライ_氏名.prompt_false={tts_g: かしこまりました。折り返しの際にお伺いいたします。}

# ===== 中之島CL$電話番号聴取 =====
リトライ_携帯_確認.prompt_true={tts_g: 恐れ入りますがご回答が確認できませんでした。今一度、}
リトライ_携帯_確認.prompt_false={tts_g: かしこまりました。折り返しの際にお伺いいたします。}
リトライ_電話番号.prompt_true={tts_g: 恐れ入りますがご回答が確認できませんでした。今一度、}
リトライ_電話番号.prompt_false={tts_g: 申し訳ございません。折り返し先のお電話番号を聞き取ることができませんでした。}
リトライ_電話番号_確認.prompt_true={tts_g: 恐れ入りますがご回答が確認できませんでした。今一度、}
リトライ_電話番号_確認.prompt_false={tts_g: かしこまりました。折り返しの際にお伺いいたします。}
```

---

## 環境設定

```properties
# wait
wait.wait=2000

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
office_id=TODO_要確認
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

> **TODO**: `office_id` は Dr.JOY 管理画面で施設IDを確認して設定すること。
